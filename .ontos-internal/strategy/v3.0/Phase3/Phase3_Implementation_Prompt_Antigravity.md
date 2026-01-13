---
id: phase3_implementation_prompt_antigravity
type: strategy
status: active
depends_on: [phase3_implementation_spec, chief_architect_phase3_response]
concepts: [configuration, init, implementation, v3-transition]
---

# Ontos v3.0 Phase 3: Implementation Prompt for Antigravity

**Author:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-13
**Spec Version:** 1.1
**Target:** Antigravity (Developer Agent)

---

## Overview

You will implement Phase 3 of Ontos v3.0: the Configuration & Init system. This includes:

1. **Config dataclasses** in `core/config.py` — OntosConfig, section configs, validation
2. **Config I/O** in `io/config.py` — find, load, save `.ontos.toml` files
3. **Init command** in `commands/init.py` — project initialization with hooks
4. **CLI routing** in `_scripts/ontos.py` — route `ontos init` to new implementation

**Source of truth:** `.ontos-internal/strategy/v3.0/Phase3/Phase3-Implementation-Spec.md` v1.1

---

## Pre-Implementation Checklist

Before writing any code, verify:

- [ ] On correct branch (create `phase3-config-init` from `main`)
- [ ] Phase 2 is merged and working
- [ ] Golden Master tests pass on current main
- [ ] Read and understand the spec (Phase3-Implementation-Spec.md v1.1)

**Commands to run:**
```bash
git checkout main
git pull origin main
git checkout -b phase3-config-init
pytest tests/ -v  # Must pass before starting
```

---

## Architecture Constraints (DO NOT VIOLATE)

These constraints are **mandatory**. Violating them breaks the architecture.

### 1. core/config.py must NOT import from io/
```python
# FORBIDDEN in ontos/core/config.py:
from ontos.io import anything      # NO
from ontos.io.toml import ...      # NO
from ontos.io.files import ...     # NO

# ALLOWED:
from dataclasses import dataclass  # YES
from typing import List, Optional  # YES
from pathlib import Path           # YES
```

### 2. core/config.py must be stdlib-only
```python
# FORBIDDEN:
import tomli          # NO
import yaml           # NO

# ALLOWED (stdlib only):
from dataclasses import dataclass, field  # YES
from typing import List, Optional         # YES
from pathlib import Path                  # YES
```

### 3. io/config.py may import from core/config
```python
# ALLOWED:
from ontos.core.config import OntosConfig, default_config, ConfigError  # YES
from ontos.io.toml import load_config_if_exists, write_config           # YES
```

### 4. commands/init.py may import from both core and io
```python
# ALLOWED:
from ontos.core.config import default_config, ConfigError   # YES
from ontos.io.config import save_project_config             # YES
from ontos.commands.map import generate_context_map         # YES
```

### 5. Use existing io/toml.py functions
```python
# EXISTING FUNCTIONS (do NOT reimplement):
from ontos.io.toml import load_config_if_exists  # Returns Optional[Dict]
from ontos.io.toml import write_config           # Writes dict to TOML file
```

---

## Open Question Decisions (Implement These)

| Question | Decision | Implementation |
|----------|----------|----------------|
| Config location | `.ontos.toml` | Use `CONFIG_FILENAME = ".ontos.toml"` |
| Init failure | Exit 1 + `--force` | Return `(1, "Already initialized...")` |
| Init UX | Minimal defaults | Set `interactive=False`, reserve for v3.1 |

---

## Task Sequence

### Day 1: Core Config Module

#### Task 3.1.1: Add ConfigError exception

**File:** `ontos/core/config.py` (MODIFY — file exists)

**Instructions:**
1. Open `ontos/core/config.py`
2. Keep ALL existing code (BLOCKED_BRANCH_NAMES, get_source, get_git_last_modified)
3. Add imports at TOP of file (after any existing imports):

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
```

4. Add ConfigError class BEFORE existing functions:

```python
class ConfigError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""
    pass
