---
id: project_ontos_audit_doctor_rce_tracker
type: tracker
status: active
deliverable_id: project-ontos-audit-doctor-rce
issue: 147
release: v4.7.1
depends_on:
  - project_ontos_audit_remediation_2026_07_dispatch_147
  - project_ontos_audit_remediation_release_line_tracker
  - project-ontos-codex-audit-revalidation-2026-07
---

# project-ontos-audit-doctor-rce — Tracker

Current lifecycle state: **`code_fixed_evidence_pending`**.

Implementation base: `c8672e90f2382f4147ef61b4fba918969483e73e`.
Implementation of record: `03c36e6ac999d2c411c13252baa2e8fcff60e6ed`.
GitHub issue state observed after parity synchronization on 2026-07-10: open
(reopened with the evidence-pending contract). Issue state and release
certification remain separate axes.

| Phase | Owner | Status | Artifact | Evidence | Timestamp |
|---|---|---|---|---|---|
| rebaseline | codex | complete | `docs/reviews/2026-07-10-codex-audit-revalidation.md` | Reopened the label-only completion claim; exact-argv implementation and evidence gap independently checked. | 2026-07-10 |
| implementation | merged PR #160 | code fixed | `03c36e6`; `ontos/core/mcp_shared.py`; `ontos/core/cursor_mcp.py`; `ontos/commands/doctor.py`; `SECURITY.md` | Full managed argv equality; safe defaults; five focused regressions pass. | 2026-07-09 |
| B.1 | external families | pending fresh wrapper dispatch | expected `B.1-*-dispatch-{intent,result}.yaml` and refreshed reviews | Existing Markdown reviews have no wrapper receipts and are historical only. | 2026-07-10 |
| B.3 | codex meta-consolidator | pending refresh | `B.3-verdict.md` | Existing verdict predates the exact-argv fix and cannot close the reopened chain. | 2026-07-10 |
| C | codex reconciliation | pending | implementation/spec reconciliation | Confirm `03c36e6` against the newly approved exact-argv spec; change code only for a preserved blocker. | 2026-07-10 |
| D.2 | external families | pending fresh wrapper dispatch | expected `D.2-*-dispatch-{intent,result}.yaml` and refreshed reviews | No valid receipts exist. | 2026-07-10 |
| D.3 | codex meta-consolidator | pending refresh | `D.3-verdict.md` | Must adjudicate the exact implementation and real D.2 evidence. | 2026-07-10 |
| D.5 | external families | pending fresh wrapper dispatch | expected `D.5-*-dispatch-{intent,result}.yaml` and refreshed verifiers | No valid receipts exist. | 2026-07-10 |
| D.6 | codex final-approval | not approved | `final-approval.md` | `code_fixed_evidence_pending`; strict receipts, clean full suite, and issue-only scope gate remain open. | 2026-07-10 |
| E | codex retro | reopened | `docs/retros/project-ontos-audit-doctor-rce-retro.md` | Return to complete only after a truthful terminal lifecycle state. | 2026-07-10 |

## Exact five-test contract

`tests/test_doctor_mcp_probe_regression.py` must retain exactly these cases:

1. hostile repo Python payload is not executed;
2. exact managed launcher still probes;
3. trusted launcher cannot smuggle a subcommand;
4. duplicate `--workspace` is rejected; and
5. omitted opt-out remains safe by default.

Latest focused run: `.venv/bin/python -m pytest
tests/test_doctor_mcp_probe_regression.py -q` → `5 passed in 0.44s` on
2026-07-10.

## Evidence policy

- `docs/reviews/project-ontos-audit-doctor-rce/lifecycle-receipt-inventory.yaml`
  intentionally contains `receipts: []`.
- Do not derive capture IDs, model identities, timestamps, or hashes from the
  existing prose. Only wrapper output may populate new receipt rows.
- Strict P3 is the default release gate. If strict provider access remains
  impossible, a maintainer must explicitly authorize an emergency waiver with
  a non-certified terminal status; the 2026-07-03 provider-limited prose does
  not automatically close this reopened implementation.

## Scope policy

Use the manifest and implementation base, not a bare working-tree diff:

```bash
bash .llm-dev/framework/scripts/verify-changed-path-scope.sh \
  --manifest manifests/project-ontos-audit-doctor-rce.yaml \
  --base c8672e90f2382f4147ef61b4fba918969483e73e
```

Run that gate in a dedicated #147 worktree. The shared meta-cycle branch contains
unrelated sibling and registry paths and is expected to fail an issue-only scope
check.

## Historical record

The 2026-07-03 Phase 0→E rows and provider-limited authorization remain visible
in git history and in the historical review files. They are superseded for
current status because the original implementation was bypassable and its
review artifacts were not wrapper-dispatched. Nothing in this tracker claims
those artifacts are receipts.
