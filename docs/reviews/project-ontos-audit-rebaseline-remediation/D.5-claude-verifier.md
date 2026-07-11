---
id: audit-rb-D5-cv
deliverable_id: project-ontos-audit-rebaseline-remediation
role: verifier
family: claude
phase: D.5
evidence_mode: direct-run
canonical_verdict_consumed: docs/reviews/project-ontos-audit-rebaseline-remediation/D.3-verdict.md
fix_summary_consumed: docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-fix-summary.md
clarification_artifacts: []
status: completed
verdict: Request Further Fixes
---

# Verification — project-ontos-audit-rebaseline-remediation / D.5 / claude

Every one of the six canonical D.3 findings is independently reproduced as
broken pre-fix and closed post-fix by direct execution. The full suite is green
at 1720 passed. **The product fixes are functionally sound.**

D.4 is nevertheless honestly `status: halted` on **D4-INFRA-1**, and I verified
that claim directly against the framework source rather than accepting it. It
holds, and it is materially worse than the summary states: the EH-15-A
manifest-mode gate does not merely fail to register adopter fixtures — it
returns **exit 0 / `OK`** while asserting a fix summary "does not exist" at a
path where a tracked 12,148-byte file plainly does exist. A gate that cannot
find the artifact it is gating and reports success is fail-open. Functional
success is therefore **not** certification, and my body verdict is
`Request changes`.

## Environment preconditions

| Precondition | Observed | Evidence |
|---|---|---|
| Disposable worktree HEAD | `8d5096eba940aafe1e8b86bdd3a8852961bab815` | direct-run: `git rev-parse HEAD` |
| Disposable worktree clean at entry | yes — `git status --porcelain` = 0 lines | direct-run |
| Test interpreter | `/tmp/project-ontos-worktrees/.../.venv/bin/python` → Python 3.14.6 | direct-run |
| Interpreter imports `ontos` from disposable worktree | yes — `ontos.__file__ = /private/tmp/project-ontos-d5-claude/ontos/__init__.py` | direct-run |
| Disposable worktree clean at exit | yes — restored to `8d5096e`, 0 dirty paths | direct-run |

The import-origin check is load-bearing: the venv lives in the *lifecycle*
worktree, so had `ontos` resolved there, every source swap below would have been
a no-op producing false PASSes. It resolves to the disposable worktree via cwd
precedence, so the swaps genuinely take effect.

### Deviation from the prescribed pytest flags (recorded, not silent)

The dispatch specified `--cache-clear`, but `--cache-clear` is owned by pytest's
`cacheprovider` plugin and is therefore **mutually exclusive** with
`-p no:cacheprovider`; the combination exits `4` with
`unrecognized arguments: --cache-clear`. I resolved this in the direction of
*stronger* evidence, per Template 15's bytecode-cache invariant:

- dropped `-p no:cacheprovider` and kept `--cache-clear`;
- added `-B` (Template 15 names `-B` as the equivalent guard);
- additionally purged every `__pycache__` directory before each swap run.

`--cache-clear` alone clears `.pytest_cache`, not `__pycache__` — `-B` plus the
purge is what actually defeats the stale-`.pyc` false-PASS that D5+D6 FL#4
recorded. All swap runs below satisfy the invariant.

## Per-finding verification table

Pre-fix implementation: `aa41c3982e21b0e0cff6c3c5486f4af9e5e55e05`.
Post-fix implementation (I2): `311b60b6e86abe6d0b5a7ac61e16d07049387707`.
Tests held at HEAD `8d5096e` throughout; only the named implementation files
were swapped.

| Blocker ID | Original failure reproduced? | Fix addresses it? | Regression test fails pre-fix? | Regression test passes post-fix? | Evidence label |
|------------|------------------------------|-------------------|--------------------------------|----------------------------------|----------------|
| CAN-ACT-1 | Yes — human `not_usable` output carried **no** `Reason:` line (`assert 0 == 1 where 0 = len([])`) | Yes | Yes — exit `1` | Yes — exit `0` | direct-run |
| CAN-ACT-2 | Yes — malformed range returned `"Config error: version clause 'not-a-range' is not a valid semantic version"`, missing the mandated `Invalid [ontos].required_version:` prefix/anchor | Yes | Yes — exit `1` | Yes — exit `0` | direct-run |
| CAN-CP-1 | Yes — issue-158 owner/scope errors absent; `root_program mismatch for issue #158` and `finding scope exceeds owner #158` never emitted | Yes | Yes — exit `1` | Yes — exit `0` | direct-run |
| CAN-CP-2 | Yes — `shared_path_leases row 0 has duplicate programs` / `duplicate order` never emitted under synchronized O5 | Yes | Yes — exit `1` | Yes — exit `0` | direct-run |
| CAN-CP-3 | Yes — malformed registry + both child manifests returned **`assert 2 == 1`** (exit `2`/`ERROR`, the fail-open routing) | Yes | Yes — exit `1` | Yes — exit `0` | direct-run |
| CAN-ID-1 | Yes — incl. the invalid same-ID false-green; live CLI pre-fix returned exit `0`/`nothing_to_do` | Yes | Yes — exit `1` | Yes — exit `0` | direct-run |

