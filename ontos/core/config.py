"""Configuration helpers.

This module contains functions for resolving configuration values
and getting session source information.

PURE (after Phase 2 refactor): Functions accept optional callbacks for git operations.

For production use:
    source = get_source(git_username_provider=my_git_provider)

The caller (commands layer) provides the IO callback.
"""

import os
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable


# Branch names that should not be used as auto-slugs
BLOCKED_BRANCH_NAMES = {'main', 'master', 'dev', 'develop', 'HEAD'}


# =============================================================================
# Phase 3: Configuration System
# =============================================================================


class ConfigError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""
    pass


@dataclass
class OntosSection:
    """[ontos] section."""
    version: str = "3.0"
    required_version: Optional[str] = None


@dataclass
class PathsConfig:
    """[paths] section."""
    docs_dir: str = "docs"
    logs_dir: str = "docs/logs"
    context_map: str = "Ontos_Context_Map.md"


@dataclass
class ScanningConfig:
    """[scanning] section."""
    skip_patterns: List[str] = field(default_factory=lambda: [
        "_template.md", "archive/*", ".git/*", "node_modules/*", "__pycache__/*"
    ])
    scan_paths: List[str] = field(default_factory=list)
    default_scope: str = "docs"


@dataclass
class ValidationConfig:
    """[validation] section."""
    max_dependency_depth: int = 5
    allowed_orphan_types: List[str] = field(default_factory=lambda: ["atom"])


@dataclass
class WorkflowConfig:
    """[workflow] section."""
    log_retention_count: int = 20  # Required by Roadmap


@dataclass
class HooksConfig:
    """[hooks] section."""
    pre_push: bool = True
    pre_commit: bool = True
    strict: bool = False  # When True, hooks block on validation errors


@dataclass
class McpConfig:
    """[mcp] section."""
    usage_logging: bool = False
    usage_log_path: Optional[str] = None