```

**Verification:**
```bash
python -c "from ontos.core.config import ConfigError; print('OK')"
```

---

#### Task 3.1.2: Add config dataclasses

**File:** `ontos/core/config.py` (MODIFY)

**Instructions:**
Add these dataclasses AFTER ConfigError, BEFORE existing functions:

```python
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
    log_retention_count: int = 20  # Required by Roadmap

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
```

**Verification:**
```bash
python -c "from ontos.core.config import OntosConfig; c = OntosConfig(); print(c.workflow.log_retention_count)"
# Should print: 20
```

---

#### Task 3.1.3: Add config helper functions

**File:** `ontos/core/config.py` (MODIFY)

**Instructions:**
Add these functions AFTER the dataclasses:

```python
def default_config() -> OntosConfig:
    """Create default configuration."""
    return OntosConfig()

def config_to_dict(config: OntosConfig) -> dict:
    """Convert config dataclass to dict for TOML serialization."""
    from dataclasses import asdict
    return asdict(config)
```

**Verification:**
```bash
python -c "from ontos.core.config import default_config, config_to_dict; print(config_to_dict(default_config())['workflow'])"
```

---

#### Task 3.1.4: Add validation functions

**File:** `ontos/core/config.py` (MODIFY)

**Instructions:**
Add these validation functions:

```python
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
```

**Verification:**
```bash
python -c "
from ontos.core.config import _validate_types, ConfigError
try:
    _validate_types({'workflow': {'log_retention_count': 'not_int'}})
except ConfigError as e:
    print('Caught:', e)
"
```

---

#### Task 3.1.5: Add dict_to_config function

**File:** `ontos/core/config.py` (MODIFY)

**Instructions:**
Add this function:

```python
def dict_to_config(data: dict, repo_root: Optional[Path] = None) -> OntosConfig:
    """Convert dict from TOML to config dataclass."""
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

**Verification:**
```bash
python -c "
from ontos.core.config import dict_to_config
config = dict_to_config({'workflow': {'log_retention_count': 50}})
print(config.workflow.log_retention_count)  # Should be 50
print(config.paths.docs_dir)  # Should be 'docs' (default)
"
```

---

#### Task 3.1.6: Update core/__init__.py exports

**File:** `ontos/core/__init__.py` (MODIFY)

**Instructions:**
Add these imports (keep existing imports):

```python
from ontos.core.config import (
    ConfigError,
    OntosConfig,
    OntosSection,
    PathsConfig,
    ScanningConfig,
    ValidationConfig,
    WorkflowConfig,
    HooksConfig,
    default_config,
    config_to_dict,
    dict_to_config,
    # Keep existing exports:
    BLOCKED_BRANCH_NAMES,
    get_source,
    get_git_last_modified,
)
```

**Verification:**
```bash
python -c "from ontos.core import OntosConfig, ConfigError, default_config; print('OK')"
pytest tests/ -v  # Must still pass
```

**Checkpoint:** Commit with message `"feat(config): add config dataclasses and validation to core/config.py"`

---

### Day 2: IO Config Module

#### Task 3.2.1: Create io/config.py

**File:** `ontos/io/config.py` (CREATE — new file)

**Instructions:**
Create this new file with the following content:

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
    """Load config from file, or return defaults if not found."""
    if config_path is None:
        config_path = find_config()

    if config_path is None:
        return default_config()

    # Error handling for malformed TOML
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

**Verification:**
```bash
python -c "from ontos.io.config import find_config, load_project_config, save_project_config; print('OK')"
```

---

#### Task 3.2.2: Update io/__init__.py exports

**File:** `ontos/io/__init__.py` (MODIFY)

**Instructions:**
Add these imports (keep existing imports):

```python
from ontos.io.config import (
    CONFIG_FILENAME,
    find_config,
    load_project_config,
    save_project_config,
    config_exists,
)
```

Also add to `__all__` list:
```python
__all__ = [
    # ... existing entries ...
    # config
    "CONFIG_FILENAME",
    "find_config",
    "load_project_config",
    "save_project_config",
    "config_exists",
]
```

