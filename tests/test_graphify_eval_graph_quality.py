from __future__ import annotations

import importlib.util
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


def test_graphify_eval_is_script_scaffolding_not_packaged_source() -> None:
    assert SCRIPT_PATH.exists()
    assert not (ROOT / "src" / "sid_reco" / "graphify_eval.py").exists()


def test_graphify_eval_graph_quality_passes_for_document_context_fixture() -> None:
    module = _load_graphify_eval_module()
    result = module.evaluate_graph_quality_from_paths(
        graph_path=GRAPH_FIXTURES / "document_context_graph.json",
        expectation_path=EVAL_FIXTURES / "graph_expectation_document_context.json",
    )

    assert result.passed is True
    assert result.node_count == 7
    assert result.link_count == 8
    assert result.semantic_link_count == 8
    assert result.relation_type_count == 4
    assert not result.missing_source_files
    assert not result.missing_relation_types
    assert not result.missing_node_ids


def test_graphify_eval_graph_quality_rejects_code_only_fixture_for_document_context_expectation() -> (
    None
):
    module = _load_graphify_eval_module()
    result = module.evaluate_graph_quality_from_paths(
        graph_path=GRAPH_FIXTURES / "code_only_graph.json",
        expectation_path=EVAL_FIXTURES / "graph_expectation_document_context.json",
    )

    assert result.passed is False
    assert result.node_count == 1
    assert result.link_count == 0
    assert result.semantic_link_count == 0
    assert "raw/design/adr/adr-001-dev-environment.md" in result.missing_source_files
    assert "references" in result.missing_relation_types
    assert "adr_one" in result.missing_node_ids