@dataclass
class OntosConfig:
    """Root configuration object."""
    ontos: OntosSection = field(default_factory=OntosSection)
    paths: PathsConfig = field(default_factory=PathsConfig)
    scanning: ScanningConfig = field(default_factory=ScanningConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    hooks: HooksConfig = field(default_factory=HooksConfig)
    mcp: McpConfig = field(default_factory=McpConfig)


def default_config() -> OntosConfig:
    """Create default configuration."""
    return OntosConfig()


def config_to_dict(config: OntosConfig) -> dict:
    """Convert config dataclass to dict for TOML serialization."""
    return asdict(config)


def _validate_path(path_str: str, repo_root: Path) -> bool:
    """Ensure path resolves within repo root."""
    try:
        resolved = (repo_root / path_str).resolve()
        return resolved.is_relative_to(repo_root)
    except (ValueError, RuntimeError):
        return False


def _validate_types(data: dict) -> None:
    """Validate types in config data before dataclass instantiation."""
    type_requirements = {
        ("validation", "max_dependency_depth"): int,
        ("workflow", "log_retention_count"): int,
        ("hooks", "pre_push"): bool,
        ("hooks", "pre_commit"): bool,
        ("hooks", "strict"): bool,
        ("mcp", "usage_logging"): bool,
        ("mcp", "usage_log_path"): str,
    }

    for (section, key), expected_type in type_requirements.items():
        if section in data and key in data[section]:
            value = data[section][key]
            if section == "mcp" and key == "usage_log_path" and value is None:
                continue
            if not isinstance(value, expected_type):
                raise ConfigError(
                    f"{section}.{key} must be {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )


def dict_to_config(data: dict, repo_root: Optional[Path] = None) -> OntosConfig:
    """Convert dict from TOML to config dataclass."""
    data = _normalize_legacy_config(data)
    _validate_section_names(data)

    # Type validation
    _validate_types(data)

    # Path validation
    if repo_root is not None and "paths" in data:
        paths_section = data["paths"]
        for key in ["docs_dir", "logs_dir", "context_map"]:
            if key in paths_section:
                if not _validate_path(paths_section[key], repo_root):
                    raise ConfigError(
                        f"paths.{key} must resolve within repository root"
                    )

    # Build config with defaults for missing fields
    ontos = OntosSection(**_section_kwargs(OntosSection, "ontos", data.get("ontos")))
    paths = PathsConfig(**_section_kwargs(PathsConfig, "paths", data.get("paths")))
    scanning = ScanningConfig(**_section_kwargs(ScanningConfig, "scanning", data.get("scanning")))
    validation = ValidationConfig(
        **_section_kwargs(ValidationConfig, "validation", data.get("validation"))
    )
    workflow = WorkflowConfig(**_section_kwargs(WorkflowConfig, "workflow", data.get("workflow")))
    hooks = HooksConfig(**_section_kwargs(HooksConfig, "hooks", data.get("hooks")))
    mcp = McpConfig(**_section_kwargs(McpConfig, "mcp", data.get("mcp")))

    return OntosConfig(
        ontos=ontos,
        paths=paths,
        scanning=scanning,
        validation=validation,
        workflow=workflow,
        hooks=hooks,
        mcp=mcp,
    )


def _normalize_legacy_config(data: dict) -> dict:
    """Map known legacy config fields onto the current schema."""
    normalized = {
        key: (dict(value) if isinstance(value, dict) else value)
        for key, value in data.items()
    }
    # Legacy user projects may still carry a top-level [project] section.
    # Current runtime code does not consume those fields, so treat it as a
    # compatibility no-op while keeping strict validation for every other
    # unknown section.
    normalized.pop("project", None)

    validation = normalized.get("validation")
    if not isinstance(validation, dict):
        return normalized

    legacy_strict = validation.pop("strict", None)
    if legacy_strict is None:
        return normalized

    hooks = normalized.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        normalized["hooks"] = hooks
    hooks.setdefault("strict", legacy_strict)
    return normalized


def _validate_section_names(data: dict) -> None:
    """Reject unknown top-level config sections."""
    allowed = {field_info.name for field_info in fields(OntosConfig)}
    for section_name in data:
        if section_name not in allowed:
            raise ConfigError(f"Unknown config section '{section_name}'")


def _section_kwargs(section_type: type, section_name: str, raw_values: object) -> dict:
    """Return constructor kwargs for one config section and reject unknown keys."""
    if not isinstance(raw_values, dict):
        return {}
    allowed = {field_info.name for field_info in fields(section_type)}
    for key in raw_values:
        if key not in allowed:
            raise ConfigError(f"Unknown config key '{section_name}.{key}'")
    return dict(raw_values)


# =============================================================================
# Legacy functions (Phase 2)
# =============================================================================


def get_source(
    git_username_provider: Optional[Callable[[], Optional[str]]] = None
) -> Optional[str]:
    """Get session log source with fallback chain.

    PURE: Accepts optional callback for git operations.

    For production use:
        source = get_source(git_username_provider=my_git_provider)

    The caller (commands layer) provides the IO callback.

    Resolution order:
    1. ONTOS_SOURCE environment variable
    2. DEFAULT_SOURCE in config
    3. git config user.name (via provider)
    4. None (caller should prompt)

    Args:
        git_username_provider: Optional callback that returns git user.name or None.

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

    # 3. Git user name via provider
    if git_username_provider is not None:
        try:
            git_username = git_username_provider()
            if git_username:
                return git_username
        except Exception:
            pass

    # 4. Caller should prompt
    return None


def get_git_last_modified(
    filepath: str,
    git_mtime_provider: Optional[Callable[[Path], Optional[datetime]]] = None
) -> Optional[datetime]:
    """Get the last git commit date for a file.

    PURE: Accepts optional callback for git operations.

    For production use with git:
        from ontos.io.git import get_file_mtime
        modified = get_git_last_modified(path, git_mtime_provider=get_file_mtime)

    Args:
        filepath: Path to the file to check.
        git_mtime_provider: Optional callback that takes a Path and returns
            a datetime from git history.

    Returns:
        datetime of last modification, or None if not tracked by git.
    """
    if git_mtime_provider is not None:
        try:
            return git_mtime_provider(Path(filepath))
        except Exception:
            pass
    return None
