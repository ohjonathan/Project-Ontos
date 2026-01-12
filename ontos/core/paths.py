"""Path resolution helpers.

This module contains functions for resolving Ontos directory and file paths
with mode-awareness (contributor vs user mode) and backward compatibility.

IMPURE: Many functions use os.path.exists() and imports from config modules.
"""

import os
import warnings
from datetime import datetime
from typing import Optional


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


# Track deprecation warnings to avoid spam
_deprecation_warned = set()


def _warn_deprecated(old_path: str, new_path: str) -> None:
    """Issue deprecation warning using Python's warnings system.

    Uses stdlib warnings module for proper filtering, deduplication,
    and CLI suppression. No caller changes required.
    """
    if old_path in _deprecation_warned:
        return
    _deprecation_warned.add(old_path)
    warnings.warn(
        f"Using deprecated path '{old_path}'. "
        f"Expected: '{new_path}'. "
        f"Run 'python3 ontos_init.py' to update.",
        FutureWarning,
        stacklevel=3  # Point to caller's caller
    )


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


def get_logs_older_than(days: int) -> list:
    """Get list of log filenames older than N days.
    
    Args:
        days: Age threshold in days.
        
    Returns:
        List of log filenames (not full paths) older than threshold.
    """
    from datetime import timedelta
    logs_dir = get_logs_dir()
    if not os.path.exists(logs_dir):
        return []
    
    cutoff = datetime.now() - timedelta(days=days)
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
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'reference', 'decision_history.md')
    
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


def find_last_session_date(logs_dir: str = None) -> str:
    """Find the date of the most recent session log.

    Args:
        logs_dir: Directory containing log files. If None, uses LOGS_DIR from config.

    Returns:
        Date string in YYYY-MM-DD format, or empty string if no logs found.
    """
    if logs_dir is None:
        logs_dir = get_logs_dir()
    
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
