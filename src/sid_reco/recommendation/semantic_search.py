"""Module 2.2 taxonomy-aligned semantic retrieval and filtering."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import faiss  # type: ignore[import-untyped]
import numpy as np

from sid_reco.recommendation.stats_store import load_recommendation_stats_store
from sid_reco.recommendation.types import InterestSketch, RecommendationRequest
from sid_reco.sid.compiler import QuerySID, build_query_sid, load_codebooks
from sid_reco.sid.serialization import serialize_taxonomy_text
from sid_reco.taxonomy.item_projection import load_taxonomy_master_dictionary


class TextEncoder(Protocol):
    """Small protocol for semantic query encoding."""

    def encode(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True, slots=True)
class SemanticCandidate:
    """Candidate returned from semantic retrieval."""

    faiss_idx: int
    recipe_id: int
    sid_string: str
    sid_path: tuple[int, ...]
    score: float
    serialized_text: str
    taxonomy: Mapping[str, tuple[str, ...]]
    popularity: int
    cooccurrence_with_history: int


@dataclass(frozen=True, slots=True)
class DroppedCandidate:
    """Candidate dropped during CPU hard filtering."""

    recipe_id: int
    reason: str


@dataclass(frozen=True, slots=True)
class SemanticSearchResult:
    """Semantic retrieval output ready for Module 2.3."""

    query_text: str
    query_sid: QuerySID
    candidates: tuple[SemanticCandidate, ...]
    dropped_candidates: tuple[DroppedCandidate, ...]
    retrieved_count: int
    survivor_count: int
    low_coverage: bool


def search_semantic_candidates(
    request: RecommendationRequest,
    sketch: InterestSketch,
    *,
    sid_index_dir: Path,
    taxonomy_dictionary_path: Path,
    stats_path: Path,
    encoder: TextEncoder,
    retrieval_k: int = 100,
    survivor_k: int = 30,
) -> SemanticSearchResult:
    """Search FAISS with a taxonomy-guided query and apply CPU hard filtering."""
    if retrieval_k < 1:
        raise ValueError("retrieval_k must be at least 1.")
    if survivor_k < 1:
        raise ValueError("survivor_k must be at least 1.")

    taxonomy_dictionary = load_taxonomy_master_dictionary(taxonomy_dictionary_path)
    query_text = serialize_taxonomy_text(
        {key: list(values) for key, values in sketch.taxonomy_values.items()},
        feature_order=tuple(taxonomy_dictionary.keys()),
    )
    if not query_text:
        raise ValueError("Interest sketch did not produce a taxonomy-aligned retrieval query.")

    codebooks = load_codebooks(sid_index_dir / "residual_codebooks.npz")

    raw_vector = np.asarray(encoder.encode([query_text]), dtype=np.float32)
    if raw_vector.ndim != 2 or raw_vector.shape[0] != 1:
        raise ValueError("Semantic search encoder must return exactly one query vector.")

    query_matrix = _normalize_query_matrix(raw_vector)
    query_sid = build_query_sid(raw_vector[0], codebooks=codebooks)

    index = faiss.read_index(str(sid_index_dir / "item_index.faiss"))
    score_matrix, idx_matrix = index.search(query_matrix, retrieval_k)

    id_map = _load_id_map(sid_index_dir / "id_map.jsonl")
    serialized_items = _load_serialized_items(sid_index_dir / "serialized_items.jsonl")
    stats_store = load_recommendation_stats_store(stats_path)

    survivors: list[SemanticCandidate] = []
    dropped: list[DroppedCandidate] = []
    for raw_score, raw_idx in zip(score_matrix[0], idx_matrix[0], strict=True):
        faiss_idx = int(raw_idx)
        if faiss_idx < 0:
            continue
        mapped = id_map[faiss_idx]
        serialized_item = serialized_items[mapped["recipe_id"]]
        if not _passes_hard_filters(serialized_item["taxonomy"], request.hard_filters):
            dropped.append(
                DroppedCandidate(
                    recipe_id=mapped["recipe_id"],
                    reason="failed_hard_filters",
                )
            )
            continue
        survivors.append(
            SemanticCandidate(
                faiss_idx=faiss_idx,
                recipe_id=mapped["recipe_id"],
                sid_string=mapped["sid_string"],
                sid_path=mapped["sid_path"],
                score=float(raw_score),
                serialized_text=serialized_item["serialized_text"],
                taxonomy=serialized_item["taxonomy"],
                popularity=stats_store.popularity_for(mapped["recipe_id"]),
                cooccurrence_with_history=stats_store.cooccurrence_with_history(
                    mapped["recipe_id"],
                    request.liked_item_ids,
                ),
            )
        )

    final_candidates = tuple(survivors[:survivor_k])
    return SemanticSearchResult(
        query_text=query_text,
        query_sid=query_sid,
        candidates=final_candidates,
        dropped_candidates=tuple(dropped),
        retrieved_count=sum(1 for value in idx_matrix[0] if int(value) >= 0),
        survivor_count=len(final_candidates),
        low_coverage=len(final_candidates) < survivor_k,
    )


def _normalize_query_matrix(matrix: np.ndarray) -> np.ndarray:
    row_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if float(row_norms[0][0]) == 0.0:
        raise ValueError("Semantic search query vector must be non-zero.")
    return np.asarray(matrix / row_norms, dtype=np.float32)


def _load_id_map(id_map_path: Path) -> list[dict[str, Any]]:
    if not id_map_path.exists():
        raise FileNotFoundError(f"Missing SID id map file: {id_map_path}")
    entries: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(
        id_map_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"SID id map line {line_number} is not valid JSON.") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"SID id map line {line_number} must be a JSON object.")
        faiss_idx = parsed.get("faiss_idx")
        recipe_id = parsed.get("recipe_id")
        sid_string = parsed.get("sid_string")
        sid_path_raw = parsed.get("sid_path")
        if (
            not isinstance(faiss_idx, int)
            or not isinstance(recipe_id, int)
            or not isinstance(sid_string, str)
            or not isinstance(sid_path_raw, list)
            or not all(isinstance(value, int) for value in sid_path_raw)
        ):
            raise ValueError(f"SID id map line {line_number} has invalid required fields.")
        expected_sid_string = "-".join(f"<{int(value)}>" for value in sid_path_raw)
        if expected_sid_string != sid_string:
            raise ValueError(
                f"SID id map line {line_number} has inconsistent sid_path and sid_string."
            )
        entries.append(
            {
                "faiss_idx": faiss_idx,
                "recipe_id": recipe_id,
                "sid_string": sid_string,
                "sid_path": tuple(int(value) for value in sid_path_raw),
            }
        )
    entries.sort(key=lambda entry: int(entry["faiss_idx"]))
    return entries


def _load_serialized_items(serialized_path: Path) -> dict[int, dict[str, Any]]:
    if not serialized_path.exists():
        raise FileNotFoundError(f"Missing serialized items file: {serialized_path}")
    items: dict[int, dict[str, Any]] = {}
    for line_number, raw_line in enumerate(
        serialized_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Serialized items line {line_number} is not valid JSON.") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"Serialized items line {line_number} must be a JSON object.")
        recipe_id = parsed.get("recipe_id")
        serialized_text = parsed.get("serialized_text")
        taxonomy = parsed.get("taxonomy")
        if (
            not isinstance(recipe_id, int)
            or not isinstance(serialized_text, str)
            or not isinstance(taxonomy, dict)
        ):
            raise ValueError(f"Serialized items line {line_number} has invalid required fields.")
        items[recipe_id] = {
            "serialized_text": serialized_text,
            "taxonomy": {
                str(key): tuple(str(value) for value in values)
                for key, values in taxonomy.items()
                if isinstance(values, list)
            },
        }
    return items


def _passes_hard_filters(
    candidate_taxonomy: Mapping[str, tuple[str, ...]],
    hard_filters: Mapping[str, tuple[str, ...]],
) -> bool:
    for key, required_values in hard_filters.items():
        candidate_values = set(candidate_taxonomy.get(key, ()))
        if not set(required_values).issubset(candidate_values):
            return False
    return True
