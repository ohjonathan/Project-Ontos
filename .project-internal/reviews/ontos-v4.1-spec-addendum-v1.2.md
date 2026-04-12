# Ontos v4.1 Spec Addendum — v1.2

**Supersedes:** sections of `Ontos-v4.1-Implementation-Spec.md` v1.1 as noted below.
**Triggered by:** Track B C.0 investigation (`ontos-v4_1-trackB-C0-findings.md`)
**Scope:** Six corrections required before Track B enters Phase C. This addendum is additive — v1.1 remains authoritative except where explicitly superseded.

---

## A1. Single-Lock Discipline (SUPERSEDES §4.8 lines 1239-1245)

**Problem:** v1.1 prescribes nesting `workspace_lock()` with `SessionContext.commit()`. Both open `<workspace>/.ontos.lock` with independent fds. Per `flock(2)`, same-process fds are treated independently — the second `LOCK_EX | LOCK_NB` call returns `EWOULDBLOCK`, triggering the 5s retry loop in `SessionContext._acquire_lock` and raising `RuntimeError`. **Every write tool would fail.**

**Resolution:** Adopt Option 3 from the C.0 findings. `SessionContext` gains an `owns_lock: bool = True` parameter. When `owns_lock=False`, `_acquire_lock()` and `_release_lock()` are no-ops; `commit()` assumes the caller holds the flock.

**New usage pattern for Track B write tools:**

```python
with workspace_lock(cache.workspace_root):
    ctx = SessionContext(workspace_root=..., owns_lock=False)
    ctx.buffer_write(...)
    ctx.commit()  # no re-acquisition; flock held by outer context
```

**Defaults preserved:** All existing callers (CLI commands invoking `SessionContext` directly) pass nothing and get `owns_lock=True`. No existing call site changes. No `commit()` signature change for existing callers.

**Hard contract:**
- Every Track B write tool MUST wrap the entire mutation (buffer_write + commit + any post-commit rebuild) inside a single `workspace_lock()` context.
- Every `SessionContext` constructed INSIDE a `workspace_lock()` block MUST pass `owns_lock=False`.
- Dev 1 implements the `owns_lock` mode; Devs 2 and 3 consume it.

**Test requirement:** Add integration test that exercises the new pattern and would fail (deadlock/RuntimeError) against the pre-addendum behavior.

---

## A2. Slugifier Binding (SUPERSEDES §4.8.1 line 1002)

v1.1 references `{date}_{slugified_title}.md` without specifying which slugifier. Two exist in the codebase with different semantics:

| Purpose | Function | Behavior on empty input |
|---------|----------|------------------------|
| Workspace identity | `ontos.mcp.scanner.slugify` | Returns `"workspace"` |
| Title slugification | `ontos.commands.log._slugify` | Returns `""` (caller handles) |

**Binding:**
- **Workspace slugs** (workspace identity in DB, `rebuild_workspace(slug, root)`, collision handling): `ontos.mcp.scanner.slugify` + `allocate_slug`.
- **Title slugs** (log filenames, scaffolded document filenames, any user-provided free-text name → filename): `ontos.commands.log._slugify`.

Track B tools MUST import the correct function per use case. Dev prompt enumerates each call site.

---

## A3. DB-Files Consistency Gap (SUPERSEDES §4.9 line 1716)

v1.1 claim "No gap for inconsistency" is factually incorrect. The sequence `commit()` → `rebuild_workspace()` is NOT atomic. A crash between the file commit and the DB rebuild leaves the DB stale relative to the filesystem. This is a small consistency window, not corruption — the files are the source of truth; the DB is a derived index.

**Resolution in spec:**
- Acknowledge the gap explicitly. Files are authoritative; portfolio DB is a derived index.
- Recovery path: on crash between commit and rebuild, the next `rebuild_workspace(slug)` call (triggered by any subsequent write, or by `verify --portfolio`, or by explicit user action) fully reconciles.
- **Post-rollback recovery:** after `git checkout -- .` rollback of failed writes, `rename_document` MUST re-invoke `rebuild_workspace(slug, root)` to resync the DB.
- **Single-file write tools:** `scaffold_document`, `log_session`, and `promote_document` use rebuild-on-error recovery only. They do not attempt a filesystem rollback before the rebuild.

