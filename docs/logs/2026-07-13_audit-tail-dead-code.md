---
id: log_20260713_audit-tail-dead-code
type: log
status: active
event_type: chore
source: Codex
branch: codex/audit-tail-dead-code
created: '2026-07-13'
concepts: [cleanup, cli-surface, packaging, testing]
depends_on: [project_ontos_audit_tail_dead_code_spec]
---

# audit-tail-dead-code

## Goal

Resolve the nine patch-safe PR B dead-code findings from
`origin/main@d6eca479d5c5d71b2335e3ee2abad4f8d2651e3e` without deleting any
supported or re-exported import path. Preserve the breaking v2 path compatibility
surface for Ontos 5.x, add its v5.0.1 deprecation window, and leave release actions
and the actual removal to the maintainer-gated v6.0.0 PR.

## Key Decisions

- Applied the maintainer's public-surface rule to every target: package
  initializers, `__all__`, re-exports, supported documentation, and whole-tree
  consumers were checked before deletion.
- Corrected the original 12-name path audit count: `resolve_config` is live and
  supported, so the deferred compatibility surface is 11 names (`PROJECT_ROOT`
  plus ten callables).
- Kept all 11 path names importable. The ten functions warn only when called and
  name v6.0.0 plus a current replacement; `PROJECT_ROOT` creates no import-time
  warning.
- Treated the two command-layer core re-export shims as unsupported internal usage,
  per the program assumption, while retaining the canonical core modules.
- Kept bare `ontos export` routed through the registered deprecated Claude exporter
  and replaced the expired v3.4 promise with current `export claude`/`export data`
  guidance.
- Left package version metadata at 5.0.0 because tagging, version changes, and all
  release actions remain assigned to later maintainer-owned work.

## Alternatives Considered

- Deleting the 11 path names because they had zero internal call sites was rejected:
  ten are re-exported from `ontos` and `ontos.core`, and `PROJECT_ROOT` remains a
  direct public compatibility import.
- Emitting a warning when `PROJECT_ROOT` is imported was rejected because an
  import-time warning would affect every package import; its deprecation is instead
  documented for v6.0.0.
- Removing the canonical Obsidian/BOM behavior with its orphan module was rejected;
  useful BOM and leading-whitespace coverage now exercises `load_document`.
- Keeping package-data entries for deleted private packages was rejected because a
  source-only cleanup would leave stale distribution contents.

## Impacts

- Removed the private `_templates` and `_hooks` packages, obsolete Obsidian reader,
  internal command shims, dead export shadow, private directory helper, six
  zero-consumer helpers, and exactly 11 tracked backup files.
- Removed the matching package-data declarations, so wheel and sdist artifacts no
  longer ship the retired packages.
- Preserved useful loader, hook, initialization, export, and formatting coverage on
  canonical implementations.
- Updated the O4 ledger to record PR A's merged progress, PR B's review state, and
  the still-open v6 compatibility removal without changing the original 8/25
  reconciliation arithmetic.

## Testing

- Focused PR B regressions: 219 passed.
- Complete suite: 1,585 passed; the approved WAL/SHM flake did not reproduce.
- Wheel/sdist build and content inspection passed; a fresh non-editable wheel install
  with declared dependencies passed version, import-surface, export, and hook CLI
  smoke tests outside the checkout.
- The 11 compatibility names remain importable in source and installed-wheel tests;
  callable warning behavior and warning-free `PROJECT_ROOT` import are covered.
- `git diff --check`, compileall, llm-dev manifest/schema/review-seat checks, Ontos
  doctor/activation/link checks, final map regeneration, and CI are completed or
  recorded at the publication gate.
