import json
from pathlib import Path

import numpy as np
import pytest

from sid_reco.config import Settings
from sid_reco.sid.embed_backend import (
    EmbeddedSIDItems,
    encode_serialized_items,
    encode_serialized_items_with_mlx,
    write_embedded_items,
)
from sid_reco.sid.serialization import SerializedSIDItem


class _FakeEncoder:
    def __init__(self, model_id: str = "mlx-community/Qwen3-Embedding-4B-4bit-DWQ") -> None:
        self.model_id = model_id
        self.calls: list[list[str]] = []

    def encode(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]


def test_encode_serialized_items_returns_float32_matrix_in_item_order() -> None:
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
    ]
    encoder = _FakeEncoder()

    embedded = encode_serialized_items(items, encoder=encoder)

    assert isinstance(embedded, EmbeddedSIDItems)
    assert [item.recipe_id for item in embedded.items] == [101, 102]
    assert encoder.calls == [["cuisine: american", "cuisine: italian"]]
    assert embedded.model_id == "mlx-community/Qwen3-Embedding-4B-4bit-DWQ"
    assert embedded.embedding_dim == 3
    assert embedded.matrix.dtype == np.float32
    assert np.allclose(embedded.matrix, np.asarray([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]))


def test_encode_serialized_items_rejects_encoder_length_mismatch() -> None:
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
    ]

    class _ShortEncoder(_FakeEncoder):
        def encode(self, texts: list[str]) -> list[list[float]]:
            self.calls.append(texts)
            return [[0.1, 0.2, 0.3]]

    with pytest.raises(ValueError, match="output size does not match"):
        encode_serialized_items(items, encoder=_ShortEncoder())


def test_encode_serialized_items_with_mlx_reuses_encoder_from_settings(monkeypatch) -> None:
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
    ]
    settings = Settings(
        project_root=Path("/tmp/project"),
        llm_backend="mlx",
        llm_model="test-llm",
        embed_model="test-embed-model",
        sid_catalog_path=Path("/tmp/project/data/catalog.csv"),
        sid_cache_dir=Path("/tmp/project/data/sid_cache"),
        llm_max_tokens=256,
        llm_temperature=0.0,
        llm_top_p=1.0,
    )
    encoder = _FakeEncoder(model_id="test-embed-model")

    monkeypatch.setattr(
        "sid_reco.sid.embed_backend.MLXEmbeddingEncoder.from_settings",
        lambda resolved_settings: encoder if resolved_settings is settings else None,
    )

    embedded = encode_serialized_items_with_mlx(items, settings=settings)

    assert embedded.model_id == "test-embed-model"
    assert encoder.calls == [["cuisine: american", "cuisine: italian"]]
    assert np.allclose(embedded.matrix, np.asarray([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]))


def test_write_embedded_items_writes_npy_and_manifest(tmp_path: Path) -> None:
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
    ]
    embedded = EmbeddedSIDItems(
        items=items,
        matrix=np.asarray([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], dtype=np.float32),
        embedding_dim=3,
        model_id="test-embed-model",
    )

    summary = write_embedded_items(embedded, out_dir=tmp_path / "sid_index")

    assert summary.item_count == 2
    assert summary.embedding_dim == 3
    assert summary.embeddings_path == tmp_path / "sid_index" / "embeddings.npy"
    assert summary.manifest_path == tmp_path / "sid_index" / "embedding_manifest.json"
    assert np.allclose(
        np.load(summary.embeddings_path),
        np.asarray([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], dtype=np.float32),
    )
    assert json.loads(summary.manifest_path.read_text(encoding="utf-8")) == {
        "embedding_dim": 3,
        "item_count": 2,
        "model_id": "test-embed-model",
    }
