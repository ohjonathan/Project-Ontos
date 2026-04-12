# Ontos v4.1 Track B — Design Note

> **This is a design note, not a handoff.** It names the interfaces
> Track B will consume and the tool contracts Track B will deliver. It
> does *not* authorize branch creation, Dev-agent spawning, or PRs.
> Execution is gated by §13.

## Drafting-context caveat

This note was drafted against a pre-#85 snapshot of the repo. Since
then, PR #85 ("v4.1 Track A — portfolio index, read tools, flock
substrate") and PR #87 ("update legacy SessionContext lock tests for
flock") have landed on `main`. That means some Track A items this note
lists as "not yet landed" are in fact present (notably flock on
`.ontos.lock`, which is already the `SessionContext` lock primitive —
see §4). The §13 checklist must be re-audited against current `main`
before Track B kickoff; items that are already satisfied become
verification steps rather than dependencies.

Everything below is written as if pre-#85, with forward-pointers where
current `main` has moved past the draft's assumptions.

## 1. Context & status

The draft this note refines was written against a post-Track-A repo
state that did not exist when the plan was drafted: no v4.1 spec
addendum, no `workspace_lock` primitive, no `portfolio` / `bundler` /
`portfolio_config` / `scanner` modules, `SessionContext` presumed to
still use PID-file locking. PR #85 has since landed the flock substrate
and parts of the portfolio index, which collapses some of the "Track A
must produce" bullets below into "Track A has produced; verify."

For the shipped v4.0 baseline, see `.ontos-internal/strategy/v4.0/`.

## 2. Scope (unchanged from draft)

Track B delivers:

- `scaffold_document` — single-file write tool.
- `log_session` — single-file write tool.
- `promote_document` — single-file write tool.
- `rename_document` — multi-file write tool with body-reference
  rewriting and git-clean precondition.
- Bundle config wiring (`bundle_token_budget`, `bundle_max_logs`,
  `bundle_log_window_days`) consumed by the read-side bundle tool.
- Deferred SF/m closures inventoried in §11.

## 3. Track A deliverables this note depends on

(Replaces the draft's "pre-flight" section, which falsely implied these
were already present.)

| # | Deliverable | Contract Track B consumes |
|---|---|---|
| 3.1 | **Spec addendum document** | Versioned file at a canonical path, listing CB-1..CB-11 contracts by ID. |
| 3.2 | **`workspace_lock()` primitive** | flock-based; lock file `.ontos.lock` at repo root; reentrant-by-handle or with `owns_lock` opt-out (see §4). Already substantially present post-#85. |
| 3.3 | **Portfolio index API** | `rebuild_workspace(slug: str, root: Path) -> None` with FTS5 parity to the current scanner output. Called by A3 rollback path. |
| 3.4 | **Bundle config module** | Three fields + defaults (see §7); `get_context_bundle()` reader consumes them. |
| 3.5 | **Slugifier surface** | Two functions only: `scanner.slugify` (workspace identity) and the existing `log._slugify` (title→filename). No third slugifier. |
| 3.6 | **Registry loader** | `load_registry_records()` returning portfolio registry rows; used by tools that need workspace lookups. |
| 3.7 | **CB-1..CB-11 hard-contracts table** | Location TBD by Track A; cited by each tool's test plan. |
| 3.8 | **`.gitignore` addition** | `.ontos.lock` (lock file must never be committed). |

## 4. A1 — lock discipline (conditional)

**Current code (verified at HEAD `4ee3e54`):** `SessionContext` already
uses flock, not a PID file. Lock path is built at `ontos/core/context.py:151`
as `self.repo_root / ".ontos.lock"`. `_acquire_lock` uses
`fcntl.flock(..., LOCK_EX | LOCK_NB)` at `context.py:227`. `_release_lock`
is at `context.py:243`. This means the "Track A must switch from PID to
flock" framing in the draft is already obsolete — Track A shipped the
substrate in #85.

