---
id: audit-rb-B1-ca
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: B.1
role: adversarial
family: claude
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Adversarial Review — project-ontos-audit-rebaseline-remediation / B.1 / claude

## 1. Input boundary attestation

The prompt exposed only operational preflight (identity, workspace, bounded
inspection method), the spec bytes (`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`
v1.5), the frozen implementation I0 `b6f89d7` reachable through
`git show b6f89d7:<path>` / `git diff bf91b42...b6f89d7`, and the deliverable
manifest (for evidence cap and cardinality facts). No suite outcome, prior
verdict, guard-discharge, coverage-sufficiency, or already-proved claim was
supplied as a prefilled fact. I read no sibling B.1 lens, no B.2/D.2/D.5
bundle, no tracker conclusion, and no Phase C byte. No blocker against the
prompt assembly.

Branch/commit attestation for all "present/absent" claims below:

```
git branch --show-current  -> codex/audit-rebaseline-remediation-lifecycle
git rev-parse HEAD          -> fe585c56e94d9bb28533adb97e870c05d578d3d7
git merge-base --is-ancestor bf91b42 b6f89d7 -> bf91b42 is ancestor of b6f89d7
```

Evidence cap: `cli_capability_matrix.claude` declares no `evidence_cap`, so my
cap defaults to `direct-run`. Every finding below is nonetheless reproducible.
Family diversity: adversarial `claude` differs in provider from author `codex`
under `manifest_version: 2.0.0` — invariant satisfied, no same-provider halt.

## 2. Invariant re-derivation

Derived from the spec and diff, independent of author claims:

- **I1 — Quarantine-before-all-consumers.** The registry validator must
  structurally/type-validate every control-plane root and collection (registry
  root; `findings`, `programs`, `shared_path_leases`, `shared_tree_integration`,
  GitHub snapshot maps, `external_drift`; child-manifest roots) before any
  index/hash/set/sort/count/lookup/parity op, and `main()` must exit `1`/`FAILED`
  (never `2`/`ERROR`) on malformed input. *The spec explicitly frames this as a
  Phase C upgrade; frozen I0 is the "pre-upgrade consumer surface."*
- **I2 — Exact program membership.** Normalized program issue set = exactly
  `#146`–`#157`; `#158` is the epic, not a program.
- **I3 — Semantic serialize / string IDs.** `serialize_frontmatter` preserves
  field order and round-trips semantically; IDs are strings matching
  `^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$`; canonical validator owns all
  ID error copy; CLI must reuse it under `E_USER_INPUT`.
- **I4 — Log/lock no-follow boundary.** Every `ontos log` write (Markdown +
  `.ontos/session_archived` marker) and both workspace-lock entry points
  (`SessionContext`, MCP `workspace_lock`) go through an anchored no-follow
  pipeline; archive-marker failure is warnings-only exit `3`. *Spec labels
  frozen I0 as still defective here (`.resolve()` in log path; plain MCP lock
  open) — a Phase C gate.*
- **I5 — Version skew/copy.** `[ontos].required_version` parses every clause
  eagerly; malformed-clause literal appears exactly once; doctor executes the
  PATH program and compares its reported version; exact activation
  code/status/message + Migration anchor.
- **I6 — Read-only MCP.** Omits write tools, refuses persistent graph export.
- **I7 — Exit/schema compatibility.** Envelope keys fixed; exit taxonomy
  `0/1/2/3/5/130`; code `4` reserved and never emitted.
- **I8 — Publishing provenance.** One wheel; exact `ontos==tag` from TestPyPI
  with `--no-deps`; OIDC only on publisher jobs.
- **I9 — Lifecycle/release nonclaims.** No per-issue certification, no D.6,
  no merge/tag/publish/release; 41 open / 7 partial states preserved.

## 3. Assumption attack

