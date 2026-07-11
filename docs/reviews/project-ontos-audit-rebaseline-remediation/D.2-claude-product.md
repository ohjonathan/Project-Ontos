---
id: project-ontos-audit-rebaseline-remediation-D.2-claude-product
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: D.2
role: product
family: claude
evidence_labels_used: [direct-run, static-inspection, not-run]
status: completed
---

# Product Review — project-ontos-audit-rebaseline-remediation / D.2 / claude

Reviewed spec v1.5 (`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`)
against the exact Phase C implementation I1
`05b090d53f7b0c9c4afdbb5fb23ab58cdfa01fa0`. The current worktree HEAD is
`9dbe5e1` on branch `codex/audit-rebaseline-remediation-lifecycle`; because
`9dbe5e1` carries later review-board scaffolding plus a small validator/registry
delta, all runtime evidence below was produced against a clean `git archive` of
I1 (`05b090d`) so behavior is faithful to the reviewed commit. Surfaces were
exercised in a throwaway `ontos init` project and with bounded synthetic
inputs (fake PATH `ontos` shim, symlinked archive marker, synthetic wheel),
running the I1 package via the repo `.venv` interpreter with
`PYTHONPATH=<I1 export>`.

## 1. User-value assessment

The user here is an operator or an AI coding agent driving Ontos across a
repository whose team wants the v4.7.x audit-remediation contract enforced:
pinned runtime compatibility, safe document/log writes, exhaustive read-only
introspection, a stable machine JSON envelope, and honest release provenance.
The job-to-be-done is "activate a usable documentation context, and when
something is wrong, be told clearly enough to fix it and continue" — with a
parallel machine job of "consume a stable, exhaustive JSON contract that never
lies about state."

Against that job the implementation is strong on the golden path and on the
machine (JSON) surface. Activation, log creation, doctor diagnostics, read-only
MCP, type reporting, map generation, and release verification all behave as the
spec promises, and the JSON envelope is exactly the schema-v4 shape with the
documented exit taxonomy (direct-run). The remediation's core user value —
"failures are visible, honest, and recoverable" — is delivered for the JSON /
agent consumer and for most human surfaces.

The gap is narrow but real and it sits precisely on the failure-visibility
promise the spec invested most in: for a **human** operator (non-`--json`)
running `ontos activate`, an activation failure prints an outcome
(`not_usable` / `halt`) with **no reason and no recovery pointer** at all, and
the malformed-`required_version` path emits copy that both diverges from the
documented text and omits the migration guidance anchor the spec made mandatory
for that failure form. These do not break the golden path or the agent
contract, but they degrade the exact "the user knows what went wrong and what
to do next" experience the deliverable is selling. Details in §6–§7.

## 2. Product-surface cross-reference

### 2.1 Spec-declared user-visible surfaces

| ID | Surface type | Spec reference | User action that reaches it |
|----|--------------|----------------|-----------------------------|
| S-1 | State + copy: activation usable/not_usable + reason | §4.4, §7 | `ontos activate` (`--json`) with/without valid `required_version` |
| S-2 | Copy: incompatible-version reason `Incompatible Ontos version …` + migration anchor | §4.4 | `ontos activate` when running version fails the pin |
| S-3 | Copy: invalid-range reason `Invalid [ontos].required_version …` + migration anchor | §4.4 | `ontos activate` with malformed `required_version` |
| S-4 | State + copy: doctor PATH-executable version skew | §4.4 | `ontos doctor` when PATH `ontos` differs from running package |
| S-5 | Copy + exit: log collision `E_LOG_EXISTS`, no overwrite, recovery hint | §4.3 | `ontos log --title X` twice |
| S-6 | Copy + exit: archive-marker warning, warnings-only exit `3` | §4.3, §7 | `ontos log` when `.ontos/session_archived` cannot be written |
| S-7 | Contract: schema-v4 JSON envelope (9 keys) + exit taxonomy (`0/1/2/3/5/130`, `4` reserved) | §4.4, §7 | any command with `--json` |
| S-8 | Behavior: read-only MCP omits write tools, refuses persistent export | §4.4 | MCP server started `read_only` |
| S-9 | State: exhaustive type counts incl. zero-count types | §4.4 | MCP `workspace_overview` / canonical view |
| S-10 | State: generated context map is stable across regenerations | §4.5 | `ontos map` run twice |
| S-11 | Copy: CLI invalid-ID `E_USER_INPUT`, canonical validator message | §4.2 | `ontos stub --id 'bad id!'` |
| S-12 | Copy: release-artifact verification / mismatch messaging | §4.5 | `scripts/check_release_artifact.py` |
| S-13 | Doc copy: migration guidance section + anchor target | §7 | operator follows the anchor from an error message |

