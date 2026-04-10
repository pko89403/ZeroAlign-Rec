# Spec: Phase 2 - Modular 100% Training-Free LLM Recommendation Engine

## Assumptions I'm Making

1. This feature starts **after Phase 1** and depends on `data/processed/foodcom/sid_index/` produced by `compile-sid-index`.
2. The recommendation engine must remain **100% training-free**:
   - no collaborative filtering
   - no supervised ranker
   - no fine-tuning
   - no gradient updates
3. The online system may use only:
   - pre-trained LLM capabilities already supported by this repository
   - Phase 1 FAISS and sidecar artifacts
   - deterministic runtime filters and mapping logic
4. The initial external contract must include **both**:
   - a Python library API
   - a CLI command
5. The Phase 2 design should be explicit at the module level rather than described as one opaque end-to-end pipeline.
6. The user wants the feature organized as four modules:
   - **Module 2.1: proactive control and user-interest sketch**
   - **Module 2.2: pure semantic search and hard filtering**
   - **Module 2.3: explainable zero-shot reranking**
   - **Module 2.4: confidence verification and elastic mapping**
7. The recommendation response must return ranked items plus structured explanation fields and downstream-inspectable rationale.
8. Hallucination policy, position-bias policy, and persistent trace artifacts are still open questions and should remain visible in the spec.
9. Offline benchmarking/report generation is mostly out of scope for V1.

## Objective

Build the first usable online recommendation engine for this repository so that user intent can be converted into ranked recommendations **without any recommendation-model training**.

This feature should turn the existing Phase 1 offline artifact layer into a runtime engine that:

1. interprets sparse or messy user intent
2. turns that intent into a structured interest sketch
3. retrieves candidates through pure semantic search over the Phase 1 vector substrate
4. applies deterministic hard filters
5. re-ranks the surviving candidates with LLM reasoning
6. returns structured recommendation results with explanation and confidence signals

The product goal is not just "search plus LLM output." It is a **modular training-free recommender** whose decision points remain inspectable.

### User-facing intent

Given:

- a Phase 1 `sid_index/` directory
- catalog metadata such as `recipes.csv`
- a user request expressed as free text, item likes/dislikes, and optional hard constraints

the maintainer should be able to run one command or call one API and obtain:

- ranked recommendations from the existing catalog
- structured explanation fields per item
- a rationale for the final order
- a confidence-oriented signal indicating whether the result set is strong, weak, or semantically stretched

## Non-Goals

This spec does **not** include:

- collaborative filtering or matrix factorization
- training a learned retriever or learned reranker
- instruction tuning, preference tuning, or RLHF
- offline leaderboard/report generation as a V1 requirement
- generating new items outside the indexed catalog
- mutating Phase 1 artifacts during online recommendation

## Phase 2 Module Breakdown

### Module 2.1: Proactive Control and Taxonomy-Guided User-Interest Sketch

This module converts raw user input into a structured and controllable request representation **using the Phase 1 taxonomy master dictionary as the mandatory vocabulary boundary**.

#### Responsibilities

- load the Phase 1 taxonomy master dictionary and inject it into the LLM prompt
- normalize incoming request fields
- infer the user's likely interests from sparse language and/or item history
- separate:
  - positive preferences
  - negative preferences
  - must-have constraints
  - avoid constraints
  - uncertainty or ambiguity markers
- compress the user's semantic themes **only within the allowed taxonomy facets and values**
- produce a machine-readable **interest sketch** for downstream retrieval

#### Why it exists

The user may provide incomplete, contradictory, or vague intent. The system should not pass raw text directly into retrieval without first extracting a stable representation. By forcing the sketch into the Phase 1 taxonomy vocabulary, the engine keeps the query space aligned with the item-feature space already indexed in FAISS.

#### Minimum outputs

- normalized query summary
- extracted taxonomy-constrained preference facets
- hard filters
- taxonomy-guided semantic anchors for retrieval
- ambiguity notes for later confidence handling
- a record of which taxonomy facets and values were selected

#### Required sketching contract

