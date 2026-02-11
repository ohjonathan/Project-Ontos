"""
Export data command — bulk document export to JSON.
"""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from ontos.core.snapshot import SnapshotFilters
from ontos.io.snapshot import create_snapshot, DocumentSnapshot
from ontos.core.migration import classify_documents
from ontos.io.files import find_project_root


@dataclass
class ExportDataOptions:
    """Options for export data command."""
    output_path: Optional[Path] = None
    types: Optional[str] = None  # Comma-separated
    status: Optional[str] = None  # Comma-separated
    concepts: Optional[str] = None  # Comma-separated
    no_content: bool = False
    deterministic: bool = False
    force: bool = False
    quiet: bool = False
    json_output: bool = False


def _parse_csv(value: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated string to list."""
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def _compute_content_hash(content: str) -> str:
    """Compute SHA256 hash of content."""
    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]}"


def _snapshot_to_json(
    snapshot: DocumentSnapshot,
    filters: Optional[SnapshotFilters],
    deterministic: bool = False,
) -> Dict[str, Any]:
    """Convert snapshot to JSON-serializable dict."""
    import ontos

    from ontos.core.snapshot import matches_filter
    from ontos.core.migration import classify_documents

    # Get migration classifications
    report = classify_documents(snapshot)
 
    # Build documents list
    documents = []
    included_ids = set()
    for doc_id in sorted(snapshot.documents.keys()) if deterministic else snapshot.documents.keys():
        doc = snapshot.documents[doc_id]
        
        # Apply filters during serialization (B2)
        if not matches_filter(doc, filters):
            continue

        included_ids.add(doc_id)
        classification = report.classifications.get(doc_id)

        doc_type = doc.type.value if hasattr(doc.type, 'value') else str(doc.type)
        doc_status = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)

        doc_dict = {
            "id": doc.id,
            "type": doc_type,
            "status": doc_status,
            "path": str(doc.filepath),
            "depends_on": sorted(doc.depends_on) if deterministic else doc.depends_on,
            "concepts": sorted(doc.tags) if deterministic else doc.tags,
            "decision_summary": doc.frontmatter.get("decision_summary"),
            "decision_rationale": doc.frontmatter.get("decision_rationale"),
            "alternatives_rejected": doc.frontmatter.get("alternatives_rejected"),
            "migration_status": doc.frontmatter.get("migration_status"),
            "migration_status_reason": doc.frontmatter.get("migration_status_reason"),
            "inferred_migration_status": classification.inferred_status if classification else None,
            "effective_migration_status": classification.effective_status if classification else None,
            "content": doc.content if doc.content else None,
            "content_hash": _compute_content_hash(doc.content) if doc.content else None,
        }
        documents.append(doc_dict)

    # Build graph edges
    edges = []
    for doc_id in sorted(snapshot.graph.edges.keys()) if deterministic else snapshot.graph.edges.keys():
        if doc_id not in included_ids:
            continue
        for dep_id in sorted(snapshot.graph.edges[doc_id]) if deterministic else snapshot.graph.edges[doc_id]:
            # Optional: should we include edges to non-exported docs?
            # Re-Architecture spec says: classification reflects position in COMPLETE graph.
            # But the export should probably only show edges between exported docs for clarity.
            if dep_id in included_ids:
                edges.append({
                    "from": doc_id,
                    "to": dep_id,
                    "type": "depends_on"
                })

    # Build provenance
    provenance = {
        "exported_at": "deterministic" if deterministic else datetime.now().isoformat(),
        "ontos_version": ontos.__version__,
        "git_commit": "deterministic" if deterministic else snapshot.git_commit,
        "project_root": str(snapshot.project_root),
    }

    # Build summary (only for included documents)
    by_type: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    for doc_id in included_ids:
        doc = snapshot.documents[doc_id]
        doc_type = doc.type.value if hasattr(doc.type, 'value') else str(doc.type)
        doc_status = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)
        by_type[doc_type] = by_type.get(doc_type, 0) + 1
        by_status[doc_status] = by_status.get(doc_status, 0) + 1

    result = {
        "schema_version": "ontos-export-v1",
        "provenance": provenance,
        "filters": {
            "types": filters.types if filters else None,
            "status": filters.status if filters else None,
            "concepts": filters.concepts if filters else None,
        },
        "summary": {
            "total_documents": len(documents),
            "by_type": dict(sorted(by_type.items())) if deterministic else by_type,
            "by_status": dict(sorted(by_status.items())) if deterministic else by_status,
        },
        "documents": documents,
        "graph": {
            "nodes": sorted(list(included_ids)) if deterministic else list(included_ids),
            "edges": edges,
        },
    }

    # S2: Include parse warnings if any
    if snapshot.warnings:
        result["summary"]["warnings"] = snapshot.warnings

    return result


def export_data_command(options: ExportDataOptions) -> Tuple[int, str]:
    """
    Export documents as structured JSON.

    Returns:
        Tuple of (exit_code, message)
    """
    try:
        root = find_project_root()
    except Exception as e:
        return 1, f"Error: {e}"

    # Check output file
    if options.output_path:
        if options.output_path.exists() and not options.force:
            return 1, f"Error: Output file exists: {options.output_path}. Use --force to overwrite."

    # Create FULL snapshot first for accurate migration classification (B2)
    full_snapshot = create_snapshot(
        root=root,
        include_content=not options.no_content,
        filters=None,  # Get everything
    )

    # Convert to JSON with filters applied during serialization
    filters = SnapshotFilters(
        types=_parse_csv(options.types),
        status=_parse_csv(options.status),
        concepts=_parse_csv(options.concepts),
    )
    data = _snapshot_to_json(full_snapshot, filters, options.deterministic)

    # Serialize
    if options.deterministic:
        json_str = json.dumps(data, indent=2, sort_keys=True)
    else:
        json_str = json.dumps(data, indent=2)

    # Output
    if options.output_path:
        try:
            options.output_path.parent.mkdir(parents=True, exist_ok=True)
            options.output_path.write_text(json_str, encoding='utf-8')
        except (IOError, OSError) as e:
            # S1: Improved error handling
            return 1, f"Error writing to {options.output_path}: {e}"
        return 0, f"Exported {len(data['documents'])} documents to {options.output_path}"
    else:
        # Print to stdout (handled by CLI layer)
        return 0, json_str
