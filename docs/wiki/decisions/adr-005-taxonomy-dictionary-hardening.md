---
title: "Taxonomy Dictionary 생성 hardening 결정"
date: 2026-04-08
type: adr
status: Accepted
supersedes: decisions/adr-004-taxonomy-dictionary-generation.md
sources: []
---

# ADR-005: Taxonomy Dictionary 생성 hardening 결정

## Context

`build-taxonomy-dictionary`의 초기 구현은 Food.com recipe metadata 전체를 direct one-shot prompt로
LLM에 전달하는 방식을 전제로 했다. 그러나 실제 개발 과정에서 아래 문제가 확인되었다.

- catalog row 수만 커져도 prompt 크기가 빠르게 증가한다
- row 수가 제한되어도 긴 `description` 때문에 payload 길이가 여전히 과도해질 수 있다
- malformed JSON이나 empty taxonomy가 success-shaped output으로 보일 위험이 있다
- CLI 결과만 보면 전체 catalog 수와 실제 prompt 입력 수를 구분하기 어렵다

따라서 taxonomy dictionary 생성 정책은 reproducibility를 유지하되, 입력 크기와 실패 모드를
더 명확하게 통제하는 방향으로 보강할 필요가 생겼다.

## Decision

Taxonomy dictionary 생성 정책을 아래와 같이 갱신한다.

### 입력 구성 정책

- 입력 파일은 계속 `data/processed/foodcom/recipes.csv`를 사용한다
- 사용 필드는 계속 `name`, `description`, `tags`, `ingredients`만 사용한다
- prompt 입력 item 수는 최대 `1000`개로 제한한다
- catalog가 `1000`개를 초과하면 deterministic evenly spaced sampling으로 prompt 입력을 구성한다
- sampled payload가 여전히 크면 serialized payload 길이 상한 안에 들어올 때까지 sample 크기를 추가로 줄인다

### 출력 검증 정책

- model output은 첫 complete JSON object만 파싱 대상으로 본다
- 1차 JSON 파싱 실패 시 1회 repair pass를 허용한다
- repair까지 실패하면 명시적인 `ValueError`로 종료한다
- normalization 후 usable feature/value가 하나도 남지 않으면 실패로 처리한다

### 관측성 정책

- `prompt_snapshot.json`에 전체 item 수, 실제 prompt item 수, sampling strategy를 저장한다
- CLI summary는 `Catalog items`와 `Prompt items`를 분리해 출력한다
- taxonomy 결과를 사람이 검토할 수 있도록 standalone HTML report 생성 결과를 함께 활용할 수 있다

## Consequences

### 긍정적

- large catalog에서도 direct one-shot 대비 더 안정적으로 taxonomy 생성을 시도할 수 있다
- malformed JSON, empty output, misleading summary 같은 failure mode가 줄어든다
- prompt snapshot과 CLI 출력만으로도 실제 입력 규모를 추적할 수 있다

### 부정적/제약

- evenly spaced sampling은 rare taxonomy value를 일부 놓칠 수 있다
- item cap과 payload budget은 heuristic이므로 최적 sampling 품질을 보장하지 않는다
- prompt 길이를 완전히 token-aware하게 계산하는 방식은 아직 도입되지 않았다

### 다음 단계

1. taxonomy quality를 사람 검토와 downstream tagging 실험으로 추가 확인한다
2. 필요하면 payload budget을 token-aware 추정으로 정교화한다
3. taxonomy HTML report를 검토 루틴에 포함할지 결정한다

## Related

- [Food Taxonomy Dictionary](../entities/food-taxonomy-dictionary.md) — 현재 생성 규칙과 산출물
- [Food.com 데이터셋](../entities/food-com-dataset.md) — taxonomy dictionary 생성의 입력 데이터
- [개발 환경 세팅](../entities/dev-environment.md) — 로컬 MLX LLM 실행 환경
- [ADR-004: Taxonomy Dictionary 생성 방식 결정](adr-004-taxonomy-dictionary-generation.md) — superseded된 초기 결정
- [Taxonomy Dictionary 개발 이슈 개요](../overviews/taxonomy-dictionary-development-issues.md) — 개발 중 확인된 문제와 해결 내역
