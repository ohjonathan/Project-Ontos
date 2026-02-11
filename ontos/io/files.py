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
from dataclasses import dataclass

from ontos.core.types import DocumentType, DocumentStatus, DocumentData
from ontos.core.cache import DocumentCache


@dataclass
class DocumentLoadIssue:
    code: str  # parse_error | duplicate_id | invalid_enum | invalid_reference_type
    path: Path
    message: str
    doc_id: Optional[str] = None
    field: Optional[str] = None
    value: Optional[Any] = None


@dataclass
class DocumentLoadResult:
    documents: Dict[str, DocumentData]
    issues: List[DocumentLoadIssue]
    duplicate_ids: Dict[str, List[Path]]  # sorted; first path is canonical kept doc

    @property
    def has_errors(self) -> bool:
        """True if any issues were found during loading."""
        return len(self.issues) > 0

    @property
    def has_fatal_errors(self) -> bool:
        """True if any fatal issues (duplicates, parse errors) were found."""
        fatal_codes = {"duplicate_id", "parse_error", "io_error"}
        return any(issue.code in fatal_codes for issue in self.issues)


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


def load_frontmatter(
    path: Path,
    frontmatter_parser: Callable[[str], Tuple[Dict[str, Any], str]]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Load and return frontmatter and body from a file.

    Args:
        path: Path to document
        frontmatter_parser: Function to parse frontmatter from content

    Returns:
        Tuple of (frontmatter_dict, body_string). Returns (None, None) if file not found.
    """
    try:
        content = path.read_text(encoding="utf-8")
        return frontmatter_parser(content)
    except OSError:
        return None, None


def load_documents(
    paths: List[Path],
    frontmatter_parser: Callable[[str], Tuple[Dict[str, Any], str]],
    cache: Optional[DocumentCache] = None
) -> DocumentLoadResult:
    """Load multiple documents with duplicate detection and error tracking.

    Args:
        paths: List of file paths to load
        frontmatter_parser: Parser function (S4 contract)
        cache: Optional DocumentCache for mtime-based optimization

    Returns:
        DocumentLoadResult containing docs, issues, and collision details
    """
    documents: Dict[str, DocumentData] = {}
    issues: List[DocumentLoadIssue] = []
    duplicate_ids: Dict[str, List[Path]] = {}
    
    # Determinism: paths processed in sorted order
    sorted_paths = sorted(paths)
    
    for path in sorted_paths:
        try:
            doc = None
            mtime = None
            
            if cache:
                try:
                    mtime = path.stat().st_mtime
                    doc = cache.get(path, mtime)
                except OSError:
                    pass # Handled below by catch-all
            
            if doc is None:
                # Lenient read (BOM stripping and leading lstrip for frontmatter detection)
                raw_bytes = path.read_bytes()
                if raw_bytes.startswith(b'\xef\xbb\xbf'):
                    raw_bytes = raw_bytes[3:]
                content = raw_bytes.decode('utf-8', errors='replace').lstrip()
                
                doc = load_document_from_content(path, content, frontmatter_parser)
                
                if cache and mtime is not None:
                    cache.set(path, doc, mtime)
            
            # Duplicate ID handling
            if doc.id in documents:
                # Collision detected
                if doc.id not in duplicate_ids:
                    duplicate_ids[doc.id] = [documents[doc.id].filepath]
                duplicate_ids[doc.id].append(path)
                
                issues.append(DocumentLoadIssue(
                    code="duplicate_id",
                    path=path,
                    message=f"Duplicate ID '{doc.id}' found in {path}. Keeping original from {documents[doc.id].filepath}.",
                    doc_id=doc.id
                ))
                continue
                
            documents[doc.id] = doc
            
        except (ValueError, UnicodeDecodeError) as e:
            # S4: parse failures skip with warning
            issues.append(DocumentLoadIssue(
                code="parse_error",
                path=path,
                message=f"Error parsing {path.name}: {e}"
            ))
        except OSError as e:
            issues.append(DocumentLoadIssue(
                code="io_error",
                path=path,
                message=f"IO error reading {path.name}: {e}"
            ))
            
    return DocumentLoadResult(
        documents=documents,
        issues=issues,
        duplicate_ids=duplicate_ids
    )


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
    raw_bytes = path.read_bytes()
    if raw_bytes.startswith(b'\xef\xbb\xbf'):
        raw_bytes = raw_bytes[3:]
    content = raw_bytes.decode('utf-8', errors='replace').lstrip()
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
    from ontos.core.frontmatter import (
    normalize_depends_on, 
    normalize_type, 
    normalize_status, 
    normalize_tags, 
    normalize_aliases
)
    from ontos.core.staleness import normalize_describes
    from ontos.core.cache import DocumentCache # This import is not used in this function, but kept as per instruction.
    
    fm, body = frontmatter_parser(content)
    
    # Core fields (B1 Canonical Mapping)
    doc_id = fm.get('id', path.stem)
    doc_type = normalize_type(fm.get('type'))
    doc_status = normalize_status(fm.get('status'))
    depends_on = normalize_depends_on(fm.get('depends_on'))
    impacts = normalize_depends_on(fm.get('impacts'))
    tags = normalize_tags(fm)
    aliases = normalize_aliases(fm, doc_id)
    describes = normalize_describes(fm.get('describes'))

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
        describes=describes
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
