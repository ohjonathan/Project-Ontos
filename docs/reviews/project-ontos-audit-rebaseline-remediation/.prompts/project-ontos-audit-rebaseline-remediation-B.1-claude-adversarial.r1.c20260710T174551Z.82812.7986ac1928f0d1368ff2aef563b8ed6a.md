# B.1 adversarial dispatch

Work in the current repository. Read `.llm-dev/framework/templates/01-worker-session-contract.md`, `02-phase-dispatch-handoff.md`, and `05-review-board-adversarial.md` completely and obey them as the session contract.

You are the Claude adversarial reviewer for `project-ontos-audit-rebaseline-remediation`, phase `B.1`. This is a Codex-authored code-first deliverable; you are independent and have direct-run capability. Review only:

- `docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`
- the implementation diff `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95...b6f89d77e7fb684b8bd9a181a24c773d5777397a`
- operational identity: branch `codex/audit-rebaseline-remediation-lifecycle`, I0 `b6f89d7...`, output path below.

Do not consult other reviewer verdicts, approvals, green-result summaries, or the orchestrator's conclusions. Re-derive invariants. Attack fail-closed behavior, negative controls, writer security, serializer inputs, version skew, release provenance, scope/status parity, and overclaiming. A blocker needs direct-run or orchestrator-preflight evidence and a runnable reproduction.

Write exactly one artifact: `docs/reviews/project-ontos-audit-rebaseline-remediation/B.1-claude-adversarial.md`. Use the Template 05 YAML frontmatter and mandatory sections, `status: completed` or `halted`, H1, and `## Verdict` with a bare canonical verdict line. Do not commit.
