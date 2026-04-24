from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH_FIXTURES = ROOT / "tests" / "fixtures" / "graphify"
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


def _run_graphify_eval(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    return subprocess.run(
        ["python", "scripts/graphify_eval.py", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_graphify_eval_scorecard_passes_when_all_three_axes_pass() -> None:
    module = _load_graphify_eval_module()
    result = module.build_graphify_scorecard_from_paths(
        graph_path=GRAPH_FIXTURES / "document_context_graph.json",
        expectation_path=EVAL_FIXTURES / "graph_expectation_document_context.json",
        question_bank_path=EVAL_FIXTURES / "question_bank.json",
        answers_path=EVAL_FIXTURES / "answers_passing.json",
        benchmark_path=EVAL_FIXTURES / "assistant_task_set.json",
        run_set_path=EVAL_FIXTURES / "assistant_runs_passing.json",
    )

    assert result.passed is True
    assert result.graph_quality.passed is True
    assert result.explanation_quality.passed is True
    assert result.assistant_utility.passed is True
    assert result.assistant_utility.improved_task_count == 2


def test_graphify_eval_scorecard_fails_when_assistant_utility_regresses() -> None:
    module = _load_graphify_eval_module()
    result = module.build_graphify_scorecard_from_paths(
        graph_path=GRAPH_FIXTURES / "document_context_graph.json",
        expectation_path=EVAL_FIXTURES / "graph_expectation_document_context.json",
        question_bank_path=EVAL_FIXTURES / "question_bank.json",
        answers_path=EVAL_FIXTURES / "answers_passing.json",
        benchmark_path=EVAL_FIXTURES / "assistant_task_set.json",
        run_set_path=EVAL_FIXTURES / "assistant_runs_regressing.json",
    )

    assert result.passed is False
    assert result.graph_quality.passed is True
    assert result.explanation_quality.passed is True
    assert result.assistant_utility.passed is False
    assert result.assistant_utility.wrong_file_delta > 0.0


def test_graphify_eval_scorecard_cli_returns_nonzero_exit_code_on_failed_scorecard() -> None:
    result = _run_graphify_eval(
        "scorecard",
        "--graph",
        "tests/fixtures/graphify/document_context_graph.json",
        "--expectation",
        "tests/fixtures/graphify_eval/graph_expectation_document_context.json",
        "--question-bank",
        "tests/fixtures/graphify_eval/question_bank.json",
        "--answers",
        "tests/fixtures/graphify_eval/answers_passing.json",
        "--benchmark",
        "tests/fixtures/graphify_eval/assistant_task_set.json",
        "--runs",
        "tests/fixtures/graphify_eval/assistant_runs_regressing.json",
    )

    assert result.returncode == 1


def test_graphify_eval_scorecard_cli_returns_zero_exit_code_on_passing_scorecard() -> None:
    result = _run_graphify_eval(
        "scorecard",
        "--graph",
        "tests/fixtures/graphify/document_context_graph.json",
        "--expectation",
        "tests/fixtures/graphify_eval/graph_expectation_document_context.json",
        "--question-bank",
        "tests/fixtures/graphify_eval/question_bank.json",
        "--answers",
        "tests/fixtures/graphify_eval/answers_passing.json",
        "--benchmark",
        "tests/fixtures/graphify_eval/assistant_task_set.json",
        "--runs",
        "tests/fixtures/graphify_eval/assistant_runs_passing.json",
    )

    assert result.returncode == 0
