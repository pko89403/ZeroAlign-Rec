"""Shared recommendation contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from sid_reco.taxonomy.dictionary import _to_snake_case


@dataclass(frozen=True, slots=True)
class RecommendationRequest:
    """Normalized request contract for recommendation entrypoints."""

    query: str | None
    liked_item_ids: tuple[int, ...]
    disliked_item_ids: tuple[int, ...]
    hard_filters: Mapping[str, tuple[str, ...]]
    top_k: int


@dataclass(frozen=True, slots=True)
class InterestSketch:
    """Taxonomy-constrained representation of user intent."""

    summary: str
    positive_facets: tuple[str, ...]
    negative_facets: tuple[str, ...]
    hard_filters: Mapping[str, tuple[str, ...]]
    ambiguity_notes: tuple[str, ...]
    taxonomy_values: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class RecommendedItem:
    """Final recommendation payload for one catalog item."""

    recipe_id: int
    sid_string: str
    rank: int
    title: str
    rationale: str
    matched_preferences: tuple[str, ...]
    cautions: tuple[str, ...]
    confidence_band: str
    mscp: float | None
    mapping_mode: str
    evidence_refs: tuple[str, ...]
    bootstrap_support: int
    popularity: float | None
    cooccurrence_with_history: int | None


@dataclass(frozen=True, slots=True)
class RecommendationResponse:
    """Public response contract for recommendation entrypoints."""

    sketch: InterestSketch
    items: tuple[RecommendedItem, ...]
    rerank_summary: str
    confidence_summary: str
    selected_candidate_indices: tuple[int, ...]


def normalize_recommendation_request(
    *,
    query: str | None = None,
    liked_item_ids: tuple[int, ...] | list[int] = (),
    disliked_item_ids: tuple[int, ...] | list[int] = (),
    hard_filters: Mapping[str, tuple[str, ...] | list[str] | str] | None = None,
    top_k: int = 10,
) -> RecommendationRequest:
    """Normalize runtime request fields into a stable typed contract."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    normalized_query = query.strip() if query is not None else ""
    normalized_liked = _normalize_item_ids(liked_item_ids)
    normalized_disliked = _normalize_item_ids(disliked_item_ids)
    overlap = set(normalized_liked).intersection(normalized_disliked)
    if overlap:
        raise ValueError("liked_item_ids and disliked_item_ids must not overlap.")

    normalized_filters = _normalize_filter_mapping(hard_filters or {})
    if (
        not normalized_query
        and not normalized_liked
        and not normalized_disliked
        and not normalized_filters
    ):
        raise ValueError(
            "RecommendationRequest requires at least one query, preference, or filter."
        )

    return RecommendationRequest(
        query=normalized_query or None,
        liked_item_ids=normalized_liked,
        disliked_item_ids=normalized_disliked,
        hard_filters=normalized_filters,
        top_k=top_k,
    )


def _normalize_item_ids(raw_ids: tuple[int, ...] | list[int]) -> tuple[int, ...]:
    normalized = sorted({int(item_id) for item_id in raw_ids})
    return tuple(normalized)


def _normalize_filter_mapping(
    raw_filters: Mapping[str, tuple[str, ...] | list[str] | str],
) -> Mapping[str, tuple[str, ...]]:
    normalized: dict[str, tuple[str, ...]] = {}
    for raw_key, raw_values in raw_filters.items():
        key = _to_snake_case(str(raw_key))
        if not key:
            continue
        values: tuple[str, ...]
        if isinstance(raw_values, str):
            values = (raw_values,)
        else:
            values = tuple(raw_values)
        normalized_values = sorted(
            {value for raw_value in values for value in (_to_snake_case(str(raw_value)),) if value}
        )
        if normalized_values:
            normalized[key] = tuple(normalized_values)
    return normalized
