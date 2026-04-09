import json
from pathlib import Path

import pandas as pd

from sid_reco.taxonomy.item_projection import (
    DEFAULT_NEIGHBOR_COUNT,
    build_item_projection_context,
    build_item_projection_prompt,
    finalize_item_taxonomy,
    generate_item_taxonomy,
    structure_taxonomy_batch,
    structure_taxonomy_item,
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


def test_build_item_projection_context_loads_target_neighbors_and_taxonomy(tmp_path: Path) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(tmp_path)

    context = build_item_projection_context(
        recipe_id=101,
        recipes_path=recipes_path,
        neighbor_context_path=neighbors_path,
        taxonomy_dictionary_path=taxonomy_path,
    )

    assert context.recipe_id == 101
    assert context.target_item["name"] == "Tomato Soup"
    assert [neighbor["recipe_id"] for neighbor in context.neighbors] == [102, 103, 104, 105, 106]
    assert list(context.taxonomy_dictionary) == ["cuisine", "dish_type", "taste_mood"]


def test_build_item_projection_prompt_embeds_target_neighbors_and_vocab(tmp_path: Path) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(tmp_path)
    context = build_item_projection_context(
        recipe_id=101,
        recipes_path=recipes_path,
        neighbor_context_path=neighbors_path,
        taxonomy_dictionary_path=taxonomy_path,
    )

    bundle = build_item_projection_prompt(context)

    assert "Top-5 neighbors" in bundle.user_prompt
    assert "Tomato Soup" in bundle.user_prompt
    assert "Tomato Pasta" in bundle.user_prompt
    assert "comfort_food" in bundle.user_prompt
    assert "few-shot guidance" in bundle.user_prompt
    assert "collapse duplicates and near-synonyms" in bundle.user_prompt
    assert "Do not repeat the same concept across multiple keys" in bundle.user_prompt
    assert bundle.user_prompt.index("few-shot guidance") < bundle.user_prompt.index(
        'return ["empty"]'
    )
    assert bundle.required_keys == ("cuisine", "dish_type", "taste_mood")


def test_generate_item_taxonomy_allows_open_vocab_values_for_known_keys(tmp_path: Path) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(tmp_path)
    context = build_item_projection_context(
        recipe_id=101,
        recipes_path=recipes_path,
        neighbor_context_path=neighbors_path,
        taxonomy_dictionary_path=taxonomy_path,
    )
    bundle = build_item_projection_prompt(context)
    generator = _QueuedGenerator(
        [
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": ["Cozy Dinner"],
                }
            ),
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": ["Cozy Dinner"],
                }
            ),
        ]
    )

    taxonomy = generate_item_taxonomy(
        generator=generator,  # type: ignore[arg-type]
        prompt_bundle=bundle,
        context=context,
    )

    assert taxonomy == {
        "cuisine": ["italian"],
        "dish_type": ["soup"],
        "taste_mood": ["cozy_dinner"],
    }
    assert len(generator.calls) == 1


def test_generate_item_taxonomy_self_refines_canonicalizable_variants(tmp_path: Path) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(
        tmp_path,
        taxonomy_dictionary={
            "cuisine": ["italian"],
            "dish_type": ["soup"],
            "taste_mood": ["comfort_food"],
        },
    )
    context = build_item_projection_context(
        recipe_id=101,
        recipes_path=recipes_path,
        neighbor_context_path=neighbors_path,
        taxonomy_dictionary_path=taxonomy_path,
    )
    bundle = build_item_projection_prompt(context)
    generator = _QueuedGenerator(
        [
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soups"],
                    "Taste Mood": ["Comfort Food"],
                }
            ),
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": ["Comfort Food"],
                }
            ),
        ]
    )

    taxonomy = generate_item_taxonomy(
        generator=generator,  # type: ignore[arg-type]
        prompt_bundle=bundle,
        context=context,
    )

    assert taxonomy == {
        "cuisine": ["italian"],
        "dish_type": ["soup"],
        "taste_mood": ["comfort_food"],
    }
    assert len(generator.calls) == 2
    assert "Draft taxonomy JSON" in str(generator.calls[1]["prompt"])


def test_generate_item_taxonomy_repairs_missing_required_keys(tmp_path: Path) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(tmp_path)
    context = build_item_projection_context(
        recipe_id=101,
        recipes_path=recipes_path,
        neighbor_context_path=neighbors_path,
        taxonomy_dictionary_path=taxonomy_path,
    )
    bundle = build_item_projection_prompt(context)
    generator = _QueuedGenerator(
        [
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                }
            ),
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": ["Cozy Dinner"],
                }
            ),
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": ["Cozy Dinner"],
                }
            ),
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": ["Cozy Dinner"],
                }
            ),
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": ["Cozy Dinner"],
                }
            ),
        ]
    )

    taxonomy = generate_item_taxonomy(
        generator=generator,  # type: ignore[arg-type]
        prompt_bundle=bundle,
        context=context,
    )

    assert taxonomy == {
        "cuisine": ["italian"],
        "dish_type": ["soup"],
        "taste_mood": ["cozy_dinner"],
    }
    assert len(generator.calls) == 2


