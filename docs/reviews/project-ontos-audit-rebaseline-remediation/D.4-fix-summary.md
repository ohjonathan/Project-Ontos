---
id: project-ontos-audit-rebaseline-remediation-D.4-fix-summary
deliverable_id: project-ontos-audit-rebaseline-remediation
role: fix-author
family: codex
phase: D.4
canonical_verdict_consumed: docs/reviews/project-ontos-audit-rebaseline-remediation/D.3-verdict.md
template_version: 1.1.0
status: halted
---

# Fix Summary — project-ontos-audit-rebaseline-remediation / D.4

The six canonical D.3 should-fix findings are functionally addressed at I2
`311b60b6e86abe6d0b5a7ac61e16d07049387707`. D.4 nevertheless halts because
llm-dev-framework v2.0.1 cannot honestly register or verify adopter-local
regression fixtures under EH-15-A. The product fixes, test-first evidence, and
all passing repository gates remain preserved; no emergency waiver or false
certification is inferred.

The post-D.5 loose falsification pass then reproduced two additional defects.
Both are fixed at I3 `859ecf778389aaa67f69146d7ae8cd2564445af5`:

| Finding | Fix | Regression evidence |
|---|---|---|
| LF-ID-1 | Unquoted rename replacements now use the canonical PyYAML-backed serializer, so numeric-, date-, and float-like IDs reload as exact strings in target and reference fields. | Three cases failed before the fix and pass in `test_rename_yaml_like_ids_remain_strings_in_all_frontmatter_shapes`. |
| LF-CP-1 | Program IDs and roots share one normalized ownership namespace, including the synthetic issue-158 owner, before issue-keyed/O4 consumers run. | Two synchronized collisions failed open before the fix and now return `FAILED`/exit 1 in `test_program_identity_collision_fails_when_findings_and_o4_are_synchronized`. |

At I3 the focused falsification set is `5 passed` and the complete suite is
`1725 passed, 1 warning`. D.4 remains halted on D4-INFRA-1; fixing product code
does not convert the unavailable framework gate into certification.

Pre-fix implementation: `aa41c3982e21b0e0cff6c3c5486f4af9e5e55e05`.
Post-fix implementation (I2): `311b60b6e86abe6d0b5a7ac61e16d07049387707`.
Scope-recovery checkpoint: `737fe27`.

## Per-blocker fix table

The D.3 preserved-blocker list is empty. These rows cover the six should-fix
findings explicitly required for this D.4 pass.

| Blocker ID | Fix | Regression test | File:line | Evidence |
|------------|-----|-----------------|-----------|----------|
| CAN-ACT-1 | Human `activate` output renders one nonempty `Reason:` line for `not_usable`. | `tests/commands/test_agentic_activation_resilience.py::test_activate_human_renders_incompatible_version_reason_once` | `ontos/commands/activate.py:227` | direct-run |
| CAN-ACT-2 | A typed malformed-range category carries raw detail into one canonical public formatter; activation catches it before generic config errors. | `tests/commands/test_agentic_activation_resilience.py::test_activate_json_renders_malformed_range_contract_once`; `tests/core/test_config_phase3.py::test_eager_required_version_validation_preserves_typed_raw_detail` | `ontos/core/config.py:36,198,280`; `ontos/commands/activate.py:91` | direct-run |
| CAN-CP-1 | Issue 158 has an explicit synthetic owner and reserved ID/issue pairing; root and scope checks use the same owner path as program rows. | `tests/test_audit_remediation_registry_validator.py::test_issue_158_control_plane_finding_is_checked_against_synthetic_owner`; `::test_control_plane_finding_id_and_issue_158_are_reserved_as_a_pair` | `scripts/validate-audit-remediation-registry.py:36,1364,1418` | direct-run |
| CAN-CP-2 | Lease `programs` and `order` reject duplicates before set conversion or rendered-O5 comparison. | `tests/test_audit_remediation_registry_validator.py::test_duplicate_lease_lists_fail_even_when_o5_is_synchronized` | `scripts/validate-audit-remediation-registry.py:480` | direct-run |
| CAN-CP-3 | YAML syntax/read/decode failures become typed control-plane input failures and `FAILED`/exit 1; unexpected runtime defects remain `ERROR`/exit 2. | `tests/test_audit_remediation_registry_validator.py::test_malformed_registry_yaml_returns_exit_one_never_two`; `::test_malformed_child_manifest_yaml_returns_exit_one_never_two`; `::test_unexpected_validator_runtime_error_remains_exit_two` | `scripts/validate-audit-remediation-registry.py:225,232,1942` | direct-run |
| CAN-ID-1 | Both operands use `validate_document_id` before CLI project discovery, MCP preflight/locking, and same-ID no-op; only canonical operand errors map to `E_USER_INPUT`. | `tests/commands/test_rename.py::test_rename_invalid_id_is_rejected_before_project_discovery`; `tests/mcp/test_rename_document.py::test_rename_document_rejects_invalid_id_before_preflight` | `ontos/commands/rename.py:158,306,438`; `ontos/mcp/rename_tool.py:359` | direct-run |

