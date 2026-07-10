---
id: project-ontos-audit-rebaseline-remediation-receipt-recovery
type: review
status: active
depends_on:
  - project-ontos-audit-rebaseline-remediation-spec
concepts:
  - lifecycle-evidence
  - strict-p3
  - receipt-recovery
---

# Strict-P3 receipt recovery record

## Trigger

`scripts/llm-dev verify-lifecycle --explain-recovery` rejected the genuine
B.1 GLM round-3 receipt because the framework wrapper placed its generated
prior run identifier in `supersedes_run_ids[]`, while the strict route
redaction verifier did not exempt that wrapper-owned backlink from its
high-entropy scan. The prompt, transcript, artifact, route attestation, and
receipt remain preserved in `lifecycle-receipt-inventory.yaml` (SHA-256
`9ef5ff4fcdf5380906ab4912a7a30ef4803c5782de7232bc2674eb49e141feaa`); this record
does not change or certify them.

## Recovery decision

No receipt is edited, copied, reconstructed, or restamped. The manifest points
to a new `lifecycle-receipt-inventory-recertification.yaml`. Every engineering
seat from B.1 and B.2 is dispatched again through
`dispatch-family-review.sh --append-receipt` as a fresh round-1 capture, using
new intent, result, prompt, raw-output, and verdict paths. The unaffected
Product seats remain backed by their original wrapper dispatches and artifacts;
they are not strict-P3 receipt tuples.

The original inventory and failed/intermediate captures are retained as
non-certifying attempt history. Both Product seats are also replayed in separate
P10-compliant Claude wrapper sessions against spec v1.2 and included in the
fresh required bundles; their genuine wrapper receipts are appended even though
Product is not a mechanically required strict-P3 tuple. Only the new inventory
is eligible for the current strict lifecycle gate. D.2 and D.5 will append their
own genuine receipts to that same new inventory.

## Boundary

This is evidence repair, not a framework defect fix and not a release waiver.
Any recertification reviewer finding is handled through the ordinary lifecycle
loop. Strict-P3 must pass without `--allow-warn` before this deliverable can
advance beyond D.5.
