"""Module 2.4 CPU confidence aggregation for bootstrap rerank outputs."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from sid_reco.recommendation.semantic_search import SemanticCandidate
from sid_reco.recommendation.zero_shot_rerank import BootstrapRerankResult


@dataclass(frozen=True, slots=True)
class ConfidenceCandidate:
    """Aggregated confidence evidence for one candidate across rerank passes."""

    candidate: SemanticCandidate
    vote_count: int
    mscp: float
    average_rank: float
    rationale: str
    matched_preferences: tuple[str, ...]
    cautions: tuple[str, ...]
    supporting_passes: tuple[int, ...]
    confidence_band: str


@dataclass(slots=True)
class _MutableConfidenceAggregate:
    candidate: SemanticCandidate
    vote_count: int = 0
    rank_sum: int = 0
    supporting_passes: list[int] = field(default_factory=list)
    reason_counts: Counter[str] = field(default_factory=Counter)
    matched_preferences: set[str] = field(default_factory=set)
    cautions: set[str] = field(default_factory=set)


def compute_bootstrap_confidence(
    result: BootstrapRerankResult,
    *,
    selection_size: int = 3,
) -> tuple[ConfidenceCandidate, ...]:
    """Compute per-candidate MSCP and aggregate rationale evidence on CPU."""
    if selection_size < 1:
        raise ValueError("selection_size must be at least 1.")
    if not result.passes:
        raise ValueError("compute_bootstrap_confidence requires at least one rerank pass.")

    aggregates: dict[int, _MutableConfidenceAggregate] = {}
    for pass_number, pass_result in enumerate(result.passes, start=1):
        rationale_by_index = {
            rationale.candidate_index: rationale
            for rationale in pass_result.parsed_response.rationales
        }
        for rank, candidate_index in enumerate(
            pass_result.parsed_response.ranked_candidate_indices[:selection_size],
            start=1,
        ):
            candidate = pass_result.presented_candidates[candidate_index - 1]
            rationale = rationale_by_index[candidate_index]
            aggregate = aggregates.get(candidate.recipe_id)
            if aggregate is None:
                aggregate = _MutableConfidenceAggregate(candidate=candidate)
                aggregates[candidate.recipe_id] = aggregate
            aggregate.vote_count += 1
            aggregate.rank_sum += rank
            aggregate.supporting_passes.append(pass_number)
            aggregate.reason_counts[rationale.reason] += 1
            aggregate.matched_preferences.update(rationale.matched_preferences)
            aggregate.cautions.update(rationale.tradeoffs_or_caveats)

    total_passes = len(result.passes)
    confident_candidates = tuple(
        sorted(
            (
                ConfidenceCandidate(
                    candidate=aggregate.candidate,
                    vote_count=aggregate.vote_count,
                    mscp=aggregate.vote_count / total_passes,
                    average_rank=aggregate.rank_sum / aggregate.vote_count,
                    rationale=_select_representative_reason(aggregate.reason_counts),
                    matched_preferences=tuple(sorted(aggregate.matched_preferences)),
                    cautions=tuple(sorted(aggregate.cautions)),
                    supporting_passes=tuple(aggregate.supporting_passes),
                    confidence_band=_confidence_band(aggregate.vote_count / total_passes),
                )
                for aggregate in aggregates.values()
            ),
            key=lambda item: (
                -item.mscp,
                item.average_rank,
                -item.candidate.score,
                item.candidate.recipe_id,
            ),
        )
    )
    return confident_candidates


def summarize_confidence(
    confident_candidates: tuple[ConfidenceCandidate, ...],
    *,
    total_passes: int,
) -> str:
    """Create a compact confidence summary for final delivery."""
    if total_passes < 1:
        raise ValueError("total_passes must be at least 1.")
    if not confident_candidates:
        return "No grounded candidates survived confidence aggregation."

    top_candidate = confident_candidates[0]
    return (
        f"Top candidate support: {top_candidate.vote_count}/{total_passes} "
        f"passes (MSCP {top_candidate.mscp:.2f}, {top_candidate.confidence_band})."
    )


def _select_representative_reason(reason_counts: Counter[str]) -> str:
    ranked = sorted(
        reason_counts.items(),
        key=lambda item: (-item[1], len(item[0]), item[0]),
    )
    return ranked[0][0]


def _confidence_band(mscp: float) -> str:
    if mscp >= 0.8:
        return "high"
    if mscp >= 0.5:
        return "medium"
    return "low"
