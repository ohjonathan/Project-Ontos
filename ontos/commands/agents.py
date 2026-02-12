"""AGENTS.md and .cursorrules generation command."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from ontos.core.instruction_artifacts import (
    find_repo_root,
    gather_stats,
    generate_agents_content,
    generate_agents_files,
    transform_to_cursorrules,
)


@dataclass
class AgentsOptions:
    """Configuration for agents command."""

    output_path: Optional[Path] = None
    force: bool = False
    format: str = "agents"  # agents|cursor
    all_formats: bool = False
    scope: Optional[str] = None


def _run_agents_command(options: AgentsOptions) -> Tuple[int, str]:
    """Generate AGENTS.md and/or .cursorrules files."""
    repo_root = find_repo_root()
    if repo_root is None:
        return 2, "Error: No repository found. Run from within a git repository or Ontos project."

    return generate_agents_files(
        repo_root=repo_root,
        output_path=options.output_path,
        force=options.force,
        format=options.format,
        all_formats=options.all_formats,
        scope=options.scope,
    )


def agents_command(options: AgentsOptions) -> int:
    """Generate AGENTS.md and/or .cursorrules files and return exit code."""
    exit_code, _ = _run_agents_command(options)
    return exit_code
