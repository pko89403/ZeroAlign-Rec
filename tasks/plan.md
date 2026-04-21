# Implementation Plan: Worktree-Isolated Phase Executor

## Overview

현재 `scripts/execute.py`는 저장소 루트 작업 디렉터리에서 직접 step을 실행하고,
branch 생성, status 갱신, commit까지 함께 처리한다.
장기 운영 기능으로 발전시키려면 실행 대상 코드를 사용자 작업 트리와 분리하고,
phase 단위 실행을 전용 git worktree 안으로 격리해야 한다.

이 계획의 최종 목표는 다음이다.

1. phase 실행마다 전용 worktree를 만든다.
2. inner agent와 outer executor의 git ownership을 분리한다.
3. `docs/sources/` immutability를 hook + post-step audit 양쪽에서 강제한다.
4. 실패/중단/재시작 시에도 상태와 정리(cleanup)가 일관되게 유지된다.

## Assumptions

- 현재 `scripts/execute.py`와 `phases/`는 선택적 실행 레이어이며,
  기본 규칙은 여전히 `AGENTS.md`와 repo-local skills가 우선한다.
- phase metadata는 현재 저장소 루트의 `phases/` 아래에 유지하는 편이 운영상 더 낫다.
- worktree는 `codex/<phase-name>` branch prefix와 양립해야 한다.
- 장기 목표는 dirty main worktree에서도 안전하게 phase를 실행하는 것이다.
- 구현 전까지는 planning-only 상태를 유지하며, 이 문서는 작업 분해와 검증 기준만 다룬다.

## Architecture Decisions

- **Execution isolation**
  - phase step 실행은 저장소 루트가 아니라 전용 worktree에서 수행한다.
  - 사용자 메인 checkout과 executor checkout을 분리해 commit/staging 충돌을 막는다.

- **Single git owner**
  - commit/stage/push는 outer executor만 담당한다.
  - inner agent는 파일 수정과 step 상태 갱신만 수행한다.

- **Two-layer immutability enforcement**
  - Claude hook 단계에서 `docs/sources/` 쓰기 시도를 최대한 차단한다.
  - step 완료 후 executor가 실제 git diff를 검사해 `docs/sources/` 변경이 있으면 실패 처리한다.

- **Shared metadata, isolated code checkout**
  - `phases/` 메타데이터는 루트에 두되, worktree 안에서는 읽기/쓰기 계약을 명확히 둔다.
  - 필요하면 phase output snapshot 경로와 worktree-relative 경로를 분리한다.

- **Recovery-first lifecycle**
  - created/started/completed/failed/blocked 상태 외에 worktree 준비/정리 상태도 추적한다.
  - orphaned worktree 감지 및 정리 루틴을 별도 명시한다.

## Dependency Graph

```text
Executor contract hardening
    │
    ├── Git ownership cleanup
    │       │
    │       └── Worktree manager abstraction
    │               │
    │               ├── Metadata/state model updates
    │               ├── Step execution in isolated checkout
    │               └── Recovery and cleanup flow
    │
    └── Immutability enforcement
            │
            └── Post-step diff audit in worktree mode
```

## Phases

### Phase 1: Stabilize the current executor contract

- remove competing git ownership between inner agent and outer executor
- define clean staging/commit boundaries
- define the future worktree execution contract without changing storage layout yet

### Checkpoint: Executor contract

- current executor contract is explicit
- no ambiguous ownership of commit/stage/push remains in the design
- the worktree migration path is documented

### Phase 2: Introduce worktree execution foundations

- add worktree manager abstraction
- define per-phase worktree path, branch naming, reuse/cleanup behavior
- separate repository root metadata from execution checkout path

### Checkpoint: Worktree foundation

- a phase can be resolved to a deterministic branch + worktree path
- executor can reason about root path vs execution path without mixing them
- failure states for setup/teardown are explicit

### Phase 3: Enforce safety and immutability in isolated runs

- add Bash-level path guards where possible
- add post-step audit for `docs/sources/`
- fail safely if forbidden changes appear in worktree diff

### Checkpoint: Safety enforcement

- immutable source violations are caught even if shell commands bypass hooks
- dirty main checkout does not leak into phase commits
- secret scanning and validation still run in the isolated checkout

### Phase 4: Recovery, observability, and documentation

- define retry/restart semantics with retained worktrees
- add cleanup and orphan detection
- document operator workflow, limits, and troubleshooting

### Checkpoint: Ready for implementation

- task graph is complete
- verification story is explicit
- rollout can proceed incrementally without breaking the current optional executor

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| worktree path handling breaks relative file assumptions | High | introduce explicit `root_path` vs `execution_path` abstraction before migration |
| phase metadata and step outputs become split-brain across root/worktree | High | keep `phases/` authoritative at root and define one-way sync rules |
| inner agent still performs git actions despite guidance | Medium | remove commit instruction from prompt and add hook-level warnings/blockers |
| cleanup leaks orphaned worktrees on failure | Medium | add explicit cleanup command and startup reconciliation |
| hook-based immutability remains bypassable | High | add post-step git diff audit as the real enforcement point |

## Open Questions

- phase metadata를 루트에만 둘지, worktree 내부 mirror를 둘지
- worktree 이름을 `codex/<phase>` branch와 동일 slug로만 관리할지
- phase 완료 후 worktree를 즉시 제거할지, 디버깅을 위해 일정 기간 유지할지
- `--push` 이후 merge/PR까지 executor 범위에 포함할지

## Recommended Implementation Order

1. executor contract와 git ownership을 먼저 정리한다.
2. 그 다음 worktree manager와 execution path abstraction을 넣는다.
3. 이후 immutability audit와 cleanup lifecycle을 붙인다.
4. 마지막에 docs/tests/operator workflow를 마무리한다.
