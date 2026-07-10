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

| Deliverable | Issue | Release | Severity | Lifecycle state | GitHub | Base / implementation | Current truth |
|---|---:|---|---:|---|---|---|---|
| serializer corruption | #146 | v4.7.1 | P0 | `code_fixed_evidence_pending` | open; M1 | base `bf91b42`; uncommitted working tree | Safe serializer, ID validation, and writer regressions are implemented and focused tests pass; no fix commit or terminal lifecycle evidence exists. |
| doctor RCE | #147 | v4.7.1 | P1·sec | `code_fixed_evidence_pending` | open; M1 | base `c8672e9`; fix `03c36e6` | Exact-argv fix and five regressions are present; zero strict-P3 receipts; issue reopened with the evidence-pending contract. |
| quick wins | #148 | v4.8.0 (selected hotfix items v4.7.1) | P1 | `partial_implementation_uncommitted_lifecycle_pending` | open; M2 | base `bf91b42`; uncommitted tree | Five originals are implemented; six remain open. Secure writer/log/config and TestPyPI work are present but uncertified. |
| docs/dead-code sweep | #149 | v4.8.0 (activation item v4.7.1) | **P1-containing** | `partial_implementation_uncommitted_lifecycle_pending` | open; M2 | base `bf91b42`; uncommitted tree | Required-version activation is implemented; packaged-hook repair is partial; the broad sweep remains open. |
| characterization tests | #150 | v4.8.0 (hermeticity prerequisite v4.7.1) | P2 + R2 P1 | `partial_implementation_uncommitted_lifecycle_pending` | open; M2 | base `bf91b42`; uncommitted tree | Eight originals are implemented and three are partial; hermeticity is implemented but still needs the clean-clone gate. |
| parser consolidation | #151 | v4.8.0 (safe log serialization v4.7.1) | P1 | `implementation_uncommitted_lifecycle_pending` | open; M2 | base `bf91b42`; uncommitted tree | All five original rows plus lifecycle-type enumeration are implemented; no fix commit or lifecycle certification exists. |
| write-path/body refs | #152 | v4.8.0 | P1 | `implementation_uncommitted_lifecycle_pending` | open; M2 | base `bf91b42`; uncommitted tree | All six graph/link and formatting-preservation rows are implemented; no fix commit or lifecycle certification exists. |
| MCP dispatch/rename | #153 | v4.8.0 (secure writer v4.7.1) | P1 | `partial_implementation_uncommitted_lifecycle_pending` | open; M2 | base `bf91b42`; uncommitted tree | Duplicate writes and all three owned R2 rows are implemented; durable crash recovery and broader rename work remain. |
| exit-code/envelope | #154 | v4.9.0 | P1 | `partial_implementation_uncommitted_lifecycle_pending` | open; M3 | base `bf91b42`; uncommitted tree | Ten originals are implemented, one is partial, and three remain open; this is not a completed schema-version release. |
| CLI command table | #155 | v4.9.0 | P2 | `partial_implementation_uncommitted_lifecycle_pending` | open; M3 | base `bf91b42`; uncommitted tree | Declarative discovery/order substrate exists; registrar and handler boilerplate remain. |
| pre-commit rewire / slim | #156 | v4.8.0 rewire; v4.9.0 archive | P1 | `partial_implementation_uncommitted_lifecycle_pending` | open; M2 | base `bf91b42`; uncommitted tree | The two runtime/CI shadowing rows are implemented; archive extraction and churn work remain. |
| graph traversal | #157 | v4.9.0 | P2 | `implementation_uncommitted_lifecycle_pending` | open; M3 | base `bf91b42`; uncommitted tree | Both iterative-depth and case-insensitive path rows are implemented with focused regressions; no fix commit exists. |

### Active blockers

- #146's code fix is present only in the uncommitted working tree. Provider-
  limited authorization permits honest continuation; focused tests do not
  create a fix commit, complete the missing review seats, or certify release.
- #147 is code-fixed but not release-certified. The old B.1/D.2/D.5 prose was
  not wrapper-dispatched, the receipt inventory is empty, and no receipt may be
  reconstructed. Run a fresh review chain over `c8672e9..03c36e6`.
- Tests were not hermetic at the revalidation baseline. Isolation and clean-
  tree gates are now implemented, but a green suite is not a release signal
  until a clean-clone full run proves both tracked and untracked state remain
  clean.
- Seven original rows remain only partially implemented. In particular,
  exception rollback is not durable crash recovery and the command registry is
  substrate rather than a completed boilerplate removal.
- `shared_tree_integration.status` is `unproven_rebaseline_integration` and
  release-blocking. The structural collision graph is valid, but this shared
  dirty tree cannot retroactively prove that #146/#148–#157 held leases in the
  required order; each deliverable still needs a base-SHA scope receipt from an
  isolated review diff.

