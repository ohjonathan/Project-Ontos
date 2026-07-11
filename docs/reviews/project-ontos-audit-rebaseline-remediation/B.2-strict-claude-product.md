---
id: audit-rb-B2-cp
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.2
role: product
family: claude
evidence_labels_used: [static-inspection, not-run]
status: completed
---

# Product Review — project-ontos-audit-rebaseline-remediation / B.2 / claude

Fresh Product session on committed spec v1.5
(`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`, `version: 1.5`).
Frozen I0 `b6f89d77e7fb684b8bd9a181a24c773d5777397a` (`b6f89d7`) was read only to
distinguish pre-upgrade operator behavior from the Phase C contract; no reviewer
verdict, consolidation, or in-progress Phase C worktree was consulted or treated
as certification. Evidence is `static-inspection` (frozen-I0 source read via
`git show`) and `not-run` (the operator tool was not executed).

## 1. User-value assessment

The user here is the Ontos **operator/adopter** — someone who runs `ontos`
commands (`log`, `activate`, `doctor`, `map`), consumes the JSON envelope from
shell automation and CI, pins `[ontos].required_version` in their project, and
publishes/consumes the released wheel. Their job is to keep documentation and
lifecycle state trustworthy without silent corruption, silent data loss, or
misleading error copy that sends them down the wrong recovery path.

Spec v1.5 brings that job materially closer to done. At I0 the operator can be
misled in exactly the ways this spec closes: an archive-marker write can fail and
the command still returns exit `0` "Session log created" with no signal at all
(frozen-I0 `b6f89d7:ontos/commands/log.py:314,343-350` — the `except` arm comments
"Non-fatal: marker creation failure shouldn't break logging" and no warning is
surfaced); a mistyped `required_version` such as `>=99.0.0, garbage` is reported
as "Incompatible Ontos version" rather than "invalid", because
`version_satisfies_requirement` reduces with `all(...)` and short-circuits on the
first false clause before the malformed later clause is ever parsed
(`b6f89d7:ontos/core/config.py:238-246`). The spec converts both into honest,
operator-legible outcomes — a warnings-only exit `3` with the log path retained,
and eager clause parsing so an invalid range is named as invalid — and it pins a
single stable migration anchor the operator can navigate to. This is genuine
problem-solution fit for the operator's actual need, not a proxy.

The spec is also honest about the boundary of the value it delivers: it repeatedly
refuses to certify Windows, TestPyPI/PyPI, child-issue lifecycles, D.6, merge,
tag, publication, or release readiness (§2 out-of-scope, §3 dependency table, §8,
and the nonclaim sentence closing every incorporation note). For an operator, that
restraint is itself user-value: the deliverable will not tell them their release
is safe when the external proofs have not run.

## 2. Product-surface cross-reference

### 2.1 Spec-declared user-visible surfaces (always required)

This is a CLI/operator tool: its "surfaces" are command messages (human + JSON),
exit codes, the JSON envelope shape, MCP tool availability, and migration/reference
copy. The spec inventories these with prose-level copy detail.

| ID | Surface type | Spec reference | User action that reaches it |
|----|--------------|----------------|-----------------------------|
| S-1 | Copy/state — log collision refusal, `E_LOG_EXISTS`, no overwrite, path retained + recovery hint (choose different title/slug, or move/remove existing log) | §4.3 ¶2; §6; §11 row 5 | `ontos log` when the target log already exists |
| S-2 | Copy/state — archive-marker ancillary failure warning beginning `Session log created, but archive marker was not updated:`; JSON `warnings[]`; exit `3`; `result.status: warnings`; created log path in `data` | §4.3 ¶4; §4.4 exit table; §11 row 9 | `ontos log` when the primary log writes but the `.ontos/session_archived` marker cannot be written |
| S-3 | Copy — invalid document ID: `Document id must be a string` / `Document id must not be empty` / plain-language pattern copy; CLI surfaces via `E_USER_INPUT` from the canonical validator | §4.2 ¶2; §11 row 2 | Any CLI command taking an ID; batch load records `parse_error` |
| S-4 | Copy/state — `required_version` incompatible: shell `1`, `error.code: E_ACTIVATION_UNUSABLE`, `data.status: not_usable`, reason beginning `Incompatible Ontos version`; invalid ranges beginning `Invalid [ontos].required_version`; both point to the migration anchor | §4.4 ¶3 | `ontos activate` under an incompatible/malformed `[ontos].required_version` |
| S-5 | State — `doctor` PATH-executable version skew (runs the PATH program, compares reported version) | §4.4 ¶1; §11 row 6 | `ontos doctor` when the PATH `ontos` differs from the active runtime |
| S-6 | State — schema-v4 JSON envelope: exactly the nine top-level keys; public exit taxonomy `0/1/2/3/5/130`, code `4` reserved | §4.4 ¶2 | Any command with `--json`, consumed by automation/CI |
| S-7 | State — read-only MCP: omits write tools, refuses persistent graph export, suppresses usage logs, opens only an existing immutable portfolio snapshot | §4.4 ¶1; §11 row 15 | Operator connects an MCP client in read-only mode |
| S-8 | State — MCP type counts enumerate every canonical lifecycle type including zero-count types | §4.4 ¶1 | Operator reads type inventory over MCP |
| S-9 | Copy — migration/reference docs (`Migration_v3_to_v4.md#audit-remediation-compatibility-contracts`, `Ontos_Manual.md`): ranges, activation contract, ID rules, `parse_error`, `E_USER_INPUT`, `E_LOG_EXISTS` recovery, archive-marker/exit-`3`, schema `4.0`, reserved code `4`, exit taxonomy, warnings-vs-failure automation warning | §7 ¶2; §11 row 14 | Operator upgrading and adding `required_version` |
| S-10 | State — exact-wheel provenance (one wheel, version/hash, downloaded-artifact test, exact `ontos==tag` from TestPyPI `--no-deps`, OIDC only to publisher jobs) | §4.5 ¶2; §11 row 16 | Operator installs/verifies the published artifact |

