---
id: architect_v2_7_phil_synthesis
type: atom
status: complete
depends_on: []
concepts: [ontology, documentation, synthesis, architecture]
---

# Architect Synthesis: v2.7 Documentation Ontology Reviews

**Date:** 2025-12-18
**Author:** Claude Code (Opus 4.5) as Architect
**Role:** Owner of design conversation
**Inputs:** Reviews from Codex, Claude, and Gemini acting as technical co-founders

---

## Executive Summary

Three technical co-founder reviews converge on the same core conclusion: **approve the philosophy with refinements**. This document synthesizes their feedback, analyzes each point thoroughly, and resolves open questions with architectural decisions for the v2.7 implementation proposal.

### Key Resolutions

| Decision | Resolution | Source |
|----------|------------|--------|
| Field name | `describes` (not `documents`) | Claude's analysis |
| Targets | Valid atom IDs only | Claude + Codex |
| Verification | Doc-level `describes_verified: <date>` | Codex + Claude |
| Transitive staleness | No — direct relationships only | Claude |
| Section-level | Deferred to v2.8 | All three |
| Performance | < 1 second for staleness check | Gemini |
| Unknown ID handling | Fail-fast with actionable error | Codex |
| `describes` requirement | Optional | Architect |

---

## Part I: Deep Analysis of Each Review

### Codex Review

#### What Codex Gets Right

**1. Source-of-truth clarity**
> "Pick one canonical source (frontmatter) and treat any manifest as generated to avoid drift."

Good engineering discipline. Dual sources always drift. Codex correctly identifies that the philosophy proposal hints at "frontmatter + manifest" without resolving which is authoritative.

**2. Identity & churn problem**
> "Needs an explicit stance that `documents` targets stable IDs; renames require an intentional migration step."

Important operational concern nobody else raised. If we rename an atom from `auth_flow` to `authentication_flow`, every doc with `describes: [auth_flow]` breaks. We need a migration story.

**3. Coverage semantics**
> "Clarify partial coverage vs completeness to avoid false confidence."

Subtle but important. If a doc says `describes: [ontos_end_session]`, does that mean it covers ALL of that atom's behavior, or just SOME? This affects how much trust we place in "no staleness warning."

**4. Defensive defaults**
> "If a doc lists an unknown atom ID, fail generation."

Good fail-fast principle. Don't silently accept broken references.

#### What Codex Misses

- **Naming analysis**: Uses `documents` without engaging with whether it's the right word
- **Transitive staleness**: Doesn't address the edge case
- **Performance**: No mention of hook speed
- **Ontological boundary**: Doesn't explicitly state what can be a target

#### Unique Contribution

**Type discipline via concepts**: "Tag with a concept like `documentation` to distinguish from code atoms." This is clever — instead of creating a new type or subtype, use the existing concepts system. Keeps the ontology flat while enabling filtering.

---

### Claude Review

#### What Claude Gets Right

**1. Naming analysis is rigorous**
> "When reading this, the brain parses 'documents' as a noun (a list of documents), not a verb."

Legitimate linguistic analysis. Compare:
- `depends_on: [foo]` — unambiguous verb
- `impacts: [foo]` — could be noun or verb, but context clarifies
- `documents: [foo]` — genuinely ambiguous

Claude's alternatives (`describes`, `represents`, `covers`) are all clearer.

**2. Ontological boundary problem is the deepest insight**

> "But `ontos_end_session.py` is a Python script, not an atom. Atoms in Ontos are markdown files with frontmatter."

The question nobody else asked: **what are we actually pointing to?**

Three interpretations:
1. Extend what can be an atom (Python files become first-class)
2. Allow `describes` to point outside the ontology (to raw files)
3. Require corresponding atom docs to exist

Claude argues for (3): maintain ontological closure. Everything referenced must exist within the system. If you want to track a script, create an atom doc for it.

**3. Transitive staleness resolution**

> "Changes to transitive dependencies do NOT trigger documentation staleness warnings."

Only Claude addressed this. The reasoning is sound: docs describe *interfaces*, not implementation details. If `some_internal_module` changes but `ontos_end_session`'s interface is unchanged, the Manual is still accurate.

**4. Implementation phasing**

Each phase independently shippable. Good engineering practice.

#### What Claude Misses

