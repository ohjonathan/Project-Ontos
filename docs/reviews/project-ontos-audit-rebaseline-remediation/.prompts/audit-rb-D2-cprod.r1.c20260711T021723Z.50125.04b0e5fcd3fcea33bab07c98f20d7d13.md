# D.2 independent Product implementation review

Read `.llm-dev/framework/templates/01-worker-session-contract.md`,
`02-phase-dispatch-handoff.md`, and `19-review-board-product.md` completely. You
are the independent Claude Product reviewer for
`project-ontos-audit-rebaseline-remediation`, phase `D.2`, in a separate
external session from the engineering peer seat.

Review spec v1.5 at
`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md` against exact
Phase C implementation I1 `05b090d53f7b0c9c4afdbb5fb23ab58cdfa01fa0`.
Inventory and exercise the user/operator-visible surfaces: activation version
failure and recovery, doctor skew reporting, log collision and archive-marker
warning flows, JSON/schema/exit semantics, read-only MCP behavior, exhaustive
type reporting, generated-map stability, and release provenance messaging.
Walk a golden path and representative recoverable failure paths using bounded
commands or temporary projects. Do not run the full suite. Do not read D.1,
B-family verdicts, D.2 siblings, dispatch results, receipts, or tracker
conclusions. Do not convert missing real Windows/TestPyPI runs into a product
failure when the UI honestly marks them external-pending.

Write only
`docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-strict-claude-product.md`.
Follow Template 19 with literal
`id: audit-rb-D2-cprod`,
`deliverable_id: project-ontos-audit-rebaseline-remediation`, `phase: D.2`,
`role: product`, `family: claude`, evidence labels actually used, and
`status: completed` or `halted`. Include all Phase-D product-surface sections
and exact unnumbered `## Verdict` with one bare canonical token first. A
blocking user-visible issue needs direct-run/orchestrator-preflight evidence
and an exact reproduction. Do not edit any other file, spawn nested agents, or
commit.
