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
| -A.proposal authoring | proposal-author:codex | content complete — review pending | `docs/specs/project-ontos-v5-remediation-release-plan-proposal.md` | Published from current-main baseline `7d07556e0f71c0f1eca8760614aef6d21951f874`; `G-scope-1` and `G-branch-1` pass on the dedicated branch, while terminal clean-tree verification is performed after commit | 2026-07-14 |
| -A.proposal review | proposal-reviewer:claude-opus | pending | `docs/reviews/project-ontos-v5-remediation-release-plan/pre-a-proposal-verdict.md` | Template 16 two-lens non-author review | |
| 0 — child split | orchestrator | pending | release-specific child proposals and manifests | Enter only after the exact `Split into multiple proposals` verdict; each child re-enters at Pre-A and this parent never enters Phase A | |
| Child governance | orchestrator | pending | each child manifest and Phase A spec | Every child carries a scoped v5/v6 watch item; children changing public CLI/config/query/export/JSON/MCP/migration contracts, including #173/#177/#178, set `user_facing: true` and receive Product review | |
