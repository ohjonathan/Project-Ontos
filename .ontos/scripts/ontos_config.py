"""Ontos configuration - User customizations.

This file imports defaults from ontos_config_defaults.py and allows you to
override any settings for your project. This file is NEVER touched by
ontos_update.py, so your customizations are safe.

To customize a setting, simply reassign it after the import:

    DOCS_DIR = 'documentation'  # Override default 'docs'
    SKIP_PATTERNS = ['_template.md', 'drafts/']  # Add more patterns

"""

from ontos_config_defaults import (
    # Version info (re-exported for backward compatibility)
    ONTOS_VERSION,
    ONTOS_REPO_URL,
    ONTOS_REPO_RAW_URL,
    # Type system (generally don't override these)
    TYPE_DEFINITIONS,
    TYPE_HIERARCHY,
    # Defaults to potentially override
    DEFAULT_DOCS_DIR,
    DEFAULT_LOGS_DIR,
    DEFAULT_CONTEXT_MAP_FILE,
    DEFAULT_MIGRATION_PROMPT_FILE,
    DEFAULT_MAX_DEPENDENCY_DEPTH,
    DEFAULT_ALLOWED_ORPHAN_TYPES,
    DEFAULT_SKIP_PATTERNS,
)

# Backward compatibility alias
__version__ = ONTOS_VERSION

# =============================================================================
# USER CONFIGURATION - Override defaults below as needed
# =============================================================================

# Directory where your documentation lives
DOCS_DIR = DEFAULT_DOCS_DIR

# Directory for session logs
LOGS_DIR = DEFAULT_LOGS_DIR

# Output file for the context map
CONTEXT_MAP_FILE = DEFAULT_CONTEXT_MAP_FILE

# Output file for migration prompts
MIGRATION_PROMPT_FILE = DEFAULT_MIGRATION_PROMPT_FILE

# Maximum allowed dependency chain depth
MAX_DEPENDENCY_DEPTH = DEFAULT_MAX_DEPENDENCY_DEPTH

# Document types that are allowed to have no dependents
ALLOWED_ORPHAN_TYPES = DEFAULT_ALLOWED_ORPHAN_TYPES

# File patterns to skip during scanning (add your own patterns here)
SKIP_PATTERNS = DEFAULT_SKIP_PATTERNS

# =============================================================================
# EXAMPLE CUSTOMIZATIONS (uncomment and modify as needed)
# =============================================================================

# DOCS_DIR = 'documentation'
# LOGS_DIR = 'documentation/session-logs'
# SKIP_PATTERNS = DEFAULT_SKIP_PATTERNS + ['drafts/', 'archive/']
