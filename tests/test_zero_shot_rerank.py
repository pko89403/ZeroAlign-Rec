import json
from pathlib import Path

from sid_reco.recommendation import (
    InterestSketch,
    SemanticCandidate,
    parse_rerank_response,
    run_bootstrap_rerank,
)


class _FakeEncoder:
    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            if "italian" in text and "dinner" in text:
                vectors.append([1.0, 0.0, 0.0])
            elif "american" in text:
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.5, 0.5, 0.0])
        return vectors


class _FakeGenerator:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 256,
        temperature: float = 0.0,
        top_p: float = 1.0,
        verbose: bool = False,
    ) -> str:
        self.prompts.append(prompt)
        return json.dumps(
            {
                "ranked_candidate_indices": [1, 2],
                "candidate_rationales": [
                    {
                        "candidate_index": 1,
                        "reason": "Best semantic fit. Strong dinner alignment.",
                        "matched_preferences": ["italian", "dinner"],
                        "tradeoffs_or_caveats": [],
                    },
                    {
                        "candidate_index": 2,
                        "reason": "Still relevant. Slightly weaker fit.",
                        "matched_preferences": ["dinner"],
                        "tradeoffs_or_caveats": ["less_specific"],
                    },
                ],
            }
        )


class _TruncationProneGenerator:
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 256,
        temperature: float = 0.0,
        top_p: float = 1.0,
        verbose: bool = False,
    ) -> str:
        if (
            "Return exactly 3 ranked candidate_index values." not in prompt
            or "Provide candidate_rationales only for those ranked candidates." not in prompt
        ):
            return '{"candidate_rationales": ['

        return json.dumps(
            {
                "ranked_candidate_indices": [1, 2, 3],
                "candidate_rationales": [
                    {
                        "candidate_index": 1,
                        "reason": "Best semantic fit. Strong dinner alignment.",
                        "matched_preferences": ["italian", "dinner"],
                        "tradeoffs_or_caveats": [],
                    },
                    {
                        "candidate_index": 2,
                        "reason": "Still relevant. Slightly weaker fit.",
                        "matched_preferences": ["italian"],
                        "tradeoffs_or_caveats": ["less_specific"],
                    },
                    {
                        "candidate_index": 3,
                        "reason": "Useful backup option. Broader cuisine match.",
                        "matched_preferences": ["dinner"],
                        "tradeoffs_or_caveats": ["broader_match"],
                    },
                ],
            }
        )


class _TokenBudgetGenerator:
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 256,
        temperature: float = 0.0,
        top_p: float = 1.0,
        verbose: bool = False,
    ) -> str:
        if max_tokens < 512:
            return (
                '{"candidate_rationales": [{"candidate_index": 1, '
                '"matched_preferences": ["italian"], '
                '"reason": "Truncated response'
            )
        return json.dumps(
            {
                "ranked_candidate_indices": [1, 2, 3],
                "candidate_rationales": [
                    {
                        "candidate_index": 1,
                        "reason": "Best semantic fit. Strong dinner alignment.",
                        "matched_preferences": ["italian", "dinner"],
                        "tradeoffs_or_caveats": [],
                    },
                    {
                        "candidate_index": 2,
                        "reason": "Still relevant. Slightly weaker fit.",
                        "matched_preferences": ["italian"],
                        "tradeoffs_or_caveats": ["less_specific"],
                    },
                    {
                        "candidate_index": 3,
                        "reason": "Useful backup option. Broader cuisine match.",
                        "matched_preferences": ["dinner"],
                        "tradeoffs_or_caveats": ["broader_match"],
                    },
                ],
            }
        )


def _make_sketch() -> InterestSketch:
    return InterestSketch(
        summary="italian dinner",
        positive_facets=("italian", "dinner"),
        negative_facets=(),
        hard_filters={},
        ambiguity_notes=(),
        taxonomy_values={"course": ("dinner",), "cuisine": ("italian",)},
    )


def _make_candidate(
    *,
    faiss_idx: int,
    recipe_id: int,
    sid_string: str,
    score: float,
    cuisine: str,
    cooccurrence_with_history: int = 0,
) -> SemanticCandidate:
    return SemanticCandidate(
        faiss_idx=faiss_idx,
        recipe_id=recipe_id,
        sid_string=sid_string,
        sid_path=(faiss_idx,),
        score=score,
        serialized_text=f"course: dinner, cuisine: {cuisine}",
        taxonomy={"course": ("dinner",), "cuisine": (cuisine,)},
        popularity=2,
        cooccurrence_with_history=cooccurrence_with_history,
    )


