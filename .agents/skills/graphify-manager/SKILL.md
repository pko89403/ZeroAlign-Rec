---
name: graphify-manager
description: "Run the repository's full Graphify refresh workflow against the staged corpus, verify that design/docs context made it into the graph, and optionally sync verified results into root graphify-out/."
argument-hint: "full refresh, verify only, or sync verified results"
---

# Graphify Manager

Run the repository's **full Graphify refresh automation**.
This is separate from `scripts/graphify_code_refresh.sh`, which is code-only bootstrap.
Hooks may now auto-refresh the graph after relevant local edits.
Use this workflow when you want to run or inspect the full staged producer path explicitly.

## When to Use

- You need a full graph that includes code **and** docs/design context
- You want to reflect the current `raw/` source corpus into `graphify-out/`
- You want to refresh `.graphify-work/corpus/graphify-out/` and promote it into root `graphify-out/`

## Workflow

### 1. Prepare staged corpus

Always start by preparing the deterministic staged corpus:

```bash
bash scripts/graphify_prepare_corpus.sh
```

This creates `.graphify-work/corpus/` with:

- `src/`
- `tests/`
- `raw/`

### 2. Run Graphify full pipeline on staged corpus

Run the repo-local full refresh producer on `.graphify-work/corpus/`.
The high-level order is fixed:

1. detect
2. AST extraction
3. semantic extraction
4. graph build / cluster / analysis
5. report / json / html export
6. verify gate
7. optional sync

```bash
uv run --with graphifyy==0.4.23 python scripts/graphify_full_refresh.py .graphify-work/corpus
```

If the producer fails, stop there and report the exact failure.
Do not claim success or run root sync in that case.

### 3. Required semantic targets

The full refresh is only useful if semantic extraction includes document context.
At minimum, make sure the staged corpus graph captures nodes/relationships sourced from:

- `raw/design/adr/**`
- `raw/design/notes/**`
- `raw/design/specs/**` when present
- `raw/external/**` as source-file presence

### 4. Verify staged output

After Graphify writes `.graphify-work/corpus/graphify-out/`, run:

```bash
python3 scripts/graphify_verify_full_refresh.py .graphify-work/corpus/graphify-out
```

This must succeed before root sync.
If `.graphify-work/corpus/graphify-out/BUILD_INFO.json` does not exist yet,
report that no staged full refresh output was produced and stop there.
Verification now requires more than source file presence:

- required `raw/design/adr/**` and `raw/design/notes/**` files must exist as graph nodes
- required raw design files must participate in non-trivial semantic links
- `raw/design/specs/**` participates when present
- `raw/external/**` and binary-like design assets must appear as source-file presence
- semantic links must carry relation + confidence metadata

### 5. Sync verified result (optional)

Only after verification passes:

```bash
bash scripts/graphify_sync_staged.sh
```

This copies the verified staged artifacts into root `graphify-out/`.

## Rules

- CI may prepare a candidate note, but it does not run the producer, verify, or sync.
- Hooks may auto-refresh after relevant local edits, so check `graphify-out/BUILD_INFO.json` before assuming the current graph state.
- Do not overwrite root `graphify-out/` before the verify gate passes.
- `raw/` is the only source corpus for full refresh.
- Keep Graphify version pinned through the repository scripts and metadata.
- If full refresh fails verification, report which required documentation sources were missing from the graph.

## Related

- `scripts/graphify_code_refresh.sh`
- `scripts/graphify_prepare_corpus.sh`
- `scripts/graphify_full_refresh.py`
- `scripts/graphify_verify_full_refresh.py`
- `scripts/graphify_sync_staged.sh`
