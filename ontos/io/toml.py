"""
TOML configuration loading and writing.

Supports Python 3.9+ with tomli fallback for older versions.

Phase 2 Decomposition - Created from Phase2-Implementation-Spec.md Section 4.8
"""

from pathlib import Path
from typing import Any, Dict, Optional

# Python 3.11+ has tomllib in stdlib
try:
    import tomllib
except ImportError:
    # Python 3.9-3.10 needs the tomli package
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore


def load_config(path: Path) -> Dict[str, Any]:
    """Load configuration from TOML file.

    Args:
        path: Path to .toml file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If TOML parsing fails or tomli not available
    """
    if tomllib is None:
        raise ValueError(
            "TOML support requires Python 3.11+ or the 'tomli' package. "
            "Install with: pip install tomli"
        )

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config_if_exists(path: Path) -> Optional[Dict[str, Any]]:
    """Load configuration from TOML file if it exists.

    Args:
        path: Path to .toml file

    Returns:
        Configuration dictionary or None if file doesn't exist
    """
    if not path.exists():
        return None
    try:
        return load_config(path)
    except (ValueError, FileNotFoundError):
        return None


def write_config(path: Path, config: Dict[str, Any]) -> None:
    """Write configuration to TOML file.

    Note: This is a simple implementation. For complex TOML writing,
    consider using the tomlkit package.

    Args:
        path: Destination path
        config: Configuration dictionary
    """
    def _format_value(v: Any) -> str:
        """Format a value for TOML output."""
        if v is None:
            return '""'  # TOML doesn't have null, use empty string
        elif isinstance(v, bool):
            return str(v).lower()
        elif isinstance(v, str):
            # Escape quotes and backslashes
            escaped = v.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        elif isinstance(v, (int, float)):
            return str(v)
        elif isinstance(v, list):
            items = ", ".join(_format_value(item) for item in v)
            return f'[{items}]'
        else:
            return str(v)

    lines = []
    for key, value in config.items():
        if isinstance(value, dict):
            lines.append(f'[{key}]')
            for k, v in value.items():
                if v is None:
                    continue
                lines.append(f'{k} = {_format_value(v)}')
            lines.append('')
        else:
            if value is None:
                continue
            lines.append(f'{key} = {_format_value(value)}')

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configuration dictionaries.

    Later configs override earlier ones.

    Args:
        *configs: Configuration dictionaries to merge

    Returns:
        Merged configuration
    """
    result: Dict[str, Any] = {}
    for config in configs:
        if config:
            for key, value in config.items():
                if isinstance(value, dict) and isinstance(result.get(key), dict):
                    # Deep merge for nested dicts
                    result[key] = {**result[key], **value}
                else:
                    result[key] = value
    return result
