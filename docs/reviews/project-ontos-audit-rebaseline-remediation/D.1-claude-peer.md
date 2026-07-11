---
id: project-ontos-audit-rebaseline-remediation-D.1-claude-peer
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: D.1
role: peer
family: claude
evidence_labels_used: [direct-run, static-inspection, not-run]
status: completed
---

# Peer Review — project-ontos-audit-rebaseline-remediation / D.1 / claude

Fresh, non-certifying pre-review of spec v1.5
(`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`) against the
frozen Phase C implementation I1 `05b090d` and the committed evidence
checkpoint at HEAD `7467a73`, branch
`codex/audit-rebaseline-remediation-lifecycle`. Historical base `bf91b42`;
immutable I0 `b6f89d7`. Both `git diff bf91b42..05b090d` and
`git diff 05b090d..HEAD` were inspected. This review does not read
B.1/B.2/D verdicts, receipt inventories, dispatch results, or sibling
reviews; conclusions are independent. It does not certify lifecycle
closure, external (Windows/TestPyPI/live-GitHub) proof, or a release.

## 1. Completeness check

Every Phase C construction gate the spec pins to §§4.1–4.5 is present and
was exercised where reachable offline:

- **§4.1 typed/quarantine control plane** — `scripts/validate-audit-remediation-registry.py`
  performs a structural + type pass (`validate()`, `scripts/…:867-960`) before
  any consumer. Non-mapping root (`:872`), non-list `findings/programs/
  shared_path_leases` (`:889-891`), per-row mapping guards, enum validation
  (`FINDING_ORIGINS`/`FINDING_SEVERITIES`, `:951-960`), canonical-path checks
  (`is_canonical_repo_path`, `:273`), and normalized `#146`–`#157` membership
  are all wired. `main()` (`:1881-1911`) returns `1`/`FAILED` on collected
  errors and reserves `2`/`ERROR` for the fail-closed `except` net only.
  **Direct-run** (18 malformed constructions below) confirms exit `1`, never
  `2`, for every case reached.
- **§4.2 loader/serializer + ID contract** — `validate_document_id`
  (`ontos/core/schema.py:83-97`) uses the exact spec pattern and the three
  documented messages; CLI ID input routes through the same validator and
  surfaces `E_USER_INPUT` (`ontos/commands/stub.py:183-187`). No divergent
  CLI regex found (**direct-inspection** of all `validate_document_id`
  callers).
- **§4.3 safe writer / logging / lock** — `SessionContext` carries
  source/temp/backup `_EntryBinding`s and rechecks device/inode/type before
  and after every rename/unlink (`ontos/core/context.py:397-613`);
  `create_text_file_exclusively` (`:229-286`) is O_EXCL + O_NOFOLLOW +
  anchor-pinned. Log collision → `E_LOG_EXISTS` with the no-overwrite fact +
  title/move-or-remove recovery hint (`ontos/commands/log.py:319-332`);
  archive-marker failure → human warning beginning `Session log created, but
  archive marker was not updated:`, JSON `warnings[]`, exit `3`
  (`:362-388`). `logs_dir` is kept lexical (no `.resolve()`, `:130-133`).
  Both lock entry points (`SessionContext._acquire_lock` `:1361-1450`, MCP
  `workspace_lock` `ontos/mcp/locking.py:26-108`) share
  `open_lock_file`/`verify_lock_file_binding` with `st_nlink != 1` and
  reparse rejection before acquire (`ontos/core/locking.py:134-214`).
- **§4.4 CLI/MCP/activation/platform** — eager clause parsing +
  singular-literal + clause-identification + exact guidance anchor
  (`ontos/core/config.py:222-345`, **direct-run** below); doctor executes
  the PATH `ontos --version` and reports skew/incompatibility
  (`ontos/commands/doctor.py:594-696`); read-only MCP omits write tools
  (`ontos/mcp/server.py:197-217`) and refuses persistent graph export
  (`ontos/mcp/tools.py:396-400`); JSON envelope has exactly the nine
  top-level keys and the `0/1/2/3/5/130` taxonomy with `4` absent from
  `ExitCode` (`ontos/ui/json_output.py:29-49,331-343`).