Copy verification within §2.1: the two highest-stakes error/warning surfaces have
their leading strings pinned exactly and consistently — S-2's warning prefix
`Session log created, but archive marker was not updated:` (§4.3 ¶4) and S-4's
`Incompatible Ontos version` / `Invalid [ontos].required_version` prefixes plus the
`E_ACTIVATION_UNUSABLE` / `not_usable` states (§4.4 ¶3). The migration anchor
`docs/reference/Migration_v3_to_v4.md#audit-remediation-compatibility-contracts`
appears identically at §4.4, §7 (`#audit-remediation-compatibility-contracts`),
and §11 row 14 — it is discoverable and drift-free, so an operator who lands on an
activation error can navigate to a single stable location. Exit `3` is described
as `warnings` / `result.status: warnings` at every occurrence (§4.3 ¶4, §4.4 exit
table, §7 ¶2, §11 row 9) and is **never** described as a failure; §7 explicitly
tells adopters their shell automation must stop treating every non-zero result as
a hard error. The one residual copy asymmetry (S-2 lacks a recovery hint/consequence
that S-1 has) is recorded as PRD-1 below.

### 2.2 Spec-vs-implementation cross-reference (Phase D.2 only)

n/a (Phase B — no implementation to cross-reference). Per Template 19 §2.2 the
Product lens does not evaluate spec-vs-code at B.2. The spec is code-first and
cites frozen I0, but the manifest field driving the code-first Product override
(`implementation_sequencing.mode: code-first-user-gated`) is not something this
Product session may assume from prose alone; the spec itself is explicit that the
Phase C typed/quarantine/no-follow/exit-`3` behaviors are *requirements to build
and verify*, not I0 state (§4.1 ¶3, §4.3 ¶2/¶4, and the closing nonclaim of every
incorporation note). §2.2 therefore stays n/a and no I0 code path is treated as
delivering a Phase C surface.

## 3. UX-friction inventory

| ID | Flow step | Friction | Severity | Evidence |
|----|-----------|----------|----------|----------|
| U-1 | `ontos log`, marker write fails | Operator gets exit `3` + "archive marker was not updated" but no statement of *what the marker does* (pre-push enforcement) or *what to do next*; must infer the consequence | should-fix | static-inspection §4.3 ¶4; I0 marker purpose `b6f89d7:ontos/commands/log.py:314,343-350` |
| U-2 | Adopter adds `required_version`, later runs under an older pre-adoption Ontos | Cognitive load: the old runtime may reject the key or fail activation before the new copy exists; spec correctly pushes this into migration copy (§7 ¶2) so the friction is documented, not silent | minor (mitigated) | static-inspection §7 ¶2 |
| U-3 | Automation consumer reads JSON after an exit-`3` command | Must distinguish `warnings` from `findings`/`usage`/`internal`; genuinely new branch, but §7 calls it out and the envelope separates `status`/`result`/`warnings`/`error` | minor (mitigated) | static-inspection §4.4 ¶2, §7 ¶2 |

Golden path (successful `ontos log`, `activate`, `map`) is unchanged and low-friction;
the friction lives on the failure/edge paths, which is where this spec concentrates.

## 4. Copy review

