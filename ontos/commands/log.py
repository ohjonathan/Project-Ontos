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
