---
id: log_20260713_pr-163-rename-staging-sweep-liveness-fix
type: log
status: active
event_type: fix
source: codex
branch: codex/ontos-v5.0.0
created: '2026-07-13'
depends_on: [project-ontos-v5-0-0-spec]
concepts: [cli, hardening, testing]
---

# PR 163 rename staging sweep liveness fix

## Goal

Prevent token-matched non-regular staging artifacts or unlink races from
stranding a valid rename journal after document bytes have been restored.

## Key Decisions

- Kept invalid staging tokens fatal while making all staging-sweep filesystem
  operations best-effort.
- Skipped symlinks and directories without removing them, swallowed
  `FileNotFoundError` races, and logged other `OSError` failures without
  propagating them.
- Kept journal unlink and journal-directory fsync authoritative; only the
  ancillary staging cleanup changed behavior.
- Used the shared cleanup boundary so recovery and successful completion have
  the same liveness guarantee.

## Alternatives Considered

Moving cleanup after journal deletion would also prevent this specific brick,
but a best-effort helper preserves the existing cleanup order and gives both
callers the same explicit contract.

## Impacts

Interrupted renames now restore original bytes, clear the recovery journal,
and allow a subsequent CLI or MCP rename even when a persistent symlink or
directory occupies a token-matched staging name. The skipped entry remains
untouched. No lifecycle evidence or release state changed.

## Testing

- Focused transaction and rename command suites: 56 passed.
- Full repository suite: 1,556 passed, one pre-existing deprecation warning.
- Regressions cover symlink and directory staging entries, `complete()`, a
  deterministic `FileNotFoundError` race, byte restoration, journal removal,
  and a subsequent real `rename --apply`.
- `git diff --check`: clean.

## Testing
