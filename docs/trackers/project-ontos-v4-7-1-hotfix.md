---
id: project-ontos-v4-7-1-hotfix-tracker
deliverable_id: project-ontos-v4-7-1-hotfix
type: tracker
status: active
depends_on:
  - project-ontos-v4-7-1-hotfix-spec
---

# Project Ontos v4.7.1 Hotfix — Lifecycle Tracker

Baseline: `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`
Branch: `audit/v4.7.1-hotfix`
Merge authority: maintainer only; this lifecycle may recommend but may not merge,
tag, publish, release, or close issues.

| Phase | Owner | Status | Artifact | Evidence | Timestamp |
|---|---|---|---|---|---|
| A | codex | completed | `docs/specs/project-ontos-v4-7-1-hotfix-spec.md` | Ten-section contract split spec with two diagrams; manifest conformance passes | 2026-07-11 |
| B.1 | claude / gemini / glm / product | pending | `docs/reviews/project-ontos-v4-7-1-hotfix/B.1-*` | Fresh family dispatch required | — |
| B.2 | claude / gemini / glm / product | pending | `docs/reviews/project-ontos-v4-7-1-hotfix/B.2-*` | Fresh second design round required | — |
| B.3 | codex | pending | `docs/reviews/project-ontos-v4-7-1-hotfix/B.3-verdict.md` | Awaiting B.1/B.2 evidence | — |
| C | codex | preimplemented-user-gated | branch working tree | Focused regressions: 290 passed; full pre-lifecycle run: 1536 passed, 4 failed, 2 skipped; three failures were environment-path selection and pass with hotfix venv on PATH, one unsafe outside-workspace fixture was corrected | 2026-07-11 |
| D.1 | claude | pending | `docs/reviews/project-ontos-v4-7-1-hotfix/D.1-claude-peer.md` | Fresh implementation inspection required | — |
| D.2 | claude / gemini / glm / product | pending | `docs/reviews/project-ontos-v4-7-1-hotfix/D.2-*` | Must target the Phase C commit | — |
| D.3 | codex | pending | `docs/reviews/project-ontos-v4-7-1-hotfix/D.3-verdict.md` | Awaiting D.2 board | — |
| D.4 | codex | pending | `docs/reviews/project-ontos-v4-7-1-hotfix/D.4-fix-summary.md` | Required even if no-op | — |
| D.5 | claude / gemini / glm | pending | `docs/reviews/project-ontos-v4-7-1-hotfix/D.5-*-verifier.md` | Must target final reviewed commit | — |
| D.6 | codex | withheld | `docs/reviews/project-ontos-v4-7-1-hotfix/final-approval.md` | May run only after admissible strict-P3 evidence; provider-limited fallback keeps D.6 withheld | — |
| E | codex | pending | `docs/retros/project-ontos-v4-7-1-hotfix-retro.md` | After lifecycle status is mechanically known | — |

## Contract decisions

| Decision | v4.7.1 disposition |
|---|---|
| General strict UTF-8 loading | Deferred to v5; mutation reads remain strict |
| Command envelope | Main's schema 3.4 and key set retained exactly |
| Map timestamp suppression | Deferred; real map generation semantics unchanged |
| Activation incompatibility state/reason | Deferred because it alters CLI/MCP results |
| Wheel-only publication | Deferred because removing the sdist changes distribution contract |
| Hook rewiring | Deferred pending command/exit parity proof |
| Golden recapture | Deferred; all tracked baselines remain unchanged |

## Active blockers

- No lifecycle receipt exists yet for this focused deliverable.
- D.6 is withheld until strict-P3 succeeds. If a genuine provider dispatch
  fails and the framework fallback verifies, the terminal label must remain
  `provider_limited_fallback_complete; strict P3 not certified; maintainer release actions deferred`.
- PR #161 cannot be rebased into a v5.0.0 PR until this hotfix is reviewed and
  merged by the maintainer.
