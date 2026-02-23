---
id: log_20260222_add-promote-check-task-to-ontos-maintain
type: log
status: active
event_type: feature
source: Antigravity
branch: feat/maintain-promote-check
created: 2026-02-22
concepts: [maintain, curation, promote]
impacts: [ontos_manual, ontos_agent_instructions]
---

# Add promote_check task to ontos maintain

## Summary

Added `promote_check` (order 45) as the 9th task in the `ontos maintain` pipeline. After review, applied root correctness (decoupled from CWD via `repo_root`), ready semantics (`--check` reports ready count vs total candidates), and artifact consistency fixes. Squash-merged as PR #78.

## 1. Goal

Include scaffold and promote workflows under "Maintain Ontos" so weekly maintenance automatically reports curation opportunities.

## 2. Key Decisions

- **Scaffold not added separately** — `migrate_untagged` (order 10) already calls `find_untagged_files` + `_run_scaffold_command(apply=True)`, making a separate scaffold task redundant.
- **promote_check uses `--check` mode** — Non-interactive, read-only. Reports promotable docs without mutating anything.
- **Order 45** — Placed between `curation_stats` (40) and `consolidate_logs` (50), keeping the curation-related tasks grouped.
- **Root correctness** — Added `repo_root` to `PromoteOptions` so maintain passes `ctx.repo_root`, decoupling from CWD.
- **Ready semantics** — `--check` reports "N ready for promotion (M candidates)" where ready = `info.promotable == True`.

## 3. Alternatives Considered

- Considered adding both `scaffold` and `promote` as separate tasks — rejected because scaffold is already covered by `migrate_untagged`.
- Considered running `promote --all-ready` to auto-promote — rejected because promotion should be a deliberate human action.

## Testing

- 29/29 tests pass across `test_maintain.py`, `test_promote_parity.py`, `test_b2_promote_absolute_path.py`
- Key new tests: `test_promote_check_uses_repo_root_not_cwd`, `test_promote_check_excludes_non_ready_from_ready_count`

## Documentation

- Updated `Ontos_Manual.md` and `Ontos_Agent_Instructions.md` (8 → 9 tasks, ready count semantics)