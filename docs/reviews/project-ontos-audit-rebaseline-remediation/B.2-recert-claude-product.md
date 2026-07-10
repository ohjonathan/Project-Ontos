---
id: project-ontos-audit-rebaseline-remediation-B.2-recert-claude-product
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.2
role: product
family: claude
evidence_labels_used: [static-inspection, direct-run]
status: completed
---

# Product Review — project-ontos-audit-rebaseline-remediation / B.2 / claude

Recertification of corrected spec v1.3 (`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`)
against frozen implementation snapshot I0 `b6f89d77e7fb684b8bd9a181a24c773d5777397a`.
Manifest declares `implementation_sequencing.mode: code-first-user-gated` with
`implementation_ref: b6f89d7` (`manifests/project-ontos-audit-rebaseline-remediation.yaml:13-16`,
direct-run), so §2.2 spec-vs-implementation cross-reference is run against I0 per
Template 19 § 2.2 code-first exception. All I0 citations below are read via
`git show b6f89d77:<path>` (static-inspection of the frozen blob); the branch/commit
and tracked-file attestations are direct-run. The live worktree is on
`codex/audit-rebaseline-remediation-lifecycle` @ `c1047589` with an in-progress
Phase C — its bytes are **not** treated as I0 evidence. No other verdict was consulted.

## 1. User-value assessment

The user here is the **Ontos operator/adopter** who runs the CLI and MCP surface,
plus the **downstream reviewer** who consumes the umbrella lifecycle proof. The job
to be done: adopt a set of deliberately breaking v4.7.1/v4.8.0/v4.9.0 contracts
(semantic-safe YAML, string-only IDs, pinned `required_version`, collision-safe
logging, no-follow writes, exhaustive MCP type counts, a schema-v4 JSON/exit
taxonomy) *without* getting silently corrupted documents, silently-swallowed
failures, or an inability to tell "warning" from "error" in shell automation.

v1.3 solves the real user problem rather than a proxy. It (a) makes every
breaking, user-visible contract a **named, testable** gate with an exact code /
prefix / status, and (b) is scrupulous that these are *specification gates to
implement and verify in Phase C*, not claims the current tree is already green
(§1, §26–28, §13). Crucially for a recert, the spec never rounds the umbrella
review up into a release or a per-issue certification: §2 out-of-scope, §3
external-blocker rows, the "No dependency may be converted into a synthetic
receipt" clause (§3), and §9 exclusions all hold the line. This is the correct
thing to build: it protects the adopter from the exact silent-failure classes the
Fable audit surfaced, and it keeps the review honest about what it does and does
not prove.

## 2. Product-surface cross-reference

### 2.1 Spec-declared user-visible surfaces

Every surface below is a place the operator reads text, sees a state change, or a
machine consumer keys off an exact code. All are declared in the spec with an
exact contract; "gate" = spec marks it "Phase C direct-run required" (not yet
satisfied at I0).

| ID | Surface type | Spec reference | User action that reaches it |
|----|--------------|----------------|-----------------------------|
| S-1 | State + copy + code: incompatible `required_version` | §4.4; §11 row 5 | Activate a project whose `[ontos].required_version` excludes the running version |
| S-2 | Copy + code: invalid `required_version` range | §4.4 | Activate with a malformed range clause |
| S-3 | Copy: invalid document ID (loader) | §4.2; §11 row 2 | Load/serialize frontmatter with a bad `id` |
| S-4 | Copy + code: invalid document ID (CLI) | §4.2, §6 | `ontos stub --id <bad>` |
| S-5 | State + copy + code: log collision | §4.3; §11 row 4 | `ontos log` when the target file exists |
| S-6 | Code: loader batch `parse_error` | §4.2 | Batch-load a doc set containing an invalid ID |
| S-7 | Machine contract: schema-v4 JSON envelope + exit taxonomy (incl. warnings exit `3`, reserved `4`) | §4.4; §11 row 6 | Any `--json` command; any shell caller reading `$?` |
| S-8 | Behavior: read-only MCP omits write tools / refuses export / suppresses usage logs | §4.4; §11 row "Read-only MCP performs no writes" | Start MCP server in read-only mode |
| S-9 | State: workspace-lock / log-parent no-follow fail-closed | §4.3, §4.4; §11 rows 7–9 | Operate with a symlinked/reparse `.ontos.lock` or `logs_dir` component |
| S-10 | Copy/discoverability: Migration + Manual adoption guidance | §7; §11 row "Migration warns…" | Read the docs before adopting `required_version` / exit-`3` semantics |
| S-11 | Copy: malformed `required_version` clause is singular + actionable | §4.4; §11 row "Required-version clause copy…" | Activate with a multi-clause range containing one bad clause |

