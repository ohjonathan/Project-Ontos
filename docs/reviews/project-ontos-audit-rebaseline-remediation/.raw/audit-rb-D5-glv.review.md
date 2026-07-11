---
id: audit-rb-D5-glv
deliverable_id: project-ontos-audit-rebaseline-remediation
role: verifier
family: glm
phase: D.5
evidence_mode: direct-run
canonical_verdict_consumed: docs/reviews/project-ontos-audit-rebaseline-remediation/D.3-verdict.md
fix_summary_consumed: docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-fix-summary.md
clarification_artifacts: []
status: completed
verdict: Request Further Fixes
---

# Verification — project-ontos-audit-rebaseline-remediation / D.5 / glm

Every one of the six canonical D.3 should-fixes is independently reproduced as
broken pre-fix and closed post-fix by direct execution against parallel
repository-local snapshots. The full suite is green at 1720 passed. The product
fixes are functionally sound.

D.4 is nevertheless honestly `status: halted` on **D4-INFRA-1**. I verified
that claim directly, not by accepting it. It holds, and the fail-open surface is
materially worse than a missing registration: the EH-15-A manifest-mode gate
returns **exit 0 / `OK`** while asserting the fix summary "does not exist"
at a path where a tracked file plainly does exist. A gate that cannot find
the artifact it is gating and reports success is fail-open. Functional success
is therefore not certification, and my body verdict is `Request changes`.

## Environment and snapshots

Pre-fix implementation: `aa41c3982e21b0e0cff6c3c5486f4af9e5e55e05`.
Post-fix implementation (I2): `311b60b6e86abe6d0b5a7ac61e16d07049387707`.
Scope-recovery checkpoint: `737fe27`.

Two orchestrator-prepared, plain snapshots inside the served repository (neither
contains a `.git` pointer; no sandbox-external git access is needed):

- post-fix: `.venv/d5-glm-post`
- pre-fix: `.venv/d5-glm-pre` — same tests with only the five target
  implementation files (`ontos/commands/activate.py`, `ontos/core/config.py`,
  `ontos/commands/rename.py`, `ontos/mcp/rename_tool.py`,
  `scripts/validate-audit-remediation-registry.py`) restored from pre-fix
  `aa41c39`.

From each snapshot directory the test interpreter is `../bin/python` (resolves
to `.venv/bin/python`, Python 3.14.6); all commands are repository-relative.

| Precondition | Observed | Evidence |
|---|---|---|
| `ontos.__file__` resolves under `d5-glm-post` | `.venv/d5-glm-post/ontos/__init__.py` | direct-run |
| `ontos.__file__` resolves under `d5-glm-pre` | `.venv/d5-glm-pre/ontos/__init__.py` | direct-run |
| Post snapshot has fix markers | `Reason:` in activate.py (1); `InvalidRequiredVersionError` in config.py (2); `_ID_PATTERN` absent from rename.py (0); `validate_rename_ids` in rename.py (4) + rename_tool.py (2); `ControlPlaneInputError` (4) + `CONTROL_PLANE_OWNER` (2) in validator | direct-run |
| Pre snapshot has pre-fix markers | `Reason:` absent (0); `InvalidRequiredVersionError` absent (0); `_ID_PATTERN` present in rename.py (3); `validate_rename_ids` absent from rename.py (0) + rename_tool.py (0); `ControlPlaneInputError` absent (0); `CONTROL_PLANE_OWNER` absent (0) | direct-run |

The import-origin check is load-bearing: the interpreter is shared (`../bin/python`),
but `ontos.__file__` resolves under each snapshot whose tests are being run, so
the five-file restore genuinely takes effect — post-fix code runs in `d5-glm-post`
and pre-fix code runs in `d5-glm-pre`, against the SAME post-fix test files in
both snapshots.

### pytest flag discipline

Every focused snapshot invocation used `-B` plus `--cache-clear` (never combined
with `-p no:cacheprovider`, which removes the owning plugin and rejects
`--cache-clear`). The full-suite run used `-q -p no:cacheprovider` as directed.
The bounded group-3 selector avoids a false secret-scanner match on a long
pytest identifier while selecting the same regression set.

