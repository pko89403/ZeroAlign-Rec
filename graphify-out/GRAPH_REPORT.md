# Graph Report - /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco/.claude/worktrees/elated-sammet-50a514  (2026-04-23)

## Corpus Check
- 64 files · ~196,028 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1010 nodes · 4237 edges · 27 communities detected
- Extraction: 30% EXTRACTED · 70% INFERRED · 0% AMBIGUOUS · INFERRED: 2960 edges (avg confidence: 0.81)
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
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]

## God Nodes (most connected - your core abstractions)
1. `MLXTextGenerator` - 103 edges
2. `Context` - 93 edges
3. `Settings` - 66 edges
4. `MLXEmbeddingEncoder` - 64 edges
5. `InterestSketch` - 50 edges
6. `Context` - 44 edges
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
- `main()` --rationale_for--> `Context`  [INFERRED]
  /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco/.claude/worktrees/elated-sammet-50a514/src/sid_reco/cli.py → raw/design/adr/adr-005-taxonomy-dictionary-hardening.md
- `doctor()` --rationale_for--> `Context`  [INFERRED]
  /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco/.claude/worktrees/elated-sammet-50a514/src/sid_reco/cli.py → raw/design/adr/adr-005-taxonomy-dictionary-hardening.md

## Communities

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (148): Run the full training-free recommendation pipeline., Run the full training-free recommendation pipeline., _assign_to_centroids(), build_item_sids(), build_query_sid(), _canonicalize_clusters(), _centroids_close(), _fit_deterministic_kmeans() (+140 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (132): QuerySID, Hierarchical SID assignment for one runtime query vector., FewShotExample, load_fewshot_examples(), _normalize_matrix(), Dynamic few-shot example retrieval for Module 2.3., Small protocol for few-shot example encoding., One successful recommendation example used for dynamic prompting. (+124 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (117): Run the full training-free recommendation pipeline., Diagnose whether the current environment can initialize MLX safely., smoke_mlx(), build_bounded_taxonomy_payload(), build_taxonomy_dictionary(), build_taxonomy_dictionary_prompt(), _evenly_spaced_indices(), generate_taxonomy_dictionary() (+109 more)

### Community 3 - "Community 3"
Cohesion: 0.04
Nodes (97): from_settings(), MLXEmbeddingEncoder, Local MLX embedding utilities., Lazy wrapper around an MLX embedding model., Build an encoder from application settings., Encode a batch of texts into normalized embedding vectors., Encode a single text and return one embedding vector., Load the embedding model only once. (+89 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (99): apply_k_core_filter(), build_manifest(), build_recipe_stats(), build_temporal_splits(), DatasetSummary, _ensure_columns(), filter_positive_interactions(), load_raw_interactions() (+91 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (96): Related, Taxonomy Item Structuring, 개요, 동작 규칙, 사용법/설정, 실행 명령, 현재 구현과 GRLM 레퍼런스의 대응, 현재 상태 (+88 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (83): build_neighbor_context_command(), build_taxonomy_dictionary_command(), compile_sid_index_command(), doctor(), main(), _parse_hard_filters(), prepare_foodcom(), CLI entry points for local development. (+75 more)

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
Nodes (5): GroundingDecision, Module 2.4 SID-aware fallback mapping helpers., Resolved canonical identity for a recommendation candidate., Resolve a candidate through direct id_map lookup, then SID fallback., resolve_grounding()

### Community 16 - "Community 16"
Cohesion: 0.4
Nodes (1): _FakeEncoder

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

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (1): Normalized request contract for recommendation entrypoints.

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): Taxonomy-constrained representation of user intent.

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (1): Final recommendation payload for one catalog item.

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (1): Public response contract for recommendation entrypoints.

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (1): Normalize runtime request fields into a stable typed contract.

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Load residual codebooks from NPZ and validate against the sibling manifest.

## Knowledge Gaps
- **204 isolated node(s):** `Load and query offline recommendation statistics.`, `Lookup-friendly popularity and co-occurrence statistics.`, `Load recommendation statistics persisted by compile-sid-index.`, `Module 2.4 SID-aware fallback mapping helpers.`, `Resolved canonical identity for a recommendation candidate.` (+199 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 18`** (2 nodes): `test_git_hooks_delegate_to_shared_scripts_with_repo_root_fallback()`, `test_git_hook_scripts.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `app.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `i18n.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `Normalized request contract for recommendation entrypoints.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `Taxonomy-constrained representation of user intent.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `Final recommendation payload for one catalog item.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `Public response contract for recommendation entrypoints.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `Normalize runtime request fields into a stable typed contract.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `Load residual codebooks from NPZ and validate against the sibling manifest.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SID recommender package.` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 5`, `Community 6`, `Community 15`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `MLXTextGenerator` connect `Community 5` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 6`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 99 inferred relationships involving `MLXTextGenerator` (e.g. with `_FakeTokenizer` and `_FakeTokenListTokenizer`) actually correct?**
  _`MLXTextGenerator` has 99 INFERRED edges - model-reasoned connections that need verification._
- **Are the 92 inferred relationships involving `Context` (e.g. with `main()` and `doctor()`) actually correct?**
  _`Context` has 92 INFERRED edges - model-reasoned connections that need verification._
- **Are the 64 inferred relationships involving `Settings` (e.g. with `_FakeEncoder` and `_FakeEncoder`) actually correct?**
  _`Settings` has 64 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `MLXEmbeddingEncoder` (e.g. with `_FakeArray` and `Settings`) actually correct?**
  _`MLXEmbeddingEncoder` has 59 INFERRED edges - model-reasoned connections that need verification._