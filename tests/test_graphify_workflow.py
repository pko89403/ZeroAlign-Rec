from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "graphify"


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    return repo


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_raw_corpus(root: Path) -> Path:
    corpus = root / ".graphify-work" / "corpus"
    _write_file(corpus / "raw" / "design" / "adr" / "adr-001-dev-environment.md", "# adr\n")
    _write_file(
        corpus / "raw" / "design" / "notes" / "phase2-recommendation-runtime.md",
        "# note\n",
    )
    _write_file(corpus / "raw" / "design" / "specs" / "recommendation-v2.md", "# spec\n")
    _write_file(corpus / "raw" / "design" / "diagrams" / "flow.png", "png\n")
    _write_file(corpus / "raw" / "external" / "papers" / "sid-paper.pdf", "pdf\n")
    _write_file(corpus / "raw" / "external" / "datasets" / "foodcom.md", "# dataset\n")
    return corpus


def test_graphify_prepare_corpus_script_copies_only_curated_inputs(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write_file(repo / "src" / "app.py", "def run() -> None:\n    return None\n")
    _write_file(repo / "tests" / "test_app.py", "def test_ok():\n    assert True\n")
    _write_file(repo / "tests" / "__pycache__" / "bad.pyc", "x")
    _write_file(repo / "raw" / "design" / "adr" / "adr-001-alpha.md", "# adr\n")
    _write_file(repo / "raw" / "design" / "notes" / "alpha.md", "# note\n")
    _write_file(repo / "raw" / "external" / "papers" / "paper.md", "external source\n")
    _write_file(repo / "artifacts" / "report.txt", "skip\n")
    _write_file(repo / "data" / "processed" / "x.txt", "skip\n")

    script = ROOT / "scripts" / "graphify_prepare_corpus.sh"
    subprocess.run(["bash", str(script)], cwd=repo, check=True, capture_output=True, text=True)

    assert (repo / ".graphify-work" / "corpus" / "src" / "app.py").exists()
    assert (repo / ".graphify-work" / "corpus" / "tests" / "test_app.py").exists()
    assert (
        repo / ".graphify-work" / "corpus" / "raw" / "design" / "adr" / "adr-001-alpha.md"
    ).exists()
    assert (
        repo / ".graphify-work" / "corpus" / "raw" / "external" / "papers" / "paper.md"
    ).exists()
    assert not (repo / ".graphify-work" / "corpus" / "README.md").exists()
    assert not list((repo / ".graphify-work" / "corpus").rglob("__pycache__"))
    assert not list((repo / ".graphify-work" / "corpus").rglob("*.pyc"))


def test_graphify_verify_full_refresh_rejects_code_only_graph(tmp_path: Path) -> None:
    staged = tmp_path / "graphify-out"
    staged.mkdir()
    shutil.copy2(FIXTURES / "code_only_graph.json", staged / "graph.json")
    shutil.copy2(FIXTURES / "graph_report.md", staged / "GRAPH_REPORT.md")
    corpus = _seed_raw_corpus(tmp_path)
    build_info = json.loads((FIXTURES / "build_info_full_refresh.json").read_text(encoding="utf-8"))
    build_info["corpus_path"] = str(corpus)
    (staged / "BUILD_INFO.json").write_text(
        json.dumps(build_info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    verify = ROOT / "scripts" / "graphify_verify_full_refresh.py"
    result = subprocess.run(
        ["python3", str(verify), str(staged)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "missing required raw source context" in result.stderr


def test_graphify_verify_full_refresh_accepts_doc_context_graph(tmp_path: Path) -> None:
    staged = tmp_path / "graphify-out"
    staged.mkdir()
    shutil.copy2(FIXTURES / "full_refresh_graph.json", staged / "graph.json")
    shutil.copy2(FIXTURES / "graph_report.md", staged / "GRAPH_REPORT.md")
    corpus = _seed_raw_corpus(tmp_path)
    build_info = json.loads((FIXTURES / "build_info_full_refresh.json").read_text(encoding="utf-8"))
    build_info["corpus_path"] = str(corpus)
    (staged / "BUILD_INFO.json").write_text(
        json.dumps(build_info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    verify = ROOT / "scripts" / "graphify_verify_full_refresh.py"
    subprocess.run(
        ["python3", str(verify), str(staged)],
        check=True,
        capture_output=True,
        text=True,
    )

    updated = json.loads((staged / "BUILD_INFO.json").read_text(encoding="utf-8"))
    marker = json.loads((staged / "VERIFY_FULL_REFRESH.json").read_text(encoding="utf-8"))

    assert updated["verified"] is True
    assert updated["verification_profile"] == "raw-source-coverage-v3"
    assert updated["verification_metrics"]["semantic_link_count"] >= 8
    assert marker["verified"] is True
    assert marker["verification_profile"] == "raw-source-coverage-v3"


def test_graphify_sync_staged_requires_verify_marker(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    root_graph = repo / "graphify-out"
    root_graph.mkdir()
    staged = repo / ".graphify-work" / "corpus" / "graphify-out"
    staged.mkdir(parents=True)
    shutil.copy2(FIXTURES / "full_refresh_graph.json", staged / "graph.json")
    shutil.copy2(FIXTURES / "graph_report.md", staged / "GRAPH_REPORT.md")
    (staged / "graph.html").write_text("<html></html>\n", encoding="utf-8")
    shutil.copy2(FIXTURES / "build_info_full_refresh.json", staged / "BUILD_INFO.json")

    sync = ROOT / "scripts" / "graphify_sync_staged.sh"
    result = subprocess.run(
        ["bash", str(sync)],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "VERIFY_FULL_REFRESH.json" in result.stderr


def test_graphify_sync_staged_copies_verified_outputs(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    root_graph = repo / "graphify-out"
    root_graph.mkdir()
    staged = repo / ".graphify-work" / "corpus" / "graphify-out"
    staged.mkdir(parents=True)
    shutil.copy2(FIXTURES / "full_refresh_graph.json", staged / "graph.json")
    shutil.copy2(FIXTURES / "graph_report.md", staged / "GRAPH_REPORT.md")
    (staged / "graph.html").write_text("<html>fresh</html>\n", encoding="utf-8")
    build_info = json.loads((FIXTURES / "build_info_full_refresh.json").read_text(encoding="utf-8"))
    build_info["verified"] = True
    (staged / "BUILD_INFO.json").write_text(
        json.dumps(build_info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (staged / "VERIFY_FULL_REFRESH.json").write_text(
        json.dumps({"verified": True}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    sync = ROOT / "scripts" / "graphify_sync_staged.sh"
    subprocess.run(
        ["bash", str(sync)],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    assert (repo / "graphify-out" / "graph.json").exists()
    assert (repo / "graphify-out" / "GRAPH_REPORT.md").exists()
    assert (repo / "graphify-out" / "graph.html").read_text(
        encoding="utf-8"
    ) == "<html>fresh</html>\n"
    synced_info = json.loads(
        (repo / "graphify-out" / "BUILD_INFO.json").read_text(encoding="utf-8")
    )
    assert synced_info["mode"] == "full_refresh"


def test_graphify_ci_candidate_writes_manual_note_when_no_staged_output(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    script = ROOT / "scripts" / "graphify_ci_candidate.sh"

    subprocess.run(["bash", str(script)], cwd=repo, check=True, capture_output=True, text=True)

    note = (repo / ".graphify-work" / "FULL_REFRESH_CANDIDATE.md").read_text(encoding="utf-8")
    assert "did **not** run the full refresh producer" in note
    assert "bash scripts/graphify_prepare_corpus.sh" in note
    assert "uv run --with graphifyy==0.4.23 python scripts/graphify_full_refresh.py" in note


def test_graphify_ci_candidate_is_candidate_only_even_when_staged_output_exists(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    staged = repo / ".graphify-work" / "corpus" / "graphify-out"
    staged.mkdir(parents=True)
    shutil.copy2(FIXTURES / "full_refresh_graph.json", staged / "graph.json")
    shutil.copy2(FIXTURES / "graph_report.md", staged / "GRAPH_REPORT.md")
    build_info = json.loads((FIXTURES / "build_info_full_refresh.json").read_text(encoding="utf-8"))
    (staged / "BUILD_INFO.json").write_text(
        json.dumps(build_info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    candidate = ROOT / "scripts" / "graphify_ci_candidate.sh"

    # make repo-local scripts reachable with the relative paths used inside the candidate script
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    shutil.copy2(candidate, scripts_dir / "graphify_ci_candidate.sh")

    subprocess.run(["bash", str(candidate)], cwd=repo, check=True, capture_output=True, text=True)

    note = (repo / ".graphify-work" / "FULL_REFRESH_CANDIDATE.md").read_text(encoding="utf-8")
    assert "did **not** run the full refresh producer" in note
    assert "bash scripts/graphify_prepare_corpus.sh" in note
    assert "python3 scripts/graphify_verify_full_refresh.py" in note
