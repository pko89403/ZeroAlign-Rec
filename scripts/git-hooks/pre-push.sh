#!/bin/bash

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  script_dir="$(cd "$(dirname "$0")" && pwd)"
  repo_root="$(cd "$script_dir/../.." && pwd)"
fi

cd "$repo_root"

echo "pre-push: uv run ruff check ."
uv run ruff check .

echo "pre-push: uv run ruff format --check ."
uv run ruff format --check .

echo "pre-push: uv run mypy src"
uv run mypy src

echo "pre-push: uv run pytest --ignore=tests/test_mlx_runtime.py --ignore=tests/test_cli_smoke_mlx.py"
uv run pytest --ignore=tests/test_mlx_runtime.py --ignore=tests/test_cli_smoke_mlx.py
