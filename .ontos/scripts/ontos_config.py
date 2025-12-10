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

# Directory where your documentation lives (resolved to absolute path)
DOCS_DIR = os.path.join(PROJECT_ROOT, DEFAULT_DOCS_DIR)

# Directory for session logs (resolved to absolute path)
LOGS_DIR = os.path.join(PROJECT_ROOT, DEFAULT_LOGS_DIR)

# Output file for the context map (resolved to absolute path)
CONTEXT_MAP_FILE = os.path.join(PROJECT_ROOT, DEFAULT_CONTEXT_MAP_FILE)

# Output file for migration prompts (resolved to absolute path)
MIGRATION_PROMPT_FILE = os.path.join(PROJECT_ROOT, DEFAULT_MIGRATION_PROMPT_FILE)

# Maximum allowed dependency chain depth
MAX_DEPENDENCY_DEPTH = DEFAULT_MAX_DEPENDENCY_DEPTH

# Document types that are allowed to have no dependents
# Include 'atom' since technical specs are often leaf nodes in documentation trees
ALLOWED_ORPHAN_TYPES = DEFAULT_ALLOWED_ORPHAN_TYPES + ['atom']

# File patterns to skip during scanning (add your own patterns here)
SKIP_PATTERNS = DEFAULT_SKIP_PATTERNS

# =============================================================================
# EXAMPLE CUSTOMIZATIONS (uncomment and modify as needed)
# =============================================================================

# DOCS_DIR = os.path.join(PROJECT_ROOT, 'documentation')
# LOGS_DIR = os.path.join(PROJECT_ROOT, 'documentation/session-logs')
# SKIP_PATTERNS = DEFAULT_SKIP_PATTERNS + ['drafts/', 'archive/']
