---
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: peer
family: glm
evidence_labels_used:
  - direct-run
  - static-inspection
status: completed
---

# Peer Review — project-ontos-audit-rebaseline-remediation / B.1 / glm

## 1. Completeness check

All mandatory spec sections are present: Overview (§1), Scope (§2), Dependencies
(§3), Technical Design (§4), Open Questions (§5), Test Strategy (§6), Migration
(§7), Risk Assessment (§8), Exclusion List (§9), Diagrams (§10), Contract/
Invariant-to-Evidence Matrix (§11), Helper-Divergence Disclosure (§12), and
Self-Review (§13). No TBD or placeholder text remains (spec §13 bullet 2;
verified by static-inspection).

The spec covers every CREATE/MODIFY/DELETE target listed in §4 with specific
file paths. Each CPI technical section (§4.1–§4.5) names the files to modify
and the behavior to implement. The Open Questions table (§5) has all four rows
resolved with recommendations. The Risk Assessment (§8) enumerates six credible
risks with severity levels and observable signals.

The frozen implementation at `b6f89d7` contains every CREATE target the spec
names: `scripts/validate-audit-remediation-registry.py` (728 lines),
`scripts/check_release_artifact.py` (144 lines), `ontos/core/locking.py` (81
lines), `ontos/command_registry.py` (123 lines), the 100-row registry at
`manifests/project-ontos-audit-remediation-registry.yaml`, and the revalidation
report at `docs/reviews/2026-07-10-codex-audit-revalidation.md` (direct-run:
`git show b6f89d7` on each path; `python3` registry parse confirms 91 original +
9 R2 findings).

The 188-file diff between `bf91b42` and `b6f89d7` matches the spec's §1 claim
("I0 changes 188 files") exactly (direct-run: `git diff --stat bf91b42 b6f89d7`).

The B.1 incorporation note (§1) converts two Claude adversarial findings (X-M1,
X-M2) into explicit Phase C requirements with current-defect line citations.
Neither finding is claimed as resolved at I0 — both are correctly tagged as
Phase C gates.

## 2. Diagram-prose cross-reference

### Architecture / Component Diagram (§10.1)

| Diagram component | In prose? | Prose component | In diagrams? |
|-------------------|-----------|-----------------|--------------|
| Audit Registry (A) | Yes — §4.1 | Audit registry in §4.1 | Yes — A | Yes |
| Validator / Control Plane (V) | Yes — §4.1 | Validator in §4.1 | Yes — V | Yes |
| O4 Ledger + O5 Leases (L) | Yes — §4.1 | O4 ledger / O5 lease graph §4.1 | Yes — L | Yes |
| Canonical Loader + Serializer (S) | Yes — §4.2 | serialize_frontmatter §4.2 | Yes — S | Yes |
| Safe Writer + CLI Logging (W) | Yes — §4.3 | SessionContext.commit / log §4.3 | Yes — W | Yes |
| CLI / MCP Contracts (C) | Yes — §4.4 | CLI / MCP contracts §4.4 | Yes — C | Yes |
| Activation + Doctor (X) | Yes — §4.4 | required_version / doctor §4.4 | Yes — X | Yes |
| Cross-platform Locking (K) | Yes — §4.4 | locking.py §4.4 | Yes — K | Yes |
| Release Pipeline (P) | Yes — §4.5 | publish.yml §4.5 | Yes — P | Yes |
| Tests + Lifecycle Evidence (T) | Yes — §6 | Test strategy §6 | Yes — T | Yes |
| Generated Context Map + AGENTS (M) | Yes — §4.5 | Context map generation §4.5 | Yes — M | Yes |
| EXTERNAL: GitHub (G) | Yes — §3 | GitHub dependency §3 | Yes — G (dashed) | Yes |
| EXTERNAL: Windows Runner (R) | Yes — §3 | Windows dependency §3 | Yes — R (dashed) | Yes |
| EXTERNAL: TestPyPI / PyPI (Y) | Yes — §3 | TestPyPI/PyPI dependency §3 | Yes — Y (dashed) | Yes |

