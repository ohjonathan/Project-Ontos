---
id: phase4_implementation_spec
type: strategy
status: approved
depends_on: [phase3_final_approval_chief_architect]
concepts: [cli, argparse, doctor, hook, export, json-output, pypi, legacy-deletion]
---

# Phase 4 Implementation Spec: Full CLI Release

**Version:** 1.1
**Author:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-13
**Status:** Approved for Implementation

**Change History:**
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-13 | Initial draft |
| 1.1 | 2026-01-13 | Review Board feedback incorporated. All open questions decided. Blocking issues addressed. |

---

## 1. Overview

Phase 4 is the final implementation phase of Ontos v3.0.0. Theme: **"Ship it."**

**Goal:** Complete CLI with all commands, hooks, JSON output, and PyPI-ready package. Delete legacy scripts.

**Deliverables:**
| Deliverable | Description |
|-------------|-------------|
| `cli.py` | Full argparse CLI with all 13 commands |
| `commands/doctor.py` | Health check and diagnostics (NEW) |
| `commands/hook.py` | Git hook dispatcher (NEW) |
| `commands/export.py` | CLAUDE.md generation (NEW) |
| `ui/json_output.py` | JSON formatting for `--json` mode (NEW) |
| `ui/progress.py` | Progress indicators (NEW) |
| Shim hooks | Python-based with graceful fallback |
| Deletion | Remove legacy `_scripts/` files with archive |

**Risk Level:** MEDIUM-HIGH (user-facing release, legacy deletion)

---

## 2. Current State Assessment

### 2.1 Post-Phase 3 State

**CLI (`ontos/cli.py`):**
- 132 lines, thin wrapper (NOT argparse yet)
- Two code paths:
  1. Native: `ontos init` routed directly to `commands/init.py`
  2. Delegation: All other commands passed to `_scripts/ontos.py`
- Global options: `--version`, `--help` only
- No `--json`, `--quiet` support yet

**Commands (`ontos/commands/`):**

| File | Type | Status |
|------|------|--------|
| `init.py` | Native | Phase 3 complete |
| `map.py` | Native | Phase 2 complete |
| `log.py` | Native | Phase 2 complete |
| `verify.py` | Wrapper | Delegates to `_scripts/` |
| `query.py` | Wrapper | Delegates to `_scripts/` |
| `migrate.py` | Wrapper | Delegates to `_scripts/` |
| `consolidate.py` | Wrapper | Delegates to `_scripts/` |
| `promote.py` | Wrapper | Delegates to `_scripts/` |
| `scaffold.py` | Wrapper | Delegates to `_scripts/` |
| `stub.py` | Wrapper | Delegates to `_scripts/` |

**UI (`ontos/ui/`):**
- `output.py` — `OutputHandler` class with emoji output, quiet mode
- No JSON output handling yet

**Entry Point (`pyproject.toml`):**
```toml
[project.scripts]
ontos = "ontos.cli:main"
```

### 2.2 What Needs to Be Built

| Component | File | Priority |
|-----------|------|----------|
| Full argparse CLI | `cli.py` | P0 |
| Doctor command | `commands/doctor.py` | P0 |
| Hook dispatcher | `commands/hook.py` | P0 |
| Export command | `commands/export.py` | P1 |
| JSON output handler | `ui/json_output.py` | P0 |
| Progress indicators | `ui/progress.py` | P2 |

### 2.3 Legacy Scripts Inventory

**`ontos/_scripts/` (28 files):**

| Status | Count | Files |
|--------|-------|-------|
| Delete in v3.0.0 | 8 | `ontos_install_hooks.py`, `ontos_create_bundle.py`, `ontos_generate_ontology_spec.py`, `ontos_summarize.py`, `ontos_migrate_frontmatter.py`, `ontos_migrate_v2.py`, `ontos_remove_frontmatter.py`, `install.py` |
| Archive then delete | 11 | Command wrappers + hook implementations |
| Keep (config) | 2 | `ontos_config.py`, `ontos_config_defaults.py` |
| Delete last | 1 | `ontos_lib.py` (15+ imports depend on it) |
| Keep (dispatcher) | 1 | `ontos.py` (needed until all commands native) |

**Critical Dependency:** `ontos_lib.py` is imported by 15+ files and must be deleted last after all imports migrated.

---

## 3. Scope

### 3.1 In Scope

