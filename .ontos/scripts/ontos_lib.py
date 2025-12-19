"""Shared utilities for Ontos scripts.

This module contains common functions used across multiple Ontos scripts.
Centralizing them here ensures consistency and simplifies maintenance.
"""

import os
import re
import yaml
import subprocess
from datetime import datetime, date
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple, List, Dict


# =============================================================================
# V2.7 DESCRIBES FIELD TYPES
# =============================================================================


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
    """Internal function to fetch last modified date."""
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
        # Git not installed (R3) - fall back to mtime with warning
        print("WARN: git not found. Falling back to file modification time (less reliable).")
        mtime = os.path.getmtime(filepath)
        return (date.fromtimestamp(mtime), ModifiedSource.MTIME)
    
    except subprocess.TimeoutExpired:
        # Git command hung - fall back to mtime
        print("WARN: git command timed out. Falling back to file modification time.")
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
        parts = [f"ERROR: {self.message}", f"  File: {self.filepath}"]
        if self.field_value:
            parts.append(f"  Field: {self.field_value}")
        if self.suggestion:
            parts.append(f"  To fix: {self.suggestion}")
        return "\n".join(parts)


class DescribesWarning:
    """Represents a warning for describes field."""
    
    def __init__(self, filepath: str, warning_type: str, message: str):
        self.filepath = filepath
        self.warning_type = warning_type
        self.message = message
    
    def __str__(self) -> str:
        return f"WARN: {self.message}\n  File: {self.filepath}"