No blocking mismatches. Every diagram component appears in prose and every
major prose component appears in the diagram. External boundaries are correctly
dashed and labeled (`parity`, `platform proof`, `artifact proof`).

One unlabeled-edge clarity gap: the diagram shows `A --> S` (Registry →
Serializer) and `A --> C` (Registry → CLI/MCP). The prose does not explain
what data or constraint flows along these edges; the registry informs the
validator and audit state, but the serializer/CLI changes are independent
MODIFY targets. A brief label or prose note would clarify intent (see Issues
§5 Minor).

### Lifecycle State Machine (§10.2)

All lifecycle states match the phase descriptions in §2 scope and §6 test
strategy. The D.4 feedback loops (D.3→D.4 on blocking, D.5→D.4 on FAIL, loose
falsification→D.4 on catch) match the test strategy's callback of "a failed
check blocks D.5 PASS or returns the lifecycle to D.4" (§6). The `D6_Pending`
terminal state with "stop boundary; no release claim" matches §2 out-of-scope
("D.6 final approval ... declaring a release ready"). No mismatches.

## 3. Quality assessment

The spec is well-designed and implementable without follow-up questions. The
technical design sections (§4.1–§4.5) each name the CREATE/MODIFY/DELETE
targets, the public contract, the direct-read citation anchors, and the
Phase C requirements derived from B.1 adversarial findings. A mid-level
engineer can trace from the spec's §11 evidence matrix to the implementation
test files and reproduce the contract claims.

The control-plane architecture is clear: the registry is the sole status
authority, the validator enforces cardinality and parity, and the ledger and
lease graph are renderings — not independent sources. This separation prevents
the "false-green lifecycle/control plane" risk enumerated in §8. The
validator's enforcement of exact original cardinality (91: P0=1, P1=27, P2=63)
and R2 count (9 named IDs) is verifiable by direct run (confirmed:
`python3 -c 'import yaml...'` on the registry returns matching counts).

The concurrency envelope is honestly scoped: §1 states "single-operator-
crash-safe" with serialization of cooperative writers and best-effort rollback,
explicitly disclaiming distributed transaction guarantees. This precision
prevents implementers from over-engineering locking beyond the stated envelope.

The Helper-Divergence Disclosure (§12) is a strong design-quality signal: it
pre-discloses four existing helpers with their shapes, integration needs, and
dispositions (extend internals, extend guard, diverge with substrate). This
gives Phase C implementers clear modification boundaries and prevents ad-hoc
divergence.

The spec's self-review (§13) correctly self-checks mandatory sections, diagram
consistency, absence of placeholders, direct-read anchor accuracy, scope
preservation, risk retention, and B.1 incorporation. The evidence labels on
each self-review bullet (static-inspection or direct-run) are honest.

## 4. UX review

The spec documents user-visible contract changes accurately. §7 Migration/
Compatibility enumerates the breaking changes (invalid/non-string IDs fail, log
collisions fail, MCP type counts become exhaustive, read-only MCP performs no
writes, activation version incompatibility, CLI JSON/exit taxonomy). The
migration documentation obligation is explicit: Phase C must add normative
copy to `docs/reference/Migration_v3_to_v4.md` and reference copy to
`docs/reference/Ontos_Manual.md` covering `required_version` ranges, activation
exit/code/message contracts, string-only ID rules with quoting guidance, and
the public exit taxonomy. Documentation drift from code anchors blocks D.1.

The CLI JSON envelope contract (§4.4) is precise: nine exact top-level keys
(`schema_version`, `command`, `status`, `exit_code`, `message`, `result`,
`data`, `warnings`, `error`) with `result` separating domain status, result
kind, exit category, and diagnostic basis/count completeness. Verified against
`b6f89d7` implementation at `ontos/ui/json_output.py:331-345` — all nine keys
present in the `emit_json` dict (direct-run: `git show b6f89d7:ontos/ui/
json_output.py`). The exit code taxonomy (0/1/2/3/5/130) matches the
`ExitCode` IntEnum at lines 28-35.

Error-message quality is good: the ID contract gives exact error strings
("Document id must be a string", "Document id must not be empty"), verified at
`ontos/core/schema.py:83-97`. The activation failure messages begin with
"Incompatible Ontos version" and "Invalid [ontos].required_version" as claimed,
verified at `ontos/core/config.py:259-262` and `ontos/commands/activate.py:93-95`.

