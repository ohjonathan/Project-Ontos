---
id: audit-rb-D3-verdict
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: D.3
role: meta-consolidator
family: codex
families_consulted: [claude, gemini, glm]
verdicts_consulted:
  - docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-strict-claude-peer.md
  - docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-strict-gemini-adversarial.md
  - docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-strict-glm-alignment.md
  - docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-strict-claude-product.md
consolidation_mode: external
preserved_blocker_ids: []
verify_family_dispatch_verified_by:
  family: gemini
  session_id: gemini-strict-d2-attestation-20260711
  at: "2026-07-11T02:36:33Z"
  command_output_sha256: 5a32a264a031dd32ac44a92ee92fba86b57b801c7046d8b62ea9b158d4822837
status: completed
---

# Canonical Verdict — project-ontos-audit-rebaseline-remediation / D.3

## Context header

- **Phase:** D.3 — code consolidation.
- **Date:** 2026-07-10 (America/Los_Angeles).
- **Spec under review:** `docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`
  v1.5, SHA-256
  `222c8c7a768b3f364d1b4c96f7083840a9fdde843b27e81101b5929c280a3ef7`
  (`direct-run`: `sha256sum`).
- **Implementation under review:** I1
  `05b090d53f7b0c9c4afdbb5fb23ab58cdfa01fa0`; the current committed evidence
  checkpoint is `94eb92cd10d6eaedab362b96c0e0ecbcb27363d4`
  (`direct-run`: `git rev-parse`).
- **Reviewers:** Claude / Peer, Gemini / Adversarial, GLM / Alignment, and a
  separate Claude / Product session (`orchestrator-preflight`: strict dispatch
  result plus independent Gemini attestation).
- **User-facing:** true.
- **Overall Status:** **Needs Fixes**. Six directly reproduced should-fix items
  advance to D.4; no merge-blocking item is preserved (`direct-run` and
  `static-inspection`, detailed below).

## Dispatch-integrity recheck

`verify-family-dispatch.sh --require-complete` independently returned four
completed dispatches and `OK`; the captured output still hashes to
`5a32a264a031dd32ac44a92ee92fba86b57b801c7046d8b62ea9b158d4822837`
(`direct-run`). The Gemini blind packet also passes
`verify-blind-review.sh --base-dir "$PWD"` (`direct-run`). All four verdicts and
the Gemini attestation are tracked files, none carries invalidation frontmatter,
and the verdict count equals the four formal intent rows (`direct-run`). The
attestation time above is the UTC form of the introducing commit's verified
committer timestamp, `2026-07-10T19:36:33-07:00` (`direct-run`: `git log -1
--format=%cI -- <attestation>`).

## Family verdict table

| Family | Role | Verdict | Blocker count |
|---|---|---|---:|
| Claude | Peer | Needs Fixes | 0 |
| Gemini | Adversarial | Needs Fixes | 0 |
| GLM | Alignment | Approve | 0 |
| Claude | Product | Approve | 0 |

The table is a direct transcription of the four certifying D.2 artifacts
with each source `Request changes` token normalized to Template 06's canonical
`Needs Fixes` vocabulary (`static-inspection`). The earlier non-certifying D.2
attempts were not consolidated.

## Preserved blockers (merge-blocking)

None. No formal family claimed a blocker, and independent reproduction found no
defect that warrants blocker-grade escalation before D.4 (`direct-run`).

## Downgraded blockers (now should-fix)

None. There were no blocker claims to downgrade (`static-inspection`).

## Should-fix findings

