"""Module 2.1 taxonomy-guided interest sketching."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from sid_reco.config import DEFAULT_LLM_MAX_TOKENS, Settings
from sid_reco.llm import MLXTextGenerator
from sid_reco.recommendation.prompting import build_interest_sketch_prompt
from sid_reco.recommendation.types import InterestSketch, RecommendationRequest
from sid_reco.taxonomy.dictionary import _to_snake_case
from sid_reco.taxonomy.item_projection import load_taxonomy_master_dictionary


class TextGenerator(Protocol):
    """Small protocol for recommendation prompt generation."""

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = DEFAULT_LLM_MAX_TOKENS,
        temperature: float = 0.0,
        top_p: float = 1.0,
        verbose: bool = False,
    ) -> str: ...


def generate_interest_sketch(
    request: RecommendationRequest,
    *,
    taxonomy_dictionary_path: Path,
    generator: TextGenerator,
    max_tokens: int = DEFAULT_LLM_MAX_TOKENS,
) -> InterestSketch:
    """Generate and validate a taxonomy-guided interest sketch."""
    taxonomy_dictionary = load_taxonomy_master_dictionary(taxonomy_dictionary_path)
    _validate_request_filters(request.hard_filters, taxonomy_dictionary=taxonomy_dictionary)
    bundle = build_interest_sketch_prompt(request, taxonomy_dictionary=taxonomy_dictionary)
    raw_response = generator.generate(
        bundle.user_prompt,
        system_prompt=bundle.system_prompt,
        max_tokens=max_tokens,
        temperature=0.0,
        top_p=1.0,
    )
    return parse_interest_sketch_response(
        raw_response,
        taxonomy_dictionary=taxonomy_dictionary,
        hard_filters=request.hard_filters,
    )


def generate_interest_sketch_with_mlx(
    request: RecommendationRequest,
    *,
    taxonomy_dictionary_path: Path,
    settings: Settings,
    max_tokens: int | None = None,
) -> InterestSketch:
    """Generate an interest sketch with the configured local MLX LLM."""
    generator = MLXTextGenerator.from_settings(settings)
    return generate_interest_sketch(
        request,
        taxonomy_dictionary_path=taxonomy_dictionary_path,
        generator=generator,
        max_tokens=max_tokens or settings.llm_max_tokens,
    )


def parse_interest_sketch_response(
    raw_response: str,
    *,
    taxonomy_dictionary: Mapping[str, list[str]],
    hard_filters: Mapping[str, tuple[str, ...]],
) -> InterestSketch:
    """Parse and validate a JSON interest sketch response."""
    parsed = _parse_json_object(raw_response)
    summary = _require_string(parsed, "summary")
    positive_facets = _normalize_flat_taxonomy_values(
        _require_string_list(parsed, "positive_facets"),
        taxonomy_dictionary=taxonomy_dictionary,
        field_name="positive_facets",
    )
    negative_facets = _normalize_flat_taxonomy_values(
        _require_string_list(parsed, "negative_facets"),
        taxonomy_dictionary=taxonomy_dictionary,
        field_name="negative_facets",
    )
    ambiguity_notes = tuple(sorted(_require_string_list(parsed, "ambiguity_notes")))
    taxonomy_values = _normalize_taxonomy_values(
        parsed.get("taxonomy_values"),
        taxonomy_dictionary=taxonomy_dictionary,
    )
    return InterestSketch(
        summary=summary,
        positive_facets=positive_facets,
        negative_facets=negative_facets,
        hard_filters=hard_filters,
        ambiguity_notes=ambiguity_notes,
        taxonomy_values=taxonomy_values,
    )


def _parse_json_object(raw_response: str) -> dict[str, object]:
    stripped = raw_response.strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Interest sketch response must contain a JSON object.")
    try:
        parsed = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError("Interest sketch response did not contain valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Interest sketch response must be a JSON object.")
    return parsed


def _require_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Interest sketch field '{key}' must be a non-empty string.")
    return value.strip()


def _require_string_list(payload: Mapping[str, object], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Interest sketch field '{key}' must be an array of strings.")
    return [item for item in value if item.strip()]


def _normalize_flat_taxonomy_values(
    raw_values: list[str],
    *,
    taxonomy_dictionary: Mapping[str, list[str]],
    field_name: str,
) -> tuple[str, ...]:
    allowed_values = {value for values in taxonomy_dictionary.values() for value in values}
    normalized = sorted(
        {
            normalized_value
            for raw_value in raw_values
            for normalized_value in (_to_snake_case(raw_value),)
            if normalized_value
        }
    )
    invalid = [value for value in normalized if value not in allowed_values]
    if invalid:
        raise ValueError(
            f"Interest sketch field '{field_name}' used values outside taxonomy: "
            f"{', '.join(invalid)}"
        )
    return tuple(normalized)


def _normalize_taxonomy_values(
    raw_value: object,
    *,
    taxonomy_dictionary: Mapping[str, list[str]],
) -> Mapping[str, tuple[str, ...]]:
    if not isinstance(raw_value, dict):
        raise ValueError("Interest sketch field 'taxonomy_values' must be an object.")

    normalized: dict[str, tuple[str, ...]] = {}
    for raw_key, raw_values in raw_value.items():
        key = _to_snake_case(str(raw_key))
        if key not in taxonomy_dictionary:
            raise ValueError(f"Interest sketch taxonomy key is not allowed: {key}")
        if not isinstance(raw_values, list) or not all(
            isinstance(item, str) for item in raw_values
        ):
            raise ValueError(
                f"Interest sketch taxonomy_values['{key}'] must be an array of strings."
            )
        values = sorted(
            {
                normalized_value
                for item in raw_values
                for normalized_value in (_to_snake_case(item),)
                if normalized_value
            }
        )
        invalid = [value for value in values if value not in taxonomy_dictionary[key]]
        if invalid:
            raise ValueError(
                f"Interest sketch taxonomy_values['{key}'] used values outside taxonomy: "
                f"{', '.join(invalid)}"
            )
        if values:
            normalized[key] = tuple(values)

    return {key: normalized[key] for key in taxonomy_dictionary if key in normalized}


def _validate_request_filters(
    hard_filters: Mapping[str, tuple[str, ...]],
    *,
    taxonomy_dictionary: Mapping[str, list[str]],
) -> None:
    for key, values in hard_filters.items():
        if key not in taxonomy_dictionary:
            raise ValueError(f"Unknown hard filter taxonomy key: {key}")
        invalid = [value for value in values if value not in taxonomy_dictionary[key]]
        if invalid:
            raise ValueError(
                f"Hard filter '{key}' used values outside taxonomy: {', '.join(invalid)}"
            )
