from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_session_start_canonical_script_contains_graphify_policy() -> None:
    canonical = (ROOT / "scripts" / "hooks" / "session-start.sh").read_text(encoding="utf-8")

    assert "graphify-mode-note.sh" in canonical
    assert "BUILD_INFO.json" in canonical


def test_graphify_mode_canonical_script_mentions_full_refresh_policy() -> None:
    canonical = (ROOT / "scripts" / "hooks" / "graphify-mode-note.sh").read_text(encoding="utf-8")

    assert "BUILD_INFO.json" in canonical
    assert "full_refresh" in canonical
    assert "raw/" in canonical


def test_claude_safety_canonical_scripts_share_common_helper() -> None:
    check_secrets = (ROOT / "scripts" / "hooks" / "check-secrets.sh").read_text(encoding="utf-8")
    stop_checks = (ROOT / "scripts" / "hooks" / "claude-stop-checks.sh").read_text(encoding="utf-8")

    assert "common.sh" in check_secrets
    assert "common.sh" in stop_checks
    assert "WARN: staged diff may contain credentials" in check_secrets
    assert "uv run mypy src" in stop_checks
