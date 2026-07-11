---
id: project-ontos-audit-rebaseline-remediation-tracker
type: tracker
status: active
depends_on:
  - project-ontos-codex-audit-revalidation-2026-07
  - project_ontos_audit_remediation_release_line_tracker
---

# project-ontos-audit-rebaseline-remediation — lifecycle tracker

## Phase 0 authority and immutable inputs

This is a new branch-level integration deliverable. It reviews the exact audit
re-baseline/remediation snapshot as one code-first integration diff; it does not
reuse or broaden the narrower #146 or #147 deliverable lifecycles.

| Input | Value |
|---|---|
| Deliverable | `project-ontos-audit-rebaseline-remediation` |
| Historical implementation base | `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95` |
| Immutable implementation snapshot (I0) | `b6f89d77e7fb684b8bd9a181a24c773d5777397a` |
| Integration target branch | `codex/audit-rebaseline-remediation` |
| Lifecycle worktree branch | `codex/audit-rebaseline-remediation-lifecycle` |
| Dedicated worktree | `/tmp/project-ontos-worktrees/project-ontos-audit-rebaseline-remediation` |
| Sequencing | `code-first-user-gated` |
| Framework | repo-local `llm-dev-framework` v2.0.1 wrapper |

### User gate — 2026-07-10

The user explicitly authorized lifecycle execution on the already implemented
snapshot:

> Okay, run the full llm-dev lifecycle, until the D.5 and falsification review done. Go.

This tracker section and the matching session-log section are the auditable
`implementation_sequencing.user_gate_ref`. The authorization changes the
sequence, not the rigor: Phase A still authors the spec; B.1 reviews the spec
and I0; B.2 re-reviews the corrected spec; C reconciles I0 against the approved
spec; and the complete D review chain runs through D.5.

## Certification boundary

In scope for this lifecycle:

- review the exact `bf91b42...b6f89d7` integration snapshot and subsequent
  lifecycle-authorized fixes;
- verify that the audit addendum, 100-row registry, ledger, implementation,
  tests, and status claims agree;
- preserve open and partial findings as open or partial rather than rounding
  them up to completion;
- execute strict-P3 design/code review and D.5 verification, followed by the
  separately chartered loose falsification pass requested by the user.

Explicit non-claims:

- This lifecycle does **not** retroactively prove the original shared-tree
  lease history or clear `shared_tree_integration`.
- Its receipts do **not** substitute for #146 or #147 receipts and do not
  certify any #146–#157 issue lifecycle individually.
- It does **not** complete the registry's confirmed-open or partial rows.
- It does **not** authorize D.6, Phase E, merge, tag, TestPyPI/PyPI publication,
  release, GitHub issue closure, or checkbox completion.
- The two user-owned documents excluded from I0 remain outside lifecycle scope:
  `docs/specs/project-ontos-rationale-capture-template-proposal.md` and
  `docs/zeta.md`.

## Isolation and scope custody

All lifecycle authoring, dispatch, scope checks, and evidence capture occur in
the dedicated worktree above. The original checkout remains the integration
target and retains the two excluded user documents. The changed-path gate uses
the immutable base SHA and must account for committed, staged, unstaged, and
untracked paths. Generated prompts, raw captures, dispatch bundles, verdicts,
and receipts stay under the deliverable-specific review directory.

If I0 changes, the implementation reference must advance explicitly, the
affected reviewed diff must be re-dispatched, and this tracker must record the
transition. Evidence may never be rebound silently to a different tree.

## Certifying route roster and role rotation

The roster uses three distinct non-author families and the routes proven during
Phase 0 preflight. Product seats, when required by the manifest, are separate
dispatches and never replace an engineering strict-P3 seat.

| Phase | Claude / Anthropic (`claude`) | Gemini / Google (`agy`) | GLM / Neuralwatt (`opencode`, attested `glm-5.2`) |
|---|---|---|---|
| B.1 | adversarial | alignment | peer |
| B.2 | adversarial | alignment | peer |
| D.2 | peer | adversarial | alignment |
| D.5 | verifier | verifier | verifier |

The D.2 rotation is normative. The GLM route must use the framework-owned
`neuralwatt-opencode-glm-5-2-v1` attestation profile. Gemini remains the Gemini
family when executed through AGY; AGY is a substrate, not a fourth family.
Provider/tool failure is recorded as a failed dispatch and a blocker unless the
user separately grants an explicit fallback or emergency waiver.

