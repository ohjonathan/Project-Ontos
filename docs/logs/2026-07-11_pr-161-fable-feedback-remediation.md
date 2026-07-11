---
id: log_20260711_pr-161-fable-feedback-remediation
type: log
status: active
event_type: fix
source: codex
branch: codex/audit-rebaseline-remediation-lifecycle
created: '2026-07-11'
---

# PR 161 Fable feedback remediation

## Summary

Pressure-tested every claim in Claude Fable 5's PR #161 review against exact
head `601591b`, fixed the confirmed in-scope defects, and recorded the complete
claim disposition without changing lifecycle receipts or certification state.

## Goal

Make PR #161 safer and more reviewable while preserving its draft,
`review_pending` boundary and the documented D.4/D.5 framework blockers.

## Root Cause

- The shared frontmatter editor assumed every document declared an explicit ID.
- The consolidated splitter narrowed the historical whitespace-fence contract.
- The secure staging path overrode umask-derived modes for new files.
- Local coverage outputs were not ignored, coverage was advisory, and the audit
  registry validator was absent from CI.

## Fix Applied

- Preserve filename-derived IDs while validating explicit/added IDs.
- Accept only unindented `---` fences with optional trailing spaces/tabs.
- Apply process umask to new staged files and preserve existing-file modes.
- Keep invalid UTF-8 fail-closed with explicit tests and policy comments.
- Gate coverage at measured floors, ignore local coverage artifacts, and run
  local registry validation in CI.
- Add a migration note and a complete PR-feedback disposition/status record.

## Key Decisions

- Retain schema-v4 link-check behavior and strict UTF-8 decoding; both changes
  are intentional contracts, not defects to revert.
- Defer legacy direct-writer symlink consolidation and validator decomposition
  to their existing remediation streams.
- Keep D.5 `review_pending`; do not run D.6 or fabricate/waive evidence.

## Alternatives Considered

- Restoring lossy UTF-8 replacement was rejected because corrupt content could
  be written back silently.
- A global legacy-writer refactor and PR split were rejected as out of scope and
  snapshot-invalidating for this follow-up.

## Impacts

ID-less documents can be patched safely, frontmatter compatibility is restored,
restrictive umasks remain restrictive, and CI now fails on coverage or registry
drift. Existing public schema-v4 semantics and lifecycle evidence remain intact.

## Testing

- Focused integration: `123 passed`.
- Full suite: `1739 passed, 1 warning`; coverage `82.76%` (82% gate passed).
- Registry local and live GitHub parity: PASS.
- Manifest conformance: `4/4`; changed-path scope: PASS.
- Strict lifecycle: expected `review_pending`; receipt schema: expected
  D5-INFRA-2 failure.
