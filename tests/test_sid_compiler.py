import json
from pathlib import Path

import numpy as np
import pytest

from sid_reco.sid.compiler import (
    ItemSID,
    QuerySID,
    ResidualKMeansLevel,
    TrainedResidualCodebooks,
    build_item_sids,
    load_codebooks,
    train_codebooks,
    write_codebooks,
)


def test_train_codebooks_and_build_item_sids_return_stable_paths_and_metadata() -> None:
    recipe_ids = [40, 10, 20, 30]
    matrix = np.asarray(
        [
            [9.0, 9.0],
            [0.0, 0.0],
            [0.0, 0.1],
            [9.0, 9.1],
        ],
        dtype=np.float32,
    )

    codebooks = train_codebooks(
        matrix,
        branching_factor=2,
        depth=2,
        normalize_residuals=False,
    )
    first = build_item_sids(recipe_ids, matrix, codebooks=codebooks)
    second = build_item_sids(recipe_ids, matrix, codebooks=codebooks)

    assert isinstance(codebooks, TrainedResidualCodebooks)
    assert all(isinstance(item, ItemSID) for item in first)
    assert codebooks.normalize_residuals is False
    assert codebooks.branching_factor == 2
    assert codebooks.depth == 2
    assert codebooks.embedding_dim == 2
    assert [item.recipe_id for item in first] == [40, 10, 20, 30]
    assert [item.sid_path for item in first] == [item.sid_path for item in second]
    assert [item.sid_string for item in first] == [item.sid_string for item in second]
    assert len(codebooks.levels) == 2
    assert codebooks.levels[0].cluster_count == 2
    assert codebooks.levels[0].cluster_sizes == (2, 2)
    assert codebooks.levels[1].cluster_count == 2
    assert codebooks.levels[1].cluster_sizes == (2, 2)
    assert codebooks.levels[0].iteration_count >= 1
    assert codebooks.levels[1].iteration_count >= 1


def test_train_codebooks_collapses_duplicate_vectors_deterministically() -> None:
    recipe_ids = [101, 102, 103]
    matrix = np.asarray(
        [
            [1.0, 1.0],
            [1.0, 1.0],
            [5.0, 5.0],
        ],
        dtype=np.float32,
    )

    codebooks = train_codebooks(
        matrix,
        branching_factor=3,
        depth=2,
        normalize_residuals=False,
    )
    items = build_item_sids(recipe_ids, matrix, codebooks=codebooks)

    assert codebooks.levels[0].cluster_count == 2
    assert codebooks.levels[1].cluster_count == 1
    assert items[0].sid_path == items[1].sid_path
    assert items[0].sid_string == items[1].sid_string


def test_build_item_sids_reuses_normalization_setting() -> None:
    recipe_ids = [1, 2, 3, 4]
    matrix = np.asarray(
        [
            [2.0, 0.0],
            [1.8, 0.2],
            [0.0, 2.0],
            [0.2, 1.8],
        ],
        dtype=np.float32,
    )

    normalized_codebooks = train_codebooks(
        matrix,
        branching_factor=2,
        depth=2,
        normalize_residuals=True,
    )
    raw_codebooks = train_codebooks(
        matrix,
        branching_factor=2,
        depth=2,
        normalize_residuals=False,
    )

    build_item_sids(recipe_ids, matrix, codebooks=normalized_codebooks)
    build_item_sids(recipe_ids, matrix, codebooks=raw_codebooks)

    assert normalized_codebooks.levels[0].centroids.shape == (2, 2)
    assert raw_codebooks.levels[0].centroids.shape == (2, 2)
    assert normalized_codebooks.levels[0].centroids.dtype == np.float32
    assert raw_codebooks.levels[0].centroids.dtype == np.float32


def test_train_codebooks_and_build_item_sids_reject_invalid_inputs() -> None:
    matrix = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)

    with pytest.raises(ValueError, match="branching_factor must be at least 1"):
        train_codebooks(matrix, branching_factor=0)
    with pytest.raises(ValueError, match="depth must be at least 1"):
        train_codebooks(matrix, depth=0)
    with pytest.raises(ValueError, match="Embedding matrix must be a non-empty 2D matrix"):
        train_codebooks(np.asarray([1.0, 2.0], dtype=np.float32))
    with pytest.raises(ValueError, match="Recipe ID count must match"):
        build_item_sids(
            [1],
            matrix,
            codebooks=train_codebooks(matrix, branching_factor=2, depth=2),
        )


def test_item_sid_and_query_sid_are_independent_dataclasses() -> None:
    item = ItemSID(sid_path=(0, 1), sid_string="<0>-<1>", recipe_id=42)
    query = QuerySID(sid_path=(0, 1), sid_string="<0>-<1>")

    assert item.recipe_id == 42
    assert item.sid_path == query.sid_path
    assert item.sid_string == query.sid_string
    assert not isinstance(query, ItemSID)
    assert not isinstance(item, QuerySID)


