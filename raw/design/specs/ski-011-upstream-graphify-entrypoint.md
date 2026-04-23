# 스펙: SKI-11 — upstream Graphify public entrypoint 복구

## 가정 (Assumptions I'm Making)

1. 이 스펙은 루트 `SPEC.md` 단일 파일 관행을 `raw/design/specs/ski-NNN-*.md` 이슈 스코프 레이아웃으로 대체하는 마이그레이션(SKI 구조 전환) 이후 작성되었다.
2. 실제 구현은 전용 branch/worktree에서 진행한다. 이 스펙은 그 전제를 포함한다.
3. integration 기준선은 repo-local wrapper가 아니라 upstream Graphify가 제공하는 다음 install surface다.
   - `graphify claude install`
   - `graphify codex install`
   - `graphify opencode install`
4. 이 저장소의 3-레이어 모델(`AGENTS.md` / `graphify-out/` / `raw/`)과 `raw/` source boundary는 유지한다.
5. 현재의 staged full refresh, verify, sync, `BUILD_INFO.json` trust signal은 의도된 guardrail이며 제거 대상이 아니다.
6. 현재 public surface인 `/graphify-manager`, `/graphify-full`는 migration 완료 후 제거 대상이다.
7. upstream가 생성하는 얇은 `AGENTS.md`/`CLAUDE.md`/hook 자산은 이 저장소의 richer schema와 안전 훅을 **통째로 대체할 수 없고**, merge/composition 대상으로 다뤄야 한다.

## 목표 (Objective)

이 작업의 목표는 **original/upstream Graphify의 기본 UX를 `/graphify` 단일 public entrypoint로 복구**하면서도,
현재 저장소가 이미 갖고 있는 curated corpus와 verify gate를 그대로 보존하는 것이다.

구체적으로:

1. `/graphify`를 이 저장소의 **유일한 공개 Graphify 진입점**으로 복구한다.
2. assistant 통합은 upstream install 산출물(Claude/Codex/OpenCode)을 **1차 source of truth**로 사용한다.
3. `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`, `.codex/hooks.json`는 upstream 산출물과 **충돌 없이 merge/composition**한다.
4. repo-local guardrail은 유지한다.
   - `raw/`는 human-owned source corpus
   - `graphify-out/BUILD_INFO.json`은 trust signal
   - full refresh는 staged corpus -> producer -> verify -> sync 순서를 강제
   - raw `graphify update .`는 full refresh 대체 경로가 아님
5. `/graphify-manager`, `/graphify-full`를 제거하고, 문서/테스트/하네스를 `/graphify` 중심으로 재정렬한다.

## 원래 Graphify와의 동일성 범위

이번 스펙의 목표는 **upstream Graphify와 public UX/mental model을 최대한 같게 만드는 것**이지,
이 저장소의 내부 운영 정책까지 byte-for-byte 동일하게 만드는 것은 아니다.

### 같아지는 부분

1. 공개 진입점이 `/graphify` 하나로 복구된다.
2. assistant integration 기준선이 upstream install 산출물로 돌아간다.
3. 사용자는 repo-specific command를 먼저 배우지 않고, upstream Graphify 감각으로 진입할 수 있다.
4. 가능 범위에서 `query`, `path`, `explain` 계열 follow-up surface도 upstream command model 기준으로 검토한다.

### 의도적으로 남기는 차이

1. full refresh source boundary는 `src/`, `tests/`, `raw/`로 제한한다.
2. `raw/`만 human-owned source corpus로 취급한다.
3. `graphify-out/BUILD_INFO.json`의 `mode`/`verified`를 공식 trust signal로 유지한다.
4. semantic full refresh는 staged `prepare -> producer -> verify -> sync`를 반드시 거친다.
5. raw `graphify update .`는 `code_update` 전용 bootstrap으로만 사용한다.

즉 최종 결과는 **“겉으로는 원래 Graphify처럼 쓰이되, 안쪽에는 이 저장소의 검증/신뢰 모델이 남아 있는 상태”**다.

## 비목표 (Non-Goals)

이 스펙은 **다음을 포함하지 않는다**:

