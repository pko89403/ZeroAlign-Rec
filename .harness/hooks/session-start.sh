#!/bin/bash
# agent-skills session start hook
# Injects the using-agent-skills meta-skill into every new session

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SKILLS_DIR="$REPO_ROOT/.agents/skills"
META_SKILL="$SKILLS_DIR/using-agent-skills/SKILL.md"
GRAPHIFY_REPORT="$REPO_ROOT/graphify-out/GRAPH_REPORT.md"
GRAPHIFY_JSON="$REPO_ROOT/graphify-out/graph.json"
GRAPHIFY_BUILD_INFO="$REPO_ROOT/graphify-out/BUILD_INFO.json"
GRAPHIFY_MODE_NOTE_SCRIPT="$REPO_ROOT/.harness/hooks/graphify-mode-note.sh"

if [ -f "$META_SKILL" ]; then
  CONTENT=$(cat "$META_SKILL")
  GRAPHIFY_NOTE=""
  if [ -f "$GRAPHIFY_REPORT" ] && [ -f "$GRAPHIFY_JSON" ] && [ -x "$GRAPHIFY_MODE_NOTE_SCRIPT" ]; then
    MODE_NOTE=$("$GRAPHIFY_MODE_NOTE_SCRIPT" || true)
    if [ -n "${MODE_NOTE:-}" ]; then
      GRAPHIFY_NOTE="\n\n$MODE_NOTE"
    fi
  fi
  # Output as JSON for Claude Code hook consumption
  cat <<EOF
{
  "priority": "IMPORTANT",
  "message": "agent-skills loaded. Use the skill discovery flowchart to find the right skill for your task.$GRAPHIFY_NOTE\n\n$CONTENT"
}
EOF
else
  echo '{"priority": "INFO", "message": "agent-skills: using-agent-skills meta-skill not found. Skills may still be available individually."}'
fi
