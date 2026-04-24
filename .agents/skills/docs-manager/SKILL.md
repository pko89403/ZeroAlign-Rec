---
name: docs-manager
description: "Manage the repository documentation and Graphify source corpus end-to-end. Use when: maintain raw/, review Graphify artifacts, update README.md, sync AGENTS.md, sync .github/copilot-instructions.md, sync .agents/policies/local-adaptation.md, sync .agents/skills/graphify/SKILL.md, or run a docs/harness sync after code changes."
argument-hint: "raw sync, graph review, ADR update, or docs sync"
---

# docs-manager

Graphify-first 지식 레이어(`graphify-out/`)와 human-owned source corpus(`raw/`),
그리고 저장소 루트 문서/하네스 진입점(`README.md`, `AGENTS.md`,
`.github/copilot-instructions.md`, `.agents/policies/local-adaptation.md`, `.agents/skills/graphify/SKILL.md`)을 함께 관리하는 스킬이다.

## When to Use

- `raw/` 아래 설계 source, ADR, 외부 문서를 추가/정리할 때
- `graphify-out/GRAPH_REPORT.md`를 검토해 하네스/README 반영이 필요한지 점검할 때
- 코드/CLI/워크플로 변경 후 사용자-facing 문서와 하네스 규칙을 한 번에 정리할 때

## Procedure

### Step 0: 스키마 로드

항상 프로젝트 루트의 `AGENTS.md`를 먼저 읽는다.
`raw/` source corpus 모델, `graphify-out/` generated output, upstream `/graphify` 사용 모델, `.graphifyignore` boundary가 이 파일에 정의되어 있다.

sync/update 작업이라면 추가로 아래 파일을 함께 읽는다.

- `raw/README.md`
- `graphify-out/GRAPH_REPORT.md` (존재 시)
- `graphify-out/graph.json` (존재 시)
- `README.md`
- `.github/copilot-instructions.md`
- `.agents/policies/local-adaptation.md`
- `.agents/skills/graphify/SKILL.md`
- `.graphifyignore`

### Operation: Raw Source Maintenance

`raw/`를 Graphify source corpus 관점에서 유지한다.

1. `raw/design/adr/`에 ADR을 추가하거나 갱신한다
2. `raw/design/notes/`에 설계 노트/개요를 추가하거나 갱신한다
3. `raw/external/`에 논문/데이터셋/모델/실험 자료를 정리한다
4. `.agents/policies/`, `.agents/playbooks/`는 Graphify source가 아니므로 source corpus와 섞지 않는다

### Operation: Graph Review

Graphify 산출물과 corpus boundary를 사람이 읽는 문서와 하네스 규칙에 연결한다.

1. `graphify-out/GRAPH_REPORT.md`를 읽는다
2. 새 핵심 노드, community, drift를 확인한다
3. `.graphifyignore`가 기본 `/graphify .` 입력 경계와 맞는지 확인한다
4. 아래 문서 반영이 필요한지 판단한다
   - `README.md`
   - `AGENTS.md`
   - `.github/copilot-instructions.md`
   - `.agents/policies/local-adaptation.md`
   - `.agents/skills/graphify/SKILL.md`
   - `.github/pull_request_template.md`와 PR workflow 문구

### Operation: Sync

코드/CLI/워크플로 변경 뒤 문서와 하네스 규칙을 한 번에 동기화한다.

1. 변경 범위를 파악한다
2. `raw/`와 `graphify-out/GRAPH_REPORT.md` 사이 드리프트를 확인한다
3. `.graphifyignore`가 기본 corpus boundary 설명과 맞는지 확인한다
4. 아래 파일에 새 워크플로/명령/규칙을 반영한다
    - `README.md`
    - `AGENTS.md`
    - `.github/copilot-instructions.md`
   - `.agents/policies/local-adaptation.md`
   - `.agents/skills/graphify/SKILL.md`
   - `.github/pull_request_template.md` 관련 운영 규칙

## Quality Checks

- [ ] `raw/` 구조가 source corpus 역할에 맞게 유지되는가?
- [ ] `graphify-out/graph.html`, `GRAPH_REPORT.md`, `graph.json`이 존재하는가?
- [ ] `.graphifyignore`가 기본 `/graphify .` 입력 경계를 올바르게 설명하는가?
- [ ] `README.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `.agents/policies/local-adaptation.md`, `.agents/skills/graphify/SKILL.md`가 `raw/` 모델과 일치하는가?
- [ ] PR 생성 규칙이 `.github/pull_request_template.md` 기준과 일치하는가?
- [ ] `.agents/policies/`, `.agents/playbooks/`가 Graphify source처럼 취급되고 있지 않은가?

## Key Conventions

- **Source corpus**: `raw/`
- **Generated graph**: `graphify-out/`
- **Default corpus boundary**: `.graphifyignore`
- **Graph entrypoint**: upstream `.agents/skills/graphify/SKILL.md`