- the Phase 1 taxonomy master dictionary must be available at runtime
- Module 2.1 must not emit free-form retrieval vocabulary outside the approved taxonomy for the interest sketch
- historical preference signals must be compressed into taxonomy-constrained facets before semantic retrieval
- this module is the primary guardrail against query-generation hallucination at the retrieval stage

### Module 2.2: Pure Semantic Search and Hard Filtering

This module compresses the first candidate set quickly and accurately by combining:

- taxonomy-aligned dense query embedding
- FAISS-based vector retrieval
- CPU-driven hard filtering
- training-free popularity and co-occurrence lookups

Its purpose is to produce a strong, over-sampled candidate pool for Module 2.3 without introducing any learned CF model.

#### Responsibilities

- load Phase 1 FAISS and sidecar artifacts
- encode the Module 2.1 taxonomy-guided query with the local MLX embedding model
- execute semantic retrieval over the indexed item representations
- apply hard filters after retrieval or during candidate pruning
- fetch offline popularity and co-occurrence statistics for surviving candidates
- never use collaborative or learned user-item scoring
- produce a stable candidate set for reranking

#### Required retrieval contract

- retrieval source must be the existing Phase 1 vector corpus
- retrieval signal must be semantic, not CF-derived
- the query vector must come from the taxonomy-guided sketch rather than raw unconstrained text
- initial retrieval must be cosine-similarity search over `item_index.faiss`
- hard filters must be explicit, deterministic, and CPU-enforced
- popularity and co-occurrence may be added only as offline statistics, not as a trained CF model
- candidate identifiers must remain traceable to the catalog and Phase 1 sidecars

#### Minimum outputs

- ordered candidate pool
- candidate metadata bundle
- filter-application summary
- dropped-candidate reasons when filters remove items
- per-candidate popularity and co-occurrence metadata for Module 2.3

#### 2.2.1 Taxonomy-Aligned Vector Search

- convert the Module 2.1 taxonomy-guided query into a dense vector using the local MLX embedding model
- search `item_index.faiss` with cosine similarity
- retrieve an intentionally over-sampled candidate pool, with **Top-100** as the default design target
- because query and items share the same taxonomy vocabulary, semantic alignment should be maximized at retrieval time

#### 2.2.2 CPU-Driven Over-Sampled Hard Filtering

- apply explicit user constraints after the Top-100 retrieval pass
- perform filtering in the application layer on CPU
- prune items that violate the user's stated hard conditions
- use the over-sampled pool to prevent filter exhaustion
- forward the strongest surviving **Top-30** candidates by default to Module 2.3
- if fewer than 30 survive, forward all survivors together with a low-coverage signal

#### 2.2.3 Training-Free Pseudo-CF Signal Integration

- look up precomputed offline statistics for each surviving candidate
- include at least:
  - item popularity
  - co-occurrence counts with the user's liked-history items
- do not use these signals as a learned score in Module 2.2
- instead, attach them as structured JSON metadata so Module 2.3 can reason over semantic fit and weak collaborative evidence together

### Module 2.3: Resource-Optimized Explainable Zero-Shot Re-ranking

This module uses the local LLM as an **explainable zero-shot reranker** while minimizing VRAM/KV-cache pressure, reducing decoding latency, and blocking OOD recommendation outputs.

#### Responsibilities

- compare retrieved candidates against the user-interest sketch
- inject only one dynamically retrieved successful recommendation example at runtime
- determine final ranking order with schema-constrained outputs
- keep rationale generation short and cheap to decode
- return candidate indices rather than generated item names
- expose why one item outranks another
- support repeated order-perturbed evaluations for position-bias mitigation

#### Required reranking contract

- reranking must operate on retrieved candidates only
- rationale must be returned in structured form
- output schema must remain parseable and testable
- ranking and explanation generation should be one coherent reasoning step, not two unrelated passes
- the model must not generate free-form catalog item names in the final selection output
- final ranking output must be candidate-index based so the CPU application layer can ground it back to canonical item metadata

#### Minimum outputs

- ranked candidate indices
- short per-item rationale
- matched-preference fields
- caveat/tradeoff fields
- rerank summary
- bootstrap-vote or agreement metadata for downstream confidence handling

