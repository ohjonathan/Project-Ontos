---
id: log_20260301_tiered-final-cleanup-and-merge
type: log
status: active
event_type: fix
source: cli
branch: v3.4_Tiered_context
created: 2026-03-01
---

# tiered-final-cleanup-and-merge

## Summary

Completed final cleanup for the `--compact tiered` PR before merge. The changes remove the last behavior drift in shared Tier 1 rendering, align full-map log ordering with the tiered renderer, tighten regression coverage, and update the v3.4 proposal text so the documented test scope matches the implementation.

## Root Cause

The branch was functionally merge-safe after the earlier review fixes, but two follow-up issues remained:

- the Tier 1 summary fallback treated every falsy summary as missing instead of only `None`/missing values
- the full-map timeline still used raw ID ordering while Tier 1 and tiered mode had moved to date-aware log ordering

That left small but avoidable consistency debt in the renderer and tests.

## Fix Applied

The cleanup made three targeted changes:

- narrowed the Tier 1 summary fallback so only missing or explicit `None` values become `No summary`
- updated the Tier 3 timeline to reuse `_log_date_sort_key()` so dated/undated logs are ordered consistently across the full map and tiered output
- added regressions for empty-string summary preservation and full-map date-aware timeline ordering, and updated the v3.4 proposal wording to reflect tiered coverage tests instead of the stale “6 tests” phrasing

## Testing

- `/Users/jonathanoh/Dev/Ontos-dev/.venv/bin/pytest -q -s tests/test_map_compact.py` (`20 passed`)
- `/Users/jonathanoh/Dev/Ontos-dev/.venv/bin/pytest -q -s` (`939 passed, 2 skipped`)

## Goal

Leave PR #79 with no known review debt before merge.

## Key Decisions

- Finish the work in a separate git worktree so unrelated untracked files in the main worktree remain untouched.
- Keep the fixes minimal and scoped to behavior already discussed in review rather than broadening the PR.

## Alternatives Considered

- Merge as-is and accept the small behavior drift.
- Defer the cleanup to a follow-up PR.

Both were rejected because the remaining issues were easy to fix safely in the same branch.

## Impacts

- `--compact tiered` and full-map log sections now agree on recent-log ordering.
- Explicit empty summaries are preserved instead of being rewritten.
- The PR history now includes a matching Ontos log entry for the final cleanup and merge step.
