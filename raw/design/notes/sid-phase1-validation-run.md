---
title: "SID Phase 1 실행 검증 개요"
date: 2026-04-09
type: overview
sources: []
---

# SID Phase 1 실행 검증 개요

## 범위

이 문서는 `structure-taxonomy-batch` 이후의
Phase 1 마지막 단계가 실제 데이터에서 어디까지 동작하는지 정리한다.

검증 범위는 아래 순서를 포함한다.

1. `taxonomy_structured/items.jsonl` 로드
2. deterministic serialization
3. MLX embedding 추출 및 `embeddings.npy` 저장
4. CPU residual K-means codebook 학습
5. SID assignment 생성
6. FAISS index 및 mapping artifact 저장

당시 검증은 `src/sid_reco/sid/` 모듈 함수들을 직접 연결해 수행했다. 이후 같은 흐름은 public `compile-sid-index` CLI로도 연결되었다.

## 주제 요약

2026-04-09 기준 실제 실행은 `data/processed/foodcom/`의 Food.com processed artifact를 사용해 완료되었다.

- 입력 item 수: `192`
- 임베딩 모델: `mlx-community/Qwen3-Embedding-4B-4bit-DWQ`
- 임베딩 차원: `2560`
- residual K-means 설정:
  - branching factor: `32`
  - depth: `3`
  - normalize residuals: `true`
- 생성된 unique SID 수: `183`

생성이 확인된 산출물:

- `data/processed/foodcom/sid_index/serialized_items.jsonl`
- `data/processed/foodcom/sid_index/embeddings.npy`
- `data/processed/foodcom/sid_index/embedding_manifest.json`
- `data/processed/foodcom/sid_index/compiled_sid.jsonl`
- `data/processed/foodcom/sid_index/item_to_sid.json`
- `data/processed/foodcom/sid_index/sid_to_items.json`
- `data/processed/foodcom/sid_index/id_map.jsonl`
- `data/processed/foodcom/sid_index/item_index.faiss`
- `data/processed/foodcom/sid_index/manifest.json`

개수 정합성도 맞았다.

- serialized rows: `192`
- compiled SID rows: `192`
- `item_to_sid` entries: `192`
- `sid_to_items` assignment total: `192`
- `id_map` rows: `192`
- FAISS `ntotal`: `192`

## 핵심 인사이트

이번 검증에서 중요한 점은 **임베딩 추출과 quantization/indexing 단계를 분리해서 운영할 수 있다는 것**이다.

- MLX는 embedding 생성 단계에만 필요하다
- 그 이후 residual K-means codebook 학습, SID assignment, FAISS indexing은 CPU-only로 처리 가능하다
- 따라서 rerun 비용을 줄이려면 `serialized_items.jsonl`과 `embeddings.npy`를 중간 산출물로 유지하는 것이 유리하다

또 하나의 중요한 관찰은 `32 x 32 x 32`의 이론적 코드 공간 전체를 다 쓰지 않아도,
실제 `192`개 item에서는 `183`개의 unique SID가 생성되었다는 점이다.
즉 현재 규모에서는 충돌이 제한적이며,
structured taxonomy + dense embedding + residual quantization 흐름이 충분히 discriminative하게 작동하고 있다.

## 미해결 질문

- train된 residual codebook 자체를 별도 artifact로 저장할지
- `compile-sid-index` CLI에서 기본 branching/depth를 무엇으로 둘지
- 현재 `32/3` 설정이 dataset scale이 커졌을 때도 적절한지
- SID 충돌률과 downstream retrieval quality를 어떤 지표로 평가할지

## Related

- [SID 컴파일 및 인덱싱](sid-compilation-indexing.md) — 현재 구현 범위와 내부 모듈 설명
- [Taxonomy Item Structuring](taxonomy-item-structuring.md) — Phase 1 마지막 단계의 직접 입력 생성 단계
- [Neighbor Context](neighbor-context-index.md) — upstream embedding/FAISS evidence 단계
- [Phase 2 추천 런타임](phase2-recommendation-runtime.md) — Phase 1 산출물을 실제 추천 실행에 연결하는 downstream 단계
- [Phase 2 추천 런타임 실행 검증 개요](phase2-recommendation-runtime-validation.md) — 실제 추천 경로에서 확인된 후속 검증 결과
