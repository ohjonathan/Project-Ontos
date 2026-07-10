---
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.2
role: peer
family: glm
status: completed
---

# Peer Review — project-ontos-audit-rebaseline-remediation / B.2 / glm

## 1. Completeness check

All mandatory sections are present (§1 Overview through §13 Self-Review); no TBD or
placeholder remains. v1.1's B.1 incorporation note (§1) plus §4.1/§4.3 convert adversarial
findings X-M1 and X-M2 into explicit Phase C gates with current-defect citations, and
neither is claimed closed at I0 — the correct "tracked, not discharged" posture.

Direct-run verification against frozen I0 `b6f89d7` (branch
`codex/audit-rebaseline-remediation-lifecycle`, HEAD `5367842`):

- `git diff --stat bf91b42 b6f89d7` → 188 files changed → matches §1 "I0 changes 188 files."
- registry parse (`manifests/project-ontos-audit-remediation-registry.yaml`): 100 rows,
  91 original + 9 R2; original `confirmed_open`=41 and
  `partial_implementation_uncommitted_verification_pending`=7 → matches §1 "41 confirmed_open
  and seven partially implemented."
- JSON envelope (`b6f89d7:ontos/ui/json_output.py`, `emit_json` dict): exactly the nine
  top-level keys → matches §4.4.
- ID contract (`b6f89d7:ontos/core/schema.py:83-97`): "Document id must be a string …",
  "Document id must not be empty", pattern message → match §4.2.
- X-M1 (`b6f89d7:ontos/commands/log.py:115` resolves `logs_dir` with `.resolve()`, following
  symlinks; `_write_log_exclusively` at 334-340 rejects no symlinked component) → §4.3 accurate.
- X-M2 (`b6f89d7:scripts/validate-audit-remediation-registry.py:244` accesses `row["id"]`
  directly before the missing-fields collection) → §4.1 accurate.

Test strategy (§6) is complete for a spec of this risk class: serializer/writer fixtures,
hermetic log/map tests with a post-suite clean-tree check, activation/doctor/lock anchors,
the three B.1 regressions, wheel provenance, and registry parity. Required commands and the
clean start/end snapshot comparison are explicit; a failed check blocks D.5 PASS or returns
to D.4 (§6).

Carry-forward: the v1.1 amendment folded in the adversarial X-M1/X-M2 but did not address the
B.1 peer board's three should-fix or three minor items; they persist (see §5).

## 2. Diagram-prose cross-reference

### Architecture / Component Diagram (§10.1)

| Diagram component | In prose? | Prose component | In diagrams? |
|-------------------|-----------|-----------------|--------------|
| Audit Registry (A) | Yes — §4.1 | Audit registry §4.1 | Yes (A) |
| Validator / Control Plane (V) | Yes — §4.1 | Validator §4.1 | Yes (V) |
| O4 Ledger + O5 Leases (L) | Yes — §4.1 | O4 ledger / O5 lease §4.1 | Yes (L) |
| Canonical Loader + Serializer (S) | Yes — §4.2 | serialize_frontmatter §4.2 | Yes (S) |
| Safe Writer + CLI Logging (W) | Yes — §4.3 | SessionContext.commit / log §4.3 | Yes (W) |
| CLI / MCP Contracts (C) | Yes — §4.4 | CLI / MCP §4.4 | Yes (C) |
| Activation + Doctor (X) | Yes — §4.4 | required_version / doctor §4.4 | Yes (X) |
| Cross-platform Locking (K) | Yes — §4.4 | locking.py §4.4 | Yes (K) |
| Release Pipeline (P) | Yes — §4.5 | publish.yml §4.5 | Yes (P) |
| Tests + Lifecycle Evidence (T) | Yes — §6 | Test strategy §6 | Yes (T) |
| Generated Context Map + AGENTS (M) | Yes — §4.5 | Context map §4.5 | Yes (M) |
| EXTERNAL GitHub/Windows/TestPyPI (G/R/Y) | Yes — §3 | Dependencies §3 | Yes (dashed) |

No prose component is missing from the diagram and no diagram component lacks prose; external
boundaries are correctly dashed and labeled. Carry-forward minors P-4 (unlabeled `A --> S`,
`A --> C`) and P-6 (O4/O5 undefined at first use) persist.

### Lifecycle State Machine (§10.2)

States and D.4 feedback loops (D.3→D.4 on blocking; D.5→D.4 on FAIL; loose-falsification→D.4 on
catch) match §2 scope and §6 callback. The `D6_Pending` terminal "stop boundary; no release
claim" matches §2 out-of-scope. No mismatches.

## 3. Quality assessment

The spec is well-designed and implementable without follow-up questions. Each technical
section (§4.1–§4.5) names CREATE/MODIFY/DELETE targets, the public contract, direct-read
citations, and the Phase C requirements derived from B.1; a mid-level engineer can trace
§11's evidence matrix to the implementation test files and reproduce the contract claims.

The control-plane separation is clear and correctly risk-aligned: the registry is the sole
status authority, the validator enforces cardinality/severity/parity, and ledger + lease graph
are renderings — directly mitigating the §8 "false-green lifecycle/control plane" risk. The
concurrency envelope is honestly scoped ("single-operator-crash-safe"; serialization +
best-effort rollback; no distributed-transaction claim), preventing over-engineering of
locking. The Helper-Divergence Disclosure (§12) gives Phase C explicit modification
boundaries, and §13 self-review evidence labels are honest.

Second-board observation (B.2): implementability is unchanged from B.1 — the substantive
Phase C gates (X-M1/X-M2) are correctly incorporated and direct-run confirmed at `b6f89d7`.
The persisting findings are matrix-traceability and citation-consistency polish, not
ambiguity or contract gaps, so they do not impede Phase C.