| ID | Surface | Current copy (spec) | Issue | Suggested alternative |
|----|---------|---------------------|-------|-----------------------|
| C-1 | Archive-marker warning (S-2) | `Session log created, but archive marker was not updated:` + error detail | States the fact; omits the *consequence* (a later `git push` pre-push archive check may complain) and any next step, unlike the collision hint | Append a short next-step, e.g. `…: <err>. Your log was saved; re-run the archive step or move the marker manually before pushing.` |
| C-2 | Log-collision recovery hint (S-1) | prose: "choose a different title/slug, or move/remove the existing log intentionally" | Semantic content is clear and testable, but the exact operator-facing string is left to Phase C; low risk given §6 asserts the hint's presence | Pin the final literal string in Phase C regression so it is the contract, not paraphrase |
| C-3 | `required_version` incompatible (S-4) | `Incompatible Ontos version: running X, but this project requires 'Y'. Use a compatible Ontos installation.` (I0 form) + migration anchor | "Use a compatible Ontos installation" is generic, but the added stable anchor answers "where do I go"; acceptable | none required — anchor discharges the gap |

Overall the copy is honest and audience-appropriate: it names paths, codes, and
recovery choices in operator language rather than engineer shorthand. The single
material gap is C-1/PRD-1.

## 5. Accessibility surface

| Concern | Evidence | Severity | Remediation category |
|---------|----------|----------|----------------------|
| CLI/JSON tool — no GUI contrast/focus/aria surface | static-inspection (whole spec) | n/a | — |
| Machine-readability as the accessibility analogue: JSON envelope has a fixed nine-key shape + typed exit taxonomy, so automation can branch without scraping human prose | §4.4 ¶2 | positive | localization/structure |
| Human copy is plain-language (ID rules, collision recovery, version guidance) rather than raw tracebacks | §4.2 ¶2, §4.3 ¶2, §4.4 ¶3 | positive | copy/localization hook |

No inaccessible surface ships; for a CLI the relevant "assistive" contract is a
stable, typed, non-scraped JSON envelope, which the spec provides.

## 6. Failure-visibility

| Failure path | User-visible signal | Recovery available? | Evidence |
|--------------|---------------------|---------------------|----------|
| Log collision | `E_LOG_EXISTS`, exit `1`, path + no-overwrite fact + recovery hint (human & JSON) | Yes — change title/slug or move/remove existing log; original log untouched | static-inspection §4.3 ¶2; I0 base `b6f89d7:ontos/commands/log.py:288-311` |
| Archive-marker ancillary failure | Warning prefix (human) + same in `warnings[]` (JSON) + exit `3` + `result.status: warnings` + **created log path retained in `data`** | Yes — primary log is saved and locatable; marker is best-effort/non-destructive. Understandable & recoverable in BOTH modes. Gap: next step not stated (PRD-1) | static-inspection §4.3 ¶4; I0 silent-at-exit-0 baseline `b6f89d7:ontos/commands/log.py:314,343-350` |
| Incompatible `required_version` | shell `1`, `E_ACTIVATION_UNUSABLE`, `data.status: not_usable`, `Incompatible Ontos version…` + migration anchor | Yes — install compatible version; anchor gives guidance | static-inspection §4.4 ¶3 |
| Malformed `required_version`, incl. a malformed *later* clause after an earlier false one | `Invalid [ontos].required_version …`, offending clause named; eager parsing means it is reported as **invalid**, not silently "incompatible" | Yes — fix the clause; not misdirected to "upgrade" | static-inspection §4.4 ¶3; I0 short-circuit defect `b6f89d7:ontos/core/config.py:238-246` |
| Invalid document ID | typed `ValueError` messages surfaced via `E_USER_INPUT`; batch → `parse_error` | Yes — correct the ID | static-inspection §4.2 ¶2 |
| Unsafe staged path / symlinked `logs_dir` / lock target | fail-closed no-follow rejection; external sentinel unchanged | Yes — refusal, not corruption; operator's external data provably intact | static-inspection §4.3 ¶3/¶5 |

