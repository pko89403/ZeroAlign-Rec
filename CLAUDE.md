# AGENTS.md

이 파일은 LLM이 이 프로젝트의 지식 저장소를 체계적으로 관리하기 위한 스키마 레이어다.
사용자와 LLM이 시간이 지남에 따라 함께 진화시킨다.

---

## 프로젝트 개요

SID(Semantic ID) 기반 training-free 추천 시스템을 로컬 환경에서 실험하기 위한 Python 코드베이스다.

- **로컬 추론**: Apple Silicon MLX (`mlx-lm`, `mlx-embeddings`)
- **생성 모델**: `mlx-community/Qwen3.5-9B-OptiQ-4bit`
- **임베딩 모델**: `mlx-community/Qwen3-Embedding-4B-4bit-DWQ`
- **패키지 관리**: `uv`
- **CLI**: `typer` + `rich`

### 주요 모듈

| 모듈 | 경로 | 역할 |
|------|------|------|
| config | `src/sid_reco/config.py` | 환경 변수 + `.env` 기반 설정, 경로 해석 |
| llm | `src/sid_reco/llm.py` | `MLXTextGenerator` — 로컬 생성 추론 |
| embedding | `src/sid_reco/embedding.py` | `MLXEmbeddingEncoder` — 로컬 임베딩 추론 |
| mlx_runtime | `src/sid_reco/mlx_runtime.py` | MLX 런타임 probe 및 지원 환경 진단 |
| datasets | `src/sid_reco/datasets/` | 데이터셋 로더 및 전처리 (`foodcom.py`) |
| taxonomy | `src/sid_reco/taxonomy/` | neighbor context 임베딩/FAISS 검색, taxonomy dictionary 생성, item-level taxonomy structuring (`item_projection.py`) |
| sid | `src/sid_reco/sid/` | Phase 1 마지막 단계용 structured item serialization, MLX embedding, CPU residual K-means compiler, FAISS indexing, recommendation statistics 생성 (`serialization.py`, `embed_backend.py`, `compiler.py`, `indexing.py`, `stats.py`) |
| recommendation | `src/sid_reco/recommendation/` | Phase 2 recommendation pipeline: interest sketch, semantic retrieval, bootstrap rerank, confidence aggregation, grounding |
| cli | `src/sid_reco/cli.py` | `doctor`, `smoke-mlx`, `smoke-llm`, `smoke-embed`, `prepare-foodcom`, `build-neighbor-context`, `build-taxonomy-dictionary`, `structure-taxonomy-item`, `structure-taxonomy-batch`, `compile-sid-index`, `recommend` |

### 빌드 및 검증 명령

```bash
uv sync --all-groups          # 의존성 설치
uv run pytest                 # 테스트
uv run ruff check .           # 린트
uv run mypy src               # 타입체크
uv run sid-reco doctor        # 환경 상태 확인
uv run sid-reco smoke-mlx     # MLX 런타임 진단
uv run sid-reco recommend --help
uv run sid-reco build-neighbor-context --help
uv run sid-reco build-taxonomy-dictionary --help
uv run sid-reco structure-taxonomy-item --help
uv run sid-reco structure-taxonomy-batch --help
uv run sid-reco compile-sid-index --help
```

### Repo-local Codex Commands

이 저장소의 repo-local Codex 확장점은 `.agents/skills/`다.
공식 Codex App built-in slash command와는 별개로, enabled skill은 slash 목록에 나타날 수 있다.

