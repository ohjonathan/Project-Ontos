---
id: audit-rb-D2-cp
deliverable_id: project-ontos-audit-rebaseline-remediation
phase: D.2
role: peer
family: claude
evidence_labels_used: [direct-run, static-inspection, not-run]
status: completed
---

# Peer Review — project-ontos-audit-rebaseline-remediation / D.2 / claude

**Lens:** quality and completeness. Is the Phase C implementation well-designed,
complete, clear, and implementable/maintainable without follow-up questions?

**Scope of this review.** Spec v1.5 (`docs/specs/project-ontos-audit-rebaseline-remediation-spec.md`)
against the exact Phase C implementation I1
`05b090d53f7b0c9c4afdbb5fb23ab58cdfa01fa0` (reconciliation on top of I0
`b6f89d77e7fb684b8bd9a181a24c773d5777397a`; historical base
`bf91b42f4eb5ba2ed6e0e3ea5e76d22ec6d7ec95`). I inspected the base→I1 diff and
the current committed control-plane evidence delta (I1→HEAD `bfc0ca8`).

**Branch / commit attestation (Template 03 file-existence discipline).**
`git branch --show-current` = `codex/audit-rebaseline-remediation-lifecycle`;
`git rev-parse HEAD` = `bfc0ca8112b0212207fbca91f2d7d3765f2507ab`. I verified
`git merge-base --is-ancestor` proves I0 → I1 → HEAD linear ancestry
(direct-run). I confirmed the `ontos/` package tree is **byte-identical**
between I1 and HEAD (`git diff --stat 05b090d5 HEAD -- 'ontos/**'` is empty),
so package-behavior tests run from the working tree exercise exact I1 code. The
only I1→HEAD code/test delta is `scripts/validate-audit-remediation-registry.py`
(+24), `tests/test_audit_remediation_registry_validator.py` (+29), and the
registry row for `R2-control-plane-parity-1` — i.e., the "current committed
control-plane evidence delta" that records I1's own control-plane fix as
`implemented_committed_parity_verified` / `fix_commit: 05b090d5`. I ran the
validator + suite at **both** I1 and HEAD to confirm each is internally
self-consistent. Registry validator tests were run from a throwaway detached
worktree at I1 (`/tmp/ontos-i1-review`) to preserve this worktree.

External Windows, TestPyPI/PyPI, and live-GitHub service claims remain external
and are labelled `not-run`; I did not synthesize them.

## 1. Completeness check

The Phase C reconciliation implements the §4 construction gates that B.2 raised.
Spot-verified surfaces (direct-read at I1 / direct-run tests):

- **§4.1 typed/quarantine control plane** — `scripts/validate-audit-remediation-registry.py`
  structurally validates registry, `findings`, `programs`, `shared_path_leases`,
  `shared_tree_integration`, child-manifest roots, and GitHub parity metadata
  before every consumer; malformed input yields `main()` exit `1`/`FAILED`,
  never exit `2`/`ERROR`/traceback (direct-run repro below).
- **§4.2 serializer + ID contract** — `ontos/core/schema.py:83-97`
  `validate_document_id` matches spec copy exactly; `stub.py:180-192` routes
  CLI IDs through it under `E_USER_INPUT` (static-inspection + tests). **Gap:**
  `rename` does not — see P-1.
- **§4.3 safe writer + logging** — `ontos/core/context.py` captures a no-follow
  `_EntryBinding` (device/inode/type) for staged writes, backup reservations,
  and move/delete sources, and rechecks it immediately before every
  rename/unlink and after replacement (`_verify_entry_binding`, lines
  394-577); `commands/log.py` routes creation through the exclusive no-follow
  writer, keeps `logs_dir` lexical (no `.resolve()`), preserves the
  no-overwrite `E_LOG_EXISTS` fact plus the title/move-or-remove recovery hint,
  and renders the archive-marker failure as a visible warnings-only exit `3`.
- **§4.4 CLI/MCP/activation/lock** — `ontos/core/locking.py` gates on
  `st_nlink == 1` / `nNumberOfLinks == 1` before the backend writes its
  sentinel; both `SessionContext.commit` and MCP `workspace_lock` share the
  same `open_lock_file`/`WorkspaceLockGuard` primitives; `config.py`
  `required_version` parses every clause eagerly (list comprehension, lines
  252-254) and identifies the offending clause literal exactly once; exit
  taxonomy omits `4` (reserved, tested).
- **§4.5 release/tests/map** — `check_release_artifact.py`, `command_registry.py`,
  `core/locking.py` all exist (`git ls-files`); `map.py` `_write_context_map_if_changed`
  achieves double-generation stability.

No mandatory §4 surface is missing. The one substantive gap is a CLI ID
consumer left unreconciled (P-1).

## 2. Diagram-prose cross-reference

Both §10 diagrams reconcile with the §4 prose and §3 dependencies. External
nodes are correctly marked. No mismatch found (mismatch would be blocking).