### Group A — CAN-ACT-1 / CAN-ACT-2

```bash
cd /tmp/project-ontos-d5-claude
PY=/tmp/project-ontos-worktrees/project-ontos-audit-rebaseline-remediation/.venv/bin/python
SEL="tests/commands/test_agentic_activation_resilience.py -k 'human_renders_incompatible or human_renders_malformed or json_renders_malformed'"

# post-fix (HEAD)
$PY -B -m pytest $SEL -q --cache-clear                       # exit 0 — 4 passed, 7 deselected
# pre-fix swap
git restore --source aa41c3982e21b0e0cff6c3c5486f4af9e5e55e05 -- ontos/commands/activate.py ontos/core/config.py
$PY -B -m pytest $SEL -q --cache-clear                       # exit 1 — 4 failed, 7 deselected
# restore
git restore --source HEAD -- ontos/commands/activate.py ontos/core/config.py
$PY -B -m pytest $SEL -q --cache-clear                       # exit 0 — 4 passed, 7 deselected
```

Pre-fix exit `1`; post-fix and restored exit `0`. The failure text is the D.3
failure mode verbatim, not incidental breakage.

### Group B — CAN-CP-1 / CAN-CP-2 / CAN-CP-3

```bash
K='issue_158_control_plane or control_plane_finding_id_and_issue_158 or duplicate_lease_lists or malformed_registry_yaml or malformed_child_manifest_yaml'

$PY -B -m pytest tests/test_audit_remediation_registry_validator.py -k "$K" -q --cache-clear   # exit 0 — 8 passed
git restore --source aa41c3982e21b0e0cff6c3c5486f4af9e5e55e05 -- scripts/validate-audit-remediation-registry.py
$PY -B -m pytest tests/test_audit_remediation_registry_validator.py -k "$K" -q --cache-clear   # exit 1 — 8 failed
git restore --source HEAD -- scripts/validate-audit-remediation-registry.py
$PY -B -m pytest tests/test_audit_remediation_registry_validator.py -k "$K" -q --cache-clear   # exit 0 — 8 passed
```

**Evidence caveat, recorded rather than glossed.** Restoring only the validator
script (as scoped) while the registry YAML stays at HEAD means the pre-fix run
also emits one *unrelated* error line —
`R2-control-plane-parity-1 must bind its fix commit to Phase C close I1` —
because commit `2dede68` re-bound that evidence. Consequently, for CAN-CP-1 and
CAN-CP-2 the **nonzero exit alone is weak evidence**: the run would be nonzero
anyway. The load-bearing proof is that these tests assert on the *specific
canonical error strings*, and those strings are demonstrably absent pre-fix
(`AssertionError: assert 'shared_path_leases row 0 has duplicate programs' in
'audit-registry: FAILED\n- R2-control-plane-parity-1 must bind...'`). On that
basis the regressions genuinely cover the reported failure modes. CAN-CP-3 needs
no such caveat — `assert 2 == 1` is a direct exit-code observation.

### Group C — CAN-ID-1

```bash
K='rename_invalid_ids_use_canonical or rename_invalid_id_is_rejected_before_project_discovery or build_rename_plan_uses_canonical or rename_document_invalid_ids_use_canonical or rename_document_rejects_invalid_id_before_preflight'

$PY -B -m pytest tests/commands/test_rename.py tests/mcp/test_rename_document.py -k "$K" -q --cache-clear  # exit 0 — 24 passed
git restore --source aa41c3982e21b0e0cff6c3c5486f4af9e5e55e05 -- ontos/commands/rename.py ontos/mcp/rename_tool.py
$PY -B -m pytest tests/commands/test_rename.py tests/mcp/test_rename_document.py -k "$K" -q --cache-clear  # exit 1 — 24 failed
git restore --source HEAD -- ontos/commands/rename.py ontos/mcp/rename_tool.py
$PY -B -m pytest tests/commands/test_rename.py tests/mcp/test_rename_document.py -k "$K" -q --cache-clear  # exit 0 — 24 passed
```

