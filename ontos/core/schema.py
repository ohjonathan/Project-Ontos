"""Schema versioning for Ontos documents.

This module provides schema version detection, validation, and compatibility
checking for Ontos frontmatter. It enables forward compatibility for V3
migration by allowing documents to declare their schema version.

Per v2.9 implementation plan:
- Schema versions are independent of Ontos versions (2.0, 2.1, 2.2, 3.0)
- Legacy documents without ontos_schema are inferred from field presence
- Documents with future schema versions fail gracefully

STDLIB ONLY: This module uses only Python standard library (3.9+).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


class SchemaCompatibility(Enum):
    """Result of schema compatibility check."""
    COMPATIBLE = "compatible"           # Tool can fully read/write document
    READ_ONLY = "read_only"             # Tool can read but not write safely
    INCOMPATIBLE = "incompatible"       # Tool cannot handle this document


@dataclass
class SchemaCheckResult:
    """Result of checking schema compatibility."""
    compatibility: SchemaCompatibility
    document_version: str
    tool_version: str
    message: str


# Schema version definitions
# Each schema defines required and optional fields
SCHEMA_DEFINITIONS: Dict[str, Dict[str, List[str]]] = {
    "1.0": {
        "required": ["id"],
        "optional": ["type", "depends_on"],
    },
    "2.0": {
        "required": ["id", "type"],
        "optional": ["status", "depends_on", "concepts", "event_type", "impacts"],
    },
    "2.1": {
        "required": ["id", "type"],
        "optional": ["status", "depends_on", "concepts", "describes", "describes_verified"],
    },
    "2.2": {
        "required": ["id", "type", "status"],
        "optional": ["depends_on", "concepts", "ontos_schema", "curation_level"],
    },
    "3.0": {
        "required": ["id", "type", "status", "ontos_schema"],
        "optional": ["depends_on", "concepts", "implements", "tests", "deprecates"],
    },
}

# Current schema version for new documents
CURRENT_SCHEMA_VERSION = "2.2"

# Minimum tool version that can read each schema
SCHEMA_TOOL_REQUIREMENTS: Dict[str, str] = {
    "1.0": "1.0",
    "2.0": "2.0",
    "2.1": "2.7",
    "2.2": "2.9",
    "3.0": "3.0",
}

# Schema version bounds for documentation and validation
MIN_READABLE_SCHEMA = "1.0"   # Oldest schema this tool can read
MAX_READABLE_SCHEMA = "2.2"   # Newest schema this tool fully supports


def parse_version(version_str: str) -> Tuple[int, int]:
    """Parse a version string to major.minor tuple.

    Args:
        version_str: Version string like "2.1" or "3.0".

    Returns:
        Tuple of (major, minor) integers.

    Raises:
        ValueError: If version string is invalid.

    Examples:
        >>> parse_version("2.1")
        (2, 1)
        >>> parse_version("3.0")
        (3, 0)
    """
    if not version_str or not isinstance(version_str, str):
        raise ValueError(f"Invalid version string: {version_str!r}")
    
    version_str = version_str.strip()
    parts = version_str.split('.')
    
    if len(parts) != 2:
        raise ValueError(f"Version must be in 'major.minor' format: {version_str!r}")
    
    try:
        major = int(parts[0])
        minor = int(parts[1])
    except ValueError as e:
        raise ValueError(f"Version components must be integers: {version_str!r}") from e
    
    if major < 0 or minor < 0:
        raise ValueError(f"Version components must be non-negative: {version_str!r}")
    
    return (major, minor)


def detect_schema_version(frontmatter: Dict[str, Any]) -> str:
    """Detect schema version from frontmatter.

    Priority:
    1. Explicit ontos_schema field
    2. Field inference for legacy documents
    3. Default to "1.0"

    Args:
        frontmatter: Dictionary of frontmatter fields.

    Returns:
        Schema version string (e.g., "2.1").

    Examples:
        >>> detect_schema_version({"id": "test", "ontos_schema": "2.2"})
        '2.2'
        >>> detect_schema_version({"id": "test", "describes": ["foo"]})
        '2.1'
        >>> detect_schema_version({"id": "test"})
        '1.0'
    """
    if not frontmatter:
        return "1.0"
    
    # Priority 1: Explicit schema declaration
    if 'ontos_schema' in frontmatter:
        schema = frontmatter['ontos_schema']
        if schema and isinstance(schema, str):
            return schema.strip()
    
    # Priority 2: Field inference for legacy documents
    # Check for v3.0 fields
    if 'implements' in frontmatter or 'tests' in frontmatter or 'deprecates' in frontmatter:
        return "3.0"
    
    # Check for v2.2 fields (curation_level is v2.2+)
    if 'curation_level' in frontmatter:
        return "2.2"
    
    # Check for v2.1 fields (describes is v2.1+)
    if 'describes' in frontmatter or 'describes_verified' in frontmatter:
        return "2.1"
    
    # Check for v2.0 fields (logs have event_type, impacts)
    if 'event_type' in frontmatter or 'impacts' in frontmatter:
        return "2.0"
    
    # Check for v2.0 fields (type is required in v2.0+)
    if 'type' in frontmatter and frontmatter.get('type'):
        return "2.0"
    
    # Default: v1.0 (minimal schema)
    return "1.0"


def check_compatibility(
    doc_version: str,
    tool_version: str
) -> SchemaCheckResult:
    """Check if a tool version can handle a document schema version.

    Args:
        doc_version: Schema version of the document (e.g., "2.1").
        tool_version: Version of the Ontos tool (e.g., "2.8.6").

    Returns:
        SchemaCheckResult with compatibility status and message.

    Examples:
        >>> result = check_compatibility("2.1", "2.9.0")
        >>> result.compatibility == SchemaCompatibility.COMPATIBLE
        True
        >>> result = check_compatibility("3.0", "2.9.0")
        >>> result.compatibility == SchemaCompatibility.READ_ONLY
        True
    """
    try:
        doc_major, doc_minor = parse_version(doc_version)
    except ValueError as e:
        return SchemaCheckResult(
            compatibility=SchemaCompatibility.INCOMPATIBLE,
            document_version=doc_version,
            tool_version=tool_version,
            message=f"Invalid document schema version: {e}"
        )
    
    # Parse tool version (may have patch, e.g., "2.9.0")
    tool_parts = tool_version.split('.')
    try:
        tool_major = int(tool_parts[0])
        tool_minor = int(tool_parts[1]) if len(tool_parts) > 1 else 0
    except (ValueError, IndexError):
        return SchemaCheckResult(
            compatibility=SchemaCompatibility.INCOMPATIBLE,
            document_version=doc_version,
            tool_version=tool_version,
            message=f"Invalid tool version: {tool_version}"
        )
    
    # Check for future major version (incompatible)
    if doc_major > tool_major:
        return SchemaCheckResult(
            compatibility=SchemaCompatibility.INCOMPATIBLE,
            document_version=doc_version,
            tool_version=tool_version,
            message=f"Document uses schema {doc_version}, but tool only supports up to {tool_major}.x"
        )
    
    # Check for future minor version within same major (read-only)
    if doc_major == tool_major and doc_minor > tool_minor:
        return SchemaCheckResult(
            compatibility=SchemaCompatibility.READ_ONLY,
            document_version=doc_version,
            tool_version=tool_version,
            message=f"Document uses schema {doc_version}. Tool {tool_version} can read but may not preserve all fields."
        )
    
    # Check for known schema versions
    if doc_version not in SCHEMA_DEFINITIONS:
        # Unknown but compatible major version - treat as read-only
        if doc_major <= tool_major:
            return SchemaCheckResult(
                compatibility=SchemaCompatibility.READ_ONLY,
                document_version=doc_version,
                tool_version=tool_version,
                message=f"Unknown schema version {doc_version}. Reading with best effort."
            )
    
    # Fully compatible
    return SchemaCheckResult(
        compatibility=SchemaCompatibility.COMPATIBLE,
        document_version=doc_version,
        tool_version=tool_version,
        message="Compatible"
    )


def validate_frontmatter(
    frontmatter: Dict[str, Any],
    schema_version: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """Validate frontmatter against a schema version.

    Args:
        frontmatter: Dictionary of frontmatter fields.
        schema_version: Schema version to validate against (auto-detected if None).

    Returns:
        Tuple of (is_valid, list of error messages).

    Examples:
        >>> valid, errors = validate_frontmatter({"id": "test", "type": "atom"}, "2.0")
        >>> valid
        True
        >>> valid, errors = validate_frontmatter({"type": "atom"}, "2.0")
        >>> valid
        False
    """
    if schema_version is None:
        schema_version = detect_schema_version(frontmatter)
    
    if schema_version not in SCHEMA_DEFINITIONS:
        return True, []  # Unknown schema, can't validate
    
    schema = SCHEMA_DEFINITIONS[schema_version]
    errors = []
    
    # Check required fields
    for field in schema["required"]:
        if field not in frontmatter or frontmatter[field] is None:
            errors.append(f"Missing required field: {field}")
        elif isinstance(frontmatter[field], str) and not frontmatter[field].strip():
            errors.append(f"Required field '{field}' is empty")
    
    return len(errors) == 0, errors


def serialize_frontmatter(fm: Dict[str, Any]) -> str:
    """Serialize frontmatter dict to YAML-like string using STDLIB ONLY.

    This function handles common YAML types without requiring PyYAML.

    Args:
        fm: Frontmatter dictionary.

    Returns:
        YAML-formatted string without the surrounding --- markers.

    Examples:
        >>> serialize_frontmatter({"id": "test", "type": "atom"})
        'id: test\\ntype: atom'
        >>> serialize_frontmatter({"id": "test", "depends_on": ["foo", "bar"]})
        'id: test\\ndepends_on: [foo, bar]'
    """
    lines = []
    
    # Define field order for consistent output
    field_order = [
        'id', 'type', 'status', 'ontos_schema', 'curation_level',
        'depends_on', 'concepts', 'describes', 'describes_verified',
        'event_type', 'impacts', 'implements', 'tests', 'deprecates'
    ]
    
    # Process ordered fields first
    processed = set()
    for key in field_order:
        if key in fm:
            lines.append(_serialize_field(key, fm[key]))
            processed.add(key)
    
    # Process remaining fields in original order
    for key, value in fm.items():
        if key not in processed:
            lines.append(_serialize_field(key, value))
    
    return '\n'.join(lines)


def _serialize_field(key: str, value: Any) -> str:
    """Serialize a single frontmatter field.

    Args:
        key: Field name.
        value: Field value.

    Returns:
        Formatted line like "key: value".
    """
    if value is None:
        return f"{key}: null"
    
    if isinstance(value, bool):
        return f"{key}: {str(value).lower()}"
    
    if isinstance(value, (int, float)):
        return f"{key}: {value}"
    
    if isinstance(value, list):
        if not value:
            return f"{key}: []"
        # Simple list format for short lists
        if all(isinstance(v, str) and ' ' not in v and ':' not in v for v in value):
            items = ', '.join(str(v) for v in value)
            return f"{key}: [{items}]"
        # Multi-line format for complex lists
        lines = [f"{key}:"]
        for item in value:
            lines.append(f"  - {item}")
        return '\n'.join(lines)
    
    if isinstance(value, str):
        # Check if value needs quoting
        if ':' in value or value.startswith('{') or value.startswith('['):
            return f'{key}: "{value}"'
        # Multi-line strings
        if '\n' in value:
            lines = [f"{key}: |"]
            for line in value.split('\n'):
                lines.append(f"  {line}")
            return '\n'.join(lines)
        return f"{key}: {value}"
    
    # Nested dict handling (defensive - rare in Ontos frontmatter)
    if isinstance(value, dict):
        # Serialize nested dict as inline JSON-like format
        import json
        return f"{key}: {json.dumps(value)}"
    
    # Fallback: convert to string
    return f"{key}: {value}"


def add_schema_to_frontmatter(
    frontmatter: Dict[str, Any],
    schema_version: Optional[str] = None
) -> Dict[str, Any]:
    """Add or update ontos_schema field in frontmatter.

    Args:
        frontmatter: Original frontmatter dictionary.
        schema_version: Schema version to set (auto-detected if None).

    Returns:
        New frontmatter dict with ontos_schema field.
    """
    result = frontmatter.copy()
    
    if schema_version is None:
        schema_version = detect_schema_version(frontmatter)
    
    result['ontos_schema'] = schema_version
    return result


def get_schema_info(version: str) -> Optional[Dict[str, List[str]]]:
    """Get schema definition for a version.

    Args:
        version: Schema version string.

    Returns:
        Dictionary with 'required' and 'optional' field lists, or None.
    """
    return SCHEMA_DEFINITIONS.get(version)
