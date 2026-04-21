from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    return repo


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _commit_all(repo: Path, message: str = "seed") -> None:
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _copy_graphify_runtime(repo: Path) -> None:
    for relative in (
        ".harness/hooks/graphify-auto-refresh.sh",
        "scripts/graphify_code_refresh.sh",
        "scripts/graphify_prepare_corpus.sh",
        "scripts/graphify_full_refresh.py",
        "scripts/graphify_semantic_adapter.py",
        "scripts/graphify_verify_full_refresh.py",
        "scripts/graphify_sync_staged.sh",
    ):
        source = ROOT / relative
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    subprocess.run(
        ["chmod", "+x", str(repo / ".harness/hooks/graphify-auto-refresh.sh")],
        check=True,
        capture_output=True,
        text=True,
    )

    graph_dir = repo / "graphify-out"
    graph_dir.mkdir(parents=True, exist_ok=True)
    for name in ("BUILD_INFO.json", "GRAPH_REPORT.md", "graph.json", "graph.html"):
        shutil.copy2(ROOT / "graphify-out" / name, graph_dir / name)


def _seed_repo(repo: Path) -> None:
    _write_file(repo / "src" / "pkg" / "core.py", "class Alpha:\n    pass\n")
    _write_file(repo / "tests" / "test_core.py", "def test_ok():\n    assert True\n")
    _write_file(repo / "raw" / "design" / "adr" / "adr-001-alpha.md", "# ADR\nAlpha decision\n")
    _write_file(repo / "raw" / "design" / "notes" / "alpha.md", "# Alpha\nUses Alpha\n")


def test_graphify_auto_refresh_runs_code_refresh_after_code_only_change(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_repo(repo)
    _copy_graphify_runtime(repo)
    _commit_all(repo)

    auto_refresh = repo / ".harness/hooks/graphify-auto-refresh.sh"
    subprocess.run(
        ["bash", str(auto_refresh)],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    _write_file(repo / "src" / "pkg" / "core.py", "class Alpha:\n    value = 1\n")
    subprocess.run(
        ["bash", str(auto_refresh)],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    build_info = json.loads((repo / "graphify-out" / "BUILD_INFO.json").read_text(encoding="utf-8"))
    assert build_info["mode"] == "code_update"


def test_graphify_auto_refresh_runs_full_refresh_after_doc_change(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_repo(repo)
    _copy_graphify_runtime(repo)
    _commit_all(repo)

    auto_refresh = repo / ".harness/hooks/graphify-auto-refresh.sh"
    subprocess.run(
        ["bash", str(auto_refresh)],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    _write_file(
        repo / "raw" / "design" / "notes" / "alpha.md",
        "# Alpha\nUses Alpha\n## Context\n왜 Alpha가 필요한지 설명한다.\n",
    )
    subprocess.run(
        ["bash", str(auto_refresh)],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    build_info = json.loads((repo / "graphify-out" / "BUILD_INFO.json").read_text(encoding="utf-8"))
    assert build_info["mode"] == "full_refresh"
    assert build_info["verified"] is True


def test_graphify_auto_refresh_bootstrap_does_not_skip_first_doc_change(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_repo(repo)
    _copy_graphify_runtime(repo)
    _commit_all(repo)

    auto_refresh = repo / ".harness/hooks/graphify-auto-refresh.sh"
    _write_file(
        repo / "raw" / "design" / "notes" / "alpha.md",
        "# Alpha\nUses Alpha\n## Context\n첫 변경이다.\n",
    )
    subprocess.run(
        ["bash", str(auto_refresh)],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    build_info = json.loads((repo / "graphify-out" / "BUILD_INFO.json").read_text(encoding="utf-8"))
    assert build_info["mode"] == "full_refresh"
    assert build_info["verified"] is True


def test_graphify_auto_refresh_bootstrap_runs_code_refresh_for_first_code_change(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    _seed_repo(repo)
    _copy_graphify_runtime(repo)
    _commit_all(repo)

    auto_refresh = repo / ".harness/hooks/graphify-auto-refresh.sh"
    _write_file(repo / "src" / "pkg" / "core.py", "class Alpha:\n    value = 2\n")
    subprocess.run(
        ["bash", str(auto_refresh)],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    build_info = json.loads((repo / "graphify-out" / "BUILD_INFO.json").read_text(encoding="utf-8"))
    assert build_info["mode"] == "code_update"