- upstream Graphify 엔진 자체를 재구현하거나 포크하는 일
- `graphifyy` 패키지나 upstream CLI를 repo-local bespoke implementation으로 치환하는 일
- full refresh source corpus를 `src/`, `tests/`, `raw/` 밖으로 넓히는 일
- `.agents/`, `scripts/`, `README*`, `AGENTS.md`, `CLAUDE.md`를 Graphify source input으로 승격하는 일 (단 `raw/design/specs/`는 이미 source corpus 일부)
- raw `graphify update .`를 semantic full refresh의 동등 경로로 인정하는 일
- verify gate, auto-refresh, `BUILD_INFO.json` trust model을 제거하거나 약화하는 일
- `/graphify` 외의 새 public Graphify entrypoint를 추가로 유지하는 일
- unrelated Query-SID, 추천 로직, MLX 파이프라인 범위의 변경

## 현재 문제 (Why Change)

현재 저장소는 Graphify를 완전히 없앤 상태가 아니라, **repo-local full-refresh orchestration 중심으로 재배치**한 상태다.

### 현재 상태

| 항목 | 현재 |
|---|---|
| public entrypoint | `/graphify-manager`, `/graphify-full` |
| code-only refresh | `scripts/graphify_code_refresh.sh` -> `graphify update .` -> `mode=code_update` |
| full semantic refresh | staged corpus -> `scripts/graphify_full_refresh.py` -> `scripts/graphify_verify_full_refresh.py` -> `scripts/graphify_sync_staged.sh` |
| trust signal | `graphify-out/BUILD_INFO.json` |
| public docs | README / Copilot instructions / local adaptation이 `graphify-manager` 계열을 안내 |
| assistant integration baseline | upstream installer가 아니라 repo-local wrapper/문서 중심 |

### 문제점

1. upstream Graphify의 기본 mental model인 **“assistant 안에서 `/graphify`로 폴더를 knowledge graph로 만든다”**가 public surface에서 사라졌다.
2. Claude/Codex/OpenCode install surface가 현재 설계의 baseline이 아니라, 나중에 참고하는 부가 정보로 밀려났다.
3. `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`, `.codex/hooks.json`는 이미 존재하지만, upstream integration과의 composition 규칙이 문서화되어 있지 않다.
4. 결과적으로 사용자는 **repo-specific command를 먼저 학습**해야 하고, upstream Graphify를 기대한 접근과 어긋난다.

## Source of Truth 계층

이번 복구는 “upstream 우선 + repo-local 예외 최소화” 원칙을 따른다.

| 관심사 | 1차 기준 | repo-local 제약 |
|---|---|---|
| public `/graphify` UX | upstream Graphify command model | skill wrapper는 thin composition만 수행 |
| assistant integration | `graphify claude install`, `graphify codex install`, `graphify opencode install` 산출물 | 기존 `AGENTS.md`, `CLAUDE.md`, hook 파일은 보존하며 merge |
| source corpus | upstream의 느슨한 any-folder model | 이 저장소에서는 `src/`, `tests/`, `raw/`만 curated full-refresh 대상 |
| docs/design semantic coverage | upstream general graph build | `raw/` source boundary + verify gate 필수 |
| graph freshness/trust | upstream refresh 결과 | `graphify-out/BUILD_INFO.json`의 `mode`/`verified`를 공식 trust signal로 사용 |

## 공개 계약 (Public Contract)

### 1. `/graphify`가 단일 public entrypoint다

- 구현 후 사용자가 Graphify 작업을 시작할 때 기본 진입점은 `/graphify` 하나다.
- `/graphify-manager`, `/graphify-full`는 migration 이후 public surface에서 제거한다.
- 문서, skill index, Copilot instructions, 테스트는 모두 이 계약을 기준으로 갱신한다.

### 2. `/graphify`는 upstream mental model을 우선한다

`/graphify`는 최소한 아래 성격의 요청을 upstream Graphify 감각으로 수용해야 한다.

1. 현재 그래프 생성/갱신
2. 그래프 상태와 trust signal 확인
3. 특정 refresh가 code update인지 full refresh인지 안내
4. 가능하다면 `query`, `path`, `explain` 계열 follow-up surface도 `/graphify` 아래에서 설명/지원

단, slash 환경이나 repo-local 제약 때문에 1차 구현에서 보류되는 sub-surface가 있더라도:

- legacy command로 조용히 우회하지 않는다.
- `/graphify`가 **지원/보류/예외 조건**을 명시적으로 설명해야 한다.

