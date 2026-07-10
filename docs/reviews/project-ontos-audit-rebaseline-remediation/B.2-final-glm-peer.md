---
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.2
role: peer
family: glm
evidence_labels_used: [static-inspection]
status: completed
---

# Peer Review — project-ontos-audit-rebaseline-remediation / B.2 / glm

## 1. Completeness check

Spec v1.5 (`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`) is
structurally complete: all 13 sections (Overview through Self-Review) are
present, no TBD/placeholder remains, and all three open questions carry a
recommendation plus a resolved status (static-inspection:
`project-ontos-audit-rebaseline-remediation-spec.md:159-163`).

The v1.5 incorporation note (spec line 32) and Self-Review bullets
(lines 379-388) cover the seven C-FZ corrections exactly: eager clause
parsing, entry-binding rechecks, root/child-manifest quarantine,
enum-closed lease filtering, exact GitHub identity/checklists,
single-link lockfiles, and canonical owner/path parity. Each is
expressed as a Phase C requirement with a deterministic regression
target, never as a claim that I0 already satisfies it.

The four advisory board findings folded into v1.5 (archive-marker
visibility, migration anchor precision, frozen-I0 anchor labelling,
O4/O5 producer-edge clarity) are individually traceable to spec
prose: archive warning/exit-3 JSON semantics at §4.3 lines 101;
exact Migration guidance anchor at §4.4 line 134 and §7 line 224;
frozen-I0 direct-read annotations throughout §§4.1-4.4; and the
O4/O5 producer edge at §4.1 line 75. No section is truncated or
missing content.

## 2. Diagram-prose cross-reference

Architecture diagram §10.1 and lifecycle diagram §10.2 were checked
component-by-component against §4 prose.

### Architecture (§10.1)

| Diagram component | In prose? | Prose component | In diagrams? |
|-------------------|-----------|-----------------|--------------|
| Audit Registry (A) | Yes — §4.1 CREATE | Advisory-lock backend (§4.4) | Yes — K |
| Validator / Control Plane (V) | Yes — §4.1 line 73 | No-follow opener (§4.3/4.4) | Yes — K→W, K→C (Phase C contract) |
| O4 Ledger + O5 Leases (L) | Yes — §4.1 line 75 | required_version (§4.4) | Yes — X→C |
| Canonical Loader + Serializer (S) | Yes — §4.2 | Archive marker (§4.3) | Yes — W→T |
| Safe Writer + CLI Logging (W) | Yes — §4.3 | Exit code / JSON taxonomy (§4.4) | Yes — C→T |
| CLI / MCP Contracts (C) | Yes — §4.4 | Release Pipeline (§4.5) | Yes — P→T |
| Activation + Doctor (X) | Yes — §4.4 line 116 | Generated Context Map (§4.5) | Yes — T→M |
| Cross-platform Locking (K) | Yes — §4.4 line 118 | EXTERNAL: GitHub | Yes — G (dashed) |
| Release Pipeline (P) | Yes — §4.5 | EXTERNAL: Windows Runner | Yes — R (dashed) |
| Tests + Lifecycle Evidence (T) | Yes — §6 | EXTERNAL: TestPyPI/PyPI | Yes — Y (dashed) |
| Generated Context Map + AGENTS (M) | Yes — §4.5 line 151 | | |

All eleven internal components and three external boundaries appear in
both diagram and prose. The external nodes use the dashed `external`
class, matching §3 Dependencies (Windows, TestPyPI, GitHub) and the
nonclaim boundaries in §9. No orphaned diagram edge or unillustrated
prose component was found.

### Lifecycle (§10.2)

The state machine includes the code-first `Phase_C_Reconciliation`
state between `B2_CodeFirst_Review` and `D1_Implementation_Snapshot`,
satisfying the v1.4 incorporation note (spec line 378). All retry
edges are present: `D3_Verdict → D4_Fix` (blocking finding),
`D5_Verification → D4_Fix` (FAIL/reproducible defect),
`D4_Fix → D2_PostImpl_Review` (rerun affected reviews), and the
`Loose_Falsification` branch (catch → D4, no catch → D6_Pending).
The terminal `D6_Pending → [*]` carries the annotation "stop
boundary; no release claim," matching §2 scope and §9 exclusion list.

## 3. Quality assessment

The spec's highest-value quality trait is its relentless I0-vs-Phase-C
honesty. Every frozen-I0 anchor is labelled with the short SHA and an
explicit "pre-upgrade shape" or "frozen-I0 defect" qualifier; every
Phase C correction is framed as a construction-level requirement with a
deterministic regression target, not a retroactive claim. The v1.5
incorporation note (line 32) and the Self-Review bullets (lines
379-388) each close with the same invariant formula: "None is rounded
up from the prior green suite or represented as D.5/release proof."
This is the correct discipline for a code-first lifecycle where I0
is a real integration commit that the review must assess without
confusing existing code with certified completion.

