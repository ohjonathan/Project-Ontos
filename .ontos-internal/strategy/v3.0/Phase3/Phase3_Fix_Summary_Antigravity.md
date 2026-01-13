# Phase 3: Fix Implementation Summary

**Developer:** Antigravity (powered by Gemini 2.5 Pro)  
**Date:** 2026-01-13  
**PR:** #43

---

## Summary

| Fixes Required | Fixes Applied | Tests Pass |
|----------------|---------------|------------|
| 3 | 3 | ✅ |

**Status:** Ready for verification

---

## Fixes Applied

| # | Issue | Fix | Commit |
|---|-------|-----|--------|
| B1 | Module shadowing breaks CLI outside repo | Handle init natively in cli.py | `51b03e2` |
| M1 | Malformed TOML returns defaults silently | Use load_config() and raise ConfigError | `f566763` |
| M2 | Missing negative test for malformed TOML | Add test_load_project_config_raises_on_malformed_toml | `470c591` |

---

## Fix Details

### Fix B1: Module Shadowing (BLOCKING)

**Issue:** When running `python -m ontos init` from outside a git repo, the `ontos/_scripts/ontos.py` script file shadows the `ontos` package, causing `ModuleNotFoundError: 'ontos' is not a package`.

**Flagged by:** Codex (Adversarial)

**Location:** `ontos/cli.py:82-94`

**Root Cause:** The subprocess delegation to `_scripts/ontos.py` puts the scripts directory on sys.path, which contains a file named `ontos.py` that shadows the `ontos` package.

**Fix Applied:**
- Handle `init` command natively in `cli.py` instead of delegating to subprocess
- This avoids the sys.path contamination entirely

**Verification:**
```bash
cd /tmp && mkdir test-fix && cd test-fix
python -m ontos init
# Result: Exit code 2, "Not a git repository. Run 'git init' first."
```

---

### Fix M1: Malformed TOML Silent Defaulting

**Issue:** If `.ontos.toml` exists but contains malformed TOML, `load_project_config` returns default config silently instead of raising an error.

**Flagged by:** Codex (Adversarial)

**Location:** `ontos/io/config.py:38-45`

**Fix Applied:**
- Use `load_config()` instead of `load_config_if_exists()`
- Catch parse exceptions and raise `ConfigError` with details
- Added docstring documenting the new behavior

---

### Fix M2: Missing Negative Test

**Issue:** No test verifying that malformed TOML raises `ConfigError`.

**Flagged by:** Codex (Adversarial)

**Fix Applied:**
- Added `test_load_project_config_raises_on_malformed_toml()` in `tests/io/test_config_phase3.py`
- Test writes invalid TOML and asserts `ConfigError` is raised

---

## Verification Results

### Test Results

```
44 Phase 3 tests: ALL PASSED ✅
344 total tests: 344 passed, 3 failed (pre-existing)
```

### Import Checks

| Check | Result |
|-------|--------|
| `import ontos` | ✅ |
| `from ontos.core.config import OntosConfig` | ✅ |
| `from ontos.io.config import load_project_config` | ✅ |
| `from ontos.commands.init import init_command` | ✅ |

### Manual Testing

| Test | Result |
|------|--------|
| `ontos init` in non-git directory | ✅ Exit code 2 |
| `ontos init` in fresh git repo | ✅ Exit code 0, creates .ontos.toml |
| Config file created correctly | ✅ |
| Hooks installed | ✅ |

---

## Ready for Verification

**Next Step:** Codex (Adversarial) verification review

**Specifically verify:**
1. B1 fix: `python -m ontos init` works outside git repo (returns exit 2)
2. M1 fix: Malformed `.ontos.toml` raises `ConfigError`

---

**Fix summary signed by:**
- **Role:** Developer
- **Agent:** Antigravity (powered by Gemini 2.5 Pro)
- **Date:** 2026-01-13
