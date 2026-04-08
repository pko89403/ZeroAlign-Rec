---
description: Run the pre-launch checklist and prepare for production deployment
---

Invoke the repository-local `shipping-and-launch` skill.
Read `.harness/reference/local-adaptation.md` before running repository-specific checks.

Run through the complete pre-launch checklist:

1. **Code Quality** — `uv run pytest`, `uv run ruff check .`, `uv run mypy src` pass
2. **Environment** — `.env` expectations are documented and `uv run sid-reco doctor` passes
3. **Runtime Path** — relevant `uv run sid-reco ...` CLI commands or smoke paths succeed
4. **Security** — no secrets committed, cache/output paths stay outside git, model downloads are documented
5. **Artifacts** — generated data or reports are either reproducible or intentionally excluded from git
6. **Documentation** — README current, wiki/ADR updates made when architecture or workflow changed

Report any failing checks and help resolve them before deployment.
Define the rollback plan before proceeding.
