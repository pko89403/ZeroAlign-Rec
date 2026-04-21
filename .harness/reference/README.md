# Harness Reference

이 디렉터리는 upstream skill pack에서 가져온 문서 스냅샷과
로컬 적응 규칙을 담는 하네스 내부 reference 레이어다.

## 포함 내용

- `getting-started.md` — 범용 사용 가이드
- `skill-anatomy.md` — `SKILL.md` 구조 규약
- `copilot-setup.md`, `cursor-setup.md`, `gemini-cli-setup.md`, `windsurf-setup.md`
- `upstream-README.md` — upstream README 스냅샷
- `upstream-AGENTS.md` — upstream AGENTS 스냅샷
- `local-adaptation.md` — 이 저장소에서의 경로/명령 보정 규칙

## 원본

- Source repository: `https://github.com/addyosmani/agent-skills`
- Imported on: `2026-04-08`

활성 스킬 자체는 `.agents/skills/`에 있고, 로컬 `agent-skills/` 미러 없이도 동작한다.
체크리스트는 루트 `references/`에 있다.
command-style prompt 초안은 `command-drafts/`, persona markdown 스냅샷은
`agent-personas/`에 보관한다.

상위 개요는 [`.harness/README.md`](../README.md)를 본다.
