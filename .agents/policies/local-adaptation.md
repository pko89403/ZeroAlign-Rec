# Local Adaptation Rules

이 문서는 imported `agent-skills`를 `Training-Free-SID-Reco`에 맞게 해석하는 **로컬 적응 규칙** 그리고 이 저장소의 **도메인 구체 정보**를 담는다.
`CLAUDE.md`(= `AGENTS.md`)가 스키마/메타/거버넌스 레이어라면, 이 문서는 그 아래에서 실제 도메인을 기술한다.
upstream 문서와 충돌하면 이 문서를 우선한다.

## Top-Level Rules

- 최상위 규칙 파일은 `AGENTS.md`다.
- primary machine-readable knowledge layer는 `graphify-out/`다.
- `raw/`가 Graphify source corpus의 정본이다.
- `graphify-out/`가 generated graph output이다.
- imported general skills는 코드 구현, 테스트, 리뷰, 릴리스 워크플로에 우선 사용한다.

## Path Mapping

| Upstream expectation | This repository |
|---|---|
| `docs/decisions/` | `raw/design/adr/` |
| `CLAUDE.md` | `AGENTS.md` |
| `.claude/commands/` | `.agents/skills/<shortcut>/SKILL.md` wrapper skills |
| `.claude/settings.json` | `.claude/settings.json` active safety hooks |
| Graphify primary graph | `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.json` |
| `skills/` | `.agents/skills/` |

## Primary Tech Stack

- **로컬 추론**: Apple Silicon MLX (`mlx-lm`, `mlx-embeddings`)
- **생성 모델**: `mlx-community/Qwen3.5-9B-OptiQ-4bit`
- **임베딩 모델**: `mlx-community/Qwen3-Embedding-4B-4bit-DWQ`
- **패키지 관리**: `uv`
- **CLI**: `typer` + `rich`

## Main Modules

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

## Primary Validation Commands

기본 품질 게이트는 아래 명령을 사용한다.

```bash
uv sync --all-groups          # 의존성 설치
uv run pytest                 # 테스트
uv run ruff check .           # 린트
uv run mypy src               # 타입체크
uv run sid-reco doctor        # 환경 상태 확인
uv run sid-reco smoke-mlx     # MLX 런타임 진단
```

도메인별 추가 검증 예시:

```bash
uv run sid-reco smoke-llm "사용자 취향을 요약해줘"
uv run sid-reco smoke-embed "미스터리 스릴러"
uv run sid-reco recommend --help
uv run sid-reco build-neighbor-context --help
uv run sid-reco build-taxonomy-dictionary --help
uv run sid-reco structure-taxonomy-item --help
uv run sid-reco structure-taxonomy-batch --help
uv run sid-reco compile-sid-index --help
```

## Repo-local Codex Commands

이 저장소의 repo-local Codex 확장점은 `.agents/skills/`다.
공식 Codex App built-in slash command와는 별개로, enabled skill은 slash 목록에 나타날 수 있다.

