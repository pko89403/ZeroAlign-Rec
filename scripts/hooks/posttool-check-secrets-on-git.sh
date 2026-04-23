#!/bin/bash
# PostToolUse:Bash — run check-secrets.sh only when the Bash call was git add/commit.
# Non-blocking: check-secrets.sh itself emits stderr warnings only.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cmd="${CLAUDE_TOOL_INPUT:-}"

if echo "$cmd" | grep -qE 'git[[:space:]]+add|git[[:space:]]+commit'; then
  bash "$SCRIPT_DIR/check-secrets.sh"
fi
