# Phase 1 Spec: Round 2 Verification Consolidation

**Date:** 2026-01-12
**Reviews Consolidated:** 3
**Spec Version:** 1.1
**Round:** 2 (Verification)

---

## 1. Verdict Summary

| Reviewer | Round 1 Verdict | Round 2 Verdict | Improvement |
|----------|-----------------|-----------------|-------------|
| Gemini | Request Revision | Approve | ↑ |
| Codex | Request Revision | Approve with minor changes | ↑ |
| Claude | Request Revision | Approve | ↑ |

**Consensus:** 3/3 approve or approve with minor changes

**Overall Verdict:** Minor Fix Then Ready

---

## 2. Critical Issue Resolution

| Issue | Gemini | Codex | Claude | Consensus |
|-------|--------|-------|--------|-----------|
| C1: CLI depends on unpackaged files | ✅ | ✅ | ✅ | Resolved |
| C2: Public API mismatch | ✅ | ✅ | ✅ | Resolved |
| C3: `ontos_init.py` not packaged | ✅ | ✅ | ✅ | Resolved |

**Critical Issues Status:** All 3/3 resolved

---

## 3. Major Issue Resolution

| Issue | Gemini | Codex | Claude | Consensus |
|-------|--------|-------|--------|-----------|
| M1: Subprocess loses TTY | ✅ | ✅ | ✅ | Resolved |
| M2: Missing architecture stubs | ✅ | ✅ | ✅ | Resolved |
| M3: Hardcoded paths | ✅ | ✅ | ✅ | Resolved |
| M4: Version duplication | ✅ | ⚠️ | ✅ | Resolved (2/3) |
| M5: Move vs copy ambiguity | ✅ | ✅ | ✅ | Resolved |
| M6: No repo root discovery | ✅ | ✅ | ✅ | Resolved |

**Major Issues Status:** 6/6 resolved (Codex notes M4 could use more detail, but accepts fix)

---

## 4. Architecture Decision

**Option D — Bundle scripts in `ontos/_scripts/`**

| Reviewer | Endorses? | Concerns |
|----------|-----------|----------|
| Gemini | Yes | None |
| Codex | Yes | `ontos init` edge case (see new issue) |
| Claude | Yes | None |

**Consensus:** 3/3 endorse Option D

**Concerns raised:** One edge case — `find_project_root()` blocks `ontos init` in fresh directories. This is a new issue introduced by the fix, not a flaw in Option D itself.

---

## 5. Verification Questions

### Q1: Does `cli.py` correctly locate bundled scripts?

| Gemini | Codex | Claude | Consensus |
|--------|-------|--------|-----------|
| Yes | Yes | Yes | **Yes** |

**Concerns:** None

---

### Q2: Is the public API exactly preserved?

| Gemini | Codex | Claude | Consensus |
|--------|-------|--------|-----------|
| Yes | Yes (needs enforcement) | Yes | **Yes** |

**Concerns:** Codex suggests adding a verification step to compare new `__init__.py` against legacy copy.

---

### Q3: Do both install modes work?

| Gemini | Codex | Claude | Consensus |
|--------|-------|--------|-----------|
| Yes | Cannot verify from spec | Yes (design correct) | **Yes (design)** |

**Concerns:** Full verification requires implementation and testing.

---

## 6. New Issues Introduced

| Issue | Flagged By | Severity | Action Needed |
|-------|------------|----------|---------------|
| `ontos init` blocked outside project | Codex | Major | Yes — exempt `init` from root discovery |

**New issues found:** 1

**Blocking new issues:** 1 (but simple fix)

---

## 7. Final Decision

### 7.1 Spec Status

| Metric | Value |
|--------|-------|
| Critical issues resolved | 3/3 |
| Major issues resolved | 6/6 |
| Architecture decision endorsed | 3/3 |
| Verification questions answered | 3/3 Yes |
| New blocking issues | 1 (simple fix) |

### 7.2 Decision

**Spec Status:** Minor Fix Then Approved

### 7.3 Minor Fix Needed

Chief Architect to address before implementation:

1. **`ontos init` must work outside a project** — Modify `cli.py` to bypass `find_project_root()` when the command is `init`. The `init` command is the only command that legitimately runs outside an existing Ontos project.

**Suggested fix (no re-review needed):**
```python
# In cli.py main():
# Handle init specially - it doesn't need project root
if len(sys.argv) > 1 and sys.argv[1] == "init":
    project_root = Path.cwd()  # Use current directory for init
else:
    project_root = find_project_root()
    if project_root is None:
        print("Error: Not in an Ontos-enabled project.", file=sys.stderr)
        sys.exit(1)
```

### 7.4 Next Steps

| Step | Owner | Action |
|------|-------|--------|
| 1 | Chief Architect | Apply `ontos init` fix to spec (Section 4.4) |
| 2 | Implementer | Proceed with Phase 1 implementation |
| 3 | Implementer | Verify both install modes during implementation |

---

## 8. Summary

Round 1 identified a fundamental distribution flaw. The Chief Architect's response (Option D — bundle scripts) successfully resolves all critical issues. All three reviewers endorse this approach.

One new edge case was introduced: `find_project_root()` blocks `ontos init` in fresh directories. This is a simple fix that can be applied during implementation without re-review.

**The spec is approved.** Apply the minor `ontos init` fix and proceed to implementation.

---

*End of Consolidation*
