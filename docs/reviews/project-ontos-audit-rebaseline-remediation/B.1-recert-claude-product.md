---
id: project-ontos-audit-rebaseline-remediation-B.1-recert-claude-product
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: product
family: claude
evidence_labels_used: [static-inspection, direct-run]
status: completed
---

# Product Review — project-ontos-audit-rebaseline-remediation / B.1 / claude

Scope note: this is a B.1 recertification of spec v1.2 under code-first
sequencing. The manifest declares `user_facing: true` and
`implementation_sequencing.mode: code-first-user-gated` with
`implementation_ref: b6f89d77e7fb684b8bd9a181a24c773d5777397a` (I0), so
per Template 19 §2.2 (v1.11.0 exception) the spec-vs-implementation
cross-reference is run against the frozen I0 diff, not deferred. All
implementation claims below are evaluated at I0 via `git show b6f89d7:<path>`
(static-inspection) with repo-state attestation via git (direct-run):

```
git branch --show-current -> codex/audit-rebaseline-remediation-lifecycle
git rev-parse HEAD         -> 5e04094d26d9711a54ee4ab11876cd19cb52a9c4
git rev-parse b6f89d7      -> b6f89d77e7fb684b8bd9a181a24c773d5777397a (I0)
git rev-parse bf91b42      -> bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95 (base)
```

## 1. User-value assessment

The "user" here is two overlapping populations: (a) the **operator**
driving the audit-remediation lifecycle review, whose job is to know —
truthfully — which findings are closed, which remain open, and what has
and has not been certified; and (b) the **end user of the Ontos CLI/MCP**,
whose observable contracts (log creation, document-ID validation,
activation, JSON output, exit codes, read-only MCP) are intentionally
changed by I0. The spec's problem statement (§1) is the real job for both:
integrate a 188-file security-sensitive diff while making every
user-visible contract change explicit, safe on failure, and honestly
scoped.

The spec brings that job materially closer to done. It converts the
audit registry into the single machine authority (§4.1), enumerates each
changed CLI/MCP surface with a concrete implementation and test anchor
(§§4.2–4.4, §11), and — most importantly for user trust — it refuses to
overclaim: 41 open / 7 partial findings stay "explicit and
release-blocking" (§2, §9), and D.6 approval, tagging, publishing,
per-issue certification, Windows results, and TestPyPI availability are
all held as pending/external blockers rather than inferred (§3, §9).
For an audit-remediation deliverable, this honesty *is* the user value:
an operator who reads this spec cannot be misled into thinking a release
is ready.

The one genuine user-value gap is timing, not substance: the spec routes
the user-facing **documentation** of every new failure mode
(`E_LOG_EXISTS`, `required_version` contract, exit taxonomy, reserved
code `4`, string-ID rules) to Phase C (§7). At I0 the migration guide
does not yet document any of them (see §2.2 S-11). The spec is explicit
that this is a Phase C gate and that "documentation drift ... blocks
D.1," and it carries an adopter-safety warning (§7), so the value is
scheduled rather than dropped. This is discussed in §7 Issues as a
should-fix visibility item, not a blocker.

## 2. Product-surface cross-reference

### 2.1 Spec-declared user-visible surfaces

