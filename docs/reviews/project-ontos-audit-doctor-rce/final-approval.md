---
id: project-ontos-audit-doctor-rce-final-approval
type: review
deliverable_id: project-ontos-audit-doctor-rce
role: final-approval
family: codex
status: complete
---

# Final-Approval Gate — project-ontos-audit-doctor-rce

## Gate Table

| # | Prerequisite | Result | Evidence class | Reproduction |
|---|--------------|--------|----------------|--------------|
| 1 | Doctor RCE regression passes. | PASSED | test-pass | `.venv/bin/python -m pytest tests/test_doctor_mcp_probe_regression.py -q` -> 2 passed |
| 2 | Full test suite. | FAILED | test-fail | `.venv/bin/python -m pytest tests/ -q` -> 1 failed, 1443 passed, 2 skipped |
| 3 | No whitespace errors. | PASSED | command-exit-0 | `git diff --check` |
| 4 | Manifest conformance. | PASSED | command-exit-0 | `scripts/llm-dev verify manifests/project-ontos-audit-doctor-rce.yaml` |
| 5 | Framework verify-all. | FAILED | test-fail | `bash .llm-dev/framework/scripts/verify-all.sh` -> fails `v1_10_0-agy-substrate-fixture.py` and `verify-d6-gate.sh(strict-p3-fixtures)` |
| 6 | B.3 verdict exists. | PASSED | file-exists | `docs/reviews/project-ontos-audit-doctor-rce/B.3-verdict.md` |
| 7 | D.3 verdict exists. | PASSED | file-exists | `docs/reviews/project-ontos-audit-doctor-rce/D.3-verdict.md` |
| 8 | D.5 verifier artifacts exist. | PASSED | count-eq | Three `D.5-*-verifier.md` artifacts exist under provider-limited fallback. |
| 9 | Release actions deferred. | PASSED | static-inspection | No commit, tag, push, PR, merge, release, or issue closure performed. |

## Failure Diagnosis

The full suite failure is `tests/commands/test_doctor_phase4.py::TestDoctorCommand::test_returns_exit_code_0_when_checks_pass`. The assertion expects 12 passed checks, but the current workspace activation graph reports one warning, so the result is 11 passed and 1 warning. This was observed before final closeout and is not caused by the RCE guard; the targeted regression passes.

The framework `verify-all` failure reproduces the same unrelated fixture failures observed before closeout: `v1_10_0-agy-substrate-fixture.py` refuses a framework-submodule artifact path under adopter-root containment, and `verify-d6-gate.sh(strict-p3-fixtures)` returns exit 2 for one strict-P3 fixture invocation expected to exit 0.

## Provider-Limited Caveat

Strict P3 is not certified. GPT-family dispatch was blocked by model access, and Jonathan authorized `provider-limited-review-exception` on 2026-07-03. Re-adjudicate GPT-family B.1, D.2, and D.5 when a working `gpt-*` model is available.

## Release-Action Split

| Action | Performed in session? | Deferred to maintainer? |
|--------|------------------------|--------------------------|
| `git commit` | no | yes — deferred to maintainer |
| `git tag` | no | yes — deferred to maintainer |
| `git push` | no | yes — deferred to maintainer |
| PR creation / merge | no | yes — deferred to maintainer |
| GitHub release | no | yes — deferred to maintainer |
| Issue closure (#147) | no | yes — deferred to maintainer |

## Decision

Provider-limited fallback complete with a failed full-suite gate caused by the existing activation-warning-count test. Maintainer release actions are deferred.
