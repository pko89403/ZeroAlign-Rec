# Local Adaptation Rules

이 문서는 imported `agent-skills`를 `Training-Free-SID-Reco`에 맞게 해석하는
로컬 적응 규칙이다. upstream 문서와 충돌하면 이 문서를 우선한다.

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
| `references/` | `references/` |
| `.claude/commands/` | `.agents/skills/<shortcut>/SKILL.md` wrapper skills |
| `.claude/settings.json` | `.claude/settings.json` active safety hooks |
| Graphify primary graph | `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.json` |
| `skills/` | `.agents/skills/` |

## Primary Validation Commands

기본 품질 게이트는 아래 명령을 사용한다.

```bash
uv run pytest
uv run ruff check .
uv run mypy src
uv run sid-reco doctor
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
```

## Output Locations

- 스펙: `SPEC.md`
- primary graph artifact: `graphify-out/`
- source corpus: `raw/`

## Notes

- imported references는 일반 체크리스트다. Graphify source corpus는 `raw/`만 사용한다.
- taxonomy 관련 작업은 `build-neighbor-context` → `build-taxonomy-dictionary` → `structure-taxonomy-item|batch` 순서의 파이프라인을 기본 흐름으로 읽는다.
- Phase 1 SID 작업은 `structure-taxonomy-batch` 이후에 이어지며, 현재 구현 기준으로는 `compile-sid-index` CLI와 `src/sid_reco/sid/` 모듈이 `sid_index/serialized_items.jsonl`, `embeddings.npy`, `embedding_manifest.json`, `compiled_sid.jsonl`, `item_to_sid.json`, `sid_to_items.json`, `id_map.jsonl`, `item_index.faiss`, `recommendation_stats.json`, `manifest.json` 까지 산출한다.
- Phase 2 recommendation 경로는 `src/sid_reco/recommendation/`과 `sid-reco recommend`를 기준으로 읽고, 기본 생성 budget은 `SID_RECO_LLM_MAX_TOKENS=1024`를 사용한다.
- `structured taxonomy` 입력에는 중복 `recipe_id`가 허용되지 않으며, 중복이 있으면 serialization 단계에서 즉시 실패한다.
- 브라우저/웹 접근성/Core Web Vitals 항목은 HTML 리포트나 UI 작업이 실제로 있을 때만 적용한다.
- `npm audit`, `npm run build` 같은 문구는 일반 예시로 읽고, 실제 실행은 이 저장소의 `uv` 명령으로 치환한다.
- Codex App에서 repo-local slash-like entrypoint가 필요하면 command 파일이 아니라 skill 이름으로 노출되도록 wrapper skill을 만든다.
- `scripts/execute.py`는 선택적 Claude-driven phase executor다. 호출 시 `phases/`가 로컬에 생성되며, `.gitignore`로 커밋되지 않는다.
- Claude Code active safety hooks는 `.claude/settings.json`과 `scripts/hooks/claude-stop-checks.sh`를 기준으로 읽는다.
- Graphify bootstrap/regeneration은 `scripts/graphify_code_refresh.sh`를 우선 사용한다.
- `graphify update .`는 AST-only refresh이므로 committed graph bootstrap과 code drift 반영에 사용한다.
- doc/paper/image semantic refresh는 `raw/`를 source corpus로 하는 staged full refresh를 사용한다.
- curated full refresh가 필요하면 `scripts/graphify_prepare_corpus.sh`로 `.graphify-work/corpus/`를 준비하고, `scripts/graphify_full_refresh.py` -> `scripts/graphify_verify_full_refresh.py` -> `scripts/graphify_sync_staged.sh` 순서를 따른다.
- repo-local full refresh orchestration entrypoint는 `.agents/skills/graphify-manager/SKILL.md`다.
- `graphify-out/BUILD_INFO.json`의 `mode`가 `full_refresh`이고 `verified=true`이면 현재 `raw/` source corpus가 그래프에 반영된 상태로 본다.
- 사용자가 자연어로 PR 생성을 요청해도 `.github/pull_request_template.md`를 반드시 기준으로 사용한다.
- `gh pr create --body` 또는 `--body-file`는 템플릿을 우회할 수 있으므로, 템플릿 기반 본문을 먼저 만들지 않은 상태에서는 사용하지 않는다.
