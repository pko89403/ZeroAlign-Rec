#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"
init_repo_context "$0"

cd "$REPO_ROOT"

staged_python_files=$(git_in_repo diff --cached --name-only --diff-filter=ACMR -- "*.py" "*.pyi")

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

git_in_repo add -- "$@"
