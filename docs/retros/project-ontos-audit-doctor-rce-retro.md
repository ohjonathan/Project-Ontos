---
id: project-ontos-audit-doctor-rce-retro
type: retro
status: active
deliverable_id: project-ontos-audit-doctor-rce
family: codex
depends_on:
  - project_ontos_audit_remediation_2026_07_dispatch_147
  - meta-orchestrator-kickoff
  - project-ontos-codex-audit-revalidation-2026-07
---

# Reopened retro — project-ontos-audit-doctor-rce

## Goal

Remove the `ontos doctor` arbitrary-code-execution path from repo-committed
Cursor MCP config and correct SECURITY.md's MCP write-tool description.

## Product outcome

Code-fixed at `03c36e6ac999d2c411c13252baa2e8fcff60e6ed`. The final implementation
validates the complete managed serve argv, pins the expected workspace, rejects
extra/duplicated/reordered arguments, and defaults unmanaged probes off. The
five focused regressions pass.

## Why this retro is reopened

The 2026-07-03 retro declared Phase E after the first implementation. External
review later showed that comparing only the launcher executable and an empty
prefix was vacuously permissive: a trusted Ontos binary could be asked to run an
attacker-chosen subcommand while `serve` and `--workspace` tokens merely appeared
elsewhere. More importantly, the recorded B.1/D.2/D.5 documents were authored
in-session and never produced wrapper receipts. Provider-limited labels do not
turn them into lifecycle evidence.

Current lifecycle state is `code_fixed_evidence_pending`, not Phase E complete.

## Lifecycle backing artifacts

mode_label: framework lifecycle

user_facing: false

author_family: codex

implementation_sequencing: code-first-user-gated

implementation_sequencing_user_gate_ref: docs/reviews/2026-07-10-codex-audit-revalidation.md#147-doctor-rce

phase_a_spec_path: docs/specs/project-ontos-audit-doctor-rce-spec.md

lifecycle_status: code_fixed_evidence_pending

- Implementation diff: `c8672e90f2382f4147ef61b4fba918969483e73e..03c36e6ac999d2c411c13252baa2e8fcff60e6ed`
- Manifest: `manifests/project-ontos-audit-doctor-rce.yaml`
- Tracker: `docs/trackers/project-ontos-audit-doctor-rce.md`
- Revised spec: `docs/specs/project-ontos-audit-doctor-rce-spec.md`
- Reopened gate: `docs/reviews/project-ontos-audit-doctor-rce/final-approval.md`
- Receipt inventory: `docs/reviews/project-ontos-audit-doctor-rce/lifecycle-receipt-inventory.yaml` (`receipts: []`)
- Revalidation authority: `docs/reviews/2026-07-10-codex-audit-revalidation.md`

## Testing

- PASS: `.venv/bin/python -m pytest tests/test_doctor_mcp_probe_regression.py -q`
  → `5 passed in 0.44s` on 2026-07-10.
- PENDING: full suite plus clean-tree postcondition.
- PENDING: base-SHA changed-path scope in a dedicated #147 worktree.
- PENDING: fresh wrapper-dispatched strict-P3 lifecycle verification.

## Decisions and lessons

- Security allowlists validate the entire executable contract, not marker-token
  presence or an executable prefix.
- Safe behavior is the default at every public and internal call boundary.
- Code correctness and lifecycle certification are separate state dimensions.
- Missing receipts stay missing. Reconstructing them would destroy the evidence
  boundary the framework is intended to provide.
- An emergency waiver, if explicitly granted later, is warning-only and remains
  distinct from strict-P3 certification.

## Remaining work

Run fresh B.1, D.2, and D.5 wrapper dispatches over the exact implementation,
refresh the canonical verdicts, pass the full/clean/scope gates, and only then
return this retro to `status: complete`.
