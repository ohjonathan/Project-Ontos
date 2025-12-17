"""Shared utilities for Ontos scripts.

This module contains common functions used across multiple Ontos scripts.
Centralizing them here ensures consistency and simplifies maintenance.
"""

import os
import re
import yaml
import subprocess
from datetime import datetime
from typing import Optional


def parse_frontmatter(filepath: str) -> Optional[dict]:
    """Parse YAML frontmatter from a markdown file.

    Args:
        filepath: Path to the markdown file.

    Returns:
        Dictionary of frontmatter fields, or None if no valid frontmatter.
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    if content.startswith('---'):
        try:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                return frontmatter
        except yaml.YAMLError as e:
            print(f"Error parsing YAML in {filepath}: {e}")
    return None


def normalize_depends_on(value) -> list[str]:
    """Normalize depends_on field to a list of strings.

    Handles YAML edge cases: null, empty, string, or list.

    Args:
        value: Raw value from YAML frontmatter.

    Returns:
        List of dependency IDs (empty list if none).
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None and str(v).strip()]
    return []


def normalize_type(value) -> str:
    """Normalize type field to a string.

    Args:
        value: Raw value from YAML frontmatter.

    Returns:
        Type string ('unknown' if invalid).
    """
    if value is None:
        return 'unknown'
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or '|' in stripped:
            return 'unknown'
        return stripped
    if isinstance(value, list):
        if value and value[0] is not None:
            first = str(value[0]).strip()
            if '|' in first:
                return 'unknown'
            return first if first else 'unknown'
    return 'unknown'


def load_common_concepts(docs_dir: str = None) -> set[str]:
    """Load known concepts from Common_Concepts.md if it exists.
    
    Args:
        docs_dir: Documentation directory to search.
    
    Returns:
        Set of known concept strings.
    """
    if docs_dir is None:
        from ontos_config import DOCS_DIR
        docs_dir = DOCS_DIR
    
    possible_paths = [
        os.path.join(docs_dir, 'reference', 'Common_Concepts.md'),
        os.path.join(docs_dir, 'Common_Concepts.md'),
        'docs/reference/Common_Concepts.md',
    ]
    
    concepts_file = None
    for path in possible_paths:
        if os.path.exists(path):
            concepts_file = path
            break
            
    if not concepts_file:
        return set()
    
    concepts = set()
    try:
        with open(concepts_file, 'r', encoding='utf-8') as f:
            content = f.read()
        matches = re.findall(r'\|\s*`([a-z][a-z0-9-]*)`\s*\|', content)
        concepts.update(matches)
    except (IOError, OSError):
        pass
    
    return concepts


def get_git_last_modified(filepath: str) -> Optional[datetime]:
    """Get the last modified date of a file from git history.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        datetime of last modification, or None if not in git.
    """
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cd', '--date=iso-strict', '--', filepath],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            date_str = result.stdout.strip()
            # Handle timezone offset format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return None


def find_last_session_date(logs_dir: str = None) -> str:
    """Find the date of the most recent session log.

    Args:
        logs_dir: Directory containing log files. If None, uses LOGS_DIR from config.

    Returns:
        Date string in YYYY-MM-DD format, or empty string if no logs found.
    """
    if logs_dir is None:
        from ontos_config import LOGS_DIR
        logs_dir = LOGS_DIR
    
    if not os.path.exists(logs_dir):
        return ""

    log_files = []
    for filename in os.listdir(logs_dir):
        if filename.endswith('.md') and len(filename) >= 10:
            date_part = filename[:10]
            if date_part.count('-') == 2:
                log_files.append(date_part)

    if not log_files:
        return ""

    return sorted(log_files)[-1]


def resolve_config(setting_name: str, default=None):
    """Resolve a config value considering mode presets and overrides.
    
    Resolution order:
    1. Explicit override in ontos_config.py
    2. Mode preset value (if ONTOS_MODE is set)
    3. Default from ontos_config_defaults.py
    4. Provided default parameter
    
    Args:
        setting_name: Name of the setting (e.g., 'AUTO_ARCHIVE_ON_PUSH')
        default: Fallback value if setting not found anywhere
    
    Returns:
        Resolved configuration value.
    """
    import ontos_config_defaults as defaults
    
    # 1. Try explicit override in user config
    try:
        import ontos_config as user_config
        if hasattr(user_config, setting_name):
            return getattr(user_config, setting_name)
    except ImportError:
        pass
    
    # 2. Try mode preset
    try:
        import ontos_config as user_config
        mode = getattr(user_config, 'ONTOS_MODE', None)
    except ImportError:
        mode = getattr(defaults, 'ONTOS_MODE', None)
    
    if mode and hasattr(defaults, 'MODE_PRESETS'):
        presets = defaults.MODE_PRESETS.get(mode, {})
        if setting_name in presets:
            return presets[setting_name]
    
    # 3. Try default from ontos_config_defaults.py
    if hasattr(defaults, setting_name):
        return getattr(defaults, setting_name)
    
    # 4. Return provided default
    return default


