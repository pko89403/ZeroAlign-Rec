---
title: "Phase 2 추천 런타임"
date: 2026-04-10
type: entity
tags: [recommendation, phase2, sid, mlx, runtime]
sources: []
---

# Phase 2 추천 런타임

## 개요

`Phase 2 추천 런타임`은 Phase 1에서 준비한 `sid_index/` 산출물과
taxonomy dictionary, catalog metadata, few-shot casebank를 묶어
training-free 추천 응답을 생성하는 downstream 파이프라인이다.

현재 구현은 `src/sid_reco/recommendation/` 아래에 들어 있으며,
아래 모듈 순서로 동작한다.

1. taxonomy-guided interest sketch
2. semantic retrieval + CPU hard filter + stats enrichment
3. bootstrap rerank
4. confidence aggregation + grounding

public entrypoint는 `uv run sid-reco recommend` CLI와
동일 로직을 감싼 Python API다.

## 현재 상태

2026-04-10 기준 현재 구현은 아래 요소를 포함한다.

- `interest_sketch.py`
  - query / liked item / disliked item / hard filter를
    taxonomy vocabulary 안으로 정규화
- `semantic_search.py`
  - Phase 1 `item_index.faiss` 검색
  - `id_map.jsonl` / `sid_to_items.json` 로드
  - CPU hard filter 적용
  - `recommendation_stats.json` 기반 popularity / co-occurrence 부착
- `zero_shot_rerank.py`
  - few-shot casebank에서 동적 example 1개 선택
  - candidate-index 기반 structured rerank
  - bootstrap aggregation
- `confidence.py`
  - item-level vote와 confidence band 계산
- `grounding.py`
  - 최종 추천 항목을 catalog metadata와 다시 결합

실제 CLI 경로도 검증되었고,
현재 recommendation runtime은 structured JSON 출력 안정성을 위해
`SID_RECO_LLM_MAX_TOKENS=1024` 기본 budget을 사용한다.

## 사용법/설정

가장 직접적인 entry는 아래 명령이다.

```bash
uv run sid-reco recommend --help
```

현재 런타임이 기대하는 핵심 입력은 아래와 같다.

- `data/processed/foodcom/sid_index/`
  - `item_index.faiss`
  - `id_map.jsonl`
  - `sid_to_items.json`
  - `recommendation_stats.json`
- taxonomy dictionary JSON
- catalog CSV
- recommendation few-shot casebank JSONL

runtime 요청은 자연어 query뿐 아니라,
반복 가능한 liked/disliked item ID와 hard filter를 함께 받을 수 있다.

## Related

- [SID 컴파일 및 인덱싱](sid-compilation-indexing.md) — 추천 런타임이 소비하는 upstream artifact 생성 단계
- [SID Phase 1 실행 검증 개요](../overviews/sid-phase1-validation-run.md) — upstream 산출물 정합성 검증
- [Phase 2 추천 런타임 실행 검증 개요](../overviews/phase2-recommendation-runtime-validation.md) — 실제 추천 경로에서 확인한 실행 이슈와 안정화 결과