Copy strings for S-1…S-13 are inventoried in the spec (§4.2–§4.5, §7) and, for
the collision, archive-marker, exit-taxonomy, and ID surfaces, mirrored in
`docs/reference/Migration_v3_to_v4.md`. One documented string (S-3) does not
match what the code renders — see §2.2 and PRD-2.

### 2.2 Spec-vs-implementation cross-reference (Phase D.2)

| Spec-declared surface | In implementation? | Implementation surface | In §2.1? |
|-----------------------|--------------------|------------------------|----------|
| S-1 activation state/reason | Yes | `activate.run_activation` → JSON `data.status`/`data.reason` (direct-run) | Yes |
| S-2 incompatible reason + anchor | Yes | `config.required_version_incompatibility` → `data.reason` "Incompatible Ontos version … See …#audit-remediation-compatibility-contracts." (direct-run) | Yes |
| S-3 invalid-range reason `Invalid [ontos].required_version` + anchor | **Partial / drifted** | Activation surfaces `Config error: version clause '…' is not a valid semantic version` (no `Invalid …` prefix, no anchor); the anchored branch at `config.py:273` is shadowed by the load-time eager parse at `config.py:181-184` (direct-run) | Yes — PRD-2 |
| S-4 doctor skew | Yes | `doctor.check_cli_availability` FAIL/WARN with anchor + retry hint in `details` (direct-run) | Yes |
| S-5 log collision | Yes | `log.py:311-320` human + JSON, exit `1`, path + recovery hint (direct-run) | Yes |
| S-6 archive-marker warning | Yes | `log.py:342-355`, `_create_archive_marker` — exit `3`, `result.status: warnings`, message in `warnings[]`, log path retained (direct-run) | Yes |
| S-7 JSON envelope + exit taxonomy | Yes | `ui/json_output.py:16-49` — 9-key envelope, `ExitCode` enum lacks `4` (direct-run) | Yes |
| S-8 read-only MCP | Yes | `server.py:197` omits `_register_write_tools`; `tools.export_graph` raises `E_READ_ONLY` (direct-run) | Yes |
| S-9 exhaustive types | Yes | `tools.py:72` seeds all 15 canonical types at 0 (direct-run) | Yes |
| S-10 map stability | Yes | `map._write_context_map_if_changed` skips timestamp-only rewrites (direct-run) | Yes |
| S-11 CLI invalid ID | Yes | `E_USER_INPUT`, canonical `validate_document_id` copy, exit `2` (direct-run) | Yes |
| S-12 release messaging | Yes | `check_release_artifact.main` "verified …" / "release artifact verification failed: …" (direct-run) | Yes |
| S-13 migration anchor | Yes | `Migration_v3_to_v4.md:120` heading slugs to `audit-remediation-compatibility-contracts` (static-inspection) | Yes |

Rendered-copy check: all surfaces match spec-declared strings **except S-3**.
The migration doc (`Migration_v3_to_v4.md:141`) states "A malformed range uses a
reason beginning `Invalid [ontos].required_version`," but the tool renders
`Config error: version clause '…' is not a valid semantic version`. Drift on a
rendered error string is a spec/doc-vs-code copy mismatch (PRD-2).

No implementation surface was found that is absent from §2.1.

## 3. UX-friction inventory