def test_generate_item_taxonomy_retries_when_response_contains_empty_values(tmp_path: Path) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(tmp_path)
    context = build_item_projection_context(
        recipe_id=101,
        recipes_path=recipes_path,
        neighbor_context_path=neighbors_path,
        taxonomy_dictionary_path=taxonomy_path,
    )
    bundle = build_item_projection_prompt(context)
    generator = _QueuedGenerator(
        [
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": [],
                }
            ),
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": ["Cozy Dinner"],
                }
            ),
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": ["Cozy Dinner"],
                }
            ),
        ]
    )

    taxonomy = generate_item_taxonomy(
        generator=generator,  # type: ignore[arg-type]
        prompt_bundle=bundle,
        context=context,
    )

    assert taxonomy == {
        "cuisine": ["italian"],
        "dish_type": ["soup"],
        "taste_mood": ["cozy_dinner"],
    }
    assert len(generator.calls) == 2


def test_generate_item_taxonomy_falls_back_to_empty_label_after_five_empty_attempts(
    tmp_path: Path,
) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(tmp_path)
    context = build_item_projection_context(
        recipe_id=101,
        recipes_path=recipes_path,
        neighbor_context_path=neighbors_path,
        taxonomy_dictionary_path=taxonomy_path,
    )
    bundle = build_item_projection_prompt(context)
    generator = _QueuedGenerator(
        [
            json.dumps(
                {
                    "Cuisine": [],
                    "Dish Type": ["Soup"],
                    "Taste Mood": [],
                }
            )
        ]
        * 5
    )

    taxonomy = generate_item_taxonomy(
        generator=generator,  # type: ignore[arg-type]
        prompt_bundle=bundle,
        context=context,
    )

    assert taxonomy == {
        "cuisine": ["empty"],
        "dish_type": ["soup"],
        "taste_mood": ["empty"],
    }
    assert len(generator.calls) == 5


def test_finalize_item_taxonomy_canonicalizes_variants_and_drops_weak_american_bias(
    tmp_path: Path,
) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(
        tmp_path,
        include_all_sources=True,
        taxonomy_dictionary={
            "cuisine": ["american", "italian"],
            "dish_type": ["soup", "pasta", "salad"],
            "taste_mood": ["comfort_food"],
            "cooking_method": ["roast"],
            "primary_ingredient": ["tomato"],
        },
    )
    context = build_item_projection_context(
        recipe_id=101,
        recipes_path=recipes_path,
        neighbor_context_path=neighbors_path,
        taxonomy_dictionary_path=taxonomy_path,
    )

    taxonomy = finalize_item_taxonomy(
        taxonomy={
            "cuisine": ["american"],
            "dish_type": ["soups"],
            "taste_mood": ["comfort_food"],
            "cooking_method": ["roasted"],
            "primary_ingredient": ["tomatoes"],
        },
        taxonomy_dictionary=context.taxonomy_dictionary,
        context=context,
    )

    assert taxonomy == {
        "cuisine": ["empty"],
        "dish_type": ["soup"],
        "taste_mood": ["comfort_food"],
        "cooking_method": ["roast"],
        "primary_ingredient": ["tomato"],
    }


def test_finalize_item_taxonomy_drops_contradictory_dietary_labels(tmp_path: Path) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(
        tmp_path,
        include_all_sources=True,
        taxonomy_dictionary={
            "cuisine": ["american", "italian"],
            "dish_type": ["soup", "pasta", "salad"],
            "taste_mood": ["comfort_food"],
            "dietary_style": ["gluten_free", "vegetarian"],
        },
    )
    context = build_item_projection_context(
        recipe_id=102,
        recipes_path=recipes_path,
        neighbor_context_path=neighbors_path,
        taxonomy_dictionary_path=taxonomy_path,
    )

    taxonomy = finalize_item_taxonomy(
        taxonomy={
            "cuisine": ["italian"],
            "dish_type": ["pasta"],
            "taste_mood": ["comfort_food"],
            "dietary_style": ["gluten_free", "vegetarian"],
        },
        taxonomy_dictionary=context.taxonomy_dictionary,
        context=context,
    )

    assert taxonomy["dietary_style"] == ["vegetarian"]


def test_build_item_projection_context_requires_top5_neighbors(tmp_path: Path) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(
        tmp_path,
        neighbor_count=4,
    )

    try:
        build_item_projection_context(
            recipe_id=101,
            recipes_path=recipes_path,
            neighbor_context_path=neighbors_path,
            taxonomy_dictionary_path=taxonomy_path,
            top_k=DEFAULT_NEIGHBOR_COUNT,
        )
    except ValueError as exc:
        assert str(exc) == "Recipe 101 does not have the required top-5 neighbor context."
    else:
        raise AssertionError("Expected ValueError when fewer than five neighbors are available.")


