# D.5 current-head GLM verifier

Read `.llm-dev/framework/templates/01-worker-session-contract.md` and
`.llm-dev/framework/templates/15-verifier.md` completely. You are the external
GLM verifier for `project-ontos-audit-rebaseline-remediation`, phase D.5,
routed through the attested Neuralwatt OpenCode GLM-5.2 profile. You are not
the orchestrator or fix author. Do not commit, stage, spawn agents, or write
any repository file. Emit the entire complete verdict artifact on stdout only;
do not use file-writing tools and do not merely print a file path. This is
required so the framework wrapper promotes the verdict-shaped raw transcript.

Verify exact product target `388845c`. Confirm `git rev-parse HEAD` identifies
that target and that product/test paths have no working-tree changes. Read
`D.3-verdict.md`, `D.4-fix-summary.md`, `D.4-current-head-addendum.md`,
`PR-161-fable-feedback-disposition.md`, the manifest, and
`git diff 859ecf7..388845c`. Run the focused current-head tests from the
addendum and the complete `tests/` suite. Run registry local/external parity,
changed-path scope from `bf91b42`, manifest conformance, and
`git diff --check bf91b42..388845c`. Re-run both EH-15-A probes. Validate the
current receipt inventory against the framework schema and inspect whether
`verify-lifecycle` applies that schema.

Verify every historical D.4 row and every current-head addendum row. Record
exact commands, exits, and test counts. Do not include full 40- or 64-character
hashes, capture IDs, tokens, endpoints, or environment values in the artifact;
use short commit SHAs such as `388845c`. If code passes, say so. If a framework
defect remains, preserve it as required further action and use `Request
changes`; do not waive or repair receipts manually.

Output a Template-15 artifact with frontmatter: `id:
audit-rb-D5-current-glv`, correct deliverable, `phase: D.5`, `role: verifier`,
`family: glm`, `evidence_mode: direct-run`, `status: completed`, and an
appropriate canonical verdict. Include one H1, per-finding tables,
regression/scope results, framework findings, then exact `## Verdict` followed
first by the bare canonical phrase. Do not claim D.6, strict-P3, merge, tag,
or release.
