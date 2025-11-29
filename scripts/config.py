"""Ontos configuration constants."""

# Version
__version__ = '0.4.0'

# Directory settings
DEFAULT_DOCS_DIR = 'docs'
LOGS_DIR = 'docs/logs'

# Output files
CONTEXT_MAP_FILE = 'CONTEXT_MAP.md'
MIGRATION_PROMPT_FILE = 'migration_prompt.txt'

# Validation thresholds
MAX_DEPENDENCY_DEPTH = 5

# Document type hierarchy (lower number = higher in hierarchy)
TYPE_HIERARCHY = {
    'kernel': 0,
    'strategy': 1,
    'product': 2,
    'atom': 3,
    'unknown': 4
}

# Types that are allowed to be orphans (no dependents)
ALLOWED_ORPHAN_TYPES = ['product', 'strategy', 'kernel']

# Files/patterns to skip during scanning
SKIP_PATTERNS = ['_template.md']
