# Ontos v4.1 Spec v1.1 - B.4 Verification (Codex)

**Phase:** B.4 Lightweight Verification  
**Date:** 2026-04-11  
**Reviewer:** Codex  
**Artifact verified:** `Ontos-v4.1-Implementation-Spec.md` v1.1 final  
**Inputs checked:** Spec v1.1, CA Response v1.1 (+ C.0 addendum), B verdict, targeted codebase facts

## 1. Verification Verdict Summary

| Issue | Verdict | One-line rationale |
|-------|---------|---------------------|
| UB-1 FTS5 | Accept | One standalone FTS5 schema remains, BM25 matches 3 columns, and no duplicate DDL remains elsewhere. |
| UB-2 Atomicity | Accept with Note | Core write-path language is corrected, but old atomicity wording still leaks into overview, tests, and risk text. |
| UB-3 Locking | Accept with Note | Unified `.ontos.lock` + `flock` substrate is coherent, but a little stale-lock wording remains outside the design section. |
| UB-4 Rename | Accept with Note | `_prepare_plan()` and ID-only rename are correctly specified, but the Track B test table still says "file rename." |
| UB-5 MCP Surface | Accept with Note | The matrix, routing wrappers, and `--read-only` contract now exist, but a few prose lines still drift from the matrix and from `get_context_bundle()`'s actual logic. |
| UB-6 verify | Challenge | `verify` is in scope now, but the new section conflicts with the existing CLI/codebase and uses an inconsistent registry path. |
| UB-7 Single-WS Crash | Accept with Note | The crash path is removed and the single-workspace guard is explicit, but the bundle data-source description still disagrees across sections. |

**Overall verdict:** Partial Challenge

## 2. Per-Issue Verification Detail

### UB-1: FTS5 schema consolidation

**Verdict:** Accept

**Evidence**
- Section 4.1 now contains one canonical FTS5 definition at lines 217-230: standalone `fts5(title, concepts, body)` with BM25 weights `bm25(10.0, 3.0, 1.0)`.
- The standalone rationale and rebuild rules are consistent at lines 240-250.
- Global search found one `CREATE VIRTUAL TABLE fts_content` occurrence and one BM25 rank definition in the spec.
- Section 6 no longer carries a second schema block; instead it references standalone-specific tests (`test_portfolio.py`, `test_search.py`) at lines 1511 and 1515.

**Concerns**
- Historical references to rejected external-content mode remain as explanation, which is fine. I found no live contradictory schema.

### UB-2: Atomicity claim correction

**Verdict:** Accept with Note

**Evidence**
- `rename_document()` now states the real guarantee at lines 1047-1058: git clean-state precondition plus "best-effort sequential" commit semantics.
- Section 4.9 repeats the corrected recovery model at lines 1247-1255.
- Section 10.3's write lifecycle now shows `SessionContext.commit()` as "best-effort sequential" at lines 1907-1915.
- The recovery path is reachable from the write-tool sections: lines 1074-1076 and 1253-1255.

**Concerns**
- Residual old language remains in the spec and should be scrubbed before implementation:
  - Overview line 42 still says "multi-file atomicity (rename)".
  - Track B tests line 1537 still says `test_rename_document.py` covers "multi-file atomicity".
  - Track B risk line 1655 says "`SessionContext` provides atomic writes."
  - Track B risk note line 1659 still refers to "rename atomicity guarantees."
- This no longer breaks the core design, but it is still enough to misdirect Track B planning if left in place.

### UB-3: Lock unification

**Verdict:** Accept with Note

**Evidence**
- Section 4.9 clearly specifies one lock file, `<workspace>/.ontos.lock`, using `fcntl.flock(fd, LOCK_EX | LOCK_NB)` at lines 1187-1189.
- Both MCP write tools and CLI `SessionContext._acquire_lock()` are explicitly moved onto the same flock mechanism at lines 1190 and 1227-1232.
- The file-change list puts `ontos/mcp/locking.py` and the `SessionContext._acquire_lock()` migration in Track A substrate scope at lines 1181-1183.
- Track A -> B handoff state requires the unified flock substrate before Track B begins at line 1374.

**Concerns**
- The busy-message text at lines 1216-1218 says "delete .ontos.lock manually." Under flock, a leftover old lock file is not itself harmful; the lock state is the kernel-held flock, not the file contents. The upgrade case looks mechanically safe, but the spec does not explain that explicitly.
- Track B risk line 1655 still says "Stale locks are auto-detected," which is PID-era language and should be removed.

### UB-4: Rename factual error

**Verdict:** Accept with Note

**Evidence**
- Section 4.8.2 now references `_prepare_plan()` with the correct signature at lines 1049-1053.
- The design is explicitly ID-only at lines 1026, 1060-1070, and OQ-2 is resolved to ID-only at lines 1476-1480.
- `RenameDocumentResponse` now uses `path` instead of `old_path` / `new_path` at lines 1317-1323.
- Codebase spot-check:
  - `_prepare_plan()` exists at `ontos/commands/rename.py:278`.
  - `rg` over `ontos/commands/rename.py` found no `os.rename`, `Path.rename`, or `buffer_move` calls.

**Concerns**
- Track B tests line 1537 still says `test_rename_document.py` covers "file rename." That is stale scope and should be corrected to match the accepted ID-only design.

### UB-5: MCP surface contract coherence

**Verdict:** Accept with Note

**Evidence**
- Section 4.4 now has one authoritative 15-tool availability matrix at lines 441-459.
- `--read-only` is settled as "write tools absent from `tools/list`" at line 461.
- `_invoke_tool()` routing is now explicit via three wrappers at lines 465-476.

