---
id: project-ontos-audit-rebaseline-remediation-D.2-claude-peer
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: D.2
role: peer
family: claude
evidence_labels_used: [direct-run, static-inspection]
status: completed
---

# Peer Review — project-ontos-audit-rebaseline-remediation / D.2 / claude

Independent quality/completeness review of spec v1.5
(`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`) against the
exact Phase C implementation I1 `05b090d53f7b0c9c4afdbb5fb23ab58cdfa01fa0`.
Historical base `bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`; I0
`b6f89d77e7fb684b8bd9a181a24c773d5777397a`. Reviewed the base→I1 diff and the
current committed control-plane evidence delta (I1→HEAD) independently. Did not
read D.1, B-family verdicts, sibling D.2 reviews, dispatch results, receipts, or
tracker conclusions.

**File-existence attestation (Template 03 v1.3+).**

- `git branch --show-current` → `codex/audit-rebaseline-remediation-lifecycle`
- `git rev-parse HEAD` → `9dbe5e1fb61cb0546e48019a1476898900f828cf`
- Code/script/test tree at HEAD equals I1 for `ontos/**`, `scripts/**`,
  `tests/**` except the control-plane evidence delta
  (`git diff --stat 05b090d HEAD` touches only the registry YAML, the validator's
  R2 expectation branch, and one added validator test) (direct-run).

**Environment.** `.venv/bin/python` = CPython 3.14.6, pytest 8.4.2. Code targets
`requires-python >= 3.9`. Bounded focused suites only; the full suite was not run
per scope.

## 1. Completeness check

Every §4 construction gate maps to committed code and a non-vacuous regression,
verified by direct-run rather than by trusting green:

- **§4.1 typed/quarantine-before-consumers.** `validate-audit-remediation-registry.py`
  fails closed on malformed control-plane input with exit `1`/`FAILED`, never
  exit `2`/`ERROR`. Direct-run battery through `main()` with a monkeypatched
  `REGISTRY_PATH`: registry-root-as-list, non-mapping `findings` row,
  `verification_evidence` containing a nested/unhashable list, absolute path,
  `None`, and escaping `../` path, invalid `lease_state` enum (`acitve`), dropped
  required program `#146`, non-list `shared_path_leases`, and duplicate
  `shared_tree_integration.affected_issues` — all returned `rc=1` / `FAILED`
  (direct-run: `scripts/validate-audit-remediation-registry.py:1881-1909`,
  path guard `:273-`, `verification_evidence` guard `:997-1016`). Local validator
  run: `audit-registry: PASS`, `original findings: 91`, `revalidation findings: 9`.
- **§4.2 serializer + canonical ID.** `serialize_frontmatter` public signature
  preserved (`ontos/core/schema.py:315`); `validate_document_id` owns the exact
  documented pattern (`ontos/core/schema.py:78-97`); the CLI stub calls the same
  validator and surfaces `E_USER_INPUT` — no divergent regex
  (`ontos/commands/stub.py:8,183-185`). `test_stub_parity.py` (21 cases) green.
- **§4.3 safe writer / logging / lock.** Log collision → `E_LOG_EXISTS`, retains
  `data.path`, adds the "choose a different `--title`, or move/remove" recovery
  hint (`ontos/commands/log.py:307-325`). Archive-marker failure →
  warnings-only exit `3`, `warnings[]`, `result_status: warnings`, log path
  retained, both writes via `SessionContext` (`ontos/commands/log.py:339-387`).
  Workspace lock centralized in `ontos/core/locking.py` with `O_NOFOLLOW` and
  `st_nlink != 1` / `nNumberOfLinks` rejection re-checked immediately before
  acquisition (`:82,163-192,437-`), consumed by both `SessionContext` and MCP
  `workspace_lock` (`ontos/mcp/locking.py:11-24,62-74`).
- **§4.4 CLI/activation/platform.** JSON envelope has exactly the nine spec keys
  and `result` splits status/kind/exit_category/diagnostics
  (`ontos/ui/json_output.py:329-346`); exit taxonomy `0/1/2/3/5/130` with `4`
  reserved and absent from `ExitCode` (`:29-37`). `required_version` parses every
  clause eagerly before reduction (list comprehension + explanatory comment,
  `ontos/core/config.py:249-255`).
- **§4.5 release/tests/metadata.** All CREATE artifacts tracked
  (`scripts/check_release_artifact.py`, `ontos/command_registry.py`,
  `ontos/core/locking.py`, the registry + validator + revalidation report); CI has
  a `windows-latest` job (`ci.yml:139-141`); publish downloads
  `ontos==${expected_version}` from `test.pypi.org/simple/` with `--no-deps` and
  enforces a single wheel (`publish.yml:262-266,298-301`) (direct-run/static).

No missing §4 construction, CREATE artifact, or §6 test class was found.

## 2. Diagram-prose cross-reference

