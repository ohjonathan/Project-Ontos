---
id: project_ontos_audit_remediation_release_line_tracker
type: tracker
status: active
meta_cycle_id: project-ontos-audit-remediation-2026-07
owner: meta-orchestrator (codex rebaseline, 2026-07-10)
depends_on:
  - project-ontos-codex-audit-revalidation-2026-07
---

# Release-line tracker — project-ontos-audit-remediation-2026-07

Cross-deliverable custody artifact for issues #146–#157 and epic #158. The sole
machine-readable authority is
`manifests/project-ontos-audit-remediation-registry.yaml`; O4 and O5 below are
human renderings checked by `scripts/validate-audit-remediation-registry.py`.
Finding state, release placement, or lease ownership must be changed in the
registry first and then reflected here.

## O4 — Cross-deliverable verification ledger

`status` and `lifecycle_state` are separate axes. In particular, a GitHub issue
may be closed and its code may be fixed while lifecycle evidence remains pending.
Only `strict_p3_review_complete` is certified. An explicit emergency waiver is a
non-certified terminal state and must never be relabeled as strict P3.

| Deliverable ID | Issue | Default release | Severity | Lifecycle state | GitHub | Base / implementation | Finding states | Current truth |
|---|---:|---|---:|---|---|---|---|---|
| `project-ontos-audit-serializer-corruption` | #146 | v4.7.1 | P0 | `code_fixed_evidence_pending` | open; M1 | base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`; implementation `b6f89d77e7fb684b8bd9a181a24c773d5777397a` | code_fixed_evidence_pending=1; implemented_committed_verification_pending=1 | Safe serializer, ID validation, and writer regressions are committed; no terminal child-lifecycle evidence exists. |
| `project-ontos-audit-doctor-rce` | #147 | v4.7.1 | P1 | `code_fixed_evidence_pending` | open; M1 | base `c8672e90f2382f4147ef61b4fba918969483e73e`; implementation `03c36e6ac999d2c411c13252baa2e8fcff60e6ed` | code_fixed=2 | Security fix and five regressions are present; zero strict-P3 receipts; issue reopened with the evidence-pending contract. |
| `project-ontos-audit-relN-quick-wins` | #148 | v4.8.0 | P1 | `partial_implementation_committed_lifecycle_pending` | open; M2 | base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`; implementation `b6f89d77e7fb684b8bd9a181a24c773d5777397a` | confirmed_open=6; implemented_committed_verification_pending=6 | Five originals are implemented; six remain open. Selected v4.7.1 pull-forwards remain separately recorded on finding rows. |
| `project-ontos-audit-relN-sweep` | #149 | v4.8.0 | P1 | `partial_implementation_committed_lifecycle_pending` | open; M2 | base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`; implementation `b6f89d77e7fb684b8bd9a181a24c773d5777397a` | confirmed_open=18; implemented_committed_verification_pending=2; partial_implementation_committed_verification_pending=1 | P1-containing. Required-version activation is implemented; the broad sweep remains open. |
| `project-ontos-audit-characterization-tests` | #150 | v4.8.0 | P2 | `partial_implementation_committed_lifecycle_pending` | open; M2 | base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`; implementation `b6f89d77e7fb684b8bd9a181a24c773d5777397a` | confirmed_open=4; implemented_committed_verification_pending=9; partial_implementation_committed_verification_pending=3 | Eight originals are implemented and three are partial; the R2 hermeticity prerequisite is a v4.7.1 pull-forward. |
| `project-ontos-audit-parser-consolidation` | #151 | v4.8.0 | P1 | `implementation_committed_lifecycle_pending` | open; M2 | base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`; implementation `b6f89d77e7fb684b8bd9a181a24c773d5777397a` | implemented_committed_verification_pending=6 | All five original rows plus lifecycle-type enumeration are implemented; child lifecycle certification remains pending. |
| `project-ontos-audit-writepath-bodyref` | #152 | v4.8.0 | P1 | `implementation_committed_lifecycle_pending` | open; M2 | base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`; implementation `b6f89d77e7fb684b8bd9a181a24c773d5777397a` | implemented_committed_verification_pending=6 | All six graph/link and formatting-preservation rows are implemented; child lifecycle certification remains pending. |
| `project-ontos-audit-mcp-dispatch-rename` | #153 | v4.8.0 | P1 | `partial_implementation_committed_lifecycle_pending` | open; M2 | base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`; implementation `b6f89d77e7fb684b8bd9a181a24c773d5777397a` | confirmed_open=7; implemented_committed_verification_pending=4; partial_implementation_committed_verification_pending=1 | Duplicate writes and all three owned R2 rows are implemented; durable crash recovery remains open. |
| `project-ontos-audit-exitcode-envelope` | #154 | v4.9.0 | P1 | `partial_implementation_committed_lifecycle_pending` | open; M3 | base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`; implementation `b6f89d77e7fb684b8bd9a181a24c773d5777397a` | confirmed_open=3; implemented_committed_verification_pending=10; partial_implementation_committed_verification_pending=1 | Ten originals are implemented, one is partial, and three remain open; this is not a completed schema-version release. |
| `project-ontos-audit-cli-command-table` | #155 | v4.9.0 | P2 | `partial_implementation_committed_lifecycle_pending` | open; M3 | base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`; implementation `b6f89d77e7fb684b8bd9a181a24c773d5777397a` | partial_implementation_committed_verification_pending=1 | Declarative discovery/order substrate exists; registrar and handler boilerplate remain. |
| `project-ontos-audit-precommit-rewire-slim` | #156 | v4.8.0 | P1 | `partial_implementation_committed_lifecycle_pending` | open; M2 | base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`; implementation `b6f89d77e7fb684b8bd9a181a24c773d5777397a` | confirmed_open=3; implemented_committed_verification_pending=2 | Runtime/CI rewire defaults to v4.8.0; three archive/slimming finding rows remain assigned to v4.9.0. |
| `project-ontos-audit-graph-traversal` | #157 | v4.9.0 | P2 | `implementation_committed_lifecycle_pending` | open; M3 | base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`; implementation `b6f89d77e7fb684b8bd9a181a24c773d5777397a` | implemented_committed_verification_pending=2 | Both iterative-depth and case-insensitive path rows are implemented with focused regressions; child lifecycle certification remains pending. |