Implementability is strong. The v1.5 corrections give a Phase C
author concrete acceptance criteria: the eager-clause requirement
names both earlier-false/later-invalid orderings (§4.4 line 134,
§6 lines 196-200); the entry-binding recheck names staged, backup,
move/delete, and final bindings (§4.3 line 95); the quarantine
boundary enumerates every consumed collection including
`shared_tree_integration` and `external_drift` (§4.1 line 77); the
multi-link lock check names POSIX `st_nlink` and Windows
`nNumberOfLinks` (§4.3 line 103); the GitHub identity/checklist
requirement names `number`, title, typed state/milestone/labels/body,
and exact checklist-set equality with a phantom-rows target
(§4.1 line 83); and the archive warning/exit-3 contract gives exact
human message prefix, JSON `warnings[]` placement, `result.status`
value, exit code, and `data` retention (§4.3 line 101). A mid-level
engineer can build Phase C from these without follow-up questions.

The test strategy (§6) is detailed and anchored: serializer fixtures,
writer swap regressions, registry table-driven validation with
`main()` exit `1`/`FAILED` assertions, required-version clause
regressions, log-collision hint verification, map double-generation,
and release workflow assertions all carry concrete test file/line
anchors. The §11 invariant-to-evidence matrix uses honest labels
(`direct-run` for I0-proven invariants; `Phase C direct-run required`
for C-FZ gates), so the evidence baseline does not overclaim. One
gap in the test strategy is noted as P-2 below.

The honest state/external/nonrelease boundaries are preserved: the
100-row registry with 41 `confirmed_open` and 7 partials is stated as
unchanged truth (§1 line 22); Windows/TestPyPI/GitHub are
external-blocker pending (§3, §11); child-issue per-issue certification,
D.6, merge, tag, publication, and release are explicitly nonclaimed
(§2, §9, §11 matrix rows). The `shared_tree_integration` section of
the registry at I0 correctly records
`status: unproven_rebaseline_integration, release_blocking: true`
(static-inspection: `b6f89d7:manifests/project-ontos-audit-remediation-registry.yaml`
row at the `shared_tree_integration` key), matching spec §4.1 line 77.

## 4. UX review

The user-facing surface is the CLI/MCP contract: schema-v4 JSON
envelope (§4.4), exact exit-code taxonomy (`0`/`1`/`2`/`3`/`5`/`130`,
code `4` reserved), `E_LOG_EXISTS` collision message with actionable
recovery hint (§4.3 line 97), and the Migration/Ontos_Manual copy
(§7). The v1.5 corrections improve UX in three ways: (1) the archive-
marker warning prefix `Session log created, but archive marker was not
updated:` is actionable and present in both human and JSON output;
(2) the required-version clause diagnostic identifies which clause
failed rather than echoing the whole range; (3) the log-collision
recovery hint offers concrete choices (different title/slug or
intentional move/remove). The migration copy requirement to warn
adopters that exit `3` is warnings-only (not a hard error) is a
correct backward-compatibility callout (§7 line 224). No error
message lacks an actionable path.

## 5. Issues found

