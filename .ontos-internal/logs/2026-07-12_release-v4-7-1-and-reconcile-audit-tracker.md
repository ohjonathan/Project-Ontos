---
id: log_20260712_release-v4-7-1-and-reconcile-audit-tracker
type: log
status: active
event_type: release
source: codex
branch: release/v4.7.1-changelog
created: '2026-07-12'
---

# release v4.7.1 and reconcile audit tracker

## Summary

Released Ontos v4.7.1 from `main`, verified the tag-triggered PyPI workflow,
published the GitHub release, and reconciled the audit epic and O4 ledger.

## Goal

Ship the serializer and write-safety hotfix to users while preserving the
documented provider-limited review caveat and bringing GitHub/O4 tracking into
parity with the release outcome.

## Changes Made

- Dated the v4.7.1 changelog and pushed commit `0fa8309` to `main`.
- Created and pushed annotated tag `v4.7.1`; publish workflow `29215182087`
  completed successfully and published wheel and sdist artifacts to PyPI.
- Published the non-prerelease GitHub release.
- Closed #146 and #147 with merge `19868ad` and release evidence.
- Left #148 and #149 open on milestone `Audit Release N+1` (v4.8.0).
- Checked off #146/#147 and documented the v4.8.0 re-scope in epic #158.
- Reconciled the O4 ledger in commit `819c8a8`, including the authorized
  Template-07 release actions and the provider-limited outcome.

## Key Decisions

- Used a clean temporary worktree because the maintainer's active checkout had
  unrelated changes; no user work was modified.
- Tagged the changelog commit at `0fa8309`, then committed the post-release O4
  reconciliation separately so the tag reflects the exact published source.
- Closed #147 because no product sub-item remained unshipped; strict-P3 evidence
  remains an explicitly disclosed process caveat rather than a product residual.

## Alternatives Considered

- A tiny PR for the changelog was unnecessary because direct push to `main`
  succeeded and branch protection did not reject the authorized change.
- Manual `twine` publication was not used; the tag-triggered workflow was the
  only publication path.
- The dirty active checkout was not cleaned, reset, or reused for release work.

## Impacts

- PyPI and GitHub now expose Ontos v4.7.1 to users.
- Audit issues #146/#147 and epic #158 match the shipped state; #148/#149 remain
  visible as v4.8.0 work.
- The O4 ledger records `provider_limited_fallback_complete`, strict P3 not
  certified, and D.6 withheld without obscuring the maintainer's release choice.

## Testing

- GitHub Actions publish workflow `29215182087`: success, including tests,
  version/tag validation, build, TestPyPI publish and exact-artifact install,
  and final PyPI publish.
- PyPI JSON API reported version `4.7.1` with wheel and source distribution.
- GitHub release verified published, non-draft, and non-prerelease.
- Final issue-state checks: #146/#147 closed; #148/#149 open on
  `Audit Release N+1`; #158 open with reconciled checkboxes.
- Local `git diff --check` passed for both release-document commits. The
  pre-commit Ontos validator still reports the pre-existing 35 documentation
  findings present on the green release base; commits used the authorized
  release path with that known caveat recorded.
