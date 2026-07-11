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
| Phase C close snapshot (I1) | `05b090d53f7b0c9c4afdbb5fb23ab58cdfa01fa0` |
| D.4 functional-fix snapshot (I2) | `311b60b6e86abe6d0b5a7ac61e16d07049387707` |
| Post-falsification functional-fix snapshot (I3) | `859ecf778389aaa67f69146d7ae8cd2564445af5` |
| PR-feedback verification target | `388845cbd0cfc6ee8a9b2f61f7ebe5f14eff70a2` |
| Post-D.5 mechanical delta | Version surfaces bumped to `4.7.1`; `.coverage.*` ignored; no certification claim extends beyond `388845c` |
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

### Maintainer handoff — 2026-07-11

The maintainer subsequently authorized a fresh three-family D.5 retry against
`388845c`, D.6, and the exact provider-limited fallback label if the same
v2.0.1 defects persisted. That authorization permits a withheld D.6 and the
warning-only fallback record; it does not authorize merge, tag, publication,
release, issue closure, receipt fabrication, or a strict-P3 waiver.

## Certification boundary

In scope for this lifecycle:

- review the exact `bf91b42...b6f89d7` integration snapshot and the
  lifecycle-authorized Phase C successor frozen at `05b090d`;
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
- The original gate did **not** authorize D.6. The 2026-07-11 maintainer
  handoff later authorized a D.6 attempt, which is withheld rather than passed.
  Phase E, merge, tag, TestPyPI/PyPI publication, release, GitHub issue closure,
  and checkbox completion remain unauthorized.
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

I0 is immutable product-row provenance. Any successor implementation snapshot
must advance explicitly, the affected reviewed diff must be re-dispatched, and
this tracker must record the transition. Evidence may never be rebound silently
to a different tree.

### Phase-0 scope-audit recovery — D.4

The first post-fix changed-path gate found one manifest omission:
`ontos/commands/rename.py`. Approved spec §4.2 already governs every
CLI-supplied ID, strict D.2 Claude P-1 identifies `rename` as the violating
mutation command, and canonical D.3 CAN-ID-1 requires that exact file's repair.
The path is not excluded or forbidden, and the companion MCP and rename-test
paths were already allowlisted. The manifest therefore adds only this exact
file—no directory pattern or adjacent surface. This is a Phase-0 control-plane
correction, not a spec deviation or product-scope expansion.

