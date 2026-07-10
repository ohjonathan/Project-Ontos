---
id: project-ontos-audit-rebaseline-remediation-B.2-final-claude-adversarial
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.2
role: adversarial
family: claude
evidence_labels_used: [static-inspection]
status: completed
---

# Adversarial Review — project-ontos-audit-rebaseline-remediation / B.2 / claude

Blind falsification of committed spec **v1.5** at
`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md` against frozen
I0 `b6f89d7`, base `bf91b42`, and the reproduction statements in
`docs/reviews/project-ontos-audit-rebaseline-remediation/C-phase-falsification-findings.md`.
I did not read B.1/B.2 verdicts, receipts, result bundles, test summaries,
tracker conclusions, or sibling reviews.

**File-existence attestation (per Template 05):**

```
git branch --show-current  -> codex/audit-rebaseline-remediation-lifecycle
git rev-parse HEAD         -> d12f85147e9c3ebb7dc1bdcc4976b6126eb4d860
git rev-parse b6f89d7      -> b6f89d77e7fb684b8bd9a181a24c773d5777397a  (I0, exists)
git rev-parse bf91b42      -> bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95  (base, exists)
git ls-files docs/specs/project-ontos-audit-rebaseline-remediation-spec.md  -> tracked
```

Provider diversity: author family `codex`, reviewer family `claude` — providers
differ under a v2.0.0 manifest; no same-provider halt. Evidence cap for `claude`
is unset → defaults to `direct-run`; I nonetheless claim only `static-inspection`
because every check is a bounded `git show` read of frozen code, not an execution.

## 1. Input boundary attestation

