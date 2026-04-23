---
name: plan
description: Shortcut wrapper for planning-and-task-breakdown. Use when the user explicitly types /plan or asks to break a spec into ordered, verifiable tasks.
---

# Plan

Use the `planning-and-task-breakdown` workflow for this repository.

## Procedure

1. Read `SPEC.md` if it exists, then inspect the relevant code and docs.
2. Stay in read-only planning mode.
3. Identify the dependency graph between components.
4. Slice work vertically (one complete path per task) and draft tasks with acceptance criteria + verification steps.
5. Present the execution flow, checkpoints, and ordered task list in the conversation for the user to review.
6. Use repository validations from `.agents/policies/local-adaptation.md`.

## Related

- Follow `planning-and-task-breakdown` as the source workflow.
