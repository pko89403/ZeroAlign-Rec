---
title: "Taxonomy Item Structuring"
date: 2026-04-09
type: entity
tags: [taxonomy, llm, json, tid, recommendation]
sources: []
---

# Taxonomy Item Structuring

## 개요

`Taxonomy Item Structuring`은 개별 Food.com recipe를 대상으로
`target item + top-5 neighbors + taxonomy dictionary`를 함께 사용해
구조화된 taxonomy JSON을 생성하는 단계다.

이 단계의 목표는 자유 텍스트 기반 item metadata를
`cuisine`, `dish_type`, `taste_mood`, `cooking_method`, `primary_ingredient`
같은 feature key에 맞는 TID 형태로 정리하는 것이다.

## 현재 상태

현재 구현은 `src/sid_reco/taxonomy/item_projection.py`에 들어 있으며,
단일 item과 전체 batch 두 경로를 모두 지원한다.

- 입력:
  - `data/processed/foodcom/recipes.csv`
  - `data/processed/foodcom/neighbor_context/neighbor_context.csv`
  - `data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json`
- 출력:
  - 단일 item JSON
  - batch JSONL (`data/processed/foodcom/taxonomy_structured/items.jsonl`)

이 batch JSONL은 현재 진행 중인 Phase 1 마지막 단계에서
`src/sid_reco/sid/` 모듈이 읽는 직접 입력이다.
현재 구현된 downstream 중간 산출물은
`data/processed/foodcom/sid_index/serialized_items.jsonl`,
`embeddings.npy`, `embedding_manifest.json` 이다.

현재 item structuring 경로의 주요 동작은 다음과 같다.

- 모든 required key를 항상 포함한다
- empty array는 허용하지 않고 필요 시 `["empty"]` sentinel로 채운다
- extraction prompt에서 중복 label과 동의어 남발을 억제한다
- 필요할 때만 self-refine pass를 수행해 draft JSON을 정리한다
- taxonomy dictionary 쪽 canonical label로 보수적으로 수렴시킨다
- `cuisine`, `dietary_style`에 대해 명백한 오분류를 줄이는 validator를 적용한다
- batch 실행 시 진행률 로그를 출력한다

## 사용법/설정

### 실행 명령

단일 item:

```bash
uv run sid-reco structure-taxonomy-item \
  --recipe-id 101 \
  --recipes-path data/processed/foodcom/recipes.csv \
  --neighbor-context-path data/processed/foodcom/neighbor_context/neighbor_context.csv \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json
```

전체 batch:

```bash
uv run sid-reco structure-taxonomy-batch \
  --recipes-path data/processed/foodcom/recipes.csv \
  --neighbor-context-path data/processed/foodcom/neighbor_context/neighbor_context.csv \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json \
  --out-path data/processed/foodcom/taxonomy_structured/items.jsonl
```

### 동작 규칙

- neighbor context는 recipe별 top-5 이웃을 사용한다
- taxonomy dictionary는 closed vocabulary가 아니라 few-shot guidance로 사용한다
- raw extraction에서 vocabulary 밖 label이 나와도 후처리에서 canonicalization을 시도한다
- self-refine는 중복/동의어/간단한 canonicalization 필요성이 있을 때만 수행한다
- validator는 근거가 약한 `american` cuisine과 모순된 dietary label을 보수적으로 제거한다
- batch는 item별 순차 LLM 호출이므로 실행 시간이 길 수 있다

## Related

- [Food Taxonomy Dictionary](food-taxonomy-dictionary.md) — item structuring이 참조하는 master vocabulary
- [Neighbor Context](neighbor-context-index.md) — top-5 neighbor evidence 제공 단계
- [SID 컴파일 및 인덱싱](sid-compilation-indexing.md) — structured taxonomy JSONL을 serialization/embedding 산출물로 넘기는 다음 단계
- [ADR-003: Neighbor Context 정책 결정](../decisions/adr-003-neighbor-context-retrieval.md) — neighbor context 정책
- [ADR-005: Taxonomy Dictionary 생성 hardening 결정](../decisions/adr-005-taxonomy-dictionary-hardening.md) — dictionary 생성과 입력 bounded 정책
- [ADR-006: Strict TID hardening 결정](../decisions/adr-006-strict-tid-hardening.md) — self-refine, canonicalization, validator 정책