| ID | Raised/corroborated by | Supported finding | Location | Evidence and observed result | Required D.4 action |
|---|---|---|---|---|---|
| CAN-ACT-1 | Claude Product PRD-1; meta-consolidator | Human `ontos activate` omits the actionable `reason` when activation is `not_usable`; the payload and JSON channel retain it, but the ordinary human lines show only status/counts/recommendation. | `ontos/commands/activate.py:218-246` | `direct-run`: an injected incompatible config returned exit `1` and the full `Incompatible Ontos version...` payload reason; `format_activation_output(payload)` contained no reason (`reason_rendered=False`). | Render a stable `Reason: <payload.reason>` line for `not_usable` human output and add incompatible + malformed-range human regressions. |
| CAN-ACT-2 | Claude Product PRD-2; meta-consolidator | Config-load validation shadows the public malformed-range path: activation returns `Config error: ...`, losing the mandated `Invalid [ontos].required_version` prefix and exact Migration anchor. | `ontos/core/config.py:181-184`; `ontos/commands/activate.py:85-95`; documented branch `ontos/core/config.py:258-280` | `direct-run`: malformed `>=not.a.version` returned exit `1`, reason `Config error: version clause ...`, `prefix_ok=False`, `anchor_ok=False`. | Route malformed `required_version` errors through the one public incompatibility formatter without double-echoing the clause; preserve `E_ACTIVATION_UNUSABLE`, `not_usable`, exact prefix/anchor, eager parsing, and singular offending-clause copy. |
| CAN-CP-1 | Meta-consolidator | The legitimate issue-158 control-plane finding is exempted from the owning-program branch, so arbitrary nonempty `root_program` and canonical `allowed_paths` values bypass owner/scope parity while validation returns success. | `manifests/project-ontos-audit-remediation-registry.yaml:1097-1118`; `scripts/validate-audit-remediation-registry.py:1404-1425` | `direct-run`: changed only `R2-control-plane-parity-1.root_program` to `unrelated-root-with-no-program` and `allowed_paths` to `outside/program/scope.md` in memory; `validate(False)` returned `[]`. | Give the issue-158 row an explicit owner/scope authority (without adding it to the required #146-#157 program set), validate its exact root, and prove every allowed path is covered by that authority. Add root and scope mutation regressions through `main()`. |
| CAN-CP-2 | Meta-consolidator | `shared_path_leases[].programs` does not reject duplicates. A synchronized O5 row with `programs: [146, 147, 147]` and `order: [146, 147]` passes because later collision logic reduces participants to a set. | `scripts/validate-audit-remediation-registry.py:409-459,1526-1542,1677-1711` | `direct-run`: in-memory registry + synchronized in-memory O5 mutation returned `validate(False) == []`. | Reject duplicates independently in both `programs` and `order` during normalization, before set conversion or O5 comparison; add asymmetric duplicate regressions through `main()`. |
| CAN-CP-3 | GLM Alignment A-1; meta-consolidator | Syntactically invalid registry or child-manifest YAML escapes `load_yaml` and is caught by `main()` as `ERROR`, exit `2`, contrary to the fail-closed validation contract. | `scripts/validate-audit-remediation-registry.py:209-216,1506-1515,1889-1898` | `direct-run`: injected `yaml.YAMLError` at the registry and #146 child load sites; both returned `2` with `audit-registry: ERROR: synthetic syntax error`. | Convert YAML syntax failures at every registry-owned YAML input to path-qualified validation errors; `main()` must emit `FAILED` and exit `1`. Add registry and child syntax regressions. |
| CAN-ID-1 | Claude Peer P-1/P-2; meta-consolidator | `rename` duplicates the document-ID regex, validates only `new_id`, uses a regex-only `invalid_new_id`/exit-1 surface instead of canonical `E_USER_INPUT`, and performs the same-ID no-op before validating either supplied ID. Invalid `old_id == new_id` therefore reports success. | `ontos/commands/rename.py:28,277-328,448-475,1241-1259`; canonical `ontos/core/schema.py:83-97` | `direct-run`: invalid new ID returned exit `1`, `error.code=invalid_new_id`, and regex copy; invalid old ID returned `old_id_not_found`; `ontos --json rename 'bad id!' 'bad id!'` returned exit `0`, `nothing_to_do`. | Validate both CLI-supplied IDs with `validate_document_id` before the no-op branch; remove `_ID_PATTERN`; surface canonical copy through `E_USER_INPUT` and the public usage exit; keep the reserved-word rule only as an additional semantic guard. Add new-ID, old-ID, and invalid-same-ID parity regressions, including MCP mapping where applicable. |

All six are real contract or false-green defects, but each is bounded, has a
deterministic repair, and produced neither document corruption nor an unsafe
external write in the reproduction (`direct-run`). They are therefore
should-fix findings for D.4, not preserved blockers.

## Minor / deferred findings

| ID | Source | Disposition | Evidence |
|---|---|---|---|
| MIN-1 | Claude Peer P-3 | Defer or document: `--quiet` suppresses archive-marker text while exit `3` remains. Quiet-mode suppression is internally consistent; D.4 may add an explicit test/comment if it touches this path. | `static-inspection`: `ontos/commands/log.py:357-361`; no incorrect exit was claimed. |
| MIN-2 | Claude Product PRD-3 | Cosmetic defer: the archive-marker warning precedes the success line. Both lines and the retained path are visible; order does not change recovery or exit semantics. | `direct-run` evidence in the Product verdict. |
| MIN-3 | GLM Alignment A-2 | No required change: `--title` is the actual input that determines the slug, so the current collision hint supplies the documented recovery even without the literal word `slug`. | `static-inspection`: `ontos/commands/log.py:310-313`; GLM also classified this non-behavioral. |

Claude Peer P-2 is subsumed by CAN-ID-1 rather than counted again
(`static-inspection`).

## Dismissed findings

| Signal | Disposition | Direct evidence |
|---|---|---|
| Gemini S-1 — incompatibility fallback must be terminal | Dismiss as contrary to the approved contract, not an implementation defect. | `static-inspection`: `AGENTS.md:33-36`, `Migration_v3_to_v4.md:138-143`, and the user-approved plan explicitly require fallback when a candidate is absent **or incompatible**. This verdict does not re-scope that authority. |
| Gemini S-2 — quarantining malformed #146 can silently pass | Refuted. | `direct-run`: invalidated #146's `allowed_paths`; validation returned 83 errors, including `required program membership mismatch: missing=[146]`, unavailable child-manifest parity, and O4 mismatch. |
| Gemini S-3 — destination symlink swap overwrites the symlink target | Refuted for the stated reproduction. | `direct-run`: `test_commit_verifies_final_binding_and_restores_original` and `test_commit_parent_swap_after_validation_cannot_escape_workspace` passed; the external sentinels remained unchanged. `static-inspection`: mutations use pinned directory descriptors and no-follow binding checks (`ontos/core/context.py:994-1183`). |
| Gemini S-4 — YAML-coerced IDs reach sorting and crash | Refuted. | `direct-run`: `tests/test_document_loading_contract_a1.py` and `tests/test_frontmatter_roundtrip_regression.py` passed (23 tests in those files); non-string IDs become `parse_error` with canonical copy before sorting. |
| Gemini M-1 — `ontos verify` needs an explicit target/dirty-tree warning | Dismiss as unsupported and outside the approved contract. | `static-inspection`: no spec requirement or reproduced wrong-target mutation was cited. |
| Gemini M-2 — deleted init logs remain in the context map | Refuted. | `direct-run`: `rg '2026-07-0[239]_init' Ontos_Context_Map.md` returned no match, and the three paths are untracked/absent. |
| Gemini diagram claims | Refuted. | `static-inspection`: spec §10.2 already routes D.5 failure to D.4 and D.4 back through D.2; the audit validator is a control-plane script, not a runtime dependency of `activate` or `link-check`, so the proposed Validator→CLI/MCP edge is not required. |

## Contradictions

| Contradiction | Family claims | Resolution |
|---|---|---|
| Every CLI ID uses the canonical validator. | GLM marked the constraint verified after checking `stub`; Claude Peer found the `rename` duplicate. | Claude is factually correct for the complete surface. `rename.py:28,324-327` duplicates the regex, and direct CLI runs show divergent copy/code plus an invalid-ID no-op. CAN-ID-1 controls (`direct-run`, `static-inspection`). |
| Malformed activation ranges use the documented prefix and anchor. | GLM inspected `required_version_incompatibility`; Product observed the reachable activation path returning `Config error`. | Product is factually correct for reachability. Config-load parsing at `config.py:181-184` raises before `required_version_incompatibility` runs; direct execution reproduced the missing prefix/anchor. CAN-ACT-2 controls (`direct-run`). |
| Name-based writer replacement remains exploitable. | Gemini predicted an external overwrite; Claude/GLM described binding/pinned-directory protection. | The stated Gemini fact is false on the reviewed implementation: targeted destination and parent-swap regressions pass with unchanged external sentinels. No unresolved factual contradiction remains (`direct-run`). |
| Quarantined programs and non-string IDs silently fall through. | Gemini predicted false-green/crash; Claude/GLM described exact-set and loader gates. | Direct runs support Claude/GLM: malformed #146 produces membership/downstream errors; non-string IDs are rejected as loader parse errors. No unresolved factual contradiction remains (`direct-run`). |

## Agreement analysis

- **Issues raised by at least two independent passes:** CAN-ACT-1,
  CAN-ACT-2, CAN-CP-3, and CAN-ID-1 were raised by a formal family and
  independently reproduced by the meta-consolidator (`direct-run`).
- **Single-pass issues with reproduction:** CAN-CP-1 and CAN-CP-2 are new
  meta-consolidator findings with full `validate(False)` false-green
  reproductions (`direct-run`).
- **Single-family issues without surviving reproduction:** Gemini S-1 through
  S-4 and M-1/M-2 are dismissed with the evidence above; none is promoted by
  vote counting (`direct-run`, `static-inspection`).

## Metrics

| Counter | Value |
|---|---:|
| Blockers claimed (all families) | 0 |
| Blockers preserved | 0 |
| Blockers downgraded to should-fix | 0 |
| Should-fix findings (canonical) | 6 |
| Minor/deferred findings (canonical) | 3 |

| Family / role | Claimed blockers | Preserved | Downgraded | Manifest evidence cap |
|---|---:|---:|---:|---|
| Claude / Peer | 0 | 0 | 0 | — |
| Gemini / Adversarial | 0 | 0 | 0 | static-inspection |
| GLM / Alignment | 0 | 0 | 0 | — |
| Claude / Product | 0 | 0 | 0 | — |

## Required actions for author

1. Close CAN-ACT-1 and CAN-ACT-2 together so both human and JSON activation
   channels retain the exact version-failure reason contract.
2. Close CAN-CP-1, CAN-CP-2, and CAN-CP-3 in the quarantine-before-consumers
   boundary, with each mutation exercised through `main()` and asserted as
   exit `1` / `FAILED`, never `2` / `ERROR`.
3. Close CAN-ID-1 for both `old_id` and `new_id` before same-ID short-circuiting,
   then prove canonical copy/code equality at CLI and shared rename surfaces.
4. Run the focused activation, registry, rename, writer, and loader matrices,
   then the full manifest D.5 smoke suite. Any changed implementation snapshot
   must become the new reviewed implementation reference before D.5.

## Smoke-check re-baseline implications

There are no preserved blockers and no manifest smoke-check output regex is
implicated (`static-inspection`). D.4 must add regressions without weakening the
full-suite or registry-validator commands; no smoke regex re-baseline is
currently needed.

## Watch items (non-gating at D.3)

- Real Windows runner, TestPyPI/PyPI tag-run, and live GitHub parity remain
  external-pending evidence, exactly as spec §§2-3 and §11 state
  (`static-inspection`).
- Runtime fallback on incompatibility is an intentional approved behavior; the
  migration requirement to upgrade every candidate runtime before adopting
  `required_version` remains the mitigating operator instruction
  (`static-inspection`).
- The manifest declares no top-level formal `watch_item`, so no P15
  watch-item re-attestation section applies (`static-inspection`).

## Nonclaim boundary

This verdict does **not** certify D.5 or D.6, the #146/#147 child lifecycles,
Windows execution, live GitHub parity, a TestPyPI/PyPI artifact, merge, tag,
publication, issue closure, or release readiness (`static-inspection`: spec
§§2-3 and §9). The registry's 41 open and seven partial original findings and
the release-blocking shared-tree integration record remain authoritative; this
umbrella consolidation does not reinterpret them (`static-inspection`).

## Direct reproduction record

### Dispatch and packet integrity

```bash
bash .llm-dev/framework/scripts/verify-family-dispatch.sh --require-complete \
  --manifest manifests/project-ontos-audit-rebaseline-remediation.yaml \
  --intent docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-strict-final-dispatch-intent.yaml \
  --result docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-strict-final-dispatch-result.yaml

bash .llm-dev/framework/scripts/verify-blind-review.sh \
  --intent docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-strict-final-dispatch-intent.yaml \
  --result docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-strict-final-dispatch-result.yaml \
  --base-dir "$PWD"
```

Result: four dispatches verified; blind Gemini packet verified; both commands
exit `0` (`direct-run`).

### Activation and rename

```bash
./.venv/bin/python - <<'PY'
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from ontos.commands import activate
from ontos.core.config import ConfigError, dict_to_config
from ontos.io.config import load_project_config

root = Path.cwd()
base = load_project_config(repo_root=root)
bad = replace(base, ontos=replace(base.ontos, required_version=">=99.0.0"))
with patch.object(activate, "load_project_config", return_value=bad):
    code, payload = activate.run_activation(None, write_map=False, root=root)
lines = activate.format_activation_output(payload)
print(code, payload["reason"], any(payload["reason"] in line for line in lines))

try:
    dict_to_config({"ontos": {"required_version": ">=not.a.version"}}, repo_root=root)
except ConfigError as exc:
    with patch.object(activate, "load_project_config", side_effect=exc):
        code, payload = activate.run_activation(None, write_map=False, root=root)
print(code, payload["reason"])
PY

./.venv/bin/python -m ontos --json rename valid_id 'bad id!'
./.venv/bin/python -m ontos --json rename 'bad id!' valid_id
./.venv/bin/python -m ontos --json rename 'bad id!' 'bad id!'
```

Result: activation printed `(1, Incompatible..., False)` and then a generic
`Config error` without the stable anchor; rename produced respectively
`invalid_new_id`/exit `1`, `old_id_not_found`/exit `1`, and
`nothing_to_do`/exit `0` (`direct-run`).

### Control-plane false-green and syntax cases

```bash
./.venv/bin/python - <<'PY'
import contextlib, copy, importlib.util, io, sys, yaml
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "audit_validator_d3", Path("scripts/validate-audit-remediation-registry.py")
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
original_load = m.load_yaml
registry = original_load(m.REGISTRY_PATH)
ledger = m.LEDGER_PATH.read_text(encoding="utf-8")

r1 = copy.deepcopy(registry)
f = next(x for x in r1["findings"] if x["id"] == "R2-control-plane-parity-1")
f["root_program"] = "unrelated-root-with-no-program"
f["allowed_paths"] = ["outside/program/scope.md"]
m.load_yaml = lambda p: r1 if p == m.REGISTRY_PATH else original_load(p)
print("CP1", m.validate(False))

r2 = copy.deepcopy(registry)
lease = next(x for x in r2["shared_path_leases"] if x["path"] == "docs/logs/")
lease["programs"] = [146, 147, 147]
ledger2 = ledger.replace(
    "| `docs/logs/` | #146, #147 | #146 → #147 | ordered |",
    "| `docs/logs/` | #146, #147, #147 | #146 → #147 | ordered |",
    1,
)
original_read = Path.read_text
def read_text(self, *args, **kwargs):
    return ledger2 if self == m.LEDGER_PATH else original_read(self, *args, **kwargs)
m.load_yaml = lambda p: r2 if p == m.REGISTRY_PATH else original_load(p)
with patch.object(Path, "read_text", read_text):
    print("CP2", m.validate(False))

def syntax_case(target):
    def raising_load(path):
        if path == target:
            raise yaml.YAMLError("synthetic syntax error")
        return original_load(path)
    m.load_yaml = raising_load
    err = io.StringIO()
    with patch.object(sys, "argv", ["validator"]), contextlib.redirect_stderr(err):
        code = m.main()
    return code, err.getvalue().strip()
print("CP3-registry", syntax_case(m.REGISTRY_PATH))
print("CP3-child", syntax_case(m.SERIALIZER_MANIFEST_PATH))
PY
```

Result: CP1 `[]`; CP2 `[]`; both CP3 cases `(2, 'audit-registry: ERROR:
synthetic syntax error')` (`direct-run`).

### Refutation checks

```bash
./.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_session_context.py::TestSessionContext::test_commit_verifies_final_binding_and_restores_original \
  tests/test_session_context.py::TestSessionContext::test_commit_parent_swap_after_validation_cannot_escape_workspace \
  tests/test_document_loading_contract_a1.py \
  tests/test_frontmatter_roundtrip_regression.py
```

Result: `25 passed`; the two writer attacks preserve external sentinels, and
the loader/serializer cases reject coerced IDs before downstream sorting
(`direct-run`).

## Verdict

Needs Fixes

## Decision summary

The split D.2 board is mechanically valid and the strongest direct evidence
supports six should-fix defects: two activation-copy/visibility gaps, three
control-plane false-green/error-routing gaps, and one canonical rename-ID gap.
None caused corruption or an external write in reproduction, so the preserved
blocker list is empty; nevertheless the implementation does not yet satisfy
spec v1.5 and must not advance directly to D.5 (`direct-run`,
`static-inspection`).

## Next phase

Proceed to **D.4 fix-author** for CAN-ACT-1, CAN-ACT-2, CAN-CP-1,
CAN-CP-2, CAN-CP-3, and CAN-ID-1. Re-review and D.5 verification must bind to
the resulting committed implementation snapshot; D.6 remains outside the
user-authorized stop boundary.
