#!/bin/bash

set -euo pipefail

init_repo_context() {
  local script_path="${1:-$0}"
  local script_dir

  REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [ -z "$REPO_ROOT" ]; then
    script_dir="$(cd "$(dirname "$script_path")" && pwd)"
    REPO_ROOT="$(cd "$script_dir/../.." && pwd)"
  fi

  GIT_ARGS=()
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    return 0
  fi

  if [ -d "$REPO_ROOT/.git" ] && git --git-dir="$REPO_ROOT/.git" --work-tree="$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    GIT_ARGS=(--git-dir="$REPO_ROOT/.git" --work-tree="$REPO_ROOT")
  fi
}

git_in_repo() {
  git "${GIT_ARGS[@]}" "$@"
}