| Diagram component | In prose? | Prose component | In diagrams? |
|-------------------|-----------|-----------------|--------------|
| A Audit Registry | §4.1 | Registry/control plane | 10.1 A/V |
| V Validator / Control Plane | §4.1 | O4 ledger + O5 leases | 10.1 L |
| L O4 Ledger + O5 Leases | §4.1 | Loader + serializer | 10.1 S |
| S Canonical Loader + Serializer | §4.2 | Safe writer + logging | 10.1 W |
| W Safe Writer + CLI Logging | §4.3 | CLI/MCP contracts | 10.1 C |
| C CLI / MCP Contracts | §4.4 | Activation + doctor | 10.1 X |
| X Activation + Doctor | §4.4 | Cross-platform locking | 10.1 K |
| K Cross-platform Locking | §4.3/§4.4 | Release pipeline | 10.1 P |
| P Release Pipeline | §4.5 | Tests + lifecycle evidence | 10.1 T |
| T Tests + Lifecycle Evidence | §6 | Generated map + AGENTS | 10.1 M |
| M Generated Context Map + AGENTS | §4.5 | GitHub/Windows/PyPI (external) | 10.1 G/R/Y + §3 |

Lifecycle diagram (§10.2) matches the described code-first flow through
`Phase_C_Reconciliation → D1 → D2 → D3 → {D4 loop | D5} → Loose_Falsification →
D6_Pending`. No diagram-prose mismatch found; both directions close.

## 3. Quality assessment

The implementation is unusually well-reconciled to the spec. The most
security-sensitive surface — the safe writer — is the strongest part: the
device/inode/type binding discipline (§4.3) is realized as capture-while-open
plus recheck-before-every-name-op plus verify-after-replacement, and it is
matched by dedicated adversarial tests for staged-temp swap, backup-reservation
swap, phase-one source-binding swap, move-destination-after-rename, recreated
delete destination, ambiguous backup rename, disappeared move destination, and
parent-swap-after-validation (`tests/test_session_context.py:189-812`). The lock
opener is correctly centralized into `ontos/core/locking.py` and consumed by both
CLI and MCP callers, which discharges the §4.4 "centralize for both callers"
requirement rather than duplicating two subtly different openers — the right
design choice, and the Windows path is exercised via a simulated CRT backend that
asserts rejection happens before `msvcrt.open` is ever called.

The validator's fail-closed boundary is comprehensive: it normalizes and
quarantines roots, collections, rows, and downstream fields before any hashing,
`set`, sort, or lookup, so malformed input degrades to a diagnosed exit `1`
instead of a `KeyError`/`TypeError` exit `2`. The `required_version` eager-parse
fix is small, correct, and carries a comment that explains the failure mode it
guards, which will survive future maintenance.

Two quality caveats, both non-blocking. First, the committed evidence delta adds
a per-finding-ID special-case branch in the validator
(`is_control_plane = finding_id == "R2-control-plane-parity-1"` with inline
expected status/fix_commit/lifecycle); this does not scale as further R2 rows
advance and would read better as a per-row expected-state table. Second, the
same delta promotes that row to a status vocabulary
(`implemented_committed_parity_verified` /
`parity_verified_lifecycle_pending`) that spec v1.5 never names, so a reader
working only from the spec cannot predict it (see §5).

## 4. UX review

User-facing copy is accurate and actionable. The log-collision message names the
path and the two recovery choices; the archive-marker warning begins with the
exact spec string `Session log created, but archive marker was not updated:` and
surfaces as a distinct warnings-only exit `3` rather than being conflated with a
findings failure — this is the correct ergonomics for shell automation and is
called out in the migration doc (`Migration_v3_to_v4.md:175-177`). The
`required_version` diagnostics distinguish `Invalid [ontos].required_version:`
(malformed) from `Incompatible Ontos version:` (unsatisfied), identify the
offending clause as `version clause '<literal>'`, print that literal exactly once,
and point to the stable `#audit-remediation-compatibility-contracts` anchor
(direct-run probe over five ranges). Migration/manual copy documents the exit
taxonomy, `E_LOG_EXISTS`, `E_USER_INPUT`, `E_ACTIVATION_UNUSABLE`, reserved code
`4`, and the warnings-exit-`3` automation impact.

## 5. Issues found

### Blocking (Critical)

