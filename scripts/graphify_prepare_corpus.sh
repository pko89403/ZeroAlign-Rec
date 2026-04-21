#!/bin/bash

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  script_dir="$(cd "$(dirname "$0")" && pwd)"
  repo_root="$(cd "$script_dir/.." && pwd)"
fi

cd "$repo_root"

CORPUS_ROOT=".graphify-work/corpus"
rm -rf "$CORPUS_ROOT"
python3 - <<'PY'
from pathlib import Path
import shutil

root = Path(".")
corpus = Path(".graphify-work/corpus")
corpus.mkdir(parents=True, exist_ok=True)


def _ignore(dirpath: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name == "__pycache__":
            ignored.add(name)
        elif name.endswith(".pyc"):
            ignored.add(name)
    return ignored


shutil.copytree(root / "src", corpus / "src", dirs_exist_ok=True, ignore=_ignore)
shutil.copytree(root / "tests", corpus / "tests", dirs_exist_ok=True, ignore=_ignore)
shutil.copytree(root / "raw", corpus / "raw", dirs_exist_ok=True, ignore=_ignore)
PY

echo "graphify: prepared staged corpus at $CORPUS_ROOT"
