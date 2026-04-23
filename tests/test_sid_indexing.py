import json
from pathlib import Path

import faiss  # type: ignore[import-untyped]
import numpy as np
import pytest

from sid_reco.sid.compiler import (
    ItemSID,
    ResidualKMeansLevel,
    TrainedResidualCodebooks,
)
from sid_reco.sid.embed_backend import EmbeddedSIDItems
from sid_reco.sid.indexing import write_sid_index_outputs
from sid_reco.sid.serialization import SerializedSIDItem


def test_write_sid_index_outputs_persists_faiss_and_mapping_artifacts(tmp_path: Path) -> None:
    items = [
        SerializedSIDItem(
            recipe_id=101,
            taxonomy={"cuisine": ["american"]},
            serialized_text="cuisine: american",
        ),
        SerializedSIDItem(
            recipe_id=102,
            taxonomy={"cuisine": ["italian"]},
            serialized_text="cuisine: italian",
        ),
        SerializedSIDItem(
            recipe_id=103,
            taxonomy={"cuisine": ["american"]},
            serialized_text="cuisine: american",
        ),
    ]
    embedded = EmbeddedSIDItems(
        items=items,
        matrix=np.asarray(
            [
                [3.0, 0.0, 4.0],
                [0.0, 5.0, 0.0],
                [6.0, 0.0, 8.0],
            ],
            dtype=np.float32,
        ),
        embedding_dim=3,
        model_id="test-embed-model",
    )
    codebooks = TrainedResidualCodebooks(
        branching_factor=2,
        depth=2,
        embedding_dim=3,
        normalize_residuals=True,
        levels=(
            ResidualKMeansLevel(
                level=1,
                cluster_count=2,
                centroids=np.asarray([[0.0, 1.0, 0.0], [1.0, 0.0, 0.0]], dtype=np.float32),
                cluster_sizes=(2, 1),
                iteration_count=3,
                inertia=0.0,
            ),
            ResidualKMeansLevel(
                level=2,
                cluster_count=2,
                centroids=np.asarray([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32),
                cluster_sizes=(1, 2),
                iteration_count=2,
                inertia=0.0,
            ),
        ),
    )
    sid_items = [
        ItemSID(sid_path=(0, 1), sid_string="<0>-<1>", recipe_id=101),
        ItemSID(sid_path=(1, 0), sid_string="<1>-<0>", recipe_id=102),
        ItemSID(sid_path=(0, 1), sid_string="<0>-<1>", recipe_id=103),
    ]

    summary = write_sid_index_outputs(
        embedded=embedded,
        codebooks=codebooks,
        items=sid_items,
        out_dir=tmp_path / "sid_index",
    )

    assert summary.item_count == 3
    assert summary.embedding_dim == 3
    assert summary.compiled_sid_path == tmp_path / "sid_index" / "compiled_sid.jsonl"
    assert summary.item_to_sid_path == tmp_path / "sid_index" / "item_to_sid.json"
    assert summary.sid_to_items_path == tmp_path / "sid_index" / "sid_to_items.json"
    assert summary.id_map_path == tmp_path / "sid_index" / "id_map.jsonl"
    assert summary.index_path == tmp_path / "sid_index" / "item_index.faiss"
    assert summary.manifest_path == tmp_path / "sid_index" / "manifest.json"
    assert summary.codebooks_path == tmp_path / "sid_index" / "residual_codebooks.npz"
    assert (
        summary.codebooks_manifest_path
        == tmp_path / "sid_index" / "residual_codebooks_manifest.json"
    )
    assert summary.codebooks_path.exists()
    assert summary.codebooks_manifest_path.exists()

    compiled_lines = summary.compiled_sid_path.read_text(encoding="utf-8").strip().splitlines()
    assert [json.loads(line) for line in compiled_lines] == [
        {"recipe_id": 101, "sid_path": [0, 1], "sid_string": "<0>-<1>"},
        {"recipe_id": 102, "sid_path": [1, 0], "sid_string": "<1>-<0>"},
        {"recipe_id": 103, "sid_path": [0, 1], "sid_string": "<0>-<1>"},
    ]
    assert json.loads(summary.item_to_sid_path.read_text(encoding="utf-8")) == {
        "101": "<0>-<1>",
        "102": "<1>-<0>",
        "103": "<0>-<1>",
    }
    assert json.loads(summary.sid_to_items_path.read_text(encoding="utf-8")) == {
        "<0>-<1>": [101, 103],
        "<1>-<0>": [102],
    }
    id_map_lines = summary.id_map_path.read_text(encoding="utf-8").strip().splitlines()
    assert [json.loads(line) for line in id_map_lines] == [
        {"faiss_idx": 0, "recipe_id": 101, "sid_path": [0, 1], "sid_string": "<0>-<1>"},
        {"faiss_idx": 1, "recipe_id": 102, "sid_path": [1, 0], "sid_string": "<1>-<0>"},
        {"faiss_idx": 2, "recipe_id": 103, "sid_path": [0, 1], "sid_string": "<0>-<1>"},
    ]
    assert json.loads(summary.manifest_path.read_text(encoding="utf-8")) == {
        "branching_factor": 2,
        "codebooks_manifest_path": "residual_codebooks_manifest.json",
        "codebooks_path": "residual_codebooks.npz",
        "depth": 2,
        "embedding_dim": 3,
        "index_type": "faiss.IndexFlatIP",
        "item_count": 3,
        "level_cluster_counts": [2, 2],
        "model_id": "test-embed-model",
        "normalize_residuals": True,
    }

    index = faiss.read_index(str(summary.index_path))
    assert index.ntotal == 3
    assert index.d == 3


def test_write_sid_index_outputs_rejects_misaligned_recipe_ids(tmp_path: Path) -> None:
    embedded = EmbeddedSIDItems(
        items=[
            SerializedSIDItem(
                recipe_id=101,
                taxonomy={"cuisine": ["american"]},
                serialized_text="cuisine: american",
            )
        ],
        matrix=np.asarray([[1.0, 0.0]], dtype=np.float32),
        embedding_dim=2,
        model_id="test-embed-model",
    )
    codebooks = TrainedResidualCodebooks(
        branching_factor=2,
        depth=1,
        embedding_dim=2,
        normalize_residuals=True,
        levels=(
            ResidualKMeansLevel(
                level=1,
                cluster_count=1,
                centroids=np.asarray([[1.0, 0.0]], dtype=np.float32),
                cluster_sizes=(1,),
                iteration_count=1,
                inertia=0.0,
            ),
        ),
    )
    items = [ItemSID(sid_path=(0,), sid_string="<0>", recipe_id=999)]

    with pytest.raises(ValueError, match="align by recipe_id"):
        write_sid_index_outputs(
            embedded=embedded,
            codebooks=codebooks,
            items=items,
            out_dir=tmp_path / "sid_index",
        )
