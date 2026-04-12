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
