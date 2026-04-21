from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_SPAN_RE = re.compile(r"`([^`]+)`")
TOKEN_RE = re.compile(
    r"[A-Za-z0-9\u3131-\u318E\uAC00-\uD7A3]"
    r"[A-Za-z0-9_\-./\u3131-\u318E\uAC00-\uD7A3]{1,}"
)

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "when",
    "where",
    "then",
    "than",
    "only",
    "use",
    "uses",
    "using",
    "docs",
    "doc",
    "readme",
    "spec",
    "agents",
    "graphify",
    "legacy",
    "index",
    "page",
    "pages",
    "file",
    "files",
    "section",
    "sections",
    "what",
    "how",
    "why",
    "does",
    "did",
    "done",
    "있는",
    "있는지",
    "그리고",
    "에서",
    "으로",
    "한다",
    "합니다",
    "위한",
    "대한",
    "기반",
    "프로젝트",
    "문서",
    "규칙",
    "설명",
    "개요",
    "현재",
    "관련",
    "역할",
    "사용",
    "유지",
    "추가",
    "변경",
}
RATIONALE_TOKENS = {
    "background",
    "context",
    "decision",
    "decisions",
    "consequence",
    "consequences",
    "rationale",
    "motivation",
    "tradeoff",
    "trade",
    "why",
    "because",
    "배경",
    "맥락",
    "결정",
    "결론",
    "근거",
    "이유",
    "동기",
    "제약",
    "트레이드오프",
    "후속",
    "영향",
}


def _slug(value: str) -> str:
    normalized = re.sub(r"[^0-9a-z\u3131-\u318e\uac00-\ud7a3]+", "_", value.lower()).strip("_")
    return normalized


def _compact(value: str) -> str:
    return re.sub(r"[^0-9a-z\u3131-\u318e\uac00-\ud7a3]+", "", value.lower())


def _node_id(prefix: str, value: str) -> str:
    slug = _slug(value)
    return f"{prefix}_{slug}" if slug else prefix


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in TOKEN_RE.findall(text):
        token = raw.strip("`").lower()
        if len(_compact(token)) < 2:
            continue
        if token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def _is_rationale_heading(heading: str) -> bool:
    compact_heading = _compact(heading)
    return any(token in compact_heading for token in RATIONALE_TOKENS)


def _resolve_local_markdown_target(
    raw_target: str, document: Path, corpus_root: Path
) -> str | None:
    target = raw_target.strip()
    if not target or "://" in target or target.startswith("#"):
        return None
    target_path = (document.parent / target).resolve()
    if not target_path.exists():
        return None
    try:
        return target_path.relative_to(corpus_root).as_posix()
    except ValueError:
        return None


