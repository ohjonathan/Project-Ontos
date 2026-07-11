---
id: audit-rb-D2-gla
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: D.2
role: alignment
family: glm
evidence_labels_used: [direct-run, static-inspection]
reference_documents_consulted:
  - docs/specs/project-ontos-audit-rebaseline-remediation-spec.md
  - .llm-dev/framework/templates/01-worker-session-contract.md
  - .llm-dev/framework/templates/02-phase-dispatch-handoff.md
  - .llm-dev/framework/templates/04-review-board-alignment.md
  - docs/reference/Migration_v3_to_v4.md
  - docs/reference/Ontos_Manual.md
  - scripts/validate-audit-remediation-registry.py
  - manifests/project-ontos-audit-remediation-registry.yaml
  - .github/workflows/ci.yml
  - .github/workflows/publish.yml
status: completed
---

# Alignment Review — project-ontos-audit-rebaseline-remediation / D.2 / glm

Provenance: independent GLM alignment reviewer, executed through the attested
Neuralwatt/OpenCode GLM-5.2 route (family `glm`). Reviewed spec v1.5 against the
exact Phase C implementation I1 `05b090d53f7b0c9c4afdbb5fb23ab58cdfa01fa0`
(commit "Complete Phase C audit remediation reconciliation"), historical base
`bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`, frozen I0 snapshot
`b6f89d77e7fb684b8bd9a181a24c773d5777397a`, and the current committed evidence
checkpoint (HEAD = I1 on branch `codex/audit-rebaseline-remediation-lifecycle`).
Constraints were re-derived from the approved spec only; tracker conclusions,
B/D verdicts, sibling D.2 reviews, dispatch results, and receipts were not
read. Bounded focused direct-run checks were used; the full suite was not run
and the worktree was preserved.

## 1. Architecture compliance

The I1 Phase C reconciliation implements the architecture described in spec §4
without layer violations:

- Registry / control plane (§4.1): `scripts/validate-audit-remediation-registry.py`
  is the producer + parity gate. `validate()` (line 867) performs structural
  type-validation over the registry root, findings, programs, shared_path_leases,
  shared_tree_integration, github_snapshot counts, and external_drift BEFORE any
  indexing/set/sort/overlap/parity operation. Non-mapping rows are quarantined to
  `errors` and `continue`d (lines 921-923), never raising. Enums
  (`FINDING_STATUSES`, `PROGRAM_LEASE_STATES`, etc.) guard status partition /
  active-lease filtering. `REQUIRED_PROGRAM_ISSUES = set(range(146, 158))` (line 73)
  pins exact #146–#157 membership. `load_yaml` keeps the path lexical so the
  no-follow writer can reject a symlinked root (static-inspection).
- Canonical loader / serializer (§4.2): `serialize_frontmatter` public signature
  preserved; `validate_document_id` (`ontos/core/schema.py:83-97`) raises
  `ValueError` beginning `Document id must be a string`, `Document id must not
  be empty`, and plain-language pattern copy matching the spec literal.
- Safe writer (§4.3): `ontos/core/context.py` captures no-follow
  device/inode/type bindings while the staging descriptor is open
  (`_regular_binding`), revalidates "immediately before use"
  (`_verify_entry_binding`, line 1001), unlinks only the bound entry
  (`_unlink_bound_entry`, line 1182), and re-verifies backups/temps during
  rollback (lines 1252, 1305). `O_NOFOLLOW` exclusive temp create (line 1037).
- CLI/MCP/activation (§4.4): `ontos/command_registry.py` centralizes discovery;
  doctor probes PATH executable version; advisory-lock backend selects
  fcntl/msvcrt without unconditional cross-platform imports
  (`ontos/core/locking.py`); read-only MCP omits write tools
  (`server.py:197-198`), refuses persistent graph export (`tools.py:399`),
  suppresses usage logs (`server.py:1003`), and opens only an existing immutable
  portfolio snapshot (`server.py:1061,1072`); type counts seed every canonical
  type including zero-count (`tools.py:68`).

No import-layer or module-boundary violations found in the reviewed diff.

## 2. Diagram-architecture cross-reference

