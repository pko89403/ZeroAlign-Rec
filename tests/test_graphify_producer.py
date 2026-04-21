from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _clean_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
    )
    return repo


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _copy_script(repo: Path, name: str) -> Path:
    script_path = ROOT / "scripts" / name
    target = repo / "scripts" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(script_path, target)
    return target


def test_graphify_full_refresh_produces_staged_outputs_with_doc_context(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write_file(repo / "src" / "pkg" / "core.py", "class Alpha:\n    pass\n")
    _write_file(repo / "tests" / "test_core.py", "def test_ok():\n    assert True\n")
    _write_file(repo / "raw" / "design" / "adr" / "adr-001-alpha.md", "# ADR\nAlpha decision\n")
    _write_file(repo / "raw" / "design" / "notes" / "alpha.md", "# Alpha\nUses Alpha\n")
    _write_file(repo / "raw" / "design" / "specs" / "alpha-spec.md", "# Spec\nAlpha architecture\n")
    _write_file(repo / "raw" / "external" / "papers" / "sid-paper.md", "Alpha paper\n")

    for name in (
        "graphify_prepare_corpus.sh",
        "graphify_full_refresh.py",
        "graphify_semantic_adapter.py",
    ):
        _copy_script(repo, name)

    subprocess.run(
        ["bash", str(repo / "scripts" / "graphify_prepare_corpus.sh")],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
    )
    subprocess.run(
        [
            "uv",
            "run",
            "--with",
            "graphifyy==0.4.23",
            "python",
            str(repo / "scripts" / "graphify_full_refresh.py"),
            ".graphify-work/corpus",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
    )

    out_dir = repo / ".graphify-work" / "corpus" / "graphify-out"
    assert (out_dir / "graph.json").exists()
    assert (out_dir / "GRAPH_REPORT.md").exists()
    assert (out_dir / "graph.html").exists()
    build_info = json.loads((out_dir / "BUILD_INFO.json").read_text(encoding="utf-8"))
    assert build_info["mode"] == "full_refresh"
    assert build_info["verified"] is False

    graph = json.loads((out_dir / "graph.json").read_text(encoding="utf-8"))
    source_files = {node.get("source_file") for node in graph.get("nodes", [])}
    assert "raw/design/adr/adr-001-alpha.md" in source_files
    assert "raw/design/notes/alpha.md" in source_files
    assert "raw/design/specs/alpha-spec.md" in source_files
    assert "raw/external/papers/sid-paper.md" in source_files

    semantic_links = [link for link in graph.get("links", []) if link.get("relation") != "contains"]
    assert semantic_links
    assert any(link.get("relation") == "references" for link in semantic_links)
    node_by_id = {node["id"]: node for node in graph.get("nodes", []) if "id" in node}
    assert any(
        node_by_id.get(link.get("source"), {}).get("source_file") == "raw/design/notes/alpha.md"
        or node_by_id.get(link.get("target"), {}).get("source_file") == "raw/design/notes/alpha.md"
        for link in semantic_links
    )


def test_graphify_full_refresh_reports_partial_state_on_semantic_failure(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write_file(repo / "src" / "pkg" / "core.py", "class Alpha:\n    pass\n")
    _write_file(repo / "tests" / "test_core.py", "def test_ok():\n    assert True\n")
    _write_file(repo / "raw" / "design" / "adr" / "adr-001-alpha.md", "# ADR\nAlpha decision\n")
    _write_file(repo / "raw" / "design" / "notes" / "alpha.md", "# Alpha\nUses Alpha\n")

    for name in (
        "graphify_prepare_corpus.sh",
        "graphify_full_refresh.py",
        "graphify_semantic_adapter.py",
    ):
        _copy_script(repo, name)

    subprocess.run(
        ["bash", str(repo / "scripts" / "graphify_prepare_corpus.sh")],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
    )
    env = dict(os.environ)
    env["GRAPHIFY_SEMANTIC_ADAPTER_MODE"] = "fail"
    env = {key: value for key, value in env.items() if not key.startswith("GIT_")}
    result = subprocess.run(
        [
            "uv",
            "run",
            "--with",
            "graphifyy==0.4.23",
            "python",
            str(repo / "scripts" / "graphify_full_refresh.py"),
            ".graphify-work/corpus",
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 1
    assert "semantic extraction failed" in result.stderr
    out_dir = repo / ".graphify-work" / "corpus" / "graphify-out"
    assert (out_dir / ".graphify_detect.json").exists()
    assert (out_dir / ".graphify_ast.json").exists()
    assert not (out_dir / "BUILD_INFO.json").exists()
