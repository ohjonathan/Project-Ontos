---
id: project-ontos-codex-audit-revalidation-2026-07
type: review
status: complete
depends_on:
  - project-ontos-fable-repo-audit-2026-07
---

# Codex revalidation of the 2026-07 Fable repository audit

Revalidation baseline: `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95` (`main` on
2026-07-10). Historical audit baseline: `589d919`. This document is an addendum,
not a rewrite of the Fable report. The canonical machine-readable finding and
assignment register is
`manifests/project-ontos-audit-remediation-registry.yaml`.

Implementation snapshot I0 is
`b6f89d77e7fb684b8bd9a181a24c773d5777397a`. It commits the integrated
post-baseline work for review; it does not supply historical per-deliverable
lease receipts, strict-P3 child certification, merge evidence, or release
authority.

## Executive verdict

The Fable audit is a useful, high-signal defect baseline for `589d919`; it is not
the live status authority for later commits. Its concrete findings were generally
reproducible, but its release roadmap, review-provenance claims, grade, and model
attribution are not sufficiently reproducible to be release gates.

| Claim | Revalidation result |
|---|---|
| The merged report was 1,308 lines and contains 1 P0, 27 P1, and 63 P2 findings. | Confirmed for the pre-addendum artifact. The required current-status pointer adds lines, but the register still has 91 unique `### D…` headings with that exact severity distribution. |
| Issues #146–#157 assign all 91 findings exactly once. | Confirmed from the issue bodies observed 2026-07-10: no missing, duplicate, extra, or severity-mismatched original IDs. |
| Report §5 is the complete finding-to-work-stream roadmap. | Refuted. Expanded literally, it mentions 68 of the 91 confirmed IDs and also cites `D6a-test-gaps-3`, which is not a registered finding. |
| The release-line, dispatch, and #147 artifacts are uncommitted. | Obsolete. Those artifacts and the #147 code landed through PR #160 and are reachable from `bf91b42`. |
| `D2b-roundtrip-3` is a live P0. | Confirmed at `bf91b42`. The safe serializer/ID/write-path implementation is committed in I0 (`b6f89d7`); its current state remains `code_fixed_evidence_pending`, not lifecycle-certified or released. |
| The doctor RCE is remediated. | Code-fixed, evidence-pending. Commit `03c36e6` validates the complete managed `serve --workspace <root> [--read-only]` argv and five focused regressions pass. Existing lifecycle artifacts have no wrapper receipts and do not certify strict P3. |
| O5 prevents cross-deliverable collisions. | Refuted. The old table omitted or misassigned numerous collisions, including `commands/map.py`, `commands/log.py`, `core/context.py`, `core/git.py`, `core/config.py`, `core/paths.py`, `mcp/tools.py`, `mcp/writes.py`, `mcp/server.py`, `commands/query.py`, `commands/verify.py`, `core/link_diagnostics.py`, and shared test infrastructure. |
| Three independent reviewers reproduced every finding; C+ is the repository grade; per-model attribution is reliable. | Not independently auditable from repository evidence. These may be useful narrative context but must not determine release state. |

At the revalidation baseline, `D4b-trust-1` and `D4b-trust-2` are code-fixed;
the other 89 original findings remain open. The observed suite result was `1447
passed, 2 skipped`, but that green result is overstated until the suite proves it
leaves a clean tracked and untracked workspace.

The shared post-baseline integration snapshot I0 contains a code fix for
`D2b-roundtrip-3`, complete implementations for 40 other original findings,
partial implementations for seven, and implementations for all nine R2
findings. Those 57 I0-backed rows bind their fix reference to `b6f89d7`. The
91-row original register therefore currently partitions into 2 historical
code-fixed, 1 code-fixed/evidence-pending, 40 implemented-committed pending, 7
partial-committed pending, and 41 confirmed-open rows. Product rows remain
verification/lifecycle pending; the control-plane row alone is
`implemented_committed_verification_pending`. These states do not revise the
historical `bf91b42` verdict or imply lifecycle certification, historical lease
proof, merge, release, or per-issue completion.

## Pressure-test method and evidence

