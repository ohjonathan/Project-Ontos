---
id: log_20260209_make-critical-paths-config-driven
type: log
status: active
event_type: v3-2-1b-critical-paths
source: cli
branch: fix/critical-paths-config
created: 2026-02-09
---

# Make critical paths config-driven

## Summary

Implemented v3.2.1b config-driven Critical Paths output and added coverage for user vs
contributor mode and custom logs_dir.

## Goal

Replace hardcoded Critical Paths with config-driven paths and contributor-only strategy
output, without breaking Tier 1 Key Documents.

## Key Decisions

- Added docs_dir/logs_dir/is_contributor_mode to map generation config.
- Always include Critical Paths (small, Tier 1-safe) and mark missing paths explicitly.
- Kept Key Documents unchanged and appended Critical Paths after it.

## Alternatives Considered

- Omitting Critical Paths when paths are missing (rejected: less informative).
- Showing .ontos-internal/strategy/ in all modes (rejected: user-mode leakage).

## Changes Made

- Added config-driven Critical Paths section in Tier 1.
- Passed docs_dir/logs_dir/is_contributor_mode into map generation.
- Added tests for user mode, contributor mode, and custom logs_dir.

## Impacts

- `ontos/commands/map.py`
- `tests/commands/test_map.py`

## Testing

- Not run (not requested).
