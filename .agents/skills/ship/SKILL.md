---
name: ship
description: Shortcut wrapper for shipping-and-launch. Use when the user explicitly types /ship or asks for a release-readiness or deployment checklist.
---

# Ship

Use `shipping-and-launch` for repository release checks.

## Procedure

1. Read `references/local-adaptation.md`.
2. Verify code quality:
   - `uv run pytest`
   - `uv run ruff check .`
   - `uv run mypy src`
3. Verify environment and runtime paths:
   - `uv run sid-reco doctor`
   - relevant `uv run sid-reco ...` smoke commands
4. Confirm artifacts, docs, and rollback considerations.

## Related

- `shipping-and-launch`

