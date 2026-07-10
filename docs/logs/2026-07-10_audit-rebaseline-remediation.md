---
id: log_20260710_audit-rebaseline-remediation
type: log
status: active
event_type: refactor
source: codex
branch: codex/audit-rebaseline-remediation
created: '2026-07-10'
---

# audit-rebaseline-remediation

## Summary

Revalidated the Fable audit against current main, rebuilt the remediation
control plane, and implemented the verified hotfix/consolidation slices without
claiming lifecycle certification.

## Goal

Make the audit register mechanically trustworthy and remediate the live P0,
writer, activation, release-provenance, MCP read-only, graph/path, and CLI
contract defects that could be verified in this release line.

## Key Decisions

- Kept the 2026-07-02 audit immutable apart from a revalidation pointer.
- Made the 100-row registry authoritative and recorded shared-tree lease
  compliance as unproven rather than reconstructing receipts or scope proof.
- Used PyYAML semantic round trips for every discovered frontmatter writer.
- Anchored POSIX writes to no-follow directory descriptors and preserved failed
  rollback backups for recovery.
- Kept #147 `code_fixed_evidence_pending` after the fresh Gemini dispatch failed.

## Alternatives Considered

- Rejected treating the historical C+ grade or reviewer prose as a release gate.
- Rejected marking the shared integration branch scope-clean for individual
  deliverables.
- Rejected an sdist publication path that was not tied to the tested wheel hash.

## Impacts

- Serializer/log/mutation paths preserve semantic YAML values and line endings.
- Read-only MCP no longer creates graph exports, usage logs, portfolio config, or
  SQLite sidecars.
- Activation prefers the repository virtualenv when PATH is stale.
- Exit code/envelope schema 4.0, graph/path resolution, Windows locking, and
  publishing provenance now have regression coverage.

## Testing

- Full pytest suite plus clean-snapshot rerun.
- Registry validation in local and live-GitHub parity modes.
- `scripts/llm-dev doctor` and both manifest conformance checks.
- Lifecycle and per-deliverable scope gates executed and retained as expected
  release blockers.
- Wheel build/metadata/hash/import smoke and `git diff --check HEAD`.

## Lifecycle authorization and start — 2026-07-10

After the implementation snapshot and initial technical verification were
complete, the user gave the following explicit directive:

> Okay, run the full llm-dev lifecycle, until the D.5 and falsification review done. Go.

This directive is the auditable user gate for a new
`project-ontos-audit-rebaseline-remediation` branch-level integration
deliverable using `code-first-user-gated` sequencing. The immutable inputs are:

- base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`;
- implementation snapshot I0
  `b6f89d77e7fb684b8bd9a181a24c773d5777397a`;
- lifecycle branch `codex/audit-rebaseline-remediation-lifecycle`; and
- dedicated worktree
  `/tmp/project-ontos-worktrees/project-ontos-audit-rebaseline-remediation`.

Phase 0 began by freezing the integration boundary, route roster, exact scope,
and empty receipt inventory. The lifecycle runs every code-first phase through
D.5, including mandatory B.2, and then runs the framework's separate loose
falsification convention. Reproduced falsification findings return to D.4 and
require fresh D.5 verification.

This authorization does not clear the historical shared-tree lease blocker,
does not certify #146–#157 individually, and does not authorize D.6, Phase E,
merge, tag, publication, release, GitHub closure, or completion of registry rows
still recorded as open or partial. The two pre-existing user documents excluded
from I0 remain outside lifecycle scope and untouched.
