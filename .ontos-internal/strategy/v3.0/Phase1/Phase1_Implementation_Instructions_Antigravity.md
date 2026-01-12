# Ontos v3.0 Phase 1: Implementation Instructions for Antigravity

**Date:** 2026-01-12
**Spec Version:** 1.2 (Approved)
**Target:** Transform Ontos into a pip-installable Python package
**Constraint:** Zero behavior changes — Golden Master tests must pass

---

## Executive Summary

You are implementing Phase 1 of the Ontos v3.0 restructuring. Your job is to:

1. Create a proper Python package structure at project root (`ontos/`)
2. Bundle all legacy scripts inside the package (`ontos/_scripts/`)
3. Update imports across the codebase
4. Ensure both `pip install -e .` and `pip install .` work
5. Verify Golden Master tests pass (no behavior changes)

**Critical Rule:** Do NOT modify any business logic. Only move files and update imports.

---

## Pre-Implementation Checklist

Before starting, verify:

```bash
# 1. You're in the correct directory
pwd  # Should show: /Users/jonathanoh/Dev/Project-Ontos

# 2. Git is clean (or stash changes)
git status

# 3. Golden Master baseline exists
ls tests/golden/baselines/

# 4. Current tests pass
python -m pytest tests/ -v --tb=short
```

---

## Phase 1A: Create Package Structure

### Step 1.1: Create `pyproject.toml`

**File:** `/Users/jonathanoh/Dev/Project-Ontos/pyproject.toml`

**Action:** Create new file with this exact content:

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "ontos"
version = "3.0.0a1"
description = "Local-first documentation management for AI-assisted development"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Ontos Project", email = "ontos@example.com"}
]
keywords = ["documentation", "ai", "context", "llm", "developer-tools"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Documentation",
    "Topic :: Software Development :: Documentation",
]
dependencies = [
    "pyyaml>=6.0",
    "tomli>=2.0.1; python_version<'3.11'",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pre-commit>=3.0",
]
mcp = [
    "pydantic>=2.0",
]

[project.scripts]
ontos = "ontos.cli:main"

[project.urls]
Homepage = "https://github.com/ohjona/Project-Ontos"
Documentation = "https://github.com/ohjona/Project-Ontos/tree/main/docs"
Repository = "https://github.com/ohjona/Project-Ontos"
Issues = "https://github.com/ohjona/Project-Ontos/issues"

[tool.setuptools.packages.find]
where = ["."]
include = ["ontos", "ontos.*"]

[tool.setuptools.package-data]
"ontos._scripts" = ["*.py"]

