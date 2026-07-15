---
id: project_ontos_v5_0_3_dependency_resolver_tracker
type: tracker
status: scaffold
owner: Project Ontos Maintainers
depends_on:
  - project_ontos_v5_0_3_dependency_resolver_proposal
concepts:
  - proposals
  - link-check
  - workflow
---

# Project Ontos v5.0.3 Dependency Resolver — Tracker

| Phase | Owner | Status | Artifact | Evidence | Timestamp |
|-------|-------|--------|----------|----------|-----------|
| 0 — child scaffold | orchestrator | scaffolded | `manifests/project-ontos-v5-0-3-dependency-resolver.yaml`; proposal; tracker | Parent split assigns #176 only; no Phase A or implementation authority is claimed | 2026-07-15 |
| -A.proposal | proposal-reviewer:glm | pending | `docs/reviews/project-ontos-v5-0-3-dependency-resolver/pre-a-proposal-verdict.md` | Awaiting an independent Template 16 decision on the proposal | |
| A | spec-author:codex | blocked | `docs/specs/project-ontos-v5-0-3-dependency-resolver-spec.md` | Blocked until the exact non-author verdict `Proceed to Phase A`; future branch and immutable base SHA are not yet created | |
| B.1 | external board + Product | not started | family and Product verdicts | Starts only after an approved Phase A specification | |
| B.2 | external board + Product | not started | family and Product verdicts | Starts only if the B.1 review loop requires it | |
| B.3 | meta-consolidator | not started | canonical specification verdict | No specification review evidence exists | |
| C | implementation-author:codex | not started | scoped implementation | No implementation is authorized by this scaffold | |
| D.1 | peer reviewer | not started | review artifact | Awaiting implementation | |
| D.2 | external board + Product | not started | family and Product verdicts | Awaiting implementation | |
| D.3 | meta-consolidator | not started | canonical implementation verdict | Awaiting D.2 evidence | |
| D.4 | fix-author:codex | not started | fix summary | Runs only if D.3 preserves findings | |
| D.5 | external verifiers | not started | verifier artifacts | Awaiting reviewed implementation | |
| D.6 | final approval | not started | final approval | Awaiting all lifecycle gates | |
| E | retro author | not started | retrospective | Awaiting an approved and merged deliverable | |
