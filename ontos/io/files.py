"""
File system operations for Ontos.

Provides file I/O utilities that core modules should NOT call directly.
This module handles the type normalization boundary - converting strings to enums.

Phase 2 Decomposition - Created from Phase2-Implementation-Spec.md Section 4.7
"""

import os
from fnmatch import fnmatch
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Any

from ontos.core.types import DocumentType, DocumentStatus, DocumentData


def find_project_root(start_path: Path = None) -> Path:
    """Find Ontos project root by walking up from start_path.

    Resolution precedence:
    1. Nearest `.ontos.toml` file
    2. Directory containing `.ontos/` or `.ontos-internal/`
    3. Git repository root (`.git/` directory)
    4. Raises FileNotFoundError

    Args:
        start_path: Starting directory (defaults to cwd)

    Returns:
        Path to project root

    Raises:
        FileNotFoundError: If no project root found
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    while current != current.parent:
        # Check for .ontos.toml
        if (current / ".ontos.toml").exists():
            return current
        # Check for .ontos or .ontos-internal directories
        if (current / ".ontos").exists() or (current / ".ontos-internal").exists():
            return current
        # Check for .git
        if (current / ".git").exists():
            return current
        current = current.parent

    raise FileNotFoundError(
        f"No Ontos project found. Run 'ontos init' to initialize, "
        f"or ensure you're in a git repository."
    )


def scan_documents(
    dirs: List[Path],
    skip_patterns: List[str] = None
) -> List[Path]:
    """Recursively find markdown files.

    Args:
        dirs: Directories to scan
        skip_patterns: Glob patterns to skip

    Returns:
        List of markdown file paths
    """
    skip_patterns = skip_patterns or []
    results = set()

    for dir_path in dirs:
        if not dir_path.exists():
            continue
        for md_file in dir_path.rglob("*.md"):
            # Check skip patterns against full path for robust matching
            skip = False
            path_str = str(md_file)
            for pattern in skip_patterns:
                if fnmatch(path_str, pattern) or md_file.match(pattern):
                    skip = True
                    break
            if not skip:
                results.add(md_file.resolve())

    return sorted(list(results))


def read_document(path: Path) -> str:
    """Read document content.

    Args:
        path: Path to document

    Returns:
        Document content as string
    """
    return path.read_text(encoding="utf-8")


def load_document(
    path: Path,
    frontmatter_parser: Callable[[str], Tuple[Dict[str, Any], str]]
) -> DocumentData:
    """Load and normalize a document file.

    This is the type normalization boundary - strings become enums here.

    Args:
        path: Path to document
        frontmatter_parser: Function to parse frontmatter from content

    Returns:
        DocumentData with normalized types
    """
    content = path.read_text(encoding="utf-8")
    return load_document_from_content(path, content, frontmatter_parser)


def load_document_from_content(
    path: Path,
    content: str,
    frontmatter_parser: Callable[[str], Tuple[Dict[str, Any], str]]
) -> DocumentData:
    """Load and normalize a document from provided content.

    Args:
        path: Original file path (for ID fallback and metadata)
        content: File content string
        frontmatter_parser: Function to parse frontmatter from content

    Returns:
        DocumentData with normalized types
    """
    from ontos.core.frontmatter import normalize_tags, normalize_aliases
    
    fm, body = frontmatter_parser(content)
    
    doc_id = fm.get("id", path.stem)

    # Normalize strings to enums at this boundary
    type_str = fm.get("type", "atom")
    status_str = fm.get("status", "draft")

    # Handle unknown types gracefully
    try:
        doc_type = DocumentType(type_str)
    except ValueError:
        doc_type = DocumentType.ATOM

    try:
        doc_status = DocumentStatus(status_str)
    except ValueError:
        doc_status = DocumentStatus.DRAFT

    # Normalize tags and aliases
    tags = normalize_tags(fm)
    aliases = normalize_aliases(fm, doc_id)

    # Normalize depends_on to list
    depends_on = fm.get("depends_on", [])
    if depends_on is None:
        depends_on = []
    elif isinstance(depends_on, str):
        depends_on = [depends_on]

    # Normalize impacts to list
    impacts = fm.get("impacts", [])
    if impacts is None:
        impacts = []
    elif isinstance(impacts, str):
        impacts = [impacts]

    return DocumentData(
        id=doc_id,
        type=doc_type,
        status=doc_status,
        filepath=path,
        frontmatter=fm,
        content=body,
        depends_on=depends_on,
        impacts=impacts,
        tags=tags,
        aliases=aliases,
    )


def get_file_mtime(path: Path) -> Optional[datetime]:
    """Get file modification time from filesystem.

    Args:
        path: Path to file

    Returns:
        Datetime or None if file doesn't exist
    """
    try:
        stat = path.stat()
        return datetime.fromtimestamp(stat.st_mtime)
    except OSError:
        return None


def write_text_file(
    path: Path,
    content: str,
    encoding: str = "utf-8"
) -> None:
    """Write text content to file.

    For simple writes. Use SessionContext for transactional multi-file writes.

    Args:
        path: Destination path
        content: Content to write
        encoding: File encoding
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)