- Full argparse CLI with 13 commands
- Global options: `--version`, `--help`, `--quiet`, `--json`
- Three new commands: `doctor`, `hook`, `export`
- JSON output system with consistent schema
- Python-based shim hooks with graceful fallback
- Exit code standardization (0-5)
- Archive and deletion of legacy scripts per Roadmap 6.10
- PyPI publication readiness

### 3.2 Out of Scope

- MCP server integration (v4.0)
- AI-powered features (`ontos summarize`) (v4.0)
- Multiple export templates (v4.0)
- Windows GUI (never)

### 3.3 Deferred to v3.1/v4.0

- `--interactive` flag for `ontos init`
- Multiple export templates (`--type agents-md`, `--type cursor`)
- `ontos activate` command for AI session bootstrap
- Native implementations of all wrapper commands

---

## 4. Technical Design

### 4.1 CLI Architecture (`cli.py`)

**Replace current thin wrapper with full argparse implementation.**

```python
"""Ontos CLI - Unified command interface."""
import argparse
import sys
from pathlib import Path

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ontos",
        description="Local-first documentation management for AI-assisted development",
    )

    # Global options
    parser.add_argument("--version", "-V", action="store_true", help="Show version")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress non-essential output")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Register each command
    register_init(subparsers)
    register_map(subparsers)
    register_log(subparsers)
    register_doctor(subparsers)
    register_export(subparsers)
    register_hook(subparsers)
    register_verify(subparsers)
    register_query(subparsers)
    register_migrate(subparsers)
    register_consolidate(subparsers)
    register_promote(subparsers)
    register_scaffold(subparsers)
    register_stub(subparsers)

    return parser

def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    if args.version:
        import ontos
        print(f"ontos {ontos.__version__}")
        return 0

    if not args.command:
        parser.print_help()
        return 0

    # Route to command handler
    return args.func(args)
```

**Command Registration Pattern:**

```python
def register_init(subparsers):
    p = subparsers.add_parser("init", help="Initialize Ontos in a project")
    p.add_argument("--force", "-f", action="store_true", help="Overwrite existing config")
    p.add_argument("--skip-hooks", action="store_true", help="Don't install git hooks")
    p.set_defaults(func=cmd_init)

def cmd_init(args) -> int:
    from ontos.commands.init import init_command, InitOptions
    options = InitOptions(
        path=Path.cwd(),
        force=args.force,
        skip_hooks=args.skip_hooks,
    )
    code, msg = init_command(options)
    if not args.json:
        print(msg)
    else:
        from ontos.ui.json_output import emit_json
        emit_json({"status": "success" if code == 0 else "error", "message": msg, "exit_code": code})
    return code
```

**JSON Validation for Wrapper Commands:**

When wrapper commands are invoked with `--json`, the CLI must:
1. Pass `--json` flag to the legacy script
2. Capture output
3. Attempt to parse as JSON
4. If valid JSON: emit as-is
5. If invalid JSON: emit error JSON with the original output in `details`

```python
def run_wrapper_with_json(legacy_script: str, args: List[str], json_mode: bool) -> int:
    """Run a wrapper command with JSON validation."""
    if json_mode:
        args = ["--json"] + args

    result = subprocess.run(
        [sys.executable, legacy_script] + args,
        capture_output=True,
        text=True
    )

    if json_mode:
        try:
            # Validate it's actually JSON
            json.loads(result.stdout)
            print(result.stdout)
        except json.JSONDecodeError:
            # Emit error JSON with original output
            emit_error(
                message="Command does not support JSON output in v3.0",
                code="E_JSON_UNSUPPORTED",
                details=result.stdout
            )
    else:
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

    return result.returncode
```

---

### 4.2 `commands/doctor.py`

**Purpose:** Health check and diagnostics for troubleshooting.

**Decision:** Option B (Standard) — 7 checks as specified in roadmap.

**7 Health Checks:**

| # | Check | Pass | Fail |
|---|-------|------|------|
| 1 | Configuration | `.ontos.toml` exists and valid | Missing or malformed |
| 2 | Git hooks | `pre-push`, `pre-commit` installed | Missing or not executable |
| 3 | Python version | >= 3.9 | < 3.9 |
| 4 | Docs directory | Exists, contains `.md` files | Missing or empty |
| 5 | Context map | Exists, valid frontmatter | Missing or invalid |
| 6 | Validation | No hard errors | Errors present |
| 7 | CLI availability | `ontos` in PATH | Not found |

