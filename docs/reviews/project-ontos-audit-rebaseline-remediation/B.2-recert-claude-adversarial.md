---
id: project-ontos-audit-rebaseline-remediation-B.2-recert-claude-adversarial
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.2
role: adversarial
family: claude
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Adversarial Review — project-ontos-audit-rebaseline-remediation / B.2 / claude

## 1. Input boundary attestation

The prompt exposed only: (a) operational preflight (identity, worktree, frozen
SHA pair, throwaway-checkout permission, the no-current-bytes-as-Phase-C-proof
constraint); (b) the artifact under review — corrected spec v1.2 and the frozen
diff `bf91b42…b6f89d7`; (c) governing references (the spec itself, review
templates 01/02/05). No suite outcome, prior approval, guard-discharge,
coverage-sufficiency, or "implementation matches spec" claim was handed to me as
a prefilled fact. I did not read any sibling verdict, receipt, or green-result
summary. Boundary is clean; no prompt-assembly blocker.

Author family is `codex` (spec frontmatter); this adversarial family is `claude`
— cross-provider, so the v1.2 family-diversity invariant is satisfied and this is
strict (non-fallback) adversarial evidence.

## 2. Invariant re-derivation

Re-derived from spec §§2, 4.1, 4.3, 4.4, 7 and the frozen I0 code, independent of
author claims:

- **INV-1 (malformed-registry closure, §4.1).** For **any** finding row missing
  **any** required field, the validator must yield *collected* `missing fields`
  errors and a non-zero exit **at every direct-subscript site** — never surfacing
  a bare key fault instead of the collected list. Regressions must cover ≥2
  distinct omissions (`id`, `issue`), and duplicate-ID analysis must skip
  missing/`None` IDs rather than report `[None]`.
- **INV-2 (reachable log-parent no-follow, §4.3).** Log creation must reject a
  symlinked `logs_dir` component using the same anchored no-follow parent pin as
  `SessionContext`, **before and without collapsing the path through
  `.resolve()`**. The regression must exercise a *config-contained* path (not one
  rejected by config) and prove an outside-workspace sentinel is unchanged.
- **INV-3 (singular invalid-clause copy, §4.4).** A malformed `required_version`
  clause must appear **once** in one actionable message.
- **INV-4 (status/lifecycle independence, §4.1/§2).** Registry status and
  lifecycle state are independent; the umbrella I0 commit does not retroactively
  certify per-issue leases; 41 open / 7 partial states are preserved.
- **INV-5 (public-contract fidelity, §§4.2/4.4/7).** Cited ID/version/exit copy
  and patterns must match I0 code, and Phase-C migration/manual copy must document
  them; drift blocks D.1.

## 3. Assumption attack

| Assumption | Why it might be wrong | Impact if wrong | Reproduction / proof |
|------------|------------------------|-----------------|----------------------|
| The §4.1 enumerated "current sites" list is the complete inventory of direct-subscript sites Phase C must harden | The list omits reachable direct subscripts: `row["issue"]` at 348/369/622 and `row["severity"]` at **404** | A site-by-site Phase-C fix that follows the list literally leaves `severity`-omission unprotected | direct-run, see X-1 |
| The mandated regression floor (`id`, `issue`) forces protection of all directly-subscripted required fields | Only `id` and `issue` are directly subscripted *and* regression-forced; `severity` is directly subscripted at 404 but has no mandated omission test | Named test `…_collected_without_traceback` can go green while `severity`-omission still bypasses the collected-fields path | direct-run, see X-1 |
| A "reported once" test proves INV-3 | The already-singular token at I0 is the `Invalid [ontos].required_version` **prefix**; the *duplicated* token is the clause literal (`'garbage' 'garbage'`) | A test asserting `count(prefix)==1` passes on unfixed code — vacuous | direct-run, see X-2 |
| INV-2's "config-contained path" and "outside-workspace sentinel" are jointly realizable as written | `_validate_path` uses `.resolve()`; a symlink resolving outside is rejected by config, one resolving inside has no outside target | A literal reading yields a vacuous rejection test unless the no-follow pin + plant-timing is spelled out | static-inspection, see M-1 |

## 4. Failure mode analysis

| Failure | How it happens | Would we notice? | Reproduction / proof |
|---------|----------------|------------------|----------------------|
| `severity`-missing row raises `KeyError` at un-enumerated site 404, bypassing collected `missing fields` | Per-row loop collects `missing` but does **not** `continue`; no `return errors` exists between the loop (224) and final return (694); first direct `row["severity"]` subscript is line 404 | Only if a `severity` regression exists — spec mandates none; named test covers `id`/`issue` only | X-1 (direct-run traceback) |
| Named `…_reported_once` test green on unfixed code | Test asserts on the `Invalid [ontos].required_version` prefix (already count 1) instead of the doubled clause literal | Prefix count is 1 even at I0 | X-2 (direct-run) |
| Log-symlink regression passes because config rejected the path, never exercising the no-follow pin | Symlinked `logs_dir` resolving outside is rejected by `_validate_path`; test asserts non-zero exit and mis-attributes it | Spec warns against it but leaves the non-vacuous construction implicit | M-1 (static-inspection) |

