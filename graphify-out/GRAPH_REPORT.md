# Graph Report - /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco/.claude/worktrees/elated-sammet-50a514  (2026-04-23)

## Corpus Check
- 64 files · ~194,101 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 997 nodes · 4192 edges · 23 communities detected
- Extraction: 30% EXTRACTED · 70% INFERRED · 0% AMBIGUOUS · INFERRED: 2918 edges (avg confidence: 0.82)
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
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]

## God Nodes (most connected - your core abstractions)
1. `MLXTextGenerator` - 102 edges
2. `Context` - 93 edges
3. `Settings` - 65 edges
4. `MLXEmbeddingEncoder` - 63 edges
5. `Context` - 44 edges
6. `InterestSketch` - 43 edges
7. `SID recommender package.` - 40 edges
8. `후속 변경` - 37 edges
9. `ADR-005: Taxonomy Dictionary 생성 hardening 결정` - 36 edges
10. `Decision` - 36 edges

## Surprising Connections (you probably didn't know these)
- `_interaction()` --rationale_for--> `제약`  [INFERRED]
  /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco/.claude/worktrees/elated-sammet-50a514/tests/test_foodcom_dataset.py → raw/design/adr/adr-003-neighbor-context-retrieval.md
- `MLXTextGenerator` --rationale_for--> `Context`  [INFERRED]
  /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco/.claude/worktrees/elated-sammet-50a514/src/sid_reco/llm.py → raw/design/adr/adr-002-foodcom-preprocessing-policy.md
- `MLXTextGenerator` --rationale_for--> `부정적/제약`  [INFERRED]
  /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco/.claude/worktrees/elated-sammet-50a514/src/sid_reco/llm.py → raw/design/adr/adr-004-taxonomy-dictionary-generation.md
- `TaxonomyPayload` --rationale_for--> `Context`  [INFERRED]
  /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco/.claude/worktrees/elated-sammet-50a514/src/sid_reco/taxonomy/dictionary.py → raw/design/adr/adr-005-taxonomy-dictionary-hardening.md
- `TaxonomyPromptBundle` --rationale_for--> `Context`  [INFERRED]
  /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco/.claude/worktrees/elated-sammet-50a514/src/sid_reco/taxonomy/dictionary.py → raw/design/adr/adr-005-taxonomy-dictionary-hardening.md

