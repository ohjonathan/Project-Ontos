---
id: project_ontos_v5_remediation_release_plan_tracker
type: tracker
status: active
owner: Project Ontos Maintainers
depends_on:
  - project_ontos_v5_remediation_release_plan_proposal
concepts:
  - proposals
  - release
  - workflow
---

# Project Ontos v5 Remediation Release Plan — Tracker

| Phase | Owner | Status | Artifact | Evidence | Timestamp |
|-------|-------|--------|----------|----------|-----------|
| Charter | orchestrator | active | `manifests/project-ontos-v5-remediation-release-plan.yaml` | Framework-governed Template 16 Pre-A proposal; only `Split into multiple proposals` is accepted; no parent A-E certification is claimable | 2026-07-14 |
| -A.proposal authoring | proposal-author:codex | content complete — review pending | `docs/specs/project-ontos-v5-remediation-release-plan-proposal.md` | Merged proposal corrected from `main@bd04620376ed6a8d0024e990e04a86da402b9398` so the v5.0.3 required-version preflight has its own sixth child; the GLM verdict must record the exact reviewed commit | 2026-07-14 |
| -A.proposal review | proposal-reviewer:glm | pending | `docs/reviews/project-ontos-v5-remediation-release-plan/pre-a-proposal-verdict.md` | Template 16 two-lens non-author review through the named attested GLM route | |
| 0 — child split | orchestrator | pending | six release-specific child proposals, trackers, and manifests | Enter only after the exact `Split into multiple proposals` verdict; each child re-enters at Pre-A and this parent never enters Phase A | |
| Child governance | orchestrator | pending | each of six child manifests and proposals | Every child carries a scoped v5/v6 watch item, starts with an independent Pre-A review, sets `user_facing: true`, and receives Product review | |
