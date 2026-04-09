import json
from pathlib import Path

from typer.testing import CliRunner

from sid_reco.cli import app
from sid_reco.config import Settings

runner = CliRunner()


class _FakeEncoder:
    def __init__(self, model_id: str = "test-embed-model") -> None:
        self.model_id = model_id

    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for index, text in enumerate(texts, start=1):
            score = float(sum(ord(char) for char in text) % 97)
            vectors.append(
                [
                    score + float(index),
                    float(len(text.split())) + 1.0,
                    float(len(text)) + 1.0,
                ]
            )
        return vectors


def test_compile_sid_index_cli_writes_all_outputs(tmp_path: Path, monkeypatch) -> None:
    structured_items_path, taxonomy_dictionary_path = _write_sid_inputs(tmp_path)
    out_dir = tmp_path / "sid_index"
    settings = Settings(
        project_root=tmp_path,
        llm_backend="mlx",
        llm_model="test-llm-model",
        embed_model="test-embed-model",
        sid_catalog_path=tmp_path / "catalog.csv",
        sid_cache_dir=tmp_path / "sid_cache",
        llm_max_tokens=256,
        llm_temperature=0.0,
        llm_top_p=1.0,
    )

    monkeypatch.setattr("sid_reco.cli.Settings.from_env", lambda: settings)
    monkeypatch.setattr(
        "sid_reco.sid.embed_backend.MLXEmbeddingEncoder.from_settings",
        lambda resolved_settings: _FakeEncoder(model_id=resolved_settings.embed_model),
    )

    result = runner.invoke(
        app,
        [
            "compile-sid-index",
            "--structured-items-path",
            str(structured_items_path),
            "--taxonomy-dictionary-path",
            str(taxonomy_dictionary_path),
            "--out-dir",
            str(out_dir),
            "--branching-factor",
            "3",
            "--depth",
            "2",
            "--no-normalize-residuals",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "SID Compilation Index" in result.stdout
    assert (out_dir / "serialized_items.jsonl").exists()
    assert (out_dir / "embeddings.npy").exists()
    assert (out_dir / "embedding_manifest.json").exists()
    assert (out_dir / "compiled_sid.jsonl").exists()
    assert (out_dir / "item_to_sid.json").exists()
    assert (out_dir / "sid_to_items.json").exists()
    assert (out_dir / "id_map.jsonl").exists()
    assert (out_dir / "item_index.faiss").exists()
    assert (out_dir / "manifest.json").exists()

    serialized_payloads = [
        json.loads(line)
        for line in (out_dir / "serialized_items.jsonl")
        .read_text(encoding="utf-8")
        .strip()
        .splitlines()
    ]
    assert [payload["recipe_id"] for payload in serialized_payloads] == [101, 102, 103]
    assert serialized_payloads[0]["serialized_text"] == (
        "course: dinner, cuisine: italian, taste_mood: cozy_dinner"
    )

    embedding_manifest = json.loads(
        (out_dir / "embedding_manifest.json").read_text(encoding="utf-8")
    )
    assert embedding_manifest == {
        "embedding_dim": 3,
        "item_count": 3,
        "model_id": "test-embed-model",
    }

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["branching_factor"] == 3
    assert manifest["depth"] == 2
    assert manifest["embedding_dim"] == 3
    assert manifest["item_count"] == 3
    assert len(manifest["level_cluster_counts"]) == 2
    assert manifest["model_id"] == "test-embed-model"

    item_to_sid = json.loads((out_dir / "item_to_sid.json").read_text(encoding="utf-8"))
    assert sorted(item_to_sid) == ["101", "102", "103"]


def test_compile_sid_index_cli_reports_missing_taxonomy_dictionary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    structured_items_path, _ = _write_sid_inputs(tmp_path)
    settings = Settings(
        project_root=tmp_path,
        llm_backend="mlx",
        llm_model="test-llm-model",
        embed_model="test-embed-model",
        sid_catalog_path=tmp_path / "catalog.csv",
        sid_cache_dir=tmp_path / "sid_cache",
        llm_max_tokens=256,
        llm_temperature=0.0,
        llm_top_p=1.0,
    )

    monkeypatch.setattr("sid_reco.cli.Settings.from_env", lambda: settings)

    result = runner.invoke(
        app,
        [
            "compile-sid-index",
            "--structured-items-path",
            str(structured_items_path),
            "--taxonomy-dictionary-path",
            str(tmp_path / "missing-taxonomy.json"),
            "--out-dir",
            str(tmp_path / "sid_index"),
        ],
    )

    assert result.exit_code == 1
    assert "Missing taxonomy dictionary file" in result.stdout


def _write_sid_inputs(tmp_path: Path) -> tuple[Path, Path]:
    structured_items_path = tmp_path / "items.jsonl"
    taxonomy_dictionary_path = tmp_path / "food_taxonomy_dictionary.json"

    structured_items_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "recipe_id": 103,
                        "taxonomy": {
                            "taste_mood": ["cozy_dinner"],
                            "course": ["dinner"],
                            "cuisine": ["italian"],
                        },
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "recipe_id": 101,
                        "taxonomy": {
                            "taste_mood": ["cozy_dinner"],
                            "course": ["dinner"],
                            "cuisine": ["italian"],
                        },
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "recipe_id": 102,
                        "taxonomy": {
                            "taste_mood": ["bright"],
                            "course": ["lunch"],
                            "cuisine": ["american"],
                        },
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    taxonomy_dictionary_path.write_text(
        json.dumps(
            {
                "course": ["breakfast", "lunch", "dinner"],
                "cuisine": ["american", "italian"],
                "taste_mood": ["bright", "cozy_dinner"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return structured_items_path, taxonomy_dictionary_path
