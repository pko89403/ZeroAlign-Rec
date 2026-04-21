---
title: "Taxonomy Dictionary 개발 이슈 개요"
date: 2026-04-08
type: overview
sources: []
---

# Taxonomy Dictionary 개발 이슈 개요

## 범위

이 문서는 `build-taxonomy-dictionary` 구현 및 검증 과정에서 실제로 발생한 오류와 그 처리 상태를 정리한다.
대상 범위는 테스트 실행, 정적 검증, CLI summary 검토, 실제 MLX LLM 실행, 결과 리포트 생성까지 포함한다.

## 주제 요약

taxonomy dictionary 기능 자체는 구현되었고, mocked LLM 기반 테스트는 모두 통과했다.
초기 구현에서는 입력 크기, JSON 파싱, empty output, CLI 가시성 쪽에서 몇 가지 문제가 확인되었지만
후속 hardening 후 현재는 실제 로컬 MLX LLM으로 end-to-end 생성과 HTML 리포트 생성까지 완료했다.

### 1. `uv` 홈 캐시 접근 오류

- 증상:
  - `uv run ruff check .`
  - `uv run mypy src`
  - `uv run sid-reco build-taxonomy-dictionary --help`
  실행 시 `~/.cache/uv` 접근 중 `Operation not permitted` 발생
- 원인:
  - 현재 세션의 샌드박스가 사용자 홈 캐시 디렉터리 쓰기를 허용하지 않음
- 조치:
  - 프로젝트 설정에 `cache-dir = ".uv_cache"`를 추가해 홈 캐시 대신 저장소 내부 캐시를 사용하도록 변경
- 현재 상태:
  - 기존의 `~/.cache/uv` 권한 오류는 재현되지 않음

### 2. `uv` 런타임 panic

- 증상:
  - 일부 `uv run ...` 명령에서 `system-configuration` 관련 panic 발생
- 원인:
  - 현재 샌드박스 환경에서 `uv` 런타임이 macOS system configuration 접근 중 비정상 종료
- 결과:
  - 코드 오류가 아니라 `uv` 실행 경로 자체의 환경 문제로 판단
- 우회:
  - `.venv/bin/ruff check .`
  - `.venv/bin/mypy src`
  - `.venv/bin/python -m sid_reco.cli ...`
  방식으로 검증 수행
- 현재 상태:
  - `uv run pytest`는 통과
  - 일부 `uv run` 경로는 여전히 panic이 남아 있음

### 3. 실제 MLX LLM 실행 중 Metal 초기화 크래시

- 증상:
  - `.venv/bin/python -m sid_reco.cli build-taxonomy-dictionary ...`
  실행 시 `NSRangeException`
  - stack trace 상 `libmlx.dylib`의 Metal device 초기화 단계에서 종료
- 원인:
  - 현재 세션에서 MLX가 사용할 Metal device 목록을 정상 확보하지 못한 것으로 보임
- 영향:
  - 원래는 프로세스 전체가 비정상 종료되었음
- 조치:
  - MLX import 전 child process probe를 추가해, 네이티브 crash를 메인 프로세스 abort 대신 `RuntimeError`로 변환
- 현재 상태:
  - taxonomy dictionary 명령은 hard crash 대신 진단 가능한 에러 메시지를 반환하도록 개선되었다
  - 이후 로컬 터미널 세션에서 실제 end-to-end 생성이 성공했고 현재는 blocker가 아니다

### 4. direct one-shot 전체 입력의 prompt 확장성 부족

- 증상:
  - Food.com metadata 전체를 direct one-shot prompt로 넣는 정책은 catalog 규모가 커질수록 길이 제약에 취약했다
- 원인:
  - row 수 제한과 payload 길이 제한이 초기 구현에 없었다
- 조치:
  - prompt item 수를 최대 `1000`개로 제한했다
  - deterministic evenly spaced sampling을 도입했다
  - sampled payload가 여전히 크면 payload 길이 상한 안에 들어올 때까지 sample 수를 추가로 줄이도록 바꿨다
- 현재 상태:
  - prompt 입력은 item cap과 payload budget 두 단계로 bounded된다

### 5. JSON 파싱과 repair failure 메시지의 모호성

- 증상:
  - JSON 뒤에 brace가 포함된 텍스트가 붙으면 greedy extraction 때문에 parse 실패 가능성이 있었다
  - repair pass 이후에도 invalid JSON이면 실패 원인이 불명확했다
- 조치:
  - 첫 complete JSON object만 파싱 대상으로 읽도록 수정했다
  - repair까지 실패하면 명시적인 오류 메시지를 반환하도록 바꿨다
- 현재 상태:
  - malformed output 처리 경로가 더 진단 가능해졌다

### 6. empty output과 CLI 요약의 success-shaped 결과

- 증상:
  - normalization 후 usable value가 없어도 empty taxonomy가 성공처럼 저장될 수 있었다
  - CLI summary는 전체 catalog 수만 보여줘 실제 prompt 입력 규모를 파악하기 어려웠다
- 조치:
  - empty taxonomy를 hard failure로 바꿨다
  - CLI summary를 `Catalog items`와 `Prompt items`로 분리했다
  - 결과 검토용 `taxonomy_report.html`을 생성했다
- 현재 상태:
  - 실패 모드와 실행 결과를 사람이 더 쉽게 해석할 수 있다

## 핵심 인사이트

- 초기 이슈는 런타임 환경과 Python 구현 두 축에 모두 걸쳐 있었다.
- MLX probe, bounded input, robust parsing, empty-output validation을 함께 넣어 taxonomy 생성 경로가 훨씬 안정화되었다.
- 현재는 실행 결과 자체뿐 아니라 prompt 규모와 taxonomy coverage를 문서/리포트로 검토할 수 있게 되었다.

## 미해결 질문

- payload budget을 token-aware 추정으로 더 정교화할 필요가 있는지는 추가 검토가 필요하다.
- evenly spaced sampling이 rare taxonomy value를 얼마나 놓치는지 downstream tagging 단계에서 확인이 필요하다.

## Related

- [Food Taxonomy Dictionary](food-taxonomy-dictionary.md) — 문제 발생 대상 기능
- [개발 환경 세팅](dev-environment.md) — 로컬 런타임과 검증 환경
- [ADR-004: Taxonomy Dictionary 생성 방식 결정](../adr/adr-004-taxonomy-dictionary-generation.md) — superseded된 초기 생성 정책
- [ADR-005: Taxonomy Dictionary 생성 hardening 결정](../adr/adr-005-taxonomy-dictionary-hardening.md) — 현재 hardening 정책
