# D.5 current-head Claude verifier

Read `.llm-dev/framework/templates/01-worker-session-contract.md` and
`.llm-dev/framework/templates/15-verifier.md` completely. You are the external
Claude verifier for `project-ontos-audit-rebaseline-remediation`, phase D.5.
You are not the orchestrator or fix author. Do not commit, stage, spawn agents,
or edit repository files. Return only the complete verdict artifact on stdout;
the framework wrapper owns creation of
`docs/reviews/project-ontos-audit-rebaseline-remediation/D.5-current-claude.md`.

Verify exact product target `388845c` rather than relying on prior reviews.
First confirm `git rev-parse HEAD` is `388845cbd0cfc6ee8a9b2f61f7ebe5f14eff70a2`
and that any working-tree differences are lifecycle evidence only, not
`ontos/`, `tests/`, `scripts/`, `.github/`, or `pyproject.toml`. Read, in order:

1. `D.3-verdict.md`
2. `D.4-fix-summary.md`
3. `D.4-current-head-addendum.md`
4. `PR-161-fable-feedback-disposition.md`
5. `git diff 859ecf7..388845c` and all changed implementation/tests

Run the current-head focused tests named in the addendum, then the complete
`tests/` suite. Run local and external registry parity, changed-path scope from
`bf91b42`, manifest conformance, and `git diff --check bf91b42..388845c`.
Re-run both EH-15-A probes from `D.4-fix-summary.md`. Inspect the lifecycle
receipt schema against the current inventory and determine whether
`verify-lifecycle` applies it. Record exact commands, exits, and counts.

Verify every historical D.4 row and every addendum row. Do not convert CI or a
prior reviewer claim into your own direct-run evidence. If product checks pass,
say so. If either framework defect remains, preserve it as required further
action and use `Request changes`; do not waive it or fabricate evidence.

Output the complete bytes for
`docs/reviews/project-ontos-audit-rebaseline-remediation/D.5-current-claude.md`
as a Template-15 artifact with frontmatter: `id:
audit-rb-D5-current-cv`, the correct deliverable, `phase: D.5`, `role:
verifier`, `family: claude`, `evidence_mode: direct-run`, `status: completed`,
and an appropriate canonical verdict. Include one H1, per-finding tables,
exact target `388845c` (use the short SHA in the artifact), regressions/scope,
framework findings, then exact `## Verdict` followed first by the bare
canonical phrase. Do not claim D.6, strict-P3, merge, tag, or release.