## Communities

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (202): build_neighbor_context_command(), build_taxonomy_dictionary_command(), compile_sid_index_command(), doctor(), main(), _parse_hard_filters(), prepare_foodcom(), CLI entry points for local development. (+194 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (153): Run the full training-free recommendation pipeline., Run the full training-free recommendation pipeline., _assign_to_centroids(), build_item_sids(), build_query_sid(), _canonicalize_clusters(), _centroids_close(), _fit_deterministic_kmeans() (+145 more)

### Community 2 - "Community 2"
Cohesion: 0.03
Nodes (136): compute_bootstrap_confidence(), _confidence_band(), ConfidenceCandidate, _MutableConfidenceAggregate, Module 2.4 CPU confidence aggregation for bootstrap rerank outputs., Create a compact confidence summary for final delivery., Aggregated confidence evidence for one candidate across rerank passes., Compute per-candidate MSCP and aggregate rationale evidence on CPU. (+128 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (141): build_bounded_taxonomy_payload(), build_taxonomy_dictionary(), build_taxonomy_dictionary_prompt(), _evenly_spaced_indices(), generate_taxonomy_dictionary(), load_taxonomy_items(), normalize_taxonomy_dictionary(), _parse_string_list() (+133 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (100): Project-level configuration helpers., Resolve relative paths against the project root., _resolve_project_path(), from_settings(), MLXEmbeddingEncoder, Local MLX embedding utilities., Lazy wrapper around an MLX embedding model., Build an encoder from application settings. (+92 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (0): 

### Community 6 - "Community 6"
Cohesion: 0.12
Nodes (7): App(), avgMscp(), buildLangHref(), escapeHtml(), JsonView(), MetricsStrip(), OverviewGrid()

### Community 7 - "Community 7"
Cohesion: 0.3
Nodes (16): build_item_projection_context(), build_item_projection_prompt(), _QueuedGenerator, test_build_item_projection_context_loads_target_neighbors_and_taxonomy(), test_build_item_projection_context_requires_top5_neighbors(), test_build_item_projection_prompt_embeds_target_neighbors_and_vocab(), test_finalize_item_taxonomy_canonicalizes_variants_and_drops_weak_american_bias(), test_finalize_item_taxonomy_drops_contradictory_dietary_labels() (+8 more)

### Community 8 - "Community 8"
Cohesion: 0.21
Nodes (12): _FakeEncoder, _FakeGenerator, _make_candidate(), _make_sketch(), test_parse_rerank_response_rejects_long_reasoning(), test_parse_rerank_response_rejects_wrong_selection_size(), test_run_bootstrap_rerank_injects_one_dynamic_example_and_runs_multiple_passes(), test_run_bootstrap_rerank_limits_structured_output_to_selection_size() (+4 more)

### Community 9 - "Community 9"
Cohesion: 0.39
Nodes (11): _clean_env(), _init_repo(), _seed_raw_corpus(), test_graphify_ci_candidate_is_candidate_only_even_when_staged_output_exists(), test_graphify_ci_candidate_writes_manual_note_when_no_staged_output(), test_graphify_prepare_corpus_script_copies_only_curated_inputs(), test_graphify_sync_staged_copies_verified_outputs(), test_graphify_sync_staged_requires_verify_marker() (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.69
Nodes (10): _clean_env(), _commit_all(), _copy_graphify_runtime(), _init_repo(), _seed_repo(), test_graphify_auto_refresh_bootstrap_does_not_skip_first_doc_change(), test_graphify_auto_refresh_bootstrap_runs_code_refresh_for_first_code_change(), test_graphify_auto_refresh_runs_code_refresh_after_code_only_change() (+2 more)

### Community 11 - "Community 11"
Cohesion: 0.4
Nodes (8): _load_execute_module(), test_build_preamble_keeps_git_ownership_in_executor(), test_check_blockers_exits_for_blocked_steps(), test_ensure_clean_worktree_exits_when_repo_is_dirty(), test_ensure_created_at_records_task_timestamp(), test_invoke_claude_writes_output_and_uses_expected_command(), test_load_guardrails_uses_repo_specific_documents(), _write_phase_index()

### Community 12 - "Community 12"
Cohesion: 0.2
Nodes (2): _EmptyTaxonomyGenerator, _FakeGenerator

### Community 13 - "Community 13"
Cohesion: 0.33
Nodes (5): _FakeTokenizer, _FakeTokenListTokenizer, test_generate_raises_runtime_error_when_probe_fails(), test_generate_supports_chat_template_that_returns_token_ids(), test_generate_uses_chat_template()

### Community 14 - "Community 14"
Cohesion: 0.33
Nodes (6): _ProjectionGenerator, test_structure_taxonomy_batch_cli_can_include_evidence(), test_structure_taxonomy_batch_cli_writes_jsonl(), test_structure_taxonomy_item_cli_can_include_evidence(), test_structure_taxonomy_item_cli_prints_json(), _write_projection_inputs()

### Community 15 - "Community 15"
Cohesion: 0.71
Nodes (6): _clean_env(), _copy_script(), _init_repo(), test_graphify_full_refresh_produces_staged_outputs_with_doc_context(), test_graphify_full_refresh_reports_partial_state_on_semantic_failure(), _write_file()

### Community 16 - "Community 16"
Cohesion: 0.43
Nodes (4): _FakeEncoder, test_compile_sid_index_cli_reports_missing_taxonomy_dictionary(), test_compile_sid_index_cli_writes_all_outputs(), _write_sid_inputs()

### Community 17 - "Community 17"
Cohesion: 0.4
Nodes (1): _FakeEncoder

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (2): _recipe_row(), test_prepare_foodcom_cli_writes_processed_outputs()

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): Load residual codebooks from NPZ and validate against the sibling manifest.

## Knowledge Gaps
- **204 isolated node(s):** `Shared recommendation contracts.`, `Normalized request contract for recommendation entrypoints.`, `Taxonomy-constrained representation of user intent.`, `Final recommendation payload for one catalog item.`, `Public response contract for recommendation entrypoints.` (+199 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 19`** (2 nodes): `test_git_hooks_delegate_to_shared_scripts_with_repo_root_fallback()`, `test_git_hook_scripts.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `app.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `i18n.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `Load residual codebooks from NPZ and validate against the sibling manifest.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SID recommender package.` connect `Community 2` to `Community 1`, `Community 3`, `Community 4`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `MLXTextGenerator` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 4`, `Community 13`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 16`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 98 inferred relationships involving `MLXTextGenerator` (e.g. with `_FakeTokenizer` and `_FakeTokenListTokenizer`) actually correct?**
  _`MLXTextGenerator` has 98 INFERRED edges - model-reasoned connections that need verification._
- **Are the 92 inferred relationships involving `Context` (e.g. with `main()` and `doctor()`) actually correct?**
  _`Context` has 92 INFERRED edges - model-reasoned connections that need verification._
- **Are the 63 inferred relationships involving `Settings` (e.g. with `_FakeEncoder` and `_FakeEncoder`) actually correct?**
  _`Settings` has 63 INFERRED edges - model-reasoned connections that need verification._
- **Are the 58 inferred relationships involving `MLXEmbeddingEncoder` (e.g. with `_FakeArray` and `Settings`) actually correct?**
  _`MLXEmbeddingEncoder` has 58 INFERRED edges - model-reasoned connections that need verification._