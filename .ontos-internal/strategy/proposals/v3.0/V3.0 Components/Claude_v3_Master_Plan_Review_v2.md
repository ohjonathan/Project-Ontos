---
id: claude_v3_master_plan_review_v2
type: atom
status: complete
depends_on: [v2_strategy]
concepts: [architecture, v3, review, mcp, concurrency]
---

# Architectural Review: v3_master_plan_context_kernel.md (v3.0.0)

**Reviewer:** Claude Opus 4.5
**Date:** 2025-12-19
**Document Version:** 3.0.0 (Synthesized Architect Edition)

---

## Part 1: What Changed & What's Now Right

### 1.1 Feedback Incorporated Successfully

| Previous Critique | Resolution in v3.0.0 | Assessment |
|---------------------|---------------------|------------|
| Config management missing | Section 2.2 "Configuration Cascade" | **Addressed well** |
| install.sh fragility | ADR-002 explicitly rejects .sh for .py | **Addressed** |
| MCP tool contract undefined | Section 2.3 defines 4 tools | **Partially addressed** |
| State threading in God Object | Section 2.1 "Context Object Pattern" | **Addressed well** |
| Schema evolution strategy | V2.9 "Schema Versioning" feature | **Addressed** |
| Obsidian export distraction | Removed from roadmap | **Addressed** |
| Friction vs adoption tension | "Curation Levels" + ADR-003 | **Addressed elegantly** |

**The "Librarian's Compromise" (ADR-003) is particularly well-designed.** It acknowledges reality: developers doing hotfixes won't stop to curate. The `status: pending_curation` flag is a pragmatic solution that maintains signal while lowering the entry barrier.

### 1.2 New Strengths

**1. The "Functional Core, Imperative Shell" principle is excellent.**

