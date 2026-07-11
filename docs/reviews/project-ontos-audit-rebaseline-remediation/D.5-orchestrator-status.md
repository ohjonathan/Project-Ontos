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
