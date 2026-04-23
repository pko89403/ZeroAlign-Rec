#!/bin/bash
# PreToolUse:Write/Edit — block direct writes under graphify-out/ (generated output).
# Exit 2 blocks the tool call; refresh pipelines remain the only way in.

set -euo pipefail

input="${CLAUDE_TOOL_INPUT:-}"
file=$(echo "$input" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')

if echo "$file" | grep -qE '(^|/)graphify-out/'; then
  echo 'BLOCKED: graphify-out/ 는 generated output 입니다. refresh path를 사용하세요.' >&2
  exit 2
fi
