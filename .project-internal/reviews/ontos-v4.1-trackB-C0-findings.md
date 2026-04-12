# Track B C.0 Investigation Findings

**Investigator:** Claude Code (local)
**Date:** 2026-04-11
**Inputs:** merged Track A at HEAD `4ee3e54`, spec v1.1 (`.project-internal/v4.1/phaseA/Ontos-v4.1-Implementation-Spec.md`), Phase D verdict (`.project-internal/reviews/ontos-v4.1-trackA-D-verdict.md`), Claude Code + Codex Phase D consolidations.

**Note on authority:** A `v4.1_Sequence_Ledger.md` does not exist in this repo. The trackA-D verdict §10 (Track B Implications) is the closest authoritative post-merge record of contract changes. All "ledger" references below are resolved against that plus the merged code.

---

## Q1: Slugify Contract

**Shared function exists at the ledger-claimed location.**
`slugify(directory_name: str) -> str` at `ontos/mcp/scanner.py:35-40`. It lowercases, replaces `.`/space with `-`, replaces any remaining non-`[a-z0-9-]` with `-`, collapses runs of `-`, strips leading/trailing `-`, and returns `"workspace"` on empty. `allocate_slug(base_slug, used_slugs)` at `scanner.py:281-286` is the collision-suffix helper (`-2`, `-3`, …).

**Every current call site uses it:**
- `ontos/mcp/server.py:22,741-742` — `_workspace_slug(root)` is a one-line wrapper around `slugify(root.name)`.
- `ontos/mcp/tools.py:19,545-546` — `_slugify_workspace_name(raw)` is a one-line wrapper.
- `ontos/commands/verify.py:402,409` — imports `slugify, allocate_slug, load_registry_records`.
- `ontos/mcp/scanner.py:95` — internal use in `discover_projects`.

The three divergent fallback implementations flagged by CB-6/B-5 have been eliminated. `server.py:741-742` and `tools.py:545-546` collapse to the same canonical function.

**Track B call sites (per spec agent extraction):**

| Track B tool | Needs slugify for | Planned import |
|---|---|---|
| `scaffold_document` | workspace identity in DB invalidation, **plus** slugifying log titles for filenames | `from ontos.mcp.scanner import slugify` |
| `rename_document` | workspace identity for `rebuild_workspace(slug, root)` call | same |
| `log_session` | workspace identity; log-title slugification for filename (`{date}_{slug}.md`) | same |
| `promote_document` | workspace identity | same |

**Flag — NOT covered by shared function:** the spec (agent §1, line 1002) references `{date}_{slugified_title}.md` for log filenames. The workspace `slugify()` is tuned for directory names and falls back to `"workspace"` on empty input. For log *titles*, the existing `ontos/commands/log.py:204 _slugify()` is already the canonical title-slugifier (CLI uses it). Track B must reuse `commands/log.py:_slugify` for title slugs, NOT the workspace `scanner.slugify`. The spec is ambiguous here — the prompt writer must spell this out.

---

## Q2: Lock Substrate Under Write Contention

### 🚨 **NEW BLOCKING DISCOVERY — same-process double-lock deadlock**

This was not in the Phase D verdict. It is a direct consequence of the spec's prescribed usage pattern.

**The substrate:**
- `workspace_lock()` at `ontos/mcp/locking.py:16-42` opens `<workspace>/.ontos.lock` and calls `fcntl.flock(fd, LOCK_EX | LOCK_NB)` with a 5s retry loop; raises `OntosUserError(code="E_WORKSPACE_BUSY")` on timeout; sets `os.set_inheritable(fd, False)` at `locking.py:22` (CB-8 fix confirmed merged).
- `SessionContext._acquire_lock()` at `ontos/core/context.py:227-241` opens `<repo_root>/.ontos.lock` (SAME FILE) and calls `fcntl.flock(fd, LOCK_EX | LOCK_NB)` with a 5s retry loop; returns `False` on timeout, which causes `commit()` at `context.py:152-156` to raise `RuntimeError("Could not acquire write lock...")`.

**The deadlock.** Spec agent §8 (lines 1239-1245) prescribes:

```python
with workspace_lock(cache.workspace_root):     # fd1 holds LOCK_EX on .ontos.lock
    ctx.buffer_write(...)
    ctx.commit()                                # opens fd2, tries LOCK_EX → blocks
```