## Per-should-fix verification table

The D.3 preserved-blocker list is empty (`preserved_blocker_ids: []`). The empty
blocker list does not waive the six canonical should-fix findings — each was
directly reproduced pre-fix and closed post-fix.

| Blocker ID | Original failure reproduced? | Fix addresses it? | Regression test fails pre-fix? | Regression test passes post-fix? | Evidence label |
|---|---|---|---|---|---|
| CAN-ACT-1 | Yes — human `not_usable` output carried 0 `Reason:` lines (`assert 0 == 1`) | Yes | Yes — exit `1`, 4 failed | Yes — exit `0`, 4 passed | direct-run |
| CAN-ACT-2 | Yes — malformed range reason began with `Config error:` instead of `Invalid [ontos].required_version:` prefix/anchor | Yes | Yes — exit `1`, 4 failed | Yes — exit `0`, 4 passed | direct-run |
| CAN-CP-1 | Yes — issue-158 root/scope mutations not detected; `root_program mismatch for issue #158` and `finding scope exceeds owner #158` never emitted | Yes | Yes — exit `1`, 8 failed | Yes — exit `0`, 8 passed | direct-run |
| CAN-CP-2 | Yes — `shared_path_leases row 0 has duplicate programs` / `duplicate order` never emitted under synchronized O5 | Yes | Yes — exit `1`, 8 failed | Yes — exit `0`, 8 passed | direct-run |
| CAN-CP-3 | Yes — malformed registry + both child manifests returned exit `2`/`ERROR` (`assert 2 == 1`), the fail-open routing | Yes | Yes — exit `1`, 8 failed | Yes — exit `0`, 8 passed | direct-run |
| CAN-ID-1 | Yes — incl. the invalid same-ID false-green (live pre-fix CLI returned exit `0`/`nothing_to_do`); MCP preflight ran before validation | Yes | Yes — exit `1`, 24 failed | Yes — exit `0`, 24 passed | direct-run |

### Group 1 — CAN-ACT-1 / CAN-ACT-2

Selection: `tests/commands/test_agentic_activation_resilience.py -k 'human_renders_incompatible or human_renders_malformed or json_renders_malformed'`

| Snapshot | Collected | Deselected | Selected | Passed | Failed | Exit |
|---|---|---|---|---|---|---|
| `d5-glm-post` | 11 | 7 | 4 | 4 | 0 | 0 |
| `d5-glm-pre` | 11 | 7 | 4 | 0 | 4 | 1 |

```bash
# post-fix (expect pass)
cd .venv/d5-glm-post
../bin/python -B -m pytest tests/commands/test_agentic_activation_resilience.py \
  -k 'human_renders_incompatible or human_renders_malformed or json_renders_malformed' \
  --cache-clear -v
# → 4 passed, 7 deselected

# pre-fix (expect nonzero)
cd .venv/d5-glm-pre
../bin/python -B -m pytest tests/commands/test_agentic_activation_resilience.py \
  -k 'human_renders_incompatible or human_renders_malformed or json_renders_malformed' \
  --cache-clear -v
# → 4 failed, 7 deselected, exit 1
```

Pre-fix behavioral failures: CAN-ACT-1 — `assert 0 == 1` where `0 = len([])`
(the human output rendered zero `Reason:` lines for `not_usable`). CAN-ACT-2 —
`assert False` where the JSON reason was `"Config error: version clause
'not-a-range' is not a valid semantic version"`, missing the mandated
`Invalid [ontos].required_version:` prefix and Migration anchor.

### Group 2 — CAN-CP-1 / CAN-CP-2 / CAN-CP-3

Selection: `tests/test_audit_remediation_registry_validator.py -k 'issue_158_control_plane or control_plane_finding_id_and_issue_158 or duplicate_lease_lists or malformed_registry_yaml or malformed_child_manifest_yaml'`

