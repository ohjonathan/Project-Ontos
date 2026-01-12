"""Shared utilities for Ontos scripts.

DEPRECATED: Import from ontos.core instead.
============================================
This module re-exports functions from their new locations in the ontos package.

    # OLD (still works via this shim)
    from ontos_lib import parse_frontmatter, SessionContext

    # NEW (preferred for new code)
    from ontos.core.frontmatter import parse_frontmatter
    from ontos.core.context import SessionContext

DEPRECATION TIMELINE:
- v2.8: Silent operation (no warnings)
- v2.9.2: FutureWarning on import - YOU ARE HERE
- v3.0: Module removed, use ontos package directly
"""

# v2.9.2: Emit FutureWarning on import (visible by default)
import warnings
warnings.warn(
    "Importing from 'ontos_lib' is deprecated. "
    "Import from 'ontos.core' instead. "
    "This module will be removed in v3.0. "
    "See: docs/reference/Ontos_Manual.md#migration-guide",
    FutureWarning,
    stacklevel=2
)

# =============================================================================
# RE-EXPORTS FROM NEW PACKAGE STRUCTURE
# =============================================================================
# These are the ONLY imports needed - all function definitions have been moved
# to their respective modules in ontos/core/

# Context
from ontos.core.context import SessionContext, FileOperation, PendingWrite

# Frontmatter parsing
from ontos.core.frontmatter import (
    parse_frontmatter,
    normalize_depends_on,
    normalize_type,
    load_common_concepts,
)

# Staleness detection
from ontos.core.staleness import (
    ModifiedSource,
    normalize_describes,
    parse_describes_verified,
    validate_describes_field,
    detect_describes_cycles,
    check_staleness,
    get_file_modification_date,
    clear_git_cache,
    DescribesValidationError,
    DescribesWarning,
    StalenessInfo,
)

# History generation
from ontos.core.history import (
    ParsedLog,
    parse_log_for_history,
    sort_logs_deterministically,
    generate_decision_history,
    get_log_date,
)

# Path helpers
from ontos.core.paths import (
    resolve_config,
    get_logs_dir,
    get_log_count,
    get_logs_older_than,
    get_archive_dir,
    get_decision_history_path,
    get_proposals_dir,
    get_archive_logs_dir,
    get_archive_proposals_dir,
    get_concepts_path,
    find_last_session_date,
    _warn_deprecated,
)

# Config helpers
from ontos.core.config import (
    BLOCKED_BRANCH_NAMES,
    get_source,
    get_git_last_modified,
)

# Proposal helpers
from ontos.core.proposals import (
    load_decision_history_entries,
    find_draft_proposals,
)

# UI
from ontos.ui.output import OutputHandler

# Version
from ontos import __version__
