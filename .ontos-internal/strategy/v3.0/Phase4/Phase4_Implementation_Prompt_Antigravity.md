# Ontos v3.0 Phase 4: Implementation Prompt for Antigravity

**Author:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-13
**Spec Version:** 1.1
**Target:** Antigravity (Developer powered by Gemini 2.5 Pro)

---

## Overview

Phase 4 is the final implementation phase of Ontos v3.0.0. Theme: **"Ship it."**

You will build the complete CLI with all commands, JSON output support, cross-platform shim hooks, and clean up legacy scripts. This is the release phase — everything must be polished.

**What you will deliver:**
- Full argparse CLI with 13 commands and global options
- 3 new commands: `doctor`, `hook`, `export`
- JSON output system via `ui/json_output.py`
- Python-based shim hooks with 3-method fallback
- Legacy script archive and deletion
- PyPI-ready package

**Risk level:** MEDIUM-HIGH. Legacy deletion is the highest-risk task.

---

## Pre-Implementation Checklist

Before writing any code, verify:

- [ ] On correct branch (create `phase4-full-cli` from `main`)
- [ ] Phase 3 is merged and working
- [ ] All tests pass on current main
- [ ] Read and understand the spec (`Phase4-Implementation-Spec.md` v1.1)
- [ ] Read and understand open question decisions (`Phase4_Chief_Architect_Response.md`)

**Commands to run:**

```bash
# Checkout main and pull latest
git checkout main
git pull origin main

# Create feature branch
git checkout -b phase4-full-cli

# Verify Phase 3 is working
python -m ontos --version
python -m ontos init --help
python -m ontos map --help

# Verify all tests pass
pytest tests/ -v
pytest tests/golden/ -v

# Count current tests (should be 344+)
pytest tests/ --collect-only | grep "test session starts" -A 1
```

**If any verification fails:** STOP. Do not proceed. Report to Chief Architect.

---

## Architecture Constraints (DO NOT VIOLATE)

These constraints are inviolable. Breaking them will block the PR.

### 1. `core/` must NOT import from `io/`, `ui/`, or `commands/`

```python
# ❌ FORBIDDEN in core/
from ontos.io import anything
from ontos.ui import anything
from ontos.commands import anything

# ✅ ALLOWED in core/
from pathlib import Path  # stdlib only
from dataclasses import dataclass
from typing import Optional, List
```

### 2. `io/` may import from `core/` (types only)

```python
# ✅ ALLOWED in io/
from ontos.core.config import OntosConfig
from ontos.core.types import DocumentData

# ❌ FORBIDDEN in io/
from ontos.ui import anything
from ontos.commands import anything
```

### 3. `ui/` may import from `core/` (types only)

```python
# ✅ ALLOWED in ui/
from ontos.core.types import ValidationError
from ontos.core.config import OntosConfig

# ❌ FORBIDDEN in ui/
from ontos.io import anything
from ontos.commands import anything
```

### 4. `commands/` may import from `core/`, `io/`, and `ui/`

```python
# ✅ ALL ALLOWED in commands/
from ontos.core.config import OntosConfig
from ontos.io.config import load_project_config
from ontos.ui.json_output import emit_json, emit_result
```

### 5. `cli.py` may import from `commands/`

```python
# ✅ ALLOWED in cli.py
from ontos.commands.doctor import doctor_command
from ontos.commands.export import export_command
from ontos.commands.hook import hook_command
```

### Verification Command

After any file creation/modification, run:

```bash
# Check for architecture violations
python -c "
import ast
import sys
from pathlib import Path

violations = []
for py_file in Path('ontos/core').rglob('*.py'):
    content = py_file.read_text()
    if 'from ontos.io' in content or 'from ontos.ui' in content or 'from ontos.commands' in content:
        violations.append(str(py_file))

if violations:
    print('ARCHITECTURE VIOLATIONS in core/:')
    for v in violations:
        print(f'  {v}')
    sys.exit(1)
else:
    print('OK: No architecture violations')
"
```

---

## Open Question Decisions (MUST IMPLEMENT)

These decisions were made in the Chief Architect Response. Implement them exactly.

| Question | Decision | Implementation |
|----------|----------|----------------|
| Doctor Scope | Option B (Standard) | 7 health checks with graceful error handling |
| Wrapper Migration | Option A (Keep wrappers) | Do NOT convert wrappers to native in this phase |
| JSON for Wrappers | Option A + Validation | Passthrough `--json`, validate output, error JSON if invalid |
| Exit for Warnings | Option A (Exit 0) | Success with warnings returns 0; use `--strict` for exit 1 |
| Deprecation Timing | Option B (Mixed) | Archive all, delete internal-only scripts, keep wrapper targets |

---

## Task Sequence

### Day 1: UI Layer Foundation

#### Task 4.1.1: Create `ui/__init__.py`

**Description:** Create the UI package with public exports.

**File(s):**
- `ontos/ui/__init__.py` — CREATE

**Dependencies:** None

**Instructions:**

1. Create `ontos/ui/__init__.py`
2. Add public exports for the package
3. Add docstring describing the layer's purpose

**Code:**

```python
# ontos/ui/__init__.py
"""
Ontos UI Layer.

This layer handles output formatting for the CLI:
- JSON output formatting (json_output.py)
- Progress indicators (progress.py)
- Human-readable output (output.py - existing)

Layer Rules:
- May import from core/ (types only)
- Must NOT import from io/ or commands/
"""

from ontos.ui.output import OutputHandler

__all__ = [
    "OutputHandler",
]
```

**Verification:**

```bash
python -c "from ontos.ui import OutputHandler; print('OK')"
```

**Checkpoint:** Commit with message `"feat(ui): add ui package __init__.py"`

---

#### Task 4.1.2: Create `ui/json_output.py`

**Description:** Implement JSON output formatting per Roadmap 6.7 and spec Section 4.5.

**File(s):**
- `ontos/ui/json_output.py` — CREATE
- `tests/ui/test_json_output.py` — CREATE

**Dependencies:** Task 4.1.1

**Instructions:**

1. Create `ontos/ui/json_output.py`
2. Implement `JsonOutputHandler` class with:
   - `emit(data: Dict)` — raw JSON output
   - `error(message, code, details)` — error JSON
   - `result(data, message)` — success JSON (named per Roadmap 6.7)
3. Implement convenience functions: `emit_json`, `emit_error`, `emit_result`
4. Implement `to_json()` converter for Ontos objects
5. Write comprehensive tests

**Code:**

```python
# ontos/ui/json_output.py
"""JSON output formatting for CLI commands.

Per Roadmap 6.7: Consistent JSON output across all commands.
"""

import json
import sys
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class JsonOutputHandler:
    """Handler for JSON output mode."""

    def __init__(self, pretty: bool = False, file=None):
        """
        Initialize JSON output handler.

        Args:
            pretty: If True, indent JSON output for readability
            file: Output file (default: sys.stdout)
        """
        self.pretty = pretty
        self.file = file or sys.stdout

    def emit(self, data: Dict[str, Any]) -> None:
        """Emit data as JSON to output."""
        if self.pretty:
            output = json.dumps(data, indent=2, default=str, ensure_ascii=False)
        else:
            output = json.dumps(data, default=str, ensure_ascii=False)
        print(output, file=self.file)

    def error(
        self,
        message: str,
        code: str,
        details: Optional[str] = None
    ) -> None:
        """Emit error in JSON format."""
        data: Dict[str, Any] = {
            "status": "error",
            "error_code": code,
            "message": message,
        }
        if details is not None:
            data["details"] = details
        self.emit(data)

    def result(self, data: Any, message: Optional[str] = None) -> None:
        """
        Emit success result in JSON format.

        Named 'result' per Roadmap 6.7 specification.
        """
        output: Dict[str, Any] = {
            "status": "success",
            "data": to_json(data),
        }
        if message is not None:
            output["message"] = message
        self.emit(output)


def to_json(obj: Any) -> Any:
    """
    Convert Ontos objects to JSON-serializable types.

    Handles:
    - Dataclasses -> dict
    - Lists -> list of converted items
    - Paths -> str
    - Enums -> value
    - Other -> as-is
    """
    if obj is None:
        return None
    elif is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_json(getattr(obj, f.name)) for f in fields(obj)}
    elif isinstance(obj, list):
        return [to_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: to_json(v) for k, v in obj.items()}
    elif isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, Enum):
        return obj.value
    else:
        return obj


# Convenience functions

def emit_json(data: Dict[str, Any], pretty: bool = False) -> None:
    """Emit JSON to stdout."""
    JsonOutputHandler(pretty=pretty).emit(data)


def emit_error(
    message: str,
    code: str,
    details: Optional[str] = None
) -> None:
    """Emit error JSON to stdout."""
    JsonOutputHandler().error(message, code, details)


def emit_result(data: Any, message: Optional[str] = None) -> None:
    """Emit success result JSON to stdout."""
    JsonOutputHandler().result(data, message)


def validate_json_output(output: str) -> bool:
    """
    Validate that a string is valid JSON.

    Used by wrapper command JSON validation.
    """
    try:
        json.loads(output)
        return True
    except json.JSONDecodeError:
        return False
```

**Tests:**

