# Phase 1 Spec Verification Review - Codex (Round 2)

**Reviewer:** Codex (Adversarial)  
**Date:** 2026-01-12  
**Spec Version:** 1.1  
**Round:** 2 (Verification)

---

## 1. Critical Issue Resolution

| Issue | Fixed? | Adequate? | Concerns |
|-------|--------|-----------|----------|
| C1: CLI depends on unpackaged files | Yes | Yes | Bundling `_scripts/` resolves site-packages layout. |
| C2: Public API mismatch | Yes | Mostly | Spec mandates exact copy of v2.8 `__init__.py`. Needs enforcement check. |
| C3: `ontos_init.py` not packaged | Yes | Yes | Included in `_scripts/`. |

**Critical Issues Verdict:** All resolved

---

## 2. Major Issue Resolution

| Issue | Addressed? | Adequate? | Notes |
|-------|------------|-----------|-------|
| M1: Subprocess loses TTY | Yes | Yes | `stdin/stdout/stderr` passthrough added. |
| M2: Missing architecture stubs | Yes | Yes | `commands/`, `io/`, `mcp/` placeholders included. |
| M3: Hardcoded paths | Yes | Mostly | Bundling avoids repo paths; relies on `find_project_root`. |
| M4: Version duplication | Partially | No | Spec does not document deprecation path or consolidation steps. |
| M5: Move vs copy ambiguity | Yes | Yes | Clarified as copy; old path retained. |
| M6: No repo root discovery | Yes | Mostly | `find_project_root()` added. |

**Major Issues Verdict:** Mostly resolved — one gap (M4), one new edge case (see §4)

---

## 3. Architecture Decision Review

**Option Selected:** D — Bundle scripts in `ontos/_scripts/`

| Aspect | Assessment |
|--------|------------|
| Solves the distribution problem | Yes |
| Minimal scope increase | Yes |
| Maintains backward compatibility | Yes |
| Sets up Phase 2 correctly | Yes |

**Concerns with this approach:**  
- `find_project_root()` blocks `ontos init` in a fresh directory (no `.ontos` yet). That’s a new failure mode for initialization.

**Alternative you'd prefer:** None — Option D is sound if `ontos init` is exempted from root discovery.

---

## 4. New Issues Check

| New Issue | Severity | Notes |
|-----------|----------|-------|
| `ontos init` blocked outside a project | Major | `find_project_root()` exits before dispatch, so new projects cannot be initialized. |

**New Issues Found:** 1 — `ontos init` blocked

---

## 5. Verification Questions

### Q1: Does `cli.py` correctly locate bundled scripts?

**Answer:** Yes  
**Evidence:** `get_bundled_script()` resolves `ontos/_scripts/ontos.py` via `__file__`, and package data includes `ontos._scripts` files.

---

### Q2: Is the public API exactly preserved?

**Answer:** Yes (per spec) / Uncertain (until verified)  
**Evidence:** Spec requires copying `.ontos/scripts/ontos/__init__.py` exactly with only `__version__` change. Needs a verification check to ensure the copy is exact.

---

### Q3: Do both install modes work?

**Answer:** Cannot verify from spec alone  
**Evidence:** Spec includes explicit tests for `pip install -e .` and `pip install .`, but implementation behavior must be validated.

---

## 6. Final Verdict

**Recommendation:** Approve with minor changes

**Blocking Issues:** 1 — `ontos init` must work outside a repo (root discovery should be bypassed for `init`).

**Minor Suggestions:**
- Add a verification step to compare new `ontos/__init__.py` against legacy copy to guarantee API parity.
- Add a short note on version duplication cleanup (M4) since it was accepted in response.

**Summary:** The core distribution flaw is fixed. Option D is sound and keeps Phase 1 scope minimal. One new regression (init blocked) needs a small CLI exception before approval.

---

*End of Verification Review - Codex*
