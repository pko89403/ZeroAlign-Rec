#!/bin/bash

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  script_dir="$(cd "$(dirname "$0")" && pwd)"
  repo_root="$(cd "$script_dir/.." && pwd)"
fi

cd "$repo_root"

GRAPHIFY_VERSION="0.4.23"
GRAPHIFY_CMD=(uvx --from "graphifyy==$GRAPHIFY_VERSION" graphify)

echo "graphify: refreshing committed code graph bootstrap"
"${GRAPHIFY_CMD[@]}" update .

for path in graphify-out/graph.html graphify-out/GRAPH_REPORT.md graphify-out/graph.json; do
  if [ ! -f "$path" ]; then
    echo "graphify: missing expected artifact: $path" >&2
    exit 1
  fi
done

python3 - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

build_info = {
    "graphify_version": "0.4.23",
    "mode": "code_update",
    "command": "uvx --from graphifyy==0.4.23 graphify update .",
    "generated_at": datetime.now(timezone.utc).isoformat(),
}
Path("graphify-out/BUILD_INFO.json").write_text(
    json.dumps(build_info, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
PY

echo "graphify: graphify-out refreshed"