#### 2.3.1 Context-Efficient Dynamic Few-Shot

- do not rely on a large static prompt stuffed with many examples
- at runtime, retrieve exactly **one** past successful recommendation example most similar to the current interest sketch
- inject only that one example into the prompt
- the retrieved example should contain:
  - prior interest sketch
  - compact recommendation rationale pattern
  - target output format example
- this keeps the prompt small while preserving domain adaptation

#### 2.3.2 Latency-Optimized Structured Outputs

- use strict structured generation such as JSON Schema, XGrammar, Outlines, or an equivalent constrained-decoding mechanism
- force rationale length to **1-2 short sentences**
- do not allow the model to generate raw item titles as the final ranking output
- require the model to emit only candidate index identifiers, such as `[3, 7, 1, ...]`, for final ordering
- this minimizes decoding cost and prevents OOD recommendation outputs

#### 2.3.3 Prefix-Cache Friendly Bootstrapping

- preserve the system prompt and user-interest sketch as a reusable prompt prefix
- vary only the ordering of the Top-30 candidate list beneath that prefix
- run **3-5** order-perturbed reranking passes, with **5** as the preferred default when latency budget permits
- aggregate the resulting index-based rankings into a final rerank decision
- use this bootstrap process as the primary V1 position-bias mitigation mechanism

#### 2.3.4 Grounding and Memory Offloading

- do not place heavy catalog structures or search trees in VRAM
- let the LLM output candidate indices only
- let the CPU application layer map those indices back to canonical item metadata
- use Phase 1 grounding artifacts such as `id_map.jsonl` to resolve index-to-item identity
- keep grounding outside the LLM so the final returned items stay canonical and deterministic

### Module 2.4: LCR-Based Confidence Verification and Elastic Grounding

This module gathers the repeated index-array outputs from Module 2.3 on CPU, computes a mathematical confidence signal from the model's repeated choices, and delivers a fully grounded final recommendation list with **OOD = 0%** item selection.

#### Responsibilities

- parse repeated rerank outputs on CPU
- extract only valid candidate indices from the allowed range
- compute item-level confidence from repeated model agreement
- ground candidate indices back to canonical SID and item metadata
- support **elastic grounding** when identifier resolution needs SID-aware fallback
- prepare the final user-facing payload by combining grounded metadata with short reasoning text

#### Why it exists

A training-free system needs a cheap way to estimate internal model confidence without calling another LLM pass. Because Module 2.3 emits controlled candidate indices rather than free-form item names, clustering can be replaced with CPU-side vote aggregation and deterministic grounding.

#### Minimum outputs

- parsed rerank index votes
- MSCP confidence scores
- grounded SID and item identities
- mapping mode
- confidence notes
- final delivery payload that combines grounded metadata and recommendation reasoning

#### 2.4.1 Fast CPU Parsing

- parse the 3-5 repeated Module 2.3 outputs on CPU using simple text parsing or regex extraction
- accept only valid candidate indices in the allowed range, typically `1..30`
- discard malformed tokens without invoking the GPU or another LLM pass
- keep parsing cost effectively constant relative to the much heavier model inference step

#### 2.4.2 LCR-Style MSCP Confidence Computation

- treat repeated candidate-index selections as already-clustered semantic outputs
- compute **MSCP (Maximum Semantic Cluster Proportion)** from simple frequency counts on CPU
- for example, if one item is chosen in 4 of 5 rerank passes, its `MSCP = 0.8`
- use MSCP as the primary confidence signal for final ordering and safe delivery
- this replaces a heavier LLM-based clustering stage because the output schema is already index-controlled

#### 2.4.3 GRLM-Style Elastic Identifier Grounding

- map the parsed candidate indices back to canonical identities using Phase 1 grounding artifacts
- use at least:
  - `id_map.jsonl`
  - `sid_to_items.json`
- direct mapping is the default path and should dominate because candidate indices are schema-constrained
- if direct mapping needs recovery logic, use SID-aware elastic grounding rather than free-form fuzzy generation
- grounding must preserve `OOD = 0%` item delivery

#### 2.4.4 Explainable Output Delivery

