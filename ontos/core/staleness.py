"""Staleness detection and describes field validation.

This module contains functions for v2.7 describes field validation
and staleness detection between documentation and described atoms.

IMPURE FUNCTIONS:
    - get_file_modification_date() - calls subprocess.run for git
    - check_staleness() - uses get_file_modification_date()

For testing, mock these functions directly:
    with patch('ontos.core.staleness.get_file_modification_date') as mock:
        mock.return_value = (date(2025, 12, 20), ModifiedSource.GIT)
        result = check_staleness(doc, ctx)
"""

import os
import subprocess
from datetime import date, datetime
from enum import Enum
from typing import Optional, Tuple, List, Dict


class ModifiedSource(Enum):
    """Indicates the source and reliability of last-modified date.
    
    Used by staleness detection to track how we obtained the date.
    """
    GIT = "git"           # From git log (reliable)
    MTIME = "mtime"       # From filesystem (unreliable, git resets this)
    UNCOMMITTED = "uncommitted"  # File exists but not in git yet (treat as today)
    MISSING = "missing"   # File doesn't exist


# In-memory cache for git lookups (C1 from v2.7 spec)
_git_date_cache: Dict[str, Tuple[Optional[date], ModifiedSource]] = {}


def clear_git_cache() -> None:
    """Clear the git date cache. Useful for testing."""
    global _git_date_cache
    _git_date_cache = {}


def get_file_modification_date(filepath: str) -> Tuple[Optional[date], ModifiedSource]:
    """Get last modification date for a file with source tracking.
    
    IMPURE: This function calls subprocess.run() to execute git commands.
    For testing, mock this function directly.
    
    Returns both the date and the source of that date (git, mtime, etc.)
    to indicate reliability. Uses caching for performance.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        (date, source) where source indicates reliability:
        - GIT: From git log (reliable)
        - MTIME: From filesystem (unreliable, git resets this)
        - UNCOMMITTED: File exists but not in git yet (treat as today)
        - MISSING: File doesn't exist
    """
    # Normalize path for cache key
    cache_key = os.path.abspath(filepath)
    
    # Check cache first (C1)
    if cache_key in _git_date_cache:
        return _git_date_cache[cache_key]
    
    result = _fetch_last_modified(filepath)
    _git_date_cache[cache_key] = result
    return result


def _fetch_last_modified(filepath: str) -> Tuple[Optional[date], ModifiedSource]:
    """Internal function to fetch last modified date.
    
    IMPURE: Uses subprocess.run for git commands.
    """
    # Handle missing file
    if not os.path.exists(filepath):
        return (None, ModifiedSource.MISSING)
    
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci", "--", filepath],
            capture_output=True, text=True, timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            # Git has history for this file
            # Format: "2025-12-19 14:30:00 -0800" → extract "2025-12-19"
            date_str = result.stdout.strip().split()[0]
            return (date.fromisoformat(date_str), ModifiedSource.GIT)
        else:
            # File exists but no git history (uncommitted) - treat as today (R2)
            return (date.today(), ModifiedSource.UNCOMMITTED)
    
    except FileNotFoundError:
        # Git not installed (R3) - fall back to mtime
        # Note: warning suppressed, caller should handle via source type
        mtime = os.path.getmtime(filepath)
        return (date.fromtimestamp(mtime), ModifiedSource.MTIME)
    
    except subprocess.TimeoutExpired:
        # Git command hung - fall back to mtime
        mtime = os.path.getmtime(filepath)
        return (date.fromtimestamp(mtime), ModifiedSource.MTIME)


