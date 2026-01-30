"""Ontos - Context Management System.

v2.8: Unified package structure for clean architecture.

Package structure:
    ontos.core - Pure logic (no I/O except marked impure functions)
    ontos.ui   - I/O layer (CLI, output, prompts)
"""

__version__ = "3.2.0"

# Re-export commonly used items for convenience
from ontos.core.context import SessionContext, FileOperation, PendingWrite
from ontos.core.frontmatter import parse_frontmatter, normalize_depends_on, normalize_type
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
from ontos.core.history import (
    ParsedLog,
    parse_log_for_history,
    sort_logs_deterministically,
    generate_decision_history,
    get_log_date,
)
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
)
from ontos.core.config import (
    BLOCKED_BRANCH_NAMES,
    get_source,
    get_git_last_modified,
)
from ontos.core.proposals import (
    load_decision_history_entries,
    find_draft_proposals,
)
from ontos.ui.output import OutputHandler