- select the highest-confidence final recommendations, with **Top-3** as the default UI delivery target
- load canonical item metadata such as title and image URL on CPU
- combine that metadata with the short reasoning produced in Module 2.3
- emit a JSON-ready response payload for API/CLI/UI delivery

## Inputs and Outputs

### Required inputs

- `sid_index/` artifact directory from Phase 1
- taxonomy master dictionary path from Phase 1 taxonomy generation
- offline statistics store for popularity and co-occurrence lookup
- dynamic few-shot example store for successful recommendation cases
- catalog metadata needed to render results
- user request data, which may include:
  - natural-language query
  - liked item IDs
  - disliked item IDs
  - hard filters
  - requested `top_k`

### Required outputs

- ordered recommendation results
- structured explanation payload per item
- rerank rationale metadata
- confidence and elastic-mapping metadata
- grounded final item metadata resolved by CPU from candidate indices

### Minimum response shape

Each result should support fields equivalent to:

- `recipe_id`
- `rank`
- `title`
- `score` or ordinal placement
- `explanation_summary`
- `matched_preferences`
- `tradeoffs_or_caveats`
- `rerank_rationale`
- `confidence_band`
- `mscp`
- `mapping_mode`
- `evidence_refs`
- `bootstrap_support`

The CLI and Python API may serialize these differently, but they must preserve the same information contract.

## Public Interface

### Proposed Python API

```python
@dataclass(frozen=True, slots=True)
class RecommendationRequest:
    query: str | None
    liked_item_ids: tuple[int, ...]
    disliked_item_ids: tuple[int, ...]
    hard_filters: Mapping[str, tuple[str, ...]]
    top_k: int


@dataclass(frozen=True, slots=True)
class InterestSketch:
    summary: str
    positive_facets: tuple[str, ...]
    negative_facets: tuple[str, ...]
    hard_filters: Mapping[str, tuple[str, ...]]
    ambiguity_notes: tuple[str, ...]
    taxonomy_values: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class RecommendedItem:
    recipe_id: int
    sid_string: str
    rank: int
    title: str
    rationale: str
    matched_preferences: tuple[str, ...]
    cautions: tuple[str, ...]
    confidence_band: str
    mscp: float | None
    mapping_mode: str
    evidence_refs: tuple[str, ...]
    bootstrap_support: int
    popularity: float | None
    cooccurrence_with_history: int | None


@dataclass(frozen=True, slots=True)
class RecommendationResponse:
    sketch: InterestSketch
    items: tuple[RecommendedItem, ...]
    rerank_summary: str
    confidence_summary: str
    selected_candidate_indices: tuple[int, ...]
```

Suggested entrypoint:

```python
def recommend(
    *,
    request: RecommendationRequest,
    sid_index_dir: Path,
    taxonomy_dictionary_path: Path,
    stats_store_path: Path,
    fewshot_store_path: Path,
    catalog_path: Path,
) -> RecommendationResponse:
    ...
```

### Proposed CLI

```bash
uv run sid-reco recommend \
  --sid-index-dir data/processed/foodcom/sid_index \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json \
  --stats-store-path data/processed/foodcom/recommendation_stats.sqlite \
  --fewshot-store-path data/processed/foodcom/recommendation_casebank \
  --catalog-path data/processed/foodcom/recipes.csv \
  --query "I want hearty but not too heavy comfort food for a weeknight" \
  --top-k 10
```

Structured-input example:

```bash
uv run sid-reco recommend \
  --sid-index-dir data/processed/foodcom/sid_index \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json \
  --stats-store-path data/processed/foodcom/recommendation_stats.sqlite \
  --fewshot-store-path data/processed/foodcom/recommendation_casebank \
  --catalog-path data/processed/foodcom/recipes.csv \
  --liked-item-id 101 \
  --liked-item-id 225 \
  --disliked-item-id 87 \
  --filter dietary_style=vegetarian \
  --top-k 5
```

## Tech Stack

- Python `3.12`
- `uv`
- `typer` + `rich`
- existing repository modules under `src/sid_reco/`
- existing local LLM runtime conventions in `src/sid_reco/llm.py`
- existing Phase 1 FAISS plus sidecar artifact layout under `data/processed/foodcom/sid_index/`

