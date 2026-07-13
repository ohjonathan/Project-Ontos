---
id: log_20260713_release-ontos-v5-0-0-and-close-audit-meta-cycle
type: log
status: active
event_type: release
source: codex
branch: codex/ontos-v5-release-closeout
created: '2026-07-13'
concepts: [release, workflow, testing, docs]
depends_on: [project_ontos_audit_remediation_release_line_tracker]
---

# Release Ontos v5.0.0 and close audit meta-cycle

## Goal

Release Ontos 5.0.0 through the repository's trusted-publisher workflow,
publish honest breaking-change and lifecycle provenance, close the shipped
#150–#157 program, and complete the July audit-remediation release meta-cycle
without erasing residual custody or fabricating lifecycle certification.

## Key Decisions

- Treated the maintainer's 2026-07-13 dispatch as the separate explicit
  authorization for ready, merge, tag, publish, release, and issue closeout.
- Used the consciously selected provider-limited governance waiver: current-head
  strict-P3 and provider-limited receipts did not complete, so D.6 remains
  WITHHELD and the release is not called llm-dev v2.0.1 certification.
- Tagged the reviewed merge commit rather than the feature head, and allowed
  only the tag-triggered OIDC workflow to publish. No hand-publish occurred.
- Recorded that the green TestPyPI smoke resolved 4.7.1 because it was unpinned;
  relied on independently matching TestPyPI/PyPI 5.0.0 hashes for the published
  artifact fact, and transferred workflow hardening to #148.
- Closed #150 and #156 only after transferring their remaining hygiene and
  repository-slimming tails to #148 and #149, respectively.
- Left epic #158 open as the post-v5 residual/control-plane tracker while
  closing the July release meta-cycle by explicit custody transfer.

## Alternatives Considered

- Hand-publishing after any workflow problem: rejected by the release dispatch;
  the workflow succeeded, so no manual path was attempted.
- Relabeling historical lifecycle receipts as current-head certification:
  rejected because those receipts are head-bound and D.6 is withheld.
- Closing #148/#149 or checking the missing control-plane registry row:
  rejected because those residuals remain real and explicitly tracked.
- Closing #150/#156 without preserving their unshipped tails: rejected in favor
  of linked custody-transfer comments before closure.

## Changes Made

- Marked PR #163 ready and merged it as
  `f8c148be0fbf2810cd94ce75fa69834a3e19166c`.
- Created and pushed annotated tag `v5.0.0` at that exact merge.
- Observed trusted-publisher run `29291879298` complete successfully and
  independently verified PyPI 5.0.0.
- Published the GitHub v5.0.0 release with breaking-change notes, tag-pinned
  migration guide, artifact hashes, and provider-limited provenance.
- Closed #150–#157 with issue-specific evidence; updated #148/#149 residual
  custody and epic #158.
- Completed the O4 release-line ledger with actual release evidence and the
  distinct `provider_limited_governance_waiver_released` outcome.

## Impacts

- Ontos 5.0.0 is publicly available from PyPI and GitHub Releases.
- Consumers have a public migration path for schema 4.0, exit behavior,
  physical link lines, CLI parsing, and MCP graph-stat changes.
- The July release meta-cycle is closed without conflating product shipment
  with lifecycle certification.
- #148, #149, and epic #158 retain the remaining TestPyPI, consolidation, and
  control-plane parity backlog.

## Testing

- PR #163 exact-head CI: all six jobs passed; 1,556 tests and 82.11% coverage.
- Tag workflow `29291879298`: tests, tag/version check, build, TestPyPI publish,
  TestPyPI smoke, and PyPI trusted publication all completed successfully.
- PyPI 5.0.0 wheel SHA-256:
  `c5ecdf6cc021b4f6f3cd05f4543d407713f392be7d44615a7903b17227738639`.
- PyPI 5.0.0 sdist SHA-256:
  `e673b98cb137e581cc2e48722b499a22ad972afe121038e1f6217a1d109fa800`.
- TestPyPI exposes the same two hashes.
- GitHub issue-state verification confirmed #150–#157 closed and #148/#149/#158
  open.
- `ontos link-check --no-orphans --quiet`: clean across 206 documents.
- `pre-commit run --all-files`: document graph and auto-consolidation hooks
  passed.
