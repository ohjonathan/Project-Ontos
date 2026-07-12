---
id: project-ontos-v4-7-1-hotfix-D.5-orchestrator-status
deliverable_id: project-ontos-v4-7-1-hotfix
phase: D.5
role: orchestrator-status
family: codex
provider_limited_fallback: true
strict_p3_certified: false
canonical_p3_evidence: false
status: completed
lifecycle_outcome: completed-with-provider-gap
---

# D.5 Orchestrator Status — Project Ontos v4.7.1 Hotfix

This is a dispatch/falsification status artifact, not a verifier verdict or a
receipt. It does not substitute Codex evidence for any external family.

## Implementation under verification

- Pre-fix: `a71ac4a0d55ad86b8f9051f9c339bd1397ff4751`
- Final product-fix code reviewed at D.5: `a0062ae8b6e8413f15e64259ec16d1c927d55328`
- Final branch verification ref: `ef869f7e805b691fc614e7017c16438e2d33de0a`
- Lifecycle-only head at dispatch: `98d765cd339a2ce9cdf3ec98798e385a25318456`
- D.4 blockers: `D1-FM-QUOTED-KEY-BOUNDARY`,
  `D1-PORTFOLIO-WAL-SNAPSHOT`

## External verifier dispatches

| Dispatch | Family | Outcome | Admissible artifact / receipt |
|---|---|---|---|
| `ontos-471-D5-cv` | Claude | Exceeded the bounded run; wrapper recorded `status: failed` and no artifact. | none |
| `ontos-471-D5-gv` | Gemini | Headless workspace-trust prerequisite blocked provider execution. | none |
| `ontos-471-D5-gv-r2` | Gemini | After the trust prerequisite was satisfied, the provider rejected the retired individual client with `IneligibleTierError` / `UNSUPPORTED_CLIENT`. | none |
| `ontos-471-D5-glv` | GLM via OpenCode/Neuralwatt | Route reached the model but rejected required repository commands; wrapper recorded failed/no artifact and `auth-401-403`. | none |

`verify-family-dispatch.sh --require-complete` reports 0 completed and 4
pending, with four `result.status=failed` violations. The final receipt
inventory remains empty. No receipt was reconstructed from raw output.

## Falsification results

| Claim | Pre-fix falsification | Post-fix result |
|---|---|---|
| Quoted target keys can append duplicates; a quoted non-target boundary can be deleted. | Reproduced directly against `a71ac4a`, including field deletion. | Five core/consumer regressions pass; complete mapping equality now fails closed for unsupported key syntax. |
| A passive per-workspace checkpoint can strand committed rows in WAL while an immutable reader sees the old main DB. | Reproduced directly with a held WAL reader: immutable reader saw the old row set while plain read-only saw the new rows. | Concurrent-reader regression passes; rebuild blocks for `TRUNCATE`, inspects SQLITE_BUSY, and publishes a zero-length/absent WAL before returning. |
| D.4 fixes regress the repository. | Not applicable. | Focused set: 82 passed. Full suite: 1572 passed, 2 skipped, 2 warnings; exact pre/post porcelain snapshots matched. |
| Patch accidentally imports v5 contracts. | Compared to `bf91b42`. | Envelope remains schema 3.4/eight keys/no `result`; forbidden v5 sources and tracked goldens are unchanged; version is 4.7.1. |

Residual risk: SQLite `immutable=1` assumes the fixed-path database is not
modified during a query. The truncating checkpoint fixes the demonstrated
persistent-WAL staleness bug, but an actually versioned immutable snapshot is
the stronger follow-up design.

## Framework gate results

| Gate | Exact result |
|---|---|
| Manifest conformance | PASS, 4/4 |
| Re-adjudication queue | PASS, 3 open items |
| D.5 family dispatch completeness | FAIL, 4 violations / 0 completed |
| Strict lifecycle | FAIL, 12 issues; `status=review_pending` |
| Provider-limited lifecycle | FAIL, 12 issues; `status=provider_limited_fallback_incomplete` |
| Primary receipt inventory schema | FAIL: wrapper-emitted Product role is forbidden by the v2.0.1 receipt schema |
| Final receipt inventory schema | FAIL: empty `receipts` is forbidden |
| EH-15-A fix-summary verifier | FAIL: adopter paths are incorrectly resolved under the framework checkout |
| Fallback receipt generator | FAIL: requires the failed empty artifact path to equal the real stderr blockage-evidence path |

The remaining failures are framework evidence/tooling failures, not product
test failures. They are also a reproduction signal for llm-dev-framework issue
#214. Pointing fallback evidence at an empty artifact, filtering the Product
receipt, editing the GLM hash-bound artifact, or hand-writing receipts would
make the mechanics greener by making the evidence false; none was done.

After the external D.5 attempts, the withheld framework artifact exposed an
existing non-hermetic aggregate doctor test: it called live activation and
user-level Cursor checks while asserting an exact pass count. Commit `ef869f7`
mocks those two checks inside the aggregate unit tests. It changes no product
code or command contract; 8 focused doctor/security tests pass. No external
receipt is claimed for this post-D.5 test-harness correction.

## Status

Maintainer-directed process label:

`provider_limited_fallback_complete; strict P3 not certified; maintainer release actions deferred`

Framework verifier output remains
`status=provider_limited_fallback_incomplete`. The first string records that
the authorized fallback path and genuine retry are complete; it is not a claim
that v2.0.1 mechanically certified the lifecycle. D.6 is withheld.