### Active blockers

- #146's code fix is committed in I0 (`b6f89d7`). Provider-limited
  authorization permits honest continuation; that integration commit and its
  focused tests do not complete the missing child review seats or certify
  release.
- #147 is code-fixed but not release-certified. The old B.1/D.2/D.5 prose was
  not wrapper-dispatched, the receipt inventory is empty, and no receipt may be
  reconstructed. Run a fresh review chain over `c8672e9..03c36e6`.
- Tests were not hermetic at the revalidation baseline. Umbrella I1
  (`05b090d`) now passes a detached full replay (`1679 passed`) with empty
  porcelain before and after, and unchanged map bytes/mtime on a second
  generation. This closes the umbrella clean-snapshot gate, not the remaining
  Windows, publishing, child-lifecycle, or shared-tree release gates.
- Seven original rows remain only partially implemented. In particular,
  exception rollback is not durable crash recovery and the command registry is
  substrate rather than a completed boilerplate removal.
- `shared_tree_integration.status` is `unproven_rebaseline_integration` and
  release-blocking. The structural collision graph is valid, but this shared
  I0 commit cannot retroactively prove that #146/#148–#157 held leases in the
  required order; each deliverable still needs a base-SHA scope receipt from
  an isolated review diff. This umbrella lifecycle does not certify the child
  issues.

