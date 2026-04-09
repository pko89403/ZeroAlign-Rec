import json
from pathlib import Path

import pandas as pd

from sid_reco.taxonomy.dictionary import (
    DEFAULT_MAX_PAYLOAD_CHARS,
    DEFAULT_MAX_PROMPT_ITEMS,
    EVENLY_SPACED_SAMPLING_STRATEGY,
    FULL_CATALOG_SAMPLING_STRATEGY,
    _parse_taxonomy_json,
    build_bounded_taxonomy_payload,
    build_taxonomy_dictionary_prompt,
    generate_taxonomy_dictionary,
    load_taxonomy_items,
    normalize_taxonomy_dictionary,
)


class _QueuedGenerator:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
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
        return self.responses.pop(0)


def test_load_taxonomy_items_parses_required_metadata_fields(tmp_path: Path) -> None:
    recipes_path = tmp_path / "recipes.csv"
    pd.DataFrame(
        [
            {
                "recipe_id": 101,
                "name": "Tomato Soup",
                "description": "Warm tomato soup.",
                "tags": json.dumps(["soup", "easy"]),
                "ingredients": json.dumps(["tomato", "salt"]),
                "minutes": 20,
            }
        ]
    ).to_csv(recipes_path, index=False)

    items = load_taxonomy_items(recipes_path)

    assert items == [
        {
            "recipe_id": 101,
            "name": "Tomato Soup",
            "description": "Warm tomato soup.",
            "tags": ["soup", "easy"],
            "ingredients": ["tomato", "salt"],
        }
    ]


def test_build_prompt_includes_few_shot_examples_and_payload() -> None:
    payload = build_bounded_taxonomy_payload(
        [
            {
                "recipe_id": 1,
                "name": "Tomato Soup",
                "description": "Warm tomato soup.",
                "tags": ["soup"],
                "ingredients": ["tomato"],
            }
        ],
        max_prompt_items=DEFAULT_MAX_PROMPT_ITEMS,
    )

    bundle = build_taxonomy_dictionary_prompt(payload)

    assert "You are an expert in food recommendations." in bundle.user_prompt
    assert "Example 1" in bundle.user_prompt
    assert "Example 2" in bundle.user_prompt
    assert payload.dataset_payload in bundle.user_prompt
    assert bundle.items_count == 1
    assert bundle.sampled_items_count == 1
    assert bundle.sampling_strategy == FULL_CATALOG_SAMPLING_STRATEGY
    assert (
        bundle.system_prompt
        == "You are an expert in food recommendations and domain taxonomy design. "
        "Return only valid JSON."
    )


def test_build_bounded_taxonomy_payload_samples_large_catalog_deterministically() -> None:
    items = [
        {
            "recipe_id": index,
            "name": f"Recipe {index}",
            "description": "",
            "tags": [],
            "ingredients": [],
        }
        for index in range(1500)
    ]

    payload = build_bounded_taxonomy_payload(items)
    sampled_items = json.loads(payload.dataset_payload)

    assert payload.items_count == 1500
    assert payload.sampled_items_count == 1000
    assert payload.max_prompt_items == DEFAULT_MAX_PROMPT_ITEMS
    assert payload.sampling_strategy == EVENLY_SPACED_SAMPLING_STRATEGY
    assert len(sampled_items) == 1000
    assert sampled_items[0]["recipe_id"] == 0
    assert sampled_items[-1]["recipe_id"] == 1499
    assert sampled_items == json.loads(build_bounded_taxonomy_payload(items).dataset_payload)


def test_build_bounded_taxonomy_payload_reduces_sample_size_to_fit_payload_budget() -> None:
    items = [
        {
            "recipe_id": index,
            "name": f"Recipe {index}",
            "description": "x" * 1200,
            "tags": ["tag"],
            "ingredients": ["ingredient"],
        }
        for index in range(20)
    ]

    payload = build_bounded_taxonomy_payload(
        items,
        max_prompt_items=20,
        max_payload_chars=DEFAULT_MAX_PAYLOAD_CHARS // 10,
    )

    assert payload.items_count == 20
    assert payload.sampled_items_count < 20
    assert len(payload.dataset_payload) <= DEFAULT_MAX_PAYLOAD_CHARS // 10
    assert payload.sampling_strategy == EVENLY_SPACED_SAMPLING_STRATEGY


