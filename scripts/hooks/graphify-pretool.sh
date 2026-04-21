#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NOTE="$("$SCRIPT_DIR/graphify-mode-note.sh" || true)"

if [ -z "${NOTE:-}" ]; then
  exit 0
fi

cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"$NOTE"}}
EOF
