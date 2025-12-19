---
id: claude_v2_7_implementation_review
type: atom
status: complete
depends_on: []
concepts: [review, describes, immutable-history, implementation]
---

# Architectural Review: v2.7 Implementation Plan

**Reviewer:** Claude Opus 4.5
**Date:** 2025-12-19
**Document Version:** 1.0.0 (Initial Draft)
**Review Scope:** Technical implementation readiness

---

## Part 1: Overall Assessment

**Grade: A-**

This is a strong implementation plan. It demonstrates:
- Clear problem statements with concrete scenarios
- Well-formulated open questions with options, pros/cons, and recommendations
- Comprehensive testing strategy
- Pragmatic phased rollout
- Self-hosting requirement (dogfooding)

The plan is **ready for implementation** after resolving the open questions and addressing a few gaps identified below.

---

## Part 2: Section-by-Section Review

### Section 1: Executive Summary

**[APPROVE]**

Scope is well-bounded. The "out of scope" list is appropriately aggressive — deferring section-level tracking and suggest-links to v2.8+ is the right call.

---

### Section 2: `describes` Field

#### 2.3 Schema Changes

**[APPROVE WITH CHANGES]**

**Open Question Votes:**

| Question | My Vote | Rationale |
|----------|---------|-----------|
| **2.3.A** (What types can USE describes?) | **Atom only** | Agree with recommendation. Allowing strategy to describe atoms inverts the hierarchy. If product specs need this, introduce `product` using describes in v2.8. |
| **2.3.B** (What types can BE described?) | **Atom only** | Agree. The purpose is "implementation staleness." Strategy/kernel changes are paradigm shifts, not incremental drift. |
| **2.3.C** (Self-reference?) | **Disallow** | Agree. Semantically meaningless. |

**Additional validation rule needed:**

```
| describes_verified is in the future | **WARN** — suspicious, may never trigger staleness |
```

*Rationale:* A user setting `describes_verified: 2030-01-01` would never see staleness warnings. This is probably an error.

---

#### 2.4 Staleness Detection Logic

**[APPROVE WITH CHANGES]**

**Open Question Votes:**

| Question | My Vote | Rationale |
|----------|---------|-----------|
| **2.4.A** (How to determine last modified?) | **Option A (Git) with Option D fallback** | Agree. Git is the source of truth. The fallback handles edge cases. |
| **2.4.B** (Date precision?) | **Day precision** | Agree. Avoids timezone complexity. |
| **2.4.C** (When does staleness check run?) | **Context map gen + Archive Ontos only** | Disagree with "all of the above." |

**Why not pre-push?**

Pre-push already has potential warnings (unarchived session, consolidation reminders). Adding staleness warnings creates **warning fatigue**. Users will learn to ignore all warnings.

**Recommended behavior:**
- **Context map gen:** Shows persistent state (for agents)
- **Archive Ontos:** Natural checkpoint when user is "finishing work"
- **Pre-push:** Skip staleness warning (user already saw it at Archive Ontos)

---

**Edge cases not addressed:**

1. **Uncommitted files:**
   ```python
   git log -1 --format=%ci -- new_file.md
   # Returns empty string for files not yet committed
   ```
   **Solution:** If git returns empty, treat as "modified today" (conservative).

2. **File deleted after being added to `describes`:**
   ```yaml
   describes: [some_atom_that_was_deleted]
   ```
   The plan says "fail with actionable error" for unknown IDs. But what if the file existed when describes was added, then got deleted later? Same behavior, but error message should account for this case.

3. **Git not installed:**
   ```python
   subprocess.run(["git", ...])  # FileNotFoundError if git not in PATH
   ```
   **Solution:** Catch exception, warn, fall back to mtime with clear message.

---

#### 2.6 Verification Workflow

**[APPROVE]**

**Open Question Vote:**

| Question | My Vote | Rationale |
|----------|---------|-----------|
| **2.6.A** (How to update verified date?) | **Option D (Manual + Command)** | Agree. Manual is the base case. Command is convenience. Option C risks "click yes to dismiss." |

---

#### 2.8 Script Modifications

**[APPROVE WITH CHANGES]**

**Open Question Votes:**

