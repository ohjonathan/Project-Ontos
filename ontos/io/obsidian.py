"""Obsidian-specific file utilities.

Handles Obsidian vault edge cases like BOM and leading whitespace.
"""

from pathlib import Path
from typing import Optional


def read_file_lenient(path: Path) -> str:
    """Read file with Obsidian-compatible leniency.

    Handles common Obsidian vault edge cases:
    1. UTF-8 BOM (Byte Order Mark) at file start
    2. Leading whitespace/newlines before frontmatter delimiter

    Args:
        path: Path to the markdown file.

    Returns:
        File content with BOM stripped and leading whitespace
        normalized for frontmatter detection.
    """
    content = path.read_bytes()

    # Strip UTF-8 BOM if present
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]

    text = content.decode('utf-8')

    # Find first --- after stripping leading whitespace
    stripped = text.lstrip()
    if stripped.startswith('---'):
        return stripped
    return text


def detect_obsidian_vault(path: Path) -> bool:
    """Detect if path is within an Obsidian vault.

    Args:
        path: Path to check.

    Returns:
        True if .obsidian directory found in path or parents.
    """
    current = path.resolve()
    while current != current.parent:
        if (current / '.obsidian').is_dir():
            return True
        current = current.parent
    return False
