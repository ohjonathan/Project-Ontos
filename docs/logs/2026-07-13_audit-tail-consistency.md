---
id: log_20260713_audit-tail-consistency
type: log
status: active
event_type: fix
source: Codex
branch: codex/audit-tail-consistency
created: '2026-07-13'
concepts: [testing, docs, db]
depends_on: [project_ontos_audit_tail_consistency_spec]
---

# audit-tail-consistency

## Goal

Resolve `D1b-counts-1/2/3/4` from
`origin/main@f2ed48d8b935a486a1d09778efa345910400257b` by making sibling command
counts derive from shared validation, scan, and link-diagnostic paths without
adding warnings to the default clean repository. Retire the accepted portfolio
WAL/SHM flake deterministically and leave versioning and release actions to the
maintainer.

## Key Decisions

- Chose validation-on for concept vocabulary because map's existing
  authoritative check is established behavior. CLI activation/doctor, snapshot
  MCP activation, and MCP context-map now agree; link-only commands retain their
  reference-specific contract.
- Passed `max_dependency_depth` verbatim to snapshot and MCP map validation so
  zero is not replaced by a truthy default.
- Excluded the configured generated map once in `collect_scoped_documents` by
  resolved-path identity. Map keeps only its additional custom-output rule.
- Enabled body scanning in maintain's existing shared link-diagnostic call so a
  real broken body reference fails both maintain and `link-check`.
- Added vocabulary files to MCP cache freshness inputs after independent review
  found that a live vocabulary edit could otherwise split snapshot activation
  from MCP context-map counts.
- Wrapped every portfolio connection in deterministic transaction-and-close
  ownership, including setup exceptions; test teardown enforces test-local DBs
  and the absence of WAL/SHM sidecars.
- Routed activation map writes through the semantic no-op writer so
  timestamp-only regeneration does not rewrite the artifact.

## Alternatives Considered

- Removing vocabulary validation from map was rejected because it would regress
  the established concept validator instead of reconciling its siblings.
- Leaving snapshots vocabulary-free was rejected because MCP activation would
  remain a different full-validation surface.
- Adding generated-map exclusions independently to link-check, query, doctor,
  and MCP was rejected in favor of one scoped-document source of truth.
- Keeping maintain frontmatter-only and merely relabeling its metric was rejected
  by the current dispatch: a real body reference must surface rather than be
  described away.
- Calling `gc.collect()` or rerunning the flaky order was rejected because it
  masks unclosed SQLite connections instead of fixing their lifetime.

## Impacts

- Default docs-scope activation remains zero-error/zero-warning. Non-default
  library scope deliberately gains the 874 vocabulary warnings map already
  reported, making the full validators consistent rather than silently clean.
- Generated context maps no longer inflate document/orphan counts in any scoped
  consumer, including cache freshness and portfolio scans.
- Portfolio reads and writes preserve the same commit/rollback semantics while
  releasing SQLite resources deterministically.
- O4 now records PR B merged at `f2ed48d`, 24/33 findings landed on `main`, and
  PR C's four findings implemented for review. Package metadata remains 5.0.0.

## Testing

- Focused PR C suite: 229 passed.
- Complete suite: 1,600 passed; no WAL/SHM exemption.
- Resource-warning order gate: forward, reverse, and isolated target orders each
  passed three consecutive runs with `ResourceWarning` and unraisable SQLite
  warnings promoted to errors; independent review also ran five forward and five
  reverse repetitions.
- Exact doctor 12-check tripwire and clean activation-health regression passed.
- llm-dev manifest/schema/P3/gate-category/artifact checks passed.
- Ontos map/activation/doctor/link checks, `git diff --check`, compileall, branch
  scope, and CI are completed or recorded at the publication gate.
