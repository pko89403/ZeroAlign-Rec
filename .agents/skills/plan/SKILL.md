---
name: plan
description: Shortcut wrapper for planning-and-task-breakdown. Use when the user explicitly types /plan or asks to break a spec into ordered, verifiable tasks.
---

# Plan

Use the `planning-and-task-breakdown` workflow for this repository.

## Procedure

1. 사용자가 지정한 `raw/design/specs/ski-NNN-*.md`를 먼저 읽는다. 지정이 없으면 `raw/design/specs/` 하위에서 가장 최근 파일을 기준으로 확인한 뒤, 관련 코드와 문서를 검사한다.
2. Stay in read-only planning mode.
3. Identify the dependency graph between components.
4. Slice work vertically (one complete path per task) and draft tasks with acceptance criteria + verification steps.
5. Present the execution flow, checkpoints, and ordered task list in the conversation for the user to review.
6. Use repository validations from `.agents/policies/local-adaptation.md`.

## Related

- Follow `planning-and-task-breakdown` as the source workflow.
