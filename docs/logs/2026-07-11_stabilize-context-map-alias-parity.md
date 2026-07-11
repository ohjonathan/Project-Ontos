---
id: log_20260711_stabilize-context-map-alias-parity
type: log
status: active
event_type: pr-161-lifecycle-fallback-closeout
source: cli
branch: codex/audit-rebaseline-remediation-lifecycle
created: '2026-07-11'
---

# PR #161 lifecycle fallback closeout

## Summary

Retried the complete three-family D.5 board against exact product head
`388845c`, preserved the genuine provider and wrapper evidence, applied the
maintainer-requested `4.7.1` version bump, and executed D.6 as an honest
withheld gate.

## Goal

Reach strict-P3 if and only if fresh current-head receipts and the pinned
framework gates are mechanically admissible; otherwise close on the exact
maintainer-authorized warning-only fallback without merging or releasing.

## Changes Made

- Added a current-head D.4 addendum and fresh D.5 dispatch bundle.
- Landed valid current-head Claude and GLM verifier artifacts/round-2 receipts;
  preserved Gemini exit-55 provider-policy evidence.
- Declared the formal provider-limited exception and blocking re-adjudication
  queue in the manifest.
- Authored a withheld D.6 artifact; no passing gate rows or release authority.
- Bumped both package version sources to `4.7.1`, updated version-sensitive
  goldens, and ignored parallel `.coverage.*` artifacts.
- Recorded the split-before-merge recommendation and whole-PR revert boundary.

## Key Decisions

- Treated `verify-lifecycle` as insufficient for strict certification while its
  own receipt schema rejects wrapper-emitted values.
- Stopped after one genuine Gemini retry and one evidence-based Claude/GLM
  artifact-shape correction; no blind retries or cross-family relabeling.
- Did not mutate, reconstruct, or fabricate historical receipt rows.
- Kept the PR draft and deferred merge, tag, publish, release, and issue closure.

## Alternatives Considered

- A full receipt-inventory rollover was rejected because it would require fresh
  B.1/B.2/D.2 dispatches and cannot be achieved by copying old receipts.
- Hand-restamping the schema-v1 inventory or deleting supersession metadata was
  rejected as receipt mutation.
- A passing D.6 was rejected because strict and formal fallback lifecycle gates
  both remain nonzero.

## Impacts

Product head `388845c` has independent current-head verification and green CI.
The branch advertises `4.7.1`, but the lifecycle remains warning-only and the
recommended release path is an extracted v4.7.1 hotfix slice with fresh review.

## Testing

- GitHub Actions `29155957357`: 7/7 green at `388845c`; `1740 passed`,
  coverage `82.76%`.
- Current-head Claude/GLM: `104` focused and `1740` complete tests passed.
- Post-bump focused version/golden/release checks: `7 passed`; portfolio
  read-only race did not reproduce in five isolated reruns.
- Post-bump complete suite: `1740 passed, 1 warning` in `122.68s`.
- Manifest conformance: 4/4; re-adjudication queue: PASS; D.6 withheld shape:
  PASS under `--allow-gated` and expected failure under `--strict-p3`.
- Strict lifecycle: exit 1, `review_pending`; provider-limited lifecycle:
  exit 1, `provider_limited_fallback_incomplete`; receipt schema: exit 1 with
  six pinned-framework producer/schema mismatches.

Final status: `provider_limited_fallback_complete; strict P3 not certified; maintainer release actions deferred`.
