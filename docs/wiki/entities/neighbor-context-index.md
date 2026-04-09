---
title: "Neighbor Context"
date: 2026-04-07
type: entity
tags: [taxonomy, faiss, embedding, recommendation]
sources: []
---

# Neighbor Context

## 개요

`Neighbor Context`는 전처리된 Food.com recipe catalog를 임베딩해
각 recipe의 top-k neighbor evidence를 materialize하는 단계다.

이 프로젝트에서는 `name + description + tags + ingredients`만 임베딩 본문으로 사용한다.

## 현재 상태

2026-04-07 기준으로 실제 산출물이 생성된 상태다.

- 입력:
  - `data/processed/foodcom/recipes.csv`
- 출력:
  - `data/processed/foodcom/neighbor_context/items_with_embeddings.csv`
  - `data/processed/foodcom/neighbor_context/neighbor_context.csv`
  - `data/processed/foodcom/neighbor_context/id_map.csv`
  - `data/processed/foodcom/neighbor_context/item_index.faiss`
  - `data/processed/foodcom/neighbor_context/manifest.json`

- 실제 생성 결과:
  - `item_rows`: `192`
  - `neighbor_rows`: `960`
  - `embedding_dim`: `2560`
  - `top_k`: `5`
  - `index_type`: `faiss.IndexFlatIP`
  - `initial_batch_size`: `64`
  - `final_batch_size`: `64`

즉, 현재 상태는 `Food.com recipe catalog에 대한 item embedding + top-5 neighbor context`가 로컬에 준비된 상태다.

## 사용법/설정

### 실행 명령

```bash
uv run sid-reco build-neighbor-context \
  --recipes-path data/processed/foodcom/recipes.csv \
  --out-dir data/processed/foodcom/neighbor_context \
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

- [Food.com 데이터셋](food-com-dataset.md) — neighbor context의 원천 catalog
- [ADR-003: Neighbor Context 정책 결정](../decisions/adr-003-neighbor-context-retrieval.md) — neighbor context 정책 결정
- [개발 환경 세팅](dev-environment.md) — MLX와 CLI가 실행되는 로컬 환경
- [Taxonomy Item Structuring](taxonomy-item-structuring.md) — top-5 neighbor를 downstream evidence로 사용하는 단계
- [SID 컴파일 및 인덱싱](sid-compilation-indexing.md) — structuring 이후 serialization/embedding 중간 산출물과 이어지는 downstream 단계
- [ADR-006: Strict TID hardening 결정](../decisions/adr-006-strict-tid-hardening.md) — top-5 neighbor evidence의 downstream 사용 정책