The prompt exposed operational preflight (identity, SHAs, no-touch paths,
output path), the artifact bytes (spec v1.5), and governing references
(frozen-I0 code via `git show`, base SHA, the C-phase falsification
reproduction table). No suite outcome, prior approval, guard-discharge, or
coverage-sufficiency claim was supplied as a prefilled fact. The falsification
table's "Current state" column carries `implemented uncommitted; focused
verified` strings; I treated those as **substantive assurance claims** and
ignored them for correctness purposes — I re-derived each defect from I0 bytes
independently. No blocker against prompt assembly.

## 2. Invariant re-derivation

Derived from spec §§4.1–4.5 + §11 and the seven C-FZ reproductions, then checked
against frozen I0:

1. **Eager clause parsing** (§4.4 / C-FZ-1): every `required_version` clause is
   parsed before compatibility is reduced; an earlier false comparison may not
   mask a malformed later clause; each malformed clause literal/repr appears
   **exactly once** and the diagnostic names the offending clause.
2. **Entry-binding recheck** (§4.3 / C-FZ-2): device/inode/type of each staged,
   backup, move, and delete entry is captured while its descriptor is open and
   re-verified immediately before every name-based rename/unlink and after
   replacement.
3. **Control-plane quarantine** (§4.1 / C-FZ-3, C-FZ-7): every consumed root and
   collection (registry root; `findings`/`programs`/`shared_path_leases`/
   `shared_tree_integration`/`github_snapshot` maps/`external_drift`; #146/#147
   child-manifest roots + scope collections) is structurally + type-validated
   and quarantined before any index/hash/set/sort/count/lookup/parity op;
   `main()` returns exit `1`/`FAILED`, never exit `2`/`ERROR`.
4. **Enum-closed lease filtering** (§4.1 / C-FZ-4): finding/program state fields
   are enum-validated before any status partition or active-lease filter; a
   misspelling cannot delete an overlapping program from the collision gate.
5. **Exact GitHub identity** (§4.1 / C-FZ-5): live payload `number` matches the
   requested issue; title/state/milestone/labels/body are typed; the epic
   checklist ID set matches the registry-owned set exactly (phantom/duplicate
   rows fail).
6. **Single-link no-follow lock** (§4.3–4.4 / C-FZ-6): both `SessionContext.commit`
   and MCP `workspace_lock` open `<workspace>/.ontos.lock` through a workspace
   anchor with no-follow/reparse protection and reject `st_nlink>1` /
   `nNumberOfLinks>1` **before** any backend can write its one-byte sentinel.
7. **Canonical ownership/paths** (§4.1 / C-FZ-7): each finding's `root_program`
   equals its owning program's root; evidence/scope/lease paths are canonical,
   repo-relative, non-escaping.
8. **Visible archive-marker failure** (§4.3): an ancillary `.ontos/session_archived`
   failure yields human warning `Session log created, but archive marker was not
   updated:`, JSON `warnings[]`, exit `3`, `result.status: warnings`, log path
   retained in `data`; primary log is not rolled back.
9. **Immutable boundary**: 41 open / 7 partial states, 91+9=100 rows, immutable
   SHA pair, and every external/per-issue/child/D.6/merge/tag/publish/release
   nonclaim are preserved.

Each I0 anchor cited by the spec was read and matches the described pre-fix
defect (see §§3–4). The spec consistently frames the corrections as Phase C
requirements, not as already-verified — congruent with the falsification table's
"no `fix_commit`" nonclaim.

## Fresh attack-surface derivation

| Attack surface | In scope? | Evidence attempted | Result |
| --- | --- | --- | --- |
| Lazy `all()` hides malformed later clause | Yes | `git show b6f89d7:ontos/core/config.py:246-248` | Confirmed defect; spec fix eager-parses. Non-vacuous test. |
| Clause literal double-count via whole-requirement echo | Yes | config.py:263-265 `{required!r}` wrapper | Real tension; spec makes whole-echo optional + counts literal, resolving it. Minor. |
| Staged-temp swap between fd close and `os.replace` | Yes | context.py:700-772 (`_stage_text`/`_replace_entry`) | Confirmed no binding recheck at I0; spec adds capture/recheck. |
| Registry/child-root type confusion → exit 2 | Yes | validator 213-244, 155-157 (no isinstance before `row["id"]`/`.get`) | Confirmed; spec quarantines all roots, asserts exit 1. |
| Enum bypass (`acitve`) removing overlap | Yes | validator 510 `lease_state == "active"` string compare | Confirmed; spec enum-validates before filter. |
| Epic checklist phantom rows via subset `<=` | Yes | validator 635 `expected_ids <= set(body.split())` | Confirmed subset-not-equality defect; spec requires exact set. Impl caveat noted (M-3). |
| Program-membership vs issue-span contradiction | Yes | validator 241/374/628/643/688 (#146–157 programs; #158 epic) | Falsified — internally consistent. |
| Multi-link `.ontos.lock` → NUL through hard link (msvcrt) | Yes | mcp/locking.py:24 plain `open`; core/locking.py:60-64 `write("\0")` | Confirmed; spec adds nlink check before backend write. |
| CLI ID regex divergence / suffix bypass | Yes | stub.py:188 `_ID_PATTERN.match` (not `fullmatch`); schema.py:83-97 canonical | Confirmed divergence; spec routes CLI through canonical validator. |
| Exit-code taxonomy collision (code 4) | Yes | json_output.py:28-35 `ExitCode` enum | No `4` present; spec "reserved" claim consistent. |
| Symlinked `logs_dir` regression vacuity | Yes | config.py:360-363 guard; log.py:115 `.resolve()` | Spec's default-path/post-config-plant construction defeats vacuity. |
| Immutable SHA/count/nonclaim regression | Yes | spec §§1–2,7–9 vs validator 244-346 | Preserved; no drift. |
| Windows `nNumberOfLinks` real proof | Out (external) | n/a — real-runner only | Spec marks external-pending; not local-falsifiable. |
| TestPyPI/PyPI service behavior | Out (external) | n/a — tag-run only | Spec marks external-pending. |

## 3. Assumption attack

| Assumption | Why it might be wrong | Impact if wrong | Reproduction / proof |
|------------|------------------------|-----------------|----------------------|
| Program issue set `#146`–`#157` contradicts dependency `#146`–`#158` | Two different ranges appear in §4.1 vs §3 | Membership gate would reject the epic or admit a phantom program | Falsified: `git show b6f89d7:scripts/validate-audit-remediation-registry.py` lines 374/628/635/643/688 show `#158` is the **epic** (subset body check, special-cased), programs are `#146`–`#157`; O4 is the "12-deliverable" ledger. Consistent. |
| "Clause literal appears exactly once" is satisfiable while also "identify which clause failed" | Frozen wrapper echoes full `{required!r}`, which contains the malformed clause substring → count 2 | A lazy fix passes review but ships a double-count message | config.py:263-265 echoes `Invalid [ontos].required_version {required!r}` + inner `invalid version clause {clause!r}` → literal twice. Spec §4.4 pre-empts: whole-requirement echo "optional, not a substitute"; test counts the token, so a double-count fails. Tension resolved, non-blocking. |
| Symlinked-`logs_dir` regression is non-vacuous | Config guard (360-363) may reject the redirect before the write boundary is reached | Test passes without exercising the log no-follow fix | Spec §4.3 mandates default-path (no explicit `logs_dir`, guard silent) or post-config plant, and "observed rejection must come from the log/write no-follow boundary." Vacuity path explicitly forbidden. |
| Epic exactness is implementable as stated | I0 checks `set(body.split())` (all body tokens incl. prose) | `set(body.split()) == expected_ids` would never pass → gate unreachable if naively tightened | validator:635. Spec intent is "checklist ID set," not raw body tokens; achievable by parsing checklist rows. Recorded as M-3 (implementation caution, not spec contradiction). |

