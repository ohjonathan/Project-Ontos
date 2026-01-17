---
id: phase1_package_structure_spec
type: strategy
status: draft
depends_on: [v3_0_implementation_roadmap]
---

# Phase 1 Implementation Spec: Package Structure

**Version:** 1.2
**Date:** 2026-01-12
**Author:** Claude Opus 4.5 (Chief Architect)
**Status:** Approved for Implementation

**References:**
- `V3.0-Implementation-Roadmap.md` v1.3, Section 3
- `V3.0-Technical-Architecture.md` v1.4
- `Phase0/phase0_implementation_spec.md` v1.1 (template reference)

**Revision History:**
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-12 | Initial spec |
| 1.1 | 2026-01-12 | Incorporated review feedback (3 reviewers). See `Chief_Architect_Phase1_Response.md`. Key changes: Bundle scripts in package, preserve exact v2.8 API, add project root discovery. |
| 1.2 | 2026-01-12 | Round 2 verification fix: Exempt `ontos init` from project root discovery. See `phase1_review_consolidation_round2.md`. |

---

## 1. Overview

### 1.1 Purpose

Transform Ontos from a repository-injected script collection into a proper pip-installable Python package. After Phase 1, users will be able to run:

```bash
pip install -e .           # Developer mode
pip install ontos          # User mode (future PyPI)
ontos map                  # CLI available in PATH
python -m ontos map        # Module invocation
```

This is a **structural transformation only** — no behavior changes. Golden Master tests must pass before and after.

**v1.1 Note:** The package now bundles legacy scripts inside `ontos/_scripts/` to ensure the CLI works for both editable and non-editable installations.

### 1.2 Scope

| In Scope | Out of Scope |
|----------|--------------|
| Create `pyproject.toml` with build metadata | CLI command additions |
| Move `ontos/` package to project root | God Script decomposition (Phase 2) |
| **Bundle legacy scripts in package** (v1.1) | Configuration system changes (Phase 3) |
| Configure entry points for CLI commands | New features or behaviors |
| Update import paths across codebase | Windows-specific fixes |
| Migrate test infrastructure | Performance optimizations |
| Ensure Golden Master tests pass | |

### 1.3 Exit Criteria

From Roadmap Section 3.4:
- [ ] `pip install -e .` completes without error
- [ ] `pip install .` completes without error (v1.1 addition)
- [ ] `python -m ontos` prints version
- [ ] `ontos` command available in PATH after install
- [ ] All existing tests pass (with import fixes)
- [ ] Golden Master tests pass
- [ ] No behavior changes from v2.9.x
- [ ] Public API unchanged (v1.1 addition)

### 1.4 Prerequisites

