"""
YAML parsing wrapper for Ontos.

Isolates PyYAML from core modules to maintain stdlib-only constraint in core/.
Core modules that need YAML parsing should accept a parser function as parameter.

Phase 2 Decomposition - Created from Phase2-Implementation-Spec.md Section 4.9
"""

import yaml
from typing import Any, Dict, Optional


def parse_yaml(content: str) -> Dict[str, Any]:
    """Parse YAML content into a dictionary.

    Args:
        content: YAML string to parse

    Returns:
        Parsed dictionary (empty dict if parsing fails or content is empty)
    """
    if not content or not content.strip():
        return {}
    try:
        result = yaml.safe_load(content)
        return result if isinstance(result, dict) else {}
    except yaml.YAMLError:
        return {}


def dump_yaml(data: Dict[str, Any], default_flow_style: bool = False) -> str:
    """Dump dictionary to YAML string.

    Args:
        data: Dictionary to serialize
        default_flow_style: If True, use flow style (inline) for collections

    Returns:
        YAML string representation
    """
    return yaml.dump(data, default_flow_style=default_flow_style, allow_unicode=True)


def parse_frontmatter_yaml(content: str) -> Optional[Dict[str, Any]]:
    """Parse YAML frontmatter from document content.

    Extracts content between --- markers at the start of the document.

    Args:
        content: Full document content with potential frontmatter

    Returns:
        Parsed frontmatter dict, or None if no valid frontmatter found
    """
    if not content.startswith('---'):
        return None

    lines = content.split('\n')
    end_idx = None

    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            end_idx = i
            break

    if end_idx is None:
        return None

    yaml_content = '\n'.join(lines[1:end_idx])
    return parse_yaml(yaml_content)


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
    if not content.startswith('---'):
        return {}, content
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    
    fm = parse_yaml(parts[1])
    body = parts[2].lstrip('\n')
    return fm, body

