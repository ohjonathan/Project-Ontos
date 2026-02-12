# ontos/commands/export.py
"""
CLAUDE.md generation command.

Generates AI assistant integration file per Spec v1.1 Section 4.4.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from ontos.core.instruction_artifacts import generate_claude_file


@dataclass
class ExportOptions:
    """Configuration for export command."""
    output_path: Optional[Path] = None
    force: bool = False


def find_repo_root() -> Path:
    """Find the repository root."""
    current = Path.cwd()

    for parent in [current] + list(current.parents):
        if (parent / ".ontos.toml").exists():
            return parent
        if (parent / ".git").exists():
            return parent

    return current


def _run_export_command(options: ExportOptions) -> Tuple[int, str]:
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
        repo_root = find_repo_root()
    except Exception as e:
        return 2, f"Configuration error: {e}"

    return generate_claude_file(
        repo_root=repo_root,
        output_path=options.output_path,
        force=options.force,
    )


def export_command(options: ExportOptions) -> int:
    """Generate CLAUDE.md and return exit code only."""
    exit_code, _ = _run_export_command(options)
    return exit_code
