---
name: spec
description: Shortcut wrapper for spec-driven-development. Use when the user explicitly types /spec or asks to write a project or feature spec before implementation.
---

# Spec

Use the `spec-driven-development` workflow for this repository.

## Procedure

1. Read `AGENTS.md`, `README.md`, and `.harness/reference/local-adaptation.md`.
2. Clarify the objective, acceptance criteria, constraints, and boundaries.
3. Produce a structured `SPEC.md` in the repository root.
4. Include repository-specific commands such as:
   - `uv run pytest`
   - `uv run ruff check .`
   - `uv run mypy src`
   - `uv run sid-reco doctor`
5. Confirm the spec before implementation starts.

## Related

- Follow `spec-driven-development` as the source workflow.

