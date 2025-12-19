---
id: claude_2_7_phil_v1_review
type: atom
status: complete
depends_on: []
concepts: [ontology, documentation, review, architecture]
---

# Technical Co-Founder Review: v2.7 Documentation Ontology Philosophy

**Reviewer:** Claude Code (Opus 4.5)
**Role:** Technical Co-Founder
**Date:** 2025-12-18
**Document Reviewed:** v2.7_documentation_ontology.md (Philosophy Proposal)

---

## Executive Summary

**Verdict:** Approve the philosophy with revisions.

The core insight is valid — there's a real relationship between user-facing docs and implementations that `depends_on` cannot express. The proposed `documents` relationship fills a genuine ontological gap. However, several edges need tightening before implementation.

### Key Revisions Required

| # | Revision | Rationale |
|---|----------|-----------|
| 1 | Rename `documents` → `describes` | Avoid noun/verb ambiguity |
| 2 | Require atom IDs as targets | Maintain ontological closure |
| 3 | Cut section-level tracking | Defer complexity to v2.8 |
| 4 | Add verification workflow | `verified: <date>` field |
| 5 | Clarify: no transitive staleness | Direct relationships only |
| 6 | Drop "second-order atom" from user-facing language | Keep as internal intuition only |

---

## 1. What the Proposal Gets Right

### 1.1 The Core Insight is Valid

There's a real relationship between user-facing docs and implementations that `depends_on` can't express. The Manual doesn't "implement" the archiving script — it *describes* it. That's ontologically different, and the current system is blind to it.

### 1.2 Key Decisions I Agree With

| Decision | Why It's Correct |
|----------|------------------|
| Docs declare `documents`, not atoms declaring `documented_by` | The doc author has the moment of intentionality — they're choosing what to cover |
| Single-source with computed inverse | Dual declaration always drifts. This is the only maintainable approach |
| Version bumps as primary trigger | Natural significance filter. Not every change matters |
| No hierarchy among user-facing docs | Simplifies the model. Each doc stands alone |

---

## 2. What I Would Have Probed Differently

### 2.1 The "Second-Order Atom" Framing

The proposal introduces hierarchical language: first-order atoms implement strategy, second-order atoms describe first-order atoms.

**Concern:** This adds conceptual weight that might not be necessary.

What we're actually modeling is simpler: **atoms can have multiple relationship types to other atoms.** Currently we have one (`depends_on`). We're adding another (`documents`/`describes`). They're still all atoms — we don't need to stratify them into orders.

The "second-order" framing is useful intuition for explaining *why* we need this, but it shouldn't leak into the implementation or user-facing concepts. Keep the ontology flat with multiple edge types, not hierarchical with implicit ordering.

**Recommendation:** Use "second-order" in explanatory contexts only. The schema and tooling should treat all atoms uniformly.

### 2.2 The Naming: `documents` is Overloaded

```yaml
documents:
  - ontos_end_session
```

When reading this, the brain parses "documents" as a noun (a list of documents), not a verb (things this doc documents). It's ambiguous.

**Alternatives:**
- `describes: [...]` — clear verb, no collision
- `represents: [...]` — philosophically accurate
- `covers: [...]` — plain English

**Recommendation:** Use **`describes`**. It's unambiguous and reads naturally: "This doc describes these atoms."

### 2.3 The Ontological Boundary Problem

This is my biggest concern. The proposal uses examples like:

> "Manual documents `ontos_end_session.py`"

But `ontos_end_session.py` is a Python script, not an atom. Atoms in Ontos are markdown files with frontmatter.

**What are we actually pointing to?**

Three possible interpretations:
1. We're extending what can be an atom (Python files become first-class)
2. `documents`/`describes` can point outside the ontology (to raw files)
3. We expect corresponding atom docs exist (e.g., `ontos_end_session.md` describes the script)

The proposal seems to assume (3) implicitly, but this needs to be explicit. If we allow (2), we're creating an ontological hole — things referenced that can't be validated, tracked, or reasoned about.

**Recommendation:** `describes` MUST point to valid atom IDs. If you want to track a Python script, create an atom doc for it. This maintains ontological closure.

### 2.4 Transitive Staleness

The proposal says:
> Changes to A don't affect README (even if Manual mentions README)

Good — no cascading among docs. But what about:

```
Manual describes → ontos_end_session (atom)
ontos_end_session depends_on → some_internal_module (atom)
some_internal_module changes
```

Is Manual now stale? The proposal doesn't address this.

