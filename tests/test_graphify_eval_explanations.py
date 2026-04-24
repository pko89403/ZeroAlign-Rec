from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_FIXTURES = ROOT / "tests" / "fixtures" / "graphify_eval"
SCRIPT_PATH = ROOT / "scripts" / "graphify_eval.py"


def _load_graphify_eval_module():
    spec = importlib.util.spec_from_file_location("sid_reco_graphify_eval_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load graphify_eval.py from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_graphify_eval_explanations_pass_for_evidence_backed_answers() -> None:
    module = _load_graphify_eval_module()
    result = module.evaluate_explanation_quality_from_paths(
        question_bank_path=EVAL_FIXTURES / "question_bank.json",
        answers_path=EVAL_FIXTURES / "answers_passing.json",
    )

    assert result.passed is True
    assert result.question_pass_rate == 1.0
    assert result.why_source_rate == 1.0
    assert not result.failed_question_ids


def test_graphify_eval_explanations_fail_when_why_answers_skip_required_sources() -> None:
    module = _load_graphify_eval_module()
    result = module.evaluate_explanation_quality_from_paths(
        question_bank_path=EVAL_FIXTURES / "question_bank.json",
        answers_path=EVAL_FIXTURES / "answers_missing_sources.json",
    )

    assert result.passed is False
    assert "why-runtime-note" in result.failed_question_ids
    assert "explain-document-context-state" in result.failed_question_ids
    assert result.why_source_rate == 0.0
