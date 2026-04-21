from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from graphify.analyze import god_nodes, suggest_questions, surprising_connections
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.detect import detect
from graphify.export import to_html, to_json
from graphify.extract import extract
from graphify.report import generate
from graphify_semantic_adapter import extract_semantic_fragments

GRAPHIFY_VERSION = "0.4.23"


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _normalize_source_file(path: str | None, root: Path) -> str | None:
    if path is None:
        return None
    path_obj = Path(path)
    try:
        return path_obj.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path_obj.as_posix()


def _normalize_ast_payload(payload: dict[str, Any], root: Path) -> dict[str, Any]:
    normalized = dict(payload)
    nodes: list[dict[str, Any]] = []
    for node in payload.get("nodes", []):
        item = dict(node)
        item["source_file"] = _normalize_source_file(item.get("source_file"), root)
        nodes.append(item)
    edges: list[dict[str, Any]] = []
    for edge in payload.get("edges", []):
        item = dict(edge)
        item["source_file"] = _normalize_source_file(item.get("source_file"), root)
        item.setdefault("confidence_score", 1.0)
        edges.append(item)
    normalized["nodes"] = nodes
    normalized["edges"] = edges
    return normalized


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/graphify_full_refresh.py <corpus-root>", file=sys.stderr)
        return 1

    corpus_root = Path(sys.argv[1]).resolve()
    if not corpus_root.exists():
        print(f"corpus root not found: {corpus_root}", file=sys.stderr)
        return 1

    output_dir = corpus_root / "graphify-out"
    output_dir.mkdir(parents=True, exist_ok=True)

    detection = detect(corpus_root)
    _write_json(output_dir / ".graphify_detect.json", detection)

    code_files = [Path(path) for path in detection["files"]["code"]]
    ast_payload = (
        extract(code_files, cache_root=corpus_root)
        if code_files
        else {
            "nodes": [],
            "edges": [],
            "input_tokens": 0,
            "output_tokens": 0,
        }
    )
    ast_payload = _normalize_ast_payload(ast_payload, corpus_root)
    _write_json(output_dir / ".graphify_ast.json", ast_payload)

    document_files = [
        Path(path)
        for key in ("document", "paper", "image")
        for path in detection["files"].get(key, [])
    ]

    try:
        semantic_payload = extract_semantic_fragments(
            corpus_root=corpus_root,
            document_files=document_files,
            ast_nodes=ast_payload["nodes"],
        )
    except Exception as exc:
        print(f"semantic extraction failed: {exc}", file=sys.stderr)
        return 1

    _write_json(output_dir / ".graphify_semantic.json", semantic_payload)

    seen_node_ids: set[str] = set()
    merged_nodes: list[dict[str, Any]] = []
    for payload in (ast_payload, semantic_payload):
        for node in payload.get("nodes", []):
            node_id = node.get("id")
            if not isinstance(node_id, str) or node_id in seen_node_ids:
                continue
            seen_node_ids.add(node_id)
            merged_nodes.append(node)

    merged_edges = list(ast_payload.get("edges", [])) + list(semantic_payload.get("edges", []))
    extraction = {
        "nodes": merged_nodes,
        "edges": merged_edges,
        "input_tokens": semantic_payload.get("input_tokens", 0),
        "output_tokens": semantic_payload.get("output_tokens", 0),
    }
    _write_json(output_dir / ".graphify_extract.json", extraction)

    graph = build_from_json(extraction)
    communities = cluster(graph)
    cohesion = score_all(graph, communities)
    labels = {community_id: f"Community {community_id}" for community_id in communities}
    questions = suggest_questions(graph, communities, labels)
    surprises = surprising_connections(graph, communities)
    gods = god_nodes(graph)

    analysis = {
        "communities": {str(k): v for k, v in communities.items()},
        "cohesion": {str(k): v for k, v in cohesion.items()},
        "gods": gods,
        "surprises": surprises,
        "questions": questions,
    }
    _write_json(output_dir / ".graphify_analysis.json", analysis)
    _write_json(output_dir / ".graphify_labels.json", {str(k): v for k, v in labels.items()})

    report = generate(
        graph,
        communities,
        cohesion,
        labels,
        gods,
        surprises,
        detection,
        {
            "input": extraction.get("input_tokens", 0),
            "output": extraction.get("output_tokens", 0),
        },
        str(corpus_root),
        suggested_questions=questions,
    )
    (output_dir / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    to_json(graph, communities, str(output_dir / "graph.json"))
    to_html(graph, communities, str(output_dir / "graph.html"), community_labels=labels or None)

    build_info = {
        "graphify_version": GRAPHIFY_VERSION,
        "mode": "full_refresh",
        "command": f"python3 scripts/graphify_full_refresh.py {corpus_root.as_posix()}",
        "generated_at": datetime.now(UTC).isoformat(),
        "corpus_path": corpus_root.as_posix(),
        "verified": False,
        "semantic_backend": semantic_payload.get("backend", "heuristic"),
    }
    _write_json(output_dir / "BUILD_INFO.json", build_info)

    print(
        f"graphify: full refresh staged at {output_dir} "
        f"({len(merged_nodes)} nodes, {len(merged_edges)} edges)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
