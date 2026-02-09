---
id: log_20260207_improve-hidden-command-handling-add-warn-legacy
type: log
status: active
event_type: chore
source: cli
branch: v3.2.1-external-review-remediation
created: 2026-02-07
---

# improve hidden command handling + add warn_legacy 

## Summary

Improved hidden command handling and added `warn_legacy` support in config resolution to surface legacy settings more clearly.

## Changes Made

- Hardened hidden-command handling so suppressed commands don't leak in user-facing help flows.
- Added `warn_legacy` support to `resolve_config` usage to surface legacy-config warnings where appropriate.

## Goal

Reduce user confusion from hidden command exposure and make legacy configuration usage visible.

## Key Decisions

- Prefer warning users about legacy configuration rather than silently accepting it.
- Keep hidden commands truly hidden in help/UX paths.

## Alternatives Considered

- Leave hidden command handling unchanged (rejected: continued UX confusion).
- Suppress all legacy warnings globally (rejected: hides important upgrade signals).

## Impacts

- Cleaner CLI help output with fewer unexpected hidden commands.
- Better visibility into legacy configuration usage.

## Testing

- Not recorded for this log.
