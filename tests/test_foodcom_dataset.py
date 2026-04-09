import json

import pandas as pd

from sid_reco.datasets.foodcom import (
    RECIPES_COLUMNS,
    apply_k_core_filter,
    build_recipe_stats,
    build_temporal_splits,
    filter_positive_interactions,
    normalize_interactions,
    normalize_recipes,
    select_top_recipes,
)


def _interaction(
    user_id: int,
    recipe_id: int,
    date: str,
    rating: int,
    review: str = "",
) -> dict[str, object]:
    return {
        "user_id": user_id,
        "recipe_id": recipe_id,
        "date": date,
        "rating": rating,
        "review": review,
    }


def test_normalize_recipes_drops_rows_with_malformed_list_columns() -> None:
    raw_recipes = pd.DataFrame(
        [
            {
                "id": 1,
                "name": "Alpha",
                "minutes": 10,
                "tags": "['quick', 'easy']",
                "nutrition": "[100, 5, 10]",
                "n_steps": 2,
                "steps": "['mix', 'serve']",
                "description": "good",
                "ingredients": "['salt', 'pepper']",
                "n_ingredients": 2,
            },
            {
                "id": 2,
                "name": "Broken",
                "minutes": 15,
                "tags": "not-a-list",
                "nutrition": "[100, 5, 10]",
                "n_steps": 1,
                "steps": "['cook']",
                "description": "bad",
                "ingredients": "['oil']",
                "n_ingredients": 1,
            },
        ]
    )

    normalized = normalize_recipes(raw_recipes)

    assert normalized["recipe_id"].tolist() == [1]
    assert normalized.iloc[0]["tags"] == ["quick", "easy"]
    assert normalized.iloc[0]["ingredients"] == ["salt", "pepper"]


def test_normalize_interactions_filters_invalid_rows() -> None:
    raw_interactions = pd.DataFrame(
        [
            {"user_id": 1, "recipe_id": 11, "date": "2024-01-01", "rating": 5, "review": "great"},
            {"user_id": 2, "recipe_id": 11, "date": "bad-date", "rating": 4, "review": "skip"},
            {"user_id": 3, "recipe_id": 12, "date": "2024-01-02", "rating": 8, "review": "skip"},
            {"user_id": 1, "recipe_id": 11, "date": "2024-01-01", "rating": 5, "review": "great"},
        ]
    )

    normalized = normalize_interactions(raw_interactions)

    assert normalized.to_dict(orient="records") == [
        {
            "user_id": 1,
            "recipe_id": 11,
            "date": "2024-01-01",
            "rating": 5.0,
            "review": "great",
            "source_rating": 5.0,
        }
    ]


