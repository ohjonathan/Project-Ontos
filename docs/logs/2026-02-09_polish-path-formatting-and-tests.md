---
id: log_20260209_polish-path-formatting-and-tests
type: log
status: active
event_type: pr-62-key-documents-paths
source: cli
branch: fix/key-documents-spec
created: 2026-02-09
---

# Polish path formatting and tests

## Summary

Aligned Key Documents output to the spec, prevented absolute path leakage in the context map,
and added coverage for path formatting edge cases.

## Goal

Ship the Key Documents formatting fixes without leaking absolute paths, and lock behavior
down with targeted tests.

## Key Decisions

- Centralized path formatting in `_format_rel_path` and used it for Tier 1 + Tier 2.
- Ensured all fallbacks avoid absolute paths; filename-only is the final fallback.
- Added `(path unknown)` when a Key Documents entry has no path.

## Alternatives Considered

- Leaving Tier 2 paths absolute (rejected: leaks user paths).
- Returning absolute paths when outside root (rejected: leakage risk).
- Keeping blank path for missing docs (rejected: ugly output).

## Changes Made

- Implemented safe relative path formatting with `.as_posix()` output.
- Applied relative path formatting to Tier 2 document table.
- Added branch coverage tests for `_format_rel_path`.
- Added leakage tests for Tier 1 + Tier 2.

## Impacts

- `ontos/commands/map.py`
- `tests/commands/test_map_tier1_key_documents.py`

## Testing

- Not run (not requested).
