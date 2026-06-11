"""Config file I/O operations."""
from pathlib import Path
from typing import Optional

from ontos.core.config import (
    OntosConfig,
    ConfigError,
    default_config,
    dict_to_config,
    config_to_dict,
)
from ontos.io.toml import load_config, write_config

CONFIG_FILENAME = ".ontos.toml"


def find_config(start_path: Optional[Path] = None) -> Optional[Path]:
    """Find .ontos.toml walking up directory tree."""
    path = start_path or Path.cwd()
    for parent in [path] + list(path.parents):
        config_path = parent / CONFIG_FILENAME
        if config_path.exists():
            return config_path
    return None


def load_project_config(
    config_path: Optional[Path] = None,
    repo_root: Optional[Path] = None,
) -> OntosConfig:
    """Load config from file, or return defaults if not found.
    
    Args:
        config_path: Explicit path to config file, or None to search
        repo_root: Repository root for path validation
        
    Returns:
        OntosConfig instance
        
    Raises:
        ConfigError: If config file exists but is malformed
    """
    if config_path is None:
        # (#133) When the caller names a repo root, that root IS the project:
        # use exactly repo_root/.ontos.toml or defaults. No upward walk —
        # discovery above repo_root silently inherited an unrelated ancestor
        # config (verified leak: a child repo without .ontos.toml picked up
        # the parent's allowed_orphan_types, changing orphan counts).
        if repo_root is not None:
            candidate = Path(repo_root) / CONFIG_FILENAME
            if not candidate.exists():
                return default_config()
            config_path = candidate
        else:
            config_path = find_config()

    if config_path is None:
        return default_config()
    
    if not config_path.exists():
        return default_config()

    # M1 Fix: Raise ConfigError on malformed TOML (don't silently default)
    try:
        data = load_config(config_path)
    except (ValueError, FileNotFoundError) as e:
        raise ConfigError(f"Failed to parse {config_path}: {e}") from e

    # Use config file's parent as repo root if not specified
    effective_repo_root = repo_root or config_path.parent

    return dict_to_config(data, repo_root=effective_repo_root)


def save_project_config(config: OntosConfig, path: Path) -> None:
    """Save configuration to .ontos.toml file."""
    data = config_to_dict(config)
    write_config(path, data)


def config_exists(path: Optional[Path] = None) -> bool:
    """Check if .ontos.toml exists."""
    check_path = path or Path.cwd() / CONFIG_FILENAME
    return check_path.exists()
