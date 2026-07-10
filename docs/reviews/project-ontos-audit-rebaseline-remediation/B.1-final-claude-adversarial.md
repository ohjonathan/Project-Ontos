---
id: project-ontos-audit-rebaseline-remediation-B.1-final-claude-adversarial
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: adversarial
family: claude
evidence_labels_used: [static-inspection]
status: completed
---

# Adversarial Review — project-ontos-audit-rebaseline-remediation / B.1 / claude

Blind review of committed spec v1.4 (`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`)
and frozen implementation I0 `b6f89d7` against base `bf91b42`. Branch
`codex/audit-rebaseline-remediation-lifecycle`; `HEAD 43dd7dc`; `bf91b42`
and `b6f89d7` both resolve. I0 inspected only via `git show b6f89d7:<path>`
and `git diff bf91b42...b6f89d7`. No prior verdict, receipt, result bundle,
test summary, tracker conclusion, or Phase C byte was read. Author family is
`codex`; adversarial family `claude` — cross-provider, no same-provider halt.

## 1. Input boundary attestation

The prompt exposed only operational preflight (identity, SHAs, path bounds,
process constraints), the spec bytes, and bounded read access to I0 diff/blob
bytes. No suite outcome, prior approval, guard-discharge, coverage-sufficiency,
or "implementation matches spec" claim was supplied as a prefilled fact. The
spec's own §11 "Evidence" column and §§1–4 hedges ("Phase C direct-run
required", "not represented as already satisfied by I0") are artifact bytes
under review, not orchestrator assurances, and I treated them as claims to
falsify. No prompt-assembly blocker.

## 2. Invariant re-derivation

Re-derived from spec + I0 diff, then attacked:

- **I-1 Membership.** Normalized program-issue set = exactly `#146`–`#157`
  (§4.1); consumers use normalized membership, never `KeyError`.
- **I-2 Quarantine-before-all-consumers.** Every registry-owned collection the
  validator consumes is typed/structurally validated and quarantined before
  any index/hash/set/sort/count/lookup/parity op; malformed input yields exit
  `1`/`FAILED`, never exit `2`/`ERROR` or bare `KeyError`/`TypeError` (§4.1).
- **I-3 Serializer.** `serialize_frontmatter(mapping)->str` preserves order and
  fails closed unless output reparses to a semantically equal mapping (§4.2).
- **I-4 String ID.** IDs are strings matching
  `^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$`; canonical validator owns the
  copy; CLI must not maintain a divergent regex (§4.2).
- **I-5 Log/lock no-follow.** Every `ontos log` write (doc + archive marker) and
  both `.ontos.lock` entry points (`SessionContext.commit`, MCP `workspace_lock`)
  open through a workspace-root anchor with no-follow/reparse fail-closed,
  without `.resolve()` collapse (§4.3).
- **I-6 Version skew/copy.** `required_version` mismatch → shell `1`,
  `E_ACTIVATION_UNUSABLE`, `data.status: not_usable`, reason `Incompatible Ontos
  version`; invalid ranges begin `Invalid [ontos].required_version`; each
  malformed non-empty clause literal/repr appears exactly once and multi-clause
  diagnostics name the offending clause (§4.4).
- **I-7 Read-only MCP / exit taxonomy.** Read-only omits write tools; exit codes
  are `{0,1,2,3,5,130}` with `4` reserved (§4.4).
- **I-8 Publishing provenance / clean map / external blockers / nonclaims.**
  One wheel, exact `ontos==tag` from TestPyPI `--no-deps`, OIDC scoped to
  publishers; map derived from clean tracked snapshot; Windows/TestPyPI/GitHub
  are explicit external blockers; no per-issue, D.6, merge, tag, publication,
  or release claim (§§2,4.5,8,9).

Critical structural finding: **the spec frames I-2/I-4/I-5/I-6 as Phase C
upgrades and does NOT claim I0 satisfies them.** I therefore attacked two
targets: (a) does the spec accurately describe I0's pre-upgrade state, and (b)
are the Phase C acceptance requirements internally complete and falsifiable.