class StalenessInfo:
    """Information about a stale document."""
    
    def __init__(self, doc_id: str, doc_path: str, describes: List[str],
                 verified_date: date, stale_atoms: List[Tuple[str, date]]):
        self.doc_id = doc_id
        self.doc_path = doc_path
        self.describes = describes
        self.verified_date = verified_date
        self.stale_atoms = stale_atoms  # List of (atom_id, changed_date)
    
    @property
    def is_stale(self) -> bool:
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
        describes: List of IDs this doc describes.
        describes_verified: Date when doc was last verified.
        all_docs: Dict mapping id -> {type, path} for all known docs.
        
    Returns:
        (errors, warnings) tuple.
    """
    errors = []
    warnings = []
    
    if not describes:
        return errors, warnings
    
    # Note: The describes targets (atoms) are validated when checking for unknown IDs below.
    # Any document type can use describes to declare what implementation it documents.
    
    # Rule: describes cannot be empty list (pointless)
    if len(describes) == 0:
        warnings.append(DescribesWarning(
            filepath=doc_path,
            warning_type="empty_describes",
            message="Document has empty 'describes' field. Why declare empty describes?"
        ))
    
    # Rule: Self-reference not allowed
    if doc_id in describes:
        errors.append(DescribesValidationError(
            filepath=doc_path,
            error_type="self_reference",
            message="Document describes itself",
            field_value=f"describes: [{doc_id}]",
            suggestion="Remove the self-reference from the describes list."
        ))
    
    # Rule: All described IDs must exist and be atoms
    for target_id in describes:
        if target_id == doc_id:
            continue  # Already handled above
        
        if target_id not in all_docs:
            errors.append(DescribesValidationError(
                filepath=doc_path,
                error_type="unknown_id",
                message=f"Unknown atom ID '{target_id}' in describes field",
                field_value=f"describes: [..., {target_id}, ...]",
                suggestion=f"Create an atom doc with id: {target_id}, or remove it from describes."
            ))
        else:
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


# =============================================================================
# V2.7 IMMUTABLE HISTORY GENERATION
# =============================================================================


def get_log_date(log_path: str, frontmatter: Optional[dict] = None) -> Optional[date]:
    """Extract date from a log file.
    
    Resolution order:
    1. Frontmatter 'date' field
    2. Filename prefix (YYYY-MM-DD_slug.md)
    3. File modification time (least reliable)
    
    Args:
        log_path: Path to the log file.
        frontmatter: Pre-parsed frontmatter (optional, will parse if not provided).
        
    Returns:
        date object, or None if cannot be determined.
    """
    # 1. Try frontmatter date field
    if frontmatter is None:
        frontmatter = parse_frontmatter(log_path) or {}
    
    if 'date' in frontmatter:
        try:
            date_val = frontmatter['date']
            if isinstance(date_val, date):
                return date_val
            if isinstance(date_val, datetime):
                return date_val.date()
            if isinstance(date_val, str):
                return date.fromisoformat(date_val.strip())
        except ValueError:
            pass
    
    # 2. Try filename prefix (YYYY-MM-DD_slug.md)
    filename = os.path.basename(log_path)
    match = re.match(r'^(\d{4}-\d{2}-\d{2})_', filename)
    if match:
        try:
            return date.fromisoformat(match.group(1))
        except ValueError:
            pass
    
    # 3. Last resort: file mtime (least reliable)
    try:
        mtime = os.path.getmtime(log_path)
        return date.fromtimestamp(mtime)
    except OSError:
        return None


class ParsedLog:
    """Represents a parsed session log for history generation."""
    
    def __init__(self, log_id: str, log_path: str, log_date: date,
                 event_type: str, summary: str, impacts: List[str], concepts: List[str]):
        self.id = log_id
        self.path = log_path
        self.date = log_date
        self.event_type = event_type
        self.summary = summary
        self.impacts = impacts
        self.concepts = concepts


def parse_log_for_history(log_path: str) -> Optional[ParsedLog]:
    """Parse a session log for history generation.
    
    Args:
        log_path: Path to the log file.
        
    Returns:
        ParsedLog object, or None if parsing failed.
    """
    try:
        frontmatter = parse_frontmatter(log_path)
        if not frontmatter:
            return None
        
        log_id = frontmatter.get('id', os.path.basename(log_path).replace('.md', ''))
        log_date = get_log_date(log_path, frontmatter)
        if not log_date:
            return None
        
        # Get event type (default to 'chore' if missing)
        event_type = frontmatter.get('event_type', frontmatter.get('event', 'chore'))
        if isinstance(event_type, list):
            event_type = event_type[0] if event_type else 'chore'
        
        # Get impacts and concepts
        impacts = normalize_depends_on(frontmatter.get('impacts', []))
        concepts = normalize_depends_on(frontmatter.get('concepts', []))
        
        # Get summary from content (first non-header paragraph after frontmatter)
        summary = ""
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Extract content after frontmatter
            parts = content.split('---', 2)
            if len(parts) >= 3:
                body = parts[2].strip()
                # Find first paragraph that's not a header
                for line in body.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        summary = line[:200] + ('...' if len(line) > 200 else '')
                        break
        except (IOError, OSError):
            pass
        
        return ParsedLog(
            log_id=log_id,
            log_path=log_path,
            log_date=log_date,
            event_type=event_type,
            summary=summary,
            impacts=impacts,
            concepts=concepts
        )
    except Exception:
        return None


def sort_logs_deterministically(logs: List[ParsedLog]) -> List[ParsedLog]:
    """Sort logs deterministically for history generation.
    
    Sort order:
    1. Date descending (newest first)
    2. Event type alphabetically
    3. Log ID alphabetically
    
    Args:
        logs: List of ParsedLog objects.
        
    Returns:
        Sorted list of logs.
    """
    return sorted(logs, key=lambda l: (
        -l.date.toordinal(),  # Descending date
        l.event_type,          # Alphabetical type
        l.id                   # Alphabetical ID
    ))


def generate_decision_history(
    logs_dirs: List[str],
    output_path: str = None
) -> Tuple[str, List[str]]:
    """Generate decision_history.md from logs.
    
    v2.7: Makes history a generated artifact rather than manually maintained.
    
    Args:
        logs_dirs: List of directories containing log files.
        output_path: Path to write the generated file (optional).
        
    Returns:
        (markdown_content, list_of_warnings)
    """
    parsed = []
    warnings = []
    active_count = 0
    archived_count = 0
    
    for logs_dir in logs_dirs:
        if not os.path.exists(logs_dir):
            continue
        
        is_archive = 'archive' in logs_dir.lower()
        
        for log_file in os.listdir(logs_dir):
            if not log_file.endswith('.md'):
                continue
            # Only process date-prefixed files (session logs)
            if not log_file[0].isdigit():
                continue
            
            log_path = os.path.join(logs_dir, log_file)
            try:
                log = parse_log_for_history(log_path)
                if log:
                    parsed.append(log)
                    if is_archive:
                        archived_count += 1
                    else:
                        active_count += 1
                else:
                    warnings.append(f"Skipping malformed log: {log_file}")
            except Exception as e:
                warnings.append(f"Skipping malformed log: {log_file} ({e})")
    
    if warnings:
        for w in warnings:
            print(f"WARN: {w}")
    
    # Sort deterministically
    sorted_logs = sort_logs_deterministically(parsed)
    
    # Generate markdown
    now = datetime.now().isoformat(timespec='seconds')
    skipped = len(warnings)
    
    header = f"""<!--