Per `flock(2)`: different fds to the same file from the **same process** are treated independently. The second `flock(LOCK_EX | LOCK_NB)` returns `EWOULDBLOCK`. `SessionContext._acquire_lock` retries for 5s, returns `False`, and `commit()` raises `RuntimeError`. **Every Track B write tool will fail at the commit step.**

**This must be resolved before Track B implementation begins.** Options:
1. Make Track B tools call into the existing CLI command layer (which creates its own `SessionContext` and acquires its own flock), bypassing `workspace_lock()` entirely. Since both mechanisms use the same file, the CLI lock alone provides mutual exclusion against concurrent MCP writes — as long as read tools also respect it, which they do via `workspace_lock()`.
2. Plumb the already-acquired `SessionContext` (or its fd) through to `commit()` so it skips re-acquisition.
3. Give `SessionContext` an "already-locked" mode where `commit()` executes without touching the lock.

**Answers to the Q2 sub-questions:**

| Sub-question | Answer |
|---|---|
| Lock acquisition pattern | `workspace_lock(cache.workspace_root)` context manager, wrapping the whole tool body. |
| Two writes, same workspace, concurrent | One acquires; other retries for 5s, then `E_WORKSPACE_BUSY`. Inter-process: correct. Intra-process (same MCP server handling two requests): same-process flock-on-different-fd behavior — a second thread/task in the same process opening a new fd will also be denied. |
| Write tool vs. `verify --portfolio` holding read locks | `verify --portfolio` does NOT hold workspace locks in Track A (it reads portfolio.db). No contention at the workspace-lock layer. **However:** it reads the portfolio DB while write tools are calling `rebuild_workspace()` which mutates the DB — this is the CB-10 surface (FTS5 `BEGIN IMMEDIATE` starvation). CB-10 fix adds `timeout=5.0` but concurrent FTS5 rebuild + verify read is still a partial-ordering issue. |
| Operations that must NOT block on workspace lock | Portfolio-level read tools (`project_registry`, `search_portfolio`) — they operate on portfolio.db only and must not be stalled by a slow write in one workspace. Current Track A design already respects this. |

---

## Q3: Partial-Commit Boundaries

**`SessionContext.commit()` is two-phase temp-then-rename, not transactional.** Behavior per `context.py:134-205`:
1. **Phase 1 (lines 163-175):** write all WRITE ops to `.tmp` sidecars; record DELETE/MOVE as staged tuples.
2. **Phase 2 (lines 178-187):** for each staged tuple, `temp.rename(final)` (POSIX-atomic per-file) or `final.unlink()` for deletes.
3. **On exception mid-phase-2 (lines 189-199):** remaining `.tmp` files are unlinked but already-renamed files remain in new state. Errors are recorded on `self.errors` and re-raised.

So: **if the 5th of 10 buffered writes fails during rename, files 1-4 are already committed and files 5-10 are partially rolled back (their `.tmp` files are deleted but their final paths retain old content).**

**Per-tool state + partial-commit surface:**

