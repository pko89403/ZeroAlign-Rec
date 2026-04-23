#!/bin/bash
# PreToolUse:Write/Edit — warn when the target file looks like secret material.
# Non-blocking: writes a stderr note only; final secret enforcement is on commit.

set -euo pipefail

input="${CLAUDE_TOOL_INPUT:-}"
file=$(echo "$input" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
basename=$(basename "$file")

if echo "$basename" | grep -qiE '^\.env$|^\.env\.|^credentials\.json$|^secrets?\.(json|yaml|yml|toml)$|\.pem$|\.key$|\.p12$|\.pfx$'; then
  if ! echo "$basename" | grep -qE '\.example$'; then
    echo "WARN: 시크릿 파일 쓰기/수정 감지: $file" >&2
  fi
fi
