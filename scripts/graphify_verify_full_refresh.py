from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

NON_SEMANTIC_RELATIONS = {"contains"}
MIN_SEMANTIC_LINKS = 8
MIN_RELATION_TYPES = 2
VERIFICATION_PROFILE = "raw-source-coverage-v3"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_source_files(graph: dict) -> set[str]:
    source_files: set[str] = set()
    for node in graph.get("nodes", []):
        source_file = node.get("source_file")
        if isinstance(source_file, str) and source_file:
            source_files.add(source_file)
    return source_files


def _collect_links(graph: dict) -> list[dict]:
    raw_links = graph.get("links")
    if isinstance(raw_links, list):
        return raw_links
    raw_edges = graph.get("edges")
    if isinstance(raw_edges, list):
        return raw_edges
    return []


def _files_under(corpus_root: Path, relative: str) -> set[str]:
    base = corpus_root / relative
    if not base.exists():
        return set()
    return {
        path.relative_to(corpus_root).as_posix()
        for path in base.rglob("*")
        if path.is_file() and path.name != ".gitkeep"
    }


def _collect_corpus_source_sets(corpus_root: Path) -> dict[str, set[str]]:
    return {
        "design_required": _files_under(corpus_root, "raw/design/adr")
        | _files_under(corpus_root, "raw/design/notes"),
        "design_optional": _files_under(corpus_root, "raw/design/specs"),
        "presence_only": _files_under(corpus_root, "raw/design/diagrams")
        | _files_under(corpus_root, "raw/design/screenshots")
        | _files_under(corpus_root, "raw/external"),
    }


def _collect_semantic_metrics(graph: dict, required_files: set[str]) -> dict[str, object]:
    nodes = graph.get("nodes", [])
    links = _collect_links(graph)
    node_by_id = {node.get("id"): node for node in nodes if isinstance(node.get("id"), str)}

    semantic_link_count = 0
    relation_counts: Counter[str] = Counter()
    missing_confidence: list[str] = []
    coverage: defaultdict[str, set[str]] = defaultdict(set)

    for link in links:
        relation = link.get("relation")
        if not isinstance(relation, str) or relation in NON_SEMANTIC_RELATIONS:
            continue

        source_id = link.get("source", link.get("from"))
        target_id = link.get("target", link.get("to"))
        source_node = node_by_id.get(source_id)
        target_node = node_by_id.get(target_id)

        touched_files = {
            source_file
            for source_file in (
                source_node.get("source_file") if isinstance(source_node, dict) else None,
                target_node.get("source_file") if isinstance(target_node, dict) else None,
            )
            if isinstance(source_file, str) and source_file in required_files
        }
        if not touched_files:
            continue

        if not link.get("confidence") or "confidence_score" not in link:
            missing_confidence.append(
                f"{relation}:{source_id or '<missing>'}->{target_id or '<missing>'}"
            )
            continue

        semantic_link_count += 1
        relation_counts[relation] += 1
        for source_file in touched_files:
            coverage[source_file].add(relation)

    return {
        "semantic_link_count": semantic_link_count,
        "relation_counts": dict(relation_counts),
        "coverage": {key: sorted(value) for key, value in sorted(coverage.items())},
        "missing_confidence": missing_confidence,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "Usage: python3 scripts/graphify_verify_full_refresh.py <staged-graphify-out>",
            file=sys.stderr,
        )
        return 1

    staged = Path(sys.argv[1]).resolve()
    graph_path = staged / "graph.json"
    report_path = staged / "GRAPH_REPORT.md"
    build_info_path = staged / "BUILD_INFO.json"

    missing_files = [
        path.name for path in (graph_path, report_path, build_info_path) if not path.exists()
    ]
    if missing_files:
        print(
            f"missing required staged artifacts: {', '.join(missing_files)}",
            file=sys.stderr,
        )
        return 1

    report_text = report_path.read_text(encoding="utf-8").strip()
    if not report_text:
        print("GRAPH_REPORT.md is empty", file=sys.stderr)
        return 1

    build_info = _load_json(build_info_path)
    if build_info.get("mode") != "full_refresh":
        print("BUILD_INFO.json must declare mode=full_refresh", file=sys.stderr)
        return 1

    for field in ("graphify_version", "command", "generated_at", "corpus_path"):
        if not build_info.get(field):
            print(f"BUILD_INFO.json missing required field: {field}", file=sys.stderr)
            return 1

    corpus_root = Path(str(build_info["corpus_path"])).resolve()
    if not corpus_root.exists():
        print(f"corpus root not found for verification: {corpus_root}", file=sys.stderr)
        return 1
    source_sets = _collect_corpus_source_sets(corpus_root)
    required_semantic_files = source_sets["design_required"] | source_sets["design_optional"]
    presence_only_files = source_sets["presence_only"]

    graph = _load_json(graph_path)
    source_files = _collect_source_files(graph)

    missing_context = [
        required
        for required in sorted(required_semantic_files | presence_only_files)
        if required not in source_files
    ]
    if missing_context:
        print(
            "missing required raw source context in graph.json: " + ", ".join(missing_context),
            file=sys.stderr,
        )
        return 1

    semantic_metrics = _collect_semantic_metrics(graph, required_semantic_files)
    missing_confidence = semantic_metrics["missing_confidence"]
    if missing_confidence:
        print(
            "semantic links touching raw design docs are missing confidence metadata: "
            + ", ".join(missing_confidence[:5]),
            file=sys.stderr,
        )
        return 1

    semantic_link_count = int(semantic_metrics["semantic_link_count"])
    if required_semantic_files and semantic_link_count < MIN_SEMANTIC_LINKS:
        print(
            "semantic raw design coverage too weak: "
            f"expected at least {MIN_SEMANTIC_LINKS} non-trivial links, got {semantic_link_count}",
            file=sys.stderr,
        )
        return 1

    relation_counts = semantic_metrics["relation_counts"]
    if required_semantic_files and len(relation_counts) < MIN_RELATION_TYPES:
        print(
            "semantic raw design coverage too narrow: "
            f"expected at least {MIN_RELATION_TYPES} relation types, got {sorted(relation_counts)}",
            file=sys.stderr,
        )
        return 1

    coverage = semantic_metrics["coverage"]
    uncovered_required = [
        required for required in sorted(required_semantic_files) if required not in coverage
    ]
    if uncovered_required:
        print(
            "required raw design docs exist but lack semantic links: "
            + ", ".join(uncovered_required),
            file=sys.stderr,
        )
        return 1

    build_info["verified"] = True
    build_info["verification_profile"] = VERIFICATION_PROFILE
    build_info["verification_metrics"] = {
        "required_semantic_files": sorted(required_semantic_files),
        "presence_only_files": sorted(presence_only_files),
        **semantic_metrics,
    }
    build_info_path.write_text(
        json.dumps(build_info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    marker = {
        "verified": True,
        "verified_at": datetime.now(UTC).isoformat(),
        "required_semantic_files": sorted(required_semantic_files),
        "presence_only_files": sorted(presence_only_files),
        "verification_profile": VERIFICATION_PROFILE,
        "verification_metrics": semantic_metrics,
    }
    (staged / "VERIFY_FULL_REFRESH.json").write_text(
        json.dumps(marker, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("verified full refresh: raw source coverage passed and BUILD_INFO marked verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
