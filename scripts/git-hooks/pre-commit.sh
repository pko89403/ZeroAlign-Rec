#!/bin/bash

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  script_dir="$(cd "$(dirname "$0")" && pwd)"
  repo_root="$(cd "$script_dir/../.." && pwd)"
fi

cd "$repo_root"

staged_python_files=$(git diff --cached --name-only --diff-filter=ACMR -- "*.py" "*.pyi")

if [ -z "$staged_python_files" ]; then
  exit 0
fi

set --
while IFS= read -r file; do
  [ -n "$file" ] || continue
  [ -f "$file" ] || continue
  set -- "$@" "$file"
done <<EOF
$staged_python_files
EOF

if [ "$#" -eq 0 ]; then
  exit 0
fi

echo "pre-commit: uv run ruff check --fix"
uv run ruff check --fix "$@"

echo "pre-commit: uv run ruff format"
uv run ruff format "$@"

git add -- "$@"
