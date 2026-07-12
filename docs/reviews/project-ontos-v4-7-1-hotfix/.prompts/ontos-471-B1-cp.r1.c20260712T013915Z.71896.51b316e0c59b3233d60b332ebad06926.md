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

Role: product, family: claude. This is a separate worker session from the adversarial review.
Artifact path: docs/reviews/project-ontos-v4-7-1-hotfix/B.1-claude-product.md
Evaluate user impact and contract clarity, especially collision refusal, unsafe-path failures, malformed UTF-8 behavior, unchanged JSON/exit semantics, recovery guidance, and whether a patch release is correctly scoped. Required artifact shape:
---
id: project-ontos-v4-7-1-hotfix-B.1-claude-product
deliverable_id: project-ontos-v4-7-1-hotfix
phase: B.1
role: product
family: claude
evidence_labels_used: [direct-run]
status: completed
---
# Product Review — project-ontos-v4-7-1-hotfix / B.1 / claude
## 1. User-value assessment
## 2. Product-surface cross-reference
### 2.1 Spec-declared user-visible surfaces
### 2.2 Spec-vs-implementation cross-reference
## 3. UX-friction inventory
## 4. Copy review
## 5. Accessibility surface
## 6. Failure-visibility
## 7. Issues found
### Blocking
### Should-fix
### Minor
## 8. Positive observations
## 9. Verdict
## 10. Notes
