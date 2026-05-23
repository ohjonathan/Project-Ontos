---
id: phase5_implementation_spec
type: strategy
status: active
depends_on: []
concepts: [polish, v3.0.1, documentation, technical-debt, pypi]
---

# Phase 5 Implementation Spec: Polish & Fixes

**Version:** 1.1
**Author:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-13
**Status:** Active

---

## Changelog (v1.0 → v1.1)

**From Review Board:**
- **P5-1 (Arch Violation):** Elevated to **Must**. Use Dependency Injection.
- **P5-2 (Legacy):** Added `install.py` deletion. Added pre-deletion import scan requirement.
- **P5-3 (Hooks):** Elevated to **Should**. Clarified "lenient" check is for `doctor` ONLY. Added negative test cases requirement.
- **P5-4 (Frontmatter):** Added Golden Master baseline update requirement.
- **P5-8 (Release):** Added `ontos --version` check. Added `pyproject.toml` URL verification.

---

## 1. Overview

Phase 5 addresses post-v3.0.0 release issues: bug fixes, UX improvements, documentation updates, technical debt cleanup, and PyPI publication.

**Target Version:** v3.0.1 (patch release)
**Theme:** "Full Polish"
**Risk Level:** LOW — No architectural changes, focused on polish

---

## 2. Scope

### 3.1 In Scope (v3.0.1)

**Must (7 items):**
- [ ] P5-5: Update README.md for v3.0
- [ ] P5-6: Create migration guide
- [ ] P5-7: Update Ontos_Manual.md
- [ ] P5-8: Publish to PyPI
- [ ] P5-9: Verify performance targets
- [ ] **P5-1: Fix architecture violation (core/ imports io/)**
- [ ] **P5-2: Remove ontos_lib.py AND install.py**

**Should (2 items):**
- [ ] P5-3: Fix non-Ontos hooks warning (Doctor only)
- [ ] P5-4: Add frontmatter to context map

### 3.2 Out of Scope (v3.1+)
- `ontos deinit`
- MCP integration

---

## 4. Technical Changes

### 4.1 Documentation Updates
(Same as v1.0)

### 4.2 Technical Debt

#### P5-1: Fix core/ imports io/ (MUST)

**Strategy:** Dependency Injection.

```python
# ontos/core/config.py

# Remove: from ontos.io.git import get_git_config

def get_source(
    git_username_provider: Optional[Callable[[], Optional[str]]] = None
) -> Optional[str]:
    # Use provider instead of direct import
    ...
```

**Action:** Update `cli.py` to inject `ontos.io.git.get_git_config` when calling core functions.

#### P5-2: Remove Legacy Files (MUST)

**Delete:**
- `.ontos/scripts/ontos_lib.py`
- `install.py` (Root)

**Pre-deletion Verification (B1 Mitigation):**
```bash
# Must return 0 matches outside archive/
grep -r 'ontos_lib' . --include='*.py' | grep -v 'archive/'
```
Any remaining references must be updated or removed before deletion.

---

### 4.3 UX Polish

#### P5-3: Fix Non-Ontos Hooks Warning (SHOULD)

**Strict Rule:** `ontos init` MUST use `# ontos-managed-hook` to decide overwrite.
**Lenient Rule:** `ontos doctor` MAY use heuristics to report status.

**Change in `commands/doctor.py`:**
```python
def is_ontos_hook_lenient(hook_path: Path) -> bool:
    """Check if hook is Ontos-managed (heuristic for reporting only)."""
    content = hook_path.read_text()
    return (
        "# ontos-managed-hook" in content or
        "ontos hook" in content or
        "python3 -m ontos" in content
    )
```

**Required Tests (B2 Mitigation):**
- Negative test: foreign hook (e.g., husky, pre-commit) → should NOT match
- Negative test: empty hook → should NOT match
- Negative test: binary hook → should handle gracefully (no crash)

#### P5-4: Add Frontmatter to Context Map (SHOULD)

**Change:** Add YAML frontmatter to `Ontos_Context_Map.md` so Ontos can "read itself".

**Pre-merge Requirement (B3 Mitigation):**
Update Golden Master baselines in test fixtures BEFORE merging this change. Frontmatter changes output format; tests must match.

---

### 4.4 Release Tasks

#### P5-8: PyPI Publication

**Add Verification:**
- Check `ontos --version` matches `pyproject.toml`.
- Check `pyproject.toml` URLs are valid.

---

## 10. Implementation Order

1.  **P5-1 & P5-2:** Technical debt (Clean foundation)
2.  **P5-3 & P5-4:** UX Fixes
3.  **Documentation**
4.  **Release**

---

*Spec Version: 1.1*
*Ready for Implementation*