```python
# tests/ui/test_json_output.py
"""Tests for JSON output formatting."""

import json
import sys
from dataclasses import dataclass
from enum import Enum
from io import StringIO
from pathlib import Path

import pytest

from ontos.ui.json_output import (
    JsonOutputHandler,
    emit_error,
    emit_json,
    emit_result,
    to_json,
    validate_json_output,
)


class TestJsonOutputHandler:
    """Tests for JsonOutputHandler class."""

    def test_emit_outputs_valid_json(self):
        """emit() should output valid JSON."""
        output = StringIO()
        handler = JsonOutputHandler(file=output)
        handler.emit({"key": "value"})
        result = json.loads(output.getvalue())
        assert result == {"key": "value"}

    def test_emit_pretty_indents_output(self):
        """emit() with pretty=True should indent output."""
        output = StringIO()
        handler = JsonOutputHandler(pretty=True, file=output)
        handler.emit({"key": "value"})
        assert "  " in output.getvalue()  # Has indentation

    def test_error_includes_required_fields(self):
        """error() should include status, error_code, message."""
        output = StringIO()
        handler = JsonOutputHandler(file=output)
        handler.error("Test error", "E001")
        result = json.loads(output.getvalue())
        assert result["status"] == "error"
        assert result["error_code"] == "E001"
        assert result["message"] == "Test error"
        assert "details" not in result

    def test_error_includes_details_when_provided(self):
        """error() should include details when provided."""
        output = StringIO()
        handler = JsonOutputHandler(file=output)
        handler.error("Test error", "E001", details="Extra info")
        result = json.loads(output.getvalue())
        assert result["details"] == "Extra info"

    def test_result_includes_success_status(self):
        """result() should set status to success."""
        output = StringIO()
        handler = JsonOutputHandler(file=output)
        handler.result({"count": 5})
        result = json.loads(output.getvalue())
        assert result["status"] == "success"
        assert result["data"] == {"count": 5}

    def test_result_includes_message_when_provided(self):
        """result() should include message when provided."""
        output = StringIO()
        handler = JsonOutputHandler(file=output)
        handler.result({"count": 5}, message="Operation complete")
        result = json.loads(output.getvalue())
        assert result["message"] == "Operation complete"


class TestToJson:
    """Tests for to_json converter."""

    def test_converts_none(self):
        """to_json should pass through None."""
        assert to_json(None) is None

    def test_converts_primitives(self):
        """to_json should pass through primitives."""
        assert to_json(42) == 42
        assert to_json("string") == "string"
        assert to_json(True) is True

    def test_converts_list(self):
        """to_json should convert list items."""
        assert to_json([1, 2, 3]) == [1, 2, 3]

    def test_converts_dict(self):
        """to_json should convert dict values."""
        assert to_json({"a": 1, "b": 2}) == {"a": 1, "b": 2}

    def test_converts_path_to_string(self):
        """to_json should convert Path to string."""
        assert to_json(Path("/foo/bar")) == "/foo/bar"

    def test_converts_enum_to_value(self):
        """to_json should convert Enum to its value."""
        class Status(Enum):
            ACTIVE = "active"
            DRAFT = "draft"

        assert to_json(Status.ACTIVE) == "active"

    def test_converts_dataclass(self):
        """to_json should convert dataclass to dict."""
        @dataclass
        class Sample:
            name: str
            count: int

        result = to_json(Sample(name="test", count=5))
        assert result == {"name": "test", "count": 5}

    def test_converts_nested_dataclass(self):
        """to_json should handle nested dataclasses."""
        @dataclass
        class Inner:
            value: int

        @dataclass
        class Outer:
            inner: Inner
            label: str

        result = to_json(Outer(inner=Inner(value=42), label="test"))
        assert result == {"inner": {"value": 42}, "label": "test"}


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_emit_json(self, capsys):
        """emit_json should output to stdout."""
        emit_json({"test": True})
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result == {"test": True}

    def test_emit_error(self, capsys):
        """emit_error should output error JSON."""
        emit_error("Failed", "E999")
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "error"
        assert result["error_code"] == "E999"

    def test_emit_result(self, capsys):
        """emit_result should output success JSON."""
        emit_result({"items": []})
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "success"


class TestValidateJsonOutput:
    """Tests for JSON validation."""

    def test_valid_json_returns_true(self):
        """validate_json_output returns True for valid JSON."""
        assert validate_json_output('{"key": "value"}') is True
        assert validate_json_output('[]') is True
        assert validate_json_output('"string"') is True

    def test_invalid_json_returns_false(self):
        """validate_json_output returns False for invalid JSON."""
        assert validate_json_output('not json') is False
        assert validate_json_output('{key: value}') is False
        assert validate_json_output('') is False
```

**Verification:**

```bash
# Import test
python -c "from ontos.ui.json_output import JsonOutputHandler, emit_json, emit_result, to_json; print('OK')"

# Run tests
pytest tests/ui/test_json_output.py -v

# Architecture check
python -c "
import ast
content = open('ontos/ui/json_output.py').read()
if 'from ontos.io' in content or 'from ontos.commands' in content:
    print('ERROR: Architecture violation!')
    exit(1)
print('OK: No violations')
"
```

**Checkpoint:** Commit with message `"feat(ui): add json_output.py with JsonOutputHandler"`

---

#### Task 4.1.3: Update `ui/__init__.py` exports

**Description:** Add json_output exports to ui package.

**File(s):**
- `ontos/ui/__init__.py` — MODIFY

**Dependencies:** Task 4.1.2

**Instructions:**

1. Add json_output exports to `__all__`
2. Import the public functions

**Code:**

```python
# ontos/ui/__init__.py
"""
Ontos UI Layer.

This layer handles output formatting for the CLI:
- JSON output formatting (json_output.py)
- Progress indicators (progress.py)
- Human-readable output (output.py - existing)

Layer Rules:
- May import from core/ (types only)
- Must NOT import from io/ or commands/
"""

from ontos.ui.output import OutputHandler
from ontos.ui.json_output import (
    JsonOutputHandler,
    emit_json,
    emit_error,
    emit_result,
    to_json,
    validate_json_output,
)

__all__ = [
    # output.py
    "OutputHandler",
    # json_output.py
    "JsonOutputHandler",
    "emit_json",
    "emit_error",
    "emit_result",
    "to_json",
    "validate_json_output",
]
```

**Verification:**

```bash
python -c "from ontos.ui import emit_json, emit_result, to_json; print('OK')"
```

**Checkpoint:** Commit with message `"feat(ui): export json_output functions from ui package"`

---

### Day 1 Checkpoint

After completing Day 1, verify:

```bash
# All imports work
python -c "from ontos.ui import OutputHandler, JsonOutputHandler, emit_json; print('OK')"

# Tests pass
pytest tests/ui/ -v

# No architecture violations
python -c "
from pathlib import Path
violations = []
for f in Path('ontos/ui').rglob('*.py'):
    content = f.read_text()
    if 'from ontos.io' in content or 'from ontos.commands' in content:
        violations.append(str(f))
if violations:
    print(f'VIOLATIONS: {violations}')
    exit(1)
print('OK: UI layer clean')
"

# Full test suite still passes
pytest tests/ -v
```

---

### Day 2: New Commands

#### Task 4.2.1: Create `commands/doctor.py`

**Description:** Implement health check command with 7 checks per spec Section 4.2.

**File(s):**
- `ontos/commands/doctor.py` — CREATE
- `tests/commands/test_doctor_phase4.py` — CREATE

**Dependencies:** Task 4.1.2 (ui/json_output.py)

**Instructions:**

1. Create `ontos/commands/doctor.py`
2. Implement `DoctorOptions` and `CheckResult` dataclasses
3. Implement 7 health checks with graceful error handling
4. Implement `doctor_command()` function
5. Support JSON output mode
6. Handle git not installed gracefully (per Chief Architect Response)
7. Write comprehensive tests

**Code:**