| Assumption | Why it might be wrong | Impact if wrong | Reproduction / proof |
|---|---|---|---|
| Program set is exactly #146–#157; #158 is epic | §3 says "Issues #146–#158 must match registry state" — could imply #158 is a program | Membership gate off-by-one; KeyError-prone consumers | `git show b6f89d7:manifests/…-registry.yaml` — programs carry `issue:` 146…157 (12); `github_snapshot.epic_issue: 158`. Distinct sets, consistent. **Assumption holds.** (direct-run) |
| Frozen-I0 direct-read anchors are accurate | A wrong line cite would mislead Phase C | Phase C builds on a fiction; M6 preflight breach | Every cited range checked (§4/§11): schema 83-97/315-343, files 388-414, log 283-300/115/334-340, config 360-363/223-266, context 485-501/645-695, mcp locking 21-27, server 191-204, tools 384-405, doctor 593-692, locking 13-81, command_registry 15-84, json_output 16-49, validator main()@697. **All accurate.** (direct-run) |
| I0 does NOT already satisfy the quarantine boundary | Spec could be over-claiming I0 | False-green control plane | Spec §4.1 states the typed/quarantine boundary "is a Phase C upgrade and is not represented as already satisfied by I0." No over-claim to falsify. (static-inspection) |
| State counts are truthful | 41/7/91+9 could be stale | Scope overclaim | `yaml.safe_load`: 100 findings, 41 `confirmed_open`, 7 `partial_…`, 91 `fable_audit` + 9 `codex_revalidation`. **All match §1.** (direct-run) |

## 4. Failure mode analysis

| Failure | How it happens | Would we notice? | Reproduction / proof |
|---|---|---|---|
| Malformed registry row crashes validator with exit 2 at I0 | I0 validator is pre-upgrade; consumers index before typing | Yes — spec makes this the exact Phase C gate; not claimed fixed | Spec §4.1/§11 flag it; I0 anchor `18-728` cited as pre-upgrade surface. Corroborates spec, not a defect against it. (static-inspection) |
| Short-circuit hides a malformed later version clause | `version_satisfies_requirement` uses `all(...)` (short-circuits) | Yes — spec §4.4 requires eager parsing as a Phase C fix | `git show b6f89d7:ontos/core/config.py:245` — `return all(_version_clause_matches…)`. Matches spec's frozen-I0 characterization. (direct-run) |
| Log write follows a symlinked `logs_dir` via `.resolve()` | I0 `logs_dir = (…/logs_dir).resolve()`; marker write uses plain `mkdir/open("x")` | Yes — spec §4.3 X-M1 gate | `config.py:115`, `log.py:334-340` confirm the defect the spec targets. (direct-run) |
| Umbrella review silently erases external release blocker | Consolidation rounds up shared-tree integration | Yes — mechanical gate | `shared_tree_integration.status: unproven_rebaseline_integration`, `release_blocking: true`; manifest G-blocker-2 asserts both. (direct-run) |

No failure mode contradicts a spec claim. The failures the spec names as
open (I1/I4/I5 at I0) are corroborated by direct inspection, exactly as the
spec labels them.

## 5. Diagram completeness attack

The §10.1 architecture diagram maps A→V→L, S→W→C, X/K→C, K→W, the
producer edges A→S/A→C, and the three external boundaries (GitHub, Windows,
TestPyPI/PyPI) as dashed external nodes — consistent with §4's components and
§3's external blockers. The §10.2 lifecycle state machine shows the code-first
path (I0_Frozen→…→Phase_C_Reconciliation→D.1→D.2⇄D.4→D.3→D.5→Loose_Falsification→D6_Pending),
with both failure/retry edges (D.3→D.4 blocking; D.5→D.4 FAIL;
Loose_Falsification→D.4 catch) and the explicit "stop boundary; no release
claim" terminal. No prose error-path or component is absent from the
diagrams. No blocking mismatch.

## 6. Edge case inventory

- Empty/missing required field, non-mapping root, wrong/unhashable keyed value,
  invalid state enum, absolute/escaping/`None` path, ownership drift, phantom
  epic ID, duplicate/`None` ID — all enumerated in §4.1 + §6 table-driven proof.
- Missing `#146`/`#147` program rows → ordinary validation failure, not KeyError
  (§4.1) — spec-level requirement, correct.
- Empty version clause, earlier-false/later-invalid multi-clause ordering — §4.4
  requires both orderings; matches the short-circuit defect at I0.
- Symlinked default `docs/logs` vs post-config-plant configured path — §4.3
  requires the non-vacuous construction; addresses the config-layer false pass.
- Duplicate pending destination, staged-temp swap after descriptor close,
  hard-link lockfile — covered by §4.3/§6.

The spec's edge-case coverage is complete for a review deliverable; I could
not construct an unlisted breaking input class.

## 7. Security surface

