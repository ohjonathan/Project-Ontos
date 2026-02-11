"""Core module - Pure logic layer.

This module contains pure functions and classes that do NOT perform I/O,
except for functions explicitly marked as IMPURE in their docstrings.

IMPURE functions (Phase 1 legacy - to be refactored):
    - staleness.get_file_modification_date() - calls git subprocess
    - staleness.check_staleness() - uses get_file_modification_date()
    - config.get_source() - calls git subprocess
    - config.get_git_last_modified() - calls git subprocess
    - paths.* - most functions use os.path.exists()
"""

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
)

# Config helpers
from ontos.core.config import (
    BLOCKED_BRANCH_NAMES,
    get_source,
    get_git_last_modified,
    # Phase 3: Config System
    ConfigError,
    OntosConfig,
    OntosSection,
    PathsConfig,
    ScanningConfig,
    ValidationConfig,
    WorkflowConfig,
    HooksConfig,
    default_config,
    config_to_dict,
    dict_to_config,
)

# Proposal helpers
from ontos.core.proposals import (
    load_decision_history_entries,
    find_draft_proposals,
)

# Ontology definitions (v2.9.6+)
from ontos.core.ontology import (
    TypeDefinition,
    FieldDefinition,
    TYPE_DEFINITIONS,
    FIELD_DEFINITIONS,
    get_type_hierarchy,
    get_valid_types,
    get_valid_type_status,
)

# Phase 2 additions: Types
from ontos.core.types import (
    DocumentType,
    DocumentStatus,
    ValidationErrorType,
    DocumentData,
    ValidationError,
    ValidationResult,
    TEMPLATES,
    SECTION_TEMPLATES,
    CurationLevel,
)

# Phase 2 additions: Token estimation
from ontos.core.tokens import (
    estimate_tokens,
    format_token_count,
)

# Phase 2 additions: Graph
from ontos.core.graph import (
    GraphNode,
    DependencyGraph,
    build_graph,
    detect_cycles,
    detect_orphans,
    calculate_depths,
)

# Phase 2 additions: Suggestions
from ontos.core.suggestions import (
    load_document_index,
    load_common_concepts as load_common_concepts_from_map,
    suggest_impacts,
    validate_concepts,
)

# Phase 2 additions: Validation
from ontos.core.validation import (
    ValidationOrchestrator,
    validate_describes_field as validate_describes_field_v2,
)

