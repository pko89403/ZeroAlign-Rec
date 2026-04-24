# Graph Report - /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco-graphify-upstream-entrypoint  (2026-04-23)

## Corpus Check
- 99 files · ~196,394 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 906 nodes · 2032 edges · 32 communities detected
- Extraction: 59% EXTRACTED · 41% INFERRED · 0% AMBIGUOUS · INFERRED: 830 edges (avg confidence: 0.66)
- Token cost: 2,503 input · 9,822 output

## Community Hubs (Navigation)
- [[_COMMUNITY_SID Request Types|SID Request Types]]
- [[_COMMUNITY_Embedding Core Models|Embedding Core Models]]
- [[_COMMUNITY_Taxonomy Projection|Taxonomy Projection]]
- [[_COMMUNITY_Taxonomy Generation LLM|Taxonomy Generation LLM]]
- [[_COMMUNITY_Recommendation Pipeline|Recommendation Pipeline]]
- [[_COMMUNITY_Neighbor Retrieval|Neighbor Retrieval]]
- [[_COMMUNITY_SID Compiler|SID Compiler]]
- [[_COMMUNITY_Food.com Preparation|Food.com Preparation]]
- [[_COMMUNITY_Repo Docs ADRs|Repo Docs ADRs]]
- [[_COMMUNITY_Design Notes|Design Notes]]
- [[_COMMUNITY_Desktop Demo UI|Desktop Demo UI]]
- [[_COMMUNITY_CLI Entry Points|CLI Entry Points]]
- [[_COMMUNITY_Serialization Utilities|Serialization Utilities]]
- [[_COMMUNITY_MLX Runtime Checks|MLX Runtime Checks]]
- [[_COMMUNITY_Zero-Shot Rerank Tests|Zero-Shot Rerank Tests]]
- [[_COMMUNITY_Demo Components|Demo Components]]
- [[_COMMUNITY_Recommendation Stats|Recommendation Stats]]
- [[_COMMUNITY_Brand Identity|Brand Identity]]
- [[_COMMUNITY_Auto Refresh Tests|Auto Refresh Tests]]
- [[_COMMUNITY_Graphify Workflow Tests|Graphify Workflow Tests]]
- [[_COMMUNITY_Phase Executor Tests|Phase Executor Tests]]
- [[_COMMUNITY_Taxonomy CLI Tests|Taxonomy CLI Tests]]
- [[_COMMUNITY_Structure Taxonomy CLI|Structure Taxonomy CLI]]
- [[_COMMUNITY_Mobile Demo UI|Mobile Demo UI]]
- [[_COMMUNITY_Compile Index CLI|Compile Index CLI]]
- [[_COMMUNITY_Graphify Producer Tests|Graphify Producer Tests]]
- [[_COMMUNITY_Graphify Eval Scorecard|Graphify Eval Scorecard]]
- [[_COMMUNITY_Neighbor Context CLI|Neighbor Context CLI]]
- [[_COMMUNITY_Graph Quality Eval|Graph Quality Eval]]
- [[_COMMUNITY_Graphify Evaluation Docs|Graphify Evaluation Docs]]
- [[_COMMUNITY_Explanation Eval Tests|Explanation Eval Tests]]
- [[_COMMUNITY_Prepare Foodcom CLI|Prepare Foodcom CLI]]

