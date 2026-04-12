# CA Response: Ontos v4.1 Spec v1.1

**Date:** 2026-04-11
**Author:** Claude (Chief Architect)
**Input:** Phase B Spec Review verdict (9 reviewers, 3 model families)
**Output:** Spec v1.1 + this response document

---

## 1. Summary

**Overall disposition:** All 7 blocking issues addressed. 3 are pending C.0 orchestrator resolution with placeholder language in the spec. The remaining 4 are fully resolved in v1.1.

| Severity | Total | Accepted | Deferred | Rejected | C.0 Pending |
|----------|-------|----------|----------|----------|-------------|
| Blocking (P1) | 7 | 4 | 0 | 0 | 3 (partial -- each has a recommended option drafted in spec) |
| Should-fix (P2) | 13 | 11 | 2 | 0 | 0 |
| Minor (P3) | 24 | 0 | 24 | 0 | 0 |

---

## 2. Blocking Issues Response

### UB-1: FTS5 schema broken / not implementable

**Verdict finding:** FTS5 virtual table references `concepts` column not in `documents` table. Dual schema definitions contradict. BM25 weights don't match column count. External content mode ordinal positions misaligned.

**Action taken:**
- Added `concepts TEXT` to `documents` table in §4.1 canonical schema
- Drafted both FTS5 mode options (standalone vs. external content) with clear tradeoff annotations
- Fixed BM25 weight vector comment to explicitly state "3 elements matching 3 FTS5 columns"
- Replaced the FTS5 content note with a `[PENDING C.0 RESOLUTION]` block explaining both options
- **C.0 question 1** surfaced in §5.1 below

**Spec sections affected:** §4.1, §4.6

### UB-2: Write atomicity overstated

**Verdict finding:** `SessionContext.commit()` uses sequential temp-then-rename. Not atomic. Spec claimed "atomic multi-file writes."

**Action taken:**
- Replaced all "atomic" language with "best-effort sequential commit with temp-file cleanup" in §4.8 shared properties
- Added git clean-state precondition to `rename_document()` (Step 4 in §4.8.2)
- Documented recovery path (`git checkout -- .`) in §4.9
- Updated state diagram (§10.3) to show "best-effort sequential" in EXECUTING state

**Spec sections affected:** §4.8, §4.8.2, §4.9, §10.3

### UB-3: Lock mechanism deficient

**Verdict finding:** MCP `.ontos.lock` and CLI `.ontos/write.lock` have zero coordination. PID-reuse vulnerability in stale detection.

**Action taken:**
- Rewrote §4.9 with three lock architecture options (flock, PID+timestamp, dual)
- Recommended Option A (unified flock-based locking) which eliminates PID-reuse entirely
- Documented the trade-off: requires minor CLI code change to `SessionContext._acquire_lock()` (~30 lines)
- **C.0 question 2** surfaced in §5.2 below

**Spec sections affected:** §4.9

### UB-4: Rename factual errors

