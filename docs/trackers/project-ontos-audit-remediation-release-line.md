---
id: project_ontos_audit_remediation_release_line_tracker
type: tracker
status: active
meta_cycle_id: project-ontos-audit-remediation-2026-07
owner: meta-orchestrator (claude; meta-cycle project-ontos-audit-remediation-2026-07)
depends_on: []
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
Evidence modes: `strict-P3` | `provider-limited` | `—`. Terminal status strings (exact,
per Template 24 §10.5 fields 4/5): `strict_p3_review_complete` or
`provider_limited_fallback_complete; strict P3 not certified; maintainer release actions
deferred`.

| deliverable_id | Issue | Release | Lifecycle status | Evidence mode | Final status string | Updated |
|---|---|---|---|---|---|---|
| project-ontos-audit-serializer-corruption | #146 | v4.7.1 | **B.1 — STALLED** (Phase 0 ✅, A ✅; B.1 partial: claude-sonnet peer complete, gpt halted, gemini no result). Phase C not started — **the P0 is still unfixed**. | provider-limited (authorized 2026-07-03) | — (no terminal status; deliverable incomplete) | 2026-07-09 |
| project-ontos-audit-doctor-rce | #147 | v4.7.1 | **E — session-declared complete, NOT mechanically verifiable** (Phase 0→E; D.6 with caveat). Hardened again 2026-07-09 after external review found the launcher gate bypassable. | provider-limited, **label-only** (no wrapper receipts) | session emitted `provider_limited_fallback_complete; strict P3 not certified; maintainer release actions deferred`, but `verify-lifecycle --mode provider-limited-fallback` does **not** certify it | 2026-07-09 |
| project-ontos-audit-relN-quick-wins | #148 | v4.7.1 | not started | — | — | 2026-07-03 |
| project-ontos-audit-relN-sweep | #149 | v4.7.1 | not started | — | — | 2026-07-03 |
| project-ontos-audit-characterization-tests | #150 | v4.8.0 | not started | — | — | 2026-07-03 |
| project-ontos-audit-parser-consolidation | #151 | v4.8.0 | not started (blocked on #150) | — | — | 2026-07-03 |
| project-ontos-audit-writepath-bodyref | #152 | v4.8.0 | not started (blocked on #150) | — | — | 2026-07-03 |
| project-ontos-audit-mcp-dispatch-rename | #153 | v4.8.0 | not started (blocked on #150) | — | — | 2026-07-03 |
| project-ontos-audit-exitcode-envelope | #154 | v4.9.0 | not started | — | — | 2026-07-03 |
| project-ontos-audit-cli-command-table | #155 | v4.9.0 | not started | — | — | 2026-07-03 |
| project-ontos-audit-precommit-rewire-slim | #156 | v4.9.0 | not started | — | — | 2026-07-03 |
| project-ontos-audit-graph-traversal | #157 | v4.9.0 | not started | — | — | 2026-07-03 |

**Update discipline.** Only the meta-cycle session updates this ledger (as deliverables
report Phase transitions and terminal statuses). Per-deliverable trackers stay
per-deliverable-owned (F-2). A ledger row's "Final status string" is filled only with one
of the two exact terminal strings above, copied verbatim from the deliverable's final
response.

### Active blockers (as of 2026-07-09)

- **#146 (P0) is stalled and is the critical path for v4.7.1.** Its B.1 review board never
  closed: the strict GPT-family dispatch halted (the Codex substrate rejects `gpt-5`,
  `gpt-4o`, `gpt-4.1`, `gpt-4-turbo`, `gpt-5-codex` for this ChatGPT account), and the
  Gemini dispatch has a `B.1-gemini-dispatch-intent.yaml` with **no result and no review
  artifact** — it was never executed or never returned. The maintainer granted
  `provider-limited-review-exception` on 2026-07-03
  (`tracker:project-ontos-audit-serializer-corruption#fallback-authorization-2026-07-03`),
  so the deliverable is *authorized to continue* under fallback labeling; it simply never
  resumed. Remaining work: close B.1, author B.3 verdict, Phase C (replace
  `_serialize_field` with `yaml.safe_dump` + re-parse assertion; add the round-trip
  regression test), D.2/D.3/D.5/D.6, Phase E retro. `ontos/core/schema.py` is still
  unmodified — **the audit's lone P0 data-corruption defect remains live in the tree.**
- **#147's original fix was incomplete (found by external review of PR #160, 2026-07-09).**
  The managed-launcher gate validated only the executable and an *empty* launcher prefix,
  so `is_ontos_managed_launcher()` returned true for any argv whose executable resolved to
  Ontos. A repo-committed `.cursor/mcp.json` could therefore name Ontos's own trusted
  launcher and smuggle a different subcommand (e.g. `scaffold --apply` behind a `--`
  separator, or a duplicated `--workspace`) past the `serve`/`--workspace` preflight. Fixed
  by `is_ontos_managed_serve_argv()`, which requires exact equality with the argv Ontos
  itself generates, plus safe-by-default `allow_*_unmanaged_probe=False`. Three regression
  tests added.
- **The doctor test failure was NOT pre-existing — this line's docs caused it.** Earlier
  notes here and in #147's tracker claimed `test_returns_exit_code_0_when_checks_pass` was
  a pre-existing environment-sensitive failure. That was wrong: base `c8672e9` is green and
  head was red. The committed spec carried `status: draft-for-review`, an invalid Ontos
  status, which degraded `check_activation_health` from success to warning. Fixed
  (`status: draft`, `type: atom`, and `docs/handoffs/**` added to `allowed_orphan_paths`).
- **#147 has NO strict-P3 receipts, and its fallback is label-only.** Its 11 review
  artifacts all carry `provider_limited_fallback: true` but none were dispatched through
  `dispatch-family-review.sh`; the inventory has no `receipts[]` and no
  capture_id/resolved_model/artifact_sha256 anywhere. `verify-lifecycle --mode
  provider-limited-fallback` therefore does not certify it. Receipts were deliberately left
  empty rather than reconstructed. By contrast **#146's B.1 claude-sonnet review *was*
  genuinely wrapper-dispatched** (`capture_id`, `resolved_model: sonnet`,
  `status: completed`) — the stalled deliverable holds better evidence than the
  "complete" one.
- **Neither #146 nor #147 achieved strict P3.** Both ran under the provider-limited
  fallback owing to the same GPT-family model-access blockage. Strict P3 is not certified
  for the v4.7.1 line.

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