def test_run_bootstrap_rerank_injects_one_dynamic_example_and_runs_multiple_passes(
    tmp_path: Path,
) -> None:
    taxonomy_path, casebank_path = _write_casebank_bundle(tmp_path)
    generator = _FakeGenerator()
    sketch = _make_sketch()
    candidates = (
        _make_candidate(
            faiss_idx=0,
            recipe_id=101,
            sid_string="<0>",
            score=0.99,
            cuisine="italian",
            cooccurrence_with_history=1,
        ),
        _make_candidate(
            faiss_idx=1,
            recipe_id=102,
            sid_string="<1>",
            score=0.75,
            cuisine="american",
        ),
    )

    result = run_bootstrap_rerank(
        sketch,
        candidates,
        casebank_path=casebank_path,
        taxonomy_dictionary_path=taxonomy_path,
        encoder=_FakeEncoder(),
        generator=generator,
        passes=3,
        seed=7,
    )

    assert result.example.case_id == "case-italian"
    assert len(result.passes) == 3
    assert all(
        pass_result.parsed_response.ranked_candidate_indices == (1, 2)
        for pass_result in result.passes
    )
    assert all("Few-shot example" in prompt for prompt in generator.prompts)


def test_run_bootstrap_rerank_limits_structured_output_to_selection_size(
    tmp_path: Path,
) -> None:
    taxonomy_path, casebank_path = _write_casebank_bundle(tmp_path)
    sketch = _make_sketch()
    candidates = tuple(
        _make_candidate(
            faiss_idx=index,
            recipe_id=200 + index,
            sid_string=f"<{index}>",
            score=0.9 - (index * 0.05),
            cuisine="italian" if index < 3 else "american",
        )
        for index in range(5)
    )

    result = run_bootstrap_rerank(
        sketch,
        candidates,
        casebank_path=casebank_path,
        taxonomy_dictionary_path=taxonomy_path,
        encoder=_FakeEncoder(),
        generator=_TruncationProneGenerator(),
        passes=1,
        selection_size=3,
    )

    assert result.passes[0].parsed_response.ranked_candidate_indices == (1, 2, 3)
    assert {item.candidate_index for item in result.passes[0].parsed_response.rationales} == {
        1,
        2,
        3,
    }


def test_run_bootstrap_rerank_uses_expanded_token_budget_for_structured_output(
    tmp_path: Path,
) -> None:
    taxonomy_path, casebank_path = _write_casebank_bundle(tmp_path)
    sketch = _make_sketch()
    candidates = tuple(
        _make_candidate(
            faiss_idx=index,
            recipe_id=300 + index,
            sid_string=f"<{index}>",
            score=0.9 - (index * 0.05),
            cuisine="italian" if index < 3 else "american",
        )
        for index in range(5)
    )

    result = run_bootstrap_rerank(
        sketch,
        candidates,
        casebank_path=casebank_path,
        taxonomy_dictionary_path=taxonomy_path,
        encoder=_FakeEncoder(),
        generator=_TokenBudgetGenerator(),
        passes=1,
        selection_size=3,
        max_tokens=256,
    )

    assert result.passes[0].parsed_response.ranked_candidate_indices == (1, 2, 3)


def test_parse_rerank_response_rejects_long_reasoning() -> None:
    raw_response = json.dumps(
        {
            "ranked_candidate_indices": [1],
            "candidate_rationales": [
                {
                    "candidate_index": 1,
                    "reason": "Sentence one. Sentence two. Sentence three.",
                    "matched_preferences": ["italian"],
                    "tradeoffs_or_caveats": [],
                }
            ],
        }
    )

    try:
        parse_rerank_response(raw_response, candidate_count=1)
    except ValueError as exc:
        assert "1-2 sentences" in str(exc)
    else:
        raise AssertionError("Expected parse_rerank_response to reject long reasoning.")


def test_parse_rerank_response_rejects_wrong_selection_size() -> None:
    raw_response = json.dumps(
        {
            "ranked_candidate_indices": [1, 2],
            "candidate_rationales": [
                {
                    "candidate_index": 1,
                    "reason": "Best semantic fit. Strong dinner alignment.",
                    "matched_preferences": ["italian"],
                    "tradeoffs_or_caveats": [],
                },
                {
                    "candidate_index": 2,
                    "reason": "Still relevant. Slightly weaker fit.",
                    "matched_preferences": ["dinner"],
                    "tradeoffs_or_caveats": ["less_specific"],
                },
            ],
        }
    )

    try:
        parse_rerank_response(raw_response, candidate_count=3, selection_size=3)
    except ValueError as exc:
        assert "exactly 3" in str(exc)
    else:
        raise AssertionError("Expected parse_rerank_response to reject a short ranking.")


def _write_casebank_bundle(tmp_path: Path) -> tuple[Path, Path]:
    taxonomy_path = tmp_path / "food_taxonomy_dictionary.json"
    casebank_path = tmp_path / "recommendation_casebank.jsonl"
    taxonomy_path.write_text(
        json.dumps(
            {
                "course": ["dinner"],
                "cuisine": ["american", "italian"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    casebank_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "case_id": "case-italian",
                        "summary": "italian dinner success",
                        "taxonomy_values": {
                            "course": ["dinner"],
                            "cuisine": ["italian"],
                        },
                        "output_example": {"ranked_candidate_indices": [1, 2]},
                    }
                ),
                json.dumps(
                    {
                        "case_id": "case-american",
                        "summary": "american dinner success",
                        "taxonomy_values": {
                            "course": ["dinner"],
                            "cuisine": ["american"],
                        },
                        "output_example": {"ranked_candidate_indices": [2, 1]},
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return taxonomy_path, casebank_path