**Graceful Error Handling:**

Each check must handle missing dependencies gracefully:

```python
def check_git_hooks() -> CheckResult:
    """Check git hooks are installed. Handles git not installed."""
    # First, verify git is available
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return CheckResult(
                name="git_hooks",
                status="fail",
                message="Git not installed or not in PATH"
            )
    except FileNotFoundError:
        return CheckResult(
            name="git_hooks",
            status="fail",
            message="Git executable not found"
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="git_hooks",
            status="warn",
            message="Git check timed out"
        )

    # Check if we're in a git repo
    git_dir = Path.cwd() / ".git"
    if not git_dir.is_dir():
        return CheckResult(
            name="git_hooks",
            status="warn",
            message="Not a git repository (hooks not applicable)"
        )

    # Now check hooks...
    # [rest of implementation]
```

**Implementation:**

```python
@dataclass
class DoctorOptions:
    """Configuration for doctor command."""
    verbose: bool = False
    json_output: bool = False

@dataclass
class CheckResult:
    name: str
    status: str  # "pass", "fail", "warn"
    message: str
    details: Optional[str] = None

def doctor_command(options: DoctorOptions) -> Tuple[int, List[CheckResult]]:
    """
    Run health checks and return results.

    Returns:
        Tuple of (exit_code, list of check results)
        Exit code 0 if all pass, 1 if any fail
    """
    results = []

    results.append(check_configuration())
    results.append(check_git_hooks())
    results.append(check_python_version())
    results.append(check_docs_directory())
    results.append(check_context_map())
    results.append(check_validation())
    results.append(check_cli_availability())

    failed = any(r.status == "fail" for r in results)
    return (1 if failed else 0), results
```

**Output Format (normal):**

```
Configuration: .ontos.toml valid
Git hooks: pre-push, pre-commit installed
Python: 3.11.0 (>=3.9 required)
Docs: 25 documents in docs/
Validation: 2 warnings (run `ontos map --strict`)
CLI: ontos available in PATH

Health check: 6/7 passed, 1 warning
```

**Output Format (JSON):**

```json
{
  "status": "pass",
  "checks": [
    {"name": "configuration", "status": "pass", "message": ".ontos.toml valid"},
    {"name": "git_hooks", "status": "pass", "message": "pre-push, pre-commit installed"},
    {"name": "python_version", "status": "pass", "message": "3.11.0 (>=3.9 required)"},
    {"name": "docs_directory", "status": "pass", "message": "25 documents in docs/"},
    {"name": "validation", "status": "warn", "message": "2 warnings"},
    {"name": "cli_availability", "status": "pass", "message": "ontos available in PATH"}
  ],
  "summary": {"passed": 6, "failed": 0, "warnings": 1}
}
```

---

### 4.3 `commands/hook.py`

**Purpose:** Internal dispatcher called by git hook shims.

**Usage:** `ontos hook <hook-type> [args...]`

**Supported hooks:**
- `pre-push` — Validate before push
- `pre-commit` — Check before commit

**Implementation:**

```python
@dataclass
class HookOptions:
    hook_type: str  # "pre-push" or "pre-commit"
    args: List[str] = field(default_factory=list)

def hook_command(options: HookOptions) -> int:
    """
    Dispatch git hook execution.

    Returns:
        0 = Allow git operation
        1 = Block git operation
    """
    if options.hook_type == "pre-push":
        return run_pre_push_hook(options.args)
    elif options.hook_type == "pre-commit":
        return run_pre_commit_hook(options.args)
    else:
        print(f"Unknown hook type: {options.hook_type}", file=sys.stderr)
        return 0  # Don't block on unknown hooks

def run_pre_push_hook(args: List[str]) -> int:
    """Pre-push validation."""
    config = load_project_config()

    # Check if hook enabled
    if not config.hooks.pre_push:
        return 0

    # Run validation
    from ontos.commands.map import generate_context_map, GenerateMapOptions
    # ... validation logic ...

    if errors:
        print("Push blocked: validation errors found", file=sys.stderr)
        return 1
    return 0

def run_pre_commit_hook(args: List[str]) -> int:
    """Pre-commit checks."""
    config = load_project_config()

    # Check if hook enabled
    if not config.hooks.pre_commit:
        return 0

    # Warn about uncommitted docs (don't block)
    # ... warning logic ...

    return 0  # Pre-commit doesn't block by default
```