**Position:** No. We track direct documentation relationships only. Transitive staleness through `depends_on` chains would be too noisy and philosophically inconsistent — the Manual documents the *interface* of ontos_end_session, not its implementation details.

**Recommendation:** State explicitly: "Staleness is computed from direct `describes` relationships only. Changes to transitive dependencies do not trigger documentation staleness warnings."

### 2.5 Section-Level Tracking Should Be Cut

The proposal floats:

```yaml
documents:
  - id: ontos_end_session
    sections: ["2. Archive Ontos", "3.1 Graduation Workflow"]
```

**Recommendation: Reject for v2.7.**

Reasons:
- Section identifiers are fragile (renumber, restructure)
- Dual maintenance burden (update content AND frontmatter)
- Marginal value over doc-level tracking
- Adds schema complexity for an edge case

If there's demand after v2.7 ships, consider for v2.8. Not now.

---

## 3. Open Questions That Need Resolution

### 3.1 Verification Workflow

The proposal lists "how docs mark themselves as reviewed" as open. This isn't optional — it's core to the UX.

If we warn about staleness, we need a dismiss mechanism. Otherwise warnings accumulate forever.

**Proposed Solution:**

```yaml
describes:
  - id: ontos_end_session
    verified: 2025-12-18
```

When you get a staleness warning:
1. Review the doc
2. If still accurate, update `verified` date
3. Warning clears

This is:
- **Explicit** — no git timestamp tricks
- **Auditable** — you can see when it was last verified
- **Low-friction** — just update a date

**Alternative (simpler but less precise):**

```yaml
describes: [ontos_end_session, ontos_maintain]
describes_verified: 2025-12-18
```

Single verification date for all described atoms. Simpler schema, coarser granularity.

### 3.2 What Actually Triggers the Check?

The proposal says:
- Version bumps (primary)
- Archive Ontos / git push (fallback for non-versioned projects)

But "every git push" could be noisy. Ten pushes a day means ten checks.

**Refinement:** Only check when the push/archive impacts an atom that something describes. Don't check everything every time.

```python
if impacted_atoms.intersection(described_atoms):
    run_staleness_check()
```

This is smarter and reduces alert fatigue.

---

## 4. Technical Workload Assessment

If we implement as proposed (with revisions):

| Component | Effort | Risk |
|-----------|--------|------|
| Schema: add `describes` field | Low | None |
| Validation: must reference valid atoms | Low | None |
| Context map: compute inverse (`described_by`) | Low-Medium | Edge cases in bidirectional computation |
| Staleness detection in Archive Ontos | Medium | Timestamp reliability, hook integration |
| Verification workflow (`verified` field) | Low | UX decisions |
| Documentation updates | Low | Just writing |
| Testing | Medium | Many edge cases to cover |
| Migration | None | Opt-in, no breaking changes |

**Total Assessment:** Medium-sized feature. Not trivial, but not a major architecture change. The philosophical foundation is sound; implementation is mostly plumbing.

### 4.1 Implementation Order Recommendation

1. **Schema first** — add `describes` field, update validation
2. **Context map** — compute bidirectional view
3. **Staleness detection** — integrate with Archive Ontos
4. **Verification workflow** — add `verified` field support
5. **Documentation** — update Manual and Agent Instructions

Each phase is independently shippable.

---

## 5. Verdict

### Approve with Revisions

The core insight is correct. The architecture is sound. The following revisions tighten the edges before we write code:

1. **Rename `documents` → `describes`** — clearer semantics, no noun/verb ambiguity

2. **Explicitly require atom IDs as targets** — maintain ontological closure; no pointing to raw files

3. **Cut section-level tracking** — defer to v2.8 if demand emerges

4. **Add verification workflow to spec** — `verified: <date>` field is required for usable UX

5. **Clarify: no transitive staleness** — direct relationships only; state this explicitly

6. **Drop "second-order atom" from user-facing language** — useful as internal intuition, but keep the ontology flat in documentation and tooling

---

## 6. Questions for the Team

Before implementation proposal:

1. **Do we agree on `describes` over `documents`?** — naming matters for adoption

2. **Simple or granular verification?**
   - Simple: one `describes_verified` date for entire doc
   - Granular: per-atom `verified` dates in the `describes` array

3. **Should we require at least one `describes` entry for user-facing docs?** — or is it purely optional?

4. **What's the staleness threshold?** — warn immediately when atom is newer, or allow a grace period?

---

*Review complete. Ready to proceed to implementation proposal once philosophy is aligned.*
