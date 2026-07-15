---
id: project_ontos_issue_165_audit_registry_tracker
type: tracker
status: scaffold
owner: Project Ontos Maintainers
depends_on:
  - project_ontos_issue_165_audit_registry_proposal
concepts:
  - workflow
  - external-review
  - proposals
---

# Project Ontos Issue #165 Audit Registry — Tracker

| Phase | Owner | Status | Artifact | Evidence | Timestamp |
|-------|-------|--------|----------|----------|-----------|
| 0 — child scaffold | orchestrator:codex | scaffolded | `manifests/project-ontos-issue-165-audit-registry.yaml` | Parent split authorizes Phase 0 scaffolding only; no registry implementation, workflow change, ledger replacement, or GitHub write is authorized | 2026-07-15 |
| -A.proposal authoring | proposal-author:codex | scaffolded | `docs/specs/project-ontos-issue-165-audit-registry-proposal.md` | Registry authority, 100-record invariant, namespace separation, parity tiers, rollback, and review questions drafted from approved evidence | 2026-07-15 |
| -A.proposal review | proposal-reviewer:glm | pending | `docs/reviews/project-ontos-issue-165-audit-registry/pre-a-proposal-verdict.md` | Must be a non-author Template 16 verdict; only exact `Proceed to Phase A` opens Phase A | |
| A — specification | spec-author:codex | blocked | `docs/specs/project-ontos-issue-165-audit-registry-spec.md` | Blocked on non-author Pre-A approval; must reconcile all 100 source records and freeze schema, transitions, determinism, and parity behavior | |
| B — design review | review board | not started | `docs/reviews/project-ontos-issue-165-audit-registry/` | User-facing Product review is required in B.1 and B.2; strict-P3 design review must preserve the #165/#174 boundary | |
| C — implementation | implementation-author:codex | not started | registry, schema, validator, renderer, focused tests, generated O4 projection, and read-only parity workflow | No implementation begins before the approved specification; no live issue mutation is in scope | |
| D — implementation review and verification | review board | not started | `docs/reviews/project-ontos-issue-165-audit-registry/` | Strict-P3 implementation review, Product review, blocker fixes, three-family verification, offline fork proof, and authenticated read-only parity evidence | |
| E — retrospective | retro-author:codex | not started | `docs/retros/project-ontos-issue-165-audit-registry-retro.md` | Begins only after final approval and verified O4 authority handoff; completion unblocks the v5.1 release gate | |