Spec §10.1 architecture diagram edges are each realized by implementation
anchors cited in §1 and §4 below (Registry→Validator→O4/O5, Serializer→Writer→
CLI/MCP, Activation/Doctor→CLI/MCP, Locking→Writer+CLI/MCP, Release Pipeline→
Tests/Evidence, three EXTERNAL boundaries GitHub/Windows/TestPyPI marked dashed).
Spec §10.2 lifecycle state machine shows the code-first Phase C reconciliation
edge (`B2_CodeFirst_Review → Phase_C_Reconciliation → D1_Implementation_Snapshot
→ D2_PostImpl_Review`) with D.4 retry and the D.6 stop boundary carrying "no
release claim." I1 is precisely the Phase C reconciliation node; the lifecycle
placement is consistent with the diagram. No diagram/prose mismatch found
(static-inspection).

## 3. Roadmap alignment

Spec §1 roadmap targets v4.7.1, v4.8.0, v4.9.0 and frames this deliverable as a
branch-level lifecycle review, explicitly NOT a release. The implementation
matches: no tag/merge/publish/release action is taken in I1; the validator emits
stop-boundary-preserving status (`mode: local`, `confirmed_open=41`,
`partial_committed_pending=7` matching spec §1 evidence baseline) without
certifying per-issue lifecycle or historical O5 lease compliance. Target
releases remain referenced in the registry/workflow as the planned line only.

## 4. Constraint verification

| Constraint | Source (doc:lines) | Verified? | Evidence |
|------------|--------------------|-----------|----------|
| Registry = 91 originals + 9 R2; 41 confirmed_open + 7 partial preserved | spec §1; §2 out-of-scope | Yes | direct-run: `scripts/validate-audit-remediation-registry.py` → PASS, original findings 91, confirmed_open=41, partial=7 |
| Exact #146–#157 program membership | spec §4.1 | Yes | static-inspection: `validate-audit-remediation-registry.py:73` `set(range(146,158))` |
| Quarantine-before-consumers; `main()` exit 1/FAILED never exit 2/ERROR for enumerated cases | spec §4.1, §11 | Yes (enumerated) | direct-run: 194 registry tests pass; `main()` returns 1/FAILED on errors (lines 1894-1898) |
| Eager required_version clause parsing before reduction; clause literal/repr once; identify failing clause | spec §4.4 | Yes | direct-run: `tests/core/test_config_phase3.py` (all pass); static-inspection: `config.py:251-256` builds full list before `all()`; `_version_clause_matches` names clause via `{clause!r}` |
| Invalid range begins `Invalid [ontos].required_version`; both failures point to exact Migration anchor | spec §4.4 | Yes | static-inspection: `config.py:262-280` |
| Activation: shell 1, `E_ACTIVATION_UNUSABLE`, `data.status: not_usable`, `Incompatible Ontos version` | spec §4.4 | Yes | static-inspection: `ontos/commands/activate.py:60,83-95,267` |
| CLI ID via canonical validator + `E_USER_INPUT`; no divergent regex | spec §4.2, §4.4 | Yes | direct-run: `tests/commands/test_stub_parity.py` pass; static-inspection: `stub.py:182-188` removes `_ID_PATTERN`, calls `validate_document_id` |
| Log collision `E_LOG_EXISTS`, no overwrite + recovery hint, exit 1 | spec §4.3 | Yes | direct-run: `tests/commands/test_log.py` pass; static-inspection: `log.py:319-325` |
| Archive marker no-follow + warning `Session log created, but archive marker was not updated:` + exit 3 + `warnings[]` + path retained | spec §4.3 | Yes | direct-run: `tests/commands/test_log.py` pass; static-inspection: `log.py:340-356` |
| Log `logs_dir` kept lexical (no `.resolve()` collapse) before no-follow writer | spec §4.3 | Yes | static-inspection: `log.py:116-119` |
| Workspace lock no-follow + single-link for BOTH `SessionContext.commit` and MCP `workspace_lock` (st_nlink/nNumberOfLinks before backend write) | spec §4.3 | Yes | direct-run: `tests/mcp/test_locking.py` pass; static-inspection: `context.py:1389-1410,1477`; `mcp/locking.py` rewrites `workspace_lock` to use guarded opener + `verify_lock_file_binding` (st_nlink==1 at `locking.py:168,189`); `locking.py` Windows nNumberOfLinks (line 408) |
| Schema-v4 envelope keys + exit taxonomy 0/1/2/3/5/130, code 4 reserved | spec §4.4 | Yes | direct-run: `tests/test_cli_contract_v4.py` pass (incl. `test_exit_code_four_remains_reserved`); static-inspection: `json_output.py:331-344,449-470` |
| Read-only MCP no writes; exhaustive type counts incl. zero | spec §4.4 | Yes | static-inspection: `server.py:197,973-975,1003,1061`; `tools.py:68` |
| One-wheel provenance, TestPyPI exact `ontos==tag --no-deps`, manifest compare, OIDC permission only to publisher jobs | spec §4.5 | Yes | static-inspection: `publish.yml` builds one wheel, records hash, verify-wheel downloads `--no-deps ontos==${expected_version}`; top-level OIDC permission removed and granted only on TestPyPI/PyPI publisher jobs |
| Windows CI jobs present (import/lock smoke) | spec §3, §4.5 | Yes (mechanism); proof external-pending (nonclaim honored) | static-inspection: `ci.yml` `windows-base-cli` job (`runs-on: windows-latest`, import + workspace_lock acquire/release) |
| Context map always generated, never hand-edited; double-generation no diff | spec §4.5 | Yes | direct-run-adjacent: `tests/commands/test_map.py:107` `test_second_identical_map_generation_preserves_bytes_and_mtime`; `Ontos_Context_Map.md` is generator-produced |
| Migration docs cover required_version, exit-3 warning, E_USER_INPUT, E_LOG_EXISTS, archive marker, reserved code 4, exit taxonomy | spec §7 | Yes | static-inspection: `Migration_v3_to_v4.md` and `Ontos_Manual.md` both carry all required copy |
| Immutable SHA pair preserved (base `bf91b42`, I0 `b6f89d7`) | spec §1, §9 | Yes | direct-run: validator pins `REVALIDATION_COMMIT=bf91b42...`, `INTEGRATION_COMMIT=b6f89d7...` (lines 31-32) and PASSes; I1 did not move I0 |
| Preserved user docs + framework untouched | spec §9 | Yes | direct-run: `git diff --stat base..I1 -- docs/zeta.md docs/specs/project-ontos-rationale-capture-template-proposal.md .llm-dev/framework .git .venv` → empty |
| No synthetic Windows/TestPyPI/GitHub receipts; external proof pending | spec §2, §3, §9 | Yes | direct-run: validator reports `mode: local` (not external); GitHub parity requires `--require-external-parity` (live service) — pending, not synthesized |
| Stop boundary: no D.6/merge/tag/publish/release claim | spec §2, §10.2 | Yes | static-inspection: I1 is code only; no orchestrator-only action taken |

