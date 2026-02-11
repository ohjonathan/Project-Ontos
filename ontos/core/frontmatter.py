"""Frontmatter parsing and normalization.

This module contains pure functions for parsing and validating
YAML frontmatter in Ontos documents.

PURE FUNCTIONS (Phase 2 refactor):
    - parse_frontmatter() - accepts optional yaml_parser callback
    - normalize_depends_on() - pure string/list normalization
    - normalize_type() - pure string normalization
    - load_common_concepts() - file reading only

For production use:
    frontmatter = parse_frontmatter(filepath, yaml_parser=my_yaml_parser)

The caller (commands layer) provides the IO callback.
"""

import os
import re
from typing import Optional, List, Dict, Any, Callable


def parse_frontmatter(
    filepath: str,
    yaml_parser: Optional[Callable[[str], Dict[str, Any]]] = None
) -> Optional[dict]:
    """Parse YAML frontmatter from a markdown file.

    NON-CANONICAL internal-legacy API. Use io/files.py:load_documents() for runtime loading.
    PURE: Accepts optional callback for YAML parsing.
    When yaml_parser is None, returns raw frontmatter string split only.

    For production use:
        frontmatter = parse_frontmatter(filepath, yaml_parser=my_yaml_parser)

    The caller (commands layer) provides the IO callback.

    Args:
        filepath: Path to the markdown file.
        yaml_parser: Optional callback that takes a YAML string and returns
            a dictionary. If None, attempts to use fallback parsing.

    Returns:
        Dictionary of frontmatter fields, or None if no valid frontmatter.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except (IOError, OSError):
        return None

    if not content.startswith('---'):
        return None

    try:
        parts = content.split('---', 2)
        if len(parts) < 3:
            return None

        yaml_content = parts[1].strip()
        if not yaml_content:
            return {}

        # Use provided parser if available
        if yaml_parser is not None:
            try:
                result = yaml_parser(yaml_content)
                return result if isinstance(result, dict) else None
            except Exception:
                return None

        # Fallback: basic key-value parsing for simple frontmatter
        # This handles common cases without PyYAML dependency
        return _fallback_yaml_parse(yaml_content)

    except Exception:
        return None


def _fallback_yaml_parse(content: str) -> Optional[Dict[str, Any]]:
    """Fallback YAML parser for simple key-value frontmatter.
    
    Handles basic cases like:
        id: some_id
        type: atom
        status: active
        depends_on: [dep1, dep2]
    
    For complex YAML, use the yaml_parser callback with PyYAML.
    
    Args:
        content: YAML content string.
        
    Returns:
        Dictionary of parsed values, or None if parsing fails.
    """
    result = {}
    
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if ':' not in line:
            continue
            
        key, _, value = line.partition(':')
        key = key.strip()
        value = value.strip()
        
        if not key:
            continue
        
        # Handle empty values
        if not value or value in ('null', '~', 'None'):
            result[key] = None
            continue
        
        # Handle inline lists: [item1, item2]
        if value.startswith('[') and value.endswith(']'):
            items = value[1:-1].split(',')
            result[key] = [item.strip().strip('"\'') for item in items if item.strip()]
            continue
        
        # Handle quoted strings
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            result[key] = value[1:-1]
            continue
        
        # Handle booleans
        if value.lower() in ('true', 'yes'):
            result[key] = True
            continue
        if value.lower() in ('false', 'no'):
            result[key] = False
            continue
        
        # Handle numbers
        try:
            if '.' in value:
                result[key] = float(value)
            else:
                result[key] = int(value)
            continue
        except ValueError:
            pass
        
        # Default: string value
        result[key] = value
    
    return result if result else None


def normalize_reference_list(value: Any, field_name: str, on_warning: Optional[Callable[[str], None]] = None) -> List[str]:
    """Normalize reference lists (depends_on, impacts) to List[str].
    
    Args:
        value: Raw value from YAML.
        field_name: Name of field for warning context.
        on_warning: Optional callback for warning messages.
        
    Returns:
        Normalized list of strings.
    """
    if value is None:
        return []
        
    if isinstance(value, (str, int, float, bool)):
        if isinstance(value, str):
            stripped = value.strip()
            return [stripped] if stripped else []
        return [str(value)]
        
    if isinstance(value, list):
        results = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, (str, int, float, bool)):
                if isinstance(item, str):
                    stripped = item.strip()
                    if stripped:
                        results.append(stripped)
                else:
                    results.append(str(item))
            else:
                if on_warning:
                    on_warning(f"Invalid nested type '{type(item).__name__}' in field '{field_name}' dropped.")
        return results
        
    if on_warning:
        on_warning(f"Invalid type '{type(value).__name__}' for field '{field_name}' - expected list or scalar.")
    return []


def normalize_depends_on(value, on_warning: Optional[Callable[[str], None]] = None) -> List[str]:
    """Normalize depends_on field to a list of strings.

    Delegates to the canonical normalize_reference_list utility.

    Args:
        value: Raw value from YAML frontmatter.
        on_warning: Optional callback for warning messages.

    Returns:
        List of dependency IDs (empty list if none).
    """
    return normalize_reference_list(value, "depends_on", on_warning=on_warning)


def normalize_type(value, on_error: Optional[Callable[[str, Any, List[str]], None]] = None) -> Any:
    """Normalize type field to DocumentType enum.
    
    Args:
        value: Raw value from YAML.
        on_error: Optional callback (message, value, options) for failures.
        
    Returns:
        DocumentType enum (ATOM if invalid).
    """
    from ontos.core.types import DocumentType
    
    if isinstance(value, DocumentType):
        return value
        
    # Standard string normalization
    type_str = 'unknown'
    if isinstance(value, str):
        type_str = value.strip().lower()
    elif isinstance(value, list) and value:
        type_str = str(value[0]).strip().lower()
        
    try:
        return DocumentType(type_str)
    except (ValueError, TypeError):
        if on_error:
            options = [t.value for t in DocumentType]
            on_error(f"Invalid doc type '{type_str}'", type_str, options)
        return DocumentType.UNKNOWN

def normalize_status(value, on_error: Optional[Callable[[str, Any, List[str]], None]] = None) -> Any:
    """Normalize status field to DocumentStatus enum.
    
    Args:
        value: Raw value from YAML.
        on_error: Optional callback (message, value, options) for failures.
        
    Returns:
        DocumentStatus enum (DRAFT if invalid).
    """
    from ontos.core.types import DocumentStatus
    
    if isinstance(value, DocumentStatus):
        return value
        
    # Standard string normalization
    status_str = 'unknown'
    if isinstance(value, str):
        status_str = value.strip().lower()
    elif isinstance(value, list) and value:
        status_str = str(value[0]).strip().lower()
        
    try:
        return DocumentStatus(status_str)
    except (ValueError, TypeError):
        if on_error:
            options = [s.value for s in DocumentStatus]
            on_error(f"Invalid doc status '{status_str}'", status_str, options)
        return DocumentStatus.UNKNOWN


def load_common_concepts(docs_dir: str = None) -> set:
    """Load known concepts from Common_Concepts.md if it exists.
    
    Args:
        docs_dir: Documentation directory to search.
    
    Returns:
        Set of known concept strings.
    """
    if docs_dir is None:
        try:
            from ontos_config import DOCS_DIR
            docs_dir = DOCS_DIR
        except ImportError:
            docs_dir = 'docs'
    
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


def normalize_tags(frontmatter: dict) -> list[str]:
    """Extract tags from frontmatter, merging concepts + explicit tags.

    Priority:
    1. Explicit 'tags' field (if present)
    2. 'concepts' field (Ontos standard)

    Args:
        frontmatter: Parsed YAML frontmatter dictionary.

    Returns:
        List of unique tag strings, sorted alphabetically.
    """
    tags = set()

    if 'tags' in frontmatter:
        raw_tags = frontmatter['tags']
        if isinstance(raw_tags, list):
            tags.update(str(t).strip() for t in raw_tags if t)
        elif isinstance(raw_tags, str):
            stripped = raw_tags.strip()
            if stripped:
                tags.add(stripped)

    if 'concepts' in frontmatter:
        concepts = frontmatter['concepts']
        if isinstance(concepts, list):
            tags.update(str(c).strip() for c in concepts if c)

    return sorted(tags)


def normalize_aliases(frontmatter: dict, doc_id: str) -> list[str]:
    """Extract aliases from frontmatter, auto-generating from id.

    Args:
        frontmatter: Parsed YAML frontmatter dictionary.
        doc_id: Document ID for auto-generation.

    Returns:
        List of alias strings including auto-generated variants.
    """
    aliases = set()

    if 'aliases' in frontmatter:
        raw = frontmatter['aliases']
        if isinstance(raw, list):
            aliases.update(str(a).strip() for a in raw if a)
        elif isinstance(raw, str):
            stripped = raw.strip()
            if stripped:
                aliases.add(stripped)

    # Auto-generate aliases from id
    if doc_id:
        # snake_case → Title Case
        aliases.add(doc_id.replace('_', ' ').title())
        # snake_case → kebab-case
        aliases.add(doc_id.replace('_', '-'))

    return sorted(aliases)
