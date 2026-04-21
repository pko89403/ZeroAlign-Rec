#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"
init_repo_context "$0"

cd "$REPO_ROOT"

mkdir -p .graphify-work

STATE_FILE=".graphify-work/auto_refresh_state.json"

if [ "${#GIT_ARGS[@]}" -eq 2 ]; then
  export GIT_DIR="${GIT_ARGS[0]#--git-dir=}"
  export GIT_WORK_TREE="${GIT_ARGS[1]#--work-tree=}"
fi

python3 - <<'PY'
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(".").resolve()
STATE_FILE = ROOT / ".graphify-work" / "auto_refresh_state.json"
BUILD_INFO_FILE = ROOT / "graphify-out" / "BUILD_INFO.json"


def _iter_files(paths: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for path in paths:
        if path.is_file():
            files.add(path)
        elif path.is_dir():
            files.update(candidate for candidate in path.rglob("*") if candidate.is_file())
    return sorted(files)


def _digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in _iter_files(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _load_state() -> dict[str, str]:
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def _write_state(payload: dict[str, str]) -> None:
    payload = {"schema_version": "raw-source-v1", **payload}
    STATE_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _run(command: list[str], *, label: str) -> bool:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"graphify auto-refresh: {label} completed")
        return True

    print(f"graphify auto-refresh: {label} failed", flush=True)
    if result.stdout.strip():
        print(result.stdout.strip(), flush=True)
    if result.stderr.strip():
        print(result.stderr.strip(), flush=True)
    return False


def _detect_bootstrap_changes() -> tuple[bool, bool]:
    result = subprocess.run(
        [
            "git",
            "status",
            "--short",
            "--untracked-files=all",
            "--",
            "src",
            "tests",
            "raw",
            "scripts/graphify_code_refresh.sh",
            "scripts/graphify_prepare_corpus.sh",
            "scripts/graphify_full_refresh.py",
            "scripts/graphify_semantic_adapter.py",
            "scripts/graphify_verify_full_refresh.py",
            "scripts/graphify_sync_staged.sh",
            "scripts/graphify_ci_candidate.sh",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    changed_paths = [line[3:] for line in result.stdout.splitlines() if len(line) >= 4]
    has_full_refresh_changes = any(
        path.startswith("raw/")
        or path
        in {
            "scripts/graphify_prepare_corpus.sh",
            "scripts/graphify_full_refresh.py",
            "scripts/graphify_semantic_adapter.py",
            "scripts/graphify_verify_full_refresh.py",
            "scripts/graphify_sync_staged.sh",
            "scripts/graphify_ci_candidate.sh",
        }
        for path in changed_paths
    )
    has_code_changes = any(
        path.startswith("src/")
        or path.startswith("tests/")
        or path == "scripts/graphify_code_refresh.sh"
        for path in changed_paths
    )
    return has_code_changes, has_full_refresh_changes


code_inputs = _digest([ROOT / "src", ROOT / "tests"])
full_inputs = _digest(
    [
        ROOT / "raw",
        ROOT / "scripts" / "graphify_full_refresh.py",
        ROOT / "scripts" / "graphify_semantic_adapter.py",
        ROOT / "scripts" / "graphify_verify_full_refresh.py",
    ]
)

state = _load_state()
if state.get("schema_version") != "raw-source-v1":
    state = {}
last_code_inputs = state.get("code_inputs")
last_full_inputs = state.get("full_inputs")

if not state and BUILD_INFO_FILE.exists():
    existing_build_info = json.loads(BUILD_INFO_FILE.read_text(encoding="utf-8"))
    existing_mode = existing_build_info.get("mode")
    has_code_changes, has_full_refresh_changes = _detect_bootstrap_changes()
    bootstrap_code_inputs = code_inputs
    bootstrap_full_inputs = full_inputs
    if has_full_refresh_changes:
        bootstrap_full_inputs = ""
    elif has_code_changes or existing_mode != "full_refresh":
        bootstrap_code_inputs = ""
    _write_state({"code_inputs": bootstrap_code_inputs, "full_inputs": bootstrap_full_inputs})
    last_code_inputs = bootstrap_code_inputs
    last_full_inputs = bootstrap_full_inputs
    print("graphify auto-refresh: initialized state from existing graph")

if last_full_inputs != full_inputs:
    ok = _run(["bash", "scripts/graphify_prepare_corpus.sh"], label="prepare corpus")
    ok = ok and _run(
        [
            "uv",
            "run",
            "--with",
            "graphifyy==0.4.23",
            "python",
            "scripts/graphify_full_refresh.py",
            ".graphify-work/corpus",
        ],
        label="full refresh producer",
    )
    ok = ok and _run(
        [
            "python3",
            "scripts/graphify_verify_full_refresh.py",
            ".graphify-work/corpus/graphify-out",
        ],
        label="verify full refresh",
    )
    ok = ok and _run(["bash", "scripts/graphify_sync_staged.sh"], label="sync full refresh")
    if ok:
        _write_state({"code_inputs": code_inputs, "full_inputs": full_inputs})
    raise SystemExit(0)

if last_code_inputs != code_inputs:
    ok = _run(["bash", "scripts/graphify_code_refresh.sh"], label="code refresh")
    if ok:
        _write_state({"code_inputs": code_inputs, "full_inputs": full_inputs})
    raise SystemExit(0)

print("graphify auto-refresh: inputs unchanged")
PY
