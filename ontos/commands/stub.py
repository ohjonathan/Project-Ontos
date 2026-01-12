"""
Document stub creation command.

Wrapper module that delegates to the bundled ontos_stub.py script.
Full migration to be completed in Phase 4.

Phase 2 Decomposition - Wrapper for ontos/_scripts/ontos_stub.py
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Any


def create_stub(
    doc_id: str,
    doc_type: str = "atom",
    target_dir: Optional[Path] = None
) -> Path:
    """Create a minimal stub document.

    Args:
        doc_id: ID for the stub document
        doc_type: Type of document (default: atom)
        target_dir: Optional target directory

    Returns:
        Path to created stub
    """
    from ontos._scripts.ontos_stub import create
    from ontos.ui.output import OutputHandler

    output = OutputHandler()
    return Path(create(doc_id, doc_type, str(target_dir) if target_dir else None, output))


def create_stubs_for_missing(
    doc_ids: List[str]
) -> List[Path]:
    """Create stubs for missing document IDs.

    Args:
        doc_ids: List of document IDs to stub

    Returns:
        List of paths to created stubs
    """
    from ontos._scripts.ontos_stub import create_missing
    return [Path(p) for p in create_missing(doc_ids)]
