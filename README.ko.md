<p align="center">
  <img src="artifacts/branding/zeroalign-rec-logo.svg" alt="ZeroAlign-Rec logo" width="760">
</p>

<h1 align="center">ZeroAlign-Rec</h1>

<p align="center"><strong>Training-free semantic recommendation with SID, local MLX inference, and taxonomy-aware item alignment.</strong></p>

<p align="center"><a href="./README.md">English</a> | <strong>한국어</strong></p>

`ZeroAlign-Rec`은 `SID` 기반 training-free 추천 시스템을 로컬 환경에서 실험하기 위한 Python 코드베이스다. Apple Silicon에서 `MLX`를 사용해 생성형 LLM과 임베딩 모델을 로컬로 실행하고, Food.com 데이터셋 전처리부터 taxonomy dictionary 생성, taxonomy-aligned item structuring까지 한 흐름으로 검증할 수 있다.

## 목차

- [왜 ZeroAlign-Rec인가](#왜-zeroalign-rec인가)
- [요구 사항](#요구-사항)
- [설치](#설치)
- [빠른 시작](#빠른-시작)
- [핵심 워크플로](#핵심-워크플로)
- [설정](#설정)
- [검증](#검증)
- [저장소 구조](#저장소-구조)
- [문서와 지식 베이스](#문서와-지식-베이스)
- [Copilot 및 Agent 하네스](#copilot-및-agent-하네스)

## 왜 ZeroAlign-Rec인가

- **Training-free recommendation experiments**: SID 기반 추천 흐름을 별도 model training 없이 빠르게 검증할 수 있다.
- **Local-first inference**: `mlx-lm`과 `mlx-embeddings`를 사용해 Apple Silicon에서 로컬 추론을 수행한다.
- **Taxonomy-aware pipeline**: dataset preparation, neighbor index, taxonomy dictionary, item structuring을 단계별로 분리해 재현 가능하게 다룬다.
- **Agent-friendly repository**: Copilot/Codex용 `.github/`, `.agents/skills/`, `.harness/`, `AGENTS.md`가 함께 정리되어 있다.

## 요구 사항

- `macOS` on Apple Silicon
- Python `3.12`
- [`uv`](https://docs.astral.sh/uv/)
- 로컬 터미널 세션 권장

기본 로컬 모델:

- Generative LLM: `mlx-community/Qwen3.5-9B-OptiQ-4bit`
- Embedding model: `mlx-community/Qwen3-Embedding-4B-4bit-DWQ`

지원 환경과 관련해 가장 중요한 점:

- **권장**: 로그인된 로컬 macOS Apple Silicon 세션
- **best-effort**: SSH, CI, 샌드박스, 헤드리스 세션
- MLX/Metal 상태 점검은 `uv run sid-reco smoke-mlx`를 먼저 실행하는 것이 안전하다

## 설치

```bash
uv sync --all-groups
source .venv/bin/activate
cp .env.example .env
```

`.env`는 필요한 값만 채우면 된다. 상세 변수는 아래 [Configuration](#configuration)을 참고한다.

## 빠른 시작

가장 빠른 smoke path는 아래 순서다.

```bash
uv run sid-reco doctor
uv run sid-reco smoke-mlx
uv run sid-reco smoke-llm "사용자 취향을 요약해줘"
uv run sid-reco smoke-embed "범죄 스릴러 영화 추천"
```

이후 end-to-end 실험은 다음 순서로 이어간다.

```bash
uv run sid-reco prepare-foodcom --raw-dir data/raw/foodcom --out-dir data/processed/foodcom
uv run sid-reco build-taxonomy-step1
uv run sid-reco build-taxonomy-dictionary
uv run sid-reco structure-taxonomy-batch \
  --recipes-path data/processed/foodcom/recipes.csv \
  --neighbor-context-path data/processed/foodcom/taxonomy_step1/neighbor_context.csv \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json \
  --out-path data/processed/foodcom/taxonomy_structured/items.jsonl
```

## 핵심 워크플로

### 1. Food.com 데이터셋 준비

원본 CSV를 small-scale 실험용 catalog와 split으로 정리한다.

```bash
uv run sid-reco prepare-foodcom \
  --raw-dir data/raw/foodcom \
  --out-dir data/processed/foodcom \
  --top-recipes 3000 \
  --core-k 5 \
  --positive-threshold 4
```

주요 산출물:

- `data/processed/foodcom/recipes.csv`
- `data/processed/foodcom/interactions.csv`
- `data/processed/foodcom/splits/{train,valid,test}.csv`
- `data/processed/foodcom/manifest.json`

### 2. Taxonomy step 1 neighbor index 생성

item metadata embedding과 FAISS 기반 top-k neighbor context를 생성한다.

```bash
uv run sid-reco build-taxonomy-step1 \
  --recipes-path data/processed/foodcom/recipes.csv \
  --out-dir data/processed/foodcom/taxonomy_step1 \
  --top-k 5
```

주요 산출물:

- `items_with_embeddings.csv`
- `neighbor_context.csv`
- `item_index.faiss`
- `manifest.json`

### 3. Taxonomy dictionary 생성

로컬 LLM으로 domain taxonomy dictionary를 생성한다.

```bash
uv run sid-reco build-taxonomy-dictionary \
  --recipes-path data/processed/foodcom/recipes.csv \
  --out-dir data/processed/foodcom/taxonomy_dictionary \
  --max-tokens 4096
```

주요 산출물:

- `food_taxonomy_dictionary.json`
- `prompt_snapshot.json`

### 4. Taxonomy-aligned JSON으로 item 구조화

taxonomy dictionary와 step 1 neighbor context를 함께 사용해 item별 structured output을 만든다.

단일 item:

```bash
uv run sid-reco structure-taxonomy-item \
  --recipe-id 101 \
  --recipes-path data/processed/foodcom/recipes.csv \
  --neighbor-context-path data/processed/foodcom/taxonomy_step1/neighbor_context.csv \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json
```

batch:

```bash
uv run sid-reco structure-taxonomy-batch \
  --recipes-path data/processed/foodcom/recipes.csv \
  --neighbor-context-path data/processed/foodcom/taxonomy_step1/neighbor_context.csv \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json \
  --out-path data/processed/foodcom/taxonomy_structured/items.jsonl
```

## 설정

`.env.example`를 기준으로 `.env`를 만들고 필요한 값만 조정하면 된다.

| Variable | Description |
| --- | --- |
| `SID_RECO_LLM_BACKEND` | 현재는 `mlx` 사용 |
| `SID_RECO_LLM_MODEL` | 생성형 LLM 모델 이름 |
| `SID_RECO_EMBED_MODEL` | 임베딩 모델 이름 |
| `SID_RECO_CATALOG_PATH` | item metadata catalog 경로 |
| `SID_RECO_CACHE_DIR` | intermediate artifacts / cache 경로 |
| `SID_RECO_LLM_MAX_TOKENS` | 기본 생성 토큰 수 |
| `SID_RECO_LLM_TEMPERATURE` | 기본 temperature |
| `SID_RECO_LLM_TOP_P` | 기본 nucleus sampling 값 |

## 검증

```bash
uv run sid-reco doctor
uv run sid-reco smoke-mlx
uv run pytest
uv run ruff check .
uv run mypy src
```

## 저장소 구조

| Path | Role |
| --- | --- |
| `src/sid_reco/` | application package |
| `tests/` | automated tests |
| `data/` | local datasets and processed artifacts |
| `artifacts/` | generated reports, branding, and outputs |
| `docs/` | user-facing knowledge base and wiki |
| `.github/` | Copilot-facing instructions and agent personas |
| `.agents/skills/` | repo-local agent skills |
| `.harness/` | internal harness support and reference assets |
| `AGENTS.md` | top-level repository rules and schema |

## 문서와 지식 베이스

상세 설명은 README에 길게 중복하기보다 `docs/`와 위키 문서에 정리한다.

- [docs/README.md](docs/README.md)
- [docs/wiki/entities/dev-environment.md](docs/wiki/entities/dev-environment.md)
- [docs/wiki/entities/food-com-dataset.md](docs/wiki/entities/food-com-dataset.md)
- [docs/wiki/entities/food-taxonomy-dictionary.md](docs/wiki/entities/food-taxonomy-dictionary.md)
- [docs/wiki/entities/taxonomy-step1-neighbor-index.md](docs/wiki/entities/taxonomy-step1-neighbor-index.md)
- [docs/wiki/decisions/adr-001-dev-environment.md](docs/wiki/decisions/adr-001-dev-environment.md)
- [docs/wiki/decisions/adr-002-foodcom-preprocessing-policy.md](docs/wiki/decisions/adr-002-foodcom-preprocessing-policy.md)
- [docs/wiki/decisions/adr-003-taxonomy-step1-neighbor-index.md](docs/wiki/decisions/adr-003-taxonomy-step1-neighbor-index.md)
- [docs/wiki/decisions/adr-004-taxonomy-dictionary-generation.md](docs/wiki/decisions/adr-004-taxonomy-dictionary-generation.md)

## Copilot 및 Agent 하네스

이 저장소는 Copilot/Codex 친화적인 harness를 함께 유지한다.

- Copilot 프로젝트 지침: `.github/copilot-instructions.md`
- specialized personas: `.github/agents/`
- repo-local skills: `.agents/skills/`
- harness support assets: `.harness/`
- local adaptation rules: `.harness/reference/local-adaptation.md`

주요 shortcut:

- `/docs-manager` or `/doc-manager`
- `/spec`
- `/plan`
- `/build`
- `/test`
- `/code-simplify`
- `/ship`

문서/위키 작업에서는 일반 workflow보다 `docs-manager`와 `AGENTS.md` 규칙이 우선한다.