def test_normalize_taxonomy_dictionary_merges_duplicate_keys_and_values() -> None:
    normalized = normalize_taxonomy_dictionary(
        {
            "Dish Type": ["Soup", "Bread", "bread "],
            "dish_type": ["Salad"],
            "Cuisine": ["Italian", "thai curry"],
            "ignore_me": 5,
        }
    )

    assert normalized == {
        "cuisine": ["italian", "thai_curry"],
        "dish_type": ["bread", "salad", "soup"],
    }


def test_generate_taxonomy_dictionary_repairs_malformed_json() -> None:
    generator = _QueuedGenerator(
        [
            '```json\n{"Dish Type": ["Soup", "Bread",],}\n```',
            '{"Dish Type": ["Soup", "Bread"], "Cuisine": ["Italian"]}',
        ]
    )
    bundle = build_taxonomy_dictionary_prompt(
        build_bounded_taxonomy_payload(
            [
                {
                    "recipe_id": 1,
                    "name": "Recipe 1",
                    "description": "",
                    "tags": [],
                    "ingredients": [],
                }
            ]
        )
    )

    taxonomy = generate_taxonomy_dictionary(
        generator=generator,  # type: ignore[arg-type]
        prompt_bundle=bundle,
        max_tokens=512,
    )

    assert taxonomy == {
        "cuisine": ["italian"],
        "dish_type": ["bread", "soup"],
    }
    assert len(generator.calls) == 2
    assert "Convert the following text into valid JSON only." in str(generator.calls[1]["prompt"])


def test_generate_taxonomy_dictionary_rejects_empty_dictionary() -> None:
    generator = _QueuedGenerator(["{}"])
    bundle = build_taxonomy_dictionary_prompt(
        build_bounded_taxonomy_payload(
            [
                {
                    "recipe_id": 1,
                    "name": "Recipe 1",
                    "description": "",
                    "tags": [],
                    "ingredients": [],
                }
            ]
        )
    )

    try:
        generate_taxonomy_dictionary(
            generator=generator,  # type: ignore[arg-type]
            prompt_bundle=bundle,
        )
    except ValueError as exc:
        assert str(exc) == "Taxonomy generation produced no usable features or values."
    else:
        raise AssertionError("Expected ValueError for an empty taxonomy dictionary.")


def test_generate_taxonomy_dictionary_rejects_degenerate_values() -> None:
    generator = _QueuedGenerator(['{"Cuisine": ["!!!"]}'])
    bundle = build_taxonomy_dictionary_prompt(
        build_bounded_taxonomy_payload(
            [
                {
                    "recipe_id": 1,
                    "name": "Recipe 1",
                    "description": "",
                    "tags": [],
                    "ingredients": [],
                }
            ]
        )
    )

    try:
        generate_taxonomy_dictionary(
            generator=generator,  # type: ignore[arg-type]
            prompt_bundle=bundle,
        )
    except ValueError as exc:
        assert str(exc) == "Taxonomy generation produced no usable features or values."
    else:
        raise AssertionError("Expected ValueError for degenerate taxonomy values.")


def test_parse_taxonomy_json_ignores_trailing_brace_text() -> None:
    parsed = _parse_taxonomy_json(
        '{"Cuisine": ["Italian"], "Dish Type": ["Soup"]}\nNote: keep {cuisine} broad.',
    )

    assert parsed == {
        "Cuisine": ["Italian"],
        "Dish Type": ["Soup"],
    }


def test_generate_taxonomy_dictionary_reports_repair_failure_clearly() -> None:
    generator = _QueuedGenerator(["not-json", "still not json"])
    bundle = build_taxonomy_dictionary_prompt(
        build_bounded_taxonomy_payload(
            [
                {
                    "recipe_id": 1,
                    "name": "Recipe 1",
                    "description": "",
                    "tags": [],
                    "ingredients": [],
                }
            ]
        )
    )

    try:
        generate_taxonomy_dictionary(
            generator=generator,  # type: ignore[arg-type]
            prompt_bundle=bundle,
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "Taxonomy generation failed: both initial and repair attempts produced invalid JSON."
        )
    else:
        raise AssertionError("Expected ValueError for repeated invalid JSON output.")
