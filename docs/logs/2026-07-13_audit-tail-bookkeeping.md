---
id: log_20260713_audit-tail-bookkeeping
type: log
status: active
event_type: chore
source: cli
branch: codex/audit-tail-bookkeeping
created: '2026-07-13'
concepts: [release, docs, workflow, testing]
---

# audit-tail-bookkeeping

## Goal

Correct the audit-remediation custody record before the #148/#149 implementation sweep,
without changing product code or claiming unresolved work complete.

## Key Decisions

- Returned the O4 ledger to `active` and bound its reconciliation to
  `main@3dd093e51e1125147e3533352abda75d7ae1d489`.
- Preserved the exact 8-addressed / 25-remaining arithmetic while tracking five inherited
  #150/#156 tails separately.
- Routed 24 patch-safe findings to v5.0.1 and the one breaking public-path removal to
  v6.0.0 after deprecation.
- Created #165 as the open owner of `R2-control-plane-parity-1`; #158 records custody
  transfer rather than implementation completion.
- Kept llm-dev strict lifecycle review pending for the public draft PR instead of
  fabricating external-family evidence.

## Alternatives Considered

- Leaving the ledger complete was rejected because #148/#149 and 25 findings remain open.
- Bundling the 11 legacy path removals into v5.0.1 was rejected as a breaking patch.
- Treating the control-plane transfer as a completed implementation was rejected; #165
  remains open.
- Editing the existing dirty checkout was rejected in favor of an isolated worktree.

## Impacts

- #148 now has six verified v5 findings checked; #149 has two.
- Both issues contain per-finding reproduction evidence and the A=7, B=9, C=4, D=4,
  E=1 implementation split.
- The authoritative #158 body no longer says the July meta-cycle is complete and points
  the control-plane row to #165; its newer correction comment supersedes the historical
  closeout comment.
- No runtime, test, workflow, package metadata, tag, release, or merge state changed.

## Testing

- `scripts/llm-dev doctor --manifest`: PASS.
- `scripts/llm-dev verify`: PASS, 4/4 manifest-conformance checks.
- llm-dev test, scope, and cardinality gate preflights: PASS with the declared
  `ONTOS_PYTHON` gate environment.
- Complete test gate: PASS, 1,556 tests.
- Ontos map/agent regeneration and link-check: PASS; 209 documents, clean graph.
- Ontos doctor: 10 passed, 0 failed, with only the pre-existing non-Ontos-hook and
  stale PATH-CLI warnings.
- Three subsequent diagnostic full-suite runs reproduced an existing order-dependent
  SQLite WAL snapshot failure in
  `test_read_only_portfolio_queries_existing_snapshot_without_mutation` (1,555 passed);
  the same test passes in isolation. No Phase 0 file is in its execution path, so the
  draft PR is not represented as merge-ready despite the earlier green complete run.
