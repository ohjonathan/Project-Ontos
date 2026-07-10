---
id: project-ontos-audit-rebaseline-remediation-B.2-claude-product
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.2
role: product
family: claude
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Product Review — project-ontos-audit-rebaseline-remediation / B.2 / claude

Code-first B.2 re-review of corrected spec **v1.1**. Per the manifest
(`implementation_sequencing.mode: code-first-user-gated`,
`implementation_ref: b6f89d77e7fb684b8bd9a181a24c773d5777397a`) and Template 19
§2.2, this Product review cross-references the corrected spec against the real,
runnable implementation at I0. Preconditions attested (direct-run): branch
`codex/audit-rebaseline-remediation-lifecycle`, HEAD
`19af0c96a33d29fd587c27ee612856029052fb36` (`git rev-parse HEAD`), I0 `b6f89d7`
is an ancestor of HEAD (`git merge-base --is-ancestor` → yes), and
`git diff --stat b6f89d7..HEAD -- ontos/ scripts/` is **empty** — the sources I
exercised are the frozen snapshot, not drift. The B.2 mandate is narrower than
B.1's: confirm v1.1 turns the B.1 user-facing gaps into **testable Phase C
contracts** and surface any user-facing gap the incorporation left open.

## 1. User-value assessment

The user is unchanged from B.1: the Ontos operator/maintainer and the AI agents
that run `ontos activate|log|doctor|serve`, embed Ontos in CI, and consume its
JSON envelope. Their job is "manage docs safely and know, unambiguously, when
something went wrong." B.1 (Product Approve) established that the I0
implementation already delivers that value and that its failure copy is honest
and remedy-bearing; the residual gaps were **discoverability and copy** ones
(PRD-1 migration/manual omit the intentional breaking changes; PRD-2 the spec
left the copy contract implicit; PRD-3 a doubled clause literal in the
`required_version` config error), plus two adversarial minors the spec chose to
adopt (X-M1 log symlink-parent asymmetry; X-M2 validator crash instead of a
collected error list).

The right question at B.2 is whether v1.1 converts those user-facing gaps into
Phase C work a downstream verifier can mechanically close, rather than into prose
aspiration. It does. v1.1 adds an explicit "**B.1 incorporation note**" (§1) that
converts the adversarial findings into Phase C requirements without letting the
B.1 approval discharge them, then encodes each gap as a specific, anchored,
gated obligation:

