---
id: log_20260714_date-v5-0-1-changelog
type: log
status: active
event_type: v5-0-2-audit-tail
source: cli
branch: codex/v5.0.2-audit-tail
created: '2026-07-14'
concepts: [testing, workflow, devops]
---

# Ontos v5.0.2 audit-tail patch

## Goal

Finalize the O4 ledger for the shipped v5.0.1 release and prepare v5.0.2 with
bounded TestPyPI propagation polling plus #148's two inherited test-hygiene
fixes.

## Key Decisions

- Retry only pip output that reports the exact manifest version unavailable.
  Hash mismatches, unrelated pip failures, and manifest mismatches fail on the
  first attempt.
- Keep a 12-attempt, 10-second bound matching the existing TestPyPI metadata
  poll.
- Replace duplicated help subprocesses with recursive parser/registry and
  in-process golden assertions, retaining only genuine process boundaries.
- Record v5.0.1's initial fail-safe block and targeted failed-job recovery as a
  provenance-gate success, without upgrading provider-limited certification.

## Alternatives Considered

- A blanket shell retry loop was rejected because it could retry hash failures.
- Retrying the full publish workflow was rejected because TestPyPI 5.0.1 was
  already occupied; the recorded recovery correctly reran only failed jobs.
- Keeping per-command subprocess help checks was rejected because the command
  registry and parser tree can cover the same contract faster and more fully.

## Impacts

- v5.0.2 remains contract-preserving and leaves the v6 path-removal surface
  untouched.
- #148 can close only after v5.0.2 is released and verified.
- #149 remains open for `D5b-dead-code-3`; #165 remains transferred and outside
  the 33-finding arithmetic.

## Testing

- Focused release-artifact, CLI-help, and version tests: 24 passed.
- Converted CLI and command regression set: 177 passed.
- Full suite: 1,568 passed with six existing deprecation warnings.
- Wheel/sdist manifest verification and fresh non-editable install smoke passed
  for 5.0.2.