| Attack surface | In scope? | Evidence attempted | Result |
|---|---|---|---|
| Symlink/reparse path escape on log + lock writes | Yes | `git show` of context.py no-follow anchor (`O_NOFOLLOW|O_DIRECTORY`, `O_EXCL|O_NOFOLLOW`), log.py + mcp/locking.py plain-open gaps | I0 gaps accurately flagged as Phase C gates; SessionContext writer already no-follow. No unclaimed hole. |
| TOCTOU between staged descriptor and rename/unlink | Yes | §4.3 binding-recheck requirement re-derived | Spec mandates device/inode/type recheck before every name op — sound; Phase C direct-run. |
| Publishing OIDC over-grant | Yes | `publish.yml` grep — `id-token: write` only on publisher jobs (165-167, 318-320) | Scoped correctly. |
| MCP read-only write bypass | Yes | server.py `if not read_only` gate; tools.py `E_READ_ONLY` on export_to_file | Enforced. |
| Registry validator crash-as-DoS (exit 2 on hostile input) | Yes | I0 pre-upgrade surface | Spec targets exactly this; not over-claimed as fixed. |
| Injection (SQL/command/template) | No | No SQL/shell-eval surface introduced by the reviewed contracts | Out of scope. |

No security finding survives as a defect against the spec: every hazard is
either already guarded or explicitly assigned to Phase C with a non-vacuous
regression construction.

## 8. Issues found

### Blocking (Critical)

None. Every load-bearing factual claim in the spec (direct-read anchors, exit
taxonomy, ID pattern, program membership, state counts) is reproducibly
accurate, and every not-yet-satisfied invariant is honestly scoped to Phase C
rather than claimed as already green. I could construct no runnable
reproduction of a spec defect.

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| — | (none) | — | — | — | — | — |

### Should-fix (Major)

None blocker-eligible. Reachability note: the new validation-layer rules
(quarantine, enum-closed lease filter, epic-checklist parity) are Phase C
constructions not present in I0 by the spec's own statement, so end-to-end
rule-reachability cannot be exercised at B.1; it is correctly deferred to the
Phase C table-driven acceptance proof in §4.1/§6. No latent unreachable rule
in the reviewed artifact.

### Minor

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| X-m1 | §3 dependency row reads "Issues #146–#158 must match registry state" while §4.1 pins the program set to exactly #146–#157. Not an error — #158 is the epic issue (`github_snapshot.epic_issue: 158`) covered by the epic-checklist-parity clause — but the two ranges appear without a one-word cross-reference. | spec §3 vs §4.1 | static-inspection | `git show b6f89d7:manifests/…-registry.yaml \| grep -nE '158\|epic'` → `epic_issue: 158`; programs carry issue 146…157 | Two consistent sets stated in different ranges; a reader may momentarily conflate them | Optional: annotate §3 that #158 is the epic (parity via §4.1), not a program. No behavioral impact. |

## Verdict

Approve

The spec is internally consistent and every falsifiable claim it makes about
frozen I0 `b6f89d7` is reproducibly accurate. The quarantine-before-consumers
boundary, log/lock no-follow discipline, eager version-clause parsing,
canonical ID copy, and archive-marker warnings-exit-`3` behavior are correctly
specified as Phase C construction gates and explicitly *not* claimed as
already satisfied by I0. The exit taxonomy (`0/1/2/3/5/130`, `4` reserved and
unemitted), ID pattern, exact `#146`–`#157` program membership (`#158` epic),
read-only MCP, publishing provenance, and the 41-open / 7-partial / 91+9=100
state counts all verify. Lifecycle/release nonclaims are preserved and backed
by mechanical manifest gates (G-blocker-1/2, G-scope-1, G-cardinality-1). One
non-blocking readability nit (X-m1). No blocker, no should-fix.

## Notes

- All reproductions used bounded `git show b6f89d7:<path>` and a
  `yaml.safe_load` of the frozen registry; no worktree created, no full suite
  run, no nested agent, no implementation edit, no sibling review consulted.
- This is a strict-P3 adversarial artifact (no provider-limited fallback
  fields); adversarial `claude` is cross-provider to author `codex`.
- I0 anchors verified as-cited: `ontos/core/schema.py:78-97,315-343`,
  `ontos/io/files.py:388-414`, `ontos/commands/log.py:115,283-300,334-340`,
  `ontos/core/config.py:223-266,360-363`, `ontos/core/context.py:485-501,645-695`,
  `ontos/mcp/locking.py:21-27`, `ontos/mcp/server.py:191-204`,
  `ontos/mcp/tools.py:384-405`, `ontos/commands/doctor.py:593-692`,
  `ontos/core/locking.py:13-81`, `ontos/command_registry.py:15-84`,
  `ontos/ui/json_output.py:16-49`, `scripts/validate-audit-remediation-registry.py` main()@697/728.