## 5. Backward compatibility

Intentional, spec-sanctioned breaking changes (spec §7) are implemented with
migration paths: YAML semantic round trips; invalid/non-string IDs fail via the
canonical validator; log collisions fail with `E_LOG_EXISTS` + recovery hint;
unsafe buffered/symlinked paths fail; MCP type counts exhaustive; read-only MCP
non-mutating; activation reports version incompatibility; CLI JSON/exit use the
documented schema. Exit code `4` remains reserved (not emitted). Both
`Migration_v3_to_v4.md` and `Ontos_Manual.md` add the normative copy including
the warnings-only-exit-`3` impact on shell automation that previously treated
every non-zero result as hard error. Rollback remains commit-level (revert I0 as
one unit, then regenerate map/agents) — consistent with spec §7. No
undocumented breaking change found.

## 6. Consistency check

No conflict with the approved spec, prior decisions, or the spec's own
incorporation notes (B.1/B.2/Phase C falsification notes in §§1). The validator's
pinned integration commit stays at I0 (`b6f89d7`) — correct, because the spec's
"frozen implementation snapshot" is I0 and I1 is the Phase C reconciliation
layer recorded atop it, not a new integration snapshot. The registry's
`integration_commit` was not moved to I1 (validator still PASSes), preserving the
immutable SHA pair. Spec §4.1's frozen-I0 consumer-surface framing
("pre-upgrade shape ... not represented as already satisfied by I0") is
consistent with I1 implementing the upgrade.

## 7. Deviation report

| Divergence | Authority cited? | Authority source | Severity |
|------------|------------------|------------------|----------|
| `load_yaml` does not quarantine `yaml.YAMLError`; a syntactically-malformed registry/child-manifest YAML reaches `main()`'s `except Exception` → exit 2/`ERROR` | No | — | should-fix |
| Log collision hint says "Choose a different `--title`" vs spec literal "title/slug" | Yes (slug is mechanically derived from title) | spec §4.3 | minor |

## 8. Issues found

### Blocking
| ID | Description | Authority violated | Artifact location | Evidence | Suggested action |
|----|-------------|--------------------|-------------------|----------|------------------|
| — | No blocking deviations found | — | — | — | — |

