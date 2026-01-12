"""
Log consolidation command.

Wrapper module that delegates to the bundled ontos_consolidate.py script.
Full migration to be completed in Phase 4.

Phase 2 Decomposition - Wrapper for ontos/_scripts/ontos_consolidate.py
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import date


def consolidate_logs(
    before_date: Optional[date] = None,
    dry_run: bool = False
) -> int:
    """Consolidate old session logs.

    Args:
        before_date: Consolidate logs before this date
        dry_run: If True, don't make changes

    Returns:
        0 on success, 1 on failure
    """
    from ontos._scripts.ontos_consolidate import consolidate
    from ontos.ui.output import OutputHandler

    output = OutputHandler()
    return consolidate(before_date, dry_run, output)


def get_consolidation_candidates(
    before_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Get logs that would be consolidated.

    Args:
        before_date: Check logs before this date

    Returns:
        List of log dicts that would be consolidated
    """
    from ontos._scripts.ontos_consolidate import find_candidates
    return find_candidates(before_date)
