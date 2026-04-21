from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_git_hooks_delegate_to_shared_scripts_with_repo_root_fallback() -> None:
    pre_commit = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")
    pre_push = (ROOT / ".githooks" / "pre-push").read_text(encoding="utf-8")
    shared_pre_commit = (ROOT / "scripts" / "git-hooks" / "pre-commit.sh").read_text(
        encoding="utf-8"
    )
    shared_pre_push = (ROOT / "scripts" / "git-hooks" / "pre-push.sh").read_text(encoding="utf-8")

    assert "scripts/git-hooks/pre-commit.sh" in pre_commit
    assert "scripts/git-hooks/pre-push.sh" in pre_push
    assert "git rev-parse --show-toplevel 2>/dev/null || true" in pre_commit
    assert "git rev-parse --show-toplevel 2>/dev/null || true" in pre_push
    assert 'cd "$repo_root"' in shared_pre_commit
    assert 'cd "$repo_root"' in shared_pre_push
    assert "uv run ruff check --fix" in shared_pre_commit
    assert "uv run pytest --ignore=tests/test_mlx_runtime.py" in shared_pre_push
