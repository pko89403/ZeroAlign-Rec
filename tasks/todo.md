# Todo: Worktree-Isolated Phase Executor

## Task 1: Define executor ownership boundaries

**Description:** `scripts/execute.py`의 책임을 명확히 나눈다. 특히 commit/stage/push는 outer executor만 담당하고, inner agent는 파일 수정과 step 상태 갱신만 담당하는 계약으로 정리한다.

**Acceptance criteria:**
- [ ] inner agent prompt에서 git ownership이 제거된 목표 상태가 문서화된다
- [ ] outer executor가 유일한 git owner라는 규칙이 plan/doc 수준에서 고정된다
- [ ] dirty worktree와 unrelated change가 왜 위험한지 설계 문서에 설명된다

**Verification:**
- [ ] `tasks/plan.md`와 `tasks/todo.md`에 ownership rule이 일관되게 반영되어 있다
- [ ] 검토 기준이 `scripts/execute.py` 현재 문제점과 연결된다

**Dependencies:** None

**Files likely touched:**
- `tasks/plan.md`
- `tasks/todo.md`

**Estimated scope:** Small

## Task 2: Specify the worktree execution model

**Description:** phase 실행을 위한 전용 worktree lifecycle을 설계한다. branch naming, worktree path, reuse policy, teardown policy를 명시한다.

**Acceptance criteria:**
- [ ] root checkout과 execution checkout의 역할이 분리되어 정의된다
- [ ] phase name → branch → worktree path 매핑 규칙이 정해진다
- [ ] setup failure, missing worktree, stale worktree의 처리 방식이 정리된다

**Verification:**
- [ ] dependency graph에 worktree manager 계층이 포함된다
- [ ] lifecycle이 최소 create / reuse / cleanup / reconcile 단계를 가진다

**Dependencies:** Task 1

**Files likely touched:**
- `tasks/plan.md`
- `tasks/todo.md`

**Estimated scope:** Small

## Checkpoint: Contract and lifecycle

- [ ] git ownership과 worktree lifecycle의 책임 분리가 문서상 명확하다
- [ ] 현재 executor를 어디까지 호환 유지할지 결정되어 있다

## Task 3: Design metadata and path abstraction

**Description:** `phases/` metadata는 루트에 남기고, 실행 코드는 worktree에서 돌아가도록 경로 모델을 설계한다. `root_path`, `execution_path`, `phase_metadata_path`를 분리한다.

**Acceptance criteria:**
- [ ] metadata authoritative location이 하나로 정해진다
- [ ] step prompt, output snapshot, status file 경로 해석 규칙이 정의된다
- [ ] relative path가 worktree migration에서 깨질 수 있는 지점이 식별된다

**Verification:**
- [ ] 경로 모델이 root/worktree split-brain 위험을 직접 다룬다
- [ ] `phases/README.md`와 호환 가능한 운영 해석이 유지된다

**Dependencies:** Task 2

**Files likely touched:**
- `tasks/plan.md`
- `tasks/todo.md`

**Estimated scope:** Medium

## Task 4: Plan immutability enforcement as a two-layer control

**Description:** `docs/sources/` immutability를 hook 차단과 post-step audit 두 단계로 강제하는 설계를 만든다.

**Acceptance criteria:**
- [ ] Bash hook 수준 예방책이 정의된다
- [ ] executor가 실제 diff를 검사하는 post-step audit이 요구사항으로 포함된다
- [ ] violation 발생 시 step status와 operator message 정책이 정리된다

**Verification:**
- [ ] 우회 가능한 shell mutation 경로가 명시적으로 다뤄진다
- [ ] immutability enforcement가 hook-only가 아니라 audit-backed로 정의된다

**Dependencies:** Task 2

**Files likely touched:**
- `tasks/plan.md`
- `tasks/todo.md`

**Estimated scope:** Small

## Checkpoint: Isolation and safety model

- [ ] worktree 격리와 immutability enforcement가 함께 설명된다
- [ ] dirty main checkout에서도 안전해야 한다는 목표가 유지된다

## Task 5: Define recovery and cleanup semantics

**Description:** 실패, blocked, 중단, 재시작, orphaned worktree 상황에서 executor가 어떻게 복구되는지 정리한다.

**Acceptance criteria:**
- [ ] retry가 worktree를 재사용할지 재생성할지 규칙이 정해진다
- [ ] blocked/error 상태에서 operator가 수행할 cleanup 절차가 정의된다
- [ ] orphaned worktree 감지와 정리 루틴이 계획에 포함된다

**Verification:**
- [ ] 상태 전이와 worktree lifecycle이 충돌하지 않는다
- [ ] cleanup 없는 long-running feature가 되지 않도록 guardrail이 있다

**Dependencies:** Task 3

**Files likely touched:**
- `tasks/plan.md`
- `tasks/todo.md`

**Estimated scope:** Small

## Task 6: Define verification and test strategy for the migration

**Description:** worktree 기반 executor를 실제로 검증할 테스트 층을 설계한다. unit test, temp git repo integration test, hook validation, dirty-worktree regression test를 포함한다.

**Acceptance criteria:**
- [ ] 최소 단위 테스트와 통합 테스트 범위가 구분된다
- [ ] dirty worktree leakage regression test가 포함된다
- [ ] `docs/sources/` mutation detection test가 포함된다
- [ ] 기존 repo validation chain과의 관계가 명시된다

**Verification:**
- [ ] `uv run pytest`
- [ ] `uv run ruff check .`
- [ ] `uv run mypy src`
- [ ] 테스트 전략이 temp repo / worktree 생성까지 포괄한다

**Dependencies:** Task 4, Task 5

**Files likely touched:**
- `tasks/plan.md`
- `tasks/todo.md`

**Estimated scope:** Medium

## Task 7: Plan rollout and documentation updates

**Description:** 새 executor가 도입될 때 README, AGENTS, local adaptation, phases docs, operator usage 문서를 어떤 순서로 바꿀지 정리한다.

**Acceptance criteria:**
- [ ] 운영 문서 업데이트 대상이 모두 나열된다
- [ ] optional feature에서 supported feature로 승격되는 조건이 정의된다
- [ ] rollback plan과 migration note가 포함된다

**Verification:**
- [ ] 문서 변경 범위가 `.github/`, `.harness/`, `README*`, `AGENTS.md`, `phases/README.md`를 포함한다
- [ ] operator-facing command examples가 업데이트 대상으로 명시된다

**Dependencies:** Task 6

**Files likely touched:**
- `tasks/plan.md`
- `tasks/todo.md`

**Estimated scope:** Small

## Final Checkpoint

- [ ] worktree-isolated executor를 구현하기 위한 ordered task graph가 완성되었다
- [ ] 각 task에 acceptance criteria와 verification이 있다
- [ ] 장기 운영 관점의 핵심 위험이 plan 문서에 반영되어 있다
