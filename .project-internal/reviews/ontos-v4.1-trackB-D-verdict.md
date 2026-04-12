# Review Verdict: Ontos v4.1 Track B Code Review

**Phase:** D (Code Review)
**Date:** 2026-04-12
**PR:** #92 (`feature/v4.1-track-b` → `main`)
**Reviewers:** 9 reviewers across 3 platforms (Claude Code, Codex, Gemini CLI agent teams)
**Overall Status:** **Needs Fixes**

---

## 0. Meta-finding — HEAD drift across platforms

Each platform reviewed the PR at a different tip. Findings are preserved verbatim per hard rule #1; HEAD drift is annotated inline rather than smoothed away.

| Platform | HEAD reviewed | Pytest observed |
|---|---|---|
| Claude Code | `7cbc3152` (verified by `gh pr view 92 --json headRefOid`) | 1113 passed, 2 skipped (`.venv-mcp` Python 3.14) |
| Codex | Pre-Dev-4 state (test count 1255 across `tests/` + `.ontos/scripts/tests/`; 1103 in `tests/` matches pre-Dev-4 snapshot) | 1103 passed + 152 legacy (1255 total), 2 skipped |
| Gemini | Not stated in review | Not reported |

Claude Code's adversarial reviewer independently detected drift from the stale `88fe711` pin and checked out `7cbc3152`. Codex + Gemini did not. Per user direction, this verdict preserves every platform's findings verbatim and does **not** re-verify Codex's or Gemini's claims at the correct tip.

---

## 1. Cross-Platform Verdict Summary

| Platform | Model Family | Verdict | Blocking | Top Concern |
|---|---|---|---|---|
| Claude Code | Anthropic | approve-with-fixes (at `7cbc3152`) | 0 | SF-1 tautological `build_rename_plan` equivalence test |
| Codex | OpenAI | Needs fixes | 3 | `read_only=True` still registers all four write tools |
| Gemini CLI | Google | **DO NOT MERGE** | 3 | Cross-workspace lock bypass in `rename_document` (data-corruption risk) |

**Cross-platform consensus:** **Needs Fixes** (regression found). Per hard rule #5, with Codex + Gemini both skeptical, the consolidated framing sides with the skeptical platforms; Claude Code's `approve-with-fixes` is the minority view and is a HEAD-drift-adjusted position at the correct tip.

Zero blocking issues are confirmed 3-of-3. Two are confirmed 2-of-3 or involve explicit platform disagreement. Three are single-platform. Per hard rule #2, every blocking issue below is preserved at its platform's stated severity.

---

## 2. Critical Blocking Issues (Combined)

Deduplicated by issue, not by wording. Each row below is **one** bug, however each platform worded it.

