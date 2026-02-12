# ontos/commands/export.py
"""
CLAUDE.md generation command.

Generates AI assistant integration file per Spec v1.1 Section 4.4.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from ontos.commands.claude_template import generate_claude_content


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

    output_path = options.output_path or repo_root / "CLAUDE.md"

    # Path safety validation
    try:
        resolved_output = output_path.resolve()
        resolved_root = repo_root.resolve()
        resolved_output.relative_to(resolved_root)
    except ValueError:
        return 2, f"Error: Output path must be within repository root ({repo_root})"

    if output_path.exists() and not options.force:
        return 1, f"CLAUDE.md already exists at {output_path}. Use --force to overwrite."

    try:
        existing_content = None
        if output_path.exists():
            existing_content = output_path.read_text(encoding="utf-8")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            generate_claude_content(existing_content),
            encoding="utf-8",
        )
    except Exception as e:
        return 2, f"Error writing file: {e}"

    return 0, f"Created {output_path}"


def export_command(options: ExportOptions) -> int:
    """Generate CLAUDE.md and return exit code only."""
    exit_code, _ = _run_export_command(options)
    return exit_code