This is a well-known pattern (Gary Bernhardt's "Boundaries" talk) and making it an explicit invariant will guide all future implementation decisions. The three-layer architecture (Core → IO → UI/MCP) is clean.

**2. The Configuration Cascade is well-specified.**

```
CLI Flags → Repo Config → User Global → Defaults
```

This is the standard pattern (similar to Git's config resolution). The explicit migration path (`ontos migrate v2-to-v3`) addresses the Python-to-YAML transition.

**3. The MCP Protocol Schema is a good starting point.**

Four tools is the right granularity to start:
- `get_context` — read
- `search_graph` — query
- `log_session` — write
- `check_health` — diagnostics

---

## Part 2: Honest Critique — What Still Needs Work

### 2.1 The MCP Schema is Underspecified for Implementation

The current definition:

```
get_context(focus_ids: List[str], depth: int)
  Returns: Concatenated markdown of requested atoms + dependencies.
```

**Missing specifications:**

| Question | Why It Matters |
|----------|----------------|
| What's the max token limit? | Agent needs to know if response will be truncated |
| What if an ID doesn't exist? | Error handling contract |
| Does `depth: 0` mean "just this doc" or "no dependencies"? | Semantic ambiguity |
| Is response streaming or atomic? | Affects client implementation |
| What's the format? Raw markdown or JSON wrapper? | Protocol design |

**For `log_session`:**

```
log_session(event: str, changes: List[str], decisions: List[str])
  Action: Writes a log file to the repo.
```

| Question | Why It Matters |
|----------|----------------|
| What's the return value? | Does it return the created log ID? |
| Is this synchronous? | Does the agent wait for git commit? |
| What if there's a conflict? | Concurrent write handling |
| What about `impacts` and `concepts`? | These are in the current log schema but not in the API |

**Recommendation:** Before V3.0 implementation, produce a formal **OpenAPI/JSON-RPC spec** for the MCP tools. The current description is good for strategy but insufficient for code generation.

### 2.2 Concurrency Is Still Unaddressed

The document doesn't mention what happens when:

1. **Two agents call `log_session` simultaneously** → Race condition on file write
2. **Agent A reads context while Agent B modifies a doc** → Stale read
3. **Human pushes while MCP server has uncommitted changes** → Conflict

**The SessionContext pattern helps but doesn't solve this.** You need either:

- **Pessimistic locking:** `.ontos/locks/session.lock` file
- **Optimistic concurrency:** Version field in frontmatter, fail on conflict
- **Append-only log:** Never modify, only append (conflict-free)

**Recommendation:** Add a section to the spec: **"Concurrency Model"** with explicit guarantees.

### 2.3 The `search_graph` Tool Has a Contradiction

```
search_graph(query: str, semantic: bool = False)
```

**The `semantic: bool` flag contradicts Core Invariant #5 (The Librarian's Wager):**

> "We trade Higher Friction for Higher Signal (deterministic context)."

Semantic search is probabilistic. If `semantic=True`, you're doing RAG-style retrieval — exactly what Ontos claims to avoid.

**Options:**

1. **Remove `semantic` parameter entirely** — Stay pure to the philosophy
2. **Rename to `fuzzy: bool`** — Make clear it's a "best effort" fallback, not primary
3. **Add ADR explaining when semantic is acceptable** — E.g., "Only for discovery, never for retrieval"

**Recommendation:** Clarify the philosophical stance. Is semantic search ever acceptable, or is it an escape hatch for edge cases?

### 2.4 Typed Edges (V3.0) Still Lacks Validation Rules

The tracker says:

> "Semantic edges: implements, tests, deprecates."

**Still unanswered:**

| Question | Risk if Unanswered |
|----------|-------------------|
| Can `atom` implement `atom`? | Confusing graphs |
| Can `log` deprecate `strategy`? | Type hierarchy violation |
| Is `implements` bidirectional? | If A implements B, does B know about A? |
| What happens to existing `depends_on`? | Migration confusion |

**Recommendation:** Add a **"Type × Edge Matrix"** similar to the existing Type-Status Matrix. Define which edges are valid between which types.

### 2.5 Transaction Boundaries Are Implicit

The Context Object pattern defines state, but not **transaction boundaries**.

**Example scenario:**

```
1. Agent calls log_session()
2. Core writes log file to disk ✓
3. Core attempts to update decision_history.md
4. Step 3 fails (disk full, permissions, etc.)
```

**What's the state now?**
- Log file exists but history is inconsistent
- Is the log considered "created" or should it be rolled back?

**Recommendation:** Define explicit **commit/rollback semantics**:

```python
class SessionContext:
    pending_writes: List[PendingWrite]  # Buffered until commit

    def commit(self) -> Result:
        # Atomic write all pending changes

    def rollback(self):
        # Discard pending changes
```

### 2.6 Success Metrics Are Good But Methodology Is Thin

```
Method: Run 50 random SWE-bench tasks. Control: RAG. Test: Ontos MCP.
```

**Issues:**

1. **50 tasks is statistically weak** — Need power analysis to determine sample size
2. **"Random" selection may not be representative** — Stratify by task type
3. **"RAG" is underspecified** — Which RAG? Naive? Reranked? What embedding model?
4. **Who runs the benchmark?** — If Ontos team runs it, there's bias risk

**Recommendation:** Either:
- Defer to V3.1 when you have resources for rigorous methodology
- Partner with an external team (academic lab, AI eval company) for credibility

### 2.7 The "Growing Context Window" Question Remains

This is an **existential risk** to Ontos that the document doesn't address.

**The challenge:** Claude's context is 200K tokens. Gemini is 1M+. In 2026, we may have 10M token windows.

**If an agent can fit the entire repo in context, why maintain a structured graph?**

**The answer exists, but it's not in the document:**

1. **Curation > Raw Context** — Even with 10M tokens, garbage in = garbage out
2. **History is infinite** — Context windows grow, but decision logs accumulate forever
3. **Graph enables reasoning** — "What depends on X?" is O(1) with a graph, O(n) with raw text
4. **Cost efficiency** — 10M tokens is expensive; curated context is cheaper

**Recommendation:** Add a section: **"Why Ontos Matters in a Long-Context World"** — This is a FAQ that every adopter will ask.

---

## Part 3: New Issues Introduced in v3.0.0

### 3.1 The "Curation Levels" Feature Needs More Definition

```
Level 0 (Scaffold) → Level 1 (Stub Log) → Level 2 (Full Curation)
```

**What's in each level?**

| Level | What's Required | What's Optional | What's Validated |
|-------|-----------------|-----------------|------------------|
| 0 | ??? | ??? | ??? |
| 1 | ??? | ??? | ??? |
| 2 | ??? | ??? | ??? |

**Recommendation:** Define the schema requirements for each level. E.g.:

- **Level 0:** `id`, `type` only. No validation.
- **Level 1:** + `status`, `event_type`. Warns on missing `impacts`.
- **Level 2:** + `concepts`, `impacts`, `alternatives`. Full validation.

### 3.2 The `search_graph(semantic: bool)` Implies a Dependency

If `semantic=True` does semantic search, **what's the embedding model?**

- If it's in the V3 package, you need to ship a model (huge binary)
- If it calls an API, you've violated "Local-First"
- If it's optional (`pip install ontos[semantic]`), you need to handle the import gracefully

**Recommendation:** Either remove semantic search or add it to ADRs with explicit trade-off acknowledgment.

### 3.3 The `changes: List[str]` in `log_session` Is Ambiguous

```
log_session(event: str, changes: List[str], decisions: List[str])
```

**What are "changes"?**
- File paths that were modified?
- Descriptions of changes ("Added auth flow")?
- Git commit hashes?

The current log schema uses `impacts: [doc_id]`. Is `changes` the same thing with a different name?

**Recommendation:** Align the MCP API parameter names with the existing frontmatter schema (`impacts`, `concepts`, etc.) to avoid confusion.

---

## Part 4: Remaining Gaps from Previous Review

| Gap | Status in v3.0.0 |
|-----|------------------|
| Concurrency/locking | **Still missing** |
| Rollback capability | **Still missing** |
| Multi-repo federation | Not addressed (OK for V3.0) |
| Agent feedback loops | Not addressed |
| Typed edge validation rules | **Still missing** |

---

## Summary of Recommendations

| Priority | Recommendation | Target |
|----------|----------------|--------|
| **Critical** | Formalize MCP tool schema (params, returns, errors) | Before V3.0 coding |
| **Critical** | Add concurrency model section | V2.8 or V3.0 |
| **Critical** | Define Curation Level requirements | V2.9 |
| **High** | Clarify `semantic` search philosophy (or remove) | V3.0 |
| **High** | Add transaction/rollback semantics to Context Object | V2.8 |
| **High** | Define Typed Edge validation matrix | V3.0 |
| **Medium** | Address "Why Ontos in Long-Context World" | Strategy doc |
| **Medium** | Align MCP param names with frontmatter schema | V3.0 |
| **Low** | Strengthen SWE-bench methodology or defer | V3.1 |

---

## Final Assessment

**This is a substantial improvement over v2.2.0.** The document now addresses the critical gaps identified in the first review:
- Configuration management ✓
- State threading ✓
- install.py over install.sh ✓
- Schema versioning ✓
- Friction mitigation (Curation Levels) ✓

**The remaining gaps are implementation-level details**, not strategic errors. The plan is now **ready for technical implementation planning** with the following pre-requisites:

1. **Formalize the MCP tool contract** (JSON-RPC or OpenAPI spec)
2. **Define the concurrency model** (locking strategy)
3. **Specify Curation Level schemas** (what's required at each level)

Once these three items are documented, V2.8 implementation can begin with confidence.

**Grade: B+ → A-** (significant improvement; needs polish on implementation specs)

---

## Pre-requisites for Implementation Planning

Before generating technical implementation plans for each version, the following specs should be finalized:

### For V2.7
- `describes` field schema and validation rules
- Staleness detection algorithm (mtime vs explicit date)

### For V2.8
- Complete SessionContext dataclass definition
- Layer boundaries (what lives in Core vs IO vs UI)
- Transaction/commit semantics

### For V2.9
- Curation Level schema requirements (Level 0/1/2)
- install.py bootstrap flow and error handling
- Schema versioning migration logic

### For V3.0
- Full MCP tool specifications (OpenAPI or JSON-RPC)
- Concurrency model and locking strategy
- Config cascade resolution implementation
- Typed edge validation matrix

---

*End of review. Ready to proceed to implementation planning for V2.7/V2.8 when pre-requisites are addressed.*
