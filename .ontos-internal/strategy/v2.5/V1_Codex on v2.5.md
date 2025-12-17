# Review: Ontos v2.5 "Promises" Implementation Plan

## What this addresses (problem statement)
- Core problem is “users forget to consolidate logs”; proposed fix is mode-based consolidation with automated mode doing pre-commit consolidation, prompted mode reminding, advisory warning only.
- Goal is to uphold the “zero friction” promise by moving consolidation to pre-commit so changes land in the commit and avoid dirty working trees.

## Consistency and gaps in the plan
- Auto-staging scope risk (§5.3): `git add -u` will stage all tracked modifications, breaking partial commits. Constrain staging to Ontos-managed paths (decision_history, archive, moved logs) or use `git add --update <ontos paths>`.
- “Never blocks” not guaranteed (§5.3): only the final `return 0` ensures non-blocking; import/IO errors before main will fail the hook. Wrap top-level logic in try/except, log a short warning, and exit 0 to truly keep commits unblocked.
- Trigger/behavior mismatch (§5.3): hook fires on `log_count > LOG_RETENTION_COUNT` but consolidates by age (`--days` default 30). Many recent logs will trigger every commit yet never reduce count. Consider count-based consolidation (shrink until count <= threshold) or dual condition (count OR age).
- Pre-commit coexistence risk (§5.4): installing our hook overwrites existing pre-commit setups (e.g., pre-commit.com) even with backups. Offer chaining or an appendable snippet instead of replacement.
- Mode/default alignment: default remains `prompted`, so “forget to consolidate” is only solved in automated mode plus agent reminders. If teams skip “Activate Ontos” per session, consider a lightweight push-time nudge to avoid silent accumulation.
- Error visibility (§5.3): consolidation failure currently silent; users need a clear warning in commit output so they know to run maintenance manually.

## Extra considerations / potential improvements
- CI safety: optionally skip consolidation when `CI=true` (or similar) to avoid unexpected staging during release/build pipelines.
- Observability: emit a concise summary when consolidation runs (how many logs consolidated, paths touched) to build trust without noise.

## Open questions
- Should auto-consolidation be skipped in CI/automation contexts (e.g., `CI=true`) to avoid unexpected staging during release/build pipelines?
