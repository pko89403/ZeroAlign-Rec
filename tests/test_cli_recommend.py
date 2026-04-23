import json
from pathlib import Path

import numpy as np
from typer.testing import CliRunner

from sid_reco.cli import app
from sid_reco.config import Settings
from sid_reco.sid.compiler import ItemSID, ResidualKMeansLevel, TrainedResidualCodebooks
from sid_reco.sid.embed_backend import EmbeddedSIDItems
from sid_reco.sid.indexing import write_sid_index_outputs
from sid_reco.sid.serialization import SerializedSIDItem, write_serialized_items
from sid_reco.sid.stats import build_recommendation_stats, write_recommendation_stats

runner = CliRunner()


def test_recommend_cli_returns_ranked_items(tmp_path: Path, monkeypatch) -> None:
    bundle = _write_recommendation_bundle(tmp_path)
    settings = Settings(
        project_root=tmp_path,
        llm_backend="mlx",
        llm_model="test-llm-model",
        embed_model="test-embed-model",
        sid_catalog_path=bundle["catalog_path"],
        sid_cache_dir=tmp_path / "sid_cache",
        llm_max_tokens=256,
        llm_temperature=0.0,
        llm_top_p=1.0,
    )

    monkeypatch.setattr("sid_reco.cli.Settings.from_env", lambda: settings)
    monkeypatch.setattr(
        "sid_reco.cli.MLXTextGenerator.from_settings",
        lambda resolved_settings: _FakeGenerator(),
    )
    monkeypatch.setattr(
        "sid_reco.cli.MLXEmbeddingEncoder.from_settings",
        lambda resolved_settings: _FakeEncoder(),
    )

    result = runner.invoke(
        app,
        [
            "recommend",
            "--query",
            "Need italian dinner ideas",
            "--hard-filter",
            "course=dinner",
            "--top-k",
            "2",
            "--sid-index-dir",
            str(bundle["sid_index_dir"]),
            "--taxonomy-dictionary-path",
            str(bundle["taxonomy_path"]),
            "--stats-store-path",
            str(bundle["stats_path"]),
            "--fewshot-store-path",
            str(bundle["casebank_path"]),
            "--catalog-path",
            str(bundle["catalog_path"]),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "Recommendation Results" in result.stdout
    assert "Tomato Pasta" in result.stdout
    assert "Veggie Pasta" in result.stdout
    assert "Top candidate support: 3/3" in result.stdout


class _FakeEncoder:
    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            if "course: dinner, cuisine: italian" == text:
                vectors.append([1.0, 0.0, 0.0])
            elif "course: dinner, cuisine: american" == text:
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.5, 0.5, 0.0])
        return vectors


class _FakeGenerator:
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
        if "Build a taxonomy-guided interest sketch" in prompt:
            return json.dumps(
                {
                    "summary": "italian dinner",
                    "positive_facets": ["italian", "dinner"],
                    "negative_facets": [],
                    "ambiguity_notes": [],
                    "taxonomy_values": {
                        "course": ["dinner"],
                        "cuisine": ["italian"],
                    },
                }
            )
        if "Rerank the provided candidates" in prompt:
            candidates = _extract_json_block(prompt, "Candidates:\n")
            candidate_index_by_recipe = {
                int(candidate["recipe_id"]): int(candidate["candidate_index"])
                for candidate in candidates
            }
            first_index = candidate_index_by_recipe[101]
            second_index = candidate_index_by_recipe[103]
            return json.dumps(
                {
                    "ranked_candidate_indices": [first_index, second_index],
                    "candidate_rationales": [
                        {
                            "candidate_index": first_index,
                            "reason": "Best semantic fit. Strong dinner alignment.",
                            "matched_preferences": ["italian", "dinner"],
                            "tradeoffs_or_caveats": [],
                        },
                        {
                            "candidate_index": second_index,
                            "reason": "Good backup. Vegetarian option.",
                            "matched_preferences": ["dinner"],
                            "tradeoffs_or_caveats": ["less_specific"],
                        },
                    ],
                }
            )
        raise AssertionError(f"Unexpected prompt: {prompt}")


def _extract_json_block(prompt: str, marker: str) -> list[dict[str, object]]:
    start = prompt.index(marker) + len(marker)
    end = prompt.index("\nOutput JSON shape:")
    payload = json.loads(prompt[start:end])
    assert isinstance(payload, list)
    return payload


