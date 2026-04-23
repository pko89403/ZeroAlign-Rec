#!/bin/bash
# PreToolUse:Bash — block destructive shell commands.
# Exit 2 blocks the tool call and surfaces stderr to Claude.
# Exit 0 allows.

set -euo pipefail

cmd="${CLAUDE_TOOL_INPUT:-}"

if echo "$cmd" | grep -qE 'rm[[:space:]]+-rf|git[[:space:]]+push[[:space:]]+--force|git[[:space:]]+reset[[:space:]]+--hard|git[[:space:]]+checkout[[:space:]]+--|git[[:space:]]+clean[[:space:]]+-fd|git[[:space:]]+branch[[:space:]]+-D|find[[:space:]]+.+[[:space:]]+-delete'; then
  echo 'BLOCKED: 위험한 destructive 명령이 감지되었습니다.' >&2
  exit 2
fi
