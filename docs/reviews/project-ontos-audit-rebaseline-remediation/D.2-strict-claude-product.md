---
id: audit-rb-D2-cprod
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: D.2
role: product
family: claude
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Product Review — project-ontos-audit-rebaseline-remediation / D.2 / claude

Reviewed spec v1.5 (`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`)
against the exact Phase C implementation I1
`05b090d53f7b0c9c4afdbb5fb23ab58cdfa01fa0`. I exercised the implementation from a
clean detached worktree at I1 (`git worktree add --detach`) using the project's
`.venv` interpreter, so every `direct-run` result below is against I1's real bytes,
not the review-branch HEAD. Source drift I1→HEAD is limited to
`scripts/validate-audit-remediation-registry.py` and its test; every operator-visible
surface I exercised is byte-identical at I1 and HEAD.

## 1. User-value assessment

The user here is an operator or coding agent driving Ontos at a repository where the
audit-remediation branch changed public CLI/MCP/activation contracts (§1, §7). Their
jobs: activate a project safely, learn when their runtime is incompatible, record a
session log without silently clobbering prior work, trust that read-only MCP does not
mutate the tree, and — for release engineers — trust that only the exact tagged wheel
ships. The spec's central product promise (§7) is that "user-visible changes are
intentional" and *legible*: failures announce themselves with actionable copy and a
stable exit taxonomy rather than crashing or corrupting.

Against that promise the implementation is strong. The golden path
(`activate` → `map` → `log`) works, and — more importantly for a safety-oriented
tool — the *recoverable failure paths* are where I1 spends its care: log collision
refuses to overwrite and tells the user exactly how to recover; an archive-marker
write that hits a symlink degrades to a visible warnings-only exit `3` while leaving
the external inode untouched and the primary log intact; incompatible runtimes are
caught at activation (shell `1`, `E_ACTIVATION_UNUSABLE`) and again, more legibly, by
`doctor`. The job the user is trying to do is genuinely brought closer to done, and
the destructive-failure modes the spec worries about (§8 P0/P1) are surfaced rather
than hidden.