The parametrization `[bad same!-bad same!-bad same!]` fails pre-fix and passes
post-fix — that is exactly D.3's "invalid `old_id == new_id` therefore reports
success" false-green. Confirmed live at HEAD:

```bash
$PY -m ontos --json rename 'bad id!' 'bad id!'
# exit 2 — {"error": {"code": "E_USER_INPUT"}, "exit_category": "usage",
#           "message": "Document id must start and end with an alphanumeric character..."}
```

Pre-fix this returned exit `0` / `nothing_to_do`. Canonical code, canonical
copy, canonical usage exit.

## Regression check

| Smoke check | Result | Evidence |
|-------------|--------|----------|
| Full suite, disposable worktree (`pytest tests/ -q -p no:cacheprovider`) | **PASS** — exit 0, `1720 passed, 1 warning` in 95.39s | direct-run |
| Registry validation — local | **PASS** — exit 0 | direct-run |
| Registry validation — external/live GitHub parity (`--require-external-parity`) | **PASS** — exit 0, `mode: local+external` | direct-run |
| Changed-path scope from `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95` | **PASS** — exit 0, `OK (578 changed path(s) within scope)` | direct-run |
| Manifest conformance (`scripts/llm-dev verify <manifest>`) | **PASS** — exit 0, 4/4 checks | direct-run |
| `git diff --check HEAD` (lifecycle worktree) | **PASS** — exit 0 | direct-run |
| EH-15-A probe 1 — manifest mode | **FAIL-OPEN** — exit 0 on a false "does not exist" claim | direct-run |
| EH-15-A probe 2 — explicit summary path | **FAIL** — exit 2, `cannot read` an existing tracked file | direct-run |

The 1720-passed count matches D.4's claim exactly. The scope gate reports 578
paths where D.4 recorded 559; that is not a discrepancy — HEAD advanced by the
two D.4/D.5 documentation commits (`8d5096e`, and `0941d2f` in the lifecycle
worktree) after the summary was written. All 578 are within scope.

Note that `scripts/llm-dev verify` itself prints:
`manifest-only — does NOT prove lifecycle execution.` Its 4/4 PASS is a
conformance result, not a certification result.

## Scope-lock check

- Paths touched outside allowed set: **none**. The changed-path verifier returns
  `OK (578 changed path(s) within scope)` from the declared base.
- The `ontos/commands/rename.py` manifest omission that D.4 hit is genuinely
  closed by `737fe27`, which adds exactly that one path — no directory pattern,
  no widened lease. The recovery record in `D.4-scope-audit-recovery.md` matches
  what the manifest actually contains.
- The five implementation files changed across `aa41c39..311b60b`
  (`activate.py`, `rename.py`, `config.py`, `rename_tool.py`,
  `validate-audit-remediation-registry.py`; +184/−63) are exactly the files the
  fix summary names. No undeclared implementation drift.

## D4-INFRA-1 — verified directly, and it is worse than reported

D.4 claims llm-dev v2.0.1 (a) cannot register adopter-local EH-15-A fixtures and
(b) is fail-open in manifest-mode summary lookup. I did not take this on trust.
Both halves reproduce, and I confirmed the mechanism in the framework source.

**Probe 1 — manifest mode returns success on a file it failed to find.**

```bash
bash .llm-dev/framework/scripts/verify-fix-summary-regressions.sh \
  --manifest "$PWD/manifests/project-ontos-audit-rebaseline-remediation.yaml"
# exit 0
# verify-fix-summary-regressions: OK (no D.4 fix-summary exists at
#   docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-fix-summary.md)
```

That file **does** exist. It is tracked (`git ls-files` returns it) and is 12,148
bytes. The gate asserts nonexistence at the exact path where the artifact lives,
and grades that as `OK` / exit `0`.

**Probe 2 — explicit path cannot read the same existing file.**