### 3. code update와 full refresh의 경계는 유지한다

`/graphify`는 upstream UX를 제공하더라도, 내부 동작은 다음 구분을 유지해야 한다.

#### code update

- 경로: `scripts/graphify_code_refresh.sh`
- 핵심 명령: `uvx --from "graphifyy==0.4.23" graphify update .`
- 산출물: `graphify-out/graph.html`, `GRAPH_REPORT.md`, `graph.json`, `BUILD_INFO.json`
- 결과 의미: `BUILD_INFO.json.mode = "code_update"`

#### full refresh

- 경로:
  1. `bash scripts/graphify_prepare_corpus.sh`
  2. `uv run --with graphifyy==0.4.23 python scripts/graphify_full_refresh.py .graphify-work/corpus`
  3. `python3 scripts/graphify_verify_full_refresh.py .graphify-work/corpus/graphify-out`
  4. `bash scripts/graphify_sync_staged.sh`
- 결과 의미:
  - staged verify가 통과해야 root sync 가능
  - root `graphify-out/BUILD_INFO.json`이 `mode=full_refresh`이고 `verified=true`일 때만 raw source corpus 반영 상태로 간주

### 4. `raw/` source boundary는 public contract에 포함된다

full refresh에서 사람 문맥 source corpus는 `raw/`가 유일하다.

- semantic required: `raw/design/adr/**`, `raw/design/notes/**`
- semantic optional: `raw/design/specs/**`
- presence only: `raw/design/diagrams/**`, `raw/design/screenshots/**`, `raw/external/**`

다음은 Graphify source input이 아니다.

- `.agents/`
- `.agents/policies/`
- `scripts/`
- `README*`
- `AGENTS.md`
- `CLAUDE.md`

### 5. raw `graphify update .`는 full refresh 대체 경로가 아니다

- `/graphify`가 upstream UX를 보여주더라도, semantic docs/design coverage가 필요한 상황에서는 staged full refresh로 분기해야 한다.
- `graphify update .`는 **code bootstrap refresh**로만 취급한다.
- public docs와 skill 설명은 이 차이를 분명히 드러내야 한다.

## Assistant별 integration / composition 계약

### Claude

- upstream의 `graphify claude install` 산출물을 baseline으로 분석한다.
- 하지만 이 저장소의 `.claude/settings.json`이 현재 보유한 active hook surface는 유지해야 한다.
  - `bash scripts/hooks/graphify-pretool.sh`
  - `bash scripts/hooks/graphify-auto-refresh.sh`
- `CLAUDE.md`는 얇은 upstream template로 교체하지 않고, repo-local schema 문서를 유지하면서 upstream directive를 흡수한다.

### Codex

- upstream의 `graphify codex install` 산출물을 baseline으로 분석한다.
- `.codex/hooks.json`의 현재 active behaviors는 유지해야 한다.
  - `SessionStart` -> `scripts/hooks/session-start.sh`
  - `Stop` -> `scripts/hooks/claude-stop-checks.sh`
  - `PreToolUse` Graphify pretool + destructive-command / graphify-out / secret-file guard
  - `PostToolUse` auto-refresh + git secret check
- Codex 쪽에서도 `/graphify`가 repo-local public surface로 노출되도록 wrapper skill과 문서가 정렬돼야 한다.

### OpenCode

- upstream의 `graphify opencode install` 산출물도 1차 기준으로 inventory한다.
- 저장소가 현재 OpenCode를 주 실행 환경으로 쓰지 않더라도, 최소한 다음은 문서화되어야 한다.
  1. upstream가 생성하는 integration 자산 종류
  2. 이 저장소의 schema/hook와 충돌 시 merge/composition 원칙
  3. `/graphify` public contract와의 정합성

### 공통 규칙

1. upstream installer가 생성하는 파일/문구/manifest는 **reference only가 아니라 source of truth**다.
2. repo-local 파일은 이를 흡수하는 composition layer이지, 별도 계약을 창조하는 레이어가 아니다.
3. upstream installer 산출물이 현재 저장소 파일과 충돌할 때는:
   - 통째 overwrite 금지
   - preserved local guardrail 명시
   - merge 지점과 책임 경계 문서화

## 구현 방향 (Design Direction)