| ID | Surface type | Spec reference | User action that reaches it |
|----|--------------|----------------|-----------------------------|
| S-1 | state / error copy — log-collision `E_LOG_EXISTS` | §4.3, §7 | `ontos log` when today's log already exists |
| S-2 | error copy — string/pattern document-ID `ValueError` | §4.2 | loading a doc whose frontmatter `id` is non-string / empty / malformed |
| S-3 | error copy — CLI invalid `--id` (`E_USER_INPUT`) | §4.2 | `ontos stub --id "<bad id>"` |
| S-4 | state / error copy — activation incompatibility (`E_ACTIVATION_UNUSABLE`, `data.status: not_usable`) | §4.4, §7 | `ontos activate` when `[ontos].required_version` mismatches the running version |
| S-5 | error copy — invalid `required_version` range | §4.4 | `ontos activate` with a malformed `required_version` clause |
| S-6 | machine-readable state — schema-v4 JSON envelope keys | §4.4, §7 | any command with `--json` |
| S-7 | state — public exit-code taxonomy (0/1/2/3/5/130; 4 reserved) | §4.4, §7 | shell `$?` after any command |
| S-8 | control availability — read-only MCP omits write tools / refuses persistent export | §4.4 | MCP client connecting in read-only mode |
| S-9 | state — doctor executes PATH program and compares reported version | §4.4 | `ontos doctor` |
| S-10 | copy / state — MCP type counts enumerate every lifecycle type incl. zero-count | §4.4 | MCP type-count read |
| S-11 | copy — migration/manual documentation of S-1…S-10 | §7 | adopter reading `Migration_v3_to_v4.md` / `Ontos_Manual.md` |

Copy-completeness within §2.1: the spec pins the exact user-visible
strings for the load-bearing failure surfaces — activation reason begins
`Incompatible Ontos version`, invalid range begins
`Invalid [ontos].required_version`, ID errors begin
`Document id must be a string` / `Document id must not be empty`,
collision is `E_LOG_EXISTS`, invalid CLI id is `E_USER_INPUT`, loader
records `parse_error` (§4.2, §4.4). These are complete and unambiguous at
spec level; a downstream implementation cannot silently reword them
without failing the anchor.

### 2.2 Spec-vs-implementation cross-reference (I0, code-first)

| Spec-declared surface (§2.1) | In implementation @I0? | Implementation surface | In §2.1? |
|------------------------------|------------------------|------------------------|----------|
| S-1 `E_LOG_EXISTS` | Yes | `log.py` `Session log already exists: {output_path}`, code `E_LOG_EXISTS`, `data.path`, returns 1, never overwrites (uses `open("x")`) | Yes |
| S-2 ID `ValueError` copy | Yes | `schema.py` `validate_document_id` plain-English messages matching §4.2 | Yes |
| S-3 CLI invalid `--id` | Yes — but copy drifts | `stub.py` `_validate_stub_params` raises `E_USER_INPUT` with `Invalid --id. Expected ^[A-Za-z0-9]...$` (raw regex) | Yes |
| S-4 activation incompat | Yes | `activate.py` `_not_usable` → `status: not_usable`, reason from `required_version_incompatibility()` beginning `Incompatible Ontos version` | Yes |
| S-5 invalid range | Yes | `config.py` `Invalid [ontos].required_version {required!r}: ...` | Yes |
| S-6 JSON envelope keys | Yes — exact | `json_output.py:331–344` emits exactly `schema_version, command, status, exit_code, message, result, data, warnings, error` | Yes |
| S-7 exit taxonomy | Yes — exact | `ExitCode(IntEnum)` = 0/1/2/3/5/130; **no** `4` defined (reserved) | Yes |
| S-8 read-only MCP | Yes | `server.py:191–204` registers write tools only `if not read_only`; `tests/mcp/test_read_only_registration.py` present | Yes |
| S-11 migration copy | **No @I0** | `Migration_v3_to_v4.md` at I0 contains no `E_LOG_EXISTS` / `required_version` / exit-taxonomy / reserved-`4` copy | Yes (spec gates to Phase C) |

Rendered-copy match: every string I could resolve at I0 matches the
spec-declared string exactly, with the single exception of S-3 (the CLI
invalid-`--id` message renders a raw regex where the loader path renders
plain English — see §4). The S-11 documentation drift is expected: it is
the Phase C obligation, not an unplanned regression, and the spec makes
it a D.1 gate.

## 3. UX-friction inventory