Two should-fix gaps keep this from being frictionless, both on the *activation
version* surface: the human (non-JSON) `activate` channel drops the actionable reason
string, and the malformed-`required_version` copy the user actually sees ("Config
error: …") does not match what the user-facing migration doc promises
("Invalid [ontos].required_version …"). Neither is a dead-end — recovery information
is reachable — so they degrade the experience without blocking ship.

The spec honestly marks Windows and TestPyPI/PyPI as external-pending blockers (§3,
Dependencies; §11 matrix). I did not convert those unavailable real-runner surfaces
into product failures; the UI and matrix are honest about their pending state.

## 2. Product-surface cross-reference

### 2.1 Spec-declared user-visible surfaces

| ID | Surface type | Spec reference | User action that reaches it |
|----|--------------|----------------|-----------------------------|
| S-1 | copy + exit (activation version incompatible) | §4.4; §7 | `ontos activate` with incompatible `[ontos].required_version` |
| S-2 | copy + exit (activation invalid range) | §4.4; §7 | `ontos activate` with malformed `required_version` |
| S-3 | state/copy (doctor version skew + incompatibility) | §4.4; §11 | `ontos doctor` when PATH ontos differs from running package |
| S-4 | copy + exit (log collision refusal + recovery hint) | §4.3; §7 | `ontos log <existing title>` |
| S-5 | copy + exit `3` (archive-marker warning) | §4.3; §11 | `ontos log` when `.ontos/session_archived` cannot be safely written |
| S-6 | JSON envelope + exit taxonomy | §4.4; §7 | any `--json` command; any non-zero result |
| S-7 | behavior (read-only MCP omits write tools) | §4.4; §11 | connect an MCP client in read-only mode |
| S-8 | state (exhaustive type counts incl. zero-count) | §4.4; §11 | MCP `workspace_overview` / canonical snapshot |
| S-9 | copy (CLI invalid document ID via `E_USER_INPUT`) | §4.2 | `ontos stub --id "<invalid>"` |
| S-10 | state (generated context map stability / exclusions) | §4.5; §11 | `ontos map` (twice) |
| S-11 | copy + exit (release artifact provenance messaging) | §4.5; §11 | `scripts/check_release_artifact.py` in the publish workflow |

Copy strings are inventoried in the spec at prose level for each of the above
(collision recovery hint, archive-marker warning prefix, activation reason prefixes,
migration-doc copy). Copy is complete and internally consistent within the spec.

### 2.2 Spec-vs-implementation cross-reference (Phase D.2)

| Spec-declared surface (§2.1) | In implementation? | Implementation surface (I1) | In §2.1? |
|------------------------------|--------------------|-----------------------------|----------|
| S-1 incompatible version | Yes | `config.py:258-282` reason; JSON `E_ACTIVATION_UNUSABLE`, `data.status: not_usable`; shell `1` (direct-run) | Yes |
| S-2 invalid range | Partial (copy drift) | `config.py:181-184` eager load-time validation renders "Config error: …", shadowing the `Invalid [ontos].required_version` branch at `config.py:273` (direct-run) | Yes |
| S-3 doctor skew/incompat | Yes | `doctor.py:671-692` WARN skew / FAIL incompatible with "retry with … -m ontos" (direct-run) | Yes |
| S-4 log collision | Yes | `E_LOG_EXISTS`; path + no-overwrite + "Choose a different --title, or … move/remove" (direct-run) | Yes |
| S-5 archive-marker warning | Yes | exit `3`, `result.status: warnings`, warning begins "Session log created, but archive marker was not updated:", external sentinel unchanged (direct-run) | Yes |
| S-6 JSON envelope/exit | Yes | exactly 9 top-level keys, `schema_version 4.0`; findings=`1`, usage=`2`, warnings=`3` (direct-run) | Yes |
| S-7 read-only MCP | Yes | `server.py:197` gates `_register_write_tools`; `tests/mcp/test_read_only_registration.py` 7/7 (direct-run) | Yes |
| S-8 exhaustive types | Yes | `tools.py:68-99` seeds all 15 `TYPE_DEFINITIONS` to 0 + sum-invariant; `test_workspace_overview.py` pass (direct-run/static) | Yes |
| S-9 invalid CLI ID | Yes | canonical validator message via `E_USER_INPUT`, exit `2` (direct-run) | Yes |
| S-10 map stability | Yes | double-generation byte-identical; two preserved user docs absent from committed map (direct-run) | Yes |
| S-11 release provenance | Yes | actionable messages; exit `1` mismatch/missing, `0` verified (direct-run) | Yes |

No implementation surface appeared that §2.1 does not name. The only cross-reference
gap is directional copy drift on S-2 (see PRD-2): what the code renders is actionable,
but it is not the string the user-facing migration reference tells the user to expect.

## 3. UX-friction inventory

| ID | Flow step | Friction | Severity | Evidence |
|----|-----------|----------|----------|----------|
| U-1 | `ontos activate` fails on incompatible/invalid version | Human output shows only `Activation status: not_usable` + `halt`; the *why* is absent from the default channel — the user must re-run with `--json` or run `doctor` to learn it is a version problem | should-fix | direct-run |
| U-2 | Read migration doc, then hit a malformed range | Doc says expect `Invalid [ontos].required_version`; user sees `Config error: …` — a momentary "is this the right error?" hesitation before they recognize it | should-fix | direct-run |
| U-3 | `ontos log` archive-marker warning | Human prints the ⚠️ warning line *before* the ✅ "created" line; the warning text itself states the log was created, so it reads fine, but top-down scanning surfaces the warning first | minor | direct-run |

## 4. Copy review

| ID | Surface | Current copy | Issue | Suggested alternative |
|----|---------|--------------|-------|-----------------------|
| C-1 | activate human (version fail) | *(reason not printed)* | Actionable reason exists in payload but is never rendered in human output | Append a `Reason: <payload.reason>` line in `format_activation_output` when status is `not_usable` |
| C-2 | activate invalid range (JSON `data.reason`) | `Config error: version clause '…' is not a valid semantic version` | Accurate and actionable, but not the `Invalid [ontos].required_version` prefix the migration doc promises | Either route the load-time failure through `required_version_incompatibility` so it carries the documented prefix + Migration anchor, or update `Migration_v3_to_v4.md:140-141` to match rendered copy |
| C-3 | log collision | `Session log already exists: <path>. Choose a different --title, or intentionally move/remove the existing log before retrying.` | None — clear, retains path + no-overwrite fact + two concrete recovery actions | (keep) |
| C-4 | archive-marker warning | `Session log created, but archive marker was not updated: … Fix the .ontos path or permissions before pushing.` | None — begins with the exact spec-required phrase and gives a next step | (keep) |
| C-5 | doctor skew | `PATH ontos reports 4.6.0, but the running package is 4.7.0 … Activation should retry with '… -m ontos'.` | None — names both versions and the fix | (keep) |

## 5. Accessibility surface

| Concern | Evidence | Severity | Remediation category |
|---------|----------|----------|----------------------|
| CLI is a text stream; no color-only signaling for failures | direct-run (exit codes + textual `FAIL/WARN/OK`, `❌/⚠️/✅` are paired with words) | none | n/a |
| JSON channel carries full machine-readable status/exit/reason for assistive or automated consumers | direct-run (9-key envelope, `error.code`, `warnings[]`) | none | localization/aria n/a for a CLI |

No accessibility blocker: severity is conveyed by exit code and by textual prefixes
(`FAIL:`/`WARN:`/`OK:`, `Error:`), not by glyph or color alone. The emoji markers are
decorative redundancies over the words.

## 6. Failure-visibility

| Failure path | User-visible signal | Recovery available? | Evidence |
|--------------|---------------------|---------------------|----------|
| Incompatible runtime version | JSON: `E_ACTIVATION_UNUSABLE` + reason + Migration anchor; `doctor` FAIL. Human `activate`: `not_usable`/`halt` only (reason omitted) | Yes — via JSON/doctor; degraded on human `activate` | direct-run |
| Malformed `required_version` | `Config error: …` naming the offending clause; shell `1` | Yes — clause is named | direct-run |
| Log title collision | `E_LOG_EXISTS`, path retained, no overwrite, recovery hint | Yes — pick new title / move existing | direct-run |
| Archive-marker unsafe write | warnings-only exit `3`, `result.status: warnings`, message + retained log path; primary log intact; external inode untouched | Yes — non-destructive; fix `.ontos` path/perms | direct-run |
| PATH/running version skew | `doctor` WARN naming both versions + fallback command | Yes | direct-run |
| Release wheel version mismatch / missing | `Version mismatch: expected … got …` / `Expected one wheel file …`; exit `1` | Yes — pipeline fails closed | direct-run |
| Invalid CLI document ID | canonical validator message + `E_USER_INPUT`, exit `2` | Yes | direct-run |

The only visibility gap is the human `activate` reason omission (U-1/C-1). Every other
failure path announces itself with actionable copy and a correct exit code, and the
two destructive-risk paths (log overwrite, symlinked marker) are honestly non-destructive.

## 7. Issues found

### Blocking (Critical)
None. No user-facing regression, inaccessible surface, failure dead-end, or misleading
error-path copy that would drive a wrong user action was reproduced. The two findings
below leave the user with a reachable, actionable recovery in every case.

### Should-fix (Major)
| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-1 | Human `ontos activate` output omits the actionable failure reason on `not_usable`. The reason ("Incompatible Ontos version …" / "Config error …") is present in the payload but `format_activation_output` never renders it, so a human operator sees only `Activation status: not_usable` + `Recommended agent action: halt` with no *why*. | `ontos/commands/activate.py:218-247` (reason set at `:260-268`, never emitted in human lines) | direct-run | In a project with `required_version=">=99.0.0"`, run `ontos activate` (no `--json`); output has no reason line; `--json` shows `data.reason` beginning "Incompatible Ontos version". | Emit a `Reason:` line in `format_activation_output` when `status == not_usable`. |
| PRD-2 | Malformed `required_version` renders "Config error: …", but the user-facing migration reference promises a reason beginning "Invalid [ontos].required_version". Because config-load validates the range eagerly (`config.py:181-184`), the documented `Invalid [ontos].required_version` branch (`config.py:273`) is shadowed on the activation path, so a user greping automation for the documented prefix never matches. | rendered: `ontos/core/config.py:181-184`; promised copy: `docs/reference/Migration_v3_to_v4.md:140-141` | direct-run | `required_version=">=not.a.version"` → `ontos --json activate`; `data.reason` = "Config error: version clause '>=not.a.version' is not a valid semantic version" (surveyed 5 malformed ranges; none rendered the documented prefix). | Reconcile the two: route load-time failures through `required_version_incompatibility` (documented prefix + Migration anchor), or amend the migration doc to the rendered copy. The exact-prefix contract in spec §4.4 is Alignment's to gate; flagged here as user-facing doc↔behavior drift. |

### Minor
| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-3 | Archive-marker human output prints the ⚠️ warning line before the ✅ "created" line. | `ontos/commands/log.py` (warning emission order) | direct-run | Plant `.ontos/session_archived` as a symlink; run `ontos log`; warning precedes the created-confirmation. | Print the ✅ created line first, then the warning; or fold both into one ordered block. |

## 8. Positive observations

- **Log collision (S-4)** is exactly the right product behavior: it refuses to
  overwrite, retains the full path, and hands the user two concrete recovery actions
  in one sentence — `E_LOG_EXISTS`, exit `1`, mirrored in JSON.
- **Archive-marker warnings-only exit `3` (S-5)** is the standout: the ancillary
  failure is loud (human warning + JSON `warnings[]` + `result.status: warnings`), the
  primary log is preserved with its path in `data`, the external sentinel's contents
  and inode are provably untouched, and the exit code lets shell automation distinguish
  a warning from a hard error — precisely the §7 migration concern.
- **Doctor version skew (S-3)** gives operators the legible version diagnostics that
  `activate` (PRD-1) withholds: it names both versions, distinguishes incompatible
  (FAIL) from merely-shadowing (WARN), and prints the exact fallback command.
- **Exit taxonomy (S-6)** is consistent across every surface I exercised
  (`0/1/2/3`), and the JSON envelope is exactly the nine spec-declared keys at
  `schema_version 4.0`.
- **Release provenance (S-11)** fails closed with clear, specific messages and correct
  non-zero exits on mismatch/missing, so a wrong artifact cannot silently pass.
- **Map stability (S-10)** double-generation is byte-identical and the two preserved
  user documents are absent from the committed map.
- The spec's **external-pending honesty** (Windows, TestPyPI) is preserved in the
  matrix and not papered over with synthetic receipts.

## Verdict

Approve

The implementation delivers the user value the spec promises: safe, legible
recoverable-failure paths with actionable recovery copy and a correct, stable exit
taxonomy across every operator-visible surface I exercised at I1. No blocking
user-facing issue was reproduced. Two should-fix findings (PRD-1 human-`activate`
reason omission; PRD-2 malformed-range copy vs. migration-doc promise) degrade the
activation-version surface without leaving the user at a dead-end — recovery
information is always reachable via `--json` or `doctor`. I recommend addressing both
in Phase D.4 but neither blocks ship from a product lens.

## 10. Notes

- Cross-cutting: PRD-2 has an obvious technical consequence — the eager load-time
  validation at `config.py:181-184` structurally shadows the `Invalid
  [ontos].required_version` branch at `config.py:273` for the activation path. Whether
  the exact-prefix contract in spec §4.4 (and the migration doc) is binding-blocking is
  an Alignment call; from the product lens the rendered message remains actionable, so
  I rank it should-fix.
- I exercised I1 from a detached worktree at `05b090d…` using the repo `.venv`
  interpreter via `PYTHONPATH`. One early "doctor OK 4.7.0" reading was a test-harness
  artifact (the PATH console-script subprocess inherited `PYTHONPATH` and imported the
  I1 tree); re-tested with a version-pinned PATH shim, doctor's skew detection is
  correct. Recorded so the observation is not mistaken for a defect.
- Per role scope I did not perform scope/forbidden-path/cardinality checks (mechanical
  gate), spec-surface enumeration (Alignment), or reachability/attack analysis
  (Adversarial). I did not run the full suite; the two MCP/type tests above are bounded
  single-file runs for direct-run evidence.

## Final report — project-ontos-audit-rebaseline-remediation / D.2 / product / claude
- Status: completed
- Artifacts written: docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-strict-claude-product.md
- Smoke checks: golden path (activate/map/log) = pass (evidence: direct-run); recoverable failure paths (version fail+recover, log collision, archive-marker exit 3, doctor skew, release provenance) = pass (evidence: direct-run)
- Cardinality checks: n/a to product role (mechanical gate owns scope/cardinality)
- Commit: not committed (review-phase worker; orchestrator stages + commits)
- Notes: 0 blocking, 2 should-fix (PRD-1, PRD-2), 1 minor (PRD-3). Verdict Approve. Reviewed exact I1 05b090d53f7b0c9c4afdbb5fb23ab58cdfa01fa0; operator-visible surfaces byte-identical I1↔HEAD.