| Snapshot | Collected | Deselected | Selected | Passed | Failed | Exit |
|---|---|---|---|---|---|---|
| `d5-glm-post` | 205 | 197 | 8 | 8 | 0 | 0 |
| `d5-glm-pre` | 205 | 197 | 8 | 0 | 8 | 1 |

```bash
# post-fix (expect pass)
cd .venv/d5-glm-post
../bin/python -B -m pytest tests/test_audit_remediation_registry_validator.py \
  -k 'issue_158_control_plane or control_plane_finding_id_and_issue_158 or duplicate_lease_lists or malformed_registry_yaml or malformed_child_manifest_yaml' \
  --cache-clear -v
# → 8 passed, 197 deselected

# pre-fix (expect nonzero)
cd .venv/d5-glm-pre
../bin/python -B -m pytest tests/test_audit_remediation_registry_validator.py \
  -k 'issue_158_control_plane or control_plane_finding_id_and_issue_158 or duplicate_lease_lists or malformed_registry_yaml or malformed_child_manifest_yaml' \
  --cache-clear -v
# → 8 failed, 197 deselected, exit 1
```

Pre-fix behavioral failures: CAN-CP-1 — issue-158 root/scope authority checks
absent; the expected fragments (`root_program mismatch for issue #158`,
`finding scope exceeds owner #158`) never appeared. CAN-CP-2 — duplicate
lease-list values not rejected; expected `shared_path_leases row 0 has duplicate
programs/order` absent while synchronized-O5 mutations passed through. CAN-CP-3
— `assert 2 == 1` for malformed registry YAML and both child-manifest YAML
cases: exit `2`/`audit-registry: ERROR` instead of exit `1`/`FAILED`.

### Group 3 — CAN-ID-1

Selection: `tests/commands/test_rename.py tests/mcp/test_rename_document.py -k 'rename_invalid_ids_use_canonical or rename_invalid_id_is_rejected_before_project_discovery or build_rename_plan_uses_canonical or rename_document_invalid_ids_use_canonical or rejects_invalid_id_before_preflight'`

| Snapshot | Collected | Deselected | Selected | Passed | Failed | Exit |
|---|---|---|---|---|---|---|
| `d5-glm-post` | 75 | 51 | 24 | 24 | 0 | 0 |
| `d5-glm-pre` | 75 | 51 | 24 | 0 | 24 | 1 |

```bash
# post-fix (expect pass)
cd .venv/d5-glm-post
../bin/python -B -m pytest tests/commands/test_rename.py tests/mcp/test_rename_document.py \
  -k 'rename_invalid_ids_use_canonical or rename_invalid_id_is_rejected_before_project_discovery or build_rename_plan_uses_canonical or rename_document_invalid_ids_use_canonical or rejects_invalid_id_before_preflight' \
  --cache-clear -v
# → 24 passed, 51 deselected

# pre-fix (expect nonzero)
cd .venv/d5-glm-pre
../bin/python -B -m pytest tests/commands/test_rename.py tests/mcp/test_rename_document.py \
  -k 'rename_invalid_ids_use_canonical or rename_invalid_id_is_rejected_before_project_discovery or build_rename_plan_uses_canonical or rename_document_invalid_ids_use_canonical or rejects_invalid_id_before_preflight' \
  --cache-clear -v
# → 24 failed, 51 deselected, exit 1
```

Pre-fix behavioral failures: CAN-ID-1 — invalid old ID returned
`old_id_not_found` (not `invalid_old_id`); invalid new ID used regex copy
`new_id must match ^[A-Za-z0-9]...` instead of canonical `validate_document_id`
message; invalid same-ID returned exit `0`/`nothing_to_do` (the false-green);
CLI returned exit `1` instead of canonical exit `2`; MCP returned
`E_INVALID_ID`/`E_DOCUMENT_NOT_FOUND` instead of `E_USER_INPUT`; MCP preflight
ran before ID validation (`AssertionError: preflight must not run for invalid
IDs`); `build_rename_plan` reported `old_id_not_found` and accepted the
same-ID no-op for invalid operands.

## Regression check