---

### 4.4 `commands/export.py`

**Purpose:** Generate CLAUDE.md for AI assistant integration.

**Scope Clarification:** This is NOT a scope expansion vs Strategy Q2. Strategy Q2 defers "export templates" (multiple templates, customization) to v4.0. A single hardcoded CLAUDE.md template is explicitly in v3.0.x scope per Roadmap 1.2 and 6.6.

**v3.0 Scope:** Single hardcoded template. v4.0 will add multiple templates.

**Implementation:**

```python
@dataclass
class ExportOptions:
    output_path: Optional[Path] = None  # Default: repo_root/CLAUDE.md
    force: bool = False

CLAUDE_MD_TEMPLATE = '''# CLAUDE.md

## Ontos Activation

This project uses **Ontos** for documentation management.

At the start of every session:
1. Run `ontos map` to generate the context map
2. Read `Ontos_Context_Map.md` to understand the project documentation structure

When ending a session:
3. Run `ontos log` to record your work

## What is Ontos?

Ontos is a local-first documentation management system that:
- Maintains a context map of all project documentation
- Tracks documentation dependencies and status
- Ensures documentation stays synchronized with code changes

For more information, see `docs/reference/Ontos_Manual.md`.
'''

def export_command(options: ExportOptions) -> Tuple[int, str]:
    """
    Generate CLAUDE.md file.

    Returns:
        Tuple of (exit_code, message)

    Exit Codes:
        0: Success
        1: File exists (use --force)
        2: Configuration error
    """
    # Determine repo root
    try:
        repo_root = find_project_root()
    except Exception as e:
        return 2, f"Configuration error: {e}"

    # Determine output path
    output_path = options.output_path or repo_root / "CLAUDE.md"

    # PATH SAFETY: Validate output path is within repo
    try:
        output_path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return 2, f"Error: Output path must be within repository root"

    # Check if exists
    if output_path.exists() and not options.force:
        return 1, f"CLAUDE.md already exists. Use --force to overwrite."

    # Write file
    output_path.write_text(CLAUDE_MD_TEMPLATE)

    return 0, f"Created {output_path}"
```

---

### 4.5 `ui/json_output.py`

**Purpose:** Consistent JSON output for `--json` flag across all commands.

**Implementation (aligned with Roadmap 6.7):**

```python
"""JSON output formatting for CLI commands."""
import json
import sys
from typing import Any, Dict, Optional

class JsonOutputHandler:
    """Handler for JSON output mode."""

    def __init__(self, pretty: bool = False):
        self.pretty = pretty

    def emit(self, data: Dict[str, Any]) -> None:
        """Emit data as JSON to stdout."""
        if self.pretty:
            print(json.dumps(data, indent=2, default=str))
        else:
            print(json.dumps(data, default=str))

    def error(self, message: str, code: str, details: Optional[str] = None) -> None:
        """Emit error in JSON format."""
        data = {
            "status": "error",
            "error_code": code,
            "message": message,
        }
        if details:
            data["details"] = details
        self.emit(data)

    def result(self, data: Any, message: Optional[str] = None) -> None:
        """Emit success result in JSON format. (Named per Roadmap 6.7)"""
        output = {"status": "success", "data": data}
        if message:
            output["message"] = message
        self.emit(output)

# Convenience functions
def emit_json(data: Dict[str, Any], pretty: bool = False) -> None:
    """Emit JSON to stdout."""
    JsonOutputHandler(pretty=pretty).emit(data)

def emit_error(message: str, code: str, details: Optional[str] = None) -> None:
    """Emit error JSON to stdout."""
    JsonOutputHandler().error(message, code, details)

def emit_result(data: Any, message: Optional[str] = None) -> None:
    """Emit success result JSON to stdout."""
    JsonOutputHandler().result(data, message)
```

**JSON Converters (per Roadmap 6.7):**

```python
def to_json(obj: Any) -> Dict:
    """Convert Ontos objects to JSON-serializable dicts."""
    if hasattr(obj, '__dataclass_fields__'):
        return {k: to_json(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, list):
        return [to_json(item) for item in obj]
    elif isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, Enum):
        return obj.value
    else:
        return obj
```

**JSON Schema (all commands):**

```json
{
  "status": "success | error | partial",
  "message": "Human-readable message",
  "data": { ... },
  "error_code": "E001",
  "details": "..."
}
```

---

### 4.6 Shim Hooks

