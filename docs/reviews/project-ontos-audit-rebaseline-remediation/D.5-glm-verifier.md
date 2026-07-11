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
dispatch_id: audit-rb-D5-glv
route_attestation_profile_id: neuralwatt-opencode-glm-5-2-v1
serving_provider: neuralwatt
opencode_model_ref: neuralwatt/glm-5.2
evidence_trust_tier: attested-third-party
---

# Verification — project-ontos-audit-rebaseline-remediation / D.5 / glm

All six canonical D.3 should-fix findings are independently reproduced as
broken pre-fix and closed post-fix by direct execution against the two
orchestrator-prepared snapshots (`.venv/d5-glm-post` post-fix,
`.venv/d5-glm-pre` pre-fix). The full suite is green at 1720 passed with zero
regressions. **The product fixes are functionally sound.**

D4-INFRA-1 was verified directly and **holds**: the EH-15-A framework gate is
fail-open in manifest mode (exit 0 / `OK` while falsely asserting the fix
summary "does not exist") and fails in explicit-path mode (exit 1 / `FAILED`)
because no adopter pytest fixture is registered in the framework-owned
shell-fixture registry. Per the dispatch instruction, D4-INFRA-1 holding
requires `Request changes` even though every product test passes.

## Snapshot preconditions

| Precondition | Observed | Evidence |
|---|---|---|
| Lifecycle worktree HEAD | `599ae90723aaad5b83eca3bbe075dc83afd8c980` on `codex/audit-rebaseline-remediation-lifecycle` | direct-run: `git rev-parse HEAD` |
| Post-fix snapshot | `.venv/d5-glm-post` — 5 target implementation files match I2 `311b60b` (git object hashes MATCH) | direct-run: `git hash-object` vs `git rev-parse` |
| Pre-fix snapshot | `.venv/d5-glm-pre` — 5 target implementation files match `aa41c39` (git object hashes MATCH) | direct-run: `git hash-object` vs `git rev-parse` |
| Snapshot diff | Exactly 5 source files differ: `ontos/commands/activate.py`, `ontos/core/config.py`, `ontos/commands/rename.py`, `ontos/mcp/rename_tool.py`, `scripts/validate-audit-remediation-registry.py` (plus stale `.pyc` invalidated by `-B`/`--cache-clear`) | direct-run: `diff -rq` |
| `ontos.__file__` post | `.venv/d5-glm-post/ontos/__init__.py` (resolves under the snapshot) | direct-run: `../bin/python -c "import ontos"` |
| `ontos.__file__` pre | `.venv/d5-glm-pre/ontos/__init__.py` (resolves under the snapshot) | direct-run: `../bin/python -c "import ontos"` |
| Test interpreter | `../bin/python` → Python 3.14.6, pytest 8.4.2 | direct-run |
| Tests identical across snapshots | Yes — no test file appears in snapshot diff | direct-run: `diff -rq` |

The `ontos.__file__` check is load-bearing: it proves `ontos` resolves from the
snapshot directory, not the lifecycle worktree venv. Every focused run below
executes against the snapshot whose import resolves there, so pre-fix source
genuinely takes effect.

## Per-blocker verification table

Pre-fix implementation: `aa41c3982e21b0e0cff6c3c5486f4af9e5e55e05`.
Post-fix implementation (I2): `311b60b6e86abe6d0b5a7ac61e16d07049387707`.

| Blocker ID | Original failure reproduced? | Fix addresses it? | Regression test fails pre-fix? | Regression test passes post-fix? | Evidence label |
|---|---|---|---|---|---|
| CAN-ACT-1 | Yes — human `not_usable` output carried no `Reason:` line (`assert 0 == 1` where `0 = len([])`) | Yes | Yes — 4 failed, exit 1 | Yes — 4 passed, exit 0 | direct-run |
| CAN-ACT-2 | Yes — malformed range returned `"Config error: version clause 'not-a-range' is not a valid semantic version"`, missing the mandated `Invalid [ontos].required_version:` prefix | Yes | Yes — 4 failed, exit 1 | Yes — 4 passed, exit 0 | direct-run |
| CAN-CP-1 | Yes — issue-158 owner/scope mutations not checked; `root_program mismatch for issue #158` and `finding scope exceeds owner #158` never emitted | Yes | Yes — 8 failed, exit 1 | Yes — 8 passed, exit 0 | direct-run |
| CAN-CP-2 | Yes — `shared_path_leases row 0 has duplicate programs`/`duplicate order` never emitted under synchronized O5 | Yes | Yes — 8 failed, exit 1 | Yes — 8 passed, exit 0 | direct-run |
| CAN-CP-3 | Yes — malformed registry + both child manifests returned `assert 2 == 1` (exit 2 / `ERROR`, the fail-open routing) | Yes | Yes — 8 failed, exit 1 | Yes — 8 passed, exit 0 | direct-run |
| CAN-ID-1 | Yes — invalid same-ID false-green returned exit 0 / `nothing_to_do`; divergent `old_id_not_found`/`invalid_new_id` codes and regex copy; MCP `E_INVALID_ID` instead of `E_USER_INPUT`; preflight ran before ID validation | Yes | Yes — 24 failed, exit 1 | Yes — 24 passed, exit 0 | direct-run |

