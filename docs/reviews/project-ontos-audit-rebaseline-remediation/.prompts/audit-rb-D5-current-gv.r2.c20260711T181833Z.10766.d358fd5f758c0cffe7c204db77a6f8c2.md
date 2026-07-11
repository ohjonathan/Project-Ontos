# D.5 current-head Gemini verifier

Read `.llm-dev/framework/templates/01-worker-session-contract.md` and
`.llm-dev/framework/templates/15-verifier.md` completely. You are the external
Gemini verifier for `project-ontos-audit-rebaseline-remediation`, phase D.5.
Your evidence cap is `static-inspection`: do not claim shell execution,
direct-run evidence, or test results you did not personally produce. Do not
edit files. Return only the complete verdict artifact on stdout; the framework
wrapper owns artifact creation.

Independently inspect exact product target `388845c` using tracked repository
content. Read `D.3-verdict.md`, `D.4-fix-summary.md`,
`D.4-current-head-addendum.md`, `PR-161-fable-feedback-disposition.md`, the
manifest, the changed implementation/tests, and the diff `859ecf7..388845c`.
Check traceability for every historical D.4 row and every current-head addendum
row. Inspect the EH-15-A verifier's adopter-root, fixture, and registry path
resolution. Inspect the receipt-inventory schema, wrapper producer fields, and
whether `verify-lifecycle.sh` validates that schema. Treat prior execution
counts only as inputs labelled `orchestrator-preflight` or quoted historical
evidence, never as your own execution.

Reject unrelated fixtures, receipt editing/copying, framework-checkout edits,
or a lifecycle success string that bypasses a schema the produced inventory
fails. If code traceability is sound, say so; if a framework defect remains,
preserve it as required further action and return `Request changes`.

Output a complete Template-15 artifact. Frontmatter: `id:
audit-rb-D5-current-gv`, correct deliverable, `phase: D.5`, `role: verifier`,
`family: gemini`, `evidence_mode: static-inspection`, `status: completed`, and
an appropriate canonical verdict. The first body line after frontmatter must
be one H1. Include per-finding tables, target `388845c`, framework findings,
then exact `## Verdict` followed first by the bare canonical phrase. Do not
claim D.6, strict-P3, merge, tag, or release.