- Parsed every finding heading from the source report and compared its severity
  with the corresponding issue body for #146–#157.
- Inspected the report roadmap separately from the issue assignment map; the two
  are not equivalent, and the roadmap's phantom `D6a-test-gaps-3` must not be
  promoted into the registry.
- Compared the #146 and #147 manifests, trackers, specs, review inventories,
  final approval, retro, merged code, and focused regressions.
- Diffed the actual primary and intended implementation paths by work-stream to
  reconstruct the shared-path collision graph rather than trusting the old O5
  table.
- Reproduced the activation-skew symptom in this checkout: the PATH-level
  `ontos activate` reported `not_usable`, an existing map, and zero loaded
  documents, while the repository-local lifecycle wrapper's `doctor` passed.
- Treated test-created repository files and context-map mutation as correctness
  failures, not harmless fixture residue. The diagnostic July 10 `*_init.md`
  file and the tracked recent `*_init.md` files are release-blocking cleanup
  evidence; substantive user-authored untracked documents are not cleanup
  targets.

## New revalidation findings

The IDs below are stable. They are registered alongside the 91 originals and
must not be silently folded into an older ID.

| ID | Severity | Finding | Baseline evidence |
|---|---:|---|---|
| `R2-test-hermeticity-1` | P1 | Tests can write or overwrite live repository logs and `Ontos_Context_Map.md`; a passing suite can leave a dirty checkout. | Test helpers resolve the real checkout, log/map paths are mutable, and the audit run left dated `*_init.md` artifacts plus a modified map. |
| `R2-context-tmp-symlink-1` | P1 | `SessionContext.commit` uses predictable `<target>.tmp` paths and follows a pre-created symlink, enabling an outside-workspace write. | `bf91b42:ontos/core/context.py` derives the deterministic suffix and calls `write_text` before rename. |
| `R2-loader-id-type-1` | P1 | YAML numeric/date/null IDs reach the canonical loader as non-strings; they can crash sorting/string consumers or poison dictionary keys. This widens the serializer P0 beyond the originally named values. | `load_document_from_content` assigns `fm.get('id', path.stem)` directly to `DocumentData.id` without type/pattern validation. |
| `R2-windows-fcntl-import-1` | P1 | The base package imports POSIX-only `fcntl` unconditionally and therefore cannot import on Windows. | `bf91b42:ontos/core/context.py` imports `fcntl` at module import time; the second lock implementation repeated the platform assumption. |
| `R2-lifecycle-type-enumeration-1` | P1 | Valid lifecycle document types are accepted by the canonical enum but omitted from stub creation and the MCP overview type table; the latter omitted roughly 35% of the current corpus. | `DocumentType` contains 16 non-unknown values, while `stub.py` allows five and the MCP `OVERVIEW_TYPES` tuple contains five. |
| `R2-testpypi-provenance-1` | P1 | TestPyPI verification installs an unconstrained `ontos` and publication uses `skip-existing`, so the verified artifact need not be the wheel/version about to reach PyPI. | `bf91b42:.github/workflows/publish.yml` installs `ontos` without the tag version and permits an older TestPyPI artifact to satisfy publication. |
| `R2-activation-version-skew-1` | P1 | A stale global `ontos` can shadow the repository runtime during mandatory activation, and doctor can report the PATH executable as healthy without executing and comparing its version. | PATH activation returned zero documents; `bf91b42:doctor.py` treats `shutil.which('ontos')` as success before invoking `python -m ontos`. |
| `R2-mcp-readonly-export-1` | P2 | `export_graph` can write a caller-selected workspace file even when the server is described as read-only. | `export_graph(export_to_file=…)` creates parents and writes JSON, while the tool remains registered and is annotated non-read-only. |
| `R2-control-plane-parity-1` | P1 process | Roadmap, leases, bare-diff scope checks, GitHub labels/state, and lifecycle prose can disagree without a blocking parity check. | At the revalidation baseline, #149 was titled/labeled P2 despite four P1 rows and #147 was closed while strict evidence was absent; old O5 omitted shared paths; scope gates ignored committed, staged, or untracked changes. |

### Post-baseline implementation evidence

