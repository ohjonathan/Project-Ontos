---
id: project-ontos-audit-rebaseline-remediation-D.5-orchestrator-status
type: review
status: completed
depends_on:
  - project-ontos-audit-rebaseline-remediation-D.4-fix-summary
---

# D.5 orchestrator status — halted, not certified

Functional evidence is strong but strict D.5 is incomplete:

- Claude directly reproduced and closed all six I2 findings and produced a
  valid hash-bound `Request changes` verifier receipt.
- GLM independently reproduced the same pre/post results and ran the I2 suite
  at `1720 passed`, but its first receipt used an inadmissible OpenCode artifact
  source. A round-2 sibling-promotion attempt completed the checks but the
  wrapper refused promotion. No receipt was reconstructed.
- Gemini/AGY returned unrelated output or timed out; the direct Gemini CLI was
  unavailable for the account. No valid Gemini artifact or receipt exists.
- Loose falsification then found LF-ID-1 and LF-CP-1. They are fixed at I3, so
  the I2 verifier artifacts are not represented as verification of I3.

Two upstream framework defects independently prevent honest certification:

1. D4-INFRA-1: EH-15-A cannot resolve/register adopter-local regression tests
   and its manifest lookup can return a false success.
2. D5-INFRA-2: the v2.0.1 receipt schema rejects wrapper-emitted Product roles
   and `opencode_written_file_promoted`, while `verify-lifecycle` can still
   return complete because it does not apply the full receipt schema.

Repository outcome at I3: the five loose-falsification regressions pass,
registry validation passes, and the complete suite is `1725 passed, 1 warning`.
Lifecycle outcome: `review_pending`. D.6 was not run.

## Current-head retry — 2026-07-11

The maintainer authorized one genuine strict retry against exact product head
`388845c`, followed by the documented warning-only fallback if the pinned
framework still halted. Fresh dispatch IDs, prompts, result rows, artifacts,
raw captures, and receipts were used; no prior receipt was edited or recreated.

| Seat | Outcome | Evidence |
|---|---|---|
| Claude verifier | Completed after one wrapper-shape correction; `104` focused and `1740` full-suite tests passed; verdict `Request changes` on the two framework defects | `D.5-current-claude.md`; round-2 receipt and raw capture in `lifecycle-receipt-inventory-strict-final.yaml` |
| Gemini verifier | Genuine direct-provider invocation failed with exit `55`: the individual-client tier is no longer supported; no verdict or receipt | `D.5-current-dispatch-result.yaml`; wrapper-captured stderr SHA-256 `a679000b…e656` |
| GLM verifier | Direct checks passed (`104` focused; `1740` full); artifact and receipt landed after one wrapper-shape correction; verdict `Request changes` | `D.5-current-glm.md`; round-2 receipt, raw capture, and route-attestation sidecar |

Strict gates still fail. `verify-family-dispatch --require-complete` reports two
completed seats and the failed Gemini seat, plus v2.0.1 rejects the GLM
`worker_file` receipt/prompt. `verify-lifecycle --mode strict-p3` returns exit
`1`, `status=review_pending`; its GLM supersession backlink triggers the known
route-redaction defect. Applying the framework receipt schema independently
returns exit `1` with the same six producer/schema mismatches recorded before.
EH-15-A remains independently reproducible.

D.6 was therefore run only as a withheld gate at `final-approval.md`; no
passing rows, waiver, receipt reconstruction, merge, or release action exists.

Final status:

`provider_limited_fallback_complete; strict P3 not certified; maintainer release actions deferred`
