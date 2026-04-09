"""Food.com dataset loading and downsampling helpers."""

from __future__ import annotations

import ast
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

RAW_RECIPES_FILENAME = "RAW_recipes.csv"
RAW_INTERACTIONS_FILENAME = "RAW_interactions.csv"
DEFAULT_CORE_K = 5
DEFAULT_POSITIVE_THRESHOLD = 4.0
RECIPES_COLUMNS = [
    "recipe_id",
    "name",
    "minutes",
    "tags",
    "nutrition",
    "n_steps",
    "steps",
    "description",
    "ingredients",
    "n_ingredients",
    "interaction_count",
    "avg_rating",
    "review_count",
]
INTERACTIONS_COLUMNS = ["user_id", "recipe_id", "date", "rating", "review"]
LIST_COLUMNS = ["tags", "nutrition", "steps", "ingredients"]


@dataclass(frozen=True, slots=True)
class DatasetSummary:
    """High-level summary for a processed dataset export."""

    recipes_rows: int
    interactions_rows: int
    train_rows: int
    valid_rows: int
    test_rows: int
    unique_users: int
    unique_recipes: int


def load_raw_recipes(raw_dir: Path) -> pd.DataFrame:
    """Load raw Food.com recipes CSV."""
    return pd.read_csv(_require_raw_file(raw_dir, RAW_RECIPES_FILENAME))


def load_raw_interactions(raw_dir: Path) -> pd.DataFrame:
    """Load raw Food.com interactions CSV."""
    return pd.read_csv(_require_raw_file(raw_dir, RAW_INTERACTIONS_FILENAME))


