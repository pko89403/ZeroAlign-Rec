"""Neighbor-context pipeline for taxonomy item embeddings and nearest-neighbor export."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import faiss  # type: ignore[import-untyped]
import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from numpy.typing import NDArray

from sid_reco.embedding import MLXEmbeddingEncoder

ITEM_METADATA_COLUMNS = ["recipe_id", "name", "description", "tags", "ingredients"]
ITEMS_WITH_EMBEDDINGS_COLUMNS = ITEM_METADATA_COLUMNS + ["embedding_text", "embedding"]
NEIGHBOR_CONTEXT_COLUMNS = [
    "source_recipe_id",
    "neighbor_rank",
    "neighbor_recipe_id",
    "cosine_similarity",
]
DEFAULT_TOP_K = 5
DEFAULT_INITIAL_BATCH_SIZE = 64
DEFAULT_MAX_BATCH_SIZE = 128
DEFAULT_FALLBACK_BATCH_SIZE = 32
MIN_ADAPTIVE_BATCH_SIZE = 8

FloatMatrix = NDArray[np.float32]


@dataclass(frozen=True, slots=True)
class EncodedCatalog:
    """Encoded item table plus runtime batching metadata."""

    items: pd.DataFrame
    embeddings: FloatMatrix
    initial_batch_size: int
    final_batch_size: int
    min_batch_size: int
    detected_total_memory_bytes: int | None


@dataclass(frozen=True, slots=True)
class NeighborContextSummary:
    """High-level summary for the neighbor-context export."""

    items_rows: int
    neighbor_rows: int
    embedding_dim: int
    top_k: int
    initial_batch_size: int
    final_batch_size: int


def load_recipe_catalog(recipes_path: Path) -> pd.DataFrame:
    """Load the processed recipe catalog required for neighbor-context building."""
    if not recipes_path.exists():
        raise FileNotFoundError(f"Missing recipe catalog file: {recipes_path}")

    catalog = pd.read_csv(recipes_path)
    missing = sorted(set(ITEM_METADATA_COLUMNS).difference(catalog.columns))
    if missing:
        raise ValueError(f"Missing required recipe catalog columns: {', '.join(missing)}")

    items = catalog.loc[:, ITEM_METADATA_COLUMNS].copy()
    items["recipe_id"] = pd.to_numeric(items["recipe_id"], errors="coerce")
    items = items.loc[items["recipe_id"].notna()].copy()
    items["recipe_id"] = items["recipe_id"].astype(int)

    for column in ("name", "description"):
        items[column] = items[column].fillna("").astype(str).str.strip()

    for column in ("tags", "ingredients"):
        items[column] = items[column].apply(_serialize_list_field)

    items = items.drop_duplicates(subset=["recipe_id"]).sort_values(
        "recipe_id",
        ascending=True,
        kind="mergesort",
    )
    items = items.reset_index(drop=True)
    if items.empty:
        raise ValueError(f"Recipe catalog is empty after normalization: {recipes_path}")
    return items


def build_embedding_text(catalog: pd.DataFrame) -> pd.DataFrame:
    """Build the fixed embedding text used for neighbor-context retrieval."""
    items = catalog.copy()
    items["embedding_text"] = [
        _compose_embedding_text(
            name=row.name,
            description=row.description,
            tags=row.tags,
            ingredients=row.ingredients,
        )
        for row in items.itertuples(index=False)
    ]
    return items


def prepare_neighbor_catalog(recipes_path: Path) -> pd.DataFrame:
    """Load and normalize the recipe catalog plus its embedding text."""
    return build_embedding_text(load_recipe_catalog(recipes_path))


def encode_catalog_with_adaptive_batches(
    items: pd.DataFrame,
    *,
    encoder: MLXEmbeddingEncoder,
    batch_size: int | None = None,
) -> EncodedCatalog:
    """Encode item metadata text with adaptive batch sizing."""
    if items.empty:
        raise ValueError("Cannot encode an empty item catalog.")

    texts = items["embedding_text"].tolist()
    detected_total_memory_bytes = detect_total_memory_bytes()
    initial_batch_size = (
        batch_size
        if batch_size is not None
        else suggest_embedding_batch_size(
            num_items=len(texts),
            total_memory_bytes=detected_total_memory_bytes,
        )
    )
    initial_batch_size = max(1, min(initial_batch_size, len(texts), DEFAULT_MAX_BATCH_SIZE))
    min_batch_size = min(MIN_ADAPTIVE_BATCH_SIZE, len(texts))
    current_batch_size = initial_batch_size
    final_batch_size = initial_batch_size

    vectors: list[list[float]] = []
    start_index = 0
    while start_index < len(texts):
        end_index = min(start_index + current_batch_size, len(texts))
        batch_texts = texts[start_index:end_index]
        try:
            batch_vectors = encoder.encode(batch_texts)
        except (MemoryError, RuntimeError) as exc:
            if current_batch_size <= min_batch_size:
                raise RuntimeError(
                    f"Embedding failed at the minimum batch size of {current_batch_size}.",
                ) from exc
            current_batch_size = max(min_batch_size, current_batch_size // 2)
            continue

        if len(batch_vectors) != len(batch_texts):
            raise ValueError("Embedding batch output size does not match the input batch size.")

        vectors.extend(batch_vectors)
        start_index = end_index
        final_batch_size = current_batch_size

    embeddings = _as_normalized_float32_matrix(vectors)
    encoded_items = items.copy()
    encoded_items["embedding"] = [
        json.dumps([float(value) for value in vector], ensure_ascii=False)
        for vector in embeddings.tolist()
    ]
    return EncodedCatalog(
        items=encoded_items.loc[:, ITEMS_WITH_EMBEDDINGS_COLUMNS],
        embeddings=embeddings,
        initial_batch_size=initial_batch_size,
        final_batch_size=final_batch_size,
        min_batch_size=min_batch_size,
        detected_total_memory_bytes=detected_total_memory_bytes,
    )


def build_faiss_index(embeddings: FloatMatrix) -> faiss.IndexFlatIP:
    """Build a local FAISS cosine-similarity index over normalized embeddings."""
    if embeddings.ndim != 2 or embeddings.shape[0] == 0:
        raise ValueError("Embeddings must be a non-empty 2D matrix.")

    index = faiss.IndexFlatIP(int(embeddings.shape[1]))
    index.add(embeddings)
    return index


def search_topk_neighbors(
    *,
    index: faiss.IndexFlatIP,
    embeddings: FloatMatrix,
    recipe_ids: list[int],
    top_k: int,
) -> pd.DataFrame:
    """Search exact top-k item neighbors with deterministic tie-breaking."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")
    if len(recipe_ids) != int(embeddings.shape[0]):
        raise ValueError("Recipe ID count must match the embedding matrix row count.")

    search_width = min(len(recipe_ids), top_k + 1)
    scores, indices = index.search(embeddings, search_width)
    rows: list[dict[str, Any]] = []
    for source_position, source_recipe_id in enumerate(recipe_ids):
        candidates: list[tuple[float, int]] = []
        for raw_score, neighbor_position in zip(
            scores[source_position].tolist(),
            indices[source_position].tolist(),
            strict=True,
        ):
            if neighbor_position < 0 or neighbor_position == source_position:
                continue
            neighbor_recipe_id = recipe_ids[neighbor_position]
            candidates.append((float(raw_score), int(neighbor_recipe_id)))

        candidates.sort(key=lambda item: (-item[0], item[1]))
        for rank, (cosine_similarity, neighbor_recipe_id) in enumerate(
            candidates[:top_k],
            start=1,
        ):
            rows.append(
                {
                    "source_recipe_id": int(source_recipe_id),
                    "neighbor_rank": rank,
                    "neighbor_recipe_id": neighbor_recipe_id,
                    "cosine_similarity": cosine_similarity,
                }
            )

    return pd.DataFrame.from_records(rows, columns=NEIGHBOR_CONTEXT_COLUMNS)


