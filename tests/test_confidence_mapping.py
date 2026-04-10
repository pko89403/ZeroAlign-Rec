import json
from pathlib import Path

from sid_reco.recommendation import (
    BootstrapRerankPass,
    BootstrapRerankResult,
    CandidateRationale,
    ParsedRerankResponse,
    SemanticCandidate,
    compute_bootstrap_confidence,
    ground_recommended_items,
    summarize_confidence,
)


def test_compute_bootstrap_confidence_aggregates_votes_across_permuted_passes() -> None:
    candidate_a = _candidate(recipe_id=101, sid_string="<0>", score=0.98, cuisine="italian")
    candidate_b = _candidate(recipe_id=102, sid_string="<1>", score=0.85, cuisine="american")
    candidate_c = _candidate(recipe_id=103, sid_string="<2>", score=0.50, cuisine="mexican")
    rerank_result = BootstrapRerankResult(
        example=_example_payload(),
        passes=(
            _pass(
                (candidate_a, candidate_b, candidate_c),
                ranked_indices=(1, 2),
                reasons={
                    1: "Best semantic fit. Strong dinner match.",
                    2: "Good backup. Weaker cuisine alignment.",
                },
            ),
            _pass(
                (candidate_b, candidate_a, candidate_c),
                ranked_indices=(2, 1),
                reasons={
                    2: "Best semantic fit. Strong dinner match.",
                    1: "Good backup. Weaker cuisine alignment.",
                },
            ),
            _pass(
                (candidate_c, candidate_a, candidate_b),
                ranked_indices=(2, 3),
                reasons={
                    2: "Best semantic fit. Strong dinner match.",
                    3: "Good backup. Weaker cuisine alignment.",
                },
            ),
        ),
    )

    confident_candidates = compute_bootstrap_confidence(rerank_result, selection_size=2)

    assert [item.candidate.recipe_id for item in confident_candidates] == [101, 102]
    assert confident_candidates[0].vote_count == 3
    assert confident_candidates[0].mscp == 1.0
    assert confident_candidates[0].average_rank == 1.0
    assert confident_candidates[0].confidence_band == "high"
    assert confident_candidates[1].average_rank == 2.0
    assert summarize_confidence(confident_candidates, total_passes=3).startswith(
        "Top candidate support: 3/3"
    )


def test_ground_recommended_items_uses_direct_mapping_and_catalog_metadata(
    tmp_path: Path,
) -> None:
    _write_grounding_sidecars(
        tmp_path,
        id_map_entries=(
            {"faiss_idx": 0, "recipe_id": 101, "sid_string": "<0>", "sid_path": [0]},
            {"faiss_idx": 1, "recipe_id": 102, "sid_string": "<1>", "sid_path": [1]},
        ),
        sid_to_items={"<0>": [101], "<1>": [102]},
    )
    catalog_path = _write_catalog(
        tmp_path,
        rows=(
            (101, "Tomato Pasta"),
            (102, "Cheeseburger"),
        ),
    )
    confident_candidates = (
        _confident_candidate(recipe_id=101, sid_string="<0>", rank_score=0.98, vote_count=3),
        _confident_candidate(recipe_id=102, sid_string="<1>", rank_score=0.85, vote_count=2),
    )

    grounded_items = ground_recommended_items(
        confident_candidates,
        sid_index_dir=tmp_path,
        catalog_path=catalog_path,
        top_k=2,
    )

    assert [item.recipe_id for item in grounded_items] == [101, 102]
    assert [item.title for item in grounded_items] == ["Tomato Pasta", "Cheeseburger"]
    assert all(item.mapping_mode == "direct" for item in grounded_items)