### Full smoke suite (post-fix)

| Smoke check | Result | Evidence |
|---|---|---|
| Full `tests/` suite in `d5-glm-post` | PASS — 1720 passed, 1 deprecation warning, exit 0 | direct-run |

```bash
cd .venv/d5-glm-post
../bin/python -m pytest tests/ -q -p no:cacheprovider
# → 1720 passed, 1 warning in 96.60s, exit 0
```

### Lifecycle worktree checks

| Check | Command | Result | Evidence |
|---|---|---|---|
| Registry local validation | `python3 scripts/validate-audit-remediation-registry.py` | PASS — `audit-registry: PASS`, exit 0 | direct-run |
| Registry external parity | `python3 scripts/validate-audit-remediation-registry.py --require-external-parity` | PASS — `audit-registry: PASS, mode: local+external`, exit 0 | direct-run |
| Changed-path scope | `bash .llm-dev/framework/scripts/verify-changed-path-scope.sh --manifest manifests/project-ontos-audit-rebaseline-remediation.yaml --base bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95` | PASS — `OK (598 changed path(s) within scope)`, exit 0 | direct-run |
| Manifest conformance | `scripts/llm-dev verify manifests/project-ontos-audit-rebaseline-remediation.yaml` | PASS — `PASSED manifest-conformance (4/4 checks)`, exit 0 | direct-run |
| `git diff --check HEAD` | `git diff --check HEAD` | PASS — exit 0 | direct-run |
| `git diff --check` (D.2 base) | `git diff --check bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95..HEAD` | PASS — exit 0 | direct-run |

### Cardinality assertions

| Cardinality assertion | Result | Evidence |
|---|---|---|
| Registry contains exactly 100 findings | PASS — `100` | direct-run |
| I0 exists (`b6f89d77...`) | PASS — exit 0 | direct-run |
| I1 exists (`05b090d5...`) | PASS — exit 0 | direct-run |
| I2 exists (`311b60b6...`) | PASS — exit 0 | direct-run |
| Forbidden paths absent | PASS — exit 0 | direct-run |

Narrative: the scope-recovery commit `737fe27` added only `ontos/commands/rename.py`
to `scope.allowed_paths` (manifest line 86) without amending `311b60b`; the
changed-path gate reports 598 paths within scope (the delta from the D.4
summary's 559 reflects post-recovery D.5 review files added under the
`docs/reviews/project-ontos-audit-rebaseline-remediation/**` pattern).

## Scope-lock check

- Paths touched outside allowed set: **none.** All implementation and test
  changes fall within the manifest's `scope.allowed_paths` or the
  `docs/reviews/project-ontos-audit-rebaseline-remediation/**` pattern.
- The five target implementation files (`ontos/commands/activate.py`,
  `ontos/core/config.py`, `ontos/commands/rename.py`,
  `ontos/mcp/rename_tool.py`, `scripts/validate-audit-remediation-registry.py`)
  are all explicitly listed in `scope.allowed_paths` (lines 78, 92, 86, 111,
  119).

## D4-INFRA-1 — framework integration blocker (verified directly)

The D.4 fix summary halts on D4-INFRA-1: `verify-fix-summary-regressions.sh`
hard-binds its bundle, registry, and fixture resolution to `.llm-dev/framework`;
no config key or adopter hook registers Project Ontos tests. I verified this
directly with three probes:

### EH-15-A manifest-mode probe (fail-open)

```bash
bash .llm-dev/framework/scripts/verify-fix-summary-regressions.sh \
  --manifest "$PWD/manifests/project-ontos-audit-rebaseline-remediation.yaml"
```

Result: **exit 0** —
`verify-fix-summary-regressions: OK (no D.4 fix-summary exists at
docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-fix-summary.md)`.

This is fail-open: the fix summary file EXISTS as a tracked 183-line file at
that exact repository-relative path, but the script resolves the path relative to
the manifest directory (`manifests/`) instead of the adopter root and cannot
find it. A gate that reports `OK` while unable to locate the artifact it is
gating is fail-open.