| ID | Flow step | Friction | Severity | Evidence |
|----|-----------|----------|----------|----------|
| U-1 | Golden path: operator reads spec to learn what is/ isn't certified | Low. §1/§2/§9 state the stop boundary and open counts plainly; the lifecycle diagram (§10.2) ends at `D6_Pending: stop boundary; no release claim`. | minor | static-inspection §9,§10.2 |
| U-2 | End user hits `ontos log` twice in one day | Low. Second run fails fast with a named, non-destructive error naming the existing path; user re-runs later or edits. | minor | static-inspection `log.py:283–300` |
| U-3 | Adopter adds `[ontos].required_version` before upgrading their PATH/CI runtimes | Medium at I0. The behavior is safe (activation fails with an actionable message), but the *documentation* that would prevent the mistake lands in Phase C. Spec §7 carries the warning; docs do not yet. | should-fix | static-inspection §7; `Migration_v3_to_v4.md`@I0 |
| U-4 | Developer parses `ontos <cmd> --json` output | Low. Fixed nine-key envelope + separated `result` (domain status / kind / exit category) is a stable, self-describing contract. | minor | static-inspection `json_output.py:331–344` |
| U-5 | User typos `ontos stub --id "bad id"` | Medium. Fails correctly with `E_USER_INPUT`, but the message hands the user a raw regex instead of the plain-language rule the loader uses for the same concept. | should-fix | static-inspection `stub.py:183–192` |

## 4. Copy review

| ID | Surface | Current copy | Issue | Suggested alternative |
|----|---------|--------------|-------|-----------------------|
| C-1 | CLI invalid `--id` (`stub.py`) | `Invalid --id. Expected ^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$` | Written-by-engineers-for-engineers: exposes a raw regex to an end user, and diverges from the plain-English copy the loader emits for the *same* invalid-ID concept (`schema.py`: "Document id must start and end with an alphanumeric character and contain only letters, numbers, '_', '-', or '.'"). Two different messages for one rule is a copy-consistency gap. | Use the loader's plain-English sentence (optionally append the pattern as a parenthetical), so both entry points read identically. |
| C-2 | Log collision (`log.py`) | `Session log already exists: {output_path}` | Clear, honest, names the path and does not overwrite. No change. | — |
| C-3 | Activation incompat (`config.py`) | `Incompatible Ontos version: running {v}, but this project requires {req}. Use a compatible Ontos installation.` | Actionable and honest; states both versions and a next step. No change. | — |
| C-4 | Activation recommendation (`activate.py`) | `halt; no usable Ontos context is available` | Appropriate for the machine/agent consumer; clear. No change. | — |

The spec should, at Phase C, require the CLI and loader invalid-ID copy
to converge (C-1). This is a copy contract the spec currently under-pins:
§4.2 names the codes (`E_USER_INPUT` vs `parse_error`) but not that the
two paths must share user-facing wording.

## 5. Accessibility surface

| Concern | Evidence | Severity | Remediation category |
|---------|----------|----------|----------------------|
| CLI is text-only; no color-only signaling relied upon for the audited surfaces | static-inspection (errors carry text + code + path, not color) | minor | contrast |
| Machine-readability for assistive/agent consumers | `--json` envelope is stable and typed (`json_output.py`), and the read-only MCP surface exposes structured tools; this is the "screen-reader" equivalent for an agent audience and is well-formed | positive | aria/localization |
| Localization hooks | Error strings are hard-coded English literals with no i18n indirection | minor | localization |

No blocking accessibility finding. For a developer-CLI/MCP audience the
structured JSON + exit taxonomy is the accessibility-relevant surface and
it is sound; hard-coded English copy is a pre-existing, non-regressing
limitation, not introduced by this deliverable.

## 6. Failure-visibility