- **§4.5 release/tests/metadata** — `scripts/check_release_artifact.py`,
  `.github/workflows/{ci,publish}.yml`, and the generated-map machinery are
  present in the `bf91b42..05b090d` diff; workflow/wheel/map assertions live
  in `tests/test_ci_release_workflows.py`, `tests/test_release_artifact.py`,
  and `tests/commands/test_map.py` (**static-inspection**; not executed per
  the no-full-suite instruction).

The HEAD checkpoint (`05b090d..HEAD`) adds one control-plane parity row
(`R2-control-plane-parity-1`) binding its fix commit to Phase C close I1
(`05b090d`) with a matching validator gate and regression
(`tests/test_audit_remediation_registry_validator.py:413-440`). This is
evidence bookkeeping, not a behavior change, and is internally consistent.

No mandatory spec section is missing.

## 2. Diagram-prose cross-reference

Both diagrams (§10.1 component, §10.2 lifecycle) were checked against §§3–4
prose. Every diagram node maps to prose and every prose subsystem appears in
a diagram; the lifecycle diagram shows the D.4→D.2 retry and
D.5→loose-falsification paths. No mismatch — no blocking diagram finding.

| Diagram component | In prose? | Prose component | In diagrams? |
|-------------------|-----------|-----------------|--------------|
| Audit Registry (A) | §4.1 | Registry/validator/control plane | A/V |
| Validator / Control Plane (V) | §4.1 | O4 ledger + O5 leases | L |
| O4 Ledger + O5 Leases (L) | §4.1 | Loader + serializer | S |
| Canonical Loader + Serializer (S) | §4.2 | Safe writer + CLI logging | W |
| Safe Writer + CLI Logging (W) | §4.3 | CLI/MCP contracts | C |
| CLI / MCP Contracts (C) | §4.4 | Activation + doctor | X |
| Activation + Doctor (X) | §4.4 | Cross-platform locking | K |
| Cross-platform Locking (K) | §4.4 | Release pipeline | P |
| Release Pipeline (P) | §4.5 | Tests + lifecycle evidence | T |
| Tests + Lifecycle Evidence (T) | §4.5/§6 | Generated map + AGENTS | M |
| Generated Map + AGENTS (M) | §4.5 | GitHub (external) | G |
| EXTERNAL GitHub (G) | §3/§4.1 | Windows runner (external) | R |
| EXTERNAL Windows Runner (R) | §3/§4.4 | TestPyPI/PyPI (external) | Y |
| EXTERNAL TestPyPI/PyPI (Y) | §3/§4.5 | — | — |

## 3. Quality assessment

The implementation is unusually faithful to a demanding spec. The
control-plane validator is the standout: rather than a finite list of
subscript guards, it normalizes every consumed collection through dedicated
`normalize_*` helpers that append row/field-scoped errors and quarantine bad
rows, so the fail-closed `except` in `main()` is a genuine last resort rather
than the primary error path. My 18-case direct-run table (non-mapping roots,
wrong list/mapping types, `None`/absolute/escaping/nested paths, unhashable
IDs, invalid enums, ownership drift, dropped `#146`, malformed snapshot
metadata, duplicate `affected_issues`) all produced exit `1`/`FAILED` with
descriptive messages and zero uncaught exceptions.

The filesystem layer is the other high-quality area. The `_EntryBinding`
capture/recheck discipline in `SessionContext.commit`, the shared
no-follow/single-link lock opener used by both CLI and MCP callers, and the
deliberately-lexical `logs_dir` (with an inline comment explaining why
`.resolve()` would defeat the no-follow writer) show the author internalized
the spec's threat model rather than pattern-matching it. Exception hygiene is
sound: the no-follow checks raise only `ValueError`/`RuntimeError`/OSError
subclasses, exactly the set both the primary-log and archive-marker handlers
catch, so a symlinked `logs_dir` or a marker failure degrades to a visible
error/warning rather than a traceback.

The required-version diagnostics meet the letter of §4.4: clauses are
collected into a list before `all()` (so an earlier false comparison cannot
mask a later malformed clause — proven by the `>4.7.0, ~bad` case), the
offending clause literal appears exactly once, the multi-clause message names
the failing clause, and every failure form points at the exact
`#audit-remediation-compatibility-contracts` anchor, which resolves to a real
heading in the migration doc.