**Copy completeness at spec time.** The exact leading strings, codes, and statuses
are inventoried and unambiguous: `E_ACTIVATION_UNUSABLE` / `data.status: not_usable`
/ `Incompatible Ontos version` and `Invalid [ontos].required_version` (S-1/S-2);
`Document id must be a string` / `Document id must not be empty` / plain-language
pattern copy (S-3); `E_USER_INPUT` (S-4); `E_LOG_EXISTS` + no-overwrite + recovery
hint (S-5); `parse_error` (S-6); the nine envelope keys and the `0/1/2/3/5/130`
codes with `4` reserved (S-7). Copy *direction* for the two new strings — the log
recovery hint ("choose a different title/slug, or move/remove the existing log
intentionally", §4.3) and the Migration/Manual `required_version` pointer (§4.4,
§7) — is specified semantically and left to Phase C authoring, which is
appropriate for a spec. This satisfies §2.1's copy-completeness bar.

### 2.2 Spec-vs-implementation cross-reference (against I0 `b6f89d7`)

| Spec-declared surface | Present at I0? | I0 evidence | Matches spec's Phase-C framing? |
|---|---|---|---|
| S-1 activation code/status/prefix | Yes | `activate.py:60` `E_ACTIVATION_UNUSABLE`, `:267` `"status": "not_usable"`; `config.py:264` `Incompatible Ontos version:` | Yes — I0 has code/status/prefix; spec gates *adding the Migration/Manual pointer* |
| S-2 invalid-range prefix | Yes | `config.py:260` `Invalid [ontos].required_version {required!r}: {exc}` | Yes — prefix present; pointer is the Phase-C add |
| S-3 loader ID copy | Yes | `schema.py:85-96` string/empty/pattern messages verbatim | Yes — canonical copy already exists |
| S-4 CLI ID copy | **Divergent** | `stub.py:186-189` raises `Invalid --id. Expected ^[A-Za-z0-9]…` (raw regex, does **not** call `validate_document_id`) | Yes — spec §4.2 names this exact anchor as the defect to close in Phase C |
| S-5 log collision | **No recovery hint** | `log.py:289` `Session log already exists: {output_path}`; data `{path}` only | Yes — spec §4.3 gates adding the actionable recovery hint |
| S-7 envelope/exit taxonomy | Yes | `json_output.py:16` schema `"4.0"`; `ExitCode` enum `0,1,2,3,5,130` — `4` intentionally absent | Yes — contract present; spec pins it testable and reserves `4` |
| S-9 lock/log no-follow | Backends present, contract not proven | `ontos/core/locking.py` + `ontos/mcp/locking.py` exist at I0 (tracked) | Yes — spec §4.3/§4.4 gate the no-follow open + both entry points + regressions |
| S-10 Migration/Manual copy | **Absent/partial** | `Migration_v3_to_v4.md:113` mentions the exit taxonomy but names no `required_version` adoption / `E_LOG_EXISTS` / reserved-`4` / warnings-exit-`3` shell-impact copy; `Ontos_Manual.md` has 0 `required_version` mentions | Yes — spec §7 gates this doc copy |
| S-11 singular clause copy | **Duplicated** | `config.py:260` wraps the clause `{exc}` inside `{required!r}`, so a bad clause literal appears in both the requirement repr and the nested `invalid version clause 'x'` | Yes — spec §4.4 gates de-duplication and pins the test to count the clause literal, not the prefix |

