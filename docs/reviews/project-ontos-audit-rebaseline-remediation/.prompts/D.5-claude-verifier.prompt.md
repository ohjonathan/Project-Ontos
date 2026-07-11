# D.5 independent Claude verifier

Read `.llm-dev/framework/templates/01-worker-session-contract.md` and
`.llm-dev/framework/templates/15-verifier.md` completely. You are the external
Claude verifier for `project-ontos-audit-rebaseline-remediation`, phase D.5.
You are not the orchestrator or fix author. Do not commit, stage, spawn agents,
or edit anything except your one verdict artifact.

Read, in order:

1. `docs/reviews/project-ontos-audit-rebaseline-remediation/D.3-verdict.md`
2. `docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-fix-summary.md`
3. `docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-scope-audit-recovery.md`
4. `git diff aa41c3982e21b0e0cff6c3c5486f4af9e5e55e05..311b60b6e86abe6d0b5a7ac61e16d07049387707`
5. the changed implementation and regression files named by the summary.

The D.3 preserved-blocker list is empty, but D.4 was explicitly tasked with
CAN-ACT-1/2, CAN-CP-1/2/3, and CAN-ID-1. Verify all six; do not exploit the empty
blocker list to skip them. D.4 is honestly `status: halted` on D4-INFRA-1:
llm-dev v2.0.1 cannot register adopter-local EH-15-A fixtures and manifest-mode
summary lookup is fail-open. Verify that claim directly. If it holds, your body
verdict must be `Request changes` even when every product regression passes.

Use only the pre-created disposable test worktree
`/tmp/project-ontos-d5-claude` for source swaps and pytest. Its HEAD must be
`8d5096eba940aafe1e8b86bdd3a8852961bab815`; halt if dirty at entry. Use
`/tmp/project-ontos-worktrees/project-ontos-audit-rebaseline-remediation/.venv/bin/python`
as the test interpreter; confirm it imports `ontos` from the disposable
worktree. For each group below, run the post-fix selection, restore only the
listed implementation files from pre-fix `aa41c3982e21b0e0cff6c3c5486f4af9e5e55e05`,
rerun the SAME selection with `--cache-clear` and require nonzero, then restore
from HEAD and require the selection to pass again:

- CAN-ACT-1/2 implementation files: `ontos/commands/activate.py`,
  `ontos/core/config.py`. Tests:
  `tests/commands/test_agentic_activation_resilience.py -k 'human_renders_incompatible or human_renders_malformed or json_renders_malformed'`.
- CAN-CP-1/2/3 implementation file:
  `scripts/validate-audit-remediation-registry.py`. Tests:
  `tests/test_audit_remediation_registry_validator.py -k 'issue_158_control_plane or control_plane_finding_id_and_issue_158 or duplicate_lease_lists or malformed_registry_yaml or malformed_child_manifest_yaml'`.
- CAN-ID-1 implementation files: `ontos/commands/rename.py`,
  `ontos/mcp/rename_tool.py`. Tests:
  `tests/commands/test_rename.py tests/mcp/test_rename_document.py -k 'rename_invalid_ids_use_canonical or rename_invalid_id_is_rejected_before_project_discovery or build_rename_plan_uses_canonical or rename_document_invalid_ids_use_canonical or rename_document_rejects_invalid_id_before_preflight'`.

`git restore --source <sha> -- <listed-files>` is authorized only inside this
disposable worktree for the verification swap. Do not use it in the lifecycle
worktree. Record exact commands and pre/post exit codes. Restore the disposable
worktree to clean HEAD before reporting.

Then run in the disposable worktree:

```bash
PY=/tmp/project-ontos-worktrees/project-ontos-audit-rebaseline-remediation/.venv/bin/python
$PY -m pytest tests/ -q -p no:cacheprovider
```

From the lifecycle worktree, also run local and external registry parity,
changed-path scope from `bf91b42...`, manifest conformance, `git diff --check
HEAD`, and both EH-15-A probes from the D.4 summary (manifest mode and explicit
summary path). Distinguish functional success from certification.

Write only
`docs/reviews/project-ontos-audit-rebaseline-remediation/D.5-claude-verifier.md`.
Use Template 15 frontmatter with `id: audit-rb-D5-cv`, `phase: D.5`,
`role: verifier`, `family: claude`, `evidence_mode: direct-run`,
`status: completed`, and `verdict: Request Further Fixes`. Include an H1, a
six-row per-finding verification table, regression/scope checks, D4-INFRA-1 as
the required-further-action row, and exact `## Verdict` followed by bare
`Request changes`. Do not claim D.6, child certification, merge, or release.
