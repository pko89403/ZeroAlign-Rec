from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_gitignore_ignores_only_graphify_runtime_cache() -> None:
    content = (ROOT / ".gitignore").read_text(encoding="utf-8")
    lines = {line.strip() for line in content.splitlines()}

    assert "graphify-out/cache/" in lines
    assert "graphify-out/memory/" in lines
    assert "graphify-out/" not in lines


def test_graphifyignore_excludes_non_curated_paths() -> None:
    content = (ROOT / ".graphifyignore").read_text(encoding="utf-8")

    assert ".agents/" in content
    assert ".harness/" in content
    assert "docs/" in content
    assert "scripts/" in content
    assert "tasks/" in content


def test_claude_settings_prefer_graphify_before_raw_search() -> None:
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))

    pretool = settings["hooks"]["PreToolUse"]
    graphify_hooks = [
        hook["command"]
        for entry in pretool
        if entry["matcher"] == "Glob|Grep"
        for hook in entry["hooks"]
    ]

    assert graphify_hooks
    assert graphify_hooks[0] == "bash .harness/hooks/graphify-pretool.sh"

    posttool = settings["hooks"]["PostToolUse"]
    auto_refresh_hooks = [
        hook["command"]
        for entry in posttool
        if entry["matcher"] == "Write|Edit|Bash"
        for hook in entry["hooks"]
    ]

    assert auto_refresh_hooks
    assert auto_refresh_hooks[0] == "bash .harness/hooks/graphify-auto-refresh.sh"


def test_session_start_mentions_graphify_priority() -> None:
    content = (ROOT / ".harness" / "hooks" / "session-start.sh").read_text(encoding="utf-8")

    assert "graphify-mode-note.sh" in content
    assert "BUILD_INFO.json" in content


