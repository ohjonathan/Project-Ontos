---
id: claude_v3_master_plan_review
type: atom
status: complete
depends_on: [v2_strategy]
concepts: [architecture, v3, review, mcp]
---

# Architectural Review: v3_master_plan_context_kernel.md

**Reviewer:** Claude Opus 4.5 (Architectural Analysis)
**Date:** 2025-12-19
**Document Under Review:** Strategic Master Plan & Context Kernel v2.2.0 (Gemini 3 Thinking)

---

## Part 1: Honest Feedback

### 1.1 What the Document Gets Right

**Strong strategic framing.** The "Context Death" problem statement is crisp and defensible. The dual-ontology model (Space vs Time) is a genuine insight that differentiates Ontos from RAG-based approaches.

**Good use of ADRs.** Documenting what was *rejected* (ADR-001 through ADR-003) is excellent practice. This prevents future engineers from re-proposing the same ideas.

**The "Librarian's Wager" is intellectually honest.** Acknowledging the friction-signal tradeoff as a *bet* rather than a certainty shows maturity. The 5%/40% hypothesis is testable.

**Phase boundaries are clear.** V2.x = Remediation (humans), V3.0 = Protocol (agents), V3.1+ = Scale. This communicates intent well.

### 1.2 Structural Weaknesses

**1. The V2.8 → V2.9 → V3.0 Transition is Underspecified**

The plan calls for:
- V2.8: Split `ontos_end_session.py` into `ontos.lib.logic` + `ontos.lib.ui`
- V2.9: Add `install.sh` bootstrap + unified CLI
- V3.0: `pip install ontos` + MCP server

This is a **major architectural cliff**. Consider:

| Aspect | V2.9 (Scripts) | V3.0 (Package) |
|--------|----------------|----------------|
| Installation | Copy files | `pip install` |
| Updates | `git pull` | `pip upgrade` |
| Configuration | `ontos_config.py` in repo | ??? |
| Data location | Same repo | Same repo (but logic is external) |

**The config story is missing.** If logic moves to a system package, where does user config live? The plan says "User repo contains only Data/Config" but doesn't specify:
- How does the system-installed `ontos` CLI find the repo's config?
- What happens when config schema changes between versions?
- How do you run `ontos serve` if it's not in the repo?

**2. The God Object Refactor (V2.8) Has Hidden Complexity**

The plan says: *"Split into ontos.lib.logic (Headless/Pure Python) and ontos.lib.ui (Interactive Wrapper)"*

This is necessary but insufficient. Looking at `ontos_end_session.py` (1,625 lines), the real challenge is **state threading**, not just I/O separation:

```
Current flow:
1. Parse git diff → extract file changes
2. Prompt user for session metadata
3. Generate log from template
4. Write file to disk
5. Suggest graduation (if proposal)
6. Update decision_history.md
```

Steps 1, 3, 4, 5, 6 are pure logic. Step 2 is UI. But the *sequencing* depends on user choices at step 2 affecting steps 3-6.

**The document doesn't address:**
- How does the MCP server handle the stateful multi-step workflow?
- If an agent calls `create_log()`, does it pass all metadata upfront, or is there a session object?
- What's the transaction boundary if step 5 fails after step 4 succeeds?

**3. "Typed Edges" (V3.0) Needs More Rigor**

The plan proposes: `implements`, `tests`, `deprecates`

Questions not addressed:
- What are the validation rules? Can an `atom` implement another `atom`? Can a `log` deprecate a `strategy`?
- How do typed edges interact with `depends_on`? Are they additive or orthogonal?
- What happens to existing `depends_on` relationships? Migration path?

**4. The S3 Deferral is Correct, But the MCP Credential Story is Problematic**

The S3 analysis doc (which I cross-referenced) proposes using an MCP server for S3 operations. But this creates a **circular dependency**:

- V3.0 introduces `ontos serve` (Ontos as MCP server)
- S3 integration uses an *external* MCP server for credentials
- So running Ontos MCP requires another MCP server?

This needs clarification. Is the S3 MCP server a peer to Ontos, or is it composed into Ontos's server?

### 1.3 Logical Inconsistencies

**"Zero-Dependency" Rule vs. V3.0 Reality**

The plan states: *"All V2 tools must run on Python Standard Library (3.9+) ONLY. No pip install until V3.0."*

But V3.0 introduces `pip install ontos` with `boto3` as a dependency. This is a **breaking change to the philosophy**, not just an implementation detail. Users who chose Ontos *because* of zero-dependency will face:
- New failure modes (boto3 conflicts with other packages)
- Security audit surface expands dramatically

