import json
from pathlib import Path

import numpy as np

from sid_reco.recommendation import (
    InterestSketch,
    normalize_recommendation_request,
    search_semantic_candidates,
)
from sid_reco.sid.compiler import CompiledSIDItem, CompiledSIDItems, ResidualKMeansLevel
from sid_reco.sid.embed_backend import EmbeddedSIDItems
from sid_reco.sid.indexing import write_sid_index_outputs
from sid_reco.sid.serialization import SerializedSIDItem, write_serialized_items
from sid_reco.sid.stats import build_recommendation_stats, write_recommendation_stats


class _FakeEncoder:
    def encode(self, texts: list[str]) -> list[list[float]]:
        assert texts == ["course: dinner, cuisine: italian"]
        return [[1.0, 0.0, 0.0]]


def test_search_semantic_candidates_returns_enriched_survivors(tmp_path: Path) -> None:
    sid_index_dir, taxonomy_path, stats_path = _write_semantic_search_bundle(tmp_path)
    request = normalize_recommendation_request(
        query="Need Italian dinner",
        liked_item_ids=[101],
        hard_filters={"course": ["dinner"]},
    )
    sketch = InterestSketch(
        summary="italian dinner",
        positive_facets=("italian", "dinner"),
        negative_facets=(),
        hard_filters=request.hard_filters,
        ambiguity_notes=(),
        taxonomy_values={"course": ("dinner",), "cuisine": ("italian",)},
    )

    result = search_semantic_candidates(
        request,
        sketch,
        sid_index_dir=sid_index_dir,
        taxonomy_dictionary_path=taxonomy_path,
        stats_path=stats_path,
        encoder=_FakeEncoder(),
        retrieval_k=3,
        survivor_k=2,
    )

    assert result.query_text == "course: dinner, cuisine: italian"
    assert [candidate.recipe_id for candidate in result.candidates] == [101, 103]
    assert result.candidates[0].popularity == 2
    assert result.candidates[0].cooccurrence_with_history == 0
    assert result.candidates[1].cooccurrence_with_history == 1
    assert result.survivor_count == 2
    assert result.retrieved_count == 3
    assert result.low_coverage is False


def test_search_semantic_candidates_filters_disallowed_items(tmp_path: Path) -> None:
    sid_index_dir, taxonomy_path, stats_path = _write_semantic_search_bundle(tmp_path)
    request = normalize_recommendation_request(
        query="Need dinner only",
        hard_filters={"course": ["dinner"], "dietary_style": ["vegetarian"]},
    )
    sketch = InterestSketch(
        summary="dinner",
        positive_facets=("dinner",),
        negative_facets=(),
        hard_filters=request.hard_filters,
        ambiguity_notes=(),
        taxonomy_values={"course": ("dinner",), "cuisine": ("italian",)},
    )

    result = search_semantic_candidates(
        request,
        sketch,
        sid_index_dir=sid_index_dir,
        taxonomy_dictionary_path=taxonomy_path,
        stats_path=stats_path,
        encoder=_FakeEncoder(),
        retrieval_k=3,
        survivor_k=2,
    )

    assert [candidate.recipe_id for candidate in result.candidates] == [103]
    assert [candidate.recipe_id for candidate in result.dropped_candidates] == [101, 102]
    assert result.low_coverage is True


def _write_semantic_search_bundle(tmp_path: Path) -> tuple[Path, Path, Path]:
    sid_index_dir = tmp_path / "sid_index"
    taxonomy_path = tmp_path / "food_taxonomy_dictionary.json"
    interactions_path = tmp_path / "interactions.csv"

    items = [
        SerializedSIDItem(
            recipe_id=101,
            taxonomy={"course": ["dinner"], "cuisine": ["italian"]},
            serialized_text="course: dinner, cuisine: italian",
        ),
        SerializedSIDItem(
            recipe_id=102,
            taxonomy={"course": ["lunch"], "cuisine": ["american"]},
            serialized_text="course: lunch, cuisine: american",
        ),
        SerializedSIDItem(
            recipe_id=103,
            taxonomy={
                "course": ["dinner"],
                "cuisine": ["italian"],
                "dietary_style": ["vegetarian"],
            },
            serialized_text="course: dinner, cuisine: italian, dietary_style: vegetarian",
        ),
    ]
    write_serialized_items(items, out_path=sid_index_dir / "serialized_items.jsonl")
    embedded = EmbeddedSIDItems(
        items=items,
        matrix=np.asarray(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.8, 0.2, 0.0],
            ],
            dtype=np.float32,
        ),
        embedding_dim=3,
        model_id="test-embed-model",
    )
    compiled = CompiledSIDItems(
        items=[
            CompiledSIDItem(recipe_id=101, sid_path=(0,), sid_string="<0>"),
            CompiledSIDItem(recipe_id=102, sid_path=(1,), sid_string="<1>"),
            CompiledSIDItem(recipe_id=103, sid_path=(0,), sid_string="<0>"),
        ],
        branching_factor=2,
        depth=1,
        embedding_dim=3,
        levels=(
            ResidualKMeansLevel(
                level=1,
                cluster_count=2,
                centroids=np.asarray([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32),
                cluster_sizes=(2, 1),
                iteration_count=1,
                inertia=0.0,
            ),
        ),
    )
    write_sid_index_outputs(embedded=embedded, compiled=compiled, out_dir=sid_index_dir)

    taxonomy_path.write_text(
        json.dumps(
            {
                "course": ["dinner", "lunch"],
                "cuisine": ["american", "italian"],
                "dietary_style": ["vegetarian"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    interactions_path.write_text(
        "\n".join(
            [
                "user_id,recipe_id,date,rating,review",
                "1,101,2024-01-01,1.0,good",
                "1,102,2024-01-02,1.0,good",
                "2,101,2024-01-03,1.0,good",
                "2,103,2024-01-04,1.0,good",
                "3,102,2024-01-05,1.0,good",
                "3,103,2024-01-06,1.0,good",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    stats = build_recommendation_stats(interactions_path)
    stats_path = sid_index_dir / "recommendation_stats.json"
    write_recommendation_stats(stats, out_path=stats_path)
    return sid_index_dir, taxonomy_path, stats_path