def test_docs_manager_skill_switches_to_graphify_first() -> None:
    content = (ROOT / ".agents" / "skills" / "docs-manager" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "Graphify-first" in content
    assert "Raw Source Maintenance" in content
    assert "scripts/graphify_code_refresh.sh" in content
    assert "scripts/graphify_full_refresh.py" in content


def test_graphify_artifacts_exist() -> None:
    assert (ROOT / "graphify-out" / "GRAPH_REPORT.md").exists()
    assert (ROOT / "graphify-out" / "graph.json").exists()
    assert (ROOT / "graphify-out" / "graph.html").exists()


def test_code_refresh_script_pins_graphify_version_and_writes_build_info() -> None:
    script = (ROOT / "scripts" / "graphify_code_refresh.sh").read_text(encoding="utf-8")

    assert "graphifyy==0.4.23" in script
    assert "graphify update ." in script
    assert "BUILD_INFO.json" in script
    assert "command -v graphify" not in script


def test_build_info_records_supported_graph_mode() -> None:
    build_info = json.loads((ROOT / "graphify-out" / "BUILD_INFO.json").read_text(encoding="utf-8"))

    assert build_info["graphify_version"] == "0.4.23"
    assert build_info["mode"] in {"code_update", "full_refresh"}
    assert build_info["command"]
    if build_info["mode"] == "full_refresh":
        assert build_info["verified"] is True
        assert build_info["verification_profile"] == "raw-source-coverage-v3"


def test_corpus_prep_script_excludes_python_caches() -> None:
    script = (ROOT / "scripts" / "graphify_prepare_corpus.sh").read_text(encoding="utf-8")

    assert "__pycache__" in script
    assert ".pyc" in script


def test_claude_active_surface_no_longer_keeps_full_legacy_workflow() -> None:
    content = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    assert "docs/wiki" not in content
    assert "docs/sources" not in content
    assert "raw/" in content
    assert "graphify-manager" in content


def test_claude_contains_upstream_graphify_baseline_with_local_overrides() -> None:
    content = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    assert "## graphify" in content
    assert "This project has a graphify knowledge graph at `graphify-out/`." in content
    assert (
        "Before answering architecture or codebase questions, read "
        "`graphify-out/GRAPH_REPORT.md` for god nodes and community structure." in content
    )
    assert "Project overrides:" in content
    assert "scripts/graphify_code_refresh.sh" in content
    assert "graphify-out/BUILD_INFO.json" in content
    assert "raw/" in content
    assert "graphify-out/wiki/index.md" not in content


def test_raw_readme_exists_with_source_corpus_contract() -> None:
    content = (ROOT / "raw" / "README.md").read_text(encoding="utf-8")

    assert "정본 source corpus" in content
    assert "graphify-out/" in content
    assert "references/" in content


def test_graphify_manager_skill_exists_with_full_refresh_flow() -> None:
    content = (ROOT / ".agents" / "skills" / "graphify-manager" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "graphify_prepare_corpus.sh" in content
    assert "uv run --with graphifyy==0.4.23 python scripts/graphify_full_refresh.py" in content
    assert "graphify_verify_full_refresh.py" in content
    assert "graphify_sync_staged.sh" in content
    assert "detect" in content
    assert "AST extraction" in content
    assert "semantic extraction" in content
    assert "verify gate" in content
    assert "auto-refresh the graph after relevant local edits" in content
    assert "raw/design/adr" in content


def test_graphify_full_wrapper_skill_exists() -> None:
    content = (ROOT / ".agents" / "skills" / "graphify-full" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "graphify-manager" in content
    assert "staged producer path" in content


def test_graphify_mode_helper_mentions_full_refresh_policy() -> None:
    content = (ROOT / ".harness" / "hooks" / "graphify-mode-note.sh").read_text(encoding="utf-8")

    assert "BUILD_INFO.json" in content
    assert "full_refresh" in content
    assert "raw/" in content
    assert "raw source coverage" in content


def test_codex_hooks_expose_graphify_pretool_baseline() -> None:
    hooks = json.loads((ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))

    pretool = hooks["hooks"]["PreToolUse"]
    bash_hooks = [
        hook["command"]
        for entry in pretool
        if entry["matcher"] == "Bash"
        for hook in entry["hooks"]
    ]

    assert bash_hooks
    assert bash_hooks[0] == "bash .harness/hooks/graphify-pretool.sh"

    posttool = hooks["hooks"]["PostToolUse"]
    auto_refresh_hooks = [
        hook["command"]
        for entry in posttool
        if entry["matcher"] == "Write|Edit|Bash"
        for hook in entry["hooks"]
    ]

    assert auto_refresh_hooks
    assert auto_refresh_hooks[0] == "bash .harness/hooks/graphify-auto-refresh.sh"


def test_github_instructions_expose_graphify_full_entrypoint() -> None:
    content = (ROOT / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")

    assert "/graphify-full" in content or "graphify-full" in content


def test_ci_workflow_has_graphify_candidate_job_without_auto_sync() -> None:
    content = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    graphify_job = content.split("graphify-full-refresh-candidate:", maxsplit=1)[1]

    assert "graphify-full-refresh-candidate:" in content
    assert "dorny/paths-filter@v3" in content
    assert "scripts/graphify_prepare_corpus.sh" in graphify_job
    assert "scripts/graphify_ci_candidate.sh" in graphify_job
    assert "raw/**" in graphify_job
    assert ".github/workflows/ci.yml" in graphify_job
    assert "upload-artifact@v4" in graphify_job
    assert "scripts/graphify_full_refresh.py" in graphify_job
    assert "astral-sh/setup-uv@v5" not in graphify_job
    assert "run: bash scripts/graphify_sync_staged.sh" not in graphify_job


def test_docs_manager_marks_full_refresh_as_explicit_only() -> None:
    content = (ROOT / ".agents" / "skills" / "docs-manager" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "raw/" in content
    assert "legacy wiki" not in content


def test_active_doc_surfaces_no_longer_point_to_legacy_wiki_paths() -> None:
    documentation_skill = (
        ROOT / ".agents" / "skills" / "documentation-and-adrs" / "SKILL.md"
    ).read_text(encoding="utf-8")
    meta_skill = (ROOT / ".agents" / "skills" / "using-agent-skills" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    docs_manager_agent = (
        ROOT / ".agents" / "skills" / "docs-manager" / "agents" / "openai.yaml"
    ).read_text(encoding="utf-8")
    doc_manager_agent = (
        ROOT / ".agents" / "skills" / "doc-manager" / "agents" / "openai.yaml"
    ).read_text(encoding="utf-8")
    issue_template = (
        ROOT / ".github" / "ISSUE_TEMPLATE" / "research-attribution-review.yml"
    ).read_text(encoding="utf-8")
    ideas_readme = (ROOT / "ideas" / "README.md").read_text(encoding="utf-8")
    idea_refine_script = (
        ROOT / ".agents" / "skills" / "idea-refine" / "scripts" / "idea-refine.sh"
    ).read_text(encoding="utf-8")

    for content in (
        documentation_skill,
        meta_skill,
        docs_manager_agent,
        doc_manager_agent,
        issue_template,
        ideas_readme,
        idea_refine_script,
    ):
        assert "docs/wiki" not in content
        assert "docs/sources" not in content

    assert "raw/design/adr/" in documentation_skill
    assert "raw/design/notes/" in documentation_skill
    assert "raw/" in meta_skill
    assert "raw/design/adr" in docs_manager_agent
    assert "raw/design/notes" in issue_template
    assert 'IDEAS_DIR="ideas"' in idea_refine_script


def test_pr_creation_rules_require_template_based_flow() -> None:
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    copilot = (ROOT / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    local_adaptation = (ROOT / ".harness" / "reference" / "local-adaptation.md").read_text(
        encoding="utf-8"
    )

    assert ".github/pull_request_template.md" in claude
    assert "gh pr create --body" in claude
    assert ".github/pull_request_template.md" in copilot
    assert "--template .github/pull_request_template.md" in copilot
    assert ".github/pull_request_template.md" in local_adaptation
    assert "--body-file" in local_adaptation