**Template for `.git/hooks/pre-push`:**

```python
#!/usr/bin/env python3
# ontos-managed-hook
"""Ontos pre-push hook. Delegates to ontos CLI."""
import subprocess
import sys
from pathlib import Path

def run_hook():
    """Try multiple methods to invoke ontos hook."""
    args = ["hook", "pre-push"] + sys.argv[1:]

    # Method 1: PATH lookup (preferred)
    try:
        return subprocess.call(["ontos"] + args)
    except FileNotFoundError:
        pass

    # Method 2: sys.executable -m ontos
    try:
        return subprocess.call([sys.executable, "-m", "ontos"] + args)
    except Exception:
        pass

    # Method 3: Graceful degradation
    print("Warning: ontos not found. Skipping hook.", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(run_hook())
```

**Key Features:**
- `# ontos-managed-hook` marker for detection
- Three fallback methods for finding `ontos`
- Graceful degradation (exit 0) if not found
- Cross-platform (Python, not shell)

#### 4.6.1 Windows-Specific Behavior

**Known Windows Challenges:**

| Challenge | Mitigation |
|-----------|------------|
| No shebang execution | Python shim called via git's Python; fallback to `sys.executable` |
| Path separators (\ vs /) | Use `pathlib.Path` for all path operations; normalize with `.as_posix()` |
| chmod not available | No-op on Windows; hooks are executable by default |
| Python not in PATH | Method 2 (`sys.executable -m ontos`) handles this |
| Long path names (>260 chars) | Known limitation; recommend enabling long path support in Windows settings |

**Windows-Specific Implementation Notes:**

```python
# In init.py when installing hooks:
import os
import stat

def install_hook(hook_path: Path, content: str) -> None:
    """Install a hook with cross-platform compatibility."""
    hook_path.write_text(content, encoding='utf-8')

    # Set executable permission (no-op on Windows, required on Unix)
    if os.name != 'nt':  # Not Windows
        current_mode = hook_path.stat().st_mode
        hook_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
```

**Windows Support Level:** Best-effort. Hooks work via git's Python integration; standalone invocation may require Python in PATH.

---

### 4.7 Legacy Deletion Plan

**Decision:** Option B (Mixed) — Immediate deletion for internal-only scripts; archive user-visible scripts; delete in v3.1.

#### 4.7.1 Archive Step (Required by Roadmap 6.10)

Before any deletion, archive the entire `_scripts/` directory:

```bash
# Archive command (to be run before deletion)
mkdir -p .ontos-internal/archive/scripts-v2
cp -r ontos/_scripts/* .ontos-internal/archive/scripts-v2/
echo "Archived on $(date) for v3.0.0 release" > .ontos-internal/archive/scripts-v2/ARCHIVED.txt
```

#### 4.7.2 Deletion Phases

**Phase 4 v3.0.0 Deletions (Immediate):**

| File | Reason | Risk |
|------|--------|------|
| `install.py` | Replaced by pip install | Low (internal) |
| `ontos_install_hooks.py` | Replaced by Phase 3 init | Low (internal) |
| `ontos_create_bundle.py` | Not in v3.0 spec | Low (internal) |
| `ontos_generate_ontology_spec.py` | Not in v3.0 spec | Low (internal) |
| `ontos_summarize.py` | Deferred to v4.0 | Low (internal) |
| `ontos_migrate_frontmatter.py` | Legacy migration | Low (internal) |
| `ontos_migrate_v2.py` | Legacy migration | Low (internal) |
| `ontos_remove_frontmatter.py` | Legacy utility | Low (internal) |

**Deferred to v3.1 (Keep with Deprecation Warning):**

| File | Reason | Action |
|------|--------|--------|
| `ontos.py` | Dispatcher for wrappers | Keep until native impls |
| `ontos_lib.py` | 15+ imports | Keep until migrated |
| `ontos_verify_describes.py` | Wrapper target | Keep until native |
| `ontos_query.py` | Wrapper target | Keep until native |
| (other wrapper targets) | ... | ... |

#### 4.7.3 Deprecation Warning Strategy

For scripts kept in v3.0.0, add deprecation warning at top:

```python
import warnings
warnings.warn(
    "This script is deprecated and will be removed in v3.1. "
    "Use 'ontos <command>' instead.",
    DeprecationWarning,
    stacklevel=2
)
```

#### 4.7.4 Verification Before Deletion