The table groups original rows for readability; the registry retains one row
and its concrete evidence paths per finding.

| Finding(s) | I0 status | Evidence anchors |
|---|---|---|
| `D2b-roundtrip-3` | `code_fixed_evidence_pending` | `tests/core/test_schema.py`; `tests/test_frontmatter_roundtrip_regression.py` |
| `D1a-graph-link-1` through `D1a-graph-link-9` | `implemented_committed_verification_pending` | `tests/core/test_graph.py`; `tests/core/test_body_refs.py`; `tests/core/test_link_diagnostics.py`; `tests/commands/test_rename.py` |
| `D2a-write-safety-2`, `D2a-write-safety-7`, `D2a-write-safety-9`, `D2b-roundtrip-1`, `D2b-roundtrip-4`, `D2b-roundtrip-5`, `D3a-parsers-2`, `D3a-parsers-3`, `D3b-structure-1`, `D3b-structure-2`, `D4a-config-2` | `implemented_committed_verification_pending` | `tests/core/test_git_safety.py`; `tests/test_session_context.py`; `tests/core/test_frontmatter_edit_pipeline.py`; `tests/core/test_frontmatter_repair.py`; `tests/commands/test_log.py`; `tests/core/test_config_phase3.py` |
| `D5a-repo-redundancy-1`, `D5a-repo-redundancy-2`, `D5b-dead-code-7` | `implemented_committed_verification_pending` | `tests/test_ci_release_workflows.py`; `tests/test_test_isolation.py`; `tests/commands/test_agentic_activation_resilience.py`; `tests/commands/test_doctor_phase4.py` |
| `D6a-test-gaps-2`, `D6a-test-gaps-4`, `D6a-test-gaps-6`, `D6a-test-gaps-8`, `D6a-test-gaps-10`, `D6b-test-quality-1`, `D6b-test-quality-5`, `D6b-test-quality-9` | `implemented_committed_verification_pending` | `tests/io/test_git_empty_diff.py`; `tests/commands/test_hook_phase4.py`; `tests/golden/test_golden_master.py`; `tests/io/test_toml_roundtrip.py`; `tests/commands/test_consolidate_parity.py`; `tests/test_test_isolation.py` |
| `D1c-envelope-4`, `D1c-envelope-5`, `D7-cli-consistency-2`, `D7-cli-consistency-3`, `D7-cli-consistency-4`, `D7-cli-consistency-6`, `D7-cli-consistency-7`, `D7-cli-consistency-8`, `D7-cli-consistency-10` | `implemented_committed_verification_pending` | `tests/test_cli_contract_v4.py`; `tests/ui/test_json_output.py`; `tests/commands/test_verify_portfolio.py` |
| `D2a-write-safety-6`, `D3b-structure-6`, `D5a-repo-redundancy-3`, `D6a-test-gaps-7`, `D6a-test-gaps-9`, `D6b-test-quality-6`, `D7-cli-consistency-5` | `partial_implementation_committed_verification_pending` | See the residual-risk list below and the per-row registry evidence. |
| `R2-test-hermeticity-1` | `implemented_committed_verification_pending` | `tests/test_test_isolation.py`; `tests/conftest.py` |
| `R2-context-tmp-symlink-1` | `implemented_committed_verification_pending` | `tests/mcp/test_write_tools.py`; `tests/test_session_context.py` |
| `R2-loader-id-type-1` | `implemented_committed_verification_pending` | `tests/test_document_loading_contract_a1.py` |
| `R2-windows-fcntl-import-1` | `implemented_committed_verification_pending` | `ontos/core/locking.py`; `ontos/mcp/locking.py`; `tests/mcp/test_locking.py`; `tests/test_ci_release_workflows.py` |
| `R2-lifecycle-type-enumeration-1` | `implemented_committed_verification_pending` | `tests/commands/test_stub_parity.py`; `tests/mcp/test_workspace_overview.py` |
| `R2-testpypi-provenance-1` | `implemented_committed_verification_pending` | `tests/test_release_artifact.py`; `tests/test_ci_release_workflows.py` |
| `R2-activation-version-skew-1` | `implemented_committed_verification_pending` | `tests/commands/test_agentic_activation_resilience.py`; `tests/commands/test_doctor_phase4.py`; `tests/commands/test_instruction_protocol.py` |
| `R2-mcp-readonly-export-1` | `implemented_committed_verification_pending` | `ontos/mcp/portfolio.py`; `tests/mcp/test_read_only_registration.py` |
| `R2-control-plane-parity-1` | `implemented_committed_verification_pending` | `scripts/validate-audit-remediation-registry.py`; `tests/test_audit_remediation_registry_validator.py`. I0 added the parity validator, but Phase C falsification proved that provenance, rendered O4/O5 order, and malformed child-manifest roots were not yet fail-closed. Promotion waits for the C-close fix commit and fresh local/external evidence. |