**Not required:** Two-phase commit, transactional wrapping of DB+files, or any atomicity guarantee between the two. The inconsistency window is bounded and self-healing.

---

## A4. Bundle Config Wired In Track B (SUPERSEDES §4.2 lines 295-301 deferral implication)

v1.1 defines `bundle_token_budget`, `bundle_max_logs`, `bundle_log_window_days` in `portfolio_config.py:19-21`. They are parsed but not consumed (SF-3 in Phase D verdict). Track B wires them.

**Requirements:**
- `get_context_bundle()` in `ontos/mcp/bundler.py` consumes all three fields from the loaded portfolio config.
- `bundle_token_budget`: hard cap on total bundle token count. Bundle truncates (tail-first, preserving recent logs) when exceeded.
- `bundle_max_logs`: max number of log entries included, regardless of token budget.
- `bundle_log_window_days`: exclude logs older than this many days from bundle candidates.
- Defaults: document in `portfolio_config.py` alongside the field definitions. Reasonable starting values: `bundle_token_budget=8000`, `bundle_max_logs=20`, `bundle_log_window_days=30`.
- Dev 4 owns this work and ALSO fixes SF-4 (equal-date tiebreaker determinism) and SF-9 (deterministic input ordering before sort).

**Test requirement:** Unit tests for each of the three fields independently (budget cap, log cap, window filter) plus an integration test combining all three.

---

## A5. `.gitignore` Verification

Track B dev prompt must include a verification step: confirm `.gitignore` at repo root contains `.ontos.lock`. If absent, Dev 1 adds it. Quick grep, not a standalone task.

---

## A6. `rename_document` Filesystem-Rename Claim Verification

v1.1 §4.8.2 line 1062 asserts "existing CLI rename does NOT perform filesystem file renames." Not verified during C.0. Dev 3 MUST verify against `ontos/commands/rename.py` before implementing `rename_document`. If the claim is wrong, Dev 3 flags it to the orchestrator before proceeding — do NOT silently adapt the tool design to match whatever `rename.py` actually does.

---

## Decomposition (Adopted from C.0 Findings)

Four developers, dependency-ordered:

| Dev | Scope | Depends On | Deferred Items Closed |
|-----|-------|------------|----------------------|
| **Dev 1** | Lock discipline (A1), `SessionContext(owns_lock=False)`, `.gitignore` verification (A5), write-contention integration tests | — | SF-8, m-12 |
| **Dev 2** | `scaffold_document`, `log_session`, `promote_document` (single-file mutators). Wire `read_only` enforcement. Reuse CB-10 timeout pattern. | Dev 1 | m-2, m-7, m-14 |
| **Dev 3** | `rename_document` (multi-file mutator), A6 verification, post-rollback rebuild path (A3), N-file reference updates via `core/body_refs.py` | Dev 1, Dev 2 | m-8, m-13 |
| **Dev 4** | Bundle config wiring (A4), SF-3/SF-4/SF-9, plus m-1, m-3, m-5, m-9, m-10, m-11 | — (parallel with Dev 1) | SF-3, SF-4, SF-9, m-1, m-3, m-5, m-9, m-10, m-11 |

**Parallel execution:** Devs 1 and 4 can start simultaneously. Dev 2 starts when Dev 1's `owns_lock` mode is merged to the Track B branch. Dev 3 starts when Dev 2's single-file mutators are merged.

**Deferred out-of-scope items:** SF-1, SF-2, SF-5, m-4, m-6. Documented in sequence ledger for v4.1.2 or later.

---

## Addendum Gate Criteria (Pre-Phase C)

Before generating the Dev Team meta-prompt, orchestrator confirms:
- [x] Lock discipline resolved (A1)
- [x] Slugifier binding specified (A2)
- [x] Consistency gap documented + recovery path defined (A3)
- [x] Bundle config scope decided: wire in Track B (A4)
- [x] Minor verifications scoped (A5, A6)
- [x] Decomposition and dependency ordering specified

**Status: READY.** Dev Team meta-prompt may be generated against v1.1 + this addendum.
