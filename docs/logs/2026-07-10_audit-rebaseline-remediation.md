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