| Failure path | User-visible signal | Recovery available? | Evidence |
|--------------|--------------------|--------------------|----------|
| Log already exists | `E_LOG_EXISTS` + `Session log already exists: <path>`, exit 1, JSON `data.path`; **existing log untouched** | Yes — non-destructive; retry later / edit existing | static-inspection `log.py:283–300` |
| Invalid document ID (loader) | plain-English `ValueError`, recorded as `parse_error` in batch load | Yes — user fixes frontmatter `id` | static-inspection `schema.py:83–97` |
| Invalid `--id` (CLI) | `E_USER_INPUT` + regex message, non-zero | Yes — but message clarity is weak (C-1) | static-inspection `stub.py:183–192` |
| `required_version` mismatch | `E_ACTIVATION_UNUSABLE`, `data.status: not_usable`, reason `Incompatible Ontos version: ...`, exit 1 | Yes — install compatible Ontos; message names both versions | static-inspection `activate.py`, `config.py:249–266` |
| Malformed `required_version` | `Invalid [ontos].required_version '<clause>': ...`, exit 1 | Yes — user fixes the clause | static-inspection `config.py:239–266` |
| Adopter enables `required_version` before runtimes upgraded | Safe fail (above), but no doc warns them first at I0 | Partial — recoverable, but avoidable friction until Phase C docs land | static-inspection §7; `Migration_v3_to_v4.md`@I0 |
| Unsafe log path via symlinked `logs_dir` component | **Not yet a visible refusal at I0** — spec §4.3/§11 mark X-M1 as a Phase C gate ("Phase C direct-run required"); `_write_log_exclusively` still `mkdir(parents=True)` + `open("x")` without a no-follow parent pin | Reachability/refusal is an **Adversarial-lens** question; noted here only for failure-visibility completeness. Spec does not claim it is closed. | static-inspection `log.py:334–340` |

Failure visibility for the *implemented* surfaces is strong: every path
produces a named code, human text, a machine field, and (for the
destructive-adjacent log path) an explicit non-overwrite guarantee. The
one genuinely reachable-at-I0 gap (symlinked `logs_dir`) is honestly
carried as an open Phase C requirement, not masked.

## 7. Issues found

### Blocking (Critical)
None. No user-facing regression, inaccessible surface, failure dead-end,
or misleading error-path copy rises to blocking at spec-recert level. The
implemented failure surfaces are named, non-destructive, and recoverable;
the deferred items are honestly gated, not concealed. (Per P5, all
findings below rest on `static-inspection` of the I0 tree via `git show`
— no live `pytest`/CLI run — so none may gate on their own regardless.)

### Should-fix (Major)
| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-1 | CLI invalid-`--id` error hands the user a raw regex and diverges from the plain-English copy the loader emits for the same rule; the spec (§4.2) pins the codes but not shared user-facing wording, so nothing prevents the drift. | `ontos/commands/stub.py:183–192` vs `ontos/core/schema.py:83–97` | static-inspection | `git show b6f89d7:ontos/commands/stub.py \| sed -n '183,192p'` shows the regex-only message | Add a spec clause (Phase C) requiring CLI and loader invalid-ID copy to share the plain-English sentence; converge the two messages. |
| PRD-2 | At I0 the user-facing migration/manual docs do not document any of the new failure contracts (`E_LOG_EXISTS`, `required_version`/activation exit-code-message contract, reserved code `4`, string-ID rules, `E_USER_INPUT`, `parse_error`). Adopters who enable `required_version` before docs land can hit an undocumented activation failure. | `docs/reference/Migration_v3_to_v4.md`@I0 (grep for `E_LOG_EXISTS`/`required_version` → none) | static-inspection | `git show b6f89d7:docs/reference/Migration_v3_to_v4.md \| grep -niE 'E_LOG_EXISTS\|required_version'` → no contract copy | None to the spec — the spec already gates this to Phase C (§7) with a D.1 block and an adopter-upgrade warning. Recorded so consolidation can confirm Phase C closes it before D.1. |

### Minor
| ID | Description | Location | Evidence | Suggested action |
|----|-------------|----------|----------|------------------|
| PRD-3 | Error/copy strings are hard-coded English with no localization indirection. | multiple (`log.py`, `config.py`, `schema.py`) | static-inspection | Out of scope for this deliverable; note only. |
| PRD-4 | Exit code `3` (warnings → non-zero) may surprise users who equate non-zero with failure. | `json_output.py` `ExitCode.WARNINGS = 3` | static-inspection | Ensure Phase C migration copy calls out `3 = warnings` prominently (already required by §7). |