### Blocking (Critical)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| — | No blocking findings. | — | — | — | — |

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-1 | §3 Dependencies says "Issues #146–#158 must match registry state" while §4.1 says "the normalized program issue set must equal exactly #146 through #157." The apparent range discrepancy (#158 vs #157) is not resolved by a clarifying note that #158 is the epic, parity-checked separately, not a program row. An implementer reading only §3 may expect 13 program rows rather than 12. | spec §3 line 61 vs §4.1 line 81 | static-inspection | Read §3 table row (GitHub dependency) alongside §4.1 program-membership sentence. At I0 the registry `source_issues` list is `[146..157]` and `epic_issue: 158` is separate (static-inspection: `b6f89d7:manifests/project-ontos-audit-remediation-registry.yaml` `github_snapshot` block). | Add a one-clause note to §3 or §4.1 clarifying that #158 is the epic issue, not a program row; program set is #146–#157 exactly. | |
| P-2 | The test strategy (§6) covers invalid status enums (rejected by validation) but does not explicitly name a regression for status-count parity drift — the invariant that the 41/40/7/2/1 distribution of valid statuses matches expected. The validator at I0 enforces this via `expected_status_counts` comparison (static-inspection: `b6f89d7:scripts/validate-audit-remediation-registry.py:296-308`), but the spec's table-driven testing list (§6 lines 189-195) names field omission, type errors, enum drift, path/owner drift, and `main()` exit behaviour without naming "status partition of known counts." A Phase C implementer could add enum validation without adding a test that flips a `confirmed_open` finding to `implemented_uncommitted` and asserts the count-distribution parity fails. | spec §6 lines 196-195, §11 "Registry is sole status authority" row | static-inspection | Inspect I0 validator `expected_status_counts` block at lines 296-308; cross-reference §6 test-strategy bullet list. The count-distribution invariant is enforced at I0 but not named as a Phase C regression target. | Add an explicit §6 bullet: "status-distribution parity regression asserting the 41/40/7/2/1 partition fails on count drift." | |

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-3 | §4.4 says the JSON envelope `result` separates "exit category" but does not enumerate the canonical exit-category strings mapping to each exit code (0/1/2/3/5/130). An implementer building the result object must infer the category labels from the I0 `json_output.py` code. | spec §4.4 line 132 | static-inspection | Read §4.4 JSON-envelope sentence; compare to I0 `ontos/ui/json_output.py:16-49,202-345` for the category enum. | Consider a one-line table mapping exit code → result.exit_category label in §4.4 or §7. |

## 6. Positive observations

- **I0 anchor accuracy.** Every frozen-I0 direct-read citation was
  verified against `git show b6f89d7:<path>`. The lazy `all()` clause
  parser (C-FZ-1) is at `b6f89d7:ontos/core/config.py:266`; the
  `except Exception → exit 2/ERROR` path (C-FZ-3) is at
  `b6f89d7:scripts/validate-audit-remediation-registry.py:707-709`;
  the bare `lease_state == "active"` filter (C-FZ-4) is at
  `b6f89d7:scripts/validate-audit-remediation-registry.py:525`;
  the silent archive-marker `except OSError: pass` (v1.5 archive
  correction) is at `b6f89d7:ontos/commands/log.py:345-352`; the
  MCP bare `open("a+")` with no `st_nlink` check (C-FZ-6) is at
  `b6f89d7:ontos/mcp/locking.py:21-27`; the advisory backend writing
  its `\0` sentinel without nlink precheck is at
  `b6f89d7:ontos/core/locking.py:13-81`; the missing
  `live.get("number") == issue` identity check (C-FZ-5) is absent from
  `b6f89d7:scripts/validate-audit-remediation-registry.py:163` and
  the parity loop at lines 640-697; and the `#audit-remediation-
  compatibility-contracts` anchor heading is absent from
  `b6f89d7:docs/reference/Migration_v3_to_v4.md`. All anchors are
  accurate: the spec describes real I0 code, not aspirational code.

- **Honest Phase C framing.** Every v1.5 correction is stated as
  "Phase C must" with a regression target, and every incorporation
  note closes with the immutable SHA / external-proof / child-
  lifecycle / D.6 / merge / tag / publication / release nonclaim
  formula. The spec does not round up the C-FZ-focused evidence
  (`315 passed` writer/lock/config matrix, `13 passed` archive
  matrix) as full-suite proof — it explicitly states a fresh
  clean-snapshot suite is mandatory before C-close.

- **Nonclaim integrity.** The 41 open / 7 partial states, the
  `shared_tree_integration: unproven_rebaseline_integration` release
  blocker, the external Windows/TestPyPI/GitHub pending status, and
  the D.6/merge/tag/publication/release boundary are stated
  consistently across §§1-3, 8-9, and 11.

- **Diagram-prose alignment.** All architecture components and
  external boundaries appear in both diagram and prose; the
  lifecycle diagram's code-first reconciliation path and loose-
  falsification branch are internally consistent with §§2 and 6.

## Verdict

Approve

Spec v1.5 is complete, accurately anchored to frozen I0 `b6f89d7`,
diagram-prose consistent, implementable, and honestly scoped with
preserved state/external/nonrelease boundaries. All seven v1.5
corrections (eager clause parsing, entry-binding rechecks, control-
plane quarantine, enum-closed lease filtering, exact GitHub
identity/checklists, multi-link lockfile refusal, canonical owner/
path parity) plus the four advisory-board closures (archive warning/
exit-3, exact guidance anchor, frozen-I0 anchor labelling, O4/O5
producer edge) are grounded in verified I0 gaps and framed as
Phase C requirements with deterministic regressions — never as
already-satisfied claims. The two should-fix findings (P-1 issue-
range clarification, P-2 status-count parity regression target)
and one minor (P-3 exit-category label mapping) are clarity and
test-strategy-completeness improvements that do not block Phase C
implementation.

## Notes

- File-existence attestation (Template 03 v1.3+):
  `git branch --show-current` → `codex/audit-rebaseline-remediation-lifecycle`;
  `git rev-parse --short HEAD` → `d12f851`;
  `git ls-files docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`
  → tracked.
- I0 inspected exclusively via bounded `git show b6f89d7:<path>` /
  `git show b6f89d7:<path> | grep/sed`. No worktree was created, no
  full suite was run, no agents were invoked, no implementation was
  edited, no commits were made.
- `C-phase-falsification-findings.md` was read for reproduction
  statements only (C-FZ-1 through C-FZ-7 pre-fix observables); no
  reviewer verdict, result, or receipt from that file was used as
  proof. All I0 code confirmations in this review derive from
  independent `static-inspection` of the frozen commit.
- Evidence label: `static-inspection` only. No `direct-run` or
  `orchestrator-preflight` claims are made; blocking-findings table
  is empty by construction (peer lens, no critical findings).