## 5. Issues found

### Blocking (Critical)

None.

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-1 | Evidence matrix (§11) entry for "Runtime version compatibility" cites only `ontos/core/config.py:223-266` but §4.4's Phase C note for duplicate invalid-clause copy cites `ontos/core/config.py:239-266,279-345`. The matrix omits the second range (279-345), creating ambiguity about which code the Phase C deduplication gate covers. A D.5 verifier using only the matrix would miss the `_version_clause_matches` functions that produce the duplicated clause text. | spec §11 vs §4.4 | static-inspection | Compare §11 "Runtime version compatibility" row's implementation anchor column against §4.4 Phase C note | Add `,279-345` to the §11 row's implementation anchor to match §4.4 |
| P-2 | The evidence matrix (§11) has no rows for the three B.1 regression tests listed in §6 (symlinked `logs_dir` rejection for X-M1, malformed registry row for X-M2, invalid `required_version` deduplication). While §6 names these test anchors, the matrix — the primary D.5 traceability artifact — is silent. Without matrix rows, a D.5 verifier must cross-reference §6 to find the Phase C gates. | spec §11 (missing rows) vs §6 "B.1 regressions" bullet | static-inspection | Grep §11 matrix for "X-M1", "X-M2", "symlink", "logs_dir", "malformed" — no matches | Add three matrix rows: X-M1 log symlink rejection, X-M2 registry missing-id handling, invalid `required_version` deduplication — each with implementation anchor, test anchor, and evidence label |
| P-3 | Doctor line citation inconsistency: §4.4 cites `ontos/commands/doctor.py:593-675` but §11 cites `593-685` for the same "Runtime version compatibility" contract. The `check_cli_availability` function at `b6f89d7` starts at ~line 595 and the version comparison code extends through ~line 675; lines 676-685 begin the `TestDoctorCommand` class. The §11 end-boundary of 685 over-extends into test-class territory. | spec §4.4 vs §11 | direct-run | `git show b6f89d7:ontos/commands/doctor.py` lines 593-700: function body ends ~675, class def at ~677 | Reconcile both citations to `593-675` to match the actual function boundary |

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-4 | The architecture diagram shows unlabeled edges `A --> S` (Audit Registry → Canonical Loader + Serializer) and `A --> C` (Registry → CLI/MCP Contracts). The prose does not explain what data or constraint flows along these edges; the registry's role is to feed the validator, while the serializer/CLI are independent MODIFY targets. A reader may infer a direct data dependency that does not exist in the implementation. | spec §10.1 diagram vs §4.2/§4.4 prose | static-inspection | Inspect mermaid block edges: `A --> S`, `A --> C` have no labels; search §4.2/§4.4 for registry→serializer or registry→CLI data flow | Add brief edge labels (e.g., `contracts`, `ID rules`) or a prose note clarifying the relationship |
| P-5 | §4.4 lists exit codes 0, 1, 2, 3, 5, 130 — skipping 4. The spec does not note that 4 is intentionally reserved/unused. A Phase C implementer or future reader may wonder whether the gap is accidental. | spec §4.4 | static-inspection | Exit codes listed: clean=0, findings=1, usage=2, warnings=3, (gap), internal=5, interrupted=130 | Add a parenthetical noting exit code 4 is intentionally reserved |
| P-6 | §10.1 diagram component "O4 Ledger + O5 Leases" uses labels O4/O5 but §4.1 and §3 do not define what O4 and O5 refer to. These are presumably release-line tracker and lifecycle-state references from the dependency `project_ontos_audit_remediation_release_line_tracker`, but a first-time reader would need to infer this. | spec §10.1 vs §4.1 | static-inspection | Grep §4.1 and §3 for "O4" or "O5" — no definition found | Add a one-line definition of O4 (ledger) and O5 (lease graph) at first use in §4.1 |

## 6. Positive observations

