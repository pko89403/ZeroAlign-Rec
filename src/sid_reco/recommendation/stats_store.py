"""Load and query offline recommendation statistics."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RecommendationStatsStore:
    """Lookup-friendly popularity and co-occurrence statistics."""

    popularity: dict[int, int]
    cooccurrence: dict[int, dict[int, int]]

    def popularity_for(self, recipe_id: int) -> int:
        return self.popularity.get(recipe_id, 0)

    def cooccurrence_with_history(
        self,
        recipe_id: int,
        liked_item_ids: tuple[int, ...],
    ) -> int:
        return sum(
            self.cooccurrence.get(recipe_id, {}).get(liked_item_id, 0)
            for liked_item_id in liked_item_ids
        )


def load_recommendation_stats_store(stats_path: Path) -> RecommendationStatsStore:
    """Load recommendation statistics persisted by compile-sid-index."""
    if not stats_path.exists():
        raise FileNotFoundError(f"Missing recommendation stats file: {stats_path}")
    try:
        payload = json.loads(stats_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Recommendation stats file is not valid JSON: {stats_path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Recommendation stats payload must be a JSON object.")
    return RecommendationStatsStore(
        popularity=_parse_nested_int_mapping(payload.get("popularity"), field_name="popularity"),
        cooccurrence=_parse_double_nested_int_mapping(
            payload.get("cooccurrence"),
            field_name="cooccurrence",
        ),
    )


def _parse_nested_int_mapping(raw_value: object, *, field_name: str) -> dict[int, int]:
    if not isinstance(raw_value, dict):
        raise ValueError(f"Recommendation stats field '{field_name}' must be an object.")
    normalized: dict[int, int] = {}
    for raw_key, raw_count in raw_value.items():
        if not isinstance(raw_count, int):
            raise ValueError(
                f"Recommendation stats field '{field_name}' must map recipe IDs to integers."
            )
        normalized[int(raw_key)] = raw_count
    return dict(sorted(normalized.items()))


def _parse_double_nested_int_mapping(
    raw_value: object,
    *,
    field_name: str,
) -> dict[int, dict[int, int]]:
    if not isinstance(raw_value, dict):
        raise ValueError(f"Recommendation stats field '{field_name}' must be an object.")
    normalized: dict[int, dict[int, int]] = {}
    for raw_key, raw_inner in raw_value.items():
        if not isinstance(raw_inner, dict):
            raise ValueError(
                f"Recommendation stats field '{field_name}' must map recipe IDs to objects."
            )
        normalized[int(raw_key)] = _parse_nested_int_mapping(
            raw_inner,
            field_name=f"{field_name}[{raw_key}]",
        )
    return dict(sorted(normalized.items()))