- **PRD-1 → §7:** "Phase C must add normative migration copy to
  `docs/reference/Migration_v3_to_v4.md` and reference copy to
  `docs/reference/Ontos_Manual.md`" documenting the `required_version` ranges,
  the exact activation exit/code/message contract, string-only ID rules
  (including quoting date-like, numeric, and `null` YAML scalars — directly
  answering B.1's U-3 migrator concern), loader `parse_error`, CLI
  `E_USER_INPUT`, schema `4.0`, and the public exit taxonomy — and
  "Documentation drift from the code/test anchors in §§4.2/4.4 **blocks D.1**."
  A gate, not a wish.
- **PRD-2/PRD-3 → §4.4:** the exact activation contract is now spelled out
  (shell `1`, `E_ACTIVATION_UNUSABLE`, `data.status: not_usable`, reason
  beginning `Incompatible Ontos version`), and "Phase C must remove duplicated
  invalid-clause copy so each malformed clause appears once in one actionable
  message."
- **X-M1 → §4.3** and **X-M2 → §4.1:** each is a named "Phase C must close"
  obligation with the current defect anchor and, for X-M1, a required proof
  ("a test must prove an outside-workspace sentinel is unchanged").
- **§6 Test Strategy** names regression coverage for all three fix classes: "B.1
  regressions for a symlinked `logs_dir`, malformed registry rows, and one-copy
  invalid `required_version` diagnostics."

That is the correct thing to build: v1.1 hardens the user-facing contract into
testable obligations while §2/§3/§9 keep the umbrella review from over-claiming
release readiness. Scope calibration is right.

## 2. Product-surface cross-reference

### 2.1 Spec-declared user-visible surfaces

v1.1 now inventories the copy contract that B.1 flagged as implicit (PRD-2): the
error codes and message prefixes are named in-line in §§4.2–4.4, and §7 enumerates
the copy that must reach the user-facing docs. Every surface resolves to a
concrete anchor in I0 (direct-run confirmations noted).

| ID | Surface type (control / copy / state / aria) | Spec reference | User action that reaches it |
|----|----------------------------------------------|----------------|-----------------------------|
| S-1 | copy/error (`E_LOG_EXISTS`) + state (no overwrite) | §4.3, §7 | `ontos log` when today's session log already exists (`log.py:294`, direct-run) |
| S-2 | copy/error (string/pattern ID; `ValueError` prefixes) | §4.2, §7 | any mutate/repair/log touching a doc with a non-string or malformed `id` |
| S-3 | copy/error (`E_READ_ONLY`) + control (write tools omitted) | §4.4, §7 | MCP `export_graph(export_to_file=...)` or a write tool under `--read-only` |
| S-4 | copy/error + exit `1` (activation incompatibility) | §4.4, §7 | `ontos activate` with `[ontos].required_version` unsatisfied (`activate.py:60` `E_ACTIVATION_UNUSABLE`, direct-run) |
| S-5 | copy/state (doctor PATH-CLI version skew) | §4.4 | `ontos doctor` when PATH `ontos` differs from the running package |
| S-6 | state/JSON (exhaustive lifecycle type counts incl. zero) | §4.4 | MCP/CLI type-count output |
| S-7 | JSON envelope + exit taxonomy (`schema_version 4.0`; 0/1/2/3/5/130) | §4.4, §4.5, §7 | any `--json` command; any scripted exit-code check (`json_output.py:16` `= "4.0"`, direct-run) |
| S-8 | copy/exit (release-artifact provenance failure) | §4.5 | publish/CI runs `scripts/check_release_artifact.py` on a mismatched wheel |

Copy completeness at B.2: the PRD-2 gap is substantially closed — v1.1 names the
codes and prefixes and routes the full copy contract to the migration guide via a
D.1-gating clause. Two residual copy-scope observations are recorded below
(PRD-B2-1, PRD-B2-2); neither is blocking because the contract is now explicit
and testable.

### 2.2 Spec-vs-implementation cross-reference (code-first)

The artifact under review is spec v1.1 (a re-review after incorporation); I0 is
the pre-Phase-C snapshot, so the cross-reference has two honest halves.

| Spec-declared item | In I0 implementation? | Implementation surface / evidence |
|--------------------|-----------------------|-----------------------------------|
| S-1…S-8 user-visible surfaces (§2.1) | Yes (unchanged since B.1) | Confirmed B.1 §2.2; re-attested: `log.py:294`, `activate.py:60`, `errors.py:14`, `json_output.py:16` (direct-run grep) |
| v1.1 Phase C contract — doubled-clause fix (PRD-3, §4.4) | **Not yet** (correct — Phase C work) | Reproduced at I0: `required_version_incompatibility("not-a-range","4.7.1")` → `Invalid [ontos].required_version 'not-a-range': version clause 'not-a-range' 'not-a-range' is not a valid semantic version` (direct-run) |
| v1.1 Phase C contract — migration/manual copy (PRD-1, §7) | **Not yet** (correct — Phase C work) | `git grep -niE 'required_version' -- 'docs/reference/*'` → exit 1 (no matches); string-ID/date-like copy → exit 1 (no matches) (direct-run) |
| v1.1 Phase C contract — X-M1 log no-follow (§4.3), X-M2 collected-error (§4.1) | **Not yet** (correct — Phase C work) | Defect anchors cited in spec; X-M2 crash reproduced in B.1 adversarial |

No spec-declared user-visible surface is missing from I0, and I found no
user-visible I0 surface the spec never mentions. The v1.1-added Phase C contracts
are, correctly, *not* present in the pre-Phase-C snapshot — that is the expected
state and the reason they are Phase C obligations rather than B.2 blockers.

## 3. UX-friction inventory

The B.1 friction items (U-1 silent-break-on-adoption, U-2 garbled range error,
U-3 undocumented ID break) are all now addressed by v1.1 as Phase C contracts.
The one residual friction is a copy-scope nuance in how the migration contract is
framed.

| ID | Flow step | Friction | Severity | Evidence |
|----|-----------|----------|----------|----------|
| U-1' | Maintainer adds `[ontos].required_version` to `.ontos.toml`, collaborators/agents on an older CLI hit hard `ontos activate` exit-1 | v1.1 §7 mandates documenting the *contract* (ranges, exit/code/message) but does not explicitly require the pre-adoption **caution** ("upgrade every CLI install before enabling this") that `Migration_v3_to_v4.md:113` already models for `allowed_external_dependency_paths` | should-fix | static-inspection (§7 text); direct-run (grep: no `required_version` in reference docs at I0) |
| U-2' | User mistypes a `required_version` range | v1.1 §4.4 requires the doubled-clause literal removed → one actionable message | resolved-by-contract | direct-run (defect reproduced at I0; §4.4 gates the fix) |
| U-3' | Existing doc carries a date-like/numeric `id` | v1.1 §7 requires migration copy on "quoting date-like, numeric, and `null` YAML scalars" | resolved-by-contract | static-inspection §7 |

Golden path is unchanged and clean. Friction is confined to the adopt-a-new-
contract edge, and v1.1 turns nearly all of it into documented, gated Phase C
work.

## 4. Copy review

| ID | Surface | Current copy (I0) | Issue | Suggested alternative |
|----|---------|-------------------|-------|-----------------------|
| C-1' | invalid `required_version` config error | `Invalid [ontos].required_version 'not-a-range': version clause 'not-a-range' 'not-a-range' is not a valid semantic version` (direct-run) | Clause literal repeated — reads as a bug to the user. v1.1 §4.4 now **requires** Phase C to collapse this to one occurrence; confirmed the defect still exists at I0, so the contract targets a real string. | `version clause 'not-a-range' is not a valid semantic version` |
| C-2' | activation / ID / read-only / doctor / `E_LOG_EXISTS` messages | (see B.1 §1/§6) | None — clear, name the value + the remedy; v1.1 pins their exact prefixes in §§4.2–4.4 | — |

The one visibly-off string (C-1') is now under an explicit "each malformed clause
appears once in one actionable message" Phase C obligation. Good — v1.1 converts
a B.1 minor into a testable copy contract.

## 5. Accessibility surface

| Concern | Evidence | Severity | Remediation category |
|---------|----------|----------|----------------------|
| Terminal/MCP surfaces are plain text + structured JSON; no color-only or spatial-only signaling in the reviewed paths | static-inspection | n/a | — |
| Failure signals carry a machine-readable `error.code`/exit category alongside prose (`json_output.py`), aiding non-visual/tooling consumers | direct-run (`schema_version "4.0"` at `json_output.py:16`) | positive | — |

No accessibility blocker for a CLI/MCP surface. Localization is not in scope and
none is promised. v1.1's requirement that the exit taxonomy + `schema_version 4.0`
reach the migration doc improves discoverability for tooling/agent consumers.

## 6. Failure-visibility

v1.1's incorporation strengthens failure-visibility rather than weakening it. Each
reviewed failure path stays non-silent and recoverable, and X-M2's contract turns
a traceback into a collected, user-readable error list.

| Failure path | User-visible signal | Recovery available? | Evidence |
|--------------|---------------------|---------------------|----------|
| Log name collision | `E_LOG_EXISTS` + conflicting `path` in JSON; exit 1; existing log untouched | Yes — inspect/rename existing log | static-inspection `log.py:294`; §4.3 |
| Non-string/malformed ID | `ValueError` naming type/pattern; `parse_error` on batch load; `E_USER_INPUT` on CLI input | Yes — fix the `id` | §4.2; `errors.py:14` (direct-run) |
| Version incompatibility (activate) | `E_ACTIVATION_UNUSABLE` + exit 1; reason begins `Incompatible Ontos version` | Yes — install compatible Ontos | direct-run `activate.py:60`; §4.4 |
| Read-only write attempt | `E_READ_ONLY` + in-memory-export hint | Yes — omit `export_to_file` / drop `--read-only` | §4.4 (B.1 `tools.py:397-402`) |
| Malformed registry row (X-M2) | v1.1 §4.1 contract: collected "missing fields" error + non-zero exit, **never** an uncaught `KeyError` | Yes — fix the row from the listed fields | §4.1; B.1 direct-run repro of the current crash |
| Interrupted multi-file writer work | best-effort rollback with retained recovery evidence; §4.3 honestly labels durable crash recovery as one of the 7 partial areas | Partial — non-overclaimed | static-inspection §4.3 |

Failure-visibility remains a strength, and the §4.3 refusal to over-claim durable
crash recovery is the honest thing to tell a user.

## 7. Issues found

### Blocking (Critical — user-facing regression, inaccessible surface, failure dead-end, misleading copy in error path)

None. v1.1 converts every B.1 user-facing gap (PRD-1/PRD-2/PRD-3) and the two
adopted adversarial minors (X-M1/X-M2) into named, anchored, testable Phase C
contracts with §6 regression coverage and a §7 D.1-gating clause. No user-facing
regression, inaccessible surface, failure dead-end, or misleading error-path copy
was reproduced at I0.

### Should-fix (Major — degrades UX without blocking ship)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-B2-1 | The §7 migration-copy contract mandates documenting the `required_version` ranges + the exact activation exit/code/message contract, but does not explicitly require the **pre-adoption caution** that enabling `required_version` hard-breaks `ontos activate` for every collaborator/agent on an older CLI — the specific B.1 PRD-1 concern (U-1). `docs/reference/Migration_v3_to_v4.md:113` already models this pattern ("upgrade every CLI install before adopting it") for a sibling config-driven break. Documenting the mechanics without the "upgrade collaborators first" framing leaves the discoverability gap half-closed for the maintainer about to enable the gate. | spec §7 | static-inspection (§7 text) + direct-run (`git grep -niE 'required_version' -- 'docs/reference/*'` → exit 1, no matches at I0) | Enable `required_version: ">=4.7.0"`; run `ontos activate` on a 4.6.x install → exit 1 | Extend §7 to require the migration copy to carry an explicit pre-adoption caution (mirroring `Migration_v3_to_v4.md:113`), so the breaking activation gate is discoverable *before* a maintainer enables it, not only after it fires. |

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-B2-2 | §7's enumerated required migration content, and its "blocks D.1" drift gate (anchored only to §§4.2/4.4), omit the log-collision `E_LOG_EXISTS` user-visible contract (§4.3, surface S-1). A user reading the migration/manual will find the ID, activation, exit-taxonomy, and schema copy but not the "log collisions now fail, never overwrite" behavior change, and doc drift on that surface is not gated. | spec §7 (content list + §§4.2/4.4 drift anchor) | static-inspection | — | Add the `E_LOG_EXISTS` / no-overwrite behavior to the §7 required-copy list and extend the drift gate's anchor set to include §4.3, so the log-collision contract is both documented and drift-gated alongside the others. |

## 8. Positive observations

- v1.1's §1 "B.1 incorporation note" explicitly refuses to let the B.1 approval
  discharge the adopted findings — "The B.1 approval does not discharge those
  requirements" — which is exactly the honest bookkeeping that keeps a re-review
  from becoming a rubber stamp.
- Every B.1 user-facing gap became a **testable** contract, not prose: §7 gates
  D.1 on documentation drift from code/test anchors; §6 names the three
  regressions; §4.1/§4.3/§4.4 carry "Phase C must close/remove" obligations with
  current-defect anchors. Direct-run confirmed the doubled-clause string and the
  missing-doc state still exist at I0, so the contracts target real defects.
- The string-ID migration contract (§7) explicitly covers "quoting date-like,
  numeric, and `null` YAML scalars" — a precise, user-actionable answer to the
  B.1 U-3 migrator concern, not a vague "IDs are stricter now."
- External release evidence stays honestly pending: §3 ("No dependency may be
  converted into a synthetic receipt"), §9 ("Do not synthesize … Windows
  results, or TestPyPI results"), and the §11 matrix's "external pending" rows
  mean an operator reading the evidence will not be misled into thinking Windows
  or TestPyPI behavior is certified. That is the correct, non-overclaiming thing
  to ship from a release-evidence-wording lens.
- §4.3 labels durable crash recovery as one of the seven still-partial areas
  rather than claiming it — honest failure copy about the tool's own limits.

## Verdict

Approve

v1.1 turns the B.1 user-facing gaps into testable, anchored Phase C contracts,
and no B.2 blocker was reproduced at I0. Required-version adoption, string/YAML ID
migration, error codes/copy, log/MCP failure recovery, JSON/exit compatibility,
documentation discoverability, and external release-evidence wording are each
converted into a named obligation with a §6 regression and, for docs, a §7
D.1-gating drift clause (direct-run: the doubled-clause string and the missing
migration copy still exist at I0, so the contracts target real defects). The two
residual findings are copy-scope refinements to the §7 migration contract —
PRD-B2-1 (add the pre-adoption breaking-change caution) should-fix and PRD-B2-2
(include the `E_LOG_EXISTS` contract) minor — neither a user-facing regression
nor a dead-end, and this umbrella review explicitly does not gate a release. They
should be folded into the Phase C documentation work before v4.7.1/v4.8.0/v4.9.0
ship, but they do not block B.2.

## 10. Notes

- Cross-cutting (product→technical): PRD-B2-1 and PRD-B2-2 are product decisions
  (make the breaking `required_version` gate and the log-collision contract
  discoverable) with small technical consequences (edits within the already-
  allowed `docs/reference/*` scope and the §7 contract text). Depth on
  doc/spec parity belongs to Alignment.
- Overlap-by-design with Adversarial on failure-visibility: I frame "does the
  user understand the failure and know what to do?" (answer under v1.1: yes,
  uniformly, and X-M2's contract improves it from traceback to collected error
  list). Adversarial owns "is the failure reachable/exploitable?" (X-M1 symlink
  reachability) — deferred to that seat.
- Scope discipline: per Template 19 §"NOT your lens" (v1.2+ boundary), I did not
  perform forbidden-path / cardinality / allowed-path checks — those belong to
  the mechanical gate and Alignment. Findings here are UX/copy/discoverability
  only.
- S-6 (exhaustive zero-count lifecycle type enumeration) was not independently
  exercised at B.2; asserted by spec §4.4 + §6 tests. All other rows are
  direct-run or static-inspection as labeled.

## Final report — project-ontos-audit-rebaseline-remediation / B.2 / product / claude
- Status: completed
- Artifacts written: docs/reviews/project-ontos-audit-rebaseline-remediation/B.2-claude-product.md
- Smoke checks: n/a for Product reviewer (no phase-B.2 product smoke defined in manifest) = not-run (evidence: static-inspection)
- Cardinality checks: not a scope-authority role (Template 19 §"NOT your lens"); mechanical scope/cardinality gate owns these = not-run
- Commit: not committed (review-phase worker; orchestrator stages + commits per Template 01)
- Notes: Verdict Approve. Blocking: none. Should-fix: PRD-B2-1 (§7 migration copy should require the pre-adoption breaking-change caution for required_version). Minor: PRD-B2-2 (§7 required content + D.1 drift gate omit the E_LOG_EXISTS log-collision contract). Confirmed v1.1 converts B.1 PRD-1/PRD-2/PRD-3 + adopted X-M1/X-M2 into testable Phase C contracts (§4.1/§4.3/§4.4/§6/§7). Code-first §2.2 cross-reference run against I0 b6f89d7 (unchanged since freeze; direct-run: doubled-clause string + missing migration copy still present, confirming contracts target real defects).