No implementation surface exists at I0 that §2.1 fails to name. Every divergence
(S-4, S-5, S-9, S-10, S-11) is exactly the set the spec marks "Phase C direct-run
required" — the spec's inventory and I0 reality agree. No blocking §2.2 mismatch.

## 3. UX-friction inventory

| ID | Flow step | Friction | Severity | Evidence |
|----|-----------|----------|----------|----------|
| U-1 | Adopter adds `[ontos].required_version` before upgrading every runtime | Pre-adoption CLI/hook/CI can reject the key or fail activation, bricking a repo for collaborators | should-fix (mitigated) | Spec §7 mandates an explicit "upgrade + verify repo/PATH/hook/CI runtimes first" warning; mirrors the I0 `allowed_external_dependency_paths` precedent at `Migration_v3_to_v4.md:113` (static-inspection) |
| U-2 | Shell automation reads `$?` after a warnings-only run | Callers that treated every non-zero as a hard error now mis-handle new exit `3` | should-fix (mitigated) | Spec §4.4 + §7 require the doc to call out the warnings-vs-findings-vs-usage distinction (static-inspection) |
| U-3 | Operator hits a log collision | Must know *how* to proceed, not just that it failed | should-fix (mitigated) | I0 message states the fact only (`log.py:289`); spec §4.3 gates the recovery hint (static-inspection) |

All three friction points are on the happy-adoption path and all three are
explicitly mitigated by v1.3 requirements. None is left unaddressed.

## 4. Copy review

| ID | Surface | Current copy (I0) | Issue | Suggested alternative |
|----|---------|-------------------|-------|-----------------------|
| C-1 | CLI invalid `--id` | `Invalid --id. Expected ^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$` (`stub.py:186-189`) | Regex-as-error is engineer-facing; also diverges from the friendlier loader copy — same error, two voices | Spec §4.2 already requires the canonical plain-language message; see PRD-1 on preserving the `--id` locus |
| C-2 | Log collision | `Session log already exists: {output_path}` (`log.py:289`) | States the fact, gives no next step | Spec §4.3 gates "choose a different title/slug, or move/remove the existing log intentionally" — good direction |
| C-3 | `required_version` failures | `Incompatible Ontos version: …` / `Invalid [ontos].required_version …` (`config.py:260,264`) | Correct + honest, but no pointer to *where to learn how to fix* | Spec §4.4/§7 gate a Migration/Manual guidance pointer while preserving the leading prefixes — correct |

Copy direction across v1.3 is honest and user-first (states the true state, avoids
false reassurance, adds actionable next steps). The only substantive copy tension
is C-1 / PRD-1 below.

## 5. Accessibility surface

This is a CLI/MCP product; "accessibility" maps to machine-readability,
localization hooks, and stable non-color signals.

| Concern | Evidence | Severity | Remediation category |
|---|---|---|---|
| Stable machine-readable error identity | Exact `error.code` tokens (`E_ACTIVATION_UNUSABLE`, `E_LOG_EXISTS`, `E_USER_INPUT`, `parse_error`) + fixed exit taxonomy give assistive/automation consumers a non-prose, non-color signal | n/a (satisfied) | localization / machine-contract |
| Structured envelope | Nine-key schema-v4 envelope with separate `status`/`exit_code`/`message`/`warnings`/`error` (`json_output.py`, §4.4) lets non-visual consumers branch without parsing English | n/a (satisfied) | machine-contract |
| Localization of dynamic copy | Recovery hint (S-5) and guidance pointer (S-10) are new English strings; spec does not require i18n but the stable *codes* remain the locale-independent key | minor | localization |

