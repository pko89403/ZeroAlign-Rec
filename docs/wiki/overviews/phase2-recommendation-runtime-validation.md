---
title: "Phase 2 추천 런타임 실행 검증 개요"
date: 2026-04-10
type: overview
sources: []
---

# Phase 2 추천 런타임 실행 검증 개요

## 범위

이 문서는 `recommend` CLI와 `src/sid_reco/recommendation/` 파이프라인이
실제 Food.com processed artifact 위에서 어디까지 동작하는지 정리한다.

검증 범위는 아래 순서를 포함한다.

1. Phase 1 `sid_index/` artifact 로드
2. recommendation statistics / few-shot casebank 준비
3. taxonomy-guided interest sketch 생성
4. semantic retrieval + CPU hard filter
5. bootstrap rerank
6. confidence aggregation + grounding

## 주제 요약

2026-04-10 기준 실제 추천 경로 검증에서 확인된 핵심 사항은 다음과 같다.

- `compile-sid-index` 산출물 외에 recommendation runtime에는
  `recommendation_stats.json`이 필요하다
- few-shot rerank를 위해 valid casebank JSONL도 필요하다
- 초기 실제 실행에서는 rerank 응답 JSON이 중간에서 잘리는 문제가 있었다
- 원인은 모델 context 한계가 아니라 application-level `max_tokens` budget 부족이었다
- rerank prompt를 top-k only 계약으로 조정하고
  기본 generation budget을 `1024`로 높인 뒤,
  원래 30-candidate 경로에서도 실제 CLI 실행이 안정화되었다

## 핵심 인사이트

이번 검증에서 중요한 점은
**테스트 통과와 실제 추천 운영 가능 상태가 다를 수 있다**는 사실이다.

- 오프라인 artifact가 모두 준비되어 있어야 한다
- rerank는 자유 형식 텍스트보다 structured JSON contract가 훨씬 중요하다
- 모델의 `model_max_length`가 크더라도,
  실제 실패 원인은 호출 시점의 `max_tokens` budget일 수 있다

또 하나의 중요한 관찰은
Phase 2 추천 품질/안정성 이슈의 상당 부분이 model choice 자체보다
**artifact completeness + prompt contract + token budget**에서 발생했다는 점이다.

## 미해결 질문

- query-side SID assignment용 codebook artifact를 별도로 저장할지
- item-level confidence 외에 SID-group confidence를 추가할지
- low coverage 상황에서 Adaptive Exploration Radius를 어떤 규칙으로 열지
- diversity / popularity skew / perceived serendipity를 어떤 실험 루틴으로 평가할지

## Related

- [Phase 2 추천 런타임](../entities/phase2-recommendation-runtime.md) — 현재 recommendation package와 CLI entrypoint 설명
- [SID 컴파일 및 인덱싱](../entities/sid-compilation-indexing.md) — Phase 2가 소비하는 upstream artifact 생성 단계
- [SID Phase 1 실행 검증 개요](sid-phase1-validation-run.md) — upstream 정합성 검증 기록