External parity was synchronized on 2026-07-10: #147 is open with the evidence-
pending contract; #148/#149 are on milestone 2; #149 is P1-containing; R2 rows
are present on their owner issues; #156 is on milestone 2 with its v4.8/v4.9
split recorded; and epic #158 reflects the revised release line. Original
finding checkboxes remain unchecked by policy until work is merged and
verified; the registry's uncommitted statuses therefore do not claim external
completion.

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

| Shared path | Programs | Lease order / policy |
|---|---|---|
| `docs/logs/` | #146, #147 | #146 lifecycle/log scope → #147 historical merge-log evidence. |
| `.github/workflows/` | #148, #156 | #148 publication hardening → #156 CI/runtime rewire. |
| `ontos/core/schema.py` | #146, #151 | #146 → #151. |
| `ontos/io/yaml.py` | #146, #151 | #146 → #151. |
| `ontos/commands/promote.py` | #146, #151, #152 | #146 → #151 → #152. |
| `ontos/commands/migrate.py` | #146, #152 | #146 → #152. |
| `ontos/mcp/writes.py` | #146, #152, #153, #154 | #146 → #152 → #153 → #154. |
| `ontos/commands/log.py` | #148, #151 | #148's configured-path hotfix → #151 parser/log consolidation. |
| `ontos/commands/activate.py` | #148, #149 | #148 activation/count work → #149 required-version activation. |
| `ontos/commands/doctor.py` | #147, #149 | #147 exact-argv implementation/evidence freeze → #149 PATH-version diagnostics. |
| `ontos/commands/link_check.py` | #148, #154 | #148 count basis → #154 contract work. |
| `ontos/commands/map.py` | #148, #149, #154 | #148 → #149 → #154. |
| `ontos/core/config.py` | #148, #149 | #148 type validation → #149 activation/dead-key follow-up. |
| `ontos/core/context.py` | #148, #153 | Secure writer/encoding work completes before #153 transactional consolidation. |
| `ontos/core/frontmatter_edit.py` | #148, #151, #152 | #148 strict decoding → #151 parser consolidation → #152 write-path unification. |
| `ontos/core/git.py` | #148, #150 | #148 trackedness fix → #150 characterization. |
| `ontos/mcp/portfolio_config.py` | #148, #149 | #148 neutral defaults → #149 cleanup. |
| `ontos/cli.py` | #149, #154, #155 | #149 cleanup → #154 contract → #155 declarative registry. |
| `ontos/commands/consolidate.py` | #149, #154 | #149 semantics/docs cleanup → #154 envelope contract. |
| `ontos/core/paths.py` | #149, #150 | #150 characterizes user-mode paths before #149 removes compatibility debt. |
| `ontos/mcp/tools.py` | #149, #151, #153, #154 | #149 cleanup → #151 exhaustive type enumeration → #153 read-only enforcement → #154 response contract. |
| `ontos/commands/query.py` | #150, #154 | #150 characterization → #154 envelope contract. |
| `ontos/commands/verify.py` | #151, #154 | #151 canonical loader → #154 structured response. |
| `ontos/core/body_refs.py` | #151, #152 | #151 fence/line semantics → #152 reference rewrite behavior. |
| `ontos/core/link_diagnostics.py` | #151, #152, #154 | #151 → #152 → #154. |
| `ontos/mcp/server.py` | #153, #154 | #153 dispatch consolidation → #154 contract. |
| `ontos/core/graph.py` | #154, #157 | #154 diagnostics contract → #157 traversal rewrite. |
| `tests/` | #146, #147, #148, #149, #150, #151, #152, #153, #154, #155, #156, #157 | #146 → #147 → #150 → #148 → #149 → #151 → #152 → #153 → #154 → #155 → #156 → #157 for shared infrastructure. #150 owns characterization helpers; all others use unique regression files and may not edit a sibling's test. |

Only #146 currently holds an active product-code lease while its uncommitted
implementation is verified. #147 is evidence-only; its implementation diff is
frozen at `03c36e6`. Other programs contain rebaseline-time uncommitted
implementations and are marked integration-pending, not retroactively certified
as having held collision-free leases. They must be split/reviewed from their
recorded base SHA before release; future simultaneous ownership remains
forbidden by the order above.

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
  recorded #146 plus all R2 implementations as uncommitted/uncertified rather
  than assigning synthetic fix commits. GitHub parity then synchronized #147,
  #148, #149, the R2 owner checklists, and epic #158.
- 2026-07-10 — reconciled the expanded working tree: 40 original rows are now
  implemented-uncommitted, seven are partial-uncommitted, and 41 remain open;
  added the previously omitted activation/doctor collisions and kept all
  uncommitted rows free of synthetic fix commits or certification claims.
