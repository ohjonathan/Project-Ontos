You are an external Phase B.1 reviewer, not the implementation author or orchestrator.

Workspace: /tmp/project-ontos-worktrees/project-ontos-v4.7.1-hotfix
Expected branch: audit/v4.7.1-hotfix
Implementation snapshot: e33a31d0c0040de9afa1f8efe22246c798534edd
Baseline: bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95
Deliverable: project-ontos-v4-7-1-hotfix
Phase: B.1

Before reviewing, run or inspect:
- git status --short --branch
- git rev-parse HEAD
- docs/specs/project-ontos-v4-7-1-hotfix-spec.md
- manifests/project-ontos-v4-7-1-hotfix.yaml
- git diff bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95..e33a31d0c0040de9afa1f8efe22246c798534edd
- CHANGELOG.md
- relevant tests and code named by the spec

Review the real code-first implementation and the spec independently. Do not accept author claims as evidence. Reproduce blocking findings when your capability permits. Evidence labels are direct-run, orchestrator-preflight, static-inspection, or not-run. Do not merge, commit, tag, push, alter product code, edit docs/logs, or touch any file except the one artifact path named below. If you cannot write the artifact, return the complete artifact as stdout so the wrapper can promote it. Do not fabricate findings. The first nonblank line under the verdict heading must be exactly Approve, Request changes, Reject, or Concur.

Role: adversarial, family: claude.
Artifact path: docs/reviews/project-ontos-v4-7-1-hotfix/B.1-claude-adversarial.md
Attack the contract split, safe YAML round trips, path containment, symlink and race handling, rollback, cross-platform behavior, strict-vs-replacement UTF-8 boundary, unchanged envelope, and test hermeticity. Required artifact shape:
---
id: project-ontos-v4-7-1-hotfix-B.1-claude-adversarial
deliverable_id: project-ontos-v4-7-1-hotfix
phase: B.1
role: adversarial
family: claude
evidence_labels_used: [direct-run]
status: completed
---
# Adversarial Review — project-ontos-v4-7-1-hotfix / B.1 / claude
## 1. Input boundary attestation
## 2. Invariant re-derivation
## 3. Assumption attack
## 4. Failure mode analysis
## 5. Diagram completeness attack
## 6. Edge case inventory
## 7. Security surface
## 8. Issues found
### Blocking (Critical)
### Should-fix (Major)
### Minor
## Verdict
## Notes
