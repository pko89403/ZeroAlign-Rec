"""Offline recommendation statistics for Phase 1 recommendation support."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

RECOMMENDATION_STATS_REQUIRED_COLUMNS = ("user_id", "recipe_id")


@dataclass(frozen=True, slots=True)
class RecommendationStats:
    """Deterministic popularity and co-occurrence statistics."""

    interaction_count: int
    user_count: int
    item_count: int
    popularity: dict[int, int]
    cooccurrence: dict[int, dict[int, int]]


@dataclass(frozen=True, slots=True)
class RecommendationStatsWriteSummary:
    """Summary for persisted recommendation statistics."""

    output_path: Path
    interaction_count: int
    user_count: int
    item_count: int
    cooccurrence_pair_count: int


def build_recommendation_stats(interactions_path: Path) -> RecommendationStats:
    """Build deterministic popularity and item-item co-occurrence statistics."""
    interactions = _load_interactions(interactions_path)
    popularity = _build_popularity(interactions)
    cooccurrence = _build_cooccurrence(interactions)
    user_count = int(interactions["user_id"].nunique())
    item_ids = sorted({*popularity, *cooccurrence})
    return RecommendationStats(
        interaction_count=len(interactions),
        user_count=user_count,
        item_count=len(item_ids),
        popularity=popularity,
        cooccurrence=cooccurrence,
    )


def write_recommendation_stats(
    stats: RecommendationStats,
    *,
    out_path: Path,
) -> RecommendationStatsWriteSummary:
    """Persist recommendation statistics as deterministic JSON."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "cooccurrence": {
            str(recipe_id): {
                str(other_recipe_id): count
                for other_recipe_id, count in sorted(other_counts.items())
            }
            for recipe_id, other_counts in sorted(stats.cooccurrence.items())
        },
        "interaction_count": stats.interaction_count,
        "item_count": stats.item_count,
        "popularity": {
            str(recipe_id): count for recipe_id, count in sorted(stats.popularity.items())
        },
        "user_count": stats.user_count,
    }
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return RecommendationStatsWriteSummary(
        output_path=out_path,
        interaction_count=stats.interaction_count,
        user_count=stats.user_count,
        item_count=stats.item_count,
        cooccurrence_pair_count=_count_unique_pairs(stats.cooccurrence),
    )


def _load_interactions(interactions_path: Path) -> pd.DataFrame:
    if not interactions_path.exists():
        raise FileNotFoundError(f"Missing interactions file: {interactions_path}")

    interactions = pd.read_csv(interactions_path)
    missing = sorted(
        set(RECOMMENDATION_STATS_REQUIRED_COLUMNS).difference(interactions.columns),
    )
    if missing:
        raise ValueError(f"Missing required interactions columns: {', '.join(missing)}")

    normalized = interactions.loc[:, list(RECOMMENDATION_STATS_REQUIRED_COLUMNS)].copy()
    for column in RECOMMENDATION_STATS_REQUIRED_COLUMNS:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    if normalized.isna().any().any():
        raise ValueError("Interactions file contains non-numeric user_id or recipe_id values.")

    normalized["user_id"] = normalized["user_id"].astype(int)
    normalized["recipe_id"] = normalized["recipe_id"].astype(int)
    if normalized.empty:
        raise ValueError(f"Interactions file is empty after normalization: {interactions_path}")
    return normalized.sort_values(["user_id", "recipe_id"], kind="mergesort").reset_index(drop=True)


def _build_popularity(interactions: pd.DataFrame) -> dict[int, int]:
    popularity = (
        interactions.groupby("recipe_id")
        .size()
        .rename("count")
        .reset_index()
        .sort_values(["recipe_id"], kind="mergesort")
    )
    return {int(row.recipe_id): int(row.count) for row in popularity.itertuples(index=False)}


def _build_cooccurrence(interactions: pd.DataFrame) -> dict[int, dict[int, int]]:
    user_items = (
        interactions.loc[:, ["user_id", "recipe_id"]]
        .drop_duplicates()
        .sort_values(["user_id", "recipe_id"], kind="mergesort")
    )
    counts: dict[int, dict[int, int]] = {}
    for _, user_rows in user_items.groupby("user_id", sort=False):
        recipe_ids = [int(recipe_id) for recipe_id in user_rows["recipe_id"].tolist()]
        for index, recipe_id in enumerate(recipe_ids):
            for other_recipe_id in recipe_ids[index + 1 :]:
                counts.setdefault(recipe_id, {})
                counts.setdefault(other_recipe_id, {})
                counts[recipe_id][other_recipe_id] = counts[recipe_id].get(other_recipe_id, 0) + 1
                counts[other_recipe_id][recipe_id] = counts[other_recipe_id].get(recipe_id, 0) + 1
    return {
        recipe_id: {
            other_recipe_id: other_counts[other_recipe_id]
            for other_recipe_id in sorted(other_counts)
        }
        for recipe_id, other_counts in sorted(counts.items())
    }


def _count_unique_pairs(cooccurrence: dict[int, dict[int, int]]) -> int:
    return sum(
        1
        for recipe_id, others in cooccurrence.items()
        for other_recipe_id in others
        if recipe_id < other_recipe_id
    )
