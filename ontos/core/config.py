"""Configuration helpers.

This module contains functions for resolving configuration values
and getting session source information.

IMPURE: get_source() calls subprocess for git config.
"""

import os
import subprocess
from typing import Optional


# Branch names that should not be used as auto-slugs
BLOCKED_BRANCH_NAMES = {'main', 'master', 'dev', 'develop', 'HEAD'}


def get_source() -> Optional[str]:
    """Get session log source with fallback chain.
    
    IMPURE: Calls subprocess.run for git config.
    
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


def get_git_last_modified(filepath: str) -> Optional:
    """Get the last git commit date for a file.
    
    IMPURE: Calls subprocess.run for git log.
    
    Args:
        filepath: Path to the file to check.
        
    Returns:
        datetime of last modification, or None if not tracked by git.
    """
    from datetime import datetime
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
