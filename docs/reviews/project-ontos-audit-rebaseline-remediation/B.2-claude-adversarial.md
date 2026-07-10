---
id: project-ontos-audit-rebaseline-remediation-B.2-claude-adversarial
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.2
role: adversarial
family: claude
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Adversarial Review — project-ontos-audit-rebaseline-remediation / B.2 / claude

Blind review of corrected spec v1.1 (`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`)
and the frozen integration diff `bf91b42…b6f89d7` (I0). Attestation:

```
git branch --show-current -> codex/audit-rebaseline-remediation-lifecycle
git rev-parse HEAD         -> 536784230d658b42932363693a3ed00abe0e6326
```

The three Phase C target files are byte-identical between I0 (`b6f89d7`) and the
worktree HEAD (`git diff --quiet b6f89d7 HEAD -- <file>` = 0 for
`scripts/validate-audit-remediation-registry.py`, `ontos/commands/log.py`,
`ontos/core/config.py`), so direct-run against the worktree observes the I0
behavior under review. Provider check: author family `codex`, adversarial family
`claude` — cross-provider, no same-provider halt.

## 1. Input boundary attestation

The prompt exposed operational preflight, the spec v1.1 bytes, and the frozen
SHA pair only. No suite outcomes, prior approvals, guard-discharge, or coverage
claims were injected as prefilled facts. The spec's own §1 "B.1 incorporation
note" references a prior B.1 approval, but that text is content of the artifact
under review, not an orchestrator-asserted correctness fact; it explicitly
disclaims discharging the Phase C requirements, which I treated as the contract
to attack. No prompt-assembly blocker.

## 2. Invariant re-derivation

From spec §§4.1/4.3/4.4 + diff, the re-derived Phase C invariants:

- **I-REG**: the registry validator must convert *any* malformed finding row
  into a collected validation error and a non-zero exit — never an uncaught
  `KeyError` traceback (§4.1; validator is the "sole status authority", §11).
- **I-LOG**: log creation must not write outside the workspace root through a
  symlinked `logs_dir` component; a regression must prove an outside-workspace
  sentinel is unchanged (§4.3, X-M1).
- **I-VER**: `[ontos].required_version` invalid ranges emit exactly one
  actionable message beginning `Invalid [ontos].required_version`; skew emits
  `Incompatible Ontos version`; each malformed clause appears once (§4.4).
- **I-ID**: document IDs are strings matching
  `^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$` with the three fixed messages
  (§4.2).

I-VER and I-ID are re-derived and then verified against the frozen code below;
both citations are accurate. I-REG and I-LOG are the attack surfaces where the
requirement's *scope* — not its direction — is defective.

## 3. Assumption attack

| Assumption | Why it might be wrong | Impact if wrong | Reproduction / proof |
|------------|------------------------|-----------------|----------------------|
| X-M2 = "a row missing `id` KeyErrors at 244-285" fully bounds the defect | `id` is one of 12 `REQUIRED_FINDING_FIELDS`; `row["id"]`/`row["issue"]` are subscripted at 6+ sites, several outside 244-285 | A Phase C fix + regression scoped to the literal requirement still crashes on other malformed rows, and the §6 "malformed registry rows" test can pass vacuously | direct-run `/tmp/repro_xm2.py` — see SF-1 |
| X-M1 lives entirely in `log.py` and a symlinked `logs_dir` is otherwise unguarded | `config._validate_path` already rejects an *explicitly-configured* `logs_dir` that resolves outside root, but skips **default** paths and re-`.resolve()`s | The obvious Phase C regression (configure an outside symlink `logs_dir`) is caught at config load and never reaches log.py — vacuous pass; the real reachable vector is the default `docs/logs` path | direct-run `/tmp/repro_xm1.py` + `/tmp/repro_xm1b.py` — see SF-2 |
| "reject every symlinked component" can be checked after computing `logs_dir` | line 115 does `(root / logs_dir).resolve()`, collapsing symlinks before any check sees them | A no-follow check placed after `.resolve()` is blind and passes on a traversed symlink | static-inspection, `ontos/commands/log.py:115` |