1. **Branch-level vs per-issue certification distinction is exemplary.** The
   spec is explicit and unambiguous: §1 states "this deliverable itself is a
   branch-level lifecycle review, not a release"; §5 resolves "Does umbrella
   D.5 certify child issues? No; require each child manifest's own strict
   receipts"; §9 exclusion list prohibits claiming "per-issue strict-P3
   certification, D.6 approval, merge, tag, publication, or release readiness
   from this deliverable." This prevents scope overclaim — the highest-risk
   process failure mode enumerated in §8.

2. **External evidence honesty is strong.** The evidence matrix (§11) marks
   "Windows external pending" and "external pending" for TestPyPI. The
   dependencies table (§3) distinguishes local-verifiable claims from external
   blockers: "local POSIX emulation is not release evidence" and "only a
   tag-run proves service behavior." Section §3's closing rule — "No
   dependency may be converted into a synthetic receipt" — is the correct
   anti-fabrication guardrail.

3. **Direct-read citations are accurate.** I verified the spec's file:line
   claims against `b6f89d7` by direct run: the 100-row registry (91 original +
   9 R2), the JSON envelope's nine keys, the ID pattern regex, the exact
   error message strings, the lock backend selection (fcntl/msvcrt), the MCP
   read-only write-tool omission, the Windows CI matrix (3.9/3.14), the
   single-wheel provenance chain, and the test anchor line ranges — all match
   the frozen implementation.

4. **Helper-Divergence Disclosure (§12) is valuable and unusual.** Pre-
   disclosing where the implementation diverges from existing helper signatures
   — with explicit disposition (extend internals, extend guard, diverge with
   substrate) and rationale — gives Phase C implementers clear modification
   boundaries and prevents ad-hoc divergence that would break the public
   contract.

5. **B.1 incorporation note is precise.** §1 names the two adversarial
   findings (X-M1, X-M2), their current-defect locations (`log.py:115,336-340`
   and `validate-audit-remediation-registry.py:244-285`), and their exact
   Phase C acceptance criteria. I confirmed both defects exist at `b6f89d7`:
   X-M1 — `log.py` resolves `logs_dir` with `.resolve()` (follows symlinks)
   and `_write_log_exclusively` does not reject symlinked components; X-M2 —
   `validate-audit-remediation-registry.py` checks for missing `id` in a loop
   but then accesses `row["id"]` directly at the `original = {...}` dict
   comprehension, which would raise an uncaught `KeyError` before collected
   errors print (direct-run: `git show b6f89d7` on both files).

## Verdict

Approve

The spec is well-designed, complete, clear, accurately cited, and directly
implementable without follow-up questions. The branch-level vs per-issue/release
certification distinction and external Windows/TestPyPI evidence honesty are
exemplary. Direct-run verification against `b6f89d7` confirms the 188-file diff,
the 100-row registry, the JSON envelope keys, the locking backend, the MCP
read-only guard, the CI Windows matrix, and the test anchor line ranges.

The three should-fix findings (P-1 through P-3) are traceability and citation-
consistency improvements in the evidence matrix — not correctness defects, spec
ambiguity, or diagram-prose mismatches. They do not block Phase C implementation
or B.2 code-first review. The minor findings (P-4 through P-6) are clarity polish.
None requires a spec revision round before downstream phases proceed.

## 8. Notes

- Evidence baseline: all direct-run evidence was obtained by running `git show
  b6f89d7`, `git diff --stat bf91b42 b6f89d7`, and `python3` registry parsing in
  the worktree at `project-ontos-audit-rebaseline-remediation` on branch
  `codex/audit-rebaseline-remediation`.
- The spec's version is 1.1 (frontmatter `version: 1.1`) with a B.1
  incorporation note documenting the conversion of X-M1/X-M2 into Phase C
  requirements. This version-1.1 amendment is correctly scoped: it does not
  claim the defects are closed, only that they are explicitly tracked.
- The spec's risk retention is honest: §8 keeps "Silent document corruption"
  at P0 and "Symlink/path escape or partial write" at P1 with mitigations,
  while §1 retains "high" risk classification throughout.
- The frozen implementation at `b6f89d7` was authored by family `codex` (spec
  frontmatter `family: codex`). This GLM peer review is a cross-family lens.
