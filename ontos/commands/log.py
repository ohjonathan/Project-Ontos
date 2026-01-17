"""
Session log creation command.

Orchestrates the creation of session logs using
extracted core and io modules.

Phase 2 Decomposition - Created from Phase2-Implementation-Spec.md Section 4.11
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple

from ontos.core.suggestions import suggest_impacts, load_document_index, validate_concepts
from ontos.core.types import TEMPLATES, SECTION_TEMPLATES


# Event type aliases for common shorthand names
EVENT_TYPE_ALIASES = {
    "feat": "feature",
    "docs": "chore",
    "test": "chore",
    "perf": "refactor",
    "release": "chore",
}


def _get_template(event_type: str) -> str:
    """Get template for event type, handling aliases."""
    canonical = EVENT_TYPE_ALIASES.get(event_type, event_type)
    return TEMPLATES.get(canonical, TEMPLATES.get("chore", ""))


@dataclass
class EndSessionOptions:
    """Configuration options for session log creation."""
    event_type: str = "chore"
    topic: Optional[str] = None
    auto_mode: bool = False
    source: Optional[str] = None
    concepts: List[str] = field(default_factory=list)
    impacts: List[str] = field(default_factory=list)
    branch: Optional[str] = None
    dry_run: bool = False


@dataclass
class LogOptions:
    """CLI-level options for log command."""
    event_type: str = ""
    source: str = ""
    epoch: str = ""  # Deprecated: alias for source
    title: str = ""
    topic: str = ""
    auto: bool = False
    json_output: bool = False
    quiet: bool = False


def create_session_log(
    project_root: Path,
    options: EndSessionOptions,
    git_info: Dict[str, Any]
) -> Tuple[str, Path]:
    """Create a session log file.

    Args:
        project_root: Path to project root
        options: Session log options
        git_info: Dictionary with git information (branch, commits, changed_files)

    Returns:
        Tuple of (log content, output path)
    """
    # Determine log metadata
    branch = options.branch or git_info.get("branch", "unknown")
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Generate topic slug
    topic = options.topic or _generate_auto_topic(git_info.get("commits", []))
    topic_slug = _slugify(topic)
    
    # Generate log ID
    log_id = f"log_{date_str.replace('-', '')}_{topic_slug}"
    
    # Build frontmatter
    frontmatter = _build_frontmatter(
        log_id=log_id,
        event_type=options.event_type,
        source=options.source or "unknown",
        branch=branch,
        concepts=options.concepts,
        impacts=options.impacts,
    )
    
    # Get template body (with alias support for Bug 3 fix)
    template = _get_template(options.event_type)
    
    # Fill in section placeholders
    body = f"# {topic}\n\n{template}"
    for section, placeholder in SECTION_TEMPLATES.items():
        body = body.replace(f"## {section}\n\n", f"## {section}\n\n{placeholder}\n\n")
    
    # Combine content
    content = f"---\n{frontmatter}---\n\n{body}"
    
    # Determine output path (Bug 4 fix: use config if available)
    try:
        from ontos_config import LOGS_DIR
        logs_dir = Path(LOGS_DIR)
        # Align relative path with project_root to prevent CWD-dependent output
        if not logs_dir.is_absolute():
            logs_dir = project_root / logs_dir
    except ImportError:
        logs_dir = project_root / "docs" / "logs"
    
    filename = f"{date_str}_{topic_slug}.md"
    output_path = logs_dir / filename
    
    return content, output_path


def suggest_session_impacts(
    context_map_path: Path,
    changed_files: List[str],
    commit_messages: List[str]
) -> List[str]:
    """Suggest impacts for a session log.

    Args:
        context_map_path: Path to context map file
        changed_files: List of changed file paths
        commit_messages: List of commit messages

    Returns:
        List of suggested impact doc_ids
    """
    if not context_map_path.exists():
        return []
    
    content = context_map_path.read_text(encoding="utf-8")
    doc_index = load_document_index(content)
    
    return suggest_impacts(changed_files, doc_index, commit_messages)


def validate_session_concepts(
    context_map_path: Path,
    concepts: List[str]
) -> Tuple[List[str], List[str]]:
    """Validate concepts for a session log.

    Args:
        context_map_path: Path to context map file
        concepts: List of concepts to validate

    Returns:
        Tuple of (valid_concepts, unknown_concepts)
    """
    if not context_map_path.exists():
        return concepts, []
    
    from ontos.core.suggestions import load_common_concepts
    content = context_map_path.read_text(encoding="utf-8")
    known = load_common_concepts(content)
    
    return validate_concepts(concepts, known)


def _build_frontmatter(
    log_id: str,
    event_type: str,
    source: str,
    branch: str,
    concepts: List[str],
    impacts: List[str]
) -> str:
    """Build YAML frontmatter for session log."""
    lines = [
        f"id: {log_id}",
        "type: log",
        "status: active",
        f"event_type: {event_type}",
        f"source: {source}",
        f"branch: {branch}",
        f"created: {datetime.now().strftime('%Y-%m-%d')}",
    ]
    
    if concepts:
        concepts_str = ", ".join(concepts)
        lines.append(f"concepts: [{concepts_str}]")
    
    if impacts:
        impacts_str = ", ".join(impacts)
        lines.append(f"impacts: [{impacts_str}]")
    
    return "\n".join(lines) + "\n"


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    if not text:
        return "session"
    
    # Lowercase and replace non-alphanumeric with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower())
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Limit length
    if len(slug) > 50:
        slug = slug[:50].rstrip('-')
    
    return slug or "session"


def _generate_auto_topic(commits: List[str]) -> str:
    """Generate topic from commit messages."""
    if not commits:
        return "session"

    # Use first commit message as topic basis
    first_commit = commits[0]

    # Clean up common prefixes
    prefixes = ["feat:", "fix:", "chore:", "docs:", "refactor:", "test:"]
    for prefix in prefixes:
        if first_commit.lower().startswith(prefix):
            first_commit = first_commit[len(prefix):].strip()
            break

    # Take first 50 chars
    return first_commit[:50] if first_commit else "session"


def log_command(options: LogOptions) -> int:
    """Execute log command from CLI.

    Orchestrates git info gathering, log creation, and file writing.

    Args:
        options: CLI-level log options

    Returns:
        Exit code (0 for success)
    """
    from ontos.io.git import (
        get_git_root,
        get_current_branch,
        get_commits_since_push,
        get_changed_files_since_push,
    )

    # Get project root
    project_root = get_git_root()
    if not project_root:
        if not options.quiet:
            print("Error: Not in a git repository")
        return 1

    # Gather git info
    git_info = {
        "branch": get_current_branch() or "unknown",
        "commits": get_commits_since_push(),
        "changed_files": get_changed_files_since_push(),
    }

    # Map CLI options to session options
    event_type = options.event_type or "chore"
    if options.epoch and not options.source:
        options.source = options.epoch

    session_options = EndSessionOptions(
        event_type=event_type,
        topic=options.title or options.topic or None,
        auto_mode=options.auto,
        source=options.source or "cli",
    )

    # Create the log content
    content, output_path = create_session_log(project_root, session_options, git_info)

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the file
    output_path.write_text(content, encoding="utf-8")

    # Create marker for pre-push enforcement (best effort)
    _create_archive_marker(project_root, output_path)

    # Output result
    if options.json_output:
        import json
        print(json.dumps({
            "status": "success",
            "path": str(output_path),
            "log_id": output_path.stem,
        }))
    elif not options.quiet:
        print(f"Session log created: {output_path}")

    return 0


def _create_archive_marker(project_root: Path, log_path: Path) -> None:
    """Create marker file to signal that a session was archived."""
    marker_path = project_root / ".ontos" / "session_archived"
    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(str(log_path), encoding="utf-8")
    except OSError:
        # Non-fatal: marker creation failure shouldn't break logging
        pass
