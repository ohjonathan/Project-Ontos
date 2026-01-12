# Phase 1 Spec Verification Review - Gemini

**Reviewer:** Gemini (Alignment Reviewer)
**Date:** 2026-01-12
**Spec Version:** 1.1
**Round:** 2 (Verification)

---

## 1. Critical Issue Resolution

| Issue | Fixed? | Adequate? | Concerns |
|-------|--------|-----------|----------|
| C1: CLI depends on unpackaged files | Yes | Yes | Bundling scripts in `ontos/_scripts/` ensures they are distributed to `site-packages`. |
| C2: Public API mismatch | Yes | Yes | Mandating an exact copy of v2.8 exports guarantees backward compatibility. |
| C3: `ontos_init.py` not packaged | Yes | Yes | Including `ontos_init.py` in the bundle makes `ontos init` functional globally. |

**Critical Issues Verdict:** **All resolved**

---

## 2. Major Issue Resolution

| Issue | Addressed? | Adequate? | Notes |
|-------|------------|-----------|-------|
| M1: Subprocess loses TTY | Yes | Yes | Passing stdio streams preserves interactive prompts/colors. |
| M2: Missing architecture stubs | Yes | Yes | Placeholders align directory structure with architecture docs. |
| M3: Hardcoded paths | Yes | Yes | Relative paths (`Path(__file__).parent`) are robust. |
| M4: Version duplication | Yes | Yes | Deprecation path is documented. |
| M5: Move vs copy ambiguity | Yes | Yes | Explicitly defined as copy + keep old. |
| M6: No repo root discovery | Yes | Yes | `find_project_root()` enables running from subdirectories. |

**Major Issues Verdict:** **All resolved**

---

## 3. Architecture Decision Review

**Option Selected:** D — Bundle scripts in `ontos/_scripts/`

| Aspect | Assessment |
|--------|------------|
| Solves the distribution problem | Yes |
| Minimal scope increase | Yes |
| Maintains backward compatibility | Yes |
| Sets up Phase 2 correctly | Yes |

**Concerns with this approach:** None. While "pure" refactoring (Option A) is cleaner theoretically, Option D is the superior strategic choice for Phase 1 as it respects the "Zero Behavior Change" constraint and minimizes risk. It creates a stable, distributable artifact immediately.

**Alternative you'd prefer:** None — Option D is sound.

---

## 4. New Issues Check

| New Issue | Severity | Notes |
|-----------|----------|-------|
| None | - | The proposed changes are targeted and safe. |

**New Issues Found:** 0 — None

---

## 5. Verification Questions

### Q1: Does `cli.py` correctly locate bundled scripts?

**Answer:** Yes

**Evidence:** `get_bundled_script` uses `Path(__file__).parent / "_scripts" / script_name`. Since `_scripts` is configured as package data and located alongside `cli.py` in the package tree, this relative resolution works in both source checkouts and `site-packages` installations.

---

### Q2: Is the public API exactly preserved?

**Answer:** Yes

**Evidence:** Section 4.2 explicitly mandates copying the current `.ontos/scripts/ontos/__init__.py` exactly, changing only the version string. This effectively freezes the v2.8 API for the v3.0 alpha, preventing regression.

---

### Q3: Do both install modes work?

**Answer:** Yes

**Evidence:**
- **Editable (`pip install -e .`):** The `ontos` directory in the repo is used directly. `_scripts` exists there (copied in Task 1.6). `cli.py` finds it.
- **Standard (`pip install .`):** `pyproject.toml` includes `ontos` and `package-data` includes `ontos._scripts`. The installer copies the full tree to `site-packages`. `cli.py` finds `_scripts` via relative path.

---

## 6. Final Verdict

**Recommendation:** **Approve**

**Blocking Issues:** 0 — None

**Minor Suggestions:** None

**Summary:**
The updated spec (v1.1) successfully addresses the fundamental distribution flaw identified in Round 1. The decision to bundle legacy scripts inside the package ("Option D") effectively bridges the gap between the repository-based v2 architecture and the package-based v3 architecture without risky refactoring. The addition of project root discovery and stream passthrough makes the CLI robust for real-world usage. The spec is ready for implementation.
