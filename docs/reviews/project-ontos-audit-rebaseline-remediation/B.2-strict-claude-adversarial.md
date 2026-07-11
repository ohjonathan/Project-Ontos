---
id: audit-rb-B2-ca
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.2
role: adversarial
family: claude
evidence_labels_used: [static-inspection, not-run]
status: completed
---

# Adversarial Review — project-ontos-audit-rebaseline-remediation / B.2 / claude

## 1. Input boundary attestation

The prompt exposed operational preflight (identity, location, frozen SHA pair,
no-touch list), the artifact bytes (spec v1.5 at
`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`), the governing
reproduction statements (`C-phase-falsification-findings.md`), and read access to
frozen I0 `b6f89d7` / base `bf91b42`. No suite outcome, prior-approval, guard-
discharge, coverage-sufficiency, or "spec matches implementation" claim was
supplied as a prefilled fact. The falsification-findings doc is a **reproduction
input** (it states pre-fix observables and required dispositions), not a result
assurance about the spec under review; I treated its "frozen at I1 / focused
verified" column as out-of-scope claims about a snapshot I was not given
(`I1`) and did not rely on them as proof that any spec gate is satisfied. No
prompt-assembly blocker.

Family diversity: author family is `codex` (spec frontmatter); this review is
`claude`. Providers differ — no same-provider adversarial halt.

## 2. Invariant re-derivation

Invariants derived from the spec + frozen diff (not restated author claims):

- **I0 immutability.** Base→I0 (`bf91b42`→`b6f89d7`) is the only diff under
  review; every anchor is a frozen-I0 or current-tree citation, not a promise.
- **Quarantine-before-consumers.** The validator must structurally + type-
  validate every control-plane root/collection/row/field before any index,
  hash, set/Counter, sort, aggregate, normalize, count, lookup, or parity op,
  returning exit `1`/`FAILED` — never exit `2`/`ERROR`, `KeyError`, or
  `TypeError` (§4.1).
- **Program membership is exact.** After quarantine the normalized program
  issue set must equal exactly `#146`–`#157`; downstream child/lease/milestone/
  integration/GitHub consumers use the normalized membership and never
  `KeyError` (§4.1).
- **Eager clause parsing.** Every `required_version` clause is parsed before
  compatibility is reduced; an earlier false comparison may not hide a later
  malformed clause (§4.4).
- **No-follow write boundary.** Every `ontos log` write (document, archive
  marker, `.ontos.lock` for both `SessionContext.commit` and MCP
  `workspace_lock`) is workspace-contained, no-follow, and single-link; nlink
  checks precede any backend sentinel write; entry device/inode/type bindings
  are rechecked immediately before each name-based mutation (§4.3).
- **Exact public string/exit contracts.** ID copy, activation
  code/status/message, exit taxonomy (`0/1/2/3/5/130`, `4` reserved), and the
  Migration guidance anchor are exact and stable (§4.2/§4.4).
- **Nonclaims stand.** Immutable SHA/count/status, external (GitHub/Windows/
  TestPyPI), per-issue, child-lifecycle, D.6, merge, tag, publication, and
  release nonclaims are unchanged (§1/§2/§9).

## 3. Assumption attack