- `/docs-manager` 또는 `/doc-manager` — `raw/` source corpus 관리와 `README.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `references/local-adaptation.md` 동기화를 포함한 문서 반영 루틴
- `/spec` — 구현 전에 `SPEC.md`를 정리하는 spec-driven workflow
- `/plan` — spec-driven workflow 후속 작업 분해
- `/build` — incremental-implementation + TDD 기반 구현 흐름
- `/test` — TDD / Prove-It 기반 검증 흐름
- built-in `/review` 또는 `$code-review-and-quality` — 5축 코드 리뷰
- `/code-simplify` — 동작 보존 단순화 검토
- `/ship` — 배포/릴리스 전 체크리스트

---

## 개발 워크플로 스킬 레이어

이 저장소에는 범용 엔지니어링 워크플로 스킬 레이어도 함께 존재한다.

- 활성 스킬 위치: `.agents/skills/`
- Claude runtime 설정: `.claude/settings.json`
- Codex hook 설정: `.codex/hooks.json`
- 체크리스트 및 upstream 참조: `references/`
- hook 스크립트: `scripts/hooks/`
- optional phase executor: `scripts/execute.py`

운영 원칙:

1. `raw/`, `graphify-out/`, ADR/설계 노트 작업은 항상 `docs-manager`와 이 `AGENTS.md` 스키마가 우선한다.
2. 코드 구현, 테스트, 리뷰, 릴리스 흐름은 imported agent skills를 사용할 수 있다.
3. imported skill의 일반 예시가 이 저장소 구조와 충돌하면 `references/local-adaptation.md` 규칙을 우선한다.
4. `raw/design/**` 문서는 계속 한국어로 유지한다.
5. Claude Code safety hooks는 `.claude/settings.json`과 `scripts/hooks/` 스크립트로 활성화된다.
6. primary machine-readable knowledge layer는 `graphify-out/`다.
7. Graphify의 유일한 source corpus는 `raw/`다.
8. `scripts/graphify_code_refresh.sh`는 code-only bootstrap이고, full refresh는 `graphify-manager` skill이 orchestration 한다.
9. 사용자가 자연어로 PR 생성을 요청해도 `.github/pull_request_template.md`를 반드시 기준으로 사용한다.
10. `gh pr create --body` 또는 `--body-file`로 템플릿을 우회하지 않는다. `gh`를 쓸 때는 `--template .github/pull_request_template.md` 또는 동등한 템플릿 기반 경로를 사용한다.
11. 사용자에게 의사결정 옵션을 제시할 때는 공수가 크더라도 근본적으로 '제대로된 방향'을 권장안으로 먼저 제안한다. 공수 절충안이나 현상 유지 옵션은 권장안 뒤에 함께 병기한다.

---

## 3-레이어 아키텍처

이 프로젝트의 지식 저장소는 3개 레이어로 구성된다.

```
.
├── AGENTS.md                          ← 스키마 레이어 (이 파일)
├── graphify-out/                      ← primary machine-readable knowledge graph
└── raw/                               ← human-owned source corpus
    ├── design/
    │   ├── adr/                       ADR / 의사결정 기록
    │   ├── specs/                     설계 스펙
    │   ├── diagrams/                  다이어그램 source
    │   ├── screenshots/               시각 reference
    │   └── notes/                     설계 노트 / 개요
    └── external/
        ├── papers/                    논문/외부 문서
        ├── datasets/                  데이터셋 원문 문서
        ├── models/                    모델 원문 문서
        └── experiments/               실험 자료
```

### 레이어 1: 원문 소스 (`raw/`)

**진실의 원천(Source of Truth)**이다.

- `raw/design/**`는 설계/ADR/노트/다이어그램 source다
- `raw/external/**`는 논문/데이터셋/모델/실험 원문 source다
- `references/`는 하네스 체크리스트이며 Graphify source가 아니다

### 레이어 2: Primary Graph (`graphify-out/`)

현재 assistant가 먼저 읽어야 하는 machine-readable knowledge layer다.

- Graphify 산출물은 커밋 대상이다: `graph.html`, `GRAPH_REPORT.md`, `graph.json`
- code bootstrap regenerate는 `scripts/graphify_code_refresh.sh`를 사용한다
- `graphify-out/BUILD_INFO.json`을 읽어 `code_update`인지 `full_refresh`인지 먼저 확인한다
- full refresh는 `graphify-manager` skill과 staged corpus 경로를 통해 수행한다
- full refresh 입력은 `src/`, `tests/`, `raw/`만 사용한다

### 레이어 3: 스키마 (이 파일)

LLM에게 현재 knowledge model과 Graphify-first 운영 규칙을 알려주는 설정 문서다.
사용자와 LLM이 시간이 지남에 따라 함께 진화시킨다.

## graphify

This project has a graphify knowledge graph at `graphify-out/`.

Rules:

- Before answering architecture or codebase questions, read `graphify-out/GRAPH_REPORT.md` for god nodes and community structure.
- If `GRAPH_REPORT.md` is insufficient, inspect `graphify-out/graph.json` next and use `raw/` only for source-level confirmation.

Project overrides:

- For code-only refresh after source changes, run `bash scripts/graphify_code_refresh.sh`.
- Do not treat raw `graphify update .` as a substitute for the repository's full refresh path.
- For docs/design semantic refresh, use `graphify-manager` or the staged full refresh flow: producer -> verify -> sync.
- Use `graphify-out/BUILD_INFO.json` as the trust signal for `code_update` vs `full_refresh`.
- hooks automatically refresh the graph after relevant local edits. Code-only changes may produce `code_update`, while `raw/` changes trigger the staged full refresh flow. CI remains candidate-only and does not promote root `graphify-out/`.
