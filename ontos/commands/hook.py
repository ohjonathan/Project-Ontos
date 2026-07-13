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

To enable blocking behavior, set strict mode in .ontos.toml.

JSON mode reports the same checks through the schema-4 command envelope while
the installed Git-hook path keeps the fail-open human behavior described above.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ontos.ui.json_output import ExitCode


@dataclass
class HookOptions:
    """Configuration for hook command."""
    hook_type: str  # "pre-push" or "pre-commit"
    args: List[str] = field(default_factory=list)
    json_output: bool = False


@dataclass(frozen=True)
class HookEvaluation:
    """Structured hook outcome before CLI or human rendering."""

    human_exit_code: int
    json_exit_code: int
    message: str
    result_status: str
    execution_succeeded: bool = True
    error_code: Optional[str] = None
    human_message: Optional[str] = None


def hook_command(options: HookOptions) -> int:
    """
    Dispatch git hook execution.

    Returns:
        0 = Allow git operation to proceed
        1 = Block git operation
    """
    if options.json_output:
        return evaluate_hook(options).json_exit_code
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


def evaluate_hook(options: HookOptions) -> HookEvaluation:
    """Evaluate a hook without printing, for structured JSON dispatch."""
    if options.hook_type == "pre-push":
        return _evaluate_pre_push_hook(options.args)
    if options.hook_type == "pre-commit":
        return _evaluate_pre_commit_hook(options.args)
    message = f"Unknown hook type '{options.hook_type}'."
    return HookEvaluation(
        human_exit_code=0,
        json_exit_code=int(ExitCode.USAGE),
        message=message,
        result_status="error",
        execution_succeeded=False,
        error_code="E_USER_INPUT",
        human_message=f"Warning: {message} Skipping.",
    )


def _render_human_result(result: HookEvaluation) -> int:
    if result.human_message:
        print(result.human_message, file=sys.stderr)
    return result.human_exit_code


def run_pre_push_hook(args: List[str]) -> int:
    """
    Pre-push hook: Validate documentation before push.

    Returns:
        0 = Allow push
        1 = Block push (validation errors with strict mode)
    """
    return _render_human_result(_evaluate_pre_push_hook(args))


def _validation_result(message: str, *, strict: bool) -> HookEvaluation:
    if strict:
        return HookEvaluation(
            human_exit_code=1,
            json_exit_code=int(ExitCode.FINDINGS),
            message=message,
            result_status="findings",
            human_message=f"Error: {message}",
        )
    return HookEvaluation(
        human_exit_code=0,
        json_exit_code=int(ExitCode.WARNINGS),
        message=message,
        result_status="warnings",
        human_message=f"Warning: {message}",
    )


def _evaluate_pre_push_hook(args: List[str]) -> HookEvaluation:
    del args
    try:
        from ontos.io.config import load_project_config

        config = load_project_config()
        if not config.hooks.pre_push:
            return HookEvaluation(0, 0, "Pre-push hook disabled", "clean")

        context_map = Path.cwd() / config.paths.context_map
        if not context_map.exists():
            return _validation_result(
                "Context map not found. Run 'ontos map' before pushing.",
                strict=config.hooks.strict,
            )

        try:
            content = context_map.read_text()
        except Exception as exc:
            message = f"Could not read context map: {exc}"
            return HookEvaluation(
                human_exit_code=0,
                json_exit_code=int(ExitCode.INTERNAL),
                message=message,
                result_status="error",
                execution_succeeded=False,
                error_code="E_HOOK_IO",
                human_message=f"Warning: {message}",
            )

        if not content.startswith("---"):
            return _validation_result(
                "Context map missing frontmatter. Run 'ontos map' to regenerate.",
                strict=config.hooks.strict,
            )
        return HookEvaluation(0, 0, "Pre-push hook checks passed", "clean")
    except Exception as exc:
        message = f"Hook error (push allowed): {exc}"
        return HookEvaluation(
            human_exit_code=0,
            json_exit_code=int(ExitCode.INTERNAL),
            message=message,
            result_status="error",
            execution_succeeded=False,
            error_code="E_HOOK_FAILED",
            human_message=f"Warning: {message}",
        )


def run_pre_commit_hook(args: List[str]) -> int:
    """
    Pre-commit hook: Check documentation status before commit.

    Returns:
        0 = Always (pre-commit doesn't block by default)
    """
    return _render_human_result(_evaluate_pre_commit_hook(args))


def _evaluate_pre_commit_hook(args: List[str]) -> HookEvaluation:
    del args
    try:
        from ontos.io.config import load_project_config

        config = load_project_config()
        message = (
            "Pre-commit hook checks passed"
            if config.hooks.pre_commit
            else "Pre-commit hook disabled"
        )
        return HookEvaluation(0, 0, message, "clean")
    except Exception as exc:
        return HookEvaluation(
            human_exit_code=0,
            json_exit_code=int(ExitCode.INTERNAL),
            message=f"Pre-commit hook error (commit allowed): {exc}",
            result_status="error",
            execution_succeeded=False,
            error_code="E_HOOK_FAILED",
        )