| Assumption | Why it might be wrong | Impact if wrong | Reproduction / proof |
|---|---|---|---|
| Every finding's `root_program` equals its owning program's root, AND the program set is exactly `#146`–`#157` (§4.1) | Finding `R2-control-plane-parity-1` explicitly sets `root_program: project-ontos-audit-remediation-2026-07` / `issue: 158`, a root absent from the 12-program set | An ownership check built literally either fails-closed on the authoritative registry or must silently exempt umbrella-owned rows — the exit-2/`KeyError` class the gate forbids | `git show b6f89d7:manifests/project-ontos-audit-remediation-registry.yaml | sed -n '584,587p'` (explicit umbrella root) vs `sed -n '93,413p' | grep root_program` (programs = #146–#157) |
| Frozen-I0 anchors cited by the spec are accurate | Direct-read miss (M6 pattern) would make gates cite non-existent code | Phase C would implement against fiction | Verified ~15 anchors (see §4/§8); all accurate |
| `required_version` at I0 short-circuits (C-FZ-1) so eager parsing is a real, non-vacuous requirement | Could already be eager | Test would be vacuous | `git show b6f89d7:ontos/core/config.py` line 246 = `return all(_version_clause_matches(...) for clause in clauses)` — lazy `all()`; confirms the reproduction |
| The `logs_dir` symlink regression is reachable, not swallowed by the config guard | config.py:360-363 already rejects outside-configured `logs_dir` before the write boundary | A vacuous config-layer pass | Spec §4.3 pre-empts this: default-path test must prove no explicit `logs_dir` + default symlink resolves outside; configured-path test plants redirect after validation |

## 4. Failure mode analysis

| Failure | How it happens | Would we notice? | Reproduction / proof |
|---|---|---|---|
| Umbrella `#158` KeyErrors a GitHub-parity/ownership consumer | §3 requires parity over issues `#146`–`#158`; §4.1 fixes program membership at `#146`–`#157`; a consumer looking up `#158` in the program map has no key | Only if a regression covers umbrella-owned rows; §4.1/§6 table enumerates missing `#146`/`#147` but not umbrella-owned lookups | Registry parse above; no runnable repro at I0 (ownership/parity-over-membership checks are Phase C additions) → static-inspection, should-fix |
| Required-version test blesses whole-requirement echo instead of clause id | If a test counts a bare substring rather than the quoted repr, echoing the full requirement re-introduces the token | Spec §4.4/§6 counts the clause `literal/repr` (quoted) and requires clause identification, disambiguating from the whole-requirement echo | Non-vacuous as written; no defect |
| Archive-marker exit `3` fires on benign first-run (no `.ontos/`) | If best-effort marker mkdir is treated as "not updated" | Would surface as every fresh `ontos log` returning `3` | Impl detail; `WARNINGS=3` exists at I0 (`json_output.py:20`); marker path is Phase C — no I0 repro |

## 5. Diagram completeness attack

- **Architecture (§10.1)** matches §4: Registry→Validator/Control-Plane→
  O4/O5; Serializer→Writer→CLI/MCP; Activation/Doctor and Locking feed
  contracts; external GitHub/Windows/TestPyPI are dashed. The command registry
  (§4.4, `ontos/command_registry.py`) is not a distinct node but is subsumed in
  the `CLI/MCP Contracts` node — non-blocking (no cited-line contradiction).
- **Lifecycle (§10.2)** matches §2/§4.5: `D5_Verification → Loose_Falsification
  → D6_Pending` stop boundary, D.4 retry edges, and code-first Phase C
  reconciliation node are all present.

No prose/diagram error path is contradicted with cited lines + a reproducible
proof → no blocking diagram mismatch.

## 6. Edge case inventory

Fresh attack-surface derivation (mandatory):

| Attack surface | In scope? | Evidence attempted | Result |
|---|---|---|---|
| Malformed control-plane roots/rows → exit 2/`KeyError` | Yes | Registry parse; C-FZ-3 reproduction; §4.1 quarantine gate | Gate is falsifiable + table-driven; no defect |
| Umbrella `#158` ownership/parity vs exact `#146`–`#157` membership | Yes | Registry parse (`R2-control-plane-parity-1`) | **Should-fix S-1** — spec never reconciles |
| Eager vs lazy `required_version` clause parse | Yes | `config.py:246` lazy `all()` | Reproduction confirmed; gate non-vacuous |
| `logs_dir`/archive-marker/`.ontos.lock` no-follow reachability | Yes | `log.py:115/334-340`, `config.py:360-363`, `mcp/locking.py:24`, `context.py:485-501/645-695` | Anchors accurate; non-vacuity guarded by §4.3 |
| Multi-link lock refusal before backend write | Yes | `mcp/locking.py` plain `open("a+")`; C-FZ-6 | Gap real; gate falsifiable |
| CLI ID divergent regex/copy | Yes | `stub.py:183-192` divergent `_ID_PATTERN` + regex-only string | Reproduction confirmed; canonical-validator gate sound |
| Exact activation/exit string contracts | Yes | `E_ACTIVATION_UNUSABLE`, `Incompatible Ontos version`, `Invalid [ontos].required_version`, `WARNINGS=3`, reserved `4` | All present/accurate at I0 |
| External service behavior (GitHub/Windows/TestPyPI) | No — external blockers, out of local review scope | Workflow anchors only (`ci.yml:139-170`, `publish.yml:74-102/249-320`) | Anchors accurate; service proof correctly left pending |
| Live suite / validator execution | No — instruction bars full-suite run and nested agents | not-run | Not exercised |

## 7. Security surface

- **Path/symlink escape** is the primary surface. Frozen-I0 defects are real and
  cited accurately: `log.py:115` collapses `logs_dir` through `.resolve()`;
  `mcp/locking.py:24` opens `.ontos.lock` with a plain `open("a+")` (no no-follow,
  no nlink check); `context.py:645-654` `_reject_parent_symlinks` uses `lstat`
  per-component. The spec's no-follow/single-link/entry-binding gates target
  exactly these; the anchors are pre-upgrade evidence, not satisfaction claims.
- **Injection/authZ/secret exposure** — not applicable to this review target
  (spec text + frozen filesystem behavior); no new external input surface is
  introduced by the spec itself.
- No secret-bearing content in the artifact under review.

## 8. Issues found

### Blocking (Critical)

None. No finding admits a runnable reproduction of a defect in the spec's
constructions. All frozen-I0 anchors verify; each corrected construction maps to
a reproduced C-FZ-* failure; every gate is falsifiable and non-vacuous by
construction; and the spec is correctly hedged that I0 does not satisfy the
Phase C gates.

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| — | — | — | — | — | — | — |

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| S-1 | The umbrella program `project-ontos-audit-remediation-2026-07` / issue `#158` is simultaneously (a) the explicit `root_program` of finding `R2-control-plane-parity-1`, (b) a required GitHub-parity issue (§3 "Issues #146–#158"), and (c) excluded from the mandated "program issue set must equal exactly `#146`–`#157`" (§4.1). The spec never states how `#158` participates as a finding-owner and parity target while being absent from `programs`. A Phase C validator built literally to "every finding's `root_program` must equal its owning program's root" + "may never raise a `KeyError`" could fail-closed on the authoritative registry or need an undocumented umbrella carve-out — the exact exit-2/`KeyError` class §4.1 forbids. | spec §4.1, §3; `b6f89d7:manifests/project-ontos-audit-remediation-registry.yaml:584-587` vs `:93-413` | static-inspection | `git show b6f89d7:manifests/project-ontos-audit-remediation-registry.yaml | sed -n '584,587p'` shows `root_program: project-ontos-audit-remediation-2026-07`, `issue: 158`; `... | sed -n '93,413p' | grep 'issue:'` shows programs = `#146`–`#157` only | Registry has an umbrella-owned finding whose root is outside the program set; spec asserts universal per-program ownership + exact `#146`–`#157` membership + no-KeyError without reconciling `#158` | Add an explicit clause: the umbrella `#158` is a valid finding-owner and parity target distinct from the child-program membership set, and the ownership/parity consumers must normalize `#158` without KeyError; require a regression covering an umbrella-owned finding row (not only `#146`/`#147` removal). |

### Minor

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| m-1 | §3 dependency copy ("Issues #146–#158 must match registry state") reads as a range inconsistent with §4.1's exact `#146`–`#157` program membership. They reconcile only if the reader infers `#158` = umbrella issue vs `#146`–`#157` = child programs. | spec §3 vs §4.1 | static-inspection | Textual diff of the two clauses | Two nearby clauses use overlapping-but-different issue ranges | State the umbrella-vs-child distinction inline where the ranges appear. |
| m-2 | §4.2 compound citation `direct-read: ontos/core/schema.py:315-343` is attached to "IDs are strings matching the documented ID pattern," but `315-343` is `serialize_frontmatter` (supports the order/serialize claim); the ID-pattern/error copy lives at `83-97` (correctly cited separately). The pattern-definition symbol itself is not at `315-343`. | spec §4.2 | static-inspection | `git show b6f89d7:ontos/core/schema.py | sed -n '315p'` → `def serialize_frontmatter(fm...)` | Anchor supports the serializer half of a compound sentence, not the ID-pattern half | Split the citation so the ID-pattern claim points at the `DOCUMENT_ID_PATTERN`/`validate_document_id` lines. |

## Verdict

Approve

The spec accurately reflects frozen I0 (`b6f89d7`): every load-bearing anchor I
checked — `log.py:283-300/115/334-340`, `config.py:239-266/279-345/360-363`,
`context.py:485-501/645-695`, `core/locking.py:13-81`, `mcp/locking.py:21-27`,
`validate-audit-remediation-registry.py:18-728` (incl. `main()`),
`schema.py:83-97`, `stub.py:183-192`, `json_output.py:16-49`,
`activate.py:85-95`, `ci.yml:139-170`, `publish.yml:74-102/249-320` — is
present and matches the cited behavior. Each corrected construction maps to a
reproduced C-FZ-* failure (lazy `all()`, plain MCP lock open, divergent stub
regex, `.resolve()`-collapsed `logs_dir`), the public string/exit contracts are
exact, and every gate is falsifiable and non-vacuous by construction. No finding
carries a runnable reproduction of a spec defect, so nothing is blocker-grade.
Should-fix S-1 (umbrella `#158` ownership/membership reconciliation) should be
addressed before Phase C so the validator does not resurface the exit-2/`KeyError`
class the gate is meant to eliminate.

## Notes

- Evidence discipline: findings are `static-inspection` (bounded `git show` /
  `git grep` over frozen I0); the full suite, registry validator, and Phase C
  successor code were `not-run` per the review instruction (no full-suite run,
  no nested agents, no implementation edits). Blocker bar (runnable repro /
  orchestrator-preflight) was therefore correctly unmet — no reproduced defect
  exists in the spec's constructions.
- I did not read B.1/B.2 verdicts, receipts, result bundles, test summaries,
  tracker conclusions, or sibling reviews. The `C-phase-falsification-findings.md`
  was used only as the reproduction-statement input named in the prompt.
- Repository state preserved: read-only inspection only; no implementation edit,
  no commit (review-phase worker — orchestrator stages/commits this artifact).
- B.2 approval does not certify Phase C, D.5, any child lifecycle, or a release;
  all immutable SHA/count/status and external nonclaims remain intact.

## Final report — project-ontos-audit-rebaseline-remediation / B.2 / adversarial / claude
- Status: completed
- Artifacts written: docs/reviews/project-ontos-audit-rebaseline-remediation/B.2-strict-claude-adversarial.md
- Smoke checks: frozen-I0 anchor verification = pass (evidence: static-inspection); full suite = not-run (evidence: not-run)
- Cardinality checks: programs #146–#157 = pass; 91 original + 9 R2 = 100 findings = pass (evidence: static-inspection)
- Commit: not committed by worker (orchestrator stages/commits review artifacts)
- Notes: Approve with one should-fix (S-1 umbrella #158 ownership/membership) and two minors; no blocker (no runnable reproduction).