## Test-anchor additions (v1.4+ S4)

| Test file:line | Test name | Closes blocker | Satisfies spec § 18 anchor | Evidence |
|----------------|-----------|----------------|----------------------------|----------|
| `tests/commands/test_agentic_activation_resilience.py:107` | `test_activate_human_renders_incompatible_version_reason_once` | CAN-ACT-1 | Human activation failure visibility | direct-run |
| `tests/commands/test_agentic_activation_resilience.py:123,147` | malformed-range human/JSON contract tests | CAN-ACT-2 | Required-version exact-copy and anchor parity | direct-run |
| `tests/core/test_config_phase3.py:303,316` | typed eager validation + canonical formatter tests | CAN-ACT-2 | Canonical validation construction | direct-run |
| `tests/test_audit_remediation_registry_validator.py:518,555` | synthetic owner + reserved pairing tests | CAN-CP-1 | Registry owner/scope parity | direct-run |
| `tests/test_audit_remediation_registry_validator.py:733` | synchronized-O5 duplicate lease test | CAN-CP-2 | Collision/lease completeness | direct-run |
| `tests/test_audit_remediation_registry_validator.py:918,939,964,986` | malformed YAML/read/decode and unexpected-runtime tests | CAN-CP-3 | Malformed control-plane input exits 1, never 2 | direct-run |
| `tests/commands/test_rename.py:108,134,164,639,669` | CLI canonical operands, entry ordering, builder ordering, valid no-op | CAN-ID-1 | Every CLI ID uses the canonical validator | direct-run |
| `tests/mcp/test_rename_document.py:319,342,367` | MCP canonical errors, reserved rule, preflight ordering | CAN-ID-1 | Shared CLI/MCP rename semantics | direct-run |

## Regression Coverage (EH-15-A)

These are the real adopter-local runnable pytest regressions. The v2.0.1
mechanical verifier rejects them because it resolves fixtures and the
`scripts/verify-all.sh` registry only under `.llm-dev/framework`, not under the
adopter root. They are intentionally not replaced with unrelated registered
framework fixtures.

| Finding ID | Change class | Regression |
|------------|--------------|------------|
| CAN-ACT-1 | code | `tests/commands/test_agentic_activation_resilience.py` |
| CAN-ACT-2 | code | `tests/commands/test_agentic_activation_resilience.py`, `tests/core/test_config_phase3.py` |
| CAN-CP-1 | code | `tests/test_audit_remediation_registry_validator.py` |
| CAN-CP-2 | code | `tests/test_audit_remediation_registry_validator.py` |
| CAN-CP-3 | code | `tests/test_audit_remediation_registry_validator.py` |
| CAN-ID-1 | code | `tests/commands/test_rename.py`, `tests/mcp/test_rename_document.py` |

## Framework blocker — D4-INFRA-1

`templates/14-fix-summary.md` requires every code row above to name a runnable
fixture registered in `scripts/verify-all.sh`. In v2.0.1,
`verify-fix-summary-regressions.sh` hard-binds its bundle, registry, and fixture
resolution to `.llm-dev/framework`; no config key or adopter hook registers
Project Ontos tests. The wrapper's adopter-mode `verify-all.sh` path exits into
the four-check manifest verifier before the EH-15-A registry is exercised.

The manifest path mode is additionally fail-open for this adopter layout:

```bash
bash .llm-dev/framework/scripts/verify-fix-summary-regressions.sh \
  --manifest "$PWD/manifests/project-ontos-audit-rebaseline-remediation.yaml"
```

Before this summary existed, the command returned exit 0 with `no D.4
fix-summary exists` because it searched relative to `manifests/` and then the
framework bundle, not the adopter root. Invoking the verifier with this summary
path directly is expected to fail because the honest pytest paths are not in
the framework-owned shell-fixture registry.

Required resolution is upstream framework support for an explicit adopter root
and adopter-owned runnable-fixture registry, followed by a pinned framework
upgrade and fresh D.4/D.5. Editing the forbidden framework checkout, citing an
unrelated framework fixture, using a path collision, lowering the manifest
version, or silently waiving the gate would fabricate closure. No such action
was taken.

## Should-fix disposition

