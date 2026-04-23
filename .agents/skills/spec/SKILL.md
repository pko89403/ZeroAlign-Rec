---
name: spec
description: Shortcut wrapper for spec-driven-development. Use when the user explicitly types /spec or asks to write a project or feature spec before implementation.
---

# Spec

Use the `spec-driven-development` workflow for this repository.

## Procedure

1. Read `AGENTS.md`, `README.md`, and `.agents/policies/local-adaptation.md`. `raw/design/specs/` 하위 파일명만 스캔해 다음 번호와 기존 패턴을 확인한다 (내용 선탐독 불필요).
2. Clarify the objective, acceptance criteria, constraints, and boundaries.
3. 새 spec은 `raw/design/specs/ski-NNN-<slug>.md` 형식으로 생성한다. `NNN`은 3자리 zero-pad된 다음 번호, `<slug>`는 짧은 영어 kebab-case 요약.
4. Include repository-specific commands such as:
   - `uv run pytest`
   - `uv run ruff check .`
   - `uv run mypy src`
   - `uv run sid-reco doctor`
5. Confirm the spec before implementation starts.

## Related

- Follow `spec-driven-development` as the source workflow.

