---
id: project-ontos-audit-rebaseline-remediation-B.1-claude-product
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: product
family: claude
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Product Review — project-ontos-audit-rebaseline-remediation / B.1 / claude

Code-first B.1 review. Per the manifest
(`implementation_sequencing.mode: code-first-user-gated`,
`implementation_ref: b6f89d77e7fb684b8bd9a181a24c773d5777397a`) and Template 19
§2.2, this Product review cross-references the spec against the real, runnable
implementation at I0, not only the spec prose. I0 is unchanged since freeze:
`git diff --stat b6f89d7..HEAD -- ontos/ scripts/` is empty (direct-run), so the
working-tree sources I exercised are the frozen snapshot. Branch
`codex/audit-rebaseline-remediation-lifecycle`, HEAD
`1973ccab047d18acf487428d6a891ed242a19e34` (direct-run).

## 1. User-value assessment

The user here is an Ontos operator/maintainer and the AI agents that bootstrap
against a project — the people who run `ontos activate|log|doctor|serve`, embed
Ontos in CI, and consume its JSON. The job is "manage docs safely and know,
unambiguously, when something went wrong." The spec's problem statement (§1, §7)
is that the pre-I0 stack could silently corrupt documents on serialize, overwrite
logs, accept malformed IDs, mutate state from a "read-only" MCP server, and ship
the wrong wheel — failures the user would only discover downstream. This is a real
user problem, not a proxy: silent corruption and false-read-only are exactly the
class where the user's trust in the tool collapses after the fact.

The I0 implementation moves that job materially closer to done, and the copy the
user actually reads when these paths fire is strong. Direct-run of the two most
load-bearing surfaces:

- `validate_document_id`: `id: 2026-07-10` (YAML-parsed date) →
  `Document id must be a string, got date: ...`; `-lead` →
  `Document id must start and end with an alphanumeric character and contain only
  letters, numbers, '_', '-', or '.'` (direct-run, `.venv/bin/python`).
- `required_version_incompatibility(">=4.7.0, <5.0.0", "4.6.0")` →
  `Incompatible Ontos version: running 4.6.0, but this project requires
  '>=4.7.0, <5.0.0'. Use a compatible Ontos installation.` (direct-run).