| Finding ID | Disposition | Rationale |
|------------|-------------|-----------|
| CAN-ACT-1 | addressed | Pre-fix failure reproduced; focused and full post-fix suites pass. |
| CAN-ACT-2 | addressed | Typed/canonical copy preserves eager parsing, exact prefix/anchor, and single offender occurrence. |
| CAN-CP-1 | addressed | Root/scope mutation now fails through `main`; fix commit is non-self-referentially bound in the registry. |
| CAN-CP-2 | addressed | Duplicate `programs` and `order` each fail even when O5 is synchronized. |
| CAN-CP-3 | addressed | Registry and both child syntax failures return 1/`FAILED`; internal runtime errors retain 2/`ERROR`. |
| CAN-ID-1 | addressed | CLI, builder, and MCP enforce canonical validation before all no-op/preflight shortcuts. |

Functional disposition is not lifecycle certification while D4-INFRA-1 remains.

## Spec deviations declared

None. The exact `ontos/commands/rename.py` manifest correction is documented in
`D.4-scope-audit-recovery.md` as a Phase-0 omission recovery authorized by
approved spec §4.2 and canonical D.3 CAN-ID-1; it does not change behavior or
broaden the product contract.

## Scope-lock proof

- Initial post-fix gate: failed on the single omitted path
  `ontos/commands/rename.py`; evidence is preserved in
  `D.4-scope-audit-recovery.md`.
- Exact recovery: commit `737fe27` adds only that file to the manifest and
  records the sequencing incident without rewriting `311b60b`.
- Post-recovery changed-path gate: PASS, 559 paths within scope from
  `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`.
- Forbidden paths: unchanged; the two user-owned documents remain absent from
  the isolated lifecycle worktree.
- Cardinality: registry remains exactly 100 rows; I0, I1, and I2 commit
  assertions pass.
- Manifest conformance: `scripts/llm-dev verify` passes all four checks.

## Regression count (v1.4+ S4)

| Counter | Value |
|---------|-------|
| Preserved blockers CLOSED this round | 0 (D.3 preserved none) |
| Preserved blockers REMAINING (re-deferred or not addressed) | 0 |
| Canonical should-fix findings functionally addressed | 6 |
| New tests added | 41 collected test cases (1679 → 1720) |
| Lines changed (D.3 checkpoint through scope recovery) | +821 / -97 |
| Commits in this D.4 round before this summary | 5 |
| New blockers INTRODUCED by this D.4 round (surfaced at D.5 r2) | 0 product blockers; 1 pre-existing framework integration blocker surfaced (D4-INFRA-1) |

## Smoke checks after fix

| Check | Result | Evidence |
|-------|--------|----------|
| Activation/config/doctor/MCP matrix | PASS — 124 passed | direct-run |
| Registry validator module | PASS — 205 passed | direct-run |
| Rename CLI/MCP matrix | PASS — 109 passed | direct-run |
| Complete Project Ontos suite | PASS — 1720 passed, 1 deprecation warning | direct-run |
| Post-suite porcelain | PASS — empty before later reviewer activation refreshed the generated map | direct-run |
| Registry local validation | PASS | direct-run |
| Registry live GitHub parity | PASS | direct-run |
| Changed-path scope after exact recovery | PASS — 559 paths | direct-run |
| Manifest conformance | PASS — 4/4 | direct-run |
| `git diff --check HEAD` at I2 | PASS | direct-run |
| EH-15-A adopter regression registration | **FAIL — D4-INFRA-1** | direct-run + static-inspection |

## Smoke-check re-baseline (v1.3+)

- [x] No product fix in this summary changes the shape of an artifact that a
  manifest `smoke_checks[*].checks[*].command` regex consumes. Existing smoke
  commands remain correct.
- [ ] At least one fix changes a smoke-regex-consumed artifact shape.

## Commits

| SHA | Blocker addressed | Message |
|-----|-------------------|---------|
| `f6d6b77` | CAN-ACT-1, CAN-ACT-2 | Fix D3 activation diagnostics |
| `5c5a9cd` | CAN-CP-1, CAN-CP-2, CAN-CP-3 | Harden audit remediation control-plane validation |
| `2dede68` | CAN-CP-1, CAN-CP-2, CAN-CP-3 | Bind control-plane registry evidence to D4 fix |
| `311b60b` | CAN-ID-1 | Use canonical ID validation for rename |
| `737fe27` | CAN-ID-1 scope custody | Correct D4 rename scope omission |
| `859ecf7` | LF-ID-1, LF-CP-1 | Close loose falsification regressions |

## D.4 verdict

**Halted on D4-INFRA-1.** All eight reproduced product/control-plane findings
are functionally fixed and repository verification passes;
EH-15-A adopter regression certification is unavailable in the pinned
framework. D.5 may independently reproduce the product fixes, but it must
preserve this infrastructure blocker and cannot approve lifecycle closure.
