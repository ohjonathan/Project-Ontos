---
id: project_ontos_v5_remediation_board_hygiene_proposal
type: spec
status: proposed
created: 2026-07-15
owner: Project Ontos Maintainers
depends_on:
  - project_ontos_v5_remediation_release_plan_proposal
  - project_ontos_audit_remediation_release_line_tracker
  - project_ontos_v5_remediation_phase_0_live_issue_audit
concepts:
  - proposals
  - workflow
  - external-review
---

# Project Ontos v5 Remediation Board Hygiene Proposal

## 1. Decision Requested

Return the exact Template 16 verdict **Proceed to Phase A** if this proposal is
an appropriately bounded way to reconcile the public GitHub issue board with
the already-approved v5 remediation program.

Approval would authorize a Phase A specification for the board transaction. It
would not authorize an issue edit, issue creation, issue closure, label or
milestone change, product-code change, release, merge, or publication. This
scaffolding pull request makes no GitHub issue mutation.

## 2. Parent Authority and Fixed Boundary

The merged
`project_ontos_v5_remediation_release_plan_proposal` received the terminal
parent disposition **Split into multiple proposals**. Its Phase 0 route
authorizes this independent child to propose the board-hygiene work described
in parent §§8, 10, 21, and 23. This child must receive its own non-author Pre-A
decision before Phase A begins.

The inherited release boundary is fixed:

> Project Ontos completes the approved feature and remediation program in v5;
> v6.0.0 removes only the exact eleven deprecated path-compatibility names.

This child cannot reinterpret that boundary. In particular, it cannot close
issue #149 early, describe unshipped successor work as complete, defer full
issue #178 delivery to v6, or use issue cleanup to broaden the v6 break.

## 3. Evidence and Problem

### 3.1 The public board is not the same thing as implementation state

The parent proposal reconciled current-main source inspection, released audit
evidence, the 2026-07-10 revalidation snapshot, and the live issue bodies. The
remaining problem is public custody, not an assertion that the product work is
already done. GitHub issues are externally visible coordination contracts; a
stale title, checklist, milestone, or closure statement can make released,
deferred, and successor work indistinguishable.

The 2026-07-15 read-only Phase 0 audit confirmed that all nine tracked issues
remain open. It also confirmed that #149, #158, and #165 still require the
approved reconciliation and that #173–#178 still have no labels or milestones.
No live issue has become invalid or already closed since the parent decision.

### 3.2 Issue #149 mixes shipped work with one retained compatibility promise

The patch-safe work previously carried by #149 shipped through v5.0.2. The
remaining issue is the promised v6 deletion of exactly eleven public names,
plus residual log-path and archive concerns that need their own custody. The
live wording observed by the parent still treated PR #170 as draft/merge
pending after it had merged and shipped. A board-only transaction should:

- record the shipped patch state without rewriting its historical severity;
- enumerate the exact eleven remaining compatibility names;
- state that those names stay available throughout v5;
- record PR #170 as merged and released;
- move the log-path and archive residuals into separately owned issues; and
- keep #149 open under a v6 milestone until published-artifact verification.

### 3.3 Issue #158 is a coordination tracker, not proof that successors shipped

The parent found that #158 needed the v5.0.2/#148 provenance recorded, its
arithmetic moved from 10/12 to 11/12, and explicit successor custody for #149,
#165, and the extracted residuals. It can close when the coordination transfer
is complete, but the closure text must not imply that any successor issue is
fixed or released.

### 3.4 Remaining open issues need calibrated labels and milestones

The parent also identified bounded board corrections for #165 and #173–#178:

- #165 should be `P1-high` unless an explicit severity-downgrade rationale is
  approved, and its body should separate offline deterministic parity from
  authenticated live parity;
- #176 should be a `bug`, `P1-high`, and targeted to v5.0.3;
- #177 needs its Markdown-resolution wording corrected;
- #174 needs `finding_key` represented in its contract;
- #175 must not lose optional cross-device CAS custody through an implicit
  checkbox deletion; and
- #178 should record both v5.0.3 slices—the built-in alias and required-version
  downgrade preflight—while staying open for complete v5.1 vocabulary
  delivery.

These are board truth corrections. They do not amend implementation contracts
silently; any substantive change beyond the parent authority must return for
separate approval.

## 4. Goals

1. Make #149 distinguish shipped patch work, extracted residuals, and the exact
   promised v6 deletion.
2. Close #158 only after its arithmetic, provenance, and successor-custody
   statement are accurate.
3. Create durable issue custody for the log-path and archive residuals.
4. Normalize the parent-authorized labels, milestones, and wording for #165
   and #173–#178.
5. Preserve every open acceptance criterion unless it is completed by released
   evidence or transferred through an explicit source/destination transaction.
6. Produce before/after evidence sufficient to audit every live board write.
7. Keep the entire deliverable product-code-free.

## 5. Non-Goals

This child does not:

- implement #149, #165, or #173–#178;
- remove or change a public compatibility name;
- edit source, tests, workflows, package metadata, release notes, or published
  artifacts;
- migrate or delete internal archive/history data;
- create a dynamic vocabulary or treat the safe alias slice as closure of
  #178;
- close #165, #173, #174, #175, #176, #177, or #178;
- decide the technical design of any successor child;
- transfer #175 optional-CAS criteria without an accepted destination issue;
  or
- make a GitHub write during this scaffolding proposal.

## 6. Owned, Composed, and Forbidden Scope

### 6.1 Locally owned lifecycle artifacts

This child owns only its proposal, future specification, tracker, review
evidence, retrospective, manifest, and orchestrator-generated Ontos map/agent
updates. It does not own the audit release-line ledger rendered by #165.

### 6.2 Later live-board write scope

Only after independent Pre-A approval and the full lifecycle gate, the child
may own the following live GitHub transaction:

- update #149 and #158;
- create the two residual issues in §7.3;
- apply the parent-authorized label, milestone, and wording corrections to
  #165 and #173–#178; and
- add reciprocal source/destination links for every custody transfer.

The Phase A spec must turn this list into an exact before/after plan. No issue
outside this list may be edited by inference.

### 6.3 Composed evidence

The child reads, but does not own:

- the merged parent proposal;
- the Fable audit and Codex revalidation;
- the 2026-07-15 Phase 0 live-issue audit;
- released v5.0.1/v5.0.2 evidence;
- the historical audit release-line tracker; and
- fresh live GitHub issue snapshots captured immediately before any approved
  transaction.

### 6.4 Forbidden scope

Product code, tests, workflows, package metadata, release artifacts, internal
archives, session logs, and the #165 registry/renderer are forbidden. GitHub
writes are forbidden until Phase C and explicit operator authority.

## 7. High-Level Contract

### 7.1 Plan, review, apply, verify

The later specification should define one bounded transaction with four
observable stages:

1. **Snapshot:** record issue number, state, title, body digest, labels,
   milestone, and relevant checklist/custody rows.
2. **Plan:** produce an exact human-reviewable before/after operation list with
   no writes.
3. **Apply:** after approval, execute only operations whose preconditions still
   match the snapshot; halt on drift instead of overwriting concurrent edits.
4. **Verify:** re-read every target and compare the live result to the plan,
   recording created issue numbers and reciprocal links.

The check/plan path must be offline-safe with respect to writes: missing
credentials may prevent a fresh live snapshot, but can never turn a check into
an edit. The apply path must require authenticated, explicitly granted write
authority.

### 7.2 Issue-by-issue disposition

| Issue | Required board result | Closure rule |
|---|---|---|
| #149 | Record v5.0.2 patch completion, exact eleven-name v6 remainder, PR #170 merged/released, extracted residual links, `audit` + `P2-hygiene`, and v6 milestone | Remains open until v6 artifact verification |
| #158 | Record #148/TestPyPI provenance, 11/12 coordination arithmetic, and successor custody for #149, #165, and both residuals | May close only with wording that successor work remains open |
| #165 | Prefer `P1-high` or record an approved downgrade rationale; separate offline and authenticated parity | Remains open until all 100 IDs and both parity tiers pass |
| #173 | Apply enhancement/priority/milestone truth from the parent | Remains open for v5.1 delivery |
| #174 | Add `finding_key` contract clarity and v5.2 custody | Remains open for v5.2 delivery |
| #175 | Preserve same-device/core and optional-CAS custody; transfer optional CAS only to an accepted successor | Remains open absent complete delivery or explicit transfer |
| #176 | Apply `bug`, `P1-high`, and v5.0.3 milestone | Closes only after published-wheel reproduction |
| #177 | Correct Markdown-resolution wording and v5.2 custody | Remains open for classifier/policy delivery |
| #178 | Record both v5.0.3 slices—the built-in alias and required-version downgrade preflight—and v5.1 complete-vocabulary custody | Stays open until the complete cross-surface feature ships |

### 7.3 Required residual issues

The transaction creates exactly these two issues, with acceptance criteria and
reciprocal links back to #149 and #158:

1. `[Bug] Align contributor log writes and consolidation with configured logs_dir`
2. `[Chore] Classify and extract eligible internal archive material; repair links`

The first owns active log-path parity and the seven log-related #149 wrapper
delegations. The second owns classification/extraction only after the log-path
authority is explicit; it may not infer that the still-canonical internal
archive/history ledger is frozen or ready for deletion.

If #175's optional cross-device CAS work is transferred, it requires a third,
separately accepted successor with a reciprocal checklist transaction. That is
not one of the two mandatory #149 residuals and must not be created or used as
closure evidence speculatively.

## 8. Issue Custody Rules

Every transferred criterion must have:

- one source issue and one destination issue;
- the exact criterion text or stable identifier;
- a source-side link naming the new owner;
- a destination-side link naming the source;
- a transfer timestamp/evidence reference; and
- no interval in which both issues claim closure or neither issue owns the
  work.

