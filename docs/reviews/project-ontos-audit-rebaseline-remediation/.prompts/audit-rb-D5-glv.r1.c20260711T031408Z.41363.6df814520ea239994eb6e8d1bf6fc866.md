# D.5 independent GLM verifier

Read `.llm-dev/framework/templates/01-worker-session-contract.md` and
`.llm-dev/framework/templates/15-verifier.md` completely. You are the external
GLM verifier for `project-ontos-audit-rebaseline-remediation`, phase D.5,
routed through the attested Neuralwatt OpenCode GLM-5.2 profile. You are not the
orchestrator or fix author. Do not commit, stage, spawn agents, or edit anything
except the review file the wrapper instructs you to write.

Consume the committed D.3 verdict, D.4 fix summary, D.4 scope recovery, manifest,
and code/test diff from `aa41c3982e21b0e0cff6c3c5486f4af9e5e55e05` to I2
`311b60b6e86abe6d0b5a7ac61e16d07049387707`. Verify all six canonical
should-fixes CAN-ACT-1/2, CAN-CP-1/2/3, and CAN-ID-1; the empty D.3 blocker list
does not waive them. Verify D4-INFRA-1 directly. If it holds, return
`Request changes` even when product tests pass.

Use only `/tmp/project-ontos-d5-glm` for source swaps/tests. Confirm its HEAD is
`8d5096eba940aafe1e8b86bdd3a8852961bab815` and its entry state is clean. Use
`/tmp/project-ontos-worktrees/project-ontos-audit-rebaseline-remediation/.venv/bin/python`;
confirm imports resolve from the disposable worktree. For each group, run the
post-fix tests, restore the listed implementation files from pre-fix
`aa41c3982e21b0e0cff6c3c5486f4af9e5e55e05`, rerun the identical tests with
`--cache-clear` and require nonzero, restore from HEAD, and require pass:

1. `ontos/commands/activate.py ontos/core/config.py` with
   `tests/commands/test_agentic_activation_resilience.py -k 'human_renders_incompatible or human_renders_malformed or json_renders_malformed'`.
2. `scripts/validate-audit-remediation-registry.py` with
   `tests/test_audit_remediation_registry_validator.py -k 'issue_158_control_plane or control_plane_finding_id_and_issue_158 or duplicate_lease_lists or malformed_registry_yaml or malformed_child_manifest_yaml'`.
3. `ontos/commands/rename.py ontos/mcp/rename_tool.py` with
   `tests/commands/test_rename.py tests/mcp/test_rename_document.py -k 'rename_invalid_ids_use_canonical or rename_invalid_id_is_rejected_before_project_discovery or build_rename_plan_uses_canonical or rename_document_invalid_ids_use_canonical or rename_document_rejects_invalid_id_before_preflight'`.

`git restore --source <sha> -- <listed-files>` is authorized only in this
disposable verification worktree. Restore clean HEAD at the end. Run the full
`tests/` suite there with `-q -p no:cacheprovider`. From the lifecycle worktree,
run registry local/external parity, changed-path scope, manifest conformance,
`git diff --check HEAD`, plus the summary's manifest-mode and explicit-path
EH-15-A probes. Record exact commands and evidence; do not call an expected
nonzero pre-fix or infrastructure probe a test-harness failure.

Write only the wrapper-designated artifact, using Template 15 frontmatter with
`id: audit-rb-D5-glv`, `phase: D.5`, `role: verifier`, `family: glm`,
`evidence_mode: direct-run`, `status: completed`, and
`verdict: Request Further Fixes`. Include an H1, six finding rows, full smoke
and scope results, D4-INFRA-1 required action, and exact `## Verdict` followed
by bare `Request changes`. Do not claim D.6, per-child certification, merge,
publication, or release readiness.
