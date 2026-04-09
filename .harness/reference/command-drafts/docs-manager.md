---
description: Manage this repository's 3-layer knowledge base and docs/harness sync routine using AGENTS.md and the docs-manager skill. Use for ingest, query, lint, ADR creation, wiki page updates, cross-reference fixes, wiki backups, and syncing README/harness files after workflow changes.
---

# Docs Manager

Run the repository-local docs workflow for `docs/sources/`, `docs/wiki/`, `README.md`, `AGENTS.md`, `.github/copilot-instructions.md`, and `.harness/reference/local-adaptation.md`.

## Preflight

1. Read `AGENTS.md` first. Treat it as the authoritative wiki schema for this repository.
2. Read `.agents/skills/docs-manager/SKILL.md` and follow its operation-specific workflow.
3. Inspect `docs/wiki/INDEX.md` before changing wiki pages.
4. If the request references source material, confirm the target file exists under `docs/sources/`.
5. If the request is a write operation, identify the affected wiki category and its `README.md`.
6. If the request follows code or CLI changes, inspect whether README/harness sync is also required.

Stop and report the exact blocker if a required file or source path is missing.

## Plan

Choose the operation mode from the user's command arguments:

- `ingest` for adding a new source into the wiki
- `query` for answering from the wiki with citations
- `lint` for consistency checks and repair suggestions
- `backup` for archiving `docs/wiki/`
- `update` for direct wiki edits, ADR creation, or cross-reference maintenance
- `sync` for repository-wide docs and harness reflection after implementation changes

Before editing, state:

1. Which operation mode is being used
2. Which wiki pages will be read or modified
3. Whether `INDEX.md` and a category `README.md` must be updated in the same pass

## Commands

Follow the `docs-manager` skill exactly.

### `ingest`

1. Read the requested source file from `docs/sources/<category>/`.
2. Create or update the required wiki pages using the templates in `AGENTS.md`.
3. Update `docs/wiki/INDEX.md` and the affected category `README.md` together.
4. Add or repair bidirectional links in each page's `## Related`.
5. Create `docs/wiki/logs/ingest-YYYY-MM-DD-<slug>.md`.

### `query`

1. Read `docs/wiki/INDEX.md` to find the relevant pages.
2. Read only the necessary wiki pages.
3. Answer in Korean and cite wiki pages with relative markdown links.
4. If the answer should be preserved, ask whether to save it as a wiki page.

### `lint`

Check at minimum:

- missing or invalid YAML frontmatter
- `INDEX.md` drift versus actual wiki pages
- category `README.md` drift
- missing bidirectional `## Related` links
- orphan pages
- missing concept/entity pages implied by repeated references

Report findings by severity: `HIGH`, `MEDIUM`, `LOW`.

### `backup`

Create a timestamped archive:

```bash
tar czf docs/wiki-backup-YYYY-MM-DD.tar.gz docs/wiki/
```

After backup, report the archive path and what was included.

### `update`

Use this mode for page edits that are not tied to a new source ingest:

- add or revise an entity page
- add or revise an ADR
- repair cross-references
- sync `INDEX.md` and category `README.md`
- normalize page structure to the `AGENTS.md` schema

### `sync`

Use this mode when implementation changes should automatically propagate into docs and harness files:

1. Read the relevant code diff and CLI/workflow surfaces.
2. Update `README.md` where user-facing setup, validation, or workflow changed.
3. Update `AGENTS.md`, `.github/copilot-instructions.md`, and `.harness/reference/local-adaptation.md` if rules, commands, or default workflow changed.
4. If the change introduces or reshapes a concept, entity, or decision, update `docs/wiki/` and sync `INDEX.md` plus category `README.md`.
5. Verify that README, harness files, and wiki all describe the same current workflow.

## Verification

After the operation, confirm:

- every modified wiki page still has valid YAML frontmatter
- `docs/wiki/INDEX.md` matches the actual wiki pages
- affected category `README.md` files are synced
- all new or touched `## Related` links are bidirectional
- documents remain written in Korean
- source paths in frontmatter are valid when present
- `README.md`, `AGENTS.md`, `.github/copilot-instructions.md`, and `.harness/reference/local-adaptation.md` are aligned with the implementation

## Summary

Return a concise result in this format:

```md
## Docs Manager Result
 - **Operation**: ingest | query | lint | backup | update | sync
- **Status**: success | partial | failed
- **Pages**: created/updated/checked pages
- **Index Sync**: updated | not-needed | failed
- **Notes**: key findings or follow-up risks
```

## Next Steps

- If lint finds issues, propose the smallest safe repair set first.
- If ingest creates new knowledge, suggest adjacent pages that should also be updated.
- If query produces reusable synthesis, offer to save it as an overview or comparison page.
- If backup succeeds, mention the archive path for later restore use.
