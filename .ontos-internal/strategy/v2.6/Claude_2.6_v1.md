---
id: claude_2_6_v1_review
type: atom
status: complete
depends_on: [v2_6_proposals_and_tooling]
concepts: [architecture, review, proposals, validation]
---

# Architectural Review: V2.6 Proposals & Validation

**Reviewer:** Claude Reviewer (Architect)
**Date:** 2025-12-17
**Document:** v2.6_proposals_and_tooling.md (Revision 2.0)
**Verdict:** APPROVE with Amendments

---

## 1. Problem Statement Analysis

### 1.1 Problems Identified by Author

| # | Problem | Validity | Evidence |
|---|---------|----------|----------|
| P1 | Rejected ideas not recorded | **VALID** | decision_history.md has 4 entries, all approvals |
| P2 | No status validation | **VALID** | `VALID_TYPES` exists, `VALID_STATUS` does not |
| P3 | Schema/config event_type mismatch | **VALID** | Schema: `implementation` / Config: `feature, fix, refactor` |
| P4 | No stale proposal detection | **VALID** | No lint rule exists |
| P5 | Version releases miss changelog | **VALID** | Observation from v2.5.1, v2.5.2 |

**Assessment:** All problems are real and verified against the codebase.

### 1.2 Problem NOT Identified (Gap)

**P6: No validation that `status: rejected` only applies to proposals**

The proposal adds `rejected` to `VALID_STATUS` but doesn't enforce that only `type: strategy` documents in `proposals/` can have this status. A `type: log` with `status: rejected` would be semantically invalid but pass validation.

---

## 2. Does the Architecture Solve the Problems?

| Problem | Solution Proposed | Solves It? | Notes |
|---------|-------------------|------------|-------|
| P1: Rejections not recorded | Use existing decision_history format | **YES** | Elegant - no schema change needed |
| P2: No status validation | Add `VALID_STATUS` enum | **YES** | Follows existing `VALID_TYPES` pattern |
| P3: event_type mismatch | Fix schema to match config | **YES** | Straightforward |
| P4: Stale proposals | Add lint warning at 60 days | **YES** | Configurable threshold |
| P5: Changelog reminder | Pre-push advisory warning | **PARTIAL** | See Issue #1 below |

**Overall: 4.5/5 problems solved.**

---

## 3. Issues with the Proposed Solution

### Issue #1: Version Reminder Logic is Fragile (MEDIUM)

**Location:** Section 4.5, lines 287-314

**Problem:** The logic checks if `.ontos/scripts/` files were modified, then warns if changelog wasn't updated. But:

```python
# This check is insufficient
scripts_changed = any(f.startswith('.ontos/scripts/') for f in changed_files)
version_updated = '.ontos/scripts/ontos_config_defaults.py' in changed_files
```

**Issues:**
1. Changing `ontos_config_defaults.py` for ANY reason (not just version bump) suppresses the warning
2. Doesn't detect actual version string change, just file modification
3. `@{push}` ref may not exist on first push of branch

**Recommendation:** Either:
- A) Make it simpler: warn on ANY `.ontos/scripts/` change (accept false positives)
- B) Parse actual `ONTOS_VERSION` value from file diff

### Issue #2: Orphan Skip for Drafts May Hide Real Issues (LOW)

**Location:** Section 4.3.4, lines 246-251

```python
if status == 'draft':
    continue  # Skip orphan warning
```

**Problem:** This skips orphan check for ALL drafts, not just proposals. A draft `type: atom` with no dependents might be a real orphan, not an intentional proposal.

**Recommendation:** Be more specific:

```python
# Skip orphan check only for draft proposals
if status == 'draft' and 'proposals/' in filepath:
    continue
```

### Issue #3: Rejected Docs in Context Map (Open Question Q1)

**Location:** Section 10, Q1

The proposal asks whether rejected docs should appear in context map. The recommendation is "Option A: Never include."

**Counter-argument:** Rejected proposals contain valuable "why not" context. When an agent encounters a similar idea, seeing the rejection reason prevents re-treading.

**My recommendation:** Option B with modification:
- Default: exclude rejected
- `--include-archived` flag: includes rejected AND archived
- Context map header: "Run with `--include-archived` for historical decisions"

---

## 4. What I Would Have Done Differently

### 4.1 Add Type-Status Validation Matrix

Rather than just `VALID_STATUS`, I would add a matrix of valid combinations:

```python
# Valid (type, status) combinations
VALID_TYPE_STATUS = {
    'kernel': {'active', 'draft', 'deprecated'},
    'strategy': {'active', 'draft', 'deprecated', 'rejected'},  # rejected only for strategy
    'product': {'active', 'draft', 'deprecated'},
    'atom': {'active', 'draft', 'deprecated'},
    'log': {'active', 'archived'},  # logs can't be draft or rejected
}
```

This prevents semantically invalid combinations like `type: log, status: rejected`.

### 4.2 Rejection Metadata as Required Fields

The proposal suggests optional rejection metadata:

```yaml
rejected_date: 2025-12-17
rejected_reason: "Too complex"
rejected_by: "Claude"
revisit_when: "10k users"
```

