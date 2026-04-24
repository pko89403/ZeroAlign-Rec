# Graph Report - Training-Free-SID-Reco-graphify-upstream-entrypoint  (2026-04-24)

## Corpus Check
- 64 files · ~42,894 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 875 nodes · 1946 edges · 30 communities detected
- Extraction: 57% EXTRACTED · 43% INFERRED · 0% AMBIGUOUS · INFERRED: 830 edges (avg confidence: 0.66)
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
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]

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
- `test_residual_kmeans_level_dataclass_is_usable_directly()` --calls--> `ResidualKMeansLevel`  [INFERRED]
  tests/test_sid_compiler.py → src/sid_reco/sid/compiler.py
- `test_parse_rerank_response_rejects_long_reasoning()` --calls--> `parse_rerank_response()`  [INFERRED]
  tests/test_zero_shot_rerank.py → src/sid_reco/recommendation/zero_shot_rerank.py
- `test_parse_rerank_response_rejects_wrong_selection_size()` --calls--> `parse_rerank_response()`  [INFERRED]
  tests/test_zero_shot_rerank.py → src/sid_reco/recommendation/zero_shot_rerank.py
- `AGENTS Schema Layer` --semantically_similar_to--> `CLAUDE Schema Layer`  [INFERRED] [semantically similar]
  AGENTS.md → CLAUDE.md