def test_write_and_load_codebooks_round_trip(tmp_path: Path) -> None:
    matrix = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.8, 0.2, 0.0],
            [0.1, 0.9, 0.0],
        ],
        dtype=np.float32,
    )
    original = train_codebooks(matrix, branching_factor=2, depth=2, normalize_residuals=True)

    npz_path, manifest_path = write_codebooks(original, out_dir=tmp_path)

    assert npz_path == tmp_path / "residual_codebooks.npz"
    assert manifest_path == tmp_path / "residual_codebooks_manifest.json"
    assert npz_path.exists()
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest == {
        "branching_factor": original.branching_factor,
        "codebooks_path": "residual_codebooks.npz",
        "depth": original.depth,
        "embedding_dim": original.embedding_dim,
        "level_cluster_counts": [level.cluster_count for level in original.levels],
        "normalize_residuals": original.normalize_residuals,
    }

    loaded = load_codebooks(npz_path)
    assert loaded.branching_factor == original.branching_factor
    assert loaded.depth == original.depth
    assert loaded.embedding_dim == original.embedding_dim
    assert loaded.normalize_residuals == original.normalize_residuals
    assert len(loaded.levels) == len(original.levels)
    for loaded_level, original_level in zip(loaded.levels, original.levels, strict=True):
        assert loaded_level.level == original_level.level
        assert loaded_level.cluster_count == original_level.cluster_count
        assert loaded_level.cluster_sizes == original_level.cluster_sizes
        assert loaded_level.iteration_count == original_level.iteration_count
        assert loaded_level.inertia == pytest.approx(original_level.inertia, abs=1e-6)
        assert np.allclose(loaded_level.centroids, original_level.centroids)
        assert loaded_level.centroids.dtype == np.float32


def test_load_codebooks_reproduces_assignment(tmp_path: Path) -> None:
    recipe_ids = [101, 102, 103, 104]
    matrix = np.asarray(
        [
            [2.0, 0.0, 0.0],
            [0.0, 2.0, 0.0],
            [0.0, 0.0, 2.0],
            [1.0, 1.0, 0.0],
        ],
        dtype=np.float32,
    )
    original = train_codebooks(matrix, branching_factor=3, depth=2, normalize_residuals=False)
    original_items = build_item_sids(recipe_ids, matrix, codebooks=original)

    npz_path, _ = write_codebooks(original, out_dir=tmp_path)
    loaded = load_codebooks(npz_path)
    reloaded_items = build_item_sids(recipe_ids, matrix, codebooks=loaded)

    assert [item.sid_path for item in reloaded_items] == [item.sid_path for item in original_items]
    assert [item.sid_string for item in reloaded_items] == [
        item.sid_string for item in original_items
    ]


def test_load_codebooks_raises_on_missing_npz(tmp_path: Path) -> None:
    missing = tmp_path / "residual_codebooks.npz"
    with pytest.raises(FileNotFoundError, match="Missing codebook NPZ"):
        load_codebooks(missing)


def test_load_codebooks_raises_on_missing_manifest(tmp_path: Path) -> None:
    matrix = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    codebooks = train_codebooks(matrix, branching_factor=2, depth=1)
    npz_path, manifest_path = write_codebooks(codebooks, out_dir=tmp_path)
    manifest_path.unlink()

    with pytest.raises(FileNotFoundError, match="Missing codebook manifest"):
        load_codebooks(npz_path)


def test_load_codebooks_raises_on_manifest_field_mismatch(tmp_path: Path) -> None:
    matrix = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    codebooks = train_codebooks(matrix, branching_factor=2, depth=1)
    npz_path, manifest_path = write_codebooks(codebooks, out_dir=tmp_path)

    tampered = json.loads(manifest_path.read_text(encoding="utf-8"))
    tampered["embedding_dim"] = 999
    manifest_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="embedding_dim"):
        load_codebooks(npz_path)


def test_load_codebooks_raises_on_manifest_missing_field(tmp_path: Path) -> None:
    matrix = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    codebooks = train_codebooks(matrix, branching_factor=2, depth=1)
    npz_path, manifest_path = write_codebooks(codebooks, out_dir=tmp_path)

    tampered = json.loads(manifest_path.read_text(encoding="utf-8"))
    del tampered["level_cluster_counts"]
    manifest_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="level_cluster_counts"):
        load_codebooks(npz_path)


def test_load_codebooks_raises_on_truncated_npz(tmp_path: Path) -> None:
    matrix = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    codebooks = train_codebooks(matrix, branching_factor=2, depth=2)
    npz_path, _ = write_codebooks(codebooks, out_dir=tmp_path)

    with np.load(npz_path) as data:
        partial = {
            name: np.asarray(data[name]) for name in data.files if not name.startswith("level_2_")
        }
    np.savez(npz_path, **partial)

    with pytest.raises(ValueError, match="level_2"):
        load_codebooks(npz_path)


def test_codebook_manifest_uses_relative_path(tmp_path: Path) -> None:
    matrix = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    codebooks = train_codebooks(matrix, branching_factor=2, depth=1)
    _, manifest_path = write_codebooks(codebooks, out_dir=tmp_path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["codebooks_path"] == "residual_codebooks.npz"


def test_residual_kmeans_level_dataclass_is_usable_directly() -> None:
    level = ResidualKMeansLevel(
        level=1,
        cluster_count=1,
        centroids=np.zeros((1, 2), dtype=np.float32),
        cluster_sizes=(1,),
        iteration_count=1,
        inertia=0.0,
    )
    assert level.level == 1