| Question | My Vote | Rationale |
|----------|---------|-----------|
| **2.8.A** (Staleness audit format?) | **Both (inline + section)** | Agree. Quick scan + actionable list. |
| **2.8.B** (Verify script structure?) | **New script** | Agree. Migrate to unified CLI in v2.8. |

**Change needed in 2.8.1 (`ontos_lib.py`):**

The function signature:
```python
def get_git_last_modified(filepath: Path) -> Optional[date]:
```

Should also return a status indicator:
```python
def get_git_last_modified(filepath: Path) -> Tuple[Optional[date], ModifiedSource]:
    """
    Returns:
        (date, source) where source is 'git', 'mtime', or 'uncommitted'
    """
```

*Rationale:* Downstream code may want to know if the date came from git (reliable) or mtime (unreliable). The staleness warning could be different for mtime-based dates.

---

#### 2.9 Migration Strategy

**[APPROVE]**

| Question | My Vote | Rationale |
|----------|---------|-----------|
| **2.9.A** (Migration strategy?) | **Option A (Silent)** | Agree. Ship the feature. Don't overcomplicate v2.7. |

---

### Section 3: Immutable History

#### 3.3 Design Decisions

**[APPROVE WITH CHANGES]**

**Open Question Votes:**

| Question | My Vote | Rationale |
|----------|---------|-----------|
| **3.3.A** (When to regenerate?) | **Option A (Context map gen)** with opt-out flag | See note below |
| **3.3.B** (Date source?) | **Option 3 (Frontmatter with fallback)** | Agree |
| **3.3.C** (Location?) | **Option 1 (Current)** | Agree. Breaking change otherwise. |
| **3.3.D** (Git tracking?) | **Option C (Committed + marked)** | Agree |
| **3.5.A** (Consolidation relationship?) | **Independent** | Agree |
| **3.6.A** (Merge helper?) | **No helper for v2.7** | Agree |

**Note on 3.3.A:**

"On context map generation" is elegant, but may surprise users:

```bash
# User just wants to check the map
python3 .ontos/scripts/ontos_generate_context_map.py
# Side effect: decision_history.md is also modified
```

**Recommended:** Add `--skip-history` flag:
```bash
python3 .ontos/scripts/ontos_generate_context_map.py --skip-history
```

Default behavior: regenerate history. Flag allows skipping when user just wants to validate.

---

**Issue not addressed: Legacy archived logs**

The plan says:
> "Read all logs from `.ontos-internal/logs/` and `archive/logs/`"

Archived logs may have incomplete/inconsistent frontmatter (created before v2.0, manually edited, etc.). The history generator should:
1. Log a warning for unparseable logs
2. Continue with parseable logs
3. Not fail entirely on one bad log

---

#### 3.4 Output Format

**[APPROVE WITH CHANGES]**

The generated format is good. One addition:

```markdown
<!--
GENERATED FILE - DO NOT EDIT MANUALLY
Regenerated by: ontos_generate_context_map.py
Source: .ontos-internal/logs/, .ontos-internal/archive/logs/
Last generated: 2025-12-19T14:30:00Z
Log count: 47 active, 123 archived
-->
```

Adding log counts helps users understand the scope of the history.

---

### Section 4: Testing Strategy

**[APPROVE]**

Comprehensive. The deterministic output test (same logs → same hash) is particularly important.

**Add one test:**
```python
def test_history_generation_with_malformed_log():
    """History generation should skip unparseable logs with warning."""
```

---

### Section 5: Documentation Updates

**[APPROVE]**

All the right docs are identified for updates.

---

### Section 6: Rollout Plan

**[APPROVE]**

The phased approach is correct. Self-hosting (Phase 4, item 17) is the right capstone.

---

### Section 7: Open Questions Summary

**[APPROVE]**

Excellent consolidation. This table will be valuable for the review board vote.

---

### Section 8: Risks and Mitigations

**[APPROVE WITH CHANGES]**

**Missing risks:**

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Git not available in environment | Low | Medium | Graceful fallback with clear error |
| Archived logs have malformed frontmatter | Medium | Low | Skip with warning, continue generation |
| Warning fatigue from multiple checkpoints | Medium | Medium | Limit staleness warnings to context map + Archive Ontos |

---