A reconciliation-focused cross-section passed `354` tests; the MCP import-
cleanup suite separately passed `268`, and the final CLI-contract follow-up
passed `90`. Those focused results are evidence for the rows above, not a
substitute for the clean-clone full-suite and lifecycle release gates.

### Residual risk in partially implemented originals

- `D2a-write-safety-6`: caught exceptions roll back prior replacements, but a
  process crash still has no durable journal/recovery protocol.
- `D3b-structure-6`: a declarative registry now owns command discovery/order
  and alias arguments; registrar and handler boilerplate remains.
- `D5a-repo-redundancy-3`: packaged hooks now call the real package CLI, but
  they are still not the files consumed by the installer.
- `D6a-test-gaps-7`: native `query_stale` is pinned, but the other named query
  dispatch branches are not all covered.
- `D6a-test-gaps-9`: tracked/untracked rollback and one git-unavailable branch
  are pinned; the original full fail-closed branch matrix is not.
- `D6b-test-quality-6`: the legacy validation stub was removed with its obsolete
  suite, but `test_cwd_propagation` and `test_clear_cache_works` remain vacuous.
- `D7-cli-consistency-5`: canonical command names and non-empty summary data
  landed, but several tuple-returning commands still lack granular structured
  payloads.

### Adversarial acceptance replay

A second independent pass found four gaps after the first green focused runs;
they were treated as product defects rather than waived test omissions:

- `retrofit` still hand-serialized multiline aliases. It now uses safe YAML,
  reparses the complete document before buffering, and has a public CLI
  multiline regression. This closes the newly exposed P0 writer surface.
- `SessionContext` could swap a validated parent directory for an outside
  symlink and could delete a recovery backup after restoration failed. POSIX
  writes now use pinned no-follow directory handles, and failed restores retain
  and report the backup. This does not claim durable post-process-crash recovery
  for `D2a-write-safety-6`.
- read-only portfolio startup still created config/SQLite/WAL/SHM files. It now
  requires an existing immutable read-only snapshot and performs no create or
  rebuild path.
- generated activation did not try the working repository virtual environment.
  The repository runtime is now first in the documented/executable candidate
  order, ahead of system Python and a stale PATH executable.
- argparse failures and `verify --json` with no target still bypassed/misused
  the schema-v4 usage envelope. Both now emit the documented usage category;
  granular command-owned success payloads remain tracked under the partial
  `D7-cli-consistency-5` row.

The same pass found that publishing promoted an unverified sdist beside the
verified wheel; the workflow now builds and publishes the wheel as the sole
artifact. A focused acceptance replay across frontmatter, migration, MCP writes,
the secure writer, retrofit, read-only portfolio, and activation passed `130`
tests. These follow-up fixes are included in I0 and remain verification- and
lifecycle-pending.

## Current lifecycle truth

### #146 serializer corruption

The safe serializer, string-ID validation, and writer-surface regression net are
present in I0, focused tests pass, and `fix_commit` is `b6f89d7`. Phase B.1
still has one authentic Claude Sonnet wrapper receipt,
one failed GPT dispatch, and a pending Gemini intent with no result. Provider-
limited continuation was authorized on 2026-07-03, but that authorization is not
completion and is not strict-P3 certification. The manifest now declares the
fallback honestly and uses a base-SHA changed-path gate rather than requiring a
branch literally named `main`.

### #147 doctor RCE

