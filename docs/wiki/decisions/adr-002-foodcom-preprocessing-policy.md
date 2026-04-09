---
title: "Food.com 전처리 정책 결정"
date: 2026-04-07
type: adr
status: Accepted
sources: []
---

# ADR-002: Food.com 전처리 정책 결정

## Context

이 프로젝트는 Food.com 원본 데이터를 SID 기반 training-free 추천 실험에 사용할 수 있는 형태로 축소해야 한다.
원본은 explicit rating과 review를 포함하지만, 현재 목표는 retrieval, reranking, 시간 기반 평가에 바로 사용할 수 있는 compact implicit feedback 데이터셋을 만드는 것이다.

필요한 제약은 아래와 같았다.

- 로컬 Mac 환경에서 빠르게 반복 실험 가능해야 한다
- user/item 희소성이 지나치게 크지 않아야 한다
- 추천 평가용 holdout split을 바로 만들 수 있어야 한다
- review text는 이후 LLM 기반 프로파일링과 설명 생성에 재사용 가능해야 한다

## Decision

Food.com 전처리 정책을 아래와 같이 고정한다.

### 원본 입력과 출력

- 원본 입력:
  - `data/raw/foodcom/RAW_recipes.csv`
  - `data/raw/foodcom/RAW_interactions.csv`
- 출력:
  - `data/processed/foodcom/recipes.csv`
  - `data/processed/foodcom/interactions.csv`
  - `data/processed/foodcom/splits/{train,valid,test}.csv`
  - `data/processed/foodcom/manifest.json`

### interaction 정책

- `rating >= 4`만 positive interaction으로 유지한다
- 유지된 interaction의 `rating`은 `1`로 이진화한다
- 원래 rating 값은 내부적으로 `source_rating`으로 보존하여 recipe 통계 계산에 사용한다
- `review` 텍스트는 유지한다

### recipe 선택 및 core 정책

- positive interaction 기준 상호작용 수가 많은 상위 `3000`개 recipe를 먼저 선택한다
- 그 후 user/item `5-core`를 iterative하게 적용한다
- 최종 recipe 수가 `3000`보다 작아져도 그대로 허용한다

### split 정책

- user별 interaction을 시간순으로 정렬한다
- user별로 시간 기준 `8:1:1` 비율의 `train / valid / test` split을 생성한다
- 짧은 히스토리에서도 시간 순서를 우선 유지한다

## Consequences

### 긍정적

- implicit feedback 추천 실험에 바로 사용할 수 있는 일관된 데이터 계약 확보
- `5-core`로 user/item 희소성을 줄여 retrieval 및 reranking 평가 안정성 향상
- 시간 기준 split으로 leakage를 줄이고 추천 평가 현실성 확보
- review text를 남겨 이후 LLM 활용 여지 유지

### 부정적/제약

- `top-recipes 3000`을 입력해도 후속 `5-core` 때문에 실제 남는 item 수는 훨씬 작아질 수 있다
- `rating >= 4` 이진화는 fine-grained preference signal을 잃는다
- 현재 정책은 implicit setting에 최적화되어 있어 explicit rating 예측 실험과는 맞지 않는다

### 다음 단계

1. `recipes.csv` 기반 catalog loader 구현
2. `interactions.csv`와 split 파일을 사용하는 retrieval 평가 파이프라인 구현
3. 필요하면 `core-k`, `positive-threshold`, `top-k` 순서를 다시 조정하는 추가 ADR 작성
4. SID 생성 및 LLM reranking 연결

## Related

- [Food.com 데이터셋](../entities/food-com-dataset.md) — 현재 데이터셋 상태와 사용법
- [dev-environment](../entities/dev-environment.md) — 전처리 명령이 실행되는 로컬 환경
- [ADR-001: 개발 환경 및 로컬 추론 스택 결정](adr-001-dev-environment.md) — 전체 로컬 스택 결정
