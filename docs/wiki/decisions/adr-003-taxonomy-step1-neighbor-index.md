---
title: "Taxonomy Step 1 이웃 검색 정책 결정"
date: 2026-04-07
type: adr
status: Accepted
sources: []
---

# ADR-003: Taxonomy Step 1 이웃 검색 정책 결정

## Context

Taxonomy 사전 구축의 첫 단계에서는 recipe item 간의 거친 semantic neighborhood를 빠르게 만들 필요가 있다.
현재 데이터 규모는 크지 않지만, 이후 catalog 규모가 커져도 같은 형태의 파이프라인을 유지할 수 있어야 한다.

필요한 제약은 아래와 같았다.

- 로컬 Apple Silicon 환경에서 안정적으로 실행 가능해야 한다
- item 메타데이터 기반 semantic candidate를 만들어야 한다
- 결과는 후속 taxonomy 정제 단계가 다시 참조할 수 있는 로컬 인덱스로 남아야 한다
- 임베딩 단계는 현재 메모리 상황에 맞게 batch size를 조절해야 한다

## Decision

Taxonomy Step 1 이웃 검색 정책을 아래와 같이 고정한다.

### item 단위와 입력

- item universe는 `data/processed/foodcom/recipes.csv` 전체를 사용한다
- taxonomy 엔트리 단위는 recipe item이다
- 임베딩 본문은 `name + description + tags + ingredients`로 고정한다

### 임베딩 정책

- 로컬 MLX 임베딩 모델을 사용한다
- batch size는 시스템 메모리를 기준으로 초기값을 잡는다
- 임베딩 중 메모리성 예외가 나면 batch size를 절반으로 줄여 재시도한다
- 사용자가 명시적으로 `--batch-size`를 주면 자동 정책보다 우선한다

### 이웃 검색 정책

- 인덱스는 `faiss.IndexFlatIP`를 사용한다
- 벡터는 L2 normalize 후 inner product로 exact cosine similarity를 계산한다
- 각 item에 대해 self-match를 제외한 상위 `5`개 이웃을 저장한다
- 동률은 `neighbor_recipe_id` 오름차순으로 정렬한다

### 산출물 정책

- 출력 경로는 `data/processed/foodcom/taxonomy_step1/`로 고정한다
- 저장 파일:
  - `items_with_embeddings.csv`
  - `neighbor_context.csv`
  - `id_map.csv`
  - `item_index.faiss`
  - `manifest.json`
- `neighbor_context.csv`는 `ids only` 정책으로 유지한다

## Consequences

### 긍정적

- 현재와 이후 규모 모두에서 같은 검색 인터페이스 유지 가능
- exact cosine search라 결과 해석이 단순하고 재현 가능
- FAISS 인덱스를 저장하므로 후속 단계가 빠르게 재사용 가능
- adaptive batching으로 로컬 메모리 조건 변화에 대응 가능

### 제약

- 현재 단계는 metadata-only 이웃이므로 interaction co-occurrence 신호는 반영하지 않는다
- `ids only` context 정책이라 후속 단계가 별도 metadata lookup을 수행해야 한다
- exact search는 매우 큰 catalog에서는 근사 인덱스보다 느릴 수 있다

## Related

- [Taxonomy Step 1 이웃 인덱스](../entities/taxonomy-step1-neighbor-index.md) — 현재 산출물과 사용법
- [Food.com 데이터셋](../entities/food-com-dataset.md) — 원천 recipe catalog
- [ADR-001: 개발 환경 및 로컬 추론 스택 결정](adr-001-dev-environment.md) — MLX 기반 로컬 추론 스택