def test_structure_taxonomy_item_optionally_includes_evidence(tmp_path: Path) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(tmp_path)
    generator = _QueuedGenerator(
        [
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": ["Cozy Dinner"],
                }
            ),
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": ["Cozy Dinner"],
                }
            ),
        ]
    )

    structured_item = structure_taxonomy_item(
        recipe_id=101,
        recipes_path=recipes_path,
        neighbor_context_path=neighbors_path,
        taxonomy_dictionary_path=taxonomy_path,
        llm_model="test-model",
        generator=generator,  # type: ignore[arg-type]
        include_evidence=True,
    )

    record = structured_item.to_record()
    assert record["recipe_id"] == 101
    assert record["evidence"]["target_item"]["name"] == "Tomato Soup"
    assert len(record["evidence"]["neighbors"]) == 5
    assert record["evidence"]["neighbors"][0]["neighbor_recipe_id"] == 102


def test_structure_taxonomy_batch_reports_progress(tmp_path: Path) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(
        tmp_path,
        include_all_sources=True,
    )
    out_path = tmp_path / "structured_items.jsonl"
    generator = _QueuedGenerator(
        [
            json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": ["Cozy Dinner"],
                }
            )
        ]
        * 12
    )
    seen: list[tuple[int, int, int]] = []

    summary = structure_taxonomy_batch(
        recipes_path=recipes_path,
        neighbor_context_path=neighbors_path,
        taxonomy_dictionary_path=taxonomy_path,
        out_path=out_path,
        llm_model="test-model",
        generator=generator,  # type: ignore[arg-type]
        progress_callback=lambda completed, total, recipe_id: seen.append(
            (completed, total, recipe_id),
        ),
    )

    assert summary.item_count == 6
    assert seen[0] == (1, 6, 101)
    assert seen[-1] == (6, 6, 106)


def _write_projection_inputs(
    tmp_path: Path,
    *,
    neighbor_count: int = DEFAULT_NEIGHBOR_COUNT,
    include_all_sources: bool = False,
    taxonomy_dictionary: dict[str, list[str]] | None = None,
) -> tuple[Path, Path, Path]:
    recipes_path = tmp_path / "recipes.csv"
    neighbors_path = tmp_path / "neighbor_context.csv"
    taxonomy_path = tmp_path / "food_taxonomy_dictionary.json"

    pd.DataFrame(
        [
            {
                "recipe_id": 101,
                "name": "Tomato Soup",
                "description": "Warm tomato soup.",
                "tags": json.dumps(["soup", "easy"]),
                "ingredients": json.dumps(["tomato", "salt"]),
            },
            {
                "recipe_id": 102,
                "name": "Tomato Pasta",
                "description": "Simple pasta dinner.",
                "tags": json.dumps(["pasta", "easy"]),
                "ingredients": json.dumps(["tomato", "pasta"]),
            },
            {
                "recipe_id": 103,
                "name": "Basil Salad",
                "description": "Fresh basil side dish.",
                "tags": json.dumps(["salad", "fresh"]),
                "ingredients": json.dumps(["basil", "olive oil"]),
            },
            {
                "recipe_id": 104,
                "name": "Garlic Bread",
                "description": "Baked garlic bread.",
                "tags": json.dumps(["bread", "baked"]),
                "ingredients": json.dumps(["garlic", "bread"]),
            },
            {
                "recipe_id": 105,
                "name": "Roasted Tomato",
                "description": "Oven roasted tomato side.",
                "tags": json.dumps(["roasted", "side"]),
                "ingredients": json.dumps(["tomato", "olive oil"]),
            },
            {
                "recipe_id": 106,
                "name": "Creamy Soup",
                "description": "Comfort soup for dinner.",
                "tags": json.dumps(["soup", "comfort_food"]),
                "ingredients": json.dumps(["cream", "salt"]),
            },
        ]
    ).to_csv(recipes_path, index=False)

    if include_all_sources:
        ordered_neighbors_by_source = {
            101: [102, 103, 104, 105, 106],
            102: [101, 103, 104, 105, 106],
            103: [101, 102, 104, 105, 106],
            104: [101, 102, 103, 105, 106],
            105: [101, 102, 103, 104, 106],
            106: [101, 102, 103, 104, 105],
        }
        neighbor_rows = []
        for source_recipe_id, ordered_neighbors in ordered_neighbors_by_source.items():
            for rank, neighbor_recipe_id in enumerate(ordered_neighbors[:neighbor_count], start=1):
                neighbor_rows.append(
                    {
                        "source_recipe_id": source_recipe_id,
                        "neighbor_rank": rank,
                        "neighbor_recipe_id": neighbor_recipe_id,
                        "cosine_similarity": 0.9 - (rank * 0.01),
                    }
                )
    else:
        neighbor_rows = [
            {
                "source_recipe_id": 101,
                "neighbor_rank": rank,
                "neighbor_recipe_id": recipe_id,
                "cosine_similarity": 0.9 - (rank * 0.01),
            }
            for rank, recipe_id in enumerate([102, 103, 104, 105, 106][:neighbor_count], start=1)
        ]
    pd.DataFrame(neighbor_rows).to_csv(neighbors_path, index=False)

    taxonomy_path.write_text(
        json.dumps(
            taxonomy_dictionary
            or {
                "cuisine": ["italian", "american"],
                "dish_type": ["soup", "pasta", "salad"],
                "taste_mood": ["comfort_food"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return recipes_path, neighbors_path, taxonomy_path
