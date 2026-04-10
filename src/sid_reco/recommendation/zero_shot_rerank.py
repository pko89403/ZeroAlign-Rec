"""Module 2.3 resource-optimized zero-shot reranking."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from sid_reco.config import DEFAULT_LLM_MAX_TOKENS
from sid_reco.recommendation.example_store import (
    FewShotExample,
    TextEncoder,
    select_dynamic_fewshot_example,
)
from sid_reco.recommendation.semantic_search import SemanticCandidate
from sid_reco.recommendation.types import InterestSketch


class TextGenerator(Protocol):
    """Small protocol for rerank prompt generation."""

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


RERANK_SYSTEM_PROMPT = (
    "You are an explainable zero-shot reranker. Return only valid JSON. "
    "Never generate item names in the ranking field; rank only by candidate indices."
)
_MIN_RERANK_MAX_TOKENS = DEFAULT_LLM_MAX_TOKENS


@dataclass(frozen=True, slots=True)
class CandidateRationale:
    """Structured rationale for one ranked candidate."""

    candidate_index: int
    reason: str
    matched_preferences: tuple[str, ...]
    tradeoffs_or_caveats: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ParsedRerankResponse:
    """Parsed structured rerank output."""

    ranked_candidate_indices: tuple[int, ...]
    rationales: tuple[CandidateRationale, ...]


@dataclass(frozen=True, slots=True)
class BootstrapRerankPass:
    """One order-perturbed rerank pass."""

    presented_candidates: tuple[SemanticCandidate, ...]
    raw_response: str
    parsed_response: ParsedRerankResponse


@dataclass(frozen=True, slots=True)
class BootstrapRerankResult:
    """All rerank passes plus the chosen dynamic few-shot example."""

    example: FewShotExample
    passes: tuple[BootstrapRerankPass, ...]


def run_bootstrap_rerank(
    sketch: InterestSketch,
    candidates: tuple[SemanticCandidate, ...],
    *,
    casebank_path: Path,
    taxonomy_dictionary_path: Path,
    encoder: TextEncoder,
    generator: TextGenerator,
    passes: int = 3,
    seed: int = 0,
    selection_size: int = 3,
    max_tokens: int = DEFAULT_LLM_MAX_TOKENS,
) -> BootstrapRerankResult:
    """Run repeated order-perturbed rerank passes with one dynamic few-shot example."""
    if passes < 1:
        raise ValueError("passes must be at least 1.")
    if selection_size < 1:
        raise ValueError("selection_size must be at least 1.")
    if not candidates:
        raise ValueError("run_bootstrap_rerank requires at least one candidate.")

    example = select_dynamic_fewshot_example(
        sketch,
        casebank_path=casebank_path,
        taxonomy_dictionary_path=taxonomy_dictionary_path,
        encoder=encoder,
    )
    capped_selection_size = min(selection_size, len(candidates))
    generation_max_tokens = max(max_tokens, _MIN_RERANK_MAX_TOKENS)
    pass_results: list[BootstrapRerankPass] = []
    for pass_index in range(passes):
        presented_candidates = list(candidates)
        random.Random(seed + pass_index).shuffle(presented_candidates)
        prompt = _build_rerank_prompt(
            sketch,
            tuple(presented_candidates),
            example=example,
            selection_size=capped_selection_size,
        )
        raw_response = generator.generate(
            prompt,
            system_prompt=RERANK_SYSTEM_PROMPT,
            max_tokens=generation_max_tokens,
            temperature=0.0,
            top_p=1.0,
        )
        parsed_response = parse_rerank_response(
            raw_response,
            candidate_count=len(presented_candidates),
            selection_size=capped_selection_size,
        )
        pass_results.append(
            BootstrapRerankPass(
                presented_candidates=tuple(presented_candidates),
                raw_response=raw_response,
                parsed_response=parsed_response,
            )
        )
    return BootstrapRerankResult(example=example, passes=tuple(pass_results))


def parse_rerank_response(
    raw_response: str,
    *,
    candidate_count: int,
    selection_size: int | None = None,
) -> ParsedRerankResponse:
    """Parse a structured candidate-index rerank response."""
    payload = _parse_json_object(raw_response)
    ranked_indices = payload.get("ranked_candidate_indices")
    rationales = payload.get("candidate_rationales")
    if not isinstance(ranked_indices, list) or not all(
        isinstance(value, int) for value in ranked_indices
    ):
        raise ValueError(
            "Rerank response must include ranked_candidate_indices as an array of integers."
        )
    if not isinstance(rationales, list):
        raise ValueError("Rerank response must include candidate_rationales as an array.")

    normalized_indices = tuple(ranked_indices)
    if selection_size is not None and len(normalized_indices) != selection_size:
        raise ValueError(
            f"Rerank response must include exactly {selection_size} ranked candidate indices."
        )
    if len(set(normalized_indices)) != len(normalized_indices):
        raise ValueError("Rerank response candidate indices must be unique.")
    if not all(1 <= value <= candidate_count for value in normalized_indices):
        raise ValueError("Rerank response candidate indices are out of range.")

    parsed_rationales = tuple(
        _parse_candidate_rationale(item, candidate_count) for item in rationales
    )
    rationale_indices = {item.candidate_index for item in parsed_rationales}
    missing = [value for value in normalized_indices if value not in rationale_indices]
    if missing:
        raise ValueError(
            f"Rerank response is missing rationale entries for candidate indices: {missing}"
        )
    return ParsedRerankResponse(
        ranked_candidate_indices=normalized_indices,
        rationales=parsed_rationales,
    )


def _build_rerank_prompt(
    sketch: InterestSketch,
    candidates: tuple[SemanticCandidate, ...],
    *,
    example: FewShotExample,
    selection_size: int,
) -> str:
    candidate_payload = [
        {
            "candidate_index": index,
            "recipe_id": candidate.recipe_id,
            "sid_string": candidate.sid_string,
            "serialized_text": candidate.serialized_text,
            "taxonomy": {key: list(values) for key, values in candidate.taxonomy.items()},
            "popularity": candidate.popularity,
            "cooccurrence_with_history": candidate.cooccurrence_with_history,
        }
        for index, candidate in enumerate(candidates, start=1)
    ]
    ranked_indices_example = list(range(1, selection_size + 1))
    output_schema = {
        "ranked_candidate_indices": ranked_indices_example,
        "candidate_rationales": [
            {
                "candidate_index": 1,
                "reason": "1-2 short sentences.",
                "matched_preferences": ["taxonomy_value"],
                "tradeoffs_or_caveats": ["short note"],
            }
        ],
    }
    sketch_payload = json.dumps(
        _interest_sketch_payload(sketch),
        ensure_ascii=False,
        sort_keys=True,
    )
    example_payload = json.dumps(
        _fewshot_payload(example),
        ensure_ascii=False,
        sort_keys=True,
    )
    candidate_payload_json = json.dumps(
        candidate_payload,
        ensure_ascii=False,
        sort_keys=True,
    )
    output_schema_json = json.dumps(
        output_schema,
        ensure_ascii=False,
        sort_keys=True,
    )
    return "\n".join(
        [
            "Rerank the provided candidates for this interest sketch.",
            "Return JSON only.",
            "The final ranking must use candidate_index values only.",
            f"Return exactly {selection_size} ranked candidate_index values.",
            "Provide candidate_rationales only for those ranked candidates.",
            "Do not rank or explain unselected candidates.",
            "Each reason must be 1-2 short sentences.",
            f"Interest sketch:\n{sketch_payload}",
            f"Few-shot example:\n{example_payload}",
            f"Candidates:\n{candidate_payload_json}",
            f"Output JSON shape:\n{output_schema_json}",
        ]
    )


def _parse_json_object(raw_response: str) -> dict[str, object]:
    stripped = raw_response.strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Rerank response must contain a JSON object.")
    try:
        payload = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError("Rerank response did not contain valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Rerank response must be a JSON object.")
    return payload


def _parse_candidate_rationale(payload: object, candidate_count: int) -> CandidateRationale:
    if not isinstance(payload, dict):
        raise ValueError("Each rerank rationale entry must be a JSON object.")
    candidate_index = payload.get("candidate_index")
    reason = payload.get("reason")
    matched_preferences = payload.get("matched_preferences")
    tradeoffs = payload.get("tradeoffs_or_caveats")
    if not isinstance(candidate_index, int) or not 1 <= candidate_index <= candidate_count:
        raise ValueError("Rerank rationale candidate_index is out of range.")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Rerank rationale reason must be a non-empty string.")
    if not isinstance(matched_preferences, list) or not all(
        isinstance(item, str) for item in matched_preferences
    ):
        raise ValueError("Rerank rationale matched_preferences must be an array of strings.")
    if not isinstance(tradeoffs, list) or not all(isinstance(item, str) for item in tradeoffs):
        raise ValueError("Rerank rationale tradeoffs_or_caveats must be an array of strings.")
    if _sentence_count(reason) > 2:
        raise ValueError("Rerank rationale reason must be limited to 1-2 sentences.")
    return CandidateRationale(
        candidate_index=candidate_index,
        reason=reason.strip(),
        matched_preferences=tuple(
            sorted(item.strip() for item in matched_preferences if item.strip())
        ),
        tradeoffs_or_caveats=tuple(sorted(item.strip() for item in tradeoffs if item.strip())),
    )


def _interest_sketch_payload(sketch: InterestSketch) -> dict[str, object]:
    return {
        "summary": sketch.summary,
        "positive_facets": list(sketch.positive_facets),
        "negative_facets": list(sketch.negative_facets),
        "hard_filters": {key: list(values) for key, values in sketch.hard_filters.items()},
        "ambiguity_notes": list(sketch.ambiguity_notes),
        "taxonomy_values": {key: list(values) for key, values in sketch.taxonomy_values.items()},
    }


def _fewshot_payload(example: FewShotExample) -> dict[str, object]:
    return {
        "case_id": example.case_id,
        "summary": example.summary,
        "taxonomy_values": {key: list(values) for key, values in example.taxonomy_values.items()},
        "output_example": example.output_example,
    }


def _sentence_count(text: str) -> int:
    count = sum(text.count(marker) for marker in (".", "!", "?"))
    return count if count > 0 else 1