Both name the offending value and the remedy — the honest, user-oriented shape a
Product reviewer wants. Log-collision refusal (`E_LOG_EXISTS` with the conflicting
`path` in the JSON envelope, `ontos/commands/log.py:288-300`), read-only export
refusal (`E_READ_ONLY`, "omit export_to_file to receive the export in memory",
`ontos/mcp/tools.py:397-402`), and the doctor version-skew probe ("retry with
'<python> -m ontos'", `ontos/commands/doctor.py:659-672`) are all clear,
recoverable, and actionable. The deliverable delivers the promised user value.

Scope calibration is appropriate: this is explicitly an umbrella lifecycle review,
not a release (§2 out-of-scope keeps the 41 open / 7 partial findings and the
external release blocker live). That is the right thing to ship — it hardens the
user-facing contract without over-claiming closure.

## 2. Product-surface cross-reference

### 2.1 Spec-declared user-visible surfaces

Inventory of user-visible surfaces the spec promises (§4.2–4.5, §7). Every one
resolves to a concrete surface in the frozen implementation.

| ID | Surface type | Spec reference | User action that reaches it |
|----|--------------|----------------|-----------------------------|
| S-1 | copy/error (`E_LOG_EXISTS`) + state (no overwrite) | §4.3, §7 | `ontos log` when today's session log already exists |
| S-2 | copy/error (string/pattern ID) | §4.2, §7 | any mutate/repair/log touching a doc whose `id` is non-string or malformed |
| S-3 | copy/error (`E_READ_ONLY`) + control (write tools omitted) | §4.4, §7 | MCP client calls `export_graph(export_to_file=...)` or a write tool under `--read-only` |
| S-4 | copy/error + exit code 1 (activation incompatibility) | §4.4, §7 | `ontos activate` with `[ontos].required_version` unsatisfied |
| S-5 | copy/state (doctor PATH-CLI version skew) | §4.4 | `ontos doctor` when PATH `ontos` differs from the running package |
| S-6 | state/JSON (exhaustive lifecycle type counts incl. zero) | §4.4 | MCP/CLI type-count output |
| S-7 | JSON envelope + exit-code taxonomy (`schema_version 4.0`; 0/1/2/3/5/130) | §4.5, §7 | any command run with `--json`; any scripted exit-code check |
| S-8 | copy/exit (release-artifact provenance failure) | §4.5 | publish/CI runs `scripts/check_release_artifact.py` on a mismatched wheel |

Copy completeness at spec time: the spec declares each behavior in prose but does
**not** inventory the copy contract itself (error codes, message strings, the exit
taxonomy). Template 19 §2.1 normally treats a copy inventory gap as blocking. Under
code-first sequencing that is not fatal here — the copy contract exists and is
verifiable in the implementation (S-1…S-8 all confirmed above and in §6) — but the
spec should point to where that contract lives (the migration guide + the impl
anchors) rather than leaving it implicit. Recorded as PRD-2 (should-fix), not
blocking, precisely because §2.2 confirms the copy is real.

### 2.2 Spec-vs-implementation cross-reference (code-first exception)

| Spec-declared surface (from §2.1) | In implementation? | Implementation surface | In §2.1? |
|-----------------------------------|--------------------|------------------------|----------|
| S-1 log collision refusal | Yes | `ontos/commands/log.py:287-300` (`FileExistsError`→`E_LOG_EXISTS`, no overwrite) | Yes |
| S-2 string/pattern ID | Yes | `ontos/core/schema.py:83-97`, enforced in `serialize_frontmatter` `:334-335` | Yes |
| S-3 read-only MCP | Yes | write tools gated `ontos/mcp/server.py:197-204`; export refused `tools.py:397-402`; read-only portfolio `server.py:1055-1078` | Yes |
| S-4 activation incompatibility | Yes | `ontos/commands/activate.py:90-95` → exit 1 via `_not_usable` | Yes |
| S-5 doctor skew | Yes | `ontos/commands/doctor.py:593-677` | Yes |
| S-7 exit-code taxonomy/envelope | Yes | `ontos/ui/json_output.py:16-49,289-346` | Yes |
| S-8 release provenance | Yes | `scripts/check_release_artifact.py:33-136` (stderr + nonzero) | Yes |

No spec-declared surface is missing from the implementation, and I found no
user-visible implementation surface that the spec never mentions. Rendered copy
matches the intent of the spec prose. (S-6 type-count exhaustiveness asserted by
spec/tests; not independently exercised — noted `not-run` for that row only.)

## 3. UX-friction inventory

| ID | Flow step | Friction | Severity | Evidence |
|----|-----------|----------|----------|----------|
| U-1 | Maintainer adds `[ontos].required_version` to `.ontos.toml` and commits | Collaborators/agents on an older CLI now hit a hard `ontos activate` exit-1 with no pre-adoption warning in any doc the maintainer read before enabling it | should-fix | direct-run (message), git-grep attestation §7 |
| U-2 | User mistypes a `required_version` range | Config-error message echoes the clause literal twice (garbled) | minor | direct-run |
| U-3 | Existing doc carries a date-like/numeric `id` (`id: 2026-07-10`) | First mutate/log/repair now fails; behavior is intentional but undocumented for migrators | should-fix | direct-run |

Golden path (`activate` → `log` → `doctor` on a compatible install) is clean: no
added steps, and each failure path self-describes. The friction is concentrated in
the adopt-a-new-contract edge path (U-1/U-3), which is a documentation gap rather
than a runtime-copy gap.

## 4. Copy review

| ID | Surface | Current copy | Issue | Suggested alternative |
|----|---------|--------------|-------|-----------------------|
| C-1 | invalid `required_version` config error | `Invalid [ontos].required_version 'not-a-range': version clause 'not-a-range' 'not-a-range' is not a valid semantic version` | Clause literal is repeated (`'not-a-range' 'not-a-range'`) — reads as a bug to the user; source: `ontos/core/config.py:302` passes `label="version clause {clause!r}"` into `_parse_version`, which re-appends the same repr at `:273` | `version clause 'not-a-range' is not a valid semantic version` (drop the duplicated `{text!r}` when `label` already carries it) |
| C-2 | activation / ID / read-only / doctor messages | (see §1, §6) | None — clear, name the value + the remedy | — |

The bulk of user-facing copy is honest and audience-appropriate (operator, not
engineer-jargon). C-1 is the one visibly-off string.

## 5. Accessibility surface

| Concern | Evidence | Severity | Remediation category |
|---------|----------|----------|----------------------|
| Terminal/MCP surfaces are plain text + structured JSON; no color-only or spatial-only signaling observed in the reviewed paths | static-inspection (`json_output.py`, error paths) | n/a | — |
| Failure signals carry a machine-readable `error_code`/`exit_category` alongside prose, aiding non-visual/tooling consumption | direct-run (envelope shape `json_output.py:329-346`) | positive | — |

No accessibility blocker for a CLI/MCP surface. Localization hooks are not in
scope for this deliverable and none are promised.

## 6. Failure-visibility

| Failure path | User-visible signal | Recovery available? | Evidence |
|--------------|---------------------|---------------------|----------|
| Log name collision | `E_LOG_EXISTS` + conflicting `path` in JSON `data`; plain `output.error` otherwise; exit 1; existing log untouched | Yes — rename/inspect the existing log | static-inspection `log.py:288-300` |
| Non-string/malformed ID | `ValueError` copy naming the type/pattern; propagates to command error | Yes — fix the `id` | direct-run |
| Version incompatibility (activate) | `_not_usable(version_issue)` + exit 1; message names running vs required + remedy | Yes — install compatible Ontos | direct-run + `activate.py:90-95` |
| Doctor PATH-CLI skew | `failed`/`warning` CheckResult with "retry with '<python> -m ontos'" | Yes — explicit fallback given | static-inspection `doctor.py:639-677` |
| Read-only write attempt | `E_READ_ONLY` naming the read-only constraint + how to get the in-memory export | Yes — omit `export_to_file` / drop `--read-only` | static-inspection `tools.py:397-402` |
| Release artifact mismatch | `release artifact verification failed: <reason>` to stderr + nonzero exit | Yes — CI surfaces the exact mismatch | static-inspection `check_release_artifact.py:132-136` |

Failure-visibility is a strength of this deliverable: every reviewed failure is
non-silent, carries a code where JSON is available, and points at a next action.
No dead-end states found in the reviewed surfaces.

## 7. Issues found

### Blocking (Critical)

None. No user-facing regression, inaccessible surface, failure dead-end, or
misleading error-path copy was reproduced.

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-1 | The intentional user-visible breaking changes for `[ontos].required_version` activation-gating (S-4) and string/non-string ID validation (S-2) are documented in **no** tracked user-facing reference doc, even though `docs/reference/Migration_v3_to_v4.md:113` already sets the exact precedent of pre-warning about a config-driven compat break (`allowed_external_dependency_paths` / "upgrade every CLI install before adopting it"). A maintainer who enables `required_version` silently breaks every collaborator/agent on an older CLI; the runtime message is clear, but there is no pre-adoption warning where they'd look. | `docs/reference/Migration_v3_to_v4.md`, `docs/reference/Ontos_Manual.md` | direct-run (`git grep -niE 'required_version' -- docs/reference/*` → no matches; branch/HEAD attested §top); direct-run messages §1 | Enable `required_version: ">=4.7.0"`; run `ontos activate` on a 4.6.x install → exit 1 | Add a migration-guide note (mirroring the `:113` pattern) covering the `required_version` activation gate and the string-ID enforcement, so §7's "user-visible changes are intentional" is discoverable before adoption. |
| PRD-2 | Spec §2.1 copy inventory: the spec declares the S-1…S-8 behaviors in prose but does not inventory the copy contract (error codes, strings, exit taxonomy) nor cite where it is documented. Satisfiable under code-first (impl supplies it — §2.2), but the spec should point to the migration guide + impl anchors rather than leaving the contract implicit. | `docs/specs/project-ontos-audit-rebaseline-remediation-spec.md` §7 | static-inspection | — | Add a copy/error-code reference (or cite `Migration_v3_to_v4.md:113` + the impl anchors) to §4.5/§7. |

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-3 | Invalid-`required_version` config error repeats the clause literal (`'not-a-range' 'not-a-range'`). | `ontos/core/config.py:302` (label) + `:273` (append) | direct-run | `required_version_incompatibility("not-a-range", "4.7.1")` | Drop the duplicated `{text!r}` when the `label` already carries the clause repr. |

## 8. Positive observations

- Error copy is consistently honest and remedy-bearing: activation, ID, doctor,
  read-only, and release-checker messages all name the offending value/state and
  the next action (direct-run + static-inspection). This is the strongest UX
  property of the deliverable.
- `E_LOG_EXISTS` never overwrites the existing log and returns the conflicting
  path in the JSON envelope — the collision is both safe and diagnosable
  (`log.py:288-300`).
- The v4 JSON envelope (`json_output.py`) cleanly separates execution status,
  domain `result_status`, `exit_category`, and a machine-readable exit taxonomy —
  a genuine improvement for scripted/agent consumers, and `Migration_v3_to_v4.md:113`
  documents the exit codes and forward-compat CLI-upgrade caveat well.
- Read-only MCP is honestly read-only: write tools are not registered, persistent
  export is refused with a recovery hint, and the portfolio index opens an existing
  snapshot without initializing config/DB/WAL (`server.py:197-204,1055-1078`).
- Scope discipline: the deliverable refuses to convert external/unavailable proof
  (Windows, TestPyPI, GitHub parity) into synthetic certification (§3) and keeps
  the 41 open / 7 partial and the release blocker explicit — the right,
  non-overclaiming thing to ship.

## Verdict

Approve

The implementation delivers the user value the spec promises, and the user-facing
failure surfaces are clear, safe, and recoverable (direct-run verified on the core
copy). The findings are documentation/copy gaps (PRD-1/PRD-2 should-fix, PRD-3
minor), not user-facing regressions or dead-ends, and this deliverable is an
umbrella review that explicitly does not gate a release — the doc gaps can and
should be closed before v4.7.1/v4.8.0/v4.9.0 ship, but they do not block B.1.

## 10. Notes

- Cross-cutting (product→technical): PRD-1 is a product decision (make an intentional
  breaking contract discoverable) with a small technical consequence (a migration-doc
  edit within the already-allowed `docs/reference/Migration_v3_to_v4.md` scope). Depth
  belongs to Alignment, which owns doc/spec parity.
- Overlap-by-design with Adversarial on failure-visibility: I frame "does the user
  understand the failure?" (answer: yes, uniformly). Adversarial owns "is the failure
  reachable / exploitable?" — deferred to that seat.
- S-6 (exhaustive zero-count lifecycle type enumeration) was not independently
  exercised; recorded `not-run` in §2.2 for that row only. All other S-rows are
  direct-run or static-inspection as labeled.

## Final report — project-ontos-audit-rebaseline-remediation / B.1 / product / claude
- Status: completed
- Artifacts written: docs/reviews/project-ontos-audit-rebaseline-remediation/B.1-claude-product.md
- Smoke checks: n/a for Product reviewer (no phase-B.1 product smoke defined in manifest) = not-run (evidence: static-inspection)
- Cardinality checks: not a scope-authority role (Template 19 §"NOT your lens"); mechanical scope/cardinality gate owns these = not-run
- Commit: not committed (review-phase worker; orchestrator stages + commits per Template 01)
- Notes: Verdict Approve. Blocking: none. Should-fix: PRD-1 (migration/manual omit the required_version + string-ID breaking changes), PRD-2 (spec copy-inventory gap). Minor: PRD-3 (doubled clause literal in required_version config error). Code-first §2.2 cross-reference run against I0 b6f89d7 (unchanged since freeze).
