"""End-to-end recommendation orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from sid_reco.config import DEFAULT_LLM_MAX_TOKENS, Settings
from sid_reco.embedding import MLXEmbeddingEncoder
from sid_reco.llm import MLXTextGenerator
from sid_reco.recommendation.confidence import (
    compute_bootstrap_confidence,
    summarize_confidence,
)
from sid_reco.recommendation.grounding import ground_recommended_items
from sid_reco.recommendation.interest_sketch import generate_interest_sketch
from sid_reco.recommendation.semantic_search import (
    SemanticSearchResult,
    search_semantic_candidates,
)
from sid_reco.recommendation.types import (
    RecommendationResponse,
    normalize_recommendation_request,
)
from sid_reco.recommendation.zero_shot_rerank import (
    BootstrapRerankResult,
    run_bootstrap_rerank,
)


class TextGenerator(Protocol):
    """Shared protocol for recommendation generation steps."""

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = DEFAULT_LLM_MAX_TOKENS,
        temperature: float = 0.0,
        top_p: float = 1.0,
        verbose: bool = False,
    ) -> str: ...


class TextEncoder(Protocol):
    """Shared protocol for recommendation embedding steps."""

    def encode(self, texts: list[str]) -> list[list[float]]: ...


def recommend(
    *,
    sid_index_dir: Path,
    taxonomy_dictionary_path: Path,
    stats_store_path: Path,
    fewshot_store_path: Path,
    catalog_path: Path,
    generator: TextGenerator,
    encoder: TextEncoder,
    query: str | None = None,
    liked_item_ids: tuple[int, ...] | list[int] = (),
    disliked_item_ids: tuple[int, ...] | list[int] = (),
    hard_filters: Mapping[str, tuple[str, ...] | list[str] | str] | None = None,
    top_k: int = 3,
    rerank_passes: int = 3,
    retrieval_k: int = 100,
    survivor_k: int = 30,
    max_tokens: int = DEFAULT_LLM_MAX_TOKENS,
) -> RecommendationResponse:
    """Run the full training-free recommendation pipeline."""
    request = normalize_recommendation_request(
        query=query,
        liked_item_ids=liked_item_ids,
        disliked_item_ids=disliked_item_ids,
        hard_filters=hard_filters,
        top_k=top_k,
    )
    sketch = generate_interest_sketch(
        request,
        taxonomy_dictionary_path=taxonomy_dictionary_path,
        generator=generator,
        max_tokens=max_tokens,
    )
    search_result = search_semantic_candidates(
        request,
        sketch,
        sid_index_dir=sid_index_dir,
        taxonomy_dictionary_path=taxonomy_dictionary_path,
        stats_path=stats_store_path,
        encoder=encoder,
        retrieval_k=retrieval_k,
        survivor_k=survivor_k,
    )
    if not search_result.candidates:
        raise ValueError("No candidates survived semantic retrieval and hard filtering.")

    rerank_result = run_bootstrap_rerank(
        sketch,
        search_result.candidates,
        casebank_path=fewshot_store_path,
        taxonomy_dictionary_path=taxonomy_dictionary_path,
        encoder=encoder,
        generator=generator,
        passes=rerank_passes,
        selection_size=request.top_k,
        max_tokens=max_tokens,
    )
    confident_candidates = compute_bootstrap_confidence(
        rerank_result,
        selection_size=request.top_k,
    )
    if not confident_candidates:
        raise ValueError("Bootstrap reranking did not yield any confident candidates.")

    items = ground_recommended_items(
        confident_candidates,
        sid_index_dir=sid_index_dir,
        catalog_path=catalog_path,
        top_k=request.top_k,
    )
    selected_lookup = {
        candidate.recipe_id: index
        for index, candidate in enumerate(search_result.candidates, start=1)
    }
    selected_candidate_indices = tuple(
        selected_lookup[item.candidate.recipe_id]
        for item in confident_candidates[: request.top_k]
        if item.candidate.recipe_id in selected_lookup
    )
    return RecommendationResponse(
        sketch=sketch,
        items=items,
        rerank_summary=_build_rerank_summary(search_result, rerank_result),
        confidence_summary=summarize_confidence(
            confident_candidates,
            total_passes=len(rerank_result.passes),
        ),
        selected_candidate_indices=selected_candidate_indices,
        query_sid=search_result.query_sid,
    )


def recommend_with_mlx(
    *,
    sid_index_dir: Path,
    taxonomy_dictionary_path: Path,
    stats_store_path: Path,
    fewshot_store_path: Path,
    catalog_path: Path,
    query: str | None = None,
    liked_item_ids: tuple[int, ...] | list[int] = (),
    disliked_item_ids: tuple[int, ...] | list[int] = (),
    hard_filters: Mapping[str, tuple[str, ...] | list[str] | str] | None = None,
    top_k: int = 3,
    rerank_passes: int = 3,
    retrieval_k: int = 100,
    survivor_k: int = 30,
    settings: Settings | None = None,
) -> RecommendationResponse:
    """Run the recommendation pipeline with configured local MLX backends."""
    resolved_settings = settings or Settings.from_env()
    return recommend(
        sid_index_dir=sid_index_dir,
        taxonomy_dictionary_path=taxonomy_dictionary_path,
        stats_store_path=stats_store_path,
        fewshot_store_path=fewshot_store_path,
        catalog_path=catalog_path,
        generator=MLXTextGenerator.from_settings(resolved_settings),
        encoder=MLXEmbeddingEncoder.from_settings(resolved_settings),
        query=query,
        liked_item_ids=liked_item_ids,
        disliked_item_ids=disliked_item_ids,
        hard_filters=hard_filters,
        top_k=top_k,
        rerank_passes=rerank_passes,
        retrieval_k=retrieval_k,
        survivor_k=survivor_k,
        max_tokens=resolved_settings.llm_max_tokens,
    )


def _build_rerank_summary(
    search_result: SemanticSearchResult,
    rerank_result: BootstrapRerankResult,
) -> str:
    retrieved_count = search_result.retrieved_count
    survivor_count = search_result.survivor_count
    low_coverage = search_result.low_coverage
    example = rerank_result.example.case_id
    pass_count = len(rerank_result.passes)
    low_coverage_note = " low_coverage=true." if low_coverage else ""
    return (
        f"Retrieved {retrieved_count} items, kept {survivor_count} candidates, "
        f"reranked across {pass_count} passes using example {example}."
        f"{low_coverage_note}"
    )