### Step 0. 전용 branch/worktree 준비

- Graphify public surface 복구는 breaking change 성격이 있으므로 전용 branch/worktree에서 진행한다.
- spec/implementation/test/doc migration 모두 이 격리된 작업 단위 안에서 수행한다.

### Step 1. upstream install 자산 inventory

반드시 먼저 정리할 것:

1. `graphify claude install`이 생성/수정하는 자산
2. `graphify codex install`이 생성/수정하는 자산
3. `graphify opencode install`이 생성/수정하는 자산
4. 각 assistant별로 이 저장소의 현재 파일과 충돌하는 지점
5. 그대로 유지 가능한 부분 / merge 필요한 부분 / 1차 보류 부분

### Step 2. thin `/graphify` composition layer 추가

- `.agents/skills/graphify/SKILL.md`를 추가한다.
- 필요 시 `agents/openai.yaml`을 둔다.
- 이 wrapper는 repo-local bespoke workflow를 설명하는 문서가 아니라,
  **upstream Graphify contract를 이 저장소 제약 안에 매핑하는 얇은 composition layer**여야 한다.

### Step 3. legacy skill 역할 흡수

기존 `graphify-manager` / `graphify-full`가 설명하던 staged producer -> verify -> sync는
`/graphify` contract 안의 explicit full-refresh branch로 흡수한다.

- full refresh는 사라지지 않는다.
- public entrypoint만 `/graphify`로 통합된다.
- implementation 중간 단계에서 temporary alias를 둘 수는 있지만, 최종 상태에서 public docs는 `/graphify`만 안내한다.

### Step 4. 문서/지침/테스트 migration

최소한 아래 surface는 `/graphify` 기준으로 다시 써야 한다.

- `README.md`
- `README.ko.md`
- `.github/copilot-instructions.md`
- `.agents/policies/local-adaptation.md`
- `AGENTS.md`
- `CLAUDE.md`
- `tests/test_graphify_harness.py`

## 완료 조건 (Acceptance Criteria)

1. 저장소에 `/graphify` repo-local skill이 존재한다.
2. `/graphify`가 단일 public Graphify entrypoint로 문서화된다.
3. assistant integration 기준이 upstream installer 산출물이라는 점이 구현/문서/테스트에서 드러난다.
4. `.claude/settings.json`과 `.codex/hooks.json`의 현재 guardrail/auto-refresh/session-start/stop 동작이 유지된다.
5. `raw/` source boundary, staged full refresh, verify gate, `BUILD_INFO.json` trust signal이 그대로 유지된다.
6. `graphify update .`는 여전히 `code_update` 전용으로만 취급된다.
7. `/graphify-manager`, `/graphify-full`는 최종 public surface에서 제거된다.
8. README / Copilot instructions / local adaptation / AGENTS / CLAUDE / tests가 모두 같은 계약을 설명한다.

## 검증 (Validation)

구현 전후 기본 게이트:

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run mypy src
uv run sid-reco doctor
```

추가로 확인할 것:

1. `tests/test_graphify_harness.py`가 `/graphify` 존재와 legacy surface 제거를 검증하도록 갱신되었는가
2. `README.md`, `.github/copilot-instructions.md`, `.agents/policies/local-adaptation.md`가 동일한 public contract를 설명하는가
3. full refresh 경로가 여전히 `prepare -> producer -> verify -> sync` 순서를 강제하는가

## 주요 리스크 (Risks)

1. upstream installer 산출물 버전 차이로 generated manifest/hook 형태가 달라질 수 있다.
2. upstream의 느슨한 “any folder” UX와 이 저장소의 curated corpus/verify gate 사이에는 구조적 긴장이 있다.
3. `AGENTS.md`/`CLAUDE.md`를 얇은 upstream template로 덮으면 현재 저장소의 richer schema가 사라질 수 있다.
4. `/graphify-manager`, `/graphify-full` 제거는 문서와 테스트에서 광범위한 drift를 유발할 수 있다.

## 구현 시작 전 확인

이 스펙이 승인되면 다음 순서로 진행한다.

1. 전용 branch/worktree 생성
2. upstream Claude/Codex/OpenCode install 자산 inventory
3. `/graphify` thin composition layer 설계
4. legacy skill migration
5. 문서/테스트/하네스 정렬
