# Graph Report - /Users/skiiwoo/.codex/worktrees/c911/Training-Free-SID-Reco/.graphify-work/corpus  (2026-04-20)

## Corpus Check
- Corpus is ~38,126 words - fits in a single context window. You may not need a graph.

## Summary
- 936 nodes · 4167 edges · 20 communities detected
- Extraction: 29% EXTRACTED · 71% INFERRED · 0% AMBIGUOUS · INFERRED: 2975 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]

## God Nodes (most connected - your core abstractions)
1. `MLXTextGenerator` - 100 edges
2. `Context` - 96 edges
3. `Settings` - 63 edges
4. `MLXEmbeddingEncoder` - 61 edges
5. `Context` - 46 edges
6. `InterestSketch` - 43 edges
7. `SID recommender package.` - 40 edges
8. `후속 변경` - 38 edges
9. `ADR-005: Taxonomy Dictionary 생성 hardening 결정` - 37 edges
10. `Decision` - 37 edges

## Surprising Connections (you probably didn't know these)
- `제약` --rationale_for--> `_interaction()`  [INFERRED]
  raw/design/adr/adr-003-neighbor-context-retrieval.md → tests/test_foodcom_dataset.py
- `Context` --rationale_for--> `MLXTextGenerator`  [INFERRED]
  raw/design/adr/adr-002-foodcom-preprocessing-policy.md → src/sid_reco/llm.py
- `부정적/제약` --rationale_for--> `MLXTextGenerator`  [INFERRED]
  raw/design/adr/adr-004-taxonomy-dictionary-generation.md → src/sid_reco/llm.py
- `Context` --rationale_for--> `from_settings()`  [INFERRED]
  raw/design/adr/adr-002-foodcom-preprocessing-policy.md → src/sid_reco/llm.py