The plan should explicitly acknowledge: *"V3.0 trades zero-dependency for capability. This is the right tradeoff because..."*

**The "SWE-bench Sim" (V3.0) is Vaporware**

The plan says: *"Benchmark Ontos vs Control on 'First-Pass Yield' (Churn Reduction)."*

No details on:
- What's the experimental design?
- What tasks are in the benchmark?
- How do you measure "churn reduction" without controlled human subjects?
- What's the success threshold?

This is listed as a V3.0 feature, but it's actually a *validation methodology*. It should be split out or marked as speculative.

---

## Part 2: What Can Be Improved

### 2.1 Add a Configuration Management Story

**Current gap:** The plan is silent on how config evolves when logic separates from data.

**Proposed addition (V2.9 or V3.0):**

```yaml
# .ontos/config.yaml (in repo)
version: 3.0
mode: prompted
s3:
  enabled: true
  bucket: my-team-ontos
  region: us-west-2
```

```python
# System-installed ontos reads repo config
$ ontos serve  # Reads .ontos/config.yaml from cwd
$ ontos --project ~/my-repo serve  # Explicit path
```

### 2.2 Define the MCP Tool Contract Early

**Current gap:** V3.0 mentions "MCP Server" but doesn't specify the tool interface.

**Proposed addition (V2.8 or V2.9):**

Even before implementing the server, define the tool schema:

```json
{
  "tools": [
    {
      "name": "ontos_get_context",
      "description": "Retrieve relevant context for a query",
      "parameters": {
        "query": "string",
        "max_tokens": "integer",
        "include_history": "boolean"
      }
    },
    {
      "name": "ontos_log_session",
      "description": "Create a session log",
      "parameters": {
        "event_type": "enum[feature,fix,refactor,...]",
        "goal": "string",
        "decisions": "string[]",
        "impacts": "string[]"
      }
    }
  ]
}
```

This forces design decisions about stateless vs. stateful operations.

### 2.3 Add Concurrency Considerations

**Current gap:** No mention of multi-agent or multi-developer scenarios.

**Risk scenarios:**
1. Two Claude instances archive sessions simultaneously → race condition on `decision_history.md`
2. One agent runs `ontos serve` while another runs `ontos log` → write conflicts
3. Developer pushes while agent is mid-session → stale context

**Proposed addition (V2.8 or V2.9):**

Add a locking mechanism:

```python
# .ontos/locks/session.lock
# Created on session start, released on end
# If lock exists, warn: "Session in progress by [agent/user]"
```

Or adopt an append-only log format that doesn't require locks (conflict-free).

### 2.4 Specify Schema Evolution Strategy

**Current gap:** What happens when frontmatter schema changes?

**Example:** V3.0 adds `describes` field. Existing documents don't have it.

**Proposed addition (V3.0):**

```yaml
# Schema versioning in frontmatter
---
ontos_schema: 3.0
id: my_doc
type: atom
describes: [other_atom]  # New in 3.0
---
```

Migration script:
```bash
$ ontos migrate --to 3.0  # Adds missing fields with defaults
```

### 2.5 The "Obsidian Export" Feels Like a Distraction

**Current assessment:** V2.9 includes Obsidian export as a "Zero-Dep Wow Factor."

**Concern:** This is a nice-to-have, not a must-have. It adds code surface without solving core problems.

**Recommendation:** Move to V3.1+ or make it a community contribution. V2.9 should focus on installation UX and CLI unification.

---

## Part 3: Unaddressed Possibilities, Solutions, and Issues

### 3.1 The "Growing Context Window" Problem

**Issue not addressed:** Claude's context window is now 200K tokens. GPT-4 is 128K. What happens when context windows reach 1M+?

**The existential question:** If an agent can fit the entire codebase in context, why maintain a structured graph?

**Answer the plan should provide:**
- Ontos provides *curated* context, not raw context
- Even with 1M tokens, you can't fit *history* (every decision ever made)
- The graph enables *reasoning about relationships*, not just retrieval

This should be explicitly addressed because investors/adopters will ask.

### 3.2 Multi-Repo and Monorepo Scenarios

**Issue not addressed:** Real teams have:
- Multiple repos that share strategy/kernel docs
- Monorepos with independent subprojects

**Proposed future feature (V3.2?):**