**Verification:**
```bash
python -c "from ontos.io import load_project_config, save_project_config; print('OK')"
pytest tests/ -v  # Must still pass
```

**Checkpoint:** Commit with message `"feat(config): add io/config.py for .ontos.toml I/O"`

---

### Day 3: Init Command

#### Task 3.3.1: Create commands/init.py

**File:** `ontos/commands/init.py` (CREATE — new file)

**Instructions:**
Create this new file. This is the largest file — see spec section 4.3 for full implementation.

```python
"""Ontos project initialization command."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from ontos.core.config import default_config, ConfigError
from ontos.io.config import save_project_config, config_exists

# Explicit marker for hook detection
ONTOS_HOOK_MARKER = "# ontos-managed-hook"


@dataclass
class InitOptions:
    """Configuration for init command."""
    path: Path = None
    force: bool = False
    interactive: bool = False  # Reserved for v3.1
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

    # 2. Check for git repository (handle worktrees)
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

    # 6. Generate initial context map
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
    """Check if path is a valid git repository (handles worktrees)."""
    git_path = project_root / ".git"

    if git_path.is_dir():
        return None  # Normal git repo

    if git_path.is_file():
        # Git worktree or submodule - .git is a file pointing to actual repo
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
    """Get the hooks directory for a git repository (handles worktrees)."""
    git_path = root / ".git"

    if git_path.is_file():
        # Worktree: .git is a file containing "gitdir: /path/to/..."
        content = git_path.read_text().strip()
        if content.startswith("gitdir:"):
            actual_git = Path(content[7:].strip())
            if "worktrees" in actual_git.parts:
                main_git = actual_git.parent.parent
                hooks_dir = main_git / "hooks"
            else:
                hooks_dir = actual_git / "hooks"
        else:
            hooks_dir = root / ".git" / "hooks"
    else:
        hooks_dir = root / ".git" / "hooks"

    # Create hooks directory if missing
    hooks_dir.mkdir(parents=True, exist_ok=True)

    return hooks_dir


def _install_hooks(root: Path, options: InitOptions) -> int:
    """Install git hooks with collision safety."""
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
                    _write_shim_hook(hook_path, hook)
                elif options.force:
                    _write_shim_hook(hook_path, hook)
                else:
                    skipped.append(hook)
                    print(f"Warning: Existing {hook} hook detected. Skipping. "
                          f"Use --force to overwrite, or manually integrate.")
            else:
                _write_shim_hook(hook_path, hook)
        except PermissionError as e:
            print(f"Warning: Cannot write {hook} hook (permission denied): {e}")
            skipped.append(hook)
        except Exception as e:
            print(f"Warning: Failed to install {hook} hook: {e}")
            skipped.append(hook)

    return 3 if skipped else 0


def _is_ontos_hook(path: Path) -> bool:
    """Check if hook file is an Ontos shim (uses explicit marker)."""
    try:
        content = path.read_text()
        return ONTOS_HOOK_MARKER in content
    except Exception:
        return False


def _write_shim_hook(path: Path, hook_type: str) -> None:
    """Write minimal shim hook with marker."""
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

    # chmod is no-op on Windows but we still call it
    try:
        path.chmod(0o755)
    except OSError:
        pass  # Windows: chmod may fail, but hooks will still work
```

**Verification:**
```bash
python -c "from ontos.commands.init import init_command, InitOptions, ONTOS_HOOK_MARKER; print('OK')"
```

---

#### Task 3.3.2: Update commands/__init__.py exports

**File:** `ontos/commands/__init__.py` (MODIFY)

**Instructions:**
Add these imports:

```python
from ontos.commands.init import (
    InitOptions,
    init_command,
    ONTOS_HOOK_MARKER,
)
```

**Verification:**
```bash
python -c "from ontos.commands import init_command, InitOptions; print('OK')"
pytest tests/ -v  # Must still pass
```

**Checkpoint:** Commit with message `"feat(init): add commands/init.py with hook installation"`

---

### Day 4: CLI Integration

#### Task 3.4.1: Update _scripts/ontos.py routing

**File:** `ontos/_scripts/ontos.py` (MODIFY)

