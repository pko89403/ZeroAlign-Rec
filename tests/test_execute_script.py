from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def _load_execute_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "execute.py"
    spec = importlib.util.spec_from_file_location("sid_reco_harness_execute", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load execute.py from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_phase_index(root: Path, phase_name: str, *, steps: list[dict[str, object]]) -> None:
    phase_dir = root / "phases" / phase_name
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "index.json").write_text(
        json.dumps(
            {
                "project": "ZeroAlign-Rec",
                "phase": phase_name,
                "steps": steps,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_load_guardrails_uses_repo_specific_documents(tmp_path: Path) -> None:
    module = _load_execute_module()
    _write_phase_index(
        tmp_path,
        "phase-a",
        steps=[{"step": 0, "name": "setup", "status": "pending"}],
    )

    (tmp_path / "AGENTS.md").write_text("# Repo Rules\nAGENTS content\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Readme\nREADME content\n", encoding="utf-8")
    (tmp_path / "SPEC.md").write_text("# Spec\nSPEC content\n", encoding="utf-8")
    references_dir = tmp_path / "references"
    references_dir.mkdir()
    (references_dir / "local-adaptation.md").write_text(
        "# Local Adaptation\nAdaptation content\n",
        encoding="utf-8",
    )

    executor = module.StepExecutor("phase-a", root=tmp_path)

    guardrails = executor._load_guardrails()

    assert "AGENTS content" in guardrails
    assert "README content" in guardrails
    assert "SPEC content" in guardrails
    assert "Adaptation content" in guardrails


def test_check_blockers_exits_for_blocked_steps(tmp_path: Path) -> None:
    module = _load_execute_module()
    _write_phase_index(
        tmp_path,
        "phase-a",
        steps=[
            {"step": 0, "name": "setup", "status": "completed"},
            {
                "step": 1,
                "name": "needs-user-input",
                "status": "blocked",
                "blocked_reason": "Need a local model download.",
            },
        ],
    )

    executor = module.StepExecutor("phase-a", root=tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        executor._check_blockers()

    assert exc_info.value.code == 2


def test_ensure_created_at_records_task_timestamp(tmp_path: Path) -> None:
    module = _load_execute_module()
    _write_phase_index(
        tmp_path,
        "phase-a",
        steps=[{"step": 0, "name": "setup", "status": "pending"}],
    )

    executor = module.StepExecutor("phase-a", root=tmp_path)
    executor._ensure_created_at()

    index = json.loads((tmp_path / "phases" / "phase-a" / "index.json").read_text(encoding="utf-8"))
    assert "created_at" in index


def test_ensure_clean_worktree_exits_when_repo_is_dirty(tmp_path: Path) -> None:
    module = _load_execute_module()
    _write_phase_index(
        tmp_path,
        "phase-a",
        steps=[{"step": 0, "name": "setup", "status": "pending"}],
    )

    class _Result:
        def __init__(self, *, returncode: int, stdout: str = "", stderr: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def _fake_run(cmd: list[str], **kwargs: object) -> _Result:
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return _Result(returncode=0, stdout=" M README.md\n")
        return _Result(returncode=0)

    executor = module.StepExecutor("phase-a", root=tmp_path, subprocess_run=_fake_run)

    with pytest.raises(SystemExit) as exc_info:
        executor._ensure_clean_worktree()

    assert exc_info.value.code == 1


def test_invoke_claude_writes_output_and_uses_expected_command(tmp_path: Path) -> None:
    module = _load_execute_module()
    _write_phase_index(
        tmp_path,
        "phase-a",
        steps=[{"step": 0, "name": "setup", "status": "pending"}],
    )
    step_file = tmp_path / "phases" / "phase-a" / "step0.md"
    step_file.write_text("# Step 0\nDo the work.\n", encoding="utf-8")

    captured: dict[str, object] = {}

    class _Result:
        returncode = 0
        stdout = '{"ok": true}'
        stderr = ""

    def _fake_run(cmd: list[str], **kwargs: object) -> _Result:
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        captured["timeout"] = kwargs.get("timeout")
        return _Result()

    executor = module.StepExecutor("phase-a", root=tmp_path, subprocess_run=_fake_run)
    output = executor._invoke_claude({"step": 0, "name": "setup"}, "Preamble\n")

    assert captured["cmd"] == [
        "claude",
        "-p",
        "--dangerously-skip-permissions",
        "--output-format",
        "json",
        "Preamble\n# Step 0\nDo the work.\n",
    ]
    assert captured["cwd"] == str(tmp_path)
    assert captured["timeout"] == 1800
    assert output["stdout"] == '{"ok": true}'

    output_path = tmp_path / "phases" / "phase-a" / "step0-output.json"
    assert output_path.exists()


def test_build_preamble_keeps_git_ownership_in_executor(tmp_path: Path) -> None:
    module = _load_execute_module()
    _write_phase_index(
        tmp_path,
        "phase-a",
        steps=[{"step": 0, "name": "setup", "status": "pending"}],
    )

    executor = module.StepExecutor("phase-a", root=tmp_path)
    preamble = executor._build_preamble("Guardrails\n", "Context\n")

    assert "모든 변경사항을 커밋하라" not in preamble
    assert "git add/commit/push/reset/checkout/clean" in preamble
    assert "outer executor" in preamble


def test_claude_settings_enable_repo_specific_safety_hooks() -> None:
    settings_path = Path(__file__).resolve().parents[1] / ".claude" / "settings.json"

    settings = json.loads(settings_path.read_text(encoding="utf-8"))

    stop_hooks = settings["hooks"]["Stop"][0]["hooks"]
    assert stop_hooks[0]["command"] == "bash scripts/hooks/claude-stop-checks.sh"

    pretool_hooks = settings["hooks"]["PreToolUse"]
    write_commands = [
        hook["command"]
        for entry in pretool_hooks
        if entry["matcher"] == "Write"
        for hook in entry["hooks"]
    ]
    assert any("graphify-out/" in command for command in write_commands)


def test_claude_stop_script_uses_repo_validation_chain() -> None:
    root = Path(__file__).resolve().parents[1]
    content = (root / "scripts" / "hooks" / "claude-stop-checks.sh").read_text(encoding="utf-8")

    assert "uv run ruff check ." in content
    assert "uv run ruff format --check ." in content
    assert "uv run mypy src" in content
    assert "--ignore=tests/test_mlx_runtime.py" in content
    assert "--ignore=tests/test_cli_smoke_mlx.py" in content