## God Nodes (most connected - your core abstractions)
1. `MLXTextGenerator` - 89 edges
2. `Settings` - 61 edges
3. `MLXEmbeddingEncoder` - 56 edges
4. `InterestSketch` - 45 edges
5. `SID compilation helpers.` - 39 edges
6. `SerializedSIDItem` - 30 edges
7. `SemanticCandidate` - 28 edges
8. `RecommendationRequest` - 27 edges
9. `QuerySID` - 25 edges
10. `train_codebooks()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `CLAUDE Schema Layer` --semantically_similar_to--> `AGENTS Schema Layer`  [INFERRED] [semantically similar]
  CLAUDE.md → AGENTS.md
- `ZeroAlign-Rec Korean README` --semantically_similar_to--> `ZeroAlign-Rec English README`  [INFERRED] [semantically similar]
  README.ko.md → README.md
- `test_residual_kmeans_level_dataclass_is_usable_directly()` --calls--> `ResidualKMeansLevel`  [INFERRED]
  /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco-graphify-upstream-entrypoint/tests/test_sid_compiler.py → /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco-graphify-upstream-entrypoint/src/sid_reco/sid/compiler.py
- `test_parse_rerank_response_rejects_long_reasoning()` --calls--> `parse_rerank_response()`  [INFERRED]
  /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco-graphify-upstream-entrypoint/tests/test_zero_shot_rerank.py → /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco-graphify-upstream-entrypoint/src/sid_reco/recommendation/zero_shot_rerank.py
- `test_parse_rerank_response_rejects_wrong_selection_size()` --calls--> `parse_rerank_response()`  [INFERRED]
  /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco-graphify-upstream-entrypoint/tests/test_zero_shot_rerank.py → /Users/skiiwoo/PERSONAL/Training-Free-SID-Reco-graphify-upstream-entrypoint/src/sid_reco/recommendation/zero_shot_rerank.py

## Hyperedges (group relationships)
- **Graphify Knowledge Model** — agents_schema_layer, claude_schema_layer, graphify_first_knowledge_model, graphify_source_corpus_policy, graphify_refresh_workflow, graph_report_artifact, graph_html_artifact [INFERRED 0.93]
- **Taxonomy Alignment Pipeline Decisions** — adr_002_foodcom_preprocessing_decision, adr_003_neighbor_context_decision, adr_004_taxonomy_dictionary_generation_decision, adr_005_taxonomy_dictionary_hardening_decision, adr_006_strict_tid_hardening_decision [INFERRED 0.91]
- **Runtime and Demo Surface** — zeroalign_readme_en, zeroalign_readme_ko, query_sid_runtime_spec, demo_static_pipeline [INFERRED 0.84]
- **Food.com Phase 1 Pipeline** — foodcom_implicit_feedback_dataset, top_5_neighbor_evidence, bounded_taxonomy_dictionary_generation, structured_taxonomy_tid_projection, deterministic_sid_artifact_pipeline [INFERRED 0.88]
- **Recommendation Runtime Validation Loop** — phase2_recommendation_runtime, phase1_artifact_consistency_validated, recommendation_artifact_completeness, structured_top_k_rerank_contract, phase2_runtime_stabilized [INFERRED 0.84]
- **Graphify Evaluation Context** — graphify_evaluation_runbook, verified_full_refresh_evaluation_gate, graph_report_fixture, graph_report_design_context [INFERRED 0.79]
- **Sidebar inputs and the active meal brief condition the delivered recommendation set.** — left_control_sidebar, selected_weeknight_vegetarian_scenario, recommendations_board, result_theme_alignment [INFERRED 0.90]
- **The visible results board is explicitly situated inside a larger recommendation pipeline.** — pipeline_stepper, delivery_stage_active, recommendations_board [INFERRED 0.94]
- **Each result card combines rank, confidence, explanation tags, and imagery into one comparison unit.** — ranked_card_triplet, confidence_badges, rationale_tags, visual_food_placeholders [INFERRED 0.92]
- **mobile_intake_flow** — preset_scenario_selector, natural_language_query_box, preference_filter_panel, run_pipeline_cta [INFERRED 0.95]
- **responsive_navigation_pattern** — mobile_recommendation_shell, pipeline_stage_carousel, delivery_recommendations_panel [INFERRED 0.93]
- **grounded_result_pattern** — delivery_recommendations_panel, ranked_recommendation_cards, evidence_chip_metadata [INFERRED 0.95]
- **brand_lockup_system** — semantic_graph_icon, zeroalign_rec_wordmark, training_free_semantic_recommendation_tagline, accent_palette_bars [INFERRED 0.95]
- **product_name_semantics** — alignment_axis, stylized_z_path, recommendation_nodes, zeroalign_rec_wordmark, rec_suffix_highlight [INFERRED 0.93]
- **aligned_recommendation_iconography** — semantic_graph_icon, semantic_hub, alignment_axis, recommendation_nodes [INFERRED 0.92]
- **brand_identity_system** — semantic_hub, alignment_axis, stylized_z_trajectory, recommendation_nodes, tech_gradient_palette [INFERRED 0.94]
- **semantic_recommendation_scene** — semantic_hub, recommendation_nodes, orbital_context_rings [INFERRED 0.91]

## Communities

### Community 0 - "SID Request Types"
Cohesion: 0.05
Nodes (90): QuerySID, Hierarchical SID assignment for one runtime query vector., FewShotExample, load_fewshot_examples(), _normalize_matrix(), Dynamic few-shot example retrieval for Module 2.3., Small protocol for few-shot example encoding., One successful recommendation example used for dynamic prompting. (+82 more)

### Community 1 - "Embedding Core Models"
Cohesion: 0.05
Nodes (80): compile_sid_index_command(), CLI entry points for local development., Run a single prompt against the configured local MLX LLM., Generate an embedding preview for one input string., Prepare a downsampled Food.com dataset for local recommendation experiments., Build item embeddings and a FAISS top-k neighbor context., Generate a TaxRec-style taxonomy dictionary JSON from recipe metadata., Structure one recipe item into taxonomy-aligned JSON. (+72 more)

### Community 2 - "Taxonomy Projection"
Cohesion: 0.05
Nodes (82): structure_taxonomy_item_command(), Normalize free text into snake_case., _to_snake_case(), build_item_projection_context(), build_item_projection_evidence(), build_item_projection_prompt(), build_retry_prompt(), build_self_refine_prompt() (+74 more)

### Community 3 - "Taxonomy Generation LLM"
Cohesion: 0.06
Nodes (56): build_bounded_taxonomy_payload(), build_taxonomy_dictionary(), build_taxonomy_dictionary_prompt(), _evenly_spaced_indices(), generate_taxonomy_dictionary(), load_taxonomy_items(), normalize_taxonomy_dictionary(), _parse_string_list() (+48 more)

### Community 4 - "Recommendation Pipeline"
Cohesion: 0.08
Nodes (44): compute_bootstrap_confidence(), _confidence_band(), ConfidenceCandidate, _MutableConfidenceAggregate, Module 2.4 CPU confidence aggregation for bootstrap rerank outputs., Create a compact confidence summary for final delivery., Aggregated confidence evidence for one candidate across rerank passes., Compute per-candidate MSCP and aggregate rationale evidence on CPU. (+36 more)

### Community 5 - "Neighbor Retrieval"
Cohesion: 0.06
Nodes (43): build_neighbor_context_command(), _as_normalized_float32_matrix(), build_embedding_text(), build_faiss_index(), build_neighbor_context(), build_neighbor_context_manifest(), _compose_embedding_text(), detect_total_memory_bytes() (+35 more)

### Community 6 - "SID Compiler"
Cohesion: 0.11
Nodes (41): _assign_to_centroids(), build_item_sids(), build_query_sid(), _canonicalize_clusters(), _centroids_close(), _fit_deterministic_kmeans(), _format_sid(), _initialize_centroids() (+33 more)

### Community 7 - "Food.com Preparation"
Cohesion: 0.09
Nodes (37): apply_k_core_filter(), build_manifest(), build_recipe_stats(), build_temporal_splits(), DatasetSummary, _ensure_columns(), filter_positive_interactions(), load_raw_interactions() (+29 more)

### Community 8 - "Repo Docs ADRs"
Cohesion: 0.1
Nodes (32): ADR-001 Dev Environment Decision, Why the project standardizes on Apple Silicon + MLX, Why Food.com is reduced to compact implicit feedback, ADR-002 Food.com Preprocessing Policy, Why neighbor context uses exact cosine search with FAISS, ADR-003 Neighbor Context Policy, ADR-004 Taxonomy Dictionary Generation, Why taxonomy generation uses a local LLM and JSON-only output (+24 more)

### Community 9 - "Design Notes"
Cohesion: 0.12
Nodes (29): Beyond Relevance Adaptive Exploration Framework, Bounded Taxonomy Dictionary Generation, Deterministic SID Artifact Pipeline, Food.com Dataset, Food Taxonomy Dictionary, Food.com 5-core Implicit Feedback Dataset, GRLM Reference Implementation, Retain Serialized Items and Embeddings (+21 more)

### Community 10 - "Desktop Demo UI"
Cohesion: 0.11
Nodes (25): Desktop recommendation demo shell branded ZeroAlign-Rec with a clean editorial dashboard aesthetic., Brand header with ZeroAlign-Rec logo and phase subtitle, Green confidence badges use numeric scores to communicate calibrated trust for each recommendation., Delivery is the highlighted active stage, signaling that grounded final outputs are currently in focus., Korean desktop recipe recommendation demo screen, English-language copy paired with a visible KR toggle implies bilingual or locale-switchable presentation., Main grounded recommendation summary panel, Hard filter chips with active and inactive pill states (+17 more)

### Community 12 - "CLI Entry Points"
Cohesion: 0.14
Nodes (19): build_taxonomy_dictionary_command(), doctor(), _parse_hard_filters(), prepare_foodcom(), recommend_command(), smoke_embed(), smoke_llm(), structure_taxonomy_batch_command() (+11 more)

### Community 13 - "Serialization Utilities"
Cohesion: 0.15
Nodes (19): load_structured_taxonomy_items(), normalize_serializable_taxonomy(), _ordered_feature_keys(), Deterministic serialization for structured taxonomy items., Normalize a structured taxonomy into a deterministic serialization payload., Serialize taxonomy values into one flat deterministic text string., Summary for persisted serialized SID items., Load structured taxonomy items and serialize them deterministically. (+11 more)

### Community 14 - "MLX Runtime Checks"
Cohesion: 0.16
Nodes (17): smoke_mlx(), ensure_mlx_runtime_available(), get_runtime_environment_summary(), MLXRuntimeProbeResult, probe_mlx_runtime(), Helpers for probing MLX runtime availability safely., Probe MLX imports in a child process to avoid crashing the main process., High-level summary of the local execution environment. (+9 more)

### Community 15 - "Zero-Shot Rerank Tests"
Cohesion: 0.19
Nodes (13): _FakeEncoder, _FakeGenerator, _make_candidate(), _make_sketch(), test_parse_rerank_response_rejects_long_reasoning(), test_parse_rerank_response_rejects_wrong_selection_size(), test_run_bootstrap_rerank_injects_one_dynamic_example_and_runs_multiple_passes(), test_run_bootstrap_rerank_limits_structured_output_to_selection_size() (+5 more)

### Community 16 - "Demo Components"
Cohesion: 0.12
Nodes (7): App(), avgMscp(), buildLangHref(), escapeHtml(), JsonView(), MetricsStrip(), OverviewGrid()

### Community 17 - "Recommendation Stats"
Cohesion: 0.18
Nodes (15): _build_cooccurrence(), _build_popularity(), build_recommendation_stats(), _count_unique_pairs(), _load_interactions(), Offline recommendation statistics for Phase 1 recommendation support., Deterministic popularity and co-occurrence statistics., Summary for persisted recommendation statistics. (+7 more)

### Community 18 - "Brand Identity"
Cohesion: 0.18
Nodes (14): Three rounded cyan, violet, and green bars beneath the tagline that repeat the icon accent palette, Vertical cyan-to-violet-to-green line conveying alignment, centering, and ordered ranking, Halo and concentric rings around the center that imply semantic fields, reach, or graph neighborhoods, Violet -Rec suffix isolated inside the wordmark to foreground recommendation as the product function, Five colored circular nodes arranged around the hub like candidate recommendations in a graph, Rounded-square emblem containing a centered hub, vertical axis, zig-zag path, and graph-like recommendation nodes, Dark circular hub with an accent ring and white core that suggests a semantic decision nucleus, Bold white broken line forming a Z-like trajectory across the icon (+6 more)

### Community 19 - "Auto Refresh Tests"
Cohesion: 0.68
Nodes (11): _clean_env(), _commit_all(), _copy_graphify_runtime(), _init_repo(), _seed_repo(), test_graphify_auto_refresh_bootstrap_does_not_skip_first_doc_change(), test_graphify_auto_refresh_bootstrap_runs_code_refresh_for_first_code_change(), test_graphify_auto_refresh_runs_code_refresh_after_code_only_change() (+3 more)

### Community 20 - "Graphify Workflow Tests"
Cohesion: 0.39
Nodes (11): _clean_env(), _init_repo(), _seed_raw_corpus(), test_graphify_ci_candidate_is_candidate_only_even_when_staged_output_exists(), test_graphify_ci_candidate_writes_manual_note_when_no_staged_output(), test_graphify_prepare_corpus_script_copies_only_curated_inputs(), test_graphify_sync_staged_copies_verified_outputs(), test_graphify_sync_staged_requires_verify_marker() (+3 more)

### Community 21 - "Phase Executor Tests"
Cohesion: 0.4
Nodes (8): _load_execute_module(), test_build_preamble_keeps_git_ownership_in_executor(), test_check_blockers_exits_for_blocked_steps(), test_ensure_clean_worktree_exits_when_repo_is_dirty(), test_ensure_created_at_records_task_timestamp(), test_invoke_claude_writes_output_and_uses_expected_command(), test_load_guardrails_uses_repo_specific_documents(), _write_phase_index()

### Community 22 - "Taxonomy CLI Tests"
Cohesion: 0.2
Nodes (2): _EmptyTaxonomyGenerator, _FakeGenerator

### Community 23 - "Structure Taxonomy CLI"
Cohesion: 0.33
Nodes (6): _ProjectionGenerator, test_structure_taxonomy_batch_cli_can_include_evidence(), test_structure_taxonomy_batch_cli_writes_jsonl(), test_structure_taxonomy_item_cli_can_include_evidence(), test_structure_taxonomy_item_cli_prints_json(), _write_projection_inputs()

### Community 24 - "Mobile Demo UI"
Cohesion: 0.33
Nodes (9): Delivery results header for final grounded recommendations with compact supporting copy., In-card explanation chips and footer metadata exposing flavor tags, bootstrap score, and SID identifiers., Portrait mobile shell that stacks the recommendation workflow into a single narrow column with generous tap targets., Natural-language query text box for describing desired meal intent in free-form text., Horizontally scrollable pipeline stage carousel with compact cards and DELIVERY highlighted as the active step., Preference and constraint panel combining liked or disliked item signals, wrapped dietary chips, and a top-k slider., Preset scenario selector showing one highlighted card and secondary options as a lightweight mobile menu., Vertically stacked ranked recommendation cards with large hero panels, bold titles, and scroll-friendly spacing. (+1 more)

### Community 25 - "Compile Index CLI"
Cohesion: 0.43
Nodes (4): _FakeEncoder, test_compile_sid_index_cli_reports_missing_taxonomy_dictionary(), test_compile_sid_index_cli_writes_all_outputs(), _write_sid_inputs()

### Community 26 - "Graphify Producer Tests"
Cohesion: 0.71
Nodes (6): _clean_env(), _copy_script(), _init_repo(), test_graphify_full_refresh_produces_staged_outputs_with_doc_context(), test_graphify_full_refresh_reports_partial_state_on_semantic_failure(), _write_file()

### Community 27 - "Graphify Eval Scorecard"
Cohesion: 0.48
Nodes (6): _load_graphify_eval_module(), _run_graphify_eval(), test_graphify_eval_scorecard_cli_returns_nonzero_exit_code_on_failed_scorecard(), test_graphify_eval_scorecard_cli_returns_zero_exit_code_on_passing_scorecard(), test_graphify_eval_scorecard_fails_when_assistant_utility_regresses(), test_graphify_eval_scorecard_passes_when_all_three_axes_pass()

### Community 28 - "Neighbor Context CLI"
Cohesion: 0.4
Nodes (1): _FakeEncoder

### Community 29 - "Graph Quality Eval"
Cohesion: 0.6
Nodes (3): _load_graphify_eval_module(), test_graphify_eval_graph_quality_passes_for_full_refresh_fixture(), test_graphify_eval_graph_quality_rejects_code_only_fixture_for_full_refresh_expectation()

### Community 30 - "Graphify Evaluation Docs"
Cohesion: 0.6
Nodes (5): Graph Report Carries Design Context, Graph Report Fixture, Graphify Evaluation Runbook, raw/design Evidence Is Required for Why Answers, Verified Full Refresh Evaluation Gate

### Community 31 - "Explanation Eval Tests"
Cohesion: 0.83
Nodes (3): _load_graphify_eval_module(), test_graphify_eval_explanations_fail_when_why_answers_skip_required_sources(), test_graphify_eval_explanations_pass_for_evidence_backed_answers()

### Community 32 - "Prepare Foodcom CLI"
Cohesion: 1.0
Nodes (2): _recipe_row(), test_prepare_foodcom_cli_writes_processed_outputs()

## Knowledge Gaps
- **87 isolated node(s):** `Helpers for probing MLX runtime availability safely.`, `High-level summary of the local execution environment.`, `Result of a child-process MLX runtime probe.`, `Describe whether the current session matches the supported MLX environment.`, `Probe MLX imports in a child process and collect runtime metadata.` (+82 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Taxonomy CLI Tests`** (10 nodes): `_EmptyTaxonomyGenerator`, `.generate()`, `.__init__()`, `_FakeGenerator`, `.generate()`, `.__init__()`, `test_build_taxonomy_dictionary_cli_fails_for_empty_taxonomy()`, `test_build_taxonomy_dictionary_cli_reports_catalog_and_prompt_items()`, `test_build_taxonomy_dictionary_cli_writes_outputs()`, `test_cli_build_taxonomy_dictionary.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Neighbor Context CLI`** (5 nodes): `_FakeEncoder`, `.encode()`, `.__init__()`, `test_build_neighbor_context_cli_writes_outputs()`, `test_cli_build_neighbor_context.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Prepare Foodcom CLI`** (3 nodes): `_recipe_row()`, `test_prepare_foodcom_cli_writes_processed_outputs()`, `test_cli_prepare_foodcom.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SID compilation helpers.` connect `SID Request Types` to `Embedding Core Models`, `Taxonomy Projection`, `Taxonomy Generation LLM`, `Recommendation Pipeline`, `Neighbor Retrieval`, `Serialization Utilities`, `Recommendation Stats`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `MLXTextGenerator` connect `Taxonomy Generation LLM` to `SID Request Types`, `Embedding Core Models`, `Taxonomy Projection`, `Recommendation Pipeline`?**
  _High betweenness centrality (0.134) - this node is a cross-community bridge._
- **Why does `Settings` connect `Embedding Core Models` to `SID Request Types`, `Taxonomy Generation LLM`, `Recommendation Pipeline`, `CLI Entry Points`, `Compile Index CLI`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 85 inferred relationships involving `MLXTextGenerator` (e.g. with `_FakeTokenizer` and `_FakeTokenListTokenizer`) actually correct?**
  _`MLXTextGenerator` has 85 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `Settings` (e.g. with `_FakeEncoder` and `_FakeEncoder`) actually correct?**
  _`Settings` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 51 inferred relationships involving `MLXEmbeddingEncoder` (e.g. with `_FakeArray` and `Settings`) actually correct?**
  _`MLXEmbeddingEncoder` has 51 INFERRED edges - model-reasoned connections that need verification._
- **Are the 43 inferred relationships involving `InterestSketch` (e.g. with `TextGenerator` and `CandidateRationale`) actually correct?**
  _`InterestSketch` has 43 INFERRED edges - model-reasoned connections that need verification._