def _build_ast_aliases(ast_nodes: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    aliases: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in ast_nodes:
        label = node.get("label")
        if isinstance(label, str):
            key = _compact(label)
            if key:
                aliases[key].append(node)
        source_file = node.get("source_file")
        if isinstance(source_file, str) and source_file:
            path = Path(source_file)
            for value in (path.name, path.stem, source_file):
                key = _compact(value)
                if key:
                    aliases[key].append(node)
    return aliases


def _add_node(
    nodes: list[dict[str, Any]],
    seen_nodes: set[str],
    *,
    node_id: str,
    label: str,
    source_file: str,
    source_location: str | None,
    file_type: str = "document",
    kind: str | None = None,
) -> None:
    if node_id in seen_nodes:
        return
    payload: dict[str, Any] = {
        "id": node_id,
        "label": label,
        "file_type": file_type,
        "source_file": source_file,
        "source_location": source_location,
    }
    if kind is not None:
        payload["kind"] = kind
    nodes.append(payload)
    seen_nodes.add(node_id)


def _add_edge(
    edges: list[dict[str, Any]],
    seen_edges: set[tuple[str, str, str]],
    *,
    source: str,
    target: str,
    relation: str,
    confidence: str,
    confidence_score: float,
    source_file: str,
    source_location: str | None,
    weight: float = 1.0,
) -> None:
    edge_key = (source, target, relation)
    if edge_key in seen_edges:
        return
    edges.append(
        {
            "source": source,
            "target": target,
            "relation": relation,
            "confidence": confidence,
            "confidence_score": confidence_score,
            "source_file": source_file,
            "source_location": source_location,
            "weight": weight,
        }
    )
    seen_edges.add(edge_key)


def extract_semantic_fragments(
    *,
    corpus_root: Path,
    document_files: list[Path],
    ast_nodes: list[dict[str, Any]],
) -> dict[str, Any]:
    mode = os.getenv("GRAPHIFY_SEMANTIC_ADAPTER_MODE", "heuristic")
    if mode == "fail":
        raise RuntimeError(
            "semantic extraction failed: forced failure via GRAPHIFY_SEMANTIC_ADAPTER_MODE"
        )
    if mode != "heuristic":
        raise RuntimeError(f"semantic extraction failed: unsupported adapter mode '{mode}'")

    ast_aliases = _build_ast_aliases(ast_nodes)
    doc_node_id_by_path = {
        _relative(document, corpus_root): _node_id("doc", _relative(document, corpus_root))
        for document in document_files
    }

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_nodes: set[str] = set()
    seen_edges: set[tuple[str, str, str]] = set()
    doc_reference_targets: dict[str, set[str]] = defaultdict(set)
    doc_keyword_counts: dict[str, Counter[str]] = {}

    for document in document_files:
        relpath = _relative(document, corpus_root)
        text = document.read_text(encoding="utf-8", errors="ignore")
        basename = document.name
        file_node_id = doc_node_id_by_path[relpath]
        doc_keyword_counts[relpath] = Counter(_tokenize(text))

        _add_node(
            nodes,
            seen_nodes,
            node_id=file_node_id,
            label=basename,
            source_file=relpath,
            source_location=None,
            kind="document",
        )

        current_rationale_node_id: str | None = None
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            stripped = raw_line.strip()
            heading_match = HEADING_RE.match(stripped)
            if heading_match:
                heading = heading_match.group(2).strip()
                heading_node_id = _node_id("heading", f"{relpath}_{heading}")
                _add_node(
                    nodes,
                    seen_nodes,
                    node_id=heading_node_id,
                    label=heading,
                    source_file=relpath,
                    source_location=f"L{line_number}",
                    kind="heading",
                )
                _add_edge(
                    edges,
                    seen_edges,
                    source=file_node_id,
                    target=heading_node_id,
                    relation="contains",
                    confidence="EXTRACTED",
                    confidence_score=1.0,
                    source_file=relpath,
                    source_location=f"L{line_number}",
                )

                if _is_rationale_heading(heading):
                    current_rationale_node_id = _node_id("rationale", f"{relpath}_{heading}")
                    _add_node(
                        nodes,
                        seen_nodes,
                        node_id=current_rationale_node_id,
                        label=heading,
                        source_file=relpath,
                        source_location=f"L{line_number}",
                        kind="rationale",
                    )
                    _add_edge(
                        edges,
                        seen_edges,
                        source=file_node_id,
                        target=current_rationale_node_id,
                        relation="contains",
                        confidence="EXTRACTED",
                        confidence_score=1.0,
                        source_file=relpath,
                        source_location=f"L{line_number}",
                    )
                else:
                    current_rationale_node_id = None

            for _, raw_target in LINK_RE.findall(raw_line):
                resolved_target = _resolve_local_markdown_target(raw_target, document, corpus_root)
                if resolved_target is None or resolved_target not in doc_node_id_by_path:
                    continue

                target_doc_node_id = doc_node_id_by_path[resolved_target]
                _add_edge(
                    edges,
                    seen_edges,
                    source=file_node_id,
                    target=target_doc_node_id,
                    relation="links_to",
                    confidence="EXTRACTED",
                    confidence_score=1.0,
                    source_file=relpath,
                    source_location=f"L{line_number}",
                )
                doc_reference_targets[file_node_id].add(target_doc_node_id)
                if current_rationale_node_id is not None:
                    _add_edge(
                        edges,
                        seen_edges,
                        source=current_rationale_node_id,
                        target=target_doc_node_id,
                        relation="rationale_for",
                        confidence="EXTRACTED",
                        confidence_score=1.0,
                        source_file=relpath,
                        source_location=f"L{line_number}",
                    )

            span_candidates = [candidate.strip() for candidate in CODE_SPAN_RE.findall(raw_line)]
            token_candidates = span_candidates + _tokenize(raw_line)
            seen_targets_for_line: set[str] = set()
            for candidate in token_candidates:
                alias = _compact(candidate)
                if not alias:
                    continue
                for target in ast_aliases.get(alias, []):
                    target_id = target.get("id")
                    if not isinstance(target_id, str) or target_id in seen_targets_for_line:
                        continue
                    seen_targets_for_line.add(target_id)
                    _add_edge(
                        edges,
                        seen_edges,
                        source=file_node_id,
                        target=target_id,
                        relation="references",
                        confidence="INFERRED",
                        confidence_score=0.8,
                        source_file=relpath,
                        source_location=f"L{line_number}",
                    )
                    doc_reference_targets[file_node_id].add(target_id)
                    if current_rationale_node_id is not None:
                        _add_edge(
                            edges,
                            seen_edges,
                            source=current_rationale_node_id,
                            target=target_id,
                            relation="rationale_for",
                            confidence="INFERRED",
                            confidence_score=0.75,
                            source_file=relpath,
                            source_location=f"L{line_number}",
                        )

    doc_items = list(doc_node_id_by_path.items())
    for (left_path, left_node_id), (right_path, right_node_id) in combinations(doc_items, 2):
        shared_targets = doc_reference_targets[left_node_id] & doc_reference_targets[right_node_id]
        left_keywords = {
            token for token, count in doc_keyword_counts[left_path].items() if count > 0
        }
        right_keywords = {
            token for token, count in doc_keyword_counts[right_path].items() if count > 0
        }
        shared_keywords = {
            token
            for token in (left_keywords & right_keywords)
            if token not in STOPWORDS and len(_compact(token)) >= 3
        }

        if not shared_targets and not shared_keywords:
            continue

        confidence_score = 0.65
        if shared_targets:
            confidence_score += min(len(shared_targets), 3) * 0.1
        elif shared_keywords:
            confidence_score += min(len(shared_keywords), 2) * 0.05
        confidence_score = min(confidence_score, 0.9)

        _add_edge(
            edges,
            seen_edges,
            source=left_node_id,
            target=right_node_id,
            relation="semantically_related",
            confidence="INFERRED",
            confidence_score=confidence_score,
            source_file=left_path,
            source_location=None,
        )

    return {
        "nodes": nodes,
        "edges": edges,
        "input_tokens": 0,
        "output_tokens": 0,
        "backend": "heuristic",
    }
