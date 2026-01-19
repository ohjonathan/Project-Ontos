---
id: phase_v3_0_4_implementation_spec
type: spec
status: approved
depends_on: [v3.0.3_Implementation_Spec, v3_0_4_cli_wrapper_fix_proposal]
concepts: [implementation-spec, patch-release, cli-portability, wrapper-commands]
---

# Ontos v3.0.4 Implementation Spec

**Version:** 1.2
**Author:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-19
**Status:** Approved

---

## 1. Overview

This release fixes a bug where CLI wrapper commands (`verify`, `query`, `migrate`, `consolidate`, `promote`, `scaffold`, `stub`) fail in new repositories because they execute in the wrong directory (package installation directory instead of user's project).

| Category | Value |
|----------|-------|
| Target Version | 3.0.4 |
| Theme | CLI Portability — New Repository Support |
| Risk Level | LOW |
| Files Modified | 2 |
| Lines Changed | ~15 |
| Commands Fixed | 7 (all wrapper commands) |

---

## 2. Scope

### 2.1 In Scope

| Change | File | Lines | Status |
|--------|------|-------|--------|
| Fix `_get_subprocess_env()` to use user's CWD | `ontos/cli.py` | 19-32 | Pending |
| Add `ONTOS_PROJECT_ROOT` environment variable | `ontos/cli.py` | 19-32 | Pending |
| Remove hardcoded `cwd=` parameter | `ontos/cli.py` | 410 | Pending |
| Bump version to 3.0.4 | `ontos/__init__.py` | 10 | Pending |

### 2.2 Out of Scope

| Item | Rationale |
|------|-----------|
| Migrating wrapper commands to native implementations | Deferred to v3.1+ per roadmap |
| Fixing legacy `ontos_config.py` path resolution | Users should reinstall; code-side fix is sufficient |
| Adding new commands | Bug fix release only |

---

## 3. Dependencies

### 3.1 Prerequisites

| Prerequisite | Status |
|--------------|--------|
| v3.0.3 released | Complete |
| `ontos_config_defaults.py` reads `ONTOS_PROJECT_ROOT` (line 43) | Verified |

### 3.2 Blocked By

None. This is a self-contained bug fix.

---

## 4. Technical Design

### 4.1 `ontos/cli.py` — Function `_get_subprocess_env()` (Lines 19-32)

**Change Type:** MODIFY

**Current Code (verified):**
```python
def _get_subprocess_env() -> dict:
    """Get environment for subprocess calls with PYTHONPATH set.

    Ensures subprocesses can import from ontos package in source checkouts
    by adding the project root to PYTHONPATH.
    """
    env = os.environ.copy()
    project_root = str(Path(__file__).parent.parent)
    existing_pythonpath = env.get('PYTHONPATH', '')
    if existing_pythonpath:
        env['PYTHONPATH'] = f"{project_root}{os.pathsep}{existing_pythonpath}"
    else:
        env['PYTHONPATH'] = project_root
    return env
```

**New Code:**
```python
def _get_subprocess_env() -> dict:
    """Get environment for subprocess calls.

    Sets:
    - ONTOS_PROJECT_ROOT: User's current working directory (for legacy script compatibility)
    - PYTHONPATH: Includes both user's project root (for config imports) and
                  package installation root (for ontos.core imports)
    """
    env = os.environ.copy()
    # Use user's CWD as project root, not package installation directory
    try:
        project_root = str(Path.cwd())
    except OSError:
        # CWD deleted or inaccessible; subprocess will fail gracefully
        project_root = "/"
    env.setdefault('ONTOS_PROJECT_ROOT', project_root)

    # Package installation root (needed for legacy scripts to import ontos.core)
    package_root = str(Path(__file__).parent.parent)

    # Build PYTHONPATH: project_root + package_root + existing
    existing_pythonpath = env.get('PYTHONPATH', '')
    path_parts = [project_root, package_root]
    if existing_pythonpath:
        path_parts.append(existing_pythonpath)
    env['PYTHONPATH'] = os.pathsep.join(path_parts)
    return env
```

**Key Changes:**
1. `Path(__file__).parent.parent` → `Path.cwd()` for `project_root` (user's working directory)
2. Added try/except around `Path.cwd()` with fallback to `/` (B4: handles deleted/inaccessible CWD)
3. Added `env.setdefault('ONTOS_PROJECT_ROOT', project_root)` (M1/M5: respects user-set env var)
4. Added `package_root` to PYTHONPATH for legacy scripts to import `ontos.core.*` modules (v1.2 deviation approval)
5. Updated docstring to reflect actual behavior

### 4.2 `ontos/cli.py` — Function `_cmd_wrapper()` (Line 410)

**Change Type:** MODIFY

**Current Code (verified):**
```python
        result = subprocess.run(cmd, capture_output=True, text=True, env=_get_subprocess_env(), cwd=str(Path(__file__).parent.parent))
```

**New Code:**
```python
        result = subprocess.run(cmd, capture_output=True, text=True, env=_get_subprocess_env())
```

**Rationale:** Removing `cwd=` allows subprocess to inherit the user's current working directory. Combined with `ONTOS_PROJECT_ROOT` env var, legacy scripts can now find the correct project.

### 4.3 `ontos/__init__.py` — Version (Line 10)

**Change Type:** MODIFY

**Current Code (verified):**
```python
__version__ = "3.0.3"
```

**New Code:**
```python
__version__ = "3.0.4"
```

---

## 5. Open Questions

None. The fix is well-understood. The root cause is verified. The solution aligns with how native commands already work.

---

## 6. Test Strategy

### 6.1 Unit Tests

| Component | Test Coverage |
|-----------|---------------|
| `_get_subprocess_env()` | Returns dict with `ONTOS_PROJECT_ROOT` set to CWD |
| `_cmd_wrapper()` | Subprocess inherits CWD (no explicit cwd= param) |

### 6.2 Integration Tests

| Scenario | Test |
|----------|------|
| Fresh repository | Run wrapper commands in new git repo |
| Existing Ontos repo | Run commands in Project-Ontos source dir |
| Subdirectory execution | Run from `docs/` subdir, scripts should walk up |

### 6.3 Manual Verification Protocol

**Step 1: Syntax Check (Must Pass)**
```bash
python3 -m py_compile ontos/cli.py && echo "cli.py: OK"
python3 -m py_compile ontos/__init__.py && echo "__init__.py: OK"
```

**Step 2: Version Check**
```bash
python3 -m ontos --version
# Expected: ontos 3.0.4
```

**Step 3: Native Command Regression Check**
```bash
python3 -m ontos doctor
python3 -m ontos map --help
python3 -m ontos init --help
# All must work without errors
```

**Step 4: Wrapper Command Fix Check (Critical)**
```bash
# Create fresh test environment
cd /tmp && rm -rf ontos-v304-test && mkdir ontos-v304-test && cd ontos-v304-test
git init

# Initialize Ontos
python3 -m ontos init

# Create test document
mkdir -p docs
cat > docs/test.md << 'EOF'
---
id: test_doc
type: atom
status: active
---
# Test Document
EOF

# Test ALL wrapper commands (these were broken before)
python3 -m ontos verify --help      # Must show help, not ModuleNotFoundError
python3 -m ontos query --help       # Must show help, not ModuleNotFoundError
python3 -m ontos consolidate --help # Must show help, not ModuleNotFoundError
python3 -m ontos scaffold --help    # Must show help
python3 -m ontos stub --help        # Must show help
python3 -m ontos promote --help     # Must show help
python3 -m ontos migrate --help     # Must show help

# Test actual execution
python3 -m ontos map                # Generate context map
python3 -m ontos verify --all       # Must work, not fail with import error

# Verify output location
ls -la Ontos_Context_Map.md
# Expected: File exists in /tmp/ontos-v304-test/ (NOT site-packages)

# Cleanup
cd /tmp && rm -rf ontos-v304-test
```

**Step 5: Test Suite**
```bash
cd /path/to/Project-Ontos
pytest tests/ -v --ignore=tests/golden/
# Must pass
```

---

## 7. Edge Cases

| Scenario | Current Behavior | New Behavior | Acceptable? |
|----------|------------------|--------------|-------------|
| Run from project root | Fails (scans package dir) | Works (scans CWD) | Yes |
| Run from subdirectory | Fails | Partial (see note below) | Yes |
| Run from non-project dir | Fails | Fails gracefully (no .ontos.toml found) | Yes |
| Run from `/` | Fails | Fails gracefully | Yes |
| Source checkout (editable install) | Works (package dir = source) | Works (CWD = source) | Yes |
| CWD deleted/inaccessible | Crashes | Falls back to `/`, fails gracefully | Yes |
| Symlinked directories | Unknown | Follows symlinks (Python default) | Yes |

### 7.1 Subdirectory Execution Limitation (B2, M4)

**Limitation:** When running from a subdirectory (e.g., `docs/`), `ONTOS_PROJECT_ROOT` is set to that subdirectory, not the actual project root. The variable name is semantically ambiguous in this context.

**Impact:** Legacy scripts that rely solely on `ONTOS_PROJECT_ROOT` may look for `.ontos.toml` in the wrong location. However, `find_project_root()` in legacy scripts walks upward from CWD to find the project root, mitigating this issue in most cases.

**Status:** This is a known limitation of the wrapper architecture. Full resolution requires v3.1 native migration which will eliminate wrapper commands entirely.

**Trade-off:** Current behavior (COMPLETELY BROKEN) vs new behavior (WORKS from project root, PARTIAL from subdirectories). This is a strict improvement.

### 7.2 Symlinked Directories Limitation

**Limitation:** When running from a symlinked directory, `Path.cwd()` returns the symlinked path, not the resolved path. This follows Python's default behavior.

**Impact:** Low priority — symlinked project directories are uncommon. Behavior is consistent with standard Python tooling.

---

## 8. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Regression in native commands | Low | High | Native commands don't use `_get_subprocess_env()` — verified via grep |
| Breaking source checkouts | Low | Medium | PYTHONPATH still includes project root; editable installs work |
| Edge case: non-project directory | Low | Low | Behavior unchanged — fails gracefully with clear error |
| PYTHONPATH pollution | Low | Low | Adding CWD to PYTHONPATH is harmless if ontos is pip installed |
| PYTHONPATH import shadowing (B3) | Low | Medium | See security consideration below |
| CWD deleted during execution | Very Low | Low | try/except with fallback to `/` |

**Overall Risk Assessment:** LOW — Changes are isolated to subprocess invocation for wrapper commands only.

### 8.1 PYTHONPATH Security Consideration (B3)

**Risk:** CWD is prepended to PYTHONPATH, which allows import shadowing if a user runs `ontos` from an untrusted directory containing a malicious `ontos.py` or `ontos_config.py`.

**Threat Model Assessment:**
- Attack requires user to execute `ontos` from an untrusted directory containing a malicious Python file
- This is a narrow threat model — users running commands from untrusted directories already have broader exposure
- Same risk exists with `pip install -e .` (editable installs) which is standard Python practice

**Trade-off Rationale:**
- PYTHONPATH manipulation is required for legacy config imports to work
- Removing PYTHONPATH breaks the core fix
- The benefit (working wrapper commands) outweighs the edge case security risk

**Status:** Accepted — documented risk with narrow threat model.

### 8.2 Platform Limitations

**Tested Platforms:**
- macOS (Darwin) — Primary development platform
- Linux — Expected to work (same POSIX semantics)

**Untested Platforms:**
- Windows — Path separator differences (`os.pathsep`) are handled, but not tested

**Note:** Full cross-platform testing matrix is deferred to v3.1 native migration.

---

## 9. Acceptance Criteria

- [ ] `python3 -m ontos --version` shows `3.0.4`
- [ ] All native commands (`map`, `doctor`, `init`, `agents`, `log`, `hook`) continue working
- [ ] All 7 wrapper commands work in a fresh repository (no `ModuleNotFoundError`)
- [ ] Context map is generated in user's project directory, not package directory
- [ ] `pytest tests/ -v --ignore=tests/golden/` passes
- [ ] Manual verification protocol passes completely

---

## 10. Implementation Checklist

1. [ ] Edit `ontos/cli.py` lines 19-32: Rewrite `_get_subprocess_env()` function
2. [ ] Edit `ontos/cli.py` line 410: Remove `cwd=str(Path(__file__).parent.parent)` parameter
3. [ ] Edit `ontos/__init__.py` line 10: Change `"3.0.3"` to `"3.0.4"`
4. [ ] Run syntax check (`py_compile`) on both files
5. [ ] Reinstall locally: `pip install -e .`
6. [ ] Run manual verification protocol (Section 6.3)
7. [ ] Run test suite
8. [ ] Commit with message: `fix(cli): resolve wrapper command CWD bug in new repos`

---

## 11. Command Status After v3.0.4

| Command | Type | Status |
|---------|------|--------|
| `ontos init` | Native | Working |
| `ontos map` | Native | Working |
| `ontos doctor` | Native | Working |
| `ontos agents` | Native | Working |
| `ontos log` | Native | Working |
| `ontos hook` | Native | Working |
| `ontos verify` | Wrapper | **FIXED** |
| `ontos query` | Wrapper | **FIXED** |
| `ontos consolidate` | Wrapper | **FIXED** |
| `ontos scaffold` | Wrapper | **FIXED** |
| `ontos stub` | Wrapper | **FIXED** |
| `ontos promote` | Wrapper | **FIXED** |
| `ontos migrate` | Wrapper | **FIXED** |

**Note:** All 7 wrapper commands use the same `_cmd_wrapper()` function, so the fix applies to all of them uniformly.

---

## 12. Critical Files Summary

| File | Location | Change Type |
|------|----------|-------------|
| `ontos/cli.py` | Lines 19-32 | Rewrite `_get_subprocess_env()` |
| `ontos/cli.py` | Line 410 | Remove `cwd=` parameter |
| `ontos/__init__.py` | Line 10 | Version bump `3.0.3` → `3.0.4` |

---

## 13. Verification Summary

| Claim | Verification Method | Status |
|-------|---------------------|--------|
| `_get_subprocess_env()` at lines 19-32 | Read file directly | Confirmed |
| `subprocess.run()` at line 410 | Read file directly | Confirmed |
| Uses `Path(__file__).parent.parent` | Line 26 and line 410 | Confirmed |
| 7 wrapper commands exist | CLI inspection | Confirmed |
| Native commands don't use `_get_subprocess_env()` | grep | Confirmed |
| `ONTOS_PROJECT_ROOT` ready in config | `ontos_config_defaults.py:43` | Confirmed |

---

## 14. Changelog

### v1.1 → v1.2

| Section | Change | Issue # |
|---------|--------|---------|
| Header | Update version to v1.2 | — |
| 4.1 | Update code block to include `package_root` in PYTHONPATH | B2 deviation |
| 4.1 | Update key changes list to document `package_root` addition | B2 deviation |

**Decision:** Approved deviation from v1.1 spec. The implementation correctly adds `package_root` (package installation directory) to PYTHONPATH, enabling legacy scripts to import `ontos.core.*` modules. Without this, wrapper commands would fail with `ModuleNotFoundError`. See PR #50 comment for full decision rationale.

### v1.0 → v1.1

| Section | Change | Issue # |
|---------|--------|---------|
| Frontmatter | Fix `depends_on` ID validation | B1 |
| Header | Update version to v1.1, status to Approved | M2 |
| 4.1 | Add try/except for `Path.cwd()` | B4 |
| 4.1 | Use `env.setdefault()` for `ONTOS_PROJECT_ROOT` | M1, M5 |
| 7 | Add subdir execution limitation note | B2, M4 |
| 7 | Add symlink limitation note | Codex |
| 8 | Add PYTHONPATH security consideration | B3 |
| 8 | Add platform limitation note | Codex |

---

*End of Implementation Spec v1.2*

*Chief Architect: Claude Opus 4.5*
*Date: 2026-01-19*
*Status: Approved — Ready for D.6 Final Approval*
