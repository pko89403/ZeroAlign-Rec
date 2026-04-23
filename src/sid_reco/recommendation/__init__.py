"""Recommendation module contracts and Module 2.1 helpers."""

from sid_reco.recommendation.confidence import (
    ConfidenceCandidate,
    compute_bootstrap_confidence,
    summarize_confidence,
)
from sid_reco.recommendation.elastic_mapping import GroundingDecision, resolve_grounding
from sid_reco.recommendation.example_store import (
    FewShotExample,
    load_fewshot_examples,
    select_dynamic_fewshot_example,
)
from sid_reco.recommendation.grounding import ground_recommended_items
from sid_reco.recommendation.interest_sketch import (
    generate_interest_sketch,
    generate_interest_sketch_with_mlx,
    parse_interest_sketch_response,
)
from sid_reco.recommendation.pipeline import recommend, recommend_with_mlx
from sid_reco.recommendation.prompting import (
    INTEREST_SKETCH_SYSTEM_PROMPT,
    InterestSketchPromptBundle,
    build_interest_sketch_prompt,
)
from sid_reco.recommendation.semantic_search import (
    DroppedCandidate,
    SemanticCandidate,
    SemanticSearchResult,
    search_semantic_candidates,
)
from sid_reco.recommendation.stats_store import (
    RecommendationStatsStore,
    load_recommendation_stats_store,
)
from sid_reco.recommendation.types import (
    InterestSketch,
    RecommendationRequest,
    RecommendationResponse,
    RecommendedItem,
    normalize_recommendation_request,
)
from sid_reco.recommendation.zero_shot_rerank import (
    BootstrapRerankPass,
    BootstrapRerankResult,
    CandidateRationale,
    ParsedRerankResponse,
    parse_rerank_response,
    run_bootstrap_rerank,
)
from sid_reco.sid.compiler import QuerySID

__all__ = [
    "BootstrapRerankPass",
    "BootstrapRerankResult",
    "CandidateRationale",
    "ConfidenceCandidate",
    "FewShotExample",
    "GroundingDecision",
    "INTEREST_SKETCH_SYSTEM_PROMPT",
    "InterestSketch",
    "InterestSketchPromptBundle",
    "DroppedCandidate",
    "ParsedRerankResponse",
    "QuerySID",
    "RecommendedItem",
    "RecommendationStatsStore",
    "RecommendationRequest",
    "RecommendationResponse",
    "SemanticCandidate",
    "SemanticSearchResult",
    "build_interest_sketch_prompt",
    "compute_bootstrap_confidence",
    "generate_interest_sketch",
    "generate_interest_sketch_with_mlx",
    "ground_recommended_items",
    "load_fewshot_examples",
    "load_recommendation_stats_store",
    "normalize_recommendation_request",
    "parse_interest_sketch_response",
    "parse_rerank_response",
    "recommend",
    "recommend_with_mlx",
    "resolve_grounding",
    "run_bootstrap_rerank",
    "search_semantic_candidates",
    "select_dynamic_fewshot_example",
    "summarize_confidence",
]