## Fresh attack-surface derivation

| Attack surface | In scope? | Evidence attempted | Result |
|---|---|---|---|
| Program membership vs downstream lookup (`program_by_issue[...]`) | Yes | `git show b6f89d7:manifests/...registry.yaml` issue enumeration + validator `.get`/subscript reads (`:213-491`) | Programs = 146–157 exactly; `#158` is finding-only (line 1033); no lease/integration references `#158`. Membership invariant holds. |
| Quarantine list completeness vs collections validator consumes | Yes | grep validator for every top-level/get consumption | Consumed: findings, programs, shared_path_leases, shared_tree_integration, github_snapshot count maps, external_drift. Spec §4.1 enumerates all; `generated_artifacts`/`row_templates` not consumed. Complete. |
| Log/lock symlink no-follow (pre-upgrade defect honesty) | Yes | `b6f89d7:log.py:115,330-340`; `b6f89d7:mcp/locking.py:24` | Defects real and accurately cited (`.resolve()` collapse; plain `.open("a+")`). Spec labels Phase C. |
| CLI ID divergence | Yes | `b6f89d7:stub.py:189-192` | Divergent regex-only string using `.match` (not `.fullmatch`) confirmed; spec flags it. |
| Version multi-clause double-echo | Yes | `b6f89d7:config.py:240-345` | `{required!r}` wrapper + `{exc}` inner both echo clause literal → duplicate; spec flags it. |
| Exit-code taxonomy (reserved `4`) | Yes | `b6f89d7:json_output.py:16-49` | `ExitCode` enum = {0,1,2,3,5,130}; `4` absent. Holds. |
| Publishing single-wheel / TestPyPI / OIDC | Yes | `b6f89d7:publish.yml:74-102,249-320` | One-wheel guard, exact `ontos==` `--no-deps`, `--verify-manifest`, `id-token: write` on publisher only. Holds. |
| Read-only MCP write-tool omission | Yes | `b6f89d7:mcp/server.py:191-204` | `if not read_only: _register_write_tools(...)`. Holds. |
| Runtime provider authenticity, live GitHub/TestPyPI/Windows behavior | No (out of scope) | — | External blockers; spec explicitly keeps pending. Not falsifiable from committed bytes. |

## 3. Assumption attack

| Assumption | Why it might be wrong | Impact if wrong | Reproduction / proof |
|---|---|---|---|
| Program set is exactly `#146`–`#157` | A lease/integration row could reference a non-program issue (e.g. `#158`) → downstream `program_by_issue[...]` KeyError | False-green membership; validator crash exit 2 | `git show b6f89d7:manifests/project-ontos-audit-remediation-registry.yaml \| sed -n '93,446p' \| grep -n 158` → no match; programs 146–157 confirmed. Assumption holds. |
| Spec's quarantine enumeration covers every consumed collection | An un-enumerated collection (`generated_artifacts`, milestone map) could be iterated unguarded, defeating "before all consumers" | Phase C gate looks complete but leaves a crash surface | `git show b6f89d7:scripts/validate-audit-remediation-registry.py \| grep -nE "\.get\(\|registry\["`: `expected_milestones` is a hardcoded dict (`:389`), `generated_artifacts` never read. All iterated registry collections are in §4.1's list. Holds. |
| `affected_issues` must equal full program set | It omits `#147` ([146,148..157]) — could signal dropped state | Miscount / dropped issue | Validator `:421-430` derives expected set from programs with `lease_state == implementation_uncommitted_integration_pending` and compares; `#147` legitimately excluded. Internally consistent; not a count defect. |
| I0 already satisfies the typed/no-follow/canonical-CLI gates | Spec could be over-claiming I0 | Ships an unmet gate as verified | Every Phase-C-labeled gate maps to a real I0 defect (`log.py:115` `.resolve()`, `mcp/locking.py:24` plain open, `stub.py:189-192` divergent regex, validator `:244,348,370` unguarded subscripts, `config.py:260` double-echo). Spec under-claims, not over-claims. Holds. |

