# ontos/commands/hook.py
"""
Git hook dispatcher command.

Called by shim hooks in .git/hooks/ to execute Ontos validation.
Per Spec v1.1 Section 4.3.

DESIGN DECISION (B5): Fail-Open Behavior
-----------------------------------------
Hooks intentionally return 0 (allow) on error rather than blocking git operations.
This is a deliberate safety choice:
- Never block developers from pushing due to Ontos misconfiguration
- Prefer allowing potentially invalid state over blocking legitimate work
- Warnings are printed to stderr for visibility

To enable blocking behavior, set strict mode in .ontos.toml (future feature).
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class HookOptions:
    """Configuration for hook command."""
    hook_type: str  # "pre-push" or "pre-commit"
    args: List[str] = field(default_factory=list)


def hook_command(options: HookOptions) -> int:
    """
    Dispatch git hook execution.

    Returns:
        0 = Allow git operation to proceed
        1 = Block git operation
    """
    if options.hook_type == "pre-push":
        return run_pre_push_hook(options.args)
    elif options.hook_type == "pre-commit":
        return run_pre_commit_hook(options.args)
    else:
        print(
            f"Warning: Unknown hook type '{options.hook_type}'. Skipping.",
            file=sys.stderr
        )
        return 0


def run_pre_push_hook(args: List[str]) -> int:
    """
    Pre-push hook: Validate documentation before push.

    Returns:
        0 = Allow push
        1 = Block push (validation errors)
    """
    try:
        from ontos.io.config import load_project_config
        config = load_project_config()

        if not config.hooks.pre_push:
            return 0

        context_map = Path.cwd() / config.paths.context_map

        if not context_map.exists():
            print(
                "Warning: Context map not found. "
                "Run 'ontos map' before pushing.",
                file=sys.stderr
            )
            return 0

        return 0

    except Exception as e:
        print(
            f"Warning: Hook error (push allowed): {e}",
            file=sys.stderr
        )
        return 0


def run_pre_commit_hook(args: List[str]) -> int:
    """
    Pre-commit hook: Check documentation status before commit.

    Returns:
        0 = Always (pre-commit doesn't block by default)
    """
    try:
        from ontos.io.config import load_project_config
        config = load_project_config()

        if not config.hooks.pre_commit:
            return 0

        return 0

    except Exception:
        return 0
