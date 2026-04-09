<p align="center">
  <img src="artifacts/branding/zeroalign-rec-logo.svg" alt="ZeroAlign-Rec logo" width="760">
</p>

<h1 align="center">ZeroAlign-Rec</h1>

<p align="center"><strong>Training-free semantic recommendation with SID, local MLX inference, and taxonomy-aware item alignment.</strong></p>

<p align="center"><strong>English</strong> | <a href="./README.ko.md">한국어</a></p>

`ZeroAlign-Rec` is a Python codebase for experimenting with `SID`-based training-free recommendation in a local environment. It uses `MLX` on Apple Silicon to run both generative and embedding models locally, and supports an end-to-end workflow from Food.com preprocessing to taxonomy dictionary generation and taxonomy-aligned item structuring.

Current Phase 1 progress also includes an in-repository `sid` package plus a public `compile-sid-index` CLI for deterministic structured-item serialization, MLX embedding artifacts, CPU residual K-means codebook training, and FAISS indexing outputs under `data/processed/foodcom/sid_index/`.

## Table of Contents

- [Why ZeroAlign-Rec](#why-zeroalign-rec)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Workflows](#core-workflows)
- [Configuration](#configuration)
- [Validation](#validation)
- [Repository Layout](#repository-layout)
- [Docs and Knowledge Base](#docs-and-knowledge-base)
- [Research References](#research-references)
- [Copilot and Agent Harness](#copilot-and-agent-harness)

## Why ZeroAlign-Rec

- **Training-free recommendation experiments**: validate SID-based recommendation flows without separate model training.
- **Local-first inference**: run `mlx-lm` and `mlx-embeddings` locally on Apple Silicon.
- **Taxonomy-aware pipeline**: separate dataset preparation, neighbor index construction, taxonomy dictionary generation, and item structuring into reproducible steps.
- **Agent-friendly repository**: keep `.github/`, `.agents/skills/`, `.harness/`, and `AGENTS.md` organized for Copilot/Codex workflows.

## Requirements

- `macOS` on Apple Silicon
- Python `3.12`
- [`uv`](https://docs.astral.sh/uv/)
- A local interactive terminal session is recommended

Default local models:

- Generative LLM: `mlx-community/Qwen3.5-9B-OptiQ-4bit`
- Embedding model: `mlx-community/Qwen3-Embedding-4B-4bit-DWQ`

Important environment notes:

- **Recommended**: a logged-in local macOS Apple Silicon session
- **Best-effort only**: SSH, CI, sandboxed, or headless sessions
- For MLX/Metal diagnostics, start with `uv run sid-reco smoke-mlx`

## Installation

```bash
uv sync --all-groups
source .venv/bin/activate
cp .env.example .env
git config core.hooksPath .githooks
```

Fill in only the values you need in `.env`. See [Configuration](#configuration) for the main variables.
The repository-managed hooks then apply `ruff check --fix` and `ruff format` before commit, and run the automated `ruff` + `mypy` + `pytest` gate before push.

## Quick Start

The fastest smoke path is:

```bash
uv run sid-reco doctor
uv run sid-reco smoke-mlx
uv run sid-reco smoke-llm "Summarize a user's preferences"
uv run sid-reco smoke-embed "crime thriller recommendations"
```

For an end-to-end experiment, continue with:

```bash
uv run sid-reco prepare-foodcom --raw-dir data/raw/foodcom --out-dir data/processed/foodcom
uv run sid-reco build-neighbor-context
uv run sid-reco build-taxonomy-dictionary
uv run sid-reco structure-taxonomy-batch \
  --recipes-path data/processed/foodcom/recipes.csv \
  --neighbor-context-path data/processed/foodcom/neighbor_context/neighbor_context.csv \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json \
  --out-path data/processed/foodcom/taxonomy_structured/items.jsonl
uv run sid-reco compile-sid-index \
  --structured-items-path data/processed/foodcom/taxonomy_structured/items.jsonl \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json \
  --out-dir data/processed/foodcom/sid_index
```

## Core Workflows

### 1. Prepare the Food.com dataset

Convert the raw CSV files into a compact experiment-ready catalog and split set.

```bash
uv run sid-reco prepare-foodcom \
  --raw-dir data/raw/foodcom \
  --out-dir data/processed/foodcom \
  --top-recipes 3000 \
  --core-k 5 \
  --positive-threshold 4
```

Main outputs:

- `data/processed/foodcom/recipes.csv`
- `data/processed/foodcom/interactions.csv`
- `data/processed/foodcom/splits/{train,valid,test}.csv`
- `data/processed/foodcom/manifest.json`

### 2. Build the neighbor context

Generate item metadata embeddings and FAISS-based top-k neighbor context.

```bash
uv run sid-reco build-neighbor-context \
  --recipes-path data/processed/foodcom/recipes.csv \
  --out-dir data/processed/foodcom/neighbor_context \
  --top-k 5
```

Main outputs:

- `items_with_embeddings.csv`
- `neighbor_context.csv`
- `item_index.faiss`
- `manifest.json`

### 3. Generate the taxonomy dictionary

Use a local LLM to generate a domain taxonomy dictionary.
This stage is inspired by the one-time taxonomy categorization idea in
[Taxonomy-Guided Zero-Shot Recommendations with LLMs](https://aclanthology.org/2025.coling-main.102/)
(Liang et al., COLING 2025) and the accompanying
[TaxRec repository](https://github.com/yueqingliang1/TaxRec).
This repository adapts the taxonomy dictionary construction idea only; it does not implement the
full TaxRec recommendation and evaluation pipeline.

```bash
uv run sid-reco build-taxonomy-dictionary \
  --recipes-path data/processed/foodcom/recipes.csv \
  --out-dir data/processed/foodcom/taxonomy_dictionary \
  --max-tokens 4096
```

Main outputs:

- `food_taxonomy_dictionary.json`
- `prompt_snapshot.json`

### 4. Structure items into taxonomy-aligned JSON

Use the taxonomy dictionary together with neighbor context to produce structured outputs for each item. The item structuring stage now applies:

This stage is inspired by the Context-aware Term Generation idea in
[Unleashing the Native Recommendation Potential: LLM-Based Generative Recommendation via Structured Term Identifiers](https://arxiv.org/abs/2601.06798)
and the accompanying [GRLM repository](https://github.com/ZY0025/GRLM), specifically the use of
similar-item neighborhoods as contextual guidance for LLM-based item structuring.
This repository reuses the top-5 neighbor prompting idea only; it does not implement the full GRLM
Term ID generation, instruction fine-tuning, or grounding pipeline.

- prompt-level duplicate/synonym suppression
- a self-refine rewrite pass on draft JSON when labels drift outside the master vocabulary
- conservative post-processing canonicalization toward the taxonomy dictionary
- lightweight validators for obviously weak `cuisine` and contradictory `dietary_style` labels

Single item:

```bash
uv run sid-reco structure-taxonomy-item \
  --recipe-id 101 \
  --recipes-path data/processed/foodcom/recipes.csv \
  --neighbor-context-path data/processed/foodcom/neighbor_context/neighbor_context.csv \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json
```

Batch:

```bash
uv run sid-reco structure-taxonomy-batch \
  --recipes-path data/processed/foodcom/recipes.csv \
  --neighbor-context-path data/processed/foodcom/neighbor_context/neighbor_context.csv \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json \
  --out-path data/processed/foodcom/taxonomy_structured/items.jsonl
```

### 5. Compile hierarchical SID and FAISS index

Compile structured items into deterministic serialized text, dense embeddings, hierarchical SID paths, and a FAISS index.

```bash
uv run sid-reco compile-sid-index \
  --structured-items-path data/processed/foodcom/taxonomy_structured/items.jsonl \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json \
  --out-dir data/processed/foodcom/sid_index
```

Main outputs:

- `serialized_items.jsonl`
- `embeddings.npy`
- `embedding_manifest.json`
- `compiled_sid.jsonl`
- `item_to_sid.json`
- `sid_to_items.json`
- `id_map.jsonl`
- `item_index.faiss`
- `manifest.json`

## Configuration

Create `.env` from `.env.example` and adjust only the variables you need.

| Variable | Description |
| --- | --- |
| `SID_RECO_LLM_BACKEND` | currently `mlx` |
| `SID_RECO_LLM_MODEL` | generative LLM model name |
| `SID_RECO_EMBED_MODEL` | embedding model name |
| `SID_RECO_CATALOG_PATH` | path to the item metadata catalog |
| `SID_RECO_CACHE_DIR` | path for intermediate artifacts and cache |
| `SID_RECO_LLM_MAX_TOKENS` | default generation token count |
| `SID_RECO_LLM_TEMPERATURE` | default temperature |
| `SID_RECO_LLM_TOP_P` | default nucleus sampling value |

## Automated Quality Gate

```bash
uv run ruff format --check .
uv run pytest --ignore=tests/test_mlx_runtime.py --ignore=tests/test_cli_smoke_mlx.py
uv run ruff check .
uv run mypy src
```

The automated gate intentionally excludes MLX runtime validation tests.

## Local Manual MLX Checks

Run these only in a local Apple Silicon session when you want to confirm MLX/Metal behavior:

```bash
uv run sid-reco doctor
uv run sid-reco smoke-mlx
uv run sid-reco build-neighbor-context --help
uv run sid-reco build-taxonomy-dictionary --help
uv run sid-reco structure-taxonomy-item --help
uv run sid-reco structure-taxonomy-batch --help
```

## Repository Layout

| Path | Role |
| --- | --- |
| `src/sid_reco/` | application package |
| `src/sid_reco/sid/` | Phase 1 SID serialization and embedding artifact helpers |
| `tests/` | automated tests |
| `data/` | local datasets and processed artifacts |
| `artifacts/` | generated reports, branding, and outputs |
| `docs/` | user-facing knowledge base and wiki |
| `.github/` | Copilot-facing instructions and agent personas |
| `.agents/skills/` | repo-local agent skills |
| `.harness/` | internal harness support and reference assets |
| `AGENTS.md` | top-level repository rules and schema |

## Docs and Knowledge Base

Instead of duplicating long operational details in the README, this repository keeps deeper material in `docs/` and the wiki.

- [docs/README.md](docs/README.md)
- [docs/wiki/entities/dev-environment.md](docs/wiki/entities/dev-environment.md)
- [docs/wiki/entities/food-com-dataset.md](docs/wiki/entities/food-com-dataset.md)
- [docs/wiki/entities/food-taxonomy-dictionary.md](docs/wiki/entities/food-taxonomy-dictionary.md)
- [docs/wiki/entities/taxonomy-item-structuring.md](docs/wiki/entities/taxonomy-item-structuring.md)
- [docs/wiki/entities/neighbor-context-index.md](docs/wiki/entities/neighbor-context-index.md)
- [docs/wiki/entities/sid-compilation-indexing.md](docs/wiki/entities/sid-compilation-indexing.md)
- [docs/wiki/overviews/sid-phase1-validation-run.md](docs/wiki/overviews/sid-phase1-validation-run.md)
- [docs/wiki/decisions/adr-001-dev-environment.md](docs/wiki/decisions/adr-001-dev-environment.md)
- [docs/wiki/decisions/adr-002-foodcom-preprocessing-policy.md](docs/wiki/decisions/adr-002-foodcom-preprocessing-policy.md)
- [docs/wiki/decisions/adr-003-neighbor-context-retrieval.md](docs/wiki/decisions/adr-003-neighbor-context-retrieval.md)
- [docs/wiki/decisions/adr-004-taxonomy-dictionary-generation.md](docs/wiki/decisions/adr-004-taxonomy-dictionary-generation.md)
- [docs/wiki/decisions/adr-005-taxonomy-dictionary-hardening.md](docs/wiki/decisions/adr-005-taxonomy-dictionary-hardening.md)
- [docs/wiki/decisions/adr-006-strict-tid-hardening.md](docs/wiki/decisions/adr-006-strict-tid-hardening.md)
- [artifacts/reports/sid-phase1-validation.html](artifacts/reports/sid-phase1-validation.html)

## Research References

Some subcomponents in this repository explicitly adapt ideas from prior work. When discussing or
building on those specific ideas, please cite the original paper rather than this repository alone.

### GRLM

The `Taxonomy Item Structuring` stage reuses only the neighborhood-guided prompting idea from
[Unleashing the Native Recommendation Potential: LLM-Based Generative Recommendation via Structured Term Identifiers](https://arxiv.org/abs/2601.06798)
and the accompanying [GRLM repository](https://github.com/ZY0025/GRLM).
This repository does **not** implement the full GRLM training, grounding, or recommendation pipeline.

```bibtex
@article{zhang2026unleashing,
  title={Unleashing the Native Recommendation Potential: LLM-Based Generative Recommendation via Structured Term Identifiers},
  author={Zhang, Zhiyang and She, Junda and Cai, Kuo and Chen, Bo and Wang, Shiyao and Luo, Xinchen and Luo, Qiang and Tang, Ruiming and Li, Han and Gai, Kun and others},
  journal={arXiv preprint arXiv:2601.06798},
  year={2026}
}
```

## Copilot and Agent Harness

This repository also maintains a Copilot/Codex-friendly harness.

- Copilot project instructions: `.github/copilot-instructions.md`
- specialized personas: `.github/agents/`
- repo-local skills: `.agents/skills/`
- harness support assets: `.harness/`
- local adaptation rules: `.harness/reference/local-adaptation.md`

Main shortcuts:

- `/docs-manager` or `/doc-manager` — wiki/ADR/index plus README and harness sync
- `/spec`
- `/plan`
- `/build`
- `/test`
- `/code-simplify`
- `/ship`

For taxonomy work, the default repository pipeline is:

```bash
build-neighbor-context -> build-taxonomy-dictionary -> structure-taxonomy-item|batch
```

For docs/wiki work, `docs-manager` and `AGENTS.md` rules take priority over generic workflows.