def _write_recommendation_bundle(tmp_path: Path) -> dict[str, Path]:
    sid_index_dir = tmp_path / "sid_index"
    taxonomy_path = tmp_path / "food_taxonomy_dictionary.json"
    interactions_path = tmp_path / "interactions.csv"
    casebank_path = tmp_path / "recommendation_casebank.jsonl"
    catalog_path = tmp_path / "recipes.csv"

    items = [
        SerializedSIDItem(
            recipe_id=101,
            taxonomy={"course": ["dinner"], "cuisine": ["italian"]},
            serialized_text="course: dinner, cuisine: italian",
        ),
        SerializedSIDItem(
            recipe_id=102,
            taxonomy={"course": ["lunch"], "cuisine": ["american"]},
            serialized_text="course: lunch, cuisine: american",
        ),
        SerializedSIDItem(
            recipe_id=103,
            taxonomy={
                "course": ["dinner"],
                "cuisine": ["italian"],
                "dietary_style": ["vegetarian"],
            },
            serialized_text="course: dinner, cuisine: italian, dietary_style: vegetarian",
        ),
    ]
    write_serialized_items(items, out_path=sid_index_dir / "serialized_items.jsonl")
    embedded = EmbeddedSIDItems(
        items=items,
        matrix=np.asarray(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.8, 0.2, 0.0],
            ],
            dtype=np.float32,
        ),
        embedding_dim=3,
        model_id="test-embed-model",
    )
    codebooks = TrainedResidualCodebooks(
        branching_factor=2,
        depth=1,
        embedding_dim=3,
        normalize_residuals=True,
        levels=(
            ResidualKMeansLevel(
                level=1,
                cluster_count=2,
                centroids=np.asarray([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32),
                cluster_sizes=(2, 1),
                iteration_count=1,
                inertia=0.0,
            ),
        ),
    )
    sid_items = [
        ItemSID(sid_path=(0,), sid_string="<0>", recipe_id=101),
        ItemSID(sid_path=(1,), sid_string="<1>", recipe_id=102),
        ItemSID(sid_path=(0,), sid_string="<0>", recipe_id=103),
    ]
    write_sid_index_outputs(
        embedded=embedded,
        codebooks=codebooks,
        items=sid_items,
        out_dir=sid_index_dir,
    )
    taxonomy_path.write_text(
        json.dumps(
            {
                "course": ["dinner", "lunch"],
                "cuisine": ["american", "italian"],
                "dietary_style": ["vegetarian"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    interactions_path.write_text(
        "\n".join(
            [
                "user_id,recipe_id,date,rating,review",
                "1,101,2024-01-01,1.0,good",
                "1,102,2024-01-02,1.0,good",
                "2,101,2024-01-03,1.0,good",
                "2,103,2024-01-04,1.0,good",
                "3,102,2024-01-05,1.0,good",
                "3,103,2024-01-06,1.0,good",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    stats = build_recommendation_stats(interactions_path)
    stats_path = sid_index_dir / "recommendation_stats.json"
    write_recommendation_stats(stats, out_path=stats_path)
    casebank_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "case_id": "case-italian",
                        "summary": "italian dinner success",
                        "taxonomy_values": {
                            "course": ["dinner"],
                            "cuisine": ["italian"],
                        },
                        "output_example": {"ranked_candidate_indices": [1, 2]},
                    }
                ),
                json.dumps(
                    {
                        "case_id": "case-american",
                        "summary": "american lunch success",
                        "taxonomy_values": {
                            "course": ["lunch"],
                            "cuisine": ["american"],
                        },
                        "output_example": {"ranked_candidate_indices": [2, 1]},
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    catalog_path.write_text(
        "\n".join(
            [
                "recipe_id,name,description,tags,ingredients",
                '101,"Tomato Pasta","desc","[""tag""]","[""ingredient""]"',
                '102,"Burger Lunch","desc","[""tag""]","[""ingredient""]"',
                '103,"Veggie Pasta","desc","[""tag""]","[""ingredient""]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "sid_index_dir": sid_index_dir,
        "taxonomy_path": taxonomy_path,
        "stats_path": stats_path,
        "casebank_path": casebank_path,
        "catalog_path": catalog_path,
    }
