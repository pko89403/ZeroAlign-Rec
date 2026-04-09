"""Helpers for probing MLX runtime availability safely."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeEnvironmentSummary:
    """High-level summary of the local execution environment."""

    platform_name: str
    machine: str
    python_version: str
    session_kind: str
    term_program: str
    supported: bool
    support_reason: str


@dataclass(frozen=True, slots=True)
class MLXRuntimeProbeResult:
    """Result of a child-process MLX runtime probe."""

    ok: bool
    imports: tuple[str, ...]
    returncode: int
    metal_available: bool | None
    default_device: str | None
    diagnostic: str


def get_runtime_environment_summary() -> RuntimeEnvironmentSummary:
    """Describe whether the current session matches the supported MLX environment."""
    platform_name = platform.system()
    machine = platform.machine().lower()
    python_version = sys.version.split()[0]
    term_program = os.getenv("TERM_PROGRAM", "unknown")
    is_ssh = bool(os.getenv("SSH_CONNECTION") or os.getenv("SSH_TTY"))
    session_kind = "ssh" if is_ssh else "local_terminal"

    if platform_name != "Darwin":
        supported = False
        support_reason = "MLX local inference is only supported on macOS."
    elif machine not in {"arm64", "aarch64"}:
        supported = False
        support_reason = "MLX Metal workflow requires Apple Silicon."
    elif is_ssh:
        supported = False
        support_reason = "SSH or headless sessions are not supported for MLX Metal validation."
    else:
        supported = True
        support_reason = "Supported local macOS Apple Silicon terminal session."

    return RuntimeEnvironmentSummary(
        platform_name=platform_name,
        machine=machine,
        python_version=python_version,
        session_kind=session_kind,
        term_program=term_program,
        supported=supported,
        support_reason=support_reason,
    )


def probe_mlx_runtime(*, imports: tuple[str, ...]) -> MLXRuntimeProbeResult:
    """Probe MLX imports in a child process and collect runtime metadata."""
    import_statements = "\n".join(f"import {module}" for module in imports)
    inspect_device = "mlx.core" in imports
    if inspect_device:
        inspection_code = (
            "import json\n"
            "import mlx.core as mx\n"
            "print(json.dumps({"
            "'ok': True, "
            "'metal_available': bool(mx.metal.is_available()), "
            "'default_device': str(mx.default_device())"
            "}))\n"
        )
    else:
        inspection_code = "import json\nprint(json.dumps({'ok': True}))\n"

    probe_script = f"{import_statements}\n{inspection_code}"
    completed = subprocess.run(
        [sys.executable, "-c", probe_script],
        capture_output=True,
        text=True,
        check=False,
    )

    diagnostic_parts = [
        part.strip()
        for part in (completed.stderr, completed.stdout)
        if part and part.strip()
    ]
    diagnostic = diagnostic_parts[0] if diagnostic_parts else "No diagnostic output captured."

    if completed.returncode == 0:
        parsed: dict[str, object]
        try:
            parsed = json.loads(completed.stdout.strip())
        except json.JSONDecodeError:
            parsed = {}
        return MLXRuntimeProbeResult(
            ok=True,
            imports=imports,
            returncode=completed.returncode,
            metal_available=(
                bool(parsed.get("metal_available"))
                if "metal_available" in parsed
                else None
            ),
            default_device=(
                str(parsed.get("default_device"))
                if "default_device" in parsed
                else None
            ),
            diagnostic=diagnostic,
        )

    return MLXRuntimeProbeResult(
        ok=False,
        imports=imports,
        returncode=completed.returncode,
        metal_available=None,
        default_device=None,
        diagnostic=diagnostic,
    )


def ensure_mlx_runtime_available(*, imports: tuple[str, ...], context: str) -> None:
    """Probe MLX imports in a child process to avoid crashing the main process."""
    result = probe_mlx_runtime(imports=imports)
    if result.ok:
        return
    raise RuntimeError(
        "MLX runtime probe failed before "
        f"{context}. This environment cannot initialize MLX safely. "
        f"Command exit code: {result.returncode}. "
        f"Diagnostic: {result.diagnostic}"
    )
