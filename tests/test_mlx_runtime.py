import subprocess

from sid_reco.mlx_runtime import (
    MLXRuntimeProbeResult,
    RuntimeEnvironmentSummary,
    get_runtime_environment_summary,
    probe_mlx_runtime,
)


def test_get_runtime_environment_summary_marks_local_macos_terminal_supported(
    monkeypatch,
) -> None:
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("platform.machine", lambda: "arm64")
    monkeypatch.delenv("SSH_CONNECTION", raising=False)
    monkeypatch.delenv("SSH_TTY", raising=False)
    monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")

    summary = get_runtime_environment_summary()

    assert summary == RuntimeEnvironmentSummary(
        platform_name="Darwin",
        machine="arm64",
        python_version=summary.python_version,
        session_kind="local_terminal",
        term_program="iTerm.app",
        supported=True,
        support_reason="Supported local macOS Apple Silicon terminal session.",
    )


def test_probe_mlx_runtime_parses_successful_json(monkeypatch) -> None:
    def _fake_run(*args, **kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout='{"ok": true, "metal_available": true, "default_device": "gpu"}\n',
            stderr="",
        )

    monkeypatch.setattr("subprocess.run", _fake_run)

    result = probe_mlx_runtime(imports=("mlx.core", "mlx_lm"))

    assert result == MLXRuntimeProbeResult(
        ok=True,
        imports=("mlx.core", "mlx_lm"),
        returncode=0,
        metal_available=True,
        default_device="gpu",
        diagnostic='{"ok": true, "metal_available": true, "default_device": "gpu"}',
    )


def test_probe_mlx_runtime_returns_failure_diagnostic(monkeypatch) -> None:
    def _fake_run(*args, **kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=-6,
            stdout="",
            stderr="mlx crashed",
        )

    monkeypatch.setattr("subprocess.run", _fake_run)

    result = probe_mlx_runtime(imports=("mlx.core",))

    assert result.ok is False
    assert result.returncode == -6
    assert result.diagnostic == "mlx crashed"
