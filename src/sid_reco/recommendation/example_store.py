"""Dynamic few-shot example retrieval for Module 2.3."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from sid_reco.recommendation.types import InterestSketch
from sid_reco.sid.serialization import serialize_taxonomy_text
from sid_reco.taxonomy.item_projection import load_taxonomy_master_dictionary


class TextEncoder(Protocol):
    """Small protocol for few-shot example encoding."""

    def encode(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True, slots=True)
class FewShotExample:
    """One successful recommendation example used for dynamic prompting."""

    case_id: str
    summary: str
    taxonomy_values: Mapping[str, tuple[str, ...]]
    output_example: Mapping[str, object]


def load_fewshot_examples(casebank_path: Path) -> tuple[FewShotExample, ...]:
    """Load casebank examples from JSONL."""
    if not casebank_path.exists():
        raise FileNotFoundError(f"Missing few-shot casebank file: {casebank_path}")

    examples: list[FewShotExample] = []
    for line_number, raw_line in enumerate(
        casebank_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Few-shot casebank line {line_number} is not valid JSON.") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"Few-shot casebank line {line_number} must be a JSON object.")
        case_id = parsed.get("case_id")
        summary = parsed.get("summary")
        taxonomy_values = parsed.get("taxonomy_values")
        output_example = parsed.get("output_example")
        if (
            not isinstance(case_id, str)
            or not isinstance(summary, str)
            or not isinstance(taxonomy_values, dict)
            or not isinstance(output_example, dict)
        ):
            raise ValueError(f"Few-shot casebank line {line_number} has invalid required fields.")
        examples.append(
            FewShotExample(
                case_id=case_id,
                summary=summary.strip(),
                taxonomy_values={
                    str(key): tuple(str(value) for value in values)
                    for key, values in taxonomy_values.items()
                    if isinstance(values, list)
                },
                output_example=output_example,
            )
        )
    if not examples:
        raise ValueError(f"Few-shot casebank is empty: {casebank_path}")
    return tuple(examples)


def select_dynamic_fewshot_example(
    sketch: InterestSketch,
    *,
    casebank_path: Path,
    taxonomy_dictionary_path: Path,
    encoder: TextEncoder,
) -> FewShotExample:
    """Select the single most similar few-shot example for the current sketch."""
    taxonomy_dictionary = load_taxonomy_master_dictionary(taxonomy_dictionary_path)
    query_text = serialize_taxonomy_text(
        {key: list(values) for key, values in sketch.taxonomy_values.items()},
        feature_order=tuple(taxonomy_dictionary.keys()),
    )
    if not query_text:
        raise ValueError("Interest sketch did not produce a query for few-shot retrieval.")

    examples = load_fewshot_examples(casebank_path)
    example_texts = [
        serialize_taxonomy_text(
            {key: list(values) for key, values in example.taxonomy_values.items()},
            feature_order=tuple(taxonomy_dictionary.keys()),
        )
        for example in examples
    ]
    encoded = np.asarray(encoder.encode([query_text, *example_texts]), dtype=np.float32)
    normalized = _normalize_matrix(encoded)
    query_vector = normalized[0]
    example_vectors = normalized[1:]
    scores = example_vectors @ query_vector
    best_index = int(np.argmax(scores))
    return examples[best_index]


def _normalize_matrix(matrix: np.ndarray) -> np.ndarray:
    if matrix.ndim != 2:
        raise ValueError("Few-shot example encoder must return a 2D matrix.")
    row_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if np.any(row_norms == 0.0):
        raise ValueError("Few-shot example encoder returned a zero vector.")
    return np.asarray(matrix / row_norms, dtype=np.float32)
