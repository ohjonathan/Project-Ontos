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

Blind recertification of corrected spec v1.3 and frozen diff `bf91b42…b6f89d7`
(single commit `b6f89d7 Implement audit rebaseline remediation`). All
reproductions use frozen `git show b6f89d7:…` bytes or a throwaway detached I0
worktree (`git worktree add --detach <tmp> b6f89d7`); no current-worktree byte
was used as proof of a Phase C gate. Author family is `codex`; reviewer family
`claude` is provider-distinct, so no same-provider halt.

## 1. Input boundary attestation

The prompt exposed only: (a) operational preflight (identity, frozen SHA pair,
output path, the do-not-read constraint), (b) the diff/artifact bytes, and (c)
the governing spec. No suite outcome, prior approval, guard-discharge, coverage,
or "already-green" claim was supplied as a prefilled fact. I read no other
reviewer verdict, receipt, or approval. No prompt-assembly blocker.

## 2. Invariant re-derivation

From spec §4.1 / §4.4 / §11 and the frozen validator I derive the spec's own
**universal** invariants (not author claims):

- **INV-Q (quarantine-before-all-consumers).** §4.1: "Before any indexing,
  hashing, `set`/`Counter`, sorting, … count, lookup, or … GitHub parity
  operation, the validator must perform a structural and type-validation pass …
  Invalid rows are … quarantined from every downstream collection, and produce
  the ordinary validation-failure exit `1`—**never** an exception-derived exit
  `2`, bare `KeyError`/`TypeError`". §4.1 closes: "quarantine before all
  consumers is [the safety boundary]." This is stated as an absolute over
  *malformed local metadata*, but the concrete pass is scoped to "**both**
  `findings` and `programs`" plus a second paragraph covering GitHub metadata
  (snapshot maps + `external_drift`).
- **INV-LOG / INV-LOCK.** Every `ontos log`-caused write (document, archive
  marker, ancillary) and both `.ontos.lock` entry points must be
  workspace-anchored no-follow (§4.3).
- **INV-ID.** Every CLI-supplied ID calls the canonical validator; no divergent
  regex/error string (§4.2).
- **INV-VER.** Each non-empty malformed `required_version` clause literal
  appears exactly once in one actionable message (§4.4).

## Fresh attack-surface derivation

| Attack surface | In scope? | Evidence attempted | Result |
|---|---|---|---|
| Registry validator: malformed `findings`/`programs` rows | Yes | direct-run I0 + spec read | Gate present & accurate; I0 crashes as spec admits |
| Registry validator: malformed `shared_path_leases` / `shared_tree_integration` | Yes | **direct-run I0** + spec read | **BLOCKER X-1**: crash-class reachable, uncovered by §4.1 gate/test |
| Registry validator: required-issue `program_by_issue[146/147]` lookup | Yes | static-inspection I0 | Corroborates X-1 (Key→exit 2 survives a shape-only pass) |
| `github_snapshot` unconditional `.get().get()` (line 336) | Yes | static-inspection | Covered by §4.1 GitHub-metadata clause — no finding |
| Log `logs_dir` symlink (default `docs/logs`) | Yes | direct-run I0 | Defect real; §4.3 gate reachable & non-vacuous |
| Archive marker `.ontos/session_archived` follow-write | Yes | direct-run I0 | Defect real (`write_text` follows); §4.3 gate accurate |
| Both `.ontos.lock` opens (`SessionContext.commit`, MCP `workspace_lock`) | Yes | direct-run I0 | Both `open("a+")`, no no-follow; §4.3 gate accurate |
| CLI ID copy divergence (`stub.py`) | Yes | direct-run I0 | Divergent regex-only string present; §4.2 gate accurate |
| `required_version` malformed-clause dedup/count | Yes | direct-run I0 | Duplication real; count rule satisfiable — see S-1 |
| Committed-but-uncertified status transitions | Yes | spec read | Spec claims none (status:draft, §11 "Phase C required"); receipts out of blind-review inputs |
| Serializer round-trip / release-wheel / MCP read-only | Partial | static-inspection | Left to Peer/Alignment + D.5; no adversarial catch derived |

## 3. Assumption attack

| Assumption | Why it might be wrong | Impact if wrong | Reproduction / proof |
|---|---|---|---|
| A structural pass over `findings`+`programs` (+GitHub meta) makes the validator never exit `2` | Two other top-level registry collections (`shared_path_leases`, `shared_tree_integration`) are consumed via `.get()`/subscript with no structural pass | Spec-compliant Phase C still crashes exit `2` on malformed control-plane input; INV-Q falsified; acceptance test vacuous for those inputs | Direct-run, §8 X-1 |
| Naming the exact malformed clause and "count-once" are jointly achievable for multi-clause inputs | Full-requirement `repr` necessarily contains the bad clause as a substring | Dedup that keeps clause-identification counts 2; dedup that counts 1 may drop *which* clause is bad | static-inspection, §8 S-1 |

