#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"
init_repo_context "$0"

cd "$REPO_ROOT"

echo "claude stop: uv run ruff check ."
uv run ruff check .

echo "claude stop: uv run ruff format --check ."
uv run ruff format --check .

# mypy/pytest는 pre-push.sh에만 유지 — Stop hook은 fire-and-forget(핫패스)이라
# 무거운 게이트는 회피. 매 턴마다 돌리는 비용 대비 차단 효과가 없음.