External parity was synchronized on 2026-07-10: #147 is open with the evidence-
pending contract; #148/#149 are on milestone 2; #149 is P1-containing; R2 rows
are present on their owner issues; #156 is on milestone 2 with its v4.8/v4.9
split recorded; and epic #158 reflects the revised release line. Original
finding checkboxes remain unchecked except for the two historically merged-and-
verified #147 rows. All I0-backed evidence-pending, implemented, and partial
rows remain unchecked, so the registry's committed-but-uncertified statuses do
not claim external completion.

## O5 — Cross-deliverable scope-lock manifest

### Base-SHA and changed-path policy

Every program has an immutable review `base_sha` in the registry. Before Phase C,
run the framework scope verifier from a dedicated worktree:

```bash
bash .llm-dev/framework/scripts/verify-changed-path-scope.sh \
  --manifest <deliverable-manifest> \
  --base <registry-base_sha>
```

That gate unions committed changes since the base, staged changes, unstaged
changes, and untracked files. Bare `git diff` or branch-name equality is not an
acceptable scope proof. If the deliverable rebases after review, update the
registry base, re-run the relevant review over the new diff, and record the
rebase checkpoint; never silently move the base underneath existing evidence.
The registry validator additionally requires every finding path to be contained
by its owning program and requires the #146/#147 program scopes to equal their
normalized deliverable-manifest scopes.

### Shared-path leases

One program owns a shared path at a time. The issue order below is normative;
later work may not dispatch until earlier work releases the path. The table is
derived from intended implementation paths as well as the audit's primary file,
so it deliberately includes collisions the old O5 omitted.

| Shared path | Programs | Order | Policy |
|---|---|---|---|
| `docs/logs/` | #146, #147 | #146 → #147 | ordered |
| `.github/workflows/` | #148, #156 | #148 → #156 | ordered |
| `ontos/core/schema.py` | #146, #151 | #146 → #151 | ordered |
| `ontos/io/yaml.py` | #146, #151 | #146 → #151 | ordered |
| `ontos/commands/promote.py` | #146, #151, #152 | #146 → #151 → #152 | ordered |
| `ontos/commands/migrate.py` | #146, #152 | #146 → #152 | ordered |
| `ontos/mcp/writes.py` | #146, #152, #153, #154 | #146 → #152 → #153 → #154 | ordered |
| `ontos/commands/log.py` | #148, #151 | #148 → #151 | ordered |
| `ontos/commands/activate.py` | #148, #149 | #148 → #149 | ordered |
| `ontos/commands/doctor.py` | #147, #149 | #147 → #149 | ordered |
| `ontos/commands/link_check.py` | #148, #154 | #148 → #154 | ordered |
| `ontos/commands/map.py` | #148, #149, #154 | #148 → #149 → #154 | ordered |
| `ontos/core/config.py` | #148, #149 | #148 → #149 | ordered |
| `ontos/core/context.py` | #148, #153 | #148 → #153 | ordered |
| `ontos/core/frontmatter_edit.py` | #148, #151, #152 | #148 → #151 → #152 | ordered |
| `ontos/core/git.py` | #148, #150 | #148 → #150 | ordered |
| `ontos/mcp/portfolio_config.py` | #148, #149 | #148 → #149 | ordered |
| `ontos/cli.py` | #149, #154, #155 | #149 → #154 → #155 | ordered |
| `ontos/commands/consolidate.py` | #149, #154 | #149 → #154 | ordered |
| `ontos/core/paths.py` | #149, #150 | #149 → #150 | ordered |
| `ontos/mcp/tools.py` | #149, #151, #153, #154 | #149 → #151 → #153 → #154 | ordered |
| `ontos/commands/query.py` | #150, #154 | #150 → #154 | ordered |
| `ontos/commands/verify.py` | #151, #154 | #151 → #154 | ordered |
| `ontos/core/body_refs.py` | #151, #152 | #151 → #152 | ordered |
| `ontos/core/link_diagnostics.py` | #151, #152, #154 | #151 → #152 → #154 | ordered |
| `ontos/mcp/server.py` | #153, #154 | #153 → #154 | ordered |
| `ontos/core/graph.py` | #154, #157 | #154 → #157 | ordered |
| `tests/` | #146, #147, #148, #149, #150, #151, #152, #153, #154, #155, #156, #157 | #146 → #147 → #150 → #148 → #149 → #151 → #152 → #153 → #154 → #155 → #156 → #157 | #150 owns shared characterization infrastructure; every other program uses a uniquely named regression file and may not edit another program's test. |