GENERATED FILE - DO NOT EDIT MANUALLY
Regenerated by: ontos_generate_context_map.py
Source: {', '.join(logs_dirs)}
Last generated: {now}
Log count: {active_count} active, {archived_count} archived, {skipped} skipped
-->

---
id: decision_history
type: strategy
status: active
depends_on: [mission]
---

# Decision History

This file is auto-generated from session logs. Do not edit directly.

To regenerate: `python3 .ontos/scripts/ontos_generate_context_map.py`

"""
    
    # Group by date
    content_parts = [header]
    current_date = None
    
    for log in sorted_logs:
        if log.date != current_date:
            current_date = log.date
            content_parts.append(f"## {current_date.isoformat()}\n\n")
        
        # Format entry
        entry = f"### [{log.event_type}] {log.id.replace('_', ' ').replace('log ', '').title()}\n"
        entry += f"- **Log:** `{log.id}`\n"
        if log.impacts:
            entry += f"- **Impacts:** {', '.join(log.impacts)}\n"
        if log.concepts:
            entry += f"- **Concepts:** {', '.join(log.concepts)}\n"
        if log.summary:
            entry += f"\n> {log.summary}\n"
        entry += "\n"
        content_parts.append(entry)
    
    markdown_content = ''.join(content_parts)
    
    # Write to file if output_path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    return markdown_content, warnings


def parse_frontmatter(filepath: str) -> Optional[dict]:
    """Parse YAML frontmatter from a markdown file.

    Args:
        filepath: Path to the markdown file.

    Returns:
        Dictionary of frontmatter fields, or None if no valid frontmatter.
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    if content.startswith('---'):
        try:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                return frontmatter
        except yaml.YAMLError as e:
            print(f"Error parsing YAML in {filepath}: {e}")
    return None


