---
id: claude_analysis_response
type: strategy
status: draft
depends_on: [v3_2_backlog]
concepts: [review, feedback, ux, onboarding, generated-files]
---

# Response to Claude Analysis (v3.1.0)

**Context:** A separate Claude instance reviewed Project Ontos from PyPI
and GitHub. This review is more UX/product focused compared to ChatGPT's
code-level analysis. This document records our assessment.

---

## Verification of Claims

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | Self-referential docs (AGENTS.md, Context_Map in graph) | TRUE | Default `skip_patterns` = `["_template.md", "archive/*"]` -- no exclusion for generated files |
| 2 | Namespace collision (Databricks) | NOTED | Third reviewer to flag this (also Gemini). Acknowledged. |
| 3 | Legacy script baggage | TRUE | Same as ChatGPT R1. Already addressed. |
| 4 | Version confusion (tool 3.1 vs schema 2.2) | TRUE | `CURRENT_SCHEMA_VERSION = "2.2"` in `core/schema.py:62` |
| 5 | `unknown` type not in DocumentType enum | TRUE | Enum has: KERNEL, STRATEGY, PRODUCT, ATOM, LOG only |
| 6 | Discovery/visibility (1 star) | FAIR | Marketing concern, not technical. |
| 7 | Empty init (no templates) | TRUE | `ontos init` creates dirs but no starter files |
| 8 | "describes" staleness undersold | TRUE | Feature exists but README barely mentions it |

---

## What We're Adopting

### C1: Skip Generated Files by Default

The self-referential document problem is a real bug. `AGENTS.md` and
`Ontos_Context_Map.md` should never appear in the graph they describe.

**Fix:** Update default `skip_patterns` in `core/config.py`:
```python
skip_patterns: List[str] = field(default_factory=lambda: [
    "_template.md",
    "archive/*",
    "AGENTS.md",
    "Ontos_Context_Map.md",
    ".cursorrules",
])
```

**Acceptance criterion:** Running `ontos map` on a fresh `ontos init`
project does not include generated files in the output graph.

### C2: Type Validation in Scaffold

`type: unknown` shouldn't silently pass. Two options:

**Option A (strict):** Scaffold refuses to write `type: unknown`, emits
a warning asking the user to classify manually.

**Option B (pragmatic):** Add `UNKNOWN = "unknown"` to the `DocumentType`
enum as a sentinel value, and make `doctor` flag it as a warning.

We lean toward **Option A** -- the whole point is that types are curated.
An `unknown` type undermines the hierarchy's value.

**Acceptance criterion:** `ontos scaffold` never outputs `type: unknown`
without a warning. `ontos doctor` flags any document with unrecognized
type as a warning.

### C3: Init Templates

Empty directories are bad onboarding. `ontos init` should create a
minimal starter document.

**Approach:** Create one template file during init:
```
.ontos-internal/kernel/mission.md
```
With minimal content:
```yaml
---
id: mission
type: kernel
status: draft
---
# Mission

Why does this project exist? What problem does it solve?
```

This gives new users something to edit rather than staring at empty dirs.

**Acceptance criterion:** `ontos init` creates at least one kernel
document with valid frontmatter that passes `ontos doctor`.

### C4: Describe Staleness in README

The `describes` feature (tracking which docs describe which, with
staleness detection) is genuinely powerful and undersold.

**Approach:** Add a short section in README under "Use Cases" or
"Features" explaining:
- What `describes` does (document freshness tracking)
- How `ontos verify` works
- How `ontos doctor` surfaces stale docs

### C5: Version Story Clarity

Tool version 3.1.0, schema version 2.2, config version "3.0" -- three
unrelated version tracks is confusing.

**Options:**
- A) Bump schema to 3.0 to align with tool (breaking change for existing
  repos without migration)
- B) Document the separation clearly: "tool version != schema version"
- C) Rename schema version to avoid confusion (e.g., "frontmatter_format: 2.2")

We lean toward **B** for now (document it) with a note that schema 3.0
will align in a future release when there's an actual schema-breaking
change to justify it. Bumping versions for cosmetic alignment creates
unnecessary migrations.

---

## What We're Noting (Not Immediate Action)

### Namespace Collision

Third reviewer to flag this. Pattern is clear: it's a real discoverability
issue. We'll investigate:
- Is Databricks' `ontos` on PyPI? (if so, bigger problem)
- Is "Project Ontos" sufficient differentiation in practice?
- Would `ontos-ctx` or `ontos-context` as a PyPI alias help?

Not changing the name yet, but tracking this seriously.

### Discovery/Community

Valid but outside the scope of a code remediation plan. This is a
marketing/community task:
- Integration guides (Cursor, Claude Code, Windsurf)
- Example repos
- Community presence

Noting for post-v3.2 focus.

---

## What We're Not Adopting

### Shipping `_template.md` Separately from Init

The suggestion to "ship a template file during init" is adopted, but we
won't scatter `_template.md` files in every directory. One kernel document
is enough to teach the pattern. Additional templates can come from
`ontos stub --type strategy` etc.

---

## Unique Insights from This Review

Compared to Gemini and ChatGPT, this review uniquely identifies:

1. **Self-referential document bug** -- neither other reviewer caught this.
   It's the most impactful UX bug: it breaks the "deterministic output"
   promise when generated files pollute the graph.

2. **Empty init onboarding gap** -- practical UX issue that neither other
   reviewer flagged.

3. **Version number confusion** -- real cognitive load for users, not
   flagged by others.

These are all **user-facing** issues vs. ChatGPT's **developer-facing**
(internal code quality) issues. Both matter, but these are more likely
to cause first-impression failures.

---

*Response prepared 2026-01-22. Ontos v3.1.0.*