Only #146 currently holds an active product-code lease while its I0
implementation is reviewed. #147 is evidence-only; its implementation diff is
frozen at `03c36e6`. Other programs are committed in I0 and marked
integration-pending, not retroactively certified as having held collision-free
leases. They must be split and reviewed from their recorded base SHA before
release; future simultaneous ownership remains forbidden by the order above.

## Revised release sequence

### v4.7.1 — trustworthy hotfix

- Hermetic tests and a clean-tree postcondition.
- #146 serializer P0, string-ID validation, central writer hardening, safe CLI
  logging, and the exact-argv #147 evidence refresh.
- Required-version activation and exact TestPyPI/wheel provenance.
- No broad #148/#149 sweep and no tag until product, scope, lifecycle, and clean
  workspace gates all pass.

### v4.8.0 — consolidation

- #150 first, then #151–#153.
- Broad #148/#149 work, cross-platform locking/Windows CI, exhaustive lifecycle
  types, non-mutating read-only MCP, and the hook/CI rewire half of #156.

### v4.9.0 — contracts and structural debt

- #154, then #155; #157 remains isolated.
- Archive extraction and remaining repository slimming from #156 after the new
  runtime path has proven stable.

## Parity and update discipline

Run local parity after every registry or ledger edit:

```bash
python3 scripts/validate-audit-remediation-registry.py
```

Before release, also require external parity:

```bash
python3 scripts/validate-audit-remediation-registry.py --require-external-parity
```

The external mode queries live issues #146–#158 through authenticated `gh` and
fails when state, milestone, severity label, finding checklist mapping, or
checkbox completion disagrees with the canonical registry. It also validates
the stored count snapshot; registry booleans alone are not external evidence.
Only the meta-cycle updates O4/O5; per-deliverable lifecycle sessions update
their own tracker and report state back without directly editing this file.

## Change log

- 2026-07-03 — initialized O4/O5 for the meta-cycle.
- 2026-07-09 — reconciled the merged #147 code and disclosed missing receipts.
- 2026-07-10 — re-baselined against `bf91b42`; made the registry canonical;
  rebuilt the collision graph; reopened #147 as `code_fixed_evidence_pending`;
  corrected #149 to P1-containing; replaced bare-diff/branch gates with base-SHA
  changed-path policy; adopted the v4.7.1/v4.8.0/v4.9.0 sequence above; and
  recorded #146 plus all R2 implementations as uncommitted/uncertified at the
  pre-I0 checkpoint rather than assigning synthetic fix commits. GitHub parity
  then synchronized #147,
  #148, #149, the R2 owner checklists, and epic #158.
- 2026-07-10 — reconciled committed integration snapshot I0: 40 original rows are
  implemented-committed pending, seven are partial-committed pending, and 41
  remain open; bound the 57 I0-backed rows to `b6f89d7`, added the previously
  omitted activation/doctor collisions, and preserved the noncertified
  shared-tree and per-issue lifecycle states.
- 2026-07-10 — froze umbrella Phase C successor I1 at `05b090d`; closed
  lifecycle-local C-FZ-1–10; passed local/live registry parity, the 433-path
  base-SHA scope gate, stable double map generation, and a detached clean full
  replay (`1679 passed`). Product O4 rows remain I0-pinned, and
  `shared_tree_integration` remains release-blocking.
