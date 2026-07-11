# D.5 independent GLM verifier

Read `.llm-dev/framework/templates/01-worker-session-contract.md` and
`.llm-dev/framework/templates/15-verifier.md` completely. You are the external
GLM verifier for `project-ontos-audit-rebaseline-remediation`, phase D.5,
routed through the attested Neuralwatt OpenCode GLM-5.2 profile. You are not the
orchestrator or fix author. Do not commit, stage, spawn agents, or edit anything
except the sibling review file named below. This is a round-2 provenance repair:
the prior run verified the product behavior but wrote the canonical artifact
directly, which does not satisfy the OpenCode wrapper-capture contract.

Consume the committed D.3 verdict, D.4 fix summary, D.4 scope recovery, manifest,
and code/test diff from `aa41c3982e21b0e0cff6c3c5486f4af9e5e55e05` to I2
`311b60b6e86abe6d0b5a7ac61e16d07049387707`. Verify all six canonical
should-fixes CAN-ACT-1/2, CAN-CP-1/2/3, and CAN-ID-1; the empty D.3 blocker list
does not waive them. Verify D4-INFRA-1 directly. If it holds, return
`Request changes` even when product tests pass.

Use only these two orchestrator-prepared, plain snapshots inside the served
repository; neither contains a `.git` pointer, so no sandbox-external git access
is needed:

- post-fix: `.venv/d5-glm-post`
- same tests with only the five target implementation files restored from
  pre-fix `aa41c39`: `.venv/d5-glm-pre`

Use repository-relative commands only: from each snapshot directory the test
interpreter is `../bin/python`. Do not expand these paths to `/tmp/...`; the
OpenCode permission broker treats absolute ignored-directory paths as external
even though the directories sit under the served workspace. Confirm
`ontos.__file__` resolves under the snapshot whose tests you are running. For
each group, run the identical selection in `d5-glm-post` and
require pass, then in `d5-glm-pre` and require nonzero. Use `-B` plus
`--cache-clear` on every focused invocation; do not combine `--cache-clear` with
`-p no:cacheprovider` because that removes the option's owning plugin:

1. `ontos/commands/activate.py ontos/core/config.py` with
   `tests/commands/test_agentic_activation_resilience.py -k 'human_renders_incompatible or human_renders_malformed or json_renders_malformed'`.
2. `scripts/validate-audit-remediation-registry.py` with
   `tests/test_audit_remediation_registry_validator.py -k 'issue_158_control_plane or control_plane_finding_id_and_issue_158 or duplicate_lease_lists or malformed_registry_yaml or malformed_child_manifest_yaml'`.
3. `ontos/commands/rename.py ontos/mcp/rename_tool.py` with
   `tests/commands/test_rename.py tests/mcp/test_rename_document.py -k 'rename_invalid_ids_use_canonical or rename_invalid_id_is_rejected_before_project_discovery or build_rename_plan_uses_canonical or rename_document_invalid_ids_use_canonical or rejects_invalid_id_before_preflight'`.

The bounded group-3 selector avoids a false secret-scanner match on a long
pytest identifier while selecting the same regression set.
Do not quote individual pytest function names in the review; record the group
selection, counts, exit codes, and behavioral failures instead.

Do not edit either snapshot. Run the full `tests/` suite in `d5-glm-post` with
`-q -p no:cacheprovider`. From the lifecycle worktree,
run registry local/external parity, changed-path scope, manifest conformance,
`git diff --check HEAD`, plus the summary's manifest-mode and absolute
explicit-path EH-15-A probes. Record exact commands and evidence; do not call an
expected nonzero pre-fix or infrastructure probe a test-harness failure.

OpenCode provenance constraint: do not write or edit the canonical artifact
`docs/reviews/project-ontos-audit-rebaseline-remediation/D.5-glm-verifier.md`.
Write the complete verdict-shaped review only to
`docs/reviews/project-ontos-audit-rebaseline-remediation/.raw/audit-rb-D5-glv.review.md`.
After writing and validating it, emit exactly this write notice so the wrapper
can discover and promote the sibling file:
`Wrote \`docs/reviews/project-ontos-audit-rebaseline-remediation/.raw/audit-rb-D5-glv.review.md\``

Use Template 15 frontmatter with
`id: audit-rb-D5-glv`, `phase: D.5`, `role: verifier`, `family: glm`,
`evidence_mode: direct-run`, `status: completed`, and
`verdict: Request Further Fixes`. Include an H1, six finding rows, full smoke
and scope results, D4-INFRA-1 required action, and exact `## Verdict` followed
by bare `Request changes`. Do not claim D.6, per-child certification, merge,
publication, or release readiness.
