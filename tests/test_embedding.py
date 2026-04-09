import sys
from types import ModuleType, SimpleNamespace

from sid_reco.embedding import MLXEmbeddingEncoder


class _FakeArray:
    def __init__(self, data: list[list[float]]) -> None:
        self._data = data

    def tolist(self) -> list[list[float]]:
        return self._data


def test_encode_returns_python_float_vectors(monkeypatch) -> None:
    fake_mlx_core = ModuleType("mlx.core")
    fake_mlx_core.eval = lambda _: None

    fake_mlx = ModuleType("mlx")
    fake_mlx.core = fake_mlx_core

    fake_mlx_embeddings = ModuleType("mlx_embeddings")
    fake_mlx_embeddings.load = lambda model_id: ("model", "tokenizer")
    fake_mlx_embeddings.generate = lambda model, tokenizer, texts, padding, truncation: (
        SimpleNamespace(
            text_embeds=_FakeArray([[0.1, 0.2], [0.3, 0.4]]),
        )
    )

    monkeypatch.setattr("sid_reco.embedding.ensure_mlx_runtime_available", lambda **_: None)
    monkeypatch.setitem(sys.modules, "mlx", fake_mlx)
    monkeypatch.setitem(sys.modules, "mlx.core", fake_mlx_core)
    monkeypatch.setitem(sys.modules, "mlx_embeddings", fake_mlx_embeddings)

    encoder = MLXEmbeddingEncoder(model_id="mlx-community/Qwen3-Embedding-4B-4bit-DWQ")

    vectors = encoder.encode(["alpha", "beta"])

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


def test_encode_raises_runtime_error_when_probe_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        "sid_reco.embedding.ensure_mlx_runtime_available",
        lambda **_: (_ for _ in ()).throw(RuntimeError("probe failed")),
    )

    encoder = MLXEmbeddingEncoder(model_id="mlx-community/Qwen3-Embedding-4B-4bit-DWQ")

    try:
        encoder.encode(["alpha"])
    except RuntimeError as exc:
        assert str(exc) == "probe failed"
    else:
        raise AssertionError("Expected RuntimeError when the MLX probe fails.")