def test_positive_filter_and_top_recipe_stats_use_original_ratings() -> None:
    recipes = normalize_recipes(
        pd.DataFrame(
            [
                {
                    "id": 10,
                    "name": "A",
                    "minutes": 10,
                    "tags": "['a']",
                    "nutrition": "[1]",
                    "n_steps": 1,
                    "steps": "['x']",
                    "description": "A",
                    "ingredients": "['salt']",
                    "n_ingredients": 1,
                },
                {
                    "id": 20,
                    "name": "B",
                    "minutes": 20,
                    "tags": "['b']",
                    "nutrition": "[2]",
                    "n_steps": 1,
                    "steps": "['y']",
                    "description": "B",
                    "ingredients": "['pepper']",
                    "n_ingredients": 1,
                },
                {
                    "id": 30,
                    "name": "C",
                    "minutes": 30,
                    "tags": "['c']",
                    "nutrition": "[3]",
                    "n_steps": 1,
                    "steps": "['z']",
                    "description": "C",
                    "ingredients": "['oil']",
                    "n_ingredients": 1,
                },
            ]
        )
    )
    interactions = filter_positive_interactions(
        normalize_interactions(
            pd.DataFrame(
                [
                    {
                        "user_id": 1,
                        "recipe_id": 20,
                        "date": "2024-01-01",
                        "rating": 5,
                        "review": "great",
                    },
                    {
                        "user_id": 2,
                        "recipe_id": 20,
                        "date": "2024-01-02",
                        "rating": 4,
                        "review": "",
                    },
                    {
                        "user_id": 3,
                        "recipe_id": 10,
                        "date": "2024-01-03",
                        "rating": 3,
                        "review": "drop",
                    },
                    {
                        "user_id": 4,
                        "recipe_id": 30,
                        "date": "2024-01-04",
                        "rating": 5,
                        "review": "nice",
                    },
                    {
                        "user_id": 5,
                        "recipe_id": 30,
                        "date": "2024-01-05",
                        "rating": 5,
                        "review": "",
                    },
                    {
                        "user_id": 6,
                        "recipe_id": 30,
                        "date": "2024-01-06",
                        "rating": 4,
                        "review": "wow",
                    },
                ]
            )
        ),
        positive_threshold=4.0,
    )

    assert set(interactions["rating"]) == {1.0}
    assert set(interactions["source_rating"]) == {4.0, 5.0}

    selected_recipes, selected_interactions = select_top_recipes(recipes, interactions, top_n=2)
    enriched = build_recipe_stats(selected_recipes, selected_interactions).sort_values("recipe_id")

    assert selected_recipes["recipe_id"].tolist() == [20, 30]
    assert set(selected_interactions["recipe_id"]) == {20, 30}
    assert enriched["interaction_count"].tolist() == [2, 3]
    assert enriched["avg_rating"].round(2).tolist() == [4.5, 4.67]
    assert enriched["review_count"].tolist() == [1, 2]
    assert list(enriched.columns) == RECIPES_COLUMNS


def test_apply_k_core_filter_is_iterative() -> None:
    interaction_rows: list[dict[str, object]] = []
    for user_id in range(1, 5):
        for day in range(1, 5):
            interaction_rows.append(
                _interaction(user_id, 101, f"2024-01-{((user_id - 1) * 5) + day:02d}", 5),
            )
        interaction_rows.append(
            _interaction(user_id, 202, f"2024-02-{user_id:02d}", 5),
        )

    for day in range(1, 6):
        interaction_rows.append(_interaction(5, 101, f"2024-03-{day:02d}", 5))

    interaction_rows.append(_interaction(6, 202, "2024-04-01", 5))

    interactions = filter_positive_interactions(
        normalize_interactions(pd.DataFrame(interaction_rows)),
        positive_threshold=4.0,
    )

    filtered = apply_k_core_filter(
        interactions,
        min_user_interactions=5,
        min_item_interactions=5,
    )

    assert set(filtered["user_id"]) == {5}
    assert set(filtered["recipe_id"]) == {101}


def test_build_temporal_splits_uses_temporal_8_1_1_rule() -> None:
    interaction_rows = [
        _interaction(1, 10 + index, f"2024-01-{index + 1:02d}", 5) for index in range(5)
    ]
    interaction_rows.extend(
        _interaction(2, 20 + index, f"2024-02-{index + 1:02d}", 5) for index in range(10)
    )

    interactions = filter_positive_interactions(
        normalize_interactions(pd.DataFrame(interaction_rows)),
        positive_threshold=4.0,
    )

    splits = build_temporal_splits(interactions)

    assert splits["train"]["recipe_id"].tolist() == [10, 11, 12, 20, 21, 22, 23, 24, 25, 26, 27]
    assert splits["valid"]["recipe_id"].tolist() == [13, 28]
    assert splits["test"]["recipe_id"].tolist() == [14, 29]
    combined = pd.concat([splits["train"], splits["valid"], splits["test"]], ignore_index=True)
    expected_records = interactions.loc[:, ["user_id", "recipe_id", "date", "rating", "review"]]
    assert sorted(combined.to_dict(orient="records"), key=json.dumps) == sorted(
        expected_records.to_dict(orient="records"),
        key=json.dumps,
    )
