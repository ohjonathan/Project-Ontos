---
id: phase3_implementation_spec
type: strategy
status: active
depends_on: [v3_0_implementation_roadmap, v3_0_technical_architecture]
concepts: [configuration, init, toml, cli, v3-transition]
---

# Ontos v3.0 Implementation Spec: Phase 3 — Configuration & Init

**Version:** 1.1
**Author:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-13
**Status:** Ready for Implementation

---

## Changelog (v1.0 → v1.1)

### Critical Fix
- **C1:** Add context map generation to init flow (Roadmap 5.3 step 6)

### Major Fixes
- **M1:** Add `log_retention_count: int = 20` to WorkflowConfig
- **M2:** Add TOML error handling with `ConfigError` exception
- **M3:** Add type validation in `dict_to_config()`
- **M4:** Add path sanitization to prevent traversal outside repo root

### Risk Mitigations
- Add `ConfigError` exception class
- Add `ONTOS_HOOK_MARKER` constant for hook detection
- Add worktree detection (`.git` as file)
- Add PermissionError handling
- Add Windows limitations documentation

### Minor Updates
- Remove unused `shutil` import
- Create `.git/hooks` directory if missing
- Add config resolution tests
- Document `--interactive` reserved for v3.1

---

## 1. Overview

### 1.1 Purpose

Phase 3 implements the modern configuration system for Ontos v3.0:
- `ontos init` command for project initialization
- `.ontos.toml` configuration file support
- Config resolution with proper precedence (CLI → env → file → defaults)
- Hook installation with collision safety

### 1.2 Scope

**In Scope:**
- Create `commands/init.py` - new init command implementation
- Create `core/config.py` dataclasses - OntosConfig and section configs
- Create `io/config.py` - config file I/O (find, load, save)
- Update `cli.py` - add init subcommand routing
- `.ontos.toml` template and format specification

**Out of Scope (Phase 4+):**
- Full CLI restructure
- MCP layer
- Daemon functionality

**Reserved for v3.1:**
- `--interactive` flag for wizard-style init

### 1.3 Entry Criteria

- [x] Phase 2 complete and merged
- [x] Golden Master tests passing
- [x] Core/IO separation validated
- [x] `io/toml.py` exists with TOML parsing utilities

### 1.4 Exit Criteria

- [ ] `ontos init` creates valid `.ontos.toml`
- [ ] `ontos init` generates initial context map
- [ ] Config resolution works (CLI → env → file → defaults)
- [ ] Legacy `.ontos/scripts/` detection warns appropriately
- [ ] Hook collision safety implemented
- [ ] All tests pass
- [ ] Golden Master passes

### 1.5 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing workflows | Medium | High | Golden Master after every change |
| Circular imports | Medium | High | Strict layer separation |
| Config format changes | Low | Medium | Version field in config |
| Malformed TOML input | Medium | Medium | ConfigError with helpful messages |
| Hook collision false positive | Low | Medium | Explicit marker constant |

---

## 2. Current State Analysis

### 2.1 Post-Phase 2 Structure

```
ontos/
├── __init__.py          # v3.0.0a1
├── cli.py               # Two-stage delegation to _scripts/ontos.py
├── core/                # 16 modules
│   ├── config.py        # EXISTING: get_source(), get_git_last_modified() only
│   ├── types.py         # EXISTING: DocumentType, DocumentStatus, ValidationError, etc.
│   └── ...
├── io/                  # 5 modules
│   ├── toml.py          # EXISTING: load_config, write_config, merge_configs
│   ├── files.py         # EXISTING: find_project_root, scan_documents
│   └── ...
├── commands/            # 9 modules (NO init.py yet)
│   ├── map.py           # Native implementation
│   ├── log.py           # Native implementation
│   └── ...              # 7 wrapper modules
└── _scripts/
    ├── ontos_init.py    # LEGACY: 585 lines, generates Python config
    └── ...
```

### 2.2 Existing io/toml.py (COMPLETE)