def normalize_recipes(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Food.com recipe rows to the project schema."""
    recipes = df.copy()
    recipes = recipes.rename(columns={"id": "recipe_id"})

    required_columns = {
        "recipe_id",
        "name",
        "minutes",
        "tags",
        "nutrition",
        "n_steps",
        "steps",
        "description",
        "ingredients",
        "n_ingredients",
    }
    _ensure_columns(recipes, required_columns)

    invalid_mask = pd.Series(False, index=recipes.index)
    for column in LIST_COLUMNS:
        parsed = recipes[column].apply(_parse_list_literal)
        invalid_mask = invalid_mask | parsed.isna()
        recipes[column] = parsed

    for column in ("recipe_id", "minutes", "n_steps", "n_ingredients"):
        recipes[column] = pd.to_numeric(recipes[column], errors="coerce")
        invalid_mask = invalid_mask | recipes[column].isna()

    recipes = recipes.loc[~invalid_mask].copy()
    recipes["recipe_id"] = recipes["recipe_id"].astype(int)
    recipes["minutes"] = recipes["minutes"].astype(int)
    recipes["n_steps"] = recipes["n_steps"].astype(int)
    recipes["n_ingredients"] = recipes["n_ingredients"].astype(int)
    recipes["description"] = recipes["description"].fillna("").astype(str)
    recipes["name"] = recipes["name"].fillna("").astype(str)
    recipes = recipes.drop_duplicates(subset=["recipe_id"]).reset_index(drop=True)
    return recipes


def normalize_interactions(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Food.com interaction rows to the project schema."""
    interactions = df.copy()
    required_columns = {"user_id", "recipe_id", "date", "rating", "review"}
    _ensure_columns(interactions, required_columns)

    for column in ("user_id", "recipe_id", "rating"):
        interactions[column] = pd.to_numeric(interactions[column], errors="coerce")

    interactions["date"] = pd.to_datetime(interactions["date"], errors="coerce")
    interactions["review"] = interactions["review"].fillna("").astype(str)

    valid_rating = interactions["rating"].between(0, 5, inclusive="both")
    valid_mask = (
        interactions["user_id"].notna()
        & interactions["recipe_id"].notna()
        & interactions["date"].notna()
        & valid_rating
    )
    interactions = interactions.loc[valid_mask].copy()
    interactions["user_id"] = interactions["user_id"].astype(int)
    interactions["recipe_id"] = interactions["recipe_id"].astype(int)
    interactions["rating"] = interactions["rating"].astype(float)
    interactions["source_rating"] = interactions["rating"]
    interactions["date"] = interactions["date"].dt.strftime("%Y-%m-%d")
    interactions = interactions.drop_duplicates().reset_index(drop=True)
    return interactions[INTERACTIONS_COLUMNS + ["source_rating"]]


def filter_positive_interactions(
    interactions: pd.DataFrame,
    positive_threshold: float,
) -> pd.DataFrame:
    """Keep only positive interactions and binarize the rating column."""
    positive = interactions.loc[interactions["source_rating"] >= positive_threshold].copy()
    positive["rating"] = 1.0
    return positive.reset_index(drop=True)


def select_top_recipes(
    recipes: pd.DataFrame,
    interactions: pd.DataFrame,
    top_n: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep only the most interacted recipes and their connected interactions."""
    counts = (
        interactions.groupby("recipe_id")
        .size()
        .rename("interaction_count")
        .reset_index()
        .sort_values(["interaction_count", "recipe_id"], ascending=[False, True], kind="mergesort")
    )
    top_recipe_ids = counts.head(top_n)["recipe_id"]
    selected_interactions = interactions.loc[interactions["recipe_id"].isin(top_recipe_ids)].copy()
    selected_recipes = recipes.loc[recipes["recipe_id"].isin(top_recipe_ids)].copy()
    selected_interactions = selected_interactions.loc[
        selected_interactions["recipe_id"].isin(selected_recipes["recipe_id"])
    ].reset_index(drop=True)
    selected_recipes = selected_recipes.reset_index(drop=True)
    return selected_recipes, selected_interactions


def apply_k_core_filter(
    interactions: pd.DataFrame,
    *,
    min_user_interactions: int,
    min_item_interactions: int,
) -> pd.DataFrame:
    """Iteratively apply user/item k-core filtering."""
    filtered = interactions.copy()

    while True:
        previous_len = len(filtered)
        user_counts = filtered.groupby("user_id").size()
        valid_users = user_counts.loc[user_counts >= min_user_interactions].index
        filtered = filtered.loc[filtered["user_id"].isin(valid_users)].copy()

        item_counts = filtered.groupby("recipe_id").size()
        valid_items = item_counts.loc[item_counts >= min_item_interactions].index
        filtered = filtered.loc[filtered["recipe_id"].isin(valid_items)].copy()

        if len(filtered) == previous_len:
            break

    return filtered.reset_index(drop=True)


def build_recipe_stats(recipes: pd.DataFrame, interactions: pd.DataFrame) -> pd.DataFrame:
    """Add interaction summary statistics to the recipe table."""
    rating_column = "source_rating" if "source_rating" in interactions.columns else "rating"
    stats = (
        interactions.assign(has_review=interactions["review"].str.strip().ne(""))
        .groupby("recipe_id", as_index=False)
        .agg(
            interaction_count=("recipe_id", "size"),
            avg_rating=(rating_column, "mean"),
            review_count=("has_review", "sum"),
        )
    )
    enriched = recipes.merge(stats, on="recipe_id", how="left")
    enriched["interaction_count"] = (
        pd.to_numeric(enriched["interaction_count"], errors="coerce").fillna(0).astype(int)
    )
    enriched["avg_rating"] = pd.to_numeric(enriched["avg_rating"], errors="coerce").fillna(0.0)
    enriched["review_count"] = (
        pd.to_numeric(enriched["review_count"], errors="coerce").fillna(0).astype(int)
    )
    return enriched


def build_temporal_splits(
    interactions: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Split interactions into train/valid/test using user-local temporal 8:1:1 order."""
    ordered = interactions.sort_values(
        ["user_id", "date", "recipe_id"],
        ascending=[True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    splits: dict[str, pd.DataFrame] = {}
    split_frames: dict[str, list[pd.DataFrame]] = {"train": [], "valid": [], "test": []}
    for _, user_rows in ordered.groupby("user_id", sort=False):
        train_end, valid_end = _split_boundaries(len(user_rows))
        split_frames["train"].append(user_rows.iloc[:train_end])
        split_frames["valid"].append(user_rows.iloc[train_end:valid_end])
        split_frames["test"].append(user_rows.iloc[valid_end:])

    for split_name, frames in split_frames.items():
        if frames:
            splits[split_name] = pd.concat(frames, ignore_index=True).loc[:, INTERACTIONS_COLUMNS]
        else:
            splits[split_name] = pd.DataFrame(columns=INTERACTIONS_COLUMNS)
    return splits


def write_processed_dataset(
    out_dir: Path,
    recipes: pd.DataFrame,
    interactions: pd.DataFrame,
    splits: dict[str, pd.DataFrame],
    manifest: dict[str, Any],
) -> DatasetSummary:
    """Write processed CSV outputs and manifest to disk."""
    out_dir.mkdir(parents=True, exist_ok=True)
    splits_dir = out_dir / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)

    recipes_output = _serialize_recipe_lists(recipes)
    recipes_output = recipes_output.loc[:, RECIPES_COLUMNS]
    interactions_output = interactions.loc[:, INTERACTIONS_COLUMNS]

    recipes_output.to_csv(out_dir / "recipes.csv", index=False, encoding="utf-8")
    interactions_output.to_csv(out_dir / "interactions.csv", index=False, encoding="utf-8")
    for split_name, split_df in splits.items():
        split_df.loc[:, INTERACTIONS_COLUMNS].to_csv(
            splits_dir / f"{split_name}.csv",
            index=False,
            encoding="utf-8",
        )

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return DatasetSummary(
        recipes_rows=len(recipes_output),
        interactions_rows=len(interactions_output),
        train_rows=len(splits["train"]),
        valid_rows=len(splits["valid"]),
        test_rows=len(splits["test"]),
        unique_users=int(interactions_output["user_id"].nunique()),
        unique_recipes=int(recipes_output["recipe_id"].nunique()),
    )


def build_manifest(
    *,
    top_recipes: int,
    core_k: int,
    positive_threshold: float,
    recipes: pd.DataFrame,
    interactions: pd.DataFrame,
    splits: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    """Build metadata for a processed Food.com dataset export."""
    return {
        "source": {
            "dataset": "Food.com Recipes & Interactions",
            "files": [RAW_RECIPES_FILENAME, RAW_INTERACTIONS_FILENAME],
        },
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "top_recipes": top_recipes,
        "positive_threshold": positive_threshold,
        "core_filter": {
            "min_user_interactions": core_k,
            "min_item_interactions": core_k,
        },
        "split_strategy": "temporal_8_1_1",
        "recipes_rows": len(recipes),
        "interactions_rows": len(interactions),
        "train_rows": len(splits["train"]),
        "valid_rows": len(splits["valid"]),
        "test_rows": len(splits["test"]),
        "unique_users": int(interactions["user_id"].nunique()),
        "unique_recipes": int(recipes["recipe_id"].nunique()),
    }


def prepare_foodcom_dataset(
    *,
    raw_dir: Path,
    out_dir: Path,
    top_recipes: int,
    core_k: int = DEFAULT_CORE_K,
    positive_threshold: float = DEFAULT_POSITIVE_THRESHOLD,
) -> DatasetSummary:
    """Run the full Food.com downsampling pipeline."""
    raw_recipes = load_raw_recipes(raw_dir)
    raw_interactions = load_raw_interactions(raw_dir)
    recipes = normalize_recipes(raw_recipes)
    interactions = normalize_interactions(raw_interactions)
    interactions = filter_positive_interactions(interactions, positive_threshold)
    recipes, interactions = select_top_recipes(recipes, interactions, top_recipes)
    interactions = apply_k_core_filter(
        interactions,
        min_user_interactions=core_k,
        min_item_interactions=core_k,
    )
    recipes = recipes.loc[recipes["recipe_id"].isin(interactions["recipe_id"])].reset_index(
        drop=True,
    )
    recipes = build_recipe_stats(recipes, interactions)
    splits = build_temporal_splits(interactions)
    manifest = build_manifest(
        top_recipes=top_recipes,
        core_k=core_k,
        positive_threshold=positive_threshold,
        recipes=recipes,
        interactions=interactions,
        splits=splits,
    )
    return write_processed_dataset(
        out_dir=out_dir,
        recipes=recipes,
        interactions=interactions,
        splits=splits,
        manifest=manifest,
    )


def _require_raw_file(raw_dir: Path, filename: str) -> Path:
    path = raw_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing required Food.com raw file: {path}")
    return path


def _ensure_columns(df: pd.DataFrame, required_columns: set[str]) -> None:
    missing = sorted(required_columns.difference(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def _parse_list_literal(value: Any) -> list[Any] | None:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if not isinstance(value, str):
        return None
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return None
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, tuple):
        return list(parsed)
    return None


def _serialize_recipe_lists(recipes: pd.DataFrame) -> pd.DataFrame:
    output = recipes.copy()
    for column in LIST_COLUMNS:
        output[column] = output[column].apply(lambda value: json.dumps(value, ensure_ascii=False))
    return output


def _split_boundaries(num_rows: int) -> tuple[int, int]:
    if num_rows < 3:
        return num_rows, num_rows

    train_end = max(1, math.floor(num_rows * 0.8))
    valid_end = max(train_end + 1, math.floor(num_rows * 0.9))

    if valid_end >= num_rows:
        valid_end = num_rows - 1
    if train_end >= valid_end:
        train_end = max(1, valid_end - 1)

    return train_end, valid_end
