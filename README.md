# SID-Based Training-Free LLM Recommender

`SID` 기반 training-free 추천 시스템을 실험하기 위한 Python 개발 환경이다.
로컬 추론 백엔드는 `MLX`를 사용하며 기본 모델은 `Qwen3.5-9B`와 `Qwen3-Embedding-4B`다.

## Stack

- Python 3.12
- `uv` for dependency and virtual environment management
- `mlx-lm` for local generative inference on Apple Silicon
- `mlx-embeddings` for local embedding inference on Apple Silicon
- `typer` + `rich` for CLI utilities
- `pytest`, `ruff`, `mypy` for baseline quality checks

## Quick Start

```bash
uv sync --all-groups
source .venv/bin/activate
uv run sid-reco doctor
uv run sid-reco smoke-mlx
uv run sid-reco smoke-llm "사용자 취향을 요약해줘"
uv run sid-reco smoke-embed "범죄 스릴러 영화 추천"
uv run sid-reco prepare-foodcom --raw-dir data/raw/foodcom --out-dir data/processed/foodcom
uv run sid-reco build-taxonomy-step1
uv run sid-reco build-taxonomy-dictionary
uv run pytest
```

## Environment Variables

`.env.example`를 참고해서 `.env`를 만들고 값을 채우면 된다.

- `SID_RECO_LLM_BACKEND`: 현재는 `mlx`
- `SID_RECO_LLM_MODEL`: 생성형 LLM 모델 이름
- `SID_RECO_EMBED_MODEL`: 임베딩 모델 이름
- `SID_RECO_CATALOG_PATH`: 아이템 메타데이터 카탈로그 경로
- `SID_RECO_CACHE_DIR`: SID 생성 결과 및 중간 산출물 캐시 경로
- `SID_RECO_LLM_MAX_TOKENS`: 기본 생성 토큰 수
- `SID_RECO_LLM_TEMPERATURE`: 기본 temperature
- `SID_RECO_LLM_TOP_P`: 기본 nucleus sampling 값

## Supported Environment

- 지원: 로그인된 로컬 `macOS Apple Silicon` 터미널 세션
- 비지원 또는 best-effort: `SSH`, `CI`, 샌드박스 에이전트, 백그라운드 헤드리스 세션
- MLX/Metal 문제를 먼저 확인하려면 `uv run sid-reco smoke-mlx`를 실행한다

## Project Layout

```text
.
├── artifacts/         # generated outputs and caches
├── data/              # local datasets and catalogs
├── src/sid_reco/      # application package
└── tests/             # automated tests
```

## Useful Commands

```bash
uv run sid-reco doctor
uv run sid-reco smoke-mlx
uv run sid-reco smoke-llm "최근 본 아이템 로그를 요약해줘"
uv run sid-reco smoke-embed "미스터리 스릴러"
uv run sid-reco prepare-foodcom --raw-dir data/raw/foodcom --out-dir data/processed/foodcom
uv run sid-reco build-taxonomy-step1
uv run sid-reco build-taxonomy-dictionary
uv run pytest
uv run ruff check .
uv run mypy src
```

## Codex Skills And Shortcuts

Codex App의 built-in slash command와 별개로, 이 저장소는 repo-local skills를
`.agents/skills/`에 둔다. 공식 문서 기준으로 enabled skill은 slash 목록에 나타날 수 있다.

GitHub Copilot CLI / Chat용 프로젝트 지침은 `.github/copilot-instructions.md`에,
specialized agent persona는 `.github/agents/`에 둔다.

- 문서 워크플로: `/docs-manager` 또는 `/doc-manager`
- 스펙 작성: `/spec`
- 계획 분해: `/plan`
- 구현 진행: `/build`
- 테스트 우선 수정: `/test`
- 리뷰: built-in `/review` 또는 `$code-review-and-quality`
- 단순화: `/code-simplify`
- 릴리스 체크: `/ship`

