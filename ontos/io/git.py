"""
Git subprocess operations.

All git interactions should go through this module to maintain
the core/io separation required by the architecture.

Phase 2 Decomposition - Created from Phase2-Implementation-Spec.md Section 4.6
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


def get_current_branch() -> Optional[str]:
    """Get the current git branch name.

    Returns:
        Branch name or None if not in a git repo
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def get_commits_since_push(fallback_count: int = 5) -> List[str]:
    """Get commit messages for unpushed commits.

    Args:
        fallback_count: Number of commits to return if no upstream

    Returns:
        List of commit messages
    """
    try:
        # Try to get commits since last push
        result = subprocess.run(
            ["git", "log", "@{u}..HEAD", "--format=%s"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')

        # Fallback: last N commits
        result = subprocess.run(
            ["git", "log", f"-{fallback_count}", "--format=%s"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            return output.split('\n') if output else []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def get_changed_files_since_push() -> List[str]:
    """Get list of files changed since last push.

    Returns:
        List of file paths
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "@{u}..HEAD"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')

        # Fallback: files in last commit
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            return output.split('\n') if output else []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def get_file_mtime(filepath: Path) -> Optional[datetime]:
    """Get last modification time from git.

    Args:
        filepath: Path to file

    Returns:
        Datetime of last modification or None
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", str(filepath)],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return datetime.fromisoformat(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return None


def is_git_repo() -> bool:
    """Check if current directory is in a git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_git_root() -> Optional[Path]:
    """Get the root directory of the git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def get_session_git_log(max_commits: int = 20) -> List[str]:
    """Get git log for session summary.

    Args:
        max_commits: Maximum number of commits to include

    Returns:
        List of formatted commit lines
    """
    try:
        result = subprocess.run(
            ["git", "log", f"-{max_commits}", "--format=%h %s"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def get_git_config(key: str) -> Optional[str]:
    """Get a git config value.

    Args:
        key: Config key (e.g., 'user.name')

    Returns:
        Config value or None if not set
    """
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None
