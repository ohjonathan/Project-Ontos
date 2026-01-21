# Ontos v3.0.4 - Comprehensive Code Review

**Review Date**: January 20, 2026  
**Package Source**: https://pypi.org/project/ontos/  
**Version Analyzed**: 3.0.4  
**Reviewer**: Claude (via deep code inspection)

---

## Executive Summary

Ontos is a local-first documentation management tool for AI-assisted development. The core architecture is solid—clean separation between `core/` (pure logic) and `ui/` (I/O), transactional writes with two-phase commit, and a well-designed curation level system. However, the v3.0.x release has several issues that affect usability, primarily around broken wrapper commands and configuration inconsistencies.

**Severity Distribution**:
- 🔴 High Priority: 3 issues
- 🟡 Medium Priority: 8 issues
- 🟢 Low Priority: 6 issues

---

## Table of Contents

1. [High Priority Issues](#high-priority-issues)
2. [Medium Priority Issues](#medium-priority-issues)
3. [Low Priority Issues](#low-priority-issues)
4. [Architecture Observations](#architecture-observations)
5. [Questions for the Architect](#questions-for-the-architect)
6. [Priority Recommendations](#priority-recommendations)

---

## High Priority Issues

### 1. 🔴 Broken Wrapper Commands

**Affected Commands**: `verify`, `query`, `consolidate`, `migrate`, `promote`, `scaffold`, `stub`

**Problem**: These commands delegate to legacy scripts in `_scripts/` via subprocess, but argument signatures don't match between CLI registration and legacy script expectations.

**Example**:
```python
# CLI registration (cli.py):
p = subparsers.add_parser("verify", help="Verify describes dates", parents=[parent])
# Only accepts --quiet and --json from parent

# But legacy script (ontos_verify.py) expects:
parser.add_argument('filepath', nargs='?')
parser.add_argument('--all', action='store_true')
parser.add_argument('--date', type=str)
```

**Reproduction**:
```bash
$ ontos verify --all
ontos: error: unrecognized arguments: --all
```

**Impact**: Users cannot use these commands as documented. The README acknowledges `verify`, `query`, and `consolidate` are broken, but the scope is actually larger.

**Fix Options**:
1. Pass through all unknown args to subprocess (quick but dirty)
2. Native implementations for each command (clean, more work)
3. Update CLI argument registration to match legacy scripts (medium effort)

---

### 2. 🔴 MCP Extra is a No-op

**Problem**: The package declares an MCP extra that installs pydantic but provides zero functionality.

**In `pyproject.toml` (via METADATA)**:
```
Provides-Extra: mcp
Requires-Dist: pydantic<3.0,>=2.0; extra == "mcp"
```

**In `mcp/__init__.py`**:
```python
"""MCP module - Placeholder for Phase 2."""
```

**Impact**: Users who run `pip install ontos[mcp]` expecting MCP support get a dependency installed with no actual functionality. This creates false expectations and wastes install time.

**Recommendations**:
- Remove the extra until Phase 2 implementation
- OR add a runtime warning when importing the mcp module
- OR document explicitly that `[mcp]` is placeholder-only

---

### 3. 🔴 Legacy Script Config Bypass

**Problem**: Multiple commands ignore `.ontos.toml` configuration entirely.

From README:
> Legacy script limitation: Commands `scaffold`, `stub`, `promote`, `migrate` ignore `.ontos.toml` configuration.

**Root Cause**: Legacy scripts import from `ontos_config.py` (user-project file) and `ontos_config_defaults.py`, expecting a different configuration model than the TOML-based native commands.

**Impact**: Users configure settings in `.ontos.toml`, then discover half the commands ignore it. This creates a confusing split-brain configuration experience.

**Evidence**:
```python
# ontos_config_defaults.py relies on environment variable:
PROJECT_ROOT = os.environ.get("ONTOS_PROJECT_ROOT", os.getcwd())

# But then tries to import user's ontos_config.py which may not exist
from ontos_config import (
    __version__,
    DOCS_DIR,
)
```

---

## Medium Priority Issues

### 4. 🟡 Schema Version Mismatch

**Problem**: Version constants are inconsistent across the codebase.

**In `core/schema.py`**:
```python
CURRENT_SCHEMA_VERSION = "2.2"
MAX_READABLE_SCHEMA = "2.2"
```

**In `_scripts/ontos_config_defaults.py`**:
```python
ONTOS_VERSION = "3.0.3"  # Stale - should be 3.0.4
```

**In `__init__.py`**:
```python
__version__ = "3.0.4"
```

**Impact**: Confusion about what schema version to use for new documents. The schema definitions include v3.0 fields but the tool claims it only supports up to 2.2.

---

### 5. 🟡 Global Mutable State in Staleness Detection

**Location**: `core/staleness.py`

```python
_git_date_cache: Dict[str, Tuple[Optional[date], ModifiedSource]] = {}

def clear_git_cache() -> None:
    """Clear the git date cache. Useful for testing."""
    global _git_date_cache
    _git_date_cache = {}
```

**Problem**: Module-level mutable cache without thread safety. 

**Impact**: In long-running processes (daemon mode is on the roadmap) or concurrent use, this could cause race conditions or stale data. The `clear_git_cache()` function exists but there's no automatic invalidation mechanism.

---

### 6. 🟡 Transactional Writes Not Fully Atomic

**Location**: `core/context.py` - `SessionContext.commit()`

```python
# Phase 2: Atomic rename/apply
for temp, final in staged:
    if temp is None:
        # Delete operation
        final.unlink()  # Not atomic - can fail after writes succeeded
        modified.append(final)
```

**Problem**: The "two-phase commit" uses temp-then-rename for writes (which is atomic on POSIX), but deletes are done inline. If a delete fails mid-batch, earlier write operations have already committed.

**Impact**: Mixed write/delete operations can leave the filesystem in an inconsistent state on failure.

---

### 7. 🟡 Lock File PID Check Race Condition

**Location**: `core/context.py` - `_acquire_lock()`

```python
try:
    pid = int(lock_path.read_text().strip())
    os.kill(pid, 0)  # Check if process exists
except (ProcessLookupError, ValueError, OSError):
    # Stale lock - process is dead, remove it
    try:
        lock_path.unlink()  # RACE WINDOW HERE
    except FileNotFoundError:
        pass
    continue  # Try to acquire again
```

**Problem**: Classic TOCTOU (Time-of-Check-to-Time-of-Use) race. Between reading the stale lock and unlinking it, another process could acquire it.

**Impact**: Low probability in practice, but could cause two processes to believe they hold the lock simultaneously.

---

### 8. 🟡 TOML Writer is Naive

**Location**: `io/toml.py` - `write_config()`

```python
def _format_value(v: Any) -> str:
    if v is None:
        return '""'  # TOML doesn't have null, use empty string
```

**Problems**:
1. Converting `None` to `""` loses information (can't distinguish between "not set" and "empty string")
2. Doesn't handle multiline strings
3. Doesn't handle datetime values
4. Doesn't handle dotted keys
5. Doesn't handle inline tables

**Impact**: Subtle bugs with optional config values and potential data loss on round-trip.

---

### 9. 🟡 Windows Compatibility Concerns

**Issues identified**:

1. **Lock file implementation** uses `os.O_CREAT | os.O_EXCL` which may behave differently on Windows
2. **PID checking** with `os.kill(pid, 0)` doesn't work the same way on Windows
3. **Path handling** mostly uses `Path` (good) but some legacy scripts mix `os.path`

**Note**: Git hooks are Python shims (not bash), which is good for cross-platform. But the lock acquisition isn't Windows-safe.

**Impact**: Unknown - Windows isn't mentioned in requirements. Users on Windows may encounter subtle failures.

---

### 10. 🟡 Type System Inconsistency

**Pattern appearing multiple times**:
```python
doc_type = doc.type.value if hasattr(doc.type, 'value') else str(doc.type)
```

**Problem**: Document types are sometimes enums, sometimes strings. This defensive pattern suggests inconsistent typing throughout the codebase.

**Impact**: Code complexity and potential for type-related bugs.

---

### 11. 🟡 YAML Serialization Reimplements the Wheel

**Location**: `core/schema.py` - `serialize_frontmatter()`

```python
if isinstance(value, dict):
    # Serialize nested dict as inline JSON-like format
    import json
    return f"{key}: {json.dumps(value)}"  # This isn't valid YAML!
```

**Problem**: Hand-rolled YAML serialization instead of using PyYAML (which is already a required dependency). The implementation has edge cases that produce invalid YAML.

**Impact**: Potential for generating malformed frontmatter that can't be parsed back.

---

## Low Priority Issues

### 12. 🟢 Error Messages Leak Internal Paths

```python
print(f"Error: Script not found: {script_path}", file=sys.stderr)
# Outputs: Error: Script not found: /usr/local/lib/python3.12/dist-packages/ontos/_scripts/...
```

**Impact**: Minor UX issue and potential info leak in hosted environments.

---

### 13. 🟢 Frontmatter Parsing Has No Size Limit

```python
def parse_frontmatter(filepath: str) -> Optional[Dict[str, Any]]:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()  # Reads entire file into memory
```

**Impact**: A maliciously large file would consume excessive memory. Low risk in practice but worth adding a size check.

---

### 14. 🟢 Deprecation Warnings Mixed with JSON Output

```python
def emit_deprecation_notice(message: str) -> None:
    print(f"[DEPRECATION] {message}", file=sys.stderr)
```

**Problem**: When `--json` is passed, deprecation notices still go to stderr. Programs parsing both stdout and stderr may get confused.

**Impact**: Minor - affects programmatic consumers of JSON output.

---

### 15. 🟢 License Ambiguity

The license is "All Rights Reserved" proprietary:

```
This software and associated documentation files (the "Software") are
proprietary and confidential. No part of this Software may be reproduced,
distributed, or transmitted in any form or by any means...
```

**Questions**:
- Does `pip install` count as "reproduction"?
- Can packages be cached in corporate environments?
- What about CI/CD pipelines that mirror PyPI?

**Impact**: May create legal uncertainty for enterprise adoption.

---

### 16. 🟢 No Test Suite in Package

The installed package doesn't include tests.

**Impact**: Users cannot verify the package works correctly in their specific environment. Standard practice for PyPI packages, but noted for completeness.

---

### 17. 🟢 Documentation URLs May Break

```
Project-URL: Documentation, https://github.com/ohjona/Project-Ontos/tree/main/docs
```

**Impact**: If repository structure changes, documentation links become dead. Consider using GitHub Pages or a dedicated docs site.

---

## Architecture Observations

### What's Done Well

1. **Clean separation**: `core/` contains pure logic, `ui/` handles I/O. This is good for testability.

2. **Transactional writes**: `SessionContext` with `buffer_write()` / `commit()` / `rollback()` is a mature pattern.

3. **Curation levels**: The Scaffold → Stub → Full progression gives users an on-ramp without forcing full compliance upfront.

4. **Minimal dependencies**: Only PyYAML for core. Smart choice.

5. **Python shim hooks**: Using Python instead of bash for git hooks enables cross-platform compatibility.

6. **JSON output mode**: Consistent `--json` flag across commands enables programmatic use.

### Design Decisions Worth Noting

1. **Structural graph over semantic search**: Explicit `depends_on` relationships rather than embedding-based retrieval. Deterministic but requires manual maintenance.

2. **Local-first**: No cloud dependencies, no API keys. Good for privacy and offline use.

3. **Schema versioning**: Forward-thinking design for document evolution, though currently underutilized.

---

## Questions for the Architect

1. **Wrapper commands**: What's the plan? Native reimplementation seems cleaner than fixing argument passing. Is this on the v3.0.5 roadmap?

2. **Schema versioning**: Should `CURRENT_SCHEMA_VERSION` be bumped to 3.0 now that the package is v3.0.x? The mismatch creates confusion.

3. **MCP timeline**: If Phase 2 is v4.0, should the `[mcp]` extra be removed until then?

4. **Windows support**: Is this officially supported? Should OS requirements be documented?

5. **License clarification**: Any plans to clarify common use cases (CI caching, corporate environments)?

6. **Daemon mode preparation**: The current global cache and lock design may need rework for long-running processes. Is this being tracked?

7. **Why TOML over YAML for config?** The codebase already depends on PyYAML but implements a custom TOML writer. What drove this architectural decision?

8. **Test coverage**: What's the current test coverage? Are there integration tests for the CLI?

---

## Priority Recommendations

### Immediate (v3.0.5)

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| P0 | Fix wrapper command argument passing OR disable broken commands | Medium | High - users hitting errors |
| P0 | Sync version strings (`ONTOS_VERSION` in config_defaults) | Low | Medium - confusing |
| P0 | Add warning to MCP import or remove extra | Low | Medium - false expectations |

### Short-term (v3.1)

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| P1 | Native implementations for `verify`, `query` at minimum | High | High - core functionality |
| P1 | Consistent enum vs string handling for document types | Medium | Medium - code quality |
| P1 | Windows compatibility audit | Medium | Medium - platform support |
| P1 | Use PyYAML for YAML serialization | Low | Low - code simplification |

### Medium-term (v3.2+)

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| P2 | Thread-safe caching for daemon mode prep | Medium | Future-proofing |
| P2 | Truly atomic transactions (handle deletes properly) | Medium | Edge case reliability |
| P2 | Add size limits to file operations | Low | Security hardening |
| P2 | License clarification | Low | Enterprise adoption |

---

## Appendix: Files Examined

```
ontos/
├── __init__.py
├── __main__.py
├── cli.py
├── _hooks/
│   ├── pre-commit
│   └── pre-push
├── _scripts/
│   ├── ontos_config_defaults.py
│   ├── ontos_verify.py
│   ├── ontos_query.py
│   └── ... (other legacy scripts)
├── _templates/
├── commands/
│   ├── init.py
│   ├── map.py
│   ├── agents.py
│   ├── doctor.py
│   └── ...
├── core/
│   ├── config.py
│   ├── context.py
│   ├── curation.py
│   ├── frontmatter.py
│   ├── graph.py
│   ├── schema.py
│   ├── staleness.py
│   ├── validation.py
│   └── ...
├── io/
│   ├── config.py
│   ├── toml.py
│   └── ...
├── mcp/
│   └── __init__.py (placeholder)
└── ui/
    └── ...
```

---

*End of Review*
