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

## v1.4 final-inventory rollover

The complete v1.3 B.2 recertification produced genuine wrapper evidence but
returned `Request changes` from Claude adversarial and GLM peer. Spec v1.4
closes those findings. The pinned v2.0.1 wrapper cannot append a second attested
GLM receipt to the same inventory without generating a long
`supersedes_run_ids[]` backlink that its own route-redaction verifier rejects.
The framework exposes no supported receipt import, inheritance, migration, or
rollover operation.

Accordingly, `lifecycle-receipt-inventory-recertification.yaml` is now preserved
unchanged as non-certifying attempt history. The manifest points to
`lifecycle-receipt-inventory-final.yaml`, which the wrapper creates on the first
successful append. Every B.1 and B.2 engineering and Product seat is genuinely
redispatched at round 1 with fresh intent, result, prompt, raw-output, and
verdict paths. No receipt row is copied, hand-created, edited, or reconstructed.
D.2 and D.5 append to that final inventory only after both final design bundles
verify complete.