| Tool | Mutates | DB-then-file risk | File-then-DB risk |
|---|---|---|---|
| `scaffold_document` | 1 new `.md` file + `rebuild_workspace()` DB row | Low — single file. Order per spec: file write first (via `SessionContext.commit`), then `portfolio_index.rebuild_workspace()`. If commit succeeds but rebuild raises, DB is stale until next rebuild. Not corrupting — just lagging. | If commit fails after rebuild, N/A (rebuild is last). |
| `rename_document` | **N `.md` files** (target ID + every dependent's `depends_on` + every body-ref) + DB | **High.** Spec explicitly flags this (line 1060: "NOT atomic"). If commit fails mid-write, dependents point at stale IDs and the workspace is in a broken state. Spec mitigates with git-clean-state precondition + recovery via `git checkout -- .`. | Same as above; DB rebuild is post-file. |
| `log_session` | 1 new `.md` + DB row | Low. | Low. |
| `promote_document` | 1 `.md` (frontmatter) + DB row | Low. | Low. |

**Spec lines that imply atomicity and must be flagged for the dev prompt:**

| Line | Quote | Problem |
|---|---|---|
| `context.py:1-11` (docstring) | "Buffers file operations for later commit … Applies buffered writes sequentially during commit" — and per SF-7/B-1.S-4 the older phrasing "atomic writes" was here. | Already partially cleaned. The spec's Q3 framing is fine; verify no code comments in new Track B modules reintroduce "atomic." |
| Spec §4.8 line 944 | "**best-effort sequential writes with temp-file cleanup** — NOT atomic transactions." | Correct — keep. |
| Spec §4.9 lines 1249-1257 | Recovery path: "git checkout -- . … delete any .tmp files." | Correct but **incomplete**: does not mention DB rebuild. If commit succeeded for files but `rebuild_workspace()` raised, `git checkout` restores old files but the DB row still references the new content. Prompt must clarify: after file rollback, re-run `ontos verify --portfolio` or call `rebuild_workspace` again. |
| Spec line 1716 (risk register) | "Write tool holds workspace lock for the entire duration including `force_refresh()` and `rebuild_workspace()`. No gap for inconsistency." | **Incorrect.** There IS a gap — between phase-2 renames and `rebuild_workspace()`. If the process dies between those calls, DB diverges from files. |

**SF-7 status:** `context.py:1-11` already says "best-effort," not "atomic," at HEAD `4ee3e54`. SF-7 is resolved-in-merged-code.

---

## Q4: Config Validation Surface

**Post-CB-1 fix, `_section_kwargs()` is strict.** `ontos/core/config.py:219-227` raises `ConfigError(f"Unknown config key '{section_name}.{key}'")` on any unknown key. `_validate_section_names()` at `:211-216` raises on any unknown top-level section.

**The "two named exceptions"** live in `_normalize_legacy_config()` at `config.py:183-208`:
1. Top-level `[project]` section: silently dropped (line 193, `normalized.pop("project", None)`).
2. `validation.strict` → `hooks.strict`: migrated (lines 195-207).

**Track B's new config surface lives in a DIFFERENT config file.** Per `ontos/mcp/portfolio_config.py:15-63`, `PortfolioConfig` is loaded from `~/.config/ontos/portfolio.toml` (global), not the per-workspace `.ontos.toml`. It has its own loader (`load_portfolio_config`) with **permissive coercion** (`_coerce_int`, `_coerce_str_list`, `_coerce_optional_str` — unknown keys are silently ignored). This means:

- **The strict `_section_kwargs()` path does NOT apply to `[portfolio]` / `[bundle]` keys.** Track B can add new portfolio/bundle keys without touching the workspace-config allowlist.
- **No allowlist additions needed for the portfolio TOML.** But this is also CB-1's concern inverted: typos in `portfolio.toml` are silently swallowed. Track B's prompt should decide whether to harden portfolio_config's loader to match workspace config's strictness.

**Track B tool surface and config errors:**
- Write tools execute against a workspace that already has `.ontos.toml` loaded. If the config is invalid, the MCP server fails at workspace-init, not per-tool. Track B does not need to handle `ConfigError` at tool level.
- **Workspace creation** scenarios: `scaffold_document` only runs inside an initialized workspace (per spec). There is no "create workspace" write tool in Track B. So no "config doesn't exist yet" case.

**Resolution: no allowlist additions required for Track B.** Flag only: the portfolio-config loader is still permissive (SF-3 dead-bundle config + the broader looseness). This is consistent with SF-3's recommendation to either wire or remove bundle keys.

---

## Q5: Registry Parser Reuse

**Shared parser is live.** `load_registry_records(registry_path, *, tolerate_errors=True)` at `ontos/mcp/scanner.py:143-199` and `_extract_registry_items(raw)` at `:215-234` accept: top-level list, `projects`, `workspaces`, `entries`, `items`, and dict-of-slug-to-payload shapes. `_first_string(item, "path", "workspace", "root", "repo_root", "repoPath")` at `:237-242` normalizes path keys.

**Current consumers:**
- `ontos/mcp/scanner.py:50` (internal to `discover_projects`).
- `ontos/commands/verify.py:402-404` (post-CB-4 fix: `from ontos.mcp.scanner import allocate_slug, load_registry_records, slugify` and `load_registry_records(registry_path, tolerate_errors=False)`).

**Track B registry surface:** per the spec agent's §4 extraction, **no Track B tool reads or writes the registry directly.** Track B tools call `portfolio_index.rebuild_workspace(slug, root)` (`portfolio.py:92`), which is a DB-only operation keyed by an already-known slug. The portfolio index itself was built from the registry during `rebuild_all()`.

**Conclusion: Track B does not need to touch the registry parser.** If a future write tool introduces "register new workspace," it must use the shared parser. Flag for the dev prompt: **explicitly forbid introducing parallel registry parsing in Track B.**

---

## Q6: Sidecar Cleanup Precedent

**CB-7 fix merged.** `PortfolioIndex._reset_db_file()` at `ontos/mcp/portfolio.py:518-528` deletes `portfolio.db`, `portfolio.db-wal`, and `portfolio.db-shm`. Invoked from `ontos/mcp/portfolio.py:48` when a schema mismatch is detected at open.

**Track B DB mutation surface:**

| Tool | DB operation | Corruption risk | Sidecar handling needed |
|---|---|---|---|
| `scaffold_document` | `rebuild_workspace(slug, root)` — INSERTs/UPSERTs documents for one workspace | SQLite transactions are atomic at the row level; `rebuild_workspace` either commits or rolls back via SQLite's own machinery. Process kill mid-write leaves WAL, which SQLite replays correctly on reopen. | **No new cleanup needed.** Existing `_reset_db_file()` handles the only catastrophic case (schema mismatch). |
| `rename_document` | same | same | same |
| `log_session` | same | same | same |
| `promote_document` | same | same | same |

**New sidecar paths Track B should introduce:** none. `_reset_db_file()` is the right recovery seam and it already covers WAL/SHM. The recovery *precedent* is: "catch corruption → call `_reset_db_file()` → rebuild on next open." Track B tools should invoke `_reset_db_file()` if they ever catch a `sqlite3.DatabaseError` during `rebuild_workspace`.

**Flag:** m-13 (FTS5 parity check runs post-commit) and CB-10 (FTS5 BEGIN IMMEDIATE starvation) remain relevant for Track B because every write tool triggers a rebuild that can hit the same FTS5 surface. Prompt must reference the CB-10 fix pattern (SQLite `timeout=5.0`).

---

## Q7: Deferred SF/m Triage

Status annotations based on HEAD `4ee3e54` code inspection.

| ID | Classification | Rationale |
|---|---|---|
| **SF-1** (`_coerce_optional_str` semantics) | Still Relevant | `portfolio_config.py:62` still uses it. Affects Track B only indirectly, but worth fixing in the same PR to avoid `registry_path = None` silently disabling registry scanning. |
| **SF-2** (FTS5 query sanitization) | Still Relevant | Read-tool concern, but Track B rebuilds trigger FTS5 inserts that could break queries. Low priority for Track B — can be deferred to v4.1.2. |
| **SF-3** (dead bundle config) | Still Relevant | `bundle_token_budget`/`bundle_max_logs`/`bundle_log_window_days` at `portfolio_config.py:19-21` still not wired. Track B's `log_session` and `scaffold_document` interact with the bundler output — either wire them now or remove. |
| **SF-4** (recent-log tiebreaking) | Still Relevant | Bundler ordering affects `get_context_bundle` stability. Not Track-B-specific but easy to fix alongside SF-3. |
| **SF-5** (scanner collision warning) | Still Relevant | Stderr warning still absent. Track B's `rebuild_workspace` does not hit the collision path (it's scoped to one slug), so SF-5 is orthogonal to Track B's hot path. Low priority. |
| **SF-8** (stale `.ontos.lock` upgrade test) | Still Relevant | flock-based lock file is regular text; no PID inside. Test that a pre-v4.1 lockfile (PID-based) is handled gracefully during migration. Belongs in Track B test suite. |
| **SF-9** (bundler non-deterministic ordering) | Still Relevant | Same as SF-4 — deterministic bundle ordering matters for Track B write tools that rebuild bundle output. |
| **m-1** (dict-fallback ingests metadata) | Still Relevant | `scanner.py:225-232` — still iterates all dict keys. Not Track-B-specific but cheap fix. |
| **m-2** (`read_only` unused) | **Obviated by Track B Surface** | Track B introduces the first actual write tools; `read_only` will finally have semantics. Track B must consume it (refuse writes when `read_only=True`). Close m-2 by wiring it in Track B. |
| **m-3** (`_cmd_serve` arg forwarding) | Still Relevant | Orthogonal; quick cleanup. |
| **m-4** (no `__all__`) | Out of Scope | Style nit. Do separately. |
| **m-5** (schema version error msg) | Still Relevant | Trivial message update. Bundle with Track B. |
| **m-6** (`_lost_in_middle_order` pattern) | Out of Scope | Equivalent output per reviewer. Leave. |
| **m-7** (`workspace_lock()` has zero consumers) | **Obviated by Track B Surface** | Track B is literally the first consumer. Close m-7 when Track B lands. |
| **m-8** (redundant cross-workspace guards) | Still Relevant | `server.py:478` + `tools.py:513-525` both guard — Track B write tools will add a third. Consolidate into one helper before adding more call sites. |
| **m-9** (`ensure_portfolio_config` writes on read) | Still Relevant | `portfolio_config.py:38-43`. Tangential to Track B but will surface when Track B tools run on fresh installs. |
| **m-10** (cross-boundary import of `_compute_content_hash`) | Still Relevant | `portfolio.py:12` — Track B will extend `portfolio.py`; keep the boundary clean now. |
| **m-11** (excessive `Any` typing) | Still Relevant | Track B adds more `portfolio_index: Any` call sites. Tighten the Protocol type before it spreads. |
| **m-12** (`context.py._acquire_lock` handle leak on non-BlockingIOError) | **Still Relevant and urgent for Track B** | `context.py:231-241` — if any unexpected exception occurs between opening the handle and flocking, the handle leaks. Track B increases this path's traffic significantly. |
| **m-13** (FTS5 parity post-commit) | Still Relevant | Track B writes → rebuild → FTS5. Same surface. Fix alongside CB-10 test coverage. |
| **m-14** (`project_registry` discards `workspace_id`) | **Obviated by Track B Surface** | `server.py:355-356` — Track B's workspace_id validation will subsume this. Close m-14 by routing through the shared validator introduced in Track B. |