### Runtime expectations

- **Default**: local-first inference on Apple Silicon
- **Vector substrate**: existing Phase 1 FAISS index and mapping files
- **Query vectorization**: Module 2.2 uses the local MLX embedding model to encode the taxonomy-guided sketch
- **Taxonomy constraint**: Module 2.1 must use the Phase 1 taxonomy master dictionary as the sketching vocabulary
- **Rerank protocol**: Module 2.3 uses one dynamic few-shot example, constrained structured outputs, and candidate-index grounding
- **No training step**: runtime behavior comes from prompt design, taxonomy-guided sketching, semantic retrieval, deterministic filters, offline statistics lookup, and LLM reasoning

## Commands

### Existing repository validation commands

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run mypy src
uv run sid-reco doctor
```

### Existing prerequisite pipeline

```bash
uv run sid-reco prepare-foodcom --raw-dir data/raw/foodcom --out-dir data/processed/foodcom
uv run sid-reco build-neighbor-context \
  --recipes-path data/processed/foodcom/recipes.csv \
  --out-dir data/processed/foodcom/neighbor_context \
  --top-k 5
uv run sid-reco build-taxonomy-dictionary \
  --recipes-path data/processed/foodcom/recipes.csv \
  --out-dir data/processed/foodcom/taxonomy_dictionary \
  --max-tokens 4096
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

### Proposed new online recommendation command

```bash
uv run sid-reco recommend \
  --sid-index-dir data/processed/foodcom/sid_index \
  --taxonomy-dictionary-path data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json \
  --stats-store-path data/processed/foodcom/recommendation_stats.sqlite \
  --fewshot-store-path data/processed/foodcom/recommendation_casebank \
  --catalog-path data/processed/foodcom/recipes.csv \
  --query "Suggest cozy vegetarian dinners with strong comfort-food signals" \
  --top-k 10
```

### Proposed targeted validation

```bash
uv run sid-reco recommend --help
uv run pytest tests/test_interest_sketch.py tests/test_semantic_search.py tests/test_zero_shot_rerank.py tests/test_confidence_mapping.py tests/test_recommendation_pipeline.py tests/test_cli_recommend.py
uv run ruff check .
uv run mypy src
```

## Project Structure

### Existing structure

```text
src/sid_reco/                    -> application package
src/sid_reco/cli.py             -> CLI commands
src/sid_reco/llm.py             -> local LLM runtime integration
src/sid_reco/sid/               -> Phase 1 serialization, embeddings, SID, and FAISS artifacts
tests/                          -> automated tests
data/processed/foodcom/         -> processed local artifacts
SPEC.md                         -> shared feature specification
```

### Proposed additions

```text
src/sid_reco/recommendation/__init__.py          -> public recommendation exports
src/sid_reco/recommendation/types.py             -> request, sketch, and response contracts
src/sid_reco/recommendation/interest_sketch.py   -> Module 2.1 taxonomy-guided user-interest sketching
src/sid_reco/recommendation/semantic_search.py   -> Module 2.2 semantic retrieval and hard filtering
src/sid_reco/recommendation/stats_store.py       -> offline popularity and co-occurrence lookup
src/sid_reco/recommendation/example_store.py     -> dynamic few-shot example retrieval
src/sid_reco/recommendation/zero_shot_rerank.py  -> Module 2.3 explainable zero-shot reranking
src/sid_reco/recommendation/grounding.py         -> CPU-side candidate-index grounding via id_map
src/sid_reco/recommendation/confidence.py        -> Module 2.4 confidence verification
src/sid_reco/recommendation/elastic_mapping.py   -> Module 2.4 intent broadening/narrowing logic
src/sid_reco/recommendation/pipeline.py          -> orchestration layer
src/sid_reco/recommendation/prompting.py         -> prompt builders and schema templates
tests/test_interest_sketch.py                    -> Module 2.1 tests
tests/test_semantic_search.py                    -> Module 2.2 tests
tests/test_zero_shot_rerank.py                   -> Module 2.3 tests
tests/test_confidence_mapping.py                 -> Module 2.4 tests
tests/test_recommendation_pipeline.py            -> end-to-end orchestration tests
tests/test_cli_recommend.py                      -> CLI integration tests
```