Slash 목록에 바로 안 보이면 `$docs-manager`, `$spec` 같은 explicit skill invocation도 사용할 수 있다.
Skill을 추가하거나 수정한 직후에는 Codex App을 재시작해야 목록에 반영될 수 있다.

## Imported Agent Skills

`addyosmani/agent-skills`의 핵심 자산을 이 저장소에 이식했다.

- 활성 스킬: `.agents/skills/`
- Codex App shortcut wrapper skills: `.agents/skills/spec`, `.agents/skills/plan`, `.agents/skills/build` 등
- 하네스 support 자산 루트: `.harness/`
- 참조 체크리스트: `references/`
- 원본 문서 스냅샷: `.harness/reference/`
- 훅 스냅샷: `.harness/hooks/`
- archived draft command prompts: `.harness/reference/command-drafts/`
- archived persona markdown: `.harness/reference/agent-personas/`

로컬 적응 규칙은 `.harness/reference/local-adaptation.md`에 정리되어 있다.
문서/위키 작업은 일반 스킬보다 `docs-manager`와 `AGENTS.md` 규칙이 우선한다.
`.harness/README.md`는 tool-facing entrypoint와 support 자산의 역할 분리를 설명한다.

## Dataset Preparation

`Food.com Recipes & Interactions` 원본 CSV를 `data/raw/foodcom/RAW_recipes.csv`,
`data/raw/foodcom/RAW_interactions.csv`에 둔 뒤 아래 명령으로 소형화한다.

```bash
uv run sid-reco prepare-foodcom \
  --raw-dir data/raw/foodcom \
  --out-dir data/processed/foodcom \
  --top-recipes 3000 \
  --core-k 5 \
  --positive-threshold 4
```

생성 결과:

- `data/processed/foodcom/recipes.csv`
- `data/processed/foodcom/interactions.csv`
- `data/processed/foodcom/splits/train.csv`
- `data/processed/foodcom/splits/valid.csv`
- `data/processed/foodcom/splits/test.csv`
- `data/processed/foodcom/manifest.json`

원본과 가공 데이터는 로컬 전용 아티팩트로 취급하며 git에는 포함하지 않는다.
전처리는 `rating >= 4`만 positive로 유지하고, user/item `5-core` 필터링 후
시간 기준 `8:1:1` split을 생성한다.

## Taxonomy Step 1

전처리된 recipe catalog를 바탕으로 item 메타데이터 임베딩과 FAISS 기반 `top-5`
이웃 검색 결과를 생성한다.

```bash
uv run sid-reco build-taxonomy-step1 \
  --recipes-path data/processed/foodcom/recipes.csv \
  --out-dir data/processed/foodcom/taxonomy_step1 \
  --top-k 5
```

생성 결과:

- `data/processed/foodcom/taxonomy_step1/items_with_embeddings.csv`
- `data/processed/foodcom/taxonomy_step1/neighbor_context.csv`
- `data/processed/foodcom/taxonomy_step1/id_map.csv`
- `data/processed/foodcom/taxonomy_step1/item_index.faiss`
- `data/processed/foodcom/taxonomy_step1/manifest.json`

## Taxonomy Dictionary

Food.com recipe metadata 전체를 바탕으로 `TaxRec` 스타일의 domain taxonomy dictionary JSON을
로컬 LLM으로 생성한다. 입력 catalog가 1000개를 넘으면 taxonomy 생성 프롬프트에는
deterministic evenly spaced sampling으로 추린 최대 1000개 item만 포함한다. sampled payload가
여전히 너무 크면 프롬프트 payload 길이 상한 안에 들어올 때까지 item 수를 추가로 줄인다.

```bash
uv run sid-reco build-taxonomy-dictionary \
  --recipes-path data/processed/foodcom/recipes.csv \
  --out-dir data/processed/foodcom/taxonomy_dictionary \
  --max-tokens 4096
```

생성 결과:

- `data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json`
- `data/processed/foodcom/taxonomy_dictionary/prompt_snapshot.json`

주의:

