# raw

`raw/`는 이 저장소에서 Graphify가 읽는 **정본 source corpus**다.

## 역할

- `raw/design/**`
  - 설계 문서, ADR, 노트, 다이어그램, 스크린샷
- `raw/external/**`
  - 논문, 데이터셋, 모델, 실험 관련 원문/참고 자료

## Graphify 관계

- `raw/`는 입력이다.
- `graphify-out/`는 generated output이다.
- `.agents/policies/`, `.agents/playbooks/`는 하네스 운영 규칙/체크리스트이며 Graphify source가 아니다.

## 운영 원칙

- 설계 문서와 외부 자료는 `raw/` 아래에 계속 누적한다.
- Graphify full refresh는 `src/`, `tests/`, `raw/`를 읽고 `graphify-out/`만 최신 상태로 갱신한다.
- `README.md`, `README.ko.md`, `CLAUDE.md`/`AGENTS.md`는 source corpus가 아니라 결과/운영 문서다. 이슈 단위 스펙은 `raw/design/specs/ski-NNN-*.md`에 두고 source corpus의 일부다.
