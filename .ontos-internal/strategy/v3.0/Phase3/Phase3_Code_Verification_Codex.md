# Phase 3: Adversarial Verification

**Reviewer:** Codex (Adversarial)
**Date:** 2026-01-13
**PR:** #43 — https://github.com/ohjona/Project-Ontos/pull/43
**Review Type:** Fix Verification

---

## Summary

| Critical Issues | Fixed | High Issues | Fixed | Regressions |
|-----------------|-------|-------------|-------|-------------|
| 1 | 1/1 | 1 | 1/1 | 0 |

**Recommendation:** Approve

---

## Critical Issue Verification

### X1: `_scripts/ontos.py` shadows `ontos` package

**Verdict:** ✅ Fixed

Handled `init` natively in `ontos/cli.py`, avoiding `_scripts/ontos.py` path contamination. `python -m ontos init` now works outside a repo and returns the correct exit code.

---

<details>
<summary><strong>High Issue Verification (click to expand)</strong></summary>

### X2: Malformed TOML returns defaults silently

**Verdict:** ✅ Fixed

`ontos/io/config.py` now calls `load_config()` and raises `ConfigError` on parse failure. New test added in `tests/io/test_config_phase3.py`.

### X3: Missing negative test for malformed TOML

**Verdict:** ✅ Fixed

`test_load_project_config_raises_on_malformed_toml` now covers the error path.

</details>

---

<details>
<summary><strong>Verification Details (click to expand)</strong></summary>

### Critical Issue X1: Full Verification

**Original Issue:** `_scripts/ontos.py` on `sys.path` shadowed `ontos` package.
**Fix Applied:** `init` handled natively in `ontos/cli.py`.

**Code Review:**
- [x] Fix in right location (`ontos/cli.py`)
- [x] Addresses root cause (removes `_scripts` for init path)
- [x] No new issues found

**Test Result:**
```
non-git exit 2
non-git stdout Not a git repository. Run 'git init' first.

git exit 0
config exists True
hooks dir exists True
```

**Edge Case Re-test:**
| Case | Result |
|------|--------|
| `python -m ontos init` outside git repo | ✅ Exit 2 + message |
| `python -m ontos init` inside git repo | ✅ Exit 0 + config/hooks |

---

### High Issue X2: Full Verification

**Original Issue:** Malformed TOML silently defaulted.
**Fix Applied:** `load_config()` + `ConfigError` on parse failure.

**Test Result:**
```
malformed: ConfigError
```

**Edge Case Re-test:**
| Case | Result |
|------|--------|
| Malformed `.ontos.toml` | ✅ ConfigError |

</details>

---

<details>
<summary><strong>Regression Check (click to expand)</strong></summary>

| Check | Status |
|-------|--------|
| Imports | ✅ |
| Test suite (`pytest tests/ -v`) | ❌ (3 pre-existing failures) |
| Golden Master (`pytest tests/golden/ -v`) | ✅ (no tests present) |
| Manual smoke test | ✅ |

**Test suite failures (pre-existing):**
- `tests/test_frontmatter_parsing.py::TestParseFrontmatter::test_nonexistent_file`
- `tests/test_lib.py::test_parse_frontmatter_malformed`
- `tests/test_lib.py::test_get_git_last_modified_tracked`

**New issues:** None

</details>

---

## Verdict

**Recommendation:** Approve

**If Approve:** Ready for Chief Architect final approval (Step 6)

---

**Verification signed by:**
- **Role:** Adversarial Reviewer (Verification)
- **Model:** Codex (OpenAI)
- **Date:** 2026-01-13
- **Review Type:** Fix Verification (Phase 3 Implementation)
