---
id: project_ontos_audit_remediation_2026_07_final_report
type: handoff
status: active
meta_cycle_id: project-ontos-audit-remediation-2026-07
output_class: final-report
date: 2026-07-03
depends_on: []
---

# Meta-session final report — project-ontos-audit-remediation-2026-07

Emitted at the close of the meta-orchestrator kickoff session (Template 24 §11). The YAML
block below is the normative final report; the sections after it record verification and
one known discrepancy for the maintainer.

```yaml
meta_cycle_id: project-ontos-audit-remediation-2026-07
invocation_trigger_fired: [T1, T2, T5]
spanning_deliverables: [project-ontos-audit-serializer-corruption, project-ontos-audit-doctor-rce,
  project-ontos-audit-relN-quick-wins, project-ontos-audit-relN-sweep,
  project-ontos-audit-characterization-tests, project-ontos-audit-parser-consolidation,
  project-ontos-audit-writepath-bodyref, project-ontos-audit-mcp-dispatch-rename,
  project-ontos-audit-exitcode-envelope, project-ontos-audit-cli-command-table,
  project-ontos-audit-precommit-rewire-slim, project-ontos-audit-graph-traversal]
outputs_produced: [O2, O4, O5, O6]
routing_handoffs:
  - to: codex-orchestrator (fresh session; user pastes docs/handoffs/project-ontos-audit-remediation-2026-07-dispatch-146-serializer-corruption.md)
    work_routed: "dispatch #146 serializer-corruption Phase 0→E (O7 handoff; check-meta-orchestrator-handoff.sh exit 0)"
  - to: codex-orchestrator (fresh session; user pastes docs/handoffs/project-ontos-audit-remediation-2026-07-dispatch-147-doctor-rce.md)
    work_routed: "dispatch #147 doctor-rce Phase 0→E (O7 handoff; check-meta-orchestrator-handoff.sh exit 0)"
circuit_breaker_state: 0
release_line_decision: "v4.7.1 = #146 + #147 (regression tests mandatory) + #148/#149 optional in-patch; v4.8.0 = #150 first, then #151/#152/#153; v4.9.0 = #154/#155/#156/#157 — authoritative in O6 docs/handoffs/project-ontos-audit-remediation-2026-07-release-line-decision.md"
```

**O2/O7 reconciliation.** The two dispatch prompts are O7 one-shot implementation-orchestrator
handoffs (playbook "Standard outputs O1–O7"). The §11 schema's `outputs_produced` enumerates
O2..O6, so the O7s are carried under `routing_handoffs` and counted within the O2 handoff
surface rather than as a separate `O7` list item.

## Artifacts written this session (all inside kickoff §4 scope-lock)

| Output | Path |
|---|---|
| O5 scope-lock manifest + O4 verification ledger | `docs/trackers/project-ontos-audit-remediation-release-line.md` |
| O6 release-line decision (+ family-rotation discharge) | `docs/handoffs/project-ontos-audit-remediation-2026-07-release-line-decision.md` |
| O7 dispatch — #146 serializer corruption | `docs/handoffs/project-ontos-audit-remediation-2026-07-dispatch-146-serializer-corruption.md` |
| O7 dispatch — #147 doctor RCE | `docs/handoffs/project-ontos-audit-remediation-2026-07-dispatch-147-doctor-rce.md` |
| O2 final report (this file) | `docs/handoffs/project-ontos-audit-remediation-2026-07-final-report.md` |

All release actions (commit/tag/push/merge/issue-closure) are maintainer-deferred; the
working tree is left uncommitted per the maintainer's decision.

## Verification performed

- **Template self-check (§1): PASS** — kickoff frontmatter declares `id: meta-orchestrator-kickoff`.
- **Decision procedure (§3.4): Q1=YES / Q2=NO / Q3=YES** — meta session warranted.
- **Forbidden-paths preflight (F-1..F-4): PASS** — meta-cycle's own allowlist holds no
  product-code / per-deliverable-tracker / other-board / other-D.6 path.
- **`check-meta-orchestrator-handoff.sh`: 9/9 on both dispatch prompts** (exit 0) at
  authoring time (framework v1.4.2), and on the framework's own PASS fixture (sanity).
  **Re-validated 2026-07-09 against framework v2.0.1**, which added Field 10 (lifecycle
  ownership / role split) and a mandatory Worktree Isolation section (issue #188). Both
  dispatch prompts were updated with those sections and now report
  `Worktree Isolation + 10/10 fields detected`.
- **`verify-all.sh`:** framework conformance suite runs; the only failures are two of the
  framework's own untracked self-test fixtures (`v1_10_0-agy-substrate-fixture.py`,
  `verify-d6-gate.sh(strict-p3-fixtures)`) that trip an adopter-root containment check
  because `.llm-dev/framework` is nested inside the adopter repo — pre-existing and
  unrelated to any artifact authored here.
