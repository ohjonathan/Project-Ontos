# Phase 5: Adversarial Code Review

**Reviewer:** Codex (Adversarial)
**Model:** Codex (OpenAI)
**Date:** 2026-01-13
**PR:** #45
**Review Type:** Code Review

---

## 1. Summary

| Aspect | Status |
|--------|--------|
| Regressions found | Found (1) |
| Incomplete fixes | Found (2) |
| New edge cases | Found (2) |
| Test adequacy | Adequate |

**Recommendation:** Request Changes

**Blocking Issues:** 1

---

## 2. Regression Hunt

### 2.1 Test Suite Results

```bash
python3 -m pytest tests/ -v
# 411 passed in 4.56s

python3 -m pytest tests/golden/ -v
# collected 0 items (exit code 5)
```

| Suite | Result | Notes |
|-------|--------|-------|
| Unit tests | Pass | 411 passed |
| Golden Master | Fail | No tests collected; pytest exit code 5 |

### 2.2 Per-Fix Regression Analysis

| Fix | Could Regress? | What Could Break? | Tested? | Safe? |
|-----|----------------|-------------------|---------|-------|
| P5-2 remove `ontos_lib.py` | Yes | Packaging/installation metadata still referencing removed file | ✅ (grep) | ❌ |
| P5-3 hook detection heuristic | Yes | False positives on foreign hooks | ✅ (tests added) | ⚠️ |
| P5-4 frontmatter in context map | Yes | Golden Master diffs; downstream parser expectations | ⚠️ | ⚠️ |

### 2.3 Regressions Found

| Regression | Caused By | Severity | Evidence |
|------------|-----------|----------|----------|
| `ontos map` fails when running from source | Wrapper subprocess missing PYTHONPATH | Major | `ModuleNotFoundError: No module named 'ontos.io'` from map wrapper |

---

## 3. Fix Completeness Attack

### 3.1 Per-Fix Completeness

| Fix | Issue Description | Fully Addressed? | Gap |
|-----|-------------------|------------------|-----|
| P5-2 remove `ontos_lib.py` | Remove deprecated shim | Partial | `install.py` and `ontos.egg-info/SOURCES.txt` still reference removed file |
| P5-3 hook detection | Avoid false “Non-Ontos hooks” warnings | Partial | Heuristic may treat unrelated hooks with “ontos hook” substring as Ontos |
| P5-4 frontmatter | Context map should include YAML frontmatter | Yes | None |

### 3.2 Incomplete Fixes

| Fix | What's Missing | Impact | Should Block? |
|-----|----------------|--------|---------------|
| P5-2 | Clean up `install.py` and packaging metadata | Potential install/build errors | Yes |
| P5-3 | Negative cases beyond string match | False positives in doctor output | No |

---

## 4. New Edge Cases

### 4.1 Edge Cases Introduced

| Fix | New Edge Case? | Description | Handled? |
|-----|----------------|-------------|----------|
| P5-3 hook detection | Yes | Hook with “ontos hook” in comment misclassified | ✅ (partial tests) |
| P5-2 removal | Yes | Packaging metadata points to removed file | ❌ |

### 4.2 Edge Case Testing

| Edge Case | Test Performed | Result |
|-----------|----------------|--------|
| Hook strict mode blocks | `ontos hook pre-push` with `[hooks] strict = true` | Pass (exit 1) |
| Map wrapper from source | `ontos map` in fresh repo with PYTHONPATH | Fail (ModuleNotFoundError) |

---

## 5. Test Adequacy Attack

### 5.1 Per-Fix Test Coverage

| Fix | Test Added? | Catches Regression? | Covers Edge Cases? |
|-----|-------------|---------------------|-------------------|
| P5-3 hook detection | ✅ | ✅ | ✅ (negative hooks) |
| P5-4 frontmatter | ❌ | ❌ | ❌ |
| P5-2 removal | ❌ | ❌ | ❌ |

### 5.2 Missing Tests

| What's Missing | Why Needed | Severity |
|----------------|------------|----------|
| Golden Master updates for frontmatter | Prevent silent diff regressions | Must Add |
| Packaging/metadata check for removed files | Prevent build/install errors | Must Add |

### 5.3 Test Quality

| Test | Actually Tests the Fix? | Could Pass With Bug? |
|------|-------------------------|----------------------|
| `tests/commands/test_doctor_hooks.py` | Yes | No |

---

## 6. Manual Testing Results

```bash
$ python3 -m ontos --version
ontos 3.0.1

$ python3 -m ontos doctor
OK: configuration: .ontos.toml valid
WARN: git_hooks: Hooks missing: pre-push, pre-commit
OK: python_version: 3.9.6 (>=3.9 required)
OK: docs_directory: 5 documents in docs/
WARN: context_map: Context map missing frontmatter

$ python3 -m ontos map
Traceback (most recent call last):
  ...
ModuleNotFoundError: No module named 'ontos.io'; 'ontos' is not a package
```

| Test | Expected | Actual | Pass? |
|------|----------|--------|-------|
| Version shows v3.0.1 | v3.0.1 | 3.0.1 | ✅ |
| Doctor runs clean | No errors | Warnings (hooks/frontmatter) | ✅ |
| Map runs in fresh repo | Generates map | ModuleNotFoundError | ❌ |

---

## 7. Attack Scenarios

### 7.1 What If Scenarios

| Scenario | Could Happen? | Impact | Mitigated? |
|----------|---------------|--------|------------|
| Wrapper subprocess lacks PYTHONPATH | Yes | `ontos map` fails from source/dev env | ❌ |
| Packaging references missing `ontos_lib.py` | Yes | Build/install errors | ❌ |

### 7.2 Worst Case Analysis

| Worst Case | Likelihood | Impact | Current Mitigation |
|------------|------------|--------|-------------------|
| `ontos map` fails in CI using source checkout | Med | Med | None |

---

## 8. Issues Found

### Critical (Blocking)

| # | Issue | Attack Vector | Impact | Evidence |
|---|-------|---------------|--------|----------|
| X-C1 | `ontos map` fails when run from source checkout | Regression | CLI unusable in dev/CI without install | ModuleNotFoundError in manual test |

### High

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-H1 | Packaging metadata still references removed `ontos_lib.py` | Incomplete fix | Build/install errors | `ontos.egg-info/SOURCES.txt` entry |

### Medium

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-M1 | No golden tests collected | Test adequacy | Frontmatter/regression drift undetected |

---

## 9. Verdict

**Robustness:** Adequate

**Recommendation:** Request Changes

**Top Concerns:**
1. `ontos map` fails from source due to subprocess env missing module path.
2. Packaging metadata still references removed `ontos_lib.py`.
3. Golden master tests are not collected, so frontmatter changes aren’t validated.

**Summary:** Core tests pass, but a regression in the map wrapper breaks source-based use, and packaging metadata still points to removed files. Fix those and ensure golden tests execute before merge.

---

**Review signed by:**
- **Role:** Adversarial Reviewer
- **Model:** Codex (OpenAI)
- **Date:** 2026-01-13
- **Review Type:** Code Review (Phase 5)