```bash
# Before deleting each script:

# 1. Check no imports remain
grep -r "from ontos._scripts.<script_name>" ontos/
grep -r "import <script_name>" ontos/

# 2. Run tests
pytest tests/ -v

# 3. Manual smoke test
ontos init --help
ontos map --help
ontos doctor
```

---

### 4.8 PyPI Configuration

**`pyproject.toml` updates:**

```toml
[project]
name = "ontos"
version = "3.0.0"
description = "Local-first documentation management for AI-assisted development"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
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
    "tomli>=2.0; python_version < '3.11'",
]

[project.scripts]
ontos = "ontos.cli:main"

[project.urls]
Homepage = "https://github.com/ohjona/Project-Ontos"
Documentation = "https://github.com/ohjona/Project-Ontos/blob/main/docs/reference/Ontos_Manual.md"
Repository = "https://github.com/ohjona/Project-Ontos"
```

---

## 5. Open Questions (DECIDED)

### 5.1 Doctor Command Scope

**Decision:** Option B (Standard) — All 7 checks

**Rationale:** All reviewers agreed. Matches roadmap spec, provides useful diagnostics without over-engineering. Add graceful error handling for git missing scenarios.

---

### 5.2 Wrapper Command Migration

**Decision:** Option A (Keep wrappers) — Defer native implementations to v4.0

**Rationale:** Unanimous agreement. v3.0 focus is "Ship it" — wrappers work, native implementations don't add user value for release.

---

### 5.3 JSON Output for Wrappers

**Decision:** Option A (Passthrough) with validation fallback

**Rationale:** Attempt passthrough; validate output is JSON; return error JSON if invalid. See Section 4.1 implementation.

---

### 5.4 Exit Code for Warnings

**Decision:** Option A (Exit 0) — Warnings don't block CI

**Rationale:** Standard linter behavior. `--strict` mode converts warnings to errors for CI enforcement.

---

### 5.5 Legacy Script Deprecation Timing

**Decision:** Option B (Mixed) — Immediate for internal; v3.1 for user-visible

**Rationale:** Archive per Roadmap 6.10, delete internal scripts immediately, keep wrapper targets with deprecation warnings until v3.1.

---

## 6. Command Reference

| Command | Status | JSON | Description |
|---------|--------|------|-------------|
| `ontos init` | Native | Yes | Initialize repository |
| `ontos map` | Native | Yes | Generate context map |
| `ontos log` | Native | Yes | End session logging |
| `ontos doctor` | **NEW** | Yes | Health diagnostics |
| `ontos export` | **NEW** | No | CLAUDE.md generation |
| `ontos hook` | **NEW** | No | Hook dispatcher (internal) |
| `ontos verify` | Wrapper | Yes | Verify describes dates |
| `ontos query` | Wrapper | Yes | Search documents |
| `ontos migrate` | Wrapper | Yes | Schema migration |
| `ontos consolidate` | Wrapper | Yes | Archive old logs |
| `ontos promote` | Wrapper | Yes | Promote curation level |
| `ontos scaffold` | Wrapper | Yes | Generate scaffolds |
| `ontos stub` | Wrapper | Yes | Create stub documents |

---

## 7. Exit Codes

**Baseline (Roadmap 6.3):**

| Code | Meaning | Commands |
|------|---------|----------|
| 0 | Success | All |
| 1 | Validation Error | map, verify |
| 2 | Configuration Error | init, export |
| 3 | User Input Error | (baseline) |
| 4 | Git Error | hook |
| 5 | Internal Error | All |

**Command-Specific Extensions:**

| Code | Meaning | Commands | Note |
|------|---------|----------|------|
| 1 | Already exists | init, export | Subtype of validation |
| 2 | Not a git repository | init | Subtype of config |
| 3 | Hooks skipped (partial success) | init | Extension for init only |

**Note:** Exit code 3 for `ontos init` is a command-specific extension meaning "partial success — hooks skipped due to existing non-Ontos hooks." This is NOT a user input error in the context of init. Users can use `--force` to override.

**Warnings:** Commands return exit 0 for success with warnings. Use `--strict` to convert warnings to errors (exit 1).

---

## 8. Test Strategy

### 8.1 Unit Tests

| Module | Tests |
|--------|-------|
| `cli.py` | Argument parsing, command routing, global options |
| `commands/doctor.py` | Each health check individually, JSON output, graceful git missing |
| `commands/hook.py` | Hook dispatch, exit codes |
| `commands/export.py` | File creation, --force behavior, path validation |
| `ui/json_output.py` | JSON formatting, schema compliance, converters |

