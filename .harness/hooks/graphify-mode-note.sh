#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT="$REPO_ROOT/graphify-out/GRAPH_REPORT.md"
GRAPH_JSON="$REPO_ROOT/graphify-out/graph.json"
BUILD_INFO="$REPO_ROOT/graphify-out/BUILD_INFO.json"

if [ ! -f "$REPORT" ] || [ ! -f "$GRAPH_JSON" ]; then
  exit 0
fi

python3 - "$BUILD_INFO" <<'PY'
import json
import sys
from pathlib import Path

build_info = Path(sys.argv[1])
if not build_info.exists():
    print(
        "graphify: Primary graph exists at graphify-out/. Read GRAPH_REPORT.md first, then graph.json. "
        "BUILD_INFO is missing, so inspect raw/ directly if the graph lacks needed design or external source context."
    )
    raise SystemExit

data = json.loads(build_info.read_text(encoding="utf-8"))
mode = data.get("mode")
verified = bool(data.get("verified"))

if mode == "full_refresh" and verified:
    print(
        "graphify: Verified full_refresh graph with raw source coverage exists at graphify-out/. Read GRAPH_REPORT.md first, then graph.json and BUILD_INFO.json. "
        "Inspect raw/ only if the graph still lacks the needed design or external source context."
    )
else:
    print(
        "graphify: Code-only or unverified graph exists at graphify-out/. Read GRAPH_REPORT.md first, then graph.json and BUILD_INFO.json, "
        "and inspect raw/ directly for design or external source context when needed."
    )
PY
