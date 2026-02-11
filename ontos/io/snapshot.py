"""
IO-layer wrapper for runtime snapshot assembly.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

import ontos
from ontos.core.types import DocumentData
from ontos.core.snapshot import DocumentSnapshot, SnapshotFilters, matches_filter
from ontos.core.graph import build_graph
from ontos.core.validation import ValidationOrchestrator
from ontos.io.config import load_project_config
from ontos.io.files import scan_documents, load_documents
from ontos.io.yaml import parse_frontmatter_content

def create_snapshot(
    root: Path,
    include_content: bool = True,
    filters: Optional[SnapshotFilters] = None,
    git_commit_provider: Optional[Callable[[], Optional[str]]] = None,
) -> DocumentSnapshot:
    """
    Create a snapshot of all documents using the canonical loader.

    Args:
        root: Project root directory
        include_content: Whether to include document content
        filters: Optional filters (type, status, concept)
        git_commit_provider: Optional callback to get git commit hash

    Returns:
        Immutable DocumentSnapshot
    """
    # Load config
    config = load_project_config(repo_root=root)

    # Determine docs directory
    docs_dir = root / config.paths.docs_dir
    internal_dir = root / ".ontos-internal"

    scan_dirs = []
    if docs_dir.exists():
        scan_dirs.append(docs_dir)
    if internal_dir.exists():
        scan_dirs.append(internal_dir)

    # Scan documents
    skip_patterns = config.scanning.skip_patterns if config.scanning else ["_template.md", "archive/*"]
    doc_paths = scan_documents(scan_dirs, skip_patterns=skip_patterns)

    # Load documents using unified loader
    load_result = load_documents(doc_paths, parse_frontmatter_content)
    documents = load_result.documents
    warnings = [issue.message for issue in load_result.issues]

    # Apply filters
    filtered_docs: Dict[str, DocumentData] = {}
    for doc_id, doc in documents.items():
        if matches_filter(doc, filters):
            if not include_content:
                # Strip content
                doc = DocumentData(
                    id=doc.id,
                    type=doc.type,
                    status=doc.status,
                    filepath=doc.filepath,
                    frontmatter=doc.frontmatter,
                    content="",
                    depends_on=doc.depends_on,
                    impacts=doc.impacts,
                    tags=doc.tags,
                    aliases=doc.aliases,
                    describes=doc.describes
                )
            filtered_docs[doc_id] = doc

    # Build graph
    graph, _ = build_graph(filtered_docs)

    # Run structural validation only (no vocabulary check).
    # Snapshot is an IO-layer operation — vocabulary checking requires
    # project-level config (known_concepts) which is a command-layer concern.
    orchestrator = ValidationOrchestrator(filtered_docs, {})
    validation_result = orchestrator.validate_all()
    
    # Get git commit
    git_commit = None
    if git_commit_provider:
        try:
            git_commit = git_commit_provider()
        except Exception:
            pass

    return DocumentSnapshot(
        timestamp=datetime.now(),
        project_root=root,
        documents=filtered_docs,
        graph=graph,
        validation_result=validation_result,
        git_commit=git_commit,
        ontos_version=ontos.__version__,
        warnings=warnings
    )
