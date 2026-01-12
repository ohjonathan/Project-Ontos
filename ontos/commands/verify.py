"""
Document verification command.

Wrapper module that delegates to the bundled ontos_verify.py script.
Full migration to be completed in Phase 4.

Phase 2 Decomposition - Wrapper for ontos/_scripts/ontos_verify.py
"""

from __future__ import annotations
from datetime import date
from pathlib import Path
from typing import List, Dict, Optional, Any

# Re-export key functions from bundled script for API compatibility
# These will be migrated to native implementations in Phase 4


def verify_document(
    filepath: Path,
    verify_date: Optional[date] = None
) -> int:
    """Verify a document as current.

    Args:
        filepath: Path to document to verify
        verify_date: Date to set (defaults to today)

    Returns:
        0 on success, 1 on failure
    """
    # Import from bundled script
    from ontos._scripts.ontos_verify import verify_single
    from ontos.ui.output import OutputHandler

    output = OutputHandler()
    return verify_single(str(filepath), verify_date, output)


def find_stale_documents() -> List[Dict[str, Any]]:
    """Find all documents with stale describes fields.

    Returns:
        List of dicts with 'doc_id', 'filepath', 'stale_atoms' info
    """
    from ontos._scripts.ontos_verify import find_stale_documents as _find_stale
    return _find_stale()


def verify_all_interactive() -> int:
    """Interactively verify all stale documents.

    Returns:
        0 on success, 1 on failure
    """
    from ontos._scripts.ontos_verify import verify_all_interactive as _verify_all
    from ontos.ui.output import OutputHandler

    return _verify_all(OutputHandler())