A source checkbox may be marked transferred only after the destination exists
and accepts the criterion. A closed coordination tracker may say “custody
transferred”; it may not say “fixed” unless released evidence supports that
claim.

## 9. Dependencies and Sequencing

1. The parent split verdict and this scaffold establish Phase 0 only.
2. A non-author reviewer must return **Proceed to Phase A**.
3. Phase A captures fresh live issue state and freezes the exact plan.
4. Product and technical review verify wording, custody, and drift behavior.
5. Only an authorized Phase C apply may write to GitHub.
6. Verification records the final state before #158 is closed.
7. #165 consumes the reconciled board as its live-parity baseline.

The #165 registry may be designed while v5.0.3 work proceeds, but its
authenticated live parity should observe the post-hygiene board. This proposal
declares no concurrent sibling lifecycle; any future parallel pair requires a
separate reciprocal manifest/handoff decision.

## 10. Safety and Rollback

- The default operation is a no-write plan.
- Every write is preconditioned on an unchanged snapshot digest.
- A mismatch halts and requests a new plan; it never force-overwrites.
- Created issues are never deleted as rollback. If wording is wrong, correct it
  transparently and preserve the audit trail.
- Updated issue bodies retain a recorded pre-change copy in lifecycle evidence.
- Partial application halts further writes and reports applied, skipped, and
  pending operations separately.
- #158 is closed last, after every successor link verifies.
- No rollback may erase a legitimate concurrent human edit.

## 11. Acceptance Outline

Before the child can claim completion:

- [ ] A non-author Template 16 verdict authorizes Phase A.
- [ ] The Phase A spec freezes exact before/after operations and a fresh live
      snapshot.
- [ ] #149 lists the exact eleven v6 names and stays open.
- [ ] Both mandatory residual issues exist with reciprocal custody links.
- [ ] #158 records 11/12 coordination, released provenance, and open successor
      custody before closing.
- [ ] #165 and #173–#178 match the parent-authorized label, milestone, wording,
      and custody plan.
- [ ] Any #175 optional-CAS transfer has an accepted reciprocal destination;
      otherwise #175 stays open with the criterion intact.
- [ ] Check/plan mode performs no GitHub write.
- [ ] Apply refuses stale preconditions and post-apply verification matches the
      approved plan.
- [ ] No repository product, test, workflow, package, release, or archive path
      changes under this child.

## 12. Unknowns

| Unknown | Classification | Required treatment |
|---|---|---|
| Exact current label and milestone names/IDs at child branch time | `resolve-during-A` | Capture through fresh authenticated reads; do not reuse the parent's dated snapshot blindly |
| Whether #165 should retain P1 or use a downgrade rationale | `resolve-during-A` | Preserve P1 unless maintainers approve and record a concrete rationale |
| Whether #175 optional CAS already has an accepted successor | `must-resolve-pre-A` for any transfer operation | Exclude the transfer from the plan unless an accepted destination and reciprocal criteria exist |
| Exact body formatting and checklist locations | `resolve-during-A` | Preserve unrelated human content and use stable anchors/digests |
| Product implementation details of successor issues | `defer` | Each successor owns its own proposal/spec lifecycle |

None of these unknowns authorizes a broader issue set or product mutation.

## 13. Review Questions

### 13.1 Product lens

1. Will a reader understand what shipped, what remains, and who owns it without
   reading internal lifecycle artifacts?
2. Does closing #158 communicate coordination completion without implying that
   successor work is fixed?
3. Are two mandatory residual issues simpler and clearer than retaining their
   unrelated criteria inside #149?
4. Are priority and milestone changes calibrated to user impact and release
   order?
5. Is the planned transaction operationally safe for concurrent maintainer
   edits?

### 13.2 Technical lens

1. Does every transfer have complete, reciprocal, non-duplicated custody?
2. Is the exact eleven-name v6 boundary preserved mechanically and textually?
3. Can plan/apply/verify detect live drift without overwriting it?
4. Does #165 receive a coherent post-hygiene live parity baseline?
5. Are repository scope gates sufficient to prove that the child is board-only?

## 14. Exact Template 16 Verdict Set

The non-author reviewer must choose exactly one:

- **Proceed to Phase A** — the direction and boundary are ready for a detailed
  board-transaction specification.
- **Revise and re-review** — fixable proposal gaps require another Pre-A pass.
- **Split into multiple proposals** — the proposed board transaction still
  combines independently governed directions.
- **Abandon direction** — the board reconciliation is unnecessary or
  fundamentally unsound.

No abbreviated verdict is valid lifecycle evidence.

## 15. Recommendation

Return **Proceed to Phase A**. The parent has already decided the release and
issue dispositions; this child supplies the missing public-custody transaction
without implementing or claiming completion of any successor. The next action
after approval is an exact, drift-aware Phase A plan—not a live GitHub write.
