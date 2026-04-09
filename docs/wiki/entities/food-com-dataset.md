---
title: "Food.com 데이터셋"
date: 2026-04-07
type: entity
tags: [dataset, food-com, preprocessing, recommendation]
sources: []
---

# Food.com 데이터셋

## 개요

`Food.com Recipes & Interactions`는 recipe 메타데이터와 user-recipe interaction을 함께 제공하는 추천 실험용 데이터셋이다.
이 프로젝트에서는 SID 기반 training-free 추천 실험을 위해 recipe catalog, implicit feedback interaction, 시간 기반 평가 split의 출발점으로 사용한다.

## 현재 상태

이 프로젝트에서는 아래 원본 파일을 로컬에 확보한 상태다.

- `data/raw/foodcom/RAW_recipes.csv`
- `data/raw/foodcom/RAW_interactions.csv`

현재 전처리된 결과는 아래 경로에 생성되어 있다.

- `data/processed/foodcom/recipes.csv`
- `data/processed/foodcom/interactions.csv`
- `data/processed/foodcom/splits/train.csv`
- `data/processed/foodcom/splits/valid.csv`
- `data/processed/foodcom/splits/test.csv`
- `data/processed/foodcom/manifest.json`

2026-04-07 기준 실제 생성 결과:

- `recipes_rows`: `192`
- `interactions_rows`: `2708`
- `train_rows`: `2025`
- `valid_rows`: `313`
- `test_rows`: `370`
- `unique_users`: `249`
- `unique_recipes`: `192`

추가 검산 결과:

- interaction `rating` 값은 모두 `1.0`
- user 최소 interaction 수는 `5`
- item 최소 interaction 수는 `5`

즉, 현재 상태는 `implicit feedback 추천 실험에 바로 투입 가능한 소형 Food.com 데이터셋`이다.

## 사용법/설정

### 전처리 규칙

- `rating >= 4`만 positive로 유지
- 유지된 interaction의 `rating`은 `1`로 이진화
- 상호작용 수 기준 상위 `3000`개 recipe를 우선 선택
- 이후 user/item `5-core`를 iterative하게 적용
- user별 시간순 `8:1:1` split 생성

### 실행 명령

```bash
uv run sid-reco prepare-foodcom \
  --raw-dir data/raw/foodcom \
  --out-dir data/processed/foodcom \
  --top-recipes 3000 \
  --core-k 5 \
  --positive-threshold 4
```

### 해석

입력 파라미터는 `top-recipes 3000`이지만, positive filtering과 `5-core`를 동시에 적용하면 데이터가 크게 줄어든다.
현재 결과가 `192개 recipe`로 축소된 이유도 이 후속 필터링 때문이다.

item 규모를 더 크게 유지하려면 다음 중 하나를 조정해야 한다.

- `core-k` 완화
- `positive-threshold` 완화
- `top-k` 적용 순서 재설계

## Related

- [Neighbor Context 인덱스](neighbor-context-index.md) — recipe catalog를 사용하는 첫 neighbor context 생성 단계
- [Food Taxonomy Dictionary](food-taxonomy-dictionary.md) — recipe metadata 전체를 분석해 생성하는 domain taxonomy 사전
- [foodcom preprocessing ADR](../decisions/adr-002-foodcom-preprocessing-policy.md) — 현재 전처리 정책의 결정 기록
- [ADR-003: Neighbor Context 검색 정책 결정](../decisions/adr-003-neighbor-context-retrieval.md) — 이 데이터셋을 입력으로 사용하는 neighbor context 정책
- [ADR-004: Taxonomy Dictionary 생성 방식 결정](../decisions/adr-004-taxonomy-dictionary-generation.md) — superseded된 초기 taxonomy dictionary 생성 정책
- [ADR-005: Taxonomy Dictionary 생성 hardening 결정](../decisions/adr-005-taxonomy-dictionary-hardening.md) — bounded input과 validation을 포함한 현재 생성 정책
- [dev-environment](dev-environment.md) — 이 데이터셋을 처리하는 로컬 개발 환경
- [ADR-001: 개발 환경 및 로컬 추론 스택 결정](../decisions/adr-001-dev-environment.md) — 전처리 명령이 포함된 전체 개발 스택 결정
