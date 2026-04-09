---
title: "개발 환경 및 로컬 추론 스택 결정"
date: 2026-04-07
type: adr
status: Accepted
sources: []
---

# ADR-001: 개발 환경 및 로컬 추론 스택 결정

## Context

이 프로젝트는 SID(Semantic ID) 기반의 training-free 추천 시스템을 로컬 환경에서 실험하기 위한 코드베이스다.
현재 단계의 목표는 추천 알고리즘 전체 구현이 아니라, 다음 작업을 안정적으로 이어갈 수 있는 개발 환경과 로컬 추론 기반을 마련하는 것이었다.

타깃 장비는 MacBook Pro (Apple M4 Pro, 48GB unified memory, arm64)이며, 외부 API 의존 없이 로컬에서 생성 및 임베딩 추론이 가능해야 한다.

## Decision

### 로컬 생성 모델

- 모델: `mlx-community/Qwen3.5-9B-OptiQ-4bit`
- 용도: 추천 후보 reranking, 사용자 로그 요약, SID 보조 생성, 설명 생성
- 선택 이유:
  - Apple Silicon에서 `mlx-lm` 표준 경로로 바로 구동 가능
  - 한국어 포함 멀티링구얼 성능과 instruction following 균형이 좋음
  - 모델 크기가 적절해서 반복 추론 워크로드에 유리함

### 로컬 임베딩 모델

- 모델: `mlx-community/Qwen3-Embedding-4B-4bit-DWQ`
- 용도: 아이템/쿼리 임베딩, candidate retrieval, 유사도 기반 검색
- 선택 이유:
  - Qwen 계열 생성 모델과 성향이 잘 맞음
  - 멀티링구얼 지원과 임베딩 품질이 좋음
  - 현재 장비에서 충분히 감당 가능한 크기

### 언어 및 패키지 관리

- Python: `3.12`
- 가상환경/패키지 관리: `uv`

### 지원 환경 정책

- 공식 지원 환경은 로그인된 로컬 `macOS Apple Silicon` 터미널 세션으로 제한한다
- `SSH`, `CI`, 샌드박스 에이전트, 헤드리스 백그라운드 세션은 MLX Metal 검증 대상에서 제외한다
- MLX 실패 시 fallback backend는 두지 않고 `fail-fast` 정책을 유지한다

### 주요 런타임 의존성

- `mlx-lm>=0.31.1`, `mlx-embeddings>=0.1.0`
- `python-dotenv>=1.2.2`, `typer`, `rich`
- `numpy`, `pandas`, `pydantic`, `pyyaml`

### 개발용 의존성

- `pytest`, `ruff`, `mypy`, `pytest-cov`

### 코드 구조

```text
src/sid_reco/
├── __init__.py
├── cli.py          # Typer CLI 엔트리포인트
├── config.py       # 환경 변수 + .env 기반 설정
├── mlx_runtime.py  # MLX 런타임 probe 및 진단
├── embedding.py    # MLXEmbeddingEncoder
├── llm.py          # MLXTextGenerator
├── datasets/
│   ├── __init__.py
│   └── foodcom.py  # Food.com 데이터셋 전처리
└── taxonomy/
    ├── __init__.py
    ├── dictionary.py  # taxonomy dictionary 생성
    └── neighbor_context.py  # neighbor context 임베딩 및 이웃 검색
```

### 구현된 모듈

- **설정 레이어** (`config.py`): `.env` 로딩, 프로젝트 루트 기준 상대 경로 해석, 기본값 설정, 디렉터리 자동 생성
- **로컬 LLM 래퍼** (`llm.py`): `MLXTextGenerator`, `mlx_lm.load()` 기반 지연 로딩, chat template 지원
- **로컬 임베딩 래퍼** (`embedding.py`): `MLXEmbeddingEncoder`, 단일/배치 임베딩 생성, MLX 텐서 → `list[float]` 변환
- **CLI** (`cli.py`): `doctor`, `smoke-mlx`, `smoke-llm`, `smoke-embed`, `prepare-foodcom`, `build-neighbor-context`, `build-taxonomy-dictionary` 명령

## Consequences

### 긍정적

- 외부 API 없이 로컬에서 생성 및 임베딩 추론이 가능
- `Qwen3.5-9B` + `Qwen3-Embedding-4B` 조합이 현재 장비에서 안정적으로 동작
- `uv` 기반 빌드 체인이 빠르고 재현 가능
- `pytest`, `ruff`, `mypy` 모두 통과 확인 (2026-04-07)

### 부정적/제약

- `smoke-llm`과 `smoke-embed`는 첫 실행 시 Hugging Face에서 모델 다운로드가 필요
- Apple Silicon + MLX에 강하게 결합됨 — 다른 하드웨어에서는 백엔드 교체 필요
- 지원 환경 밖의 세션에서는 MLX Metal 초기화 실패 가능성이 높음
- 현재는 추천 시스템 기반만 준비된 상태이며, SID 생성·카탈로그 로더·retrieval·reranking·평가는 미구현

### 다음 단계

1. 아이템 카탈로그 스키마 정의 및 로더 구현
2. 임베딩 기반 top-k candidate retrieval 모듈
3. SID 생성 규칙/프롬프트 포맷 설계
4. LLM reranking 프롬프트 체인
5. end-to-end 추천 실험 CLI (`recommend` 명령)

## Related

- [dev-environment](../entities/dev-environment.md) — 개발 환경 세팅 상세
- [ADR-002: Food.com 전처리 정책 결정](adr-002-foodcom-preprocessing-policy.md) — Food.com 전처리 규칙
- [Food.com 데이터셋](../entities/food-com-dataset.md) — 현재 로컬 데이터셋 상태
- [ADR-003: Neighbor Context 정책 결정](adr-003-neighbor-context-retrieval.md) — neighbor context 검색 규칙
- [Food Taxonomy Dictionary](../entities/food-taxonomy-dictionary.md) — LLM 기반 taxonomy dictionary 생성 산출물
- [ADR-004: Taxonomy Dictionary 생성 방식 결정](adr-004-taxonomy-dictionary-generation.md) — taxonomy dictionary 생성 정책
