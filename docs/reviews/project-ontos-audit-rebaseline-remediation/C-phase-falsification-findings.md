---
id: project-ontos-audit-rebaseline-remediation-C-falsification-findings
deliverable_id: project-ontos-audit-rebaseline-remediation
type: review
phase: C
role: falsifier
family: codex
status: active
depends_on:
  - project-ontos-audit-rebaseline-remediation-spec
---

# Phase C independent falsification findings

## Boundary

This is a non-receipt implementation falsification pass run after the first
Phase C green suite and before B.2/D review. It does not add findings to the
100-row historical/revalidation registry, change any release state, or certify
Phase C. Stable `C-FZ-*` IDs preserve these lifecycle-local findings for B.2,
D.2, and D.5.

## Reproduced findings and dispositions

| ID | Reproduced failure | Pre-fix observable | Required disposition | Current state |
|---|---|---|---|---|
| `C-FZ-1` | `required_version` compatibility used lazy `all(...)`, so an earlier false comparison hid a malformed later clause | `>=99.0.0, not-a-range` returned `Incompatible...` instead of `Invalid...`; config validation could accept the malformed range | Parse every clause eagerly before reducing compatibility; identify the bad clause once | implemented uncommitted; focused verified |
| `C-FZ-2` | A staged temp name could be unlinked and replaced after its descriptor closed but before Phase 2 rename | `commit()` accepted a swapped symlink and left the destination naming an external sentinel | Capture device/inode/type while open; recheck staged, backup, move/delete, and final bindings immediately around mutations; roll back on mismatch | implemented uncommitted; focused verified |
| `C-FZ-3` | Malformed registry or #146/#147 child-manifest roots/scopes reached exception exit `2` | registry list root, child list root, `scope: []`, and unhashable allowed paths emitted `ERROR` | Normalize every control-plane root/scope before consumers and return exit `1`/`FAILED` | implemented uncommitted; focused verified |
| `C-FZ-4` | `lease_state` accepted any non-empty string, allowing a typo to remove a program from the active collision set | changing `active` to `acitve` let an overlap pass | Enum-validate finding/program state fields before partitions and filters | implemented uncommitted; focused verified |
| `C-FZ-5` | Live GitHub parity ignored returned issue identity/title and allowed phantom epic checklist IDs | issue #146 payload with `number: 999` and an extra `D6a-test-gaps-3` epic row added no error | Require exact issue identity, typed title, and exact checklist ID sets | implemented uncommitted; local+live parity verified |
| `C-FZ-6` | A multi-link `.ontos.lock` could alias an external file; the Windows backend may write its one-byte compatibility sentinel | a simulated msvcrt acquisition changed the external hard-link target from empty to NUL | Reject POSIX `st_nlink > 1` and Windows `nNumberOfLinks > 1` before backend writes | implemented uncommitted; focused verified; real Windows execution pending |
| `C-FZ-7` | Finding ownership and path fields were shape-valid but not authority-valid | unrelated `root_program` and absolute evidence such as `/etc/hosts` passed | Cross-check owner roots and require canonical non-escaping repo-relative evidence/scope/lease paths | implemented uncommitted; focused verified |

## Focused evidence

- Writer/lock/config/control-plane combined matrix: `315 passed`.
- Log/archive-marker public warning matrix: `13 passed`.
- Registry validator: PASS in local and live-GitHub parity modes with the exact
  91+9 counts and unchanged status partition.
- `git diff --check`: PASS.
- The earlier full suite (`1603 passed`) predates the `C-FZ-*` fixes and is not
  reused as their proof. A fresh full clean-snapshot suite remains mandatory
  before C-close.

## Nonclaims

- No Windows runner or TestPyPI service result is synthesized.
- No child issue, D.5, D.6, release, or shared-tree integration blocker is
  certified by this pass.
- The working-tree fixes have no `fix_commit` until the C-close snapshot is
  deliberately committed and independently reviewed.
