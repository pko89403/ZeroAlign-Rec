from typer.testing import CliRunner

from sid_reco.cli import app
from sid_reco.mlx_runtime import MLXRuntimeProbeResult, RuntimeEnvironmentSummary

runner = CliRunner()


def test_smoke_mlx_exits_zero_when_supported_and_all_probes_pass(monkeypatch) -> None:
    monkeypatch.setattr(
        "sid_reco.cli.get_runtime_environment_summary",
        lambda: RuntimeEnvironmentSummary(
            platform_name="Darwin",
            machine="arm64",
            python_version="3.12.9",
            session_kind="local_terminal",
            term_program="Terminal.app",
            supported=True,
            support_reason="Supported local macOS Apple Silicon terminal session.",
        ),
    )
    monkeypatch.setattr(
        "sid_reco.cli.probe_mlx_runtime",
        lambda **kwargs: MLXRuntimeProbeResult(
            ok=True,
            imports=tuple(kwargs["imports"]),
            returncode=0,
            metal_available=True,
            default_device="gpu",
            diagnostic="ok",
        ),
    )

    result = runner.invoke(app, ["smoke-mlx"])

    assert result.exit_code == 0, result.stdout
    assert "MLX Environment" in result.stdout
    assert "MLX Probes" in result.stdout


def test_smoke_mlx_exits_nonzero_when_probe_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        "sid_reco.cli.get_runtime_environment_summary",
        lambda: RuntimeEnvironmentSummary(
            platform_name="Darwin",
            machine="arm64",
            python_version="3.12.9",
            session_kind="local_terminal",
            term_program="Terminal.app",
            supported=True,
            support_reason="Supported local macOS Apple Silicon terminal session.",
        ),
    )
    monkeypatch.setattr(
        "sid_reco.cli.probe_mlx_runtime",
        lambda **kwargs: MLXRuntimeProbeResult(
            ok=False,
            imports=tuple(kwargs["imports"]),
            returncode=-6,
            metal_available=None,
            default_device=None,
            diagnostic="mlx crashed",
        ),
    )

    result = runner.invoke(app, ["smoke-mlx"])

    assert result.exit_code == 1, result.stdout
    assert "mlx crashed" in result.stdout