def test_ground_recommended_items_falls_back_to_sid_mapping(tmp_path: Path) -> None:
    _write_grounding_sidecars(
        tmp_path,
        id_map_entries=(),
        sid_to_items={"<sid-a>": [999]},
    )
    catalog_path = _write_catalog(tmp_path, rows=((999, "Recovered Item"),))
    confident_candidates = (
        _confident_candidate(
            recipe_id=101,
            sid_string="<sid-a>",
            rank_score=0.91,
            vote_count=2,
        ),
    )

    grounded_items = ground_recommended_items(
        confident_candidates,
        sid_index_dir=tmp_path,
        catalog_path=catalog_path,
        top_k=1,
    )

    assert grounded_items[0].recipe_id == 999
    assert grounded_items[0].title == "Recovered Item"
    assert grounded_items[0].mapping_mode == "sid_fallback"


def _candidate(
    *,
    recipe_id: int,
    sid_string: str,
    score: float,
    cuisine: str,
) -> SemanticCandidate:
    return SemanticCandidate(
        faiss_idx=recipe_id,
        recipe_id=recipe_id,
        sid_string=sid_string,
        score=score,
        serialized_text=f"course: dinner, cuisine: {cuisine}",
        taxonomy={"course": ("dinner",), "cuisine": (cuisine,)},
        popularity=3,
        cooccurrence_with_history=1,
    )


def _confident_candidate(
    *,
    recipe_id: int,
    sid_string: str,
    rank_score: float,
    vote_count: int,
):
    from sid_reco.recommendation.confidence import ConfidenceCandidate

    return ConfidenceCandidate(
        candidate=_candidate(
            recipe_id=recipe_id,
            sid_string=sid_string,
            score=rank_score,
            cuisine="italian",
        ),
        vote_count=vote_count,
        mscp=vote_count / 3,
        average_rank=1.0,
        rationale="Best semantic fit. Strong dinner match.",
        matched_preferences=("dinner", "italian"),
        cautions=(),
        supporting_passes=(1, 2, 3)[:vote_count],
        confidence_band="high" if vote_count == 3 else "medium",
    )


def _pass(
    presented_candidates: tuple[SemanticCandidate, ...],
    *,
    ranked_indices: tuple[int, ...],
    reasons: dict[int, str],
) -> BootstrapRerankPass:
    rationales = tuple(
        CandidateRationale(
            candidate_index=index,
            reason=reasons[index],
            matched_preferences=("dinner",),
            tradeoffs_or_caveats=(),
        )
        for index in ranked_indices
    )
    return BootstrapRerankPass(
        presented_candidates=presented_candidates,
        raw_response="{}",
        parsed_response=ParsedRerankResponse(
            ranked_candidate_indices=ranked_indices,
            rationales=rationales,
        ),
    )


def _example_payload():
    from sid_reco.recommendation.example_store import FewShotExample

    return FewShotExample(
        case_id="case-1",
        summary="italian dinner",
        taxonomy_values={"course": ("dinner",), "cuisine": ("italian",)},
        output_example={"ranked_candidate_indices": [1, 2]},
    )


def _write_grounding_sidecars(
    tmp_path: Path,
    *,
    id_map_entries: tuple[dict[str, object], ...],
    sid_to_items: dict[str, list[int]],
) -> None:
    (tmp_path / "id_map.jsonl").write_text(
        "\n".join(json.dumps(entry, sort_keys=True) for entry in id_map_entries) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "sid_to_items.json").write_text(
        json.dumps(sid_to_items, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_catalog(tmp_path: Path, *, rows: tuple[tuple[int, str], ...]) -> Path:
    catalog_path = tmp_path / "recipes.csv"
    tags_json = json.dumps(["tag"]).replace('"', '""')
    ingredients_json = json.dumps(["ingredient"]).replace('"', '""')
    catalog_lines = [
        "recipe_id,name,description,tags,ingredients",
        *[
            f'{recipe_id},"{name}","desc","{tags_json}","{ingredients_json}"'
            for recipe_id, name in rows
        ],
    ]
    catalog_path.write_text("\n".join(catalog_lines) + "\n", encoding="utf-8")
    return catalog_path
