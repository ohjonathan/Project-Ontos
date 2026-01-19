---
id: log_20251218_v2_7_philosophy_proposal
type: log
status: active
event_type: feature
concepts: [ontology, bidirectional, documentation]
impacts: [v2_strategy, v2_7_documentation_ontology]
---

# Session Log: V2.7 Philosophy Proposal

Date: 2025-12-18 01:03 KST
Source: Claude Code
Event Type: feature

## 1. Goal

Create a philosophical framework proposal for v2.7 "Documentation Ontology" - a system to detect when user-facing documentation becomes stale after atom changes.

This is a philosophy proposal (not implementation) per Project Lead's explicit request:
> "I think even before a proposal doc for implementation, we may need to make a proposal doc for philosophy / strategy update."

## 2. Key Decisions

**Captured via Q&A dialogue:**

| Question | Project Lead's Answer |
|----------|-----------------|
| Q1: Where should the link live? | Combination of frontmatter + manifest, bidirectional indication needed |
| Q2: What triggers staleness? | Version bumps (primary), Archive Ontos (fallback for non-versioned projects) |
| Q3: Role of logs? | Supplementary context, not trigger |
| Q4: Hierarchy among user-facing docs? | No - each doc is independent, no dependency chain |

**Emerged concepts:**

- **Second-order atoms**: User-facing docs that describe implementations rather than implementing strategy
- **`documents` relationship**: New relationship type distinct from `depends_on`
- **Computed bidirectionality**: Single-source declaration in docs, context map computes inverse

## 3. Changes Made

### v2.7 Philosophy Proposal
- Created v2.7 proposal directory: `.ontos-internal/strategy/proposals/v2.7/`
- Created philosophy proposal: `v2.7_documentation_ontology.md`
  - Preamble explaining why philosophy proposal precedes implementation
  - Part I: Original problem from Project Lead's observation
  - Part II: Q&A dialogue with Project Lead's answers
  - Part III: Philosophical deep dive (second-order atoms, bidirectionality)
  - Part IV: Proposed model (`documents` relationship)
  - Part V: Open questions requiring resolution
  - Part VI: Why this matters (ontological completeness, trust, mission alignment)
  - Executive summary at top with synthesis and key decisions table

### v2.6.2 Count-Based Consolidation (bonus fix)
- `ontos_consolidate.py`: Changed from age-based (30 days) to count-based (keep newest 15)
  - Added `find_excess_logs()` function
  - `--count N` flag to customize retention
  - `--by-age` flag for legacy behavior
- `ontos_maintain.py`: Updated to use `--count` instead of `--days`
- Updated help text to show all 4 maintenance steps
- Version bump to 2.6.2, changelog updated

## 4. Next Steps

1. Review philosophy proposal with Project Lead
2. Resolve open questions:
   - Frontmatter vs manifest as source of truth
   - Section-level tracking worth complexity?
   - How docs mark themselves as "reviewed and current"
3. If philosophy approved, create implementation proposal (`v2.7_implementation.md`)

## 5. Notable Quotes

Project Lead on the importance of this work:
> "This is getting deep. I don't think you are overcomplicating these; I think this is important."

Project Lead on bidirectionality:
> "Dependency (or, at least indication of relationships) need to be bi-directional."

Project Lead on doc independence:
> "I don't think so, because they can exist on their own... they all have their own independence."

---
## Raw Session History
```text
93ea4c4 - docs: add v2.7 philosophical framework proposal
7d413e5 - docs: add executive summary to v2.7 philosophy proposal
aeb9fc9 - docs: add session log for v2.7 philosophy proposal
34a749a - feat(v2.6.2): count-based consolidation
```
