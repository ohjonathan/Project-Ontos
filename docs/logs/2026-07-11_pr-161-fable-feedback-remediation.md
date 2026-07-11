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
- Coverage storage used the step-only `runner.temp` context at job scope, so
  GitHub rejected the workflow before creating jobs.
- Once jobs could run, exact help snapshots compared interpreter-controlled
  `argparse` presentation. Python 3.9-3.12 and 3.14 differ in usage wrapping,
  section labels, and repeated alias metavars despite equivalent CLI behavior.
- The advisory Codecov action downloads its uploader and checksum files into
  the checkout. A clean-tree assertion placed after that action misclassified
  the third-party download as a test-suite mutation.
- Context-map alias parity compared two independently generated timestamped
  maps byte-for-byte. A slow Python 3.12 coverage run crossed a one-second
  boundary and failed despite identical nonvolatile content.

## Fix Applied

- Preserve filename-derived IDs while validating explicit/added IDs.
- Accept only unindented `---` fences with optional trailing spaces/tabs.
- Apply process umask to new staged files and preserve existing-file modes.
- Keep invalid UTF-8 fail-closed with explicit tests and policy comments.
- Gate coverage at measured floors, ignore local coverage artifacts, and run
  local registry validation in CI; keep runner context usage step-scoped.
- Canonicalize only the known stdlib-controlled help presentation differences
  in golden assertions while retaining exact option order, names, descriptions,
  metavars, and command behavior.
- Use Codecov's documented `working-directory` input to keep its uploader and
  checksums under `runner.temp`, preserving the final clean-tree assertion.
- Compare context-map alias output with the generator's existing normalizer for
  its three declared volatile timestamp fields; retain exact comparison for all
  other bytes.
- Add a migration note and a complete PR-feedback disposition/status record.

## Key Decisions

- Retain schema-v4 link-check behavior and strict UTF-8 decoding; both changes
  are intentional contracts, not defects to revert.
- Defer legacy direct-writer symlink consolidation and validator decomposition
  to their existing remediation streams.
- Preserve D.5 as non-certified; after later maintainer authorization, run D.6
  only as a withheld gate if strict evidence remains inadmissible.

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
- Reviewed-head full suite: `1740 passed, 1 warning`; coverage `82.76%` (82% gate passed).
- Cross-version help parity: `11 passed` on Python 3.14 and Python 3.12.
- GitHub Actions run `29154665641`: discovery failure; Python 3.10 completed
  with `1737 passed, 2 failed`, and Python 3.9 also recorded the equivalent
  `scaffold` help presentation drift before fail-fast cancellation. Windows
  3.9/3.14 and non-editable smoke passed; the follow-up head rerun is pending.
- GitHub Actions run `29155102929`: ordinary suites passed on Python 3.9-3.12
  and the 3.11 coverage gate passed; its clean-tree step then found only the
  Codecov uploader and checksum downloads. The temp-directory follow-up is
  pending.
- GitHub Actions run `29155457389`: Python 3.9, 3.10, and 3.11 passed ordinary,
  coverage, and clean-tree checks; Python 3.12 ordinary passed, while coverage
  ended at `1739 passed, 1 failed` on a one-second-only context-map timestamp
  difference (`82.64%` coverage passed). The timestamp-normalized rerun is
  superseded by the green run below.
- GitHub Actions run `29155957357`: PASS, 7/7 jobs at exact head `388845c`;
  Linux 3.9–3.12, non-editable install, and Windows 3.9/3.14 all green; full
  suite `1740 passed`, coverage `82.76%`.
- Fresh D.5: Claude and GLM current-head artifacts/round-2 receipts landed;
  Gemini genuine retry failed exit `55` under the retired individual tier.
- Version metadata: `pyproject.toml` and `ontos.__version__` bumped to `4.7.1`;
  version/golden/release focused verification passes.
- Registry local and live GitHub parity: PASS.
- Manifest conformance: `4/4`; changed-path scope: PASS.
- Strict lifecycle: expected `review_pending`; receipt schema: expected
  D5-INFRA-2 failure; D.6: WITHHELD.
- Final status: `provider_limited_fallback_complete; strict P3 not certified; maintainer release actions deferred`.
