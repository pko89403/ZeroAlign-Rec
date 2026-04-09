"""Local MLX LLM utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any

from sid_reco.config import Settings
from sid_reco.mlx_runtime import ensure_mlx_runtime_available


@dataclass(slots=True)
class MLXTextGenerator:
    """Lazy wrapper around an MLX chat model."""

    model_id: str
    _model: Any | None = field(default=None, init=False, repr=False)
    _tokenizer: Any | None = field(default=None, init=False, repr=False)
    _runtime_checked: bool = field(default=False, init=False, repr=False)

    @classmethod
    def from_settings(cls, settings: Settings) -> MLXTextGenerator:
        """Build a generator from application settings."""
        return cls(model_id=settings.llm_model)

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 256,
        temperature: float = 0.0,
        top_p: float = 1.0,
        verbose: bool = False,
    ) -> str:
        """Generate a response from the configured local model."""
        model, tokenizer = self._ensure_loaded()
        formatted_prompt = _format_chat_prompt(
            tokenizer=tokenizer,
            prompt=prompt,
            system_prompt=system_prompt,
        )

        mlx_lm = import_module("mlx_lm")
        generate = mlx_lm.generate
        sample_utils = import_module("mlx_lm.sample_utils")
        make_sampler = sample_utils.make_sampler
        sampler = make_sampler(temp=temperature, top_p=top_p)

        return str(
            generate(
                model,
                tokenizer,
                prompt=formatted_prompt,
                max_tokens=max_tokens,
                verbose=verbose,
                sampler=sampler,
            ),
        )

    def _ensure_loaded(self) -> tuple[Any, Any]:
        """Load the LLM only once."""
        if self._model is None or self._tokenizer is None:
            if not self._runtime_checked:
                ensure_mlx_runtime_available(
                    imports=("mlx.core", "mlx_lm"),
                    context="local text generation",
                )
                self._runtime_checked = True
            mlx_lm = import_module("mlx_lm")
            load = mlx_lm.load
            loaded = load(self.model_id)

            self._model = loaded[0]
            self._tokenizer = loaded[1]
        return self._model, self._tokenizer


def _format_chat_prompt(
    *,
    tokenizer: Any,
    prompt: str,
    system_prompt: str | None,
) -> str | list[int]:
    """Use the tokenizer chat template when available."""
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    if getattr(tokenizer, "chat_template", None) is not None:
        attempts = (
            {"add_generation_prompt": True, "tokenize": False, "enable_thinking": False},
            {"add_generation_prompt": True, "tokenize": False},
            {"add_generation_prompt": True},
        )
        formatted: Any | None = None
        for kwargs in attempts:
            try:
                formatted = tokenizer.apply_chat_template(messages, **kwargs)
                break
            except TypeError:
                continue

        if formatted is None:
            raise TypeError("Tokenizer chat template could not be applied with supported kwargs.")

        if isinstance(formatted, (list, str)):
            return formatted
        return str(formatted)

    if system_prompt:
        return f"System: {system_prompt}\n\nUser: {prompt}\nAssistant:"
    return prompt
