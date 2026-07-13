---
id: project-ontos-v5-0-0-final-approval
deliverable_id: project-ontos-v5-0-0
role: final-approval
type: log
status: complete
original_status: withheld
deliverable_manifest_path: manifests/project-ontos-v5-0-0.yaml
halt_reason: "Reviewed head 5678e91 failed B.1; remediated product head 751799c has no head-bound lifecycle receipts yet."
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
| 1 | Product suite passes. | PASSED | test-pass | `751799c`: 1,553 tests; 82.21% coverage |
| 2 | Documentation validation is clean. | PASSED | command-exit-0 | `751799c`: 202 documents; zero warnings/findings |
| 3 | Exact Claude route canary produces a verified artifact. | PASSED | direct-run | `scripts/llm-dev lint-artifact --family claude docs/reviews/project-ontos-v5-0-0/canary/claude-opus-canary-v2.md` plus complete canary dispatch verification |
| 4 | B.1 product head has no blocking verdict. | NOT RUN | head-bound review | Historical `Request changes` applies only to `5678e91`; `751799c` requires fresh dispatch |
| 5 | Strict-P3 lifecycle receipts verified. | NOT RUN | head-bound receipts | Existing receipts/index are bound to `5678e91` and earlier |
| 6 | Provider-limited fallback verified. | NOT RUN | head-bound receipts | No exception or fallback approval exists for `751799c` |

## Current disposition

The exact Claude route recovered and produced a genuine B.1 `Request changes`
verdict against `5678e910ce11ed7a3546822cf3e34d50c5741681`. Independent review
confirmed all 11 findings. Product head
`751799cce58602e1a910a813d9bd5cc5b981c7e8` remediates those findings and passes
the complete local product, documentation, package, and artifact gates.

That remediation does not convert the old verdict into approval. No B.1–D.6
receipt is currently bound to `751799c`, and the v2.0.1 wrapper/verifier mismatch
for the genuine GLM route remains unresolved. The historical strict and
provider-limited verifier failures are retained on the sibling evidence ref,
not repurposed as current-head evidence.

## Gate outcome

WITHHELD (first unmet row: 4). D.6 is WITHHELD.

## Verdict

**WITHHELD.** The remediated product head passes local gates but has not undergone
head-bound lifecycle review. The prior strict-P3 exit 1 with 10 issues and
provider-limited exit 1 with 11 issues describe the halted `5678e91` attempt;
they cannot certify `751799c`. No missing seat, approval, exception, or fallback
receipt has been synthesized or waived.

Raw prompts, captures, route attestations, artifacts, results, and receipts are
isolated on `lifecycle-evidence/project-ontos-v5-0-0`; the product branch must
carry only the compact hash index and disposition.

## Recommendation

Hold the release and keep the PR in draft. After CI passes on `751799c`, restart
the lifecycle from the head-dependent phases and correct the llm-dev
wrapper/verifier mismatch without weakening evidence. Only a genuine current-head
approval can re-adjudicate D.6. This document grants no ready-for-review, merge,
tag, release, PyPI, issue-closure, or other maintainer action.