| ID | Flow step | Friction | Severity | Evidence |
|----|-----------|----------|----------|----------|
| U-1 | Human runs `ontos activate`, activation fails | Output shows `Activation status: not_usable` + `Recommended agent action: halt` but no reason and no next step; operator must re-run with `--json` (and parse `data.reason`) to learn it is a version problem | should-fix | direct-run (§6, PRD-1) |
| U-2 | Operator sets a typo'd `required_version` and activates | Reason names the bad clause but gives no pointer to the compatibility-contracts doc that lists supported ranges; the promised guidance anchor is absent | should-fix | direct-run (§4, PRD-2) |
| U-3 | Human runs `ontos doctor`, PATH skew FAILs | Message line is shown, but the concrete recovery (`retry with '<python> -m ontos'`) and migration anchor live in `details`, gated behind `-v`/`--json` (`doctor.py:1096`) | minor | direct-run |
| U-4 | Human `ontos log` hits an archive-marker failure | Warning line prints **above** the "Session log created" success line (stderr/stdout ordering), so a top-down reader sees the caveat before the success it qualifies | minor | direct-run |

Golden path is friction-free: `ontos activate` on a compatible pin returns
`usable`/`continue` (exit 0); `ontos log --title X` reports the created path
(exit 0); `ontos map` run twice yields an identical file.

## 4. Copy review

| ID | Surface | Current copy | Issue | Suggested alternative |
|----|---------|--------------|-------|-----------------------|
| C-1 | activate malformed-range reason (`data.reason`) | `Config error: version clause '>=abc' is not a valid semantic version` | Accurate and clause-specific, but omits the migration anchor the spec requires for *both* failure forms, and does not match the documented `Invalid [ontos].required_version` prefix | Route the malformed-range case through `required_version_incompatibility` so the reason begins `Invalid [ontos].required_version:` and ends `See docs/reference/Migration_v3_to_v4.md#audit-remediation-compatibility-contracts.` |
| C-2 | incompatible reason | `Incompatible Ontos version: running 4.7.0, but this project requires '>=5.0.0'. Use a compatible Ontos installation. See docs/reference/…#audit-remediation-compatibility-contracts.` | None — clear, honest, actionable, anchored | keep |
| C-3 | log collision | `Session log already exists: <path>. Choose a different --title, or intentionally move/remove the existing log before retrying.` | None — retains path + no-overwrite fact + recovery hint per §4.3 | keep |
| C-4 | archive-marker warning | `Session log created, but archive marker was not updated: operation path must not be a symlink: <path>. Fix the .ontos path or permissions before pushing.` | None — honest, names the fact and the fix | keep |
| C-5 | read-only export refusal | `Persistent graph export is unavailable in read-only mode; omit export_to_file to receive the export in memory.` | None — tells the user exactly how to recover | keep |
| C-6 | release verify | `verified <wheel>: ontos <ver> sha256=<hash>` / `release artifact verification failed: Version mismatch: expected '4.9.0', got '4.7.1'` | None — provenance stated plainly; failures name the differing dimension | keep |

## 5. Accessibility surface

| Concern | Evidence | Severity | Remediation category |
|---------|----------|----------|----------------------|
| Status conveyed by emoji (✅/❌/⚠️) prefixes | `log`/`stub`/`doctor` human output | none (info also carried in text: `Error:`, `WARN:`, `FAIL:`, and JSON `status`/`result_status` fields) | — |
| Machine consumers have a stable, non-visual contract | schema-v4 JSON envelope, exit taxonomy (direct-run) | none — screen-reader/no-color/no-emoji terminals and scripts read text + exit codes, not color | localization/aria (n/a for CLI) |

No blocking accessibility findings: no surface relies on color or emoji alone;
every status is also textual and machine-readable.

## 6. Failure-visibility