def normalize_describes(value) -> List[str]:
    """Normalize describes field to a list of strings.
    
    Args:
        value: Raw value from YAML frontmatter.
        
    Returns:
        List of described atom IDs (empty list if none).
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None and str(v).strip()]
    return []


def parse_describes_verified(value) -> Optional[date]:
    """Parse describes_verified field to a date.
    
    Args:
        value: Raw value from YAML frontmatter.
        
    Returns:
        date object, or None if not present or invalid.
    """
    if value is None:
        return None
    try:
        # Check datetime BEFORE date, since datetime is a subclass of date
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value.strip())
    except ValueError:
        pass
    return None


class DescribesValidationError:
    """Represents a validation error for describes field."""
    
    def __init__(self, filepath: str, error_type: str, message: str, 
                 field_value: str = None, suggestion: str = None):
        self.filepath = filepath
        self.error_type = error_type
        self.message = message
        self.field_value = field_value
        self.suggestion = suggestion
    
    def __str__(self) -> str:
        return f"[{self.error_type}] {self.filepath}: {self.message}"


class DescribesWarning:
    """Represents a warning for describes field."""
    
    def __init__(self, filepath: str, warning_type: str, message: str):
        self.filepath = filepath
        self.warning_type = warning_type
        self.message = message
    
    def __str__(self) -> str:
        return f"[{self.warning_type}] {self.filepath}: {self.message}"


class StalenessInfo:
    """Information about a stale document."""
    
    def __init__(self, doc_id: str, doc_path: str, describes: List[str],
                 verified_date: date, stale_atoms: List[Tuple[str, date]]):
        self.doc_id = doc_id
        self.doc_path = doc_path
        self.describes = describes
        self.verified_date = verified_date
        self.stale_atoms = stale_atoms  # List of (atom_id, changed_date)
    
    def is_stale(self) -> bool:
        """Return True if document is stale."""
        return len(self.stale_atoms) > 0


def validate_describes_field(
    doc_id: str,
    doc_path: str,
    doc_type: str,
    describes: List[str],
    describes_verified: Optional[date],
    all_docs: Dict[str, dict]  # id -> {type, path}
) -> Tuple[List[DescribesValidationError], List[DescribesWarning]]:
    """Validate describes field according to v2.7 rules.
    
    Args:
        doc_id: ID of the document being validated.
        doc_path: Path to the document.
        doc_type: Type of the document (atom, strategy, etc).
        describes: List of atom IDs this doc claims to describe.
        describes_verified: Date when doc was last verified.
        all_docs: Dict mapping id -> {type, path} for all docs.
        
    Returns:
        (errors, warnings) tuple.
    """
    errors = []
    warnings = []
    
    if not describes:
        return errors, warnings
    
    # Rule: Cannot describe yourself (self-reference)
    if doc_id in describes:
        errors.append(DescribesValidationError(
            filepath=doc_path,
            error_type="self_reference",
            message=f"Document cannot describe itself: '{doc_id}'",
            field_value=f"describes: [..., {doc_id}, ...]",
            suggestion="Remove self-reference from describes field."
        ))
        return errors, warnings
    
    # Note: v2.7 decision - any document type can use describes
    # (removed type constraint check)
    
    # Validate each referenced atom
    for target_id in describes:
        if target_id not in all_docs:
            errors.append(DescribesValidationError(
                filepath=doc_path,
                error_type="unknown_id",
                message=f"Describes references unknown document: {target_id}",
                field_value=f"describes: [..., {target_id}, ...]",
                suggestion=f"Create the document or remove '{target_id}' from describes."
            ))
        else:
            # Verify target is actually an atom
            target_type = all_docs[target_id].get('type', 'unknown')
            if target_type != 'atom':
                errors.append(DescribesValidationError(
                    filepath=doc_path,
                    error_type="type_constraint",
                    message=f"Can only describe atoms. '{target_id}' is type: {target_type}",
                    field_value=f"describes: [..., {target_id}, ...]",
                    suggestion="The describes field can only reference atoms."
                ))
    
    # Rule: describes_verified required if describes is present
    if not describes_verified:
        warnings.append(DescribesWarning(
            filepath=doc_path,
            warning_type="missing_verified",
            message="Document has 'describes' but no 'describes_verified'. Never been verified as current."
        ))
    else:
        # Rule: describes_verified should not be in the future
        if describes_verified > date.today():
            warnings.append(DescribesWarning(
                filepath=doc_path,
                warning_type="future_date",
                message=f"describes_verified date ({describes_verified}) is in the future. Staleness check may never trigger."
            ))
    
    return errors, warnings


def detect_describes_cycles(
    docs_with_describes: List[Tuple[str, List[str]]]  # [(doc_id, describes_list), ...]
) -> List[Tuple[str, str]]:
    """Detect circular describes relationships.
    
    Args:
        docs_with_describes: List of (doc_id, describes_list) tuples.
        
    Returns:
        List of (doc_a, doc_b) pairs that form cycles.
    """
    # Build describes graph
    describes_map = {doc_id: describes for doc_id, describes in docs_with_describes}
    
    cycles = []
    for doc_a, targets in describes_map.items():
        for doc_b in targets:
            # Check if doc_b describes doc_a (direct cycle)
            if doc_b in describes_map and doc_a in describes_map[doc_b]:
                # Add in sorted order to avoid duplicates
                pair = tuple(sorted([doc_a, doc_b]))
                if pair not in cycles:
                    cycles.append(pair)
    
    return cycles


def check_staleness(
    doc_id: str,
    doc_path: str,
    describes: List[str],
    describes_verified: Optional[date],
    id_to_path: Dict[str, str]
) -> Optional[StalenessInfo]:
    """Check if a document is stale (described atoms changed after verification).
    
    IMPURE: Uses get_file_modification_date which calls git subprocess.
    
    Args:
        doc_id: ID of the document.
        doc_path: Path to the document.
        describes: List of IDs this doc describes.
        describes_verified: Date when doc was last verified.
        id_to_path: Dict mapping atom ID -> file path.
        
    Returns:
        StalenessInfo if stale, None otherwise.
    """
    if not describes or not describes_verified:
        return None
    
    stale_atoms = []
    
    for atom_id in describes:
        if atom_id not in id_to_path:
            continue  # Skip unknown (validation error caught elsewhere)
        
        atom_path = id_to_path[atom_id]
        atom_modified, source = get_file_modification_date(atom_path)
        
        if atom_modified is None:
            continue  # Can't determine, skip
        
        if atom_modified > describes_verified:
            stale_atoms.append((atom_id, atom_modified))
    
    if stale_atoms:
        return StalenessInfo(
            doc_id=doc_id,
            doc_path=doc_path,
            describes=describes,
            verified_date=describes_verified,
            stale_atoms=stale_atoms
        )
    
    return None