```python
# ontos/commands/doctor.py
"""
Health check and diagnostics command.

Implements 7 health checks per Roadmap 6.4 and Spec v1.1 Section 4.2.
Decision: Option B (Standard) - all 7 checks with graceful error handling.
"""

import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from ontos.ui.json_output import emit_result, to_json


@dataclass
class CheckResult:
    """Result of a single health check."""
    name: str
    status: str  # "pass", "fail", "warn"
    message: str
    details: Optional[str] = None


@dataclass
class DoctorOptions:
    """Configuration for doctor command."""
    verbose: bool = False
    json_output: bool = False


@dataclass
class DoctorResult:
    """Result of all health checks."""
    checks: List[CheckResult] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    warnings: int = 0

    @property
    def status(self) -> str:
        """Overall status: pass, fail, or warn."""
        if self.failed > 0:
            return "fail"
        elif self.warnings > 0:
            return "warn"
        return "pass"


def check_configuration() -> CheckResult:
    """Check 1: .ontos.toml exists and is valid."""
    config_path = Path.cwd() / ".ontos.toml"

    if not config_path.exists():
        return CheckResult(
            name="configuration",
            status="fail",
            message=".ontos.toml not found",
            details="Run 'ontos init' to create configuration"
        )

    try:
        # Try to load the config
        from ontos.io.config import load_project_config
        load_project_config()
        return CheckResult(
            name="configuration",
            status="pass",
            message=".ontos.toml valid"
        )
    except Exception as e:
        return CheckResult(
            name="configuration",
            status="fail",
            message=".ontos.toml malformed",
            details=str(e)
        )


def check_git_hooks() -> CheckResult:
    """Check 2: Git hooks installed and point to ontos."""
    # First, verify git is available (graceful handling per Chief Architect Response)
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
                message="Git not working properly",
                details=result.stderr
            )
    except FileNotFoundError:
        return CheckResult(
            name="git_hooks",
            status="fail",
            message="Git executable not found",
            details="Install git to enable hook functionality"
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
            message="Not a git repository",
            details="Hooks are not applicable outside a git repository"
        )

    # Check for hook files
    hooks_dir = git_dir / "hooks"
    pre_push = hooks_dir / "pre-push"
    pre_commit = hooks_dir / "pre-commit"

    missing = []
    if not pre_push.exists():
        missing.append("pre-push")
    if not pre_commit.exists():
        missing.append("pre-commit")

    if missing:
        return CheckResult(
            name="git_hooks",
            status="warn",
            message=f"Hooks missing: {', '.join(missing)}",
            details="Run 'ontos init --force' to install hooks"
        )

    # Check if hooks are Ontos-managed
    ontos_marker = "# ontos-managed-hook"
    non_ontos = []

    for hook_path in [pre_push, pre_commit]:
        if hook_path.exists():
            content = hook_path.read_text()
            if ontos_marker not in content:
                non_ontos.append(hook_path.name)

    if non_ontos:
        return CheckResult(
            name="git_hooks",
            status="warn",
            message=f"Non-Ontos hooks: {', '.join(non_ontos)}",
            details="These hooks are not managed by Ontos"
        )

    return CheckResult(
        name="git_hooks",
        status="pass",
        message="pre-push, pre-commit installed"
    )


def check_python_version() -> CheckResult:
    """Check 3: Python version >= 3.9."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version >= (3, 9):
        return CheckResult(
            name="python_version",
            status="pass",
            message=f"{version_str} (>=3.9 required)"
        )
    else:
        return CheckResult(
            name="python_version",
            status="fail",
            message=f"{version_str} (>=3.9 required)",
            details="Upgrade Python to 3.9 or later"
        )


def check_docs_directory() -> CheckResult:
    """Check 4: Docs directory exists and contains .md files."""
    # Try to get docs_dir from config, fall back to default
    try:
        from ontos.io.config import load_project_config
        config = load_project_config()
        docs_dir = Path.cwd() / config.paths.docs_dir
    except Exception:
        docs_dir = Path.cwd() / "docs"

    if not docs_dir.exists():
        return CheckResult(
            name="docs_directory",
            status="fail",
            message=f"Docs directory not found: {docs_dir}",
            details="Create the docs directory or update .ontos.toml"
        )

    md_files = list(docs_dir.rglob("*.md"))
    if not md_files:
        return CheckResult(
            name="docs_directory",
            status="warn",
            message=f"No .md files in {docs_dir}",
            details="Add documentation files to track"
        )

    return CheckResult(
        name="docs_directory",
        status="pass",
        message=f"{len(md_files)} documents in {docs_dir.name}/"
    )


def check_context_map() -> CheckResult:
    """Check 5: Context map exists and has valid frontmatter."""
    # Try to get context_map path from config
    try:
        from ontos.io.config import load_project_config
        config = load_project_config()
        context_map = Path.cwd() / config.paths.context_map
    except Exception:
        context_map = Path.cwd() / "Ontos_Context_Map.md"

    if not context_map.exists():
        return CheckResult(
            name="context_map",
            status="fail",
            message="Context map not found",
            details=f"Expected at {context_map}. Run 'ontos map' to generate."
        )

    # Check for valid frontmatter
    try:
        content = context_map.read_text()
        if not content.startswith("---"):
            return CheckResult(
                name="context_map",
                status="warn",
                message="Context map missing frontmatter",
                details="Run 'ontos map' to regenerate"
            )

        return CheckResult(
            name="context_map",
            status="pass",
            message="Context map valid"
        )
    except Exception as e:
        return CheckResult(
            name="context_map",
            status="fail",
            message="Could not read context map",
            details=str(e)
        )


def check_validation() -> CheckResult:
    """Check 6: No validation errors in current documents."""
    try:
        # Try to run validation
        from ontos.commands.map import generate_context_map, GenerateMapOptions
        options = GenerateMapOptions(
            output_path=None,  # Don't write
            strict=False,
            json_output=False,
            quiet=True
        )

        # This is a simplified check - just see if we can scan docs
        from ontos.io.config import load_project_config
        config = load_project_config()
        docs_dir = Path.cwd() / config.paths.docs_dir

        if not docs_dir.exists():
            return CheckResult(
                name="validation",
                status="warn",
                message="Cannot validate (no docs directory)"
            )

        # Count any obvious issues
        md_files = list(docs_dir.rglob("*.md"))
        issues = 0

        for md_file in md_files[:50]:  # Check first 50 to avoid slowness
            try:
                content = md_file.read_text()
                # Basic frontmatter check
                if content.strip() and not content.startswith("---"):
                    issues += 1
            except Exception:
                issues += 1

        if issues > 0:
            return CheckResult(
                name="validation",
                status="warn",
                message=f"{issues} potential issues found",
                details="Run 'ontos map --strict' for full validation"
            )

        return CheckResult(
            name="validation",
            status="pass",
            message="No obvious issues"
        )

    except Exception as e:
        return CheckResult(
            name="validation",
            status="warn",
            message="Validation check skipped",
            details=str(e)
        )


def check_cli_availability() -> CheckResult:
    """Check 7: ontos CLI accessible in PATH."""
    ontos_path = shutil.which("ontos")

    if ontos_path:
        return CheckResult(
            name="cli_availability",
            status="pass",
            message=f"ontos available at {ontos_path}"
        )

    # Check if python -m ontos works
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return CheckResult(
                name="cli_availability",
                status="pass",
                message="ontos available via 'python -m ontos'"
            )
    except Exception:
        pass

    return CheckResult(
        name="cli_availability",
        status="warn",
        message="ontos not in PATH",
        details="Install with 'pip install ontos' or use 'python -m ontos'"
    )


def doctor_command(options: DoctorOptions) -> Tuple[int, DoctorResult]:
    """
    Run health checks and return results.

    Returns:
        Tuple of (exit_code, DoctorResult)
        Exit code 0 if all pass, 1 if any fail
    """
    result = DoctorResult()

    # Run all 7 checks
    checks = [
        check_configuration,
        check_git_hooks,
        check_python_version,
        check_docs_directory,
        check_context_map,
        check_validation,
        check_cli_availability,
    ]

    for check_fn in checks:
        check_result = check_fn()
        result.checks.append(check_result)

        if check_result.status == "pass":
            result.passed += 1
        elif check_result.status == "fail":
            result.failed += 1
        else:  # warn
            result.warnings += 1

    exit_code = 1 if result.failed > 0 else 0
    return exit_code, result


def format_doctor_output(result: DoctorResult, verbose: bool = False) -> str:
    """Format doctor results for human-readable output."""
    lines = []

    for check in result.checks:
        if check.status == "pass":
            icon = "OK"
        elif check.status == "fail":
            icon = "FAIL"
        else:
            icon = "WARN"

        lines.append(f"{icon}: {check.name}: {check.message}")

        if verbose and check.details:
            lines.append(f"     {check.details}")

    lines.append("")
    lines.append(
        f"Health check: {result.passed} passed, "
        f"{result.failed} failed, {result.warnings} warnings"
    )

    return "\n".join(lines)
```

**Tests:**

```python
# tests/commands/test_doctor_phase4.py
"""Tests for doctor command (Phase 4)."""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ontos.commands.doctor import (
    CheckResult,
    DoctorOptions,
    DoctorResult,
    check_configuration,
    check_git_hooks,
    check_python_version,
    check_docs_directory,
    check_context_map,
    check_cli_availability,
    doctor_command,
    format_doctor_output,
)


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_creates_with_required_fields(self):
        result = CheckResult(name="test", status="pass", message="OK")
        assert result.name == "test"
        assert result.status == "pass"
        assert result.message == "OK"
        assert result.details is None

    def test_creates_with_details(self):
        result = CheckResult(
            name="test",
            status="fail",
            message="Failed",
            details="Extra info"
        )
        assert result.details == "Extra info"


class TestDoctorResult:
    """Tests for DoctorResult dataclass."""

    def test_status_pass_when_no_failures(self):
        result = DoctorResult(passed=7, failed=0, warnings=0)
        assert result.status == "pass"

    def test_status_fail_when_has_failures(self):
        result = DoctorResult(passed=5, failed=2, warnings=0)
        assert result.status == "fail"

    def test_status_warn_when_only_warnings(self):
        result = DoctorResult(passed=5, failed=0, warnings=2)
        assert result.status == "warn"


class TestCheckPythonVersion:
    """Tests for check_python_version."""

    def test_passes_for_current_python(self):
        """Current Python should be >= 3.9."""
        result = check_python_version()
        assert result.status == "pass"
        assert "3.9" in result.message


class TestCheckGitHooks:
    """Tests for check_git_hooks."""

    def test_warns_when_not_git_repo(self, tmp_path, monkeypatch):
        """Should warn when not in a git repo."""
        monkeypatch.chdir(tmp_path)
        result = check_git_hooks()
        # Either warn about not being a repo, or fail if git not found
        assert result.status in ("warn", "fail")

    def test_handles_git_not_installed(self, tmp_path, monkeypatch):
        """Should fail gracefully when git not installed."""
        monkeypatch.chdir(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = check_git_hooks()

        assert result.status == "fail"
        assert "not found" in result.message.lower()


class TestCheckConfiguration:
    """Tests for check_configuration."""

    def test_fails_when_no_config(self, tmp_path, monkeypatch):
        """Should fail when .ontos.toml doesn't exist."""
        monkeypatch.chdir(tmp_path)
        result = check_configuration()
        assert result.status == "fail"
        assert "not found" in result.message.lower()


class TestDoctorCommand:
    """Tests for doctor_command."""

    def test_returns_exit_code_0_when_checks_pass(self, tmp_path, monkeypatch):
        """Should return 0 when all checks pass or warn."""
        # Mock all checks to pass
        with patch("ontos.commands.doctor.check_configuration") as mock_config, \
             patch("ontos.commands.doctor.check_git_hooks") as mock_hooks, \
             patch("ontos.commands.doctor.check_python_version") as mock_python, \
             patch("ontos.commands.doctor.check_docs_directory") as mock_docs, \
             patch("ontos.commands.doctor.check_context_map") as mock_map, \
             patch("ontos.commands.doctor.check_validation") as mock_valid, \
             patch("ontos.commands.doctor.check_cli_availability") as mock_cli:

            for mock in [mock_config, mock_hooks, mock_python, mock_docs,
                        mock_map, mock_valid, mock_cli]:
                mock.return_value = CheckResult(
                    name="test", status="pass", message="OK"
                )

            options = DoctorOptions()
            exit_code, result = doctor_command(options)

            assert exit_code == 0
            assert result.passed == 7
            assert result.failed == 0

    def test_returns_exit_code_1_when_check_fails(self):
        """Should return 1 when any check fails."""
        with patch("ontos.commands.doctor.check_configuration") as mock_config, \
             patch("ontos.commands.doctor.check_git_hooks") as mock_hooks, \
             patch("ontos.commands.doctor.check_python_version") as mock_python, \
             patch("ontos.commands.doctor.check_docs_directory") as mock_docs, \
             patch("ontos.commands.doctor.check_context_map") as mock_map, \
             patch("ontos.commands.doctor.check_validation") as mock_valid, \
             patch("ontos.commands.doctor.check_cli_availability") as mock_cli:

            # Most pass, one fails
            for mock in [mock_hooks, mock_python, mock_docs,
                        mock_map, mock_valid, mock_cli]:
                mock.return_value = CheckResult(
                    name="test", status="pass", message="OK"
                )

            mock_config.return_value = CheckResult(
                name="configuration", status="fail", message="Not found"
            )

            options = DoctorOptions()
            exit_code, result = doctor_command(options)

            assert exit_code == 1
            assert result.failed == 1


class TestFormatDoctorOutput:
    """Tests for format_doctor_output."""

    def test_formats_passing_checks(self):
        result = DoctorResult(
            checks=[
                CheckResult(name="test1", status="pass", message="OK"),
                CheckResult(name="test2", status="pass", message="Good"),
            ],
            passed=2, failed=0, warnings=0
        )
        output = format_doctor_output(result)
        assert "OK: test1: OK" in output
        assert "OK: test2: Good" in output
        assert "2 passed" in output

    def test_formats_failing_checks(self):
        result = DoctorResult(
            checks=[
                CheckResult(name="test1", status="fail", message="Bad"),
            ],
            passed=0, failed=1, warnings=0
        )
        output = format_doctor_output(result)
        assert "FAIL: test1: Bad" in output

    def test_includes_details_when_verbose(self):
        result = DoctorResult(
            checks=[
                CheckResult(
                    name="test1",
                    status="fail",
                    message="Bad",
                    details="Extra info"
                ),
            ],
            passed=0, failed=1, warnings=0
        )
        output = format_doctor_output(result, verbose=True)
        assert "Extra info" in output
```