def normalize_depends_on(value) -> list[str]:
    """Normalize depends_on field to a list of strings.

    Handles YAML edge cases: null, empty, string, or list.

    Args:
        value: Raw value from YAML frontmatter.

    Returns:
        List of dependency IDs (empty list if none).
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None and str(v).strip()]
    return []


def normalize_type(value) -> str:
    """Normalize type field to a string.

    Args:
        value: Raw value from YAML frontmatter.

    Returns:
        Type string ('unknown' if invalid).
    """
    if value is None:
        return 'unknown'
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or '|' in stripped:
            return 'unknown'
        return stripped
    if isinstance(value, list):
        if value and value[0] is not None:
            first = str(value[0]).strip()
            if '|' in first:
                return 'unknown'
            return first if first else 'unknown'
    return 'unknown'


def load_common_concepts(docs_dir: str = None) -> set[str]:
    """Load known concepts from Common_Concepts.md if it exists.
    
    Args:
        docs_dir: Documentation directory to search.
    
    Returns:
        Set of known concept strings.
    """
    if docs_dir is None:
        from ontos_config import DOCS_DIR
        docs_dir = DOCS_DIR
    
    possible_paths = [
        os.path.join(docs_dir, 'reference', 'Common_Concepts.md'),
        os.path.join(docs_dir, 'Common_Concepts.md'),
        'docs/reference/Common_Concepts.md',
    ]
    
    concepts_file = None
    for path in possible_paths:
        if os.path.exists(path):
            concepts_file = path
            break
            
    if not concepts_file:
        return set()
    
    concepts = set()
    try:
        with open(concepts_file, 'r', encoding='utf-8') as f:
            content = f.read()
        matches = re.findall(r'\|\s*`([a-z][a-z0-9-]*)`\s*\|', content)
        concepts.update(matches)
    except (IOError, OSError):
        pass
    
    return concepts


def get_git_last_modified(filepath: str) -> Optional[datetime]:
    """Get the last modified date of a file from git history.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        datetime of last modification, or None if not in git.
    """
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cd', '--date=iso-strict', '--', filepath],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            date_str = result.stdout.strip()
            # Handle timezone offset format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return None


def find_last_session_date(logs_dir: str = None) -> str:
    """Find the date of the most recent session log.

    Args:
        logs_dir: Directory containing log files. If None, uses LOGS_DIR from config.

    Returns:
        Date string in YYYY-MM-DD format, or empty string if no logs found.
    """
    if logs_dir is None:
        from ontos_config import LOGS_DIR
        logs_dir = LOGS_DIR
    
    if not os.path.exists(logs_dir):
        return ""

    log_files = []
    for filename in os.listdir(logs_dir):
        if filename.endswith('.md') and len(filename) >= 10:
            date_part = filename[:10]
            if date_part.count('-') == 2:
                log_files.append(date_part)

    if not log_files:
        return ""

    return sorted(log_files)[-1]


def resolve_config(setting_name: str, default=None):
    """Resolve a config value considering mode presets and overrides.
    
    Resolution order:
    1. Explicit override in ontos_config.py
    2. Mode preset value (if ONTOS_MODE is set)
    3. Default from ontos_config_defaults.py
    4. Provided default parameter
    
    Args:
        setting_name: Name of the setting (e.g., 'AUTO_ARCHIVE_ON_PUSH')
        default: Fallback value if setting not found anywhere
    
    Returns:
        Resolved configuration value.
    """
    import ontos_config_defaults as defaults
    
    # 1. Try explicit override in user config
    try:
        import ontos_config as user_config
        if hasattr(user_config, setting_name):
            return getattr(user_config, setting_name)
    except ImportError:
        pass
    
    # 2. Try mode preset
    try:
        import ontos_config as user_config
        mode = getattr(user_config, 'ONTOS_MODE', None)
    except ImportError:
        mode = getattr(defaults, 'ONTOS_MODE', None)
    
    if mode and hasattr(defaults, 'MODE_PRESETS'):
        presets = defaults.MODE_PRESETS.get(mode, {})
        if setting_name in presets:
            return presets[setting_name]
    
    # 3. Try default from ontos_config_defaults.py
    if hasattr(defaults, setting_name):
        return getattr(defaults, setting_name)
    
    # 4. Return provided default
    return default


def get_source() -> Optional[str]:
    """Get session log source with fallback chain.
    
    Resolution order:
    1. ONTOS_SOURCE environment variable
    2. DEFAULT_SOURCE in config
    3. git config user.name
    4. None (caller should prompt)
    
    Returns:
        Source string or None if caller should prompt.
    """
    # 1. Environment variable
    env_source = os.environ.get('ONTOS_SOURCE')
    if env_source:
        return env_source
    
    # 2. Config default
    try:
        from ontos_config import DEFAULT_SOURCE
        if DEFAULT_SOURCE:
            return DEFAULT_SOURCE
    except (ImportError, AttributeError):
        pass
    
    # 3. Git user name
    try:
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # 4. Caller should prompt
    return None


# Branch names that should not be used as auto-slugs
BLOCKED_BRANCH_NAMES = {'main', 'master', 'dev', 'develop', 'HEAD'}


# =============================================================================
# LOG DISCOVERY HELPERS (v2.5+)
# =============================================================================
# Centralized functions for log path resolution, counting, and age detection.
# Used by: ontos_pre_commit_check.py, ontos_generate_context_map.py


def get_logs_dir() -> str:
    """Get the logs directory path based on config.
    
    Respects LOGS_DIR config setting if set, otherwise derives from DOCS_DIR.
    Handles both contributor mode (.ontos-internal) and user mode (docs/logs).
    
    Returns:
        Absolute path to logs directory.
    """
    # Try LOGS_DIR first (most explicit)
    logs_dir = resolve_config('LOGS_DIR', None)
    if logs_dir and os.path.isabs(logs_dir):
        return logs_dir
    
    # Get PROJECT_ROOT for relative path resolution
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        # Fallback if config not available
        return 'docs/logs'
    
    # Contributor mode uses .ontos-internal/logs
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'logs')
    
    # User mode: derive from LOGS_DIR or DOCS_DIR
    if logs_dir:
        return os.path.join(PROJECT_ROOT, logs_dir)
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    return os.path.join(PROJECT_ROOT, docs_dir, 'logs')


def get_log_count() -> int:
    """Count active session logs in logs directory.
    
    Only counts markdown files starting with a digit (date-prefixed logs).
    
    Returns:
        Number of active log files.
    """
    logs_dir = get_logs_dir()
    if not os.path.exists(logs_dir):
        return 0
    
    return len([f for f in os.listdir(logs_dir)
                if f.endswith('.md') and f[0].isdigit()])


def get_logs_older_than(days: int) -> list[str]:
    """Get list of log filenames older than N days.
    
    Args:
        days: Age threshold in days.
        
    Returns:
        List of log filenames (not full paths) older than threshold.
    """
    logs_dir = get_logs_dir()
    if not os.path.exists(logs_dir):
        return []
    
    cutoff = datetime.now() - __import__('datetime').timedelta(days=days)
    old_logs = []
    
    for filename in os.listdir(logs_dir):
        if not filename.endswith('.md') or not filename[0].isdigit():
            continue
        try:
            log_date = datetime.strptime(filename[:10], '%Y-%m-%d')
            if log_date < cutoff:
                old_logs.append(filename)
        except ValueError:
            continue
    
    return old_logs


def get_archive_dir() -> str:
    """Get the archive directory path based on config.
    
    Returns:
        Absolute path to archive directory.
    """
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        return 'docs/archive'
    
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'archive')
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    return os.path.join(PROJECT_ROOT, docs_dir, 'archive')


# =============================================================================
# DEPRECATION WARNING HELPER (v2.5.2+)
# =============================================================================

_deprecation_warned = set()  # Track warnings to avoid spam


def _warn_deprecated(old_path: str, new_path: str) -> None:
    """Issue deprecation warning (once per path per session)."""
    if old_path in _deprecation_warned:
        return
    _deprecation_warned.add(old_path)
    print(f"[DEPRECATION WARNING] Using old path '{old_path}'.")
    print(f"   Expected: '{new_path}'")
    print("   Run 'python3 ontos_init.py' to update your project structure.")


# =============================================================================
# PATH HELPERS WITH BACKWARD COMPATIBILITY (v2.5.2+)
# =============================================================================


def get_decision_history_path() -> str:
    """Get decision_history.md path with backward compatibility.
    
    v2.5.2: Uses nested structure (docs/strategy/decision_history.md)
    Pre-v2.5.2: Falls back to flat structure (docs/decision_history.md)
    
    Returns:
        Absolute path to decision_history.md.
    """
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        return 'docs/strategy/decision_history.md'
    
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'strategy', 'decision_history.md')
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    
    # Try new location first (v2.5.2+)
    new_path = os.path.join(PROJECT_ROOT, docs_dir, 'strategy', 'decision_history.md')
    if os.path.exists(new_path):
        return new_path
    
    # Fall back to old location (pre-v2.5.2)
    old_path = os.path.join(PROJECT_ROOT, docs_dir, 'decision_history.md')
    if os.path.exists(old_path):
        _warn_deprecated(f'{docs_dir}/decision_history.md', f'{docs_dir}/strategy/decision_history.md')
        return old_path
    
    # Return new location for creation
    return new_path


def get_proposals_dir() -> str:
    """Get proposals directory path (mode-aware).
    
    Returns:
        Absolute path to proposals directory.
    """
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        return 'docs/strategy/proposals'
    
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'strategy', 'proposals')
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    return os.path.join(PROJECT_ROOT, docs_dir, 'strategy', 'proposals')


def get_archive_logs_dir() -> str:
    """Get archive/logs directory path with backward compatibility.
    
    v2.5.2: Uses nested structure (docs/archive/logs/)
    Pre-v2.5.2: Falls back to flat structure (docs/archive/)
    
    Returns:
        Absolute path to archive/logs directory.
    """
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        return 'docs/archive/logs'
    
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'archive', 'logs')
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    
    # Try new location first (v2.5.2+)
    new_path = os.path.join(PROJECT_ROOT, docs_dir, 'archive', 'logs')
    if os.path.exists(new_path):
        return new_path
    
    # Fall back to old location (pre-v2.5.2: logs directly in archive/)
    old_path = os.path.join(PROJECT_ROOT, docs_dir, 'archive')
    if os.path.exists(old_path):
        _warn_deprecated(f'{docs_dir}/archive/', f'{docs_dir}/archive/logs/')
        return old_path
    
    # Return new location for creation
    return new_path


def get_archive_proposals_dir() -> str:
    """Get archive/proposals directory path (mode-aware).
    
    New in v2.5.2 - no backward compatibility needed.
    
    Returns:
        Absolute path to archive/proposals directory.
    """
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        return 'docs/archive/proposals'
    
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'archive', 'proposals')
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    return os.path.join(PROJECT_ROOT, docs_dir, 'archive', 'proposals')


def get_concepts_path() -> str:
    """Get Common_Concepts.md path with backward compatibility.
    
    v2.5.2: Uses nested structure (docs/reference/Common_Concepts.md)
    Pre-v2.5.2: Falls back to flat structure (docs/Common_Concepts.md)
    
    Returns:
        Absolute path to Common_Concepts.md.
    """
    try:
        from ontos_config_defaults import PROJECT_ROOT, is_ontos_repo
    except ImportError:
        return 'docs/reference/Common_Concepts.md'
    
    if is_ontos_repo():
        return os.path.join(PROJECT_ROOT, '.ontos-internal', 'reference', 'Common_Concepts.md')
    
    docs_dir = resolve_config('DOCS_DIR', 'docs')
    
    # Try new location first (v2.5.2+)
    new_path = os.path.join(PROJECT_ROOT, docs_dir, 'reference', 'Common_Concepts.md')
    if os.path.exists(new_path):
        return new_path
    
    # Fall back to old location (pre-v2.5.2)
    old_path = os.path.join(PROJECT_ROOT, docs_dir, 'Common_Concepts.md')
    if os.path.exists(old_path):
        _warn_deprecated(f'{docs_dir}/Common_Concepts.md', f'{docs_dir}/reference/Common_Concepts.md')
        return old_path
    
    # Return new location for creation
    return new_path


# =============================================================================
# V2.6 VALIDATION HELPERS
# =============================================================================


def get_git_last_modified(filepath: str) -> Optional[datetime]:
    """Get the last git commit date for a file.
    
    Args:
        filepath: Path to the file to check.
        
    Returns:
        datetime of last modification, or None if not tracked by git.
    """
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ct', filepath],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            timestamp = int(result.stdout.strip())
            return datetime.fromtimestamp(timestamp)
    except (subprocess.SubprocessError, ValueError):
        pass
    return None


def load_decision_history_entries() -> dict:
    """Load decision_history.md entries for validation.
    
    Parses the decision history ledger to enable validation that 
    rejected/approved proposals are properly recorded.
    
    v2.6.1: Improved parsing for deterministic matching by slug and archive path.
    
    Returns:
        Dict with:
          - 'archive_paths': dict mapping archive_path -> slug
          - 'slugs': set of all slugs in ledger
          - 'rejected_slugs': set of slugs with REJECTED in outcome
          - 'approved_slugs': set of slugs with APPROVED in outcome
          - 'outcomes': dict mapping slug -> full outcome text
    """
    history_path = get_decision_history_path()
    entries = {
        'archive_paths': {},  # Now a dict: path -> slug
        'slugs': set(),
        'rejected_slugs': set(),
        'approved_slugs': set(),
        'outcomes': {}
    }
    
    if os.path.exists(history_path):
        with open(history_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Parse table rows: | date | slug | event | outcome | impacted | archive_path |
                if line.startswith('|') and not line.startswith('|:') and not line.startswith('| Date'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 7:
                        slug = parts[2]
                        outcome = parts[4]
                        archive_path = parts[6].strip('`')  # Remove backticks
                        
                        if slug:
                            entries['slugs'].add(slug)
                            entries['outcomes'][slug] = outcome
                            
                            # Deterministic outcome classification
                            outcome_upper = outcome.upper()
                            if 'REJECTED' in outcome_upper:
                                entries['rejected_slugs'].add(slug)
                            if 'APPROVED' in outcome_upper:
                                entries['approved_slugs'].add(slug)
                        
                        if archive_path:
                            entries['archive_paths'][archive_path] = slug
    return entries


def find_draft_proposals() -> list[dict]:
    """Find all draft proposals that may need review.

    v2.6.1: Used by Maintain Ontos to prompt for graduation.

    Returns:
        List of dicts with 'id', 'filepath', 'version', 'age_days'.
    """
    proposals_dir = get_proposals_dir()
    if not proposals_dir or not os.path.exists(proposals_dir):
        return []

    # Get current ONTOS_VERSION for matching
    try:
        from ontos_config_defaults import ONTOS_VERSION
    except ImportError:
        ONTOS_VERSION = None

    draft_proposals = []

    for root, dirs, files in os.walk(proposals_dir):
        for file in files:
            if not file.endswith('.md'):
                continue

            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # Just need frontmatter

                # Check if it's a draft
                if 'status: draft' not in content:
                    continue

                # Extract ID
                id_match = re.search(r'^id:\s*(.+)$', content, re.MULTILINE)
                if not id_match:
                    continue

                doc_id = id_match.group(1).strip()

                # Extract version from filepath or ID (e.g., v2.6, v2_6)
                version_match = re.search(r'v?(\d+)[._-](\d+)', filepath + doc_id)
                version = f'{version_match.group(1)}.{version_match.group(2)}' if version_match else None

                # Get file age
                mtime = os.path.getmtime(filepath)
                age_days = (datetime.now().timestamp() - mtime) / 86400

                # Check if version matches current ONTOS_VERSION
                version_match_current = False
                if version and ONTOS_VERSION:
                    version_match_current = ONTOS_VERSION.startswith(version)

                draft_proposals.append({
                    'id': doc_id,
                    'filepath': filepath,
                    'version': version,
                    'age_days': int(age_days),
                    'version_match': version_match_current,
                })

            except (IOError, OSError):
                continue

    # Sort by version match (True first), then by age
    draft_proposals.sort(key=lambda x: (not x['version_match'], -x['age_days']))

    return draft_proposals

