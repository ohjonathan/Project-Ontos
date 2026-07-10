---
id: project-ontos-audit-rebaseline-remediation-B.1-recert-claude-adversarial
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: adversarial
family: claude
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Adversarial Review — project-ontos-audit-rebaseline-remediation / B.1 (recert) / claude

Independent Claude adversarial recertification of spec v1.2 (`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`) and the frozen implementation diff `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95..b6f89d77e7fb684b8bd9a181a24c773d5777397a` (I0). Author family is `codex`; reviewer provider `claude` differs, so the v1.2 adversarial family-diversity invariant is satisfied (no same-provider halt). No other reviewer verdict, receipt, approval, or orchestrator conclusion was consulted.

## 1. Input boundary attestation

The dispatch exposed only: operational preflight (identity, paths, the SHA pair), the reviewable spec bytes, and the frozen diff. No suite-outcome, prior-approval, guard-discharge, coverage-sufficiency, or "implementation matches spec" claim was pre-supplied as fact. The spec's own §11 evidence labels (`direct-run` / `Phase C direct-run required`) are part of the artifact under review and are therefore treated as falsifiable claims, not prefilled facts. No prompt-assembly blocker.

**Scope discipline note (material to every finding below).** The working tree at review time is at HEAD `5e04094` with uncommitted post-I0 edits (`M scripts/validate-audit-remediation-registry.py`, `M manifests/...registry.yaml`, the "Authorize Phase C registry regression" churn). Those bytes are **outside** the frozen review scope. Every direct-run below was executed against a throwaway detached worktree checked out at the frozen I0 commit `b6f89d7` (`git worktree add --detach /tmp/ontos-i0 b6f89d7`), installed into an isolated venv outside the repo. Running the validator at HEAD *fails* (O4 lifecycle-state drift); running it at I0 *passes*. Reporting the HEAD failure as an I0 blocker would have been a false positive, so it is excluded.

## 2. Invariant re-derivation

Re-derived from spec §§2–4, §8, §11 and the diff, independent of author claims:

- **INV-1 (P0 corruption).** `serialize_frontmatter(mapping)` must round-trip to a semantically equal mapping or fail closed — never silently emit YAML that reparses differently (§4.2, §8, §11).
- **INV-2 (writer containment).** `SessionContext.commit` must never create/replace a file outside the workspace root, through a symlinked parent component, or onto a symlink destination (§4.3, §11).
- **INV-3 (log fail-closed).** Log creation must refuse a collision (`E_LOG_EXISTS`, no overwrite) and must reject symlinked `logs_dir` components without collapsing the path through `.resolve()` (§4.3, §11).
- **INV-4 (validator fail-closed).** A finding row missing any required field must produce collected `missing fields` errors and a non-zero exit at every direct-subscript site — never an uncaught `KeyError` — and duplicate-ID analysis must skip `None` IDs (§4.1).
- **INV-5 (non-overclaim).** The umbrella review must preserve the 41 `confirmed_open` + 7 partial states and the shared-tree release blocker; it must not certify per-issue lifecycle, D.6, tag, publish, merge, or release readiness (§2, §8, §9).

Spec self-classification of proof state: INV-1/-2/-3(collision)/-5 are asserted **already proven** (`direct-run` in §11); INV-3(symlink)=X-M1 and INV-4=X-M2 are asserted **pending Phase C** (`Phase C direct-run required`). The adversarial question is whether the "proven" set survives attack and whether the "pending" set is honestly, not deceptively, disclosed.

## Fresh attack-surface derivation

| Attack surface | In scope? | Evidence attempted | Result |
| --- | --- | --- | --- |
| Serializer semantic round-trip (INV-1) | Yes | direct-run, 15 adversarial inputs at I0 | Holds; fail-closed |
| Writer symlink / outside-root escape (INV-2) | Yes | direct-run, 3 escape vectors + control at I0 | All rejected; control passes |
| Log collision refusal (INV-3) | Yes | direct-run at I0 | Refused; content intact |
| Log `logs_dir` symlink escape (X-M1) | Yes | direct-run at I0 | Escape reproduced; matches spec disclosure |
| Validator malformed-row `KeyError` (X-M2) | Yes | direct-run at I0 | `KeyError` reproduced; matches spec disclosure |
| Registry cardinality / status parity (INV-5) | Yes | direct-run validator + parse at I0 | 100 findings, 41 open/7 partial, blocker preserved |
| Late direct-subscript reachability (632/656–661) | Yes | static-inspection | Defense-in-depth only under `--require-external-parity` |
| Windows lock backend, TestPyPI/PyPI, live GitHub parity | No — external | not-run | Spec keeps these as explicit external pendings, not certified |
| required-version single-clause copy | No — pending Phase C, low corruption risk | static-inspection | Disclosed as Phase C gate; not attacked |