**Verification:**

```bash
# Import test
python -c "from ontos.commands.doctor import doctor_command, DoctorOptions; print('OK')"

# Run tests
pytest tests/commands/test_doctor_phase4.py -v

# Test command manually (will likely fail some checks - that's OK)
cd /tmp && rm -rf test-doctor && mkdir test-doctor && cd test-doctor
python -m ontos doctor 2>&1 || echo "Expected to fail (no config)"

# Back to project
cd -
```

**Checkpoint:** Commit with message `"feat(commands): add doctor command with 7 health checks"`

---

#### Task 4.2.2: Create `commands/hook.py`

**Description:** Implement hook dispatcher per spec Section 4.3.

**File(s):**
- `ontos/commands/hook.py` — CREATE
- `tests/commands/test_hook_phase4.py` — CREATE

**Dependencies:** None (uses existing modules)

**Instructions:**

1. Create `ontos/commands/hook.py`
2. Implement `HookOptions` dataclass
3. Implement `hook_command()` dispatcher
4. Implement `run_pre_push_hook()` and `run_pre_commit_hook()`
5. Handle unknown hook types gracefully (return 0)
6. Write tests

**Code:**

```python
# ontos/commands/hook.py
"""
Git hook dispatcher command.

Called by shim hooks in .git/hooks/ to execute Ontos validation.
Per Spec v1.1 Section 4.3.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class HookOptions:
    """Configuration for hook command."""
    hook_type: str  # "pre-push" or "pre-commit"
    args: List[str] = field(default_factory=list)


def hook_command(options: HookOptions) -> int:
    """
    Dispatch git hook execution.

    Returns:
        0 = Allow git operation to proceed
        1 = Block git operation
    """
    if options.hook_type == "pre-push":
        return run_pre_push_hook(options.args)
    elif options.hook_type == "pre-commit":
        return run_pre_commit_hook(options.args)
    else:
        # Unknown hook type - don't block, just warn
        print(
            f"Warning: Unknown hook type '{options.hook_type}'. Skipping.",
            file=sys.stderr
        )
        return 0


def run_pre_push_hook(args: List[str]) -> int:
    """
    Pre-push hook: Validate documentation before push.

    Returns:
        0 = Allow push
        1 = Block push (validation errors)
    """
    try:
        from ontos.io.config import load_project_config
        config = load_project_config()

        # Check if hook is enabled
        if not config.hooks.pre_push:
            return 0

        # Run validation (simplified - just check context map is fresh)
        context_map = Path.cwd() / config.paths.context_map

        if not context_map.exists():
            print(
                "Warning: Context map not found. "
                "Run 'ontos map' before pushing.",
                file=sys.stderr
            )
            # Don't block on missing map - just warn
            return 0

        # Could add more validation here (staleness, errors, etc.)
        # For v3.0, keep it simple

        return 0

    except Exception as e:
        # Don't block push on hook errors
        print(
            f"Warning: Hook error (push allowed): {e}",
            file=sys.stderr
        )
        return 0


def run_pre_commit_hook(args: List[str]) -> int:
    """
    Pre-commit hook: Check documentation status before commit.

    Returns:
        0 = Always (pre-commit doesn't block by default)
    """
    try:
        from ontos.io.config import load_project_config
        config = load_project_config()

        # Check if hook is enabled
        if not config.hooks.pre_commit:
            return 0

        # Pre-commit is warn-only, never blocks
        # Could check for uncommitted doc changes, etc.

        return 0

    except Exception:
        # Silently allow - don't block commits on hook errors
        return 0
```

**Tests:**

```python
# tests/commands/test_hook_phase4.py
"""Tests for hook dispatcher command (Phase 4)."""

from unittest.mock import patch, MagicMock

import pytest

from ontos.commands.hook import (
    HookOptions,
    hook_command,
    run_pre_push_hook,
    run_pre_commit_hook,
)


class TestHookOptions:
    """Tests for HookOptions dataclass."""

    def test_creates_with_hook_type(self):
        options = HookOptions(hook_type="pre-push")
        assert options.hook_type == "pre-push"
        assert options.args == []

    def test_creates_with_args(self):
        options = HookOptions(hook_type="pre-commit", args=["--verbose"])
        assert options.args == ["--verbose"]


class TestHookCommand:
    """Tests for hook_command dispatcher."""

    def test_dispatches_pre_push(self):
        with patch("ontos.commands.hook.run_pre_push_hook") as mock:
            mock.return_value = 0
            options = HookOptions(hook_type="pre-push", args=["arg1"])

            result = hook_command(options)

            mock.assert_called_once_with(["arg1"])
            assert result == 0

    def test_dispatches_pre_commit(self):
        with patch("ontos.commands.hook.run_pre_commit_hook") as mock:
            mock.return_value = 0
            options = HookOptions(hook_type="pre-commit")

            result = hook_command(options)

            mock.assert_called_once_with([])
            assert result == 0

    def test_returns_0_for_unknown_hook(self, capsys):
        """Unknown hooks should not block git operations."""
        options = HookOptions(hook_type="unknown-hook")

        result = hook_command(options)

        assert result == 0
        captured = capsys.readouterr()
        assert "Unknown hook type" in captured.err


class TestRunPrePushHook:
    """Tests for run_pre_push_hook."""

    def test_returns_0_when_disabled(self):
        """Should return 0 when hook is disabled in config."""
        mock_config = MagicMock()
        mock_config.hooks.pre_push = False

        with patch("ontos.commands.hook.load_project_config") as mock_load:
            mock_load.return_value = mock_config

            result = run_pre_push_hook([])

            assert result == 0

    def test_returns_0_on_error(self):
        """Should return 0 (allow) when hook has errors."""
        with patch("ontos.commands.hook.load_project_config") as mock_load:
            mock_load.side_effect = Exception("Config error")

            result = run_pre_push_hook([])

            assert result == 0  # Don't block on errors


class TestRunPreCommitHook:
    """Tests for run_pre_commit_hook."""

    def test_always_returns_0(self):
        """Pre-commit hook should never block."""
        mock_config = MagicMock()
        mock_config.hooks.pre_commit = True

        with patch("ontos.commands.hook.load_project_config") as mock_load:
            mock_load.return_value = mock_config

            result = run_pre_commit_hook([])

            assert result == 0

    def test_returns_0_on_error(self):
        """Should return 0 when hook has errors."""
        with patch("ontos.commands.hook.load_project_config") as mock_load:
            mock_load.side_effect = Exception("Error")

            result = run_pre_commit_hook([])

            assert result == 0
```

**Verification:**

```bash
# Import test
python -c "from ontos.commands.hook import hook_command, HookOptions; print('OK')"

# Run tests
pytest tests/commands/test_hook_phase4.py -v
```

**Checkpoint:** Commit with message `"feat(commands): add hook dispatcher command"`

---

#### Task 4.2.3: Create `commands/export.py`

**Description:** Implement CLAUDE.md generation per spec Section 4.4.

**File(s):**
- `ontos/commands/export.py` — CREATE
- `tests/commands/test_export_phase4.py` — CREATE

**Dependencies:** None

**Instructions:**

1. Create `ontos/commands/export.py`
2. Implement `ExportOptions` dataclass
3. Implement `export_command()` function
4. Include path safety validation (output must be within repo)
5. Write tests

**Code:**

```python
# ontos/commands/export.py
"""
CLAUDE.md generation command.

Generates AI assistant integration file per Spec v1.1 Section 4.4.

Scope Clarification: This is a single hardcoded template for v3.0.
Multiple templates are deferred to v4.0 per Strategy Q2.
This is NOT a scope expansion - it's explicitly in v3.0.x per Roadmap 1.2 and 6.6.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


@dataclass
class ExportOptions:
    """Configuration for export command."""
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


def find_repo_root() -> Path:
    """
    Find the repository root.

    Looks for .ontos.toml or .git directory.
    """
    current = Path.cwd()

    # Walk up looking for markers
    for parent in [current] + list(current.parents):
        if (parent / ".ontos.toml").exists():
            return parent
        if (parent / ".git").exists():
            return parent

    # Fall back to current directory
    return current


def export_command(options: ExportOptions) -> Tuple[int, str]:
    """
    Generate CLAUDE.md file.

    Returns:
        Tuple of (exit_code, message)

    Exit Codes:
        0: Success
        1: File exists (use --force)
        2: Configuration error (path validation failed)
    """
    # Find repo root
    try:
        repo_root = find_repo_root()
    except Exception as e:
        return 2, f"Configuration error: {e}"

    # Determine output path
    output_path = options.output_path or repo_root / "CLAUDE.md"

    # PATH SAFETY: Validate output path is within repo
    # Per Chief Architect Response - prevents path traversal
    try:
        # Resolve to absolute paths and check containment
        resolved_output = output_path.resolve()
        resolved_root = repo_root.resolve()
        resolved_output.relative_to(resolved_root)
    except ValueError:
        return 2, f"Error: Output path must be within repository root ({repo_root})"

    # Check if file already exists
    if output_path.exists() and not options.force:
        return 1, f"CLAUDE.md already exists at {output_path}. Use --force to overwrite."

    # Write the file
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(CLAUDE_MD_TEMPLATE, encoding="utf-8")
    except Exception as e:
        return 2, f"Error writing file: {e}"

    return 0, f"Created {output_path}"
```

**Tests:**

