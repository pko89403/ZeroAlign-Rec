---
title: "개발 환경 세팅"
date: 2026-04-07
type: entity
tags: [setup, environment, mlx, uv]
sources: []
---

# 개발 환경 세팅

## 개요

이 프로젝트의 개발 환경은 Python 3.12 + `uv` 패키지 관리자 + Apple Silicon MLX 로컬 추론 스택으로 구성되어 있다.
2026-04-07 기준으로 개발 환경 세팅은 완료 상태다.

## 현재 상태

현재 이 저장소는 다음 조건을 만족한다.

- Python 기반 프로젝트 구조가 생성되어 있음
- `uv` 기반 가상환경 및 의존성 관리가 가능함
- Apple Silicon용 MLX 로컬 LLM/임베딩 런타임이 연결되어 있음
- 기본 모델이 프로젝트 설정에 반영되어 있음
- CLI로 환경 상태 확인 및 로컬 추론 smoke test 진입점이 준비되어 있음
- 테스트, 린트, 타입체크가 통과함

### 세팅 범위

1. **프로젝트 초기화**: `pyproject.toml`, `src/`, `tests/`, `data/`, `artifacts/`, `docs/` 구성
2. **패키지 및 가상환경**: `uv sync --all-groups` → `.venv`, `uv.lock` 생성
3. **로컬 모델 백엔드**: MLX 기반 LLM (`Qwen3.5-9B`) + 임베딩 (`Qwen3-Embedding-4B`)
4. **런타임 코드**: `config.py`, `llm.py`, `embedding.py`, `cli.py`
5. **검증 코드**: `test_config.py`, `test_llm.py`, `test_embedding.py`

### 기본 설정

```env
SID_RECO_LLM_BACKEND=mlx
SID_RECO_LLM_MODEL=mlx-community/Qwen3.5-9B-OptiQ-4bit
SID_RECO_EMBED_MODEL=mlx-community/Qwen3-Embedding-4B-4bit-DWQ
SID_RECO_CATALOG_PATH=data/catalog.csv
SID_RECO_CACHE_DIR=artifacts/sid_cache
SID_RECO_LLM_MAX_TOKENS=256
SID_RECO_LLM_TEMPERATURE=0.0
SID_RECO_LLM_TOP_P=1.0
```

## 사용법

### 환경 설치

```bash
uv sync --all-groups
source .venv/bin/activate
```

### 지원 환경

- 지원: 로그인된 로컬 `macOS Apple Silicon` 터미널 세션
- 비지원 또는 best-effort: `SSH`, `CI`, 샌드박스 에이전트, 백그라운드 헤드리스 세션
- 실제 생성/임베딩 실행 전에는 `smoke-mlx`로 MLX Metal 상태를 먼저 확인한다

### CLI 명령

```bash
uv run sid-reco doctor                              # 환경 상태 확인
uv run sid-reco smoke-mlx                           # MLX 런타임/Metal 진단
uv run sid-reco smoke-llm "사용자 취향을 요약해줘"    # LLM smoke test
uv run sid-reco smoke-embed "미스터리 스릴러 추천"    # 임베딩 smoke test
uv run sid-reco prepare-foodcom                      # Food.com 데이터 전처리
uv run sid-reco build-neighbor-context             # neighbor context 생성
uv run sid-reco build-taxonomy-dictionary           # taxonomy dictionary 생성
```

### Codex 명령

```text
/docs-manager lint
/docs-manager ingest docs/sources/<category>/<filename>
/docs-manager update <작업 설명>
```

### 검증 명령

```bash
uv run pytest                # 테스트
uv run ruff check .          # 린트
uv run mypy src              # 타입체크
```

### 검증 결과 (2026-04-07)

- `uv sync --all-groups` — 정상
- `uv run sid-reco doctor` — 정상
- `uv run pytest` — 통과
- `uv run ruff check .` — 통과
- `uv run mypy src` — 통과

### 현재 주의사항

- `smoke-mlx`가 실패하면 MLX/Metal 런타임 문제부터 해결해야 한다
- 현재 샌드박스 세션에서는 실제 MLX Metal 초기화가 실패할 수 있다

## 포함되지 않은 범위

개발 환경 세팅은 완료되었지만, 아래는 아직 구현되지 않았다.

- SID 생성 로직
- 아이템 카탈로그 로더
- candidate retrieval
- LLM reranking
- 추천 결과 평가 파이프라인

## Related

- [ADR-001: 개발 환경 및 로컬 추론 스택 결정](../decisions/adr-001-dev-environment.md) — 이 환경을 선택한 근거와 의사결정 기록
- [ADR-002: Food.com 전처리 정책 결정](../decisions/adr-002-foodcom-preprocessing-policy.md) — 데이터 전처리 규칙 결정
- [Food.com 데이터셋](food-com-dataset.md) — 현재 로컬에 확보한 추천 실험용 데이터셋
- [Food Taxonomy Dictionary](food-taxonomy-dictionary.md) — LLM 기반 domain taxonomy dictionary 생성 결과
- [Neighbor Context](neighbor-context-index.md) — item 임베딩과 FAISS 이웃 검색 산출물
- [ADR-004: Taxonomy Dictionary 생성 방식 결정](../decisions/adr-004-taxonomy-dictionary-generation.md) — superseded된 초기 taxonomy dictionary 생성 정책
- [ADR-005: Taxonomy Dictionary 생성 hardening 결정](../decisions/adr-005-taxonomy-dictionary-hardening.md) — 현재 bounded input과 validation 정책
- [Taxonomy Dictionary 개발 이슈 개요](../overviews/taxonomy-dictionary-development-issues.md) — 개발 및 검증 중 실제 발생한 런타임 이슈