def get_source() -> Optional[str]:
    """Get session log source with fallback chain.
    
    Resolution order:
    1. ONTOS_SOURCE environment variable
    2. DEFAULT_SOURCE in config
    3. git config user.name
    4. None (caller should prompt)
    
    Returns:
        Source string or None if caller should prompt.
    """
    # 1. Environment variable
    env_source = os.environ.get('ONTOS_SOURCE')
    if env_source:
        return env_source
    
    # 2. Config default
    try:
        from ontos_config import DEFAULT_SOURCE
        if DEFAULT_SOURCE:
            return DEFAULT_SOURCE
    except (ImportError, AttributeError):
        pass
    
    # 3. Git user name
    try:
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # 4. Caller should prompt
    return None


# Branch names that should not be used as auto-slugs
BLOCKED_BRANCH_NAMES = {'main', 'master', 'dev', 'develop', 'HEAD'}


# =============================================================================
# LOG DISCOVERY HELPERS (v2.5+)
# =============================================================================
# Centralized functions for log path resolution, counting, and age detection.
# Used by: ontos_pre_commit_check.py, ontos_generate_context_map.py


def get_logs_dir() -> str:
    """Get the logs directory path based on config.
    
    Respects LOGS_DIR config setting if set, otherwise derives from DOCS_DIR.
    Handles both contributor mode (.ontos-internal) and user mode (docs/logs).
    
    Returns:
        Absolute path to logs directory.
    """
    # Try LOGS_DIR first (most explicit)
    logs_dir = resolve_config('LOGS_DIR', None)
    if logs_dir and os.path.isabs(logs_dir):
        return logs_dir
    
    # Get PROJECT_ROOT for relative path resolution
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        # Fallback if config not available
        return 'docs/logs'
    
    # Contributor mode uses .ontos-internal/logs
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'logs')
    
    # User mode: derive from LOGS_DIR or DOCS_DIR
    if logs_dir:
        return os.path.join(PROJECT_ROOT, logs_dir)
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    return os.path.join(PROJECT_ROOT, docs_dir, 'logs')


def get_log_count() -> int:
    """Count active session logs in logs directory.
    
    Only counts markdown files starting with a digit (date-prefixed logs).
    
    Returns:
        Number of active log files.
    """
    logs_dir = get_logs_dir()
    if not os.path.exists(logs_dir):
        return 0
    
    return len([f for f in os.listdir(logs_dir)
                if f.endswith('.md') and f[0].isdigit()])


def get_logs_older_than(days: int) -> list[str]:
    """Get list of log filenames older than N days.
    
    Args:
        days: Age threshold in days.
        
    Returns:
        List of log filenames (not full paths) older than threshold.
    """
    logs_dir = get_logs_dir()
    if not os.path.exists(logs_dir):
        return []
    
    cutoff = datetime.now() - __import__('datetime').timedelta(days=days)
    old_logs = []
    
    for filename in os.listdir(logs_dir):
        if not filename.endswith('.md') or not filename[0].isdigit():
            continue
        try:
            log_date = datetime.strptime(filename[:10], '%Y-%m-%d')
            if log_date < cutoff:
                old_logs.append(filename)
        except ValueError:
            continue
    
    return old_logs


def get_archive_dir() -> str:
    """Get the archive directory path based on config.
    
    Returns:
        Absolute path to archive directory.
    """
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        return 'docs/archive'
    
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'archive')
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    return os.path.join(PROJECT_ROOT, docs_dir, 'archive')


# =============================================================================
# DEPRECATION WARNING HELPER (v2.5.2+)
# =============================================================================

_deprecation_warned = set()  # Track warnings to avoid spam


def _warn_deprecated(old_path: str, new_path: str) -> None:
    """Issue deprecation warning (once per path per session)."""
    if old_path in _deprecation_warned:
        return
    _deprecation_warned.add(old_path)
    print(f"[DEPRECATION WARNING] Using old path '{old_path}'.")
    print(f"   Expected: '{new_path}'")
    print("   Run 'python3 ontos_init.py' to update your project structure.")


# =============================================================================
# PATH HELPERS WITH BACKWARD COMPATIBILITY (v2.5.2+)
# =============================================================================


def get_decision_history_path() -> str:
    """Get decision_history.md path with backward compatibility.
    
    v2.5.2: Uses nested structure (docs/strategy/decision_history.md)
    Pre-v2.5.2: Falls back to flat structure (docs/decision_history.md)
    
    Returns:
        Absolute path to decision_history.md.
    """
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        return 'docs/strategy/decision_history.md'
    
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'strategy', 'decision_history.md')
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    
    # Try new location first (v2.5.2+)
    new_path = os.path.join(PROJECT_ROOT, docs_dir, 'strategy', 'decision_history.md')
    if os.path.exists(new_path):
        return new_path
    
    # Fall back to old location (pre-v2.5.2)
    old_path = os.path.join(PROJECT_ROOT, docs_dir, 'decision_history.md')
    if os.path.exists(old_path):
        _warn_deprecated(f'{docs_dir}/decision_history.md', f'{docs_dir}/strategy/decision_history.md')
        return old_path
    
    # Return new location for creation
    return new_path