No inaccessible surface is introduced. The code-plus-envelope contract is the
right accessibility primitive for this product.

## 6. Failure-visibility

| Failure path | User-visible signal | Recovery available? | Evidence |
|---|---|---|---|
| Incompatible / invalid `required_version` | Exit `1`, JSON `E_ACTIVATION_UNUSABLE` + `data.status: not_usable` + reason; +doc pointer (Phase C) | Yes — upgrade/fix range; doc pointer gated in §4.4/§7 | `activate.py:60,267`, `config.py:260,264` (static-inspection) |
| Log collision | Exit `1`, `E_LOG_EXISTS`, no overwrite, path (+recovery hint gated) | Yes — recovery hint gated §4.3 | `log.py:289-296` (static-inspection) |
| Invalid document ID (CLI/loader) | `E_USER_INPUT` (CLI) / `ValueError`+`parse_error` (loader) | Yes — copy states the rule | `stub.py:186`, `schema.py:85-96` (static-inspection) |
| Lock / log-parent symlink or reparse | Fail-closed rejection; external sentinel contents+inode unchanged | Yes — refuse & keep going with a different path | Spec §4.3/§4.4 gate the no-follow open + regressions (static-inspection) |
| Warnings-only run | Exit `3`, `status: warnings`, warnings array populated — distinct from findings/usage/internal | Informational — user proceeds knowingly | `json_output.py` `ExitCode.WARNINGS = 3` (static-inspection) |
| Ancillary archive-marker write fails | **Non-fatal, documented policy** — may be silent to the user | Log still written; recovery evidence retained | Spec §4.3 (static-inspection) — see PRD-2 |

Failure-visibility is strong and fail-closed across the load-bearing paths. The
one place a failure can be *quiet* is the best-effort `.ontos/session_archived`
marker; the spec preserves its "documented non-fatal policy" but does not require
the user be told the marker was skipped (PRD-2, should-fix). Per Template 19, I
frame this as "does the user understand the failure?"; whether it is *reachable*
is Adversarial's call and I do not arbitrate.

## 7. Issues found

### Blocking (Critical)
None. v1.3 makes every focus-area user-visible contract (required-version
adoption + guidance, canonical string/YAML ID copy, exact error codes/copy,
actionable log-collision recovery, lock/log/MCP failure visibility, warnings-only
exit `3`, JSON/exit compatibility, documentation discoverability, external
release-evidence wording) testable at spec level, and it does so without claiming
release readiness or per-issue certification. No Product blocker survives.

### Should-fix (Major — degrades UX without blocking ship)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| PRD-1 | Spec §4.2 says the CLI must "surface its message through `E_USER_INPUT`," but §6 pins the test to "message **equality** with the canonical validator." Read literally, strict equality forces the CLI to shed the `--id` locus the operator currently gets (`Invalid --id …`, `stub.py:186`), so a user with several arguments loses which input was rejected. "Surface" and "message equality" are in mild tension. | spec §4.2, §6; I0 `stub.py:183-192` | static-inspection | Compare I0 `Invalid --id. Expected <regex>` (names the flag) vs the canonical `Document id must start and end with…` (does not) | Reconcile the two clauses: require the CLI to *contain/surface* the canonical validator message (allowing an `Invalid --id: <canonical>` locus wrapper) rather than assert full-string equality, so consistency is gained without dropping the input locus. |
| PRD-2 | The ancillary `.ontos/session_archived` marker keeps a "documented non-fatal" failure policy; a user whose marker write is skipped gets no signal, and the spec does not require one. On the happy path this is invisible, which is fine, but a silently-missing archive marker can later read as "archival never ran." | spec §4.3 | static-inspection | `ontos log` where the marker write no-follow-refuses or `OSError`s while the primary log succeeds | Keep the non-fatal policy, but require the retained recovery evidence to include a user-visible (or `warnings[]`) note that the ancillary marker was skipped, so the state is discoverable rather than silent. |

