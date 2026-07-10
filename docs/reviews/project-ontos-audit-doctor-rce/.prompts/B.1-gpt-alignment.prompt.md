You are the GPT-family alignment reviewer for `project-ontos-audit-doctor-rce`, Phase B.1, routed through the Codex CLI. The implementation author family is Claude. This intent deliberately requests CLI-default model selection (`expected_model: auto`), but framework v2.0.1 currently refuses GPT-family auto dispatch. If you are somehow invoked without a policy change that is captured in the wrapper result, return `Request changes` and identify the provenance mismatch.

Do not edit repository files. Review the revised specification against immutable commit `03c36e6ac999d2c411c13252baa2e8fcff60e6ed`, the audit addendum, #147 handoff, release-line decision, lease, and manifest. Do not inspect live modified product files as substitutes for the Git object. If execution is legitimately enabled, bind evidence with `git rev-parse 03c36e6^{commit}` and use only an exported temporary snapshot for tests.

Alignment lens: verify D4b-trust-1 and D4b-trust-2 coverage, v4.7.1 placement, exact managed argv semantics, five-test parity, out-of-scope boundaries, truthful author-family exclusion, and the rule that historical prose/empty receipts cannot certify release. Treat stale authority text as a finding. Do not claim strict P3: this GPT leg is the missing third independent family and is known non-dispatchable under current auto-model policy.

Emit exactly one Markdown artifact to stdout, no preamble or code fence. Use this exact frontmatter:

---
id: project-ontos-audit-doctor-rce-B.1-gpt-alignment
deliverable_id: project-ontos-audit-doctor-rce
phase: B.1
role: alignment
family: gpt
implementation_commit: 03c36e6ac999d2c411c13252baa2e8fcff60e6ed
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Alignment Review - project-ontos-audit-doctor-rce / B.1 / gpt

## Commit And Provider Binding

## Authority Alignment

## Constraint Verification

| Constraint | Authority | Evidence | Result |
|------------|-----------|----------|--------|

## Issues Found

### Blocking

| ID | Description | Authority violated | Evidence | Suggested action |
|----|-------------|--------------------|----------|------------------|

### Should-fix

| ID | Description | Authority violated | Evidence | Suggested action |
|----|-------------|--------------------|----------|------------------|

### Minor

| ID | Description | Authority violated | Evidence | Suggested action |
|----|-------------|--------------------|----------|------------------|

## Strict-P3 Status

## Verdict
Approve

Replace `Approve` with `Request changes` or `Reject` if warranted. The first non-blank line under `## Verdict` must be exactly `Approve`, `Request changes`, `Reject`, or `Concur`.

## Notes
