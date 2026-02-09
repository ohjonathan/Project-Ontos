"""
Export claude command — generate CLAUDE.md file.

Refactored from export.py for v3.2 subcommand structure.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from ontos.io.files import find_project_root


CLAUDE_MD_TEMPLATE = '''# CLAUDE.md

## Ontos Activation

This project uses **Ontos** for documentation management.

At the start of every session:
1. Run `ontos map` to generate the context map
2. Read `Ontos_Context_Map.md` to understand the project documentation structure

When ending a session:
3. Run `ontos log` to record your work

## What is Ontos?

Ontos is a local-first documentation management system that:
- Maintains a context map of all project documentation
- Tracks documentation dependencies and status
- Ensures documentation stays synchronized with code changes
'''


@dataclass
class ExportClaudeOptions:
    """Options for export claude command."""
    output_path: Optional[Path] = None
    force: bool = False
    quiet: bool = False
    json_output: bool = False


def export_claude_command(options: ExportClaudeOptions) -> Tuple[int, str]:
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

    output_path = options.output_path or repo_root / "CLAUDE.md"

    # Path safety validation (only if within a project root)
    try:
        resolved_output = output_path.resolve()
        resolved_root = repo_root.resolve()
        # If we are in a project, ensure we don't write outside it
        # If we are just in a random dir, skip this strict check
        if (repo_root / ".git").exists() or (repo_root / ".ontos.toml").exists():
            resolved_output.relative_to(resolved_root)
    except ValueError:
        return 2, f"Error: Output path must be within repository root ({repo_root})"

    if output_path.exists() and not options.force:
        return 1, f"CLAUDE.md already exists at {output_path}. Use --force to overwrite."

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(CLAUDE_MD_TEMPLATE, encoding="utf-8")
    except (IOError, OSError) as e:
        # S1: Improved error handling
        return 2, f"Error writing file to {output_path}: {e}"
    except Exception as e:
        return 2, f"An unexpected error occurred: {e}"

    return 0, f"Created {output_path}"

    return 0, f"Created {output_path}"
