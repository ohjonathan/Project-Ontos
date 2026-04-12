# PR #92 Review Consolidation — Ontos v4.1 Track B

**Review date:** 2026-04-12
**PR:** #92 (`feature/v4.1-track-b` → `main`)
**Actual PR HEAD on GitHub:** `7cbc3152d36789e511bca785a4506f4c88fd39e0` (Dev 4 merged)
**Task-spec pinned HEAD (stale):** `88fe711e5647ae7d83a490d45d61c483edae1db3` (Dev 3 merge — one commit behind)
**Consolidator's independent pytest at `7cbc3152`:** **1113 passed, 2 skipped, 2 warnings in 42.58s** (Python 3.14 via `.venv-mcp`)
**Reviewer team:** Peer (sonnet), Alignment (sonnet), Adversarial (opus)

---

## 0. Critical meta-finding — stale task-spec HEAD

The task brief pinned `88fe711` as PR #92's head. GitHub reports `7cbc3152` (Dev 4's merge `8a4069c` is part of the PR). Local branch was also at `88fe711` when reviewers started. **This single error cascaded through the review:**

- **Adversarial** independently detected the drift, checked out `7cbc315`, and reviewed the correct tip.
- **Alignment** detected the drift and flagged it as SF-A, but reviewed local `88fe711` and hedged accordingly.
- **Peer** did NOT detect the drift, reviewed `88fe711`, and produced one false-positive **Blocking** finding and one false-positive **Should-Fix**, both of which are fixed by Dev 4's commits already present on the PR.

I verified both commits directly (`git show 88fe711:ontos/mcp/portfolio_config.py` vs current tip) and by checking `gh pr view 92 --json headRefOid`. The brief's SHA was wrong by one commit.

---

## 1. Verdict Summary

| Reviewer | Verdict | Pytest observed | Blocking | Should-Fix | Minor |
|---|---|---|---|---|---|
| Peer (sonnet) | approve-with-fixes | 963 passed non-MCP / MCP blocked (wrong env + stale HEAD) | 1 (refuted — stale HEAD) | 2 | 3 |
| Alignment (sonnet) | approve-with-fixes | 963 passed non-MCP / MCP blocked (wrong env, stale HEAD) | 0 | 2 | 2 |
| Adversarial (opus) | approve-with-fixes | 1113 passed, 2 skipped (at correct HEAD `7cbc315`) | 0 | 4 | 5 |
| **Consolidator verification** | **approve-with-fixes** | **1113 passed, 2 skipped** (at `7cbc315`) | **0** | **—** | **—** |

**Consensus:** `approve-with-fixes`. The four hard guards (A1 single-lock discipline, A3 post-rollback rebuild, `read_only` enforcement, conflict-merge semantics on `_validate_workspace_id`) are all intact at the actual PR tip.

---

## 2. Blocking Issues

**None at actual PR HEAD (`7cbc3152`).**

The one Blocking finding submitted (Peer B-1) was refuted by direct inspection — see §5 Agreement Analysis.

---

## 3. Should-Fix

### [SF-1] CLI-vs-MCP `build_rename_plan` equivalence test is tautological
- **Source:** Adversarial (Item 6)
- **Location:** `tests/commands/test_rename.py:526-609`
- **Evidence:** The test compares two *CLI-path* invocations of `build_rename_plan` with identical inputs. `_prepare_plan` itself calls `build_rename_plan` internally (`rename.py:473, 518`), so the test is effectively `build_rename_plan(X) == build_rename_plan(X)`. It does NOT invoke `rename_tool._rename_document_impl` through the MCP dispatcher — the CLI-vs-MCP divergence the refactor was intended to prevent is not actually guarded.
- **Cross-reviewer:** Single-reviewer (Adversarial only) — not downgraded.
- **Fix:** Add a test that invokes `rename_document()` via the MCP dispatcher, captures the files/content it would produce, and diffs against CLI's `RenamePlan`.

### [SF-2] SF-9 deterministic input ordering is not actually tested
- **Source:** Adversarial (Item 5e)
- **Location:** `ontos/mcp/bundler.py:54-55, 69, 193` (the `sorted(docs_by_id)` calls labeled "SF-9"); `tests/mcp/test_bundler.py:150-162` (the "determinism" test)
- **Evidence:** The test runs 4 passes on the SAME snapshot object. Dict-iteration order is stable for a single dict, so the test would pass even if every `sorted()` call in `bundler.py` were deleted. The SF-9 fix is not defended by the test claimed to defend it.
- **Cross-reviewer:** Single-reviewer (Adversarial) — not downgraded.
- **Fix:** Build two snapshots from the same logical files but with different filesystem-listing orders (e.g., monkeypatch `os.scandir`) and assert identical bundle output.

