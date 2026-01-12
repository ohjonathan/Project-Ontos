"""
Document query command.

Wrapper module that delegates to the bundled ontos_query.py script.
Full migration to be completed in Phase 4.

Phase 2 Decomposition - Wrapper for ontos/_scripts/ontos_query.py
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional, Any


def query_documents(
    query: str,
    doc_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Query documents matching criteria.

    Args:
        query: Search query string
        doc_type: Filter by document type
        status: Filter by status
        limit: Maximum results to return

    Returns:
        List of matching document dicts
    """
    # Import from bundled script
    from ontos._scripts.ontos_query import query_context_map

    return query_context_map(query, doc_type, status, limit)


def get_document_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
    """Get document by ID.

    Args:
        doc_id: Document ID to look up

    Returns:
        Document dict or None if not found
    """
    from ontos._scripts.ontos_query import get_document_info
    return get_document_info(doc_id)
