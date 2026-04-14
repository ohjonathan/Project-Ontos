"""Context bundle assembly for the MCP `get_context_bundle` tool."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from pathlib import Path
import re
from typing import Any

from ontos.core.snapshot import DocumentSnapshot
from ontos.core.staleness import check_staleness, parse_describes_verified
from ontos.core.tokens import estimate_tokens
from ontos.core.types import DocumentData
from ontos.mcp.tools import TYPE_RANKS

__all__ = ["BundleDocument", "build_context_bundle"]


TOP_INDEGREE_COUNT = 10


@dataclass(frozen=True)
class BundleDocument:
    id: str
    type: str
    status: str
    content: str
    score: float
    token_estimate: int


def build_context_bundle(
    snapshot: DocumentSnapshot,
    workspace_root: Path,
    workspace_slug: str,
    *,
    token_budget: int = 8000,
    max_logs: int = 20,
    log_window_days: int = 30,
) -> dict[str, Any]:
    """Build a token-budgeted context bundle from a workspace snapshot.

    Defaults mirror the addendum v1.2 §A4 bundle values; the MCP tool layer
    passes the values loaded from :class:`PortfolioConfig` explicitly.

    SF-9 (deterministic input ordering): every point where the bundler
    iterates ``snapshot.documents`` is sorted by document ID before any
    downstream sort. Python dict iteration order is insertion-order since
    3.7, but the snapshot loader's insertion order is influenced by
    ``os.listdir``/glob output and so cannot be relied upon for stable
    bundle output. An explicit sort here decouples bundle determinism from
    filesystem iteration quirks.
    """
    docs_by_id = snapshot.documents
    # SF-9: deterministic iteration — sort doc IDs before consuming dict order.
    sorted_doc_ids = sorted(docs_by_id)
    in_degree = {
        doc_id: len(snapshot.graph.reverse_edges.get(doc_id, []))
        for doc_id in sorted_doc_ids
    }
    non_kernel_degrees = [
        in_degree[doc_id]
        for doc_id in sorted_doc_ids
        if docs_by_id[doc_id].type.value != "kernel"
    ]
    max_non_kernel_indegree = max(non_kernel_degrees) if non_kernel_degrees else 0

    scored_docs = [
        _to_bundle_doc(docs_by_id[doc_id], in_degree[doc_id], max_non_kernel_indegree)
        for doc_id in sorted_doc_ids
    ]
    priority_docs = _build_priority_order(
        scored_docs,
        docs_by_id,
        in_degree,
        workspace_root,
        max_logs=max_logs,
        log_window_days=log_window_days,
    )
    included, excluded_count, total_tokens = _greedy_pack(priority_docs, token_budget)
    reordered = _lost_in_middle_order(included)
    stale_documents = _detect_stale_documents(reordered, docs_by_id)

    warnings: list[str] = []
    if excluded_count:
        warnings.append(f"Excluded {excluded_count} documents due to token budget.")

    return {
        "workspace_id": workspace_slug,
        "workspace_slug": workspace_slug,
        "token_estimate": total_tokens,
        "document_count": len(reordered),
        "bundle_text": _render_bundle_text(reordered, total_tokens, excluded_count),
        "included_documents": [
            {
                "id": doc.id,
                "type": doc.type,
                "score": round(doc.score, 4),
                "token_estimate": doc.token_estimate,
            }
            for doc in reordered
        ],
        "excluded_count": excluded_count,
        "stale_documents": stale_documents,
        "warnings": warnings,
    }


def _to_bundle_doc(
    doc: DocumentData,
    in_degree: int,
    max_non_kernel_indegree: int,
) -> BundleDocument:
    if doc.type.value == "kernel":
        score = 1.0
    elif max_non_kernel_indegree > 0:
        score = 0.5 + (0.5 * (in_degree / max_non_kernel_indegree))
    else:
        score = 0.5

    return BundleDocument(
        id=doc.id,
        type=doc.type.value,
        status=doc.status.value,
        content=doc.content or "",
        score=score,
        token_estimate=estimate_tokens(doc.content),
    )


def _build_priority_order(
    docs: list[BundleDocument],
    docs_by_id: dict[str, DocumentData],
    in_degree: dict[str, int],
    workspace_root: Path,
    *,
    max_logs: int,
    log_window_days: int,
) -> list[BundleDocument]:
    kernels = [doc for doc in docs if doc.type == "kernel"]
    kernels.sort(key=lambda doc: (-in_degree.get(doc.id, 0), doc.id))

    recent_logs = _recent_logs(
        docs,
        docs_by_id,
        workspace_root,
        max_logs=max_logs,
        log_window_days=log_window_days,
    )
    recent_log_ids = {doc.id for doc in recent_logs}

    # SF-3 / addendum A4: treat ``max_logs`` and ``log_window_days`` as hard
    # caps on the log entries in the bundle. Logs only enter the bundle via
    # the recent-logs pool (scored at 0.3). Stale logs or logs beyond the
    # ``max_logs`` cap are excluded entirely — otherwise a workspace with
    # dozens of stale logs would blow past ``max_logs`` by re-entering
    # through the ``remaining`` bucket (and would also be silently upgraded
    # to a higher non-kernel score).
    non_kernel = [doc for doc in docs if doc.type != "kernel" and doc.type != "log"]
    high_indegree = sorted(
        non_kernel,
        key=lambda doc: (-in_degree.get(doc.id, 0), doc.id),
    )[:TOP_INDEGREE_COUNT]
    high_indegree_ids = {doc.id for doc in high_indegree}

    remaining = [doc for doc in non_kernel if doc.id not in high_indegree_ids]
    remaining.sort(
        key=lambda doc: (
            TYPE_RANKS.get(doc.type, 99),
            -in_degree.get(doc.id, 0),
            doc.id,
        )
    )

    return kernels + high_indegree + recent_logs + remaining


def _recent_logs(
    docs: list[BundleDocument],
    docs_by_id: dict[str, DocumentData],
    workspace_root: Path,
    *,
    max_logs: int,
    log_window_days: int,
) -> list[BundleDocument]:
    if max_logs <= 0:
        return []

    cutoff = date.today() - timedelta(days=log_window_days)
    dated_logs: list[tuple[date, BundleDocument]] = []

    # SF-9: iterate docs in ID order so the walk that builds `dated_logs`
    # does not depend on upstream dict order before the explicit sort.
    for bundle_doc in sorted(docs, key=lambda d: d.id):
        if bundle_doc.type != "log":
            continue
        source = docs_by_id[bundle_doc.id]
        log_date = _extract_log_date(source, workspace_root)
        if log_date is None or log_date < cutoff:
            continue
        dated_logs.append((log_date, replace(bundle_doc, score=0.3)))

    # SF-4: equal-date tiebreak is *ascending* ID (spec v1.1 §4.2 — "sort
    # alphabetically by document ID" — for LLM-prompt-cache stability).
    # `reverse=True` on a tuple key would reverse both fields, so we sort by
    # (-date_ordinal, id) ascending to get newest-first + alpha-tiebreak.
    dated_logs.sort(key=lambda item: (-item[0].toordinal(), item[1].id))
    return [doc for _, doc in dated_logs[:max_logs]]


def _extract_log_date(doc: DocumentData, workspace_root: Path) -> date | None:
    raw_date = doc.frontmatter.get("date")
    if isinstance(raw_date, datetime):
        return raw_date.date()
    if isinstance(raw_date, date):
        return raw_date
    if isinstance(raw_date, str):
        parsed = _parse_iso_date(raw_date)
        if parsed is not None:
            return parsed

    for text in (doc.id, doc.filepath.name):
        parsed = _parse_iso_date(text)
        if parsed is not None:
            return parsed

    try:
        resolved = doc.filepath.resolve(strict=False)
        if not resolved.is_relative_to(workspace_root.resolve()):
            return None
        if not resolved.exists():
            return None
        return datetime.fromtimestamp(resolved.stat().st_mtime).date()
    except OSError:
        return None


def _parse_iso_date(value: str) -> date | None:
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", value)
    if not match:
        return None
    try:
        return date.fromisoformat(match.group(1))
    except ValueError:
        return None


def _greedy_pack(
    docs: list[BundleDocument],
    token_budget: int,
) -> tuple[list[BundleDocument], int, int]:
    included: list[BundleDocument] = []
    excluded_count = 0
    total_tokens = 0

    for doc in docs:
        if doc.type == "kernel":
            included.append(doc)
            total_tokens += doc.token_estimate
            continue

        if total_tokens + doc.token_estimate <= token_budget:
            included.append(doc)
            total_tokens += doc.token_estimate
        else:
            excluded_count += 1

    return included, excluded_count, total_tokens


def _lost_in_middle_order(docs: list[BundleDocument]) -> list[BundleDocument]:
    ranked = sorted(docs, key=lambda doc: (-doc.score, doc.id))
    ordered: list[BundleDocument | None] = [None] * len(ranked)
    left = 0
    right = len(ranked) - 1

    for index, doc in enumerate(ranked):
        if index % 2 == 0:
            ordered[left] = doc
            left += 1
        else:
            ordered[right] = doc
            right -= 1

    return [doc for doc in ordered if doc is not None]


def _render_bundle_text(
    docs: list[BundleDocument],
    token_estimate: int,
    excluded_count: int,
) -> str:
    sections: list[str] = []
    for doc in docs:
        sections.append(
            f"## {_humanize_id(doc.id)} ({doc.type}, {doc.status})\n\n"
            f"{doc.content}\n\n---"
        )

    body = "\n\n".join(sections)
    footer = (
        f"<!-- Bundle: {len(docs)} documents, ~{token_estimate} tokens, "
        f"{excluded_count} excluded -->"
    )
    if not body:
        return footer
    return f"{body}\n\n{footer}"


def _detect_stale_documents(
    docs: list[BundleDocument],
    docs_by_id: dict[str, DocumentData],
) -> list[dict[str, str]]:
    id_to_path = {
        doc_id: str(doc.filepath)
        for doc_id, doc in docs_by_id.items()
    }
    stale_items: list[dict[str, str]] = []

    for bundle_doc in docs:
        source_doc = docs_by_id.get(bundle_doc.id)
        if source_doc is None:
            continue

        describes = list(source_doc.describes)
        verified = parse_describes_verified(source_doc.frontmatter.get("describes_verified"))
        staleness = check_staleness(
            doc_id=source_doc.id,
            doc_path=str(source_doc.filepath),
            describes=describes,
            describes_verified=verified,
            id_to_path=id_to_path,
        )
        if staleness is None or not staleness.is_stale():
            continue

        stale_atoms = ", ".join(atom for atom, _ in staleness.stale_atoms)
        reason = f"describes targets changed after describes_verified: {stale_atoms}"
        stale_items.append({"id": source_doc.id, "reason": reason})

    return stale_items


def _humanize_id(doc_id: str) -> str:
    return doc_id.replace("_", " ").title()
