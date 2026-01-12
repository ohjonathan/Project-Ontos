"""
Document scaffolding command.

Wrapper module that delegates to the bundled ontos_scaffold.py script.
Full migration to be completed in Phase 4.

Phase 2 Decomposition - Wrapper for ontos/_scripts/ontos_scaffold.py
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional, Any


def scaffold_document(
    doc_type: str,
    doc_id: str,
    target_dir: Optional[Path] = None
) -> Path:
    """Create a new document from template.

    Args:
        doc_type: Type of document (atom, strategy, etc)
        doc_id: ID for the new document
        target_dir: Optional target directory

    Returns:
        Path to created document
    """
    from ontos._scripts.ontos_scaffold import scaffold
    from ontos.ui.output import OutputHandler

    output = OutputHandler()
    return Path(scaffold(doc_type, doc_id, str(target_dir) if target_dir else None, output))


def get_available_templates() -> Dict[str, str]:
    """Get available document templates.

    Returns:
        Dict mapping template name to description
    """
    from ontos._scripts.ontos_scaffold import list_templates
    return list_templates()
