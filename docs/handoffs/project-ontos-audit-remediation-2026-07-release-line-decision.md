---
id: project_ontos_audit_remediation_2026_07_release_line_decision
type: handoff
status: active
meta_cycle_id: project-ontos-audit-remediation-2026-07
output_class: O6
date: 2026-07-03
family_rotation_discharged: "external-multifamily-review-of-primary-input (PR #145)"
depends_on: []
---

# O6 — Release-line decision — project-ontos-audit-remediation-2026-07

This artifact **confirms, unchanged,** the `RELEASE_LINE_DECISION` pre-declaration in
kickoff §7 (`docs/handoffs/2026-07-03-audit-remediation-meta-orchestrator-kickoff.md`)
and is the authoritative release-line mapping for the meta-cycle until a superseding O6
revises it. Confirmed by the maintainer (Jonathan) on 2026-07-03 in the meta-orchestrator
session.

## Decision

GitHub milestone → version pins (milestone titles as they exist on
`ohjonathan/Project-Ontos`):

- **"Audit Release N — hotfix" → v4.7.1** (patch): #146 (P0 serializer corruption) and
  #147 (P1·sec doctor RCE + SECURITY.md correction), **each with a mandatory regression
  test**; #148 (P1 quick wins) and #149 (P2 sweep) ride in-patch — confirmed as full
  hotfix scope, matching the existing milestone contents — and roll forward to v4.8.0
  only if not ready when #146/#147 are.
- **"Audit Release N+1" → v4.8.0** (minor): #150 (characterization test net) completes
  **first**, then #151 (parser consolidation), #152 (write-path/body-ref), #153
  (MCP dispatch/rename).
- **"Audit Release N+2" → v4.9.0** (minor): #154 (exit-code/envelope), #155 (CLI command
  table), #156 (pre-commit rewire + repo slim), #157 (graph traversal).

## Sequencing constraints (binding on dispatch order)

1. #146 and #147 are independent — dispatched immediately (2026-07-03).
2. #150 MUST complete before #151/#152/#153 are dispatched ("tests before refactors",
   audit §5).
3. #154 and #156 come last; #156's pre-commit/CI rewire is a prerequisite for retiring
   the legacy `.ontos/scripts/` fork.

## Family-rotation preflight resolution (kickoff §5 — Option A)

- **Rule (spec §3.2):** a Meta Orchestrator session MUST NOT be authored by the same
  family that authored the meta-cycle's primary input artifact.
- **Facts:** the primary input (the audit report,
  `docs/reviews/2026-07-02-fable-repo-audit.md`) was authored by the **claude** family
  (Claude Fable 5); the maintainer's chosen topology is Claude-as-meta /
  Codex-as-implementation — a literal same-family conflict.
- **Resolution: Option A — discharge recorded.** The rule's intent (no family
  self-adjudicates its own artifact) is already satisfied: the audit was independently
  reproduced and confirmed by **three non-claude reviewers** (Gemini, GLM-5.2, ChatGPT)
  on PR #145 before merge — all confirmed the P0 and the doctor RCE end-to-end, 0
  findings refuted — and this meta-cycle *coordinates remediation*; it does not re-judge
  the audit's correctness. Recorded entry:
  `family_rotation_discharged: "external-multifamily-review-of-primary-input (PR #145)"`
  (also in this file's frontmatter).
- **Downstream topology:** Codex is the implementation family for all 12 deliverables;
  claude/gemini/gpt rotate as the non-author review families on the per-deliverable
  boards.
- **User confirmation:** Option A confirmed by Jonathan, 2026-07-03.

## Decision log (meta-orchestrator session, 2026-07-03)

1. **Template self-check (kickoff §1): PASS** — the kickoff frontmatter declares
   `id: meta-orchestrator-kickoff`.
2. **Decision procedure recap (spec §3.4): Q1=YES, Q2=NO, Q3=YES** — meta session
   warranted (12 concurrent deliverables, 3-release-line decision, cross-layer
   architectural fork; bounded to meta-cycle artifacts).
3. **Forbidden-paths preflight (F-1..F-4): PASS** — recorded in the O5 preamble of
   `docs/trackers/project-ontos-audit-remediation-release-line.md`.
4. **Family rotation: Option A discharge** (above), confirmed by Jonathan.
5. **Release-line mapping confirmed** as full hotfix scope (above), confirmed by
   Jonathan.
6. **`provider-limited-review-exception`: NOT pre-authorized.** Each dispatch prompt
   instructs the Codex Orchestrator to halt its review phase and request the exception
   from Jonathan if strict 3-family dispatch is unavailable, recording the authorization
   before proceeding under fallback labeling. Confirmed by Jonathan, 2026-07-03.
7. **Release actions: all maintainer-deferred.** The meta-session leaves every authored
   artifact uncommitted in the working tree; no branch, no commit, no push, no issue
   edits. (Framework default per Template 07 § Release-action split.)
8. **Host-convention side effects noted:** `ontos map` (regenerates
   `Ontos_Context_Map.md`, already dirty pre-session) and `ontos log` (writes the
   session log) are CLAUDE.md-mandated host-repo conventions executed via
   `.venv/bin/ontos` (the repo-local v4.7.0; the globally installed 4.6.0 rejects the
   repo's `validation.allowed_orphan_paths` config key — pre-existing environment
   condition). They are tool-generated outputs, not meta-cycle-authored artifacts, and
   sit outside the kickoff §4 allowlist by that classification. `ontos doctor` was NOT
   run (it is the #147 RCE surface).
9. **Ontos orphan warnings accepted:** new `docs/handoffs/` documents may emit
   non-blocking orphan warnings in `ontos map` (the kickoff itself already does);
   `docs/handoffs/**` is not in `.ontos.toml`'s `allowed_orphan_paths`. Acceptable;
   no config change made (config is product surface, F-1).

## Supersession

Revising this decision requires a new O6 handoff under
`docs/handoffs/project-ontos-audit-remediation-2026-07-*` that names this file as
superseded. Until then, this mapping is authoritative for ledger stamping and dispatch
sequencing.
