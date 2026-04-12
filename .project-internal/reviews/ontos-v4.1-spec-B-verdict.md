# Review Verdict: Ontos v4.1 Implementation Spec

**Phase:** B (Spec Review)
**Date:** 2026-04-11
**Spec:** `Ontos-v4.1-Implementation-Spec.md` v1.0 (1,776 lines)
**PR:** Spec file (PR #85 not yet created -- review against spec file)
**Reviewers:** 9 reviewers across 3 model families (Claude Code, Codex, Gemini CLI agent teams)
**Overall Status:** Needs Revision

---

## 1. Cross-Platform Verdict Summary

| Platform | Model Family | Verdict | Reviewer Breakdown | Blocking Issues | Top Concern |
|----------|--------------|---------|-------------------|-----------------|-------------|
| Claude Code | Anthropic (Opus 4.6) | Needs Revision | 0/3 approve, 3/3 Request Changes | 6 | FTS5 schema internally contradictory (B-1) |
| Codex | OpenAI | Needs Revision | 1/3 approve (R2 Alignment), 2/3 Request Changes | 3 (broad) | MCP surface contract contradictory across modes (B2) |
| Gemini CLI | Google | Needs Revision | 1/3 approve (R2 Alignment), 2/3 Request Changes | 4 | Write tool atomicity risk (B-02) |

**Cross-platform consensus: Needs Revision.**

Aggregate: 7/9 Request Changes, 2/9 Approve. Both approvals came from Alignment-lens reviewers (Codex R2, Gemini R2) focused on proposal fidelity rather than implementation readiness. All 6 Peer and Adversarial reviewers across all platforms requested changes.

All three platforms independently noted the spec is fundamentally sound and architecturally correct. The issues are concentrated in data-model consistency, safety-claim accuracy, and OQ resolution -- all fixable in a focused revision pass without rearchitecting.

---

## 2. Critical Blocking Issues (Combined)

The three platforms use different granularity: Claude Code filed 6 precise issues with line-number evidence; Codex filed 3 broader issues covering more surface area each; Gemini filed 4 issues with moderate depth. The table below normalizes to topic-based unified IDs.

| # | Issue | Flagged By | Section | Category | Action Required |
|---|-------|------------|---------|----------|-----------------|
| **UB-1** | **FTS5 schema broken / not implementable.** The `fts_content` table references a `concepts` column that does not exist in the `documents` table. Two contradictory schema definitions exist (Section 4.1: 3 columns; Section 6.1: 5 columns). BM25 weight vector matches only one. FTS5 external content mode maps by ordinal position, not name -- the `documents` ordinals do not align with `fts_content` columns, causing `snippet()` to return data from wrong columns at runtime. | **3/3** -- CC B-1, Codex B1, Gemini B-01 (partial) | 4.1, 4.6, 6 | Data model / search architecture | Consolidate to single canonical schema in Section 4.1. Add `concepts TEXT` to `documents`. Remove duplicate from Section 6.1. Switch to standalone FTS5 (not external content) or explicitly align ordinals. Fix BM25 weights. |
| **UB-2** | **Write atomicity overstated.** `SessionContext.commit()` uses sequential temp-then-rename in Phase 2. If the process crashes after renaming 3 of 7 files, already-renamed files are NOT rolled back. The spec calls this "atomic multi-file writes" but it is best-effort sequential commit with temp-file cleanup. | **3/3** -- CC B-3 (part), Codex B3 (part), Gemini B-02 | 4.8, 4.9, 10.3 | Data integrity / safety | Downgrade atomicity claim to "best-effort sequential commit." Add git clean-state precondition for `rename_document()`. Document recovery path (`git checkout -- .`). |
| **UB-3** | **Locking mechanism deficient.** The MCP workspace lock (`.ontos.lock`) and CLI write lock (`.ontos/write.lock`) are completely different files with zero coordination. Simultaneous CLI and MCP writes proceed concurrently and corrupt workspace state. Gemini additionally identified PID-reuse vulnerability in the proposed PID-based stale lock detection. | **3/3** -- CC B-3 (part), Codex B3 (part), Gemini B-03 | 4.8, 4.9, 8 | Concurrency / locking | Unify MCP and CLI lock files or have MCP write tools acquire both locks. Address PID-reuse risk (use creation timestamp + PID, or flock-based locking). Consolidate duplicate locking logic with existing `SessionContext`. |
| **UB-4** | **`rename_document()` references nonexistent functionality.** (a) Spec references `_compute_rename_plan()` which does not exist; actual function is `_prepare_plan()` (line 278) with different signature and return type. (b) The existing CLI rename command does NOT perform filesystem file renames -- zero calls to `os.rename()`, `Path.rename()`, or `SessionContext.buffer_move()` in 1,362 lines. The spec's OQ-2 recommendation (B) claims "the existing `ontos rename` CLI command already handles file renaming" -- factually incorrect. `RenameDocumentResponse` includes `old_path`/`new_path` for a feature that does not exist. | **1.5/3** -- CC B-2 (full with codebase evidence), Codex B2 (tangential via MCP surface), Gemini -- | 4.8.2, 5 (OQ-2) | Factual error / scope ambiguity | Correct function reference to `_prepare_plan()`. Resolve OQ-2 per Section 6 recommendation. Remove or repurpose `old_path`/`new_path` fields. |
| **UB-5** | **MCP surface contract contradictory across modes.** The spec simultaneously claims: "existing tools stay identical," "all tools gain `workspace_id`," "`get_context_bundle` exists in both modes," "some existing tools reject non-primary workspace IDs," and "write tools are absent but attempted calls return errors." These do not resolve to one consistent MCP surface. The `_invoke_tool()` routing logic is underspecified -- it passes `SnapshotCacheView` to read tools but needs `portfolio_index` for portfolio tools, with no mechanism to decide which. | **2/3** -- CC B-5 + B-4 (partial), Codex B2 (full systemic framing) | 4.4, 4.7, 4.8, 4.10, 6, 7, 10 | API / compatibility | Define one authoritative tool-availability matrix for `ontos serve` vs `ontos serve --portfolio`. Specify `_invoke_tool()` routing (separate wrappers per tool category recommended). Resolve `--read-only` observable behavior (tools absent vs. tool-level rejection). |
| **UB-6** | **`verify` subcommand silently omitted from Proposal D8.** Proposal D8 specifies a `verify` subcommand that "compares the DB against `projects.json` and reports discrepancies" for gradual `.dev-hub` transition. The spec does not mention this anywhere and does not acknowledge the omission. The 2-week transition criterion is also silently dropped. | **2/3** -- CC B-6, Gemini B-01 (partial) | N/A (missing) | Silent proposal deviation | Either add `verify` to Track A scope, or explicitly defer with rationale in Exclusion List (Section 9). Silent omission is not acceptable for an approved proposal decision. |
| **UB-7** | **`get_context_bundle()` crashes in single-workspace mode.** When `workspace_id` is passed in single-workspace mode (where `portfolio_index is None`), the code falls to the `else` branch and calls `_validate_workspace_id(portfolio_index, workspace_id)`. Since `portfolio_index is None`, this causes `AttributeError`. This contradicts Section 4.10's contract that `workspace_id` is "accepted but ignored." | **1/3** -- CC B-4 (single-platform finding) | 4.7, 4.10 | Logic error | Add guard: if `portfolio_index is None` and `workspace_id is not None`, either ignore `workspace_id` (per Section 4.10) or return `isError: true` with `E_CROSS_WORKSPACE_NOT_SUPPORTED`. |

**Summary by consensus tier:**
- **Universal (3/3):** UB-1 (FTS5), UB-2 (atomicity), UB-3 (locking) -- highest confidence
- **Strong (2/3):** UB-5 (MCP surface), UB-6 (verify omission) -- high confidence
- **Single-platform:** UB-4 (rename factual errors, CC), UB-7 (single-ws crash, CC) -- preserved per consolidation rules; codebase evidence is concrete

---

## 3. Major Issues (Combined)

Merged should-fix issues from all three platforms, deduplicated by topic.

| # | Issue | Flagged By | Section | Action Required |
|---|-------|------------|---------|-----------------|
| US-1 | **Bundle ranking determinism.** No secondary tiebreaker in `get_context_bundle()` scoring leads to prompt instability and degraded LLM cache performance. | CC S-11, Gemini B-04 (reclassified from blocking) | 4.7 | Add alphabetical document ID tiebreaker for deterministic output. *Note: Gemini classified as blocking; Claude Code classified as should-fix. Downgraded here because prompt instability is a quality concern, not a crash.* |
| US-2 | **Typed write-error schema missing.** The spec requires structured write-tool errors repeatedly in prose and tests but never defines the typed error payload schema for `(what happened, why, how to fix)`. How `isError: true`, `structuredContent`, and text fallback interact is unspecified. | Codex S1 | 4.8, 4.11, 6, 10.3 | Add shared error response model for write-tool failures. Specify exact `--read-only` observable behavior. |
| US-3 | **Track B "simple wrapper" language misleading.** The spec presents write tools as mostly wrapping existing CLI logic, but existing command implementations do not map cleanly to MCP contracts -- especially scaffold, rename, promote, and log. | CC B-2 (partial), Codex S2 | 4.8, 8 | Replace "simple wrapper" language with explicit reuse plan: which helpers are reused unchanged, which need adapter refactors, which are greenfield MCP behavior. |
| US-4 | **`promote_document` mixed success/error semantics.** Returns `success: false` with `isError: false`, inconsistent with other write tools. | CC S-1 | 4.8.4, 4.11 | Use `isError: true` with `E_PROMOTION_BLOCKED` for uniformity. |
| US-5 | **`partial` project classification ambiguous.** Prose is unclear on exact conditions. | CC S-2 | 4.3 | Use proposal's explicit boolean: `(has_readme AND NOT has_ontos) OR (has_ontos AND doc_count < 5)`. |
| US-6 | **`PORTFOLIO_CONFIG_PATH` doesn't expand `~`; no `mkdir -p` for `~/.config/ontos/`.** | CC S-6, S-7 | 4.2, 4.1 | Use `.expanduser()` or `Path.home()`. Create directory on first run. |
| US-7 | **`search_fts()` two queries without shared transaction.** Main query and COUNT query can see different states. | CC S-8 | 4.6 | Wrap in explicit `BEGIN`. |
| US-8 | **`.ontos.lock` not in `.gitignore` as implementation step.** | CC S-9 | 4.9 | Add to file change table. |
| US-9 | **`rebuild_workspace()` failure after write not handled.** | CC S-10 | 4.8 | Catch, log to stderr, add warning to write tool response. |
| US-10 | **Slug collision for same-named dirs in different `scan_roots`.** Both become same slug, causing `PRIMARY KEY` violation. | CC S-12 | 4.3 | Add collision detection/resolution. |
| US-11 | **Bundle/refresh behavior under-specified.** Missing tie-breakers, undefined `top_N`, ambiguous single-workspace flow, dropped `.dev-hub` reconciliation path. | Codex S3 | 4.7, 4.10, 6 | Define deterministic ordering and refresh semantics end-to-end. |
| US-12 | **Risk assessment understates real implementation risk.** Shared work is not purely mechanical; Track B is not a light wrapper. | Codex S4 | 8 | Re-rate after design corrections. |
| US-13 | **Track A -> B handoff assumptions unspecified.** Track B should explicitly state what state it assumes Track A leaves. | Gemini S-01 | 4.8, 8 | Clarify handoff state between tracks. |

---

## 4. Minor Issues

24 minor issues across all platforms (Claude Code: 20, Codex: 4, Gemini: 0), grouped by category:

**API / Registration (4):** Registration helper signatures not provided (CC M-1); `tools/list` backward compat claim imprecise (CC S-3, as minor context); `scaffold_document` wraps differently than proposal (CC M-18); pyproject.toml version bump not mentioned (CC M-20).

**Database / Search (4):** Connection strategy for `rebuild_all()` batch unclear (CC M-2); COUNT query slow at scale (CC M-3); FTS5 query edge cases -- operators, column filters (CC M-10); `threading.Lock` vs `asyncio.Lock` unclear (CC M-15).

**Bundle / Scoring (3):** Lost-in-the-middle odd-length list underspecified (CC M-6); no kernel size upper bound (CC M-13); token estimation error for code-heavy docs (CC M-14).

**Write Tools / Safety (4):** Lock empty-after-crash edge case (CC M-4); `scaffold_document()` type rejection rationale (CC M-5); `log_session()` git subprocess error handling (CC M-9); write-tool annotation `destructiveHint=False` on `rename_document()` too optimistic (Codex M1).

**Edge Cases (4):** Deleted projects in `projects.json` (CC M-11); symlink loops / missing dirs (CC M-12); partial workspaces without `.ontos.toml`, `event_type="session"` semantics, multi-process portfolio DB contention (Codex M4).

**Documentation (3):** Architecture diagram missing `bundler.py`, `scanner.py`, `portfolio_config.py` (CC M-19); packaging prose internally inconsistent on Python-version handling (Codex M2); diagrams omit failure/state transitions (Codex M3).

**Test Gaps (2):** Portfolio DB corrupt-rebuild test underspecified (CC M-7); `rebuild_all()` per-workspace error handling unspecified (CC M-8). FTS5 non-ASCII, concurrent writes, sanitization coverage gaps noted (CC M-17).

---

## 5. Cross-Platform Agreement Analysis

### Universal agreement (all 3 platforms flagged)

These are the highest-signal findings:

1. **FTS5 schema is broken (UB-1).** Every platform independently identified the `concepts` column problem and/or the schema contradictions. This is the highest-confidence finding across all 9 reviewers.
2. **Write atomicity is overstated (UB-2).** All three platforms found `SessionContext.commit()` does not provide the atomicity the spec claims.
3. **Locking needs work (UB-3).** All three platforms identified locking deficiencies -- though from different angles (dual lock gap, PID reuse, CLI/MCP coordination).
4. **The spec is fundamentally sound.** All three platforms praised the research integration, backward-compatibility discipline, and overall design quality. The direction is correct; the issues are in specification accuracy.

### 2-of-3 agreement

- **MCP surface contract contradictory (UB-5):** Claude Code (via B-5 + B-4) and Codex (via B2). Gemini did not flag this -- likely because Gemini's R2 (Alignment) approved and Gemini's adversarial reviewer focused more on concurrency than API coherence.
- **`verify` subcommand omitted (UB-6):** Claude Code (B-6) and Gemini (B-01 partial). Codex did not flag this -- Codex's alignment reviewer focused on the tool surface contract rather than individual proposal decision cross-checking.

### Single-platform findings

These are often the most valuable, reflecting each model family's distinct strengths.

**Claude Code only (Anthropic):**

| Finding | Source | Why Others Missed It |
|---------|--------|---------------------|
| Existing CLI rename does NOT do file renames (zero `os.rename()` calls in 1,362 lines) | B-2, R3 | Only Claude Code's R3 read the entire `rename.py` file. This is decisive for OQ-2. |
| `_compute_rename_plan()` references wrong function; actual is `_prepare_plan()` | B-2, R1 | Requires tracing function signatures against codebase |
| `get_context_bundle()` crashes with `workspace_id` in single-workspace mode | B-4, R3 | Requires tracing full code path through spec logic |
| `_invoke_tool()` routing logic underspecified | B-5, R1 | Requires understanding the existing handler dispatch pattern |

**Codex only (OpenAI):**

| Finding | Source | Why Others Missed It |
|---------|--------|---------------------|
| MCP surface contract as a single interconnected systemic issue (workspace_id + refresh() + --read-only + tool availability) | B2 | Broader framing that subsumes multiple scattered issues. Claude Code caught the symptoms individually; Codex identified the systemic coherence problem. |
| Typed write-error schema missing | S1 | UX-layer concern that others treated as implicit |
| `--read-only` as a blocking contract problem (tools absent vs. tool-level rejection) | B2 | Others treated as minor or did not flag |
| Proposal D2 mismatch for existing-tool `workspace_id` behavior | B2, R2 | Only Codex R2 traced input-schema changes vs. Pydantic output model changes |

**Gemini only (Google):**

| Finding | Source | Why Others Missed It |
|---------|--------|---------------------|
| PID-reuse vulnerability in locking | B-03, R1/R3 | Specific concurrency attack vector that others addressed at the design level (dual lock) rather than the mechanism level (PID reuse) |
| Bundle ranking determinism as blocking concern | B-04, R3 | Claude Code found the same issue but classified as should-fix. Gemini weighted prompt instability higher. |
| R2 approved (only approval across 9 reviewers from non-Alignment lens) | Verdict | Gemini R2 was labeled Alignment but described as "Technical" -- possible lens difference in Gemini's team configuration |

### Cross-platform disagreements

| Topic | Claude Code Says | Codex Says | Gemini Says | Type | Resolution |
|-------|-----------------|------------|-------------|------|------------|
| OQ-1: `get_context_bundle()` in single-ws mode | (B) Available in both modes | (A) Portfolio-only (majority); R1 dissents for (B) | *Misinterpreted* (see Section 6) | Genuine disagreement (2 valid positions) | Recommend (B) -- see Section 6 |
| OQ-2: Rename file path vs ID-only | (A) ID-only | (C) Configurable, ID-only default | *Misinterpreted* (see Section 6) | Compatible -- both default to ID-only | Recommend (A) -- see Section 6 |
| Bundle determinism severity | Should-fix (S-11) | Not flagged | Blocking (B-04) | Severity disagreement | Reclassified to should-fix (US-1) |
| Blocker ordering priority | FTS schema first | Tool surface contract first | Write atomicity first | Priority disagreement, not factual | All three are correct; ordering is a CA preference |
| Blocking issue granularity | 6 fine-grained issues | 3 broad systemic issues | 4 moderate issues | Framing difference | Both views preserved: systemic framing (Codex) illuminates coherence; granular framing (CC) enables targeted fixes |

**Notable absence of factual disagreements:** Across 9 reviewers and 3 model families, there are zero cases where one platform asserts a fact that another platform contradicts. All differences are in severity, priority, framing, or scope. This is strong evidence that the identified problems are real.

---

## 6. OQ-1 and OQ-2 Resolution

### Gemini OQ Misinterpretation

The spec defines:
- **OQ-1:** "Should `get_context_bundle()` be available in single-workspace mode?"
- **OQ-2:** "When renaming a document ID, should the tool also rename the file on disk?"

Gemini's consolidation addresses:
- "OQ-1 (Tool Error Response Strategy)" -- recommends `isError: true` pattern
- "OQ-2 (FTS5 Rebuild Concurrency)" -- recommends sequential locking during rebuilds

**These do not correspond to the actual open questions.** Gemini appears to have either relabeled its own findings as OQ-1/OQ-2 or had a context-loading issue where the OQ section was not properly ingested. Gemini effectively provides **no position** on the actual OQ-1 or OQ-2.

*Note:* Gemini's answers are not invalid in themselves -- the `isError: true` recommendation aligns with the spec's error handling design, and the sequential locking recommendation is a legitimate concern -- they simply answer different questions and are redirected to the relevant blocking/should-fix items.

### Aggregated Positions

| Open Question | Claude Code | Codex | Gemini | Recommendation to CA |
|---------------|-------------|-------|--------|---------------------|
| **OQ-1:** `get_context_bundle()` in single-ws mode | **(B)** Available in both modes, with logic fix from UB-7 | **(A)** Portfolio-only (R2 + R3); R1 dissents for (B) | *No valid position* (misinterpreted) | **(B) Available in both modes** |
| **OQ-2:** Rename file path vs. ID-only | **(A)** ID-only rename | **(C)** Configurable, conservative ID-only default | *No valid position* (misinterpreted) | **(A) ID-only rename** |

### OQ-1 Rationale

**Recommend (B): Available in both modes.**

Claude Code provides the stronger technical argument. Their R3 traced the actual crash path (UB-7) and demonstrated it is a localized logic fix, not a design flaw. The tool provides genuine value in single-workspace mode -- token budgeting, structured JSON output, staleness detection -- that `context_map` does not offer.

Codex's preference for (A) is motivated by reducing MCP surface-area risk and preserving the current 8-tool single-workspace contract. This is a valid concern, but one that the logic fix from UB-7 directly addresses. With only 2 valid platforms providing input, the decision weights depth of evidence: Claude Code demonstrated what breaks and how to fix it, while Codex argued for avoidance.

### OQ-2 Rationale

**Recommend (A): ID-only rename.**

Claude Code's codebase evidence is decisive. Their R3 read all 1,362 lines of `rename.py` and found: the existing CLI rename command does NOT perform filesystem file renames. There are zero calls to `os.rename()`, `Path.rename()`, or `SessionContext.buffer_move()`. The spec's recommendation of (B) -- "full rename when file name matches" -- was based on the factual claim that "the existing `ontos rename` CLI command already handles file renaming." This is incorrect.

Implementing file rename would be entirely new functionality requiring: path construction rules, case-sensitivity handling (macOS APFS), date-prefix conventions for logs, and git history considerations. This is unacknowledged scope creep that pushes Track B risk from MEDIUM-HIGH toward HIGH.

Codex's (C) -- configurable with ID-only default -- is compatible since the default behavior matches (A). The configuration toggle can be deferred to v4.2 if desired, alongside the file-rename implementation it would gate.

---

## 7. Risk Assessment Cross-Check

The spec rates: Track A = MEDIUM, Track B = MEDIUM-HIGH, Shared = LOW.

| Track | Spec Rating | Claude Code | Codex | Gemini | Recommendation |
|-------|-------------|-------------|-------|--------|----------------|
| Track A | MEDIUM | Agrees | Suggests possible re-rating after fixes | Agrees | **MEDIUM** -- no change needed. FTS5 fix (UB-1) is mechanical; it does not change the risk profile. |
| Track B | MEDIUM-HIGH | Agrees; notes rises to HIGH if file rename included | Agrees; notes "simple wrapper" language understates work | Agrees | **MEDIUM-HIGH** -- no change needed. OQ-2 = (A) removes the file-rename risk escalator. |
| Shared | LOW | Agrees | Agrees | Agrees | **LOW** -- no change needed. |

**No risk level upgrades required.** The key condition: OQ-2 must resolve to (A) ID-only. If the CA chooses (B) or (C) with file rename, Track B should be upgraded to **HIGH**.

Codex's observation that "Shared work is not purely mechanical" (S4) is noted but does not warrant a rating change -- the registration plumbing and schema work are bounded, even if slightly more complex than "LOW" implies.

---

## 8. Required Actions for CA (Prioritized)

| Priority | Action | Addresses | Effort | Source |
|----------|--------|-----------|--------|--------|
| **P1** | Unify FTS5 schema to single canonical definition; add `concepts TEXT` to `documents`; fix ordinal mapping or switch to standalone FTS5; fix BM25 weights | UB-1 | 1-2 hrs | 3/3 platforms |
| **P1** | Downgrade atomicity claim to "best-effort sequential commit"; add git clean-state precondition for `rename_document()`; document recovery path | UB-2 | 1 hr | 3/3 platforms |
| **P1** | Unify MCP and CLI lock files (or acquire both from MCP tools); address PID-reuse risk; consolidate with `SessionContext` lock | UB-3 | 1-2 hrs | 3/3 platforms |
| **P1** | Correct `_compute_rename_plan()` to `_prepare_plan()` with adaptation strategy; remove factual claim about existing file rename; resolve OQ-2 as (A) ID-only | UB-4 | 30 min | CC (decisive codebase evidence) |
| **P1** | Define authoritative tool-availability matrix for `ontos serve` vs `ontos serve --portfolio`; specify `_invoke_tool()` routing; settle `--read-only` behavior | UB-5 | 1-2 hrs | CC + Codex |
| **P1** | Address `verify` subcommand omission -- defer with rationale or add to scope | UB-6 | 15 min (defer) or 2-4 hrs (implement) | CC + Gemini |
| **P1** | Fix `get_context_bundle()` `workspace_id` guard for single-workspace mode; resolve OQ-1 as (B) | UB-7 | 30 min | CC (crash path traced) |
| **P2** | Add deterministic tiebreaker (alphabetical doc ID) to bundle scoring | US-1 | 15 min | CC + Gemini |
| **P2** | Add typed write-error schema; define `isError` / `structuredContent` / text fallback interaction | US-2 | 1 hr | Codex |
| **P2** | Replace "simple wrapper" language with explicit reuse plan per write tool | US-3 | 30 min | CC + Codex |
| **P2** | Standardize `promote_document` error semantics (`isError: true`) | US-4 | 15 min | CC |
| **P2** | Fix tilde expansion, `mkdir -p`, `partial` classification, line numbers, `.gitignore` step | US-5/6/7/8 | 30 min | CC |
| **P2** | Add slug collision handling, transaction wrapping for search, rebuild error handling | US-9/10/11 | 30 min | CC + Codex |
| **P2** | Clarify Track A -> B handoff state; re-rate risk after corrections | US-12/13 | 30 min | Codex + Gemini |

**Total estimated P1 effort:** 5-8 hours of focused spec revision.
**Total estimated P2 effort:** 3-4 hours (can be addressed during implementation).

---

## 9. Decision Summary

**Decision: Needs Revision** -- specific blocking issues require CA response; single revision cycle expected.

The spec is architecturally sound, well-researched, and covers the design space thoroughly. All 9 reviewers across 3 model families agree the core direction is correct: stdio-only, portfolio index, flat tool surface, and write tools as the main value add. Zero factual disagreements exist across platforms -- the differences are in severity, priority, and framing, which is strong evidence that the findings are real and the architecture is stable.

The 7 blocking issues are concentrated in three areas:

1. **FTS5 schema consistency (UB-1):** Mechanical fix. Unify the dual schema definitions, add the missing `concepts` column, resolve the external-content ordinal mapping.
2. **Write tool safety accuracy (UB-2, UB-3, UB-4):** The spec claims capabilities the codebase does not provide. Downgrade atomicity claims, unify locking, correct rename factual errors.
3. **MCP surface coherence (UB-5, UB-6, UB-7):** The tool availability contract has internal contradictions. Define one authoritative matrix, fix the single-workspace crash, acknowledge the `verify` omission.

None of these require changing the overall architecture. The spec can be revised to v1.1 in an estimated 5-8 hours, then proceed to Phase C Track A implementation.

---

## 10. Phase C Readiness Notes

### If "Ready for Implementation" after v1.1 revision:

**Items for Track A Development Team meta-prompt:**
- The FTS5 design decision (standalone vs. external content) from UB-1 resolution must be final before Track A begins -- it affects schema, sync logic, and test design
- The tool-availability matrix from UB-5 resolution determines which tools are registered in which mode -- central to `create_server()` implementation
- OQ-1 resolution (B) means `get_context_bundle()` must work in single-workspace mode -- requires dual code path (portfolio DB vs. `SnapshotCache`) with the UB-7 guard
- Deterministic bundle scoring (US-1) should be specified before implementation to avoid rework

**Items for Track B Development Team meta-prompt:**
- OQ-2 resolution (A) means `rename_document()` is ID-only -- remove `old_path`/`new_path` from response schema or keep them identical
- Atomicity contract (UB-2) and locking design (UB-3) must be final before Track B begins
- The explicit reuse plan from US-3 (which helpers reused, which adapted, which greenfield) is critical for accurate Track B estimation
- Typed write-error schema (US-2) should be defined before Track B to ensure consistency across all 4 write tools
- Track A -> B handoff state (US-13) must be documented

**C.0 CA Investigation questions (answer before Track A begins):**
1. **FTS5 mode:** Standalone (simpler, no ordinal footgun, duplicates storage) vs. external content (space-efficient, ordinal-mapping complexity)? Claude Code recommends standalone; Codex recommends resolving the contract either way.
2. **Lock architecture:** Single unified lock file (`.ontos.lock` in workspace root, used by both MCP and CLI) vs. dual lock with coordination? If unified, should CLI commands be updated to acquire it?
3. **`verify` subcommand:** Defer to v4.2 (15 min spec note) or include in Track A (2-4 hrs additional scope)?

---

## Handoff Brief for Orchestrator

**Headline finding:** The spec's FTS5 schema is internally contradictory and will produce garbled search results at runtime. This was the unanimous top finding across all 3 platforms and 9 reviewers.

**Decision:** Needs Revision (7/9 Request Changes; 2 approvals from Alignment-lens reviewers only).

**Blocking issues by consensus tier:**
- Universal (3/3): 3 issues (FTS5 schema, write atomicity, locking)
- Strong (2/3): 2 issues (MCP surface contract, verify omission)
- Single-platform: 2 issues (rename factual errors, single-ws crash) -- both from Claude Code with concrete codebase evidence

**OQ consensus:**
- OQ-1: Recommend (B) -- Claude Code and Codex split; Claude Code's evidence is deeper. **Gemini provided no valid position** (misinterpreted the question).
- OQ-2: Recommend (A) -- Claude Code and Codex agree on ID-only default. **Gemini provided no valid position** (misinterpreted the question).

**Single-platform findings the orchestrator should NOT lose:**
- Claude Code: CLI rename does NOT do file renames (decisive for OQ-2); `get_context_bundle()` crash in single-ws mode (UB-7)
- Codex: MCP surface contract as a single systemic coherence problem (not scattered symptoms); typed write-error schema gap
- Gemini: PID-reuse vulnerability in locking mechanism

**Risk levels:** No changes required. Track A MEDIUM, Track B MEDIUM-HIGH, Shared LOW all stand. Condition: Track B stays MEDIUM-HIGH only if OQ-2 = (A). File rename inclusion would push it to HIGH.

**Estimated revision effort:** 5-8 hours for P1 items. Recommend the CA address all 7 blocking issues in a single v1.1 revision pass, then re-enter Phase B for a lightweight confirmation review (1 platform sufficient) before proceeding to Phase C.

## B.4 Verification (Codex, 2026-04-11)

| Issue | Verdict | One-line rationale |
|-------|---------|---------------------|
| UB-1 FTS5 | Accept | One standalone FTS5 schema remains, BM25 matches 3 columns, and no duplicate DDL remains elsewhere. |
| UB-2 Atomicity | Accept with Note | Core write-path language is corrected, but old atomicity wording still leaks into overview, tests, and risk text. |
| UB-3 Locking | Accept with Note | Unified `.ontos.lock` + `flock` substrate is coherent, but a little stale-lock wording remains outside the design section. |
| UB-4 Rename | Accept with Note | `_prepare_plan()` and ID-only rename are correctly specified, but the Track B test table still says "file rename." |
| UB-5 MCP Surface | Accept with Note | The matrix, routing wrappers, and `--read-only` contract now exist, but a few prose lines still drift from the matrix and from `get_context_bundle()`'s actual logic. |
| UB-6 verify | Challenge | `verify` is in scope now, but the new section conflicts with the existing CLI/codebase and uses an inconsistent registry path. |
| UB-7 Single-WS Crash | Accept with Note | The crash path is removed and the single-workspace guard is explicit, but the bundle data-source description still disagrees across sections. |

**Overall B.4 verdict:** Partial Challenge  
**Recommendation:** Return to CA for one targeted fix, then proceed to Phase C.