def write_neighbor_context_outputs(
    *,
    out_dir: Path,
    items: pd.DataFrame,
    neighbor_context: pd.DataFrame,
    index: faiss.IndexFlatIP,
    manifest: dict[str, Any],
) -> NeighborContextSummary:
    """Persist neighbor-context tables, FAISS index, and manifest to disk."""
    out_dir.mkdir(parents=True, exist_ok=True)
    items.loc[:, ITEMS_WITH_EMBEDDINGS_COLUMNS].to_csv(
        out_dir / "items_with_embeddings.csv",
        index=False,
        encoding="utf-8",
    )
    neighbor_context.loc[:, NEIGHBOR_CONTEXT_COLUMNS].to_csv(
        out_dir / "neighbor_context.csv",
        index=False,
        encoding="utf-8",
    )
    pd.DataFrame(
        {
            "faiss_idx": list(range(len(items))),
            "recipe_id": items["recipe_id"].astype(int).tolist(),
        }
    ).to_csv(
        out_dir / "id_map.csv",
        index=False,
        encoding="utf-8",
    )
    faiss.write_index(index, str(out_dir / "item_index.faiss"))
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    embedding_dim = 0
    if not items.empty:
        first_embedding = json.loads(items.iloc[0]["embedding"])
        embedding_dim = len(first_embedding)

    return NeighborContextSummary(
        items_rows=len(items),
        neighbor_rows=len(neighbor_context),
        embedding_dim=embedding_dim,
        top_k=int(manifest["top_k"]),
        initial_batch_size=int(manifest["batching"]["initial_batch_size"]),
        final_batch_size=int(manifest["batching"]["final_batch_size"]),
    )


