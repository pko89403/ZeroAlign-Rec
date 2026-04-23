#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"
init_repo_context "$0"

if ! git_in_repo rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  exit 0
fi

cd "$REPO_ROOT"

staged_files="$(git_in_repo diff --cached --name-only)"
if [ -z "$staged_files" ]; then
  exit 0
fi

warned=0

while IFS= read -r file; do
  [ -n "$file" ] || continue
  case "$file" in
    *.example)
      continue
      ;;
    .env|.env.*|*/.env|*/.env.*|*credentials.json|*secret.json|*secrets.json|*secret.yaml|*secrets.yaml|*secret.yml|*secrets.yml|*secret.toml|*secrets.toml|*.pem|*.key|*.p12|*.pfx)
      echo "WARN: staged file looks like secret material: $file" >&2
      warned=1
      ;;
  esac
done <<EOF
$staged_files
EOF

if git_in_repo diff --cached -U0 | grep -Eq '^\+.*(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|hf_[A-Za-z0-9]{20,}|BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY|anthropic_api_key|youtube_api_key)'; then
  echo "WARN: staged diff may contain credentials or private key material." >&2
  warned=1
fi

if [ "$warned" -eq 1 ]; then
  echo "BLOCKED: staged changes contain secret material. Unstage (git reset HEAD -- <file>) and strip the secret before retrying." >&2
  # exit 2 = Claude Code block signal. PostToolUse는 이미 실행된 git add/commit을
  # 되돌리진 못하지만, 에이전트에게 "반드시 rollback/재작업" 신호가 주입됨.
  # pre-commit hook에도 걸려 있으면 거기서 실제로 커밋 자체를 차단.
  exit 2
fi