The implementation of record is commit
`03c36e6ac999d2c411c13252baa2e8fcff60e6ed`. The current contract compares the
entire expected argv, rejects extra/reordered/duplicated tokens, pins project
scope to the current workspace, and defaults unmanaged probing to disabled. The
focused regression file contains and passes these five cases:

1. a repo-sourced Python payload is not executed;
2. an exact managed launcher still probes successfully;
3. a trusted launcher cannot smuggle another subcommand;
4. a duplicate `--workspace` is rejected; and
5. callers that omit the opt-out remain safe by default.

The former Phase E and final-approval claims are reopened as
`code_fixed_evidence_pending`. The review inventory contains zero strict-P3
receipts; no receipt is reconstructed. Fresh wrapper-dispatched B.1, D.2, and
D.5 evidence is required before certification. A provider-limited outcome may
only close under an explicit emergency-waiver status that remains visibly
distinct from `strict_p3_review_complete`. GitHub issue #147 is reopened with
this evidence-pending contract.

## Revised release line

### v4.7.1 — trustworthy hotfix

- Make tests hermetic and require a post-suite clean tree.
- Fix the serializer P0, validate string IDs, harden the central writer, and
  route CLI logging through configured paths and the safe serializer.
- Re-certify #147 against the exact-argv implementation and five regressions.
- Enforce required-version activation and bind TestPyPI verification to the
  exact wheel/tag. The broad #148/#149 sweeps do not ride this patch.

### v4.8.0 — consolidation

- Land #150's characterization net after hermeticity.
- Consolidate parsing/type enumeration and all document mutation; add
  cross-platform locking and Windows CI.
- Complete #151–#153, make MCP type counts exhaustive, make read-only mode
  non-mutating, and pull the hook/CI rewire half of #156 forward.

### v4.9.0 — contracts and structural debt

- Complete the versioned exit-code/envelope/data contract and the declarative
  CLI registry.
- Finish graph/path correctness and the archive/repository-slimming half of
  #156 after the runtime rewire is proven.

## Release gates

The registry validator is the local parity gate. Release remains blocked unless:

- the report contains exactly the registry's 91 original IDs with severities
  `1/27/63`, and all nine R2 IDs are present once;
- every finding has a root program, issue, release, status, fix reference,
  evidence, allowed paths, lifecycle state, and base SHA;
- all shared-path leases are rendered in O5 and no simultaneously active leases
  overlap;
- every finding scope is contained by its owning program, #146/#147 program
  scopes equal their normalized manifest scopes, every real overlap has exactly
  one lease, and every listed lease participant has a real overlap;
- the shared-tree integration blocker is cleared only after isolated base-SHA
  scope proofs; structural lease parity must not be presented as historical
  lease compliance;
- O4, #149 severity, lifecycle documents, the 100-row issue counts, and live
  GitHub issue state/milestones/labels/checklists agree;
- `verify-changed-path-scope.sh --base <base_sha>` accounts for committed,
  staged, unstaged, and untracked paths;
- lifecycle receipt verification returns a certified terminal status or an
  explicit non-certified emergency waiver;
- focused tests, the full suite, framework checks, and `git diff --check HEAD`
  pass, and the full suite leaves `git status --porcelain` empty.

External parity was synchronized on 2026-07-10: #147 is reopened; #149 is
retitled/relabeled P1-containing; #148/#149 are on Audit Release N+1; R2 rows
are present on #146/#148/#149/#150/#151/#153; and epic #158 carries the revised
release line and mapping. #156 is also on Audit Release N+1 with the v4.8
package-CLI rewire separated from its v4.9 archive/slimming remainder. Both
local and external-parity registry validation now pass. Except for the two
historically merged-and-verified #147 rows, original issue checkboxes
intentionally remain unchecked under the recorded `merged_and_verified_only`
policy. Every I0-backed evidence-pending, implemented, and partial row remains
unchecked: committed-but-uncertified implementation status is tracked in the
registry and ledger, not misrepresented on GitHub as merged completion.
External validation now reads issues #146–#158 live through authenticated `gh`;
the stored synchronization booleans are no longer accepted as sufficient proof.