## 4. Failure mode analysis

| Failure | How it happens | Would we notice? | Reproduction / proof |
|---|---|---|---|
| Validator aborts with `audit-registry: ERROR … has no attribute 'get'`, exit `2` | `shared_path_leases` contains a non-mapping row, or `shared_tree_integration` is a non-mapping | **No** — §4.1 table-driven acceptance test omits these collections; a green suite hides it | direct-run (below) |
| Validator `KeyError` exit `2` | `programs` well-formed but missing required issue `#146`/`#147` → `program_by_issue[issue]` (I0 line 444) | No — a shape-only structural pass does not assert membership | `git show b6f89d7:scripts/validate-audit-remediation-registry.py` L439-444 |

Direct-run (throwaway detached I0 worktree, real committed registry, single
collection mutated; baseline unmutated run = `exit 0 PASS`):

```
$ git worktree add --detach /tmp/i0 b6f89d7
# mutate only manifests/project-ontos-audit-remediation-registry.yaml, then:
$ python3 scripts/validate-audit-remediation-registry.py; echo exit=$?
shared_path_leases += "not-a-mapping"      -> audit-registry: ERROR: 'str' object has no attribute 'get'      exit=2
shared_path_leases += None                 -> audit-registry: ERROR: 'NoneType' object has no attribute 'get'  exit=2
shared_tree_integration = ["x"]  (a list)  -> audit-registry: ERROR: 'list' object has no attribute 'get'      exit=2
shared_tree_integration = "unproven"       -> audit-registry: ERROR: 'str' object has no attribute 'get'       exit=2
```

Frozen anchors: `shared_path_leases` consumed at L456 (`lease.get("path")`),
L457 (`lease.get("programs")`), L458 (`lease.get("order")`) with no preceding
structural pass; `shared_tree_integration` consumed at L421/L427
(`integration.get(...)`); `main()` maps every `validate()` exception to
`return 2` (L705-707).

## 5. Diagram completeness attack

§10.1 marks GitHub/Windows/TestPyPI as external and routes GitHub parity into
the validator; §10.2 shows the D.3→D.4→D.2 retry loop and the D.5+falsification
stop boundary. No prose error-path is missing from the diagrams. No blocking
diagram/prose mismatch.

## 6. Edge case inventory

- Empty/None/duplicate-missing `id` findings: §4.1 gate + I0 line 219 filter
  handles non-dicts; dict-missing-`id` still yields the `[None]` Counter artifact
  pre-quarantine — spec correctly names this as a Phase C fix.
- Non-mapping `shared_path_leases` row / non-mapping `shared_tree_integration`
  / list-typed integration: **uncovered by the gate** — X-1.
- Programs list missing required issue `#146`/`#147`: `KeyError` exit `2`
  (corroborates X-1).
- Multi-clause vs single-clause malformed `required_version`: S-1.
- Default `docs/logs` symlink (config shadow-guard at `config.py:360-363` only
  validates *explicit* `paths.logs_dir`, so the default path is unvalidated and
  reachable): §4.3's default-path/post-config-plant construction is genuinely
  non-vacuous — no finding.

## 7. Security surface

The write/lock no-follow gates (§4.3) and the CLI-ID canonicalization (§4.2) are
the security-relevant surfaces; the frozen I0 defects they target are real
(`.resolve()` collapse at `log.py:115`; `write_text` follow at the archive
marker; `open("a+")` on both `.ontos.lock` opens; `stub.py` divergent
regex-only string with `_ID_PATTERN.match` not `fullmatch`). The spec's
remediation requirements for these are accurate and reachable. No new
injection/authZ vector derived beyond the validator crash-class in X-1.

## 8. Issues found

