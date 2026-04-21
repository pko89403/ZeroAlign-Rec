#!/bin/bash

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  script_dir="$(cd "$(dirname "$0")" && pwd)"
  repo_root="$(cd "$script_dir/.." && pwd)"
fi

cd "$repo_root"

mkdir -p .graphify-work

CANDIDATE_NOTE=".graphify-work/FULL_REFRESH_CANDIDATE.md"

cat > "$CANDIDATE_NOTE" <<'EOF'
# Graphify Full Refresh Candidate

Relevant code/docs changes were detected for Graphify full refresh.

CI prepared:
- `.graphify-work/corpus/`

CI did **not** run the full refresh producer, verify staged output, or overwrite root `graphify-out/`.
semantic/full refresh remains a human-triggered local maintainer workflow.

Recommended maintainer flow in a local checkout:

1. Run `bash scripts/graphify_prepare_corpus.sh`
2. Run `uv run --with graphifyy==0.4.23 python scripts/graphify_full_refresh.py .graphify-work/corpus`
3. Run `python3 scripts/graphify_verify_full_refresh.py .graphify-work/corpus/graphify-out`
4. Run `bash scripts/graphify_sync_staged.sh`
EOF

echo "graphify: candidate note written (producer not run in CI)"