### EH-15-A relative explicit-path probe (fail-closed on resolution)

```bash
bash .llm-dev/framework/scripts/verify-fix-summary-regressions.sh \
  docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-fix-summary.md
```

Result: **exit 2** —
`verify-fix-summary-regressions: cannot read
docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-fix-summary.md`.

The file exists at that relative path from the repository root, but the script
resolves it relative to the framework bundle. This is not a test-harness failure
— it is the expected nonzero result of an EH-15-A infrastructure probe against
a framework that cannot resolve adopter-relative paths.

### EH-15-A absolute explicit-path probe (fail-closed on fixture registry)

```bash
bash .llm-dev/framework/scripts/verify-fix-summary-regressions.sh \
  "$PWD/docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-fix-summary.md"
```

Result: **exit 1** — `verify-fix-summary-regressions: FAILED` with 12
diagnostics across all 6 rows. Each fixture path (e.g.
`tests/commands/test_agentic_activation_resilience.py`,
`tests/core/test_config_phase3.py`,
`tests/test_audit_remediation_registry_validator.py`,
`tests/commands/test_rename.py`, `tests/mcp/test_rename_document.py`) is
reported as both:

1. `does not exist` — false: each file exists and was successfully collected
   and run in the snapshot tests above (1720 items collected from `tests/`).
2. `is not registered as an exercised regression fixture in scripts/verify-all.sh
   (not listed in eh15a_regression_fixtures)` — true: no adopter hook or config
   key registers Project Ontos test paths in the framework-owned fixture
   registry.

The "does not exist" message is a path-resolution false negative: the script
resolves fixture paths under `.llm-dev/framework`, not the adopter root. The
files plainly exist — they were just executed.

### D4-INFRA-1 holds

All three probes confirm D4-INFRA-1. The framework cannot register or verify
adopter-local regression fixtures under EH-15-A. The manifest-mode gate is
fail-open (exit 0 with "does not exist" for a file that exists). The
explicit-path gate is fail-closed but for the wrong reason (path resolution,
not fixture absence). Neither satisfies the EH-15-A contract.

## Verdict

Request changes

The six canonical D.3 should-fixes (CAN-ACT-1/2, CAN-CP-1/2/3, CAN-ID-1) are
all independently reproduced as broken pre-fix and closed post-fix by direct
execution against the `d5-glm-pre` / `d5-glm-post` snapshot pair. The full
suite passes (1720 passed, 1 warning). All lifecycle worktree checks pass
(registry local + external parity, changed-path scope, manifest conformance,
`git diff --check`, cardinality assertions). The product fixes are
functionally sound and introduce no regressions.

D4-INFRA-1 nonetheless holds and is not a product defect — it is a framework
integration blocker. The EH-15-A manifest-mode gate is fail-open (exit 0 while
unable to find a tracked fix-summary file), and the explicit-path gate cannot
resolve or register adopter-owned test fixtures. Functional success is not
certification while the mechanical regression-registration gate is unsatisfied.
The required resolution is upstream framework support for an explicit adopter
root and adopter-owned runnable-fixture registry, followed by a pinned
framework upgrade and fresh D.4/D.5.

This verdict does not claim D.6, per-child certification, merge, publication, or
release readiness.

## If "Request changes"

| Finding | Evidence | Required further action |
|---|---|---|
| D4-INFRA-1 — EH-15-A regression-registration gate is fail-open and cannot resolve adopter-owned fixtures | direct-run: manifest-mode probe exit 0 / "no D.4 fix-summary exists" for a tracked 183-line file; relative explicit-path exit 2 / "cannot read"; absolute explicit-path exit 1 / FAILED with false "does not exist" for 5 fixture files that were collected and run in the snapshot tests above | Upstream framework support for an explicit adopter root and adopter-owned runnable-fixture registry in `verify-fix-summary-regressions.sh`, followed by a pinned framework upgrade and fresh D.4/D.5. Do not edit the forbidden framework checkout, cite an unrelated fixture, use a path collision, lower the manifest version, or silently waive the gate. |
