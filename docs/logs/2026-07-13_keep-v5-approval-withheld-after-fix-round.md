---
id: log_20260713_keep-v5-approval-withheld-after-fix-round
type: log
status: active
event_type: pr-163-claude-verification-lifecycle-canary
source: cli
branch: codex/ontos-v5.0.0
created: '2026-07-13'
depends_on: [project-ontos-v5-0-0-spec]
concepts: [release, external-review, hardening]
---

# PR #163 Claude verification and lifecycle canary

## Goal

Review owner comment `4960736071`, address any applicable findings, and attempt
the required current-head Claude route canary without weakening the strict-P3
or release guardrails.

## Key Decisions

- Accepted the comment's independent reproduction of all 11 fixes as product
  verification, but not as a submitted GitHub `APPROVE` review or lifecycle
  receipt.
- Made no product-code changes because the comment reported no remaining code
  defect or regression.
- Byte-verified the evidence checkout against PR head `bce26f5` and confirmed
  the exact historical Claude executable, realpath, and CLI version before the
  canary attempt.
- Halted before strict-P3 when execution policy denied the required
  `bypassPermissions` launch before provider invocation. No artifact or receipt
  was fabricated.
- Retried only after the maintainer explicitly authorized the disclosed
  external data-egress risk. Tenant policy still denied process creation, so the
  exact route remained unavailable and strict-P3 remained gated off.
- Kept PR #163 draft, the release hold active, and D.6 `WITHHELD`.

## Alternatives Considered

- Updating llm-dev from v2.0.1 to v2.0.2 was inspected and rejected: the patch
  release does not repair the receipt-schema or OpenCode/GLM verifier mismatch
  and would expand the product diff.
- Replacing the denied exact route with an indirect or weaker provider call was
  rejected because it would not satisfy the canary contract and would bypass
  the execution-policy ruling.

## Impacts

- The final disposition and lifecycle tracker now distinguish Claude's
  independent product verification from formal review and strict-P3 evidence.
- The sibling evidence ref records the pending canary intent and an honest
  pre-provider policy-block record; raw lifecycle evidence remains outside the
  product branch.
- Maintainer authorization has now been supplied; progress requires a tenant
  policy change or a genuine artifact produced outside this restricted
  execution layer. Release actions remain maintainer-deferred.

## Testing

- Ontos activation: 202 documents, zero load or validation findings.
- Final strict context map after this log: 203 documents, zero findings.
- `scripts/llm-dev doctor`: pass on pinned framework v2.0.1.
- GitHub Actions for `bce26f5`: all six jobs passed.
- Canary preflight: PR-head ancestry and product byte identity passed;
  `/Users/jonathanoh/.local/bin/claude` resolved to Claude Code 2.1.207 at the
  previously attested realpath.
- Pending canary dispatch shape passed `verify-family-dispatch --allow-pending`.
- The external canary process did not start; therefore no strict-P3 verifier
  result is claimed for the remediated head.
- The authorized retry against `0982095` was also denied before process
  creation by tenant policy; no provider artifact or receipt was generated.
