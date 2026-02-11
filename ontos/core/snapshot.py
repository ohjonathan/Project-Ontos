"""
Snapshot primitive for document collection.

Creates an immutable snapshot of all documents at a point in time.
Used by export and migration commands.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ontos.core.types import DocumentData, ValidationResult
from ontos.core.graph import DependencyGraph, build_graph
from ontos.core.validation import ValidationOrchestrator


@dataclass
class SnapshotFilters:
    """Filters for document selection."""
    types: Optional[List[str]] = None
    status: Optional[List[str]] = None
    concepts: Optional[List[str]] = None


@dataclass
class DocumentSnapshot:
    """Immutable snapshot of all documents at a point in time."""
    timestamp: datetime
    project_root: Path
    documents: Dict[str, DocumentData]
    graph: DependencyGraph
    validation_result: ValidationResult
    git_commit: Optional[str] = None
    ontos_version: str = ""
    warnings: List[str] = field(default_factory=list)

    @property
    def by_type(self) -> Dict[str, List[DocumentData]]:
        """Group documents by type."""
        result: Dict[str, List[DocumentData]] = {}
        for doc in self.documents.values():
            doc_type = doc.type.value if hasattr(doc.type, 'value') else str(doc.type)
            if doc_type not in result:
                result[doc_type] = []
            result[doc_type].append(doc)
        return result

    @property
    def by_status(self) -> Dict[str, List[DocumentData]]:
        """Group documents by status."""
        result: Dict[str, List[DocumentData]] = {}
        for doc in self.documents.values():
            doc_status = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)
            if doc_status not in result:
                result[doc_status] = []
            result[doc_status].append(doc)
        return result


def matches_filter(doc: DocumentData, filters: Optional[SnapshotFilters]) -> bool:
    """Check if document matches filter criteria."""
    if filters is None:
        return True

    # Type filter
    if filters.types:
        doc_type = doc.type.value if hasattr(doc.type, 'value') else str(doc.type)
        if doc_type not in filters.types:
            return False

    # Status filter
    if filters.status:
        doc_status = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)
        if doc_status not in filters.status:
            return False

    # Concept filter
    if filters.concepts:
        doc_concepts = set(doc.tags)
        if not doc_concepts.intersection(set(filters.concepts)):
            return False

    return True