- `/docs-manager` 또는 `/doc-manager` — `raw/` source corpus 관리와 `README.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `.agents/policies/local-adaptation.md` 동기화를 포함한 문서 반영 루틴
- `/spec` — 구현 전에 `raw/design/specs/ski-NNN-*.md`를 정리하는 spec-driven workflow (이슈 단위 1 파일)
- `/plan` — spec-driven workflow 후속 작업 분해
- `/build` — incremental-implementation + TDD 기반 구현 흐름
- `/test` — TDD / Prove-It 기반 검증 흐름
- built-in `/review` 또는 `$code-review-and-quality` — 5축 코드 리뷰
- `/code-simplify` — 동작 보존 단순화 검토
- `/ship` — 배포/릴리스 전 체크리스트
- `/graphify-manager` — full refresh orchestration (producer → verify → sync)
- `/graphify-full` — graphify-manager wrapper로 full refresh 1회 실행

## Output Locations

- 스펙: `raw/design/specs/ski-NNN-*.md` (이슈 단위 1 파일, ADR 네이밍 규약과 동일 패턴)
- primary graph artifact: `graphify-out/`
- source corpus: `raw/`

## Language Conventions

- `raw/design/**` 문서는 한국어로 유지한다.
- `raw/design/specs/**`, `tasks/plan.md`, `tasks/todo.md`는 신규 작성 또는 의미있는 개정 시 한국어로 작성한다. 기존 영어 내용은 즉시 번역할 의무는 없다.

> graphify orchestration 세부(실행 경로, 커밋 산출물, BUILD_INFO trust signal, hooks auto-refresh 동작 등)는 [`.agents/skills/graphify-manager/SKILL.md`](../.agents/skills/graphify-manager/SKILL.md)를 참조한다.

## Notes

- imported references는 일반 체크리스트다. Graphify source corpus는 `raw/`만 사용한다.
- taxonomy 관련 작업은 `build-neighbor-context` → `build-taxonomy-dictionary` → `structure-taxonomy-item|batch` 순서의 파이프라인을 기본 흐름으로 읽는다.
- Phase 1 SID 작업은 `structure-taxonomy-batch` 이후에 이어지며, 현재 구현 기준으로는 `compile-sid-index` CLI와 `src/sid_reco/sid/` 모듈이 `sid_index/serialized_items.jsonl`, `embeddings.npy`, `embedding_manifest.json`, `compiled_sid.jsonl`, `item_to_sid.json`, `sid_to_items.json`, `id_map.jsonl`, `item_index.faiss`, `recommendation_stats.json`, `manifest.json` 까지 산출한다.
- Phase 2 recommendation 경로는 `src/sid_reco/recommendation/`과 `sid-reco recommend`를 기준으로 읽고, 기본 생성 budget은 `SID_RECO_LLM_MAX_TOKENS=1024`를 사용한다.
- `structured taxonomy` 입력에는 중복 `recipe_id`가 허용되지 않으며, 중복이 있으면 serialization 단계에서 즉시 실패한다.
- 브라우저/웹 접근성/Core Web Vitals 항목은 HTML 리포트나 UI 작업이 실제로 있을 때만 적용한다.
- `npm audit`, `npm run build` 같은 문구는 일반 예시로 읽고, 실제 실행은 이 저장소의 `uv` 명령으로 치환한다.
- Codex App에서 repo-local slash-like entrypoint가 필요하면 command 파일이 아니라 skill 이름으로 노출되도록 wrapper skill을 만든다.
- `scripts/execute.py`는 선택적 Claude-driven phase executor다. 동작 계약:
  - 사용자가 `phases/<phase-name>/index.json`을 먼저 수동 작성해야 한다 (executor는 자동 생성하지 않고, 없으면 `SystemExit(1)`).
  - `phases/`는 `.gitignore`에 등록된 로컬 스크래치 디렉터리 — phase 메타데이터는 커밋 대상이 아니고 사용자 개인 worktree 안에서만 유지된다.
  - executor를 실제로 쓸 때는 `mkdir -p phases/<phase>` 후 `index.json`을 생성해서 bootstrap한다.
- Claude Code active safety hooks는 `.claude/settings.json`과 `scripts/hooks/claude-stop-checks.sh`를 기준으로 읽는다.
- curated full refresh가 필요하면 `scripts/graphify_prepare_corpus.sh`로 `.graphify-work/corpus/`를 준비하고, `scripts/graphify_full_refresh.py` -> `scripts/graphify_verify_full_refresh.py` -> `scripts/graphify_sync_staged.sh` 순서를 따른다.
- repo-local full refresh orchestration entrypoint는 `.agents/skills/graphify-manager/SKILL.md`다.
- `graphify-out/BUILD_INFO.json`의 `mode`가 `full_refresh`이고 `verified=true`이면 현재 `raw/` source corpus가 그래프에 반영된 상태로 본다.
- 사용자가 자연어로 PR 생성을 요청해도 `.github/pull_request_template.md`를 반드시 기준으로 사용한다.
- `gh pr create --body` 또는 `--body-file`는 템플릿을 우회할 수 있으므로, 템플릿 기반 본문을 먼저 만들지 않은 상태에서는 사용하지 않는다.
