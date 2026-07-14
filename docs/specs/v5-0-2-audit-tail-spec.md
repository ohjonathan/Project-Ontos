---
id: v5_0_2_audit_tail_spec
type: spec
status: active
depends_on: [project_ontos_audit_remediation_release_line_tracker]
concepts: [testing, workflow, devops]
---

# Ontos v5.0.2 audit-tail patch

## Goal

Release a contract-preserving patch that absorbs the TestPyPI upload-to-Simple
API lag observed during v5.0.1 and completes #148's two inherited test-hygiene
rows.

## Required behavior

1. The TestPyPI wheel download polls at most 12 times with a 10-second delay.
2. Only an exact `ontos==<manifest version>` not-found response is retryable.
   Hash mismatches, other pip failures, and downloaded-wheel manifest mismatches
   fail immediately and continue to block production publication.
3. The unused `legacy` pytest marker is removed.
4. CLI help coverage recursively compares the parser tree with the declarative
   registry and renders help in-process. Existing golden help comparisons remain
   active. Subprocess coverage remains only where the process boundary matters.
5. Package and distribution metadata agree on 5.0.2, with a dated changelog.
6. The O4 ledger records the shipped v5.0.1 tag, SHA, PyPI release, closed sweep
   PRs, initial fail-safe block, and targeted failed-job recovery accurately.

## Non-goals

- Tagging or publishing v5.0.2.
- Closing #148 before release verification.
- Removing the deprecated v2 path names scheduled for v6.0.0.
- Claiming strict-P3 certification or completing transferred control-plane
  issue #165.

## Verification

- Focused release-artifact and CLI-help regression tests.
- Full pytest suite and non-editable distribution smoke test.
- Wheel/sdist build and metadata inspection.
- `git diff --check`, Ontos doctor/map validation, and llm-dev manifest checks.