**Summary:**
- Still Relevant in Track B: SF-1, SF-3, SF-4, SF-8, SF-9, m-1, m-3, m-5, m-8, m-9, m-10, m-11, m-12, m-13 (14 items)
- Obviated by Track B: m-2, m-7, m-14 (3 items)
- Already Resolved (Track A fix cycle): none in this list; SF-7 separately (verified at `context.py:1-11`)
- Out of Scope: m-4, m-6 (2 items)
- Low-priority/deferrable: SF-2, SF-5 (ship as "v4.1.2" follow-up)

---

## Q8: Spec Drift Inventory

| Spec line / section | Assumes | Actually (post-Track-A merged code) | Resolution |
|---|---|---|---|
| §4.8 lines 1239-1245 (usage pattern: `with workspace_lock(...): ... ctx.commit()`) | `workspace_lock()` and `SessionContext.commit()` can nest safely. | Both open the **same** file `<workspace>/.ontos.lock` with independent fds → deadlock/timeout within the same process (see Q2). | **Spec addendum required.** Dev prompt must specify a single-lock discipline. This is a blocking spec correction. |
| §4.8.1 line 944 + §4.9 | Recovery is "git checkout -- ." after crash. | File rollback is correct, but DB state after `rebuild_workspace()` runs post-commit is not discussed. | Prompt should instruct: after file rollback, re-invoke `rebuild_workspace(slug, root)` OR rely on next `rebuild_all`. |
| Line 1716 ("No gap for inconsistency") | Workspace lock covers commit + rebuild atomically. | There IS a gap: phase-2 renames complete, then rebuild runs. A crash between them leaves DB stale. | Spec addendum: acknowledge the gap. It's a minor consistency window, not a corruption risk. |
| §4.3 line 370-372 (slugify quoted as simple dot/space→dash) | Spec's example slugify is a 2-line fn. | Merged `scanner.py:35-40` does more: lowercases, regex-strips non-`[a-z0-9-]`, collapses runs, strips, defaults to `"workspace"`. | Spec example is outdated but non-blocking. Prompt should reference the merged function by file:line rather than re-quoting. |
| §4.8.1 line 1002 (`{logs_dir}/{date}_{slugified_title}.md`) | Unspecified which slugifier applies to log titles. | Workspace `slugify` returns `"workspace"` on empty input — wrong semantics for titles. `commands/log.py:204 _slugify()` is the correct function. | Prompt must explicitly bind "title slug" → `commands/log.py._slugify`, "workspace slug" → `scanner.slugify`. |
| §4.2 lines 295-301 (bundle config fields) | Bundle config is live. | `bundle_token_budget`, `bundle_max_logs`, `bundle_log_window_days` are dead at `portfolio_config.py:19-21` (SF-3). | Prompt must wire these OR remove them OR explicitly defer and document. |
| §4.8 line 943 ("triggers `portfolio_index.rebuild_workspace(...)`") | Track B tools have direct access to `portfolio_index`. | `portfolio_index` is built per-process in `server.py:720-738` and injected into tools via `_invoke_write_tool`. This matches the spec — no drift. | No action. |
| §4.9 line 1264 (.gitignore entry) | `.ontos.lock` to be added. | File exists at workspace root when Track A runs; presumably `.gitignore` already updated by Track A. | Verify `.gitignore` contains `.ontos.lock` before Track B lands. Quick grep in dev prompt. |
| Spec's rename_document §4.8.2 line 1062 | "existing CLI rename does NOT perform filesystem file renames." | Confirm against `ontos/commands/rename.py`. (Not verified in this investigation — worth checking during Track B implementation.) | Prompt should require verification, not assumption. |