None. Every load-bearing spec v1.5 contract reproduced correctly under direct-run
against I1; no spec-vs-code divergence and no test-blessed divergence were found.

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-1 | The committed control-plane evidence delta (I1→HEAD) promotes `R2-control-plane-parity-1` to `status: implemented_committed_parity_verified` / `lifecycle_state: parity_verified_lifecycle_pending`, bound to I1 itself. Spec v1.5 never names this status vocabulary (§4.1 describes validator checks and the I0-binding baseline but not a `parity_verified` promotion), so the committed evidence is not traceable to the reviewed spec. It is honest and internally consistent (parity, not lifecycle; live+local parity passes; lifecycle stays pending), but a reader of v1.5 cannot predict it. | `manifests/project-ontos-audit-remediation-registry.yaml` R2 row + `scripts/validate-audit-remediation-registry.py:1265-1290` | static-inspection | `git diff 05b090d HEAD -- manifests/ scripts/validate-audit-remediation-registry.py` | Add one line to spec §4.1 (or the revalidation report) defining the parity-verified status/lifecycle vocabulary and that I1 is the control-plane fix commit, so the evidence delta is spec-traceable. Non-blocking: evidence is honest and validator/test-enforced. |

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-2 | Validator special-cases the control-plane row by literal finding-ID with inline expected status/fix_commit/lifecycle; each future R2 lifecycle promotion needs another bespoke branch. | `scripts/validate-audit-remediation-registry.py:1266-1290` | static-inspection | read the `is_control_plane` branch | Replace with a per-finding expected-state mapping keyed by ID. |
| P-3 | Some §11/§4 current-tree line anchors are approximate after the I0→I1 edits (e.g. `ontos/core/config.py:223-266` for runtime version compat brackets `version_satisfies_requirement`+start of `required_version_incompatibility`; still correct region, not exact). | spec §11, §4.4 | static-inspection | compare cited ranges against I1 files | Optional: refresh current-tree ranges to I1; frozen `b6f89d7:` anchors are already correct. |

### Reachability gaps

None. Each new validation-layer rule is reachable end-to-end from a citable
input: the typed/quarantine rules trigger from `main()` on malformed registry
YAML (direct-run battery in §1); the enum-closed lease filter triggers from
`lease_state: acitve`; the `#146`/`#147` membership rule triggers from dropping a
required program row; the lock single-link rule triggers from the hard-link
regressions (`test_session_context.py:946,974`); the eager-parse rule triggers
from `>=99.0.0, not-a-range`.

## 6. Positive observations

- Direct-run reproduction of the §4.1 fail-closed boundary across nine distinct
  malformed control-plane shapes all yielded exit `1`/`FAILED` — the "quarantine
  before all consumers, no finite subscript list" doctrine is genuinely realized,
  not asserted.
- The B.1 X-M1 log-symlink regression is provably non-vacuous: it removes
  `docs/logs`/`docs`, symlinks `docs` outside, asserts the default path *would*
  resolve outside, runs `log --auto` with no configured `logs_dir`, and proves
  the external sentinel and directory are untouched
  (`tests/commands/test_log.py:193-223`).
- The lock opener centralization (§4.4) is the correct single-pipeline design and
  removes the frozen-I0 MCP plain-open gap without duplicating the no-follow
  logic.
- Template-03 blessing-test greps returned zero hits — no test documents a
  spec-vs-code gap instead of catching it.
- Focused suites green under direct-run: registry-validator + config + stub
  parity `270 passed`; session-context + log + MCP locking + write-tools +
  contention `111 passed`.

## Verdict

Approve

I1 satisfies spec v1.5's Phase C construction gates: every load-bearing serializer,
writer, logging, lock, validator, activation, CLI-envelope, and release-workflow
contract reproduced correctly under direct-run, with non-vacuous adversarial
regressions and clean fail-closed behavior. No blocking or reproducible defect was
found. The only findings are a should-fix spec-traceability gap for the
parity-verified status vocabulary the committed evidence delta introduces (P-1)
and two minor maintainability/anchor nits (P-2, P-3), none of which gate D.2. This
verdict is umbrella lifecycle-local; it does not certify D.5, D.6, any child issue,
Windows, TestPyPI/PyPI, merge, tag, publication, or release — all of which remain
explicit external/pending per the spec's nonclaims.

## Notes

- Evidence labels: `direct-run` for all behavioral reproductions (validator
  battery, `required_version` probe, focused suites, artifact existence);
  `static-inspection` for code-shape/spec-traceability observations (P-1/P-2/P-3)
  and for external-pending surfaces (Windows runner, TestPyPI/PyPI service),
  which were not synthesized.
- Scope discipline: I did not read D.1, B.1/B.2/B.3 verdicts, dispatch
  result/receipt files, the C-phase falsification findings, or tracker
  conclusions; findings are from independent inspection of the spec, the base→I1
  diff, the I1→HEAD evidence delta, and direct execution.
- No blocking finding, so no orchestrator-preflight evidence was required; all
  reproductions are runnable from this worktree with `.venv/bin/python`.

## Final report — project-ontos-audit-rebaseline-remediation / D.2 / peer / claude
- Status: completed
- Artifacts written: docs/reviews/project-ontos-audit-rebaseline-remediation/D.2-claude-peer.md
- Smoke checks: registry validator local run = pass (direct-run); focused suites 270+111 = pass (direct-run); blessing-test greps = clean (direct-run)
- Cardinality checks: single-artifact write (only D.2-claude-peer.md) = pass (direct-run)
- Commit: not committed (Peer worker does not commit; orchestrator stages/commits)
- Notes: Verdict Approve; one should-fix (P-1 spec-traceability of parity-verified status), two minor (P-2 validator special-case, P-3 anchor drift). No blocking findings.
