"""Module 2.4 CPU grounding and final recommendation payload assembly."""

from __future__ import annotations

import json
from pathlib import Path

from sid_reco.recommendation.confidence import ConfidenceCandidate
from sid_reco.recommendation.elastic_mapping import resolve_grounding
from sid_reco.recommendation.types import RecommendedItem
from sid_reco.taxonomy.dictionary import load_taxonomy_items


def ground_recommended_items(
    confident_candidates: tuple[ConfidenceCandidate, ...],
    *,
    sid_index_dir: Path,
    catalog_path: Path,
    top_k: int = 3,
) -> tuple[RecommendedItem, ...]:
    """Ground the highest-confidence candidates into canonical delivery items."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    id_map_by_recipe = _load_id_map_by_recipe(sid_index_dir / "id_map.jsonl")
    sid_to_items = _load_sid_to_items(sid_index_dir / "sid_to_items.json")
    catalog_by_id = {int(item["recipe_id"]): item for item in load_taxonomy_items(catalog_path)}

    grounded_items: list[RecommendedItem] = []
    for rank, confident_candidate in enumerate(confident_candidates[:top_k], start=1):
        decision = resolve_grounding(
            recipe_id=confident_candidate.candidate.recipe_id,
            sid_string=confident_candidate.candidate.sid_string,
            id_map_by_recipe=id_map_by_recipe,
            sid_to_items=sid_to_items,
        )
        catalog_item = catalog_by_id.get(decision.recipe_id, {})
        title = str(catalog_item.get("name", "")).strip()
        if not title:
            title = confident_candidate.candidate.serialized_text
        grounded_items.append(
            RecommendedItem(
                recipe_id=decision.recipe_id,
                sid_string=decision.sid_string,
                rank=rank,
                title=title,
                rationale=confident_candidate.rationale,
                matched_preferences=confident_candidate.matched_preferences,
                cautions=confident_candidate.cautions,
                confidence_band=confident_candidate.confidence_band,
                mscp=confident_candidate.mscp,
                mapping_mode=decision.mapping_mode,
                evidence_refs=(
                    "id_map.jsonl",
                    "sid_to_items.json",
                    (
                        "supporting_passes="
                        + ",".join(str(value) for value in confident_candidate.supporting_passes)
                    ),
                ),
                bootstrap_support=confident_candidate.vote_count,
                popularity=float(confident_candidate.candidate.popularity),
                cooccurrence_with_history=confident_candidate.candidate.cooccurrence_with_history,
            )
        )
    return tuple(grounded_items)


def _load_id_map_by_recipe(id_map_path: Path) -> dict[int, str]:
    if not id_map_path.exists():
        raise FileNotFoundError(f"Missing SID id map file: {id_map_path}")

    id_map_by_recipe: dict[int, str] = {}
    for line_number, raw_line in enumerate(
        id_map_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"SID id map line {line_number} is not valid JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"SID id map line {line_number} must be a JSON object.")
        recipe_id = payload.get("recipe_id")
        sid_string = payload.get("sid_string")
        if not isinstance(recipe_id, int) or not isinstance(sid_string, str):
            raise ValueError(f"SID id map line {line_number} has invalid required fields.")
        id_map_by_recipe[recipe_id] = sid_string
    return id_map_by_recipe


def _load_sid_to_items(sid_to_items_path: Path) -> dict[str, tuple[int, ...]]:
    if not sid_to_items_path.exists():
        raise FileNotFoundError(f"Missing SID-to-items file: {sid_to_items_path}")
    try:
        payload = json.loads(sid_to_items_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("sid_to_items.json is not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("sid_to_items.json must be a JSON object.")

    normalized: dict[str, tuple[int, ...]] = {}
    for sid_string, recipe_ids in payload.items():
        if not isinstance(sid_string, str) or not isinstance(recipe_ids, list):
            raise ValueError("sid_to_items.json has invalid mapping entries.")
        if not all(isinstance(recipe_id, int) for recipe_id in recipe_ids):
            raise ValueError("sid_to_items.json recipe_id lists must contain integers only.")
        normalized[sid_string] = tuple(sorted(recipe_ids))
    return normalized
