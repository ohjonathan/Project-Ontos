---
id: project-ontos-github-issues-115-117-D.1-claude-sonnet-peer
deliverable_id: project-ontos-github-issues-115-117
phase: D.1
role: peer
family: claude-sonnet
status: completed
---

# D.1 Peer Pre-Review — claude-sonnet

## Verdict

Approve

## Summary

Pre-review of the Phase C implementation against the spec, ahead of the D.2 three-lens board. The implementation lands all seven Phase C sub-tracks for #115/#116/#117 in 8 logical commits (b8d19e6e: #116 docs, 93dc8f9: README/template skip + doctor severity, 6ff7041: bare_id_token tightening, f8182af: type/status widening, d82e39c: warning enrichment, 37fe69f: depends_on path fallback, 801e06d: #115 schema-safe warning, dd68231: B.1 blocker fixes). 1321/1321 tests pass. No D.1 blocking concerns — advance to D.2 dispatches.

## Findings

### [F1] D.5 verifier prompts still embed the spec rather than the implementation packet
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** `docs/reviews/project-ontos-github-issues-115-117/.prompts/project-ontos-github-issues-115-117-D.5-*.prompt.md`
- **Issue:** The D.5 prompts generated alongside the D.2 prompts substitute the spec as the artifact. D.5 verifiers should see the post-D.4-fix implementation + test status, not the spec alone.
- **Recommendation:** Regenerate the D.5 prompts after D.4 closes, with a "verifier packet" that includes the spec + current commits + pytest output.

## Notes

D.1 is not strict-P3 receipt-bound (the receipt schema covers B.1/B.2/D.2/D.5 only). This pre-review is orchestrator-authored under claude-sonnet authority per the manifest's `model_assignments[D.1] = {claude-sonnet: peer}`. The D.2 board will re-validate the same surface under three independent CLI dispatches.
