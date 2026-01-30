# v3.2 Ontos Activation — Spec Review (Peer)

## Your Role
**Peer Reviewer:** Gemini 2.5 Pro
**Date:** 2026-01-29
**Review Type:** Spec Review (Proposal)

---

## Part 1: Completeness Check

| Expected Section | Present? | Adequate? | Notes |
|------------------|----------|-----------|-------|
| Problem statement | ✅ | ✅ | Clear definition of the "context loss" problem. |
| Design philosophy | ✅ | ✅ | "No session capture" is a crucial boundary definition. |
| Current state analysis | ✅ | ✅ | Identifies gaps in AGENTS.md and Map structure. |
| Proposed solution | ✅ | ✅ | Auto-sync, Tiered Map, Staleness checks. |
| Implementation plan | ✅ | ✅ | Phased approach is logical. |
| Testing strategy | ✅ | ✅ | Covers unit, integration, and manual verification. |
| Risks & mitigations | ✅ | ✅ | Addresses overwrite risks and tool compatibility. |
| Success criteria | ✅ | ✅ | Clear metrics (tokens, steps). |

**What's missing that should be here?**
*   **Performance Impact Analysis:** The proposal adds logic to `ontos map` (checking git branch, log parsing, doc status). `ontos map` is currently a fast, frequently run command. There is no analysis of whether these additions will introduce noticeable latency.

---

## Part 2: Quality Assessment

| Aspect | Rating | Notes |
|--------|--------|-------|
| Problem/solution fit | **Good** | Tiered context directly addresses the re-activation friction/cost. |
| Technical approach | **Adequate** | Modifying `ontos map` to sync `AGENTS.md` is technically sound but introduces side effects to a deterministic read-only command. |
| Scope boundaries | **Good** | Rigidly adhering to "Project vs. Session" context is the correct strategic choice. |
| Implementation feasibility | **Good** | No complex dependencies or novel tech required. |
| User experience | **Adequate** | The "Auto-sync" is invisible magic. It helps *if* the agent re-reads the file. |

---

## Part 3: Open Questions Analysis

| Question | Your Research/Analysis | Recommendation | Confidence |
|----------|------------------------|----------------|------------|
| **Q1: Auto-Sync Scope** | `ontos map` is often run just to check the graph. Force-creating `AGENTS.md` would be intrusive for users who deleted it intentionally. | **B) Only sync if exists.** Respect user intent. | High |
| **Q2: Tier 1 Token Budget** | 2k tokens is roughly 1.5 pages of dense text. This is enough for a summary but tight for "Active Work" if logs are verbose. | **B) ~2k tokens.** Start tight; expand if needed. | High |
| **Q3: Active Work Detection** | "In progress" docs (metadata) and "Recent logs" (history) are reliable. "Uncommitted changes" (git) is noisy—often just linting or minor edits, not "intent." | **Modified D:** Recent logs + `status: in_progress` docs. **Exclude uncommitted git changes** to avoid noise and performance hits. | Medium |
| **Q4: CLAUDE.md Relationship** | `CLAUDE.md` is often heavily customized by users for style rules. Overwriting it risks data loss. | **B) Keep manual.** Do not touch user configs. | High |

---

## Part 4: Implementation Feasibility

| Proposed Feature | Feasible? | Concerns |
|------------------|-----------|----------|
| AGENTS.md auto-sync on `ontos map` | ✅ | Easy to implement. Risk of overwriting user customizations if not handled carefully. |
| Tiered context map (~2k/10k/50k) | ✅ | Markdown structure (H2/H3) handles this naturally. |
| Staleness detection in doctor | ✅ | Trivial timestamp comparison. |
| Cross-tool consistency | ⚠️ | **Major Concern:** We cannot force tools to re-read `AGENTS.md` after compaction. The file updating on disk doesn't mean the context window updates. |

