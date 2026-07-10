# B.1 alignment dispatch

Work in the current repository. Read `.llm-dev/framework/templates/01-worker-session-contract.md`, `02-phase-dispatch-handoff.md`, and `04-review-board-alignment.md` completely and obey them.

You are the Gemini-family Alignment reviewer, executed through AGY, for `project-ontos-audit-rebaseline-remediation`, phase `B.1`. Evidence cap is `static-inspection`. Review the Phase A spec at `docs/specs/project-ontos-audit-rebaseline-remediation-spec.md` against:

- `docs/reviews/2026-07-10-codex-audit-revalidation.md`
- `manifests/project-ontos-audit-remediation-registry.yaml`
- `docs/trackers/project-ontos-audit-remediation-release-line.md`
- `docs/trackers/project-ontos-audit-rebaseline-remediation.md`
- original audit roadmap §5 and frozen I0 diff `bf91b42...b6f89d7`.

Check all public-behavior declarations, every implementation/test anchor, exact finding/status counts, external evidence blockers, and the nonclaims about historical leases, per-issue certification, D.6, and release. Do not claim direct execution.

Output only the complete verdict artifact to stdout so the wrapper can capture it as `docs/reviews/project-ontos-audit-rebaseline-remediation/B.1-gemini-alignment.md`. It must start with YAML frontmatter, then one H1, and use `status: completed` or `halted`. F35 OVERRIDES Template 04's numbered sample: the verdict heading must be exactly the unnumbered line `## Verdict` (not `## 9. Verdict`), immediately followed by exactly one bare canonical verdict line (`Approve`, `Request changes`, `Reject`, or `Concur`). Do not omit this final section.