**Instructions:**
Find the `COMMANDS` dict and the dispatch logic. Update the init command handling:

1. Find the existing init entry in COMMANDS dict (currently maps to 'ontos_init')
2. Update the dispatch logic to route 'init' to the new implementation:

```python
# In the main dispatch logic, BEFORE the generic module loading:
if command == 'init':
    from ontos.commands.init import init_command, InitOptions
    options = InitOptions(
        path=Path.cwd(),
        force='--force' in sys.argv or '-f' in sys.argv,
        interactive=False,  # Reserved for v3.1
        skip_hooks='--skip-hooks' in sys.argv,
    )
    code, msg = init_command(options)
    print(msg)
    sys.exit(code)
```

**Note:** Add `from pathlib import Path` at the top if not already imported.

**Verification:**
```bash
# In a temp directory:
cd /tmp
rm -rf test-ontos-init && mkdir test-ontos-init && cd test-ontos-init
git init
python -m ontos init
cat .ontos.toml  # Should show config
ls -la .git/hooks/  # Should show pre-commit, pre-push
```

---

#### Task 3.4.2: Test all init scenarios

**Manual tests to run:**

```bash
# Test 1: Already initialized (should exit 1)
cd /tmp/test-ontos-init
python -m ontos init
# Expected: "Already initialized. Use --force to reinitialize."

# Test 2: Force reinitialize (should exit 0)
python -m ontos init --force
# Expected: Success message

# Test 3: Not a git repo (should exit 2)
cd /tmp
rm -rf not-git && mkdir not-git && cd not-git
python -m ontos init
# Expected: "Not a git repository. Run 'git init' first."

# Test 4: Skip hooks
cd /tmp
rm -rf test-skip && mkdir test-skip && cd test-skip
git init
python -m ontos init --skip-hooks
ls .git/hooks/
# Expected: No pre-commit or pre-push files
```

**Checkpoint:** Commit with message `"feat(cli): route ontos init to new commands/init.py"`

---

### Day 5: Testing & Polish

#### Task 3.5.1: Create tests/core/test_config.py

**File:** `tests/core/test_config.py` (CREATE)

```python
"""Tests for ontos.core.config module."""
import pytest
from pathlib import Path

from ontos.core.config import (
    ConfigError,
    OntosConfig,
    WorkflowConfig,
    default_config,
    config_to_dict,
    dict_to_config,
    _validate_types,
    _validate_path,
)


def test_default_config():
    """Default config has expected values."""
    config = default_config()
    assert config.ontos.version == "3.0"
    assert config.paths.docs_dir == "docs"
    assert config.workflow.log_retention_count == 20


def test_config_to_dict_roundtrip():
    """config_to_dict and dict_to_config are inverse operations."""
    original = default_config()
    data = config_to_dict(original)
    restored = dict_to_config(data)
    assert restored.workflow.log_retention_count == original.workflow.log_retention_count


def test_validate_types_rejects_string_for_int():
    """Type validation rejects wrong types with ConfigError."""
    with pytest.raises(ConfigError, match="must be int"):
        _validate_types({"workflow": {"log_retention_count": "twenty"}})


def test_validate_types_accepts_correct_types():
    """Type validation passes for correct types."""
    _validate_types({"workflow": {"log_retention_count": 50}})  # No exception


def test_validate_path_rejects_traversal(tmp_path):
    """Path validation rejects paths outside repo root."""
    assert _validate_path("docs", tmp_path) is True
    assert _validate_path("../outside", tmp_path) is False


def test_dict_to_config_missing_sections():
    """Missing sections use defaults."""
    config = dict_to_config({})  # Empty dict
    assert config.paths.docs_dir == "docs"  # Default value
```

---

#### Task 3.5.2: Create tests/io/test_config.py

**File:** `tests/io/test_config.py` (CREATE)