## 4. Failure mode analysis

| Failure | How it happens | Would we notice? | Reproduction / proof |
|---------|----------------|------------------|----------------------|
| Malformed later clause reported as merely "incompatible" | I0 `return all(_version_clause_matches(...) for clause in clauses)` short-circuits on first False before the malformed clause raises | Yes at Phase C — spec requires two orderings (incompatible-before-malformed) proving eager parse | config.py:246-248 `all(...)`; `>=99.0.0, not-a-range` never evaluates clause 2. |
| Destination ends up naming external sentinel after temp swap | fd closed in `_stage_text` (713-731), later `os.replace` (759-771) is name-based with no device/inode recheck | Yes at Phase C — spec §4.3 + §6 require temp/backup/move/delete swap tests asserting binding before rename & after replace | context.py:700-772. |
| Overlapping active program hidden by enum typo | I0 `active_programs = [p for p in programs if p.get("lease_state") == "active"]` — raw string compare | Yes — spec enum-validates state before the filter; C-FZ-4 repro (`acitve`) | validator:510. |
| Windows lock writes NUL through hard-linked external file | I0 MCP `open("a+")` (no nlink guard) then `try_acquire_exclusive` → msvcrt `handle.write("\0")` on empty file | Yes — spec requires nlink check before backend write + "no NUL byte through a hard link" test | mcp/locking.py:24; core/locking.py:60-64. |
| Validator crashes (exit 2) on malformed root instead of failing closed | I0 `registry.get("findings")` then `[row.get("id") for row in findings ...]` / `{row["id"]: ...}` with no root/row type guard | Yes — spec table-driven acceptance asserts `main()` exit 1/FAILED, never 2/ERROR | validator:213-244. |
| Archive-marker failure crashes or is silent | I0 `_create_archive_marker` called unguarded (log.py:315) after log written | Yes — spec §4.3 makes it a visible warnings-only exit 3 with retained `data.path` | log.py:315. |

No new failure mode survived as a **spec-level** blocker: every reproduced I0
defect maps to a construction-level gate with a non-vacuous regression, and the
public semantics (exit taxonomy, message prefixes, `E_LOG_EXISTS` retention +
recovery hint, `#146`–`#157`/`#158` split) are internally consistent.

## 5. Diagram completeness attack

`§10.1` architecture diagram: nodes for Registry→Validator→O4/O5, Serializer→
Writer→CLI/MCP, Activation/Doctor, Locking, Release→Tests→Map/AGENTS, and the
three external dashed boundaries (GitHub / Windows / TestPyPI) match §§4.1–4.5
and the external-pending rows in §11. The O4/O5 producer edge (`V --> L`) is
present, matching §4.1's "producer and parity gate." `§10.2` lifecycle diagram
shows B.2 code-first review, Phase C reconciliation, D.4↔D.2 retry, D.5→D.4 on
FAIL, D.5→Loose_Falsification→D.6_Pending stop boundary. No prose error path
(e.g., archive-marker exit-3, config-vs-write no-follow rejection) is a *diagram*
element that the state machine omits — these are code-path behaviors, not
lifecycle transitions. No blocking diagram/prose mismatch found.

## 6. Edge case inventory

- Empty `required_version` → I0 returns compatible (config.py:236-238); spec's
  eager-parse gate only fires on non-empty clauses; empty-clause diagnostic
  "remains actionable without inventing a literal" (§4.4) — covered.
- `,`-only / whitespace clause → I0 raises "must be a valid semver range"
  (config.py:242-245); spec preserves the range-level message; covered.
- Unhashable/`None`/absolute/escaping path values, non-mapping roots, wrong-typed
  keyed values, duplicate/`None` IDs → enumerated in §4.1 acceptance table.
- Multi-link + symlink lock, hard-link external sentinel, closed-descriptor temp
  swap → §6 test strategy enumerates each with external-sentinel invariance.
- Epic body with extra checklist ID (phantom) and duplicate ID → §4.1 requires
  exact-set failure (M-3 notes the parse-vs-`body.split()` implementation care).
- Zero-count lifecycle types in MCP enumeration → §4.4 "including zero-count
  types"; covered.

## 7. Security surface

- **Path/symlink escape (write + lock):** the core adversarial surface. I0
  `log.py:115 .resolve()`, `mcp/locking.py:24` plain open, and the fd-close→
  rename window in `context.py` are all real escape/alias vectors; the spec's
  no-follow anchor pins, nlink checks, and entry-binding rechecks close them by
  construction with external-sentinel-unchanged regressions. No residual
  spec-level bypass identified.
- **Injection / metadata trust:** GitHub live payloads are treated as untrusted —
  identity (`number`), typed fields, and exact checklist sets are validated
  before formatting; malformed/mismatched metadata is a parity error, not a
  crash. Sound.