- 모델 출력이 비어 있거나 normalization 후 usable feature/value가 하나도 남지 않으면 명령은 실패한다.
- `prompt_snapshot.json`에는 전체 item 수, 실제 프롬프트에 포함된 item 수, sampling strategy가 함께 기록된다.

## Taxonomy Item Structuring

생성된 master taxonomy dictionary와 taxonomy step 1의 `top-5` neighbor context를 함께 사용해
각 item을 taxonomy-aligned JSON으로 구조화할 수 있다. 출력 JSON은 모든 taxonomy key를 항상 포함하며,
각 key는 snake_case string 배열을 값으로 갖는다. value는 master vocabulary를 우선 사용하지만,
필요하면 open-vocabulary label도 허용한다. 모델 응답에 empty array가 있으면 최대 5회까지 재시도하고,
그래도 비어 있으면 해당 key는 `["empty"]`로 채운다.

단일 item:

```bash
uv run sid-reco structure-taxonomy-item \
  --recipe-id 101 \
  --recipes-path data/processed/foodcom/recipes.csv \
  --neighbor-context-path data/processed/foodcom/taxonomy_step1/neighbor_context.csv \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json
```

전체 batch:

```bash
uv run sid-reco structure-taxonomy-batch \
  --recipes-path data/processed/foodcom/recipes.csv \
  --neighbor-context-path data/processed/foodcom/taxonomy_step1/neighbor_context.csv \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json \
  --out-path data/processed/foodcom/taxonomy_structured/items.jsonl
```

생성 결과:

- single-item command: stdout JSON, optional `--out-path` JSON file
- batch command: `data/processed/foodcom/taxonomy_structured/items.jsonl`
- `--include-evidence`를 주면 single-item JSON 또는 batch JSONL 각 레코드에
  `target_item`과 ranked top-5 `neighbors` 근거가 함께 포함된다.

주의:

- item structuring은 target item마다 `neighbor_context.csv`에 top-5 neighbor rows가 있어야 한다.
- 출력 shape는 strict하게 검증하지만 value whitelist는 강제하지 않는다.

## Default Local Models

- Generative LLM: `mlx-community/Qwen3.5-9B-OptiQ-4bit`
- Embedding model: `mlx-community/Qwen3-Embedding-4B-4bit-DWQ`

첫 실행 시 Hugging Face에서 모델을 내려받기 때문에 시간이 걸릴 수 있다.
실제 생성/임베딩 실행 전에는 `uv run sid-reco smoke-mlx`로 MLX Metal 상태를 먼저 확인하는 편이 안전하다.

## Additional Docs

- [docs/wiki/entities/dev-environment.md](docs/wiki/entities/dev-environment.md): 개발 환경 세팅 상태와 사용법
- [docs/wiki/entities/food-com-dataset.md](docs/wiki/entities/food-com-dataset.md): Food.com 데이터셋 상태와 사용법
- [docs/wiki/entities/food-taxonomy-dictionary.md](docs/wiki/entities/food-taxonomy-dictionary.md): food taxonomy dictionary 생성 방식과 출력
- [docs/wiki/entities/taxonomy-step1-neighbor-index.md](docs/wiki/entities/taxonomy-step1-neighbor-index.md): taxonomy step 1 산출물과 사용법
- [docs/wiki/decisions/adr-001-dev-environment.md](docs/wiki/decisions/adr-001-dev-environment.md): 개발 환경 및 로컬 추론 스택 결정
- [docs/wiki/decisions/adr-002-foodcom-preprocessing-policy.md](docs/wiki/decisions/adr-002-foodcom-preprocessing-policy.md): Food.com 전처리 정책 결정
- [docs/wiki/decisions/adr-003-taxonomy-step1-neighbor-index.md](docs/wiki/decisions/adr-003-taxonomy-step1-neighbor-index.md): taxonomy step 1 이웃 검색 정책 결정
- [docs/wiki/decisions/adr-004-taxonomy-dictionary-generation.md](docs/wiki/decisions/adr-004-taxonomy-dictionary-generation.md): LLM 기반 taxonomy dictionary 생성 결정
