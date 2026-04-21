# references

이 디렉터리는 **저장소 밖에서 들어온 지식**과 **skill이 런타임에 참조하는 체크리스트**를 한데 모은다.
성격이 다른 4가지 자료가 섞여 있으므로 용도를 구분해서 읽는다.

## Live — repo 운영에 실제로 쓰이는 문서

| 파일 | 역할 |
|------|------|
| [`local-adaptation.md`](local-adaptation.md) | 이 저장소 고유의 경로·명령·규칙. `scripts/execute.py`의 `GUARDRAIL_FILES`에 포함되어 phase executor 프롬프트에 자동 주입된다. imported skill과 실제 repo 구조가 충돌할 때 이 파일이 **우선한다**. |

## Checklists — skill이 runtime에 링크해서 읽음

| 파일 | 참조하는 skill |
|------|---------------|
| [`accessibility-checklist.md`](accessibility-checklist.md) | `frontend-ui-engineering`, `shipping-and-launch` |
| [`performance-checklist.md`](performance-checklist.md) | `code-review-and-quality`, `performance-optimization`, `shipping-and-launch` |
| [`security-checklist.md`](security-checklist.md) | `code-review-and-quality`, `security-and-hardening`, `shipping-and-launch` |
| [`testing-patterns.md`](testing-patterns.md) | `test-driven-development` |

## Upstream — archival snapshot

| 파일 | 원본 |
|------|------|
| [`upstream-README.md`](upstream-README.md) | `addyosmani/agent-skills` README 스냅샷 (import 시점: 2026-04-08) |
| [`upstream-AGENTS.md`](upstream-AGENTS.md) | 같은 프로젝트의 AGENTS 스냅샷 |

이 둘은 **drift detection 용도**로만 유지한다. 업스트림 변경이 이 repo에 영향이 있는지 주기적으로 대조할 때 사용한다. 운영 규칙은 `local-adaptation.md`와 `CLAUDE.md`가 정본이다.

## Skill-anatomy reference

| 파일 | 용도 |
|------|------|
| [`skill-anatomy.md`](skill-anatomy.md) | 새 skill을 쓸 때 `SKILL.md` 구조 규약 참고 |

## 정책

- 새 체크리스트를 추가할 때는 이 README의 Checklists 표도 함께 갱신한다.
- upstream 스냅샷을 갱신할 때는 import 날짜를 이 README에 기록한다.
- local-adaptation.md는 imported skill 예시와 이 저장소 구조 간 차이가 발생할 때마다 업데이트한다.
- Graphify source corpus가 아니므로 `.graphifyignore`에 계속 포함한다 ([.graphifyignore:30](../.graphifyignore#L30)).
