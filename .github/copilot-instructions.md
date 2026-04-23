# GitHub Copilot Instructions

## Project

SID-based training-free recommender for Python 3.12 + MLX on Apple Silicon. Main code in `src/sid_reco/`.

## Authoritative Rules

`AGENTS.md` (== `CLAUDE.md`) is the single source of truth for project schema, workflow skills, validation commands, boundaries, and useful paths. This file only adds Copilot-specific priorities.

Read in order before acting:

1. `graphify-out/GRAPH_REPORT.md` if present — architecture and community structure.
2. `graphify-out/graph.json` if present — primary machine-readable codebase graph.
3. `graphify-out/BUILD_INFO.json` — `mode=code_update` vs `full_refresh` trust signal.
4. `AGENTS.md` — project schema, 3-layer architecture, operating principles, and skill layer overview.
5. `references/local-adaptation.md` — domain details (tech stack, main modules, validation commands, Repo-local Codex commands like `spec`/`plan`/`build`/`test`/`ship`/`docs-manager`/`code-simplify`/`graphify-full`/`graphify-manager`) and language conventions. Takes precedence when imported skill examples conflict with this repo.
6. `.agents/skills/graphify-manager/SKILL.md` — full refresh orchestration, graphify rules, and committed graph artifacts.

## Core Validation Gate

`uv sync --all-groups`, `uv run ruff check .`, `uv run mypy src`, `uv run pytest`. See `AGENTS.md` for domain-specific `sid-reco` commands.

## Graphify Trigger Model

- Hooks and session-start rules use the current graph and `BUILD_INFO.json` as trust signals.
- PostToolUse hooks may auto-refresh the graph after relevant local edits.
- CI leaves a candidate/reminder note but does not run the full refresh producer, verify staged output, or promote root `graphify-out/`.

## Pull Request Rule

- If a user asks to create a PR in natural language, still use `.github/pull_request_template.md` as the starting structure.
- Do not bypass the template with raw `gh pr create --body` or `--body-file` unless the body was first built from the repository template.
- When using `gh`, prefer `gh pr create --template .github/pull_request_template.md` or an equivalent template-filled flow.
