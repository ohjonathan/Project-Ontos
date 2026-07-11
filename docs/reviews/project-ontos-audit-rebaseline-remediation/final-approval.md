---
id: project-ontos-audit-rebaseline-remediation-final-approval
deliverable_id: project-ontos-audit-rebaseline-remediation
role: final-approval
status: withheld
deliverable_manifest_path: ../../../manifests/project-ontos-audit-rebaseline-remediation.yaml
halt_reason: "Strict-P3 is blocked by the unavailable Gemini D.5 seat and reproducible llm-dev v2.0.1 EH-15-A / receipt-schema-verifier drift; no passing D.6 gate can be issued honestly."
---

# Final-Approval Gate — project-ontos-audit-rebaseline-remediation

## Gate outcome

WITHHELD

The D.6 gate was executed as an honest withheld gate, not omitted and not
rounded up. No `PASSED` gate-table row is emitted. The repository product
checks are green, but strict lifecycle evidence is not mechanically admissible.

## Blocking evidence

| Blocker | Current result | Evidence |
|---|---|---|
| Gemini D.5 verifier | Genuine retry failed, exit `55`; no verdict or receipt | `D.5-current-dispatch-result.yaml` plus its wrapper-captured Gemini stderr |
| D.5 Claude verifier | Artifact and genuine round-2 receipt bound to product snapshot `388845c` exist; verdict `Request changes` | `D.5-current-claude.md` |
| D.5 GLM verifier | Artifact and genuine round-2 receipt bound to product snapshot `388845c` exist, but v2.0.1 records a non-interactive OpenCode result as `worker_file` and rejects its own supersession backlink | `D.5-current-glm.md`; strict lifecycle diagnostics |
| EH-15-A | Manifest mode returns false-green exit `0`; explicit adopter summary mode fails registered-fixture resolution | `D.5-current-claude.md` |
| Receipt schema | The manifest inventory fails the pinned framework schema on six framework-emitted Product/OpenCode values; `verify-lifecycle` does not apply that schema | receipt-schema command output recorded in the D.5 status |

## Mechanical closeout checks

| Check | Result |
|---|---|
| Product review snapshot | D.5 dispatched against exact requested head `388845c` |
| Package metadata | Bumped from `4.7.0` to `4.7.1` after the D.5 snapshot; no claim that this mechanical follow-up was part of the reviewed tree |
| Complete local suite | `1740 passed, 1 warning` |
| Manifest conformance | PASS, `4/4` |
| Closeout-proof metadata | PASS; proof-test, product-code-scope, and live-doc reconciliation gates are explicit |
| Lifecycle verifier | Strict mode exits `1` with `status=manifest_valid`; fallback mode exits `1` with `status=provider_limited_fallback_incomplete` |
| D.6 shape | `verify-d6-gate --allow-gated` PASS; strict-P3 mode intentionally fails |

## Maintainer-directed handoff status (not framework certification)

`provider_limited_fallback_complete; strict P3 not certified; maintainer release actions deferred`

The `_complete` token is retained only because the 2026-07-11 maintainer
handoff required that exact fallback report string after a genuine retry. The
pinned framework did not emit or mechanically attain it: fallback verification
exits `1` with `status=provider_limited_fallback_incomplete`. Under the
framework's D.6 contract the certification outcome is therefore `not complete`,
and this gate remains `WITHHELD`. The v2.0.1 fallback generator also cannot
upgrade the existing schema-v1 append-only inventory without mutating or
reconstructing historical receipts, so no synthetic fallback receipt was
created.

## Release-action split

- Lifecycle/session action: D.6 attempted and withheld; re-adjudication remains
  blocking.
- Maintainer action: merge, tag, publication, release, and issue closure remain
  deferred. This artifact grants none of those authorities.

## Recommended next action

Upgrade to a framework release that resolves llm-dev-framework issue #214,
restore a supported Gemini/AGY route, re-run the three D.5 seats against the
eventual release-slice head, and only then issue a passing D.6 artifact.
