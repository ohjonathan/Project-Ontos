---
id: project_ontos_audit_remediation_release_line_tracker
type: tracker
status: complete
meta_cycle_id: project-ontos-audit-remediation-2026-07
owner: meta-orchestrator (claude; meta-cycle project-ontos-audit-remediation-2026-07)
depends_on: []
completed: 2026-07-13
---

# Release-line tracker — project-ontos-audit-remediation-2026-07

Cross-deliverable custody artifact for the audit-remediation meta-cycle, authored under
authority M-A3 (coordinate custody across deliverables) by the meta-orchestrator session
opened from the kickoff at
`docs/handoffs/2026-07-03-audit-remediation-meta-orchestrator-kickoff.md`. This file hosts
two of the meta-cycle's expected outputs (spec §3.7): **O5** (cross-deliverable scope-lock
manifest) and **O4** (cross-deliverable verification ledger). It spans all 12 remediation
deliverables (#146–#157) and is therefore meta-cycle-owned; per-deliverable trackers
(`docs/trackers/project-ontos-audit-<slug>.md`) remain owned by their own Codex
Orchestrators (forbidden path F-2 / non-trigger N6).

## O5 — Cross-deliverable scope-lock manifest

**What this allowlist is — and is not.** The table below grants write **leases to
per-deliverable Codex Orchestrator sessions**, one deliverable at a time per shared path.
It grants **nothing** to the meta-cycle itself: the meta-cycle's own write allowlist
remains kickoff §4 verbatim (meta-cycle handoffs, this tracker file, meta-cycle proposals,
and the meta-cycle's own review-board entries) and includes **none** of the product-code
paths below. Listing a product path here is a lease assignment, not a self-grant —
treating it otherwise is an F-1 violation and halts under S2 + S7.

**Forbidden-paths preflight (spec §3.5.1 F-1..F-4), performed 2026-07-03 before any
meta-cycle write:** the meta-cycle's own allowlist (kickoff §4) contains no product-code
path (F-1 ✅), no per-deliverable tracker path (F-2 ✅), no other deliverable's
review-board path (F-3 ✅), and no other deliverable's D.6 gate path (F-4 ✅). **PASS.**

### File-ownership allowlist (write leases per shared path)

| Shared path | Deliverables touching it | Lease order / policy |
|---|---|---|
| `ontos/core/schema.py` | #146 | Exclusive to #146 until v4.7.1 ships. |
| `ontos/core/frontmatter.py`, `ontos/core/frontmatter_edit.py`, `ontos/core/frontmatter_repair.py` | #146, #151, #152 | #146 first (v4.7.1, minimal call-site changes only); then #151, then #152 (both v4.8.0, dispatched only after #150 lands). |
| `ontos/io/yaml.py` | #146, #151 | #146 first (adopts the unused `dump_yaml`); #151 consumes — does not rewrite — #146's serializer. |
| `ontos/core/body_refs.py` | #151, #152, #157 | #151 → #152 (v4.8.0) → #157 (v4.9.0). |
| `ontos/cli.py` | #154, #155 | Serialized inside v4.9.0; #154 (exit-code/envelope) before #155 (command table). |
| `ontos/mcp/` (package proper) | #146, #153, #154 | #146 leases only `ontos/mcp/writes.py` (re-parse assertion at the `promote_document` write path, v4.7.1) and releases it before #153 then #154 (v4.8.0/v4.9.0). Note: #147 does **not** lease `ontos/mcp/`; its lease is `ontos/core/mcp_shared.py`, `ontos/core/cursor_mcp.py`, `ontos/commands/doctor.py`, `SECURITY.md` (v4.7.1). |
| `ontos/commands/promote.py`, `ontos/commands/migrate.py` | #146, #152 | #146 first (re-parse assertion at call sites); #152 later routes both through `frontmatter_edit` (v4.8.0). |
| `.pre-commit-config.yaml`, `.ontos/scripts/` | #156 | Exclusive to #156 (v4.9.0). |
| `tests/` | #150 + all deliverables | #150 owns the characterization-test net (v4.8.0, before #151/#152/#153). Every other deliverable adds **only its own named regression file** (named in its dispatch prompt); no edits to another deliverable's tests. |

### Serialization rule

One deliverable holds the lease on a shared path at a time. Lease order derives from the
dependency edges below (kickoff §3). A Codex Orchestrator that finds its Phase-C path
leased to another in-flight deliverable **halts Phase C and routes back to the
meta-cycle** (deliverable-level S2); it does not negotiate directly with the sibling
session.

## O4 — Cross-deliverable verification ledger

Lifecycle states: `not started → Phase 0 → A → B.1/B.3 → C → D.1–D.6 → E → closed`.
Evidence modes: `strict-P3` | `provider-limited` |
`provider-limited-governance-waiver` | `—`. Release outcome values are
`strict_p3_review_complete`, `provider_limited_fallback_complete`, or
`provider_limited_governance_waiver_released`; certification and release-action caveats
are recorded separately so later maintainer action does not rewrite historical review
evidence.

| deliverable_id | Issue | Release | Lifecycle status | Evidence mode | Final status string | Updated |
|---|---|---|---|---|---|---|
| project-ontos-audit-serializer-corruption | #146 | v4.7.1 | **shipped / closed** — P0 serializer and canonical string-ID validation shipped from merge `19868ad` in tag `v4.7.1`. | provider-limited; strict P3 not certified; D.6 withheld | `provider_limited_fallback_complete` | 2026-07-12 |
| project-ontos-audit-doctor-rce | #147 | v4.7.1 | **shipped / closed** — exact managed-launcher argv gate and SECURITY.md correction shipped from merge `19868ad` in tag `v4.7.1`; no product residual remains. | provider-limited, label-only; strict P3 not certified; D.6 withheld | `provider_limited_fallback_complete` | 2026-07-12 |
| project-ontos-audit-relN-quick-wins | #148 | post-v5 backlog | **open / transferred** — broad consolidation remains; received #150's test-hygiene tail and retains exact TestPyPI provenance hardening after the v5 smoke resolved 4.7.1. | — | — | 2026-07-13 |
| project-ontos-audit-relN-sweep | #149 | post-v5 backlog | **open / transferred** — broad docs/dead-code program remains; received #156's archive extraction, generated-artifact churn, and consolidation-policy tail. | — | — | 2026-07-13 |
| project-ontos-audit-characterization-tests | #150 | v5.0.0 | **shipped / closed** — characterization and golden safety net shipped; 1,556-test release gate passed; residual hygiene transferred to #148. | provider-limited governance waiver; current-head strict-P3/provider receipts not certified; D.6 withheld | `provider_limited_governance_waiver_released` | 2026-07-13 |
| project-ontos-audit-parser-consolidation | #151 | v5.0.0 | **shipped / closed** — canonical fence-aware frontmatter loader and fallback-parser retirement shipped. | provider-limited governance waiver; current-head strict-P3/provider receipts not certified; D.6 withheld | `provider_limited_governance_waiver_released` | 2026-07-13 |
| project-ontos-audit-writepath-bodyref | #152 | v5.0.0 | **shipped / closed** — surgical writes, physical link lines, and aliased/heading wikilink handling shipped. | provider-limited governance waiver; current-head strict-P3/provider receipts not certified; D.6 withheld | `provider_limited_governance_waiver_released` | 2026-07-13 |
| project-ontos-audit-mcp-dispatch-rename | #153 | v5.0.0 | **shipped / closed** — unified MCP dispatch, lock-before-plan, durable rename journal, and scoped recovery shipped. | provider-limited governance waiver; current-head strict-P3/provider receipts not certified; D.6 withheld | `provider_limited_governance_waiver_released` | 2026-07-13 |
| project-ontos-audit-exitcode-envelope | #154 | v5.0.0 | **shipped / closed** — schema-4 result envelope, exit taxonomy, and noninteractive JSON behavior shipped. | provider-limited governance waiver; current-head strict-P3/provider receipts not certified; D.6 withheld | `provider_limited_governance_waiver_released` | 2026-07-13 |
| project-ontos-audit-cli-command-table | #155 | v5.0.0 | **shipped / closed** — declarative command registry, alias parity, and global-flag normalization shipped. | provider-limited governance waiver; current-head strict-P3/provider receipts not certified; D.6 withheld | `provider_limited_governance_waiver_released` | 2026-07-13 |
| project-ontos-audit-precommit-rewire-slim | #156 | v5.0.0 | **shipped / closed** — package hook/CI rewire and complete 43-file `.ontos/scripts/` retirement shipped; broader slimming tail transferred to #149. | provider-limited governance waiver; current-head strict-P3/provider receipts not certified; D.6 withheld | `provider_limited_governance_waiver_released` | 2026-07-13 |
| project-ontos-audit-graph-traversal | #157 | v5.0.0 | **shipped / closed** — iterative traversal and filesystem-sensitive path identity shipped. | provider-limited governance waiver; current-head strict-P3/provider receipts not certified; D.6 withheld | `provider_limited_governance_waiver_released` | 2026-07-13 |

**Update discipline.** Only the meta-cycle session updates this ledger (as deliverables
report Phase transitions and terminal statuses). Per-deliverable trackers stay
per-deliverable-owned (F-2).

### v4.7.1 release outcome

- #146 and #147 are shipped and closed. Release evidence is main merge `19868ad`, annotated
  tag `v4.7.1`, the green tag-triggered publish workflow, and the published GitHub release.
- Outcome: `provider_limited_fallback_complete`. This is a conscious maintainer release,
  not strict-P3 certification: strict P3 was not certified and D.6 remained withheld.
- **Template-07 release actions, authorized by Jonathan on 2026-07-12:** `git tag`, tag
  push (triggering PyPI), GitHub release publication, and closure of the v4.7.1-program
  issues changed from **maintainer-deferred** to **performed in this session, authorized
  2026-07-12**. No v5.0.0 / #161 release action was authorized or performed.
- #148 and #149 remain open under the v4.8.0 consolidation milestone.

### v5.0.0 release outcome

- #150–#157 shipped from [PR #163](https://github.com/ohjonathan/Project-Ontos/pull/163)
  and are closed. The merge and annotated `v5.0.0` tag target
  `f8c148be0fbf2810cd94ce75fa69834a3e19166c`.
- The tag-triggered [publish workflow
  29291879298](https://github.com/ohjonathan/Project-Ontos/actions/runs/29291879298)
  passed tests, version validation, build, TestPyPI publication, and trusted PyPI
  publication. [GitHub release
  v5.0.0](https://github.com/ohjonathan/Project-Ontos/releases/tag/v5.0.0) and
  [PyPI 5.0.0](https://pypi.org/project/ontos/5.0.0/) are published.
- Published SHA-256: wheel
  `c5ecdf6cc021b4f6f3cd05f4543d407713f392be7d44615a7903b17227738639`; sdist
  `e673b98cb137e581cc2e48722b499a22ad972afe121038e1f6217a1d109fa800`.
  TestPyPI and PyPI expose identical hashes.
- The workflow's unpinned TestPyPI smoke installed 4.7.1 instead of asserting 5.0.0.
  This is not recorded as exact-version certification; the hardening and #150 test-hygiene
  tail moved to #148. #156's archive/churn/consolidation tail moved to #149.
- Outcome: `provider_limited_governance_waiver_released`. Current-head strict-P3 and
  provider-limited receipt verification did not complete; D.6 remains **WITHHELD**. This
  is not llm-dev v2.0.1 certification, and historical evidence was not rebound to the
  release head.
- **Template-07 release actions, separately authorized by Jonathan on 2026-07-13:** PR
  readiness/merge, annotated tag and tag push, tag-triggered trusted publication, GitHub
  release, and #150–#157 closure were performed. The public authorization record is
  [PR comment
  4963625974](https://github.com/ohjonathan/Project-Ontos/pull/163#issuecomment-4963625974).
- The July release meta-cycle is complete by explicit residual-custody transfer. #148 and
  #149 remain open in the post-v5 backlog, and epic #158 remains open as their
  custody/control-plane tracker; `R2-control-plane-parity-1` is not claimed complete.

## Dependency edges enforced at dispatch (kickoff §3)

- #146 and #147 are independent and dispatchable immediately (v4.7.1).
- #150 (characterization test net) MUST complete before #151/#152/#153 are dispatched —
  the tests bracket the refactors (audit §5 "tests before refactors").
- #154 (exit-code/envelope) and #156 (repo slimming) come last; #156's pre-commit/CI
  rewire is a prerequisite for retiring the legacy fork and unblocks the "pre-commit
  fails on main" condition.

## Change log

- 2026-07-03 — initialized (O5 + O4) by the meta-orchestrator kickoff session
  (meta-cycle `project-ontos-audit-remediation-2026-07`).
- 2026-07-09 — O4 ledger reconciled against actual deliverable state after the 2026-07-03
  Codex dispatches ran. #147 advanced `not started → E complete` (provider-limited, D.6
  with caveat); #146 advanced `not started → B.1 STALLED` (provider-limited authorized,
  Phase C never started, P0 still unfixed). Active-blockers section added. Rows #148–#157
  remain `not started` and are unchanged.
- 2026-07-12 — released v4.7.1 from merge `19868ad` via annotated tag `v4.7.1`; the
  tag-triggered publish workflow passed and PyPI/GitHub releases were published. Closed
  #146/#147 with no product residual, re-scoped #148/#149 to v4.8.0, and recorded outcome
  `provider_limited_fallback_complete` with strict P3 not certified and D.6 withheld.
  Template-07 tag, tag-push, GitHub-release, and v4.7.1 issue-closure rows were performed
  in this session under Jonathan's 2026-07-12 authorization.
- 2026-07-13 — released v5.0.0 from merge `f8c148b` through trusted-publisher workflow
  `29291879298`; verified matching TestPyPI/PyPI artifact hashes, published the GitHub
  release, and closed #150–#157. Recorded outcome
  `provider_limited_governance_waiver_released` with current-head strict/provider receipt
  verification incomplete and D.6 withheld. Transferred residual custody to #148/#149,
  updated epic #158, and closed meta-cycle `project-ontos-audit-remediation-2026-07`
  without claiming the unresolved control-plane parity row.
