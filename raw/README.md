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
- `references/`는 하네스 체크리스트/참고자료이며 Graphify source가 아니다.

## 운영 원칙

- 설계 문서와 외부 자료는 `raw/` 아래에 계속 누적한다.
- Graphify full refresh는 `src/`, `tests/`, `raw/`를 읽고 `graphify-out/`만 최신 상태로 갱신한다.
- `README.md`, `README.ko.md`, `SPEC.md`, `CLAUDE.md`/`AGENTS.md`는 source corpus가 아니라 결과/운영 문서다.
