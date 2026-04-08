---
description: Implement the next task incrementally — build, test, verify, commit
---

Invoke the repository-local `incremental-implementation` skill alongside `test-driven-development`.
Read `.harness/reference/local-adaptation.md` before applying repository-specific validation steps.

Pick the next pending task from the plan. For each task:

1. Read the task's acceptance criteria
2. Load relevant context (existing code, patterns, types)
3. Write a failing test for the expected behavior (RED)
4. Implement the minimum code to pass the test (GREEN)
5. Run targeted tests first, then the relevant repository validations:
   - `uv run pytest`
   - `uv run ruff check .`
   - `uv run mypy src`
   - `uv run sid-reco doctor` for environment-sensitive changes
6. Run the relevant CLI command or smoke path to verify behavior
7. Commit with a descriptive message
8. Mark the task complete and move to the next one

If any step fails, follow the `debugging-and-error-recovery` skill.