[tool.pytest.ini_options]
testpaths = ["tests", ".ontos/scripts/tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["ontos"]
omit = ["tests/*", ".ontos/scripts/tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

**Verify:**
```bash
python -c "import tomli; tomli.load(open('pyproject.toml', 'rb')); print('Valid TOML')"
```

---

### Step 1.2: Create Package Directory Structure

**Action:** Create directory structure:

```bash
mkdir -p ontos/core
mkdir -p ontos/ui
mkdir -p ontos/commands
mkdir -p ontos/io
mkdir -p ontos/mcp
mkdir -p ontos/_scripts
```

---

### Step 1.3: Create `ontos/__init__.py`

**File:** `/Users/jonathanoh/Dev/Project-Ontos/ontos/__init__.py`

**CRITICAL:** This must preserve EXACT v2.8 API exports. Copy from `.ontos/scripts/ontos/__init__.py` and only change version.

**Action:** Create new file with this exact content:

```python
"""Ontos - Context Management System.

v2.8: Unified package structure for clean architecture.

Package structure:
    ontos.core - Pure logic (no I/O except marked impure functions)
    ontos.ui   - I/O layer (CLI, output, prompts)
"""

__version__ = "3.0.0a1"

# Re-export commonly used items for convenience
from ontos.core.context import SessionContext, FileOperation, PendingWrite
from ontos.core.frontmatter import parse_frontmatter, normalize_depends_on, normalize_type
from ontos.core.staleness import (
    ModifiedSource,
    normalize_describes,
    parse_describes_verified,
    validate_describes_field,
    detect_describes_cycles,
    check_staleness,
    get_file_modification_date,
    clear_git_cache,
    DescribesValidationError,
    DescribesWarning,
    StalenessInfo,
)
from ontos.core.history import (
    ParsedLog,
    parse_log_for_history,
    sort_logs_deterministically,
    generate_decision_history,
    get_log_date,
)
from ontos.core.paths import (
    resolve_config,
    get_logs_dir,
    get_log_count,
    get_logs_older_than,
    get_archive_dir,
    get_decision_history_path,
    get_proposals_dir,
    get_archive_logs_dir,
    get_archive_proposals_dir,
    get_concepts_path,
    find_last_session_date,
)
from ontos.core.config import (
    BLOCKED_BRANCH_NAMES,
    get_source,
    get_git_last_modified,
)
from ontos.core.proposals import (
    load_decision_history_entries,
    find_draft_proposals,
)
from ontos.ui.output import OutputHandler
```

---

### Step 1.4: Create `ontos/__main__.py`

**File:** `/Users/jonathanoh/Dev/Project-Ontos/ontos/__main__.py`

**Action:** Create new file:

```python
"""
Entry point for `python -m ontos` invocation.

This module enables running Ontos as a Python module:
    python -m ontos map
    python -m ontos log -e feature -s "Session summary"
"""

from ontos.cli import main

if __name__ == "__main__":
    main()
```

---

### Step 1.5: Create `ontos/cli.py`

**File:** `/Users/jonathanoh/Dev/Project-Ontos/ontos/cli.py`

**Action:** Create new file:

```python
"""
CLI entry point for Phase 1.

This module provides the main entry point for the `ontos` command.
It delegates to bundled legacy scripts to maintain exact v2.9.x behavior.

v1.1 Changes:
- Uses bundled scripts from ontos/_scripts/ (works for PyPI installs)
- Adds project root discovery (works from subdirectories)
- Passes through stdin/stdout/stderr (preserves TTY)

v1.2 Changes:
- Exempts `ontos init` from project root discovery (allows initialization in fresh directories)
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional


def find_project_root() -> Optional[Path]:
    """
    Find the Ontos project root by walking up the directory tree.

    Looks for directories containing `.ontos/` or `.ontos-internal/`.
    Returns None if no project root is found.
    """
    current = Path.cwd().resolve()

    while current != current.parent:
        if (current / ".ontos-internal").exists() or (current / ".ontos").exists():
            return current
        current = current.parent

    # Check root as well
    if (current / ".ontos-internal").exists() or (current / ".ontos").exists():
        return current

    return None


def get_bundled_script(script_name: str) -> Path:
    """
    Get path to a bundled script in ontos/_scripts/.
    """
    return Path(__file__).parent / "_scripts" / script_name


def main():
    """
    Main CLI entry point.

    Delegates to bundled legacy scripts to maintain exact v2.9.x behavior.
    Phase 4 will implement full CLI directly in this module.
    """
    import ontos

    # Handle --version flag
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-V"):
        print(f"ontos {ontos.__version__}")
        sys.exit(0)

    # Handle --help with no subcommand
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h")):
        print(f"ontos {ontos.__version__}")
        print()
        print("Usage: ontos <command> [options]")
        print()
        print("Commands:")
        print("  map         Generate context map")
        print("  log         Create session log")
        print("  init        Initialize project")
        print("  verify      Verify documentation")
        print("  query       Query documents")
        print("  promote     Promote document curation level")
        print()
        print("Use 'ontos <command> --help' for command-specific help.")
        sys.exit(0)

    # Handle init specially - it doesn't need project root (v1.2 fix)
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        project_root = Path.cwd()  # Use current directory for init
    else:
        # Find project root (v1.1: support running from subdirectories)
        project_root = find_project_root()
        if project_root is None:
            print("Error: Not in an Ontos-enabled project.", file=sys.stderr)
            print("Run 'ontos init' to initialize a project, or navigate to a project directory.", file=sys.stderr)
            sys.exit(1)

    # Use bundled unified dispatcher (v1.1: works for PyPI installs)
    unified_cli = get_bundled_script("ontos.py")

    if not unified_cli.exists():
        # This should never happen if package is installed correctly
        print(f"Error: Bundled scripts not found at {unified_cli}", file=sys.stderr)
        print("This indicates a broken installation. Try reinstalling: pip install --force-reinstall ontos", file=sys.stderr)
        sys.exit(1)

    # Execute the unified dispatcher with the same arguments
    # v1.1: Pass through streams to preserve TTY and signals
    result = subprocess.run(
        [sys.executable, str(unified_cli)] + sys.argv[1:],
        cwd=project_root,  # Run from project root
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
```

---

### Step 1.6: Copy Core Modules

**Action:** Copy entire core directory:

```bash
cp -r .ontos/scripts/ontos/core/* ontos/core/
```

**Files copied (11 files):**
- `__init__.py`
- `config.py`
- `context.py`
- `curation.py`
- `frontmatter.py`
- `history.py`
- `ontology.py`
- `paths.py`
- `proposals.py`
- `schema.py`
- `staleness.py`

**Verify:**
```bash
ls ontos/core/  # Should show 11 files
```

---

### Step 1.7: Copy UI Modules

**Action:** Copy entire ui directory:

```bash
cp -r .ontos/scripts/ontos/ui/* ontos/ui/
```

**Files copied (2 files):**
- `__init__.py`
- `output.py`

**Verify:**
```bash
ls ontos/ui/  # Should show 2 files
```

---

### Step 1.8: Create Placeholder Directories

**Action:** Create empty `__init__.py` files for architecture stubs:

**File:** `ontos/commands/__init__.py`
```python
"""Commands module - Placeholder for Phase 2."""
```

**File:** `ontos/io/__init__.py`
```python
"""IO module - Placeholder for Phase 2."""
```

**File:** `ontos/mcp/__init__.py`
```python
"""MCP module - Placeholder for Phase 2."""
```

---

### Step 1.9: Bundle Legacy Scripts (CRITICAL)

**Action:** Create `ontos/_scripts/__init__.py`:

```python
"""Bundled legacy scripts for CLI delegation."""
```

**Action:** Copy ALL 23 scripts plus root entry points:

```bash
# Copy root entry points
cp ontos.py ontos/_scripts/ontos.py
cp ontos_init.py ontos/_scripts/ontos_init.py
cp ontos_config.py ontos/_scripts/ontos_config.py

# Copy all .ontos/scripts/ontos_*.py files (23 files)
cp .ontos/scripts/ontos_config.py ontos/_scripts/
cp .ontos/scripts/ontos_config_defaults.py ontos/_scripts/
cp .ontos/scripts/ontos_consolidate.py ontos/_scripts/
cp .ontos/scripts/ontos_create_bundle.py ontos/_scripts/
cp .ontos/scripts/ontos_end_session.py ontos/_scripts/
cp .ontos/scripts/ontos_generate_context_map.py ontos/_scripts/
cp .ontos/scripts/ontos_generate_ontology_spec.py ontos/_scripts/
cp .ontos/scripts/ontos_install_hooks.py ontos/_scripts/
cp .ontos/scripts/ontos_lib.py ontos/_scripts/
cp .ontos/scripts/ontos_maintain.py ontos/_scripts/
cp .ontos/scripts/ontos_migrate_frontmatter.py ontos/_scripts/
cp .ontos/scripts/ontos_migrate_schema.py ontos/_scripts/
cp .ontos/scripts/ontos_migrate_v2.py ontos/_scripts/
cp .ontos/scripts/ontos_pre_commit_check.py ontos/_scripts/
cp .ontos/scripts/ontos_pre_push_check.py ontos/_scripts/
cp .ontos/scripts/ontos_promote.py ontos/_scripts/
cp .ontos/scripts/ontos_query.py ontos/_scripts/
cp .ontos/scripts/ontos_remove_frontmatter.py ontos/_scripts/
cp .ontos/scripts/ontos_scaffold.py ontos/_scripts/
cp .ontos/scripts/ontos_stub.py ontos/_scripts/
cp .ontos/scripts/ontos_summarize.py ontos/_scripts/
cp .ontos/scripts/ontos_update.py ontos/_scripts/
cp .ontos/scripts/ontos_verify.py ontos/_scripts/
```

**Verify:**
```bash
ls ontos/_scripts/ | wc -l  # Should show 27 files (23 scripts + 3 root + 1 __init__)
```

---

### Step 1.10: Verify Package Structure

**Action:** Run this verification:

```bash
find ontos -name "*.py" | sort
```

**Expected output (minimum):**
```
ontos/__init__.py
ontos/__main__.py
ontos/_scripts/__init__.py
ontos/_scripts/ontos.py
ontos/_scripts/ontos_config.py
ontos/_scripts/ontos_config_defaults.py
ontos/_scripts/ontos_consolidate.py
... (23 more scripts)
ontos/cli.py
ontos/commands/__init__.py
ontos/core/__init__.py
ontos/core/config.py
ontos/core/context.py
ontos/core/curation.py
ontos/core/frontmatter.py
ontos/core/history.py
ontos/core/ontology.py
ontos/core/paths.py
ontos/core/proposals.py
ontos/core/schema.py
ontos/core/staleness.py
ontos/io/__init__.py
ontos/mcp/__init__.py
ontos/ui/__init__.py
ontos/ui/output.py
```

**Checkpoint 1A Complete:** Package structure created.

---

## Phase 1B: Update Imports

### Step 2.1: Update Bundled Scripts Imports

**CRITICAL:** Every script in `ontos/_scripts/` needs its imports updated.

**Pattern to find:**
```python
# OLD (remove these lines):
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '...', '.ontos', 'scripts'))
# or
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

**Pattern to remove:** Delete any `sys.path.insert` lines that reference `.ontos/scripts`.

**Files to update in `ontos/_scripts/`:**

For each file, search for and REMOVE lines like:
```python
sys.path.insert(0, ...)
```

The imports like `from ontos.core.context import SessionContext` should remain unchanged — they will work because the package is now installed.

**Key files to check:**
1. `ontos/_scripts/ontos.py` - Main dispatcher
2. `ontos/_scripts/ontos_init.py` - Has path manipulation
3. `ontos/_scripts/ontos_config.py` - Has path manipulation
4. `ontos/_scripts/ontos_end_session.py` - Check imports
5. `ontos/_scripts/ontos_generate_context_map.py` - Check imports

**Strategy:**
```bash
# Find all files with sys.path manipulation
grep -l "sys.path.insert" ontos/_scripts/*.py
```

Then edit each file to remove the sys.path.insert lines.

---

### Step 2.2: Update Root Scripts (Backward Compatibility)

The root-level scripts (`ontos.py`, `ontos_init.py`, `ontos_config.py`) should still work. Update their imports to use the package:

**For each root script, change:**
```python
# BEFORE:
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.ontos', 'scripts'))

# AFTER:
# (delete the line entirely - package is installed)
```

---

### Step 2.3: Update Test Imports

**File:** `tests/conftest.py`

**Remove** any sys.path manipulation:
```python
# DELETE these lines if present:
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.ontos', 'scripts'))
```

**File:** `.ontos/scripts/tests/conftest.py`

Same treatment — remove sys.path manipulation.

**For all test files:** Search and remove sys.path.insert patterns.

```bash
# Find test files with path manipulation
grep -l "sys.path.insert" tests/*.py .ontos/scripts/tests/*.py
```

---

### Step 2.4: Update Deprecated Shim

**File:** `.ontos/scripts/ontos_lib.py`

This file should emit a deprecation warning. Ensure it imports from the new package:

```python
"""
DEPRECATED: This module is a compatibility shim.

As of v2.9.2, this module emits FutureWarning on import.
Will be removed in v3.0.

Migration:
    # Instead of:
    from ontos_lib import SessionContext

    # Use:
    from ontos.core.context import SessionContext
"""

import warnings

warnings.warn(
    "ontos_lib is deprecated and will be removed in v3.0. "
    "Import directly from 'ontos.core' instead.",
    FutureWarning,
    stacklevel=2
)

# Re-export from new locations for backward compatibility
from ontos.core.context import SessionContext, FileOperation, PendingWrite
from ontos.core.frontmatter import parse_frontmatter
from ontos.ui.output import OutputHandler
```

**Checkpoint 2 Complete:** Imports updated.

---

## Phase 1C: Install and Verify

### Step 3.1: Editable Install

```bash
pip install -e ".[dev]"
```

**Expected:** No errors. Package installed in development mode.

---

### Step 3.2: Verify CLI

```bash
# Version check
ontos --version
# Expected: ontos 3.0.0a1

# Help check
ontos --help
# Expected: Shows command list

# Module invocation
python -m ontos --version
# Expected: ontos 3.0.0a1
```

---

### Step 3.3: Verify Imports

```bash
python -c "import ontos; print(f'Version: {ontos.__version__}')"
# Expected: Version: 3.0.0a1

python -c "from ontos.core.context import SessionContext; print(SessionContext)"
# Expected: <class 'ontos.core.context.SessionContext'>

python -c "from ontos.ui.output import OutputHandler; print(OutputHandler)"
# Expected: <class 'ontos.ui.output.OutputHandler'>
```

---

### Step 3.4: Run Unit Tests

```bash
# Main tests
pytest tests/ -v --tb=short

# Script tests
pytest .ontos/scripts/tests/ -v --tb=short
```

**Expected:** All tests pass. If tests fail due to import errors, go back to Step 2 and fix imports.

---

### Step 3.5: Run Golden Master Tests (CRITICAL)

```bash
python tests/golden/compare_golden_master.py --fixture all
```

**Expected:** All 8 checks pass for both fixtures. This confirms NO behavior changes.

If Golden Master fails:
1. Check what changed in the output
2. You likely modified logic instead of just imports
3. Revert and try again

---

### Step 3.6: Test Non-Editable Install

```bash
# Create clean venv
python -m venv /tmp/ontos-test-venv
source /tmp/ontos-test-venv/bin/activate

# Non-editable install
pip install .

# Verify
ontos --version
python -c "import ontos; print(ontos.__version__)"

# Cleanup
deactivate
rm -rf /tmp/ontos-test-venv
```

**Expected:** Works identically to editable install.

---

### Step 3.7: Test CLI from Subdirectory

```bash
cd .ontos-internal
ontos map
cd ..
```

**Expected:** CLI finds project root and works correctly.

**Checkpoint 3 Complete:** Installation verified.

---

## Phase 1D: Update CI

### Step 4.1: Update `.github/workflows/ci.yml`

**File:** `/Users/jonathanoh/Dev/Project-Ontos/.github/workflows/ci.yml`

**Action:** Replace content with:

```yaml
name: Tests

on:
  push:
    branches: [main, v3.0, "v3.0.*"]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install package
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Verify installation
        run: |
          ontos --version
          python -m ontos --version

      - name: Run tests
        run: |
          pytest tests/ -v --tb=short
          pytest .ontos/scripts/tests/ -v --tb=short

      - name: Run Golden Master tests
        run: |
          python tests/golden/compare_golden_master.py --fixture all

      - name: Check coverage
        run: |
          pytest tests/ --cov=ontos --cov-report=xml
        continue-on-error: true

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.11'
        with:
          files: coverage.xml
        continue-on-error: true
```

**Checkpoint 4 Complete:** CI updated.

---

## Final Verification Checklist

Run through this checklist before considering Phase 1 complete:

| # | Check | Command | Expected |
|---|-------|---------|----------|
| 1 | pyproject.toml valid | `python -c "import tomli; tomli.load(open('pyproject.toml', 'rb'))"` | No error |
| 2 | Package structure | `find ontos -name "*.py" \| wc -l` | ~40+ files |
| 3 | Editable install | `pip install -e .` | Exit 0 |
| 4 | Non-editable install | `pip install .` (in clean venv) | Exit 0 |
| 5 | Version | `ontos --version` | `ontos 3.0.0a1` |
| 6 | Module invocation | `python -m ontos --version` | `ontos 3.0.0a1` |
| 7 | Import works | `python -c "import ontos"` | No error |
| 8 | Unit tests | `pytest tests/` | All pass |
| 9 | Script tests | `pytest .ontos/scripts/tests/` | All pass |
| 10 | Golden Master | `compare_golden_master.py --fixture all` | 8/8 PASS x 2 |
| 11 | Map command | `ontos map` | Generates map |
| 12 | Subdirectory | `cd .ontos-internal && ontos map` | Works |

---

## Troubleshooting

### Import Errors After Install

**Symptom:** `ModuleNotFoundError: No module named 'ontos'`

**Fix:**
1. Ensure `pip install -e .` completed successfully
2. Check you're in the right Python environment
3. Verify `ontos` appears in `pip list`

### Golden Master Fails

**Symptom:** Output doesn't match baseline

**Fix:**
1. Check what specific output changed
2. You likely modified logic — imports should be the ONLY changes
3. Diff your changes against the original files
4. Revert logic changes, keep only import changes

### CLI Not Found

**Symptom:** `command not found: ontos`

**Fix:**
1. Check `pip show ontos` to see install location
2. Ensure `~/.local/bin` or equivalent is in PATH
3. Try `python -m ontos` as alternative

### Tests Can't Import

**Symptom:** Tests fail with import errors

**Fix:**
1. Remove sys.path.insert from test files and conftest.py
2. Run `pip install -e .` to ensure package is available
3. Verify pytest uses the installed package: `python -c "import ontos; print(ontos.__file__)"`

---

## Files Summary

### Files to CREATE (new):
- `pyproject.toml`
- `ontos/__init__.py`
- `ontos/__main__.py`
- `ontos/cli.py`
- `ontos/commands/__init__.py`
- `ontos/io/__init__.py`
- `ontos/mcp/__init__.py`
- `ontos/_scripts/__init__.py`

### Files to COPY:
- `.ontos/scripts/ontos/core/*` → `ontos/core/`
- `.ontos/scripts/ontos/ui/*` → `ontos/ui/`
- `ontos.py` → `ontos/_scripts/ontos.py`
- `ontos_init.py` → `ontos/_scripts/ontos_init.py`
- `ontos_config.py` → `ontos/_scripts/ontos_config.py`
- `.ontos/scripts/ontos_*.py` (23 files) → `ontos/_scripts/`

### Files to MODIFY (import updates only):
- All files in `ontos/_scripts/` (remove sys.path.insert)
- `ontos.py` (root, if it has path manipulation)
- `ontos_init.py` (root, if it has path manipulation)
- `tests/conftest.py`
- `.ontos/scripts/tests/conftest.py`
- `.ontos/scripts/ontos_lib.py` (add deprecation warning)
- `.github/workflows/ci.yml`

### Files to NOT MODIFY:
- Any `.ontos-internal/` documentation
- Golden Master fixtures and baselines
- Core module logic (only imports change)
- `.gitignore`, `LICENSE`, `README.md`

---

## Success Criteria

Phase 1 is complete when:

1. `pip install -e .` works
2. `pip install .` works (non-editable)
3. `ontos --version` prints `ontos 3.0.0a1`
4. `python -m ontos --version` works
5. All 303+ tests pass
6. Golden Master tests pass (8/8 x 2 fixtures)
7. No behavior changes from v2.9.x
8. CI passes on all Python versions (3.9-3.12)

---

*End of Implementation Instructions*

**Reference Documents:**
- Spec: `.ontos-internal/strategy/v3.0/Phase1/phase1_implementation_spec.md` (v1.2)
- Review Consolidation: `.ontos-internal/strategy/v3.0/Phase1/phase1_review_consolidation_round2.md`
- Chief Architect Response: `.ontos-internal/strategy/v3.0/Phase1/Chief_Architect_Phase1_Response.md`
