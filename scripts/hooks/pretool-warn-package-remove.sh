#!/bin/bash
# PreToolUse:Bash — warn on package uninstall / cache clean commands.
# Non-blocking: always exits 0 and only writes to stderr when a match fires.

set -euo pipefail

cmd="${CLAUDE_TOOL_INPUT:-}"

if echo "$cmd" | grep -qE 'pip[[:space:]]+uninstall|uv[[:space:]]+pip[[:space:]]+uninstall|npm[[:space:]]+uninstall|npm[[:space:]]+cache[[:space:]]+clean|yarn[[:space:]]+remove|pnpm[[:space:]]+remove'; then
  echo 'WARN: 패키지 제거 또는 캐시 삭제 명령입니다. 의도한 것인지 확인하세요.' >&2
fi