### Optional future artifact location

If persistent traces are later approved, a natural default location would be:

```text
artifacts/recommendation_runs/
```

This is intentionally not a mandatory V1 output yet.

## Code Style

The repository already favors typed functions, `Path`-based I/O, explicit dataclasses, and `rich` CLI summaries. The new recommendation engine should follow the same conventions.

Key conventions:

- keep module boundaries visible and testable
- isolate prompt builders from transport and orchestration logic
- keep semantic retrieval deterministic given the same query vector and filters
- keep hard filtering explicit
- do not silently swallow malformed inputs or LLM schema failures
- expose confidence and mapping results as first-class structured data

## Testing Strategy

### Framework and scope

- `pytest` for automated tests
- `ruff` for lint
- `mypy` for type-checking

### Test levels

1. **Module 2.1 - Interest sketch tests**
   - raw request normalization works
   - positive and negative preference extraction is stable
   - taxonomy master dictionary is injected and enforced
   - hard filters are preserved
   - ambiguous queries surface ambiguity notes
   - output sketch stays within approved taxonomy vocabulary

2. **Module 2.2 - Semantic search tests**
   - loads Phase 1 artifacts successfully
   - local MLX query embedding is produced from the taxonomy-guided sketch
   - FAISS cosine retrieval returns an over-sampled Top-100 pool
   - hard filters remove disallowed items deterministically
   - final surviving Top-30 candidate set is stable when enough items survive
   - dropped-candidate reasons are inspectable
   - popularity and co-occurrence metadata are attached correctly

3. **Module 2.3 - Zero-shot rerank tests**
   - exactly one dynamic few-shot example is injected per request
   - ranking output parses into the expected structured schema
   - rationale length stays within the 1-2 sentence limit
   - the model emits candidate indices rather than generated item names
   - three order-perturbed rerank passes can be aggregated deterministically
   - CPU grounding maps candidate indices back to canonical item metadata

4. **Module 2.4 - Confidence and elastic-mapping tests**
   - repeated rerank outputs are parsed on CPU into valid candidate indices
   - MSCP is computed correctly from repeated selections
   - direct grounding via `id_map.jsonl` and `sid_to_items.json` resolves canonical identities
   - fallback elastic grounding preserves `OOD = 0%`
   - final delivery payload combines grounded metadata with short reasoning text

5. **Pipeline tests**
   - end-to-end run succeeds with stubbed LLM outputs
   - the module handoff contract remains stable
   - sparse or contradictory user requests still produce a valid response or explicit failure

6. **CLI integration tests**
   - `sid-reco recommend` prints human-readable ranked results
   - invalid paths or malformed options return non-zero exit codes
   - CLI options map correctly to the internal request model

## Boundaries

### Always

- keep the system **training-free**
- keep Phase 1 artifacts as the runtime recommendation corpus
- preserve all four module boundaries in the implementation
- keep Module 2.1 taxonomy-guided and vocabulary-constrained by the Phase 1 master dictionary
- use taxonomy-aligned vector retrieval plus deterministic CPU hard filtering in Module 2.2
- allow only offline popularity and co-occurrence lookup as auxiliary training-free signals
- compute final confidence on CPU from repeated candidate-index outputs
- return structured explanation and confidence fields
- keep both library API and CLI surfaces aligned

### Ask first

- locking a strict hallucination-control rule for V1
- making persistent trace artifacts mandatory
- expanding V1 into full offline evaluation/report generation
- replacing semantic retrieval with a learned retriever
- adding collaborative or supervised ranking layers

### Never

- train a collaborative-filtering model for this feature
- fine-tune a task-specific recommender model
- recommend items outside the indexed catalog
- silently invent evidence not tied to the loaded corpus
- let Module 2.1 emit free-form retrieval terms outside the taxonomy master dictionary
- replace Module 2.2 with a learned CF model or learned hybrid scorer
- let Module 2.3 emit free-form final item names instead of candidate indices
- bypass Module 2.2 with ad hoc manual item injection
- overwrite Phase 1 `sid_index/` artifacts during runtime recommendation