**Verdict finding:** Spec references `_compute_rename_plan()` (doesn't exist; actual is `_prepare_plan()`). Claims CLI rename does file renames (it does not -- zero calls to `os.rename()`). OQ-2 recommendation based on incorrect facts.

**Action taken:**
- Corrected function reference to `_prepare_plan(options: RenameOptions, *, mode: str) -> Tuple[Optional[_PreparedPlan], Optional[RenameError]]` (verified at `rename.py:278`)
- Removed all claims about existing file-rename capability
- Documented that CLI rename is ID-only: updates frontmatter `id:` field + `depends_on:` references + body references, but never moves/renames files
- Resolved OQ-2 to **(A) ID-only** in §5
- Removed `old_path`/`new_path` from `RenameDocumentResponse`, replaced with `path` (unchanged)
- Added explicit reuse plan showing which functions are reused vs. adapted

**Spec sections affected:** §4.8.2, §4.11, §5 (OQ-2)

### UB-5: MCP surface contract contradictory

**Verdict finding:** Spec simultaneously claims tools stay identical, all gain `workspace_id`, some tools are mode-dependent, `--read-only` behavior undefined. `_invoke_tool()` routing underspecified.

**Action taken:**
- Added authoritative tool-availability matrix as a table in §4.4 (15 tools x 3 modes)
- Defined `--read-only` behavior: write tools completely absent from `tools/list` (never registered)
- Specified `workspace_id` behavior: accepted but ignored in single-ws mode; `E_CROSS_WORKSPACE_NOT_SUPPORTED` for non-primary in portfolio mode
- Split `_invoke_tool()` into three explicit wrappers: `_invoke_read_tool()`, `_invoke_portfolio_tool()`, `_invoke_write_tool()` per Codex recommendation
- Organized registration into 4 helper functions with clear conditional logic

**Spec sections affected:** §4.4, §4.10

### UB-6: `verify` subcommand silently omitted

**Verdict finding:** Proposal D8 specifies a `verify` subcommand for `.dev-hub` reconciliation. Spec silently dropped it.

**Action taken:**
- Acknowledged the omission explicitly in §9 (Exclusion List) with `[PENDING C.0 RESOLUTION]` placeholder
- **C.0 question 3** surfaced in §5.3 below

**Spec sections affected:** §9

### UB-7: `get_context_bundle()` crashes in single-workspace mode

**Verdict finding:** Passing `workspace_id` in single-ws mode (where `portfolio_index is None`) falls into `else` branch calling `_validate_workspace_id(None, ...)` -> `AttributeError`.

**Action taken:**
- Rewrote workspace resolution logic in §4.7 with three explicit branches:
  1. `portfolio_index is None` -> single-ws mode, ignore `workspace_id`
  2. `portfolio_index is not None` and `workspace_id is None` -> require workspace_id
  3. `portfolio_index is not None` and `workspace_id is not None` -> validate and proceed
- Resolved OQ-1 to **(B) Available in both modes** in §5
- Updated tool-availability matrix to show `get_context_bundle` in both modes

**Spec sections affected:** §4.7, §5 (OQ-1), §4.4 (matrix)

---

## 3. Should-Fix Response

| # | Issue | Disposition | Rationale |
|---|-------|------------|-----------|
| US-1 | Bundle ranking determinism | **ACCEPT** | Added alphabetical doc ID tiebreaker in §4.7 Step 1. Direct impact on LLM prompt cache stability. |
| US-2 | Typed write-error schema missing | **ACCEPT** | Added `WriteToolError` and `WriteToolErrorEnvelope` schemas in §4.8 and §4.11. Critical for uniform write-tool error handling across all 4 tools. |
| US-3 | "Simple wrapper" language misleading | **ACCEPT** | Replaced with explicit reuse plan table in §4.8 showing which helpers are reused unchanged, adapted, or new per tool. |
| US-4 | `promote_document` mixed success/error | **ACCEPT** | Changed validation failure to `isError: true` with `E_PROMOTION_BLOCKED`. `PromoteDocumentResponse` now uses `Literal[True]` for success. No mixed semantics. |
| US-5 | `partial` classification ambiguous | **ACCEPT** | Added explicit boolean logic in §4.3 matching proposal: `(has_readme AND NOT has_ontos) OR (has_ontos AND doc_count < 5)`. |
| US-6 | Tilde expansion / `mkdir -p` | **ACCEPT** | Changed `PORTFOLIO_CONFIG_PATH` to use `Path.home()` in §4.2. Directory creation documented as part of `ensure_portfolio_config()`. |
| US-7 | `search_fts()` two queries without transaction | **ACCEPT** | Wrapped both queries in explicit `BEGIN`/`COMMIT` in §4.6. |
| US-8 | `.ontos.lock` not in `.gitignore` | **ACCEPT** | Added `.gitignore` to file change table in §4.9. |
| US-9 | `rebuild_workspace()` failure handling | **DEFER** | Implementation detail. The spec's §4.8 shared properties already state write tools catch errors and return `isError: true`. The specific `rebuild_workspace` failure -> warning path is a coding decision, not a spec-level concern. Deferred to implementation. |
| US-10 | Slug collision | **ACCEPT** | Added collision detection with numeric suffix in §4.3. First alphabetically gets unsuffixed slug. |
| US-11 | Bundle/refresh under-specified | **ACCEPT** (partially subsumed) | Most issues addressed by UB-5 (matrix), UB-7 (dual path), and US-1 (tiebreaker). The `top_N` value is implicit: all non-kernel documents sorted by in-degree, packed greedily until budget exhausted. No explicit N cap needed. |
| US-12 | Risk assessment understates risk | **DEFER** | Re-evaluated after all P1 fixes. Risk levels remain: Track A MEDIUM, Track B MEDIUM-HIGH, Shared LOW. OQ-2=(A) removes the file-rename escalator. The "simple wrapper" correction (US-3) doesn't change the risk rating -- the work is more complex than described but not more risky. |
| US-13 | Track A->B handoff unspecified | **ACCEPT** | Added §4.12 "Track A -> B Handoff State" with explicit list of 8 prerequisites Track B assumes from Track A. |

---

## 4. Minor Issues Response

24 minor issues grouped by category with bulk dispositions:

| Category | Count | Disposition | Notes |
|----------|-------|------------|-------|
| API / Registration | 4 | **DEFER to implementation** | Registration helper signatures, `tools/list` backward compat precision, scaffold wrapping differences, pyproject.toml version bump -- all implementation-time decisions that don't affect spec correctness. |
| Database / Search | 4 | **DEFER to implementation** | Connection strategy for batch rebuild, COUNT query optimization, FTS5 query edge cases, threading.Lock vs asyncio.Lock -- implementation details within the spec's architectural constraints. |
| Bundle / Scoring | 3 | **DEFER to implementation** | Lost-in-the-middle odd-length handling, kernel size upper bound, token estimation for code docs -- all tuning decisions that don't affect the algorithm's correctness as specified. |
| Write Tools / Safety | 4 | **DEFER to implementation** | Lock empty-after-crash, scaffold type rejection rationale, log git error handling, rename destructiveHint -- implementation-level safety details. Note: the `destructiveHint` for rename is a valid concern (Codex M1) but the current `False` matches proposal D5's decision. |
| Edge Cases | 4 | **DEFER to implementation** | Deleted projects, symlink loops, partial workspaces without `.ontos.toml`, multi-process portfolio DB contention -- all handled by the spec's general error-handling patterns (`isError: true`, rebuildable cache). |
| Documentation | 3 | **DEFER to implementation** | Architecture diagram missing new files, packaging prose inconsistencies, diagram state transitions -- will be updated when implementation stabilizes. |
| Test Gaps | 2 | **DEFER to implementation** | Portfolio DB corrupt-rebuild test, `rebuild_all()` error handling -- test-level details addressed when writing tests. |

---

## 5. C.0 Investigation Questions

### 5.1 FTS5 Mode: Standalone vs. External Content

**Question:** Should the FTS5 virtual table use standalone mode (stores its own copy of text) or external content mode (references the `documents` table by rowid)?

**Options:**

| | Standalone (Option A) | External Content (Option B) |
|-|----------------------|---------------------------|
| **Storage** | Duplicates ~800KB of text | No duplication |
| **Complexity** | Simple: delete + insert | Must manage ordinal mapping between `documents` columns and FTS5 columns. Ordinal errors cause `snippet()` to return wrong-column data at runtime. |
| **Sync** | Self-contained; no cross-table consistency concerns | Requires explicit delete-before-reinsert; FTS index and `documents` table can drift |
| **Performance** | Identical at this scale (400 docs, <1s rebuild) | Identical at this scale |

**Recommendation: Option A (standalone).** 800KB storage duplication is negligible. The ordinal-mapping footgun in external content mode was the #1 finding across all 9 reviewers -- it's the kind of bug that's invisible in testing and catastrophic in production (garbled search snippets). The research doc's recommendation of external content was for a much larger scale.

**Downstream impact:**
- Track A meta-prompt: if standalone, `rebuild_workspace()` deletes and reinserts FTS rows independently of `documents` table. Simpler code.
- If external content, Track A meta-prompt must include explicit ordinal mapping rules and a test that verifies column alignment.

### 5.2 Lock Architecture: Unified flock vs. Alternatives

**Question:** How should MCP write tools and CLI commands coordinate to prevent concurrent writes?

**Options:**

| | Option A: Unified flock | Option B: Unified PID+timestamp | Option C: Dual lock with cross-acquisition |
|-|------------------------|-------------------------------|-------------------------------------------|
| **Lock file** | Single `.ontos.lock` using `fcntl.flock()` | Single `.ontos.lock` with PID+timestamp | MCP: `.ontos.lock`, CLI: `.ontos/write.lock` |
| **Stale detection** | Automatic (OS releases on crash) | PID dead OR timestamp >10min | Per-file PID-based |
| **PID reuse vulnerability** | None (flock is kernel-managed) | Mitigated but not eliminated | Present |
| **CLI code change** | Yes: ~30 lines in `SessionContext._acquire_lock()` | Yes: ~30 lines | No |
| **Complexity** | Low | Medium | High (cross-acquisition logic) |
| **Cross-platform** | Unix only (macOS + Linux) | Cross-platform | Cross-platform |

**Recommendation: Option A (unified flock).** Eliminates PID-reuse entirely. The CLI code change is minor (~30 lines in `context.py:224`). Ontos targets macOS/Linux; Windows support is not a current requirement.

**Downstream impact:**
- Track A: no impact (no write tools).
- Track B meta-prompt: must specify `flock` usage pattern. Must also modify `SessionContext._acquire_lock()` to use the same lock file. This is a small Track B scope addition (~1 hour).
- If Option C chosen, Track B meta-prompt becomes more complex (dual-lock acquisition order, deadlock prevention).

### 5.3 `verify` Subcommand: Defer vs. Include

**Question:** Proposal D8 specifies a `verify` subcommand comparing portfolio DB against `projects.json`. Should v4.1 include it?

**Options:**

| | Defer to v4.2 | Include in Track A |
|-|---------------|-------------------|
| **Effort** | 15 min (spec note + exclusion entry) | 2-4 hours (design + test strategy) |
| **Risk** | `.dev-hub` transition stalls without validation tool | Minor scope creep |
| **Value** | Zero until `.dev-hub` transition is actively underway | Enables confident `.dev-hub` deprecation |

**Recommendation: Defer to v4.2** unless the `.dev-hub` transition is planned for the next 4 weeks. The portfolio DB and `project_registry()` tool already provide an implicit comparison surface -- an agent can call `project_registry()` and diff against `projects.json` manually. The `verify` subcommand adds polish, not capability.

**Downstream impact:**
- If deferred: add to §9 exclusion list with explicit forward reference to v4.2. Track A scope unchanged.
- If included: add a §4.X section with full design (CLI subcommand `ontos verify --portfolio`, reads both sources, diffs, reports discrepancies). Adds ~4-6 tests to Track A test strategy.

---

## 6. Open Items After v1.1

1. **3 C.0 placeholders** in spec await orchestrator resolution before B.4 verification.
2. **Architecture diagram** (§10.1) does not yet show new files (`bundler.py`, `scanner.py`, `portfolio_config.py`, `write_tools.py`, `locking.py`). Deferred to implementation -- the diagram shows component relationships correctly; individual file names are implementation details.
3. **US-9 (rebuild_workspace failure handling)** deferred to implementation. The spec's error handling framework is sufficient; specific catch-and-warn logic is a coding decision.

---

## 7. B.4 Verification Request

The B.4 verifier (Codex, single platform) should specifically check:

1. **UB-1:** FTS5 schema is now a single canonical definition in §4.1. `concepts TEXT` column exists in `documents` table. BM25 weight vector has 3 elements matching 3 FTS5 columns. No duplicate schema elsewhere.
2. **UB-2:** No "atomic" language remains in §4.8 or §4.9. Git clean-state precondition present in §4.8.2 Step 4. Recovery path (`git checkout -- .`) documented in §4.9.
3. **UB-3:** Lock architecture options documented with C.0 placeholder. PID-reuse addressed.
4. **UB-4:** `_prepare_plan()` referenced correctly (not `_compute_rename_plan()`). No claims about CLI file rename. OQ-2 resolved to (A). `old_path`/`new_path` removed from response schema.
5. **UB-5:** Tool-availability matrix present in §4.4. All prose statements consistent with matrix. Three `_invoke_*` wrappers specified.
6. **UB-6:** `verify` subcommand acknowledged in §9 with C.0 placeholder.
7. **UB-7:** `get_context_bundle()` workspace resolution has three explicit branches. No path where `portfolio_index is None` leads to `_validate_workspace_id()` call.

Additionally verify: no regressions in existing spec correctness (backward-compat claims, test baseline, research consensus items).

---

## 8. Track A / Track B Implications

### Changes affecting Track A Development Team meta-prompt:

- **Tool-availability matrix (§4.4)** is now the single source of truth. Track A implements: 8 v4.0 tools + `project_registry` + `search` + `get_context_bundle` (11 tools total in portfolio mode, 9 in single-ws mode).
- **`get_context_bundle()` works in both modes** (OQ-1 resolved). Track A must implement the dual code path (portfolio DB vs. SnapshotCache) with the three-branch guard from §4.7.
- **FTS5 mode** depends on C.0 resolution. Track A meta-prompt must include the resolved mode.
- **Registration uses `_register_core_tools`, `_register_portfolio_tools`, `_register_bundle_tool`** helper functions (§4.4 step 6).
- **Deterministic bundle scoring** with alphabetical ID tiebreaker (US-1).
- **Slug collision handling** with numeric suffix (US-10).
- **`PortfolioConfig` uses `Path.home()`** not tilde string (US-6).

### Changes affecting Track B Development Team meta-prompt:

- **OQ-2 = (A) ID-only rename.** No filesystem file renames. `RenameDocumentResponse` has `path` (singular, unchanged) not `old_path`/`new_path`.
- **`_prepare_plan()`** is the correct function reference (not `_compute_rename_plan()`).
- **Atomicity is best-effort**, not atomic. Git clean-state precondition on `rename_document()`. Recovery path documented.
- **Typed write-error schema** (`WriteToolErrorEnvelope`) defined -- all 4 write tools must use it uniformly.
- **Lock architecture** depends on C.0 resolution. Track B meta-prompt must include the resolved approach.
- **`promote_document` validation failures** use `isError: true` with `E_PROMOTION_BLOCKED` (not mixed `success: false`).
- **Track A->B handoff state** explicitly documented in §4.12 -- Track B meta-prompt should reference this.
- **`_invoke_write_tool()`** wrapper handles locking, refresh, and portfolio invalidation (§4.4 step 7).

---

## 9. Orchestrator C.0 Resolutions (added 2026-04-11)

The orchestrator resolved all 3 C.0 questions. Spec v1.1 is now finalized with no placeholders.

### 9.1 FTS5 Mode → Standalone (Option A)

- **Question:** Should FTS5 use standalone mode or external content mode?
- **Decision:** Standalone (Option A).
- **Rationale (orchestrator's):** 800KB storage duplication is negligible at the 400-doc scale. The ordinal-mapping bug in external content mode was the unanimous top finding across 9 reviewers — the kind of bug that escapes testing and corrupts production output. The research consensus recommended external content for generic scenarios but was not optimizing for this scale; research consensus must be re-evaluated against project-specific constraints, not adopted blindly.
- **Spec sections updated:** §4.1 (FTS5 schema — placeholder replaced with standalone DDL), §4.1 step 4 (rebuild_workspace — FTS5 row count verification added), §4.6 (no changes needed — JOIN pattern works for standalone), §6 (test_portfolio.py gains 2 tests: row count parity, snippet column correctness), OQ-3 (question text updated to remove external content reference).
- **Unintended consequences:** None found. The standalone FTS5 schema is strictly simpler than external content. The `d.rowid = fts_content.rowid` JOIN in §4.6 works correctly because `rebuild_workspace()` explicitly inserts FTS5 rows with matching rowids. No interaction issues with other spec sections.

### 9.2 Lock Architecture → Unified flock, Track A substrate (Option A)

- **Question:** How should MCP write tools and CLI commands coordinate to prevent concurrent writes?
- **Decision:** Unified flock (Option A), placed in Track A as substrate for Track B.
- **Rationale (orchestrator's):** `flock` is kernel-managed and eliminates PID-reuse entirely. PID+timestamp only mitigates. No Windows users makes Unix-only acceptable. The ~30-line change to `SessionContext._acquire_lock()` is substrate for Track B, not Track B itself — Track B cannot ship without it. Placing it in Track A means Track A's PR delivers a complete, working unified lock.
- **Spec sections updated:** §4.9 (rewritten: Track B → Shared/Track A substrate, three options replaced with single flock implementation, `workspace_lock()` context manager defined, `SessionContext._acquire_lock()` migration specified), §4.4 (file change list gains `locking.py`, `context.py`, `.gitignore`), §4.12 (Track A→B handoff gains lock substrate as prerequisite #8), §6 (Track A gains `test_locking.py` ~3 tests; Track B `test_locking.py` renamed to `test_locking_write_tools.py` ~4 tests), §8 (Track B risk row for CLI interaction downgraded from Medium to Low likelihood), §10.1 architecture diagram (label updated from `[Track B]` to `[Shared/A]`, `PID-based` → `flock-based`), §10.3 state diagram (lock release state updated from "deleted" to "flock released (OS-managed)").
- **Unintended consequences:** One interaction worth noting: the `SessionContext._acquire_lock()` change touches `ontos/core/context.py`, which is used by all CLI commands that write files (not just MCP). This is intentional (unified lock) but means the change affects CLI behavior. The existing CLI write commands that use `SessionContext` will now acquire `.ontos.lock` instead of `.ontos/write.lock`. This is correct (same lock for CLI and MCP) but B.4 should verify that no CLI test depends on the `.ontos/write.lock` path.

### 9.3 `verify` Subcommand → INCLUDED in Track A

- **Question:** Should the `verify` subcommand be deferred to v4.2 or included in v4.1 Track A?
- **Decision:** Include in Track A.
- **Rationale (orchestrator's):** The `.dev-hub` transition is planned within 4 weeks. `verify` is the validation tool for that transition and must ship before it begins. The CA Response recommended deferring; the orchestrator overrode based on the transition timeline. This is a 2-4 hour scope addition.
- **Spec sections updated:** NEW §4.13 (full Technical Design: CLI registration, `verify_portfolio()` function, algorithm, error handling, exit codes, JSON output), §1 (overview mentions verify), §2 (Track A scope gains verify and lock substrate items), §3 (dependency note for `projects.json`), §6 (Track A gains `test_verify.py` ~6 tests, manual testing steps 9-11 added), §8 (Track A risk note updated — verify is low-risk, rating stays MEDIUM), §9 (verify removed from exclusion list, CLI exclusion row updated).
- **Unintended consequences:** None found. The `verify` subcommand is entirely additive: new file (`verify.py`), new CLI registration, read-only on both sources. It does not interact with any existing spec section beyond the CLI registration in `ontos/cli.py`. The §4.12 handoff state now includes verify as prerequisite #9 for Track B, which is informational only (Track B doesn't depend on verify).

---

## 10. Roadmap Updates (added 2026-04-11)

- **Roadmap file:** `.project-internal/roadmap.md` (newly created — no prior project-wide roadmap existed)
- **New sections added:**
  - "v4.1 — Portfolio Authority" with current status and track summary
  - "Deferred from v4.1" table with 12 items, each recording where deferred, why, and revisit trigger
  - "v4.2 — Tentative Scope" with 6 candidate features seeded from deferrals
  - "Completed Versions" table (v3.3.0 through v4.0.0)
- **Items recorded as deferred to v4.2:**
  - HTTP/Streamable HTTP transport (PR #84 re-scope)
  - Security model — bearer token, audit logging, rate limiting (PR #84 re-scope)
  - Daemon mode and background indexer (PR #84 re-scope)
  - Calibrated 5-signal bundle scoring (PR #84 re-scope)
  - Personalized PageRank (PR #84 re-scope)
  - MCP Resources and Prompts primitives (PR #84 re-scope)
  - Cross-workspace `depends_on` validation (PR #84 re-scope)
  - US-9: `rebuild_workspace()` failure handling (CA Response §3)
  - US-12: Risk assessment re-rating (CA Response §3)
  - Configurable file rename — OQ-2 option C (B-verdict OQ-2 resolution)
  - `starlette`, `uvicorn`, `cachetools` dependencies (PR #84 re-scope)
- **Structural changes:** Created new roadmap file from scratch. Proposed a table-based deferral tracking format with columns: Item, Deferred Where, Why Deferred, Revisit Trigger. Marked v4.2 scope section as "tentative — to be refined before v4.2 proposal phase." If the orchestrator has a preferred format, the structure can be adjusted.

---

## 11. B.4 Cleanup Pass (added 2026-04-11)

**Date:** 2026-04-11
**Input:** B.4 Verification (Codex), Partial Challenge verdict

### Tasks Completed

1. **UB-6 fix (the Challenge):** Rewrote §4.13 as an additive extension of the existing `ontos verify` command, not a clean-room create.
2. **Registry path normalization:** All occurrences now use `~/Dev/.dev-hub/registry/projects.json`.
3. **Residual v1.0 language scrub:** Removed atomicity, file-rename, and stale-lock leftovers from §1, §6, §8.
4. **Prose drift reconciliation:** §4.4, §4.7, §4.10 now tell one consistent story about `get_context_bundle()` data sources and tool availability.

### UB-6 Detail: Existing `verify` Command

**What `ontos/commands/verify.py` currently does:** The existing `verify` command performs document staleness verification. It checks the `describes` and `describes_verified` frontmatter fields to identify documents whose `describes` targets have been modified since last verification. It supports two modes: `ontos verify <path>` (single file — updates `describes_verified` date) and `ontos verify --all` (interactive batch mode — walks all documents, prompts user for each stale document). The command uses `SessionContext` for buffered writes and `OutputHandler` for user-facing output.

**How `--portfolio` was integrated:** The `--portfolio` flag is added to the existing `_register_verify()` function at `ontos/cli.py:411`. In `_cmd_verify()` at `ontos/cli.py:1291`, an early-return `if getattr(args, "portfolio", False):` branch invokes the new `verify_portfolio()` function (added to `ontos/commands/verify.py`). When `--portfolio` is not passed, execution falls through to the existing `_run_verify_command()` path unchanged. The `--json` flag is already available via the global parent parser and requires no additional registration. Option A (flag on existing subparser) was structurally clean — `_cmd_verify` already uses branching for `path` vs `--all` modes, so adding a `--portfolio` branch was trivial with no structural awkwardness.

**Existing behavior preserved:** Confirmed. When `--portfolio` is not passed, `_cmd_verify` executes the identical code path as v4.0: constructs `VerifyOptions`, calls `_run_verify_command()`, optionally emits JSON. No existing arguments, flags, or behavior are modified.

### Stop-and-Ask Items

None. Option A integrated cleanly with the existing handler structure.

### Self-Review Checklist

All items in the updated §8.5 checklist pass. Key additions verified:
- §4.13 says MODIFY (not CREATE) for both `verify.py` and `cli.py`
- `_cmd_verify` (with underscore) is the only handler name referenced
- All registry paths use `~/Dev/.dev-hub/registry/projects.json`
- No "atomic" claims remain in §1 overview, §6 tests, or §8 risk text (outside of "NOT atomic" qualifications)
- §4.4/§4.7/§4.10 are internally consistent on `get_context_bundle` data sources