I would make `rejected_reason` **required** when `status: rejected`, not optional. The whole point of recording rejections is to capture WHY.

```python
# In validation
if status == 'rejected' and not frontmatter.get('rejected_reason'):
    warnings.append(f"[LINT] **{doc_id}**: status: rejected requires rejected_reason field")
```

### 4.3 Consolidate Status Definitions

The proposal adds `STATUS_DEFINITIONS` dict. I would co-locate it with `VALID_STATUS`:

```python
STATUS_SCHEMA = {
    'draft': {
        'description': 'Work in progress',
        'valid_for': ['kernel', 'strategy', 'product', 'atom'],
        'requires': [],
    },
    'active': {
        'description': 'Current truth',
        'valid_for': ['kernel', 'strategy', 'product', 'atom', 'log'],
        'requires': [],
    },
    'rejected': {
        'description': 'Considered but not approved',
        'valid_for': ['strategy'],  # Only proposals
        'requires': ['rejected_reason'],
    },
    # ...
}
VALID_STATUS = set(STATUS_SCHEMA.keys())
```

Single source of truth, self-documenting, enables richer validation.

---

## 5. Additional Considerations

### 5.1 Missing: What Happens to Approved Proposals?

The lifecycle diagram (lines 106-129) shows:
- REJECT: Move to `archive/proposals/`, change status to `rejected`
- APPROVE: Change status to `active`

**But where does the approved proposal go?**

Options:
- A) Stays in `proposals/` with `status: active` (confusing - why is "active truth" in proposals?)
- B) Moves to parent `strategy/` directory (cleaner)
- C) Gets absorbed into existing strategy doc (merged)

**Recommendation:** Document this explicitly. I suggest Option B - approved proposals "graduate" to `strategy/`.

### 5.2 Missing: Proposal ID Convention

The proposal shows `id: redis_cache_proposal` but doesn't specify naming convention. Should proposals have:
- Suffix: `*_proposal` (explicit)
- Prefix: `proposal_*` (groupable)
- No convention (flexible)

**Recommendation:** Add guidance. I suggest suffix `_proposal` for clarity.

### 5.3 Missing: Dual-Mode Matrix Location

Section 4.6 proposes a new reference doc `Dual_Mode_Matrix.md` in `.ontos-internal/reference/`. But this is contributor-mode only documentation.

**Question:** Should users have access to this? If a user wants to understand mode behavior, they can't see `.ontos-internal/`.

**Recommendation:** Put it in `docs/reference/` (user-visible) or document mode behavior in the Manual instead.

### 5.4 Testing Gap: No Test for Rejection Metadata Validation

Section 7 lists tests T1-T12 but none test:
- Invalid `rejected_reason` (missing when status: rejected)
- Invalid type/status combination (log with status: rejected)

**Recommendation:** Add:
- T13: `status: rejected` without `rejected_reason` triggers warning
- T14: `type: log` with `status: rejected` triggers warning

---

## 6. Summary

| Aspect | Rating | Notes |
|--------|--------|-------|
| Problem identification | Excellent | All real issues |
| Solution design | Good | Elegant reuse of existing patterns |
| Completeness | Fair | Missing approval workflow, type-status matrix |
| Simplification (v2.0) | Excellent | Removing scripts was right call |
| Dual-mode awareness | Good | Explicit consideration |
| Testability | Good | Could add 2 more tests |

---

## 7. Required Amendments

**Before implementation:**

1. **Document approved proposal workflow** - Where do approved proposals go? Recommend: graduate to `strategy/`
2. **Make `rejected_reason` required** - Not optional when `status: rejected`

**Recommended (non-blocking):**

3. Add type-status validation matrix (prevents `type: log, status: rejected`)
4. Add tests T13, T14 for rejection validation
5. Fix orphan skip to be proposal-specific (`'proposals/' in filepath`)
6. Clarify Dual_Mode_Matrix.md location (user-visible or Manual?)
7. Simplify version reminder logic (accept false positives)

---

## 8. Open Questions - My Positions

| Q# | Question | Author Rec | My Position | Rationale |
|----|----------|------------|-------------|-----------|
| Q1 | Rejected in context map? | Option A (never) | **Option B** | `--include-archived` flag for historical recall |
| Q2 | Stale threshold | Option B (60 days) | **Agree** | 60 days is reasonable balance |

---

## 9. Approval

| Reviewer | Status | Date | Notes |
|----------|--------|------|-------|
| Claude (Architect) | REVISED | 2025-12-17 | v2.0 author |
| Claude Reviewer | **APPROVED w/ AMENDMENTS** | 2025-12-17 | See Section 7 |
| Codex | PENDING | - | - |
| Gemini | PENDING | - | - |
| Human (Jonathan) | PENDING | - | - |

---

## 10. References

- [v2.6 Proposals and Tooling](v2.6_proposals_and_tooling.md)
- [Schema Specification](../../atom/schema.md)
- [Config Defaults](../../../.ontos/scripts/ontos_config_defaults.py)
- [Decision History](../decision_history.md)