| # | Issue | Flagged By | File:Line | Category | Action Required |
|---|---|---|---|---|---|
| **CB-B1** | **Bundle config wiring incomplete — `max_logs` / `log_window_days` not passed from `portfolio.toml` into `build_context_bundle`; bundler falls back to hardcoded `5 / 14` defaults.** Gemini reports `tools.py:467` passes only `token_budget`; Codex reports same at `tools.py:411` (line numbers differ because HEADs differ). Codex additionally reports that `portfolio_config.py:19,26` and `bundler.py:31` still hold pre-addendum defaults `8192 / 5 / 14` (Claude Code verified this latter sub-claim was fixed in Dev 4 `8a4069c` at `7cbc3152` — but the call-site wiring gap Gemini flags is a separate claim that Claude Code does not directly refute). | Codex (B-2) + Gemini (B-1) — 2/3 | `ontos/mcp/tools.py:411` (Codex) / `tools.py:467` (Gemini); `ontos/mcp/portfolio_config.py:19,26` (Codex); `ontos/mcp/bundler.py:31` (Codex) | A4 wiring | Thread `config.scanning.bundle_max_logs` and `config.scanning.bundle_log_window_days` into `build_context_bundle()`. Verify call-site forwarding at correct HEAD; update defaults to `8000 / 20 / 30` if not already. |
| **CB-B2** | **`read_only=True` still registers all four write tools in `tools/list`.** `_register_write_tools(...)` is always called; Codex reproduced `list_tools()` returning `scaffold_document`, `log_session`, `promote_document`, `rename_document` under `read_only=True`. Current tests cover call-time refusal only, not registration-time stripping. Cross-reviewer-confirmed within Codex's team (R1, R2, R3). **Direct platform disagreement:** Gemini explicitly clears `read_only` at attack-surface item 8 (§5 below) stating "`read_only` is enforced, returns structured `isError: true` (`E_READ_ONLY`)"; Claude Code marks the `read_only` hard guard intact at the correct HEAD. Both views preserved verbatim in §6. | Codex (B-1) — 1/3 (Gemini + Claude Code disagree) | `ontos/mcp/server.py:163`; `tests/mcp/test_write_tools.py:244`; `tests/mcp/test_rename_document.py:345` | API compliance | Skip `_register_write_tools(...)` when `read_only=True`; add `list_tools()` regression test asserting the four write tools are absent when read-only. |
| **CB-B3** | **Cross-workspace lock bypass in `rename_document` via scope-tracks-config.** Dev 3's refactor to `resolve_scan_scope(None, config.scanning.default_scope)` at `rename_tool.py:429` allows cross-workspace body-reference rewrites if a workspace configures `default_scope = portfolio`. The tool only acquires `workspace_lock(plan.workspace_root)` for the local workspace (`rename_tool.py:344`). Writing to cross-workspace files without acquiring their `workspace_lock`s violates A1/A3 write-safety guarantees. Gemini frames this as "severe concurrency vulnerability risking data corruption." **Severity disagreement:** Claude Code's Adversarial reviewer examined the same site and reached a narrower conclusion — `resolve_scan_scope` accepts only `docs`/`library` so "default_scope=portfolio" is vacuous today; the live concern is that with `default_scope=docs` MCP rename will NOT rewrite body references in `.ontos-internal/**` (m-9, flag-only). Both views preserved verbatim in §6. | Gemini (B-2) — 1/3 (Claude Code as m-9 minor) | `ontos/mcp/rename_tool.py:429`; `ontos/mcp/rename_tool.py:344`; `ontos/commands/rename.py:386-395` | Concurrency / write-safety | Either (a) override the config default for `rename_document` and always use `ScanScope.LIBRARY`, or (b) implement multi-workspace locking before accepting portfolio scope. Document the chosen contract in the spec. |
| **CB-B4** | **Rebuild uses non-canonical workspace slug (`slugify(workspace_root.name)`) → stale index under basename collisions.** Both single-file and rename preflight paths derive rebuild slug from `workspace_root.name`, then swallow rebuild failures. Addendum A-collision binds workspace identity to `scanner.slugify + allocate_slug`. Codex reproduced with two indexed repos named `workspace`: `scaffold_document()` on the second returned success while `_rebuild_safely` logged `sqlite3.IntegrityError: UNIQUE constraint failed: projects.path`; portfolio index for `workspace-2` never picked up the new file. | Codex (B-3) — 1/3 | `ontos/mcp/writes.py:146,160`; `ontos/mcp/rename_tool.py:181`; `.project-internal/reviews/ontos-v4.1-spec-addendum-v1.2.md:44` | Data integrity | Stop deriving rebuild slugs from `workspace_root.name`. Use the canonical portfolio slug (including collision suffixes) from `allocate_slug` on every write-tool rebuild path. Add basename-collision regression test. |
| **CB-B5** | **Stacked-merge conflict resolution on `_validate_workspace_id` dropped Dev 4's `Optional[PortfolioIndexLike]` type hint, reverting to `portfolio_index: Any`.** **Severity disagreement:** Gemini frames as blocking (loss of type safety); Claude Code's Adversarial reviewer tracks the same site as m-1 minor ("wrapper declares `workspace_id: str` (non-Optional); delegated helper accepts `Optional[str]`... no runtime issue") — note Claude Code's m-1 concerns the *`workspace_id`* annotation, while Gemini's blocker concerns the *`portfolio_index`* annotation at the same function; these are adjacent drift, not identical. Claude Code's Stage-1 consolidation §5 asserts "`_validate_workspace_id` preserves... Dev 4's `Optional[PortfolioIndexLike]` type hint" — direct contradiction with Gemini. Both views preserved verbatim in §6. | Gemini (B-3) — 1/3 (Claude Code m-1 minor on adjacent hint; Claude Code consolidation §5 asserts preserved) | `ontos/mcp/tools.py:494`; `ontos/mcp/tools.py:524` (Claude Code's m-1 line) | Code quality / type safety | Verify at correct HEAD: inspect `_validate_workspace_id` signature. If `portfolio_index: Any`, restore `Optional[PortfolioIndexLike]`. Align wrapper `workspace_id` signature to `Optional[str]` (Claude Code m-1). |