- **AuthZ / OIDC:** §4.5 restricts OIDC to publisher jobs and one-wheel
  provenance (external-pending proof). Not locally falsifiable; correctly gated.
- No secret-exposure, deserialization, or SSRF surface is introduced by the spec
  text.

## 8. Issues found

### Blocking (Critical)

None. No reproduction demonstrates a spec-level failure: every corrected
construction is grounded in an accurately-cited, independently-verified frozen-I0
defect; the fixes target the actual root cause; the acceptance tests are
non-vacuous (count the literal not the prefix; plant-after-config; exact epic
set; no-NUL-through-hardlink; `main()` exit 1 not 2; external sentinel
unchanged); and the immutable SHA/count/status boundary and all nonclaims are
preserved.

### Should-fix (Major)

None blocker-adjacent. The items below are minor implementation cautions, not
spec contradictions.

### Minor

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| X-m1 | Required-version "clause literal exactly once" + frozen `{required!r}` whole-requirement echo will double-count the malformed token unless Phase C restructures `required_version_incompatibility`. Spec already makes whole-echo optional, so this is a construction caution. | spec §4.4; `b6f89d7:ontos/core/config.py:263-265` | static-inspection | `git show b6f89d7:ontos/core/config.py \| sed -n '260,266p'` shows `Invalid [ontos].required_version {required!r}` wrapping the inner `invalid version clause {clause!r}`; the malformed literal is a substring of `{required!r}` → 2 occurrences. | Message must contain the malformed literal exactly once. | Phase C should identify the clause by position/comparator and not re-echo the full requirement (or echo a form that omits the raw malformed literal), as §4.4 already permits. |
| X-m2 | Epic exactness must parse checklist rows, not compare `set(body.split())` to `expected_ids`; a naive tighten of the frozen subset check to `==` on all body tokens would make the gate unreachable (prose tokens ≠ IDs). | spec §4.1; `b6f89d7:scripts/validate-audit-remediation-registry.py:635` | static-inspection | `git show b6f89d7:...:635` shows `if issue == 158 and not expected_ids <= set(body.split())` (subset over whole-body tokens). | Exact checklist-ID equality intended; whole-body equality never passes. | Phase C should extract checklist-row IDs specifically before exact-set comparison (spec intent already says "checklist ID set," so no spec change required). |
| X-m3 | CLI stub uses `_ID_PATTERN.match` (start-anchored only, not `fullmatch`), a latent suffix-acceptance divergence beyond the regex-string divergence the spec already flags. Subsumed by routing through the canonical validator (`fullmatch`). | `b6f89d7:ontos/commands/stub.py:188` vs `ontos/core/schema.py:92` | static-inspection | `git show b6f89d7:ontos/commands/stub.py \| sed -n '188p'` → `.match`; schema uses `DOCUMENT_ID_PATTERN.fullmatch`. | Divergent + weaker anchoring. | Confirms the §4.2 canonical-validator gate is strictly beneficial; ensure the CLI equality regression asserts full-match rejection of trailing-invalid IDs. |

## Verdict

Approve

Spec v1.5 closes every reproduced C-FZ gap by construction. All frozen-I0 anchors
it cites are accurate; each fix targets the verified root cause; the specified
regressions are non-vacuous and reachable; public semantics (exit taxonomy,
message prefixes, `E_LOG_EXISTS` + recovery, program `#146`–`#157` vs epic
`#158`) are internally consistent; and the immutable SHA/count/status boundary
plus all external/per-issue/child/D.6/merge/tag/publish/release nonclaims are
preserved. My one contradiction hypothesis was falsified by the validator
itself. The three minor items are Phase C construction cautions with no spec
change required; none is blocker-eligible (no reproduction of a spec-level
failure). Approval certifies the spec for Phase C; it does not certify Phase C
execution, D.5, any child lifecycle, or a release.

## Notes

- Evidence is `static-inspection` only: all frozen-I0 reads were bounded
  `git show b6f89d7:<path>` inspections; I ran no tests, the validator, or the
  full suite, and did not modify implementation or repository state.
- Blind-review isolation honored: no B.1/B.2 verdict, receipt, dispatch bundle,
  test summary, tracker conclusion, or sibling review was read.
- Anchors verified this pass: `config.py:223-266,279-345,360-363`;
  `log.py:108-120,283-300,310-345`; `context.py:485-501,645-772`;
  `mcp/locking.py:15-40`; `core/locking.py:13-81`; `schema.py:83-97,315-343`;
  `stub.py:180-195`; `json_output.py:16-49`; `validate-audit-remediation-registry.py`
  consumer surface (155-157,213-346,370-513,596-688).
