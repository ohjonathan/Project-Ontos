"""
Schema migration command.

Wrapper module that delegates to the bundled ontos_migrate_schema.py script.
Full migration to be completed in Phase 4.

Phase 2 Decomposition - Wrapper for ontos/_scripts/ontos_migrate_schema.py
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional, Any


def migrate_schema(
    target_version: str,
    dry_run: bool = False
) -> int:
    """Migrate documents to a new schema version.

    Args:
        target_version: Target schema version
        dry_run: If True, don't make changes

    Returns:
        0 on success, 1 on failure
    """
    from ontos._scripts.ontos_migrate_schema import migrate_all
    from ontos.ui.output import OutputHandler

    output = OutputHandler()
    return migrate_all(target_version, dry_run, output)


def check_schema_version() -> str:
    """Get current schema version.

    Returns:
        Current schema version string
    """
    from ontos._scripts.ontos_migrate_schema import get_current_version
    return get_current_version()
