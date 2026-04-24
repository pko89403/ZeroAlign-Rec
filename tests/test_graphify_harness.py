from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOVED_GRAPHIFY_CONTRACT_TOKENS = (
    "code_update",
    "full_refresh",
    "BUILD_INFO.json",
    "scripts/graphify_prepare_corpus.sh",
    "scripts/graphify_full_refresh.py",
    "scripts/graphify_verify_full_refresh.py",
    "scripts/graphify_sync_staged.sh",
    "PostToolUse auto-refresh",
)
LEGACY_GRAPHIFY_RUNTIME_PATHS = (
    "scripts/graphify_code_refresh.sh",
    "scripts/graphify_prepare_corpus.sh",
    "scripts/graphify_full_refresh.py",
    "scripts/graphify_semantic_adapter.py",
    "scripts/graphify_verify_full_refresh.py",
    "scripts/graphify_sync_staged.sh",
    "scripts/graphify_ci_candidate.sh",
    "scripts/hooks/graphify-auto-refresh.sh",
    "scripts/hooks/graphify-pretool.sh",
    "scripts/hooks/graphify-mode-note.sh",
    "graphify-out/BUILD_INFO.json",
)
LEGACY_GRAPHIFY_TEST_PATHS = (
    "tests/test_graphify_auto_refresh.py",
    "tests/test_graphify_producer.py",
    "tests/test_graphify_workflow.py",
)


def test_gitignore_ignores_only_graphify_runtime_cache() -> None:
    content = (ROOT / ".gitignore").read_text(encoding="utf-8")
    lines = {line.strip() for line in content.splitlines()}

    assert "graphify-out/cache/" in lines
    assert "graphify-out/memory/" in lines
    assert "graphify-out/" not in lines


