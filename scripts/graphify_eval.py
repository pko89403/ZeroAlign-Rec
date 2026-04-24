"""Deterministic Graphify evaluation helpers and CLI."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

QuestionKind = Literal["what", "why", "path", "explain"]
AssistantVariant = Literal["baseline", "graph"]


def _load_json_object(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain one top-level JSON object.")
    return cast(dict[str, object], raw)


def _require_mapping(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object.")
    return cast(dict[str, object], value)


def _require_list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array.")
    return value


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    return value


def _optional_str(value: object, field_name: str, *, default: str = "") -> str:
    if value is None:
        return default
    return _require_str(value, field_name)


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean.")
    return value


def _optional_bool(value: object, field_name: str, *, default: bool = False) -> bool:
    if value is None:
        return default
    return _require_bool(value, field_name)


def _require_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer.")
    return value


def _optional_int(value: object, field_name: str, *, default: int) -> int:
    if value is None:
        return default
    return _require_int(value, field_name)


def _require_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be a number.")
    return float(value)


def _optional_float(value: object, field_name: str, *, default: float) -> float:
    if value is None:
        return default
    return _require_float(value, field_name)


def _require_str_tuple(value: object, field_name: str) -> tuple[str, ...]:
    items = _require_list(value, field_name)
    strings: list[str] = []
    for index, item in enumerate(items):
        strings.append(_require_str(item, f"{field_name}[{index}]"))
    return tuple(strings)


def _optional_str_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    return _require_str_tuple(value, field_name)


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("Cannot compute a mean of zero values.")
    return sum(values) / float(len(values))


def _reduction_rate(*, baseline: float, graph: float) -> float:
    if baseline <= 0.0:
        return 0.0
    return (baseline - graph) / baseline


@dataclass(frozen=True, slots=True)
class GraphNode:
    """One node from a Graphify JSON export."""

    id: str
    source_file: str

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> GraphNode:
        return cls(
            id=_require_str(raw.get("id"), "GraphNode.id"),
            source_file=_require_str(raw.get("source_file"), "GraphNode.source_file"),
        )


@dataclass(frozen=True, slots=True)
class GraphLink:
    """One edge from a Graphify JSON export."""

    source: str
    target: str
    relation: str
    confidence: str

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> GraphLink:
        return cls(
            source=_require_str(raw.get("source"), "GraphLink.source"),
            target=_require_str(raw.get("target"), "GraphLink.target"),
            relation=_require_str(raw.get("relation"), "GraphLink.relation"),
            confidence=_optional_str(raw.get("confidence"), "GraphLink.confidence"),
        )


@dataclass(frozen=True, slots=True)
class GraphDocument:
    """Parsed Graphify graph.json contents."""

    nodes: tuple[GraphNode, ...]
    links: tuple[GraphLink, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> GraphDocument:
        node_dicts = _require_list(raw.get("nodes"), "GraphDocument.nodes")
        link_dicts = _require_list(raw.get("links"), "GraphDocument.links")
        return cls(
            nodes=tuple(
                GraphNode.from_dict(_require_mapping(node, f"GraphDocument.nodes[{index}]"))
                for index, node in enumerate(node_dicts)
            ),
            links=tuple(
                GraphLink.from_dict(_require_mapping(link, f"GraphDocument.links[{index}]"))
                for index, link in enumerate(link_dicts)
            ),
        )

    @classmethod
    def from_path(cls, path: Path) -> GraphDocument:
        return cls.from_dict(_load_json_object(path))


@dataclass(frozen=True, slots=True)
class GraphExpectation:
    """Gold expectations for graph quality."""

    name: str
    min_nodes: int
    min_links: int
    min_semantic_links: int
    minimum_relation_type_count: int
    required_source_files: tuple[str, ...]
    required_relation_types: tuple[str, ...]
    required_node_ids: tuple[str, ...]
    max_ambiguous_ratio: float

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> GraphExpectation:
        return cls(
            name=_require_str(raw.get("name"), "GraphExpectation.name"),
            min_nodes=_require_int(raw.get("min_nodes"), "GraphExpectation.min_nodes"),
            min_links=_require_int(raw.get("min_links"), "GraphExpectation.min_links"),
            min_semantic_links=_require_int(
                raw.get("min_semantic_links"),
                "GraphExpectation.min_semantic_links",
            ),
            minimum_relation_type_count=_optional_int(
                raw.get("minimum_relation_type_count"),
                "GraphExpectation.minimum_relation_type_count",
                default=1,
            ),
            required_source_files=_optional_str_tuple(
                raw.get("required_source_files"),
                "GraphExpectation.required_source_files",
            ),
            required_relation_types=_optional_str_tuple(
                raw.get("required_relation_types"),
                "GraphExpectation.required_relation_types",
            ),
            required_node_ids=_optional_str_tuple(
                raw.get("required_node_ids"),
                "GraphExpectation.required_node_ids",
            ),
            max_ambiguous_ratio=_optional_float(
                raw.get("max_ambiguous_ratio"),
                "GraphExpectation.max_ambiguous_ratio",
                default=0.0,
            ),
        )

    @classmethod
    def from_path(cls, path: Path) -> GraphExpectation:
        return cls.from_dict(_load_json_object(path))


@dataclass(frozen=True, slots=True)
class GraphQualityResult:
    """Deterministic graph-quality score for one graph against one expectation."""

    expectation_name: str
    node_count: int
    link_count: int
    semantic_link_count: int
    relation_type_count: int
    ambiguous_ratio: float
    missing_source_files: tuple[str, ...]
    missing_relation_types: tuple[str, ...]
    missing_node_ids: tuple[str, ...]
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "expectation_name": self.expectation_name,
            "node_count": self.node_count,
            "link_count": self.link_count,
            "semantic_link_count": self.semantic_link_count,
            "relation_type_count": self.relation_type_count,
            "ambiguous_ratio": self.ambiguous_ratio,
            "missing_source_files": list(self.missing_source_files),
            "missing_relation_types": list(self.missing_relation_types),
            "missing_node_ids": list(self.missing_node_ids),
            "passed": self.passed,
        }


def evaluate_graph_quality(
    *,
    graph: GraphDocument,
    expectation: GraphExpectation,
) -> GraphQualityResult:
    """Compare a Graphify graph.json file to a deterministic gold expectation."""
    node_ids = {node.id for node in graph.nodes}
    source_files = {node.source_file for node in graph.nodes}
    relation_types = {link.relation for link in graph.links}
    semantic_link_count = sum(1 for link in graph.links if link.relation != "contains")
    ambiguous_count = sum(1 for link in graph.links if link.confidence.upper() == "AMBIGUOUS")
    ambiguous_ratio = ambiguous_count / len(graph.links) if graph.links else 0.0

    missing_source_files = tuple(sorted(set(expectation.required_source_files) - source_files))
    missing_relation_types = tuple(
        sorted(set(expectation.required_relation_types) - relation_types)
    )
    missing_node_ids = tuple(sorted(set(expectation.required_node_ids) - node_ids))

    passed = (
        len(graph.nodes) >= expectation.min_nodes
        and len(graph.links) >= expectation.min_links
        and semantic_link_count >= expectation.min_semantic_links
        and len(relation_types) >= expectation.minimum_relation_type_count
        and not missing_source_files
        and not missing_relation_types
        and not missing_node_ids
        and ambiguous_ratio <= expectation.max_ambiguous_ratio
    )

    return GraphQualityResult(
        expectation_name=expectation.name,
        node_count=len(graph.nodes),
        link_count=len(graph.links),
        semantic_link_count=semantic_link_count,
        relation_type_count=len(relation_types),
        ambiguous_ratio=ambiguous_ratio,
        missing_source_files=missing_source_files,
        missing_relation_types=missing_relation_types,
        missing_node_ids=missing_node_ids,
        passed=passed,
    )


def evaluate_graph_quality_from_paths(
    *,
    graph_path: Path,
    expectation_path: Path,
) -> GraphQualityResult:
    """Load graph and expectation files and evaluate them."""
    return evaluate_graph_quality(
        graph=GraphDocument.from_path(graph_path),
        expectation=GraphExpectation.from_path(expectation_path),
    )


@dataclass(frozen=True, slots=True)
class ExplanationQuestion:
    """One deterministic question for graph-backed explanation scoring."""

    id: str
    kind: QuestionKind
    prompt: str
    required_terms: tuple[str, ...]
    required_sources: tuple[str, ...]
    minimum_citations: int
    allow_abstain: bool

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> ExplanationQuestion:
        kind = _require_str(raw.get("kind"), "ExplanationQuestion.kind")
        if kind not in {"what", "why", "path", "explain"}:
            raise ValueError(f"Unsupported explanation question kind: {kind}")
        return cls(
            id=_require_str(raw.get("id"), "ExplanationQuestion.id"),
            kind=cast(QuestionKind, kind),
            prompt=_require_str(raw.get("prompt"), "ExplanationQuestion.prompt"),
            required_terms=_optional_str_tuple(
                raw.get("required_terms"),
                "ExplanationQuestion.required_terms",
            ),
            required_sources=_optional_str_tuple(
                raw.get("required_sources"),
                "ExplanationQuestion.required_sources",
            ),
            minimum_citations=_optional_int(
                raw.get("minimum_citations"),
                "ExplanationQuestion.minimum_citations",
                default=1,
            ),
            allow_abstain=_optional_bool(
                raw.get("allow_abstain"),
                "ExplanationQuestion.allow_abstain",
                default=False,
            ),
        )


@dataclass(frozen=True, slots=True)
class ExplanationQuestionBank:
    """Question bank plus aggregate pass thresholds."""

    minimum_pass_rate: float
    minimum_why_source_rate: float
    questions: tuple[ExplanationQuestion, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> ExplanationQuestionBank:
        question_dicts = _require_list(raw.get("questions"), "ExplanationQuestionBank.questions")
        return cls(
            minimum_pass_rate=_optional_float(
                raw.get("minimum_pass_rate"),
                "ExplanationQuestionBank.minimum_pass_rate",
                default=1.0,
            ),
            minimum_why_source_rate=_optional_float(
                raw.get("minimum_why_source_rate"),
                "ExplanationQuestionBank.minimum_why_source_rate",
                default=1.0,
            ),
            questions=tuple(
                ExplanationQuestion.from_dict(
                    _require_mapping(question, f"ExplanationQuestionBank.questions[{index}]")
                )
                for index, question in enumerate(question_dicts)
            ),
        )

    @classmethod
    def from_path(cls, path: Path) -> ExplanationQuestionBank:
        return cls.from_dict(_load_json_object(path))


@dataclass(frozen=True, slots=True)
class ExplanationAnswer:
    """One candidate answer for a deterministic explanation question."""

    question_id: str
    answer: str
    cited_sources: tuple[str, ...]
    abstained: bool

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> ExplanationAnswer:
        return cls(
            question_id=_require_str(raw.get("question_id"), "ExplanationAnswer.question_id"),
            answer=_require_str(raw.get("answer"), "ExplanationAnswer.answer"),
            cited_sources=_optional_str_tuple(
                raw.get("cited_sources"),
                "ExplanationAnswer.cited_sources",
            ),
            abstained=_optional_bool(
                raw.get("abstained"),
                "ExplanationAnswer.abstained",
                default=False,
            ),
        )


@dataclass(frozen=True, slots=True)
class ExplanationAnswerSet:
    """Answer set for one explanation benchmark run."""

    answers: tuple[ExplanationAnswer, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> ExplanationAnswerSet:
        answer_dicts = _require_list(raw.get("answers"), "ExplanationAnswerSet.answers")
        return cls(
            answers=tuple(
                ExplanationAnswer.from_dict(
                    _require_mapping(answer, f"ExplanationAnswerSet.answers[{index}]")
                )
                for index, answer in enumerate(answer_dicts)
            )
        )

    @classmethod
    def from_path(cls, path: Path) -> ExplanationAnswerSet:
        return cls.from_dict(_load_json_object(path))


@dataclass(frozen=True, slots=True)
class ExplanationQuestionResult:
    """Per-question deterministic evaluation result."""

    question_id: str
    passed: bool
    source_ok: bool
    terms_ok: bool
    abstained: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "question_id": self.question_id,
            "passed": self.passed,
            "source_ok": self.source_ok,
            "terms_ok": self.terms_ok,
            "abstained": self.abstained,
        }


@dataclass(frozen=True, slots=True)
class ExplanationEvaluationResult:
    """Aggregate explanation-quality result."""

    question_pass_rate: float
    why_source_rate: float
    failed_question_ids: tuple[str, ...]
    question_results: tuple[ExplanationQuestionResult, ...]
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "question_pass_rate": self.question_pass_rate,
            "why_source_rate": self.why_source_rate,
            "failed_question_ids": list(self.failed_question_ids),
            "question_results": [result.to_dict() for result in self.question_results],
            "passed": self.passed,
        }


def evaluate_explanation_quality(
    *,
    question_bank: ExplanationQuestionBank,
    answers: ExplanationAnswerSet,
) -> ExplanationEvaluationResult:
    """Score explanation answers against deterministic source-backed expectations."""
    answer_by_id = {answer.question_id: answer for answer in answers.answers}
    question_results: list[ExplanationQuestionResult] = []
    failed_question_ids: list[str] = []
    pass_count = 0
    why_question_count = 0
    why_source_hits = 0

    for question in question_bank.questions:
        answer = answer_by_id.get(question.id)
        if answer is None:
            result = ExplanationQuestionResult(
                question_id=question.id,
                passed=False,
                source_ok=False,
                terms_ok=False,
                abstained=False,
            )
        else:
            answer_text = answer.answer.lower()
            terms_ok = all(term.lower() in answer_text for term in question.required_terms)
            matching_sources = {
                source
                for source in answer.cited_sources
                if source in set(question.required_sources)
            }
            if question.required_sources:
                source_ok = len(matching_sources) >= question.minimum_citations
            else:
                source_ok = True
            if question.kind == "why":
                why_question_count += 1
                if source_ok:
                    why_source_hits += 1
            passed = (question.allow_abstain and answer.abstained) or (
                not answer.abstained and terms_ok and source_ok
            )
            result = ExplanationQuestionResult(
                question_id=question.id,
                passed=passed,
                source_ok=source_ok,
                terms_ok=terms_ok,
                abstained=answer.abstained,
            )

        if result.passed:
            pass_count += 1
        else:
            failed_question_ids.append(question.id)
        question_results.append(result)

    question_pass_rate = pass_count / len(question_bank.questions)
    why_source_rate = why_source_hits / why_question_count if why_question_count > 0 else 1.0
    passed = (
        question_pass_rate >= question_bank.minimum_pass_rate
        and why_source_rate >= question_bank.minimum_why_source_rate
    )
    return ExplanationEvaluationResult(
        question_pass_rate=question_pass_rate,
        why_source_rate=why_source_rate,
        failed_question_ids=tuple(failed_question_ids),
        question_results=tuple(question_results),
        passed=passed,
    )


def evaluate_explanation_quality_from_paths(
    *,
    question_bank_path: Path,
    answers_path: Path,
) -> ExplanationEvaluationResult:
    """Load explanation fixtures and evaluate them."""
    return evaluate_explanation_quality(
        question_bank=ExplanationQuestionBank.from_path(question_bank_path),
        answers=ExplanationAnswerSet.from_path(answers_path),
    )


@dataclass(frozen=True, slots=True)
class AssistantTask:
    """One A/B task for the coding-assistant utility benchmark."""

    id: str
    kind: str
    prompt: str
    required_files: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> AssistantTask:
        return cls(
            id=_require_str(raw.get("id"), "AssistantTask.id"),
            kind=_require_str(raw.get("kind"), "AssistantTask.kind"),
            prompt=_require_str(raw.get("prompt"), "AssistantTask.prompt"),
            required_files=_optional_str_tuple(
                raw.get("required_files"),
                "AssistantTask.required_files",
            ),
        )


@dataclass(frozen=True, slots=True)
class AssistantBenchmark:
    """Task set and thresholds for graph-vs-baseline A/B evaluation."""

    minimum_accuracy_gain: float
    minimum_turn_reduction_rate: float
    minimum_duration_reduction_rate: float
    maximum_wrong_file_delta: int
    tasks: tuple[AssistantTask, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> AssistantBenchmark:
        task_dicts = _require_list(raw.get("tasks"), "AssistantBenchmark.tasks")
        return cls(
            minimum_accuracy_gain=_optional_float(
                raw.get("minimum_accuracy_gain"),
                "AssistantBenchmark.minimum_accuracy_gain",
                default=0.0,
            ),
            minimum_turn_reduction_rate=_optional_float(
                raw.get("minimum_turn_reduction_rate"),
                "AssistantBenchmark.minimum_turn_reduction_rate",
                default=0.0,
            ),
            minimum_duration_reduction_rate=_optional_float(
                raw.get("minimum_duration_reduction_rate"),
                "AssistantBenchmark.minimum_duration_reduction_rate",
                default=0.0,
            ),
            maximum_wrong_file_delta=_optional_int(
                raw.get("maximum_wrong_file_delta"),
                "AssistantBenchmark.maximum_wrong_file_delta",
                default=0,
            ),
            tasks=tuple(
                AssistantTask.from_dict(
                    _require_mapping(task, f"AssistantBenchmark.tasks[{index}]")
                )
                for index, task in enumerate(task_dicts)
            ),
        )

    @classmethod
    def from_path(cls, path: Path) -> AssistantBenchmark:
        return cls.from_dict(_load_json_object(path))


@dataclass(frozen=True, slots=True)
class AssistantRun:
    """One recorded A/B run result."""

    task_id: str
    variant: AssistantVariant
    first_response_correct: bool
    turns_to_success: int
    wrong_file_count: int
    duration_seconds: float

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> AssistantRun:
        variant = _require_str(raw.get("variant"), "AssistantRun.variant")
        if variant not in {"baseline", "graph"}:
            raise ValueError(f"Unsupported assistant benchmark variant: {variant}")
        return cls(
            task_id=_require_str(raw.get("task_id"), "AssistantRun.task_id"),
            variant=cast(AssistantVariant, variant),
            first_response_correct=_require_bool(
                raw.get("first_response_correct"),
                "AssistantRun.first_response_correct",
            ),
            turns_to_success=_require_int(
                raw.get("turns_to_success"),
                "AssistantRun.turns_to_success",
            ),
            wrong_file_count=_require_int(
                raw.get("wrong_file_count"),
                "AssistantRun.wrong_file_count",
            ),
            duration_seconds=_require_float(
                raw.get("duration_seconds"),
                "AssistantRun.duration_seconds",
            ),
        )


@dataclass(frozen=True, slots=True)
class AssistantRunSet:
    """A/B run results for a benchmark task set."""

    runs: tuple[AssistantRun, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> AssistantRunSet:
        run_dicts = _require_list(raw.get("runs"), "AssistantRunSet.runs")
        return cls(
            runs=tuple(
                AssistantRun.from_dict(_require_mapping(run, f"AssistantRunSet.runs[{index}]"))
                for index, run in enumerate(run_dicts)
            )
        )

    @classmethod
    def from_path(cls, path: Path) -> AssistantRunSet:
        return cls.from_dict(_load_json_object(path))


@dataclass(frozen=True, slots=True)
class AssistantUtilityResult:
    """Aggregate A/B benchmark result."""

    baseline_accuracy: float
    graph_accuracy: float
    accuracy_gain: float
    turn_reduction_rate: float
    duration_reduction_rate: float
    wrong_file_delta: float
    improved_task_count: int
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "baseline_accuracy": self.baseline_accuracy,
            "graph_accuracy": self.graph_accuracy,
            "accuracy_gain": self.accuracy_gain,
            "turn_reduction_rate": self.turn_reduction_rate,
            "duration_reduction_rate": self.duration_reduction_rate,
            "wrong_file_delta": self.wrong_file_delta,
            "improved_task_count": self.improved_task_count,
            "passed": self.passed,
        }


def evaluate_assistant_utility(
    *,
    benchmark: AssistantBenchmark,
    run_set: AssistantRunSet,
) -> AssistantUtilityResult:
    """Compare baseline-vs-graph task outcomes for the same task set."""
    grouped_runs: dict[str, dict[AssistantVariant, AssistantRun]] = {}
    for run in run_set.runs:
        task_runs = grouped_runs.setdefault(run.task_id, {})
        task_runs[run.variant] = run

    baseline_runs: list[AssistantRun] = []
    graph_runs: list[AssistantRun] = []
    improved_task_count = 0
    for task in benchmark.tasks:
        paired_runs = grouped_runs.get(task.id)
        if paired_runs is None or "baseline" not in paired_runs or "graph" not in paired_runs:
            raise ValueError(f"Missing baseline/graph pair for assistant task '{task.id}'.")
        baseline_run = paired_runs["baseline"]
        graph_run = paired_runs["graph"]
        baseline_runs.append(baseline_run)
        graph_runs.append(graph_run)
        if (
            (graph_run.first_response_correct and not baseline_run.first_response_correct)
            or graph_run.turns_to_success < baseline_run.turns_to_success
            or graph_run.duration_seconds < baseline_run.duration_seconds
        ):
            improved_task_count += 1

    baseline_accuracy = _mean([1.0 if run.first_response_correct else 0.0 for run in baseline_runs])
    graph_accuracy = _mean([1.0 if run.first_response_correct else 0.0 for run in graph_runs])
    baseline_turns = _mean([float(run.turns_to_success) for run in baseline_runs])
    graph_turns = _mean([float(run.turns_to_success) for run in graph_runs])
    baseline_duration = _mean([run.duration_seconds for run in baseline_runs])
    graph_duration = _mean([run.duration_seconds for run in graph_runs])
    baseline_wrong_files = _mean([float(run.wrong_file_count) for run in baseline_runs])
    graph_wrong_files = _mean([float(run.wrong_file_count) for run in graph_runs])

    accuracy_gain = graph_accuracy - baseline_accuracy
    turn_reduction_rate = _reduction_rate(baseline=baseline_turns, graph=graph_turns)
    duration_reduction_rate = _reduction_rate(
        baseline=baseline_duration,
        graph=graph_duration,
    )
    wrong_file_delta = graph_wrong_files - baseline_wrong_files

    passed = (
        graph_accuracy >= baseline_accuracy
        and wrong_file_delta <= benchmark.maximum_wrong_file_delta
        and (
            accuracy_gain >= benchmark.minimum_accuracy_gain
            or turn_reduction_rate >= benchmark.minimum_turn_reduction_rate
            or duration_reduction_rate >= benchmark.minimum_duration_reduction_rate
        )
    )
    return AssistantUtilityResult(
        baseline_accuracy=baseline_accuracy,
        graph_accuracy=graph_accuracy,
        accuracy_gain=accuracy_gain,
        turn_reduction_rate=turn_reduction_rate,
        duration_reduction_rate=duration_reduction_rate,
        wrong_file_delta=wrong_file_delta,
        improved_task_count=improved_task_count,
        passed=passed,
    )


def evaluate_assistant_utility_from_paths(
    *,
    benchmark_path: Path,
    run_set_path: Path,
) -> AssistantUtilityResult:
    """Load A/B benchmark fixtures and evaluate them."""
    return evaluate_assistant_utility(
        benchmark=AssistantBenchmark.from_path(benchmark_path),
        run_set=AssistantRunSet.from_path(run_set_path),
    )


@dataclass(frozen=True, slots=True)
class GraphifyEvaluationScorecard:
    """Overall status across graph, explanation, and utility axes."""

    graph_quality: GraphQualityResult
    explanation_quality: ExplanationEvaluationResult
    assistant_utility: AssistantUtilityResult
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "graph_quality": self.graph_quality.to_dict(),
            "explanation_quality": self.explanation_quality.to_dict(),
            "assistant_utility": self.assistant_utility.to_dict(),
            "passed": self.passed,
        }


def build_graphify_scorecard(
    *,
    graph_quality: GraphQualityResult,
    explanation_quality: ExplanationEvaluationResult,
    assistant_utility: AssistantUtilityResult,
) -> GraphifyEvaluationScorecard:
    """Combine three benchmark axes into one pass/fail scorecard."""
    return GraphifyEvaluationScorecard(
        graph_quality=graph_quality,
        explanation_quality=explanation_quality,
        assistant_utility=assistant_utility,
        passed=(graph_quality.passed and explanation_quality.passed and assistant_utility.passed),
    )


def build_graphify_scorecard_from_paths(
    *,
    graph_path: Path,
    expectation_path: Path,
    question_bank_path: Path,
    answers_path: Path,
    benchmark_path: Path,
    run_set_path: Path,
) -> GraphifyEvaluationScorecard:
    """Load all three benchmark axes and aggregate them."""
    return build_graphify_scorecard(
        graph_quality=evaluate_graph_quality_from_paths(
            graph_path=graph_path,
            expectation_path=expectation_path,
        ),
        explanation_quality=evaluate_explanation_quality_from_paths(
            question_bank_path=question_bank_path,
            answers_path=answers_path,
        ),
        assistant_utility=evaluate_assistant_utility_from_paths(
            benchmark_path=benchmark_path,
            run_set_path=run_set_path,
        ),
    )


def _print_json(payload: dict[str, object]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))


def _exit_code_from_pass_flag(passed: bool) -> int:
    return 0 if passed else 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run deterministic Graphify benchmark helpers from the command line."""
    parser = argparse.ArgumentParser(description="Deterministic Graphify benchmark helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    graph_quality_parser = subparsers.add_parser("graph-quality")
    graph_quality_parser.add_argument("--graph", type=Path, required=True)
    graph_quality_parser.add_argument("--expectation", type=Path, required=True)

    explanations_parser = subparsers.add_parser("explanations")
    explanations_parser.add_argument("--question-bank", type=Path, required=True)
    explanations_parser.add_argument("--answers", type=Path, required=True)

    assistant_parser = subparsers.add_parser("assistant-utility")
    assistant_parser.add_argument("--benchmark", type=Path, required=True)
    assistant_parser.add_argument("--runs", type=Path, required=True)

    scorecard_parser = subparsers.add_parser("scorecard")
    scorecard_parser.add_argument("--graph", type=Path, required=True)
    scorecard_parser.add_argument("--expectation", type=Path, required=True)
    scorecard_parser.add_argument("--question-bank", type=Path, required=True)
    scorecard_parser.add_argument("--answers", type=Path, required=True)
    scorecard_parser.add_argument("--benchmark", type=Path, required=True)
    scorecard_parser.add_argument("--runs", type=Path, required=True)

    args = parser.parse_args(list(argv) if argv is not None else None)
    command = cast(str, args.command)
    if command == "graph-quality":
        graph_quality_result = evaluate_graph_quality_from_paths(
            graph_path=cast(Path, args.graph),
            expectation_path=cast(Path, args.expectation),
        )
        _print_json(graph_quality_result.to_dict())
        return _exit_code_from_pass_flag(graph_quality_result.passed)
    if command == "explanations":
        explanation_result = evaluate_explanation_quality_from_paths(
            question_bank_path=cast(Path, args.question_bank),
            answers_path=cast(Path, args.answers),
        )
        _print_json(explanation_result.to_dict())
        return _exit_code_from_pass_flag(explanation_result.passed)
    if command == "assistant-utility":
        assistant_result = evaluate_assistant_utility_from_paths(
            benchmark_path=cast(Path, args.benchmark),
            run_set_path=cast(Path, args.runs),
        )
        _print_json(assistant_result.to_dict())
        return _exit_code_from_pass_flag(assistant_result.passed)

    scorecard = build_graphify_scorecard_from_paths(
        graph_path=cast(Path, args.graph),
        expectation_path=cast(Path, args.expectation),
        question_bank_path=cast(Path, args.question_bank),
        answers_path=cast(Path, args.answers),
        benchmark_path=cast(Path, args.benchmark),
        run_set_path=cast(Path, args.runs),
    )
    _print_json(scorecard.to_dict())
    return _exit_code_from_pass_flag(scorecard.passed)


if __name__ == "__main__":
    raise SystemExit(main())
