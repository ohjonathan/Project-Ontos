---
id: v3_2_1_tiered_context_map_exploration
type: strategy
status: draft
depends_on: [philosophy, ontology_spec, mission]
concepts: [activation, context-recovery, tiered-context, philosophy, ontology]
---

# Tiered Context Map: Conceptual Exploration

**Version:** 1.0
**Author:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-30
**Status:** Draft — Exploratory

---

## 1. Executive Summary

The **Tiered Context Map** is an access pattern optimization introduced in v3.2 that structures the context map into progressive layers of detail. It enables cheaper re-activation after context compaction while maintaining full graph depth for deep exploration.

**Key Insight:** Tiers are an **access pattern**, not an **ontological structure**. They don't change what knowledge exists or how it relates — they change how much an agent loads at once.

This document explores how tiers fit within Ontos's existing design philosophy and identifies areas for future development.

---

## 2. The Problem It Solves

### 2.1 Context Compaction and Re-Activation Cost

When AI tools compact their context (e.g., Claude's `/compact`), loaded project context is lost. Before tiers:

| State | Tokens | Recovery Cost |
|-------|--------|---------------|
| Full context map | ~12k+ | Read entire map |
| After compaction | 0 | Re-read entire map (~12k) |

After tiers:

| State | Tokens | Recovery Cost |
|-------|--------|---------------|
| Tier 1 only | ~2k | Minimal re-read |
| Tier 1+2 | ~12k | Standard activation |
| Full map | ~50k+ | Deep exploration |

**Result:** Re-activation after compaction costs ~2k tokens instead of ~12k.

### 2.2 Variable Context Needs

Different tasks require different context depths:

| Task Type | Needed Context | Appropriate Tier |
|-----------|----------------|------------------|
| Quick question | Project summary, recent activity | Tier 1 |
| Feature implementation | Full document index, dependencies | Tier 1 + 2 |
| Architecture review | Complete graph, validation details | Tier 1 + 2 + 3 |
| Deep debugging | Everything | Full map |

Tiers allow agents to load what they need, not everything.

### 2.3 Cross-Tool Consistency

Different tools have different context limits:

| Tool | Context Window | Practical Load |
|------|----------------|----------------|
| Claude Code | 200k | Limited |
| Gemini | 1M+ | Less constrained |
| Codex | Variable | Task-dependent |

Tiers provide a universal structure that works across tools with different capacities.

---

## 3. Conceptual Framework

### 3.1 Tiers vs Document Hierarchy (Orthogonal Concepts)

| Concept | Dimension | What It Organizes |
|---------|-----------|-------------------|
| **Document Types** (kernel→log) | Content classification | WHAT knowledge exists |
| **Tiers** (1→3) | Loading depth | HOW MUCH to load |

These are **orthogonal**:
- Tier 1 can include kernel, strategy, AND atom documents (if they're critical)
- A kernel document can appear in any tier depending on context needs

**The document hierarchy organizes content. Tiers organize access.**

### 3.2 Tiers vs Dual Ontology (Access Pattern, Not Structure)

The dual ontology (Space/Time) describes knowledge relationships:

| Dimension | Question | Relationship |
|-----------|----------|--------------|
| **Space** | What IS true? | `depends_on` → graph |
| **Time** | What HAPPENED? | `impacts` → timeline |

Tiers don't change these relationships. They determine how much of the graph/timeline to load.

**Dual ontology is about knowledge structure. Tiers are about knowledge access.**

### 3.3 Project Context vs Session Context

A key distinction emerged during tier design:

| Concern | Owner | Persistence | Example |
|---------|-------|-------------|---------|
| **Project Context** | Ontos | Permanent | Docs, graph, history |
| **Session Context** | Tooling | Ephemeral | Current task, decisions |

**Design Principle:** Ontos manages project context only. Session context recovery is tooling's responsibility.

Why this matters:
1. Session context capture is invasive and tool-specific
2. Tools will improve at session recovery naturally
3. Overreaching creates coupling and maintenance burden
4. Keeping focus tight enables portability

---

## 4. Tier Definitions

### Tier 1: Essential Context (~2k tokens)

**Purpose:** Survival minimum for quick re-activation

**Contents:**
- Project summary (name, doc count, last updated)
- Recent activity (last 3 logs)
- In-progress documents
- Critical paths (entry points)

**Use Case:** Re-orient after context compaction

**Token Budget:** Hard cap at ~2,000 tokens

### Tier 2: Document Index (~10k tokens)

**Purpose:** Full document catalog for task planning

**Contents:**
- Complete document table (ID, type, status)
- Dependency overview
- Concept index

**Use Case:** Standard activation, feature implementation

**Token Budget:** ~8,000-12,000 tokens

### Tier 3: Full Graph Details (~50k+ tokens)

**Purpose:** Deep exploration and architecture review

**Contents:**
- Complete dependency matrix
- Full validation results
- Staleness analysis
- Timeline details
- Lint results (if enabled)

**Use Case:** Architecture review, debugging, audits

**Token Budget:** Unbounded (full detail)

---

## 5. Design Decisions

### 5.1 Why Three Tiers?

**Considered alternatives:**

| Option | Pros | Cons |
|--------|------|------|
| 2 tiers (summary/full) | Simpler | No middle ground for standard work |
| 3 tiers | Covers quick/standard/deep | More complexity |
| 4+ tiers | Fine-grained control | Cognitive overhead |

**Decision:** Three tiers balance flexibility with simplicity. Most tasks fall into:
1. Quick re-orient (Tier 1)
2. Normal work (Tier 1+2)
3. Deep dive (all tiers)

### 5.2 Token Budget Rationale

| Tier | Budget | Rationale |
|------|--------|-----------|
| Tier 1 | ~2k | Fits in any tool's context, cheap to reload |
| Tier 2 | ~10k | Standard context load for most work |
| Tier 3 | Unbounded | Only loaded when explicitly needed |

The 2k Tier 1 budget ensures even small-context tools can re-activate.

### 5.3 What Goes in Each Tier

**Tier 1 selection criteria:**
- Can an agent understand the project with just this?
- Is this the minimum needed to navigate to more detail?
- Does this fit in 2k tokens reliably?

**Tier 2 selection criteria:**
- Is this needed for standard feature work?
- Does this enable finding the right documents?

**Tier 3 selection criteria:**
- Everything else (validation, deep graph, full history)

---

## 6. Philosophical Alignment

### 6.1 Mapping to the Four Pillars

| Pillar | How Tiers Align |
|--------|-----------------|
| **Intent over Automation** | User/agent chooses tier depth deliberately |
| **Portability over Platform** | Same tiers work across all tools |
| **Shared Memory over Personal** | All agents see same tiered structure |
| **Structure over Search** | Tiers are explicit structure, not search |

### 6.2 Consistency with Existing Ontology

**What tiers DON'T change:**
- Document type hierarchy (kernel→log)
- Dependency flow rules (down only)
- Dual ontology (Space + Time)
- Frontmatter schema
- Validation rules

**What tiers ADD:**
- Access pattern optimization
- Token budgeting
- Re-activation efficiency

### 6.3 The "Librarian's Wager" Connection

From the philosophy:
> "Trade intentional friction (curation) for higher signal"

Tiers extend this:
> "Trade explicit tier selection for efficient context loading"

The friction of choosing a tier (or accepting the default) is the feature — it prevents bloat and forces conscious context management.

---

## 7. Future Considerations

### 7.1 Configurable Tier Sizes

**Current:** Hard-coded token budgets

**Future possibility:** User-configurable in `.ontos.toml`

```toml
[context_map]
tier1_budget = 2000
tier2_budget = 10000
```

**Trade-off:** Flexibility vs complexity

### 7.2 Tool-Specific Tier Recommendations

**Idea:** AGENTS.md could include tool-specific guidance:

```markdown
## Tool-Specific Activation

| Tool | Recommended Default |
|------|---------------------|
| Claude Code | Tier 1+2 (200k limit) |
| Gemini | Full (1M+ capacity) |
| Cursor | Tier 1 (fast response) |
```

### 7.3 Dynamic Tier Generation

**Idea:** Tier content could adapt to the task

Example: "Implementing auth" → Tier 1 includes auth-related docs automatically

**Trade-off:** Requires task understanding; adds non-determinism

### 7.4 Tier Caching

**Idea:** Cache Tier 1 separately for instant re-activation

**Trade-off:** Staleness risk; cache invalidation complexity

---

## 8. Open Questions

### 8.1 Documentation Questions

| Question | Current State | Recommendation |
|----------|---------------|----------------|
| Document tiers in ontology_spec.md? | No | No — tiers are access, not ontology |
| Add context separation to philosophy.md? | No | Optional — implied by existing principles |
| Add tier guidance to agent instructions? | Partial (AGENTS.md) | Yes — explicit guidance helps |
| Update Ontos_Manual.md with tiers? | No | Yes — users need to understand tiers |

### 8.2 Design Questions

| Question | Status | Notes |
|----------|--------|-------|
| Should Tier 1 content be configurable? | Open | Could help large projects |
| Should tiers be explicit sections or implicit? | Decided | Explicit (## Tier N markers) |
| Should agents auto-detect appropriate tier? | Open | Risks non-determinism |
| Should tiers have stable IDs for caching? | Open | Would enable persistent caching |

### 8.3 Philosophical Questions

| Question | Exploration |
|----------|-------------|
| Are tiers a new "pillar" or derived from existing? | Derived — tiers implement "Structure over Search" |
| Do tiers violate "Intent over Automation"? | No — user/agent chooses tier depth |
| Should session context ever be in Tier 1? | No — violates project/session separation |

---

## 9. Conclusion

The tiered context map is **philosophically consistent** with Ontos. It's an implementation of "Structure over Search" applied to context loading — giving agents explicit layers instead of making them guess how much to load.

**Key insights:**
1. Tiers are orthogonal to document hierarchy
2. Tiers are an access pattern, not an ontological change
3. Project/session context separation is a new explicit principle
4. The three-tier structure balances flexibility and simplicity

**Recommendation:** Document tiers in user-facing materials (Manual, Agent Instructions) but not in ontology_spec.md, since tiers are about access, not structure.

---

## Appendix: Tier Structure Reference

```
Ontos_Context_Map.md
├── Frontmatter (version, generated_at)
├── ## Tier 1: Essential Context      ← ~2k tokens
│   ├── ### Project Summary
│   ├── ### Recent Activity
│   ├── ### In Progress (if any)
│   └── ### Critical Paths
├── ---
├── ## Tier 2: Document Index         ← ~10k tokens
│   └── Document table (ID, type, status, depends_on)
├── ---
└── ## Tier 3: Full Graph Details     ← unbounded
    ├── Validation results
    ├── Dependency tree
    ├── Timeline
    ├── Staleness analysis
    └── Lint results (optional)
```

---

**Proposal signed by:**
- **Role:** Chief Architect
- **Model:** Claude Opus 4.5
- **Date:** 2026-01-30
- **Status:** Exploratory — For discussion
