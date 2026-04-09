import json
from pathlib import Path

import pytest

from sid_reco.sid.serialization import (
    serialize_structured_items,
    serialize_taxonomy_text,
    write_serialized_items,
)


def test_serialize_taxonomy_text_uses_feature_order_and_drops_empty_values() -> None:
    serialized = serialize_taxonomy_text(
        {
            "taste_mood": ["comfort_food", "empty", "comfort_food"],
            "cuisine": ["american", "american"],
            "dish_type": ["soup"],
            "cooking_method": [],
        },
        feature_order=("cuisine", "dish_type", "taste_mood", "cooking_method"),
    )

    assert serialized == "cuisine: american, dish_type: soup, taste_mood: comfort_food"


def test_serialize_structured_items_sorts_by_recipe_id_and_ignores_evidence(
    tmp_path: Path,
) -> None:
    structured_items_path = tmp_path / "items.jsonl"
    structured_items_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "recipe_id": 102,
                        "taxonomy": {
                            "dish_type": ["pasta"],
                            "cuisine": ["italian"],
                        },
                        "evidence": {"target_item": {"name": "Tomato Pasta"}},
                    }
                ),
                json.dumps(
                    {
                        "recipe_id": 101,
                        "taxonomy": {
                            "taste_mood": ["empty", "comfort_food"],
                            "dish_type": ["soup"],
                            "cuisine": ["american", "american"],
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    items = serialize_structured_items(
        structured_items_path,
        feature_order=("cuisine", "dish_type", "taste_mood"),
    )

    assert [item.recipe_id for item in items] == [101, 102]
    assert items[0].taxonomy == {
        "cuisine": ["american"],
        "dish_type": ["soup"],
        "taste_mood": ["comfort_food"],
    }
    assert items[0].serialized_text == (
        "cuisine: american, dish_type: soup, taste_mood: comfort_food"
    )
    assert items[1].serialized_text == "cuisine: italian, dish_type: pasta"


def test_serialize_structured_items_rejects_non_list_taxonomy_values(tmp_path: Path) -> None:
    structured_items_path = tmp_path / "items.jsonl"
    structured_items_path.write_text(
        json.dumps(
            {
                "recipe_id": 101,
                "taxonomy": {
                    "cuisine": "american",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must be arrays of strings"):
        serialize_structured_items(structured_items_path)


def test_serialize_structured_items_rejects_duplicate_recipe_ids(tmp_path: Path) -> None:
    structured_items_path = tmp_path / "items.jsonl"
    structured_items_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "recipe_id": 101,
                        "taxonomy": {
                            "cuisine": ["american"],
                        },
                    }
                ),
                json.dumps(
                    {
                        "recipe_id": 101,
                        "taxonomy": {
                            "cuisine": ["italian"],
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate recipe_id in structured taxonomy items: 101"):
        serialize_structured_items(structured_items_path)


def test_write_serialized_items_writes_jsonl(tmp_path: Path) -> None:
    structured_items_path = tmp_path / "items.jsonl"
    out_path = tmp_path / "sid_index" / "serialized_items.jsonl"
    structured_items_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "recipe_id": 102,
                        "taxonomy": {
                            "dish_type": ["pasta"],
                            "cuisine": ["italian"],
                        },
                    }
                ),
                json.dumps(
                    {
                        "recipe_id": 101,
                        "taxonomy": {
                            "taste_mood": ["empty", "comfort_food"],
                            "dish_type": ["soup"],
                            "cuisine": ["american", "american"],
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    items = serialize_structured_items(
        structured_items_path,
        feature_order=("cuisine", "dish_type", "taste_mood"),
    )
    summary = write_serialized_items(items, out_path=out_path)

    assert summary.item_count == 2
    assert summary.output_path == out_path
    lines = out_path.read_text(encoding="utf-8").strip().splitlines()
    payloads = [json.loads(line) for line in lines]
    assert payloads == [
        {
            "recipe_id": 101,
            "serialized_text": "cuisine: american, dish_type: soup, taste_mood: comfort_food",
            "taxonomy": {
                "cuisine": ["american"],
                "dish_type": ["soup"],
                "taste_mood": ["comfort_food"],
            },
        },
        {
            "recipe_id": 102,
            "serialized_text": "cuisine: italian, dish_type: pasta",
            "taxonomy": {
                "cuisine": ["italian"],
                "dish_type": ["pasta"],
            },
        },
    ]