```python
"""Tests for ontos.io.config module."""
import pytest
from pathlib import Path

from ontos.core.config import ConfigError
from ontos.io.config import (
    find_config,
    load_project_config,
    save_project_config,
    config_exists,
    CONFIG_FILENAME,
)


def test_find_config_returns_none_if_missing(tmp_path):
    """find_config returns None if no .ontos.toml exists."""
    assert find_config(tmp_path) is None


def test_find_config_finds_in_current_dir(tmp_path):
    """find_config finds .ontos.toml in current directory."""
    config_file = tmp_path / CONFIG_FILENAME
    config_file.write_text("[ontos]\nversion = '3.0'\n")
    assert find_config(tmp_path) == config_file


def test_load_project_config_returns_defaults_if_missing(tmp_path):
    """Missing config returns default values."""
    config = load_project_config(config_path=tmp_path / "nonexistent.toml")
    assert config.paths.docs_dir == "docs"


def test_save_and_load_roundtrip(tmp_path):
    """save_project_config and load_project_config roundtrip."""
    from ontos.core.config import default_config

    config_path = tmp_path / CONFIG_FILENAME
    original = default_config()
    save_project_config(original, config_path)

    loaded = load_project_config(config_path=config_path)
    assert loaded.workflow.log_retention_count == 20


def test_config_exists(tmp_path):
    """config_exists correctly detects presence."""
    config_path = tmp_path / CONFIG_FILENAME
    assert config_exists(config_path) is False
    config_path.write_text("[ontos]\n")
    assert config_exists(config_path) is True
```

---

#### Task 3.5.3: Create tests/commands/test_init.py

**File:** `tests/commands/test_init.py` (CREATE)

```python
"""Tests for ontos.commands.init module."""
import pytest
from pathlib import Path
import subprocess

from ontos.commands.init import (
    init_command,
    InitOptions,
    ONTOS_HOOK_MARKER,
    _is_ontos_hook,
    _check_git_repo,
)


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    return tmp_path


def test_init_empty_directory(git_repo):
    """Init in empty git repo creates .ontos.toml."""
    options = InitOptions(path=git_repo)
    code, msg = init_command(options)

    assert code == 0 or code == 3  # 0 = success, 3 = hooks skipped (OK)
    assert (git_repo / ".ontos.toml").exists()


def test_init_already_initialized(git_repo):
    """Init fails with exit code 1 if config exists."""
    (git_repo / ".ontos.toml").write_text("[ontos]\n")

    options = InitOptions(path=git_repo)
    code, msg = init_command(options)

    assert code == 1
    assert "Already initialized" in msg


def test_init_force_reinitialize(git_repo):
    """Init --force overwrites existing config."""
    (git_repo / ".ontos.toml").write_text("[ontos]\nversion = 'old'\n")

    options = InitOptions(path=git_repo, force=True)
    code, msg = init_command(options)

    assert code == 0 or code == 3


def test_init_not_git_repo(tmp_path):
    """Init fails with exit code 2 if not git repo."""
    options = InitOptions(path=tmp_path)
    code, msg = init_command(options)

    assert code == 2
    assert "Not a git repository" in msg


def test_hook_marker_detection(tmp_path):
    """Hooks with ONTOS_HOOK_MARKER are recognized as ours."""
    hook_file = tmp_path / "pre-commit"
    hook_file.write_text(f"#!/bin/sh\n{ONTOS_HOOK_MARKER}\necho test\n")

    assert _is_ontos_hook(hook_file) is True


def test_hook_without_marker_not_detected(tmp_path):
    """Hooks without marker are not recognized as ours."""
    hook_file = tmp_path / "pre-commit"
    hook_file.write_text("#!/bin/sh\necho other hook\n")

    assert _is_ontos_hook(hook_file) is False
```

---

#### Task 3.5.4: Run full test suite

**Commands:**
```bash
# Run new tests
pytest tests/core/test_config.py -v
pytest tests/io/test_config.py -v
pytest tests/commands/test_init.py -v

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=ontos --cov-report=term-missing
```

**Checkpoint:** Commit with message `"test: add tests for Phase 3 config and init"`

---

## Verification Checkpoints

### After Day 1 (Core Config)
```bash
python -c "from ontos.core import OntosConfig, ConfigError, default_config, dict_to_config; print('OK')"
pytest tests/ -v
```

