# GitHub Copilot Instructions

## Project

- SID-based training-free recommender experiment
- Python 3.12, `uv`, `typer`, `rich`
- Local MLX inference on Apple Silicon
- Main code: `src/sid_reco/`
- Tests: `tests/`

## Load These First

1. Read `AGENTS.md` for the project schema and workflow rules.
2. If an imported skill example conflicts with this repository, follow `.harness/reference/local-adaptation.md`.
3. Repo-local skills live in `.agents/skills/`.

## Preferred Workflows

- Wiki, sources, ADR, and knowledge-base work: use `docs-manager` or `doc-manager`
- Specs before implementation: use `spec`
- Task breakdown: use `plan`
- Implementation in small slices: use `build`
- Test-first bug fixing and behavior changes: use `test`
- Review before merge: use `code-review-and-quality`
- Release readiness: use `ship`

## Validation Commands

- `uv sync --all-groups`
- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy src`
- `uv run sid-reco doctor`

Use domain-specific commands when relevant:

- `uv run sid-reco smoke-mlx`
- `uv run sid-reco smoke-llm "..." `
- `uv run sid-reco smoke-embed "..."`
- `uv run sid-reco build-taxonomy-step1 --help`
- `uv run sid-reco build-taxonomy-dictionary --help`

## Boundaries

- Do not modify `docs/sources/`; it is immutable source material.
- Keep wiki pages under `docs/wiki/` in Korean and always include YAML frontmatter.
- When wiki pages change, update `docs/wiki/INDEX.md` and the relevant category `README.md` together.
- Reuse existing patterns in `src/sid_reco/` and `tests/` before introducing new ones.
- Avoid new dependencies unless the task clearly requires them.
- Preserve the current Apple Silicon + MLX local-first assumptions unless the task explicitly changes support scope.

## Useful Paths

- `AGENTS.md`
- `.harness/README.md`
- `.harness/reference/local-adaptation.md`
- `.agents/skills/`
- `references/`
- `ideas/`
- `tasks/plan.md`
- `tasks/todo.md`
- `artifacts/reports/`
