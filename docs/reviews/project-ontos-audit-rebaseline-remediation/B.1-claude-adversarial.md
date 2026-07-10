---
id: project-ontos-audit-rebaseline-remediation-B.1-claude-adversarial
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: adversarial
family: claude
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Adversarial Review — project-ontos-audit-rebaseline-remediation / B.1 / claude

Operational identity attested: branch `codex/audit-rebaseline-remediation-lifecycle`,
`git rev-parse HEAD` = `1973ccab047d18acf487428d6a891ed242a19e34` (three commits past
frozen I0 `b6f89d7…`: spec + dispatch-freeze commits, expected). Reviewed range
`bf91b42…b6f89d7` (188 files, +9520/−4356). Author family `codex`; my provider
`claude` differs from the author provider — family-diversity invariant satisfied,
no same-provider halt.

## 1. Input boundary attestation

The dispatch exposed operational preflight (identity, paths, output location), the
spec bytes, and the implementation diff/reference bytes only. It did **not** prefill
any suite-passed, prior-approval, guard-discharged, coverage-sufficient, or
spec-matches-code assurance. No blocker against prompt assembly. I re-derived every
invariant below from the spec and the diff and then attacked it; command *outcomes*
in this review are my own direct-run results, not supplied facts.

## 2. Invariant re-derivation

Derived from spec §§4.1–4.5, §11, and the diff:

- **I-SER (fail-closed serializer):** `serialize_frontmatter(mapping)->str` keeps its
  public signature, dumps ordered fields, and MUST reject any input whose serialized
  form does not reparse to a semantically-equal mapping.
- **I-ID:** document IDs are strings matching `^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$`;
  non-string / empty / pattern-violating IDs raise.
- **I-WR (safe writer):** `SessionContext.commit` rejects outside-root paths, symlink
  parents, symlink/non-regular destinations, and duplicate pending destinations; stages
  via exclusive no-follow temp + fsync + anchored replace, with rollback.
- **I-LOG:** log creation uses configured `logs_dir` + the shared safe serializer +
  exclusive creation; a collision is a user-visible `E_LOG_EXISTS` and never overwrites.
- **I-VER:** `required_version` incompatibility (and invalid ranges) fail closed at
  activation/doctor; doctor executes the PATH `ontos` and compares its reported version.
- **I-REG (control plane):** the validator is the sole status authority and blocks on
  cardinality (exactly 91 original + 9 R2), severity parity, phantom IDs, evidence-path
  existence, issue range, and status-set drift; status ≠ lifecycle state.
- **I-SCOPE:** 41 `confirmed_open` + 7 partial originals remain explicit and are not
  reinterpreted as fixed; umbrella review does not certify child issues, D.6, or release.

## Fresh attack-surface derivation

| Attack surface | In scope? | Evidence attempted | Result |
| --- | --- | --- | --- |
| Serializer round-trip corruption (date-like/quoted/Unicode/list scalars) | Yes | direct-run (11 roundtrip regressions) + read `assert_frontmatter_roundtrip` | Fail-closed; unconditional full-dict reparse-equality check |
| Document-ID type/pattern bypass | Yes | direct-run (contract-a1 suite) + read `validate_document_id` | Enforced; non-str/empty/pattern raise before dump |
| Writer path escape / symlink parent / duplicate dest | Yes | static-inspection of `_prepare_operations`, `_safe_workspace_path`, `_open_posix_parent`, `_stage_text` | Lexical containment + dir_fd O_NOFOLLOW anchoring + dev/ino rebind check; no bypass found |
| Log writer symlink/collision | Yes | static-inspection `_write_log_exclusively` + `create_session_log` | O_EXCL refuses symlink-at-dest & collision; `logs_dir.resolve()` follows a symlinked *parent* (M-1) |
| Registry negative controls (cardinality/severity/status) | Yes | direct-run validator + read enforcement (lines 244–289) | Real hardcoded controls; malformed-row crash edge (M-2) |
| Version skew (config + doctor PATH probe) | Yes | static-inspection `config.py:223-266`, `doctor.py:593-680` | Fail-closed incl. invalid-range path |
| Read-only MCP no-writes | Yes | direct-run (`test_read_only_registration`, 7 tests) | Passes |
| Release/CI provenance (TestPyPI, OIDC, one-wheel) | Partial | static only | Spec labels external-pending; not falsifiable at B.1 — left out of scope for blocker |
| Context-map double-generation determinism | No | not run | Generating the tracked map would dirty the no-touch tree; deferred to D.5 direct-run |