- **`ontos map`:** all four new documents index with **0 parse errors** (document count
  146 → 151). Run via `.venv/bin/ontos` (repo-local v4.7.0).
- **Adversarial verification pass:** an 18-agent workflow (4 review lenses × skeptical
  per-finding verification) reviewed the four artifacts for checker-regex fragility,
  framework-rule compliance, factual accuracy against the audit and `ontos/` source, and
  cross-artifact consistency. 14 raw findings → 2 confirmed, 12 rejected as nits/misreads.
  Confirmed fix applied: hardened field 8 of both dispatch prompts with a reflow-proof
  single-line release-action statement so the checker's per-line content regex no longer
  depends solely on the markdown table surviving reformatting (both still 9/9).

## External review of PR #160 (2026-07-09) — three blockers, all confirmed

An external reviewer (ChatGPT) reviewed head `c529d04` against base `c8672e9` and raised
three merge blockers. All three were independently reproduced and are now fixed. Two were
caused by this session's own errors.

1. **[P1] The `ontos doctor` RCE fix was incomplete.** `is_ontos_managed_launcher()`
   compared only the executable and an *empty* launcher prefix, so it returned true for
   every argv running Ontos's own binary. A repo-committed `.cursor/mcp.json` could name
   the trusted launcher and smuggle a different subcommand (`scaffold --apply` behind a
   `--` separator, or a duplicated `--workspace`) past the `serve`/`--workspace` preflight.
   Confirmed by direct evaluation of the predicate. Fixed with `is_ontos_managed_serve_argv()`
   (exact equality against the argv Ontos generates) plus safe-by-default probe flags and
   three new regression tests.
2. **[P1] This PR introduced a CI failure; the "pre-existing" claim was false.** Clean
   worktrees settle it: base `c8672e9` passes `test_returns_exit_code_0_when_checks_pass`,
   head failed it. Cause: the committed spec carried `status: draft-for-review`, an invalid
   Ontos status, plus three orphaned documents — together degrading
   `check_activation_health`. **The earlier verification of this claim was invalid**: the
   stash experiment held the audit docs constant (they were untracked and present in both
   runs) instead of varying them. Fixed via `status: draft`, `type: atom` on the spec, and
   `docs/handoffs/**` in `allowed_orphan_paths`.
3. **[P2] The committed lifecycle packet failed its own gates.** `llm-dev verify` on the
   #146 manifest failed (undeclared `self_review_caveats` self-review overlap, and
   `anchor_parity_strict: true` asserting a Template-13 §11/§18 spec shape the spec does not
   use); the #147 receipt inventory had no `schema_version`; and the #146 B.1 receipts
   referenced `.prompts/`/`.raw/` evidence that this session had stripped from the commit.
   All repaired — the evidence files were restored rather than the references removed.

**Consequence recorded, not papered over:** #147 has **no strict-P3 receipts**. Its review
artifacts are fallback-*labelled* but were never wrapper-dispatched, so
`verify-lifecycle --mode provider-limited-fallback` does not certify it, and `receipts[]`
was deliberately left empty rather than reconstructed. The stalled #146, by contrast, holds
a genuine wrapper receipt for its B.1 claude-sonnet review.

## Known discrepancy surfaced to the maintainer (not fixed this session)

The **kickoff document's own filename** (`docs/handoffs/2026-07-03-audit-remediation-meta-orchestrator-kickoff.md`)
does **not** match the §4 scope-lock pattern it declares for meta-cycle handoffs
(`docs/handoffs/project-ontos-audit-remediation-2026-07-*`), even though the §4 bullet says
that pattern covers "this file". No automated gate fails (the checker lints only the 9
dispatch fields, not filenames), and the kickoff was authored by the prior audit-authoring
session as a bootstrap — so this is an internal-consistency wart in an inherited input, not
a scope violation by this meta-session. It was left unchanged deliberately: renaming an
inherited normative input and rewriting its ~7 inbound references (Ontos_Context_Map.md, the
O5 tracker, the O6 decision, and both dispatch prompts) is a maintainer scope decision.
**Recommended reconciliation** (maintainer's choice): rename the kickoff to
`docs/handoffs/project-ontos-audit-remediation-2026-07-meta-orchestrator-kickoff.md` (matches
the sibling prefix and makes the "incl. this file" clause true), or widen the §4 pattern to
admit the dated form and record the exception. All five artifacts authored this session
already use the canonical `project-ontos-audit-remediation-2026-07-` prefix and are unaffected.

## Next action for the maintainer

Open two fresh **Codex** implementation-orchestrator sessions (v4.7.1 line, independent and
dispatchable now) and paste, respectively, the #146 and #147 dispatch prompts. Do **not**
open them as Claude sessions — Codex is the implementation family per the O6 topology; claude/
gemini/gpt rotate as the non-author review families on the per-deliverable boards. After #150
(characterization tests) lands, dispatch #151/#152/#153; #154–#157 last.
