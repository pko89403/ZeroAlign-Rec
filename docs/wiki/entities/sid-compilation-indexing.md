---
title: "SID 컴파일 및 인덱싱"
date: 2026-04-09
type: entity
tags: [sid, embedding, kmeans, faiss, indexing]
sources: []
---

# SID 컴파일 및 인덱싱

## 개요

`SID 컴파일 및 인덱싱`은 `structure-taxonomy-batch`가 만든
`taxonomy_structured/items.jsonl`을 입력으로 받아,
Phase 1 마지막 단계에 필요한 중간 산출물과 최종 인덱스 계층,
그리고 Phase 2 추천 런타임이 사용하는 offline recommendation statistics를 준비하는 흐름이다.

현재 구현은 module-level 기준으로 아래 단계까지 도달했다.

- 결정론적 serialization
- MLX embedding 추출 및 산출물 저장
- CPU residual K-means codebook 학습
- SID assignment 생성
- FAISS index + mapping artifact 저장
- popularity / co-occurrence statistics 저장

현재는 public `compile-sid-index` CLI까지 연결되어 있다.

## 현재 상태

현재 구현은 `src/sid_reco/sid/` 아래에 들어 있다.

- `serialization.py`
  - structured taxonomy JSONL 로드
  - taxonomy key/value 정규화
  - `empty` 제거
  - 결정론적 `serialized_text` 생성
  - `serialized_items.jsonl` 저장
- `embed_backend.py`
  - 기존 `MLXEmbeddingEncoder` 재사용
  - serialized text를 dense embedding으로 변환
  - `embeddings.npy` 저장
  - `embedding_manifest.json` 저장
- `compiler.py`
  - GRID 스타일에 맞춘 train / inference 분리
  - `train_residual_codebooks(...)`
  - `assign_trained_residual_kmeans(...)`
  - compatibility wrapper `compile_residual_kmeans(...)`
- `indexing.py`
  - `compiled_sid.jsonl`
  - `item_to_sid.json`
  - `sid_to_items.json`
  - `id_map.jsonl`
  - `item_index.faiss`
  - `manifest.json`
- `stats.py`
  - processed interactions 기반 popularity 계산
  - item-item co-occurrence 계산
  - `recommendation_stats.json` 저장

실제 생성이 확인된 산출물:

- `data/processed/foodcom/sid_index/serialized_items.jsonl`
- `data/processed/foodcom/sid_index/embeddings.npy`
- `data/processed/foodcom/sid_index/embedding_manifest.json`
- `data/processed/foodcom/sid_index/compiled_sid.jsonl`
- `data/processed/foodcom/sid_index/item_to_sid.json`
- `data/processed/foodcom/sid_index/sid_to_items.json`
- `data/processed/foodcom/sid_index/id_map.jsonl`
- `data/processed/foodcom/sid_index/item_index.faiss`
- `data/processed/foodcom/sid_index/recommendation_stats.json`
- `data/processed/foodcom/sid_index/manifest.json`

2026-04-09 기준 실제 실행에서는 192개 item에 대해
2560차원 임베딩이 생성되었고,
모델은 `mlx-community/Qwen3-Embedding-4B-4bit-DWQ`가 사용되었다.
`branching_factor=32`, `depth=3`, `normalize_residuals=true` 설정에서
`183`개의 unique SID가 생성되었다.

## 사용법/설정

현재는 public CLI와 모듈 함수 수준 entrypoint가 모두 준비되어 있다.

- CLI entry:
  - `uv run sid-reco compile-sid-index --structured-items-path ... --taxonomy-dictionary-path ... --interactions-path ... --out-dir ...`

- serialization entry:
  - `serialize_structured_items(...)`
  - `write_serialized_items(...)`
- embedding entry:
  - `encode_serialized_items_with_mlx(...)`
  - `write_embedded_items(...)`
- compiler entry:
  - `train_residual_codebooks(...)`
  - `assign_trained_residual_kmeans(...)`
- indexing entry:
  - `write_sid_index_outputs(...)`

입력 계약에서 중요한 방어 규칙:

- `structured taxonomy` JSONL에 중복 `recipe_id`가 있으면 serialization 단계에서 즉시 실패한다.
- 이 검증은 `item_to_sid.json`, `sid_to_items.json`, `id_map.jsonl`, `item_index.faiss` 사이의 정합성이 깨지는 것을 방지하기 위한 것이다.

현재 module-level 산출물 흐름은 다음과 같다.

1. `data/processed/foodcom/taxonomy_structured/items.jsonl`
2. `data/processed/foodcom/sid_index/serialized_items.jsonl`
3. `data/processed/foodcom/sid_index/embeddings.npy`
4. `data/processed/foodcom/sid_index/embedding_manifest.json`
5. `data/processed/foodcom/sid_index/compiled_sid.jsonl`
6. `data/processed/foodcom/sid_index/item_to_sid.json`
7. `data/processed/foodcom/sid_index/sid_to_items.json`
8. `data/processed/foodcom/sid_index/id_map.jsonl`
9. `data/processed/foodcom/sid_index/item_index.faiss`
10. `data/processed/foodcom/sid_index/recommendation_stats.json`
11. `data/processed/foodcom/sid_index/manifest.json`

정적 검증 요약은 `artifacts/reports/sid-phase1-validation.html`에도 정리되어 있다.

## Related

- [Taxonomy Item Structuring](taxonomy-item-structuring.md) — 현재 단계의 직접 입력을 만드는 upstream 단계
- [Food Taxonomy Dictionary](food-taxonomy-dictionary.md) — structuring vocabulary를 제공하는 upstream artifact
- [Neighbor Context](neighbor-context-index.md) — item structuring 근거를 제공하는 upstream embedding/FAISS 단계
- [개발 환경 세팅](dev-environment.md) — MLX 임베딩 런타임과 기본 모델 설정
- [SID Phase 1 실행 검증 개요](../overviews/sid-phase1-validation-run.md) — 실데이터 기준 실행 결과와 산출물 정합성
- [Phase 2 추천 런타임](phase2-recommendation-runtime.md) — `sid_index/` 산출물을 실제 추천 파이프라인에 연결하는 downstream 단계
- [Phase 2 추천 런타임 실행 검증 개요](../overviews/phase2-recommendation-runtime-validation.md) — 실제 추천 실행, rerank 안정화, token budget 조정 결과
