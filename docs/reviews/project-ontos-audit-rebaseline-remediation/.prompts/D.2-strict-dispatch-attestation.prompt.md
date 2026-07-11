# Independent D.2 dispatch-integrity attestation

You are a fresh Gemini-family session, independent from the Codex
orchestrator. This is not a code review and not a lifecycle receipt. Confirm or
reject the orchestrator's `verify-family-dispatch --require-complete` output by
reading these repository files directly:

- `manifests/project-ontos-audit-rebaseline-remediation.yaml`
- `docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-strict-final-dispatch-intent.yaml`
- `docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-strict-final-dispatch-result.yaml`
- `docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-strict-family-verification.txt`

Use read-only inspection. If shell hashing is available, recompute SHA-256 of
the verification text; the orchestrator reports
`5a32a264a031dd32ac44a92ee92fba86b57b801c7046d8b62ea9b158d4822837`.
Independently check all four intended dispatch IDs, family/role/provider/CLI,
completed status, active result selection, artifact existence and declared
hash, evidence cap, and the OpenCode wrapper-promotion source constraint.
Confirm that no pending/failed active entry is being counted. Do not evaluate
the substantive verdicts.

Emit only one Markdown artifact beginning with YAML frontmatter. Use:

```yaml
---
id: audit-rb-D2-dispatch-attestation-gemini
type: review
status: completed
phase: D.2
role: dispatch-attestor
family: gemini
session_id: gemini-strict-d2-attestation-20260711
command_output_sha256: 5a32a264a031dd32ac44a92ee92fba86b57b801c7046d8b62ea9b158d4822837
---
```

Then an H1, a compact per-dispatch table, `## Mismatches`, and
`## Attestation`. The first nonblank line under `## Attestation` must be exactly
`Confirmed` or `Rejected`. If any check is unavailable or mismatched, use
`Rejected` and state the exact gap. Do not write files or include a code fence.
