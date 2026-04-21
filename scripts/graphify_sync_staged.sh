#!/bin/bash

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  script_dir="$(cd "$(dirname "$0")" && pwd)"
  repo_root="$(cd "$script_dir/.." && pwd)"
fi

cd "$repo_root"

STAGED_DIR="${1:-.graphify-work/corpus/graphify-out}"
ROOT_GRAPH_DIR="graphify-out"

for path in \
  "$STAGED_DIR/graph.html" \
  "$STAGED_DIR/GRAPH_REPORT.md" \
  "$STAGED_DIR/graph.json" \
  "$STAGED_DIR/BUILD_INFO.json" \
  "$STAGED_DIR/VERIFY_FULL_REFRESH.json"
do
  if [ ! -f "$path" ]; then
    echo "missing required staged artifact: $path" >&2
    exit 1
  fi
done

python3 - "$STAGED_DIR/BUILD_INFO.json" <<'PY'
import json
import sys
from pathlib import Path

build_info = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if build_info.get("mode") != "full_refresh":
    raise SystemExit("BUILD_INFO.json must declare mode=full_refresh before sync")
if build_info.get("verified") is not True:
    raise SystemExit("BUILD_INFO.json must declare verified=true before sync")
PY

mkdir -p "$ROOT_GRAPH_DIR"
cp "$STAGED_DIR/graph.html" "$ROOT_GRAPH_DIR/graph.html"
cp "$STAGED_DIR/GRAPH_REPORT.md" "$ROOT_GRAPH_DIR/GRAPH_REPORT.md"
cp "$STAGED_DIR/graph.json" "$ROOT_GRAPH_DIR/graph.json"
cp "$STAGED_DIR/BUILD_INFO.json" "$ROOT_GRAPH_DIR/BUILD_INFO.json"

echo "graphify: synced verified staged full refresh into $ROOT_GRAPH_DIR"