## 4. UX review

§7 Migration enumerates the breaking public changes and makes the documentation obligation
explicit (normative copy to `docs/reference/Migration_v3_to_v4.md`, reference copy to
`docs/reference/Ontos_Manual.md`), with documentation drift from the §§4.2/4.4 anchors
blocking D.1. The CLI JSON envelope (§4.4) — nine exact top-level keys with `result`
separating status/kind/exit-category/diagnostics — is precise and matches the implementation.
Error-message quality is good (exact ID strings; activation "Incompatible Ontos version" /
"Invalid [ontos].required_version" prefixes), verified against `b6f89d7`.

## 5. Issues found

### Blocking (Critical)

None.

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-1 | B.1 carry-forward, unfixed in v1.1: §11 "Runtime version compatibility" cites `ontos/core/config.py:223-266` only, but §4.4's Phase C dedup note cites `239-266,279-345`. The omitted `279-345` range holds `_version_clause_matches` and the wildcard parsers that raise the duplicated "invalid … clause" `ConfigError` text Phase C must dedup — so the primary D.5 traceability artifact omits the anchor the gate names. | spec §11 vs §4.4 | direct-run (`b6f89d7:ontos/core/config.py`, `_version_clause_matches` at 279) | compare §11 row anchor vs §4.4 Phase C note | append `,279-345` to the §11 implementation anchor |
| P-2 | B.1 carry-forward, unfixed: §11 matrix has no rows for the three B.1 regression tests §6 names (X-M1 symlinked `logs_dir`, X-M2 malformed registry row, invalid `required_version` dedup). A D.5 verifier must cross-reference §6 to find the Phase C gates. | spec §11 vs §6 | static-inspection | grep §11 for X-M1/X-M2/symlink/malformed → none | add three matrix rows (impl + test + evidence) |
| P-3 | B.1 carry-forward, unfixed: doctor.py version-comparison anchor differs — §4.4 cites `593-675`, §11 cites `593-685`. Both ranges lie inside `check_cli_availability` (which runs to ~692); the B.1 note that 676-685 began a test class is incorrect — those lines are the warning `CheckResult` branch, not `TestDoctorCommand`. | spec §4.4 vs §11 | direct-run (`b6f89d7:ontos/commands/doctor.py:593-692`) | reconcile both citations to one consistent in-function range | reconcile to a single range covering the version-comparison logic |

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-4 | Unlabeled edges `A --> S` and `A --> C` in §10.1; prose does not state what flows registry→serializer/CLI. | spec §10.1 vs §4.2/§4.4 | static-inspection | inspect mermaid edges | add edge labels or a prose note |
| P-5 | §4.4 lists exit codes 0,1,2,3,5,130 with no note that 4 is intentionally reserved (b6f89d7 `ExitCode` IntEnum confirms 4 absent). | spec §4.4 | static-inspection | — | parenthetical noting 4 is reserved |
| P-6 | "O4 Ledger + O5 Leases" (§10.1) uses O4/O5 but §4.1/§3 never define them. | spec §10.1 vs §4.1 | static-inspection | grep §4.1/§3 for O4/O5 → none | one-line definition at first use |

## 6. Positive observations

1. B.1 X-M1/X-M2 incorporation is accurate and disciplined: both defects confirmed at `b6f89d7`
   by direct-run, both converted to explicit Phase C acceptance criteria, and neither falsely
   claimed closed at I0.
2. Branch-level vs per-issue certification distinction remains exemplary (§1, §5, §9),
   directly preventing the §8 scope-overclaim process failure.
3. External-evidence honesty is strong (§3 "no dependency may be converted into a synthetic
   receipt"; §11 marks Windows/TestPyPI "external pending"), and direct-read anchors validate
   against `b6f89d7` (188-file diff, 100-row registry, JSON envelope, ID pattern, lock backend).
4. Helper-Divergence Disclosure (§12) pre-discloses modification boundaries, reducing ad-hoc
   Phase C divergence risk.

## Verdict

Approve

The corrected spec v1.1 is well-designed, complete, accurately cited, and directly
implementable without follow-up questions. The substantive Phase C gates (X-M1
symlinked-`logs_dir` rejection; X-M2 registry missing-id handling) are correctly incorporated
and direct-run verified at `b6f89d7`; the 188-file diff, registry counts, JSON envelope, ID
contract, and lock/error anchors all match the frozen implementation.

The three should-fix findings are B.1 carry-forward traceability and citation-consistency gaps
(evidence-matrix omissions and a doctor.py anchor split) — not correctness defects, spec
ambiguity, or diagram/prose mismatches — and do not block Phase C implementation or B.2
code-first review. I second B.1's calibration; recommend closing P-1–P-3 before D.5 so the §11
matrix is the single traceability source. The minors are clarity polish.

## 8. Notes

- Evidence: direct-run via `git show b6f89d7` on cited files, `git diff --stat bf91b42 b6f89d7`,
  and `python3` registry parse in the worktree on branch
  `codex/audit-rebaseline-remediation-lifecycle` (HEAD `5367842`); static-inspection for
  matrix/section cross-references.
- Short SHAs only, per dispatch directive; spec §1 carries the full SHA pair (base `bf91b42`,
  I0 `b6f89d7`).
- I0 was authored by family `codex` (spec frontmatter `family: codex`); this GLM peer is a
  cross-family lens on the attested neuralwatt/opencode route (the same family that ran B.1
  peer, re-reviewing the v1.1 amendment).
- B.2 confirms the v1.1 amendment addressed the adversarial X-M1/X-M2 but not the B.1 peer
  should-fix set; the findings above re-raise the latter as still-open carry-forward.
