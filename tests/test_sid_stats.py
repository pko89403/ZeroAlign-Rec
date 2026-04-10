import json
from pathlib import Path

import pytest

from sid_reco.sid.stats import build_recommendation_stats, write_recommendation_stats


def test_build_recommendation_stats_counts_popularity_and_cooccurrence(tmp_path: Path) -> None:
    interactions_path = _write_interactions_csv(tmp_path)

    stats = build_recommendation_stats(interactions_path)

    assert stats.interaction_count == 6
    assert stats.user_count == 3
    assert stats.item_count == 3
    assert stats.popularity == {101: 2, 102: 2, 103: 2}
    assert stats.cooccurrence == {
        101: {102: 1, 103: 1},
        102: {101: 1, 103: 1},
        103: {101: 1, 102: 1},
    }


def test_write_recommendation_stats_persists_deterministic_json(tmp_path: Path) -> None:
    interactions_path = _write_interactions_csv(tmp_path)
    stats = build_recommendation_stats(interactions_path)

    summary = write_recommendation_stats(
        stats,
        out_path=tmp_path / "sid_index" / "recommendation_stats.json",
    )

    assert summary.output_path == tmp_path / "sid_index" / "recommendation_stats.json"
    assert summary.interaction_count == 6
    assert summary.user_count == 3
    assert summary.item_count == 3
    assert summary.cooccurrence_pair_count == 3
    assert json.loads(summary.output_path.read_text(encoding="utf-8")) == {
        "cooccurrence": {
            "101": {"102": 1, "103": 1},
            "102": {"101": 1, "103": 1},
            "103": {"101": 1, "102": 1},
        },
        "interaction_count": 6,
        "item_count": 3,
        "popularity": {"101": 2, "102": 2, "103": 2},
        "user_count": 3,
    }


def test_build_recommendation_stats_rejects_missing_columns(tmp_path: Path) -> None:
    interactions_path = tmp_path / "interactions.csv"
    interactions_path.write_text("user_id,date\n1,2024-01-01\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing required interactions columns: recipe_id"):
        build_recommendation_stats(interactions_path)


def _write_interactions_csv(tmp_path: Path) -> Path:
    interactions_path = tmp_path / "interactions.csv"
    interactions_path.write_text(
        "\n".join(
            [
                "user_id,recipe_id,date,rating,review",
                "1,101,2024-01-01,1.0,good",
                "1,102,2024-01-02,1.0,nice",
                "2,101,2024-01-03,1.0,ok",
                "2,103,2024-01-04,1.0,ok",
                "3,102,2024-01-05,1.0,ok",
                "3,103,2024-01-06,1.0,ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return interactions_path
