"""Local MLX embedding utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any

from sid_reco.config import Settings
from sid_reco.mlx_runtime import ensure_mlx_runtime_available


@dataclass(slots=True)
class MLXEmbeddingEncoder:
    """Lazy wrapper around an MLX embedding model."""

    model_id: str
    _model: Any | None = field(default=None, init=False, repr=False)
    _tokenizer: Any | None = field(default=None, init=False, repr=False)
    _runtime_checked: bool = field(default=False, init=False, repr=False)

    @classmethod
    def from_settings(cls, settings: Settings) -> MLXEmbeddingEncoder:
        """Build an encoder from application settings."""
        return cls(model_id=settings.embed_model)

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Encode a batch of texts into normalized embedding vectors."""
        if not texts:
            return []

        model, tokenizer = self._ensure_loaded()

        import mlx.core as mx

        mlx_embeddings = import_module("mlx_embeddings")
        generate = mlx_embeddings.generate

        output = generate(
            model,
            tokenizer,
            texts=texts,
            padding=True,
            truncation=True,
        )
        mx.eval(output.text_embeds)
        vectors = output.text_embeds.tolist()
        return [[float(value) for value in row] for row in vectors]

    def encode_one(self, text: str) -> list[float]:
        """Encode a single text and return one embedding vector."""
        return self.encode([text])[0]

    def _ensure_loaded(self) -> tuple[Any, Any]:
        """Load the embedding model only once."""
        if self._model is None or self._tokenizer is None:
            if not self._runtime_checked:
                ensure_mlx_runtime_available(
                    imports=("mlx.core", "mlx_embeddings"),
                    context="local embedding generation",
                )
                self._runtime_checked = True
            mlx_embeddings = import_module("mlx_embeddings")
            load = mlx_embeddings.load

            self._model, self._tokenizer = load(self.model_id)
        return self._model, self._tokenizer
