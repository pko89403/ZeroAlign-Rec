"""Embedding helpers for serialized SID items."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from sid_reco.config import Settings
from sid_reco.embedding import MLXEmbeddingEncoder
from sid_reco.sid.serialization import SerializedSIDItem

FloatMatrix = NDArray[np.float32]


class SerializedItemEncoder(Protocol):
    """Minimal protocol for turning serialized item text into dense vectors."""

    model_id: str

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Encode serialized item texts into dense float vectors."""


@dataclass(frozen=True, slots=True)
class EmbeddedSIDItems:
    """Serialized SID items paired with a dense embedding matrix."""

    items: list[SerializedSIDItem]
    matrix: FloatMatrix
    embedding_dim: int
    model_id: str


@dataclass(frozen=True, slots=True)
class EmbeddedSIDWriteSummary:
    """Summary for persisted embedding artifacts."""

    item_count: int
    embedding_dim: int
    embeddings_path: Path
    manifest_path: Path


def encode_serialized_items(
    items: list[SerializedSIDItem],
    *,
    encoder: SerializedItemEncoder,
) -> EmbeddedSIDItems:
    """Encode serialized SID items into a stable float32 matrix."""
    texts = [item.serialized_text for item in items]
    vectors = encoder.encode(texts)
    if len(vectors) != len(items):
        raise ValueError("Encoder output size does not match the serialized item count.")

    matrix = np.asarray(vectors, dtype=np.float32)
    if matrix.ndim != 2:
        raise ValueError("Encoded SID items must form a 2D embedding matrix.")

    embedding_dim = int(matrix.shape[1]) if matrix.shape[0] > 0 else 0
    return EmbeddedSIDItems(
        items=list(items),
        matrix=matrix,
        embedding_dim=embedding_dim,
        model_id=encoder.model_id,
    )


def encode_serialized_items_with_mlx(
    items: list[SerializedSIDItem],
    *,
    settings: Settings,
    encoder: SerializedItemEncoder | None = None,
) -> EmbeddedSIDItems:
    """Encode serialized SID items using the existing MLX embedding configuration."""
    resolved_encoder = encoder or MLXEmbeddingEncoder.from_settings(settings)
    return encode_serialized_items(items, encoder=resolved_encoder)


def write_embedded_items(
    embedded: EmbeddedSIDItems,
    *,
    out_dir: Path,
) -> EmbeddedSIDWriteSummary:
    """Persist dense embedding artifacts for the SID pipeline."""
    out_dir.mkdir(parents=True, exist_ok=True)
    embeddings_path = out_dir / "embeddings.npy"
    manifest_path = out_dir / "embedding_manifest.json"

    np.save(embeddings_path, embedded.matrix)
    manifest_path.write_text(
        json.dumps(
            {
                "embedding_dim": embedded.embedding_dim,
                "item_count": len(embedded.items),
                "model_id": embedded.model_id,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return EmbeddedSIDWriteSummary(
        item_count=len(embedded.items),
        embedding_dim=embedded.embedding_dim,
        embeddings_path=embeddings_path,
        manifest_path=manifest_path,
    )