## 4. Failure mode analysis

| Failure | How it happens | Would we notice? | Reproduction / proof |
|---------|----------------|------------------|----------------------|
| Validator crashes with traceback on a finding row missing `issue` | `program_by_issue`/count map subscript `row["issue"]` at line 338 et al.; missing-fields error is collected but execution continues to the subscript | Only as a raw traceback; exit is non-zero so registry does not falsely validate (fail-closed) | `/tmp/repro_xm2.py` scenario B → `KeyError: 'issue'` at `validate-audit-remediation-registry.py:338` |
| `ontos log` writes outside the workspace | default `logs_dir="docs/logs"`; attacker makes `docs` a symlink to an outside dir; config skips `_validate_path` for defaults; line 115 `.resolve()` follows it; `_write_log_exclusively` mkdir+`open("x")` writes to target | No — command reports success with an outside path | `/tmp/repro_xm1b.py` → file created at `…/OUTSIDE_*/logs/2026-07-10_escape-probe.md` |
| Phase C X-M1 regression passes without exercising log.py | test configures `logs_dir` to an outside symlink; `dict_to_config` raises `ConfigError` at config.py:363 before log.py runs; test sees "rejected" and passes | No — green test, unexercised guard | `/tmp/repro_xm1.py` → `ConfigError: paths.logs_dir must resolve within repository root` |

## 5. Diagram completeness attack

§10.1 architecture and §10.2 lifecycle diagrams enumerate the writer→CLI/MCP,
validator→ledger/leases, external GitHub/Windows/TestPyPI boundaries, and the
D.5→loose-falsification→D.6 stop boundary. The failure/retry edges
(`D3→D4`, `D5→D4`, `Loose_Falsification→D4`) are present. No prose error path is
missing from the diagrams at a blocking level.

## 6. Edge case inventory

- Finding row missing `id` (→ KeyError 244), missing `issue` (→ KeyError 338),
  non-dict row (handled), duplicate missing-`id` rows (→ `duplicate registry
  IDs: [None]`, M-1).
- `logs_dir` default path with a symlinked intermediate component (escapes);
  explicitly-configured outside symlink (blocked at config load).
- `required_version`: `>= , <5` (empty clause), `4.x.5` (wildcard+trailing
  digit), `>=99.0.0` (skew) — all produce the correct public prefix; inner copy
  duplicates the clause (M-2, matches §4.4 requirement).
- Date-like/`null`/numeric IDs: regex accepts `2026-07-10` as a *string*, but
  YAML auto-parses unquoted scalars to non-strings that fail `validate_document_id`
  — §7 migration copy correctly must instruct quoting.

## 7. Security surface

Path traversal is the material surface. X-M1 is a real workspace-escape write
(direct-run confirmed) reachable via the default `docs/logs` path; it is
fail-open (reports success at an outside location), so the §4.3 requirement is
warranted. No new authN/authZ, injection, or secret-exposure surface introduced
by the spec's Phase C requirements themselves. Read-only-MCP no-write (§4.4) is
an in-scope guard I did not fully exercise (see Reachability gaps).

### Attack surface derivation

| Attack surface | In scope? | Evidence attempted | Result |
| --- | --- | --- | --- |
| Registry validator malformed-row handling (X-M2) | yes | direct-run repro | KeyError class wider than requirement (SF-1) |
| Log write symlink escape (X-M1) | yes | direct-run repro (two vectors) | Escape via default path; config-guard-shadowed vector is vacuous (SF-2) |
| Required-version invalid-clause copy | yes | direct-run | Duplicated inner copy confirmed; §4.4 citation accurate |
| Document-ID public contract | yes | static + direct-run | Regex + 3 messages match §4.2 exactly |
| Read-only MCP no-write | partial | static-inspection | Not exercised end-to-end (Reachability gap) |
| Migration copy presence | yes | static-inspection | Phase C deliverable, not yet present at I0 (consistent) |

Reachability gaps: read-only-MCP no-write assertion (§4.4) and exact-TestPyPI /
OIDC-scoping workflow assertions (§4.5) were not exercised end-to-end in this
seat; each is a latent surface a later phase must reach with a concrete input.