A mid-level engineer could extend this code without asking questions;
abstractions (`_EntryBinding`, `WorkspaceLockGuard`, the `normalize_*`
family, `ExitCode`/`ExitCategory`) are named and scoped consistently.

## 4. UX review

Public error/UX contracts are precise and adopter-actionable. Activation
incompatibility, invalid ranges, log collision, and archive-marker warnings
all carry stable prefixes/codes and a recovery path, and each is mirrored in
`docs/reference/Migration_v3_to_v4.md` (exit taxonomy incl. reserved `4`
lines 173-175; `E_LOG_EXISTS` + recovery line 162; marker exit `3` line 167;
`E_ACTIVATION_UNUSABLE` line 139; supported ranges + prefixes lines 128-141;
pre-adoption runtime warning line 125). The warnings-only exit `3` migration
impact for shell automation is called out (line 177). Documentation is in
sync with the §§4.2/4.4 code anchors, so the §7 "doc drift blocks D.1"
condition is satisfied. `--json` and human surfaces stay consistent (same
message text in `warnings[]` and on stdout).

## 5. Issues found

### Blocking (Critical)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| — | None. No reproducible defect surfaced; every direct-run construction behaved per spec. | — | direct-run | (see §8) | — |

No blocking Peer finding is warranted: Template 03 requires `direct-run`/
`orchestrator-preflight` evidence for a blocker, and every direct-run I
executed passed.

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| — | None. | — | static-inspection | — | — |

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-1 | Log collision returns shell exit `1` (the taxonomy's `findings` bucket) for a pre-existing-log precondition, which is semantically closer to a usage/precondition error than a lint finding. It is intentional and documented (migration doc line 162; matches frozen-I0), so this is a taxonomy-fit nit, not a defect. | `ontos/commands/log.py:319-330`; `docs/reference/Migration_v3_to_v4.md:162` | static-inspection | Run `ontos log` twice with the same title | Optionally note in the taxonomy prose that `E_LOG_EXISTS` maps to `1` by continuity; no code change required. |
| P-2 | The primary exclusive log write uses O_EXCL + O_NOFOLLOW + anchor pinning and does **not** take `.ontos.lock` (only the marker `commit()` does). This is safe (O_EXCL provides create-once atomicity across processes), but the safety rationale lives only implicitly. | `ontos/core/context.py:229-286`; `ontos/commands/log.py:349-353` | static-inspection | n/a | Add a one-line comment that primary-log concurrency safety rests on O_EXCL, not the advisory lock, to prevent a future refactor from assuming lock coverage. |

### Reachability gaps

None among the rules I could reach offline. All 18 sampled control-plane
validation rules fired end-to-end through `main()` with a citable triggering
input (§8). Two rule classes were verified only by static inspection, not
direct-run, because they need injected fixtures or a live service and are
external-pending by spec design: (a) child-manifest root/scope quarantine
(`normalize_child_manifest`/`normalized_manifest_scope`,
`scripts/…:593-775`), covered by the test's `_run_main_with_child_manifest`
harness; and (b) live-GitHub identity/epic-checklist parity
(`--require-external-parity`, `scripts/…:819-867,1804`), which the spec
correctly classes as an external blocker. Local snapshot/drift metadata
(the offline half of the GitHub gate) was exercised and returns exit `1`.

### Test-blessed divergence audit (Template 03, D-phase)

Both mandated greps over the touched test suites returned **no hits** —
no `does NOT raise` / `keeps working` / `xfail.*spec` / `assertNotRaises`
blessing comments were found. No spec-vs-code gap is being shipped as
verified via a passing test (direct-run: the two `git grep` commands in §8).

## 6. Positive observations

- The malformed-input table is genuinely fail-closed: 18 distinct
  constructions (root/collection type errors, `None`/absolute/escaping/nested
  paths, unhashable IDs, invalid enums, ownership drift, dropped `#146`,
  malformed snapshot metadata, duplicate `affected_issues`) all yield exit
  `1`/`FAILED`, never `2`/`ERROR` — the spec's central §4.1 boundary holds
  under adversarial input.
- Eager required-version parsing is real, not asserted: `>4.7.0, ~bad`
  against running `4.6.0` (earlier clause false) still reports the malformed
  `~bad`, proving `all()` does not short-circuit past a later bad clause.
- One shared no-follow/single-link lock opener backs both the CLI
  (`SessionContext`) and MCP (`workspace_lock`) entry points, with the
  `st_nlink`/reparse checks placed before advisory acquisition — the §4.3
  "both entry points" requirement is met without duplicated logic.
- The reserved exit code `4` is absent from `ExitCode` and emitted nowhere
  in `ontos/` (direct-run grep, §8).
- Migration/reference docs track the code anchors precisely, discharging the
  §7 documentation-drift gate.

## Verdict

Approve

This is a fresh, non-certifying pre-review. On implementation completeness,
abstraction quality, public error/UX contracts, cross-platform lock design,
recovery behavior, and spec-gate reachability, the frozen Phase C
implementation I1 (`05b090d`) faithfully satisfies spec v1.5's Phase C
construction gates, and every gate reachable by local direct-run behaves as
specified. No blocking or should-fix Peer finding is reproducible; two Minor
nits are recorded. Approval here does NOT certify the D.5 lifecycle,
external Windows/TestPyPI/live-GitHub proof (explicitly external-pending by
spec), the full pytest/clean-tree suite (not run per instruction), or any
D.6/merge/tag/publication/release claim.

## 8. Notes

Attestation: `git branch --show-current` → `codex/audit-rebaseline-remediation-lifecycle`;
`git rev-parse HEAD` → `7467a73996ee7a3a7816c9e927f776d8ad3bff55`.

Key reproductions (all preserve repo state; temp registries written to
`/tmp`, never the tree):

- Malformed control-plane table — a Python harness imported
  `scripts/validate-audit-remediation-registry.py`, monkeypatched
  `REGISTRY_PATH` to a `/tmp` copy of the real registry mutated per case, and
  called `main()` under captured argv/stderr. Cases A–I and E1–E6, G1–G4 all
  returned `1` (root=list, findings=dict, row=None, bad enum, `None`/abs/
  escaping/nested path, unhashable id, dropped `#146`, lease row=str,
  integration=list, snapshot=str, non-int count, external_drift=str,
  duplicate `affected_issues`). Case E's initial "PASS" was a harness error
  (I injected a nonexistent `evidence` key; the schema field is
  `verification_evidence`), corrected in E1.
- Required-version diagnostics — `.venv/bin/python` →
  `ontos.core.config.required_version_incompatibility(req, running)` for
  `>=foo`, `>4.7.0, ~bad`@4.6.0, `>=4.7.0, badclause`, `>=4.7.0,`,
  `<4.7.x`, `>=5.0.0`. Confirmed singular clause literal, clause
  identification, eager parse, and the exact
  `#audit-remediation-compatibility-contracts` anchor.
- `git grep -nE "exit_code\s*=\s*4|return 4"` over `ontos/` → no emission of
  reserved code `4`.
- Template 03 D-phase blessing-test greps over `**/test_*.py` /
  `**/*.spec.*` → no hits.

Not run (out of scope by instruction / external by spec design): full
`pytest`, post-suite clean-tree check, real Windows lock/import/CLI smoke,
TestPyPI tag-run download, and live-GitHub `--require-external-parity`.
These remain explicit pending/external states, not certified.

## Final report — project-ontos-audit-rebaseline-remediation / D.1 / peer / claude
- Status: completed
- Artifacts written: docs/reviews/project-ontos-audit-rebaseline-remediation/D.1-claude-peer.md
- Smoke checks: registry validator malformed-table = pass (evidence: direct-run); required-version diagnostics = pass (evidence: direct-run); reserved-exit-4 grep = pass (evidence: direct-run); blessing-test greps = pass/no-hits (evidence: direct-run); full pytest = not-run (evidence: not-run)
- Cardinality checks: single artifact written to declared path = pass (evidence: direct-run)
- Commit: not committed by worker (orchestrator commits review artifacts per Template 01)
- Notes: Verdict Approve — non-certifying pre-review; 0 blocking, 0 should-fix, 2 minor. External Windows/TestPyPI/live-GitHub and full-suite/clean-tree remain pending by design.