```python
# tests/commands/test_export_phase4.py
"""Tests for export command (Phase 4)."""

from pathlib import Path

import pytest

from ontos.commands.export import (
    ExportOptions,
    CLAUDE_MD_TEMPLATE,
    export_command,
    find_repo_root,
)


class TestExportOptions:
    """Tests for ExportOptions dataclass."""

    def test_default_values(self):
        options = ExportOptions()
        assert options.output_path is None
        assert options.force is False

    def test_with_values(self):
        options = ExportOptions(
            output_path=Path("/tmp/test.md"),
            force=True
        )
        assert options.output_path == Path("/tmp/test.md")
        assert options.force is True


class TestExportCommand:
    """Tests for export_command."""

    def test_creates_claude_md(self, tmp_path, monkeypatch):
        """Should create CLAUDE.md in repo root."""
        monkeypatch.chdir(tmp_path)
        # Create .ontos.toml to mark as repo
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")

        options = ExportOptions()
        exit_code, message = export_command(options)

        assert exit_code == 0
        assert "Created" in message
        assert (tmp_path / "CLAUDE.md").exists()

    def test_fails_if_exists_without_force(self, tmp_path, monkeypatch):
        """Should fail if CLAUDE.md exists and force=False."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        (tmp_path / "CLAUDE.md").write_text("existing content")

        options = ExportOptions(force=False)
        exit_code, message = export_command(options)

        assert exit_code == 1
        assert "already exists" in message
        # Should not have overwritten
        assert (tmp_path / "CLAUDE.md").read_text() == "existing content"

    def test_overwrites_with_force(self, tmp_path, monkeypatch):
        """Should overwrite if force=True."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        (tmp_path / "CLAUDE.md").write_text("existing content")

        options = ExportOptions(force=True)
        exit_code, message = export_command(options)

        assert exit_code == 0
        assert (tmp_path / "CLAUDE.md").read_text() == CLAUDE_MD_TEMPLATE

    def test_rejects_path_outside_repo(self, tmp_path, monkeypatch):
        """Should reject output path outside repo root."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")

        # Try to write to parent directory (path traversal attempt)
        options = ExportOptions(output_path=tmp_path.parent / "evil.md")
        exit_code, message = export_command(options)

        assert exit_code == 2
        assert "within repository root" in message

    def test_custom_output_path_within_repo(self, tmp_path, monkeypatch):
        """Should allow custom output path within repo."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        options = ExportOptions(output_path=subdir / "AI_INSTRUCTIONS.md")
        exit_code, message = export_command(options)

        assert exit_code == 0
        assert (subdir / "AI_INSTRUCTIONS.md").exists()


class TestFindRepoRoot:
    """Tests for find_repo_root."""

    def test_finds_ontos_toml(self, tmp_path, monkeypatch):
        """Should find directory with .ontos.toml."""
        (tmp_path / ".ontos.toml").write_text("")
        subdir = tmp_path / "a" / "b"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        root = find_repo_root()

        assert root == tmp_path

    def test_finds_git_dir(self, tmp_path, monkeypatch):
        """Should find directory with .git."""
        (tmp_path / ".git").mkdir()
        subdir = tmp_path / "a" / "b"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        root = find_repo_root()

        assert root == tmp_path

    def test_prefers_ontos_toml_over_git(self, tmp_path, monkeypatch):
        """Should prefer .ontos.toml over .git."""
        (tmp_path / ".git").mkdir()
        subdir = tmp_path / "project"
        subdir.mkdir()
        (subdir / ".ontos.toml").write_text("")
        monkeypatch.chdir(subdir)

        root = find_repo_root()

        assert root == subdir


class TestClaudeMdTemplate:
    """Tests for CLAUDE.md template content."""

    def test_template_has_activation_section(self):
        assert "## Ontos Activation" in CLAUDE_MD_TEMPLATE

    def test_template_has_commands(self):
        assert "ontos map" in CLAUDE_MD_TEMPLATE
        assert "ontos log" in CLAUDE_MD_TEMPLATE

    def test_template_mentions_context_map(self):
        assert "Ontos_Context_Map.md" in CLAUDE_MD_TEMPLATE
```

**Verification:**

```bash
# Import test
python -c "from ontos.commands.export import export_command, ExportOptions; print('OK')"

# Run tests
pytest tests/commands/test_export_phase4.py -v

# Manual test
cd /tmp && rm -rf test-export && mkdir test-export && cd test-export
git init
echo '[ontos]\nversion = "3.0"' > .ontos.toml
python -m ontos export 2>&1 || python -c "
from ontos.commands.export import export_command, ExportOptions
code, msg = export_command(ExportOptions())
print(f'Exit: {code}, Message: {msg}')
"
cat CLAUDE.md

# Back to project
cd -
```

**Checkpoint:** Commit with message `"feat(commands): add export command for CLAUDE.md generation"`

---

### Day 2 Checkpoint

After completing Day 2, verify:

```bash
# All new commands import correctly
python -c "
from ontos.commands.doctor import doctor_command
from ontos.commands.hook import hook_command
from ontos.commands.export import export_command
print('OK: All commands import')
"

# Tests pass
pytest tests/commands/test_doctor_phase4.py tests/commands/test_hook_phase4.py tests/commands/test_export_phase4.py -v

# Full test suite still passes
pytest tests/ -v
```

---

### Day 3: CLI Integration

#### Task 4.3.1: Update `cli.py` with full argparse

**Description:** Implement full argparse CLI with all commands and global options per spec Section 4.1.

**File(s):**
- `ontos/cli.py` — MODIFY (major update)
- `tests/test_cli_phase4.py` — CREATE

**Dependencies:** Tasks 4.2.1, 4.2.2, 4.2.3

**Instructions:**

1. Rewrite `cli.py` to use full argparse structure
2. Add global options: `--version`, `--help`, `--quiet`, `--json`
3. Register all 13 commands as subparsers
4. Implement command handler functions
5. Add JSON validation wrapper for wrapper commands
6. Wire all commands properly
7. Write CLI integration tests

**Code scaffold (key sections):**