- `부정적/제약` --rationale_for--> `from_settings()`  [INFERRED]
  raw/design/adr/adr-004-taxonomy-dictionary-generation.md → src/sid_reco/llm.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (155): compute_bootstrap_confidence(), _confidence_band(), ConfidenceCandidate, _MutableConfidenceAggregate, Module 2.4 CPU confidence aggregation for bootstrap rerank outputs., Create a compact confidence summary for final delivery., Aggregated confidence evidence for one candidate across rerank passes., Compute per-candidate MSCP and aggregate rationale evidence on CPU. (+147 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (165): build_neighbor_context_command(), build_taxonomy_dictionary_command(), compile_sid_index_command(), doctor(), main(), _parse_hard_filters(), prepare_foodcom(), CLI entry points for local development. (+157 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (137): build_bounded_taxonomy_payload(), build_taxonomy_dictionary(), build_taxonomy_dictionary_prompt(), _evenly_spaced_indices(), generate_taxonomy_dictionary(), load_taxonomy_items(), normalize_taxonomy_dictionary(), _parse_string_list() (+129 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (94): Related, Taxonomy Item Structuring, 개요, 동작 규칙, 사용법/설정, 실행 명령, 현재 구현과 GRLM 레퍼런스의 대응, 현재 상태 (+86 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (93): apply_k_core_filter(), build_manifest(), build_recipe_stats(), build_temporal_splits(), DatasetSummary, _ensure_columns(), filter_positive_interactions(), load_raw_interactions() (+85 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (53): CompiledSIDItem, CompiledSIDItems, ResidualKMeansLevel, EmbeddedSIDItems, _normalize_embedding_matrix(), FAISS indexing and mapping artifact writers for compiled SID outputs., Summary for persisted SID index artifacts., Persist compiled SID outputs, mapping files, and a CPU FAISS index. (+45 more)

### Community 6 - "Community 6"
Cohesion: 0.1
Nodes (0): 

### Community 7 - "Community 7"
Cohesion: 0.16
Nodes (16): ensure_mlx_runtime_available(), get_runtime_environment_summary(), MLXRuntimeProbeResult, probe_mlx_runtime(), Helpers for probing MLX runtime availability safely., Probe MLX imports in a child process to avoid crashing the main process., High-level summary of the local execution environment., Result of a child-process MLX runtime probe. (+8 more)

### Community 8 - "Community 8"
Cohesion: 0.16
Nodes (12): _ordered_neighbor_candidates(), Search exact top-k item neighbors with deterministic tie-breaking., _search_neighbor_candidates_for_source(), search_topk_neighbors(), _FlakyEncoder, _StaticSearchIndex, test_encode_catalog_with_adaptive_batches_halves_after_runtime_error(), test_encode_catalog_with_adaptive_batches_reraises_non_oom_runtime_error() (+4 more)

### Community 9 - "Community 9"
Cohesion: 0.4
Nodes (8): _load_execute_module(), test_build_preamble_keeps_git_ownership_in_executor(), test_check_blockers_exits_for_blocked_steps(), test_ensure_clean_worktree_exits_when_repo_is_dirty(), test_ensure_created_at_records_task_timestamp(), test_invoke_claude_writes_output_and_uses_expected_command(), test_load_guardrails_uses_repo_specific_documents(), _write_phase_index()

### Community 10 - "Community 10"
Cohesion: 0.35
Nodes (10): _init_repo(), _seed_raw_corpus(), test_graphify_ci_candidate_is_candidate_only_even_when_staged_output_exists(), test_graphify_ci_candidate_writes_manual_note_when_no_staged_output(), test_graphify_prepare_corpus_script_copies_only_curated_inputs(), test_graphify_sync_staged_copies_verified_outputs(), test_graphify_sync_staged_requires_verify_marker(), test_graphify_verify_full_refresh_accepts_doc_context_graph() (+2 more)

### Community 11 - "Community 11"
Cohesion: 0.2
Nodes (2): _EmptyTaxonomyGenerator, _FakeGenerator

### Community 12 - "Community 12"
Cohesion: 0.29
Nodes (7): load_recommendation_stats_store(), _parse_double_nested_int_mapping(), _parse_nested_int_mapping(), Load and query offline recommendation statistics., Lookup-friendly popularity and co-occurrence statistics., Load recommendation statistics persisted by compile-sid-index., RecommendationStatsStore

### Community 13 - "Community 13"
Cohesion: 0.33
Nodes (6): _ProjectionGenerator, test_structure_taxonomy_batch_cli_can_include_evidence(), test_structure_taxonomy_batch_cli_writes_jsonl(), test_structure_taxonomy_item_cli_can_include_evidence(), test_structure_taxonomy_item_cli_prints_json(), _write_projection_inputs()

### Community 14 - "Community 14"
Cohesion: 0.43
Nodes (4): _FakeEncoder, test_compile_sid_index_cli_reports_missing_taxonomy_dictionary(), test_compile_sid_index_cli_writes_all_outputs(), _write_sid_inputs()

### Community 15 - "Community 15"
Cohesion: 0.71
Nodes (6): _copy_graphify_runtime(), _init_repo(), _seed_repo(), test_graphify_auto_refresh_runs_code_refresh_after_code_only_change(), test_graphify_auto_refresh_runs_full_refresh_after_doc_change(), _write_file()

### Community 16 - "Community 16"
Cohesion: 0.73
Nodes (5): _copy_script(), _init_repo(), test_graphify_full_refresh_produces_staged_outputs_with_doc_context(), test_graphify_full_refresh_reports_partial_state_on_semantic_failure(), _write_file()

### Community 17 - "Community 17"
Cohesion: 0.4
Nodes (5): GroundingDecision, Module 2.4 SID-aware fallback mapping helpers., Resolved canonical identity for a recommendation candidate., Resolve a candidate through direct id_map lookup, then SID fallback., resolve_grounding()

### Community 18 - "Community 18"
Cohesion: 0.4
Nodes (1): _FakeEncoder

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (2): _recipe_row(), test_prepare_foodcom_cli_writes_processed_outputs()

## Knowledge Gaps
- **194 isolated node(s):** `Shared recommendation contracts.`, `Normalized request contract for recommendation entrypoints.`, `Taxonomy-constrained representation of user intent.`, `Final recommendation payload for one catalog item.`, `Public response contract for recommendation entrypoints.` (+189 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SID recommender package.` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 12`, `Community 17`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `MLXTextGenerator` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 4`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 5`, `Community 14`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 96 inferred relationships involving `MLXTextGenerator` (e.g. with `_FakeTokenizer` and `_FakeTokenListTokenizer`) actually correct?**
  _`MLXTextGenerator` has 96 INFERRED edges - model-reasoned connections that need verification._
- **Are the 95 inferred relationships involving `Context` (e.g. with `build_taxonomy_dictionary()` and `foodcom.py`) actually correct?**
  _`Context` has 95 INFERRED edges - model-reasoned connections that need verification._
- **Are the 61 inferred relationships involving `Settings` (e.g. with `_FakeEncoder` and `_FakeEncoder`) actually correct?**
  _`Settings` has 61 INFERRED edges - model-reasoned connections that need verification._
- **Are the 56 inferred relationships involving `MLXEmbeddingEncoder` (e.g. with `_FakeArray` and `Settings`) actually correct?**
  _`MLXEmbeddingEncoder` has 56 INFERRED edges - model-reasoned connections that need verification._