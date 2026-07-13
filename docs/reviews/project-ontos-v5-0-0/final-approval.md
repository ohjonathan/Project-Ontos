---
id: project-ontos-v5-0-0-final-approval
deliverable_id: project-ontos-v5-0-0
role: final-approval
type: log
status: complete
original_status: withheld
deliverable_manifest_path: manifests/project-ontos-v5-0-0.yaml
halt_reason: "Strict and provider-limited lifecycle verification both failed with no genuine external receipt."
branch: codex/ontos-v5.0.0
event_type: review
source: codex
depends_on: [project-ontos-v5-0-0-spec]
concepts: [release, external-review, hardening]
---

# Ontos 5.0.0 final approval — WITHHELD

## Gate table

| # | Prerequisite | Result | Evidence class | Reproduction |
|---|--------------|--------|----------------|--------------|
| 1 | Product suite passes. | PASSED | test-pass | `PYTHONPATH=. python -m pytest -q` |
| 2 | Documentation validation is clean. | PASSED | command-exit-0 | `python -m ontos map --strict --scope docs` |
| 3 | External evidence ref is complete and hash-bound. | PASSED | command-exit-0 | `python scripts/verify_lifecycle_evidence_ref.py docs/reviews/project-ontos-v5-0-0/evidence-index.yaml` |
| 4 | Strict-P3 lifecycle receipts verified. | FAILED | command-exit-nonzero | `scripts/llm-dev verify-lifecycle manifests/project-ontos-v5-0-0.yaml --mode strict-p3` |

## Failure diagnosis

Row 4 failed because the Claude provider returned `Execution error` without a
verdict artifact, leaving the receipt inventory empty. Required remediation:
repair or restore the provider/framework route and rerun the full board against
the product head before re-entering D.6.

## Gate outcome

FAILED (first failing row: 4). D.6 is WITHHELD.

## Verdict

**WITHHELD.** Product, documentation, packaging, and local quality gates pass,
but llm-dev strict P3 is not certified. The genuine B.1 Claude dispatch at
product head `8f4fc8842bd8346b541a9c5a08a9d196ee1a6319` returned only
`Execution error` after 270 seconds and produced no verdict artifact. Both the
strict and provider-limited lifecycle verifiers therefore exit 1 with an empty
receipt inventory. No receipt has been synthesized.

The raw evidence is isolated on
`lifecycle-evidence/project-ontos-v5-0-0@7a5c1d47894568c80305cf126cc2401156adf301`
and hash-bound by `evidence-index.yaml`.

## Recommendation

Hold release authorization until a genuine review board can produce the
required strict receipts, or until the framework/provider path is repaired and
the lifecycle is rerun. This document grants no merge, tag, release, PyPI,
issue-closure, or other maintainer action.
