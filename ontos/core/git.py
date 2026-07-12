"""Git helpers shared by commands and MCP tools.

The helpers in this module exist to keep git-shell-out logic in one place so
that both the CLI rename command and the MCP ``rename_document`` tool share a
single source of truth about what "clean" means for workspace mutation paths.

Semantics (v4.1 Track B):

* ``is_workspace_clean`` shells out to ``git status --porcelain``. Any
  non-empty output (including untracked files) is treated as *dirty*. This
  matches the v1.1 spec §4.8.2 recovery contract: the ``rename_document``
  precondition must guarantee that ``git checkout -- .`` restores the
  pre-mutation state, which is only safe when the working tree has nothing
  to lose.
* ``is_workspace_clean`` returns ``False`` (with a reason string) when git
  is unavailable or the repository cannot be inspected — the tool is a
  precondition for destructive multi-file edits, so we fail closed.
* ``rollback_path`` proves trackedness before taking action. Tracked paths
  are restored via ``git checkout --`` and a checkout failure never falls
  through to deletion; only proven-untracked partial files are unlinked.
  It is the scoped
  counterpart to the multi-file ``rename_tool`` rollback, which runs
  ``git checkout -- .`` over the whole workspace.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional, Tuple


def is_workspace_clean(
    root: Path,
    *,
    timeout: float = 10.0,
) -> Tuple[bool, Optional[str]]:
    """Check whether ``root`` is a clean git working tree.

    Args:
        root: Absolute path to the workspace root (passed as ``cwd`` to git).
        timeout: Seconds to wait on the git invocation before giving up.

    Returns:
        ``(True, None)`` when the working tree has no modifications and no
        untracked files; ``(False, reason)`` otherwise, where ``reason``
        is a short human-readable explanation.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return False, "git executable not found on PATH"
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"Unable to check git state: {exc}"

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        return False, stderr or "git status failed"

    if result.stdout.strip():
        return False, "working tree has uncommitted or untracked changes"
    return True, None


def rollback_path(
    root: Path,
    path: Path,
    *,
    timeout: float = 10.0,
) -> Optional[str]:
    """Revert a single path to its state at git HEAD.

    If the path is tracked, ``git checkout -- <path>`` restores the index/HEAD
    version. If the path is NOT tracked (e.g. a new file that a failed
    commit partially created), the path is unlinked from disk if present.
    A missing path after the rollback is a valid final state — the caller's
    intent is "undo the write", and nothing-to-undo is success.

    Args:
        root: Workspace root (cwd for git invocation).
        path: Absolute or ``root``-relative path whose state should be
            reverted.
        timeout: Seconds to wait on the git invocation.

    Returns:
        ``None`` on success or a short reason string on unrecoverable failure.
    """
    try:
        rel = path.relative_to(root) if path.is_absolute() else path
    except ValueError:
        return f"path is outside workspace root: {path}"

    try:
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", str(rel)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return "git executable not found on PATH"
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"Unable to determine trackedness: {exc}"

    if tracked.returncode not in (0, 1):
        stderr = (tracked.stderr or "").strip()
        return stderr or "git ls-files failed"

    if tracked.returncode == 0:
        try:
            result = subprocess.run(
                ["git", "checkout", "--", str(rel)],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError:
            return "git executable not found on PATH"
        except (OSError, subprocess.TimeoutExpired) as exc:
            return f"Unable to run git checkout: {exc}"
        if result.returncode == 0:
            return None
        stderr = (result.stderr or "").strip()
        return stderr or "git checkout failed for tracked path"

    # Only a proven-untracked path may be removed. A checkout failure for a
    # tracked path is never reinterpreted as permission to delete user data.
    abs_path = root / rel
    if abs_path.exists() or abs_path.is_symlink():
        if abs_path.is_dir() and not abs_path.is_symlink():
            return f"Refusing to unlink untracked directory: {abs_path}"
        try:
            abs_path.unlink()
        except OSError as exc:
            return f"Unable to unlink untracked path: {exc}"
    return None
