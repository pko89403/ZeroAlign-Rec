"""FAISS indexing and mapping artifact writers for compiled SID outputs."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import faiss  # type: ignore[import-untyped]
import numpy as np

from sid_reco.sid.compiler import ItemSID, TrainedResidualCodebooks, write_codebooks
from sid_reco.sid.embed_backend import EmbeddedSIDItems, FloatMatrix


@dataclass(frozen=True, slots=True)
class SIDIndexWriteSummary:
    """Summary for persisted SID index artifacts."""

    item_count: int
    embedding_dim: int
    compiled_sid_path: Path
    item_to_sid_path: Path
    sid_to_items_path: Path
    id_map_path: Path
    index_path: Path
    manifest_path: Path
    codebooks_path: Path
    codebooks_manifest_path: Path


def write_sid_index_outputs(
    *,
    embedded: EmbeddedSIDItems,
    codebooks: TrainedResidualCodebooks,
    items: list[ItemSID],
    out_dir: Path,
) -> SIDIndexWriteSummary:
    """Persist compiled SID outputs, codebook artifacts, mappings, and a CPU FAISS index."""
    _validate_embedded_codebooks_and_items(embedded=embedded, codebooks=codebooks, items=items)
    out_dir.mkdir(parents=True, exist_ok=True)

    compiled_sid_path = out_dir / "compiled_sid.jsonl"
    item_to_sid_path = out_dir / "item_to_sid.json"
    sid_to_items_path = out_dir / "sid_to_items.json"
    id_map_path = out_dir / "id_map.jsonl"
    index_path = out_dir / "item_index.faiss"
    manifest_path = out_dir / "manifest.json"

    compiled_lines: list[str] = []
    id_map_lines: list[str] = []
    item_to_sid: dict[str, str] = {}
    sid_to_items: dict[str, list[int]] = defaultdict(list)

    for faiss_idx, (embedded_item, item) in enumerate(zip(embedded.items, items, strict=True)):
        sid_path = list(item.sid_path)
        compiled_lines.append(
            json.dumps(
                {
                    "recipe_id": item.recipe_id,
                    "sid_path": sid_path,
                    "sid_string": item.sid_string,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        id_map_lines.append(
            json.dumps(
                {
                    "faiss_idx": faiss_idx,
                    "recipe_id": embedded_item.recipe_id,
                    "sid_path": sid_path,
                    "sid_string": item.sid_string,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        item_to_sid[str(item.recipe_id)] = item.sid_string
        sid_to_items[item.sid_string].append(item.recipe_id)

    compiled_sid_path.write_text("\n".join(compiled_lines) + "\n", encoding="utf-8")
    item_to_sid_path.write_text(
        json.dumps(item_to_sid, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    sid_to_items_path.write_text(
        json.dumps(
            {sid: sorted(recipe_ids) for sid, recipe_ids in sorted(sid_to_items.items())},
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    id_map_path.write_text("\n".join(id_map_lines) + "\n", encoding="utf-8")

    normalized_matrix = _normalize_embedding_matrix(embedded.matrix)
    index = faiss.IndexFlatIP(int(normalized_matrix.shape[1]))
    index.add(normalized_matrix)
    faiss.write_index(index, str(index_path))

    codebooks_path, codebooks_manifest_path = write_codebooks(codebooks, out_dir=out_dir)

    manifest_path.write_text(
        json.dumps(
            {
                "branching_factor": codebooks.branching_factor,
                "codebooks_manifest_path": codebooks_manifest_path.name,
                "codebooks_path": codebooks_path.name,
                "depth": codebooks.depth,
                "embedding_dim": embedded.embedding_dim,
                "index_type": "faiss.IndexFlatIP",
                "item_count": len(embedded.items),
                "level_cluster_counts": [level.cluster_count for level in codebooks.levels],
                "model_id": embedded.model_id,
                "normalize_residuals": codebooks.normalize_residuals,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return SIDIndexWriteSummary(
        item_count=len(embedded.items),
        embedding_dim=embedded.embedding_dim,
        compiled_sid_path=compiled_sid_path,
        item_to_sid_path=item_to_sid_path,
        sid_to_items_path=sid_to_items_path,
        id_map_path=id_map_path,
        index_path=index_path,
        manifest_path=manifest_path,
        codebooks_path=codebooks_path,
        codebooks_manifest_path=codebooks_manifest_path,
    )


def _validate_embedded_codebooks_and_items(
    *,
    embedded: EmbeddedSIDItems,
    codebooks: TrainedResidualCodebooks,
    items: list[ItemSID],
) -> None:
    if len(embedded.items) != len(items):
        raise ValueError("Embedded items and SID items must align by recipe_id.")
    if embedded.embedding_dim != codebooks.embedding_dim:
        raise ValueError("Embedded items and trained codebooks must share embedding_dim.")
    if len(codebooks.levels) != codebooks.depth:
        raise ValueError("Trained codebooks depth must match the number of stored levels.")
    for embedded_item, item in zip(embedded.items, items, strict=True):
        if embedded_item.recipe_id != item.recipe_id:
            raise ValueError("Embedded items and SID items must align by recipe_id.")


def _normalize_embedding_matrix(matrix: FloatMatrix) -> FloatMatrix:
    normalized = np.asarray(matrix, dtype=np.float32).copy()
    if normalized.ndim != 2:
        raise ValueError("Embedding matrix must be 2D for FAISS indexing.")

    row_norms = np.linalg.norm(normalized, axis=1, keepdims=True)
    nonzero_rows = row_norms[:, 0] > 0
    normalized[nonzero_rows] = normalized[nonzero_rows] / row_norms[nonzero_rows]
    return normalized.astype(np.float32, copy=False)