## 5. Diagram completeness attack

§10.1/§10.2 diagrams cover the control-plane, writer, contract, and lifecycle
retry/fail edges (`D3→D4`, `D5→D4`, `Loose_Falsification→D4`) and mark the three
external boundaries (GitHub / Windows / TestPyPI). No prose error path is missing
from the diagrams that I could reduce to a cited-line reproducible mismatch. No
blocking diagram finding.

## 6. Edge case inventory

- Finding row missing `severity` only (has `id`, `issue`, `origin: fable_audit`)
  → reaches line 404 → `KeyError` (X-1).
- Two rows both missing `id` → `Counter([None,None])` → `duplicate registry IDs:
  [None]` unless skipped (INV-1 `[None]` clause; current I0 uses `.get("id")` at
  219 so the `[None]` risk is real and the spec correctly names it).
- `required_version` with one malformed clause (`foo`, `garbage`, `~4.7.8.9`,
  `4.x.y.z`) → clause literal doubled in message (X-2).
- Empty inner clause (`>=4.7.0, , <5.0.0`) → different message shape ("valid
  semver range", clause not echoed) — INV-3 message-shape divergence noted under
  X-2.
- Symlinked `logs_dir` planted after config-load vs. resolving-inside vs.
  resolving-outside (M-1).

## 7. Security surface

The relevant surface is filesystem escape via symlinked `logs_dir` (INV-2). At I0,
`create_session_log` collapses the path through `.resolve()` at
`ontos/commands/log.py:115` and `_write_log_exclusively` does
`parent.mkdir(parents=True, exist_ok=True)` then `open("x", …)` with no no-follow
pin (`ontos/commands/log.py:334-340`, frozen `git show b6f89d7`), so I0 follows a
symlinked parent — the defect the spec targets is genuinely present. The §4.3
requirement is otherwise soundly specified; my only concern is regression vacuity
(M-1), not the fix direction. No injection/authZ/secret surface is introduced by
the reviewed change.

## 8. Issues found

### Blocking (Critical)

None. No finding reaches an uncaught traceback at the user surface at I0 (main()'s
`except Exception → exit 2` catches subscript faults), and INV-5 fidelity checks
passed, so nothing clears the blocker bar.

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| X-1 | §4.1's operative anchors permit a vacuous pass against INV-1's universal clause: the enumerated site list omits the reachable `row["severity"]` subscript at line 404 (and `row["issue"]` at 348/369/622), and the mandated omission set (`id`,`issue`) does not force a `severity` case. A spec-conformant Phase C can green the named test while a `severity`-missing row bypasses the collected-`missing fields` path and falls to the generic `except Exception → exit 2` (`ERROR: 'severity'`). | spec §4.1 + §11 anchor `scripts/validate-audit-remediation-registry.py:219-223,244-286,338,372-387,632,656-661`; actual crash `…:404` | direct-run | throwaway detached I0 (`git worktree add --detach … b6f89d7`); drop `severity` from one `origin: fable_audit` row; call `validate(False)` → `KeyError: 'severity'` at line 404 (`min((row["severity"] for row in rows), …)`) | Expected: collected `… missing fields: ['severity']` + exit 1. Observed: `KeyError`/`ERROR: 'severity'` exit 2, no row context | Either complete the enumeration (add 348/369/404/622), OR mandate a row-level skip (`continue` + filter malformed rows out of `findings`/`original` before all downstream comprehensions), OR add `severity` to the mandated omission regressions. Prefer the row-level skip so INV-1's universal clause holds by construction. |
| X-2 | INV-3's named test `test_invalid_required_version_clause_is_reported_once` can pass vacuously: the `Invalid [ontos].required_version` prefix is already singular at I0, while the token actually duplicated is the clause literal. | spec §4.4 anchor `ontos/core/config.py:239-266,279-345`; test `tests/core/test_config_phase3.py::test_invalid_required_version_clause_is_reported_once` | direct-run | throwaway I0; `required_version_incompatibility(">=4.7.0, garbage, <5.0.0","4.7.1")` → `…: version clause 'garbage' 'garbage' is not a valid semantic version`; prefix `count==1` (already), clause `'garbage'` `count==2` | Expected: assertion pins the *clause token* to count 1. Risk: a prefix-count assertion is true even unfixed | Spec should require the regression to assert the malformed **clause literal** appears exactly once (e.g., `msg.count(clause)==1`), not the prefix; and reconcile the empty-inner-clause message shape (`>=4.7.0, , <5.0.0` echoes no clause) with the "each malformed clause appears once" wording. |

### Minor

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| M-1 | INV-2's regression recipe leaves the non-vacuous construction implicit: "config-contained path… not rejected by config" and "prove an outside-workspace sentinel is unchanged" are only jointly realizable via no-follow rejection of an inside-resolving symlinked component (with a separate outside sentinel dir) or a plant-after-config-load ordering, because `_validate_path` `.resolve()`s and rejects any `logs_dir` that resolves outside. A literal reading risks a test that config-rejects the path and never exercises the log no-follow pin. | spec §4.3; `ontos/core/config.py:128-135` (`_validate_path` uses `.resolve()`), guard cite `…:360-363` | static-inspection | Read frozen `git show b6f89d7:ontos/core/config.py` `_validate_path` — `resolved = (repo_root/path_str).resolve(); return resolved.is_relative_to(repo_root)` | Expected: spec pins how the symlink both survives config and would redirect the write | Add one sentence to §4.3 fixing the construction (inside-resolving symlinked component + outside sentinel, OR symlink planted between config-load and write) so the named test cannot be written vacuously. |

## Reachability gaps

- The `row["issue"]` subscripts at **348/369/622** are un-enumerated but are, in
  practice, protected by the mandated `issue`-omission regression: an
  `issue`-missing row runs the whole validator, so any unfixed `issue` subscript
  crashes the test. They are therefore *forced* by the regression floor and are
  **not** an independent gap.
- The `row["severity"]` subscript at **404** is the one directly-subscripted
  required field that is **both** un-enumerated **and** unforced by any mandated
  regression — this is the genuine gap driving X-1.
- I could construct a reaching input for every §4.1 rule I attacked; no rule was
  unreachable end-to-end.

## Fresh attack-surface table

| Attack surface | In scope? | Evidence attempted | Result |
| --- | --- | --- | --- |
| Malformed registry row, every required field, every subscript site | Yes | direct-run on throwaway I0 (`id`/`issue`/`severity` omissions) | Gap on `severity`@404 → X-1 |
| Duplicate-ID `[None]` reporting | Yes | static-inspection of `…:219` (`.get("id")`→`None`) | Spec correctly requires skip; no new finding |
| `required_version` malformed-clause copy | Yes | direct-run of frozen `required_version_incompatibility` | Real duplication + test-vacuity → X-2 |
| Log-symlink no-follow reachability | Yes | direct-read of `log.py:115,334-340` + `config._validate_path` | Fix direction sound; regression-vacuity → M-1 |
| Status/lifecycle independence (committed-but-uncertified) | Yes | static-inspection of validator status/count pinning (268-333) | Exact per-status count pins block cross-bucket flips; no reproducible transition escape — no finding |
| Public-contract fidelity (ID copy/pattern, exit taxonomy) | Yes | direct-read of `schema.py:78-97,315`, pattern literal | Copy + regex match spec §4.2 exactly — no drift |
| Migration/manual copy | Partial — Phase-C deliverable, absent at I0 | static-inspection of §7 requirement list | Correctly deferred to Phase C; blocks D.1 per spec — no finding |
| Serializer round-trip / writer commit internals | Out of scope | — | Not attacked; no reachable spec-anchor defect surfaced in the targeted pass |

## Verdict

Request changes

Two Major should-fix findings (X-1, X-2) show the spec's operative anchors for two
of its three headline Phase-C gates permit vacuous passes against their own
universal requirements — a `severity`-missing registry row escapes the
collected-`missing fields` contract at un-enumerated line 404, and the
`…_reported_once` version test can green on unfixed code. Both are direct-run
reproduced and cheaply corrected at the spec layer before Phase C. No blockers:
public-contract fidelity holds, the log-symlink and status/lifecycle designs are
sound, and no user-surface uncaught traceback exists at I0. Tighten §4.1 (complete
the site inventory or mandate a row-level skip; add `severity` coverage), §4.4
(assert on the clause token), and §4.3 (M-1 construction) and the deliverable is
clear to proceed.

## Notes

- Evidence produced against frozen bytes only: `git show b6f89d7:…` and a
  clearly-identified throwaway detached I0 worktree (`git worktree add --detach
  /tmp/b2-i0-throwaway b6f89d7`, removed after use). Current worktree Phase-C bytes
  were not used as proof of any gate.
- Standalone-module import was used for `config.py`/the validator to bypass the
  package `__init__` chain (`tomli_w` absent in this environment); this affects
  only import mechanics, not the reproduced behavior.
- Adversarial family `claude` differs in provider from author `codex`; strict-P3
  adversarial evidence, no fallback labeling applied.