```bash
bash .llm-dev/framework/scripts/verify-fix-summary-regressions.sh \
  docs/reviews/project-ontos-audit-rebaseline-remediation/D.4-fix-summary.md
# exit 2
# verify-fix-summary-regressions: cannot read docs/reviews/.../D.4-fix-summary.md
```

**Root cause (static-inspection of `verify-fix-summary-regressions.sh`, cited):**

- `:86` — `BUNDLE = Path(sys.argv[1]).resolve()`, and `:29-30` set that bundle to
  `.llm-dev/framework`. The bundle, not the adopter root, is the universe.
- `:175-187` — `repo_path()` resolves relative paths against `[base, BUNDLE]`
  only. For the manifest-declared summary path the bases are `manifests/` and
  `.llm-dev/framework/`; the adopter root is **never** a candidate. `:187` then
  returns a `BUNDLE`-relative path even when nothing exists there.
- `:443-445` — `if not fpath.exists(): print("OK (no D.4 fix-summary exists…)");
  sys.exit(0)`. **A summary the tool failed to locate is scored as success.**
  This is the fail-open: absence of evidence is rendered as evidence of
  compliance.
- `:91` + `:349-351` — the fixture registry is `BUNDLE/scripts/verify-all.sh`,
  and each fixture is resolved as `(BUNDLE / ref)` then containment-checked with
  `.relative_to(BUNDLE)`. An honest adopter ref like
  `tests/commands/test_rename.py` resolves to
  `.llm-dev/framework/tests/commands/test_rename.py`, which does not exist, so it
  is rejected. There is no adopter-root base and no config key to supply one.

D.4's characterization is accurate in every particular, including its specific
claim that the search runs "relative to `manifests/` and then the framework
bundle, not the adopter root." D.4 was right to halt rather than cite an
unrelated framework fixture, force a path collision, edit the forbidden
framework checkout, or waive the gate. Each of those would have manufactured a
green EH-15-A result on regressions that are, in fact, real and passing — which
is the precise failure this framework exists to prevent. Refusing the false
green was the correct call.

The practical hazard is that probe 1's exit `0` is **indistinguishable from a
genuine pass** to any automated caller. A future orchestrator that shells this
gate and checks only the exit status will read "EH-15-A satisfied" on a
deliverable whose fixtures were never examined. This blocks lifecycle
certification, not the product fixes.

## If "Request changes"

| Finding | Evidence | Required further action |
|---------|----------|--------------------------|
| **D4-INFRA-1** — llm-dev v2.0.1 cannot register adopter-local EH-15-A fixtures (`BUNDLE`-rooted resolution + `relative_to(BUNDLE)` containment at `verify-fix-summary-regressions.sh:91,349-351`), and manifest-mode summary lookup is **fail-open**: exit `0` / `OK` while claiming a tracked 12,148-byte fix summary "does not exist" (`:175-187`, `:443-445`). | direct-run (both probes: exit `0` and exit `2`) + static-inspection (cited source lines) | Upstream framework support for an explicit adopter root and an adopter-owned runnable-fixture registry; **and** convert the `not fpath.exists()` branch from `OK`/exit `0` to a hard failure so an unlocatable summary can never be graded as a pass. Then pin the framework upgrade and re-run a fresh D.4/D.5. Not resolvable from inside this deliverable — the framework checkout is a forbidden path. |

No product finding requires further action. All six canonical D.3 findings are
closed with direct-run pre/post evidence and the full suite is green.

## Verdict

Request changes

The six canonical findings are genuinely fixed — I reproduced every one as
broken pre-fix and closed post-fix by source swap, and 1720/1720 tests pass. If
this deliverable were graded on product correctness alone it would be an
`Approve`.

It is not. D.4 correctly halted on D4-INFRA-1, and that blocker is real: I
confirmed it by direct execution and by reading the framework source. A
verification gate that reports `OK` / exit `0` because it could not find the
artifact it was asked to verify is fail-open, and its green result is worth
nothing. Approving here would launder that fail-open into a certification.
Functional success is not certification, and I decline to round one up into the
other.

## Nonclaim boundary

This verdict does **not** certify D.6, final approval, the #146/#147 child
lifecycles, merge, tag, publication, issue closure, or release readiness. It
does not certify strict-P3 lifecycle closure or EH-15-A regression
registration — D4-INFRA-1 is preserved and remains open. It attests only to what
I directly executed: the six D.3 findings are functionally closed at
`311b60b`/`8d5096e`, the repository gates listed above pass, and the framework
infrastructure blocker holds.