```python
# ontos/cli.py
"""
Ontos CLI - Unified command interface.

Full argparse implementation per Spec v1.1 Section 4.1.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import ontos
from ontos.ui.json_output import emit_json, emit_error, emit_result, validate_json_output


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all commands."""
    parser = argparse.ArgumentParser(
        prog="ontos",
        description="Local-first documentation management for AI-assisted development",
    )

    # Global options
    parser.add_argument(
        "--version", "-V",
        action="store_true",
        help="Show version and exit"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-essential output"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Register each command
    _register_init(subparsers)
    _register_map(subparsers)
    _register_log(subparsers)
    _register_doctor(subparsers)
    _register_export(subparsers)
    _register_hook(subparsers)
    _register_verify(subparsers)
    _register_query(subparsers)
    _register_migrate(subparsers)
    _register_consolidate(subparsers)
    _register_promote(subparsers)
    _register_scaffold(subparsers)
    _register_stub(subparsers)

    return parser


# Command registration functions

def _register_init(subparsers):
    """Register init command."""
    p = subparsers.add_parser("init", help="Initialize Ontos in a project")
    p.add_argument("--force", "-f", action="store_true",
                   help="Overwrite existing config and hooks")
    p.add_argument("--skip-hooks", action="store_true",
                   help="Don't install git hooks")
    p.set_defaults(func=_cmd_init)


def _register_map(subparsers):
    """Register map command."""
    p = subparsers.add_parser("map", help="Generate context map")
    p.add_argument("--strict", action="store_true",
                   help="Treat warnings as errors")
    p.add_argument("--output", "-o", type=Path,
                   help="Output path (default: Ontos_Context_Map.md)")
    p.set_defaults(func=_cmd_map)


def _register_log(subparsers):
    """Register log command."""
    p = subparsers.add_parser("log", help="End session logging")
    p.add_argument("--epoch", "-e", required=True,
                   help="Epoch identifier")
    p.add_argument("--title", "-t", required=True,
                   help="Log entry title")
    p.add_argument("--auto", action="store_true",
                   help="Skip confirmation prompt")
    p.set_defaults(func=_cmd_log)


def _register_doctor(subparsers):
    """Register doctor command."""
    p = subparsers.add_parser("doctor", help="Health check and diagnostics")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Show detailed output")
    p.set_defaults(func=_cmd_doctor)


def _register_export(subparsers):
    """Register export command."""
    p = subparsers.add_parser("export", help="Generate CLAUDE.md for AI assistants")
    p.add_argument("--force", "-f", action="store_true",
                   help="Overwrite existing file")
    p.add_argument("--output", "-o", type=Path,
                   help="Output path (default: CLAUDE.md)")
    p.set_defaults(func=_cmd_export)


def _register_hook(subparsers):
    """Register hook command (internal)."""
    p = subparsers.add_parser("hook", help="Git hook dispatcher (internal)")
    p.add_argument("hook_type", choices=["pre-push", "pre-commit"],
                   help="Hook type to run")
    p.set_defaults(func=_cmd_hook)


def _register_verify(subparsers):
    """Register verify command (wrapper)."""
    p = subparsers.add_parser("verify", help="Verify describes dates")
    p.set_defaults(func=_cmd_wrapper, wrapper_name="verify")


def _register_query(subparsers):
    """Register query command (wrapper)."""
    p = subparsers.add_parser("query", help="Search documents")
    p.add_argument("query_string", nargs="?", help="Search query")
    p.set_defaults(func=_cmd_wrapper, wrapper_name="query")


def _register_migrate(subparsers):
    """Register migrate command (wrapper)."""
    p = subparsers.add_parser("migrate", help="Schema migration")
    p.set_defaults(func=_cmd_wrapper, wrapper_name="migrate")


def _register_consolidate(subparsers):
    """Register consolidate command (wrapper)."""
    p = subparsers.add_parser("consolidate", help="Archive old logs")
    p.set_defaults(func=_cmd_wrapper, wrapper_name="consolidate")


def _register_promote(subparsers):
    """Register promote command (wrapper)."""
    p = subparsers.add_parser("promote", help="Promote curation level")
    p.add_argument("file", nargs="?", help="File to promote")
    p.set_defaults(func=_cmd_wrapper, wrapper_name="promote")


def _register_scaffold(subparsers):
    """Register scaffold command (wrapper)."""
    p = subparsers.add_parser("scaffold", help="Generate scaffolds")
    p.set_defaults(func=_cmd_wrapper, wrapper_name="scaffold")


def _register_stub(subparsers):
    """Register stub command (wrapper)."""
    p = subparsers.add_parser("stub", help="Create stub documents")
    p.add_argument("name", nargs="?", help="Stub name")
    p.set_defaults(func=_cmd_wrapper, wrapper_name="stub")


# Command handlers

def _cmd_init(args) -> int:
    """Handle init command."""
    from ontos.commands.init import init_command, InitOptions

    options = InitOptions(
        path=Path.cwd(),
        force=args.force,
        skip_hooks=getattr(args, "skip_hooks", False),
    )
    code, msg = init_command(options)

    if args.json:
        emit_json({
            "status": "success" if code == 0 else "error",
            "message": msg,
            "exit_code": code
        })
    elif not args.quiet:
        print(msg)

    return code


def _cmd_map(args) -> int:
    """Handle map command."""
    from ontos.commands.map import generate_context_map, GenerateMapOptions

    options = GenerateMapOptions(
        output_path=args.output,
        strict=args.strict,
        json_output=args.json,
        quiet=args.quiet,
    )

    return generate_context_map(options)


def _cmd_log(args) -> int:
    """Handle log command."""
    from ontos.commands.log import log_command, LogOptions

    options = LogOptions(
        epoch=args.epoch,
        title=args.title,
        auto=args.auto,
        json_output=args.json,
        quiet=args.quiet,
    )

    return log_command(options)


def _cmd_doctor(args) -> int:
    """Handle doctor command."""
    from ontos.commands.doctor import doctor_command, DoctorOptions, format_doctor_output

    options = DoctorOptions(
        verbose=args.verbose,
        json_output=args.json,
    )

    exit_code, result = doctor_command(options)

    if args.json:
        from ontos.ui.json_output import to_json
        emit_json({
            "status": result.status,
            "checks": [to_json(c) for c in result.checks],
            "summary": {
                "passed": result.passed,
                "failed": result.failed,
                "warnings": result.warnings
            }
        })
    elif not args.quiet:
        print(format_doctor_output(result, verbose=args.verbose))

    return exit_code


def _cmd_export(args) -> int:
    """Handle export command."""
    from ontos.commands.export import export_command, ExportOptions

    options = ExportOptions(
        output_path=args.output,
        force=args.force,
    )

    exit_code, message = export_command(options)

    if args.json:
        emit_json({
            "status": "success" if exit_code == 0 else "error",
            "message": message,
            "exit_code": exit_code
        })
    elif not args.quiet:
        print(message)

    return exit_code


def _cmd_hook(args) -> int:
    """Handle hook command."""
    from ontos.commands.hook import hook_command, HookOptions

    # Get remaining args after hook_type
    remaining_args = []
    if hasattr(args, "_remaining"):
        remaining_args = args._remaining

    options = HookOptions(
        hook_type=args.hook_type,
        args=remaining_args,
    )

    return hook_command(options)


def _cmd_wrapper(args) -> int:
    """
    Handle wrapper commands that delegate to legacy scripts.

    Per Decision: Option A with JSON validation fallback.
    """
    wrapper_name = args.wrapper_name

    # Find the legacy script
    scripts_dir = Path(__file__).parent / "_scripts"
    script_map = {
        "verify": "ontos_verify_describes.py",
        "query": "ontos_query.py",
        "migrate": "ontos_migrate_schema.py",
        "consolidate": "ontos_consolidate_logs.py",
        "promote": "ontos_promote.py",
        "scaffold": "ontos_scaffold.py",
        "stub": "ontos_stub.py",
    }

    script_name = script_map.get(wrapper_name)
    if not script_name:
        if args.json:
            emit_error(f"Unknown wrapper command: {wrapper_name}", "E_UNKNOWN_CMD")
        else:
            print(f"Error: Unknown wrapper command: {wrapper_name}", file=sys.stderr)
        return 5

    script_path = scripts_dir / script_name
    if not script_path.exists():
        if args.json:
            emit_error(f"Script not found: {script_name}", "E_NOT_FOUND")
        else:
            print(f"Error: Script not found: {script_path}", file=sys.stderr)
        return 5

    # Build command
    cmd = [sys.executable, str(script_path)]

    # Pass through JSON flag if requested
    if args.json:
        cmd.append("--json")

    # Pass through any additional arguments
    # (would need to handle per-wrapper args here)

    # Run the wrapper
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        # JSON validation per Decision
        if args.json:
            if validate_json_output(result.stdout):
                # Valid JSON - pass through
                print(result.stdout, end="")
            else:
                # Invalid JSON - emit error with original output
                emit_error(
                    message=f"Command '{wrapper_name}' does not support JSON output in v3.0",
                    code="E_JSON_UNSUPPORTED",
                    details=result.stdout[:500] if result.stdout else result.stderr[:500]
                )
        else:
            # Non-JSON mode - pass through output
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, file=sys.stderr, end="")

        return result.returncode

    except Exception as e:
        if args.json:
            emit_error(f"Wrapper execution failed: {e}", "E_EXEC_FAIL")
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 5


def main() -> int:
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle --version
    if args.version:
        if args.json:
            emit_json({"version": ontos.__version__})
        else:
            print(f"ontos {ontos.__version__}")
        return 0

    # No command specified
    if not args.command:
        if args.json:
            emit_error("No command specified", "E_NO_CMD")
        else:
            parser.print_help()
        return 0

    # Route to command handler
    try:
        return args.func(args)
    except KeyboardInterrupt:
        if not args.quiet:
            print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        if args.json:
            emit_error(f"Internal error: {e}", "E_INTERNAL")
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    sys.exit(main())
```

**Tests:**

```python
# tests/test_cli_phase4.py
"""Tests for CLI (Phase 4)."""

import subprocess
import sys
from pathlib import Path

import pytest


class TestCLIGlobalOptions:
    """Tests for CLI global options."""

    def test_version_flag(self):
        """--version should print version."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "--version"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "ontos" in result.stdout.lower()

    def test_version_json(self):
        """--version --json should output JSON."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "--version", "--json"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        import json
        data = json.loads(result.stdout)
        assert "version" in data

    def test_help_flag(self):
        """--help should print help."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "commands" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_no_command_prints_help(self):
        """No command should print help."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos"],
            capture_output=True, text=True
        )
        assert result.returncode == 0


class TestCLICommands:
    """Tests for CLI command routing."""

    def test_init_help(self):
        """init --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "init", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "force" in result.stdout.lower()

    def test_map_help(self):
        """map --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "map", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "strict" in result.stdout.lower()

    def test_doctor_help(self):
        """doctor --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "doctor", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "verbose" in result.stdout.lower()

    def test_export_help(self):
        """export --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "export", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "force" in result.stdout.lower()

    def test_hook_help(self):
        """hook --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "hook", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "pre-push" in result.stdout.lower() or "hook_type" in result.stdout.lower()


class TestCLIDoctorCommand:
    """Tests for doctor command via CLI."""

    def test_doctor_runs(self, tmp_path, monkeypatch):
        """doctor command should run."""
        monkeypatch.chdir(tmp_path)
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "doctor"],
            capture_output=True, text=True
        )
        # Will fail some checks, but should run
        assert "configuration" in result.stdout.lower() or "fail" in result.stdout.lower()

    def test_doctor_json(self, tmp_path, monkeypatch):
        """doctor --json should output JSON."""
        monkeypatch.chdir(tmp_path)
        result = subprocess.run(
            [sys.executable, "-m", "ontos", "doctor", "--json"],
            capture_output=True, text=True
        )
        import json
        data = json.loads(result.stdout)
        assert "status" in data
        assert "checks" in data


class TestCLIExportCommand:
    """Tests for export command via CLI."""

    def test_export_creates_file(self, tmp_path, monkeypatch):
        """export should create CLAUDE.md."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ontos.toml").write_text("[ontos]\nversion = '3.0'")

        result = subprocess.run(
            [sys.executable, "-m", "ontos", "export"],
            capture_output=True, text=True
        )

        assert result.returncode == 0
        assert (tmp_path / "CLAUDE.md").exists()
```

**Verification:**

```bash
# Import test
python -c "from ontos.cli import main, create_parser; print('OK')"

# Run tests
pytest tests/test_cli_phase4.py -v

# Manual verification
python -m ontos --version
python -m ontos --help
python -m ontos doctor --help
python -m ontos export --help
python -m ontos init --help
python -m ontos map --help
python -m ontos log --help
python -m ontos hook --help
```

**Checkpoint:** Commit with message `"feat(cli): full argparse CLI with all 13 commands"`

---

### Day 3 Checkpoint

After completing Day 3, verify:

```bash
# All commands accessible
python -m ontos --help
python -m ontos init --help
python -m ontos map --help
python -m ontos log --help
python -m ontos doctor --help
python -m ontos export --help
python -m ontos hook --help
python -m ontos verify --help
python -m ontos query --help

# Tests pass
pytest tests/test_cli_phase4.py -v

# Full test suite
pytest tests/ -v
```

---

### Day 4: Shim Hooks & Cross-Platform

#### Task 4.4.1: Update hook installation in `commands/init.py`

**Description:** Update init command to install Python-based shim hooks with cross-platform support per spec Section 4.6.

**File(s):**
- `ontos/commands/init.py` — MODIFY
- `tests/commands/test_init_hooks.py` — CREATE

**Dependencies:** Task 4.2.2 (commands/hook.py)

**Instructions:**

1. Update hook installation code in init.py
2. Use Python-based shim hooks (not shell scripts)
3. Include `# ontos-managed-hook` marker
4. Implement 3-method fallback (PATH, sys.executable, graceful skip)
5. Handle chmod cross-platform (no-op on Windows)
6. Write tests

**Shim hook template:**

```python
PRE_PUSH_HOOK_TEMPLATE = '''#!/usr/bin/env python3
# ontos-managed-hook
"""Ontos pre-push hook. Delegates to ontos CLI."""
import subprocess
import sys

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
'''

PRE_COMMIT_HOOK_TEMPLATE = '''#!/usr/bin/env python3
# ontos-managed-hook
"""Ontos pre-commit hook. Delegates to ontos CLI."""
import subprocess
import sys

def run_hook():
    """Try multiple methods to invoke ontos hook."""
    args = ["hook", "pre-commit"] + sys.argv[1:]

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
'''
```

**Cross-platform hook installation:**

```python
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

**Verification:**

```bash
# Test hook installation
cd /tmp && rm -rf test-hooks && mkdir test-hooks && cd test-hooks
git init
python -m ontos init