## 4. Failure mode analysis

| Failure | How it happens | Would we notice? | Reproduction / proof |
|---|---|---|---|
| Validator crashes exit 2 on malformed row at I0 | `row["id"]`/`row["issue"]`/`program["issue"]` subscripts without isinstance guard | Yes — spec §4.1 requires Phase C to convert to exit 1/FAILED; I0 is pre-upgrade | `git show b6f89d7:scripts/validate-audit-remediation-registry.py \| sed -n '244p;348p;370p'` shows unguarded subscripts. Named defect, not a hidden one. |
| Log write follows symlinked `logs_dir` component | `(project_root/logs_dir).resolve()` collapses symlinks then `.open("x")` | Yes — flagged as X-M1/X-2/M-1 Phase C gate | `git show b6f89d7:ontos/commands/log.py \| sed -n '115p;334,340p'`. |
| MCP `workspace_lock` follows symlinked `.ontos.lock` | `lock_path.open("a+")` with no no-follow/regular-file check | Yes — spec §4.3/§4.4 Phase C gate | `git show b6f89d7:ontos/mcp/locking.py \| sed -n '24p'`. |
| Multi-clause invalid version echoes clause twice | `f"Invalid [ontos].required_version {required!r}: {exc}"` where `exc` also contains the clause repr | Yes — spec §4.4 Phase C gate; §4.4/§11 anchor lines differ (239 vs 249) | `git show b6f89d7:ontos/core/config.py \| sed -n '260p;283p'`. See Minor A-1. |
| Empty-clause diagnostic invents a literal | `>=4.7.0,` → generic `must be a valid semver range`, no fabricated clause | Guarded — spec §4.4 requires "actionable without inventing a literal that was not present" | `config.py:241-245` raises generic message; matches spec carve-out. |

## 5. Diagram completeness attack

§10.1 architecture: external nodes GitHub/Windows/TestPyPI are marked with the
`external` classDef and dashed edges, matching §§3/8 blockers; validator→ledger/
lease, serializer→writer→CLI/MCP, and locking→writer/CLI edges match §4. §10.2
lifecycle shows the code-first path (I0→A→B.1→B.2→Phase_C_Reconciliation→D.1…),
both failure/retry edges (`D3→D4`, `D5→D4`, `Loose_Falsification→D4`), and the
`D6_Pending → [*]` stop boundary with "no release claim". No prose error path is
absent from the diagram; the code-first B.2/Phase C reconciliation the spec adds
in v1.4 is present. No diagram/prose mismatch backed by a reproducible proof.

## 6. Edge case inventory

- Empty/None registry collection roots, non-mapping rows, unhashable/`None`
  keys, `None` path/issue elements: spec §4.1 requires table-driven quarantine
  for each; I0 validator does not yet guard them (pre-upgrade, named).
- Missing required program `#146`/`#147`: spec requires ordinary validation
  failure with normalized-membership consumers (no KeyError).
- Empty vs multi-clause malformed `required_version`; already-singular
  `Invalid [ontos].required_version` prefix must NOT be the counted token —
  spec §4.4/§6 explicitly counts the clause literal instead (anti-vacuity).
- Symlinked default `docs/logs` vs post-config-planted redirect: spec §4.3
  forbids the vacuous config-layer pass and pins the rejection to the
  log/write no-follow boundary.
- Date-like/numeric/`null` YAML scalar IDs: spec §7 requires quoting; validator
  `assert_frontmatter_roundtrip` fails closed on semantic drift (`yaml.py:104-116`).

## 7. Security surface

- **Path/symlink escape (primary).** Two live pre-upgrade escape surfaces
  (`log.py:115` `.resolve()`; `mcp/locking.py:24` plain open) are correctly
  identified as fail-open until Phase C anchors them no-follow. The spec extends
  the boundary to ancillary writes (`.ontos/session_archived`) and both lock
  entry points — no silent gap left.
