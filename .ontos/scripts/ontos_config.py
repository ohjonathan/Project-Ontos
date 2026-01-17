"""Ontos configuration - User customizations.

This file imports defaults from ontos_config_defaults.py and allows you to
override any settings for your project. This file is NEVER touched by
ontos_update.py, so your customizations are safe.

To customize a setting, simply reassign it after the import:

    DOCS_DIR = 'documentation'  # Override default 'docs'
    SKIP_PATTERNS = ['_template.md', 'drafts/']  # Add more patterns

"""

import os


def find_project_root() -> str:
    """Find the project root by looking for the .ontos directory.

    Walks up from the script's location to find the directory containing .ontos/.
    Falls back to current working directory if not found.

    Returns:
        Absolute path to the project root.
    """
    # Start from this script's directory
    current = os.path.dirname(os.path.abspath(__file__))

    # Walk up looking for .ontos directory
    while True:
        # Check if .ontos exists in current directory
        ontos_dir = os.path.join(current, '.ontos')
        if os.path.isdir(ontos_dir):
            return current

        # Move up one directory
        parent = os.path.dirname(current)
        if parent == current:
            # Reached filesystem root, fall back to cwd
            return os.getcwd()
        current = parent


# Project root - auto-detected
PROJECT_ROOT = find_project_root()

# Define the internal directory path and marker file
INTERNAL_DIR = os.path.join(PROJECT_ROOT, '.ontos-internal')
ONTOS_REPO_MARKER = os.path.join(INTERNAL_DIR, 'kernel', 'mission.md')


def is_ontos_repo() -> bool:
    """Check if we're in the actual Ontos repository.
    
    Requires BOTH:
    1. .ontos-internal/ directory exists
    2. The expected structure exists (kernel/mission.md as marker)
    
    This prevents false positives if a user accidentally copies .ontos-internal/
    """
    return os.path.isdir(INTERNAL_DIR) and os.path.isfile(ONTOS_REPO_MARKER)


from ontos_config_defaults import (
    # Version info (re-exported for backward compatibility)
    ONTOS_VERSION,
    ONTOS_REPO_URL,
    ONTOS_REPO_RAW_URL,
    # Type system (generally don't override these)
    TYPE_DEFINITIONS,
    TYPE_HIERARCHY,
    VALID_TYPES,
    EVENT_TYPES,
    VALID_EVENT_TYPES,
    # Defaults to potentially override
    DEFAULT_DOCS_DIR,
    DEFAULT_LOGS_DIR,
    DEFAULT_CONTEXT_MAP_FILE,
    DEFAULT_MIGRATION_PROMPT_FILE,
    DEFAULT_MAX_DEPENDENCY_DEPTH,
    DEFAULT_ALLOWED_ORPHAN_TYPES,
    DEFAULT_SKIP_PATTERNS,
    # Workflow enforcement (override to customize strictness)
    ENFORCE_ARCHIVE_BEFORE_PUSH,
    REQUIRE_SOURCE_IN_LOGS,
    LOG_RETENTION_COUNT,
)

# Backward compatibility alias
__version__ = ONTOS_VERSION

# =============================================================================
# USER CONFIGURATION - Override defaults below as needed
# =============================================================================

# =============================================================================
# SMART CONFIGURATION
# Adapts to environment: Contributor Mode vs User Mode
# =============================================================================

if is_ontos_repo():
    # -------------------------------------------------------------------------
    # CONTRIBUTOR MODE: Developing Project Ontos itself
    # -------------------------------------------------------------------------
    # Confirmed Ontos repo (marker file exists)
    DOCS_DIR = INTERNAL_DIR
    LOGS_DIR = os.path.join(INTERNAL_DIR, 'logs')
    # Override defaults to allow scanning the internal dir
    SKIP_PATTERNS = ['**/_template.md', '**/Ontos_Context_Map.md', '**/archive/**']
    # Allow atoms and logs to be leaves (orphans) in the graph
    ALLOWED_ORPHAN_TYPES = ['product', 'strategy', 'kernel', 'atom', 'log']
else:
    # -------------------------------------------------------------------------
    # USER MODE: Using Project Ontos in another project
    # -------------------------------------------------------------------------
    # Either no .ontos-internal/, or it exists but lacks expected structure
    DOCS_DIR = os.path.join(PROJECT_ROOT, DEFAULT_DOCS_DIR)
    LOGS_DIR = os.path.join(PROJECT_ROOT, DEFAULT_LOGS_DIR)
    # Use defaults (which safely skip .ontos-internal if it appears by accident)
    SKIP_PATTERNS = DEFAULT_SKIP_PATTERNS
    ALLOWED_ORPHAN_TYPES = DEFAULT_ALLOWED_ORPHAN_TYPES
    
    # Warn if .ontos-internal/ exists but doesn't look like Ontos repo
    if os.path.isdir(INTERNAL_DIR) and not os.path.isfile(ONTOS_REPO_MARKER):
        import warnings
        warnings.warn(
            f"Found .ontos-internal/ directory but it doesn't appear to be the Ontos repo "
            f"(missing {ONTOS_REPO_MARKER}). Using default docs/ directory. "
            f"If this is intentional, you can ignore this warning.",
            stacklevel=2
        )

# Output file for the context map (resolved to absolute path)
CONTEXT_MAP_FILE = os.path.join(PROJECT_ROOT, DEFAULT_CONTEXT_MAP_FILE)

# Output file for migration prompts (resolved to absolute path)
MIGRATION_PROMPT_FILE = os.path.join(PROJECT_ROOT, DEFAULT_MIGRATION_PROMPT_FILE)

# Maximum allowed dependency chain depth
MAX_DEPENDENCY_DEPTH = DEFAULT_MAX_DEPENDENCY_DEPTH



# =============================================================================
# EXAMPLE CUSTOMIZATIONS (uncomment and modify as needed)
# =============================================================================

# Directory customization:
# DOCS_DIR = os.path.join(PROJECT_ROOT, 'documentation')
# LOGS_DIR = os.path.join(PROJECT_ROOT, 'documentation/session-logs')
# SKIP_PATTERNS = DEFAULT_SKIP_PATTERNS + ['drafts/', 'archive/']

# Workflow enforcement (set to False for relaxed mode):
# ENFORCE_ARCHIVE_BEFORE_PUSH = False  # Advisory-only pre-push hook
# REQUIRE_SOURCE_IN_LOGS = False       # --source becomes optional

# Memory management (set lower for token-constrained workflows):
# LOG_RETENTION_COUNT = 10
