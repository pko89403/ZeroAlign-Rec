import json
from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from sid_reco.cli import app

runner = CliRunner()


class _FakeEncoder:
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id

    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            score = float(sum(ord(char) for char in text) % 97)
            vectors.append([score + 1.0, float(len(text.split())) + 1.0, float(len(text)) + 1.0])
        return vectors


def test_build_taxonomy_step1_cli_writes_outputs(tmp_path: Path, monkeypatch) -> None:
    recipes_path = tmp_path / "recipes.csv"
    out_dir = tmp_path / "taxonomy_step1"
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
                "description": "Tomato pasta dinner.",
                "tags": json.dumps(["pasta", "easy"]),
                "ingredients": json.dumps(["tomato", "pasta"]),
            },
            {
                "recipe_id": 103,
                "name": "Green Salad",
                "description": "Fresh salad bowl.",
                "tags": json.dumps(["salad", "fresh"]),
                "ingredients": json.dumps(["lettuce", "olive oil"]),
            },
        ]
    ).to_csv(recipes_path, index=False)

    monkeypatch.setattr("sid_reco.taxonomy.step1.MLXEmbeddingEncoder", _FakeEncoder)

    result = runner.invoke(
        app,
        [
            "build-taxonomy-step1",
            "--recipes-path",
            str(recipes_path),
            "--out-dir",
            str(out_dir),
            "--top-k",
            "2",
            "--batch-size",
            "2",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (out_dir / "items_with_embeddings.csv").exists()
    assert (out_dir / "neighbor_context.csv").exists()
    assert (out_dir / "id_map.csv").exists()
    assert (out_dir / "item_index.faiss").exists()
    assert (out_dir / "manifest.json").exists()

    items = pd.read_csv(out_dir / "items_with_embeddings.csv")
    neighbors = pd.read_csv(out_dir / "neighbor_context.csv")
    id_map = pd.read_csv(out_dir / "id_map.csv")
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))

    assert len(items) == 3
    assert len(neighbors) == 6
    assert set(id_map["recipe_id"]) == {101, 102, 103}
    assert manifest["top_k"] == 2
    assert manifest["index_type"] == "faiss.IndexFlatIP"
    assert manifest["batching"]["initial_batch_size"] == 2
    assert manifest["item_rows"] == 3