### [SF-3] No direct regression test for the Py-3.14 contextlib / frozen-dataclass workaround
- **Source:** Adversarial (Item 3)
- **Location:** `ontos/mcp/writes.py:287-323`, `ontos/mcp/rename_tool.py:339-375`
- **Evidence:** The catch-inside-`with` workaround (catching `OntosUserError`/`OntosInternalError` inside `workspace_lock()` to avoid contextlib's `__exit__` mutating `__traceback__` on a frozen dataclass exception) is only incidentally protected by happy-path tests. A refactor that moves the catch outside the lock would be silent on pre-3.14 interpreters and break only on 3.14. Note: there is NO `except FrozenInstanceError` — Adversarial's inspection confirms the catch is narrow-by-type, not a masking bug.
- **Cross-reviewer:** Single-reviewer (Adversarial) — not downgraded.
- **Fix:** Add a test that forces a write-tool impl to raise `OntosUserError` from inside the lock and asserts the envelope's `error_code` survives.

### [SF-4] MCP write tools not documented in `Ontos_Manual.md` or `AGENTS.md`
- **Source:** Peer (M-2); related observation from Adversarial scope warning
- **Location:** `docs/reference/Ontos_Manual.md` (MCP section from line ~394+); `ontos/core/instruction_artifacts.py:181`
- **Evidence:** `grep scaffold_document docs/reference/Ontos_Manual.md` returns nothing. The four new tools (`scaffold_document`, `log_session`, `promote_document`, `rename_document`) are not mentioned in any user-facing doc. The Manual's MCP section still reflects Track A read-only tools only.
- **Cross-reviewer:** Single-reviewer (Peer) — not downgraded.
- **Fix:** Add a subsection for the four write tools to the Manual, with input/output schemas and `read_only` / `workspace_id` behavior. Update `instruction_artifacts.py` if it auto-generates a tool list.

### [SF-5] `load_portfolio_config` contract change (raises `FileNotFoundError` on missing config)
- **Source:** Peer (M-3)
- **Location:** `ontos/mcp/portfolio_config.py:52-62`
- **Evidence:** Pre-PR called `ensure_portfolio_config()` (write-on-read). Post-PR raises `FileNotFoundError`. The `get_context_bundle` caller catches it correctly (line 443-444), but the public-API semantics changed. No other direct callers in production today, but any future caller must be aware.
- **Cross-reviewer:** Single-reviewer (Peer) — not downgraded.
- **Fix:** Document the contract change in the module docstring or release notes. Low urgency.

---

## 4. Minor

### [m-1] `_validate_workspace_id` wrapper signature asymmetry
- **Source:** Adversarial (M-1)
- **Location:** `ontos/mcp/tools.py:524`
- **Evidence:** Wrapper declares `workspace_id: str` (non-Optional); delegated helper `_validation.validate_workspace_id` accepts `Optional[str]`. Both current callers pre-filter None, so no runtime issue — but the drift invites future callers to pass None and hit the helper's early-return path.
- **Fix:** Align wrapper signature to `Optional[str]`.

### [m-2] `_slugify_workspace_name` is a one-line wrapper on `scanner.slugify`
- **Source:** Alignment (SF-B); Peer and Adversarial did not flag
- **Location:** `ontos/mcp/tools.py:537-538`
- **Evidence:** `def _slugify_workspace_name(raw: str) -> str: return slugify(raw)` — no independent logic. Not a CB-6 violation (no divergent implementation), but the wrapper creates a spurious third symbol that could confuse which slugify to call.
- **Fix:** Remove the wrapper; have `_primary_workspace_slug` call `slugify` directly.

### [m-3] Result-helper functions copy-pasted between `writes.py` and `rename_tool.py`
- **Source:** Peer (SF-2)
- **Location:** `ontos/mcp/writes.py:66-115` vs `ontos/mcp/rename_tool.py:104-150`
- **Evidence:** `_success_result`, `_write_error_result`, `_user_error_result` are verbatim (only docstrings differ). A comment in `rename_tool.py` notes the intentional mirror. Divergence risk grows every time the error envelope shape changes.
- **Fix:** Move to shared module (e.g., `_result_helpers.py` or existing `_types.py`).

### [m-4] `E_UNKNOWN_WORKSPACE` path not exercised by write-tool tests
- **Source:** Peer (M-1)
- **Location:** `tests/mcp/test_write_tools.py`, `tests/mcp/test_rename_document.py`
- **Evidence:** Tests cover `E_PORTFOLIO_REQUIRED` (non-portfolio mode + workspace_id) but not portfolio-active + unknown slug → `E_UNKNOWN_WORKSPACE`. The helper itself is correct (`_validation.py:50-59`); only the dispatch path is untested.
- **Fix:** Add one test per write tool that asserts `E_UNKNOWN_WORKSPACE` is returned when `workspace_id` does not match a known slug in portfolio mode.

### [m-5] `rename_document` rollback uses subprocess `git checkout -- .`
- **Source:** Adversarial (M-4)
- **Location:** `ontos/mcp/rename_tool.py:270-285`
- **Evidence:** Uses `cwd=workspace_root`. Degrades silently (logs "rollback failed") if workspace is in a non-git directory or a submodule with `.git` as a file. Proceeds to raise the original exception, but the filesystem is left in partially-rolled-back state.
- **Fix:** Verify `test_a3_rollback_on_commit_failure` exercises the non-git-workspace case, or add one.

### [m-6] A3-rebuild count assertion is brittle
- **Source:** Adversarial (M-3)
- **Location:** `tests/mcp/test_write_tools.py:409`
- **Evidence:** Asserts `len(rebuild_calls) == 1`. If future code adds a pre-commit rebuild, the assertion fails in a confusing way.
- **Fix:** Assert `>=1` or tag rebuild calls with purpose.

### [m-7] `_recent_logs` mtime fallback brittle in CI
- **Source:** Adversarial (M-5)
- **Location:** `ontos/mcp/bundler.py:226-234`
- **Evidence:** Falls back to `filepath.stat().st_mtime` when no frontmatter/id/filename date. In fresh-clone CI, all files share checkout-time mtime; every undated log collapses to the same bucket and the SF-4 tiebreak becomes load-bearing.
- **Fix:** Acceptable as-is given SF-4 tiebreak is deterministic. Document the CI behavior or add a warning when many undated logs share an mtime.

### [m-8] `E_WORKSPACE_BUSY` `isError: true` path not directly tested in runnable suite
- **Source:** Alignment (m-A)
- **Location:** `ontos/mcp/writes.py:324-327`, `ontos/mcp/rename_tool.py:376-378`
- **Evidence:** The code path is functionally correct (outer `except OntosUserError` → `_user_error_result` → `isError=True`), but no test in the currently-runnable suite directly forces `workspace_lock()` to raise `E_WORKSPACE_BUSY` and checks the envelope.
- **Fix:** Add a focused test that acquires the lock in a helper thread and verifies each write tool returns `isError=True` with `error_code="E_WORKSPACE_BUSY"`.

### [m-9] Scope-tracks-config hazard for body-reference drift
- **Source:** Adversarial (Item 2 — deeper analysis)
- **Location:** `ontos/mcp/rename_tool.py:429`; `ontos/commands/rename.py:386-395`
- **Evidence:** `resolve_scan_scope` accepts only `docs`/`library`; no `portfolio` scope exists (brief's "default_scope=portfolio" hypothetical is vacuous). BUT with `default_scope=docs`, MCP rename will NOT rewrite body references living in `.ontos-internal/**`. The cross-scope collision guard only checks frontmatter-ID, not body-ref drift into LIBRARY.
- **Fix:** Document the limitation or extend the collision guard to detect body-ref drift across scopes. This was the "accepted deviation" — so flag-only, not must-fix.

---

## 5. Agreement Analysis

The three reviewers converged on `approve-with-fixes`. Substantive disagreements reproduced below **verbatim** — not smoothed.

### Disagreement #1 — Blocking vs. non-issue on bundle config defaults

**Peer (blocking, B-1):**
> "`portfolio_config.py` defaults not updated to addendum values — test asserts values that don't exist in code. The source has `8192 / 5 / 14` in both the dataclass defaults and `_DEFAULT_CONFIG_TEXT`. The test … asserts `cfg.bundle_token_budget == 8000`, `cfg.bundle_max_logs == 20`, `cfg.bundle_log_window_days == 30` — these assertions would fail against the current implementation."

**Alignment (hedged SF-A):**
> "`portfolio_config.py:19-21` local defaults remain `8192/5/14` rather than the addendum-mandated `8000/20/30`. Again, fixed in `8a4069c`. **This is present only in the local checkout.** The remote `origin/feature/v4.1-track-b` (which is the actual PR #92 HEAD) includes Dev 4 commit `8a4069c` which fully wires both fields. The local branch is behind by one merge."

**Adversarial (no finding):**
> "(b) `max_logs` independence — VERIFIED by `test_bundler_max_logs_caps_number_of_log_entries` with token_budget=128000 (huge)."

**Consolidator's independent verification:**
- `git show 88fe711:ontos/mcp/portfolio_config.py` → `8192 / 5 / 14` (Peer reading correct for that commit)
- Current tip / `7cbc3152` / PR #92's actual GitHub head → `8000 / 20 / 30` (Alignment / Adversarial correct)
- `gh pr view 92 --json headRefOid` → `7cbc3152d36789e511bca785a4506f4c88fd39e0`
- Pytest at `7cbc3152`: **1113 passed, 2 skipped**. Zero `test_portfolio_config` failures.

**Resolution:** Peer's Blocking finding is a **false positive caused by stale grounding** (task brief pinned `88fe711`, PR actually at `7cbc3152`). Not a defect in PR #92. Alignment and Adversarial are correct.

### Disagreement #2 — `bundle_max_logs` isolation test

**Peer (SF-1):**
> "`bundle_max_logs` cap is not tested in isolation — no test seeds N+1 logs (where N is `max_logs`) and asserts that only N appear in the bundle."

**Adversarial:**
> "`max_logs` independence — VERIFIED by `test_bundler_max_logs_caps_number_of_log_entries` with token_budget=128000 (huge)."

**Resolution:** Another **stale-HEAD artifact**. The test `test_bundler_max_logs_caps_number_of_log_entries` was added in Dev 4 (PR #89, absent at `88fe711`). Peer could not see it; Adversarial read it at the real HEAD. Adversarial correct at PR #92's actual state.

### Agreement on all A1, A3, read_only, conflict-merge guards

All three reviewers agreed (with varying depth of evidence) that:
- Every `SessionContext(...)` inside `workspace_lock()` passes `owns_lock=False` (Alignment provided full enumeration; Adversarial provided mutation test).
- All four write tools call `_rebuild_safely` on commit failure (A3 compliance).
- `read_only=True` is checked before `workspace_lock()` in all four tools; refusal is `isError=True` with `error_code="E_READ_ONLY"`; tests assert error-code identity, not truthy.
- Conflict-resolution site `_validate_workspace_id` preserves both Dev 2's delegation and Dev 4's `Optional[PortfolioIndexLike]` type hint with no lost semantics.

No reviewer dissented on any of the above.

---

## 6. Spec-gap vs. implementation-gap

- **Task-spec gap (not implementation):** The brief's pinned HEAD `88fe711` was one commit behind the PR. Adversarial flagged this directly (SF-4 in their report). This is the root cause of both Peer false positives. **The brief should be updated to reference `7cbc3152` for future Track B reviews.**
- **Implementation gaps:** All SF-1 through SF-5 and m-1 through m-9 above.
- **No spec-gap findings** where the spec itself would need revision.

---

## 7. Required Actions (before merge)

1. **Update reviewer grounding.** When spawning the next Track B review, pin HEAD to `7cbc3152d36789e511bca785a4506f4c88fd39e0` (the `gh pr view` oid), not a merge commit of an upstream sub-PR.
2. **No blocking remediation required for PR #92 itself.** 1113/2 passes at the actual tip; all hard contracts intact.
3. **Before merge, address at least SF-1 and SF-2** (tautological / untested deterministic ordering). These are test-quality gaps that leave real regressions silent. SF-3 is desirable but lower urgency.
4. **Doc SF-4** (Manual + AGENTS.md update for the four new write tools) should land with or immediately after the merge — users need to know the new tools exist.
5. **Defer m-1 through m-9** to a follow-up cleanup PR — none are correctness issues.

---

## Appendix: Reviewer execution notes

- Peer and Alignment were briefed to use `/Library/Developer/CommandLineTools/usr/bin/python3` (system 3.9.6). That Python cannot install `mcp>=1.27` (requires ≥3.10), so their MCP-test runs collection-errored; both reported 963 non-MCP passes. This is an environment / briefing issue, not a defect.
- Adversarial discovered `.venv-mcp/bin/python` (Python 3.14) independently and ran the full suite. Consolidator (me) replicated this with 1113/2 at `7cbc3152`.
- The 10-test delta between `88fe711` (1103) and `7cbc3152` (1113) is exactly Dev 4's `tests/mcp/test_context_bundle_config.py` additions.