**What Track B still needs on top of the substrate:**

- An `owns_lock: bool = True` parameter on write-path callers that can
  be re-entered under an already-held `workspace_lock()` (e.g., inside
  a tool that acquires the workspace lock itself). Default `True`
  preserves every existing caller; passing `False` from nested callers
  avoids self-deadlock.
- Tests: (a) contention — two writers race; second waits or fails
  cleanly; (b) write-vs-read — reader does not block on writer's lock
  unless explicitly designed to; (c) regression — a scenario that
  *would* deadlock without `owns_lock=False` being honored on the
  inner call.

If the substrate is later replaced (e.g., to a platform-abstracted
lock), the `owns_lock` contract still applies at the same call sites.

## 5. A2 — slugifier binding

Exactly two slug functions across the system:

| Function | Purpose | Location |
|---|---|---|
| `scanner.slugify` | Workspace identity (stable slug derived from repo root or an explicit identifier). | Track A deliverable; not yet created. |
| `_slugify` | Title → filename (existing behavior). | `ontos/commands/log.py`. |

Per-call-site binding (to be finalized once `scanner.slugify` lands):

| Call site | Slug function |
|---|---|
| `scaffold_document` — workspace resolution | `scanner.slugify` |
| `scaffold_document` — new-file naming | `log._slugify` |
| `log_session` — workspace resolution | `scanner.slugify` |
| `log_session` — new-file naming | `log._slugify` |
| `promote_document` — workspace resolution | `scanner.slugify` |
| `rename_document` — workspace resolution | `scanner.slugify` |
| `rename_document` — new filename | existing rename.py path logic |

**Rule:** no third slugifier is introduced. If a new call site needs
slugging, it binds to one of the two above; if neither fits, the call
site's requirements are wrong.

## 6. A3 — DB/files consistency

On commit failure + rollback, the portfolio index can drift from the
filesystem. To re-converge: after any exception path in
`SessionContext.commit()`, re-invoke
`rebuild_workspace(slug, root)` from §3.3.

**Hook point:** the `except Exception as e:` block at
`ontos/core/context.py:189-199`. Today that block cleans up temp files,
records the error via `self.error(...)`, and re-raises. Track B adds
the `rebuild_workspace` call *before* the re-raise, guarded so that a
rebuild failure is recorded (via `self.error`) and does not mask the
original exception.

## 7. A4 — bundle config defaults

Track A module (not yet created as of the draft; cross-check against
current `main` before implementation):

```
bundle_token_budget      = 8000
bundle_max_logs          = 20
bundle_log_window_days   = 30
```

Truncation policy: **tail-first** — when over budget, drop from the
*oldest* logs first, preserving the most recent session logs intact.
The reader `get_context_bundle()` reads these three values; Track B
plumbs them through `.ontos.toml` with the defaults above.

## 8. A5 — `.gitignore`

Track A must ensure `.ontos.lock` appears in `.gitignore`. Track B
verifies presence (does not add). If missing at Track B kickoff, file
a one-line PR on Track A's side, not Track B's.

## 9. A6 — rename semantics (VERIFIED)

**Verified at HEAD `4ee3e54`.** `ontos/commands/rename.py:221` reads:

```python
ctx.buffer_write(file_plan.path, file_plan.new_content)
```

There is **no** `os.rename` and **no** `buffer_move` in the rename
command's apply loop. Rename edits file content in place — it rewrites
references inside bodies; it does not move files on disk.

**Implication for `rename_document` MCP tool:** the MCP tool must match
this semantic exactly. It does not call a filesystem rename on its own.
All updates flow through `ctx.buffer_write` → `ctx.commit()`.

Reference discovery uses `scan_body_references` at
`ontos/core/body_refs.py:111` (signature:
`scan_body_references(path, body, *, context_lines, rename_target,
known_ids, include_skipped)`).

## 10. Tool contracts

