---
id: meta-orchestrator-kickoff
type: handoff
status: draft
meta_cycle_id: project-ontos-audit-remediation-2026-07
instantiated_from: .llm-dev/framework/templates/24-meta-orchestrator-kickoff.md
instantiated_by: claude-fable-5 (audit-authoring session; see §5 family-rotation preflight)
date: 2026-07-03
---

# Meta-orchestrator Kickoff — Project-Ontos Audit Remediation

> **Instance** of Template 24 (`.llm-dev/framework/templates/24-meta-orchestrator-kickoff.md`, v1.0.0).
> This document opens the meta-cycle that coordinates remediation of the 91-finding
> [Fable repo audit](../reviews/2026-07-02-fable-repo-audit.md) (merged PR #145) across the
> 12 GitHub issues #146–#157 and three release lines. Paste/hand this to a **fresh** meta-orchestrator
> session — do **not** run it from the audit-authoring session (per the peer recommendation and §5 below).

## BEGIN META-ORCHESTRATOR KICKOFF

### 1. Charter

This is a **Meta Orchestrator** session for meta-cycle `project-ontos-audit-remediation-2026-07`.
The session is bounded to meta-cycle work: cross-deliverable continuity across the 12 remediation
deliverables, release-line custody (v4.7.1 → v4.8.0 → v4.9.0), scope-lock recovery between
deliverables, stale-assumption audits, and architectural-fork escalation for the cross-surface
contract work. It does **not** replace the per-deliverable Orchestrator (Codex), override lifecycle
gates, or author per-phase product artifacts (specs, code, reviews, verifier outputs, retros).

**Template self-check (mandatory first action).** This document's frontmatter declares
`id: meta-orchestrator-kickoff`. ✅ Confirmed at authoring time. The opening session MUST re-verify
this as its first act; if the `id` field is absent or altered, halt under S7 with a self-incident log
entry and do not proceed.

### 2. Invocation trigger

`INVOCATION_TRIGGER = T1 + T2 + T5.`

- **T1 (spanning ≥2 concurrent deliverables).** The remediation coordinates 12 concurrent deliverables
  (#146–#157). Evidence: [remediation tracker #158](https://github.com/ohjonathan/Project-Ontos/issues/158)
  and the audit's §5 roadmap.
- **T2 (release-line stamping).** The cycle stamps three release lines and decides which findings ride
  which release. Evidence: milestones "Audit Release N — hotfix" / "N+1" / "N+2" (§7 below).
- **T5 (architectural-fork escalation).** Several deliverables are cross-layer contracts that no single
  deliverable's spec can resolve alone — the exit-code taxonomy + JSON-envelope/status unification
  (#154) and the frontmatter-parser consolidation (#151) span the CLI, MCP, and `core` layers with a
  layer-boundary contract. 3-part test met: ≥2 layers (CLI ⊕ MCP ⊕ core), an explicit layer-boundary
  contract (the shared serializer/envelope), non-resolvable inside one deliverable's scope. Evidence:
  audit findings `D7-cli-consistency-3/4`, `D1c-envelope-4/5`, `D3a-parsers-2/3`, `D3b-structure-1`.

### 3. Spanning deliverables

Deliverable registry (12), each carrying a `deliverable_id`, its source GitHub issue, and the
`docs/trackers/<deliverable-id>.md` tracker path it will own. **Trackers do not exist yet**: creating
each is Phase-0 work owned by that deliverable's Orchestrator (Codex), which the meta-cycle *routes to*
but does not author (non-trigger N6 / M-NA2). Until a tracker exists, the GitHub issue is the interim
deliverable-of-record.

| deliverable_id | Issue | Sev | Release |
|---|---|---|---|
| `project-ontos-audit-serializer-corruption` | #146 | P0 | v4.7.1 |
| `project-ontos-audit-doctor-rce` | #147 | P1·sec | v4.7.1 |
| `project-ontos-audit-relN-quick-wins` | #148 | P1 | v4.7.1 |
| `project-ontos-audit-relN-sweep` | #149 | P2 | v4.7.1 |
| `project-ontos-audit-characterization-tests` | #150 | P2 | v4.8.0 |
| `project-ontos-audit-parser-consolidation` | #151 | P1 | v4.8.0 |
| `project-ontos-audit-writepath-bodyref` | #152 | P1 | v4.8.0 |
| `project-ontos-audit-mcp-dispatch-rename` | #153 | P1 | v4.8.0 |
| `project-ontos-audit-exitcode-envelope` | #154 | P1 | v4.9.0 |
| `project-ontos-audit-cli-command-table` | #155 | P2 | v4.9.0 |
| `project-ontos-audit-precommit-rewire-slim` | #156 | P1 | v4.9.0 |
| `project-ontos-audit-graph-traversal` | #157 | P2 | v4.9.0 |

No T3 (resumption after halt) in this trigger, so `PRIOR_HALT_STATE_REF = n/a`.

**Dependency edges the meta-cycle must enforce when dispatching (not a free-for-all):**
- #146 and #147 are independent and dispatchable immediately (v4.7.1).
- #150 (characterization test net) MUST complete before #151/#152/#153 are dispatched — the tests
  bracket the refactors (audit §5 "tests before refactors").
- #154 (exit-code/envelope) and #156 (repo slimming) come last; #156's pre-commit/CI rewire is a
  prerequisite for retiring the legacy fork and unblocks the "pre-commit fails on main" condition.

### 4. Scope-lock manifest

Allowed paths the meta-cycle MAY write (`SCOPE_LOCK_PATHS`):

- `docs/handoffs/project-ontos-audit-remediation-2026-07-*` — meta-cycle handoffs (incl. this file).
- `docs/proposals/project-ontos-audit-remediation-2026-07-*` — meta-cycle proposal (O1), if authored.
- `docs/trackers/project-ontos-audit-remediation-release-line.md` — the **cross-deliverable** release-line
  tracker (spans ≥2 deliverables → permitted under M-A3; distinct from per-deliverable trackers).
- `.llm-dev/framework/review-board/project-ontos-audit-remediation-2026-07-*` — the meta-cycle's **own**
  review-board entries only.

**Forbidden-paths preflight (spec §3.5.1 F-1..F-4), checked before any edit:**
- **F-1** product code — `ontos/`, `tests/`, `scripts/`, and every host-product code path. The meta-cycle
  never edits these; all code changes route to per-deliverable Orchestrators.
- **F-2** per-deliverable tracker rows (`docs/trackers/project-ontos-audit-1XX-*.md`).
- **F-3** another deliverable's review-board artifacts.
- **F-4** any deliverable's D.6 final-approval gate but the meta-cycle's own.

Any forbidden entry → S2 + S7 self-incident, halt before editing.

### 5. Authority block + family-rotation preflight ⚠️ USER DECISION REQUIRED

Meta-Orchestrator authority is framework-native by role within trigger scope (M-A1..M-A4 permitted;
M-NA1..M-NA5 forbidden — verbatim per Template 24 §5; not re-listed here).

**Family-rotation preflight — the one open item before this kickoff can legally open.**
The rule (spec §3.2): *a Meta Orchestrator session MUST NOT be authored by the same family that authored
the meta-cycle's primary input artifact.* The primary input here is the **audit report**, authored by
**Claude Fable 5 (claude family)**. Your stated topology is **Claude-as-meta / Codex-as-implementation**,
which puts the *same* family (claude) on both the primary input and the meta session — a **literal
conflict** with the preflight.

Two lawful resolutions — pick one and record it in the opening session's decision log:

- **Option A — record a discharge rationale, keep Claude-as-meta (recommended, matches your topology).**
  The rotation rule exists to prevent a family from self-adjudicating its own artifact. That intent is
  already satisfied: the audit was independently reproduced and confirmed by **three non-claude
  reviewers** (Gemini, GLM-5.2, ChatGPT) on PR #145 before merge, and the meta-cycle *coordinates*
  remediation rather than re-judging the audit's correctness. Record this as an explicit
  `family_rotation_discharged: external-multifamily-review-of-primary-input (PR #145)` entry. Codex then
  remains the implementation family; claude/gemini rotate as reviewers on the per-deliverable boards.
- **Option B — conservative literal compliance.** Open the meta session as **Gemini or Codex** (non-claude)
  and let Claude serve as an implementation/review family downstream. This satisfies the letter of §3.2 but
  contradicts your stated Claude-as-meta preference.

**Default carried into this kickoff: Option A**, pending your confirmation. If you prefer strict letter,
switch to Option B before opening the session.

### 6. Decision procedure recap (spec §3.4)

```
Q1 (≥2 deliverables / release-line span / halt-state / architectural fork / stale-assumption audit?):
   YES — 12 concurrent deliverables, a 3-release-line decision, and a cross-layer architectural fork.
Q2 (can one per-deliverable Orchestrator handle it in a single Phase 0–E without crossing M-NA1/2/3?):
   NO — the work spans 12 deliverables and 3 releases; no single lifecycle covers it.
Q3 (bounded to meta-cycle artifacts only — proposal/handoff/closeout/kickoff/ledger/scope-lock manifest?):
   YES — the meta-cycle produces coordination artifacts and dispatches; it writes no product code.
```
Q1=YES ∧ Q2=NO ∧ Q3=YES ⇒ a Meta Orchestrator session is warranted.

### 7. Expected outputs

`EXPECTED_OUTPUTS` (from spec §3.7 O1..O6):
- **O2** — this handoff (and any subsequent meta-cycle handoffs).
- **O3** — this instantiated kickoff.
- **O4** — a cross-deliverable **verification ledger** tracking each deliverable's lifecycle status
  (Phase 0→E, strict-P3 vs provider-limited) as it lands.
- **O5** — a cross-deliverable **scope-lock manifest** (the `ontos/` package is co-owned by several
  deliverables — e.g. `core/frontmatter*` touched by #146, #151, #152 — so the meta-cycle owns the
  allowlist that keeps concurrent deliverables from colliding on the same files).
- **O6** — a **release-line decision artifact** confirming or revising the pre-declaration below.

The session does **not** produce per-deliverable implementation, per-phase artifacts, or D.6 verdicts.

`RELEASE_LINE_DECISION` (T2 pre-declaration — authoritative until an O6 revises it):
- **v4.7.1** (patch): #146 (P0) + #147 (RCE), each with a regression test; #148 + #149 optional in-patch.
- **v4.8.0** (minor): #150 first → then #151, #152, #153.
- **v4.9.0** (minor): #154, #155, #156, #157.
> Version numbers are proposals for your confirmation; the meta session emits O6 to finalize.

### 8. Stop conditions

Inherits S1–S7 (Template 24 §8): falsified inherited assumption (S1), scope violation (S2),
architectural fork (S3 → route to user), provenance contamination (S4), cross-provider model-pin
exception (S5), destructive repo op (S6), crossed authority line (S7). No auto-resume; resumption needs
explicit user routing + a fresh kickoff or continuation prompt.

### 9. Composition with Templates 00 / 02 / 11

Each deliverable's downstream Codex Orchestrator uses **Template 00** for its Phase 0→E lifecycle. When
the meta-cycle dispatches a deliverable, it routes to a Codex Orchestrator session opened with a
**Template 02** phase-dispatch handoff (the one-shot prompt in §10.5). **Template 11** continuation
prompts live at the worker level; not used at kickoff (no T3).

### 10.5 Implementation-orchestrator handoff — 9-field skeleton (MANDATORY per dispatch)

Every one-shot Codex dispatch prompt the meta session emits MUST carry all nine fields below, and SHOULD
be checked with `.llm-dev/framework/scripts/check-meta-orchestrator-handoff.sh` before sending (good/bad
fixtures at `.llm-dev/framework/examples/meta-orchestrator-handoff/`). Reusable skeleton — fill per
deliverable:

1. **Deliverable id** — the exact `deliverable_id` from §3 (e.g. `project-ontos-audit-serializer-corruption`).
   No inference from slug/title.
2. **User goal** — one paragraph: what success looks like for Jonathan (e.g. "`ontos promote`/`migrate`
   and MCP `promote_document` never corrupt user frontmatter; a valid file stays valid and byte-faithful
   after a write").
3. **Exact artifact list through Phase E** — Phase 0 manifest + `docs/trackers/<id>.md`; Phase A spec
   under `docs/specs/<id>.md`; B.1 board; C implementation (the `ontos/` change + tests); D.2 review; D.4
   fix-summary *only if D.3 preserves blockers*; D.5 verifier triple; D.6 final approval; E retro; plus
   the Ontos session log (`ontos log`).
4. **Strict-provider path** — when ≥3 non-author family CLIs are dispatchable:
   `scripts/dispatch-family-review.sh`, `scripts/verify-family-dispatch.sh --require-complete`,
   `scripts/verify-lifecycle.sh --mode strict-p3`. Final status string (exact): `strict_p3_review_complete`.
5. **Provider-limited fallback path** — when strict dispatch is unavailable but the user authorized
   `provider-limited-review-exception`: every B.1/B.3/D.2/D.3/D.5 artifact carries the fallback
   frontmatter + banner; D.4 and D.6 remain non-fallback honest work; **D.6 and E are NOT optional under
   fallback — "do not fabricate evidence" is a labeling rule, not a stop condition.** Final status
   (exact): `provider_limited_fallback_complete; strict P3 not certified; maintainer release actions deferred`.
6. **Stop-only path** — narrow: a missing prerequisite (referenced spec/manifest/helper absent or
   malformed). "CLI unavailable" is NOT a stop — it routes to field 5.
7. **Validation commands** — verbatim, no placeholders. Per deliverable, at minimum:
   `.venv/bin/python -m pytest tests/ -q`, `git diff --check`, plus any deliverable-specific fixture (e.g.
   a frontmatter round-trip test for #146). Framework attestation: `bash .llm-dev/framework/scripts/verify-all.sh`.
8. **Commit / tag / push / merge / issue-closure policy** — **default: ALL deferred to the maintainer
   (Jonathan).** A row flips to "performed in session" only with explicit user authorization recorded in
   that dispatch. (Matches `templates/07-final-approval-gate.md § Release-action split`.)
9. **Final response status language** — the exact status string from field 4 or 5 depending on the path
   taken. No paraphrase; downstream automation string-matches.

### 11. Final report schema (emit verbatim at meta-session end)

```yaml
meta_cycle_id: project-ontos-audit-remediation-2026-07
invocation_trigger_fired: [T1, T2, T5]
spanning_deliverables: [project-ontos-audit-serializer-corruption, project-ontos-audit-doctor-rce,
  project-ontos-audit-relN-quick-wins, project-ontos-audit-relN-sweep,
  project-ontos-audit-characterization-tests, project-ontos-audit-parser-consolidation,
  project-ontos-audit-writepath-bodyref, project-ontos-audit-mcp-dispatch-rename,
  project-ontos-audit-exitcode-envelope, project-ontos-audit-cli-command-table,
  project-ontos-audit-precommit-rewire-slim, project-ontos-audit-graph-traversal]
outputs_produced: [<O2..O6 actually written>]
routing_handoffs:
  - to: <Codex Orchestrator session id>
    work_routed: <one-line description, e.g. "dispatch #146 serializer-corruption Phase 0→E">
circuit_breaker_state: 0
release_line_decision: <present when O6 written; the confirmed v4.7.1/v4.8.0/v4.9.0 mapping>
```

**Lifecycle-backing (P18):** any cycle invoking this kickoff MUST cite this document's path in its
Phase E retro lifecycle-backing inventory, else it is a hollow-backing violation under
`verify-lifecycle-claim.sh`.

### 12. Version footer

Template version: v1.0.0 (framework v1.4.2 pilot role). Instance authored 2026-07-03.

## END META-ORCHESTRATOR KICKOFF

---

## Bootstrap note for the fresh session (not part of the normative kickoff)

Open a new Claude session and paste everything between BEGIN/END above. Its first three acts:
1. Run the **template self-check** (§1) and the **family-rotation preflight** (§5) — record Option A or B.
2. Read the authoritative inputs: the [audit report](../reviews/2026-07-02-fable-repo-audit.md),
   tracker [#158](https://github.com/ohjonathan/Project-Ontos/issues/158), and issues #146–#157.
3. Emit O5 (scope-lock manifest) + O6 (release-line decision), then dispatch #146 and #147 to Codex via
   §10.5 prompts. Do not touch `ontos/` directly.
