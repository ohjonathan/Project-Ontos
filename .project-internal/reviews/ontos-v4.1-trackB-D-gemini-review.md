# Ontos v4.1 Track B (PR #92) - Review Synthesis

## Verdict Summary

| Reviewer | Persona | Verdict | Key Findings |
| :--- | :--- | :--- | :--- |
| **R1** | Peer | **BLOCKING** | `bundle_max_logs` and `bundle_log_window_days` are parsed but ignored at runtime; `build_context_bundle()` falls back to defaults. |
| **R2** | Alignment | **BLOCKING** | Stacked-merge conflict resolution dropped Dev 4's `Optional[PortfolioIndexLike]` type hint. |
| **R3** | Adversarial | **BLOCKING** | Scope-tracks-config behavior in `rename_document` allows modifying cross-workspace files without acquiring their respective `workspace_lock`s. |

## Blocking Issues

1. **Dead Bundle Config Truncation (R1 / R3 Cross-Confirmed)**
   - **File:** `ontos/mcp/tools.py:467`
   - **Details:** `build_context_bundle()` is invoked with only the `token_budget` parameter. It does not pass `max_logs` or `log_window_days` from the portfolio config, causing the bundler to silently fall back to hardcoded defaults (5 and 14). The `portfolio.toml` settings parsed in `portfolio_config.py` are dead config at runtime.
   - **Action:** Thread `config.scanning.bundle_max_logs` and `config.scanning.bundle_log_window_days` into the `build_context_bundle` call.

2. **Cross-Workspace Lock Bypass in `rename_document` (R3)**
   - **File:** `ontos/mcp/rename_tool.py:429`
   - **Details:** Dev 3's refactor to `resolve_scan_scope(None, config.scanning.default_scope)` was explicitly accepted, but it introduces a severe concurrency vulnerability. If a workspace configures `default_scope = portfolio`, `rename_document` will find and attempt to update references in external workspaces. However, the tool only ever acquires `workspace_lock(plan.workspace_root)` for the *local* workspace (`rename_tool.py:344`). Writing to cross-workspace files without acquiring their respective locks violates the A1/A3 write-safety guarantees.
   - **Action:** Either revert `rename_document` to always use `ScanScope.LIBRARY` (overriding the config default for this specific tool), or implement multi-workspace locking.

3. **Type Hint Dropped in Conflict Resolution (R2)**
   - **File:** `ontos/mcp/tools.py:494`
   - **Details:** The stacked-merge conflict resolution on `_validate_workspace_id` correctly preserved Dev 2's delegation body (`_shared(portfolio_index, workspace_id)`), but it completely dropped Dev 4's `Optional[PortfolioIndexLike]` type hint, reverting to `portfolio_index: Any`.
   - **Action:** Restore the `Optional[PortfolioIndexLike]` type hint.

## Agreement Analysis

- **R1 vs R3 (Bundle Config):** Complete agreement. R1 identified that the parameters were missing from the function call, and R3 validated attack surface item 5, confirming that the budget truncation pressure ignores the config values entirely.
- **R2 vs R3 (Rename Scope):** Disagreement on the acceptance of Dev 3's refactor. R2 verified the refactor complied with the spec deviation as written. However, R3 (Adversarial) escalated it to a blocking vulnerability because it bypasses `workspace_lock` boundaries. **R3's finding overrides the deviation acceptance due to the severe data corruption risk.**

## Minor / Should-Fix (Attack Surface Cleared)

- **A1 Regression Test Efficacy (R3):** The test `test_default_owns_lock_true_deadlocks_under_workspace_lock` correctly proves that the old `owns_lock=True` pattern deadlocks against an outer `workspace_lock`. The regression signal is genuine and robust.
- **`FrozenInstanceError` Workaround (R3):** The `catch-inside-with` workaround in `writes.py` and `rename_tool.py` is narrowly scoped (`except OntosUserError: ...`) and clearly documented to prevent `workspace_lock()` from re-raising, mitigating the Python 3.14 dataclass traceback gotcha without leaking state.
- **Post-rollback `rebuild_workspace` (R2/R3):** Every write tool (`writes.py:169` and `rename_tool.py:237`) correctly invokes `portfolio_index.rebuild_workspace(slug, workspace_root)` on a best-effort basis after `commit()` raises, successfully satisfying addendum A3.
- **Equivalence Test Guard (R3):** `test_build_rename_plan_equivalence_cli_vs_injected_docs` successfully passes the exact same `scope_data.documents` dict to both the CLI and direct paths. If CWD-vs-injected drift is reintroduced, the test will fail as expected.
- **CB-1..CB-11 Compliance (R2):** `read_only` is enforced and returns structured `isError: true` (`E_READ_ONLY`). Invocation errors route via `_user_error_result(isError=True)`. `E_PORTFOLIO_BUSY` is correctly caught and mapped in `portfolio.py:221`. `workspace_id` propagation matches CB-11 patterns.

## Required Actions
**Do NOT merge.** Return PR #92 to the Dev team to fix the cross-workspace lock bypass, wire the bundle config, and restore the dropped type hint.