**Confidence tiers** (per Track A precedent structure, and rule #2 — NOT downgraded):
- **Universal (3/3):** None.
- **2-of-3:** CB-B1 (bundle config).
- **Single-platform:** CB-B2 (Codex — contradicted by Gemini + Claude Code on read_only, but Codex produced reproduction evidence at `server.py:163`). CB-B3 (Gemini — Claude Code treats adjacent concern as minor). CB-B4 (Codex — reproduced locally). CB-B5 (Gemini — Claude Code disputes at correct HEAD).

Per Track A precedent (§2, §7), single-platform findings are not downgraded and are "often the most valuable" (CB-5, CB-7, CB-8 from Track A were all single-platform).

---

## 3. Major Issues (Should-Fix)

| # | Issue | Flagged By | File:Line | Recommendation |
|---|---|---|---|---|
| SF-B1 | CLI-vs-MCP `build_rename_plan` equivalence test is tautological — compares two CLI-path invocations; does not invoke `rename_tool._rename_document_impl` via the MCP dispatcher. Gemini + Codex verify the equivalence test meaningful (**direct disagreement**, §6). | Claude Code (Adversarial, SF-1) | `tests/commands/test_rename.py:526-609` | Add test invoking `rename_document()` via MCP dispatcher; diff its output against CLI's `RenamePlan`. |
| SF-B2 | SF-9 deterministic input ordering is not actually tested — `test_bundler_tiebreak_determinism` runs 4 passes on the same snapshot; would pass even if every `sorted()` call in `bundler.py` were deleted. | Claude Code (Adversarial, SF-2) | `ontos/mcp/bundler.py:54-55,69,193`; `tests/mcp/test_bundler.py:150-162` | Build two snapshots from same logical files with different filesystem-listing orders (monkeypatch `os.scandir`); assert identical bundle output. |
| SF-B3 | No direct regression test for the Python 3.14 contextlib / frozen-dataclass workaround. Catch-inside-`with` only incidentally protected by happy-path tests; a refactor moving the catch outside the lock would break only on 3.14. | Claude Code (Adversarial, SF-3) | `ontos/mcp/writes.py:287-323`; `ontos/mcp/rename_tool.py:339-375` | Add a test that forces a write-tool impl to raise `OntosUserError` from inside the lock; assert envelope's `error_code` survives. |
| SF-B4 | MCP write tools not documented in `Ontos_Manual.md` or `AGENTS.md`. Four new tools (`scaffold_document`, `log_session`, `promote_document`, `rename_document`) are absent from user-facing docs. | Claude Code (Peer, SF-4) | `docs/reference/Ontos_Manual.md` (MCP section from line ~394+); `ontos/core/instruction_artifacts.py:181` | Add Manual subsection with input/output schemas and `read_only` / `workspace_id` behavior. Update `instruction_artifacts.py` if it auto-generates a tool list. |
| SF-B5 | `load_portfolio_config` contract change — now raises `FileNotFoundError` on missing config (previously `ensure_portfolio_config()` wrote on read). `get_context_bundle` catches correctly but public-API semantics changed. | Claude Code (Peer, SF-5) | `ontos/mcp/portfolio_config.py:52-62` | Document the contract change in module docstring or release notes. Low urgency. |
| SF-B6 | Missing `workspace_id` silently falls back to current workspace. `validate_workspace_id(...)` called without `require=True`; Track B design explicitly states missing `workspace_id` must return a structured error and not fall back. Design-note/implementation disagreement. | Codex (R2) | `ontos/mcp/writes.py:143`; `ontos/mcp/rename_tool.py:178`; `.project-internal/v4.1/phaseB/TrackB-Design.md:182,203` | Decide whether `workspace_id` is required for write tools; align code and tests with the chosen contract. |
| SF-B7 | Single-file write tools implement A3 as rebuild-on-error only, not rollback-then-rebuild. `writes.py:174` catches `commit()` failure and calls `_rebuild_safely(...)` directly. Addendum A3 says every write tool must rebuild after *rollback* of failed writes. Partly a doc inconsistency: Dev 2's Track B implementation spec softened to rebuild-on-error only. | Codex (lead) | `ontos/mcp/writes.py:174`; `.project-internal/reviews/ontos-v4.1-spec-addendum-v1.2.md:59`; `.project-internal/v4.1/phaseB/v4.1_TrackB_Implementation_Spec.md:146` | Resolve doc contradiction: either update addendum to match rebuild-on-error, or change `writes.py` to rollback-then-rebuild. |

---

## 4. Minor Issues

| # | Issue | Flagged By | File:Line |
|---|---|---|---|
| m-B1 | `_validate_workspace_id` wrapper declares `workspace_id: str`; delegated helper accepts `Optional[str]`. Adjacent to CB-B5 but distinct. | Claude Code (Adversarial, m-1) | `ontos/mcp/tools.py:524` |
| m-B2 | `_slugify_workspace_name` is a one-line wrapper on `scanner.slugify` with no independent logic. | Claude Code (Alignment, m-2) | `ontos/mcp/tools.py:537-538` |
| m-B3 | Result-helper functions (`_success_result`, `_write_error_result`, `_user_error_result`) copy-pasted between `writes.py` and `rename_tool.py`. | Claude Code (Peer, m-3) | `ontos/mcp/writes.py:66-115`; `ontos/mcp/rename_tool.py:104-150` |
| m-B4 | `E_UNKNOWN_WORKSPACE` dispatch path not exercised by write-tool tests. | Claude Code (Peer, m-4) | `tests/mcp/test_write_tools.py`; `tests/mcp/test_rename_document.py` |
| m-B5 | `rename_document` rollback uses subprocess `git checkout -- .` — degrades silently if workspace is non-git or submodule. | Claude Code (Adversarial, m-5) | `ontos/mcp/rename_tool.py:270-285` |
| m-B6 | A3-rebuild count assertion is brittle (`len(rebuild_calls) == 1`). | Claude Code (Adversarial, m-6) | `tests/mcp/test_write_tools.py:409` |
| m-B7 | `_recent_logs` mtime fallback brittle in CI (fresh-clone files share checkout-time mtime). | Claude Code (Adversarial, m-7) | `ontos/mcp/bundler.py:226-234` |
| m-B8 | `E_WORKSPACE_BUSY` `isError: true` path not directly tested in runnable suite. | Claude Code (Alignment, m-8) | `ontos/mcp/writes.py:324-327`; `ontos/mcp/rename_tool.py:376-378` |
| m-B9 | Scope-tracks-config hazard for body-reference drift into LIBRARY (adjacent to CB-B3 but Claude Code frames as flag-only). | Claude Code (Adversarial, m-9) | `ontos/mcp/rename_tool.py:429`; `ontos/commands/rename.py:386-395` |
| m-B10 | Several new tests use source-inspection (`inspect.getsource()`) or symbol-identity assertions rather than behavioral regressions. | Codex (R1) | `tests/mcp/test_write_tools.py:474`; `tests/test_context_contention.py:272`; `tests/mcp/test_rename_document.py:368` |

---

## 5. Attack Surface Coverage

Per hard rule #4, each of the 8 items from the review team prompt gets explicit coverage. Cells marked **BLOCKING** indicate a platform flagged this vector as blocking; "verified" indicates the platform checked and cleared the vector; "not addressed" is itself a finding.

| # | Attack Surface Item | Claude Code | Codex | Gemini | Gap? |
|---|---|---|---|---|---|
| 1 | A1 regression test exists and fails pre-addendum | **verified** — "Every `SessionContext(...)` inside `workspace_lock()` passes `owns_lock=False` (Alignment full enumeration; Adversarial mutation test)" | **verified** — "`owns_lock=False` call sites are present, the A1 regression tests are substantive" | **verified** — "`test_default_owns_lock_true_deadlocks_under_workspace_lock` correctly proves the old pattern deadlocks; regression signal is genuine and robust" | None |
| 2 | Scope-tracks-config behavior evaluation | Flagged as **m-9 minor** — "with `default_scope=docs`, MCP rename will NOT rewrite body references in `.ontos-internal/**`... flag-only, not must-fix" | **not addressed** | **BLOCKING (B-2)** — "Cross-Workspace Lock Bypass in `rename_document`... writing to cross-workspace files without acquiring their respective `workspace_lock`s violates A1/A3 write-safety guarantees" | Severity disagreement (see CB-B3, §6) |
| 3 | FrozenInstanceError workaround correctness | **SF-3 Should-Fix** — "No direct regression test for the Py-3.14 contextlib / frozen-dataclass workaround... Note: there is NO `except FrozenInstanceError` — Adversarial's inspection confirms the catch is narrow-by-type, not a masking bug" | **not addressed** | **verified** — "the `catch-inside-with` workaround... is narrowly scoped (`except OntosUserError: ...`) and clearly documented... without leaking state" | None (all agree workaround is narrow; CC flags test coverage gap) |
| 4 | Post-rollback `rebuild_workspace` in all tools | **verified** — "All four write tools call `_rebuild_safely` on commit failure (A3 compliance)" | **Should-Fix (SF-B7)** — "single-file write tools implement A3 as rebuild-on-error only, not rollback-then-rebuild" | **verified** — "Every write tool (`writes.py:169` and `rename_tool.py:237`) correctly invokes `portfolio_index.rebuild_workspace(...)` on a best-effort basis after `commit()` raises, successfully satisfying addendum A3" | Semantic: "rebuild-on-error" vs "rollback-then-rebuild" — Codex reads spec more strictly (see §6) |
| 5 | Bundle truncation tail-first behavior | **not addressed as a blocker** — "`max_logs` independence — VERIFIED by `test_bundler_max_logs_caps_number_of_log_entries` with `token_budget=128000` (huge)" | **BLOCKING (B-2)** — "bundle-config work did not land. `tools.py:411` still forwards only `token_budget`; `portfolio_config.py:19,26` and `bundler.py:31` still use the old `8192 / 5 / 14` defaults" | **BLOCKING (B-1)** — "`build_context_bundle()` is invoked with only the `token_budget` parameter. It does not pass `max_logs` or `log_window_days` from the portfolio config" | 2-of-3 agree blocking; CC verifies partial sub-claim (defaults) fixed at `7cbc3152` (see CB-B1, §6) |
| 6 | `build_rename_plan` equivalence test validity | **SF-1 Should-Fix** — "CLI-vs-MCP `build_rename_plan` equivalence test is tautological... compares two CLI-path invocations... It does NOT invoke `rename_tool._rename_document_impl` through the MCP dispatcher" | **verified** — "the `build_rename_plan` equivalence test is meaningful" | **verified** — "`test_build_rename_plan_equivalence_cli_vs_injected_docs` successfully passes the exact same `scope_data.documents` dict to both the CLI and direct paths. If CWD-vs-injected drift is reintroduced, the test will fail as expected" | Direct disagreement (see §6) |
| 7 | `tools.py` conflict resolution correctness | m-B1/m-B2 minor — "wrapper declares `workspace_id: str`... no runtime issue" (Stage-1 consolidation §5 asserts: "`_validate_workspace_id` preserves... Dev 4's `Optional[PortfolioIndexLike]` type hint") | **verified** — not flagged | **BLOCKING (B-3)** — "stacked-merge conflict resolution on `_validate_workspace_id` correctly preserved Dev 2's delegation body... but it completely dropped Dev 4's `Optional[PortfolioIndexLike]` type hint, reverting to `portfolio_index: Any`" | Direct contradiction (see CB-B5, §6) |
| 8 | `read_only` enforcement across write tools | **verified** — "`read_only=True` is checked before `workspace_lock()` in all four tools; refusal is `isError=True` with `error_code=\"E_READ_ONLY\"`; tests assert error-code identity, not truthy" | **BLOCKING (B-1)** — "`read_only=True` still advertises all four write tools in `tools/list`. `server.py:163` always calls `_register_write_tools(...)`, and I reproduced `list_tools()` returning `scaffold_document`, `log_session`, `promote_document`, and `rename_document` under `read_only=True`" | **verified** — "`read_only` is enforced, returns structured `isError: true` (`E_READ_ONLY`). Invocation errors route via `_user_error_result(isError=True)`" | Direct contradiction on registration vs call-time (see CB-B2, §6) |

**Coverage gaps:** Every attack-surface item has at least one platform's coverage. Item 3 (FrozenInstanceError) and Item 2 (scope-tracks-config) are not addressed by Codex, but Claude Code + Gemini cover both.

---

## 6. Agreement Analysis

### Strong agreement (3/3)
- **A1 single-lock discipline intact.** All three platforms verified `owns_lock=False` at every `SessionContext(...)` inside `workspace_lock()`. A1 regression test (`test_default_owns_lock_true_deadlocks_under_workspace_lock`) is substantive.
- **A3 rebuild invoked on commit failure.** All three observe `_rebuild_safely(...)` / `rebuild_workspace(...)` in every write tool (Codex qualifies semantic correctness — see SF-B7).
- **`read_only` call-time refusal works.** Envelope shape `isError: true` with `error_code="E_READ_ONLY"` on write-tool invocation verified by all platforms. Disagreement (CB-B2) is about registration-time, not call-time.
- **Workspace ID propagation matches CB-11 patterns.**

### Partial agreement (2/3)
- **Bundle config wiring incomplete (CB-B1):** Codex + Gemini agree at their respective HEADs; Claude Code at `7cbc3152` verified one sub-claim (defaults) was fixed by Dev 4, but did not directly address the call-site forwarding gap Gemini and Codex flag.

### Disagreements (preserved verbatim — not smoothed)

| Topic | Platform views | Resolution |
|---|---|---|
| **read_only registration (CB-B2)** | **Codex (B-1):** "`read_only=True` still advertises all four write tools in `tools/list`. `ontos/mcp/server.py:163` always calls `_register_write_tools(...)`, and I reproduced `list_tools()` returning `scaffold_document`, `log_session`, `promote_document`, and `rename_document` under `read_only=True`." <br><br> **Gemini (attack-surface §8):** "`read_only` is enforced, returns structured `isError: true` (`E_READ_ONLY`). Invocation errors route via `_user_error_result(isError=True)`, E_PORTFOLIO_BUSY caught/mapped in `portfolio.py:221`, `workspace_id` propagation matches CB-11 patterns." <br><br> **Claude Code (consolidation §5):** "`read_only=True` is checked before `workspace_lock()` in all four tools; refusal is `isError=True` with `error_code=\"E_READ_ONLY\"`; tests assert error-code identity, not truthy." | **Preserve Codex's blocking finding** — Codex produced reproduction evidence at `server.py:163`. Gemini and Claude Code appear to have evaluated call-time refusal only, not registration. Per rule #2 (single-platform not downgraded) and rule #5 (side with more skeptical). Orchestrator must verify at correct HEAD. |
| **Scope-tracks-config / rename cross-workspace (CB-B3)** | **Gemini (B-2):** "Dev 3's refactor to `resolve_scan_scope(None, config.scanning.default_scope)` was explicitly accepted, but it introduces a severe concurrency vulnerability. If a workspace configures `default_scope = portfolio`, `rename_document` will find and attempt to update references in external workspaces. However, the tool only ever acquires `workspace_lock(plan.workspace_root)` for the *local* workspace (`rename_tool.py:344`). Writing to cross-workspace files without acquiring their respective locks violates the A1/A3 write-safety guarantees." <br><br> **Claude Code (Adversarial m-9):** "`resolve_scan_scope` accepts only `docs`/`library`; no `portfolio` scope exists (brief's \"default_scope=portfolio\" hypothetical is vacuous). BUT with `default_scope=docs`, MCP rename will NOT rewrite body references living in `.ontos-internal/**`. The cross-scope collision guard only checks frontmatter-ID, not body-ref drift into LIBRARY.... This was the 'accepted deviation' — so flag-only, not must-fix." <br><br> **Codex:** not addressed. | **Preserve Gemini's blocking framing** per rule #5 (more skeptical wins). Claude Code's technical correction (no `portfolio` scope exists in `resolve_scan_scope` today) is material — the orchestrator must reconcile: if Gemini's attack requires a scope that doesn't exist, the vulnerability may be latent not live. But the severity disagreement stands and is not smoothed. |
| **`build_rename_plan` equivalence test validity (SF-B1 / attack-surface §6)** | **Claude Code (Adversarial SF-1):** "The test compares two *CLI-path* invocations of `build_rename_plan` with identical inputs. `_prepare_plan` itself calls `build_rename_plan` internally (`rename.py:473, 518`), so the test is effectively `build_rename_plan(X) == build_rename_plan(X)`. It does NOT invoke `rename_tool._rename_document_impl` through the MCP dispatcher — the CLI-vs-MCP divergence the refactor was intended to prevent is not actually guarded." <br><br> **Gemini:** "`test_build_rename_plan_equivalence_cli_vs_injected_docs` successfully passes the exact same `scope_data.documents` dict to both the CLI and direct paths. If CWD-vs-injected drift is reintroduced, the test will fail as expected." <br><br> **Codex:** "the `build_rename_plan` equivalence test is meaningful." | **Preserve Claude Code's Should-Fix framing** — Claude Code's Adversarial provides a specific CLI-vs-CLI mechanism; Gemini and Codex do not refute that mechanism, only confirm a weaker property. Orchestrator resolves via direct inspection at correct HEAD. |
| **Type hint drop on `_validate_workspace_id` (CB-B5)** | **Gemini (B-3):** "The stacked-merge conflict resolution on `_validate_workspace_id` correctly preserved Dev 2's delegation body... but it completely dropped Dev 4's `Optional[PortfolioIndexLike]` type hint, reverting to `portfolio_index: Any`." <br><br> **Claude Code (consolidation §5):** "Conflict-resolution site `_validate_workspace_id` preserves both Dev 2's delegation and Dev 4's `Optional[PortfolioIndexLike]` type hint with no lost semantics." <br><br> **Claude Code (Adversarial m-1):** concerns adjacent `workspace_id: str` vs `Optional[str]` drift on the *same* wrapper, not `portfolio_index`. | **Direct contradiction.** Preserve Gemini's blocking framing per rule #5 (side with more skeptical). Orchestrator must directly inspect `ontos/mcp/tools.py:494` at correct HEAD to resolve. |
| **A3 semantics: rebuild-on-error vs rollback-then-rebuild (SF-B7)** | **Codex:** "single-file write tools implement A3 as rebuild-on-error only, not rollback-then-rebuild. `writes.py:174` catches `commit()` failure and only calls `_rebuild_safely(...)`. The authoritative addendum says every write tool must rebuild after rollback of failed writes." <br><br> **Claude Code + Gemini:** both treat `_rebuild_safely(...)` on commit failure as satisfying A3. | **Preserve Codex's Should-Fix framing** — Codex notes this is partly a doc inconsistency: Dev 2's Track B implementation spec softened to rebuild-on-error only. The addendum/spec contradiction itself is a finding the orchestrator must resolve. |

---

## 7. Regression Status

Per-platform framing, not smoothed:

| Platform | Framing |
|---|---|
| Claude Code | "Clean" at correct HEAD `7cbc3152` — "four hard guards (A1 single-lock discipline, A3 post-rollback rebuild, `read_only` enforcement, conflict-merge semantics) are all intact at the actual PR tip." |
| Codex | "Needs fixes" with three blocking findings; regression found in registration-time `read_only` leakage and bundle-config non-landing. |
| Gemini | "DO NOT MERGE" with three blocking findings including cross-workspace lock bypass (data-corruption risk). A1 regression signal clean. |

**Consolidated framing:** **Regression found.** Per hard rule #5, with Codex + Gemini both flagging regressions and Claude Code at the minority, the consolidated verdict adopts the more skeptical framing. Track A precedent (§6) set the same rule: "Claude Code frames regression status as 'clean with one concern'... Codex explicitly flags 'regression found'... Gemini flags 'regression found'... **Resolution: side with Codex/Gemini framing.**"

HEAD drift is part of the regression story but does not erase the regressions — Codex's reproduction of registration leakage at `server.py:163` and slug collision at `writes.py:146,160` stand as reproduced defects.

---

## 8. Required Actions for Dev Team

| Priority | Action | Addresses | File(s) | Test Required |
|---|---|---|---|---|
| **P0** | Skip `_register_write_tools(...)` entirely when `read_only=True`; add `list_tools()` regression test asserting the four write tools are absent. | CB-B2 | `ontos/mcp/server.py:163`; new test | `list_tools()` under `read_only=True` does not contain `scaffold_document`, `log_session`, `promote_document`, `rename_document`. |
| **P0** | Resolve the `rename_document` scope-tracks-config contract: either override config default and always use `ScanScope.LIBRARY`, or implement multi-workspace locking before accepting portfolio scope. Document in spec. | CB-B3 | `ontos/mcp/rename_tool.py:429,344`; spec | Regression test for cross-workspace rename with workspace_lock contention. |
| **P0** | Wire `config.scanning.bundle_max_logs` and `config.scanning.bundle_log_window_days` into `build_context_bundle()`. Verify defaults `8000 / 20 / 30` at correct HEAD. | CB-B1 | `ontos/mcp/tools.py:411/467`; `ontos/mcp/portfolio_config.py`; `ontos/mcp/bundler.py` | Test that `portfolio.toml` override of `bundle_max_logs=N` produces a bundle with at most N logs; same for window_days. |
| **P0** | Stop deriving rebuild slugs from `workspace_root.name`. Use canonical portfolio slug (with collision suffixes) from `allocate_slug`. | CB-B4 | `ontos/mcp/writes.py:146,160`; `ontos/mcp/rename_tool.py:181` | Two-repo basename-collision test: create workspace, rename dir to collision basename, scaffold a doc, assert portfolio index picks it up. |
| **P0** | Restore `Optional[PortfolioIndexLike]` type hint on `_validate_workspace_id`. Align wrapper `workspace_id: str` → `Optional[str]`. | CB-B5, m-B1 | `ontos/mcp/tools.py:494,524` | Static type check (mypy/pyright) passes; wrapper accepts `None`. |
| **P1** | Decide whether `workspace_id` is required for write tools; align code and tests with chosen contract. Right now design note and implementation disagree. | SF-B6 | `ontos/mcp/writes.py:143`; `ontos/mcp/rename_tool.py:178`; `TrackB-Design.md:182,203` | Per chosen contract: either test structured error on missing `workspace_id`, or document fallback semantics. |
| **P1** | Resolve addendum-vs-implementation-spec contradiction on A3 semantics; either update addendum to rebuild-on-error, or change `writes.py` to rollback-then-rebuild. | SF-B7 | `writes.py:174`; `ontos-v4.1-spec-addendum-v1.2.md:59`; `v4.1_TrackB_Implementation_Spec.md:146` | Test reflects the resolved contract. |
| **P1** | Add `rename_document()` MCP-dispatcher invocation test that diffs output against CLI's `RenamePlan`. | SF-B1 | `tests/commands/test_rename.py` | Would fail if CLI-vs-MCP drift were reintroduced. |
| **P1** | Replace tautological deterministic-ordering test with two-snapshot filesystem-order test (monkeypatch `os.scandir`). | SF-B2 | `tests/mcp/test_bundler.py:150-162` | Would fail if `sorted()` calls in `bundler.py` were deleted. |
| **P2** | Add Py-3.14 regression test for contextlib/frozen-dataclass catch-inside-`with` workaround. | SF-B3 | `ontos/mcp/writes.py:287-323`; `ontos/mcp/rename_tool.py:339-375`; new test | Force `OntosUserError` from inside lock; assert envelope `error_code` survives. |
| **P2** | Document four new MCP write tools in `Ontos_Manual.md` and `AGENTS.md`. | SF-B4 | `docs/reference/Ontos_Manual.md`; `AGENTS.md`; `ontos/core/instruction_artifacts.py` | — |
| **P2** | Document `load_portfolio_config` contract change (raises `FileNotFoundError`). | SF-B5 | `ontos/mcp/portfolio_config.py:52-62` | — |
| **P3** | Tighten tests away from `inspect.getsource()` / symbol-identity assertions. | m-B10 | `test_write_tools.py:474`; `test_context_contention.py:272`; `test_rename_document.py:368` | Tests assert behavior, not source text. |
| **P3** | Defer m-B1..m-B9 to a follow-up cleanup PR (no correctness issues individually). | m-B1..m-B9 | various | — |

---

## 9. Decision Summary

**Status: Needs Fixes.**

**Rationale:** Two skeptical platforms (Codex, Gemini) flag reproducible blocking defects including registration-time `read_only` leakage, cross-workspace lock bypass in `rename_document`, non-canonical slug collisions, dropped type hints, and incomplete bundle-config wiring. Per hard rule #5, the consolidated framing sides with the skeptical platforms; Claude Code's `approve-with-fixes` at correct HEAD `7cbc3152` is the minority view and does not override regressions reproduced with evidence. Per hard rule #2, single-platform findings (CB-B2, CB-B3, CB-B4, CB-B5) are not downgraded — Track A precedent demonstrated that single-platform findings (CB-5, CB-7, CB-8) were the most consequential. One revision cycle is expected; no reimplementation needed.

---

## 10. Single-Platform Findings to NOT Lose

Explicit preservation list, per hard rule #2 and Track A precedent §10:

**Codex-only (4):**
- **CB-B2** — `read_only=True` registration leak at `server.py:163` (reproduced; Gemini + Claude Code cleared call-time only).
- **CB-B4** — Rebuild uses non-canonical slug, stale index under basename collision (reproduced with two `workspace` repos).
- **SF-B6** — Missing `workspace_id` falls back to current workspace instead of structured error.
- **SF-B7** — A3 is rebuild-on-error only, not rollback-then-rebuild (spec contradiction flagged).
- **m-B10** — Source-inspection / symbol-identity tests weaker than behavioral regressions.

**Gemini-only (2):**
- **CB-B3** — Cross-workspace lock bypass in `rename_document` via `default_scope=portfolio` (framed as severe concurrency / data-corruption risk; Claude Code downgrades to m-9 on a different mechanism).
- **CB-B5** — `_validate_workspace_id` stacked-merge dropped `Optional[PortfolioIndexLike]` type hint (Claude Code Stage-1 consolidation §5 directly contradicts — orchestrator must verify at correct HEAD).

**Claude Code-only (5):**
- **SF-B1** — `build_rename_plan` equivalence test is tautological (CLI-vs-CLI, not CLI-vs-MCP) — Gemini + Codex cleared the test but did not refute Claude Code's specific mechanism.
- **SF-B2** — SF-9 deterministic input ordering not actually tested (`sorted()` calls could all be deleted and test would still pass).
- **SF-B3** — No direct regression test for Py-3.14 contextlib / frozen-dataclass workaround.
- **SF-B4** — Four new MCP write tools missing from `Ontos_Manual.md` and `AGENTS.md`.
- **SF-B5** — `load_portfolio_config` raises `FileNotFoundError` on missing config (contract change).
- **m-B1..m-B9** — Adversarial/Peer/Alignment minor-tier findings not surfaced by Codex or Gemini.

---

## Orchestrator Handoff Brief

**Headline:** Track B is **Needs Fixes** with 5 blocking issues (one 2-of-3 confirmation, four single-platform). Core lock discipline (A1), rebuild-on-failure (A3), and call-time `read_only` refusal are all intact; the blockers concentrate in registration-time `read_only`, rename cross-workspace safety, slug canonicalization, type hints, and bundle-config wiring.

**HEAD discipline for remediation:** Pin follow-up review to `gh pr view 92 --json headRefOid` (was `7cbc3152` at this verdict). The stale-HEAD cascade from Phase D Stage 1 must not recur.

**Direct contradictions orchestrator must resolve by inspection at correct HEAD:**
1. `_validate_workspace_id` type hint (Gemini blocking vs Claude Code Stage-1 clears).
2. `read_only` registration (Codex blocking vs Gemini + Claude Code clear call-time).
3. `build_rename_plan` equivalence test meaning (Claude Code tautological vs Gemini + Codex meaningful).
4. Rename scope-tracks-config severity (Gemini blocking concurrency vs Claude Code m-9 flag-only).
5. A3 semantics (Codex rebuild-on-error vs Claude Code + Gemini consider rebuild sufficient; addendum text vs implementation-spec text inconsistency).

Per rule #1, this verdict does not smooth these contradictions; per rule #5 the consolidated framing adopts the more skeptical view. The orchestrator dispatches remediation.
