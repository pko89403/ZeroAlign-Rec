import sys
from types import ModuleType

from sid_reco.llm import MLXTextGenerator


class _FakeTokenizer:
    chat_template = "{{ chat }}"

    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        *,
        add_generation_prompt: bool,
    ) -> str:
        assert add_generation_prompt is True
        assert messages == [
            {"role": "system", "content": "You are concise."},
            {"role": "user", "content": "Summarize this."},
        ]
        return "FORMATTED_PROMPT"


class _FakeTokenListTokenizer:
    chat_template = "{{ chat }}"

    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        *,
        add_generation_prompt: bool,
        tokenize: bool,
    ) -> list[int]:
        assert add_generation_prompt is True
        assert tokenize is False
        assert messages == [
            {"role": "system", "content": "You are concise."},
            {"role": "user", "content": "Summarize this."},
        ]
        return [1, 2, 3]


def test_generate_uses_chat_template(monkeypatch) -> None:
    fake_mlx_lm = ModuleType("mlx_lm")
    fake_mlx_lm.load = lambda model_id: ("model", _FakeTokenizer())
    fake_mlx_lm.generate = lambda model, tokenizer, prompt, max_tokens, verbose, sampler: (
        f"prompt={prompt}|max_tokens={max_tokens}|sampler={sampler}"
    )
    fake_sample_utils = ModuleType("mlx_lm.sample_utils")
    fake_sample_utils.make_sampler = lambda temp, top_p: f"temp={temp}|top_p={top_p}"

    monkeypatch.setattr("sid_reco.llm.ensure_mlx_runtime_available", lambda **_: None)
    monkeypatch.setitem(sys.modules, "mlx_lm", fake_mlx_lm)
    monkeypatch.setitem(sys.modules, "mlx_lm.sample_utils", fake_sample_utils)

    generator = MLXTextGenerator(model_id="mlx-community/Qwen3.5-9B-OptiQ-4bit")

    response = generator.generate(
        "Summarize this.",
        system_prompt="You are concise.",
        max_tokens=64,
        temperature=0.2,
        top_p=0.9,
    )

    assert response == "prompt=FORMATTED_PROMPT|max_tokens=64|sampler=temp=0.2|top_p=0.9"


def test_generate_supports_chat_template_that_returns_token_ids(monkeypatch) -> None:
    fake_mlx_lm = ModuleType("mlx_lm")
    fake_mlx_lm.load = lambda model_id: ("model", _FakeTokenListTokenizer())
    fake_mlx_lm.generate = lambda model, tokenizer, prompt, max_tokens, verbose, sampler: (
        f"prompt={prompt}|max_tokens={max_tokens}|sampler={sampler}"
    )
    fake_sample_utils = ModuleType("mlx_lm.sample_utils")
    fake_sample_utils.make_sampler = lambda temp, top_p: f"temp={temp}|top_p={top_p}"

    monkeypatch.setattr("sid_reco.llm.ensure_mlx_runtime_available", lambda **_: None)
    monkeypatch.setitem(sys.modules, "mlx_lm", fake_mlx_lm)
    monkeypatch.setitem(sys.modules, "mlx_lm.sample_utils", fake_sample_utils)

    generator = MLXTextGenerator(model_id="mlx-community/Qwen3.5-9B-OptiQ-4bit")

    response = generator.generate(
        "Summarize this.",
        system_prompt="You are concise.",
        max_tokens=64,
        temperature=0.0,
        top_p=1.0,
    )

    assert response == "prompt=[1, 2, 3]|max_tokens=64|sampler=temp=0.0|top_p=1.0"


def test_generate_raises_runtime_error_when_probe_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        "sid_reco.llm.ensure_mlx_runtime_available",
        lambda **_: (_ for _ in ()).throw(RuntimeError("probe failed")),
    )

    generator = MLXTextGenerator(model_id="mlx-community/Qwen3.5-9B-OptiQ-4bit")

    try:
        generator.generate("Summarize this.")
    except RuntimeError as exc:
        assert str(exc) == "probe failed"
    else:
        raise AssertionError("Expected RuntimeError when the MLX probe fails.")