## 3. Assumption attack

| Assumption | Why it might be wrong | Impact if wrong | Reproduction / proof |
|------------|------------------------|-----------------|----------------------|
| Serializer never emits corrupt frontmatter | A value could serialize to text that reparses to a different type (e.g., `2026-07-10` → date) | Silent document corruption (P0) | `serialize_frontmatter({"id":"a","x":"2026-07-10"})` — direct-run: PyYAML quotes ambiguous scalars; roundtrip check would raise on any residual drift. No corruption. |
| Writer cannot be redirected outside root | `..`/symlink parent could escape | Path escape (P1) | Read `_safe_workspace_path` (lexical `abspath`+`is_relative_to`) and `_open_posix_parent` (per-component `O_NOFOLLOW` dir_fd). Escape rejected. |
| Registry cardinality controls are real, not count-and-report | Validator might only echo counts | False-green control plane | `scripts/validate-audit-remediation-registry.py:257-266` hardcodes `Counter({"P0":1,"P1":27,"P2":63})`, `EXPECTED_R2_IDS`, and phantom-ID guard. Real negative control. |
| Log collision never overwrites | Could truncate on retry | Data loss | `log.py:337` `open("x")` (O_EXCL) → `FileExistsError` → `E_LOG_EXISTS` (`log.py:288-300`). Holds. |

## 4. Failure mode analysis

| Failure | How it happens | Would we notice? | Reproduction / proof |
|---------|----------------|------------------|----------------------|
| Serializer raises on valid-but-ambiguous input (availability, not corruption) | Over-strict reparse-equality (e.g., NaN, tuple/set) | Yes — raises `ValueError` | static-inspection `assert_frontmatter_roundtrip`; fail-closed by design, not a corruption defect |
| Validator crashes instead of reporting on malformed registry row | `row["id"]` used after only a `row.get`-guarded error append | Yes — non-zero exit, but as traceback not clean error list | **direct-run** (M-2), see Minor |
| Log write escapes root via symlinked `logs_dir` | `logs_dir = (root/logs_dir).resolve()` follows symlink components | Only if operator inspects | static-inspection (M-1); operator-config, single-operator envelope |

## 5. Diagram completeness attack

§10.1 component diagram and §10.2 lifecycle state machine both enumerate the prose
components (registry→validator→ledger/leases; loader/serializer→writer→CLI/MCP;
activation/doctor; locking; release→tests→generated map) and mark the three external
boundaries (GitHub / Windows runner / TestPyPI) as dashed. §10.2 shows the D3→D4 fix
loop, D5 FAIL→D4, and the loose-falsification→D4 back-edge, i.e. the failure/retry
paths. No prose error-path or component is absent from the diagrams. No blocking
mismatch.

## 6. Edge case inventory

- Empty frontmatter `{}` → empty string, roundtrip `{}=={}` passes (read).
- Date-like / hash-leading / comma-in-list-item / Unicode / multiline scalars — covered
  by `tests/test_frontmatter_roundtrip_regression.py` (11 passed, direct-run).
- Non-string / whitespace-only / pattern-violating ID → raise (contract-a1, 12 passed).
- Symlink at log destination → `O_EXCL` refuses (EEXIST). Symlinked `logs_dir` parent →
  followed (M-1).
- `..` traversal / absolute path outside root in writer → rejected lexically.
- Duplicate pending destination / move onto self → rejected (`_prepare_operations`).
- Invalid `required_version` range → doctor "failed" (fail-closed).
- Registry row with `origin` but no `id` → uncaught `KeyError` (M-2).

## 7. Security surface

- **Path/symlink injection (writer):** primary POSIX path uses `openat`-style dir_fd
  chaining with `O_DIRECTORY|O_NOFOLLOW` per component, `O_EXCL|O_NOFOLLOW` temp create,
  and a `st_dev/st_ino` rebind check (`_verify_anchor_binding`); Windows pins
  non-delete-sharing handles rejecting reparse points. No TOCTOU bypass constructed.
