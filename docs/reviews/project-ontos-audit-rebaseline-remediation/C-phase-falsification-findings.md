---
id: project-ontos-audit-rebaseline-remediation-C-falsification-findings
deliverable_id: project-ontos-audit-rebaseline-remediation
type: review
phase: C
role: falsifier
family: codex
status: complete
phase_close_commit: 05b090d53f7b0c9c4afdbb5fb23ab58cdfa01fa0
depends_on:
  - project-ontos-audit-rebaseline-remediation-spec
---

# Phase C independent falsification findings

## Boundary

This is a non-receipt implementation falsification pass run after the first
Phase C green suite and before D review. It does not add findings to the
100-row historical/revalidation registry, change any release state, or certify
Phase C. Stable `C-FZ-*` IDs preserve these lifecycle-local findings for B.2,
D.2, and D.5.

## Reproduced findings and dispositions

| ID | Reproduced failure | Pre-fix observable | Required disposition | Current state |
|---|---|---|---|---|
| `C-FZ-1` | `required_version` compatibility used lazy `all(...)`, so an earlier false comparison hid a malformed later clause | `>=99.0.0, not-a-range` returned `Incompatible...` instead of `Invalid...`; config validation could accept the malformed range | Parse every clause eagerly before reducing compatibility; identify the bad clause once | frozen at I1; focused verified |
| `C-FZ-2` | Staged, destination, source, backup, or rollback names could change between descriptor capture and name-based mutation | A swapped temp poisoned the destination; a recreated DELETE target still reported success; WRITE/MOVE overwrote a destination created in the rename window; an ambiguous completed backup rename lost its recovery receipt; a vanished MOVE destination silently lost the source; rollback could unlink or rename an unbound racer | Capture device/inode/type while open; require positive or explicit-absent destination bindings inside every replace; reconcile ambiguous backup completion; treat vanished MOVE destinations as rollback failures; verify final absence after DELETE; bind every rollback rename/unlink and preserve recovery evidence on mismatch | frozen at I1; focused verified |
| `C-FZ-3` | Malformed registry or #146/#147 child-manifest roots/scopes reached exception exit `2` | Registry/child list roots, `scope: []`, unhashable paths, non-mapping sequencing, null bundle/gap lists, null gate rows, and a list receipt-inventory root emitted `ERROR` | Normalize every control-plane root, collection, row, and downstream field before consumers and return exit `1`/`FAILED` | frozen at I1; focused verified |
| `C-FZ-4` | `lease_state` accepted any non-empty string, allowing a typo to remove a program from the active collision set | changing `active` to `acitve` let an overlap pass | Enum-validate finding/program state fields before partitions and filters | frozen at I1; focused verified |
| `C-FZ-5` | Live GitHub parity ignored returned issue identity/title and allowed phantom epic checklist IDs | issue #146 payload with `number: 999` and an extra `D6a-test-gaps-3` epic row added no error | Require exact issue identity, typed title, and exact checklist ID sets | frozen at I1; local+live parity verified |
| `C-FZ-6` | A multi-link `.ontos.lock` could alias an external file; the Windows backend also had a post-open window before writing its one-byte sentinel | A simulated msvcrt acquisition changed an external hard-link alias from empty to NUL after the initial link-count check | Reject multi-link handles again immediately before acquisition and use non-mutating `LockFileEx`/`UnlockFileEx`; never extend an empty lockfile | frozen at I1; focused verified; real Windows execution pending |
| `C-FZ-7` | Finding ownership, provenance, rendered ledger rows, and lease order were shape-valid but not authority-valid | Unrelated `root_program`, absolute evidence, corrupt baseline/base/fix/release refs, bogus O4 SHAs, and reversed O5 order passed | Cross-check owner roots, commit/release/status implications, exact program authority, canonical paths, fully parsed O4 rows, and ordered O5 rows | frozen at I1; local+live parity verified; umbrella D review pending |
| `C-FZ-8` | CLI setup could mutate before the safe writer, and exclusive creation accepted a symlinked workspace root | `stub` created an external directory through a symlink before `commit()` rejected it; direct exclusive creation wrote through a symlinked root | Remove eager parent creation and reject lexical workspace-root symlink/reparse points before resolution for every writer entry point | frozen at I1; focused verified |
| `C-FZ-9` | Workspace-root and lockfile names could be rebound after validation, and cleanup errors could strand the new directory guard | Replacing the root redirected a buffered or MCP write; unlinking `.ontos.lock` allowed a second writer to lock a new inode; `owns_lock=False` accepted an arbitrary callable or a guard for another workspace; a raising `close()` leaked the root FD and could mask the primary error | Bind the root from buffer/preflight through commit; add a POSIX directory-inode flock; require a typed same-workspace outer guard; verify root/lock identities before and after mutation; centralize exception-safe cleanup while preserving the primary failure | frozen at I1; focused verified |
| `C-FZ-10` | Re-running `ontos map` on an unchanged document graph still rewrote generated timestamps | Consecutive commands produced different hashes and dirtied the tracked map despite identical document content | Compare generated maps with only the three owned timestamp lines normalized; skip the write entirely when semantic content is unchanged, preserving bytes and mtime | frozen at I1; focused verified |

## Focused evidence

- Writer/lock/config/control-plane combined matrix: `315 passed`.
- Log/archive-marker public warning matrix: `13 passed`.
- Second-pass writer/lock/config/log/stub/control-plane matrix: `414 passed`.
- Final control-plane/feature matrix: `461 passed`.
- Final writer/lock/MCP matrix, including root replacement, lock unlink,
  wrong-guard, and cleanup-failure regressions: `124 passed`.
- Map idempotence/isolation matrix: `36 passed`; two consecutive repository
  runs preserved both the SHA-256 and mtime.
- Registry validator: PASS in local and live-GitHub parity modes with the exact
  91+9 counts and unchanged status partition.
- `git diff --check`: PASS.
- Fresh post-fix full suite: `1679 passed`, with one pre-existing deprecation
  warning. The non-review worktree status was byte-for-byte unchanged before
  and after.
- Detached clean-snapshot replay at I1: `1679 passed`; porcelain was empty
  before and after the run.

## Nonclaims

- No Windows runner or TestPyPI service result is synthesized.
- No child issue, D.5, D.6, release, or shared-tree integration blocker is
  certified by this pass.
- `C-FZ-*` are lifecycle-local findings. I1 is their umbrella implementation
  snapshot; it does not rewrite historical child-program provenance or certify
  any #146–#157 issue lifecycle.