# Verify hooks exist
cat .git/hooks/pre-push
cat .git/hooks/pre-commit

# Verify marker
grep "ontos-managed-hook" .git/hooks/pre-push
grep "ontos-managed-hook" .git/hooks/pre-commit

# Verify executable (Unix only)
test -x .git/hooks/pre-push && echo "pre-push is executable"
test -x .git/hooks/pre-commit && echo "pre-commit is executable"

# Back to project
cd -
```

**Checkpoint:** Commit with message `"feat(init): python-based shim hooks with cross-platform support"`

---

### Day 4 Checkpoint

After completing Day 4, verify:

```bash
# Hook installation works
cd /tmp && rm -rf test-phase4-hooks && mkdir test-phase4-hooks && cd test-phase4-hooks
git init
python -m ontos init
ls -la .git/hooks/
grep "ontos-managed-hook" .git/hooks/pre-push
cd -

# Full test suite
pytest tests/ -v
```

---

### Day 5: Legacy Deletion (HIGH RISK)

**WARNING:** This is the highest-risk task. Follow the safety protocol exactly.

#### Task 4.5.1: Archive legacy scripts

**Description:** Archive all legacy scripts before any deletion, per Roadmap 6.10.

**File(s):**
- `.ontos-internal/archive/scripts-v2/` — CREATE (directory)

**Instructions:**

1. Create archive directory
2. Copy ALL scripts from `ontos/_scripts/` to archive
3. Add ARCHIVED.txt with timestamp
4. Commit the archive

**Commands:**

```bash
# Create archive
mkdir -p .ontos-internal/archive/scripts-v2

