"""Module 2.4 SID-aware fallback mapping helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GroundingDecision:
    """Resolved canonical identity for a recommendation candidate."""

    recipe_id: int
    sid_string: str
    mapping_mode: str


def resolve_grounding(
    *,
    recipe_id: int,
    sid_string: str,
    id_map_by_recipe: Mapping[int, str],
    sid_to_items: Mapping[str, tuple[int, ...]],
) -> GroundingDecision:
    """Resolve a candidate through direct id_map lookup, then SID fallback."""
    mapped_sid = id_map_by_recipe.get(recipe_id)
    if mapped_sid == sid_string:
        return GroundingDecision(
            recipe_id=recipe_id,
            sid_string=sid_string,
            mapping_mode="direct",
        )

    sid_items = sid_to_items.get(sid_string, ())
    if recipe_id in sid_items:
        return GroundingDecision(
            recipe_id=recipe_id,
            sid_string=sid_string,
            mapping_mode="sid_fallback",
        )
    if sid_items:
        return GroundingDecision(
            recipe_id=sid_items[0],
            sid_string=sid_string,
            mapping_mode="sid_fallback",
        )
    raise ValueError("Could not ground candidate through either id_map.jsonl or sid_to_items.json.")