def build_manifest(
    *,
    recipes_path: Path,
    items: pd.DataFrame,
    neighbor_context: pd.DataFrame,
    embed_model: str,
    top_k: int,
    encoded_catalog: EncodedCatalog,
) -> dict[str, Any]:
    """Build metadata for the neighbor-context export."""
    detected_total_memory_gb: float | None = None
    if encoded_catalog.detected_total_memory_bytes is not None:
        detected_total_memory_gb = round(
            encoded_catalog.detected_total_memory_bytes / 1024**3,
            2,
        )

    embedding_dim = int(encoded_catalog.embeddings.shape[1])
    return {
        "source": {
            "recipes_path": str(recipes_path),
        },
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "stage": "neighbor_context",
        "embedding_model": embed_model,
        "index_type": "faiss.IndexFlatIP",
        "item_rows": len(items),
        "neighbor_rows": len(neighbor_context),
        "embedding_dim": embedding_dim,
        "top_k": top_k,
        "batching": {
            "initial_batch_size": encoded_catalog.initial_batch_size,
            "final_batch_size": encoded_catalog.final_batch_size,
            "min_batch_size": encoded_catalog.min_batch_size,
            "detected_total_memory_bytes": encoded_catalog.detected_total_memory_bytes,
            "detected_total_memory_gb": detected_total_memory_gb,
        },
    }


def build_neighbor_context(
    *,
    recipes_path: Path,
    out_dir: Path,
    embed_model: str,
    top_k: int = DEFAULT_TOP_K,
    batch_size: int | None = None,
    encoder: MLXEmbeddingEncoder | None = None,
) -> NeighborContextSummary:
    """Run the full neighbor-context pipeline."""
    items = prepare_neighbor_catalog(recipes_path)
    resolved_encoder = encoder or MLXEmbeddingEncoder(model_id=embed_model)
    encoded_catalog = encode_catalog_with_adaptive_batches(
        items,
        encoder=resolved_encoder,
        batch_size=batch_size,
    )
    index = build_faiss_index(encoded_catalog.embeddings)
    neighbor_context = search_topk_neighbors(
        index=index,
        embeddings=encoded_catalog.embeddings,
        recipe_ids=encoded_catalog.items["recipe_id"].astype(int).tolist(),
        top_k=top_k,
    )
    manifest = build_manifest(
        recipes_path=recipes_path,
        items=encoded_catalog.items,
        neighbor_context=neighbor_context,
        embed_model=embed_model,
        top_k=top_k,
        encoded_catalog=encoded_catalog,
    )
    return write_neighbor_context_outputs(
        out_dir=out_dir,
        items=encoded_catalog.items,
        neighbor_context=neighbor_context,
        index=index,
        manifest=manifest,
    )


def suggest_embedding_batch_size(
    *,
    num_items: int,
    total_memory_bytes: int | None,
) -> int:
    """Choose a safe initial embedding batch size from available memory."""
    if num_items < 1:
        raise ValueError("num_items must be at least 1.")

    if total_memory_bytes is None:
        candidate = DEFAULT_FALLBACK_BATCH_SIZE
    else:
        total_memory_gb = total_memory_bytes / 1024**3
        if total_memory_gb >= 48:
            candidate = 64
        elif total_memory_gb >= 32:
            candidate = 48
        elif total_memory_gb >= 24:
            candidate = 32
        else:
            candidate = 16

    return max(1, min(candidate, DEFAULT_MAX_BATCH_SIZE, num_items))


def detect_total_memory_bytes() -> int | None:
    """Detect total system memory without adding a new runtime dependency."""
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        page_count = os.sysconf("SC_PHYS_PAGES")
        if isinstance(page_size, int) and isinstance(page_count, int):
            total_memory_bytes = page_size * page_count
            if total_memory_bytes > 0:
                return total_memory_bytes
    except (AttributeError, OSError, ValueError):
        pass

    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                check=True,
                capture_output=True,
                text=True,
            )
            output = result.stdout.strip()
            if output:
                return int(output)
        except (OSError, ValueError, subprocess.CalledProcessError):
            return None

    return None


def _compose_embedding_text(
    *,
    name: str,
    description: str,
    tags: str,
    ingredients: str,
) -> str:
    sections: list[str] = []
    cleaned_name = name.strip()
    cleaned_description = description.strip()
    tag_text = ", ".join(_parse_list_field(tags))
    ingredient_text = ", ".join(_parse_list_field(ingredients))

    if cleaned_name:
        sections.append(f"Title: {cleaned_name}")
    if cleaned_description:
        sections.append(f"Description: {cleaned_description}")
    if tag_text:
        sections.append(f"Tags: {tag_text}")
    if ingredient_text:
        sections.append(f"Ingredients: {ingredient_text}")
    return "\n".join(sections)


def _serialize_list_field(value: Any) -> str:
    return json.dumps(_parse_list_field(value), ensure_ascii=False)


def _parse_list_field(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not isinstance(value, str):
        return []

    raw_value = value.strip()
    if not raw_value:
        return []

    parsed: Any
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(raw_value)
        except (SyntaxError, ValueError):
            return []

    if not isinstance(parsed, list):
        return []
    return [str(item).strip() for item in parsed if str(item).strip()]


def _as_normalized_float32_matrix(vectors: list[list[float]]) -> FloatMatrix:
    matrix = np.asarray(vectors, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("Embedding output must be a non-empty 2D matrix.")
    matrix = np.ascontiguousarray(matrix, dtype=np.float32)
    faiss.normalize_L2(matrix)
    return matrix