Commit `311b60b` preceded the scope-gate discovery. Its history is preserved;
no receipt or commit was rewritten. The recovery record is
`docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-scope-audit-recovery.md`.
Changed-path scope and manifest conformance must pass again before D.5.

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
| B.1 — first design board | Claude adversarial; Gemini alignment; GLM peer; Claude Product (separate session) | **complete; strict inventory verified 4/4** | Complete hash-bound dispatch bundle and four verdicts | Fresh strict-inventory board against spec v1.5: Claude adversarial `Approve`, Gemini alignment `Concur`, GLM peer `Approve`, Claude Product `Approve`; `verify-family-dispatch --require-complete` passes 4/4. Earlier inventories and failed attempts remain preserved as non-certifying history. |
| B.2 — corrected-spec board | Same engineering seats; Claude Product (separate session) | **complete; strict inventory verified 4/4** | Re-review corrected spec and I0 | Fresh strict-inventory v1.5 board: Claude adversarial `Approve`, Gemini alignment `Concur`, GLM peer `Approve`, Claude Product `Approve`; `verify-family-dispatch --require-complete` passes 4/4. |
| B.3 — design consolidation | Codex fast-path under unanimous external board | **complete** | Canonical approved design verdict with every accepted finding and no hidden blocker | `B.3-verdict.md` consolidates the final B.1/B.2 artifacts, records zero preserved blockers, and carries independent Gemini dispatch verification; committed at `eeddf0f`. |
| C — code-first reconciliation | Independent Codex implementation-author worker | **complete at I1** | I0 and authorized deltas reconcile exactly to spec v1.5 | I1 `05b090d53f7b0c9c4afdbb5fb23ab58cdfa01fa0`; independent attacks closed C-FZ-1–10. Targeted matrices: `461`, `124`, and `36` passed. Full suite: `1679 passed`; detached I1 replay: `1679 passed`, with porcelain empty before and after. Registry local/live parity, 433-path base-SHA scope, Python 3.9 grammar, map double-generation, and `git diff --check` pass. |
| D.1 — pre-review | Claude peer worker | **complete — Approve** | Non-certifying, non-author implementation/spec alignment review | Wrapper-dispatched Claude peer review at `D.1-claude-peer.md`; verified bundle 1/1; zero blocking and zero should-fix findings. |
| D.2 — implementation board | Claude peer; Gemini adversarial; GLM alignment; Claude Product | **complete; strict inventory verified 4/4** | Complete hash-bound code-review bundle and verdicts, including Template-05 falsification | Fresh strict board: Claude Peer `Request changes`, Gemini adversarial `Request changes`, GLM alignment `Approve`, Claude Product `Approve`; blind-review and family-dispatch verification pass. Strict lifecycle now reports only the three expected D.5 receipt gaps. Earlier attempt inventory/captures remain preserved without editing or reconstruction. |
| D.3 — code-review consolidation | Independent Codex meta-consolidator | **complete — Needs Fixes** | Canonical blocker disposition | `D.3-verdict.md`; zero preserved blockers and six directly reproduced should-fix findings: CAN-ACT-1/2, CAN-CP-1/2/3, CAN-ID-1. Strict D.2 dispatch recheck and Gemini blind-packet verification pass; independent Gemini dispatch hash attestation matches. |
| D.4 — fixes | Codex fix-author | **functional fixes complete at I3; halted on D4-INFRA-1** | Per-ID fix summary, test-first evidence, scope proof, and honest framework-blocker disposition | I2 closes all six D.3 findings. Loose falsification added LF-ID-1/LF-CP-1; I3 `859ecf7` closes both. Full suite: `1725 passed`. Framework v2.0.1 EH-15-A remains fail-open/unavailable, so D.4 is not certified. |
| D.5 — independent verification | Claude, Gemini, and GLM verifiers | **provider-limited fallback complete; strict P3 not certified** | Fresh current-head artifacts/receipts or preserved provider blockage; strict gates remain fail-closed | At exact target `388845c`, Claude and GLM directly verified the current head (`104` focused; `1740` full) and landed genuine round-2 artifacts/receipts. Gemini's genuine retry failed exit `55` under the retired individual client. EH-15-A, receipt-schema drift, and GLM receipt-source/backlink rejection persist. The final strict verifier rejects the declared fallback mode; the fallback verifier reports `status=provider_limited_fallback_incomplete`. See `D.5-orchestrator-status.md`. |
| Loose falsification review | Fresh Codex session; provider attempts recorded separately | **complete — two findings reproduced and fixed at I3** | Reproduce-and-loop any valid catch; report discovery result without certification language | `loose-falsification-codex.md`; five pre-fix failures, five post-fix passes; complete suite `1725 passed`. |
| D.6 — final approval | Maintainer/orchestrator | **executed — WITHHELD** | A passing gate requires strict-P3 or a mechanically complete framework fallback; neither is available | `final-approval.md` passes only the framework's `--allow-gated`/withheld shape. It contains no passing gate rows and defers every release action. |
| E — retrospective | Assigned only after a passing D.6/merge authority | **not run** | Post-approval lifecycle closeout | D.6 is withheld; Phase E is not authorized. |

## Merge and rollback recommendation

Recommend **split before release/merge**. The closeout tree spans 636 committed
paths across the registry's v4.7.1, v4.8.0, and v4.9.0 programs;
13 implementation paths have multi-release ownership. There is no honest
whole-file cherry-pick for the hotfix, so extraction requires hunk-level
decomposition plus fresh tests and lifecycle review. Put the `4.7.1` release
metadata on that extracted hotfix slice.

If the maintainer nevertheless chooses a whole-PR merge, require a merge commit
and record the atomic rollback command `git revert -m 1 <merge-commit>`. Avoid a
rebase merge: it destroys the only clean whole-PR revert boundary.

### D.1 minor dispositions

- `P-1` is an acknowledged taxonomy-fit nit: `E_LOG_EXISTS` continues to map
  to exit `1` by the approved public compatibility contract; no Phase C code
  change is warranted.
- `P-2` requests an optional concurrency comment. The exclusive-create
  docstring, O_EXCL implementation, and collision regressions already bind the
  safety mechanism; no implementation change or preserved blocker is needed.

## Halt rules

- Missing or invalid strict-P3 receipt: halt the phase and repair/re-dispatch.
- Reviewer route or provider failure: retain real evidence and halt unless the
  user explicitly authorizes a non-certifying fallback.
- Scope drift outside the manifest: halt; do not broaden the lease implicitly.
- A falsification reproduction or preserved board blocker: return through D.4
  and re-run all affected D.5 verification.
- Any attempt to translate branch-level review into per-issue certification,
  release readiness, or D.6 approval: halt as a boundary violation.
