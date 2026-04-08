---
description: Run TDD workflow — write failing tests, implement, verify. For bugs, use the Prove-It pattern.
---

Invoke the repository-local `test-driven-development` skill.

For new features:
1. Write tests that describe the expected behavior (they should FAIL)
2. Implement the code to make them pass
3. Refactor while keeping tests green

For bug fixes (Prove-It pattern):
1. Write a test that reproduces the bug (must FAIL)
2. Confirm the test fails
3. Implement the fix
4. Confirm the test passes
5. Run `uv run pytest` for regressions and add `uv run ruff check .` / `uv run mypy src` when relevant

For browser-related issues, also invoke `browser-testing-with-devtools` when the target is actually HTML/UI output.
