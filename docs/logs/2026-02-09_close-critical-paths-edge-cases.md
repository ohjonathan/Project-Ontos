---
id: log_20260209_close-critical-paths-edge-cases
type: log
status: active
event_type: chore
source: cli
branch: fix/critical-paths-config
created: 2026-02-09
---

# Close critical paths edge cases

## Summary

Closed remaining Critical Paths hardening gaps and expanded tests for edge cases.

## Goal

Eliminate remaining Critical Paths edge-case risk and lock behavior with tests.

## Key Decisions

- Added null-byte hardening around `Path(raw)` to avoid ValueError crashes.
- Expanded edge-case tests (unset values, root_path=None, absolute/traversal).
- Tightened missing-annotation assertion to the specific line.

## Alternatives Considered

- Leaving null-byte handling unguarded (rejected: avoidable crash risk).
- Collapsing edge-case tests into a single test (rejected: less diagnostic).

## Changes Made

- Hardened `_format_critical_path` against invalid raw path values.
- Added tests for unset inputs and root_path=None formatting.
- Split absolute vs traversal tests; refined missing annotation assertion.

## Impacts

- `ontos/commands/map.py`
- `tests/commands/test_map.py`

## Testing

- `pytest tests/commands/test_map.py tests/commands/test_map_tier1_key_documents.py`
