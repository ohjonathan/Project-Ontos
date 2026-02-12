"""
Export claude command — generate CLAUDE.md file.

Refactored from export.py for v3.2 subcommand structure.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from ontos.core.claude_template import CLAUDE_MD_TEMPLATE
from ontos.core.instruction_artifacts import generate_claude_file
from ontos.io.files import find_project_root


@dataclass
class ExportClaudeOptions:
    """Options for export claude command."""
    output_path: Optional[Path] = None
    force: bool = False
    quiet: bool = False
    json_output: bool = False


def _run_export_claude_command(options: ExportClaudeOptions) -> Tuple[int, str]:
    """
    Generate CLAUDE.md file.

    Returns:
        Tuple of (exit_code, message)

    Exit Codes:
        0: Success
        1: File exists (use --force)
        2: Configuration error
    """
    try:
        repo_root = find_project_root()
    except Exception:
        # B1: Allow running outside project context (fallback to CWD)
        repo_root = Path.cwd()

    return generate_claude_file(
        repo_root=repo_root,
        output_path=options.output_path,
        force=options.force,
    )


def export_claude_command(options: ExportClaudeOptions) -> int:
    """Generate CLAUDE.md and return exit code only."""
    exit_code, _ = _run_export_claude_command(options)
    return exit_code