## 8. Issues found

### Blocking (Critical)

None. Both concrete defects (X-M1, X-M2) are already committed Phase C
requirements, and both observed failures are fail-closed on the pass/fail axis
(the validator crash still exits non-zero; the log escape is a write, not a
false approval). No new blocker survives with a reproduction.

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| X-1 | X-M2 requirement (§4.1) is under-scoped: it names only field `id` and only lines `244-285`, but `id` and `issue` are both required and are subscripted directly at 244, 245, 268, 275, 286, **338, 372, 375, 383, 387**, 632, 656-661. A literal-compliant fix + a §6 "malformed registry rows" regression that feeds only a missing-`id` row PASSES while a row missing `issue` (or other required field) still crashes — a test that falsely passes. | `scripts/validate-audit-remediation-registry.py:338` (and siblings) | direct-run | `/tmp/repro_xm2.py`: scenario A missing `id` → `KeyError: 'id'` @244; scenario B missing `issue` → `KeyError: 'issue'` @338 | Requirement wants "collected missing fields error, never uncaught KeyError" but only for `id`@244-285; other fields/sites still traceback | Generalize §4.1 to "any finding row missing ANY required field yields the collected missing-fields error and non-zero exit at every subscript site," and require the regression to cover ≥2 distinct missing required fields |
| X-2 | X-M1 regression can pass vacuously and the requirement omits two facts: (a) the pre-existing `config._validate_path` already rejects an *explicitly-configured* outside `logs_dir` at load (config.py:363), so a test using that vector never exercises log.py; (b) the reachable vector is the **default** `docs/logs` path, which skips `_validate_path`; and (c) line 115 `.resolve()` collapses symlinks before any check. | `ontos/commands/log.py:115,334-340`; `ontos/core/config.py:360-363` | direct-run | `/tmp/repro_xm1.py` → explicit outside symlink raises `ConfigError` (vacuous for log.py); `/tmp/repro_xm1b.py` → default-path `docs`-symlink escapes to `OUTSIDE_*/logs/…md` | Spec §4.3 test "prove sentinel unchanged" is satisfiable by a config-guard-shadowed test that never reaches log.py | Require the X-M1 regression to use a default/in-config-contained `logs_dir` with a symlinked component (not an outside-configured `logs_dir`), and require the no-follow check to precede/replace `.resolve()` |

### Minor

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| M-1 | Duplicate-ID detection maps missing-`id` rows to `None`; two such rows report `duplicate registry IDs: [None]`. | `scripts/validate-audit-remediation-registry.py:219-223` | static-inspection | Feed two `{}` finding rows to `validate` | Confusing `[None]` diagnostic | Skip rows missing `id` from the duplicate set (folds into X-1 fix) |
| M-2 | Invalid-clause message duplicates the clause literal (e.g. `'4.x.5'` appears twice; `'>=' '='`), exactly the copy §4.4 already flags for dedup. | `ontos/core/config.py:260,279-345` | direct-run | `required_version_incompatibility('4.x.5','4.7.0')` | Two copies of the clause in one message | Confirms §4.4 requirement; no extra action |

## Verdict
Approve

No reproducible blocker survives against spec v1.1: the two concrete defects are
already committed Phase C requirements and both fail closed. I approve advancement
with two should-fix items that Phase C must honor to avoid shipping a
false-passing acceptance: (X-1) widen the X-M2 requirement beyond `id`/`244-285`
to every required field and every subscript site, and (X-2) author the X-M1
regression against the *reachable* default-path symlink vector rather than the
config-guard-shadowed explicit-`logs_dir` vector, and apply the no-follow check
before `.resolve()`.

## Notes

Evidence labels: direct-run (repros `/tmp/repro_xm1.py`, `/tmp/repro_xm1b.py`,
`/tmp/repro_xm2.py`, and `required_version_incompatibility` invocation, all in
the project `.venv`), static-inspection (line-site enumeration and diagram
review). No B.1 verdicts, approvals, or test summaries were read. Did not commit;
per Template 01 the review-phase worker leaves staging/commit to the orchestrator.