| Failure path | User-visible signal | Recovery available? | Evidence |
|--------------|---------------------|---------------------|----------|
| Incompatible version, `--json` | `error.code E_ACTIVATION_UNUSABLE`, `data.status not_usable`, `data.reason` "Incompatible Ontos version … See …#audit-remediation-compatibility-contracts.", exit 1 | Yes — reason + anchor | direct-run |
| Incompatible version, **human** | `Activation status: not_usable` / `Recommended agent action: halt` — **no reason, no anchor** | Weak — human must re-run `--json` to learn why | direct-run (PRD-1) |
| Malformed range, any surface | `Config error: version clause '…' is not a valid semantic version` (human output still prints no reason at all) | Partial — clause is named, but no doc pointer; human sees nothing | direct-run (PRD-1, PRD-2) |
| Doctor PATH skew FAIL | `FAIL: cli_availability: PATH ontos <v> is incompatible with this project`; `details` add anchor + `retry with '<python> -m ontos'` | Yes (recovery in `details`; `-v`/`--json`) | direct-run |
| Log collision | `❌ Session log already exists: <path>. Choose a different --title, or … move/remove …`; JSON `E_LOG_EXISTS`, exit 1, `data.path` | Yes — explicit choices | direct-run |
| Archive-marker write blocked (symlink) | `⚠️ Session log created, but archive marker was not updated: … Fix the .ontos path or permissions before pushing.`; JSON exit 3, `warnings[]`, log path retained; external sentinel + inode unchanged | Yes — non-destructive, recovery stated | direct-run |
| Read-only persistent export | `E_READ_ONLY` "Persistent graph export is unavailable in read-only mode; omit export_to_file …" | Yes | direct-run |
| Release artifact mismatch | `release artifact verification failed: <dimension> mismatch …` / "differing fields: sha256, size", exit 1 | Yes — names the failing dimension | direct-run |
| Real Windows lock / TestPyPI / PyPI proof | Marked external-pending; validated locally + by static workflow assertions only | n/a (honestly external) | not-run |

The external Windows/TestPyPI/PyPI proofs are honestly marked external-pending
in the spec and evidence matrix; per charter I do not convert their absence into
a product failure.

## 7. Issues found

### Blocking

None. No user-facing regression, inaccessible surface, dead-end, or misleading
error copy was reproduced. The golden path and the JSON/agent contract are
sound.

### Should-fix (Major — degrades UX without blocking ship)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-1 | Human (`non-json`) `ontos activate` output never renders the failure `reason`; on any `not_usable` outcome the operator sees only `Activation status: not_usable` + `halt`, with no explanation and no recovery pointer. The reason is populated in the payload but `format_activation_output` omits it. The command's primary agent consumer (`--json`) does carry the reason + anchor, which is why this is should-fix, not blocking — but a human debugging activation gets an information dead-end on a surface §7 promises is "visible." | `ontos/commands/activate.py:218-245` (`format_activation_output`, no `reason` line); payload key set at `activate.py:259-267` | direct-run | I1 export, project with `required_version = ">=9.0.0"`: `ontos activate` → prints `Activation status: not_usable` … `Recommended agent action: halt`; `grep -i 'incompat\|migration\|reason'` on the human output returns nothing; exit 1 | Add a reason line to `format_activation_output` for `not_usable` payloads (e.g. `Reason: {payload['reason']}`) so human output matches the information the JSON surface already carries |
| PRD-2 | Malformed `required_version` on `ontos activate` surfaces `data.reason = "Config error: version clause '…' is not a valid semantic version"` instead of the spec-mandated `Invalid [ontos].required_version …` + the `#audit-remediation-compatibility-contracts` anchor. The load-time eager parse (`config.py:181-184`) raises `ConfigError` and is caught by activation's generic `Config error:` handler before `required_version_incompatibility` (whose anchored `Invalid …` branch lives at `config.py:273`) can run — so that branch is unreachable in activation and the promised guidance pointer never renders. This also makes `Migration_v3_to_v4.md:141` ("reason beginning `Invalid [ontos].required_version`") inaccurate. | `ontos/core/config.py:181-184` (eager parse) shadows `config.py:258-281`; `ontos/commands/activate.py:86-95`; documented at `docs/reference/Migration_v3_to_v4.md:141` | direct-run + static-inspection | I1 export, `required_version = ">=abc"`: `ontos --json activate` → `data.reason` = `Config error: version clause '>=abc' is not a valid semantic version` (no `Invalid …`, no `#audit-remediation-compatibility-contracts`); exit 1 | Route the malformed-range reason through `required_version_incompatibility` (or wrap the load-time `ConfigError` so the surfaced reason begins `Invalid [ontos].required_version:` and includes the anchor), then reconcile the migration-doc string. Cross-cuts Alignment (spec/doc-vs-code copy contract). |

### Minor

