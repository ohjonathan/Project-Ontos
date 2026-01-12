"""
Proposal promotion command.

Wrapper module that delegates to the bundled ontos_promote.py script.
Full migration to be completed in Phase 4.

Phase 2 Decomposition - Wrapper for ontos/_scripts/ontos_promote.py
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional, Any


def promote_proposal(
    proposal_id: str,
    target_path: Optional[Path] = None
) -> int:
    """Promote a proposal to strategy document.

    Args:
        proposal_id: ID of proposal to promote
        target_path: Optional target path for promoted doc

    Returns:
        0 on success, 1 on failure
    """
    from ontos._scripts.ontos_promote import promote
    from ontos.ui.output import OutputHandler

    output = OutputHandler()
    return promote(proposal_id, str(target_path) if target_path else None, output)


def find_promotable_proposals() -> List[Dict[str, Any]]:
    """Find proposals ready for promotion.

    Returns:
        List of proposal dicts with status 'approved'
    """
    from ontos._scripts.ontos_promote import find_approved_proposals
    return find_approved_proposals()