- **Performance**: No mention of hook speed (Gemini's key concern)
- **`touch` alternative**: Doesn't engage with Gemini's simpler approach
- **Human discipline risk**: Doesn't acknowledge maintenance burden

#### Where I Push Back on Claude

**The ontological closure requirement may be impractical.**

If we require atom docs for everything that can be described, a project with 50 scripts needs 50 atom docs. That's significant overhead.

Counter-argument: Those atom docs would be useful anyway — they'd document what each script does, its interface, its options. But is that Ontos's job to enforce?

**Resolution**: Start strict (atom IDs only) in v2.7. If the overhead proves too high in practice, relax in v2.8.

---

### Gemini Review

#### What Gemini Gets Right

**1. Performance as primary constraint**

> "The pre-push check MUST be fast. If it adds more than a second or two, developers will bypass it."

Pragmatic wisdom. Friction kills adoption. Nobody else emphasized this, but it's critical. Slow hooks get `--no-verify`'d into oblivion.

**2. Human discipline as biggest risk**

> "The system's value is entirely dependent on developers keeping the `documents` lists accurate."

The honest truth that the other reviews dance around. The whole system is worthless if devs don't maintain `describes` fields.

**3. Suggest-links as future mitigation**

> "Consider a follow-up feature to suggest-links based on content analysis."

Forward-thinking. Reduces cognitive load. Good v2.8 candidate.

**4. Concrete workload estimate**

> "One solid week of engineering."

Only reviewer to give an estimate. Whether accurate or not, it grounds the discussion.

#### What Gemini Misses

- **Naming**: Doesn't engage
- **Ontological boundary**: Doesn't address
- **Transitive staleness**: Doesn't address

#### Where I Push Back on Gemini

**The `touch` approach is elegant but fatally flawed.**

> "Use file modification time (`touch`) for marking docs as 'reviewed' instead of new metadata."

The problem: **git does not preserve file modification times.**

- `git clone` gives all files the current timestamp
- `git checkout` gives checked-out files the current timestamp
- `git stash pop` can alter timestamps
- Rebasing alters timestamps

This means:
- Fresh clone → all files have "now" as mtime → staleness detection is meaningless until files are actually modified post-clone
- Any branch switching → timestamps scrambled

Gemini's approach works in a single-developer, never-clone scenario. It breaks in any realistic team workflow.

**Explicit `verified: <date>` in frontmatter survives all git operations.** It's more verbose but actually works.

---

## Part II: Synthesis Matrix

| Topic | Codex | Claude | Gemini | Architect Position |
|-------|-------|--------|--------|-------------------|
| **Core philosophy** | Approve | Approve with revisions | Approve | **Approve** |
| **Naming** | `documents` (no analysis) | `describes` (strong argument) | `documents` (no analysis) | **`describes`** — Claude's right about ambiguity |
| **Section-level** | Defer | Defer | Defer | **Defer** — unanimous |
| **Verification** | Explicit field | Explicit field | `touch` (mtime) | **Explicit field** — mtime breaks with git |
| **Ontological closure** | Implicit (validate IDs) | Explicit (atom IDs only) | Not addressed | **Atom IDs only** — start strict, relax if needed |
| **Transitive staleness** | Not addressed | No (direct only) | Not addressed | **No** — Claude's reasoning is sound |
| **Performance** | Not addressed | Not addressed | Primary constraint (<2s) | **<1 second** — critical for adoption |
| **"Second-order" term** | Uses without comment | Internal only | "Key insight" | **Internal only** — don't burden users |
| **ID stability/renames** | Explicit migration needed | Not addressed | Not addressed | **Adopt** — important operational concern |

---

## Part III: What to Adopt

### 1. `describes` over `documents` (Claude)
The noun/verb ambiguity is real. `describes: [foo, bar]` reads clearly as "this doc describes foo and bar."

### 2. Explicit verification field (Codex/Claude)
```yaml
describes:
  - ontos_end_session
  - ontos_maintain
describes_verified: 2025-12-18
```
Simple doc-level date. Survives git operations. Auditable.

### 3. Atom IDs only as targets (Claude)
Maintain ontological closure. If you want to track a raw file, create an atom doc for it. This forces useful documentation to exist.

### 4. No transitive staleness (Claude)
Direct relationships only. Docs describe interfaces, not implementation internals.

### 5. Performance < 1 second (Gemini)
Non-negotiable constraint. Design the staleness check to be O(changed_atoms) lookups in precomputed context map.

### 6. Fail-fast on unknown IDs (Codex)
If `describes: [nonexistent_atom]`, fail context map generation with clear error explaining how to fix.

### 7. ID stability stance (Codex)
Document that `describes` targets stable IDs. Renames require updating all references. Consider a migration helper in v2.8.

---

## Part IV: What to Refine

### 1. Verification granularity
- Codex suggests per-atom `verified` dates + `verified_by` attribution
- Claude offers simple (one date) or granular (per-atom)

**Refinement**: Start with simple doc-level `describes_verified: <date>`. If one atom changes, you review the whole doc. Per-atom granularity is over-engineering for v1.

### 2. Ontological closure error handling
Codex/Claude say "fail generation" on unknown ID.

**Refinement**: Fail with actionable error message:
```
ERROR: Unknown atom ID 'foo_script' in describes field of 'manual.md'

  To fix: Create an atom doc at .ontos-internal/atom/foo_script.md
  Or: Remove 'foo_script' from the describes field
```

### 3. "Second-order atom" usage
**Refinement**: Use in philosophy/strategy docs for explanation. Never use in Agent Instructions, Manual, or user-facing error messages. Users think in terms of "docs that describe implementations," not "second-order atoms."

---

## Part V: What to Ignore

### 1. `touch` for verification (Gemini)
Elegant in theory, broken by git's timestamp behavior. Not viable for team workflows.

### 2. Separate manifest file (mentioned by Codex/Gemini)
Frontmatter is source of truth. Context map is the computed manifest. A third artifact adds maintenance burden for no benefit.

### 3. Workload estimate (Gemini: "one week")
Estimates without detailed breakdown are noise. Focus on scope definition, not time prediction.

### 4. `verified_by` attribution (Codex)
Nice for enterprise audit trails. Unnecessary for v2.7. Can add in v2.8 if teams request it.

---

## Part VI: Remaining Open Questions

### 1. Required or optional `describes`?
Claude asks: "Should we require at least one `describes` entry for user-facing docs?"

**Recommendation**: Optional. Not all docs describe atoms. A "Getting Started" guide might describe concepts, not implementations. A "Philosophy" doc might describe strategy. Don't force a field that doesn't apply.

### 2. Staleness threshold / grace period?
Claude asks: "Warn immediately when atom is newer, or allow a grace period?"

**Recommendation**: Immediate warning. No grace period. The warning is non-blocking — it's informational, not a gate. Better to alert and let humans decide than to silently suppress potentially important information.

### 3. What qualifies as a "user-facing doc"?
The philosophy proposal assumes we know which docs are user-facing. But the ontology doesn't have a `user_facing: true` flag.

**Options**:
- Tag with `concepts: [documentation]` (Codex's suggestion)
- Any atom with `describes` field is implicitly user-facing
- Explicit `audience: user` field (over-engineering?)

**Recommendation**: Any atom with `describes` field is implicitly documentation. No need for additional flags.

### 4. Cross-atom documentation
What if a section spans multiple atoms? The proposal says "list all." But what if they change at different times?

**Example**:
```yaml
describes:
  - ontos_end_session    # changed yesterday
  - ontos_maintain       # unchanged for months
describes_verified: 2025-12-15
```

Is the doc stale? Yes, because `ontos_end_session` is newer than `describes_verified`.

**Position**: This is correct behavior. If any described atom is newer than verification date, warn. The reviewer can then check if the specific change affects their doc.

---

## Part VII: Final Architectural Position

The philosophy is sound. The three reviews converge on the same core: **approve with refinements**.

For v2.7 implementation proposal:

| Decision | Resolution |
|----------|------------|
| Field name | `describes` |
| Targets | Valid atom IDs only (ontological closure) |
| Verification | Doc-level `describes_verified: <date>` |
| Transitive staleness | No — direct relationships only |
| Section-level | Deferred to v2.8 |
| Performance | < 1 second for staleness check |
| Unknown ID handling | Fail-fast with actionable error |
| `describes` requirement | Optional — only docs that describe implementations need it |

---

## Appendix: Review Sources

| Reviewer | File | Key Contribution |
|----------|------|------------------|
| Codex | `Codex_V2.7Phil_v1.md` | ID stability, fail-fast defaults, type discipline via concepts |
| Claude | `Claude_V2.7Phil_v1.md` | Naming analysis, ontological closure, transitive staleness |
| Gemini | `Gemini_V2.7Phil_v1.md` | Performance constraint, human discipline risk, `touch` proposal |

---

*Synthesis complete. Ready to proceed to implementation proposal once philosophy is aligned.*