def get_proposals_dir() -> str:
    """Get proposals directory path (mode-aware).
    
    Returns:
        Absolute path to proposals directory.
    """
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        return 'docs/strategy/proposals'
    
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'strategy', 'proposals')
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    return os.path.join(PROJECT_ROOT, docs_dir, 'strategy', 'proposals')


def get_archive_logs_dir() -> str:
    """Get archive/logs directory path with backward compatibility.
    
    v2.5.2: Uses nested structure (docs/archive/logs/)
    Pre-v2.5.2: Falls back to flat structure (docs/archive/)
    
    Returns:
        Absolute path to archive/logs directory.
    """
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        return 'docs/archive/logs'
    
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'archive', 'logs')
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    
    # Try new location first (v2.5.2+)
    new_path = os.path.join(PROJECT_ROOT, docs_dir, 'archive', 'logs')
    if os.path.exists(new_path):
        return new_path
    
    # Fall back to old location (pre-v2.5.2: logs directly in archive/)
    old_path = os.path.join(PROJECT_ROOT, docs_dir, 'archive')
    if os.path.exists(old_path):
        _warn_deprecated(f'{docs_dir}/archive/', f'{docs_dir}/archive/logs/')
        return old_path
    
    # Return new location for creation
    return new_path


def get_archive_proposals_dir() -> str:
    """Get archive/proposals directory path (mode-aware).
    
    New in v2.5.2 - no backward compatibility needed.
    
    Returns:
        Absolute path to archive/proposals directory.
    """
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        return 'docs/archive/proposals'
    
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'archive', 'proposals')
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    return os.path.join(PROJECT_ROOT, docs_dir, 'archive', 'proposals')


def get_concepts_path() -> str:
    """Get Common_Concepts.md path with backward compatibility.
    
    v2.5.2: Uses nested structure (docs/reference/Common_Concepts.md)
    Pre-v2.5.2: Falls back to flat structure (docs/Common_Concepts.md)
    
    Returns:
        Absolute path to Common_Concepts.md.
    """
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        return 'docs/reference/Common_Concepts.md'
    
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'reference', 'Common_Concepts.md')
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    
    # Try new location first (v2.5.2+)
    new_path = os.path.join(PROJECT_ROOT, docs_dir, 'reference', 'Common_Concepts.md')
    if os.path.exists(new_path):
        return new_path
    
    # Fall back to old location (pre-v2.5.2)
    old_path = os.path.join(PROJECT_ROOT, docs_dir, 'Common_Concepts.md')
    if os.path.exists(old_path):
        _warn_deprecated(f'{docs_dir}/Common_Concepts.md', f'{docs_dir}/reference/Common_Concepts.md')
        return old_path
    
    # Return new location for creation
    return new_path


# =============================================================================
# V2.6 VALIDATION HELPERS
# =============================================================================


def get_git_last_modified(filepath: str) -> Optional[datetime]:
    """Get the last git commit date for a file.
    
    Args:
        filepath: Path to the file to check.
        
    Returns:
        datetime of last modification, or None if not tracked by git.
    """
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ct', filepath],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            timestamp = int(result.stdout.strip())
            return datetime.fromtimestamp(timestamp)
    except (subprocess.SubprocessError, ValueError):
        pass
    return None


def load_decision_history_entries() -> dict:
    """Load decision_history.md entries for validation.
    
    Parses the decision history ledger to enable validation that 
    rejected/approved proposals are properly recorded.
    
    v2.6.1: Improved parsing for deterministic matching by slug and archive path.
    
    Returns:
        Dict with:
          - 'archive_paths': dict mapping archive_path -> slug
          - 'slugs': set of all slugs in ledger
          - 'rejected_slugs': set of slugs with REJECTED in outcome
          - 'approved_slugs': set of slugs with APPROVED in outcome
          - 'outcomes': dict mapping slug -> full outcome text
    """
    history_path = get_decision_history_path()
    entries = {
        'archive_paths': {},  # Now a dict: path -> slug
        'slugs': set(),
        'rejected_slugs': set(),
        'approved_slugs': set(),
        'outcomes': {}
    }
    
    if os.path.exists(history_path):
        with open(history_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Parse table rows: | date | slug | event | outcome | impacted | archive_path |
                if line.startswith('|') and not line.startswith('|:') and not line.startswith('| Date'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 7:
                        slug = parts[2]
                        outcome = parts[4]
                        archive_path = parts[6].strip('`')  # Remove backticks
                        
                        if slug:
                            entries['slugs'].add(slug)
                            entries['outcomes'][slug] = outcome
                            
                            # Deterministic outcome classification
                            outcome_upper = outcome.upper()
                            if 'REJECTED' in outcome_upper:
                                entries['rejected_slugs'].add(slug)
                            if 'APPROVED' in outcome_upper:
                                entries['approved_slugs'].add(slug)
                        
                        if archive_path:
                            entries['archive_paths'][archive_path] = slug
    return entries

