---
id: project-ontos-v5-0-0-final-approval
deliverable_id: project-ontos-v5-0-0
role: final-approval
type: log
status: complete
original_status: withheld
deliverable_manifest_path: manifests/project-ontos-v5-0-0.yaml
halt_reason: "Current-head B.1 returned a genuine Request changes verdict with reproduced product blockers; strict and provider-limited verification both failed."
branch: codex/ontos-v5.0.0
event_type: review
source: codex
depends_on: [project-ontos-v5-0-0-spec]
concepts: [release, external-review, hardening]
---

# Ontos 5.0.0 final approval — WITHHELD

## Gate table

| # | Prerequisite | Result | Evidence class | Reproduction |
|---|--------------|--------|----------------|--------------|
| 1 | Product suite passes. | PASSED | test-pass | `PYTHONPATH=. python -m pytest -q` |
| 2 | Documentation validation is clean. | PASSED | command-exit-0 | `python -m ontos map --strict --scope docs` |
| 3 | Exact Claude route canary produces a verified artifact. | PASSED | direct-run | `scripts/llm-dev lint-artifact --family claude docs/reviews/project-ontos-v5-0-0/canary/claude-opus-canary-v2.md` plus complete canary dispatch verification |
| 4 | B.1 product head has no blocking verdict. | FAILED | direct-run | `docs/reviews/project-ontos-v5-0-0/B.1-claude-adversarial.md` |
| 5 | Strict-P3 lifecycle receipts verified. | FAILED | command-exit-nonzero | `scripts/llm-dev verify-lifecycle --mode strict-p3 manifests/project-ontos-v5-0-0.yaml` |
| 6 | Provider-limited fallback verified. | FAILED | command-exit-nonzero | `scripts/llm-dev verify-lifecycle --mode provider-limited-fallback manifests/project-ontos-v5-0-0.yaml` |

## Failure diagnosis

Row 4 fails on product correctness, not provider availability. The exact Claude
route recovered and produced a genuine B.1 `Request changes` verdict against
`5678e910ce11ed7a3546822cf3e34d50c5741681`. Independent reproduction confirms
that a successful exit can emit `result.exit_category: findings`; the graph
implementation also unconditionally casefolds paths despite the specification's
filesystem-sensitive identity requirement. The verdict records additional
major findings requiring triage before a new product head can enter review.

Rows 5 and 6 fail honestly after the halt. Two real B.1 receipts exist, but the
remaining tuples are absent. The v2.0.1 family verifier also rejects the genuine
GLM receipt because its wrapper recorded a worker-written artifact for an
attested OpenCode route while the verifier requires wrapper-captured output.

## Gate outcome

FAILED (first failing row: 4). D.6 is WITHHELD.

## Verdict

**WITHHELD.** The product suite and existing CI gates pass, but the current head
has now undergone genuine lifecycle review and did not clear B.1. The Claude
adversarial verdict requests changes with reproducible product blockers.
Strict-P3 exits 1 with 10 issues; provider-limited verification exits 1 with 11
issues. No missing seat, failed attestation, or fallback receipt has been
synthesized or waived.

Raw prompts, captures, route attestations, artifacts, results, and receipts are
isolated on `lifecycle-evidence/project-ontos-v5-0-0`; the product branch must
carry only the compact hash index and disposition.

## Recommendation

Hold the release. Fix and independently verify the B.1 product findings on a new
product head, correct the llm-dev wrapper/verifier mismatch without weakening
evidence, then restart the lifecycle from the head-dependent phases. Do not seek
a provider-limited governance waiver for a head with known product blockers.
This document grants no ready-for-review, merge, tag, release, PyPI,
issue-closure, or other maintainer action.
