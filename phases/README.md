# phases

`phases/`는 선택적 실행 하네스 산출물 위치다.
`tasks/plan.md`, `tasks/todo.md`가 사람이 읽는 계획 문서라면,
`phases/`는 `scripts/execute.py`가 순차 실행하는 step bundle을 담는다.

## 용도

- 구현 계획을 독립 step으로 분해해 재현 가능한 실행 흐름으로 고정
- step별 상태(`pending`, `completed`, `error`, `blocked`) 기록
- Claude 세션 간 summary 누적
- branch 생성, 재시도, output snapshot 저장

## 구조

```text
phases/
├── index.json
└── <phase-name>/
    ├── index.json
    ├── step0.md
    ├── step1.md
    └── stepN-output.json
```

## 현재 저장소에서의 해석

- 최상위 규칙은 항상 `AGENTS.md`
- step 프롬프트는 `AGENTS.md`, `README.md`, `SPEC.md`,
  `.github/copilot-instructions.md`,
  `.harness/reference/local-adaptation.md`를 기본 guardrail로 읽는다
- `docs/sources/`는 immutable source material이므로 step에서 수정하면 안 된다
- 현재 executor는 unrelated local changes를 phase commit에 섞지 않기 위해 clean worktree를 요구한다
- 기본 branch prefix는 `codex/`다

## 실행

```bash
python3 scripts/execute.py <phase-name>
python3 scripts/execute.py <phase-name> --push
```

## 검증 기본값

Claude Code의 active safety hooks와 repo git hooks는 아래 검증 체인을 기준으로 맞춰져 있다.

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest --ignore=tests/test_mlx_runtime.py --ignore=tests/test_cli_smoke_mlx.py
```