Exit `3` is consistently a *warnings* result, not a failure; the created-log-plus-
failed-marker state is understandable and recoverable in both human and JSON modes
with the log path preserved. This is the specific certification the charter asked
for, and the spec satisfies it (modulo PRD-1's missing next-step).

## 7. Issues found

### Blocking (Critical)

None. No user-facing regression, inaccessible surface, failure dead-end, or
misleading error-path copy rises to blocking, and blocking Product findings require
`direct-run`/`orchestrator-preflight` evidence (P5) which this spec-stage session
does not have. The operator recovery paths the charter names (log+marker, exit `3`,
migration anchor, required-version, external-claim pending) are all present and
coherent.

### Should-fix (Major — degrades UX without blocking ship)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-1 | The archive-marker warning states the failure fact but, unlike the log-collision surface, gives the operator no consequence or next step. An operator who sees `Session log created, but archive marker was not updated:` does not learn that the marker feeds pre-push enforcement or what to do before pushing. Asymmetric with the explicit recovery hint the spec mandates for S-1. | §4.3 ¶4; §11 row 9; I0 marker purpose `b6f89d7:ontos/commands/log.py:314,343-350` | static-inspection | Read §4.3 ¶4: prefix + error detail only, no next step; contrast §4.3 ¶2 collision copy which mandates a recovery hint | Extend the S-2 warning (human + `warnings[]`) with a one-line next step, e.g. "log saved; re-create the archive marker or move it before your next push," and assert it in the exit-`3` regression named in §6/§11 row 9. |

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-2 | The log-collision recovery hint (S-1) is specified as semantic content, not a pinned literal string; the required-version messages are pinned by leading prefix + I0 anchor rather than full string. Low risk (tests assert presence), but the exact operator-facing wording is not yet the contract. | §4.3 ¶2; §4.4 ¶3; §6; §11 rows 5/11 | static-inspection | Compare S-2's exactly-pinned prefix with S-1's paraphrased hint | Have Phase C pin the final literal strings in the equality regressions so copy is the contract. |
| PRD-3 | The JSON envelope carries status information in several places for one command — top-level `status`, `result` (domain status/kind/exit category), `data.status` (e.g. `not_usable`), and `error.code`. Correct and typed, but an automation author must learn which field to branch on. | §4.4 ¶2/¶3 | static-inspection | Read the nine-key envelope + activation's `data.status` | Ensure the migration copy (S-9) shows one worked example of which field automation should switch on for each exit class. |

## 8. Positive observations

- **Honest pre/post framing.** Every operator-facing upgrade is anchored to the
  real I0 defect it fixes and explicitly labeled a Phase C requirement, not I0
  state (silent-marker-at-exit-0 → visible exit `3`; `all()` short-circuit →
  eager clause parsing). The spec does not round Phase C or external proofs up to
  certification — the closing nonclaim on every incorporation note, §3's
  "No dependency may be converted into a synthetic receipt," and §11's
  "external pending" rows are exactly the restraint an operator needs.
- **Exit `3` is a first-class warnings result, never a failure**, and §7 proactively
  warns adopters that their existing "non-zero == error" automation must change —
  the breaking-change impact is surfaced, not buried.
- **One stable, drift-free migration anchor** (`#audit-remediation-compatibility-contracts`)
  is referenced identically wherever activation errors point, so the operator has a
  single discoverable destination.
- **Fail-closed, non-destructive posture** across log/marker/lock/staged writes: the
  external sentinel's contents and inode are provably unchanged, so a refusal never
  costs the operator data — the correct default for a docs tool.
- **Machine-readability as accessibility:** a fixed nine-key envelope and typed exit
  taxonomy let automation branch without scraping human copy, and zero-count MCP
  types keep the type inventory complete rather than sparse.

## Verdict
Approve

The spec delivers a coherent, honest, recoverable operator experience for the
surfaces in scope: the created-log-plus-failed-marker state is visible and
recoverable in both human and JSON modes with the log path retained; exit `3` is
consistently a warnings result and never described as failure; the migration anchor
is exact and discoverable; and Windows, TestPyPI/PyPI, child-lifecycle, D.6, merge,
tag, publication, and release claims all remain explicitly pending. Findings PRD-1
(should-fix) and PRD-2/PRD-3 (minor) improve failure-path copy but do not block
ship at spec stage and carry no `direct-run` evidence, so they cannot gate advance.

## 10. Notes

- Scope discipline (Template 19 v1.2 boundary): I did not perform scope-compliance,
  forbidden-path, cardinality, or spec-surface-enumeration audits — those belong to
  Alignment and the mechanical gate. Findings above are UX/copy/failure-visibility
  signal only.
- Cross-cutting (product decision → technical consequence, surfaced briefly per
  §10): PRD-3's multi-field status model and PRD-1's marker warning both have
  Peer/Alignment depth (exact JSON contract, message assembly in
  `ontos/commands/log.py`); flagged here only for the operator-comprehension angle.
- Frozen I0 `b6f89d7` was used solely to establish pre-upgrade behavior for the
  four charter checks; no reviewer verdict, B.3 consolidation, or in-progress Phase C
  worktree was read or treated as certification. No sibling review was consulted.
- Evidence is `static-inspection` (committed frozen-I0 source) and `not-run` (the
  `ontos` CLI/MCP was not executed in this session); consistent with a Phase B
  spec-stage Product review.
