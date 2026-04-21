---
description: Manage this repository's 3-layer knowledge base and docs/harness sync routine using AGENTS.md and the docs-manager skill. Use for `raw/` source corpus maintenance, Graphify artifact review, ADR updates, and syncing README/harness files after workflow changes.
---

# Docs Manager

Run the repository-local docs workflow for `raw/`, `graphify-out/`, `README.md`, `AGENTS.md`, `.github/copilot-instructions.md`, and `.harness/reference/local-adaptation.md`.

## Preflight

1. Read `AGENTS.md` first. Treat it as the authoritative Graphify/source-corpus schema for this repository.
2. Read `.agents/skills/docs-manager/SKILL.md` and follow its operation-specific workflow.
3. Inspect `raw/` and `graphify-out/BUILD_INFO.json` before changing the source corpus or Graphify-facing docs.
4. If the request references source material, confirm the target file exists under `raw/design/` or `raw/external/`.
5. If the request is a write operation, identify whether it changes source corpus, Graphify verification policy, or docs/harness sync.
6. If the request follows code or CLI changes, inspect whether README/harness sync is also required.

Stop and report the exact blocker if a required file or source path is missing.

## Plan

Choose the operation mode from the user's command arguments:

- `ingest` for adding or normalizing source material under `raw/`
- `query` for answering from Graphify plus `raw/` source files with citations
- `lint` for consistency checks and repair suggestions across `raw/`, `graphify-out/`, and harness docs
- `backup` for archiving `raw/` before large restructures
- `update` for direct source-corpus edits, ADR creation, or Graphify/harness alignment
- `sync` for repository-wide docs and harness reflection after implementation changes

Before editing, state:

1. Which operation mode is being used
2. Which `raw/`, `graphify-out/`, or harness files will be read or modified
3. Whether Graphify artifacts or repository docs must be refreshed in the same pass

## Commands

Follow the `docs-manager` skill exactly.

### `ingest`

1. Read the requested source file or note target under `raw/design/<category>/` or `raw/external/<category>/`.
2. Create or update the required source documents using the conventions in `AGENTS.md`.
3. If the source corpus changed, refresh Graphify or note that a refresh is required.
4. Sync any affected README/harness files in the same pass.

### `query`

1. Read `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json` first.
2. Read only the necessary `raw/` source documents for confirmation.
3. Answer in Korean and cite the relevant source docs or Graphify artifact paths.
4. If the answer should be preserved, ask whether to save it into `raw/design/notes/` or `raw/design/adr/`.

### `lint`

Check at minimum:

- stale or contradictory `raw/design/**` content
- `graphify-out/BUILD_INFO.json` trust state versus the current source corpus
- README / AGENTS / harness doc drift
- missing ADR or design-note updates implied by implementation changes
- stale references to removed wiki/docs-sources paths

Report findings by severity: `HIGH`, `MEDIUM`, `LOW`.

### `backup`

Create a timestamped archive:

```bash
tar czf raw-backup-YYYY-MM-DD.tar.gz raw/
```

After backup, report the archive path and what was included.

### `update`

Use this mode for source-corpus or harness edits that are not tied to a fresh ingest:

- add or revise a design note
- add or revise an ADR
- repair Graphify-facing source coverage gaps
- sync README / AGENTS / harness docs
- normalize source-corpus structure to the `AGENTS.md` schema

### `sync`

Use this mode when implementation changes should automatically propagate into docs and harness files:

1. Read the relevant code diff and CLI/workflow surfaces.
2. Update `README.md` where user-facing setup, validation, or workflow changed.
3. Update `AGENTS.md`, `.github/copilot-instructions.md`, and `.harness/reference/local-adaptation.md` if rules, commands, or default workflow changed.
4. If the change introduces or reshapes a concept, design note, or decision, update `raw/design/` and refresh Graphify expectations.
5. Verify that README, harness files, `raw/`, and Graphify all describe the same current workflow.

## Verification

After the operation, confirm:

- modified `raw/design/**` documents remain in Korean
- `raw/` structure still matches `AGENTS.md`
- Graphify expectations are updated when source-corpus changes require them
- no removed `docs/wiki` / `docs/sources` paths were reintroduced
- `README.md`, `AGENTS.md`, `.github/copilot-instructions.md`, and `.harness/reference/local-adaptation.md` are aligned with the implementation

## Summary

Return a concise result in this format:

```md
## Docs Manager Result
- **Operation**: ingest | query | lint | backup | update | sync
- **Status**: success | partial | failed
- **Artifacts**: updated `raw/`, `graphify-out/`, or harness files
- **Graphify Sync**: updated | not-needed | pending
- **Notes**: key findings or follow-up risks
```

## Next Steps

- If lint finds issues, propose the smallest safe repair set first.
- If ingest creates new knowledge, suggest adjacent `raw/design/` documents that should also be updated.
- If query produces reusable synthesis, offer to save it as a design note or ADR.
- If backup succeeds, mention the archive path for later restore use.
