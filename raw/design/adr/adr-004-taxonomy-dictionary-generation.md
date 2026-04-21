---
title: "Taxonomy Dictionary 생성 방식 결정"
date: 2026-04-08
type: adr
status: Superseded
sources: []
---

# ADR-004: Taxonomy Dictionary 생성 방식 결정

## Context

후속 단계에서는 각 recipe item을 domain taxonomy에 따라 태깅해야 한다.
이를 위해서는 feature 축만이 아니라, 각 feature에 대해 가능한 값들의 vocabulary까지 포함하는
domain taxonomy dictionary가 먼저 필요하다.

이 사전은 Food.com metadata 전체를 바탕으로 1회성으로 구축하되, Python 코드로 재현 가능해야 한다.
또한 [Taxonomy-Guided Zero-Shot Recommendations with LLMs](https://arxiv.org/abs/2406.14043)
및 [TaxRec 공개 구현](https://github.com/yueqingliang1/TaxRec)처럼
LLM을 taxonomy 생성의 핵심 단계에 사용하는 방향을 유지해야 한다.

## Decision

Taxonomy dictionary 생성 방식을 아래와 같이 고정한다.

### 생성 방식

- 로컬 MLX LLM을 사용한다
- direct one-shot prompt로 Food.com recipe metadata 전체를 입력한다
- `TaxRec` 스타일의 taxonomy generation prompt를 food domain용으로 few-shot 확장한다

### 입력 데이터

- 입력 파일은 `data/processed/foodcom/recipes.csv`
- 사용 필드는 `name`, `description`, `tags`, `ingredients`
- `steps`, interaction 통계, split 정보는 사용하지 않는다

### 출력 형식

- 최종 산출물은 `feature_name -> [possible_values]` 구조의 JSON dictionary
- feature 이름과 value는 모두 recommendation tagging에 쓸 수 있는 canonical term이어야 한다
- JSON 외 텍스트는 허용하지 않는다

### 재현성 정책

- 생성 로직은 Python CLI 명령으로 제공한다
- 출력과 함께 `prompt_snapshot.json`을 저장한다
- 생성 파라미터는 고정한다: `temperature=0.0`, `top_p=1.0`
- malformed output은 1회 repair pass 후 정규화한다

## Consequences

### 긍정적

- item tagging 이전에 domain taxonomy를 한 번에 구축할 수 있다
- TaxRec의 핵심 아이디어를 현재 food recommendation 도메인에 맞게 유지할 수 있다
- prompt snapshot을 남겨 추후 재생성과 비교가 가능하다

### 부정적/제약

- LLM 생성 단계가 포함되므로 완전한 규칙 기반 파이프라인보다 결과 편차 가능성이 있다
- direct one-shot prompt는 데이터 규모가 커질수록 입력 길이 제약을 받을 수 있다
- taxonomy 품질은 프롬프트 설계와 모델 출력 품질에 영향을 받는다

### 다음 단계

1. 생성된 taxonomy dictionary를 검토한다
2. 각 item을 taxonomy dictionary에 따라 태깅하는 projection 단계를 구현한다
3. taxonomy 기반 feature를 retrieval/reranking 실험에 연결한다

### 후속 변경

- 이후 구현에서는 direct one-shot 전체 입력 대신 bounded sampling과 payload budget을 적용하는
  후속 결정이 채택되었다.
- 현재 정책은 [ADR-005: Taxonomy Dictionary 생성 hardening 결정](adr-005-taxonomy-dictionary-hardening.md)을 따른다.

## Related

- [Food Taxonomy Dictionary](../notes/food-taxonomy-dictionary.md) — 생성 결과와 사용법
- [Food.com 데이터셋](../notes/food-com-dataset.md) — taxonomy dictionary 생성의 입력 데이터
- [개발 환경 세팅](../notes/dev-environment.md) — 로컬 MLX LLM 실행 환경
- [ADR-001: 개발 환경 및 로컬 추론 스택 결정](adr-001-dev-environment.md) — 전체 로컬 추론 스택 결정
- [ADR-005: Taxonomy Dictionary 생성 hardening 결정](adr-005-taxonomy-dictionary-hardening.md) — 후속 hardening 정책
- [Taxonomy Dictionary 개발 이슈 개요](../notes/taxonomy-dictionary-development-issues.md) — 구현 및 검증 중 발생한 오류 기록
- 외부 레퍼런스: [Taxonomy-Guided Zero-Shot Recommendations with LLMs](https://arxiv.org/abs/2406.14043), [TaxRec 공개 구현](https://github.com/yueqingliang1/TaxRec)
