---
name: test
description: Shortcut wrapper for test-driven-development. Use when the user explicitly types /test or asks to reproduce a bug, write failing tests, and prove a fix.
---

# Test

Use `test-driven-development` for new behavior and bug fixes.

## Procedure

1. Write the failing test first.
2. Confirm the test fails for the intended reason.
3. Implement the minimum change.
4. Re-run targeted tests, then `uv run pytest`.
5. Add `uv run ruff check .` and `uv run mypy src` when relevant.

## Related

- Follow `test-driven-development` as the source workflow.