## 3. Assumption attack

| Assumption | Why it might be wrong | Impact if wrong | Reproduction / proof |
|------------|------------------------|-----------------|----------------------|
| §11 "Semantic YAML round trip" is proven | Date-like IDs, `null`/`yes` scalars, colons, hash-leading, multiline, unicode, commas-in-list could mis-serialize | P0 silent corruption | direct-run: 15 inputs serialize+reparse equal; mismatches would raise via `assert_frontmatter_roundtrip`. All `OK`. |
| §11 "Workspace-contained exclusive commit" is proven | `.resolve()`-style trust or lexical-only checks could let a symlink parent/destination escape | P1 write outside root | direct-run: symlinked-dir parent → `ValueError ...symlinked directory`; symlink destination → `...must not be a symlink`; absolute outside → `...outside the workspace`; legit inside-root write succeeds (non-vacuous control). |
| §11 "Log collision refusal" is proven | Exclusive-create could be bypassed / overwrite | Lost session log | direct-run: second `_write_log_exclusively` → `FileExistsError`; first content intact. |
| Registry is the sole, machine-enforced status authority | Validator could pass while 41-open/7-partial silently collapsed | Overclaim of closure | direct-run at I0: `PASS`, `confirmed_open=41, partial_uncommitted=7`; `shared_tree_integration.release_blocking is True`. |

## 4. Failure mode analysis

| Failure | How it happens | Would we notice? | Reproduction / proof |
|---------|----------------|------------------|----------------------|
| Log written outside workspace (X-M1) | `ontos/commands/log.py:115` `logs_dir = (root/logs_dir).resolve()` collapses an intermediate symlink; `_write_log_exclusively` then `mkdir`+`open("x")` at the collapsed target | Yes — spec §4.3/§11 discloses it as an open Phase C gate | direct-run at I0: `docs/logs → OUTSIDE`; resolved path escapes root; exclusive create lands in `OUTSIDE/`. Genuinely pending, **honestly disclosed** — not an overclaim. |
| Validator crashes on malformed registry (X-M2) | I0 keeps all rows in `findings` (no `if missing: continue`); line 244 `{row["id"]: row for row in findings if row.get("origin")=="fable_audit"}` direct-subscripts `id` | Yes — spec §4.1/§11 discloses it as an open Phase C gate | direct-run at I0: a dict row with `origin: fable_audit` and no `id` raises uncaught `KeyError: 'id'`. Matches spec's cited sites (`...:244-286` et al.). Genuinely pending, **honestly disclosed**. |
| Registry passes but hides non-closure | Status/lifecycle conflated, or blocker flag dropped | Yes | direct-run: severity totals `P0=1,P1=27,P2=63`, 91+9 cardinality enforced, release blocker asserted `True`. No collapse path found. |

## 5. Diagram completeness attack

§10.1 (architecture) marks the three external boundaries (`GitHub`, `Windows Runner`, `TestPyPI/PyPI`) as dashed external nodes, consistent with §3/§8 external-pending prose. §10.2 (lifecycle) shows the D2↔D4 retry loop, the D.5→Loose-Falsification→D6_Pending path, and a `[*]` stop boundary annotated "no release claim" — matching the §2/§9 non-closure prose. No prose error-path (collision, symlink rejection, activation-incompat) is a *lifecycle state*, so their absence from the state diagram is not a mismatch. No blocking diagram/prose divergence found.

## 6. Edge case inventory

Exercised at I0 (direct-run): empty list value, nested mapping with colon, leading-zero/numeric-like/`null`/`yes` string scalars, tab/quote/`@`/`#`-leading values, unicode, commas inside list items (INV-1); symlinked parent, symlink destination, absolute-outside, and legit-inside (INV-2); double-create collision (INV-3); missing-`id` and (by construction) missing-`issue` rows (INV-4). Not exercised (out of scope / external): Windows `msvcrt` lock path, real TestPyPI download, live GitHub checklist parity — all correctly held as external pendings by the spec rather than certified.

## 7. Security surface