The post-D.5 loose falsification pass is separate from these certifying seats.
It uses the framework's frozen falsification stance without a harness template,
wrapper receipt, or certification claim. Any reproduced catch returns to D.4
and requires fresh D.5 verification.

## Phase ledger

| Phase | Owner / roster | Status | Required artifact or exit condition | Current evidence |
|---|---|---|---|---|
| 0 — scope lock and route preflight | Codex orchestrator | **complete** | Conforming manifest, exact scope, empty receipt inventory, stable user gate and I0 | Manifest conformance, review-seat check, doctor, scope parity, isolated full suite (`1439 passed`) |
| A — specification | Independent Codex spec-author worker | **complete** | Ten-section code-first spec with diagrams, exclusions, acceptance gates, and I0 reconciliation contract | `docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`; commit `25252a2` |
| B.1 — first design board | Claude adversarial; Gemini alignment; GLM peer; Claude Product (separate session) | **complete; final inventory verified 4/4** | Complete hash-bound dispatch bundle and four verdicts | Fresh final-inventory board against spec v1.4: Claude adversarial `Approve`, Gemini alignment `Concur`, GLM peer `Approve`, Claude Product `Approve`; bundle verification passes. The malformed first Gemini verdict and GLM evidence-cap attempt are preserved as failed captures without receipts. |
| B.2 — corrected-spec board | Same engineering seats; Claude Product (separate session) | **complete; final inventory verified 4/4** | Re-review corrected spec and I0 | Final v1.5 board: Claude adversarial `Approve`, Gemini alignment `Concur`, GLM peer `Approve`, Claude Product `Approve`; receipt-bound bundle verification passes and lifecycle verification now reports only the expected D.2/D.5 gaps. |
| B.3 — design consolidation | Codex fast-path under unanimous external board | **complete** | Canonical approved design verdict with every accepted finding and no hidden blocker | `B.3-verdict.md` consolidates the final B.1/B.2 artifacts, records zero preserved blockers, and carries independent Gemini dispatch verification; committed at `eeddf0f`. |
| C — code-first reconciliation | Independent Codex implementation-author worker | **in progress — layered falsification fixes green** | I0 and authorized deltas reconcile exactly to spec v1.5 | Independent attacks found and closed destination-recreation/rollback races, ambiguous recovery, root/lock rebinding, untyped outer-lock bypass, cleanup leaks, unsafe stub parent creation, symlinked workspace-root acceptance, the Windows post-open hardlink window, map timestamp churn, and shape-only provenance/O4/O5/child-manifest parity. The final targeted matrices (`461`, `124`, and `36` tests) and dirty-tree full suite (`1679 passed`) are green with byte-identical status; detached clean-snapshot replay and the C-close commit remain required. |
| D.1 — pre-review | Claude peer worker | pending | Non-certifying, non-author implementation/spec alignment review | — |
| D.2 — implementation board | Claude peer; Gemini adversarial; GLM alignment; Product if declared | pending | Complete hash-bound code-review bundles and verdicts, including Template-05 falsification | — |
| D.3 — code-review consolidation | Non-author consolidator selected by manifest | pending | Canonical blocker disposition | — |
| D.4 — fixes | Codex fix-author worker | pending | Per-blocker fix summary and regression evidence, or an explicit zero-blocker summary | — |
| D.5 — independent verification | Claude, Gemini, and GLM verifiers | pending | Each preserved blocker reproduced pre-fix and closed post-fix; strict receipts complete | — |
| Loose falsification review | Fresh, unbriefed model sessions | pending | Reproduce-and-loop any valid catch; report discovery result without certification language | Must run after final D.5 and before any later D.6 decision |
| D.6 — final approval | Maintainer/orchestrator | **not authorized in this run** | Requires a separate decision after D.5 and falsification | Out of requested scope |
| E — retrospective | Assigned only after D.6/merge authority | **not authorized in this run** | Post-approval lifecycle closeout | Out of requested scope |

## Halt rules

- Missing or invalid strict-P3 receipt: halt the phase and repair/re-dispatch.
- Reviewer route or provider failure: retain real evidence and halt unless the
  user explicitly authorizes a non-certifying fallback.
- Scope drift outside the manifest: halt; do not broaden the lease implicitly.
- A falsification reproduction or preserved board blocker: return through D.4
  and re-run all affected D.5 verification.
- Any attempt to translate branch-level review into per-issue certification,
  release readiness, or D.6 approval: halt as a boundary violation.
