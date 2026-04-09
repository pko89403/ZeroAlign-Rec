"""Deterministic residual K-means compilation for SID paths."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatMatrix = NDArray[np.float32]
IntVector = NDArray[np.int32]


@dataclass(frozen=True, slots=True)
class CompiledSIDItem:
    """One recipe ID paired with a compiled hierarchical SID path."""

    recipe_id: int
    sid_path: tuple[int, ...]
    sid_string: str


@dataclass(frozen=True, slots=True)
class ResidualKMeansLevel:
    """Replay/debug metadata for one residual K-means level."""

    level: int
    cluster_count: int
    centroids: FloatMatrix
    cluster_sizes: tuple[int, ...]
    iteration_count: int
    inertia: float


@dataclass(frozen=True, slots=True)
class TrainedResidualCodebooks:
    """Trained residual codebooks that can be reused for deterministic SID assignment."""

    branching_factor: int
    depth: int
    embedding_dim: int
    normalize_residuals: bool
    levels: tuple[ResidualKMeansLevel, ...]


@dataclass(frozen=True, slots=True)
class CompiledSIDItems:
    """Compiled hierarchical SIDs plus residual K-means metadata."""

    items: list[CompiledSIDItem]
    branching_factor: int
    depth: int
    embedding_dim: int
    levels: tuple[ResidualKMeansLevel, ...]


@dataclass(frozen=True, slots=True)
class _KMeansFit:
    labels: IntVector
    centroids: FloatMatrix
    iteration_count: int
    inertia: float


def compile_residual_kmeans(
    recipe_ids: list[int],
    matrix: FloatMatrix,
    *,
    branching_factor: int = 256,
    depth: int = 3,
    normalize_residuals: bool = True,
    max_iter: int = 50,
    tolerance: float = 1e-6,
) -> CompiledSIDItems:
    """Train residual codebooks and immediately assign hierarchical SID paths."""
    codebooks = train_residual_codebooks(
        matrix,
        branching_factor=branching_factor,
        depth=depth,
        normalize_residuals=normalize_residuals,
        max_iter=max_iter,
        tolerance=tolerance,
    )
    return assign_trained_residual_kmeans(recipe_ids, matrix, codebooks=codebooks)


def train_residual_codebooks(
    matrix: FloatMatrix,
    *,
    branching_factor: int = 256,
    depth: int = 3,
    normalize_residuals: bool = True,
    max_iter: int = 50,
    tolerance: float = 1e-6,
) -> TrainedResidualCodebooks:
    """Train deterministic residual codebooks in a GRID-style layer-wise flow."""
    embeddings = _validate_embedding_matrix(matrix)
    _validate_compile_settings(
        branching_factor=branching_factor,
        depth=depth,
        max_iter=max_iter,
        tolerance=tolerance,
    )

    current_residuals = embeddings.copy()
    levels: list[ResidualKMeansLevel] = []
    for level_index in range(depth):
        level_inputs = _prepare_level_inputs(
            current_residuals,
            normalize_residuals=normalize_residuals,
        )
        fit = _fit_deterministic_kmeans(
            level_inputs,
            branching_factor=branching_factor,
            max_iter=max_iter,
            tolerance=tolerance,
        )
        cluster_sizes = np.bincount(fit.labels, minlength=int(fit.centroids.shape[0]))
        levels.append(
            ResidualKMeansLevel(
                level=level_index + 1,
                cluster_count=int(fit.centroids.shape[0]),
                centroids=fit.centroids,
                cluster_sizes=tuple(int(size) for size in cluster_sizes.tolist()),
                iteration_count=fit.iteration_count,
                inertia=fit.inertia,
            )
        )
        current_residuals = level_inputs - fit.centroids[fit.labels]

    return TrainedResidualCodebooks(
        branching_factor=branching_factor,
        depth=depth,
        embedding_dim=int(embeddings.shape[1]),
        normalize_residuals=normalize_residuals,
        levels=tuple(levels),
    )


def assign_trained_residual_kmeans(
    recipe_ids: list[int],
    matrix: FloatMatrix,
    *,
    codebooks: TrainedResidualCodebooks,
) -> CompiledSIDItems:
    """Assign hierarchical SID paths using previously trained residual codebooks."""
    embeddings = _validate_embedding_matrix(matrix)
    if len(recipe_ids) != int(embeddings.shape[0]):
        raise ValueError("Recipe ID count must match the embedding matrix row count.")
    if codebooks.embedding_dim != int(embeddings.shape[1]):
        raise ValueError("Embedding dimension must match the trained codebooks.")
    if len(codebooks.levels) != codebooks.depth:
        raise ValueError("Trained codebooks depth must match the number of stored levels.")

    current_residuals = embeddings.copy()
    sid_paths: list[list[int]] = [[] for _ in recipe_ids]
    for level in codebooks.levels:
        level_inputs = _prepare_level_inputs(
            current_residuals,
            normalize_residuals=codebooks.normalize_residuals,
        )
        labels = _assign_to_centroids(level_inputs, level.centroids)
        for row_index, label in enumerate(labels.tolist()):
            sid_paths[row_index].append(int(label))
        current_residuals = level_inputs - level.centroids[labels]

    items = [
        CompiledSIDItem(
            recipe_id=int(recipe_id),
            sid_path=tuple(path),
            sid_string=_format_sid(path),
        )
        for recipe_id, path in zip(recipe_ids, sid_paths, strict=True)
    ]
    return CompiledSIDItems(
        items=items,
        branching_factor=codebooks.branching_factor,
        depth=codebooks.depth,
        embedding_dim=codebooks.embedding_dim,
        levels=codebooks.levels,
    )


def _fit_deterministic_kmeans(
    samples: FloatMatrix,
    *,
    branching_factor: int,
    max_iter: int,
    tolerance: float,
) -> _KMeansFit:
    unique_rows = np.unique(samples, axis=0)
    target_clusters = min(branching_factor, int(unique_rows.shape[0]))
    centroids = _initialize_centroids(unique_rows, target_clusters)

    previous_labels: IntVector | None = None
    previous_centroids: FloatMatrix | None = None
    iteration_count = 0

    for iteration in range(1, max_iter + 1):
        iteration_count = iteration
        distances = _pairwise_squared_distances(samples, centroids)
        raw_labels = np.argmin(distances, axis=1).astype(np.int32)
        used_cluster_ids = np.unique(raw_labels)
        compact_labels = np.searchsorted(used_cluster_ids, raw_labels).astype(np.int32)
        compact_centroids = np.asarray(
            [
                samples[raw_labels == cluster_id].mean(axis=0, dtype=np.float64)
                for cluster_id in used_cluster_ids.tolist()
            ],
            dtype=np.float32,
        )
        labels, centroids = _canonicalize_clusters(compact_labels, compact_centroids)
        if (
            previous_labels is not None
            and previous_centroids is not None
            and np.array_equal(labels, previous_labels)
            and _centroids_close(centroids, previous_centroids, tolerance=tolerance)
        ):
            break
        previous_labels = labels.copy()
        previous_centroids = centroids.copy()

    distances = _pairwise_squared_distances(samples, centroids)
    inertia = float(np.sum(distances[np.arange(len(samples)), labels], dtype=np.float64))
    return _KMeansFit(
        labels=labels,
        centroids=centroids,
        iteration_count=iteration_count,
        inertia=inertia,
    )


def _validate_embedding_matrix(matrix: FloatMatrix) -> FloatMatrix:
    embeddings = np.asarray(matrix, dtype=np.float32)
    if embeddings.ndim != 2 or embeddings.shape[0] == 0 or embeddings.shape[1] == 0:
        raise ValueError("Embedding matrix must be a non-empty 2D matrix.")
    return embeddings


def _validate_compile_settings(
    *,
    branching_factor: int,
    depth: int,
    max_iter: int,
    tolerance: float,
) -> None:
    if branching_factor < 1:
        raise ValueError("branching_factor must be at least 1.")
    if depth < 1:
        raise ValueError("depth must be at least 1.")
    if max_iter < 1:
        raise ValueError("max_iter must be at least 1.")
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative.")


def _prepare_level_inputs(
    residuals: FloatMatrix,
    *,
    normalize_residuals: bool,
) -> FloatMatrix:
    if not normalize_residuals:
        return residuals
    norms = np.linalg.norm(residuals, axis=1, keepdims=True)
    normalized = residuals.copy()
    nonzero_rows = norms[:, 0] > 0
    normalized[nonzero_rows] = residuals[nonzero_rows] / norms[nonzero_rows]
    return normalized.astype(np.float32, copy=False)


def _assign_to_centroids(samples: FloatMatrix, centroids: FloatMatrix) -> IntVector:
    distances = _pairwise_squared_distances(samples, centroids)
    return np.asarray(np.argmin(distances, axis=1), dtype=np.int32)


def _initialize_centroids(unique_rows: FloatMatrix, cluster_count: int) -> FloatMatrix:
    centroids = [unique_rows[0]]
    while len(centroids) < cluster_count:
        current = np.asarray(centroids, dtype=np.float32)
        distances = _pairwise_squared_distances(unique_rows, current)
        min_distances = distances.min(axis=1)
        next_index = int(np.argmax(min_distances))
        centroids.append(unique_rows[next_index])
    return np.asarray(centroids, dtype=np.float32)


def _canonicalize_clusters(
    labels: IntVector,
    centroids: FloatMatrix,
) -> tuple[IntVector, FloatMatrix]:
    order = _lexsort_rows(centroids)
    sorted_centroids = centroids[order]
    label_remap = np.empty(len(order), dtype=np.int32)
    label_remap[order] = np.arange(len(order), dtype=np.int32)
    sorted_labels = label_remap[labels]
    return sorted_labels, sorted_centroids


def _pairwise_squared_distances(
    samples: FloatMatrix,
    centroids: FloatMatrix,
) -> NDArray[np.float32]:
    deltas = samples[:, np.newaxis, :] - centroids[np.newaxis, :, :]
    return np.asarray(np.sum(deltas * deltas, axis=2, dtype=np.float32), dtype=np.float32)


def _lexsort_rows(matrix: FloatMatrix) -> NDArray[np.intp]:
    ordered_indices = sorted(
        range(int(matrix.shape[0])),
        key=lambda index: (
            tuple(float(value) for value in matrix[index].tolist()),
            index,
        ),
    )
    return np.asarray(ordered_indices, dtype=np.intp)


def _centroids_close(
    left: FloatMatrix,
    right: FloatMatrix,
    *,
    tolerance: float,
) -> bool:
    return left.shape == right.shape and bool(np.allclose(left, right, atol=tolerance, rtol=0.0))


def _format_sid(sid_path: list[int]) -> str:
    return "-".join(f"<{level_id}>" for level_id in sid_path)