---

## Summary for Orchestrator

- **Spec corrections needed:** 4 substantive (double-lock pattern, title-vs-workspace slugify, DB rollback after file rollback, dead bundle config). 3 minor clarifications (slugify function reference, rename filesystem-rename claim, .gitignore verification).

- **New blocking discoveries (not in Phase D verdict):**
  1. **Same-process double-lock deadlock** between `workspace_lock()` and `SessionContext._acquire_lock()`. Both flock the same `.ontos.lock` file with independent fds. Every Track B write tool under the spec's prescribed usage pattern will hang 5s then raise `RuntimeError`. **Must be resolved in the implementation prompt** (Track B can't enter C.1 until a single-lock discipline is chosen).
  2. **DB-vs-files consistency gap** between `commit()` and `rebuild_workspace()`. Small window, not corrupting, but spec line 1716 is factually wrong.
  3. **Dual slugifier ambiguity** at line 1002 (title vs workspace slug not distinguished).

- **Recommended decomposition (preview):**
  - **Dev 1 — lock discipline + SessionContext integration:** resolve Q2 deadlock, rework `workspace_lock` or add `SessionContext(owns_lock=False)` mode. Land SF-8, m-12. Write contention integration tests.
  - **Dev 2 — tool implementations:** `scaffold_document`, `log_session`, `promote_document` (single-file mutators). Close m-2 (wire `read_only`), m-7, m-14. Reuse CB-10 timeout pattern.
  - **Dev 3 — `rename_document` + consistency hardening:** the multi-file tool. Git clean-state precondition, N-file reference updates via `core/body_refs.py`, post-rollback rebuild path. Close m-8, m-13.
  - **Dev 4 — bundle config wiring + polish:** SF-3/SF-4/SF-9 (wire or remove bundle config; deterministic ordering). m-1, m-3, m-5, m-9, m-10, m-11.
  - Parallelizable: 1 and 4 can run in parallel; 2 depends on 1; 3 depends on 1 + 2.

- **Risks not previously identified:**
  - Double-lock deadlock (P0, described above).
  - `rebuild_workspace()` after `commit()` is the real transactional seam, not `commit()` itself. Spec needs to document this seam.
  - `portfolio_config.py` is permissive where workspace `config.py` is strict post-CB-1; a typo in `portfolio.toml` silently disables portfolio features. Not blocking for Track B but asymmetric with the CB-1 rationale.
  - `.ontos.lock` is a regular text file with no PID/fingerprint. When coordinating between CLI process and MCP server process on the same workspace, an operator debugging a stuck lock has no way to identify the holder. Quality-of-life gap.

**Pre-dev checkpoint recommendation: NOT ready to enter Phase C as-is.** The double-lock deadlock is a spec defect, not an implementation detail. Revise the implementation prompt (or a spec addendum) to choose a single-lock discipline before developers start coding, or Dev 1's first task will be a redesign loop.