### Blocking (Critical)

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| X-1 | Spec §4.1's mandatory structural/quarantine pass is scoped to `findings`, `programs`, and GitHub metadata, but the validator also consumes `shared_path_leases` rows and `shared_tree_integration` via `.get()`/subscript. A non-mapping value in either crashes with an exception-derived exit `2` — the exact class §4.1 says must "never" occur — while the §4.1/§6 table-driven acceptance test (which omits these collections) stays green. A Phase C authored to the letter of §4.1 still violates INV-Q and passes a vacuous test w.r.t. the universal "never exit `2`/quarantine before all consumers" invariant. | spec §4.1 (gate scope) + §11 matrix rows; `scripts/validate-audit-remediation-registry.py` L421/427, L456-458 (I0); `main()` L705-707 | direct-run | Detached I0 worktree; mutate only `shared_path_leases`/`shared_tree_integration` in the committed registry (baseline run = exit 0) → 4 cases all `exit=2 audit-registry: ERROR: … has no attribute 'get'` (§4 block) | Observed: exit `2` traceback-message on malformed lease/integration. Expected per INV-Q: accumulated exit-`1` validation error. Extend the structural/quarantine pass (and the §4.1/§6 table-driven test + a §11 matrix row) to every registry-owned collection the validator consumes — at minimum `shared_path_leases` (row-mapping + `path`/`programs`/`order` shape) and `shared_tree_integration` (mapping) — and add required-issue membership fail-closed for `program_by_issue[146/147]`; OR explicitly narrow the "never exit `2`" invariant to name the collections it does not cover. |

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| S-1 | §4.4's "each non-empty malformed clause literal appears exactly once … in one **actionable** message" is under-specified for multi-clause requirements. At I0 the message is `Invalid [ontos].required_version {required!r}: {exc}`; the outer `{required!r}` (full string) always contains the bad clause as a substring, so "count == 1" can be satisfied *either* by dropping the outer full-requirement repr (loses input echo) *or* by dropping the specific-clause diagnosis (loses *which* clause is bad in a multi-clause range). The count-once regression, if written only with single-clause inputs (token == whole requirement), cannot distinguish these and can bless a less-actionable fix. | spec §4.4; §6 required-version bullet; `ontos/core/config.py` L250-267 (I0) | static-inspection | `git show b6f89d7:ontos/core/config.py` L250-267: outer wrapper always emits `{required!r}`; clause-level `ConfigError` (`invalid version clause {clause!r}`) repeats it → count 2 today | Observed: rule counts occurrences but does not pin *clause identification*. Expected: a multi-clause malformed input must still name which clause failed while counting the literal once. Add a §6 assertion that a representative **multi-clause** malformed requirement keeps clause identification (e.g., asserts the offending clause is unambiguously indicated) while the literal count is 1. |

### Minor

| ID | Description | Location | Evidence | Reproduction | Observed vs expected | Suggested action |
|----|-------------|----------|----------|--------------|----------------------|------------------|
| N-1 | §4.1 / §11 cite the validator direct-read at `…:18-50,209-266` / `:249-266`; frozen I0's malformed-input consumers extend to L336 (`github_snapshot`), L370, L421-427, L444, L456-458. The narrow anchor ranges under-represent the consumer surface the quarantine boundary must precede. | spec §4.1, §11 | static-inspection | Compare cited ranges to `git show b6f89d7:scripts/validate-audit-remediation-registry.py` consumer lines above | Anchors accurate but non-exhaustive | Broaden the cited consumer anchors so Phase C sees the full "before all consumers" surface. |

## Verdict

Request changes

X-1 is a reproducible (direct-run) falsification of the spec's own universal
INV-Q "never an exception-derived exit `2` / quarantine before all consumers"
invariant: the §4.1 gate and its named table-driven acceptance test do not cover
`shared_path_leases` or `shared_tree_integration`, so a Phase C authored exactly
to spec ships a validator that still crashes exit `2` on malformed control-plane
input, and the test greens vacuously. Everything else the recert targets —
reachable log/archive-marker symlinks, both `.ontos.lock` entry points, the
canonical-CLI-ID divergence, the malformed-clause duplication, and the
non-vacuous default-`logs_dir` construction — is accurately described against
frozen I0 and specified reachably; the spec makes no committed-but-uncertified
status claim within the blind-review inputs. Close X-1 (extend the structural/
quarantine pass + acceptance table + matrix to all consumed registry
collections, or narrow the invariant) and address S-1; the remaining v1.3 gates
stand.

## Notes

- Evidence: X-1 crash-class and the I0 log/lock/CLI defects = `direct-run` on a
  throwaway detached `b6f89d7` worktree (removed after use); spec-scoping,
  membership-lookup (X-1 corroboration), S-1, and N-1 = `static-inspection` on
  frozen `git show b6f89d7:…` bytes. No cap violation (labels ⊆ {direct-run,
  static-inspection}).
- File-existence attestation: `git branch --show-current` =
  `codex/audit-rebaseline-remediation-lifecycle`; `git rev-parse HEAD` =
  `c1047589…`; all cited impl/test paths are tracked at `b6f89d7`
  (`git cat-file -e b6f89d7:<path>` succeeded for each).
- No current-worktree byte was used as proof of a Phase C gate; the in-progress
  Phase C tree was not read for reproduction.
- Blind-review honored: no other reviewer verdict, approval, receipt, dispatch
  result, or green-result summary was read.
</content>
