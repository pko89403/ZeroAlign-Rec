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

echo "claude stop: uv run mypy src"
uv run mypy src

echo "claude stop: uv run pytest --ignore=tests/test_mlx_runtime.py --ignore=tests/test_cli_smoke_mlx.py"
uv run pytest --ignore=tests/test_mlx_runtime.py --ignore=tests/test_cli_smoke_mlx.py
