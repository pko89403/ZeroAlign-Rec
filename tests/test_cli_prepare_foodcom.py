import json
from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from sid_reco.cli import app

runner = CliRunner()


def _recipe_row(
    recipe_id: int,
    name: str,
    minutes: int,
    tags: str,
    nutrition: str,
    steps: str,
    description: str,
    ingredients: str,
) -> dict[str, object]:
    return {
        "id": recipe_id,
        "name": name,
        "minutes": minutes,
        "tags": tags,
        "nutrition": nutrition,
        "n_steps": 1 if steps == "['mix']" or steps == "['toast']" else 2,
        "steps": steps,
        "description": description,
        "ingredients": ingredients,
        "n_ingredients": 1 if ingredients == "['lettuce']" or ingredients == "['bread']" else 2,
    }


def test_prepare_foodcom_cli_writes_processed_outputs(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw" / "foodcom"
    out_dir = tmp_path / "processed" / "foodcom"
    raw_dir.mkdir(parents=True)

    pd.DataFrame(
        [
            _recipe_row(
                101,
                "Soup",
                20,
                "['comfort', 'easy']",
                "[100, 5, 10]",
                "['prep', 'cook']",
                "Warm soup",
                "['water', 'salt']",
            ),
            _recipe_row(
                102,
                "Salad",
                10,
                "['fresh']",
                "[80, 3, 7]",
                "['mix']",
                "Fresh salad",
                "['lettuce']",
            ),
            _recipe_row(
                103,
                "Toast",
                5,
                "['quick']",
                "[120, 4, 8]",
                "['toast']",
                "Quick toast",
                "['bread']",
            ),
        ]
    ).to_csv(raw_dir / "RAW_recipes.csv", index=False)
    interaction_rows: list[dict[str, object]] = []
    for user_id in range(1, 6):
        interaction_rows.extend(
            [
                    {
                        "user_id": user_id,
                        "recipe_id": 101,
                        "date": f"2024-01-{((user_id - 1) * 5) + 1:02d}",
                        "rating": 5,
                        "review": f"user-{user_id}-a",
                    },
                    {
                        "user_id": user_id,
                        "recipe_id": 103,
                        "date": f"2024-01-{((user_id - 1) * 5) + 2:02d}",
                        "rating": 5,
                        "review": "",
                    },
                    {
                        "user_id": user_id,
                        "recipe_id": 101,
                        "date": f"2024-01-{((user_id - 1) * 5) + 3:02d}",
                        "rating": 4,
                        "review": f"user-{user_id}-b",
                    },
                    {
                        "user_id": user_id,
                        "recipe_id": 103,
                        "date": f"2024-01-{((user_id - 1) * 5) + 4:02d}",
                        "rating": 5,
                        "review": "",
                    },
                    {
                        "user_id": user_id,
                        "recipe_id": 101,
                        "date": f"2024-01-{((user_id - 1) * 5) + 5:02d}",
                        "rating": 5,
                        "review": f"user-{user_id}-c",
                    },
                ]
        )
    interaction_rows.append(
        {
            "user_id": 99,
            "recipe_id": 102,
            "date": "2024-03-01",
            "rating": 2,
            "review": "drop-negative",
        }
    )
    pd.DataFrame(interaction_rows).to_csv(raw_dir / "RAW_interactions.csv", index=False)

    result = runner.invoke(
        app,
        [
            "prepare-foodcom",
            "--raw-dir",
            str(raw_dir),
            "--out-dir",
            str(out_dir),
            "--top-recipes",
            "2",
            "--core-k",
            "5",
            "--positive-threshold",
            "4",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (out_dir / "recipes.csv").exists()
    assert (out_dir / "interactions.csv").exists()
    assert (out_dir / "splits" / "train.csv").exists()
    assert (out_dir / "splits" / "valid.csv").exists()
    assert (out_dir / "splits" / "test.csv").exists()
    assert (out_dir / "manifest.json").exists()

    recipes = pd.read_csv(out_dir / "recipes.csv")
    interactions = pd.read_csv(out_dir / "interactions.csv")
    train = pd.read_csv(out_dir / "splits" / "train.csv")
    valid = pd.read_csv(out_dir / "splits" / "valid.csv")
    test = pd.read_csv(out_dir / "splits" / "test.csv")
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))

    assert set(recipes["recipe_id"]) == {101, 103}
    assert set(interactions["recipe_id"]) == {101, 103}
    assert set(interactions["rating"]) == {1.0}
    assert len(train) == 15
    assert len(valid) == 5
    assert len(test) == 5
    assert manifest["recipes_rows"] == 2
    assert manifest["interactions_rows"] == 25
    assert manifest["train_rows"] == 15
    assert manifest["valid_rows"] == 5
    assert manifest["test_rows"] == 5
    assert manifest["positive_threshold"] == 4
    assert manifest["core_filter"]["min_user_interactions"] == 5
    assert manifest["split_strategy"] == "temporal_8_1_1"
    assert manifest["unique_recipes"] == 2
