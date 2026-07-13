---
id: project-ontos-v5-0-0-final-approval
deliverable_id: project-ontos-v5-0-0
role: final-approval
type: log
status: complete
original_status: withheld
deliverable_manifest_path: manifests/project-ontos-v5-0-0.yaml
halt_reason: "Claude independently verified the remediated PR head bce26f5, but the current-head lifecycle canary was denied before provider invocation and produced no receipt."
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
| 1 | Product suite passes. | PASSED | test-pass | `bce26f5`: all six CI jobs green; 1,553 tests and 82.21% coverage locally |
| 2 | Documentation validation is clean. | PASSED | command-exit-0 | 203 documents after this disposition log; zero warnings/findings |
| 3 | Current-head exact Claude route canary produces a verified artifact. | BLOCKED | orchestrator-preflight | Exact executable/version and byte identity passed preflight; execution policy denied the `bypassPermissions` launch before process creation, so no current-head artifact or receipt exists |
| 4 | B.1 product head has no blocking verdict. | NOT RUN | head-bound review | Historical `Request changes` applies only to `5678e91`; no lifecycle board ran against `bce26f5` |
| 5 | Strict-P3 lifecycle receipts verified. | NOT RUN | head-bound receipts | Existing lifecycle receipts are bound to `5678e91` and earlier |
| 6 | Provider-limited fallback verified. | NOT RUN | head-bound receipts | No exception or fallback approval exists for `bce26f5` |

## Current disposition

The exact Claude route recovered earlier and produced a genuine B.1
`Request changes` verdict against
`5678e910ce11ed7a3546822cf3e34d50c5741681`. Product-code commit
`751799cce58602e1a910a813d9bd5cc5b981c7e8` remediates all 11 findings. At PR
head `bce26f53349ad61073fff7aa4bf932bad98d982b`, owner comment
`issuecomment-4960736071` independently reproduced every fix and reported no
regressions; all six CI jobs are green. That top-level comment is out-of-band
product verification, not a submitted `APPROVE` review or a lifecycle receipt.

That remediation and independent verification do not convert the old verdict
into lifecycle approval. A current-head canary preflight matched the proven
Claude executable, realpath, and version and confirmed byte-identical product
surfaces. The required `bypassPermissions` launch was then denied by execution
policy before process creation because of external data-egress risk. No provider
call, worker artifact, dispatch result, or receipt was produced, so strict-P3
was not started. The historical strict and provider-limited verifier failures
remain on the sibling evidence ref and are not repurposed as current-head
evidence.

## Gate outcome

WITHHELD (first unmet row: 3). D.6 is WITHHELD.

## Verdict

**WITHHELD.** The remediated PR head passes product gates and independent
reproduction, but has not undergone head-bound lifecycle review. The prior
strict-P3 exit 1 with 10 issues and provider-limited exit 1 with 11 issues
describe the halted `5678e91` attempt; they cannot certify `bce26f5`. No missing
artifact, seat, approval, exception, or fallback receipt has been synthesized
or waived.

Raw prompts, captures, route attestations, artifacts, results, and receipts are
isolated on `lifecycle-evidence/project-ontos-v5-0-0`; the product branch must
carry only the compact hash index and disposition.

## Recommendation

Hold the release and keep the PR in draft. CI has passed; lifecycle remains the
only gate. A retry of the exact Claude canary requires explicit authorization
after disclosure of its external data-egress risk. If that canary produces and
verifies a genuine artifact, restart the head-dependent lifecycle phases and
correct the llm-dev wrapper/verifier mismatch without weakening evidence. Only
genuine current-head receipts can re-adjudicate D.6. This document grants no
ready-for-review, merge, tag, release, PyPI, issue-closure, or other maintainer
action.