def test_graphifyignore_excludes_non_curated_paths() -> None:
    lines = {
        line.strip()
        for line in (ROOT / ".graphifyignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert ".agents/" in lines
    assert "scripts/" in lines
    assert "tasks/" in lines
    assert "AGENTS.md" in lines
    assert "CLAUDE.md" in lines
    assert "README.md" in lines
    assert "README.ko.md" in lines
    assert "SPEC.md" in lines
    assert "graphify-out/" in lines
    assert "apps/demo/screenshots/" in lines
    assert "assets/branding/" in lines
    assert "tests/fixtures/graphify/" in lines


def test_readmes_explain_graphifyignore_as_default_corpus_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_ko = (ROOT / "README.ko.md").read_text(encoding="utf-8")

    for content in (readme, readme_ko):
        assert ".graphifyignore" in content
        assert "AGENTS.md" in content
        assert "graphify-out/" in content
        assert "apps/demo/screenshots/" in content


def test_claude_settings_do_not_register_graphify_specific_hooks() -> None:
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    encoded = json.dumps(settings)

    assert "graphify-pretool.sh" not in encoded
    assert "graphify-auto-refresh.sh" not in encoded


def test_session_start_no_longer_uses_graphify_mode_note() -> None:
    content = (ROOT / "scripts" / "hooks" / "session-start.sh").read_text(encoding="utf-8")

    assert "graphify-mode-note.sh" not in content
    assert "BUILD_INFO.json" not in content


def test_docs_manager_skill_switches_to_graphify_first() -> None:
    content = (ROOT / ".agents" / "skills" / "docs-manager" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "Graphify-first" in content
    assert "Raw Source Maintenance" in content
    assert ".graphifyignore" in content
    assert ".agents/skills/graphify/SKILL.md" in content
    assert "graphify-manager" not in content
    for token in REMOVED_GRAPHIFY_CONTRACT_TOKENS:
        assert token not in content


def test_graphify_artifacts_exist() -> None:
    assert (ROOT / "graphify-out" / "GRAPH_REPORT.md").exists()
    assert (ROOT / "graphify-out" / "graph.json").exists()
    assert (ROOT / "graphify-out" / "graph.html").exists()


def test_legacy_graphify_runtime_files_are_removed() -> None:
    for relative in LEGACY_GRAPHIFY_RUNTIME_PATHS:
        assert not (ROOT / relative).exists()


def test_legacy_graphify_runtime_tests_are_removed() -> None:
    for relative in LEGACY_GRAPHIFY_TEST_PATHS:
        assert not (ROOT / relative).exists()


def test_claude_active_surface_no_longer_keeps_full_legacy_workflow() -> None:
    content = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    assert "docs/wiki" not in content
    assert "docs/sources" not in content
    assert "raw/" in content


def test_claude_points_to_upstream_graphify_skill_without_local_split_language() -> None:
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    assert ".agents/skills/graphify/SKILL.md" in claude
    assert ".agents/skills/graphify-manager/SKILL.md" not in claude
    assert "graphify-out/wiki/index.md" not in claude
    for token in REMOVED_GRAPHIFY_CONTRACT_TOKENS:
        assert token not in claude


def test_raw_readme_exists_with_source_corpus_contract() -> None:
    content = (ROOT / "raw" / "README.md").read_text(encoding="utf-8")

    assert "정본 source corpus" in content
    assert "graphify-out/" in content
    assert ".agents/" in content


def test_graphify_skill_matches_upstream_v4_orchestration_model() -> None:
    content = (ROOT / ".agents" / "skills" / "graphify" / "SKILL.md").read_text(encoding="utf-8")

    assert "/graphify" in content
    assert "result = detect(Path('INPUT_PATH'))" in content
    assert "from graphify.transcribe import transcribe_all" in content
    assert "from graphify.extract import collect_files, extract" in content
    assert "from graphify.cache import check_semantic_cache" in content
    assert 'subagent_type="general-purpose"' in content
    assert "from graphify.build import build_from_json" in content
    assert "python3 -m graphify.watch INPUT_PATH --debounce 3" in content
    assert "graphify hook install" in content
    assert "--watch" in content
    assert "graphify_prepare_corpus.sh" not in content
    assert "graphify_full_refresh.py" not in content
    assert "graphify_verify_full_refresh.py" not in content
    assert "graphify_sync_staged.sh" not in content
    assert "Surface Parity" not in content
    assert "PostToolUse auto-refresh" not in content


def test_graphify_docs_call_out_upstream_baseline_and_graphifyignore_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_ko = (ROOT / "README.ko.md").read_text(encoding="utf-8")

    for content in (readme, readme_ko):
        assert "graphify copilot install" in content
        assert "graphify hook install" in content
        assert "--watch" in content
        assert ".graphifyignore" in content
        for token in REMOVED_GRAPHIFY_CONTRACT_TOKENS:
            assert token not in content


def test_legacy_graphify_wrapper_skills_are_removed() -> None:
    assert not (ROOT / ".agents" / "skills" / "graphify-manager" / "SKILL.md").exists()
    assert not (ROOT / ".agents" / "skills" / "graphify-full" / "SKILL.md").exists()


def test_local_adaptation_exposes_graphify_single_entrypoint() -> None:
    content = (ROOT / ".agents" / "policies" / "local-adaptation.md").read_text(encoding="utf-8")

    assert "/graphify" in content
    assert ".graphifyignore" in content
    assert "graphify-manager" not in content
    assert "graphify-full" not in content
    for token in REMOVED_GRAPHIFY_CONTRACT_TOKENS:
        assert token not in content


def test_core_graphify_docs_do_not_describe_removed_local_layer() -> None:
    docs = (
        (ROOT / "AGENTS.md").read_text(encoding="utf-8"),
        (ROOT / "CLAUDE.md").read_text(encoding="utf-8"),
        (ROOT / ".github" / "copilot-instructions.md").read_text(encoding="utf-8"),
        (ROOT / ".agents" / "policies" / "local-adaptation.md").read_text(encoding="utf-8"),
        (ROOT / "README.md").read_text(encoding="utf-8"),
        (ROOT / "README.ko.md").read_text(encoding="utf-8"),
        (ROOT / ".agents" / "skills" / "docs-manager" / "SKILL.md").read_text(encoding="utf-8"),
        (ROOT / ".agents" / "skills" / "doc-manager" / "SKILL.md").read_text(encoding="utf-8"),
        (ROOT / ".agents" / "skills" / "docs-manager" / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        ),
        (ROOT / ".agents" / "skills" / "doc-manager" / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        ),
    )

    for content in docs:
        for token in REMOVED_GRAPHIFY_CONTRACT_TOKENS:
            assert token not in content


def test_codex_hooks_do_not_register_graphify_specific_hooks() -> None:
    hooks = json.loads((ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    encoded = json.dumps(hooks)

    assert "graphify-pretool.sh" not in encoded
    assert "graphify-auto-refresh.sh" not in encoded


def test_github_instructions_expose_graphify_single_entrypoint() -> None:
    content = (ROOT / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")

    assert "/graphify" in content or "graphify" in content
    assert "graphify-full" not in content
    assert "graphify-manager" not in content


def test_ci_workflow_no_longer_has_graphify_candidate_job() -> None:
    content = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "graphify-full-refresh-candidate:" not in content
    assert "scripts/graphify_prepare_corpus.sh" not in content
    assert "scripts/graphify_ci_candidate.sh" not in content
    assert "scripts/graphify_full_refresh.py" not in content


def test_docs_manager_mentions_graphifyignore_not_legacy_runtime() -> None:
    content = (ROOT / ".agents" / "skills" / "docs-manager" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "raw/" in content
    assert ".graphifyignore" in content
    assert "legacy wiki" not in content


def test_active_doc_surfaces_no_longer_point_to_legacy_wiki_paths() -> None:
    doc_manager_skill = (ROOT / ".agents" / "skills" / "doc-manager" / "SKILL.md").read_text(
        encoding="utf-8"
    )
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
    idea_refine_script = (
        ROOT / ".agents" / "skills" / "idea-refine" / "scripts" / "idea-refine.sh"
    ).read_text(encoding="utf-8")

    for content in (
        doc_manager_skill,
        documentation_skill,
        meta_skill,
        docs_manager_agent,
        doc_manager_agent,
        issue_template,
        idea_refine_script,
    ):
        assert "docs/wiki" not in content
        assert "docs/sources" not in content

    assert "docs/harness workflow" in doc_manager_skill
    assert "wiki maintenance" not in doc_manager_skill
    assert "raw/design/adr/" in documentation_skill
    assert "raw/design/notes/" in documentation_skill
    assert "raw/" in meta_skill
    assert "graph refresh / graph status" in meta_skill
    assert "→ graphify" in meta_skill
    assert "raw/design/adr" in docs_manager_agent
    assert ".agents/skills/graphify/SKILL.md" in docs_manager_agent
    assert ".agents/skills/graphify/SKILL.md" in doc_manager_agent
    assert "raw/design/notes" in issue_template
    assert 'IDEAS_DIR="ideas"' in idea_refine_script


def test_pr_creation_rules_require_template_based_flow() -> None:
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    copilot = (ROOT / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    local_adaptation = (ROOT / ".agents" / "policies" / "local-adaptation.md").read_text(
        encoding="utf-8"
    )

    assert ".github/pull_request_template.md" in claude
    assert "gh pr create --body" in claude
    assert ".github/pull_request_template.md" in copilot
    assert "--template .github/pull_request_template.md" in copilot
    assert ".github/pull_request_template.md" in local_adaptation
    assert "--body-file" in local_adaptation
