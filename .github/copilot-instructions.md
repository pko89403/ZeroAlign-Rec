# GitHub Copilot Instructions

## Project

SID-based training-free recommender for Python 3.12 + MLX on Apple Silicon. Main code in `src/sid_reco/`.

## Authoritative Rules

`AGENTS.md` (== `CLAUDE.md`) is the single source of truth for project schema, workflow skills, validation commands, boundaries, and useful paths. This file only adds Copilot-specific priorities.

Read in order before acting:

1. `graphify-out/GRAPH_REPORT.md` if present — architecture and community structure.
2. `graphify-out/graph.json` if present — primary machine-readable codebase graph.
3. `AGENTS.md` — project schema, 3-layer architecture, operating principles, Graphify usage model, and path boundaries.
4. `.agents/policies/local-adaptation.md` — domain details (tech stack, main modules, validation commands, Repo-local Codex commands like `spec`/`plan`/`build`/`test`/`ship`/`docs-manager`/`code-simplify`/`graphify`) and language conventions. Takes precedence when imported skill examples conflict with this repo.
5. `.agents/skills/graphify/SKILL.md` — upstream-style `/graphify` public entrypoint and follow-up graph workflow.
6. `.graphifyignore` — default corpus exclusions for `/graphify .`.

## Core Validation Gate

`uv sync --all-groups`, `uv run ruff check .`, `uv run mypy src`, `uv run pytest`. See `AGENTS.md` for domain-specific `sid-reco` commands.

## Graphify Usage Model

- Treat `.agents/skills/graphify/SKILL.md` as the authoritative upstream `/graphify` behavior.
- Treat `.graphifyignore` as the default corpus boundary for `/graphify .`.
- Do not assume a separate repo-local Graphify split or staged refresh contract unless the user explicitly asks for custom migration work.

## Pull Request Rule

- If a user asks to create a PR in natural language, still use `.github/pull_request_template.md` as the starting structure.
- Do not bypass the template with raw `gh pr create --body` or `--body-file` unless the body was first built from the repository template.
- When using `gh`, prefer `gh pr create --template .github/pull_request_template.md` or an equivalent template-filled flow.
