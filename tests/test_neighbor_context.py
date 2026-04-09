import json

import numpy as np
import pandas as pd

from sid_reco.taxonomy.neighbor_context import (
    build_embedding_text,
    build_faiss_index,
    encode_catalog_with_adaptive_batches,
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


class _UnexpectedRuntimeEncoder:
    def encode(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("bad tokenizer state")


class _StaticSearchIndex:
    def __init__(self, responses: list[tuple[np.ndarray, np.ndarray]]) -> None:
        self.responses = responses
        self.calls: list[int] = []

    def search(self, query: np.ndarray, top_k: int) -> tuple[np.ndarray, np.ndarray]:
        self.calls.append(top_k)
        response = self.responses[len(self.calls) - 1]
        return response


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


def test_encode_catalog_with_adaptive_batches_reraises_non_oom_runtime_error() -> None:
    items = pd.DataFrame(
        {
            "recipe_id": [1, 2],
            "name": ["Recipe 1", "Recipe 2"],
            "description": ["desc", "desc"],
            "tags": [json.dumps(["easy"]), json.dumps(["easy"])],
            "ingredients": [json.dumps(["salt"]), json.dumps(["salt"])],
            "embedding_text": ["Title: Recipe 1", "Title: Recipe 2"],
        }
    )

    try:
        encode_catalog_with_adaptive_batches(
            items,
            encoder=_UnexpectedRuntimeEncoder(),  # type: ignore[arg-type]
            batch_size=2,
        )
    except RuntimeError as exc:
        assert str(exc) == "bad tokenizer state"
    else:
        raise AssertionError("Expected the non-OOM runtime error to be re-raised.")


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


def test_search_topk_neighbors_uses_bounded_width_when_scores_are_distinct() -> None:
    embeddings = np.asarray(
        [
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
        ],
        dtype=np.float32,
    )
    recipe_ids = [10, 20, 30]
    index = _StaticSearchIndex(
        responses=[
            (
                np.asarray([[1.0, 0.8, 0.7]], dtype=np.float32),
                np.asarray([[0, 1, 2]], dtype=np.int64),
            ),
            (
                np.asarray([[1.0, 0.6, 0.5]], dtype=np.float32),
                np.asarray([[1, 0, 2]], dtype=np.int64),
            ),
            (
                np.asarray([[1.0, 0.9, 0.4]], dtype=np.float32),
                np.asarray([[2, 0, 1]], dtype=np.int64),
            ),
        ]
    )

    neighbors = search_topk_neighbors(
        index=index,  # type: ignore[arg-type]
        embeddings=embeddings,
        recipe_ids=recipe_ids,
        top_k=2,
    )

    assert index.calls == [3, 3, 3]
    assert len(neighbors) == 6


def test_search_topk_neighbors_expands_width_when_boundary_score_is_tied() -> None:
    embeddings = np.asarray(
        [
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
            [1.0, -1.0],
        ],
        dtype=np.float32,
    )
    recipe_ids = [10, 20, 30, 40]
    index = _StaticSearchIndex(
        responses=[
            (
                np.asarray([[1.0, 0.9, 0.9]], dtype=np.float32),
                np.asarray([[0, 3, 2]], dtype=np.int64),
            ),
            (
                np.asarray([[1.0, 0.9, 0.9, 0.8]], dtype=np.float32),
                np.asarray([[0, 3, 2, 1]], dtype=np.int64),
            ),
            (
                np.asarray([[1.0, 0.7, 0.6]], dtype=np.float32),
                np.asarray([[1, 0, 2]], dtype=np.int64),
            ),
            (
                np.asarray([[1.0, 0.7, 0.6, 0.5]], dtype=np.float32),
                np.asarray([[1, 0, 2, 3]], dtype=np.int64),
            ),
            (
                np.asarray([[1.0, 0.7, 0.6]], dtype=np.float32),
                np.asarray([[2, 0, 1]], dtype=np.int64),
            ),
            (
                np.asarray([[1.0, 0.7, 0.6, 0.5]], dtype=np.float32),
                np.asarray([[2, 0, 1, 3]], dtype=np.int64),
            ),
            (
                np.asarray([[1.0, 0.7, 0.6]], dtype=np.float32),
                np.asarray([[3, 0, 1]], dtype=np.int64),
            ),
            (
                np.asarray([[1.0, 0.7, 0.6, 0.5]], dtype=np.float32),
                np.asarray([[3, 0, 1, 2]], dtype=np.int64),
            ),
        ]
    )

    neighbors = search_topk_neighbors(
        index=index,  # type: ignore[arg-type]
        embeddings=embeddings,
        recipe_ids=recipe_ids,
        top_k=2,
    )

    source_10 = neighbors.loc[neighbors["source_recipe_id"] == 10].reset_index(drop=True)
    assert index.calls[:2] == [3, 4]
    assert source_10["neighbor_recipe_id"].tolist() == [30, 40]
