# GitHub Copilot Instructions

## Project

- SID-based training-free recommender experiment
- Python 3.12, `uv`, `typer`, `rich`
- Local MLX inference on Apple Silicon
- Main code: `src/sid_reco/` (including `src/sid_reco/sid/` for Phase 1 SID work)
- Tests: `tests/`

## Load These First

1. If present, read `graphify-out/GRAPH_REPORT.md` first.
2. If present, use `graphify-out/graph.json` as the primary machine-readable codebase graph.
3. Check `graphify-out/BUILD_INFO.json` to see whether the graph is `code_update` or `full_refresh`.
3. Read `AGENTS.md` for the project schema and workflow rules.
4. If an imported skill example conflicts with this repository, follow `.harness/reference/local-adaptation.md`.
5. Repo-local skills live in `.agents/skills/`.

## Preferred Workflows

- Graphify sync/review and `raw/` source corpus maintenance: use `docs-manager` or `doc-manager`
- Full Graphify refresh automation: use `graphify-manager` or `graphify-full` when you need to inspect or rerun the staged full-refresh path explicitly
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
- `uv run sid-reco recommend --help`
- `uv run sid-reco smoke-llm "..." `
- `uv run sid-reco smoke-embed "..."`
- `uv run sid-reco build-neighbor-context --help`
- `uv run sid-reco build-taxonomy-dictionary --help`
- `uv run sid-reco structure-taxonomy-item --help`
- `uv run sid-reco structure-taxonomy-batch --help`
- `uv run sid-reco compile-sid-index --help`

## Boundaries

- Treat `raw/` as the Graphify source corpus.
- Treat `graphify-out/` as the primary machine-readable knowledge layer.
- `references/` is checklist/reference material, not Graphify input.
- Reuse existing patterns in `src/sid_reco/` and `tests/` before introducing new ones.
- Avoid new dependencies unless the task clearly requires them.
- Preserve the current Apple Silicon + MLX local-first assumptions unless the task explicitly changes support scope.
- The current recommendation runtime uses a higher default LLM generation budget (`SID_RECO_LLM_MAX_TOKENS=1024`) to keep structured JSON outputs stable.
- `compile-sid-index` now also writes `recommendation_stats.json`, and the Phase 2 recommendation runtime expects that artifact alongside the rest of `sid_index/`.

## Useful Paths

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`
- `graphify-out/BUILD_INFO.json`
- `raw/README.md`
- `raw/design/`
- `raw/external/`
- `.agents/skills/graphify-full/SKILL.md`
- `.agents/skills/graphify-manager/SKILL.md`
- `AGENTS.md`
- `.claude/settings.json`
- `.harness/README.md`
- `.harness/reference/local-adaptation.md`
- `.agents/skills/`
- `references/`
- `scripts/execute.py`
- `scripts/graphify_code_refresh.sh`
- `scripts/graphify_prepare_corpus.sh`
- `scripts/graphify_full_refresh.py`
- `scripts/graphify_verify_full_refresh.py`
- `scripts/graphify_sync_staged.sh`

## Graphify Trigger Model

- Hooks and session-start rules use the current graph and `BUILD_INFO.json` as trust signals.
- PostToolUse hooks may auto-refresh the graph after relevant local edits.
- CI may leave a candidate/reminder note, but it does not run the full refresh producer, verify staged output, or promote root `graphify-out/`.

## Pull Request Rule

- If a user asks to create a PR in natural language, still use `.github/pull_request_template.md` as the starting structure.
- Do not bypass the template with raw `gh pr create --body` or `--body-file` unless the body was first built from the repository template.
- When using `gh`, prefer `gh pr create --template .github/pull_request_template.md` or an equivalent template-filled flow.
