# Local Adaptation Rules

이 문서는 imported `agent-skills`를 `Training-Free-SID-Reco`에 맞게 해석하는
로컬 적응 규칙이다. upstream 문서와 충돌하면 이 문서를 우선한다.

## Top-Level Rules

- 최상위 규칙 파일은 `AGENTS.md`다.
- `docs/sources/`, `docs/wiki/`, `INDEX.md`, 카테고리 `README.md`, 위키 ADR 작업은
  항상 `docs-manager`와 `AGENTS.md` 스키마가 우선한다.
- imported general skills는 코드 구현, 테스트, 리뷰, 릴리스 워크플로에 우선 사용한다.

## Path Mapping

| Upstream expectation | This repository |
|---|---|
| `docs/decisions/` | `docs/wiki/decisions/` |
| `docs/ideas/` | `ideas/` |
| `CLAUDE.md` | `AGENTS.md` |
| `references/` | `references/` |
| `.claude/commands/` | `.agents/skills/<shortcut>/SKILL.md` wrapper skills |
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

- 아이디어 정리 산출물: `ideas/`
- 스펙: `SPEC.md`
- 작업 계획: `tasks/plan.md`, `tasks/todo.md`
- 위키/ADR: `docs/wiki/` 하위
- 리포트 HTML 등 생성물: `artifacts/reports/`

## Notes

- imported references는 일반 체크리스트다. 프로젝트 특화 검증은 항상 `README.md`와 `AGENTS.md`를 함께 본다.
- taxonomy 관련 작업은 `build-neighbor-context` → `build-taxonomy-dictionary` → `structure-taxonomy-item|batch` 순서의 파이프라인을 기본 흐름으로 읽는다.
- Phase 1 SID 작업은 `structure-taxonomy-batch` 이후에 이어지며, 현재 구현 기준으로는 `compile-sid-index` CLI와 `src/sid_reco/sid/` 모듈이 `sid_index/serialized_items.jsonl`, `embeddings.npy`, `embedding_manifest.json`, `compiled_sid.jsonl`, `item_to_sid.json`, `sid_to_items.json`, `id_map.jsonl`, `item_index.faiss`, `manifest.json` 까지 산출한다.
- Phase 2 recommendation 경로는 `src/sid_reco/recommendation/`과 `sid-reco recommend`를 기준으로 읽고, 기본 생성 budget은 `SID_RECO_LLM_MAX_TOKENS=1024`를 사용한다.
- `structured taxonomy` 입력에는 중복 `recipe_id`가 허용되지 않으며, 중복이 있으면 serialization 단계에서 즉시 실패한다.
- 브라우저/웹 접근성/Core Web Vitals 항목은 HTML 리포트나 UI 작업이 실제로 있을 때만 적용한다.
- `npm audit`, `npm run build` 같은 문구는 일반 예시로 읽고, 실제 실행은 이 저장소의 `uv` 명령으로 치환한다.
- Codex App에서 repo-local slash-like entrypoint가 필요하면 command 파일이 아니라 skill 이름으로 노출되도록 wrapper skill을 만든다.
