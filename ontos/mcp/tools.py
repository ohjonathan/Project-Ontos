"""Thin MCP adapter layer over Ontos snapshot/map/export primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, Optional

import ontos
from ontos.commands.export_data import _compute_content_hash, _snapshot_to_json
from ontos.commands.map import CompactMode, GenerateMapOptions, generate_context_map
from ontos.core.errors import OntosUserError
from ontos.core.snapshot import DocumentSnapshot
from ontos.core.types import DocumentData, ValidationResult
from ontos.io.snapshot import create_snapshot
from ontos.mcp.scanner import slugify


TYPE_RANKS = {
    "kernel": 0,
    "strategy": 1,
    "product": 2,
    "atom": 3,
    "log": 4,
    "reference": 5,
    "concept": 6,
    "unknown": 7,
}
OVERVIEW_TYPES = ("kernel", "strategy", "product", "atom", "log")
@dataclass(frozen=True)
class CanonicalDocumentRow:
    id: str
    type: str
    status: str
    path: str


@dataclass(frozen=True)
class CanonicalSnapshotView:
    sorted_ids: list[str]
    total_count: int
    overview_by_type: dict[str, int]
    full_by_type: dict[str, int]
    list_rows: list[CanonicalDocumentRow]
    path_lookup: dict[str, str]


def tool_error(message: str) -> dict[str, Any]:
    """Return the normalized MCP tool error envelope."""
    return {
        "isError": True,
        "content": [{"type": "text", "text": message}],
    }


def build_canonical_snapshot_view(
    snapshot: DocumentSnapshot,
    workspace_root: Path,
) -> CanonicalSnapshotView:
    """Build shared count/list/path indexes for the canonical snapshot."""
    overview_by_type = {key: 0 for key in OVERVIEW_TYPES}
    full_by_type: dict[str, int] = {}
    path_lookup: dict[str, str] = {}
    list_rows: list[CanonicalDocumentRow] = []

    sorted_docs = sorted(
        snapshot.documents.values(),
        key=lambda doc: (TYPE_RANKS.get(doc.type.value, 99), doc.id),
    )

    for doc in sorted_docs:
        doc_type = doc.type.value
        doc_status = doc.status.value
        if doc_type in overview_by_type:
            overview_by_type[doc_type] += 1
        full_by_type[doc_type] = full_by_type.get(doc_type, 0) + 1

        rel_path = _workspace_relative_path(doc.filepath, workspace_root)
        list_rows.append(
            CanonicalDocumentRow(
                id=doc.id,
                type=doc_type,
                status=doc_status,
                path=rel_path,
            )
        )
        path_lookup[rel_path] = doc.id

    return CanonicalSnapshotView(
        sorted_ids=[row.id for row in list_rows],
        total_count=len(list_rows),
        overview_by_type=overview_by_type,
        full_by_type=full_by_type,
        list_rows=list_rows,
        path_lookup=path_lookup,
    )


def workspace_overview(cache: Any, *, workspace_id: Optional[str] = None) -> dict[str, Any]:
    """Return structured orientation data for the current workspace."""
    _enforce_workspace_scope(cache, workspace_id)
    key_documents = sorted(
        cache.snapshot.documents.values(),
        key=lambda doc: (-len(cache.snapshot.graph.reverse_edges.get(doc.id, [])), doc.id),
    )[:3]

    warnings = _normalize_warnings(
        cache.snapshot.validation_result,
        cache.snapshot.warnings,
    )[:5]

    summary = (
        f"Workspace {cache.workspace_root.name} contains "
        f"{cache.canonical_view.total_count} canonical documents in docs scope."
    )
    if key_documents:
        summary += " Top key documents: " + ", ".join(doc.id for doc in key_documents) + "."

    return {
        "summary": summary,
        "key_documents": [
            {
                "id": doc.id,
                "title": _humanize_id(doc.id),
                "type": doc.type.value,
                "status": doc.status.value,
            }
            for doc in key_documents
        ],
        "graph_stats": {
            "total": cache.canonical_view.total_count,
            "by_type": dict(cache.canonical_view.overview_by_type),
        },
        "warnings": warnings,
    }


def context_map(
    cache: Any,
    compact: str = "tiered",
    *,
    workspace_id: Optional[str] = None,
) -> dict[str, Any]:
    """Return a wrapped context-map payload."""
    _enforce_workspace_scope(cache, workspace_id)
    compact_key = str(compact).strip().lower()
    compact_modes = {
        "basic": CompactMode.BASIC,
        "rich": CompactMode.RICH,
        "tiered": CompactMode.TIERED,
        "full": CompactMode.OFF,
    }
    if compact_key not in compact_modes:
        raise OntosUserError(
            f"Invalid compact mode '{compact}'. Expected one of basic, rich, tiered, or full.",
            code="E_INVALID_COMPACT",
        )

    config_dict = {
        "project_root": str(cache.workspace_root),
        "project_name": cache.workspace_root.name,
        "version": cache.config.ontos.version,
        "allowed_orphan_types": cache.config.validation.allowed_orphan_types,
        "docs_dir": str(cache.config.paths.docs_dir),
        "logs_dir": str(cache.config.paths.logs_dir),
        "is_contributor_mode": (cache.workspace_root / ".ontos-internal").is_dir(),
    }
    markdown, validation = generate_context_map(
        cache.snapshot.documents,
        config_dict,
        GenerateMapOptions(compact=compact_modes[compact_key]),
    )
    return {
        "markdown": markdown,
        "validation": _validation_payload(validation),
    }


def get_document(
    cache: Any,
    *,
    document_id: Optional[str] = None,
    path: Optional[str] = None,
    include_content: bool = True,
    workspace_id: Optional[str] = None,
) -> dict[str, Any]:
    """Return one canonical document."""
    _enforce_workspace_scope(cache, workspace_id)
    if bool(document_id) == bool(path):
        raise OntosUserError(
            "Provide exactly one of document_id or path.",
            code="E_DOCUMENT_LOOKUP",
        )

    if document_id:
        doc = cache.snapshot.documents.get(document_id)
    else:
        resolved_path, rel_path = _resolve_workspace_path(cache.workspace_root, str(path))
        doc_id = cache.documents_by_path.get(str(resolved_path)) or cache.documents_by_path.get(rel_path)
        doc = cache.snapshot.documents.get(doc_id) if doc_id else None

    if doc is None:
        raise OntosUserError("Document not found.", code="E_DOCUMENT_NOT_FOUND")

    content_hash = _compute_content_hash(doc.content) if doc.content else None
    payload = {
        "id": doc.id,
        "type": doc.type.value,
        "status": doc.status.value,
        "frontmatter": doc.frontmatter,
        "metadata": {
            "content_hash": content_hash,
            "word_count": len(doc.content.split()),
            "depended_by": sorted(cache.snapshot.graph.reverse_edges.get(doc.id, [])),
        },
    }
    if include_content:
        payload["content"] = doc.content
    return payload


def list_documents(
    cache: Any,
    *,
    type: Optional[str] = None,
    status: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
    workspace_id: Optional[str] = None,
) -> dict[str, Any]:
    """Return paginated canonical document rows."""
    _enforce_workspace_scope(cache, workspace_id)
    if offset < 0:
        raise OntosUserError("offset must be >= 0.", code="E_INVALID_OFFSET")
    if limit <= 0:
        raise OntosUserError("limit must be > 0.", code="E_INVALID_LIMIT")

    rows = [
        row for row in cache.canonical_view.list_rows
        if (type is None or row.type == type)
        and (status is None or row.status == status)
    ]
    total_count = len(rows)
    page = rows[offset:offset + limit]
    return {
        "total_count": total_count,
        "offset": offset,
        "documents": [row.__dict__ for row in page],
    }


def export_graph(
    cache: Any,
    *,
    summary_only: bool = True,
    export_to_file: Optional[str] = None,
    workspace_id: Optional[str] = None,
) -> dict[str, Any]:
    """Return or persist a canonical export payload."""
    _enforce_workspace_scope(cache, workspace_id)
    raw_payload = _snapshot_to_json(cache.snapshot, filters=None, deterministic=False)
    ordered_payload = _ordered_export_payload(raw_payload, cache.snapshot)

    if export_to_file:
        resolved_path, rel_path = _resolve_workspace_path(cache.workspace_root, export_to_file)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.write_text(json.dumps(ordered_payload, indent=2), encoding="utf-8")
        return {
            "success": True,
            "path": rel_path,
            "doc_count": cache.canonical_view.total_count,
        }

    if summary_only:
        node_ids = ordered_payload["graph"]["nodes"]
        nodes = [
            {
                "id": doc_id,
                "type": cache.snapshot.documents[doc_id].type.value,
                "status": cache.snapshot.documents[doc_id].status.value,
            }
            for doc_id in node_ids
        ]
        return {
            "summary": ordered_payload["summary"],
            "graph": {
                "nodes": nodes,
                "edges": ordered_payload["graph"]["edges"],
            },
        }

    ordered_payload["validation"] = _validation_payload(cache.snapshot.validation_result)
    return ordered_payload


def query(cache: Any, *, entity_id: str, workspace_id: Optional[str] = None) -> dict[str, Any]:
    """Return structured graph details for one document."""
    _enforce_workspace_scope(cache, workspace_id)
    doc = cache.snapshot.documents.get(entity_id)
    if doc is None:
        raise OntosUserError("Document not found.", code="E_DOCUMENT_NOT_FOUND")

    return {
        "id": doc.id,
        "type": doc.type.value,
        "status": doc.status.value,
        "depends_on": list(doc.depends_on),
        "depended_by": sorted(cache.snapshot.graph.reverse_edges.get(doc.id, [])),
        "depth": cache.depths.get(doc.id, 0),
        "content_hash": _compute_content_hash(doc.content) if doc.content else None,
    }


def health(cache: Any, *, workspace_id: Optional[str] = None) -> dict[str, Any]:
    """Return server/cache health state."""
    _enforce_workspace_scope(cache, workspace_id)
    uptime = max(0, int((datetime.now(timezone.utc) - cache.started_at).total_seconds()))
    return {
        "server_uptime": uptime,
        "workspace": cache.workspace_root.name,
        "workspace_path": str(cache.workspace_root),
        "doc_count": cache.canonical_view.total_count,
        "last_indexed": _to_utc_z(cache.last_indexed),
        "ontos_version": ontos.__version__,
        "snapshot_revision": cache.snapshot_revision,
        "freshness_mode": cache.freshness_mode,
    }


def refresh(cache: Any, *, workspace_id: Optional[str] = None) -> dict[str, Any]:
    """Force a cache rebuild and return the observable state change."""
    _enforce_workspace_scope(cache, workspace_id)
    _snapshot, duration_ms = cache.force_refresh()
    return {
        "refreshed": True,
        "doc_count": cache.canonical_view.total_count,
        "duration_ms": duration_ms,
    }


def project_registry(portfolio_index: Any) -> dict[str, Any]:
    """Return the complete project inventory from the portfolio index."""
    if portfolio_index is None:
        raise OntosUserError(
            "project_registry is available only in portfolio mode.",
            code="E_PORTFOLIO_REQUIRED",
        )
    projects = portfolio_index.get_projects()
    return {
        "project_count": len(projects),
        "projects": [
            {
                "slug": p["slug"],
                "path": p["path"],
                "status": p["status"],
                "doc_count": p["doc_count"],
                "last_updated": p["last_scanned"],
                "tags": _parse_project_tags(p.get("tags")),
                "has_ontos": bool(p["has_ontos"]),
            }
            for p in projects
        ],
        "summary": f"Portfolio contains {len(projects)} projects.",
    }


def search(
    portfolio_index: Any,
    *,
    query_string: str,
    workspace_id: Optional[str] = None,
    offset: int = 0,
    limit: int = 20,
) -> dict[str, Any]:
    """Full-text search across the portfolio or a single workspace."""
    if portfolio_index is None:
        raise OntosUserError(
            "search is available only in portfolio mode.",
            code="E_PORTFOLIO_REQUIRED",
        )
    if not query_string or not query_string.strip():
        raise OntosUserError(
            "query_string must be non-empty.",
            code="E_EMPTY_QUERY",
        )
    if limit < 1 or limit > 100:
        raise OntosUserError(
            "limit must be between 1 and 100.",
            code="E_INVALID_LIMIT",
        )
    if offset < 0:
        raise OntosUserError(
            "offset must be >= 0.",
            code="E_INVALID_OFFSET",
        )
    if workspace_id is not None:
        _validate_workspace_id(portfolio_index, workspace_id)
    try:
        return portfolio_index.search_fts(query_string, workspace_id, offset, limit)
    except sqlite3.OperationalError as exc:
        raise OntosUserError(
            "Invalid search query syntax.",
            code="E_INVALID_QUERY",
            details=str(exc),
        ) from exc


def get_context_bundle(
    portfolio_index: Any,
    cache: Any,
    *,
    workspace_id: Optional[str] = None,
    token_budget: int = 8192,
) -> dict[str, Any]:
    """Return a token-budgeted context package for a workspace."""
    from ontos.mcp.bundler import build_context_bundle

    if token_budget < 1024:
        raise OntosUserError(
            "token_budget must be at least 1024.",
            code="E_INVALID_BUDGET",
        )
    if token_budget > 128000:
        raise OntosUserError(
            "token_budget must be at most 128000.",
            code="E_INVALID_BUDGET",
        )

    if portfolio_index is None:
        slug = _slugify_workspace_name(cache.workspace_root.name)
        snapshot = cache.get_fresh_snapshot()
        workspace_root = cache.workspace_root
    elif workspace_id is None:
        raise OntosUserError(
            "workspace_id is required in portfolio mode. "
            "Use project_registry() to discover available workspaces.",
            code="E_MISSING_WORKSPACE",
        )
    else:
        _validate_workspace_id(portfolio_index, workspace_id)
        projects = portfolio_index.get_projects()
        project = next((item for item in projects if item["slug"] == workspace_id), None)
        if project is None:
            raise OntosUserError(
                f"Unknown workspace '{workspace_id}'.",
                code="E_UNKNOWN_WORKSPACE",
            )
        if project["status"] == "undocumented":
            raise OntosUserError(
                f"Workspace '{workspace_id}' is undocumented. "
                "Run `ontos init` in that project directory first.",
                code="E_UNDOCUMENTED_WORKSPACE",
            )
        slug = workspace_id
        workspace_root = Path(project["path"]).resolve()
        snapshot = create_snapshot(
            root=workspace_root,
            include_content=True,
            filters=None,
            git_commit_provider=None,
            scope=None,
        )

    return build_context_bundle(
        snapshot,
        workspace_root,
        slug,
        token_budget=token_budget,
    )


def _humanize_id(doc_id: str) -> str:
    return doc_id.replace("_", " ").title()


def _parse_project_tags(raw: Any) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    return []


def _validate_workspace_id(portfolio_index: Any, workspace_id: str) -> None:
    """Validate workspace_id exists in portfolio. Raise OntosUserError if not."""
    if portfolio_index is None:
        raise OntosUserError(
            "workspace_id requires portfolio mode.",
            code="E_PORTFOLIO_REQUIRED",
        )
    projects = portfolio_index.get_projects()
    slugs = [project["slug"] for project in projects]
    if workspace_id not in slugs:
        sorted_slugs = ", ".join(sorted(slugs))
        raise OntosUserError(
            f"Unknown workspace '{workspace_id}'. "
            f"Valid workspace slugs: {sorted_slugs}. "
            "Use project_registry() to discover available workspaces.",
            code="E_UNKNOWN_WORKSPACE",
        )


def _enforce_workspace_scope(cache: Any, workspace_id: Optional[str]) -> None:
    if workspace_id is None:
        return
    if not _is_portfolio_mode(cache):
        return
    primary_workspace = _primary_workspace_slug(cache)
    if workspace_id == primary_workspace:
        return
    raise OntosUserError(
        "Cross-workspace reads are not supported in this tool yet. "
        "Start a separate `ontos serve` in the target workspace.",
        code="E_CROSS_WORKSPACE_NOT_SUPPORTED",
    )


def _is_portfolio_mode(cache: Any) -> bool:
    return bool(
        getattr(cache, "portfolio_mode", False)
        or getattr(cache, "is_portfolio_mode", False)
        or getattr(cache, "portfolio_enabled", False)
        or getattr(cache, "portfolio_index", None) is not None
    )


def _primary_workspace_slug(cache: Any) -> str:
    for attr in ("primary_workspace_slug", "workspace_slug", "workspace_id"):
        value = getattr(cache, attr, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return _slugify_workspace_name(cache.workspace_root.name)


def _slugify_workspace_name(raw: str) -> str:
    return slugify(raw)


def _normalize_warnings(
    validation: ValidationResult,
    snapshot_warnings: list[str],
) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    warnings.extend(_validation_issues(validation.errors))
    warnings.extend(_validation_issues(validation.warnings))
    warnings.extend({"severity": "warning", "message": message} for message in snapshot_warnings)
    return warnings


def _validation_payload(validation: ValidationResult) -> dict[str, Any]:
    return {
        "errors": _validation_issues(validation.errors),
        "warnings": _validation_issues(validation.warnings),
    }


def _validation_issues(issues: list[Any]) -> list[dict[str, str]]:
    return [
        {
            "severity": issue.severity,
            "message": issue.message,
        }
        for issue in issues
    ]


def _ordered_export_payload(
    raw_payload: dict[str, Any],
    snapshot: DocumentSnapshot,
) -> dict[str, Any]:
    ordered_documents = sorted(raw_payload["documents"], key=lambda doc: doc["id"])
    ordered_nodes = sorted(raw_payload["graph"]["nodes"])
    ordered_edges = sorted(
        raw_payload["graph"]["edges"],
        key=lambda edge: (edge["from"], edge["to"], edge["type"]),
    )
    ordered_summary = dict(raw_payload["summary"])
    ordered_summary["by_type"] = dict(sorted(raw_payload["summary"]["by_type"].items()))
    ordered_summary["by_status"] = dict(sorted(raw_payload["summary"]["by_status"].items()))
    if "warnings" in raw_payload["summary"]:
        ordered_summary["warnings"] = list(raw_payload["summary"]["warnings"])

    return {
        "schema_version": raw_payload["schema_version"],
        "provenance": raw_payload["provenance"],
        "filters": raw_payload["filters"],
        "summary": ordered_summary,
        "documents": ordered_documents,
        "graph": {
            "nodes": ordered_nodes,
            "edges": ordered_edges,
        },
    }


def _resolve_workspace_path(workspace_root: Path, raw_path: str) -> tuple[Path, str]:
    user_path = Path(raw_path)
    if raw_path.startswith("~"):
        user_path = user_path.expanduser()
    if not user_path.is_absolute():
        user_path = workspace_root / user_path
    resolved = user_path.resolve(strict=False)
    workspace_resolved = workspace_root.resolve()
    if not resolved.is_relative_to(workspace_resolved):
        raise OntosUserError(
            "Path must resolve inside the workspace root.",
            code="E_PATH_OUTSIDE_WORKSPACE",
        )
    return resolved, resolved.relative_to(workspace_resolved).as_posix()


def _workspace_relative_path(path: Path, workspace_root: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve()).as_posix()


def _to_utc_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