| ID | Description | Location | Evidence | Suggested action |
|----|-------------|----------|----------|------------------|
| PRD-3 | Doctor human (non-verbose) output shows the skew message but hides the recovery `details` (migration anchor + `retry with '<python> -m ontos'`) behind `-v`/`--json`. | `ontos/commands/doctor.py:1096` | direct-run | Consider surfacing `details` for `failed` checks in default human output, or hint "run `ontos doctor -v` for remediation." |
| PRD-4 | Archive-marker warning line prints above the "Session log created" success line in human output (stderr/stdout interleave), so the caveat reads before the success it qualifies. | `ontos/commands/log.py:358-360` | direct-run | Cosmetic; emit the success line first, or route both to one stream in order. |

## 8. Positive observations

- **Incompatible-version copy is exemplary** (C-2): names running vs required
  version, states the fix, and links the exact migration anchor (direct-run).
- **Doctor skew reporting is thorough and honest**: distinguishes disappeared /
  timed-out / failed-probe / unrecognized-version / incompatible / shadow-skew,
  each with an actionable `details` line and a `python -m ontos` fallback
  (direct-run).
- **Log collision + archive-marker flows match §4.3 precisely**: collision never
  overwrites, retains the path, and offers the title/slug-or-move/remove choice;
  the archive-marker failure is warnings-only exit `3` with the message in
  `warnings[]`, the created log path retained in `data`, and the external
  symlink sentinel's contents and inode left unchanged (direct-run).
- **Read-only MCP is genuinely non-mutating**: the five write tools
  (`log_session`, `promote_document`, `rename_document`, `scaffold_document`,
  `session_end`) are omitted and persistent export raises an actionable
  `E_READ_ONLY` (direct-run).
- **Exhaustive type reporting**: all 15 canonical types are seeded to zero and
  reported even when empty, with a sum-consistency guard (direct-run).
- **Map stability with no spurious diffs**: two consecutive `ontos map` runs
  produce a byte-identical file because timestamp-only changes are not
  rewritten — regeneration does not noise up the operator's tree (direct-run).
- **Schema-v4 envelope + exit taxonomy are exactly as documented**: the 9
  top-level keys, `schema_version: "4.0"`, and codes `0/1/2/3/5/130` with `4`
  absent from the `ExitCode` enum (direct-run).
- **Release provenance messaging is clear and honest**, naming distribution,
  version, and sha256 on success and the differing dimension on failure
  (direct-run).
- **CLI invalid-ID copy is the canonical validator message** with `E_USER_INPUT`
  and exit `2`, so the CLI and loader speak with one voice (direct-run).

## Verdict

Request changes

No blocking product findings: the golden path, the JSON/agent contract, and the
overwhelming majority of user-visible surfaces meet the spec and are done well
(§8). The two should-fix items are both on the activation-failure surface the
deliverable most promises to make "visible and recoverable": PRD-1 (human
`ontos activate` output omits the failure reason entirely) and PRD-2 (the
malformed-range reason drops the mandated migration-guidance anchor and
contradicts the documented copy). Because they are should-fix rather than
blocking, they do not on their own gate ship under P5; I record "Request
changes" to ensure the human failure-visibility gap and the copy/doc drift are
addressed, and defer final gating weight to consolidation. External
Windows/TestPyPI/PyPI proofs remain honestly external-pending and are not
counted against the implementation.

## 10. Notes

- Cross-cutting: PRD-2 has a technical root cause (load-time eager parse
  shadowing the anchored incompatibility branch) whose correctness/ordering
  aspects belong to Peer/Alignment; I raise it here only for its user-visible
  copy and failure-visibility consequences (missing anchor, doc-vs-code drift).
- Evidence was produced against a `git archive` of I1 `05b090d` rather than the
  worktree HEAD `9dbe5e1`, because HEAD carries later review-board scaffolding
  and a small validator/registry delta; running against the exported I1 tree
  keeps behavior faithful to the reviewed commit.
- Per charter I did not run the full suite, did not read D.1 / B-family /
  sibling D.2 verdicts, dispatch results, receipts, or tracker conclusions, and
  did not treat missing real Windows/TestPyPI runs (honestly marked
  external-pending) as product failures.
</content>
</invoke>
