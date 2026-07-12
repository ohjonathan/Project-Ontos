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
| B.1 | claude / gemini / glm / product | completed-with-provider-gap | `docs/reviews/project-ontos-v4-7-1-hotfix/B.1-*` | Claude adversarial/Product and GLM peer artifacts captured; Gemini direct and AGY routes failed with provider-policy evidence | 2026-07-11 |
| B.2 | claude / gemini / glm / product | attempted-no-admissible-board | `docs/reviews/project-ontos-v4-7-1-hotfix/B.2-*` | Gemini provider failure repeated; Claude artifacts were not promoted by wrapper; GLM stopped at declared timebox | 2026-07-11 |
| B.3 | codex | completed | `docs/reviews/project-ontos-v4-7-1-hotfix/B.3-verdict.md` | Eight accepted B.1 actions reconciled; lifecycle gap explicitly preserved | 2026-07-11 |
| C | codex | completed | `ef869f7e805b691fc614e7017c16438e2d33de0a` | Product fixes are in `a0062ae`; final ref adds a test-only hermetic doctor aggregate correction; 82 focused plus final full-suite verification | 2026-07-11 |
| D.1 | claude | completed-request-changes | `docs/reviews/project-ontos-v4-7-1-hotfix/D.1-claude-peer.md` | Two direct-run blockers preserved: quoted-key mutation boundary and immutable portfolio WAL publication | 2026-07-11 |
| D.2 | claude / gemini / glm / product | attempted-provider-limited | `docs/reviews/project-ontos-v4-7-1-hotfix/D.2-*` | Product artifact was substantive but shape-invalid; Gemini provider failed; GLM sandbox failed; Claude peer did not complete | 2026-07-11 |
| D.3 | codex | completed-provider-limited | `docs/reviews/project-ontos-v4-7-1-hotfix/D.3-verdict.md` | Two supported blockers preserved; artifact explicitly warning-only and non-canonical P3 evidence | 2026-07-11 |
| D.4 | codex | completed | `docs/reviews/project-ontos-v4-7-1-hotfix/D.4-fix-summary.md` | Both blockers closed in `a0062ae`; EH-15-A adopter-verifier defect recorded | 2026-07-11 |
| D.5 | claude / gemini / glm | attempted-provider-limited | `docs/reviews/project-ontos-v4-7-1-hotfix/D.5-orchestrator-status.md` | Four wrapper-recorded attempts, zero valid artifacts/receipts; direct falsification and 1572-test suite are green but do not substitute external evidence | 2026-07-11 |
| D.6 | codex | withheld | `docs/reviews/project-ontos-v4-7-1-hotfix/final-approval.md` | `--allow-gated` artifact only; strict and fallback lifecycle verifiers remain incomplete | 2026-07-11 |
| E | codex | not-reached | `docs/retros/project-ontos-v4-7-1-hotfix-retro.md` | Post-merge retrospective is maintainer-deferred because no merge occurred | — |

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

- B.1, B.2, and D.2 dispatch bundles do not pass `--require-complete`; their
  failed attempts and hash-bound raw evidence remain intact.
- The v2.0.1 receipt schema rejects wrapper-emitted Product receipts, and the
  fallback generator cannot bind real stderr evidence to an empty failed
  artifact without mislabeling it.
- The genuine D.5 wave and one correctable Gemini retry are complete. The
  framework reports `provider_limited_fallback_incomplete`; no receipt was
  reconstructed.
- D.6 is withheld. The maintainer-directed process label is
  `provider_limited_fallback_complete; strict P3 not certified; maintainer release actions deferred`.
- PR #161 cannot be rebased into a v5.0.0 PR until this hotfix is reviewed and
  merged by the maintainer.