## Success Criteria

1. Phase 2 is specified and implemented as four explicit modules: 2.1, 2.2, 2.3, and 2.4.
2. A new public recommendation surface exists as both:
   - a Python API
   - a CLI command
3. Module 2.1 produces a structured user-interest sketch from raw request input using only the Phase 1 taxonomy master dictionary vocabulary.
4. Module 2.1 prevents free-form query-sketch hallucination by constraining the sketch to approved taxonomy facets and values.
5. Module 2.2 vectorizes the taxonomy-guided query with the local MLX embedding model and retrieves a default **Top-100** pool from `item_index.faiss` using cosine similarity.
6. Module 2.2 applies deterministic CPU hard filtering to the over-sampled pool and forwards a default **Top-30** surviving candidate set when enough items survive.
7. Module 2.2 attaches offline popularity and co-occurrence statistics as training-free JSON metadata for downstream reasoning.
8. Module 2.3 injects exactly one dynamically retrieved successful recommendation example per request.
9. Module 2.3 uses schema-constrained structured generation, short 1-2 sentence rationales, and candidate-index-only final ranking outputs.
10. Module 2.3 performs 3-5 prefix-cache-friendly order-perturbed rerank passes and aggregates them for position-bias mitigation.
11. Module 2.4 parses repeated candidate-index outputs on CPU and computes MSCP confidence scores from vote frequencies.
12. Module 2.4 grounds final selected indices back to canonical SID and item metadata via `id_map.jsonl` and `sid_to_items.json`.
13. Module 2.4 emits a final explainable delivery payload that combines grounded metadata with short recommendation reasoning.
14. The system operates without any collaborative-filtering model or training phase.
15. Recommendation results remain tied to items already present in the catalog.
16. The architecture fits the repository's existing typed Python and `typer` CLI patterns.
17. New recommendation tests and existing validation commands pass once implementation is complete.

## Open Questions

1. **Hallucination policy**
   - Should explanations be restricted to retrieved evidence only in V1?
   - Or may the LLM add clearly labeled background reasoning?

2. **Persistent traces**
   - Should recommendation runs optionally or always write audit artifacts?

3. **Elastic grounding policy**
   - How aggressively may the system broaden a user's intent before it should instead say "no strong match found"?

4. **Few-shot example bank**
   - How should successful recommendation cases be curated and refreshed for dynamic retrieval?

5. **Bootstrap count**
   - Should V1 default to 3 passes or 5 passes in latency-constrained environments?

## Implementation Notes for Review

- This spec replaces the prior Phase 1 `compile-sid-index` implementation spec in `SPEC.md`.
- Phase 1 remains a prerequisite layer; this document now defines the next online recommendation stage.
- The core structure of this feature is now:
  1. **Module 2.1 - proactive control and taxonomy-guided user-interest sketch**
  2. **Module 2.2 - pure semantic search and hard filtering**
  3. **Module 2.3 - explainable zero-shot reranking**
  4. **Module 2.4 - confidence verification and elastic mapping**
- The taxonomy master dictionary is now part of the runtime contract for Module 2.1, not only an offline artifact.
- Module 2.2 now explicitly includes:
  - local MLX query embedding
  - FAISS cosine Top-100 retrieval
  - CPU pruning to a Top-30 survivor set
  - popularity and co-occurrence metadata lookup for Module 2.3
- Module 2.3 now explicitly includes:
  - one dynamic few-shot example per request
  - constrained structured outputs with short rationales
  - candidate-index-only final ranking output
  - 3-5 order-perturbed rerank passes with prefix-cache reuse
- Module 2.4 now explicitly includes:
  - CPU parsing of repeated candidate-index outputs
  - MSCP confidence computation from vote frequencies
  - direct grounding through `id_map.jsonl` and `sid_to_items.json`
  - final payload assembly with grounded metadata plus short reasoning
- Do **not** start implementation until this revised spec is reviewed and accepted.