**Concerns**
- Some prose still drifts from the matrix and from the concrete `get_context_bundle()` logic:
  - Line 431 says "New tools are registered" in single-workspace mode, but matrix rows 453-454 say `project_registry` and `search` are not.
  - Line 485 says `get_context_bundle` in portfolio mode can use "either cache or portfolio DB depending on `workspace_id`", but Section 4.7 lines 833-867 actually use `SnapshotCache` in single-workspace mode and `create_snapshot()` in portfolio mode.
  - Section 4.10 line 1281 says `get_context_bundle()` handles `workspace_id` natively because it queries the portfolio DB, which does not match Section 4.7's implementation block.
- The blocker is materially addressed, but the matrix needs one final prose-cleanup pass to truly be the single source of truth.

### UB-6: `verify` subcommand

**Verdict:** Challenge

**Evidence**
- The omission itself is fixed: `verify` is now mentioned in the overview (line 37), scope (line 63), dependencies (line 113), full design section (lines 1386-1464), tests (line 1519), risk note (line 1647), and exclusion list no longer defers it (line 1683).
- Exit codes are specified as `0 / 1 / 2` at lines 1451-1454.
- The problem is new-content correctness against the current codebase:
  - The spec says `CREATE ontos/commands/verify.py` and "register the `verify` subparser" at lines 1393-1409.
  - The repo already has an existing verify module at `ontos/commands/verify.py:1` and an existing registered verify subparser at `ontos/cli.py:411-434`.
  - The spec's code block uses `cmd_verify` at line 1406, but the real handler is `_cmd_verify` at `ontos/cli.py:1291-1308`; `cmd_verify` does not exist.
  - The spec's path contract is inconsistent: `~/Dev/.dev-hub/registry/projects.json` at line 112 versus `~/.dev-hub/registry/projects.json` at lines 113, 1388, and 1432.
  - The spec also promises "CLI fully preserved" at line 1593. As written, Section 4.13 reads like a replacement of the existing `verify` surface, not an additive extension of it.

**Concerns**
- None beyond the challenge itself. This section needs one targeted rewrite so it extends the existing `verify` command/module instead of describing a clean-room create path that the repo does not have.

### UB-7: `get_context_bundle()` single-workspace crash

**Verdict:** Accept with Note

**Evidence**
- The previously traced crash path is gone. Section 4.7 lines 833-846 explicitly guards `portfolio_index is None` before any workspace validation call.
- The single-workspace contract in Section 4.10 still says `workspace_id` is "accepted but ignored" at line 1279.
- OQ-1 is resolved to "available in both modes" at lines 1470-1474.
- I found no logic path in the v1.1 spec where `portfolio_index is None` still leads to `_validate_workspace_id()`.

**Concerns**
- Section 4.7 lines 860-867 build a fresh snapshot in portfolio mode, while Section 4.10 line 1281 says `get_context_bundle()` handles `workspace_id` by querying the portfolio DB. That mismatch does not reintroduce the crash, but it should be reconciled so Track A has one clear implementation path.

## 3. New Content Adversarial Findings

### Major: `verify` is not additive against the existing CLI surface

The new Section 4.13 is the only new-content area where I found a major issue.

- The repo already has `ontos/commands/verify.py` and a registered `verify` subcommand. The spec still describes a new-file create path and a fresh parser registration.
- The handler name in the spec (`cmd_verify`) does not exist; the current CLI uses `_cmd_verify`.
- The registry path contract is inconsistent inside the spec itself (`~/Dev/.dev-hub/...` vs `~/.dev-hub/...`).
- Because Section 7 claims "CLI fully preserved," this is not just a label nit. The design needs to specify how portfolio verification extends the existing command without breaking current document-verification behavior.

I did **not** find a separate critical/major issue in the new flock substrate or in the Track A risk re-rating:
- The flock design is coherent and the upgrade case looks mechanically safe by lock semantics.
- Section 8 explicitly re-rates Track A as MEDIUM with reasoning after the C.0 fold-in.

## 4. Regression Check

No architectural regressions found. The v1.1 revision did not break the FTS5 decision, the lock substrate placement, or the single-workspace crash fix.

The regressions I did find are consistency regressions:
- Residual v1.0 atomicity / file-rename language remains in overview, tests, and risk text (lines 42, 1537, 1655, 1659).
- Tool-availability prose still drifts from the matrix and from Section 4.7's actual logic (lines 431, 485, 1281).
- The new `verify` section introduces a backward-compat conflict against the existing CLI surface and uses an inconsistent registry path.

## 5. Recommendation to Orchestrator

**Return to CA for one targeted fix**

This is not a re-board situation. The architecture is still intact, and the remaining work is a focused spec-correction pass.

**Targeted fix scope**
1. Rewrite Section 4.13 as an extension/modification of the existing `verify` command and `ontos/commands/verify.py`, preserving current CLI behavior while adding `--portfolio`.
2. Normalize the registry path to `~/Dev/.dev-hub/registry/projects.json` everywhere, with `PortfolioConfig.registry_path` as the canonical override point.
3. In the same pass, scrub the remaining stale wording:
   - remove atomicity/file-rename leftovers from Sections 1, 6, and 8
   - remove stale-lock wording from Section 8
   - reconcile Section 4.4 / 4.10 prose with the Section 4.4 matrix and Section 4.7's actual bundle logic

**Estimated effort:** 1-2 hours of CA cleanup, then Phase C can begin.