## 8. Positive observations

- **Honest scope is the headline strength.** The spec repeatedly refuses
  to round up: 41 open / 7 partial findings stay release-blocking (§2,
  §9), and D.6/merge/tag/publish/per-issue/Windows/TestPyPI are all held
  as explicit pending or external blockers (§3, §9). The lifecycle
  diagram terminates at `D6_Pending: stop boundary; no release claim`.
  This is exactly the failure-visibility an audit deliverable owes its
  operator.
- **Non-destructive log collision.** `E_LOG_EXISTS` fails fast, names the
  path, returns a machine `data.path`, and provably never overwrites an
  existing log (`open("x")`). Good failure-recovery UX.
- **Exact, stable machine contracts.** The nine-key JSON envelope and the
  0/1/2/3/5/130 exit taxonomy (with `4` deliberately reserved and
  un-emitted) are implemented at I0 exactly as specified — a dependable
  contract for scripted/agent consumers.
- **Actionable activation copy.** The incompatibility message states both
  the running and required versions and a concrete next step; the invalid
  range message quotes the offending clause.
- **Adopter-safety foresight.** §7 warns adopters to verify repository,
  PATH, hook, and CI runtimes before adding `required_version` — the spec
  anticipates the one self-inflicted foot-gun the feature introduces.
- **Read-only MCP genuinely omits write tools** at registration
  (`if not read_only`), backed by a dedicated no-write test — the
  read-only promise is structural, not advisory.

## Verdict

Approve

## 10. Notes

**Reasoning.** As a B.1 recertification of spec v1.2 under code-first
sequencing, the Product lens asks whether this is the right thing to ship
and whether users experience it as intended. Both hold. The user-visible
contract changes (log collision, string-ID validation, activation
incompatibility, schema-v4 JSON, exit taxonomy, read-only MCP) are
specified with exact copy and concrete anchors, and every one I could
cross-reference at I0 (`b6f89d7`) matches the implemented behavior, with
the single copy drift in PRD-1. The deliverable's core user value —
truthful, non-overclaiming status for the operator — is delivered
strongly: open/partial counts and every certification the deliverable
does *not* grant are stated plainly and repeatedly. Failure surfaces are
named, recoverable, and non-destructive.

Nothing rises to blocking. PRD-1 (regex-vs-plain-English invalid-ID copy)
and PRD-2 (migration docs absent at I0) are should-fix; PRD-2 is already
gated by the spec to Phase C with a D.1 block, so it is a tracking note
rather than a spec defect. All findings rest on `static-inspection`
(reading the I0 tree via `git show`; no live `pytest`/CLI execution),
which per P5 caps them at should-fix and below — appropriately, since I
found no user-facing regression that would justify a blocker.

**Lens boundaries (not arbitrated here, per P4).** The symlinked
`logs_dir` no-follow gap (X-M1) is reachable at I0 but is an Adversarial
question ("is the failure reachable?"); I record it in §6 only for
failure-visibility completeness and note the spec honestly carries it as
an open Phase C gate rather than claiming closure. Spec-surface
enumeration completeness and compliance-with-approved-docs belong to
Alignment. Whether the malformed-registry / required-version-duplicate
regressions actually cover their failure modes belongs to Peer. I did not
consult any other family's verdict.

**Evidence.** Repo state attested via `git branch --show-current` /
`git rev-parse` / `git ls-files` (direct-run); all implementation-claim
citations via `git show b6f89d7:<path>` (static-inspection). Key anchors:
`ontos/commands/log.py:283–300,334–340`; `ontos/core/schema.py:83–97`;
`ontos/commands/stub.py:183–192`; `ontos/commands/activate.py:80–100,259–292`;
`ontos/core/config.py:239–266`; `ontos/ui/json_output.py:16–49,331–344`;
`ontos/mcp/server.py:191–204`; `docs/reference/Migration_v3_to_v4.md`@I0.
