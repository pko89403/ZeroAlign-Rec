"""Prompt builders for recommendation modules."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass

from sid_reco.recommendation.types import RecommendationRequest

INTEREST_SKETCH_SYSTEM_PROMPT = (
    "You are an expert in taxonomy-guided recommendation intent modeling. "
    "Return only valid JSON that stays inside the provided taxonomy vocabulary."
)


@dataclass(frozen=True, slots=True)
class InterestSketchPromptBundle:
    """Prompt bundle for taxonomy-guided interest sketch generation."""

    taxonomy_dictionary: Mapping[str, list[str]]
    system_prompt: str
    user_prompt: str


def build_interest_sketch_prompt(
    request: RecommendationRequest,
    *,
    taxonomy_dictionary: Mapping[str, list[str]],
) -> InterestSketchPromptBundle:
    """Build a compact taxonomy-constrained prompt for Module 2.1."""
    payload = {
        "query": request.query,
        "liked_item_ids": list(request.liked_item_ids),
        "disliked_item_ids": list(request.disliked_item_ids),
        "hard_filters": {key: list(values) for key, values in request.hard_filters.items()},
        "top_k": request.top_k,
    }
    output_schema = {
        "summary": "short plain-text summary",
        "positive_facets": ["taxonomy_value"],
        "negative_facets": ["taxonomy_value"],
        "ambiguity_notes": ["short note"],
        "taxonomy_values": {"taxonomy_key": ["taxonomy_value"]},
    }
    user_prompt = "\n".join(
        [
            "Build a taxonomy-guided interest sketch for this recommendation request.",
            "Rules:",
            "1. taxonomy_values may use only keys and values from the provided taxonomy.",
            (
                "2. positive_facets and negative_facets may use only "
                "taxonomy values from the taxonomy."
            ),
            "3. Keep summary concise.",
            "4. Return JSON only.",
            f"Request JSON:\n{json.dumps(payload, ensure_ascii=False, sort_keys=True)}",
            (
                "Taxonomy JSON:\n"
                f"{json.dumps(taxonomy_dictionary, ensure_ascii=False, sort_keys=True)}"
            ),
            f"Output JSON shape:\n{json.dumps(output_schema, ensure_ascii=False, sort_keys=True)}",
        ]
    )
    return InterestSketchPromptBundle(
        taxonomy_dictionary=taxonomy_dictionary,
        system_prompt=INTEREST_SKETCH_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )
