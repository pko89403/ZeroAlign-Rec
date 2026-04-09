import numpy as np
import pytest

from sid_reco.sid.compiler import (
    CompiledSIDItems,
    TrainedResidualCodebooks,
    assign_trained_residual_kmeans,
    compile_residual_kmeans,
    train_residual_codebooks,
)


def test_train_residual_codebooks_and_assign_ids_return_stable_sid_paths_and_metadata() -> None:
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

    codebooks = train_residual_codebooks(
        matrix,
        branching_factor=2,
        depth=2,
        normalize_residuals=False,
    )
    first = assign_trained_residual_kmeans(recipe_ids, matrix, codebooks=codebooks)
    second = assign_trained_residual_kmeans(recipe_ids, matrix, codebooks=codebooks)
    wrapped = compile_residual_kmeans(
        recipe_ids,
        matrix,
        branching_factor=2,
        depth=2,
        normalize_residuals=False,
    )

    assert isinstance(codebooks, TrainedResidualCodebooks)
    assert isinstance(first, CompiledSIDItems)
    assert codebooks.normalize_residuals is False
    assert codebooks.branching_factor == 2
    assert codebooks.depth == 2
    assert codebooks.embedding_dim == 2
    assert [item.recipe_id for item in first.items] == [40, 10, 20, 30]
    assert [item.sid_path for item in first.items] == [item.sid_path for item in second.items]
    assert [item.sid_path for item in first.items] == [item.sid_path for item in wrapped.items]
    assert [item.sid_string for item in first.items] == [item.sid_string for item in wrapped.items]
    assert first.branching_factor == 2
    assert first.depth == 2
    assert first.embedding_dim == 2
    assert len(first.levels) == 2
    assert first.levels[0].cluster_count == 2
    assert first.levels[0].cluster_sizes == (2, 2)
    assert first.levels[1].cluster_count == 2
    assert first.levels[1].cluster_sizes == (2, 2)
    assert first.levels[0].iteration_count >= 1
    assert first.levels[1].iteration_count >= 1
    assert first.levels[0].inertia == second.levels[0].inertia
    assert np.allclose(first.levels[0].centroids, second.levels[0].centroids)
    assert np.allclose(first.levels[1].centroids, second.levels[1].centroids)


def test_train_residual_codebooks_collapses_duplicate_vectors_deterministically() -> None:
    recipe_ids = [101, 102, 103]
    matrix = np.asarray(
        [
            [1.0, 1.0],
            [1.0, 1.0],
            [5.0, 5.0],
        ],
        dtype=np.float32,
    )

    codebooks = train_residual_codebooks(
        matrix,
        branching_factor=3,
        depth=2,
        normalize_residuals=False,
    )
    compiled = assign_trained_residual_kmeans(recipe_ids, matrix, codebooks=codebooks)

    assert compiled.levels[0].cluster_count == 2
    assert compiled.levels[1].cluster_count == 1
    assert compiled.items[0].sid_path == compiled.items[1].sid_path
    assert compiled.items[0].sid_string == compiled.items[1].sid_string


def test_assign_trained_residual_kmeans_reuses_normalization_setting() -> None:
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

    normalized_codebooks = train_residual_codebooks(
        matrix,
        branching_factor=2,
        depth=2,
        normalize_residuals=True,
    )
    raw_codebooks = train_residual_codebooks(
        matrix,
        branching_factor=2,
        depth=2,
        normalize_residuals=False,
    )

    normalized = assign_trained_residual_kmeans(recipe_ids, matrix, codebooks=normalized_codebooks)
    raw = assign_trained_residual_kmeans(recipe_ids, matrix, codebooks=raw_codebooks)

    assert normalized.levels[0].centroids.shape == (2, 2)
    assert raw.levels[0].centroids.shape == (2, 2)
    assert normalized.levels[0].centroids.dtype == np.float32
    assert raw.levels[0].centroids.dtype == np.float32


def test_train_residual_codebooks_and_assign_reject_invalid_inputs() -> None:
    matrix = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)

    with pytest.raises(ValueError, match="branching_factor must be at least 1"):
        train_residual_codebooks(matrix, branching_factor=0)
    with pytest.raises(ValueError, match="depth must be at least 1"):
        train_residual_codebooks(matrix, depth=0)
    with pytest.raises(ValueError, match="Embedding matrix must be a non-empty 2D matrix"):
        train_residual_codebooks(np.asarray([1.0, 2.0], dtype=np.float32))
    with pytest.raises(ValueError, match="Recipe ID count must match"):
        assign_trained_residual_kmeans(
            [1],
            matrix,
            codebooks=train_residual_codebooks(matrix, branching_factor=2, depth=2),
        )
