import json
from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from sid_reco.cli import app

runner = CliRunner()


class _FakeGenerator:
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id

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
        assert system_prompt is not None
        assert "recipe metadata" in prompt.lower()
        assert max_tokens == 1024
        return json.dumps(
            {
                "Dish Type": ["Soup", "Bread"],
                "Cuisine": ["Italian"],
                "Primary Ingredient": ["Tomato", "Wheat Flour"],
            }
        )


class _EmptyTaxonomyGenerator:
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id

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
        return "{}"


def test_build_taxonomy_dictionary_cli_writes_outputs(tmp_path: Path, monkeypatch) -> None:
    recipes_path = tmp_path / "recipes.csv"
    out_dir = tmp_path / "taxonomy_dictionary"
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
                "name": "Bread Loaf",
                "description": "Simple baked bread.",
                "tags": json.dumps(["bread", "baked"]),
                "ingredients": json.dumps(["flour", "yeast"]),
            },
        ]
    ).to_csv(recipes_path, index=False)

    monkeypatch.setattr("sid_reco.taxonomy.dictionary.MLXTextGenerator", _FakeGenerator)

    result = runner.invoke(
        app,
        [
            "build-taxonomy-dictionary",
            "--recipes-path",
            str(recipes_path),
            "--out-dir",
            str(out_dir),
            "--max-tokens",
            "1024",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (out_dir / "food_taxonomy_dictionary.json").exists()
    assert (out_dir / "prompt_snapshot.json").exists()

    taxonomy = json.loads((out_dir / "food_taxonomy_dictionary.json").read_text(encoding="utf-8"))
    snapshot = json.loads((out_dir / "prompt_snapshot.json").read_text(encoding="utf-8"))

    assert taxonomy == {
        "cuisine": ["italian"],
        "dish_type": ["bread", "soup"],
        "primary_ingredient": ["tomato", "wheat_flour"],
    }
    assert snapshot["model_id"] == "mlx-community/Qwen3.5-9B-OptiQ-4bit"
    assert snapshot["generation_params"]["max_tokens"] == 1024
    assert snapshot["items_count"] == 2
    assert snapshot["sampled_items_count"] == 2
    assert snapshot["max_prompt_items"] == 1000
    assert snapshot["sampling_strategy"] == "full_catalog"


def test_build_taxonomy_dictionary_cli_fails_for_empty_taxonomy(
    tmp_path: Path,
    monkeypatch,
) -> None:
    recipes_path = tmp_path / "recipes.csv"
    out_dir = tmp_path / "taxonomy_dictionary"
    pd.DataFrame(
        [
            {
                "recipe_id": 101,
                "name": "Tomato Soup",
                "description": "Warm tomato soup.",
                "tags": json.dumps(["soup", "easy"]),
                "ingredients": json.dumps(["tomato", "salt"]),
            }
        ]
    ).to_csv(recipes_path, index=False)

    monkeypatch.setattr(
        "sid_reco.taxonomy.dictionary.MLXTextGenerator",
        _EmptyTaxonomyGenerator,
    )

    result = runner.invoke(
        app,
        [
            "build-taxonomy-dictionary",
            "--recipes-path",
            str(recipes_path),
            "--out-dir",
            str(out_dir),
        ],
    )

    assert result.exit_code == 1, result.stdout
    assert "Taxonomy generation produced no usable features or values." in result.stdout
    assert not (out_dir / "food_taxonomy_dictionary.json").exists()
    assert not (out_dir / "prompt_snapshot.json").exists()


def test_build_taxonomy_dictionary_cli_reports_catalog_and_prompt_items(
    tmp_path: Path,
    monkeypatch,
) -> None:
    recipes_path = tmp_path / "recipes.csv"
    out_dir = tmp_path / "taxonomy_dictionary"
    pd.DataFrame(
        [
            {
                "recipe_id": 101,
                "name": "Tomato Soup",
                "description": "Warm tomato soup.",
                "tags": json.dumps(["soup", "easy"]),
                "ingredients": json.dumps(["tomato", "salt"]),
            }
        ]
    ).to_csv(recipes_path, index=False)

    monkeypatch.setattr(
        "sid_reco.cli.build_taxonomy_dictionary",
        lambda **_: type(
            "Summary",
            (),
            {
                "items_count": 3000,
                "sampled_items_count": 1000,
                "feature_count": 5,
                "total_value_count": 160,
            },
        )(),
    )

    result = runner.invoke(
        app,
        [
            "build-taxonomy-dictionary",
            "--recipes-path",
            str(recipes_path),
            "--out-dir",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "Catalog items" in result.stdout
    assert "Prompt items" in result.stdout
    assert "3000" in result.stdout
    assert "1000" in result.stdout