### After Day 2 (IO Config)
```bash
python -c "from ontos.io import load_project_config, save_project_config; print('OK')"
pytest tests/ -v
```

### After Day 3 (Init Command)
```bash
python -c "from ontos.commands import init_command, InitOptions; print('OK')"
python -c "import ontos; print('No circular imports')"
pytest tests/ -v
```

### After Day 4 (CLI Integration)
```bash
# Manual test in temp directory
cd /tmp && rm -rf test-init && mkdir test-init && cd test-init
git init
python -m ontos init
cat .ontos.toml
ls .git/hooks/
```

### After Day 5 (Tests)
```bash
pytest tests/ -v --cov=ontos
```

---

## Common Mistakes (Avoid These)

1. **Importing io in core** — Check imports in `core/config.py`. Only stdlib allowed.

2. **Reimplementing TOML loading** — Use existing `io/toml.py` functions.

3. **Forgetting __init__.py exports** — New symbols must be exported.

4. **Hardcoding config values** — Use dataclass defaults.

5. **Not handling missing config** — `load_project_config()` must return defaults.

6. **Breaking existing tests** — Run pytest after every task.

7. **Windows path issues** — Use `Path` objects, not string concatenation.

8. **Forgetting chmod try/except** — Windows will fail without it.

9. **Missing ONTOS_HOOK_MARKER** — Old hooks won't be detected as ours.

10. **Not generating context map** — Roadmap requires it in init flow.

---

## PR Preparation

When all tasks complete:

1. **Run full test suite:**
```bash
pytest tests/ -v --cov=ontos
```

2. **Test init command manually:**
```bash
cd /tmp
rm -rf final-test && mkdir final-test && cd final-test
git init
python -m ontos init
cat .ontos.toml
cat Ontos_Context_Map.md  # Should exist
ls -la .git/hooks/
```

3. **Verify no circular imports:**
```bash
python -c "import ontos; print('OK')"
```

4. **Create PR:**
```bash
git add -A
git commit -m "feat: Phase 3 - Configuration & Init

- Add config dataclasses to core/config.py
- Add io/config.py for .ontos.toml I/O
- Add commands/init.py with hook installation
- Route CLI init to new implementation
- Add comprehensive tests

Implements: Phase3-Implementation-Spec.md v1.1"

git push -u origin phase3-config-init
```

5. **PR Title:** `feat: Phase 3 - Configuration & Init`

6. **PR Description template:**
```markdown
## Summary
- Implements `.ontos.toml` configuration system
- New `ontos init` command with hook installation
- Config dataclasses with type and path validation

## Changes
- `ontos/core/config.py` - Config dataclasses, validation
- `ontos/io/config.py` - Config file I/O (NEW)
- `ontos/commands/init.py` - Init command (NEW)
- `ontos/_scripts/ontos.py` - CLI routing update

## Test plan
- [x] pytest tests/ passes
- [x] Manual init test in fresh git repo
- [x] No circular imports
- [x] Hook collision safety verified

## Spec Reference
`.ontos-internal/strategy/v3.0/Phase3/Phase3-Implementation-Spec.md` v1.1
```

---

## File Reference

| File | Action | Task |
|------|--------|------|
| `ontos/core/config.py` | MODIFY | 3.1.1-3.1.5 |
| `ontos/core/__init__.py` | MODIFY | 3.1.6 |
| `ontos/io/config.py` | CREATE | 3.2.1 |
| `ontos/io/__init__.py` | MODIFY | 3.2.2 |
| `ontos/commands/init.py` | CREATE | 3.3.1 |
| `ontos/commands/__init__.py` | MODIFY | 3.3.2 |
| `ontos/_scripts/ontos.py` | MODIFY | 3.4.1 |
| `tests/core/test_config.py` | CREATE | 3.5.1 |
| `tests/io/test_config.py` | CREATE | 3.5.2 |
| `tests/commands/test_init.py` | CREATE | 3.5.3 |

---

*End of Implementation Prompt*
