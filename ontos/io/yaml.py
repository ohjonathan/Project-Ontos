"""
YAML parsing wrapper for Ontos.

Isolates PyYAML from core modules to maintain stdlib-only constraint in core/.
Core modules that need YAML parsing should accept a parser function as parameter.

Phase 2 Decomposition - Created from Phase2-Implementation-Spec.md Section 4.9
"""

import yaml
from typing import Any, Dict, Optional, Tuple


def parse_yaml(content: str) -> Dict[str, Any]:
    """Parse YAML content into a dictionary.

    Args:
        content: YAML string to parse

    Returns:
        Parsed dictionary

    Raises:
        yaml.YAMLError: If parsing fails
    """
    if not content or not content.strip():
        return {}
    result = yaml.safe_load(content)
    return result if isinstance(result, dict) else {}


def dump_yaml(
    data: Dict[str, Any],
    default_flow_style: Optional[bool] = False,
    *,
    sort_keys: bool = True,
) -> str:
    """Dump dictionary to YAML string.

    Args:
        data: Dictionary to serialize
        default_flow_style: If True, use flow style (inline) for collections
        sort_keys: Preserve the historical public helper default when true.
            Callers that control field order may opt out explicitly.

    Returns:
        YAML string representation
    """
    return yaml.safe_dump(
        data,
        default_flow_style=default_flow_style,
        allow_unicode=True,
        sort_keys=sort_keys,
    )


def split_frontmatter_text(content: str) -> Optional[Tuple[str, str, int]]:
    """Split a Markdown document on line-delimited frontmatter fences.

    A fence must be unindented and contain only ``---`` plus optional trailing
    horizontal whitespace. A literal ``---`` inside a YAML scalar is not a
    delimiter. Returns ``(yaml_text, body, body_offset)`` or ``None``.
    """
    lines = content.splitlines(keepends=True)
    if not lines or not _is_frontmatter_fence(lines[0]):
        return None

    offset = len(lines[0])
    for index in range(1, len(lines)):
        line = lines[index]
        if _is_frontmatter_fence(line):
            frontmatter = "".join(lines[1:index])
            body_offset = offset + len(line)
            body = "".join(lines[index + 1 :])
            return frontmatter, body, body_offset
        offset += len(line)
    return None


def _is_frontmatter_fence(line: str) -> bool:
    """Return true for an unindented fence with optional spaces or tabs."""
    return line.rstrip("\r\n").rstrip(" \t") == "---"


def parse_frontmatter_content(content: str) -> tuple:
    """Parse frontmatter and return (frontmatter_dict, body_string).
    
    This function matches the contract expected by io/files.py:load_document():
        frontmatter_parser: Callable[[str], Tuple[Dict[str, Any], str]]
    
    Args:
        content: Full document content with potential frontmatter
        
    Returns:
        Tuple of (frontmatter_dict, body_string). If no frontmatter found,
        returns ({}, content).
    """
    split = split_frontmatter_text(content)
    if split is None:
        return {}, content
    yaml_text, body, _ = split
    
    try:
        fm = parse_yaml(yaml_text)
        if not fm and yaml_text.strip():
            # YAML was valid but resulted in non-dict (e.g. string) or empty
            # If parts[1] is not empty, it probably should have been a dict
            raise ValueError("Invalid YAML frontmatter: content is not a dictionary")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}")
    
    return fm, body.lstrip("\r\n")


def assert_frontmatter_roundtrip(expected: Dict[str, Any], yaml_text: str) -> None:
    """Fail closed unless serialized frontmatter reloads exactly."""
    try:
        parsed = parse_yaml(yaml_text)
        canonical, _ = parse_frontmatter_content(
            f"---\n{yaml_text.rstrip()}\n---\n"
        )
    except (ValueError, yaml.YAMLError) as exc:
        raise ValueError(
            f"Serialized frontmatter failed round-trip validation: {exc}"
        ) from exc
    if parsed != expected or canonical != expected:
        raise ValueError(
            "Serialized frontmatter failed round-trip validation: "
            f"expected {expected!r}, parsed {canonical!r}"
        )
