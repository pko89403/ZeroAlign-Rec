---
title: "Strict TID hardening 결정"
date: 2026-04-09
type: adr
status: Accepted
sources: []
---

# ADR-006: Strict TID hardening 결정

## Context

기존 item structuring 경로는 모든 required key를 포함하고 empty array도 대부분 제거했지만,
실제 batch 결과에서는 아래 문제가 남아 있었다.

- taxonomy dictionary 바깥 open-vocab label이 많이 남는다
- 같은 의미의 동의어/변형 표현이 raw output에 섞여 나온다
- `cuisine=american` 같은 약한 근거 기반 label이 과도하게 붙는다
- `dietary_style=gluten_free`처럼 ingredient evidence와 모순되는 값이 남을 수 있다

즉, 구조적 완전성은 확보되었지만 최종 TID를 사람이 검토하거나 downstream에서
재사용하기에는 canonical quality가 충분히 높지 않았다.
또한 similar-item neighborhood를 함께 넣는 item structuring 방향은 유지하되,
현재 저장소의 JSON taxonomy schema에 맞는 hardening 계층이 추가로 필요했다.

## Decision

item structuring 경로를 아래 단계로 분리해 strict TID hardening을 적용한다.

### 추출 단계

- extraction prompt에서 피처 내 중복과 near-synonym을 줄이도록 명시한다
- 같은 개념을 여러 key에 반복하지 않도록 지시한다
- taxonomy dictionary는 closed set이 아니라 few-shot guidance로 사용한다

### self-refine 단계

- 1차 raw JSON이 simple canonicalization이나 중복 제거가 필요한 경우에만 self-refine를 수행한다
- self-refine는 schema를 바꾸지 않고 draft JSON만 더 정돈하는 역할로 제한한다

### canonicalization 단계

- raw extraction 값은 taxonomy dictionary 기준으로 보수적으로 canonicalize한다
- plural/suffix/조리 방식 변형처럼 단순 규칙으로 정리 가능한 경우를 먼저 흡수한다
- 그래도 맞지 않는 값은 open-vocab으로 유지하되 final TID에서 중복은 제거한다

### validation 단계

- `cuisine`는 근거가 약한 `american` label을 제거할 수 있다
- `dietary_style`는 ingredient/tag evidence와 충돌하는 label을 제거한다
- empty 결과는 마지막에만 sentinel `["empty"]`로 채운다

## Consequences

### 긍정적

- 최종 TID가 더 schema-consistent 하고 읽기 쉬워진다
- simple synonym과 형태 변형을 downstream 전처리 없이 더 많이 흡수할 수 있다
- 명백한 dietary/cuisine 오분류를 후처리에서 줄일 수 있다

### 부정적/제약

- self-refine와 validator가 추가되어 item당 추론 시간이 늘어난다
- 지나치게 강한 canonicalization은 recall을 떨어뜨릴 수 있으므로 보수적으로 유지해야 한다
- 현재 validator는 `cuisine`, `dietary_style` 중심의 lightweight rule에 머문다

### 다음 단계

1. strict TID 정책으로 전체 batch를 재실행해 전/후 통계를 비교한다
2. out-of-vocab value 목록을 별도 artifact로 남길지 결정한다
3. 필요하면 `cooking_method`, `primary_ingredient` validator를 확장한다

## Related

- [Taxonomy Item Structuring](../entities/taxonomy-item-structuring.md) — 현재 적용 대상 파이프라인
- [Food Taxonomy Dictionary](../entities/food-taxonomy-dictionary.md) — canonicalization 기준 vocabulary
- [Neighbor Context](../entities/neighbor-context-index.md) — item evidence를 제공하는 이웃 검색 단계
- [ADR-003: Neighbor Context 정책 결정](adr-003-neighbor-context-retrieval.md) — top-5 neighbor context 정책
- [ADR-005: Taxonomy Dictionary 생성 hardening 결정](adr-005-taxonomy-dictionary-hardening.md) — upstream taxonomy dictionary hardening
- 외부 레퍼런스: [Unleashing the Native Recommendation Potential: LLM-Based Generative Recommendation via Structured Term Identifiers](https://arxiv.org/abs/2601.06798), [GRLM 공개 구현](https://github.com/ZY0025/GRLM)