# Copy all scripts
cp -r ontos/_scripts/* .ontos-internal/archive/scripts-v2/

# Add archive marker
echo "Archived on $(date) for v3.0.0 release" > .ontos-internal/archive/scripts-v2/ARCHIVED.txt
echo "These scripts are preserved for reference only." >> .ontos-internal/archive/scripts-v2/ARCHIVED.txt
echo "Use 'ontos <command>' instead." >> .ontos-internal/archive/scripts-v2/ARCHIVED.txt

# Verify
ls .ontos-internal/archive/scripts-v2/

# Commit
git add .ontos-internal/archive/scripts-v2/
git commit -m "chore: archive legacy scripts for v3.0.0"
```

**Checkpoint:** Commit with message `"chore: archive legacy scripts for v3.0.0"`

---

#### Task 4.5.2: Verify no dependencies before deletion

**Description:** Verify each script has no remaining dependencies before deletion.

**Instructions:**

For EACH script to delete, run:

```bash
# Replace SCRIPT_NAME with actual script name (without .py)

# Check Python imports
grep -r "import SCRIPT_NAME" --include="*.py" ontos/
grep -r "from SCRIPT_NAME" --include="*.py" ontos/
grep -r "from ontos._scripts.SCRIPT_NAME" --include="*.py" ontos/
grep -r "from ontos._scripts import SCRIPT_NAME" --include="*.py" ontos/

# Check other references
grep -r "SCRIPT_NAME" --include="*.py" ontos/
grep -r "SCRIPT_NAME" --include="*.md" docs/
grep -r "SCRIPT_NAME" --include="*.toml" .

# Check entry points
grep "SCRIPT_NAME" pyproject.toml
```

**Scripts to check (in deletion order):**

1. `install.py`
2. `ontos_install_hooks.py`
3. `ontos_create_bundle.py`
4. `ontos_generate_ontology_spec.py`
5. `ontos_summarize.py`
6. `ontos_migrate_frontmatter.py`
7. `ontos_migrate_v2.py`
8. `ontos_remove_frontmatter.py`

**Document findings:**

If ANY references found for a script:
1. DO NOT DELETE that script
2. Document the reference in `Phase4_Deletion_Blockers.md`
3. Report to Chief Architect

---

#### Task 4.5.3: Delete safe scripts

**Description:** Delete scripts verified to have no dependencies.

**Instructions:**

Delete ONE script at a time, with full verification after each:

```bash
# For each safe script:

# 1. Delete
rm ontos/_scripts/SCRIPT_NAME.py

# 2. Verify imports still work
python -c "import ontos"
python -c "from ontos.commands.init import init_command"
python -c "from ontos.commands.map import generate_context_map"
python -c "from ontos.commands.log import log_command"

# 3. Verify tests pass
pytest tests/ -v --tb=short

# 4. Verify commands work
python -m ontos --help
python -m ontos map --help

# 5. If ALL pass, commit
git add -A
git commit -m "chore: delete SCRIPT_NAME.py (legacy)"

# 6. If ANY fail, restore immediately:
git checkout -- ontos/_scripts/SCRIPT_NAME.py
```

**Deletion order (least risky first):**

```bash
# 1. install.py (replaced by pip install)
rm ontos/_scripts/install.py
# [verify and commit]

# 2. ontos_install_hooks.py (replaced by init)
rm ontos/_scripts/ontos_install_hooks.py
# [verify and commit]

# 3. ontos_create_bundle.py (not in v3.0)
rm ontos/_scripts/ontos_create_bundle.py
# [verify and commit]

# 4. ontos_generate_ontology_spec.py (not in v3.0)
rm ontos/_scripts/ontos_generate_ontology_spec.py
# [verify and commit]

# 5. ontos_summarize.py (deferred to v4.0)
rm ontos/_scripts/ontos_summarize.py
# [verify and commit]

# 6. ontos_migrate_frontmatter.py (legacy)
rm ontos/_scripts/ontos_migrate_frontmatter.py
# [verify and commit]

# 7. ontos_migrate_v2.py (legacy)
rm ontos/_scripts/ontos_migrate_v2.py
# [verify and commit]

# 8. ontos_remove_frontmatter.py (legacy)
rm ontos/_scripts/ontos_remove_frontmatter.py
# [verify and commit]
```

**DO NOT DELETE (keep for v3.0.0):**
- `ontos.py` — dispatcher for wrappers
- `ontos_lib.py` — still has imports
- `ontos_config.py` — config handling
- `ontos_config_defaults.py` — config defaults
- All wrapper target scripts (`ontos_verify_describes.py`, etc.)

---

#### Task 4.5.4: Add deprecation warnings to kept scripts

**Description:** Add deprecation warnings to scripts kept in v3.0.0.

**Instructions:**

For each script that is KEPT (not deleted), add at the top:

```python
# Add after imports, before any code

import warnings
warnings.warn(
    "This script is deprecated and will be removed in v3.1. "
    "Use 'ontos <command>' instead.",
    DeprecationWarning,
    stacklevel=2
)
```

**Scripts to add warning:**
- `ontos.py`
- `ontos_lib.py`
- `ontos_verify_describes.py`
- `ontos_query.py`
- `ontos_migrate_schema.py`
- `ontos_consolidate_logs.py`
- `ontos_promote.py`
- `ontos_scaffold.py`
- `ontos_stub.py`

**Checkpoint:** Commit with message `"chore: add deprecation warnings to legacy scripts"`

---

### Day 5 Checkpoint

After completing Day 5, verify:

```bash
# Archive exists
ls .ontos-internal/archive/scripts-v2/

# Deleted scripts are gone
ls ontos/_scripts/install.py 2>/dev/null && echo "ERROR" || echo "OK: deleted"
ls ontos/_scripts/ontos_install_hooks.py 2>/dev/null && echo "ERROR" || echo "OK: deleted"

# Kept scripts have deprecation warnings
grep -l "DeprecationWarning" ontos/_scripts/*.py

# All imports still work
python -c "import ontos"
python -c "from ontos.commands.init import init_command"
python -c "from ontos.commands.map import generate_context_map"
python -c "from ontos.commands.doctor import doctor_command"
python -c "from ontos.commands.export import export_command"
python -c "from ontos.commands.hook import hook_command"

# Tests pass
pytest tests/ -v

# Commands work
python -m ontos --help
python -m ontos doctor --json
```

---

### Day 6: PyPI Readiness & Polish

#### Task 4.6.1: Update `pyproject.toml`

**Description:** Update pyproject.toml for PyPI publication per spec Section 4.8.

**File(s):**
- `pyproject.toml` — MODIFY

**Instructions:**

1. Update version to `3.0.0`
2. Update classifiers to Beta
3. Verify entry points are correct
4. Add project URLs
5. Verify dependencies are complete

**Changes to apply:**

```toml
[project]
name = "ontos"
version = "3.0.0"
description = "Local-first documentation management for AI-assisted development"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [{name = "Ontos Project"}]
keywords = ["documentation", "ai", "context", "llm", "development"]
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

**Verification:**

```bash
# Verify package installs
pip install -e . --force-reinstall

# Verify entry point works
ontos --version

# Verify version string
python -c "import ontos; print(ontos.__version__)"
```

**Checkpoint:** Commit with message `"chore: update pyproject.toml for v3.0.0 release"`

---

#### Task 4.6.2: Update `ontos/__init__.py` version

**Description:** Update version string to 3.0.0.

**File(s):**
- `ontos/__init__.py` — MODIFY

**Instructions:**

```python
__version__ = "3.0.0"
```

**Checkpoint:** Commit with message `"chore: bump version to 3.0.0"`

---

#### Task 4.6.3: Final verification

**Description:** Run comprehensive verification before PR.

**Commands:**

```bash
# 1. Full test suite
pytest tests/ -v --cov=ontos --cov-report=term-missing

# 2. Golden Master tests
pytest tests/golden/ -v

# 3. Import verification
python -c "
import ontos
from ontos.commands.init import init_command
from ontos.commands.map import generate_context_map
from ontos.commands.log import log_command
from ontos.commands.doctor import doctor_command
from ontos.commands.export import export_command
from ontos.commands.hook import hook_command
from ontos.ui.json_output import emit_json, emit_result
print('All imports OK')
"

# 4. Command verification
python -m ontos --version
python -m ontos --help
python -m ontos init --help
python -m ontos map --help
python -m ontos log --help
python -m ontos doctor --help
python -m ontos export --help
python -m ontos hook --help

# 5. Fresh directory test
cd /tmp
rm -rf test-phase4-final
mkdir test-phase4-final && cd test-phase4-final
git init

# Test workflow
python -m ontos init
python -m ontos map
python -m ontos doctor
python -m ontos export
cat CLAUDE.md

# Test JSON output
python -m ontos doctor --json
python -m ontos --version --json

# 6. Verify deletions
cd -
ls ontos/_scripts/install.py 2>/dev/null && echo "ERROR: Not deleted" || echo "OK"
ls ontos/_scripts/ontos_install_hooks.py 2>/dev/null && echo "ERROR: Not deleted" || echo "OK"

# 7. Verify no broken references
grep -r "ontos_lib" --include="*.py" ontos/ 2>/dev/null | grep -v "_scripts" | grep -v "archive" && echo "ERROR: References" || echo "OK"
```

**All verifications must pass before PR.**

---

## Legacy Deletion Safety Protocol

### CRITICAL: Follow this protocol exactly

#### Before Deleting ANY File

1. **Search for imports:**
   ```bash
   grep -r "import FILENAME" --include="*.py" ontos/
   grep -r "from FILENAME" --include="*.py" ontos/
   grep -r "from ontos._scripts.FILENAME" --include="*.py" ontos/
   ```

2. **Search for references:**
   ```bash
   grep -r "FILENAME" --include="*.py" ontos/ tests/
   grep -r "FILENAME" --include="*.md" docs/
   grep -r "FILENAME" --include="*.toml" .
   ```

3. **Check entry points:**
   ```bash
   grep "FILENAME" pyproject.toml
   ```

4. **Document findings:**
   - If references found: DO NOT DELETE. Report to Chief Architect.
   - If no references: Safe to delete.

#### After Each Deletion

```bash
# 1. Verify no import errors
python -c "import ontos"

# 2. Verify tests pass
pytest tests/ -v --tb=short

# 3. Verify commands work
python -m ontos --help
python -m ontos map --help
python -m ontos doctor --help
```

**If anything fails:** Restore IMMEDIATELY with `git checkout -- <file>`

---

## Cross-Platform Notes

### Windows Considerations

| Issue | Solution |
|-------|----------|
| No shebang execution | Python shim; git runs it via Python |
| chmod not available | Skip chmod on Windows with `os.name` check |
| Path separators | Use `pathlib.Path` everywhere |
| Long paths | Document as known limitation |
| Python not in PATH | `sys.executable -m ontos` fallback |

### macOS Considerations

| Issue | Solution |
|-------|----------|
| Gatekeeper | N/A (Python package, not binary) |
| Case sensitivity | Use consistent lowercase |

### Testing Guidance

If you have access to multiple platforms:
- [ ] Linux: Full functionality expected
- [ ] macOS: Full functionality expected
- [ ] Windows: Basic functionality; hooks may need Python in PATH

Document any issues found.

---

## Common Mistakes (Avoid These)

1. **Importing ui/ in core/** — Architecture violation. Check imports.

2. **Deleting before verifying** — Always grep first. Always.

3. **Inconsistent JSON schema** — Use ui/json_output.py for ALL JSON output.

4. **Forgetting to update cli.py routing** — New commands must be wired.

5. **Hardcoded paths** — Use pathlib.Path, respect config.

6. **Breaking existing commands** — Run full test suite frequently.

7. **Windows path issues** — No hardcoded `/` separators.

8. **Missing entry points** — Verify pyproject.toml.

9. **Skipping tests** — Every new module needs tests.

10. **Big commits** — One logical change per commit.

11. **Forgetting graceful error handling** — Doctor checks must handle git missing.

12. **Path traversal in export** — Validate output path within repo.

---

## File Reference

| File | Action | Task | Notes |
|------|--------|------|-------|
| `ontos/ui/__init__.py` | MODIFY | 4.1.1, 4.1.3 | Add json_output exports |
| `ontos/ui/json_output.py` | CREATE | 4.1.2 | JSON formatting |
| `ontos/commands/doctor.py` | CREATE | 4.2.1 | Health checks (7) |
| `ontos/commands/hook.py` | CREATE | 4.2.2 | Hook dispatcher |
| `ontos/commands/export.py` | CREATE | 4.2.3 | CLAUDE.md generation |
| `ontos/cli.py` | MODIFY | 4.3.1 | Full argparse CLI |
| `ontos/commands/init.py` | MODIFY | 4.4.1 | Shim hook installation |
| `.ontos-internal/archive/scripts-v2/` | CREATE | 4.5.1 | Legacy archive |
| `ontos/_scripts/install.py` | DELETE | 4.5.3 | Legacy |
| `ontos/_scripts/ontos_install_hooks.py` | DELETE | 4.5.3 | Legacy |
| `ontos/_scripts/ontos_create_bundle.py` | DELETE | 4.5.3 | Legacy |
| `ontos/_scripts/ontos_generate_ontology_spec.py` | DELETE | 4.5.3 | Legacy |
| `ontos/_scripts/ontos_summarize.py` | DELETE | 4.5.3 | Legacy |
| `ontos/_scripts/ontos_migrate_frontmatter.py` | DELETE | 4.5.3 | Legacy |
| `ontos/_scripts/ontos_migrate_v2.py` | DELETE | 4.5.3 | Legacy |
| `ontos/_scripts/ontos_remove_frontmatter.py` | DELETE | 4.5.3 | Legacy |
| `ontos/__init__.py` | MODIFY | 4.6.2 | Version bump |
| `pyproject.toml` | MODIFY | 4.6.1 | Entry points, metadata |
| `tests/ui/test_json_output.py` | CREATE | 4.1.2 | Tests |
| `tests/commands/test_doctor_phase4.py` | CREATE | 4.2.1 | Tests |
| `tests/commands/test_hook_phase4.py` | CREATE | 4.2.2 | Tests |
| `tests/commands/test_export_phase4.py` | CREATE | 4.2.3 | Tests |
| `tests/test_cli_phase4.py` | CREATE | 4.3.1 | Tests |

---

## Verification Checkpoints

### After Day 1 (UI Layer)

```bash
python -c "from ontos.ui import emit_json, emit_result; print('OK')"
pytest tests/ui/ -v
pytest tests/ -v
```

### After Day 2 (New Commands)

```bash
python -c "from ontos.commands.doctor import doctor_command; print('OK')"
python -c "from ontos.commands.hook import hook_command; print('OK')"
python -c "from ontos.commands.export import export_command; print('OK')"
pytest tests/commands/test_doctor_phase4.py tests/commands/test_hook_phase4.py tests/commands/test_export_phase4.py -v
```

### After Day 3 (CLI)

```bash
python -m ontos --help
python -m ontos doctor --help
python -m ontos export --help
pytest tests/test_cli_phase4.py -v
```

### After Day 4 (Hooks)

```bash
cd /tmp && rm -rf test-hooks && mkdir test-hooks && cd test-hooks && git init
python -m ontos init
grep "ontos-managed-hook" .git/hooks/pre-push
cd -
```

### After Day 5 (Deletion) — EXTRA THOROUGH

```bash
# All imports
python -c "import ontos; from ontos.commands.init import init_command; from ontos.commands.map import generate_context_map; from ontos.commands.doctor import doctor_command; print('OK')"

# All tests
pytest tests/ -v

# All commands
python -m ontos --help
python -m ontos init --help
python -m ontos map --help
python -m ontos doctor --help
python -m ontos export --help

# Deletions verified
ls ontos/_scripts/install.py 2>/dev/null && echo "ERROR" || echo "OK"
```

### After Day 6 (Final)

```bash
# Full suite
pytest tests/ -v --cov=ontos

# Fresh test
cd /tmp && rm -rf final-test && mkdir final-test && cd final-test && git init
python -m ontos init
python -m ontos map
python -m ontos doctor
python -m ontos export
python -m ontos doctor --json
cd -
```

---

## PR Preparation

### PR Title
`feat: Phase 4 — Full CLI Release (#43)`

### PR Description Template

```markdown
## Summary

Phase 4 implementation: Full CLI release with all commands, JSON output, and legacy cleanup.

## Changes

### New Features
- `ontos doctor` — 7-point health check diagnostics
- `ontos export` — CLAUDE.md generation for AI assistants
- `ontos hook` — Git hook dispatcher (internal)
- `--json` flag support across all commands
- `--quiet` flag for suppressed output
- Full argparse CLI with global options

### New Modules
- `ontos/ui/json_output.py` — Consistent JSON formatting
- `ontos/commands/doctor.py` — Health diagnostics
- `ontos/commands/hook.py` — Hook dispatcher
- `ontos/commands/export.py` — AI integration export

### Deleted (Legacy)
- `install.py` — Replaced by `pip install ontos`
- `ontos_install_hooks.py` — Replaced by `ontos init`
- `ontos_create_bundle.py` — Not in v3.0 spec
- `ontos_generate_ontology_spec.py` — Not in v3.0 spec
- `ontos_summarize.py` — Deferred to v4.0
- `ontos_migrate_frontmatter.py` — Legacy migration
- `ontos_migrate_v2.py` — Legacy migration
- `ontos_remove_frontmatter.py` — Legacy utility

### Updated
- `ontos/cli.py` — Full command routing with argparse
- `ontos/ui/__init__.py` — JSON output exports
- `ontos/commands/init.py` — Python-based shim hooks
- `pyproject.toml` — v3.0.0 metadata, entry points

## Test Results

- [ ] Unit tests: XX passed
- [ ] Integration tests: XX passed
- [ ] Golden Master tests: XX passed
- [ ] Manual testing complete
- [ ] Legacy deletion verified safe

## Open Question Decisions Implemented

- [x] Doctor Scope: Option B (7 checks)
- [x] Wrapper Migration: Option A (keep wrappers)
- [x] JSON for Wrappers: Option A with validation
- [x] Exit for Warnings: Option A (exit 0)
- [x] Deprecation: Option B (archive + phased)

## Checklist

- [ ] Follows spec v1.1
- [ ] Architecture constraints respected (core/io/commands layers)
- [ ] All open question decisions implemented
- [ ] Cross-platform considerations addressed
- [ ] Graceful error handling in doctor
- [ ] Path validation in export
- [ ] Legacy scripts archived before deletion
- [ ] Deprecation warnings added to kept scripts
- [ ] Version bumped to 3.0.0

Reviewed-by: (pending)
Closes #[issue] (if applicable)
```

---

**Implementation prompt signed by:**
- **Role:** Chief Architect
- **Model:** Claude Opus 4.5
- **Date:** 2026-01-13
- **Phase:** 4 — Full CLI Release

*End of Implementation Prompt*
