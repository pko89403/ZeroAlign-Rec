# Graph Report - /Users/skiiwoo/PERSONAL/worktree/zeroalign-rec/fix-harness  (2026-04-21)

## Corpus Check
- 65 files · ~192,686 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 972 nodes · 4138 edges · 21 communities detected
- Extraction: 30% EXTRACTED · 70% INFERRED · 0% AMBIGUOUS · INFERRED: 2883 edges (avg confidence: 0.82)
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

## God Nodes (most connected - your core abstractions)
1. `MLXTextGenerator` - 100 edges
2. `Context` - 93 edges
3. `Settings` - 63 edges
4. `MLXEmbeddingEncoder` - 61 edges
5. `Context` - 44 edges
6. `InterestSketch` - 43 edges
7. `SID recommender package.` - 40 edges
8. `후속 변경` - 37 edges
9. `ADR-005: Taxonomy Dictionary 생성 hardening 결정` - 36 edges
10. `Decision` - 36 edges

## Surprising Connections (you probably didn't know these)
- `_interaction()` --rationale_for--> `제약`  [INFERRED]
  /Users/skiiwoo/PERSONAL/worktree/zeroalign-rec/fix-harness/tests/test_foodcom_dataset.py → raw/design/adr/adr-003-neighbor-context-retrieval.md
- `MLXTextGenerator` --rationale_for--> `Context`  [INFERRED]
  /Users/skiiwoo/PERSONAL/worktree/zeroalign-rec/fix-harness/src/sid_reco/llm.py → raw/design/adr/adr-002-foodcom-preprocessing-policy.md
- `MLXTextGenerator` --rationale_for--> `부정적/제약`  [INFERRED]
  /Users/skiiwoo/PERSONAL/worktree/zeroalign-rec/fix-harness/src/sid_reco/llm.py → raw/design/adr/adr-004-taxonomy-dictionary-generation.md
- `from_settings()` --rationale_for--> `Context`  [INFERRED]
  /Users/skiiwoo/PERSONAL/worktree/zeroalign-rec/fix-harness/src/sid_reco/llm.py → raw/design/adr/adr-002-foodcom-preprocessing-policy.md
- `_format_chat_prompt()` --rationale_for--> `Context`  [INFERRED]
  /Users/skiiwoo/PERSONAL/worktree/zeroalign-rec/fix-harness/src/sid_reco/llm.py → raw/design/adr/adr-002-foodcom-preprocessing-policy.md

## Communities

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (151): build_neighbor_context_command(), build_taxonomy_dictionary_command(), doctor(), main(), _parse_hard_filters(), prepare_foodcom(), CLI entry points for local development., Run a single prompt against the configured local MLX LLM. (+143 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (122): compile_sid_index_command(), _assign_to_centroids(), assign_trained_residual_kmeans(), _canonicalize_clusters(), _centroids_close(), compile_residual_kmeans(), CompiledSIDItem, CompiledSIDItems (+114 more)

### Community 2 - "Community 2"
Cohesion: 0.03
Nodes (100): Runtime settings resolved from the environment., Settings, EmbeddedSIDItems, EmbeddedSIDWriteSummary, encode_serialized_items(), encode_serialized_items_with_mlx(), Embedding helpers for serialized SID items., Minimal protocol for turning serialized item text into dense vectors. (+92 more)

### Community 3 - "Community 3"
Cohesion: 0.04
Nodes (96): Project-level configuration helpers., Create default directories used by the local workflow., Resolve relative paths against the project root., _resolve_project_path(), from_settings(), MLXEmbeddingEncoder, Local MLX embedding utilities., Lazy wrapper around an MLX embedding model. (+88 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (97): Related, Taxonomy Item Structuring, 개요, 동작 규칙, 사용법/설정, 실행 명령, 현재 구현과 GRLM 레퍼런스의 대응, 현재 상태 (+89 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (96): apply_k_core_filter(), build_manifest(), build_recipe_stats(), build_temporal_splits(), DatasetSummary, _ensure_columns(), filter_positive_interactions(), load_raw_interactions() (+88 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (79): compute_bootstrap_confidence(), _confidence_band(), ConfidenceCandidate, _MutableConfidenceAggregate, Module 2.4 CPU confidence aggregation for bootstrap rerank outputs., Create a compact confidence summary for final delivery., Aggregated confidence evidence for one candidate across rerank passes., Compute per-candidate MSCP and aggregate rationale evidence on CPU. (+71 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (0): 

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (7): App(), avgMscp(), buildLangHref(), escapeHtml(), JsonView(), MetricsStrip(), OverviewGrid()

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
Nodes (6): _ProjectionGenerator, test_structure_taxonomy_batch_cli_can_include_evidence(), test_structure_taxonomy_batch_cli_writes_jsonl(), test_structure_taxonomy_item_cli_can_include_evidence(), test_structure_taxonomy_item_cli_prints_json(), _write_projection_inputs()

### Community 14 - "Community 14"
Cohesion: 0.71
Nodes (6): _clean_env(), _copy_script(), _init_repo(), test_graphify_full_refresh_produces_staged_outputs_with_doc_context(), test_graphify_full_refresh_reports_partial_state_on_semantic_failure(), _write_file()

### Community 15 - "Community 15"
Cohesion: 0.4
Nodes (1): _FakeEncoder

### Community 16 - "Community 16"
Cohesion: 0.5
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (2): _recipe_row(), test_prepare_foodcom_cli_writes_processed_outputs()

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **194 isolated node(s):** `Shared recommendation contracts.`, `Normalized request contract for recommendation entrypoints.`, `Taxonomy-constrained representation of user intent.`, `Final recommendation payload for one catalog item.`, `Public response contract for recommendation entrypoints.` (+189 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 18`** (2 nodes): `test_git_hooks_delegate_to_shared_scripts_with_repo_root_fallback()`, `test_git_hook_scripts.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `app.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `i18n.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SID recommender package.` connect `Community 6` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `MLXTextGenerator` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 2` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 6`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 96 inferred relationships involving `MLXTextGenerator` (e.g. with `_FakeTokenizer` and `_FakeTokenListTokenizer`) actually correct?**
  _`MLXTextGenerator` has 96 INFERRED edges - model-reasoned connections that need verification._
- **Are the 92 inferred relationships involving `Context` (e.g. with `main()` and `doctor()`) actually correct?**
  _`Context` has 92 INFERRED edges - model-reasoned connections that need verification._
- **Are the 61 inferred relationships involving `Settings` (e.g. with `_FakeEncoder` and `_FakeEncoder`) actually correct?**
  _`Settings` has 61 INFERRED edges - model-reasoned connections that need verification._
- **Are the 56 inferred relationships involving `MLXEmbeddingEncoder` (e.g. with `_FakeArray` and `Settings`) actually correct?**
  _`MLXEmbeddingEncoder` has 56 INFERRED edges - model-reasoned connections that need verification._