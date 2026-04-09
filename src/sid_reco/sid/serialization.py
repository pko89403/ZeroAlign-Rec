"""Deterministic serialization for structured taxonomy items."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sid_reco.taxonomy.dictionary import _to_snake_case
from sid_reco.taxonomy.item_projection import UNKNOWN_TAXONOMY_VALUE


@dataclass(frozen=True, slots=True)
class SerializedSIDItem:
    """Structured taxonomy item plus deterministic serialized text."""

    recipe_id: int
    taxonomy: dict[str, list[str]]
    serialized_text: str


@dataclass(frozen=True, slots=True)
class SerializedSIDWriteSummary:
    """Summary for persisted serialized SID items."""

    item_count: int
    output_path: Path


def serialize_structured_items(
    structured_items_path: Path,
    *,
    feature_order: tuple[str, ...] = (),
) -> list[SerializedSIDItem]:
    """Load structured taxonomy items and serialize them deterministically."""
    items = load_structured_taxonomy_items(structured_items_path)
    serialized_items: list[SerializedSIDItem] = []
    for item in items:
        normalized_taxonomy = normalize_serializable_taxonomy(
            item["taxonomy"],
            feature_order=feature_order,
        )
        serialized_items.append(
            SerializedSIDItem(
                recipe_id=item["recipe_id"],
                taxonomy=normalized_taxonomy,
                serialized_text=_serialize_normalized_taxonomy(normalized_taxonomy),
            )
        )
    return serialized_items


def load_structured_taxonomy_items(structured_items_path: Path) -> list[dict[str, Any]]:
    """Load structured taxonomy JSONL records in stable recipe_id order."""
    if not structured_items_path.exists():
        raise FileNotFoundError(f"Missing structured taxonomy items file: {structured_items_path}")

    items: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(
        structured_items_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Structured taxonomy line {line_number} is not valid JSON.",
            ) from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"Structured taxonomy line {line_number} must be a JSON object.")
        if "recipe_id" not in parsed:
            raise ValueError(f"Structured taxonomy line {line_number} is missing recipe_id.")
        if "taxonomy" not in parsed:
            raise ValueError(f"Structured taxonomy line {line_number} is missing taxonomy.")

        recipe_id = parsed["recipe_id"]
        if not isinstance(recipe_id, int):
            raise ValueError(
                f"Structured taxonomy line {line_number} recipe_id must be an integer.",
            )
        taxonomy = parsed["taxonomy"]
        if not isinstance(taxonomy, dict):
            raise ValueError(f"Structured taxonomy line {line_number} taxonomy must be an object.")

        items.append(
            {
                "recipe_id": recipe_id,
                "taxonomy": taxonomy,
            }
        )

    items.sort(key=lambda item: item["recipe_id"])
    _validate_unique_recipe_ids(items)
    return items


def normalize_serializable_taxonomy(
    taxonomy: dict[str, Any],
    *,
    feature_order: tuple[str, ...] = (),
) -> dict[str, list[str]]:
    """Normalize a structured taxonomy into a deterministic serialization payload."""
    normalized: dict[str, list[str]] = {}
    for raw_key, raw_values in taxonomy.items():
        key = _to_snake_case(str(raw_key))
        if not key:
            continue
        if not isinstance(raw_values, list):
            raise ValueError("Structured taxonomy values must be arrays of strings.")

        values = sorted(
            {
                normalized_value
                for raw_value in raw_values
                for normalized_value in [_to_snake_case(str(raw_value))]
                if normalized_value and normalized_value != UNKNOWN_TAXONOMY_VALUE
            }
        )
        if values:
            normalized[key] = values

    ordered_keys = _ordered_feature_keys(normalized, feature_order=feature_order)
    return {key: normalized[key] for key in ordered_keys}


def serialize_taxonomy_text(
    taxonomy: dict[str, Any],
    *,
    feature_order: tuple[str, ...] = (),
) -> str:
    """Serialize taxonomy values into one flat deterministic text string."""
    normalized = normalize_serializable_taxonomy(
        taxonomy,
        feature_order=feature_order,
    )
    return _serialize_normalized_taxonomy(normalized)


def write_serialized_items(
    items: list[SerializedSIDItem],
    *,
    out_path: Path,
) -> SerializedSIDWriteSummary:
    """Persist serialized SID items as deterministic JSON Lines."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            {
                "recipe_id": item.recipe_id,
                "serialized_text": item.serialized_text,
                "taxonomy": item.taxonomy,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        for item in items
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return SerializedSIDWriteSummary(item_count=len(items), output_path=out_path)


def _serialize_normalized_taxonomy(taxonomy: dict[str, list[str]]) -> str:
    return ", ".join(f"{key}: {', '.join(values)}" for key, values in taxonomy.items())


def _validate_unique_recipe_ids(items: list[dict[str, Any]]) -> None:
    for previous_item, current_item in zip(items, items[1:], strict=False):
        if previous_item["recipe_id"] == current_item["recipe_id"]:
            raise ValueError(
                f"Duplicate recipe_id in structured taxonomy items: {current_item['recipe_id']}"
            )


def _ordered_feature_keys(
    taxonomy: dict[str, list[str]],
    *,
    feature_order: tuple[str, ...],
) -> list[str]:
    normalized_feature_order = tuple(_to_snake_case(feature) for feature in feature_order)
    seen: set[str] = set()
    ordered_keys: list[str] = []

    for key in normalized_feature_order:
        if key and key in taxonomy and key not in seen:
            ordered_keys.append(key)
            seen.add(key)

    for key in sorted(taxonomy):
        if key not in seen:
            ordered_keys.append(key)

    return ordered_keys