- **Log writer:** narrower guarantee than the SessionContext writer; symlinked `logs_dir`
  parent is followed (M-1). Requires pre-existing workspace write access to exploit → not
  a privilege boundary under the single-operator threat model.
- **Injection into serialized YAML:** `yaml.safe_dump`/`safe_load` only; ambiguous scalars
  auto-quoted; roundtrip guard blocks any injection that would change parsed structure.
- **Command execution (doctor):** runs resolved-PATH `ontos --version` with a 5s timeout
  and `capture_output`; no shell, argv list form. No injection surface.
- **Secret exposure / OIDC:** release provenance is static-only at B.1 and spec-labeled
  external-pending; no secret handling in the reviewed Python surface.

## 8. Issues found

### Blocking (Critical)

None. No reproducible blocker was constructed. The serializer, safe writer, log
collision path, version-skew checks, and registry control plane are all fail-closed
under the inputs I attacked, and the spec's direct-read citations match the code at the
cited anchors.

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| — | — | — | — | — | — | — |

### Should-fix (Major)

None gating. (M-1/M-2 below are minor; the release/Windows/TestPyPI external proofs
are already spec-declared pending, so they are not should-fix defects at B.1.)

### Minor

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| X-M1 | Log writer follows a symlinked `logs_dir` parent, unlike the no-follow `SessionContext` writer. Spec §4.3 only claims "exclusive creation" for logs, so this is honest asymmetry, not an overclaim — but it is a discovered writer surface without the no-follow hardening. | `ontos/commands/log.py:115,336-340` | static-inspection | Set `[paths].logs_dir` to a path whose component is a symlink to an out-of-root dir; `ontos log` writes the log to the symlink target (O_EXCL only refuses a symlink *at* the final file). | Log may be written outside the workspace root via a symlinked parent | Anchor log creation through the same no-follow parent-pin used by `SessionContext`, or reject symlinked `logs_dir` components explicitly. |
| X-M2 | Registry validator raises an uncaught `KeyError: 'id'` on a findings row that has `origin` but no `id`, instead of returning its graceful "missing fields" error list. Still fail-closed (crash → non-zero exit), but the negative-control message is unreachable for that row. | `scripts/validate-audit-remediation-registry.py:244` (also 245,268,274,285) | direct-run | Load the registry, append `{"origin":"fable_audit","severity":"P2"}` (no `id`) to `findings`, point `REGISTRY_PATH` at it, call `validate(False)` → `UNCAUGHT_EXCEPTION: KeyError 'id'`. | Traceback instead of the collected `missing fields: ['id',...]` error | Build `original`/`r2`/status sets over `row.get("id")` and skip/emit-error on rows already flagged for a missing id. |

## Verdict

Approve

I attacked fail-closed behavior, writer/path security, serializer inputs, version skew,
registry negative controls, scope/status parity, and overclaiming, with direct-run where
possible (registry validator PASS: 91 original [P0=1/P1=27/P2=63] + 9 R2, confirmed_open=41,
partial=7 — matching spec §1; 118 named regression tests PASS). I found no reproducible
blocking or gating defect. The implementation is unusually defensive and the spec is
notably non-overclaiming (distributed-transaction, registrar-removal, Windows, TestPyPI,
and per-issue certification are all explicitly *not* claimed; 41 open / 7 partial states
are preserved). The two minor findings (log-writer symlink-parent asymmetry; validator
malformed-row crash) are both fail-closed and non-gating. External proofs (Windows CI,
TestPyPI tag-run, live GitHub parity) remain correctly pending for D.5 and are not B.1
blockers.

## Notes

- Evidence: `direct-run` = registry validator, the seven spec invariant-matrix regression
  modules (118 tests), and the X-M2 isolated repro, all via the repo `.venv` (pytest 8.4.2,
  Python 3.14.6); `static-inspection` = reads of the cited writer/serializer/config/doctor
  anchors. No `orchestrator-preflight` claims. Evidence cap treated as `direct-run` (no
  manifest cap supplied to me).
- Context-map double-generation determinism (§4.5) is **not-run**: regenerating the tracked
  `Ontos_Context_Map.md` would dirty the no-touch tree; defer to D.5 direct-run.
- I did not commit (Adversarial review role: orchestrator stages/commits). No files written
  outside the artifact path. `docs/logs/` left untouched.