### Group A — CAN-ACT-1 / CAN-ACT-2 (activation + config)

```bash
# d5-glm-post (require pass)
../bin/python -B -m pytest tests/commands/test_agentic_activation_resilience.py \
  -k 'human_renders_incompatible or human_renders_malformed or json_renders_malformed' \
  --cache-clear -v
# 4 passed, EXIT=0

# d5-glm-pre (require nonzero)
../bin/python -B -m pytest tests/commands/test_agentic_activation_resilience.py \
  -k 'human_renders_incompatible or human_renders_malformed or json_renders_malformed' \
  --cache-clear -v
# 4 failed, EXIT=1
```

Pre-fix failure evidence: `test_activate_human_renders_incompatible_version_reason_once`
failed `assert 0 == 1` (no `Reason:` line in human output — CAN-ACT-1);
`test_activate_json_renders_malformed_range_contract_once` failed
`assert False` where reason was `"Config error: ..."` not
`"Invalid [ontos].required_version:..."` (CAN-ACT-2).

### Group B — CAN-CP-1 / CAN-CP-2 / CAN-CP-3 (registry validator)

```bash
# d5-glm-post (require pass)
../bin/python -B -m pytest tests/test_audit_remediation_registry_validator.py \
  -k 'issue_158_control_plane or control_plane_finding_id_and_issue_158 or duplicate_lease_lists or malformed_registry_yaml or malformed_child_manifest_yaml' \
  --cache-clear -v
# 8 passed, EXIT=0

# d5-glm-pre (require nonzero)
../bin/python -B -m pytest tests/test_audit_remediation_registry_validator.py \
  -k 'issue_158_control_plane or control_plane_finding_id_and_issue_158 or duplicate_lease_lists or malformed_registry_yaml or malformed_child_manifest_yaml' \
  --cache-clear -v
# 8 failed, EXIT=1
```

Pre-fix failure evidence: CP-1 mutations produced no owner/scope error (the
issue-158 finding was exempted); CP-2 duplicate `programs`/`order` produced no
`duplicate` error under synchronized O5; CP-3 malformed YAML returned
`assert 2 == 1` (exit 2 / `ERROR` instead of exit 1 / `FAILED`).

### Group C — CAN-ID-1 (rename CLI + MCP)

```bash
# d5-glm-post (require pass)
../bin/python -B -m pytest tests/commands/test_rename.py tests/mcp/test_rename_document.py \
  -k 'rename_invalid_ids_use_canonical or rename_invalid_id_is_rejected_before_project_discovery or build_rename_plan_uses_canonical or rename_document_invalid_ids_use_canonical or rename_document_rejects_invalid_id_before_preflight' \
  --cache-clear -v
# 24 passed, EXIT=0

# d5-glm-pre (require nonzero)
../bin/python -B -m pytest tests/commands/test_rename.py tests/mcp/test_rename_document.py \
  -k 'rename_invalid_ids_use_canonical or rename_invalid_id_is_rejected_before_project_discovery or build_rename_plan_uses_canonical or rename_document_invalid_ids_use_canonical or rename_document_rejects_invalid_id_before_preflight' \
  --cache-clear -v
# 24 failed, EXIT=1
```

Pre-fix failure evidence: `bad same!` `bad same!` returned exit 0 /
`nothing_to_do` (false-green same-ID no-op); invalid old ID returned
`old_id_not_found` instead of canonical `invalid_old_id`; invalid new ID
returned regex copy `new_id must match ^[A-Za-z0...` instead of canonical
`Document id must start and end...`; MCP returned `E_DOCUMENT_NOT_FOUND`/
`E_INVALID_ID`/`E_INVALID_DOCUMENT_ID` instead of `E_USER_INPUT`; preflight
ran before ID validation (`AssertionError: preflight must not run for invalid
IDs`).

## Regression check

| Smoke check | Result | Evidence |
|---|---|---|
| Full suite (`d5-glm-post`, `-q -p no:cacheprovider`) | PASS — 1720 passed, 1 deprecation warning | direct-run |
| Registry local validation | PASS | direct-run |
| Registry external parity | PASS | direct-run |
| Changed-path scope (base `bf91b42`) | PASS — 594 paths within scope | direct-run |
| Manifest conformance (`scripts/llm-dev verify`) | PASS — 4/4 checks | direct-run |
| `git diff --check HEAD` | PASS — no whitespace errors | direct-run |
| `git diff --check bf91b42..HEAD` | PASS — no whitespace errors | direct-run |
| Cardinality: registry = 100 findings | PASS | direct-run |
| Cardinality: I0/I1/I2 commits exist | PASS | direct-run |
| Cardinality: forbidden user docs absent | PASS | direct-run |