```yaml
# .ontos/config.yaml
federation:
  shared_kernel: git@github.com:team/ontos-kernel.git
  sync_on: [pull, push]
```

This enables cross-repo knowledge graphs without duplicating kernel docs.

### 3.3 The "Agent Writes Its Own Context" Problem

**Issue not addressed:** If agents become primary users (V3.0), they will:
1. Read the context map
2. Make decisions based on context
3. Write session logs documenting those decisions
4. Which become context for future agents

**Risk:** Feedback loops. An early agent misunderstands something, documents it, and all future agents inherit the misunderstanding.

**Proposed mitigation:**
- `source: agent|human` field in logs
- Different trust levels for agent-generated vs human-curated content
- Periodic human review checkpoint (e.g., "Review agent logs from last week")

### 3.4 No Rollback Story

**Issue not addressed:** What if a bad session log or incorrect `depends_on` gets committed?

**Current state:** User must manually edit and recommit.

**Proposed addition (V2.9 or V3.0):**

```bash
$ ontos rollback log_20251219_bad_decision
# Moves log to rejected/, updates decision_history with "ROLLED_BACK"
```

### 3.5 The "install.sh" Maintenance Burden

**The plan asks:** *"Does the install.sh approach create a maintenance nightmare before we get to PyPI?"*

**My answer: Yes, potentially.**

Shell scripts are fragile across:
- macOS (zsh) vs Linux (bash) vs Windows (WSL)
- Different Python installation methods (pyenv, homebrew, system)
- Permissions issues (`curl | sudo bash` is an anti-pattern)

**Alternative proposal:**

Skip `install.sh` entirely. Instead:

```bash
# V2.9: Single-file installer (Python, not shell)
curl -O https://raw.githubusercontent.com/ohjona/Project-Ontos/main/install.py
python3 install.py
```

A Python installer can:
- Detect environment properly
- Handle errors gracefully
- Work identically on all platforms

This is still "one command" but avoids shell fragility.

### 3.6 The "Activation" UX is Still Suboptimal

**Current state:** User must say "Activate Ontos" or "Ontos" to trigger context loading.

**Issue:** This requires agent instructions to be present in the prompt. If user forgets, no context.

**V3.0 opportunity:** With MCP, the agent can *proactively* query Ontos:

```
Agent startup:
1. Check if MCP server "ontos" is available
2. If yes, call ontos_get_context(query="session_start")
3. Silently inject context into working memory
```

This makes activation *implicit*, not explicit. The user never says "Ontos" — it just works.

### 3.7 What About Partial Context Loading?

**Issue not addressed:** The current model is "load relevant docs by ID."

**Problem:** For large projects, even "relevant" docs might be 50K tokens. The agent can't load all of them.

**Proposed addition (V3.0):**

```json
// MCP tool response
{
  "context": "...",
  "token_count": 12000,
  "truncated": true,
  "available_depth": ["summary", "full", "with_history"],
  "next_action": "call with depth='full' for complete context"
}
```

This enables *progressive disclosure* of context.

---

## Summary of Recommendations

| Priority | Recommendation | Target Version |
|----------|----------------|----------------|
| **Critical** | Define MCP tool contract | V2.9 |
| **Critical** | Add concurrency/locking design | V2.8 |
| **Critical** | Specify config management for V3.0 | V2.9 |
| **High** | Address schema evolution strategy | V3.0 |
| **High** | Replace `install.sh` with Python installer | V2.9 |
| **Medium** | Add rollback capability | V3.0 |
| **Medium** | Address "growing context window" question | Strategy doc |
| **Low** | Defer Obsidian export to V3.1+ | V2.9 |
| **Low** | Consider multi-repo federation | V3.2+ |

---

## Final Assessment

**The plan is directionally correct but underspecified for the V2.8-V3.0 transition.** The biggest risks are:

1. **State management** in the God Object refactor — needs explicit session/transaction design
2. **Configuration portability** when logic separates from data — not addressed
3. **Concurrency** in multi-agent scenarios — not addressed

The Gemini analysis correctly identified the "Tool → Protocol" pivot as the strategic inflection point. However, the *operational mechanics* of that pivot need more detail before implementation.

**Recommendation:** Before coding V2.8, produce a companion document: **"V3.0 MCP Interface Specification"** that defines:
- Every tool the server will expose
- The state model (stateless RPC vs. session-based)
- Authentication and multi-tenant considerations
- Failure modes and graceful degradation

This will force the hard design decisions *before* they become implementation surprises.

---

*End of review. ~2,800 words.*