### 8.2 Integration Tests

- End-to-end CLI tests via subprocess
- `ontos init` -> `ontos map` -> `ontos log` workflow
- `ontos doctor` in healthy vs. broken project
- Hook execution simulation
- JSON validation for wrapper commands

### 8.3 Cross-Platform Tests

- Shim hooks on Linux/macOS (execute directly)
- Shim hooks on Windows (via Python)
- Path handling (forward vs. backslash)
- Hook installation without chmod (Windows)

### 8.4 Deletion Verification

```bash
# Before deleting each legacy script:
1. grep -r "import <script_name>" ontos/
2. grep -r "from.*<script_name>" ontos/
3. pytest tests/ -v
4. Manual smoke test of affected commands
```

---

## 9. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Legacy deletion breaks workflows | Medium | High | Archive first (per 6.10), deprecation warnings, phased deletion |
| Cross-platform hook issues (Windows) | Medium | High | Python shim with 3 fallback methods, document limitations |
| JSON output inconsistency | Medium | Medium | Central `JsonOutputHandler`, validation wrapper for wrappers |
| Exit code misuse in CI | Low | Medium | Document clearly, test in CI environments |
| PyPI publication issues | Low | Medium | Test on test.pypi.org first |
| Export path traversal | Low | Medium | Validate output path within repo root |
| Doctor fails without git | Medium | Low | Graceful error handling, clear message |

---

## 10. Acceptance Criteria

**Functional:**
- [ ] All 13 commands accessible via `ontos <command>`
- [ ] `ontos doctor` reports 7 health checks with graceful error handling
- [ ] `ontos export` generates CLAUDE.md with path validation
- [ ] `ontos hook pre-push` validates before push
- [ ] `--json` produces valid JSON for 11 commands
- [ ] `--quiet` suppresses non-essential output
- [ ] Exit codes match specification

**Quality:**
- [ ] 303+ existing tests pass
- [ ] Golden Master tests pass
- [ ] No regressions in native commands

**Cross-Platform:**
- [ ] Shim hooks work on macOS
- [ ] Shim hooks work on Linux
- [ ] Shim hooks work on Windows (best-effort)

**Release:**
- [ ] `pip install ontos` works
- [ ] Package installable from test.pypi.org
- [ ] Version string is `3.0.0`
- [ ] README updated for v3.0
- [ ] Legacy scripts archived per Roadmap 6.10

---

## 11. Migration Guide

**For users upgrading from v2.x:**

1. **Install v3.0:**
   ```bash
   pip install ontos
   ```

2. **Initialize project:**
   ```bash
   cd your-project
   ontos init
   ```
   This creates `.ontos.toml` and installs hooks.

3. **Verify installation:**
   ```bash
   ontos doctor
   ```

4. **Generate context map:**
   ```bash
   ontos map
   ```

5. **For AI assistant integration:**
   ```bash
   ontos export
   ```
   This creates `CLAUDE.md` with activation instructions.

**Breaking changes:**
- Legacy `python3 .ontos/scripts/ontos.py` no longer supported
- Use `ontos <command>` instead
- **Config file is now `.ontos.toml`** (not `ontos_config.py`)
- Legacy config `ontos_config.py` is ignored; migrate settings manually

**File Mapping (v2 -> v3):**

| v2.x Location | v3.0 Location |
|---------------|---------------|
| `.ontos/scripts/ontos.py map` | `ontos map` |
| `.ontos/scripts/ontos_end_session.py` | `ontos log` |
| `.ontos/scripts/ontos_config.py` | `.ontos.toml` |
| (manual hook installation) | `ontos init` (automatic) |

---

## 12. Implementation Order

**Recommended sequence:**

| Step | Tasks |
|------|-------|
| 1 | `cli.py` full argparse, `ui/json_output.py` |
| 2 | `commands/doctor.py` with graceful error handling, tests |
| 3 | `commands/hook.py`, `commands/export.py` with path validation, tests |
| 4 | Integration testing, JSON output verification for wrappers |
| 5 | Archive legacy scripts, delete safe-to-delete scripts |
| 6 | PyPI testing, final verification, release |

---

*Spec Version: 1.1*
*Approved for Implementation*
*All open questions decided. All blocking issues addressed.*