| Diagram component | In prose? | Prose component | In diagrams? |
|-------------------|-----------|-----------------|--------------|
| A Audit Registry | §4.1 | Registry/control plane | A/V |
| V Validator / Control Plane | §4.1 | O4 ledger + O5 leases | L |
| L O4 Ledger + O5 Leases | §4.1 | Loader + serializer | S |
| S Canonical Loader + Serializer | §4.2 | Safe writer + logging | W |
| W Safe Writer + CLI Logging | §4.3 | CLI/MCP contracts | C |
| C CLI / MCP Contracts | §4.4 | Activation + doctor | X |
| X Activation + Doctor | §4.4 | Cross-platform locking | K |
| K Cross-platform Locking | §4.4 | Release pipeline | P |
| P Release Pipeline | §4.5 | Tests + lifecycle evidence | T |
| T Tests + Lifecycle Evidence | §4.5/§6 | Generated map + AGENTS | M |
| M Generated Context Map + AGENTS | §4.5 | EXTERNAL GitHub/Windows/TestPyPI | G/R/Y |
| G/R/Y EXTERNAL (GitHub/Windows/TestPyPI) | §3 | — | — |

§10.2 lifecycle states (B.2 code-first → Phase C reconciliation → D.1…D.6 +
loose falsification stop boundary) match §1 and the code-first sequencing prose.

## 3. Quality assessment

The writer and locking layers are the strongest parts of this implementation and
read as production-grade defensive code. `context.py` treats every name-based
mutation as adversarial: it pins parent directory descriptors with `O_NOFOLLOW`,
operates via `*at` syscalls relative to the pinned fd, and revalidates a frozen
device/inode/type binding immediately before and after each rename/unlink. The
ambiguous-backup-rename reconciliation (lines 453-505) is subtle but correct —
it distinguishes "backup received the original" from "empty reservation" by
re-statting after an ambiguous exception rather than assuming, and preserves a
recovery entry when it genuinely cannot tell. The Windows reparse-point handling
is symmetric with POSIX and cleanly `# pragma: no cover`-guarded. A mid-level
engineer could maintain this, though the commit critical section is long and
would benefit from the eventual extraction the module docstring already gestures
at.

The `required_version` clause parser correctly closes the eager-evaluation gap:
using a list comprehension rather than a generator into `all()` means a
later malformed clause is not masked by an earlier `False` comparison, and each
`ConfigError(f"...{clause!r}")` names exactly one offending clause literal. The
validator's fail-closed quarantine is well-factored and, importantly, reachable
(§5).

The single design blemish is consistency: §4.2 requires a *single* canonical ID
validator across CLI ID consumers, and the reconciliation wired `stub` but not
`rename` (P-1). This is the exact "divergent regex / regex-only error string"
anti-pattern the spec names; it is currently behavior-equivalent but is a second
source of truth for the ID grammar and a different public error surface.

## 4. UX review

`E_LOG_EXISTS` copy is genuinely actionable: it names the colliding path, states
no overwrite, and gives two concrete recoveries (different `--title`, or
intentionally move/remove). The archive-marker warning
(`Session log created, but archive marker was not updated: …`) surfaces in human
stderr, in JSON `warnings[]`, and via exit `3`/`result.status: warnings` while
retaining the created log path in `data` — a good "loud but non-destructive"
signal (subprocess-tested). Minor: under `--quiet`, the warning text is
suppressed although exit `3` is still returned; this is defensible (quiet
suppresses all output) but means the only signal in quiet mode is the code.

The rename ID error (`new_id must match ^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$`)
is a raw regex — worse UX than the canonical plain-language copy a user sees from
`stub`. Two different messages for the same grammar is an ergonomics wart.

## 5. Issues found

### Blocking (Critical)

None. No spec-vs-code divergence, diagram mismatch, or reachability gap rose to
blocking under direct-run.

### Should-fix (Major)

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-1 | §4.2 requires "**Every** CLI-supplied ID must call the same canonical validator and surface its message through `E_USER_INPUT`; a CLI must not maintain a divergent regex or regex-only error string." The `rename` command (a CLI mutation command explicitly in the §4.2 MODIFY scope, and its Phase-C-modified MCP tool) violates this literally: it keeps its own `_ID_PATTERN` regex and emits a regex-only message under code `invalid_new_id` (MCP maps → `E_INVALID_ID`, not `E_USER_INPUT`). Currently behavior-equivalent to canonical (same accept/reject set), so no user gets a wrong validation outcome — but it is a second source of truth for the ID grammar (drift risk) and a divergent public error surface, and it is untested for canonical parity. | `ontos/commands/rename.py:28,324,326-327`; MCP mapping `ontos/mcp/rename_tool.py:77`; canonical `ontos/core/schema.py:83-97`; parity test covers only `stub` (`tests/commands/test_stub_parity.py:127`) | direct-run: canonical → `"Document id must start and end with an alphanumeric character and contain only letters, numbers, '_', '-', or '.'"`; rename branch → code `invalid_new_id`/message `"new_id must match ^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$"`. static-inspection: `_ID_PATTERN` duplicates `DOCUMENT_ID_PATTERN`. | Load the venv python and run: `from ontos.core.schema import validate_document_id; import ontos.commands.rename as r; validate_document_id("bad id!")` (canonical `ValueError` copy) vs `r._ID_PATTERN.match("bad id!")` is `None` with the regex-only message at line 327. | Route `rename` `new_id` through `validate_document_id`, surface `E_USER_INPUT` with the canonical copy, delete the duplicated `_ID_PATTERN`, and add a rename canonical-parity regression mirroring `test_stub_invalid_id_uses_canonical_copy_and_user_error_code`. |