**Already implemented in Phase 2:**
```python
def load_config(path: Path) -> Dict[str, Any]
def load_config_if_exists(path: Path) -> Optional[Dict[str, Any]]
def write_config(path: Path, config: Dict[str, Any]) -> None
def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]
```

**Status:** No changes needed to io/toml.py

### 2.3 Existing core/config.py (PARTIAL)

**Current content:**
- `BLOCKED_BRANCH_NAMES` constant
- `get_source()` - resolves session source with callback injection
- `get_git_last_modified()` - gets file modification date

**Missing:** Config dataclasses (OntosConfig, PathsConfig, etc.)

### 2.4 CLI Structure

**Current routing:** `cli.py` → `_scripts/ontos.py` (unified dispatcher) → specific script

**Init already routed:** `ontos init` maps to `ontos_init.py` (legacy Python config generator)

### 2.5 Gap Analysis

| Roadmap Assumption | Current Reality | Gap |
|--------------------|-----------------|-----|
| `io/toml.py` needs creation | Already exists from Phase 2 | **No gap** |
| `commands/init.py` needed | Does not exist | **Gap - create new** |
| Config dataclasses needed | Only helper functions exist | **Gap - add dataclasses** |
| `io/config.py` needed | Does not exist | **Gap - create new** |

---

## 3. Target State

### 3.1 Package Structure After Phase 3

```
ontos/
├── core/
│   ├── config.py        # MODIFIED: Add config dataclasses + ConfigError
│   └── ...
├── io/
│   ├── config.py        # NEW: Config file I/O with error handling
│   ├── toml.py          # EXISTING (no changes)
│   └── ...
├── commands/
│   ├── init.py          # NEW: ontos init implementation
│   └── ...
└── _scripts/
    └── ontos.py         # MODIFIED: Route init to commands/init.py
```

### 3.2 Configuration File Format

```toml
# .ontos.toml - Ontos project configuration

[ontos]
version = "3.0"
# required_version = ">=3.0.0"  # Uncomment to enforce

[paths]
docs_dir = "docs"
logs_dir = "docs/logs"
context_map = "Ontos_Context_Map.md"

[scanning]
skip_patterns = ["_template.md", "archive/*"]

[validation]
max_dependency_depth = 5
allowed_orphan_types = ["atom"]
strict = false

[workflow]
enforce_archive_before_push = true
require_source_in_logs = true
log_retention_count = 20

[hooks]
pre_push = true
pre_commit = true
```

### 3.3 Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `core/config.py` | Config dataclasses, defaults, validation, ConfigError (no I/O) |
| `io/config.py` | Find/load/save config files, error handling |
| `commands/init.py` | `ontos init` command implementation |
| `io/toml.py` | Low-level TOML parsing (existing) |

---

## 4. File Specifications

### 4.1 `core/config.py` (MODIFY - Add Dataclasses)

**Add to existing file** (keep get_source, get_git_last_modified):

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

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
    skip_patterns: List[str] = field(default_factory=lambda: ["_template.md", "archive/*"])

@dataclass
class ValidationConfig:
    """[validation] section."""
    max_dependency_depth: int = 5
    allowed_orphan_types: List[str] = field(default_factory=lambda: ["atom"])
    strict: bool = False

@dataclass
class WorkflowConfig:
    """[workflow] section."""
    enforce_archive_before_push: bool = True
    require_source_in_logs: bool = True
    log_retention_count: int = 20  # v1.1: Added per Roadmap config template

@dataclass
class HooksConfig:
    """[hooks] section."""
    pre_push: bool = True
    pre_commit: bool = True

