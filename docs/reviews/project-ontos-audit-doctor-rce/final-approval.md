---
id: project-ontos-audit-doctor-rce-final-approval
type: review
deliverable_id: project-ontos-audit-doctor-rce
role: final-approval
family: codex
status: active
---

# Reopened Final-Approval Gate — project-ontos-audit-doctor-rce

Lifecycle state: `code_fixed_evidence_pending`. This file supersedes the
2026-07-03 completion decision, which reviewed the prefix-only launcher fix and
treated non-wrapper prose as provider-limited lifecycle evidence.

## Implementation under judgment

- Base: `c8672e90f2382f4147ef61b4fba918969483e73e`
- Fix: `03c36e6ac999d2c411c13252baa2e8fcff60e6ed`
- Contract: exact managed `serve --workspace <expected-root>` argv, with only an
  optional trailing `--read-only`; no extra, duplicated, reordered, or hidden
  subcommand tokens; unmanaged probes disabled by default.

## Gate table

| # | Prerequisite | State | Evidence |
|---|---|---|---|
| 1 | Exact implementation commit is present. | PASS | `git merge-base --is-ancestor 03c36e6 HEAD` |
| 2 | Five focused doctor RCE regressions pass. | PASS | `.venv/bin/python -m pytest tests/test_doctor_mcp_probe_regression.py -q` → `5 passed in 0.44s` on 2026-07-10. |
| 3 | Manifest conformance passes. | PASS | `scripts/llm-dev verify manifests/project-ontos-audit-doctor-rce.yaml` passed all four manifest-only checks on 2026-07-10. Manifest conformance alone is not lifecycle proof. |
| 4 | Changed-path scope from the implementation base passes in a dedicated issue-only worktree. | BLOCKED IN SHARED TREE | Run `verify-changed-path-scope.sh --base c8672e9`; the shared branch contains unrelated meta-cycle and sibling changes by design. |
| 5 | Fresh wrapper-dispatched B.1, D.2, and D.5 receipts validate. | FAIL / MISSING | `lifecycle-receipt-inventory.yaml` contains `receipts: []`. Existing review prose has no capture ID, resolved model, or artifact hash and is not counted. |
| 6 | Full suite passes and leaves a clean checkout. | PENDING | The prior green suite was not hermetic; passing tests without `git status --porcelain` cleanliness is insufficient. |
| 7 | B.3/D.3/final decision describes the exact-argv implementation. | PENDING | Existing canonical verdicts predate the exact-argv correction and must be refreshed by the real review chain. |

## Required five-test contract

1. Repo-sourced Python payload is not executed.
2. Exact managed launcher still initializes.
3. Trusted launcher cannot smuggle another Ontos subcommand.
4. Duplicate `--workspace` cannot pass the gate.
5. The default remains safe when a caller omits an explicit opt-out.

## Evidence policy

- Do not reconstruct receipts from the existing Markdown artifacts.
- Fresh evidence must come from `dispatch-family-review.sh` and satisfy the
  manifest's strict-P3 inventory checks.
- If provider access makes strict P3 impossible, closure requires a new explicit
  emergency-waiver decision. Its terminal state must say strict P3 is not
  certified; it cannot be recorded as ordinary completion.
- GitHub issue #147 was reopened on 2026-07-10 with this evidence-pending
  contract. Its open state does not itself provide release certification.

## Decision

**NOT APPROVED FOR RELEASE — `code_fixed_evidence_pending`.** The product-code
finding is fixed and its focused regression contract passes. Lifecycle and
clean-worktree gates remain open.