### Minor

| ID | Description | Location | Evidence | Suggested action |
|----|-------------|----------|----------|------------------|
| PRD-3 | New dynamic copy (log recovery hint, `required_version` doc pointer) is English-only; the stable `error.code` tokens remain the locale-independent key, so this is polish, not a gap. | spec §4.3, §4.4, §7 | static-inspection | Note in Phase C that codes — not prose — are the localization anchor. |

## 8. Positive observations

- **Honest gating.** v1.3 repeatedly and explicitly states these are
  "requirements to implement and verify, not claims that the current Phase C
  worktree or its tests already satisfy them" (§28, §13). For a recertification
  whose whole risk is rounding up, this is exactly right, and it matches I0:
  every gated surface (S-4/S-5/S-9/S-10/S-11) is genuinely unsatisfied at
  `b6f89d7`.
- **Exact, machine-first error contracts.** Every user-visible failure carries a
  stable code/prefix/status, and the nine-key schema-v4 envelope with a
  first-class `warnings` exit `3` gives shell and assistive consumers a
  non-prose branch point — the correct accessibility primitive for a CLI.
- **Non-vacuous tests specified for the copy that matters.** The required-version
  test is pinned to count the malformed *clause literal*, not the already-singular
  prefix (§4.4) — a real de-duplication the I0 code exhibits (`config.py:260`) —
  and the CLI-ID and log-collision tests assert the user-facing message, not just
  the exit code.
- **Release honesty.** External evidence (Windows, TestPyPI/PyPI, GitHub parity)
  is worded as explicit pending/blocking state that "may not be converted into a
  synthetic receipt" (§3), and the umbrella review is firewalled from per-issue
  certification and D.6 (§2, §9). The user is never told something shipped that did not.

## Verdict
Approve

## 10. Notes

- Scope: this is a spec-level Product recert. Per Template 19 (v1.2 boundary),
  I did not perform scope/forbidden-path/cardinality checks (mechanical gate +
  Alignment own those) nor enumerate spec surfaces for compliance (Alignment).
  Findings stay on UX/copy/failure-visibility signal.
- Lens boundary: PRD-1 and PRD-2 are framed as "does the user understand / can the
  user recover?" If Adversarial reaches a contradictory failure-visibility finding
  on the same ancillary-marker or lock paths, both stand under P4; I do not
  arbitrate reachability.
- Both should-fix findings are `static-inspection` (spec text + frozen I0 blobs),
  so per P5 they are correctly should-fix, not blocking, and do not gate B.2
  advance on their own. They are copy/spec-wording refinements the Phase A author
  can absorb cheaply; neither changes the Approve.
- Cross-cutting technical consequence (surfaced briefly, depth belongs to
  Peer/Alignment): PRD-1's "contain vs equal" reconciliation is a one-line change
  to the §6 test discipline, not an architecture change.

## Final report — project-ontos-audit-rebaseline-remediation / B.2 / product / claude
- Status: completed
- Artifacts written: docs/reviews/project-ontos-audit-rebaseline-remediation/B.2-recert-claude-product.md
- Smoke checks: I0 anchor verification (git show b6f89d77) = pass (evidence: static-inspection); branch/commit/tracked-file attestation = pass (evidence: direct-run)
- Cardinality checks: single-artifact output = pass (evidence: direct-run) — Product does not run scope/cardinality gates (Template 19 v1.2 boundary)
- Commit: not committed (review-phase worker; orchestrator stages + commits per Template 01)
- Notes: Verdict Approve. Two should-fix Product findings (PRD-1 CLI-ID "surface vs message-equality" copy locus; PRD-2 silent ancillary-marker failure visibility), both static-inspection, non-blocking. §2.2 run against I0 under code-first sequencing; all gated surfaces confirmed genuinely unsatisfied at I0, consistent with the spec's Phase-C framing. No release/per-issue-certification overclaim found.
