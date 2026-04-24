#!/usr/bin/env bash
set -euo pipefail

[ -f graphify-out/graph.json ] || exit 0

INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | python3 -c '
import sys, json
try:
    print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))
except Exception:
    pass
' 2>/dev/null || true)

SEARCH_CMD_REGEX='(^|[^a-zA-Z0-9_])(grep|egrep|fgrep|rg|ripgrep|ack|ag|find|fd)([^a-zA-Z0-9_]|$)'
if [[ "$CMD" =~ $SEARCH_CMD_REGEX ]]; then
  cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"graphify: Knowledge graph exists. Read graphify-out/GRAPH_REPORT.md for god nodes and community structure before searching raw files."}}
JSON
fi
