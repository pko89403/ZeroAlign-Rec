import json
from pathlib import Path

import pytest

from sid_reco.recommendation import (
    build_interest_sketch_prompt,
    generate_interest_sketch,
    normalize_recommendation_request,
)
from sid_reco.recommendation.types import RecommendationRequest


class _FakeGenerator:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 256,
        temperature: float = 0.0,
        top_p: float = 1.0,
        verbose: bool = False,
    ) -> str:
        self.calls.append(
            {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "verbose": verbose,
            }
        )
        return self.response


def test_normalize_recommendation_request_normalizes_and_dedupes_values() -> None:
    request = normalize_recommendation_request(
        query="  cozy dinner  ",
        liked_item_ids=[5, 2, 5],
        disliked_item_ids=[9, 7, 9],
        hard_filters={"Dietary Style": ["Vegetarian", "vegetarian"], "Course": "Dinner"},
        top_k=5,
    )

    assert request == RecommendationRequest(
        query="cozy dinner",
        liked_item_ids=(2, 5),
        disliked_item_ids=(7, 9),
        hard_filters={
            "dietary_style": ("vegetarian",),
            "course": ("dinner",),
        },
        top_k=5,
    )


def test_generate_interest_sketch_enforces_taxonomy_output(tmp_path: Path) -> None:
    taxonomy_path = _write_taxonomy_dictionary(tmp_path)
    generator = _FakeGenerator(
        json.dumps(
            {
                "summary": "cozy vegetarian dinner",
                "positive_facets": ["cozy_dinner", "vegetarian"],
                "negative_facets": ["spicy"],
                "ambiguity_notes": ["weekday not specified"],
                "taxonomy_values": {
                    "taste_mood": ["cozy_dinner"],
                    "dietary_style": ["vegetarian"],
                    "spice_level": ["spicy"],
                },
            }
        )
    )
    request = normalize_recommendation_request(
        query="Need a cozy vegetarian dinner",
        hard_filters={"dietary_style": ["vegetarian"]},
    )

    sketch = generate_interest_sketch(
        request,
        taxonomy_dictionary_path=taxonomy_path,
        generator=generator,
    )

    assert sketch.summary == "cozy vegetarian dinner"
    assert sketch.positive_facets == ("cozy_dinner", "vegetarian")
    assert sketch.negative_facets == ("spicy",)
    assert sketch.hard_filters == {"dietary_style": ("vegetarian",)}
    assert sketch.taxonomy_values == {
        "dietary_style": ("vegetarian",),
        "spice_level": ("spicy",),
        "taste_mood": ("cozy_dinner",),
    }
    assert generator.calls[0]["system_prompt"] is not None


def test_generate_interest_sketch_rejects_values_outside_taxonomy(tmp_path: Path) -> None:
    taxonomy_path = _write_taxonomy_dictionary(tmp_path)
    generator = _FakeGenerator(
        json.dumps(
            {
                "summary": "bad sketch",
                "positive_facets": ["cozy_dinner", "hallucinated_value"],
                "negative_facets": [],
                "ambiguity_notes": [],
                "taxonomy_values": {"taste_mood": ["cozy_dinner"]},
            }
        )
    )
    request = normalize_recommendation_request(query="Need dinner")

    with pytest.raises(ValueError, match="outside taxonomy"):
        generate_interest_sketch(
            request,
            taxonomy_dictionary_path=taxonomy_path,
            generator=generator,
        )


def test_build_interest_sketch_prompt_includes_taxonomy_and_request() -> None:
    request = normalize_recommendation_request(
        query="Need dinner",
        hard_filters={"course": ["dinner"]},
    )
    bundle = build_interest_sketch_prompt(
        request,
        taxonomy_dictionary={"course": ["dinner"], "taste_mood": ["cozy_dinner"]},
    )

    assert "Return only valid JSON" in bundle.system_prompt
    assert '"course": ["dinner"]' in bundle.user_prompt
    assert '"query": "Need dinner"' in bundle.user_prompt


def _write_taxonomy_dictionary(tmp_path: Path) -> Path:
    taxonomy_path = tmp_path / "food_taxonomy_dictionary.json"
    taxonomy_path.write_text(
        json.dumps(
            {
                "dietary_style": ["vegetarian", "vegan"],
                "spice_level": ["mild", "spicy"],
                "taste_mood": ["bright", "cozy_dinner"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return taxonomy_path