- **Path/symlink escape (writer):** INV-2 attack surface closed at I0 — lexical `os.path.abspath` containment + per-component `os.lstat` no-follow rejection + `dir_fd` anchoring with `follow_symlinks=False` + `st_dev/st_ino` TOCTOU recheck (`_verify_anchor_binding`). Escapes rejected under direct-run.
- **Path/symlink escape (log command):** X-M1 open at I0 (`.resolve()` collapse), but confined to the `ontos log` path, disclosed, and gated to Phase C. Not an undisclosed vector.
- **Injection / deserialization:** serializer uses safe YAML dump + mandatory reparse-equality gate; no `eval`/unsafe-load path in the reviewed serializer surface.
- **Privilege/OIDC, publish provenance:** static workflow assertions only; spec correctly keeps service behavior (TestPyPI/PyPI, tag-run) external-pending, so no local certification of publish security is claimed.

## 8. Issues found

### Blocking (Critical)

None. No reproducible defect contradicts a claim the spec asserts as proven. The two reproduced defects (X-M1, X-M2) are the spec's own explicitly-disclosed, Phase-C-gated open items; the spec's already-`direct-run` invariants (INV-1/-2/-3-collision/-5) survive adversarial direct-run.

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| — | — | — | — | — | — | — |

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| X-SF1 | X-M2 late direct-subscript guards (`632`, `656–661`) are only reachable under `--require-external-parity` and after every earlier per-row guard. Once Phase C adds an early `if missing: continue` (as INV-4 requires), a malformed row can no longer reach these lines, so a Phase C regression that claims to "exercise" them there would be a **vacuous negative control**. | `scripts/validate-audit-remediation-registry.py:632,656-661` (I0) | static-inspection | Read I0 `validate()`: rows are only subscripted after the missing-field loop; the external-parity block is entered only with `--require-external-parity`. No malformed row survives to 656 once early-skip lands. | Guard looks like coverage but the input can't reach it post-fix | In the X-M2 regression, assert the crash is prevented at the *first reachable* subscript (line 244/338) and label 632/656–661 as defense-in-depth; don't let §4.1's "every direct-subscript site" be discharged by an unreachable-input test. |

### Minor

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| X-M-a | Corroboration: X-M1 symlink escape is real at I0 and confined to `ontos log`. | `ontos/commands/log.py:115,334-340` | direct-run | Symlink `docs/logs → OUTSIDE`; `(root/'docs/logs').resolve()` escapes root; exclusive create writes into `OUTSIDE/`. | Escapes workspace vs anchored no-follow | None for B.1 — already an INV-3/X-M1 Phase C gate; confirms the disclosure is accurate, not overstated. |
| X-M-b | Corroboration: X-M2 `KeyError` is real at I0; and I0 line 219 `ids=[row.get("id") ...]` would report `[None]` for two id-less rows, exactly the case §4.1 tells Phase C to skip. | `scripts/validate-audit-remediation-registry.py:219,244` (I0) | direct-run | Dict row `{origin: fable_audit}` with no `id` → `KeyError: 'id'` at line 244. | Uncaught traceback vs collected `missing fields` | None for B.1 — already the X-M2 Phase C gate; the spec's `None`-skip clause is warranted. |

## Verdict

Approve

The B.1 recertification target — spec v1.2 plus the frozen I0 diff — is a sound and honest closeout-proof design. Under independent adversarial direct-run against the frozen snapshot, every invariant the spec asserts as already proven (serializer semantic round-trip with fail-closed equality gate, workspace-contained no-follow writer with a non-vacuous control, log-collision refusal, and the registry as machine-enforced status authority preserving 41 open / 7 partial and the release blocker) survives attack. The two reproducible defects (X-M1 log symlink escape, X-M2 validator `KeyError`) are the spec's own explicitly-disclosed, correctly-cited, Phase-C-gated open items — the disclosure is accurate, not an overclaim, and B.1 approval explicitly does not discharge them. No reproducible finding rises to blocker; the single should-fix (X-SF1) is a reachability caution for the Phase C X-M2 regression, not a spec defect.

## Notes

- Evidence base: all `direct-run` findings executed against detached worktree at `b6f89d7` (I0), isolated venv (`/tmp/ontos-recert-venv`), reviewer host; `static-inspection` for reachability of external-parity-only code paths.
- The throwaway I0 worktree and venv live outside the repo; no repo file other than this artifact was written. Post-I0 HEAD working-tree churn was deliberately excluded from scope.
- External surfaces (Windows lock runners, TestPyPI/PyPI tag-run, live GitHub parity) were not run and are correctly held by the spec as explicit external pendings rather than certified — consistent with the umbrella non-closure posture.
- Verdict is independent (no other lens consulted); `Approve` rather than `Concur` for that reason.