@dataclass
class OntosConfig:
    """Root configuration object."""
    ontos: OntosSection = field(default_factory=OntosSection)
    paths: PathsConfig = field(default_factory=PathsConfig)
    scanning: ScanningConfig = field(default_factory=ScanningConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    hooks: HooksConfig = field(default_factory=HooksConfig)

def default_config() -> OntosConfig:
    """Create default configuration."""
    return OntosConfig()

def config_to_dict(config: OntosConfig) -> dict:
    """Convert config dataclass to dict for TOML serialization."""
    from dataclasses import asdict
    return asdict(config)

def _validate_path(path_str: str, repo_root: Path) -> bool:
    """
    Ensure path resolves within repo root.

    v1.1: Added to prevent path traversal (M4).
    """
    try:
        resolved = (repo_root / path_str).resolve()
        return resolved.is_relative_to(repo_root)
    except (ValueError, RuntimeError):
        return False

def _validate_types(data: dict) -> None:
    """
    Validate types in config data before dataclass instantiation.

    v1.1: Added for type safety (M3).

    Raises:
        ConfigError: If a value has an incorrect type.
    """
    type_requirements = {
        ("validation", "max_dependency_depth"): int,
        ("validation", "strict"): bool,
        ("workflow", "enforce_archive_before_push"): bool,
        ("workflow", "require_source_in_logs"): bool,
        ("workflow", "log_retention_count"): int,
        ("hooks", "pre_push"): bool,
        ("hooks", "pre_commit"): bool,
    }

    for (section, key), expected_type in type_requirements.items():
        if section in data and key in data[section]:
            value = data[section][key]
            if not isinstance(value, expected_type):
                raise ConfigError(
                    f"{section}.{key} must be {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

def dict_to_config(data: dict, repo_root: Optional[Path] = None) -> OntosConfig:
    """
    Convert dict from TOML to config dataclass.

    Args:
        data: Dictionary from TOML parsing
        repo_root: Repository root for path validation (optional)

    Raises:
        ConfigError: If types are invalid or paths escape repo root.
    """
    # v1.1: Type validation (M3)
    _validate_types(data)

    # v1.1: Path validation (M4)
    if repo_root is not None and "paths" in data:
        paths_section = data["paths"]
        for key in ["docs_dir", "logs_dir", "context_map"]:
            if key in paths_section:
                if not _validate_path(paths_section[key], repo_root):
                    raise ConfigError(
                        f"paths.{key} must resolve within repository root"
                    )

    # Build config with defaults for missing fields
    ontos = OntosSection(**data.get("ontos", {}))
    paths = PathsConfig(**data.get("paths", {}))
    scanning = ScanningConfig(**data.get("scanning", {}))
    validation = ValidationConfig(**data.get("validation", {}))
    workflow = WorkflowConfig(**data.get("workflow", {}))
    hooks = HooksConfig(**data.get("hooks", {}))

    return OntosConfig(
        ontos=ontos,
        paths=paths,
        scanning=scanning,
        validation=validation,
        workflow=workflow,
        hooks=hooks,
    )
```

**Architecture Constraint:** stdlib-only, no io/ imports

---

### 4.2 `io/config.py` (NEW)

```python
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
from ontos.io.toml import load_config_if_exists, write_config

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
    """
    Load config from file, or return defaults if not found.

    v1.1: Added error handling for malformed TOML (M2).

    Args:
        config_path: Path to config file. If None, searches up directory tree.
        repo_root: Repository root for path validation. Defaults to config parent.

    Returns:
        OntosConfig with loaded or default values.

    Raises:
        ConfigError: If config file exists but is malformed or invalid.
    """
    if config_path is None:
        config_path = find_config()

    if config_path is None:
        return default_config()

    # v1.1: Error handling for malformed TOML (M2)
    try:
        data = load_config_if_exists(config_path)
    except Exception as e:
        raise ConfigError(f"Failed to parse {config_path}: {e}") from e

    if data is None:
        return default_config()

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
```

---

### 4.3 `commands/init.py` (NEW)

```python
"""Ontos project initialization command."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import os
import stat

from ontos.core.config import default_config, ConfigError
from ontos.io.config import save_project_config, config_exists

# v1.1: Explicit marker for hook detection (m3)
ONTOS_HOOK_MARKER = "# ontos-managed-hook"

@dataclass
class InitOptions:
    """Configuration for init command."""
    path: Path = None
    force: bool = False
    interactive: bool = False  # v1.1: Reserved for v3.1
    skip_hooks: bool = False

def init_command(options: InitOptions) -> Tuple[int, str]:
    """
    Initialize a new Ontos project.

    Returns:
        Tuple of (exit_code, message)

    Exit Codes:
        0: Success
        1: Already initialized (use --force)
        2: Not a git repository
        3: Hooks skipped due to existing non-Ontos hooks
    """
    project_root = options.path or Path.cwd()

    # 1. Check if already initialized
    config_path = project_root / ".ontos.toml"
    if config_path.exists() and not options.force:
        return 1, "Already initialized. Use --force to reinitialize."

    # 2. Check for git repository (v1.1: handle worktrees)
    git_check = _check_git_repo(project_root)
    if git_check is not None:
        return git_check

    # 3. Detect legacy .ontos/scripts/
    legacy_path = project_root / ".ontos" / "scripts"
    if legacy_path.exists():
        print("Warning: Legacy .ontos/scripts/ detected. Consider migrating.")

    # 4. Create default config
    config = default_config()
    save_project_config(config, config_path)

    # 5. Create directory structure
    _create_directories(project_root, config)

    # 6. Generate initial context map (v1.1: Added per Roadmap 5.3 step 6 - C1)
    try:
        from ontos.commands.map import generate_context_map, GenerateMapOptions
        map_options = GenerateMapOptions(
            output_path=project_root / config.paths.context_map
        )
        generate_context_map(project_root, map_options)
    except Exception as e:
        print(f"Warning: Could not generate initial context map: {e}")

    # 7. Install hooks (with collision safety)
    hooks_status = _install_hooks(project_root, options)

    # 8. Print success
    msg = f"Initialized Ontos in {project_root}\n"
    msg += f"Created: .ontos.toml, {config.paths.context_map}\n"
    msg += "Tip: Run 'ontos export' for AI assistant integration"

    return hooks_status, msg

def _check_git_repo(project_root: Path) -> Optional[Tuple[int, str]]:
    """
    Check if path is a valid git repository.

    v1.1: Handle git worktrees where .git is a file (m4).

    Returns:
        None if valid git repo, or (exit_code, message) tuple if not.
    """
    git_path = project_root / ".git"

    if git_path.is_dir():
        return None  # Normal git repo

    if git_path.is_file():
        # v1.1: Git worktree or submodule - .git is a file pointing to actual repo
        return None  # Still valid

    return 2, "Not a git repository. Run 'git init' first."

def _create_directories(root: Path, config) -> None:
    """Create standard directory structure."""
    dirs = [
        config.paths.docs_dir,
        config.paths.logs_dir,
        f"{config.paths.docs_dir}/strategy",
        f"{config.paths.docs_dir}/reference",
        f"{config.paths.docs_dir}/archive",
    ]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

def _get_hooks_dir(root: Path) -> Path:
    """
    Get the hooks directory for a git repository.

    v1.1: Handle worktrees and create hooks dir if missing (m4, m5).
    """
    git_path = root / ".git"

    if git_path.is_file():
        # Worktree: .git is a file containing "gitdir: /path/to/actual/.git/worktrees/name"
        content = git_path.read_text().strip()
        if content.startswith("gitdir:"):
            actual_git = Path(content[7:].strip())
            # For worktrees, hooks are in the main repo, not the worktree
            # Navigate up from worktrees/name to .git/hooks
            if "worktrees" in actual_git.parts:
                main_git = actual_git.parent.parent
                hooks_dir = main_git / "hooks"
            else:
                hooks_dir = actual_git / "hooks"
        else:
            hooks_dir = root / ".git" / "hooks"
    else:
        hooks_dir = root / ".git" / "hooks"

    # v1.1: Create hooks directory if missing (m5)
    hooks_dir.mkdir(parents=True, exist_ok=True)

    return hooks_dir

def _install_hooks(root: Path, options: InitOptions) -> int:
    """
    Install git hooks with collision safety.

    v1.1: Added PermissionError handling (m6).
    """
    if options.skip_hooks:
        return 0

    try:
        hooks_dir = _get_hooks_dir(root)
    except Exception as e:
        print(f"Warning: Could not access hooks directory: {e}")
        return 3

    hooks = ["pre-push", "pre-commit"]
    skipped = []

    for hook in hooks:
        hook_path = hooks_dir / hook
        try:
            if hook_path.exists():
                if _is_ontos_hook(hook_path):
                    # Our hook - safe to replace
                    _write_shim_hook(hook_path, hook)
                elif options.force:
                    # Force overwrite
                    _write_shim_hook(hook_path, hook)
                else:
                    # Foreign hook - skip
                    skipped.append(hook)
                    # v1.1: Improved message with actionable hint
                    print(f"Warning: Existing {hook} hook detected. Skipping. "
                          f"Use --force to overwrite, or manually integrate.")
            else:
                _write_shim_hook(hook_path, hook)
        except PermissionError as e:
            # v1.1: Handle permission errors gracefully (m6)
            print(f"Warning: Cannot write {hook} hook (permission denied): {e}")
            skipped.append(hook)
        except Exception as e:
            print(f"Warning: Failed to install {hook} hook: {e}")
            skipped.append(hook)

    return 3 if skipped else 0

def _is_ontos_hook(path: Path) -> bool:
    """
    Check if hook file is an Ontos shim.

    v1.1: Use explicit marker instead of substring matching (m3).
    """
    try:
        content = path.read_text()
        return ONTOS_HOOK_MARKER in content
    except Exception:
        return False

def _write_shim_hook(path: Path, hook_type: str) -> None:
    """
    Write minimal shim hook.

    v1.1: Includes ONTOS_HOOK_MARKER for future detection.
    """
    shim = f'''#!/usr/bin/env python3
{ONTOS_HOOK_MARKER}
"""Ontos {hook_type} hook (shim). Delegates to global CLI."""
import subprocess
import sys

try:
    sys.exit(subprocess.call(["ontos", "hook", "{hook_type}"] + sys.argv[1:]))
except FileNotFoundError:
    try:
        sys.exit(subprocess.call([sys.executable, "-m", "ontos", "hook", "{hook_type}"] + sys.argv[1:]))
    except Exception:
        print("Warning: ontos not found. Skipping hook.", file=sys.stderr)
        sys.exit(0)
'''
    path.write_text(shim)

    # v1.1: chmod is no-op on Windows but we still call it (m9)
    # Git will run hooks through shell which handles this
    try:
        path.chmod(0o755)
    except OSError:
        # Windows: chmod may fail, but hooks will still work
        pass
```

---

### 4.4 CLI Updates

**Modify `_scripts/ontos.py`** to route `init` to new implementation:

```python
# In COMMANDS dict, update init entry
COMMANDS = {
    ...
    'init': ('ontos.commands.init', 'Initialize Ontos project'),  # Changed
    ...
}

# In dispatch logic, handle new-style commands
if command == 'init':
    from ontos.commands.init import init_command, InitOptions
    options = InitOptions(
        path=Path.cwd(),
        force='--force' in sys.argv or '-f' in sys.argv,
        interactive=False,  # v1.1: Reserved for v3.1
        skip_hooks='--skip-hooks' in sys.argv,
    )
    code, msg = init_command(options)
    print(msg)
    sys.exit(code)
```

---

## 5. Migration Tasks

### Day 1: Core Config Dataclasses

| Task | Description | Verification |
|------|-------------|--------------|
| 5.1.1 | Add ConfigError exception to `core/config.py` | Import test |
| 5.1.2 | Add config dataclasses to `core/config.py` | Import test |
| 5.1.3 | Add `default_config()` function | Unit test |
| 5.1.4 | Add `config_to_dict()` function | Unit test |
| 5.1.5 | Add `_validate_types()` function | Unit test |
| 5.1.6 | Add `_validate_path()` function | Unit test |
| 5.1.7 | Add `dict_to_config()` with validation | Unit test |
| 5.1.8 | Update `core/__init__.py` exports | Import test |
| 5.1.9 | Run Golden Master | Must pass |

### Day 2: IO Config Module

| Task | Description | Verification |
|------|-------------|--------------|
| 5.2.1 | Create `io/config.py` | File exists |
| 5.2.2 | Implement `find_config()` | Unit test |
| 5.2.3 | Implement `load_project_config()` with error handling | Unit test |
| 5.2.4 | Implement `save_project_config()` | Unit test |
| 5.2.5 | Update `io/__init__.py` exports | Import test |
| 5.2.6 | Run Golden Master | Must pass |

### Day 3: Init Command

| Task | Description | Verification |
|------|-------------|--------------|
| 5.3.1 | Create `commands/init.py` | File exists |
| 5.3.2 | Add `ONTOS_HOOK_MARKER` constant | Import test |
| 5.3.3 | Implement `_check_git_repo()` with worktree support | Unit test |
| 5.3.4 | Implement `_get_hooks_dir()` with directory creation | Unit test |
| 5.3.5 | Implement `init_command()` with context map generation | Unit test |
| 5.3.6 | Implement hook installation with PermissionError handling | Unit test |
| 5.3.7 | Implement collision detection with marker | Unit test |
| 5.3.8 | Update `commands/__init__.py` exports | Import test |
| 5.3.9 | Run Golden Master | Must pass |

### Day 4: CLI Integration

| Task | Description | Verification |
|------|-------------|--------------|
| 5.4.1 | Update `_scripts/ontos.py` routing | Manual test |
| 5.4.2 | Test `ontos init --help` | Output correct |
| 5.4.3 | Test `ontos init` in empty dir | Creates config + context map |
| 5.4.4 | Test `ontos init --force` | Overwrites |
| 5.4.5 | Run Golden Master | Must pass |

### Day 5: Integration & Polish

| Task | Description | Verification |
|------|-------------|--------------|
| 5.5.1 | End-to-end test: init → map → log | Full workflow |
| 5.5.2 | Test legacy detection warning | Warning printed |
| 5.5.3 | Test hook collision safety | Skips foreign hooks |
| 5.5.4 | Test worktree detection | .git as file handled |
| 5.5.5 | Test malformed TOML error handling | ConfigError raised |
| 5.5.6 | Add docstrings | Coverage |
| 5.5.7 | Final Golden Master | Must pass |

---

## 6. Test Specifications

### 6.1 Unit Tests

| Test File | Tests |
|-----------|-------|
| `tests/core/test_config.py` | Dataclasses, defaults, dict conversion, type validation, path validation |
| `tests/io/test_config.py` | Find, load, save config, error handling, config resolution |
| `tests/commands/test_init.py` | All init scenarios |

### 6.2 Key Test Cases

```python
# tests/core/test_config.py

def test_default_config():
    """Default config has expected values."""

def test_config_to_dict_roundtrip():
    """config_to_dict and dict_to_config are inverse operations."""

def test_validate_types_rejects_string_for_int():
    """Type validation rejects wrong types with ConfigError."""

def test_validate_path_rejects_traversal():
    """Path validation rejects paths outside repo root."""

def test_dict_to_config_missing_sections():
    """Missing sections use defaults."""


# tests/io/test_config.py

def test_find_config_walks_up_tree():
    """find_config walks up directory tree."""

def test_load_project_config_returns_defaults_if_missing():
    """Missing config returns default values."""

def test_load_project_config_raises_on_malformed_toml():
    """Malformed TOML raises ConfigError with helpful message."""

def test_load_project_config_validates_paths():
    """Path traversal attempts raise ConfigError."""


# tests/commands/test_init.py

def test_init_empty_directory():
    """Init in empty git repo creates .ontos.toml and context map."""

def test_init_already_initialized():
    """Init fails with exit code 1 if config exists."""

def test_init_force_reinitialize():
    """Init --force overwrites existing config."""

def test_init_not_git_repo():
    """Init fails with exit code 2 if not git repo."""

def test_init_git_worktree():
    """Init works when .git is a file (worktree)."""

def test_init_detects_legacy():
    """Init warns if .ontos/scripts/ exists."""

def test_init_hook_collision_skip():
    """Init skips existing non-Ontos hooks."""

def test_init_hook_collision_force():
    """Init --force overwrites existing hooks."""

def test_init_hook_marker_detection():
    """Hooks with ONTOS_HOOK_MARKER are recognized as ours."""

def test_init_creates_hooks_directory():
    """Init creates .git/hooks if missing."""

def test_init_handles_permission_error():
    """Init handles PermissionError gracefully."""

def test_init_generates_context_map():
    """Init generates initial context map."""
```

---

## 7. Verification Protocol

### After Each Module

1. New module imports successfully
2. Unit tests pass
3. Golden Master passes
4. No circular imports

### Final Verification

```bash
# In a fresh test directory
git init test-project && cd test-project
ontos init
# Verify: .ontos.toml created, dirs created, hooks installed, context map generated
cat .ontos.toml
cat Ontos_Context_Map.md
ls docs/
ls .git/hooks/

# Test workflow
ontos map
ontos log -e chore -t "Test session"
```

---

## 8. Files to Modify/Create

| File | Action | Lines |
|------|--------|-------|
| `ontos/core/config.py` | MODIFY | +120 |
| `ontos/io/config.py` | CREATE | ~70 |
| `ontos/commands/init.py` | CREATE | ~200 |
| `ontos/_scripts/ontos.py` | MODIFY | +15 |
| `ontos/core/__init__.py` | MODIFY | +5 |
| `ontos/io/__init__.py` | MODIFY | +3 |
| `ontos/commands/__init__.py` | MODIFY | +2 |
| `tests/core/test_config.py` | CREATE | ~150 |
| `tests/io/test_config.py` | CREATE | ~100 |
| `tests/commands/test_init.py` | CREATE | ~200 |

**Total new code:** ~600 lines
**Total test code:** ~450 lines

---

## 9. Architecture Constraints

1. **`core/config.py` must NOT import from `io/`**
2. **`core/config.py` must be stdlib-only** (dataclasses, typing, pathlib)
3. **`io/config.py` may import from `core/config`** (types only)
4. **`commands/init.py` may import from both** core and io
5. **Config loading is optional** — commands work without .ontos.toml

---

## 10. Success Criteria

- [ ] `ontos init` creates valid `.ontos.toml`
- [ ] `ontos init` generates initial context map
- [ ] Config dataclasses properly serialize/deserialize
- [ ] Type validation catches invalid config values
- [ ] Path validation prevents traversal outside repo
- [ ] Hook collision detection uses explicit marker
- [ ] Worktree detection works (.git as file)
- [ ] PermissionError handled gracefully
- [ ] Legacy `.ontos/scripts/` detection warns
- [ ] All existing tests pass
- [ ] Golden Master passes
- [ ] No circular imports introduced

---

## 11. Platform Considerations

### 11.1 Windows Limitations (Best-Effort)

Per V3.0-Technical-Architecture.md Section 12.2, Windows support is "best-effort."

| Issue | Behavior | Mitigation |
|-------|----------|------------|
| `chmod(0o755)` no-op | Hooks won't have execute bit | Git runs hooks through shell; works anyway |
| Shebang ignored in CMD | `#!/usr/bin/env python3` not executed | Python shim uses `subprocess.call()` directly |
| CRLF line endings | May affect hook content | Python handles transparently |

### 11.2 macOS Considerations

| Issue | Behavior | Mitigation |
|-------|----------|------------|
| Case-insensitive FS | `.Ontos.toml` ≠ `.ontos.toml` | Config filename is lowercase; not an issue |
| Quarantine attribute | N/A | Hooks are created locally, not downloaded |

---

## 12. Open Questions (All Decided)

| Question | Decision | Reference |
|----------|----------|-----------|
| Config file location | `.ontos.toml` | Chief Architect Response §1.1 |
| Init failure behavior | Exit 1 + `--force` hint | Chief Architect Response §1.2 |
| Init UX flow | Minimal; `--interactive` reserved for v3.1 | Chief Architect Response §1.3 |

---

*End of Specification v1.1*