**Implementation questions the spec doesn't answer:**
*   **Latency:** Does parsing all logs to find "Recent Activity" slow down `ontos map`? (Currently map only reads frontmatter, not full log content).
*   **Locking:** What if `AGENTS.md` is open/locked by the user or another process?

---

## Part 5: User Experience Analysis

| Scenario | Current Behavior | Proposed Behavior | Actually Better? |
|----------|------------------|-------------------|------------------|
| **User notices context loss** | Manual re-run `ontos map` (read ~12k tokens) | Same, but read ~2k tokens (Tier 1) | ✅ **Yes** (Cheaper/Faster) |
| **User doesn't notice** | Agent hallucinates or asks for context | Agent (hopefully) sees updated AGENTS.md | **Unclear** (Depends on tool) |
| **Tool re-reads AGENTS.md** | Gets stale stats/instructions | Gets fresh branch/log info | ✅ **Yes** |

**What's the actual improvement in user experience?**
The primary win is the **Tiered Context Map**, which makes the *inevitable* re-activation less painful/expensive. The AGENTS.md sync is a nice-to-have but relies on tool behavior we don't control.

---

## Part 6: Issues Found

**Major (Should Fix):**

| # | Issue | Section | Suggestion |
|---|-------|---------|------------|
| **P-M1** | **Implicit Side Effects** | Proposed Solution (1) | `ontos map` is a read-operation generator. Adding file-writing side effects (updating `AGENTS.md`) violates the Principle of Least Surprise. **Fix:** Add a flag `--sync-agents` (default True if exists) or make it explicit in output. |
| **P-M2** | **Performance Risk** | Proposed Solution (2) | Parsing log *content* (to get summary/active work) for Tier 1 changes `ontos map` from O(docs) to O(docs + logs). **Fix:** Only read log frontmatter/filenames, or cache log summaries. |

**Minor (Consider):**

| # | Issue | Section | Suggestion |
|---|-------|---------|------------|
| **P-m1** | **Overwriting Customizations** | Risks | Ensure the sync respects a `# USER CUSTOM` block or strictly only updates specific sections of `AGENTS.md`. |
| **P-m2** | **Definition of "Active"** | Q3 | "Uncommitted changes" is a poor proxy for "Active Work" (could be `git add .` of a typo fix). Stick to Ontos artifacts (logs/docs). |

---

## Part 7: What's the Architect Not Seeing?

1.  **What assumption in this proposal is most likely wrong?**
    *   *Assumption:* That updating `AGENTS.md` on disk helps an agent that has lost context.
    *   *Reality:* Most agents load context at the *start of a session. If compaction happens, they don't fundamentally "know" to look at the file system again unless explicitly instructed or if the tool treats that file as a dynamic "system prompt" (which varies wildly by tool).

2.  **What user behavior does this assume that might not hold?**
    *   That users run `ontos map` frequently enough to keep `AGENTS.md` "fresh" without it being annoying. If `ontos map` becomes slower due to log parsing, users will run it less.

3.  **What's conspicuously absent from this proposal?**
    *   **Performance benchmarks.** `ontos map` must remain sub-second for small/medium projects.

4.  **Where is this proposal overconfident?**
    *   In the ability to "Detect Active Work" via heuristics (Q3). This is notoriously hard to get right without false positives.

---

## Part 8: Verdict

**Recommendation:** **Approve with changes**

**Blocking issues:** 0
**Major concerns to address before implementation:**

1.  **Performance:** Ensure `ontos map` remains fast. Do not parse full log files for Tier 1 generation; rely on frontmatter or file stats.
2.  **Side Effects:** Explicitly notify the user when `AGENTS.md` is updated by `ontos map`.
3.  **Heuristics:** Drop "uncommitted changes" from Active Work detection (too noisy). Stick to explicitly tracked Ontos state.

**Summary:**
The **Tiered Context Map** is a high-value, low-risk improvement that directly solves the "expensive re-activation" problem. The **AGENTS.md Auto-Sync** is useful but secondary; implementation should ensure it doesn't degrade the performance of the core `map` command.
