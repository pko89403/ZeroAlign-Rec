import json

import numpy as np
import pandas as pd

from sid_reco.taxonomy.step1 import (
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