- **AuthZ / OIDC.** `id-token: write` granted only to publisher jobs
  (`publish.yml:320`); TestPyPI download uses `PIP_CONFIG_FILE=/dev/null` and
  empty `PIP_EXTRA_INDEX_URL` to prevent index confusion (`publish.yml:252-256`).
- **Provider authenticity (residual, accepted).** Per Template 02 the
  executable-resolution layer is consistency-verified, not provenance-
  authenticated; out of this artifact's scope.
- No injection/secret-exposure surface introduced by the spec's contracts that
  is reproducible from committed bytes.

## 8. Issues found

### Blocking (Critical)

None. Every falsification attempt either confirmed the invariant or landed on a
defect the spec already names as a Phase C gate (under-claim, not over-claim). I
could not construct a reproduction showing spec v1.4 asserts a false fact about
I0 or specifies an unfalsifiable/incomplete acceptance boundary.

### Should-fix (Major)

None blocker-adjacent. The Phase-C acceptance requirements (I-2/I-4/I-5/I-6) are
by construction not reachable end-to-end at I0 — see Reachability gaps in Notes;
this is expected for a code-first B.1 spec review and is not a defect.

### Minor

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| X-A1 | Anchor line-range for the duplicated required-version copy differs between §4.4 (`config.py:239-266,279-345`) and §11 (`config.py:249-266,279-345`). 239 lands in `version_satisfies_requirement` (empty-clause branch), 249 in `required_version_incompatibility` (message producer). Both defensible; a reviewer chasing one anchor may miss the other branch. | spec §4.4, §11 | static-inspection | `git show b6f89d7:ontos/core/config.py \| sed -n '239,241p;249p;260p'` | Two overlapping-but-unequal citations of the same contract; no incorrect fact, no reproducible harm | Optionally unify to `config.py:239-266,279-345` in §11 for anchor parity. Non-gating. |

## Verdict

Approve

Spec v1.4's invariants survived falsification. Program membership is exactly
`#146`–`#157`; the quarantine-before-all-consumers enumeration is complete
against the collections the I0 validator actually consumes; serializer,
string-ID, exit-taxonomy (`4` reserved), read-only MCP, and publishing-
provenance contracts match committed I0 bytes; and every no-follow, canonical-
CLI, typed-validator, and version-copy gate maps to a real, correctly-cited I0
defect that the spec honestly labels Phase C rather than claiming as satisfied.
No blocking finding with a reproduction exists; one minor anchor-parity nit.
The external, per-issue, D.6, merge, tag, publication, and release nonclaims are
intact.

## Notes

- Evidence class: all findings are `static-inspection` — a spec/design (B.1)
  review of committed bytes; every proof is a deterministic `git show`/`grep`
  over cited lines. No code was executed and no full suite was run, per the
  worker constraints. No blocker is claimed, so the `direct-run`/
  `orchestrator-preflight` blocker-evidence bar is not invoked.
- Reachability gaps (Template 05 audit): the new validation-layer rules the
  spec introduces (typed/quarantine passes over findings/programs/leases/
  integration/parity metadata; the `main()` exit-`1`/`FAILED` guarantee;
  the canonical-CLI-ID copy; the no-follow log/lock opener; single-echo
  clause diagnostics) are Phase-C-authored and NOT present at I0, so no
  adversarial input reaches them end-to-end from `b6f89d7`. This is inherent to
  code-first B.1 sequencing (review spec + I0 diff, reconcile in Phase C), not a
  suppressed surface; the spec's §4.1/§6 table-driven acceptance proof is the
  mechanism that must exercise each rule in Phase C/D.5.
- Test-blessed-divergence audit: skipped — Phase B, no Phase-C test code under
  review.
- Attestation: `git branch --show-current` = `codex/audit-rebaseline-remediation-lifecycle`;
  `git rev-parse HEAD` = `43dd7dc`; `bf91b42` and `b6f89d7` both resolve; no
  "file absent" claim was made (all cited spec anchors were confirmed present in
  I0 via `git cat-file -e` / `git show`).