### 10.1 `scaffold_document` (single-file)

| Path | Behavior |
|---|---|
| Happy | Creates a new document in the target workspace; buffer-writes once; commits. |
| Contention | Another writer holds `.ontos.lock`; caller returns a structured "locked" error. |
| Partial-commit recovery | Temp file present, final not renamed; §6 cleanup path applies; no index rebuild needed because no prior record was touched. |
| `read_only` refusal | If the workspace is configured read-only, return a refusal code before any buffer_write. |
| Missing `workspace_id` | Fall back to the served workspace; explicit `workspace_id` values are still validated. |

### 10.2 `log_session` (single-file)

As scaffold, with workspace-specific log path derivation using
`log._slugify` for the filename.

### 10.3 `promote_document` (single-file)

As scaffold, with frontmatter mutation as the only content change.
Cannot traverse workspace boundaries.

### 10.4 `rename_document` (multi-file)

| Path | Behavior |
|---|---|
| Precondition | Git worktree clean (no unstaged changes to tracked files in the workspace). Abort with structured error if dirty. |
| Happy | Scan body references via `scan_body_references`; buffer_write each referencing file with updated content; commit atomically. |
| Contention | Standard lock semantics (§4). |
| Partial-commit recovery | §6 applies; after rebuild, re-run scan and compare — if diff is non-empty, surface via `ctx.error` and leave for human review. |
| `read_only` refusal | Same as scaffold. |
| Missing `workspace_id` | Same as scaffold. |

## 11. Deferred SF/m inventory (stub)

Source-of-truth document `ontos-v4.1-trackA-D-verdict.md` does not yet
exist. Track A must publish it before SF/m items can be mapped to
owners and target releases. Until then, this table is a stub:

| ID | One-line description | Owner | Target |
|---|---|---|---|
| SF-1 | _pending verdict doc_ | — | v4.1.2+ |
| SF-2 | _pending verdict doc_ | — | v4.1.2+ |
| SF-5 | _pending verdict doc_ | — | v4.1.2+ |
| m-4 | _pending verdict doc_ | — | v4.1.2+ |
| m-6 | _pending verdict doc_ | — | v4.1.2+ |

## 12. Out of scope for Track B

SF-1, SF-2, SF-5, m-4, m-6 — deferred to v4.1.2+.

## 13. When this design becomes executable

Track B does **not** kick off until every box below is checked against
current `main`:

- [ ] Spec addendum file exists and is versioned.
- [ ] `workspace_lock()` exists and is used by at least one caller
      (substantially satisfied by #85's flock substrate; confirm the
      `owns_lock` opt-out is wired).
- [ ] Portfolio index module exists with `rebuild_workspace(slug, root)`.
- [ ] Bundle config module exists with the three fields in §7.
- [ ] `scanner.slugify` exists.
- [ ] `load_registry_records` exists.
- [ ] CB-1..CB-11 contracts doc exists and is cited.
- [ ] `.ontos.lock` is in `.gitignore`.
- [ ] pytest baseline is known on post-Track-A `main`.

Only after all boxes check can Phase 2 (Dev spawns, branch creation, PR)
begin.

## 14. Accurate anchors retained from the draft

- `ontos/commands/rename.py:221` — `ctx.buffer_write(...)` (A6, §9).
- `ontos/core/body_refs.py:111` — `def scan_body_references(...)` (A6, §9).
- `ontos/core/context.py:151` — `.ontos.lock` path construction (§4).
- `ontos/core/context.py:227` — `_acquire_lock` with flock (§4).
- `ontos/core/context.py:243` — `_release_lock` (§4).
- `ontos/core/context.py:189-199` — `commit()` exception handler (A3 hook, §6).
- `ontos/commands/log.py` — `_slugify` (A2, §5).

(Draft citations of `context.py:148/224/262` were off by a few lines;
corrected above against HEAD `4ee3e54`.)
