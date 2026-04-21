# docs

이 디렉터리는 이제 기존 docs-first 지식 저장소의 legacy archive다.
현재 정본 source corpus는 `raw/`이고, primary machine-readable knowledge layer는
`graphify-out/`다. 라이브 정적 프론트엔드 데모는 `apps/demo/`로 이동했다.

## 현재 정본 경로

| 용도 | 현재 정본 |
|---|---|
| 설계/ADR/노트 source | `raw/design/` |
| 외부 문서 source | `raw/external/` |
| machine-readable graph | `graphify-out/` |
| 데모 frontend | `apps/demo/` |

## 운영 원칙

- 새 설계 문서, ADR, 외부 참고 자료는 `docs/`가 아니라 `raw/` 아래에 추가한다.
- 코드베이스/아키텍처 질의는 먼저 `graphify-out/GRAPH_REPORT.md`와 `graphify-out/graph.json`을 본다.
- `docs/wiki/`와 `docs/sources/`는 legacy archive로만 유지한다.
- 라이브 데모 UI 변경은 `apps/demo/`에서 작업한다.
- 자세한 Graphify 운영 규칙은 `AGENTS.md`, `.github/copilot-instructions.md`,
  `.harness/reference/local-adaptation.md`를 따른다.
