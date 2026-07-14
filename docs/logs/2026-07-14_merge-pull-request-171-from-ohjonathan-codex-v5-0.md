---
id: log_20260714_merge-pull-request-171-from-ohjonathan-codex-v5-0
type: log
status: active
event_type: v5-0-2-release
source: cli
branch: codex/release-v5.0.2
created: '2026-07-14'
concepts: [testing, workflow, devops]
---

# Ontos v5.0.2 release

## Goal

Release the authorized v5.0.2 audit-tail patch from exact green
`main@61fd4bc`, live-validate the bounded TestPyPI propagation gate, publish the
GitHub release, close #148, update #158, and reconcile the O4 ledger.

## Key Decisions

- Tagged only after the merge-triggered main workflow completed successfully.
- Treated every publish-gate failure as terminal; no manual twine upload or
  bypass path was used.
- Counted downloader attempts from the tagged workflow log rather than inferring
  from job duration.
- Kept the O4 ledger active because #149's intentionally breaking v6.0.0 path
  removal remains open.

## Alternatives Considered

- Tagging before the main workflow completed was rejected by the release
  pre-flight requirement.
- A manual publication path was excluded by the release guardrails.
- Closing epic #158 was rejected because #149 remains its sole original
  audit-tail item; transferred issue #165 also remains separately open.

## Impacts

- v5.0.2 is live on PyPI and GitHub from the exact annotated tag commit.
- The bounded TestPyPI downloader passed its first live tagged execution on
  attempt 1 of 12 with hash-locked exact-wheel verification.
- #148 is closed after both inherited test-hygiene findings shipped.
- #158 remains open for #149; provider-limited governance and D.6 withholding
  are unchanged.

## Testing

- Main workflow `29345911938`: success across Python 3.9–3.12, non-editable
  install, and v5 release gates.
- Publish workflow `29346309272`: tests, tag validation, immutable bundle,
  TestPyPI publish/verify/download/install/smoke, and PyPI publication passed.
- `download-testpypi-wheel`: succeeded on attempt 1 of 12.
- PyPI JSON reported 5.0.2; a clean external virtual environment installed
  `ontos==5.0.2`, imported from site-packages, and reported `ontos 5.0.2`.
