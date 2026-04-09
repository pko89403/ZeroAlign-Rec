import json
from pathlib import Path

import numpy as np
import pandas as pd

from sid_reco.taxonomy.neighbor_context import (
    build_embedding_text,
    build_faiss_index,
    build_neighbor_context,
    encode_catalog_with_adaptive_batches,
    prepare_neighbor_catalog,
    search_topk_neighbors,
    suggest_embedding_batch_size,
)


class _FlakyEncoder:
    def __init__(self) -> None:
        self.seen_batch_sizes: list[int] = []

    def encode(self, texts: list[str]) -> list[list[float]]:
        self.seen_batch_sizes.append(len(texts))
        if len(texts) > 8:
            raise RuntimeError("simulated OOM")
        return [[float(len(text)), float(index + 1)] for index, text in enumerate(texts)]


def test_build_embedding_text_uses_selected_metadata_fields_only() -> None:
    items = pd.DataFrame(
        [
            {
                "recipe_id": 1,
                "name": "Tomato Soup",
                "description": "Simple comfort food.",
                "tags": json.dumps(["soup", "easy"]),
                "ingredients": json.dumps(["tomato", "salt"]),
            }
        ]
    )

    embedded = build_embedding_text(items)

    assert embedded.loc[0, "embedding_text"] == (
        "Title: Tomato Soup\n"
        "Description: Simple comfort food.\n"
        "Tags: soup, easy\n"
        "Ingredients: tomato, salt"
    )


def test_prepare_neighbor_catalog_normalizes_catalog_and_embedding_text(tmp_path: Path) -> None:
    recipes_path = tmp_path / "recipes.csv"
    pd.DataFrame(
        [
            {
                "recipe_id": 3,
                "name": " Tomato Soup ",
                "description": " Comfort food ",
                "tags": json.dumps(["soup", "easy"]),
                "ingredients": json.dumps(["tomato", "salt"]),
            }
        ]
    ).to_csv(recipes_path, index=False)

    prepared = prepare_neighbor_catalog(recipes_path)

    assert prepared["recipe_id"].tolist() == [3]
    assert prepared.loc[0, "name"] == "Tomato Soup"
    assert prepared.loc[0, "embedding_text"].startswith("Title: Tomato Soup")


def test_suggest_embedding_batch_size_uses_memory_tiers() -> None:
    assert suggest_embedding_batch_size(num_items=200, total_memory_bytes=48 * 1024**3) == 64
    assert suggest_embedding_batch_size(num_items=200, total_memory_bytes=24 * 1024**3) == 32
    assert suggest_embedding_batch_size(num_items=12, total_memory_bytes=None) == 12


def test_encode_catalog_with_adaptive_batches_halves_after_runtime_error() -> None:
    items = pd.DataFrame(
        {
            "recipe_id": list(range(16)),
            "name": [f"Recipe {index}" for index in range(16)],
            "description": ["desc"] * 16,
            "tags": [json.dumps(["easy"])] * 16,
            "ingredients": [json.dumps(["salt"])] * 16,
            "embedding_text": [f"Title: Recipe {index}" for index in range(16)],
        }
    )
    encoder = _FlakyEncoder()

    encoded = encode_catalog_with_adaptive_batches(
        items,
        encoder=encoder,  # type: ignore[arg-type]
        batch_size=16,
    )

    assert encoder.seen_batch_sizes[:2] == [16, 8]
    assert encoded.initial_batch_size == 16
    assert encoded.final_batch_size == 8
    assert encoded.min_batch_size == 8
    assert encoded.embeddings.shape == (16, 2)
    assert "embedding" in encoded.items.columns


def test_search_topk_neighbors_removes_self_and_uses_recipe_id_tiebreak() -> None:
    embeddings = np.asarray(
        [
            [1.0, 0.0],
            [0.0, 1.0],
            [0.0, 1.0],
        ],
        dtype=np.float32,
    )
    recipe_ids = [10, 30, 20]
    index = build_faiss_index(embeddings)

    neighbors = search_topk_neighbors(
        index=index,
        embeddings=embeddings,
        recipe_ids=recipe_ids,
        top_k=2,
    )

    source_10 = neighbors.loc[neighbors["source_recipe_id"] == 10].reset_index(drop=True)
    assert source_10["neighbor_recipe_id"].tolist() == [20, 30]
    assert source_10["neighbor_rank"].tolist() == [1, 2]
    assert 10 not in source_10["neighbor_recipe_id"].tolist()


def test_build_neighbor_context_uses_topk_plus_self_search_width(
    tmp_path: Path,
    monkeypatch,
) -> None:
    recipes_path = tmp_path / "recipes.csv"
    out_dir = tmp_path / "neighbor_context"
    pd.DataFrame(
        [
            {
                "recipe_id": 101,
                "name": "Tomato Soup",
                "description": "Warm tomato soup.",
                "tags": json.dumps(["soup", "easy"]),
                "ingredients": json.dumps(["tomato", "salt"]),
            },
            {
                "recipe_id": 102,
                "name": "Tomato Pasta",
                "description": "Tomato pasta dinner.",
                "tags": json.dumps(["pasta", "easy"]),
                "ingredients": json.dumps(["tomato", "pasta"]),
            },
            {
                "recipe_id": 103,
                "name": "Green Salad",
                "description": "Fresh salad bowl.",
                "tags": json.dumps(["salad", "fresh"]),
                "ingredients": json.dumps(["lettuce", "olive oil"]),
            },
        ]
    ).to_csv(recipes_path, index=False)

    class _SearchRecorder:
        def __init__(self) -> None:
            self.search_calls: list[int] = []

        def add(self, embeddings: np.ndarray) -> None:
            self.embeddings = embeddings

        def search(self, queries: np.ndarray, width: int) -> tuple[np.ndarray, np.ndarray]:
            self.search_calls.append(width)
            scores = np.asarray(
                [
                    [1.0, 0.8, 0.2],
                    [1.0, 0.8, 0.5],
                    [1.0, 0.5, 0.2],
                ],
                dtype=np.float32,
            )
            indices = np.asarray(
                [
                    [0, 1, 2],
                    [1, 0, 2],
                    [2, 1, 0],
                ],
                dtype=np.int64,
            )
            return scores[:, :width], indices[:, :width]

    class _FakeEncoder:
        def __init__(self, model_id: str) -> None:
            self.model_id = model_id

        def encode(self, texts: list[str]) -> list[list[float]]:
            return [[float(index + 1), float(index + 2)] for index, _ in enumerate(texts)]

    search_recorder = _SearchRecorder()
    monkeypatch.setattr(
        "sid_reco.taxonomy.neighbor_context.faiss.IndexFlatIP",
        lambda dimension: search_recorder,
    )
    monkeypatch.setattr(
        "sid_reco.taxonomy.neighbor_context.faiss.write_index",
        lambda index, path: None,
    )

    summary = build_neighbor_context(
        recipes_path=recipes_path,
        out_dir=out_dir,
        embed_model="fake-model",
        top_k=2,
        batch_size=2,
        encoder=_FakeEncoder("fake-model"),
    )

    assert search_recorder.search_calls == [3]
    assert summary.top_k == 2
