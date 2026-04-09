---
title: "Taxonomy Step 1 이웃 인덱스"
date: 2026-04-07
type: entity
tags: [taxonomy, faiss, embedding, recommendation]
sources: []
---

# Taxonomy Step 1 이웃 인덱스

## 개요

`Taxonomy Step 1`은 전처리된 Food.com recipe catalog를 item-level taxonomy 후보 집합으로 보고,
각 recipe의 핵심 메타데이터를 임베딩한 뒤 FAISS 로컬 인덱스로 상위 이웃 item을 찾는 단계다.

이 프로젝트에서는 `name + description + tags + ingredients`만 임베딩 본문으로 사용한다.

## 현재 상태

2026-04-07 기준으로 실제 산출물이 생성된 상태다.

- 입력:
  - `data/processed/foodcom/recipes.csv`
- 출력:
  - `data/processed/foodcom/taxonomy_step1/items_with_embeddings.csv`
  - `data/processed/foodcom/taxonomy_step1/neighbor_context.csv`
  - `data/processed/foodcom/taxonomy_step1/id_map.csv`
  - `data/processed/foodcom/taxonomy_step1/item_index.faiss`
  - `data/processed/foodcom/taxonomy_step1/manifest.json`

- 실제 생성 결과:
  - `item_rows`: `192`
  - `neighbor_rows`: `960`
  - `embedding_dim`: `2560`
  - `top_k`: `5`
  - `index_type`: `faiss.IndexFlatIP`
  - `initial_batch_size`: `64`
  - `final_batch_size`: `64`

즉, 현재 상태는 `Food.com recipe catalog에 대한 item embedding + FAISS top-5 neighbor index`가 로컬에 준비된 상태다.

## 사용법/설정

### 실행 명령

```bash
uv run sid-reco build-taxonomy-step1 \
  --recipes-path data/processed/foodcom/recipes.csv \
  --out-dir data/processed/foodcom/taxonomy_step1 \
  --top-k 5
```

### 동작 규칙

- 임베딩 모델은 현재 설정된 `SID_RECO_EMBED_MODEL`을 사용한다
- 배치 크기는 현재 시스템 메모리를 기준으로 자동 결정된다
- 임베딩 실패 시 batch size를 절반으로 줄여 재시도한다
- 벡터는 L2 normalize 후 `faiss.IndexFlatIP`에 적재한다
- 각 item에 대해 self-match를 제외한 상위 `5`개 이웃을 저장한다
- `neighbor_context.csv`는 `ids only` 정책이므로 이웃 메타데이터는 `items_with_embeddings.csv`에서 조회한다
- downstream item structuring 단계는 각 recipe의 top-5 neighbor를 evidence로 재사용한다

## Related

- [Food.com 데이터셋](food-com-dataset.md) — step 1의 원천 catalog
- [ADR-003: Taxonomy Step 1 이웃 검색 정책 결정](../decisions/adr-003-taxonomy-step1-neighbor-index.md) — step 1 검색 정책 결정
- [개발 환경 세팅](dev-environment.md) — MLX와 CLI가 실행되는 로컬 환경
- [Taxonomy Item Structuring](taxonomy-item-structuring.md) — top-5 neighbor를 downstream evidence로 사용하는 단계
- [ADR-006: Strict TID hardening 결정](../decisions/adr-006-strict-tid-hardening.md) — top-5 neighbor evidence의 downstream 사용 정책