### Should-fix
| ID | Description | Authority violated | Artifact location | Evidence | Suggested action |
|----|-------------|--------------------|-------------------|----------|------------------|
| A-1 | `load_yaml` (`scripts/validate-audit-remediation-registry.py:209-216`) returns `yaml.safe_load(...)` without catching `yaml.YAMLError`. A syntactically-broken registry or child-manifest YAML raises through `validate()` into `main()`'s `except Exception` (line 1891-1893) which prints `audit-registry: ERROR` and `return 2`. The spec §4.1/§11 invariant is malformed control-plane inputs "produce validation exit 1 — never an exception-derived exit 2 ... never exit 2 with ERROR." The enumerated acceptance constructions (non-mapping roots/rows, wrong/unhashable types, invalid enums, `None` paths, missing #146/#147) all produce exit 1/FAILED (direct-run: 194 tests pass), but the prose "never exit 2" is not fully honored for the narrower class of syntactically-unparseable YAML, and no test covers that class. | spec §4.1, §11 (`main()` exit 1/FAILED, never exit 2/ERROR); `load_yaml` docstring lines 210-214 claims "not an exception-derived validator error (exit 2)" | `scripts/validate-audit-remediation-registry.py:209-216` (load_yaml), `:1889-1893` (main catch-all) | static-inspection (YAMLError uncaught; no covering test); enumerated cases direct-run PASS | Catch `yaml.YAMLError` in `load_yaml` (or in `main`) and route to a validation error so the malformed-document class also yields exit 1/FAILED. No reproduction run: OpenCode noninteractive constraint forbids temporary copies for a breaking-input fixture. |

### Minor
| ID | Description | Authority violated | Artifact location | Evidence | Suggested action |
|----|-------------|--------------------|-------------------|----------|------------------|
| A-2 | Log collision recovery hint reads "Choose a different `--title`, or intentionally move/remove the existing log" rather than the spec literal "choose a different title/slug, or move/remove the existing log intentionally." The slug is derived from the title, so the actionable recovery semantics (different title ⇒ different slug, or move/remove) are preserved; `--title` is the actual CLI flag and is arguably more precise. Not a behavioral deviation. | spec §4.3 (recovery hint wording) | `ontos/commands/log.py:310-313` | static-inspection | Optionally align the hint to mention slug, but no action required. |

## Verdict
Approve

The I1 Phase C reconciliation matches approved spec v1.5 across every
re-derived constraint area — architecture, compatibility, release-sequencing,
registry/lease, lifecycle, external-proof nonclaims, public-copy contracts, and
nonclaims. Bounded direct-run evidence (registry validator PASS with 91/41/7
baseline; 194 registry table-driven tests; 106 Phase C tests across CLI/config/
log/locking/stub) plus static-inspection confirms compliance. No blocking
deviation: the spec's enumerated acceptance criterion (malformed control-plane
inputs → exit 1/FAILED) is met. Two non-blocking notes are recorded — should-fix
A-1 (residual exit-2 path for syntactically-broken YAML, outside the enumerated
acceptance set) and minor A-2 (recovery-hint wording). External proofs (Windows
runner, TestPyPI tag-run, live GitHub parity) remain pending per the spec's own
nonclaims and are not synthesized. This is an alignment verdict only; it does not
certify D.5, D.6, per-issue lifecycle, or a release.

## 10. Notes

- OpenCode noninteractive constraint honored: only single bounded read-only
  shell commands were run; no chained commands, shell redirection, temporary
  copies, `rm`, or mutating context-map generation. No tool call was denied.
- Direct-run checks: `.venv/bin/python scripts/validate-audit-remediation-registry.py`
  (PASS, exit 0); `.venv/bin/python -m pytest tests/test_audit_remediation_registry_validator.py`
  (194 passed); `.venv/bin/python -m pytest tests/test_cli_contract_v4.py
  tests/core/test_config_phase3.py tests/commands/test_log.py tests/mcp/test_locking.py
  tests/commands/test_stub_parity.py` (106 passed). Full suite intentionally not run.
- The worktree was preserved: post-check `git status` showed only the pre-existing
  modified lifecycle-receipt file and pre-existing untracked D.2 capture artifacts;
  test runs added no tracked changes (`-p no:cacheprovider`).
- Route-redaction: workflow identity-token permissions are described in prose as
  "OIDC permission" granted only to publisher jobs; no secret-shaped configuration
  keys with literal values are quoted or reproduced.
- Sibling D.2 reviews, dispatch results, raw captures, prompts, and receipts were
  not read; constraints were derived independently from the spec and verified
  against the actual I1 diff/code.
- Evidence labels actually used: `direct-run` and `static-inspection`.
- Status: completed.
