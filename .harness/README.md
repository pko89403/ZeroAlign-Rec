# Harness Support Assets

이 디렉터리는 이 저장소의 하네스 엔지니어링 support 자산을 모아둔 곳이다.

## 역할 구분

- **tool-facing entrypoints**
  - `graphify-out/` — primary committed knowledge graph artifacts
  - `.claude/settings.json` — Claude Code active safety hooks
  - `.github/` — Copilot CLI / Chat 진입 규칙과 agent persona
  - `.agents/skills/` — repo-local skill 본체
  - `AGENTS.md` — 최상위 규칙 / 스키마 정본
  - `scripts/hooks/` — canonical hook implementation

- **harness support assets**
  - `.harness/reference/` — imported agent-skills 문서 스냅샷, 로컬 적응 규칙, command draft, persona 스냅샷
  - `.harness/hooks/` — Claude/Codex hook entrypoint wrapper와 support hook 자산

## 왜 루트 진입점은 그대로 두는가

Copilot과 skill discovery는 `.github/`, `.agents/skills/`, `AGENTS.md` 같은
관습적 경로를 직접 읽을 가능성이 높다. 따라서 support 자산만 `.harness/` 아래로
모으고, 실제 진입점은 그대로 유지한다.

## 루트에 남겨두는 관련 경로

- `references/` — imported skill이 직접 참조하는 체크리스트
- `artifacts/reports/` — HTML 보고서 등 생성 산출물
- `.graphify-work/` — ignored staged corpus/work graph for full refresh automation

## 운영 원칙

1. 새 support 문서나 스냅샷을 추가할 때는 우선 `.harness/` 아래에 둔다.
2. 외부 툴이 직접 읽는 파일은 `.claude/settings.json`, `.github/`, `.agents/skills/`, `AGENTS.md`에 유지한다.
3. 실제 hook 구현은 `scripts/hooks/`에 두고, `.harness/hooks/`는 Claude/Codex가 직접 참조하는 wrapper와 support hook 자산을 유지한다.
