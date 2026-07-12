---
id: project-ontos-v4-7-1-hotfix-final-approval
deliverable_id: project-ontos-v4-7-1-hotfix
role: final-approval
phase: D.6
status: withheld
deliverable_manifest_path: ../../../manifests/project-ontos-v4-7-1-hotfix.yaml
halt_reason: "Strict-P3 and provider-limited lifecycle verification both remain incomplete because external verifier receipts and framework-admissible fallback receipts are absent."
---

# Final-Approval Gate — Project Ontos v4.7.1 Hotfix

## Certification statement

not complete

## Gate table

| # | Prerequisite | Result | Evidence class | Reproduction |
|---|---|---|---|---|
| 1 | D.5 external-family dispatch bundle is complete. | FAILED | command-exit-nonzero | `bash .llm-dev/framework/scripts/verify-family-dispatch.sh --manifest manifests/project-ontos-v4-7-1-hotfix.yaml --intent docs/reviews/project-ontos-v4-7-1-hotfix/D.5-dispatch-intent.yaml --result docs/reviews/project-ontos-v4-7-1-hotfix/D.5-dispatch-result.yaml --adopter-root . --require-complete` |
| 2 | Strict-P3 lifecycle receipts verify. | FAILED | command-exit-nonzero | `scripts/llm-dev verify-lifecycle --mode strict-p3 manifests/project-ontos-v4-7-1-hotfix.yaml` |
| 3 | Provider-limited fallback receipts verify. | FAILED | command-exit-nonzero | `scripts/llm-dev verify-lifecycle --mode provider-limited-fallback manifests/project-ontos-v4-7-1-hotfix.yaml` |

## Failure diagnosis

- D.5 has zero completed external verifier artifacts and four failed dispatch rows.
- The wrapper cannot honestly generate fallback receipts from real stderr
  evidence because v2.0.1 requires the empty failed artifact path/hash to be
  the blockage evidence.
- Historical B.1 receipt/schema and route-redaction failures remain.
- The product implementation, focused regressions, full suite, contract
  parity, and scope checks are green; those results cannot replace receipts.

## Gate outcome

WITHHELD. No D.6 approval was run or granted.

## Release-action split

| Action | Performed in session? | Deferred to maintainer? | Evidence reference |
|---|---|---|---|
| Commit focused hotfix branch | yes | no | local branch history |
| Push focused hotfix branch | pending at artifact creation | no | task authorizes draft-PR publication only |
| Open draft pull request | pending at artifact creation | no | task authorizes a draft PR |
| Merge PR | no | yes | explicit maintainer authorization required |
| Tag / publish / release | no | yes | explicit maintainer authorization required |
| Close issues | no | yes | explicit maintainer authorization required |

## Recommended next action

Open the focused draft PR with this certification gap visible. A maintainer may
review the code and choose hold-versus-merge, but this artifact does not make
that choice and does not certify strict-P3.
