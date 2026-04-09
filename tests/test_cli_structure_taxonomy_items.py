import json
from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from sid_reco.cli import app

runner = CliRunner()


class _ProjectionGenerator:
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
        target_section = prompt.split("Top-5 neighbors:", maxsplit=1)[0]
        if '"name": "Tomato Soup"' in target_section:
            return json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Soup"],
                    "Taste Mood": ["Cozy Dinner"],
                }
            )
        if '"name": "Tomato Pasta"' in target_section:
            return json.dumps(
                {
                    "Cuisine": ["Italian"],
                    "Dish Type": ["Pasta"],
                    "Taste Mood": [],
                }
            )
        return json.dumps(
            {
                "Cuisine": [],
                "Dish Type": [],
                "Taste Mood": [],
            }
        )


def test_structure_taxonomy_item_cli_prints_json(tmp_path: Path, monkeypatch) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(tmp_path)
    monkeypatch.setattr(
        "sid_reco.taxonomy.item_projection.MLXTextGenerator",
        _ProjectionGenerator,
    )

    result = runner.invoke(
        app,
        [
            "structure-taxonomy-item",
            "--recipe-id",
            "101",
            "--recipes-path",
            str(recipes_path),
            "--neighbor-context-path",
            str(neighbors_path),
            "--taxonomy-dictionary-path",
            str(taxonomy_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload == {
        "recipe_id": 101,
        "taxonomy": {
            "cuisine": ["italian"],
            "dish_type": ["soup"],
            "taste_mood": ["cozy_dinner"],
        },
    }


def test_structure_taxonomy_item_cli_can_include_evidence(tmp_path: Path, monkeypatch) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(tmp_path)
    monkeypatch.setattr(
        "sid_reco.taxonomy.item_projection.MLXTextGenerator",
        _ProjectionGenerator,
    )

    result = runner.invoke(
        app,
        [
            "structure-taxonomy-item",
            "--recipe-id",
            "101",
            "--recipes-path",
            str(recipes_path),
            "--neighbor-context-path",
            str(neighbors_path),
            "--taxonomy-dictionary-path",
            str(taxonomy_path),
            "--include-evidence",
        ],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["evidence"]["target_item"]["name"] == "Tomato Soup"
    assert len(payload["evidence"]["neighbors"]) == 5
    assert payload["evidence"]["neighbors"][0]["neighbor_recipe_id"] == 102


def test_structure_taxonomy_batch_cli_writes_jsonl(tmp_path: Path, monkeypatch) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(tmp_path)
    out_path = tmp_path / "structured_items.jsonl"
    monkeypatch.setattr(
        "sid_reco.taxonomy.item_projection.MLXTextGenerator",
        _ProjectionGenerator,
    )

    result = runner.invoke(
        app,
        [
            "structure-taxonomy-batch",
            "--recipes-path",
            str(recipes_path),
            "--neighbor-context-path",
            str(neighbors_path),
            "--taxonomy-dictionary-path",
            str(taxonomy_path),
            "--out-path",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    lines = out_path.read_text(encoding="utf-8").strip().splitlines()
    payloads = [json.loads(line) for line in lines]
    assert [payload["recipe_id"] for payload in payloads] == [101, 102, 103, 104, 105, 106]
    assert payloads[0]["taxonomy"]["taste_mood"] == ["cozy_dinner"]
    assert payloads[1]["taxonomy"]["dish_type"] == ["pasta"]
    assert "Progress" in result.stdout
    assert "1/6" in result.stdout
    assert "6/6" in result.stdout
    assert "Taxonomy Item Structuring Batch" in result.stdout


def test_structure_taxonomy_batch_cli_can_include_evidence(tmp_path: Path, monkeypatch) -> None:
    recipes_path, neighbors_path, taxonomy_path = _write_projection_inputs(tmp_path)
    out_path = tmp_path / "structured_items_with_evidence.jsonl"
    monkeypatch.setattr(
        "sid_reco.taxonomy.item_projection.MLXTextGenerator",
        _ProjectionGenerator,
    )

    result = runner.invoke(
        app,
        [
            "structure-taxonomy-batch",
            "--recipes-path",
            str(recipes_path),
            "--neighbor-context-path",
            str(neighbors_path),
            "--taxonomy-dictionary-path",
            str(taxonomy_path),
            "--out-path",
            str(out_path),
            "--include-evidence",
        ],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(out_path.read_text(encoding="utf-8").splitlines()[0])
    assert payload["evidence"]["target_item"]["name"] == "Tomato Soup"
    assert payload["evidence"]["neighbors"][0]["neighbor_recipe_id"] == 102


def _write_projection_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
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

    neighbor_rows = []
    ordered_neighbors_by_source = {
        101: [102, 103, 104, 105, 106],
        102: [101, 103, 104, 105, 106],
        103: [101, 102, 104, 105, 106],
        104: [101, 102, 103, 105, 106],
        105: [101, 102, 103, 104, 106],
        106: [101, 102, 103, 104, 105],
    }
    for source_recipe_id, ordered_neighbors in ordered_neighbors_by_source.items():
        for rank, neighbor_recipe_id in enumerate(ordered_neighbors, start=1):
            neighbor_rows.append(
                {
                    "source_recipe_id": source_recipe_id,
                    "neighbor_rank": rank,
                    "neighbor_recipe_id": neighbor_recipe_id,
                    "cosine_similarity": 0.9 - (rank * 0.01),
                }
            )
    pd.DataFrame(neighbor_rows).to_csv(neighbors_path, index=False)

    taxonomy_path.write_text(
        json.dumps(
            {
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