### Section 9: Success Criteria

**[APPROVE]**

All criteria are testable and measurable.

---

## Part 3: Issues Not Mentioned in the Document

### 3.1 Performance: Git Batch Operations

The current design calls `git log` once per described atom:

```python
for atom_id in doc.describes:
    atom_last_modified = get_last_modified(atom_id)
```

For 20 describes relationships, that's 20 subprocess calls.

**Optimization (not required for v2.7, note for v2.8):**

```bash
git log --format="%ci %H" --name-only -- file1.md file2.md file3.md
```

This returns all file timestamps in one call. Parse output to build a cache.

### 3.2 Transitive Staleness

**Scenario:**
- `Manual.md` describes `api_spec.md`
- `api_spec.md` describes `api_implementation.py`
- `api_implementation.py` changes

**Question:** Should `Manual.md` be flagged stale?

**Current design:** No. Only direct relationships are checked.

**Recommendation:** Keep it this way. Transitive staleness is complex and likely to produce false positives. The Architect Synthesis explicitly rejected it.

### 3.3 The `describes` Field Name Confirmation

The philosophy proposal chose `describes` over `documents` to avoid noun/verb ambiguity. This plan uses `describes` throughout.

**Confirm:** This is the final field name? Changing it later is a breaking change.

### 3.4 What Happens to Existing `decision_history.md` Content?

The plan says history will be regenerated. But the current `decision_history.md` may contain:
- Manually written context
- Entries that predate the log system
- Custom formatting

**Question:** Is it acceptable to lose this content?

**Recommendation:** Before v2.7 ships, archive the current `decision_history.md` content into the existing logs (or a special "legacy" log). Then regeneration won't lose information.

### 3.5 The `--strict` Flag Behavior

Currently `--strict` fails on broken links, cycles, etc. Should it also fail on:
- `[STALE]` flags?
- Missing `describes_verified`?

**Recommendation:**
- `--strict` should NOT fail on staleness (it's a warning, not an error)
- `--strict` should warn but not fail on missing `describes_verified`

This keeps staleness in the "advisory" category, not "blocking."

---

## Part 4: Summary of My Votes

| ID | Question | My Vote | Notes |
|----|----------|---------|-------|
| 2.3.A | Types can USE describes | **Atom only** | Agree |
| 2.3.B | Types can BE described | **Atom only** | Agree |
| 2.3.C | Self-reference | **Disallow** | Agree |
| 2.4.A | Last modified source | **Git with fallback** | Agree, add uncommitted file handling |
| 2.4.B | Date precision | **Day** | Agree |
| 2.4.C | When to check | **Context map + Archive Ontos** | Remove pre-push to reduce warning fatigue |
| 2.6.A | Update verified date | **Manual + Command** | Agree |
| 2.8.A | Audit format | **Both** | Agree |
| 2.8.B | Verify script | **New script** | Agree |
| 2.9.A | Migration | **Silent** | Agree |
| 3.3.A | When to regenerate | **Context map gen** | Add --skip-history flag |
| 3.3.B | Date source | **Frontmatter with fallback** | Agree |
| 3.3.C | Location | **Current** | Agree |
| 3.3.D | Git tracking | **Committed + marked** | Agree |
| 3.5.A | Consolidation relationship | **Independent** | Agree |
| 3.6.A | Merge helper | **No helper** | Agree |

---

## Part 5: Final Recommendation

**[APPROVE WITH CHANGES]**

The plan is well-designed and ready for implementation. Address the following before starting:

### Required Changes

1. Add validation for `describes_verified` in the future
2. Handle uncommitted files in git lookup (treat as "today")
3. Handle git-not-installed gracefully
4. Handle malformed archived logs in history generation
5. Add `--skip-history` flag to context map generation

### Recommended Changes

1. Remove staleness check from pre-push (reduce warning fatigue)
2. Add log count to generated history header
3. Archive existing `decision_history.md` content before v2.7 ships
4. Return `ModifiedSource` from `get_git_last_modified()` for better downstream handling

### Deferred (v2.8+)

1. Git batch operations for performance
2. Migration helper for describes field
3. Unified CLI integration for `ontos verify`

---

*End of review. Ready for implementation after addressing required changes.*
