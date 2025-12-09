"""Ontos configuration constants."""

# Version
__version__ = '0.4.0'

# Directory settings
DEFAULT_DOCS_DIR = 'docs'
LOGS_DIR = 'docs/logs'

# Output files
CONTEXT_MAP_FILE = 'Ontos_Context_Map.md'
MIGRATION_PROMPT_FILE = 'migration_prompt.txt'

# Validation thresholds
MAX_DEPENDENCY_DEPTH = 5

# Document type definitions (single source of truth)
TYPE_DEFINITIONS = {
    'kernel': {
        'rank': 0,
        'definition': 'Immutable foundational principles that rarely change',
        'signals': ['mission', 'values', 'philosophy', 'principles']
    },
    'strategy': {
        'rank': 1,
        'definition': 'High-level decisions about goals, audiences, approaches',
        'signals': ['goals', 'roadmap', 'monetization', 'target market']
    },
    'product': {
        'rank': 2,
        'definition': 'User-facing features, journeys, requirements',
        'signals': ['user flow', 'feature spec', 'requirements', 'user story']
    },
    'atom': {
        'rank': 3,
        'definition': 'Technical implementation details and specifications',
        'signals': ['API', 'schema', 'config', 'implementation', 'technical spec']
    },
    'unknown': {
        'rank': 4,
        'definition': 'Unclassified document type',
        'signals': []
    }
}

# Derived hierarchy for backward compatibility
TYPE_HIERARCHY = {k: v['rank'] for k, v in TYPE_DEFINITIONS.items()}

# Types that are allowed to be orphans (no dependents)
ALLOWED_ORPHAN_TYPES = ['product', 'strategy', 'kernel']

# Files/patterns to skip during scanning
SKIP_PATTERNS = ['_template.md']
