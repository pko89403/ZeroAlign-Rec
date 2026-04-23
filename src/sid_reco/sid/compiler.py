"""Deterministic residual K-means compilation for SID paths."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

FloatMatrix = NDArray[np.float32]
IntVector = NDArray[np.int32]

_CODEBOOKS_NPZ_FILENAME = "residual_codebooks.npz"
_CODEBOOKS_MANIFEST_FILENAME = "residual_codebooks_manifest.json"
_REMEDIATION = (
    "Re-run `uv run sid-reco compile-sid-index --out-dir {dir}` to regenerate the codebooks."
)


@dataclass(frozen=True, slots=True)
class ItemSID:
    """Hierarchical SID assignment for one catalog item."""

    sid_path: tuple[int, ...]
    sid_string: str
    recipe_id: int


@dataclass(frozen=True, slots=True)
class QuerySID:
    """Hierarchical SID assignment for one runtime query vector."""

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
    """Trained residual codebooks that define the SID coordinate space."""

    branching_factor: int
    depth: int
    embedding_dim: int
    normalize_residuals: bool
    levels: tuple[ResidualKMeansLevel, ...]


@dataclass(frozen=True, slots=True)
class _KMeansFit:
    labels: IntVector
    centroids: FloatMatrix
    iteration_count: int
    inertia: float


def train_codebooks(
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


def build_item_sids(
    recipe_ids: list[int],
    matrix: FloatMatrix,
    *,
    codebooks: TrainedResidualCodebooks,
) -> list[ItemSID]:
    """Assign hierarchical SID paths to catalog items using trained codebooks."""
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

    return [
        ItemSID(
            sid_path=tuple(path),
            sid_string=_format_sid(path),
            recipe_id=int(recipe_id),
        )
        for recipe_id, path in zip(recipe_ids, sid_paths, strict=True)
    ]


def write_codebooks(
    codebooks: TrainedResidualCodebooks,
    *,
    out_dir: Path,
) -> tuple[Path, Path]:
    """Persist trained residual codebooks as NPZ + sibling manifest."""
    if len(codebooks.levels) != codebooks.depth:
        raise ValueError("Trained codebooks depth must match the number of stored levels.")
    out_dir.mkdir(parents=True, exist_ok=True)
    npz_path = out_dir / _CODEBOOKS_NPZ_FILENAME
    manifest_path = out_dir / _CODEBOOKS_MANIFEST_FILENAME

    payload: dict[str, np.ndarray] = {
        "branching_factor": np.asarray(codebooks.branching_factor, dtype=np.int32),
        "depth": np.asarray(codebooks.depth, dtype=np.int32),
        "embedding_dim": np.asarray(codebooks.embedding_dim, dtype=np.int32),
        "normalize_residuals": np.asarray(int(codebooks.normalize_residuals), dtype=np.int32),
    }
    for level in codebooks.levels:
        prefix = f"level_{level.level}"
        payload[f"{prefix}_centroids"] = level.centroids.astype(np.float32, copy=False)
        payload[f"{prefix}_cluster_sizes"] = np.asarray(level.cluster_sizes, dtype=np.int32)
        payload[f"{prefix}_iteration_count"] = np.asarray(level.iteration_count, dtype=np.int32)
        payload[f"{prefix}_inertia"] = np.asarray(level.inertia, dtype=np.float32)
    np.savez(npz_path, **payload)  # type: ignore[arg-type]

    manifest_path.write_text(
        json.dumps(
            {
                "branching_factor": codebooks.branching_factor,
                "codebooks_path": _CODEBOOKS_NPZ_FILENAME,
                "depth": codebooks.depth,
                "embedding_dim": codebooks.embedding_dim,
                "level_cluster_counts": [level.cluster_count for level in codebooks.levels],
                "normalize_residuals": codebooks.normalize_residuals,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return npz_path, manifest_path


def load_codebooks(npz_path: Path) -> TrainedResidualCodebooks:
    """Load residual codebooks from NPZ and validate against the sibling manifest."""
    if not npz_path.exists():
        raise FileNotFoundError(
            f"Missing codebook NPZ at {npz_path}. " + _REMEDIATION.format(dir=npz_path.parent)
        )
    manifest_path = npz_path.with_name(_CODEBOOKS_MANIFEST_FILENAME)
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Missing codebook manifest at {manifest_path}. "
            + _REMEDIATION.format(dir=npz_path.parent)
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with np.load(npz_path) as data:
        keys = set(data.files)
        for required_scalar in (
            "branching_factor",
            "depth",
            "embedding_dim",
            "normalize_residuals",
        ):
            if required_scalar not in keys:
                raise ValueError(
                    f"Codebook NPZ at {npz_path} is missing `{required_scalar}`. "
                    + _REMEDIATION.format(dir=npz_path.parent)
                )
        branching_factor = int(data["branching_factor"].item())
        depth = int(data["depth"].item())
        embedding_dim = int(data["embedding_dim"].item())
        normalize_residuals = bool(int(data["normalize_residuals"].item()))

        levels: list[ResidualKMeansLevel] = []
        level_cluster_counts: list[int] = []
        for level_index in range(1, depth + 1):
            prefix = f"level_{level_index}"
            for suffix in ("centroids", "cluster_sizes", "iteration_count", "inertia"):
                key = f"{prefix}_{suffix}"
                if key not in keys:
                    raise ValueError(
                        f"Codebook NPZ at {npz_path} is missing `{key}`. "
                        + _REMEDIATION.format(dir=npz_path.parent)
                    )
            centroids = np.asarray(data[f"{prefix}_centroids"], dtype=np.float32)
            if centroids.ndim != 2 or int(centroids.shape[1]) != embedding_dim:
                raise ValueError(
                    f"Codebook NPZ at {npz_path} has mismatched `{prefix}_centroids` shape "
                    f"{centroids.shape!r} for embedding_dim={embedding_dim}. "
                    + _REMEDIATION.format(dir=npz_path.parent)
                )
            cluster_sizes = tuple(int(value) for value in data[f"{prefix}_cluster_sizes"].tolist())
            iteration_count = int(data[f"{prefix}_iteration_count"].item())
            inertia = float(data[f"{prefix}_inertia"].item())
            levels.append(
                ResidualKMeansLevel(
                    level=level_index,
                    cluster_count=int(centroids.shape[0]),
                    centroids=centroids,
                    cluster_sizes=cluster_sizes,
                    iteration_count=iteration_count,
                    inertia=inertia,
                )
            )
            level_cluster_counts.append(int(centroids.shape[0]))

    _validate_manifest_against_npz(
        manifest=manifest,
        npz_path=npz_path,
        branching_factor=branching_factor,
        depth=depth,
        embedding_dim=embedding_dim,
        normalize_residuals=normalize_residuals,
        level_cluster_counts=level_cluster_counts,
    )

    return TrainedResidualCodebooks(
        branching_factor=branching_factor,
        depth=depth,
        embedding_dim=embedding_dim,
        normalize_residuals=normalize_residuals,
        levels=tuple(levels),
    )


def _validate_manifest_against_npz(
    *,
    manifest: object,
    npz_path: Path,
    branching_factor: int,
    depth: int,
    embedding_dim: int,
    normalize_residuals: bool,
    level_cluster_counts: list[int],
) -> None:
    if not isinstance(manifest, dict):
        raise ValueError(
            f"Codebook manifest at {npz_path.parent} must be a JSON object. "
            + _REMEDIATION.format(dir=npz_path.parent)
        )
    field_expectations: dict[str, object] = {
        "branching_factor": branching_factor,
        "depth": depth,
        "embedding_dim": embedding_dim,
        "normalize_residuals": normalize_residuals,
        "level_cluster_counts": level_cluster_counts,
    }
    for field, expected in field_expectations.items():
        if field not in manifest:
            raise ValueError(
                f"Codebook manifest at {npz_path.parent} is missing `{field}`. "
                + _REMEDIATION.format(dir=npz_path.parent)
            )
        if manifest[field] != expected:
            raise ValueError(
                f"Codebook manifest `{field}` ({manifest[field]!r}) does not match "
                f"NPZ value ({expected!r}) at {npz_path}. "
                + _REMEDIATION.format(dir=npz_path.parent)
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