| Cardinality assertion | Result | Evidence |
|---|---|---|
| Registry contains exactly 100 findings | PASS — `100` | direct-run |
| I0 `b6f89d7` exists | PASS | direct-run |
| I1 `05b090d` exists | PASS | direct-run |
| I2 `311b60b` exists | PASS | direct-run |
| User-owned docs absent | PASS | direct-run |

## Scope-lock check

- Paths touched outside allowed set: none. The D.4 scope-audit recovery
  (`D.4-scope-audit-recovery.md`) documents the single `ontos/commands/rename.py`
  manifest omission, corrected at `737fe27` without rewriting `311b60b`.
  Post-recovery changed-path scope reports 594 paths within scope and zero
  forbidden-path violations.

## D4-INFRA-1 verification (framework blocker)

D4-INFRA-1 was verified directly with two EH-15-A probes. **It holds.**

### Manifest-mode probe (fail-open / false PASS)

```bash
bash .llm-dev/framework/scripts/verify-fix-summary-regressions.sh \
  --manifest "$PWD/manifests/project-ontos-audit-rebaseline-remediation.yaml"
```

Result: **EXIT=0** — `OK (no D.4 fix-summary exists at
docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-fix-summary.md)`.

This is a **false PASS**: the D.4 fix-summary is a tracked 12,148-byte file at
exactly that path. The verifier resolves the summary path relative to
`manifests/` and then the framework bundle, not the adopter root, so it
reports the artifact as absent while returning success. A gate that cannot find
the artifact it is gating and reports `OK` is fail-open.

### Absolute explicit-path probe (fails — fixtures not registered)

```bash
bash .llm-dev/framework/scripts/verify-fix-summary-regressions.sh \
  "$PWD/docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-fix-summary.md"
```

Result: **EXIT=1** — `FAILED` with 14 diagnostics across all six findings. Every
adopter pytest fixture path is reported twice:

1. `fixture 'tests/commands/test_agentic_activation_resilience.py' does not
   exist` — the script resolves fixture paths relative to
   `.llm-dev/framework/`, not the adopter root where the tests actually live.
2. `is not registered as an exercised regression fixture in
   scripts/verify-all.sh (not listed in eh15a_regression_fixtures)` — no
   config key or adopter hook registers Project Ontos tests.

Both probe shapes confirm D4-INFRA-1: `verify-fix-summary-regressions.sh` in
the pinned framework v2.0.1 cannot honestly register or verify adopter-local
regression fixtures under EH-15-A. This is a pre-existing framework
integration blocker, not a product defect or a test-harness failure.

## Verdict

Request changes

## If "Request changes"

| Finding | Evidence | Required further action |
|---|---|---|
| CAN-ACT-1 | Pre-fix: 4 failed (exit 1), missing `Reason:` line. Post-fix: 4 passed (exit 0). direct-run. | Addressed; no further product action. |
| CAN-ACT-2 | Pre-fix: 4 failed (exit 1), `Config error:` instead of canonical prefix. Post-fix: 4 passed (exit 0). direct-run. | Addressed; no further product action. |
| CAN-CP-1 | Pre-fix: 8 failed (exit 1), issue-158 mutations not checked. Post-fix: 8 passed (exit 0). direct-run. | Addressed; no further product action. |
| CAN-CP-2 | Pre-fix: 8 failed (exit 1), duplicates not rejected. Post-fix: 8 passed (exit 0). direct-run. | Addressed; no further product action. |
| CAN-CP-3 | Pre-fix: 8 failed (exit 1), exit 2 instead of 1. Post-fix: 8 passed (exit 0). direct-run. | Addressed; no further product action. |
| CAN-ID-1 | Pre-fix: 24 failed (exit 1), false-green no-op + divergent codes. Post-fix: 24 passed (exit 0). direct-run. | Addressed; no further product action. |
| D4-INFRA-1 | Manifest-mode probe: EXIT=0 false PASS ("no fix-summary exists"). Explicit-path probe: EXIT=1 FAILED (14 diagnostics — adopter fixtures not registered). direct-run. | Upstream framework support for an explicit adopter root and adopter-owned runnable-fixture registry, followed by a pinned framework upgrade and fresh D.4/D.5. Do not edit the forbidden framework checkout, cite an unrelated fixture, lower the manifest version, or waive the gate. |

## Nonclaim boundary

This verdict does **not** certify D.6, per-child (#146/#147) lifecycle
certification, merge, tag, publication, issue closure, or release readiness.
The product fixes are functionally verified but lifecycle closure is blocked
by D4-INFRA-1. The registry's 41 open and seven partial original findings and
the release-blocking shared-tree integration record remain authoritative;
this verification does not reinterpret them.