- `ZeroAlign-Rec English README` --semantically_similar_to--> `ZeroAlign-Rec Korean README`  [INFERRED] [semantically similar]
  README.md → README.ko.md

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

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (84): build_neighbor_context_command(), build_taxonomy_dictionary_command(), doctor(), _parse_hard_filters(), prepare_foodcom(), CLI entry points for local development., Run a single prompt against the configured local MLX LLM., Generate an embedding preview for one input string. (+76 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (83): QuerySID, Hierarchical SID assignment for one runtime query vector., compute_bootstrap_confidence(), _confidence_band(), ConfidenceCandidate, _MutableConfidenceAggregate, Module 2.4 CPU confidence aggregation for bootstrap rerank outputs., Create a compact confidence summary for final delivery. (+75 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (74): Normalize free text into snake_case., _to_snake_case(), build_item_projection_context(), build_item_projection_evidence(), build_item_projection_prompt(), build_retry_prompt(), build_self_refine_prompt(), _canonicalize_feature_value() (+66 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (57): build_bounded_taxonomy_payload(), build_taxonomy_dictionary(), build_taxonomy_dictionary_prompt(), _evenly_spaced_indices(), generate_taxonomy_dictionary(), load_taxonomy_items(), normalize_taxonomy_dictionary(), _parse_string_list() (+49 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (51): compile_sid_index_command(), ItemSID, Hierarchical SID assignment for one catalog item., Replay/debug metadata for one residual K-means level., Trained residual codebooks that define the SID coordinate space., ResidualKMeansLevel, TrainedResidualCodebooks, EmbeddedSIDItems (+43 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (42): _as_normalized_float32_matrix(), build_embedding_text(), build_faiss_index(), build_neighbor_context(), build_neighbor_context_manifest(), _compose_embedding_text(), detect_total_memory_bytes(), encode_catalog_with_adaptive_batches() (+34 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (41): _assign_to_centroids(), build_item_sids(), build_query_sid(), _canonicalize_clusters(), _centroids_close(), _fit_deterministic_kmeans(), _format_sid(), _initialize_centroids() (+33 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (37): apply_k_core_filter(), build_manifest(), build_recipe_stats(), build_temporal_splits(), DatasetSummary, _ensure_columns(), filter_positive_interactions(), load_raw_interactions() (+29 more)

### Community 8 - "Community 8"
Cohesion: 0.1
Nodes (32): ADR-001 Dev Environment Decision, Why the project standardizes on Apple Silicon + MLX, Why Food.com is reduced to compact implicit feedback, ADR-002 Food.com Preprocessing Policy, Why neighbor context uses exact cosine search with FAISS, ADR-003 Neighbor Context Policy, ADR-004 Taxonomy Dictionary Generation, Why taxonomy generation uses a local LLM and JSON-only output (+24 more)

### Community 9 - "Community 9"
Cohesion: 0.12
Nodes (29): Beyond Relevance Adaptive Exploration Framework, Bounded Taxonomy Dictionary Generation, Deterministic SID Artifact Pipeline, Food.com Dataset, Food Taxonomy Dictionary, Food.com 5-core Implicit Feedback Dataset, GRLM Reference Implementation, Retain Serialized Items and Embeddings (+21 more)

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (22): generate_interest_sketch(), generate_interest_sketch_with_mlx(), _normalize_flat_taxonomy_values(), _normalize_taxonomy_values(), parse_interest_sketch_response(), _parse_json_object(), _require_string(), _require_string_list() (+14 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (25): Desktop recommendation demo shell branded ZeroAlign-Rec with a clean editorial dashboard aesthetic., Brand header with ZeroAlign-Rec logo and phase subtitle, Green confidence badges use numeric scores to communicate calibrated trust for each recommendation., Delivery is the highlighted active stage, signaling that grounded final outputs are currently in focus., Korean desktop recipe recommendation demo screen, English-language copy paired with a visible KR toggle implies bilingual or locale-switchable presentation., Main grounded recommendation summary panel, Hard filter chips with active and inactive pill states (+17 more)

### Community 13 - "Community 13"
Cohesion: 0.15
Nodes (19): load_structured_taxonomy_items(), normalize_serializable_taxonomy(), _ordered_feature_keys(), Deterministic serialization for structured taxonomy items., Normalize a structured taxonomy into a deterministic serialization payload., Serialize taxonomy values into one flat deterministic text string., Summary for persisted serialized SID items., Load structured taxonomy items and serialize them deterministically. (+11 more)

### Community 14 - "Community 14"
Cohesion: 0.12
Nodes (7): App(), avgMscp(), buildLangHref(), escapeHtml(), JsonView(), MetricsStrip(), OverviewGrid()

### Community 15 - "Community 15"
Cohesion: 0.16
Nodes (17): smoke_mlx(), ensure_mlx_runtime_available(), get_runtime_environment_summary(), MLXRuntimeProbeResult, probe_mlx_runtime(), Helpers for probing MLX runtime availability safely., Probe MLX imports in a child process to avoid crashing the main process., High-level summary of the local execution environment. (+9 more)

### Community 16 - "Community 16"
Cohesion: 0.21
Nodes (12): _FakeEncoder, _FakeGenerator, _make_candidate(), _make_sketch(), test_parse_rerank_response_rejects_long_reasoning(), test_parse_rerank_response_rejects_wrong_selection_size(), test_run_bootstrap_rerank_injects_one_dynamic_example_and_runs_multiple_passes(), test_run_bootstrap_rerank_limits_structured_output_to_selection_size() (+4 more)

### Community 17 - "Community 17"
Cohesion: 0.19
Nodes (12): _load_id_map(), _load_serialized_items(), _normalize_query_matrix(), _passes_hard_filters(), search_semantic_candidates(), load_recommendation_stats_store(), _parse_double_nested_int_mapping(), _parse_nested_int_mapping() (+4 more)

### Community 18 - "Community 18"
Cohesion: 0.18
Nodes (14): Three rounded cyan, violet, and green bars beneath the tagline that repeat the icon accent palette, Vertical cyan-to-violet-to-green line conveying alignment, centering, and ordered ranking, Halo and concentric rings around the center that imply semantic fields, reach, or graph neighborhoods, Violet -Rec suffix isolated inside the wordmark to foreground recommendation as the product function, Five colored circular nodes arranged around the hub like candidate recommendations in a graph, Rounded-square emblem containing a centered hub, vertical axis, zig-zag path, and graph-like recommendation nodes, Dark circular hub with an accent ring and white core that suggests a semantic decision nucleus, Bold white broken line forming a Z-like trajectory across the icon (+6 more)

### Community 19 - "Community 19"
Cohesion: 0.4
Nodes (8): _load_execute_module(), test_build_preamble_keeps_git_ownership_in_executor(), test_check_blockers_exits_for_blocked_steps(), test_ensure_clean_worktree_exits_when_repo_is_dirty(), test_ensure_created_at_records_task_timestamp(), test_invoke_claude_writes_output_and_uses_expected_command(), test_load_guardrails_uses_repo_specific_documents(), _write_phase_index()

### Community 20 - "Community 20"
Cohesion: 0.2
Nodes (2): _EmptyTaxonomyGenerator, _FakeGenerator

### Community 21 - "Community 21"
Cohesion: 0.33
Nodes (6): _ProjectionGenerator, test_structure_taxonomy_batch_cli_can_include_evidence(), test_structure_taxonomy_batch_cli_writes_jsonl(), test_structure_taxonomy_item_cli_can_include_evidence(), test_structure_taxonomy_item_cli_prints_json(), _write_projection_inputs()

### Community 22 - "Community 22"
Cohesion: 0.33
Nodes (9): Delivery results header for final grounded recommendations with compact supporting copy., In-card explanation chips and footer metadata exposing flavor tags, bootstrap score, and SID identifiers., Portrait mobile shell that stacks the recommendation workflow into a single narrow column with generous tap targets., Natural-language query text box for describing desired meal intent in free-form text., Horizontally scrollable pipeline stage carousel with compact cards and DELIVERY highlighted as the active step., Preference and constraint panel combining liked or disliked item signals, wrapped dietary chips, and a top-k slider., Preset scenario selector showing one highlighted card and secondary options as a lightweight mobile menu., Vertically stacked ranked recommendation cards with large hero panels, bold titles, and scroll-friendly spacing. (+1 more)

### Community 23 - "Community 23"
Cohesion: 0.48
Nodes (6): _load_graphify_eval_module(), _run_graphify_eval(), test_graphify_eval_scorecard_cli_returns_nonzero_exit_code_on_failed_scorecard(), test_graphify_eval_scorecard_cli_returns_zero_exit_code_on_passing_scorecard(), test_graphify_eval_scorecard_fails_when_assistant_utility_regresses(), test_graphify_eval_scorecard_passes_when_all_three_axes_pass()

### Community 24 - "Community 24"
Cohesion: 0.43
Nodes (4): _FakeEncoder, test_compile_sid_index_cli_reports_missing_taxonomy_dictionary(), test_compile_sid_index_cli_writes_all_outputs(), _write_sid_inputs()

### Community 25 - "Community 25"
Cohesion: 0.4
Nodes (5): GroundingDecision, Module 2.4 SID-aware fallback mapping helpers., Resolved canonical identity for a recommendation candidate., Resolve a candidate through direct id_map lookup, then SID fallback., resolve_grounding()

### Community 26 - "Community 26"
Cohesion: 0.4
Nodes (1): _FakeEncoder

### Community 27 - "Community 27"
Cohesion: 0.6
Nodes (3): _load_graphify_eval_module(), test_graphify_eval_graph_quality_passes_for_document_context_fixture(), test_graphify_eval_rejects_code_only_for_doc_context()

### Community 28 - "Community 28"
Cohesion: 0.6
Nodes (5): Graph Report Carries Design Context, Graph Report Fixture, Graphify Evaluation Runbook, raw/design Evidence Is Required for Why Answers, Verified Full Refresh Evaluation Gate

### Community 29 - "Community 29"
Cohesion: 0.83
Nodes (3): _load_graphify_eval_module(), test_graphify_eval_explanations_fail_when_why_answers_skip_required_sources(), test_graphify_eval_explanations_pass_for_evidence_backed_answers()

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (2): _recipe_row(), test_prepare_foodcom_cli_writes_processed_outputs()

## Knowledge Gaps
- **87 isolated node(s):** `Helpers for probing MLX runtime availability safely.`, `High-level summary of the local execution environment.`, `Result of a child-process MLX runtime probe.`, `Describe whether the current session matches the supported MLX environment.`, `Probe MLX imports in a child process and collect runtime metadata.` (+82 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 20`** (10 nodes): `_EmptyTaxonomyGenerator`, `.generate()`, `.__init__()`, `_FakeGenerator`, `.generate()`, `.__init__()`, `test_build_taxonomy_dictionary_cli_fails_for_empty_taxonomy()`, `test_build_taxonomy_dictionary_cli_reports_catalog_and_prompt_items()`, `test_build_taxonomy_dictionary_cli_writes_outputs()`, `test_cli_build_taxonomy_dictionary.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (5 nodes): `_FakeEncoder`, `.encode()`, `.__init__()`, `test_build_neighbor_context_cli_writes_outputs()`, `test_cli_build_neighbor_context.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (3 nodes): `_recipe_row()`, `test_prepare_foodcom_cli_writes_processed_outputs()`, `test_cli_prepare_foodcom.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SID compilation helpers.` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 13`, `Community 17`, `Community 25`?**
  _High betweenness centrality (0.146) - this node is a cross-community bridge._
- **Why does `MLXTextGenerator` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 0` to `Community 24`, `Community 1`, `Community 3`, `Community 4`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 85 inferred relationships involving `MLXTextGenerator` (e.g. with `_FakeTokenizer` and `_FakeTokenListTokenizer`) actually correct?**
  _`MLXTextGenerator` has 85 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `Settings` (e.g. with `_FakeEncoder` and `_FakeEncoder`) actually correct?**
  _`Settings` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 51 inferred relationships involving `MLXEmbeddingEncoder` (e.g. with `_FakeArray` and `Settings`) actually correct?**
  _`MLXEmbeddingEncoder` has 51 INFERRED edges - model-reasoned connections that need verification._
- **Are the 43 inferred relationships involving `InterestSketch` (e.g. with `TextGenerator` and `CandidateRationale`) actually correct?**
  _`InterestSketch` has 43 INFERRED edges - model-reasoned connections that need verification._