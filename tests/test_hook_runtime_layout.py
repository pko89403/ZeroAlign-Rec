from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_session_start_wrapper_delegates_to_canonical_script() -> None:
    wrapper = (ROOT / ".harness" / "hooks" / "session-start.sh").read_text(encoding="utf-8")
    canonical = (ROOT / "scripts" / "hooks" / "session-start.sh").read_text(encoding="utf-8")

    assert "scripts/hooks/session-start.sh" in wrapper
    assert "graphify-mode-note.sh" in canonical
    assert "BUILD_INFO.json" in canonical


def test_graphify_mode_wrapper_delegates_to_canonical_script() -> None:
    wrapper = (ROOT / ".harness" / "hooks" / "graphify-mode-note.sh").read_text(encoding="utf-8")
    canonical = (ROOT / "scripts" / "hooks" / "graphify-mode-note.sh").read_text(encoding="utf-8")

    assert "scripts/hooks/graphify-mode-note.sh" in wrapper
    assert "BUILD_INFO.json" in canonical
    assert "full_refresh" in canonical
    assert "raw/" in canonical


def test_claude_safety_wrappers_delegate_to_canonical_scripts() -> None:
    check_secrets_wrapper = (ROOT / ".harness" / "hooks" / "check-secrets.sh").read_text(
        encoding="utf-8"
    )
    stop_checks_wrapper = (ROOT / ".harness" / "hooks" / "claude-stop-checks.sh").read_text(
        encoding="utf-8"
    )
    check_secrets = (ROOT / "scripts" / "hooks" / "check-secrets.sh").read_text(encoding="utf-8")
    stop_checks = (ROOT / "scripts" / "hooks" / "claude-stop-checks.sh").read_text(encoding="utf-8")

    assert "scripts/hooks/check-secrets.sh" in check_secrets_wrapper
    assert "scripts/hooks/claude-stop-checks.sh" in stop_checks_wrapper
    assert "common.sh" in check_secrets
    assert "common.sh" in stop_checks
    assert "WARN: staged diff may contain credentials" in check_secrets
    assert "uv run mypy src" in stop_checks