- **Phase 0 Complete**: Golden Master testing infrastructure merged (PR #39)
- **Current baseline captured**: `tests/golden/baselines/` contains v2.9.x behavior

---

## 2. Current State Analysis

### 2.1 Existing Package Structure

The `ontos` package **already exists** at `.ontos/scripts/ontos/`:

```
.ontos/scripts/ontos/
├── __init__.py              # Version, re-exports
├── core/
│   ├── __init__.py          # Public API exports
│   ├── config.py            # Git operations, configuration
│   ├── context.py           # SessionContext, FileOperation, PendingWrite
│   ├── curation.py          # Curation logic
│   ├── frontmatter.py       # YAML parsing, validation
│   ├── history.py           # Decision history generation
│   ├── ontology.py          # Type definitions, hierarchy
│   ├── paths.py             # Path resolution
│   ├── proposals.py         # Draft proposal handling
│   ├── schema.py            # Schema validation
│   └── staleness.py         # Describes validation, modification tracking
└── ui/
    ├── __init__.py          # UI exports
    └── output.py            # OutputHandler (formatted output)
```

### 2.2 Current Entry Points

Root-level scripts act as entry points:

| Script | Purpose | Lines |
|--------|---------|-------|
| `ontos.py` | Unified CLI dispatcher | ~100 |
| `ontos_init.py` | Project initialization | ~600 |
| `.ontos/scripts/ontos_*.py` | Individual commands | 23 files |

### 2.3 Current Import Patterns

```python
# Root scripts use path manipulation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ontos.core.context import SessionContext

# Tests use similar path injection
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.ontos', 'scripts'))
```

### 2.4 Current Dependencies

```
# requirements.txt
pyyaml>=6.0
watchdog>=3.0
pytest>=7.0
pytest-cov>=4.0
pre-commit>=3.0
```

---

## 3. Target Package Structure

### 3.1 Directory Layout (v1.1 Updated)

```
Project-Ontos/
├── pyproject.toml           # NEW: Package configuration
├── ontos/                   # COPIED from .ontos/scripts/ontos/
│   ├── __init__.py          # Version, public API (EXACT v2.8 exports)
│   ├── __main__.py          # NEW: `python -m ontos` support
│   ├── cli.py               # NEW: CLI entry point with project root discovery
│   ├── core/                # COPIED: Pure logic modules
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── context.py
│   │   ├── curation.py
│   │   ├── frontmatter.py
│   │   ├── history.py
│   │   ├── ontology.py
│   │   ├── paths.py
│   │   ├── proposals.py
│   │   ├── schema.py
│   │   └── staleness.py
│   ├── ui/                  # COPIED: Output handling
│   │   ├── __init__.py
│   │   └── output.py
│   ├── commands/            # NEW: Placeholder for Phase 2
│   │   └── __init__.py
│   ├── io/                  # NEW: Placeholder for Phase 2
│   │   └── __init__.py
│   ├── mcp/                 # NEW: Placeholder for Phase 2
│   │   └── __init__.py
│   └── _scripts/            # NEW (v1.1): Bundled legacy scripts
│       ├── __init__.py      # Makes it importable
│       ├── ontos.py         # COPY of root ontos.py
│       ├── ontos_init.py    # COPY of root ontos_init.py
│       ├── ontos_config.py
│       ├── ontos_generate_context_map.py
│       ├── ontos_end_session.py
│       └── ... (all 23 scripts)
├── .ontos/                  # RETAINED: For backward compatibility
│   └── scripts/
│       ├── ontos/           # OLD location with deprecation warning
│       │   └── __init__.py  # Emits FutureWarning on import
│       ├── ontos_*.py       # RETAINED: Still work (import from ontos package)
│       ├── ontos_lib.py     # DEPRECATED: Compatibility shim
│       └── tests/           # RETAINED: Script-specific tests
├── tests/                   # UPDATED: Import paths fixed
│   ├── golden/              # RETAINED: Golden Master infrastructure
│   └── *.py                 # UPDATED: Import paths fixed
├── ontos.py                 # RETAINED: Still works (backward compat)
├── ontos_init.py            # RETAINED: Still works (backward compat)
└── requirements.txt         # RETAINED: Dev dependencies
```

### 3.2 Key Decisions (v1.1 Updated)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Package location | Root `ontos/` | Standard Python layout, simpler imports |
| Layout style | Flat (not src/) | Simpler for existing codebase; src-layout can come later |
| **Script bundling** | `ontos/_scripts/` | Ensures CLI works for PyPI installs (v1.1 fix) |
| Script retention | Keep `.ontos/scripts/` | Backward compatibility for v2.x users |
| Entry point | `ontos.cli:main` | Clean separation from package internals |
| **Copy vs Move** | COPY files | Keep old locations working during transition (v1.1 clarification) |
| **Architecture stubs** | Empty `commands/`, `io/`, `mcp/` | Match architecture docs, ready for Phase 2 |

---

## 4. File Specifications

### 4.1 `pyproject.toml`

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
"ontos._scripts" = ["*.py"]  # Include all Python files in bundled scripts

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

### 4.2 `ontos/__init__.py` (v1.1: Preserve Exact v2.8 API)

**CRITICAL:** Copy `.ontos/scripts/ontos/__init__.py` exactly, only changing `__version__`.

```python
"""Ontos - Context Management System.

v2.8: Unified package structure for clean architecture.

Package structure:
    ontos.core - Pure logic (no I/O except marked impure functions)
    ontos.ui   - I/O layer (CLI, output, prompts)
"""

__version__ = "3.0.0a1"  # Only change from v2.8

# Re-export commonly used items for convenience
# NOTE: These MUST match v2.8 exactly for backward compatibility
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

### 4.3 `ontos/__main__.py`

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

### 4.4 `ontos/cli.py` (v1.1: Bundled Scripts + Project Root Discovery)

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

### 4.5 `ontos/core/__init__.py`

```python
"""
Core module - Pure business logic for Ontos.

This module contains no I/O operations. All file system access,
git operations, and user interaction are handled by callers.

Modules:
    context     - SessionContext for managing file operations
    frontmatter - YAML frontmatter parsing and validation
    ontology    - Document type definitions and hierarchy
    staleness   - Describes field validation and modification tracking
    history     - Decision history generation
    paths       - Path resolution utilities
    config      - Configuration and git utilities
    curation    - Curation level management
    proposals   - Proposal graduation detection
    schema      - Frontmatter schema validation
"""

from ontos.core.context import SessionContext, FileOperation, PendingWrite
from ontos.core.frontmatter import parse_frontmatter, normalize_frontmatter
from ontos.core.ontology import (
    TYPE_DEFINITIONS,
    TYPE_HIERARCHY,
    VALID_STATUSES,
    validate_type,
    get_type_parent,
)
from ontos.core.staleness import check_staleness, validate_describes_field
from ontos.core.history import generate_decision_history
from ontos.core.paths import get_logs_dir, get_archive_dir, get_proposals_dir
from ontos.core.config import get_git_branch, get_commits_since_push
from ontos.core.curation import CurationLevel
from ontos.core.proposals import check_proposal_graduation
from ontos.core.schema import validate_frontmatter_schema

__all__ = [
    # Context
    "SessionContext",
    "FileOperation",
    "PendingWrite",
    # Frontmatter
    "parse_frontmatter",
    "normalize_frontmatter",
    # Ontology
    "TYPE_DEFINITIONS",
    "TYPE_HIERARCHY",
    "VALID_STATUSES",
    "validate_type",
    "get_type_parent",
    # Staleness
    "check_staleness",
    "validate_describes_field",
    # History
    "generate_decision_history",
    # Paths
    "get_logs_dir",
    "get_archive_dir",
    "get_proposals_dir",
    # Config
    "get_git_branch",
    "get_commits_since_push",
    # Curation
    "CurationLevel",
    # Proposals
    "check_proposal_graduation",
    # Schema
    "validate_frontmatter_schema",
]
```

### 4.6 `ontos/ui/__init__.py`

```python
"""
UI module - User interface and output handling.

This module handles all user-facing output including:
- Formatted console output
- Warning and error messages
- Progress indicators (future)
- JSON output mode (Phase 4)
"""

from ontos.ui.output import OutputHandler

__all__ = ["OutputHandler"]
```

---

## 5. Migration Tasks

### 5.1 Phase 1A: Package Setup (Day 1)

**Task 1.1: Create pyproject.toml**
- [ ] Create `pyproject.toml` at project root (copy from Section 4.1)
- [ ] Verify syntax (Python 3.11+): `python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"`
- [ ] Verify syntax (Python 3.9/3.10): `pip install tomli && python -c "import tomli; tomli.load(open('pyproject.toml', 'rb'))"`

**Task 1.2: Create package directory**
- [ ] Create `ontos/` directory at project root
- [ ] Create `ontos/__init__.py` (copy from Section 4.2)
- [ ] Create `ontos/__main__.py` (copy from Section 4.3)
- [ ] Create `ontos/cli.py` (copy from Section 4.4)

**Task 1.3: Move core modules**
- [ ] Copy `.ontos/scripts/ontos/core/` to `ontos/core/`
- [ ] Update `ontos/core/__init__.py` (copy from Section 4.5)
- [ ] Verify all 10 core modules copied

**Task 1.4: Move UI modules**
- [ ] Copy `.ontos/scripts/ontos/ui/` to `ontos/ui/`
- [ ] Update `ontos/ui/__init__.py` (copy from Section 4.6)

**Task 1.5: Create architecture placeholder directories (v1.1)**
- [ ] Create `ontos/commands/__init__.py` (empty, placeholder for Phase 2)
- [ ] Create `ontos/io/__init__.py` (empty, placeholder for Phase 2)
- [ ] Create `ontos/mcp/__init__.py` (empty, placeholder for Phase 2)

**Task 1.6: Bundle legacy scripts (v1.1 - Critical)**
- [ ] Create `ontos/_scripts/` directory
- [ ] Create `ontos/_scripts/__init__.py` (empty, makes it importable)
- [ ] Copy `ontos.py` to `ontos/_scripts/ontos.py`
- [ ] Copy `ontos_init.py` to `ontos/_scripts/ontos_init.py`
- [ ] Copy all `.ontos/scripts/ontos_*.py` files to `ontos/_scripts/`
- [ ] Verify all 23 scripts bundled

**Task 1.7: Verify package structure**
```bash
# Should show all expected files including _scripts/
find ontos -name "*.py" | sort
```

### 5.2 Phase 1B: Import Updates (Day 1-2)

**Task 2.1: Update root scripts**

Update import statements in root-level scripts. Pattern:

```python
# BEFORE (path manipulation):
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.ontos', 'scripts'))
from ontos.core.context import SessionContext

# AFTER (direct import):
from ontos.core.context import SessionContext
```

Files to update:
- [ ] `ontos.py` - Remove sys.path manipulation
- [ ] `ontos_init.py` - Remove sys.path manipulation
- [ ] `ontos_config.py` - Remove sys.path manipulation

**Task 2.2: Update .ontos/scripts/*.py**

All scripts in `.ontos/scripts/` need import updates:
- [ ] `ontos_consolidate.py`
- [ ] `ontos_end_session.py`
- [ ] `ontos_generate_context_map.py`
- [ ] (... all 23 scripts)

**Task 2.3: Update deprecated shim**

Update `.ontos/scripts/ontos_lib.py` to import from new location:

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
# ... etc
```

### 5.3 Phase 1C: Test Updates (Day 2)

**Task 3.1: Update tests/conftest.py**

```python
# BEFORE:
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.ontos', 'scripts'))

# AFTER:
# No path manipulation needed - package is installed
# pytest will find the ontos package automatically
```

**Task 3.2: Update test imports**

Update all test files to use direct imports:

```python
# BEFORE:
sys.path.insert(0, ...)
from ontos.core.context import SessionContext

# AFTER:
from ontos.core.context import SessionContext
```

Files to update:
- [ ] `tests/conftest.py`
- [ ] `tests/test_*.py` (all 27+ files)
- [ ] `.ontos/scripts/tests/conftest.py`
- [ ] `.ontos/scripts/tests/test_*.py`

**Task 3.3: Update pytest configuration**

Ensure `pyproject.toml` has correct test paths (already in spec):
```toml
[tool.pytest.ini_options]
testpaths = ["tests", ".ontos/scripts/tests"]
```

### 5.4 Phase 1D: Installation Verification (Day 2)

**Task 4.1: Editable install**
```bash
pip install -e .
```

**Task 4.2: Verify CLI**
```bash
ontos --version    # Should print: ontos 3.0.0a1
ontos --help       # Should show help
python -m ontos --version  # Should work
```

**Task 4.3: Verify imports**
```python
>>> import ontos
>>> ontos.__version__
'3.0.0a1'
>>> from ontos.core.context import SessionContext
>>> SessionContext
<class 'ontos.core.context.SessionContext'>
```

**Task 4.4: Run all tests**
```bash
pytest tests/ -v
pytest .ontos/scripts/tests/ -v
```

**Task 4.5: Run Golden Master tests**
```bash
python tests/golden/compare_golden_master.py --fixture all
```

---

## 6. CI Integration

### 6.1 Update `.github/workflows/ci.yml`

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

---

## 7. Verification

### 7.1 Commands to Run

```bash
# 1. Install package in editable mode
pip install -e .

# 2. Verify CLI works (editable mode)
ontos --version
ontos --help
python -m ontos --version

# 2b. (v1.1) Test non-editable install in clean venv
python -m venv /tmp/ontos-test-venv
source /tmp/ontos-test-venv/bin/activate
pip install .
ontos --version
deactivate
rm -rf /tmp/ontos-test-venv

# 3. Verify imports work
python -c "import ontos; print(ontos.__version__)"
python -c "from ontos.core.context import SessionContext; print(SessionContext)"
python -c "from ontos.ui.output import OutputHandler; print(OutputHandler)"

# 4. Run existing tests
pytest tests/ -v
pytest .ontos/scripts/tests/ -v

# 5. Run Golden Master tests (CRITICAL)
python tests/golden/compare_golden_master.py --fixture all

# 6. Verify existing commands still work
ontos map
# (In a project with .ontos-internal/)
```

### 7.2 Verification Checklist

| Check | Command | Expected |
|-------|---------|----------|
| Package installs (editable) | `pip install -e .` | Exit 0 |
| Package installs (non-editable) | `pip install .` | Exit 0 (v1.1) |
| Version shows | `ontos --version` | `ontos 3.0.0a1` |
| Module invocation | `python -m ontos --version` | `ontos 3.0.0a1` |
| Import works | `python -c "import ontos"` | No errors |
| Unit tests pass | `pytest tests/` | All pass |
| Golden Master pass | `compare_golden_master.py` | 8/8 PASS x 2 fixtures |
| Map command works | `ontos map` | Generates context map |
| CLI from subdirectory (v1.1) | `cd src && ontos map` | Finds project root |

### 7.3 Sign-off Checklist

- [ ] `pyproject.toml` created and valid
- [ ] Package structure matches Section 3.1
- [ ] All imports updated (no sys.path manipulation)
- [ ] `pip install -e .` succeeds
- [ ] CLI commands work (`ontos --version`, `ontos map`)
- [ ] `python -m ontos` works
- [ ] All 303+ existing tests pass
- [ ] Golden Master tests pass (small, medium)
- [ ] No behavior changes from v2.9.x
- [ ] CI workflow updated and passing
- [ ] Ready for Phase 2

---

## 8. Risks and Mitigations

### 8.1 Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Import path breakage | High | High | Update all imports systematically; run tests after each file |
| Circular imports | Medium | Medium | Review dependency graph; types.py has no internal deps |
| Test discovery issues | Medium | Low | Explicit testpaths in pyproject.toml |
| Golden Master regression | Low | High | Run after every import change |
| Backward compatibility break | Medium | Medium | Keep .ontos/scripts/ working via updated imports |

### 8.2 Rollback Plan

If Phase 1 causes issues:
1. Golden Master baselines show exact regression point
2. Git revert to pre-Phase 1 commit
3. Old import patterns still work (path manipulation)
4. `.ontos/scripts/ontos/` still exists as backup

---

## 9. Implementation Notes

### 9.1 Import Update Strategy

Use this search/replace pattern across the codebase:

```bash
# Find files with old import pattern
grep -r "sys.path.insert.*\.ontos.*scripts" --include="*.py"

# Update pattern (manual review each file)
# BEFORE: sys.path.insert(0, os.path.join(..., '.ontos', 'scripts'))
# AFTER: (delete the line)
```

### 9.2 Order of Operations

Execute in this order to minimize broken states:

1. **Create new package first** (ontos/ at root)
2. **Verify package imports work** in isolation
3. **Update root scripts** (ontos.py, ontos_init.py)
4. **Update .ontos/scripts/*.py** one at a time
5. **Update tests** after scripts work
6. **Run Golden Master** after each major change

### 9.3 Dual Installation Period

During Phase 1, both import styles should work:
```python
# OLD (still works via deprecated shim)
from ontos_lib import SessionContext

# NEW (preferred)
from ontos.core.context import SessionContext
```

This allows gradual migration and testing.

### 9.4 Files to NOT Modify

These files should remain unchanged in Phase 1:
- Core module logic (only imports change)
- `.ontos-internal/` documentation
- Golden Master fixtures
- `.gitignore`, `LICENSE`, etc.

---

## 10. Post-Phase 1

### 10.1 Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| pyproject.toml | `./pyproject.toml` | Created |
| Package root | `./ontos/` | Created |
| CLI entry point | `./ontos/cli.py` | Created |
| Updated imports | All .py files | Updated |
| CI workflow | `.github/workflows/` | Updated |

### 10.2 Next Steps (Phase 2)

Phase 2: God Script Decomposition will:
- Extract modules from `ontos_end_session.py` (1,904 lines)
- Extract modules from `ontos_generate_context_map.py` (1,295 lines)
- Create new modules: `core/graph.py`, `core/validation.py`, etc.
- All changes validated against Golden Master

### 10.3 Tag

After Phase 1 verification:
```bash
git tag -a v3.0.0-alpha -m "Phase 1: Package Structure"
git push origin v3.0.0-alpha
```

---

*End of Phase 1 Implementation Spec*