### Minor

| ID | Description | Location | Evidence | Reproduction | Suggested action |
|----|-------------|----------|----------|--------------|------------------|
| P-2 | `rename` uses `_ID_PATTERN.match(...)` rather than `.fullmatch(...)`. With the trailing `$` and `.strip()`ed input this is currently equivalent, but `.match` + `$` permits a trailing newline and is a latent divergence from the canonical `fullmatch`. Subsumed by the P-1 fix. | `ontos/commands/rename.py:301,324` | static-inspection | n/a | Fold into P-1 (use the canonical validator). |
| P-3 | Under `--quiet`, the archive-marker warning text is not printed although exit `3` is still returned; spec §4.3 emphasizes "the failure is not silent." Defensible (quiet suppresses output) but worth a one-line comment so future readers don't read it as a regression. | `ontos/commands/log.py:357-361` | static-inspection | Run `ontos log --quiet` where `.ontos` marker write fails → exit 3, no stderr text. | Optionally emit the warning even under `--quiet`, or comment the intentional suppression. |

### Reachability gaps

None. Every new validation-layer rule I checked is reachable end-to-end
(direct-run):

- **Registry quarantine → exit 1** rule: independently reproduced with five
  malformed shapes (list root, `findings` not a list, row not a mapping, empty
  file, garbage scalar) — all returned `main()` exit `1` with `FAILED`, no
  `ERROR`, no `Traceback`. The table-driven suite injects these via
  `monkeypatch` of `REGISTRY_PATH` and asserts the same (193 tests at I1).
- **Archive-marker warnings-only exit `3`** rule: reached by
  `tests/commands/test_log.py` subprocess cases asserting `returncode == 3`,
  the warning prefix, and `result.status == "warnings"`.
- **Eager `required_version` clause parse** rule: reached by
  `tests/core/test_config_phase3.py` (all passed), including earlier-false /
  later-invalid orderings.

## 6. Positive observations

- The no-follow writer (`context.py`) is genuinely thorough: frozen
  device/inode/type bindings rechecked before and after every mutation, `*at`
  syscalls against pinned fds, symmetric POSIX/Windows handling, and an honest
  best-effort rollback that preserves recovery evidence rather than guessing.
- CLI and MCP lock paths are unified on one primitive set
  (`ontos/core/locking.py`) with `st_nlink`/`nNumberOfLinks == 1` enforced
  before the advisory backend can touch the file — the §4.4 gate is real, not
  decorative.
- The control-plane validator fails closed to exit `1`/`FAILED` across every
  malformed shape I threw at it, independently reproduced outside its own test
  fixtures — the spec's "quarantine before all consumers, never a bare
  KeyError/exit 2" boundary holds.
- The registry honestly preserves the 41 `confirmed_open` + 7 partial states at
  I1 (validator direct-run), and the I1→HEAD evidence delta records only I1's
  own control-plane parity fix — no scope overclaim, no reinterpretation of open
  findings.
- D-phase blessing-test greps (Template 03) over the I1 test suite returned
  **zero** hits for spec-vs-code-blessing comment/assertion patterns — Phase C
  did not bury a divergence in a passing test.
- 225 focused package tests + 193 (I1) / 194 (HEAD) validator tests all pass.

## Verdict

Request changes

The implementation is high quality and complete across §§4.1–4.5, with an
exceptionally careful writer/lock layer and no blocking, reachability, or
diagram defects. I am requesting changes for a single, cited, reproduced
Should-fix: P-1 is a literal violation of the §4.2 construction requirement that
**every** CLI-supplied ID use the one canonical validator and `E_USER_INPUT`
copy — `rename` keeps a divergent regex and a regex-only error string, and is
untested for canonical parity. The gap is behavior-equivalent today, so a
consolidator may reasonably treat it as non-blocking and track it; I flag it at
Major because it contradicts an explicit Phase C gate and the fix is small
(route `rename` through `validate_document_id`, drop `_ID_PATTERN`, add a
parity regression). P-2/P-3 are minor and fold into the same change.

## 8. Notes

- Per instructions I did not read D.1, B-family verdicts, D.2 sibling reviews,
  dispatch results/intents, receipts, or tracker conclusions; findings derive
  from the base→I1 diff, direct-read of I1 source, and direct-run of focused
  tests + independent reproductions.
- External Windows / TestPyPI-PyPI / live-GitHub behavior is `not-run` and left
  external, as the spec's §3 dependencies and §9 exclusions require.
- Ran focused suites only; did not run the full `pytest`. Created a throwaway
  detached worktree at I1 (`/tmp/ontos-i1-review`) for exact-I1 validator runs
  and preserved this worktree; it can be removed with `git worktree remove`.
- `ontos map`/`ontos log` activation steps from CLAUDE.md were not required for
  this review task and were not run against the control plane.
