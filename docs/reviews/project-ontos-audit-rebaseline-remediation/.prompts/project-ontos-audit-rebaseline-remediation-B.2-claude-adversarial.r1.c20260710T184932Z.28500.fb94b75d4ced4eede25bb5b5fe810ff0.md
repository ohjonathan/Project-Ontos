# B.2 adversarial dispatch

Read `.llm-dev/framework/templates/01-worker-session-contract.md`, `02-phase-dispatch-handoff.md`, and `05-review-board-adversarial.md` completely. You are the independent Claude adversarial reviewer for `project-ontos-audit-rebaseline-remediation`, phase `B.2`, with direct-run capability.

Blind-review only corrected `docs/specs/project-ontos-audit-rebaseline-remediation-spec.md` v1.1 and frozen diff `bf91b42...b6f89d7`. Do not read B.1 verdicts, approvals, or test summaries. Re-derive invariants and attack the new Phase C requirements, especially the symlinked log parent, malformed registry-row handling, invalid required-version copy, migration/public contracts, and whether tests can falsely pass. A blocker needs direct-run or orchestrator-preflight evidence plus a runnable reproduction.

Write only `docs/reviews/project-ontos-audit-rebaseline-remediation/B.2-claude-adversarial.md`; do not commit or edit elsewhere. Follow Template 05, literal frontmatter phase/role/family, H1, and exact unnumbered `## Verdict` with a bare canonical token.
