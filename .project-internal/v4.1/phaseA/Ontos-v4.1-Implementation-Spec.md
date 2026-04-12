# Ontos v4.1 Implementation Spec

**Version:** 1.1 (final)
**Date:** 2026-04-11
**Author:** Claude (Chief Architect, Phase A + B.3 + C.0 fold-in)
**Status:** SPEC v1.1 FINAL -- C.0 resolutions folded in, ready for B.4 verification
**Source of truth:** [Ontos-v4.1-Proposal.md](../../.ontos-internal/strategy/proposals/v4.1/Ontos-v4.1-Proposal.md) (v3, re-scoped per PR #84 review)

---

## v1.1 Changes

Spec v1.0 was reviewed by 9 reviewers across 3 model families (Claude Code, Codex, Gemini CLI). Verdict: **Needs Revision** with 7 blocking issues, 13 should-fix issues, 24 minor issues. This v1.1 revision addresses all blocking issues and accepted P2/P3 fixes.

**Key changes (v1.1 review response):**
- **FTS5 schema unified** (UB-1): Single canonical schema definition in Section 4.1. `concepts TEXT` added to `documents` table. BM25 weight vector corrected.
- **Atomicity claims downgraded** (UB-2): "Atomic multi-file writes" replaced with "best-effort sequential commit." Git clean-state precondition added for `rename_document()`. Recovery path documented.
- **Locking architecture resolved** (UB-3): Unified `flock`-based locking in §4.9. PID-reuse vulnerability eliminated.
- **Rename factual errors corrected** (UB-4): `_compute_rename_plan()` corrected to `_prepare_plan()`. File-rename claims removed. OQ-2 resolved to (A) ID-only. `old_path`/`new_path` removed from response schema.
- **Tool-availability matrix added** (UB-5): Authoritative matrix in Section 4.4 defines exactly which tools appear in each server mode. `_invoke_tool()` routing clarified with separate wrapper pattern. `--read-only` strips write tools from `tools/list`.
- **`verify` subcommand added to Track A** (UB-6): Full Technical Design in §4.13. CLI subcommand for `.dev-hub` transition validation.
- **`get_context_bundle()` single-ws crash fixed** (UB-7): Guard added for `workspace_id` in single-workspace mode. OQ-1 resolved to (B).
- **P2 fixes accepted:** Deterministic bundle tiebreaker (US-1), typed write-error schema (US-2), wrapper language corrected (US-3), promote semantics unified (US-4), partial classification clarified (US-5), tilde/mkdir fix (US-6), search transaction (US-7), .gitignore step (US-8), slug collision handling (US-10), Track A->B handoff state (US-13).
- **P2 deferred:** Rebuild failure handling (US-9, implementation detail), risk re-rating (US-12, confirmed unchanged).

**C.0 orchestrator resolutions (folded into v1.1 final):**
- **FTS5 mode → Standalone (Option A).** 800KB duplication negligible at scale. Eliminates ordinal-mapping bug. §4.1, §4.6, §6.
- **Lock architecture → Unified flock, Track A substrate (Option A).** Kernel-managed, eliminates PID-reuse. `SessionContext._acquire_lock()` updated. §4.4, §4.9.
- **`verify` subcommand → INCLUDED in Track A.** `.dev-hub` transition within 4 weeks. New §4.13, §2, §3, §6, §8, §9 updated.

**B.4 cleanup pass (post-verification):** B.4 verifier (Codex) returned Partial Challenge. One targeted cleanup applied: (1) §4.13 rewritten as additive extension of the existing `ontos verify` command — `MODIFY` not `CREATE`, correct handler name `_cmd_verify`, `--portfolio` flag branch preserving existing staleness-verification behavior; (2) registry path normalized to `~/Dev/.dev-hub/registry/projects.json` everywhere; (3) residual v1.0 language scrubbed — atomicity claims in §1/§6/§8, "file rename" in test descriptions, "stale locks" in risk text; (4) §4.4/§4.7/§4.10 prose reconciled with tool-availability matrix — `get_context_bundle` data source correctly described as SnapshotCache (single-ws) / create_snapshot() (portfolio), not "portfolio DB."

**Self-review checklist v1.1 final:** All items pass. All 3 `[PENDING C.0 RESOLUTION]` placeholders resolved. No placeholders remain. B.4 cleanup pass applied.

---

## 1. Overview

Ontos v4.1 ("Portfolio Authority") extends the v4.0 single-project MCP bridge into a multi-workspace server with a SQLite portfolio index, cross-project FTS5 search, token-budgeted context bundles, four write-capable MCP tools, and a `verify` CLI subcommand for `.dev-hub` transition validation -- all over stdio transport.

| Track | Theme | Risk |
|-------|-------|------|
| **Track A** | Portfolio index + 3 read tools (`project_registry`, `search`, `get_context_bundle`) | **MEDIUM** -- new SQLite layer, new tool implementations, but read-only surface |
| **Track B** | 4 write tools (`scaffold_document`, `rename_document`, `log_session`, `promote_document`) + index invalidation | **MEDIUM-HIGH** -- file mutation, ID-only rename with multi-file reference updates (best-effort sequential commit), index consistency |
| **Shared** | Tool registration plumbing, types, config, `workspace_id` parameter threading | **LOW** -- mechanical wiring changes |

**Sequencing:** Track A merges (PR #1) before Track B begins (PR #2). Track B depends on Track A's merged portfolio.db schema and refresh mechanism.

---

## 2. Scope

### In-Scope

**Track A (PR #1):**
- [ ] `~/.config/ontos/portfolio.db` -- SQLite + FTS5 database
- [ ] Portfolio index builder: initial seed from `.dev-hub/registry/projects.json` + filesystem heuristic
- [ ] Incremental refresh: fingerprint-based per-workspace staleness detection
- [ ] `project_registry()` tool
- [ ] `search()` tool -- cross-project FTS5 with BM25 ranking
- [ ] `get_context_bundle()` tool -- simple bundling with token budget
- [ ] Undocumented project handling (thin metadata for projects without `.ontos.toml`)
- [ ] `~/.config/ontos/portfolio.toml` config file
- [ ] `ontos serve --portfolio` CLI flag
- [ ] `ontos verify --portfolio` flag extension for `.dev-hub` transition validation
- [ ] Unified `flock`-based workspace locking (substrate for Track B write tools)
- [ ] Optional `workspace_id` parameter plumbing on existing 8 tools (ignored in single-workspace mode)

**Track B (PR #2):**
- [ ] `scaffold_document()` tool
- [ ] `rename_document()` tool
- [ ] `log_session()` tool
- [ ] `promote_document()` tool
- [ ] `--read-only` startup flag stripping write tools from MCP surface
- [ ] Per-workspace file locking (`.ontos.lock`)
- [ ] Index invalidation hooks: write tools trigger workspace re-index in portfolio mode
- [ ] Write tool error handling: `isError: true` returns, never exceptions to client

**Shared:**
- [ ] `OntosFastMCP` registration changes to support conditional tool registration
- [ ] New Pydantic response schemas for all 7 new tools
- [ ] Common tool schema types (e.g., `WorkspaceId` parameter type)
- [ ] Config additions: `[mcp]` section gains `read_only` field; new `[portfolio]` section in `portfolio.toml`

### Out-of-Scope (deferred to v4.2)

| Item | Rationale |
|------|-----------|
| HTTP/Streamable HTTP transport | No concrete consumer. JohnnyOS doesn't exist yet. Proposal Section 13. |
| Security model (bearer token, audit logging, CORS) | Coupled to HTTP transport. |
| Daemon mode / background indexer | Stdio sessions are short-lived; startup rebuild is <1s. |
| Calibrated 5-signal bundle scoring | Needs usage data from v4.1 to calibrate. Kill criterion in proposal Section 7.3. |
| MCP Resources and Prompts primitives | No consumer demand. Proposal Q2. |
| Cross-workspace `depends_on` in frontmatter | Schema supports it, but UI/validation deferred. Proposal Q1. |
| `starlette`, `uvicorn`, `cachetools` dependencies | All downstream of HTTP transport. |

---

## 3. Dependencies

### Prerequisites

| Dependency | Current | Target | Notes |
|-----------|---------|--------|-------|
| `mcp` (PyPI) | `>=1.2` | `>=1.27.0,<2.0` | Proposal Section 8. Upper bound due to Beta status. |
| `pydantic` | `>=2.0` | `>=2.0` | Unchanged |
| `sqlite3` | stdlib | stdlib | No new PyPI dependency |
| Python (base) | `>=3.9` | `>=3.9` | Unchanged |
| Python (MCP extra) | `>=3.9` | `>=3.10` | MCP SDK mandates 3.10+. Must update `pyproject.toml` classifier and extra metadata. |

### Blockers

- **Track B is blocked by Track A merge.** Track B's write tools must invalidate the portfolio index (Section 4.8), which requires Track A's `portfolio.db` schema and `PortfolioIndex` class to be merged.
- **`.dev-hub/registry/projects.json` must exist** at `~/Dev/.dev-hub/registry/projects.json` for portfolio seeding. If missing, fall back to pure filesystem heuristic (walk `scan_roots` for `.git/` directories).
- **`verify --portfolio` reads `~/Dev/.dev-hub/registry/projects.json`** — this is an external dependency. If the file is missing, `verify` exits with code 2 and a clear error message. The file path is configurable via `portfolio.toml` `registry_path`.

### Mitigations

- If `mcp>=1.27.0` is not yet released when implementation begins, pin to the latest available `>=1.2` and add a `# TODO: bump to >=1.27.0` comment. The stdio transport path does not require 1.27.0 features.
- Portfolio DB is a rebuildable cache. Any schema migration is handled by rebuild-from-scratch (see Section 4.1).

---

## 4. Technical Design

### 4.1 Portfolio Database Layer [Track A]

**Purpose:** Persistent, rebuildable SQLite cache spanning all workspaces for cross-project queries.

**Files:**
| Action | Path |
|--------|------|
| CREATE | `ontos/mcp/portfolio.py` |
| MODIFY | `ontos/mcp/server.py` |
| CREATE | `~/.config/ontos/portfolio.db` (runtime artifact) |
| CREATE | `~/.config/ontos/portfolio.toml` (user config, created on first `--portfolio` run) |

**Implementation:**

1. Create `ontos/mcp/portfolio.py` with class `PortfolioIndex`:

```python
class PortfolioIndex:
    """SQLite-backed portfolio index for cross-project queries."""

    SCHEMA_VERSION = 1
    PRAGMA_BLOCK = """
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = NORMAL;
        PRAGMA cache_size = -16000;
        PRAGMA mmap_size = 67108864;
        PRAGMA temp_store = MEMORY;
        PRAGMA busy_timeout = 5000;
    """

    def __init__(self, db_path: Path) -> None: ...
    def open(self) -> None: ...
    def close(self) -> None: ...
    def rebuild_all(self, scan_roots: list[Path], exclude: list[str]) -> None: ...
    def rebuild_workspace(self, slug: str, workspace_root: Path) -> None: ...
    def is_workspace_stale(self, slug: str) -> bool: ...
    def get_projects(self) -> list[dict[str, Any]]: ...
    def search_fts(self, query: str, workspace: str | None, offset: int, limit: int) -> dict[str, Any]: ...
    def get_workspace_documents(self, slug: str) -> list[dict[str, Any]]: ...
```

2. On `open()`, execute the PRAGMA block, then check `PRAGMA user_version`:
   - If `user_version` matches `SCHEMA_VERSION` (1), proceed normally.
   - If mismatch or DB corrupt, close connection, delete DB file, recreate from scratch via `rebuild_all()`.
   - Run `PRAGMA optimize = 0x10002` after PRAGMAs.

3. Schema creation (executed on fresh DB):

```sql
CREATE TABLE projects (
    slug        TEXT PRIMARY KEY,
    path        TEXT NOT NULL UNIQUE,
    status      TEXT NOT NULL,        -- documented | partial | undocumented | archived
    doc_count   INTEGER DEFAULT 0,
    has_ontos   BOOLEAN DEFAULT FALSE,
    has_readme  BOOLEAN DEFAULT FALSE,
    last_scanned TEXT,
    last_modified TEXT,
    tags        TEXT,                 -- JSON array
    metadata    TEXT                  -- JSON object
);

CREATE TABLE documents (
    id           TEXT NOT NULL,
    workspace    TEXT NOT NULL REFERENCES projects(slug),
    type         TEXT NOT NULL,
    status       TEXT NOT NULL,
    path         TEXT NOT NULL,
    title        TEXT,
    curation     TEXT,
    content_hash TEXT,
    word_count   INTEGER,
    concepts     TEXT,                -- space-separated concept terms from frontmatter
    body         TEXT,                -- full document body for FTS indexing
    last_modified TEXT,
    PRIMARY KEY (workspace, id)
);

CREATE TABLE edges (
    from_workspace TEXT NOT NULL,
    from_id        TEXT NOT NULL,
    to_workspace   TEXT NOT NULL,
    to_id          TEXT NOT NULL,
    type           TEXT NOT NULL DEFAULT 'depends_on',
    PRIMARY KEY (from_workspace, from_id, to_workspace, to_id, type)
);

CREATE TABLE scan_state (
    workspace    TEXT PRIMARY KEY REFERENCES projects(slug),
    fingerprint  TEXT NOT NULL,       -- JSON: {path: [mtime_ns, size], ...}
    scanned_at   TEXT NOT NULL
);

-- FTS5 standalone mode: stores its own copy of indexed columns.
-- 800KB storage duplication is negligible at 400-doc scale.
-- Eliminates the ordinal-mapping bug risk that external content mode introduces.
CREATE VIRTUAL TABLE fts_content USING fts5(
    title,
    concepts,
    body,
    tokenize='porter unicode61',
    prefix='2,3'
);

-- Persistent BM25 rank: title 10x, concepts 3x, body 1x
-- Weight vector has 3 elements matching 3 FTS5 columns (title, concepts, body)
INSERT INTO fts_content(fts_content, rank) VALUES('rank', 'bm25(10.0, 3.0, 1.0)');

CREATE INDEX idx_documents_workspace ON documents(workspace);
CREATE INDEX idx_documents_type ON documents(type);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_edges_to ON edges(to_workspace, to_id);

PRAGMA user_version = 1;
```

**FTS5 mode: Standalone.** The FTS5 virtual table stores its own copy of indexed text (title, concepts, body). This duplicates ~800KB of text at the current 400-document scale -- negligible. Standalone mode eliminates the ordinal-mapping bug that external content mode introduces, where column position misalignment between the `documents` table and the FTS5 virtual table causes `snippet()` to return data from the wrong column at runtime. This was the unanimous top finding across all 9 Phase B reviewers.

`rebuild_workspace()` deletes all FTS5 rows for the workspace and reinserts from the `documents` table -- independent operations on independent tables with no ordinal-mapping concerns. The `documents` table includes both `concepts TEXT` (space-separated terms from frontmatter) and `body TEXT` (full markdown content) to support FTS indexing.

4. `rebuild_workspace(slug, workspace_root)` logic:
   - Acquire write lock: `BEGIN IMMEDIATE`
   - Delete existing rows for this workspace from `documents`, `edges`
   - Delete FTS5 rows: `DELETE FROM fts_content WHERE rowid IN (SELECT rowid FROM documents WHERE workspace = ?)`
     (must delete FTS5 rows BEFORE deleting `documents` rows so rowid references are still valid; alternatively delete FTS5 rows by matching on a prior rowid snapshot -- but since standalone mode stores its own copy, a simpler approach is to delete ALL fts_content rows for this workspace, then reinsert)
   - Call `create_snapshot(root=workspace_root, include_content=True, ...)` (existing `ontos.io.snapshot`)
   - For each document in snapshot: insert into `documents` (including `body=doc.content`), insert FTS5 row (`INSERT INTO fts_content(rowid, title, concepts, body) VALUES (last_insert_rowid_of_documents_row, title, concepts, body)`), insert edges from `doc.depends_on`
   - Update `scan_state` with current fingerprint (same `(mtime_ns, size)` approach as `SnapshotCache`)
   - After commit, verify: FTS5 row count for this workspace equals `documents` row count for this workspace
   - `COMMIT`

5. `is_workspace_stale(slug)` logic:
   - Read `scan_state.fingerprint` JSON for this workspace
   - Compare against current filesystem state using the same `_stat_fingerprint()` approach from `ontos/mcp/cache.py:280-285`
   - Return `True` if any file changed, added, or removed

6. Concurrency rules:
   - **All write transactions use `BEGIN IMMEDIATE`.** This is critical -- deferred transactions that upgrade from read to write cause `SQLITE_BUSY` regardless of `busy_timeout`.
   - Serialize writes through a `threading.Lock` on the `PortfolioIndex` instance.
   - Disable `wal_autocheckpoint` on writer: `PRAGMA wal_autocheckpoint = 0`. Run `PRAGMA wal_checkpoint(PASSIVE)` after every `rebuild_workspace` call.
   - Do not use connection pooling. Open a fresh connection per operation.
   - Run `INSERT INTO fts_content(fts_content) VALUES('optimize')` after `rebuild_all()` completes.

**Constraints:**
- The portfolio DB is a rebuildable cache. Deleting it must be safe -- the server rebuilds on next startup.
- No new PyPI dependencies. `sqlite3` is stdlib.
- The `documents.body` column stores the full markdown content. For 400 documents at ~2KB average, this is ~800KB -- well within SQLite's comfort zone.

### 4.2 Portfolio Config [Track A]

**Purpose:** User-facing configuration for portfolio-level settings.

**Files:**
| Action | Path |
|--------|------|
| CREATE | `ontos/mcp/portfolio_config.py` |
| MODIFY | `ontos/io/config.py` |

**Implementation:**

1. Create `ontos/mcp/portfolio_config.py`:

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import tomli  # or tomllib on 3.11+

@dataclass
class PortfolioConfig:
    scan_roots: List[str] = field(default_factory=lambda: ["~/Dev"])
    exclude: List[str] = field(default_factory=lambda: ["~/Dev/.dev-hub", "~/Dev/archive"])
    registry_path: Optional[str] = "~/Dev/.dev-hub/registry/projects.json"
    bundle_token_budget: int = 8192
    bundle_max_logs: int = 5
    bundle_log_window_days: int = 14

PORTFOLIO_CONFIG_PATH = Path.home() / ".config" / "ontos" / "portfolio.toml"

def load_portfolio_config() -> PortfolioConfig:
    """Load portfolio config from ~/.config/ontos/portfolio.toml.

    Returns default config if file does not exist.
    """
    ...

def ensure_portfolio_config() -> Path:
    """Create default portfolio.toml if it doesn't exist. Return path."""
    ...
```

2. The config file format:

```toml
[portfolio]
scan_roots = ["~/Dev"]
exclude = ["~/Dev/.dev-hub", "~/Dev/archive"]
registry_path = "~/Dev/.dev-hub/registry/projects.json"

[bundle]
token_budget = 8192
max_logs = 5
log_window_days = 14
```

3. In `ontos/io/config.py`, add a `load_portfolio_config` import path for convenience but keep the implementation in `portfolio_config.py` to avoid polluting the per-project config loader.

**Constraints:**
- `portfolio.toml` is separate from `.ontos.toml`. It lives in `~/.config/ontos/` because it's user-global, not per-project.
- Use `tomli` (already a transitive dependency via `tomli>=2.0.1` in `pyproject.toml` for Python <3.11) or `tomllib` (stdlib on 3.11+) for parsing. The same conditional import pattern already used in `ontos/io/toml.py` applies.

### 4.3 Portfolio Scanner [Track A]

**Purpose:** Discover projects and populate the portfolio index on startup.

**Files:**
| Action | Path |
|--------|------|
| CREATE | `ontos/mcp/scanner.py` |

**Implementation:**

1. Create `ontos/mcp/scanner.py`:

```python
def discover_projects(
    scan_roots: list[Path],
    exclude: list[str],
    registry_path: Path | None,
) -> list[ProjectEntry]:
    """Discover all projects from registry + filesystem heuristic."""
    ...

@dataclass
class ProjectEntry:
    slug: str         # directory name, lowercased, dots/spaces -> hyphens
    path: Path
    status: str       # documented | partial | undocumented | archived
    has_ontos: bool
    has_readme: bool
    doc_count: int
    tags: list[str]
    metadata: dict[str, Any]

def slugify(directory_name: str) -> str:
    """Convert directory name to slug. 'canary.work' -> 'canary-work'."""
    return directory_name.lower().replace(".", "-").replace(" ", "-")
```

2. Discovery algorithm:
   - Read `registry_path` (`.dev-hub/registry/projects.json`) if it exists. Extract known project paths and metadata.
   - Walk each `scan_root` directory (non-recursive -- only immediate children) looking for directories containing `.git/`.
   - Skip directories matching `exclude` patterns.
   - For each discovered directory:
     - Check for `.ontos.toml` -> `has_ontos = True`
     - Check for `README.md` -> `has_readme = True`
     - Classify (US-5, explicit boolean logic from proposal):
       - `documented`: `has_ontos AND doc_count >= 5`
       - `partial`: `(has_readme AND NOT has_ontos) OR (has_ontos AND doc_count < 5)`
       - `undocumented`: `NOT has_readme AND NOT has_ontos`
       - `archived`: explicitly marked in registry metadata
   - Merge registry entries with filesystem entries. Registry is authoritative for metadata; filesystem is authoritative for existence.
   - **Slug collision handling (US-10):** If two directories in different `scan_roots` produce the same slug, append a numeric suffix: `my-project`, `my-project-2`. Log a warning to stderr. The first directory encountered (alphabetical by `scan_root` order, then directory name) gets the unsuffixed slug.

3. The `slugify()` function implements the proposal's slugification rule (Section D2): directory name, lowercased, dots and spaces replaced by hyphens. No aliases.

**Constraints:**
- `discover_projects` must be pure-ish: it reads the filesystem but does not write to it.
- Walk `scan_roots` non-recursively (immediate children only) to avoid descending into `node_modules` or `.git` subtrees. Each child with `.git/` is a candidate.

### 4.4 Server Bootstrap Changes [Shared]

**Purpose:** Support both single-workspace and portfolio modes from the same `serve()` entry point.

**Files:**
| Action | Path |
|--------|------|
| MODIFY | `ontos/mcp/server.py` |
| MODIFY | `ontos/cli.py` |
| CREATE | `ontos/mcp/locking.py` (unified flock lock — Track A substrate for Track B) |
| MODIFY | `ontos/core/context.py` (`SessionContext._acquire_lock()` → flock-based `.ontos.lock`) |
| MODIFY | `.gitignore` (add `.ontos.lock`) |

**Implementation:**

1. Add `--portfolio` and `--read-only` flags to the `serve` subparser in `ontos/cli.py`:

```python
serve_parser.add_argument("--portfolio", action="store_true",
    help="Enable portfolio mode: index all projects under scan_roots")
serve_parser.add_argument("--read-only", action="store_true",
    help="Strip write tools from the MCP surface")
```

2. Modify `serve()` in `ontos/mcp/server.py` to accept new parameters:

```python
def serve(
    workspace_root: Path,
    *,
    portfolio: bool = False,
    read_only: bool = False,
) -> int:
    """Build the cache and start the stdio MCP runtime."""
    ...
```

3. In single-workspace mode (`portfolio=False`), behavior is identical to v4.0 plus `get_context_bundle`. The `SnapshotCache` is built as before. Track A read tools are registered conditionally per the matrix in §4.4: `project_registry` and `search` are portfolio-mode only; `get_context_bundle` is available in both modes. The `workspace_id` parameter on all tools is accepted but ignored.

4. In portfolio mode (`portfolio=True`):
   - Load `PortfolioConfig` from `~/.config/ontos/portfolio.toml`
   - Create `PortfolioIndex` at `~/.config/ontos/portfolio.db`
   - Call `portfolio_index.open()` and `portfolio_index.rebuild_all(...)` (full rebuild on startup, <1s)
   - The primary workspace is `workspace_root` (the cwd or explicitly passed root)
   - `SnapshotCache` is still built for the primary workspace (for existing tools)
   - Portfolio-specific tools (`project_registry`, `search`, `get_context_bundle`) are registered with access to `PortfolioIndex`

5. **Authoritative tool-availability matrix (UB-5):**

| Tool | Category | `ontos serve` (single-ws) | `ontos serve --portfolio` | `--read-only` effect |
|------|----------|--------------------------|--------------------------|---------------------|
| `workspace_overview` | v4.0 read | YES | YES | No change |
| `context_map` | v4.0 read | YES | YES | No change |
| `get_document` | v4.0 read | YES | YES | No change |
| `list_documents` | v4.0 read | YES | YES | No change |
| `export_graph` | v4.0 read | YES | YES | No change |
| `query` | v4.0 read | YES | YES | No change |
| `health` | v4.0 read | YES | YES | No change |
| `refresh` | v4.0 read | YES | YES | No change |
| `project_registry` | Track A portfolio | NO | YES | No change |
| `search` | Track A portfolio | NO | YES | No change |
| `get_context_bundle` | Track A read | YES | YES | No change |
| `scaffold_document` | Track B write | YES | YES | **ABSENT from tools/list** |
| `rename_document` | Track B write | YES | YES | **ABSENT from tools/list** |
| `log_session` | Track B write | YES | YES | **ABSENT from tools/list** |
| `promote_document` | Track B write | YES | YES | **ABSENT from tools/list** |

   **`--read-only` behavior:** Write tools are completely absent from `tools/list`. They are never registered. A client that attempts to call a write tool by name receives a standard MCP "tool not found" error. This is the GitHub MCP server pattern and the strongest safety primitive.

   **`workspace_id` behavior on v4.0 tools:** In single-workspace mode, `workspace_id` appears as an optional parameter in the tool schema but is silently ignored. In portfolio mode, `workspace_id` on v4.0 tools targets the primary workspace by default; passing a non-primary `workspace_id` returns `isError: true` with `E_CROSS_WORKSPACE_NOT_SUPPORTED`.

6. Tool registration organization in `create_server()`:
   - **`_register_core_tools(server, cache, workspace_name, register_fn)`** -- the 8 v4.0 read tools. Always called.
   - **`_register_portfolio_tools(server, portfolio_index, cache, register_fn)`** -- `project_registry`, `search`. Only called when `portfolio_index is not None`.
   - **`_register_bundle_tool(server, cache, portfolio_index, register_fn)`** -- `get_context_bundle`. Always called (works in both modes per OQ-1 resolution).
   - **`_register_write_tools(server, cache, register_fn, portfolio_index=None)`** -- 4 write tools. Skipped when `read_only=True`.
   - The `register` closure pattern is preserved -- each handler function captures its dependencies via closure.

7. **`_invoke_tool()` routing:** Three separate invocation wrappers (not one overloaded function):

   - **`_invoke_read_tool(tool_name, cache, tool_fn, **kwargs)`** -- existing pattern. Passes `SnapshotCacheView` to `tool_fn`. Used for v4.0 tools and `get_context_bundle` in single-ws mode.
   - **`_invoke_portfolio_tool(tool_name, portfolio_index, tool_fn, **kwargs)`** -- passes `portfolio_index` as first arg. Used for `project_registry`, `search`. No cache freshness check needed (reads from portfolio.db).
   - **`_invoke_write_tool(tool_name, cache, tool_fn, portfolio_index=None, **kwargs)`** -- passes live `cache` (not view). Acquires workspace lock. On success, calls `cache.force_refresh()` and optionally `portfolio_index.rebuild_workspace()`. Error handling returns `WriteToolErrorEnvelope`.

   All three wrappers share: usage logging, try/except for `OntosUserError`/`OntosInternalError`, `CallToolResult` construction.

8. Update `_render_instructions()` to mention new tools when registered.

**Constraints:**
- The existing `create_server(cache)` signature must remain callable with just `cache` for backward compatibility in tests. Add `portfolio_index` and `read_only` as keyword-only parameters with `None`/`False` defaults.
- The 8 existing tool registrations must produce identical `tools/list` output when `portfolio=False` and `read_only=False`. This is the backward-compatibility contract.
- `get_context_bundle` appears in `tools/list` in BOTH modes. In single-ws mode it uses the `SnapshotCache` (ignoring `workspace_id`); in portfolio mode it builds a fresh snapshot via `create_snapshot()` for the specified workspace (see §4.7 for the branching logic).

### 4.5 `project_registry()` Tool [Track A]

**Purpose:** Return the complete project inventory for routing and discovery.

**Files:**
| Action | Path |
|--------|------|
| MODIFY | `ontos/mcp/tools.py` |
| MODIFY | `ontos/mcp/schemas.py` |

**Implementation:**

1. Add to `ontos/mcp/tools.py`:

```python
def project_registry(portfolio_index: Any) -> dict[str, Any]:
    """Return the complete project inventory from the portfolio index."""
    projects = portfolio_index.get_projects()
    return {
        "project_count": len(projects),
        "projects": [
            {
                "slug": p["slug"],
                "path": p["path"],
                "status": p["status"],
                "doc_count": p["doc_count"],
                "last_updated": p["last_scanned"],
                "tags": json.loads(p["tags"]) if p["tags"] else [],
                "has_ontos": bool(p["has_ontos"]),
            }
            for p in projects
        ],
        "summary": f"Portfolio contains {len(projects)} projects.",
    }
```

2. Add Pydantic schema in `ontos/mcp/schemas.py`:

```python
class ProjectItem(StrictModel):
    slug: str
    path: str
    status: str
    doc_count: int
    last_updated: Optional[str]
    tags: List[str]
    has_ontos: bool

class ProjectRegistryResponse(StrictModel):
    project_count: int
    projects: List[ProjectItem]
    summary: str
```

3. Registration in `server.py`:

```python
register(
    name="project_registry",
    title="Project Registry",
    description="Returns the complete project inventory with metadata for routing and discovery.",
    handler=handle_project_registry,
    annotations=_readonly_annotations(),
    meta={"anthropic/maxResultSizeChars": 16000},
)
```

4. Annotations: `readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False`.

**Constraints:**
- This tool reads from `portfolio.db` only. No filesystem access during the tool call.
- In single-workspace mode (no `--portfolio`), this tool is NOT registered. It only appears in `tools/list` when portfolio mode is active.

### 4.6 `search()` Tool [Track A]

**Purpose:** Full-text search across the portfolio or a single workspace via FTS5.

**Files:**
| Action | Path |
|--------|------|
| MODIFY | `ontos/mcp/tools.py` |
| MODIFY | `ontos/mcp/schemas.py` |

**Implementation:**

1. Add to `ontos/mcp/tools.py`:

```python
def search(
    portfolio_index: Any,
    *,
    query_string: str,
    workspace_id: Optional[str] = None,
    offset: int = 0,
    limit: int = 20,
) -> dict[str, Any]:
    """Full-text search across the portfolio or a single workspace."""
    if not query_string or not query_string.strip():
        raise OntosUserError(
            "query_string must be non-empty.",
            code="E_EMPTY_QUERY",
        )
    if limit < 1 or limit > 100:
        raise OntosUserError(
            "limit must be between 1 and 100.",
            code="E_INVALID_LIMIT",
        )
    if offset < 0:
        raise OntosUserError(
            "offset must be >= 0.",
            code="E_INVALID_OFFSET",
        )
    if workspace_id is not None:
        _validate_workspace_id(portfolio_index, workspace_id)

    return portfolio_index.search_fts(query_string, workspace_id, offset, limit)
```

2. `PortfolioIndex.search_fts()` implementation (in `portfolio.py`):

```python
def search_fts(
    self, query: str, workspace: str | None, offset: int, limit: int
) -> dict[str, Any]:
    """Execute FTS5 search with BM25 ranking."""
    # Sanitize query for FTS5: escape double quotes, wrap terms
    safe_query = _sanitize_fts_query(query)

    sql = """
        SELECT d.id, d.workspace, d.type, d.status, d.path,
               snippet(fts_content, 2, '<mark>', '</mark>', '...', 32) AS snippet,
               fts_content.rank AS score
        FROM fts_content
        JOIN documents d ON d.rowid = fts_content.rowid
        WHERE fts_content MATCH ?
    """
    params: list[Any] = [safe_query]

    if workspace:
        sql += " AND d.workspace = ?"
        params.append(workspace)

    sql += " ORDER BY rank"  # CRITICAL: must ORDER BY rank for FTS5 performance
    sql += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    conn = self._connect()
    try:
        # US-7: Wrap both queries in explicit transaction for snapshot consistency
        conn.execute("BEGIN")
        rows = conn.execute(sql, params).fetchall()
        # Count total hits (without LIMIT)
        count_sql = """
            SELECT COUNT(*) FROM fts_content
            JOIN documents d ON d.rowid = fts_content.rowid
            WHERE fts_content MATCH ?
        """
        count_params: list[Any] = [safe_query]
        if workspace:
            count_sql += " AND d.workspace = ?"
            count_params.append(workspace)
        total = conn.execute(count_sql, count_params).fetchone()[0]
        conn.execute("COMMIT")
    finally:
        conn.close()

    return {
        "total_hits": total,
        "results": [
            {
                "doc_id": row[0],
                "workspace_slug": row[1],
                "type": row[2],
                "status": row[3],
                "path": row[4],
                "snippet": row[5],
                "score": round(row[6], 4),
            }
            for row in rows
        ],
    }
```

3. FTS5 query sanitization -- `_sanitize_fts_query(query: str) -> str`:
   - Strip leading/trailing whitespace
   - Escape `"` characters
   - If query contains no FTS5 operators (`AND`, `OR`, `NOT`, `NEAR`, `"`, `*`), wrap each term with implicit AND (FTS5 default)
   - If query contains FTS5 syntax, pass through (allow power users to use FTS5 query language directly)
   - Catch `sqlite3.OperationalError` from malformed FTS5 queries and raise `OntosUserError("Invalid search query syntax", code="E_INVALID_QUERY")`

4. Workspace validation helper (shared by `search` and `get_context_bundle`):

```python
def _validate_workspace_id(portfolio_index: Any, workspace_id: str) -> None:
    """Validate workspace_id exists in portfolio. Raise OntosUserError if not."""
    projects = portfolio_index.get_projects()
    slugs = [p["slug"] for p in projects]
    if workspace_id not in slugs:
        raise OntosUserError(
            f"Unknown workspace '{workspace_id}'. "
            f"Valid workspace slugs: {', '.join(sorted(slugs))}. "
            "Use project_registry() to discover available workspaces.",
            code="E_UNKNOWN_WORKSPACE",
        )
```

5. Pydantic schema:

```python
class SearchResultItem(StrictModel):
    doc_id: str
    workspace_slug: str
    type: str
    status: str
    path: str
    snippet: str
    score: float

class SearchResponse(StrictModel):
    total_hits: int
    results: List[SearchResultItem]
```

6. Registration:

```python
register(
    name="search",
    title="Search Documents",
    description="Full-text search across the portfolio or a single workspace.",
    handler=handle_search,
    annotations=_readonly_annotations(),
    meta={"anthropic/maxResultSizeChars": 32000},
)
```

**Constraints:**
- Results MUST be sorted by `ORDER BY rank` (FTS5 BM25). Any other sort forces a temp B-tree sort that is 10-50x slower per research consensus item.
- The `snippet()` function uses column index 2 (body), with `<mark>` delimiters, `...` as ellipsis, max 32 tokens per snippet.
- Portfolio-mode only. Not registered in single-workspace mode.

### 4.7 `get_context_bundle()` Tool [Track A]

**Purpose:** Return a token-budgeted context package for a workspace.

**Files:**
| Action | Path |
|--------|------|
| CREATE | `ontos/mcp/bundler.py` |
| MODIFY | `ontos/mcp/tools.py` |
| MODIFY | `ontos/mcp/schemas.py` |

**Implementation:**

1. Create `ontos/mcp/bundler.py`:

```python
from ontos.core.tokens import estimate_tokens

@dataclass
class BundleDocument:
    id: str
    type: str
    status: str
    content: str
    score: float
    token_estimate: int

def build_context_bundle(
    snapshot: DocumentSnapshot,
    workspace_root: Path,
    workspace_slug: str,
    *,
    token_budget: int = 8192,
    max_logs: int = 5,
    log_window_days: int = 14,
) -> dict[str, Any]:
    """Build a token-budgeted context bundle from a workspace snapshot."""
    ...
```

2. Bundling algorithm (proposal Section 7.2):

   **Step 1 -- Classify and score documents:**
   - `kernel` documents: score = 1.0 (always highest priority)
   - Other documents: score by in-degree. `score = 0.5 + 0.5 * (in_degree / max_in_degree)` where `in_degree = len(snapshot.graph.reverse_edges.get(doc.id, []))`. If `max_in_degree == 0`, all non-kernel scores are 0.5.
   - Recent logs (within `log_window_days` days, up to `max_logs`): score = 0.3 (included after kernels and high-in-degree docs)
   - Remaining: sorted by type rank from `TYPE_RANKS` in `ontos/mcp/tools.py` (strategy=1 > product=2 > atom=3 > log=4 > reference=5), then by in-degree within type
   - **Deterministic tiebreaker (US-1):** When two documents have the same score, sort alphabetically by document ID. This ensures identical output across invocations for LLM prompt cache stability.

   **Step 2 -- Build priority list:**
   ```
   priority = kernel_docs (sorted by in-degree desc)
            + top_N_by_indegree (non-kernel, sorted by in-degree desc)
            + recent_logs (sorted by date desc, capped at max_logs)
            + remaining (sorted by type_rank asc, then in-degree desc)
   ```

   **Step 3 -- Greedy knapsack packing:**
   - For each document in priority order, estimate tokens via `estimate_tokens(doc.content)` (existing function in `ontos/core/tokens.py:8-21`)
   - Kernel documents are always included, even if they exceed 50% of budget
   - For non-kernel documents: if `running_total + doc_tokens <= token_budget`, include; otherwise skip
   - Track excluded documents with count

   **Step 4 -- Lost-in-the-middle ordering:**
   - Split included documents into `first_half` and `second_half`
   - Place highest-scored documents at positions 0 and -1
   - Mid-priority documents go in the middle
   - Concrete algorithm: sort included by score descending. Interleave: index 0 -> position 0, index 1 -> position -1, index 2 -> position 1, index 3 -> position -2, etc.

   **Step 5 -- Render bundle text:**
   - For each included document in the reordered list:
     ```
     ## {humanized_title} ({type}, {status})

     {content}

     ---
     ```
   - Append metadata footer: `\n\n<!-- Bundle: {doc_count} documents, ~{token_estimate} tokens, {excluded_count} excluded -->`

   **Step 6 -- Detect stale documents:**
   - For each included document, check if any `describes` target has been modified more recently than the document itself (using the staleness logic from `ontos/core/staleness.py`). If so, add to `stale_documents` list.

3. Tool function in `tools.py`:

```python
def get_context_bundle(
    portfolio_index: Any,
    cache: Any,
    *,
    workspace_id: Optional[str] = None,
    token_budget: int = 8192,
) -> dict[str, Any]:
    """Return a token-budgeted context package for a workspace."""
    if token_budget < 1024:
        raise OntosUserError(
            "token_budget must be at least 1024.",
            code="E_INVALID_BUDGET",
        )
    if token_budget > 128000:
        raise OntosUserError(
            "token_budget must be at most 128000.",
            code="E_INVALID_BUDGET",
        )

    # Resolve workspace -- dual code path (UB-7 fix)
    if portfolio_index is None:
        # SINGLE-WORKSPACE MODE: ignore workspace_id per §4.10 contract
        # (workspace_id is "accepted but ignored" in single-ws mode)
        slug = slugify(cache.workspace_root.name)
        snapshot = cache.get_fresh_snapshot()
        workspace_root = cache.workspace_root
    elif workspace_id is None:
        # PORTFOLIO MODE, no workspace specified: require it
        raise OntosUserError(
            "workspace_id is required in portfolio mode. "
            "Use project_registry() to discover available workspaces.",
            code="E_MISSING_WORKSPACE",
        )
    else:
        # PORTFOLIO MODE with workspace_id
        _validate_workspace_id(portfolio_index, workspace_id)
        projects = portfolio_index.get_projects()
        project = next(p for p in projects if p["slug"] == workspace_id)
        if project["status"] == "undocumented":
            raise OntosUserError(
                f"Workspace '{workspace_id}' is undocumented. "
                "Run `ontos init` in that project directory first.",
                code="E_UNDOCUMENTED_WORKSPACE",
            )
        slug = workspace_id
        workspace_root = Path(project["path"])
        # Build a fresh snapshot for this workspace
        snapshot = create_snapshot(
            root=workspace_root,
            include_content=True,
            filters=None,
            git_commit_provider=None,
            scope=None,
        )

    bundle = build_context_bundle(
        snapshot, workspace_root, slug,
        token_budget=token_budget,
    )
    return bundle
```

4. Pydantic schema:

```python
class BundleDocumentItem(StrictModel):
    id: str
    type: str
    score: float
    token_estimate: int

class StaleDocumentItem(StrictModel):
    id: str
    reason: str

class GetContextBundleResponse(StrictModel):
    workspace_id: str
    workspace_slug: str
    token_estimate: int
    document_count: int
    bundle_text: str
    included_documents: List[BundleDocumentItem]
    excluded_count: int
    stale_documents: List[StaleDocumentItem]
    warnings: List[str]
```

5. Registration:

```python
register(
    name="get_context_bundle",
    title="Get Context Bundle",
    description="Returns a token-budgeted context package for a workspace.",
    handler=handle_get_context_bundle,
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=False,  # output depends on freshness state
        openWorldHint=False,
    ),
    meta={"anthropic/maxResultSizeChars": 200000},
)
```

**Constraints:**
- `get_context_bundle` is registered in BOTH single-workspace and portfolio modes. In single-workspace mode, `workspace_id` is ignored and the tool bundles the current workspace. In portfolio mode, `workspace_id` is required.
- Token estimation uses the existing `estimate_tokens()` from `ontos/core/tokens.py` (character heuristic: `len(content) // 4`). No new dependency on tiktoken.
- The `score` field in `included_documents` is normalized to [0.0, 1.0].

### 4.8 Write Tools [Track B]

**Purpose:** Expose file-mutating operations as MCP tools.

**Files:**
| Action | Path |
|--------|------|
| CREATE | `ontos/mcp/write_tools.py` |
| MODIFY | `ontos/mcp/server.py` |
| MODIFY | `ontos/mcp/schemas.py` |
| MODIFY | `ontos/mcp/tools.py` (add workspace_id helpers) |

**Shared write tool properties:**
- Annotations: `readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False`
- All return `{success: true, ...}` on success. Failures return `isError: true` with the typed error schema below -- never exceptions to the MCP client.
- Each write tool acquires a per-workspace file lock before modifying files (Section 4.9)
- After completing, triggers `cache.force_refresh()` so subsequent read tools see updated state
- In portfolio mode, additionally triggers `portfolio_index.rebuild_workspace(slug, workspace_root)` to update the portfolio DB
- File writes use `SessionContext.buffer_write()` + `SessionContext.commit()`, which performs **best-effort sequential writes with temp-file cleanup** -- NOT atomic transactions. If the process crashes mid-commit, some files may be written and others not. Recovery: `git checkout -- .` (see Section 4.9).

**Typed write-error schema (US-2):**

All write tool errors return `CallToolResult` with `isError=True` and `structuredContent` conforming to:

```python
class WriteToolError(StrictModel):
    error_code: str          # e.g., "E_DUPLICATE_ID", "E_WORKSPACE_BUSY"
    what: str                # What happened: "Document ID 'foo' already exists"
    why: str                 # Why it failed: "IDs must be unique within a workspace"
    fix: str                 # How to fix: "Choose a different ID or use rename_document()"

class WriteToolErrorEnvelope(StrictModel):
    isError: Literal[True]
    error: WriteToolError
    content: List[ToolErrorTextItem]  # Text fallback for clients without structuredContent
```

The `content` text fallback concatenates: `"{what}. {why}. {fix}"`. This ensures LLM clients always receive actionable guidance for self-correction, per MCP protocol semantics (JSON-RPC -32xxx errors never reach the LLM; only `isError: true` tool responses do).

**Reuse plan (US-3):** Write tools do NOT simply wrap CLI commands. Each tool reuses specific internal functions but adapts them for MCP's non-interactive context:

| Tool | Reused from CLI | Adapted / New |
|------|----------------|---------------|
| `scaffold_document` | `create_scaffold()` from `core/curation.py`, `serialize_frontmatter()` from `core/schema.py` | New: explicit parameter-driven creation (CLI scans for untagged files) |
| `rename_document` | `_prepare_plan()` from `commands/rename.py`, `scan_body_references()` from `core/body_refs.py` | Adapted: construct `RenameOptions` from MCP params, convert `RenameError` to `isError` |
| `log_session` | `create_session_log()` from `commands/log.py` | Adapted: explicit params replace interactive prompts, git info resolved server-side |
| `promote_document` | `get_curation_info()`, `promote_to_full()` from `core/curation.py` | Adapted: validation failure returns `isError: true` instead of interactive prompts |

#### 4.8.1 `scaffold_document()` [Track B]

**Purpose:** Create a new document from template at L0 curation level.

```python
def scaffold_document(
    cache: Any,
    *,
    type: str,
    id: str,
    title: str,
    workspace_id: Optional[str] = None,
    depends_on: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Create a new document from template."""
```

**Implementation steps:**

1. Validate `type` against `DocumentType` enum values: `kernel`, `strategy`, `product`, `atom`, `log`. Reject `reference`, `concept`, `unknown`. Error code: `E_INVALID_TYPE`.

2. Validate `id` format: must match `^[a-z][a-z0-9_]*$` (lowercase, underscores, starts with letter). Error code: `E_INVALID_ID`.

3. Check `id` uniqueness against `cache.snapshot.documents`. If duplicate, return `isError: true` with `E_DUPLICATE_ID`.

4. If `depends_on` is provided, validate all targets exist in `cache.snapshot.documents`. Error code: `E_DEPENDENCY_NOT_FOUND`.

5. Determine output path using existing path conventions from `ontos/core/paths.py`:
   - Logs: `{logs_dir}/{date}_{slugified_title}.md`
   - Others: `{docs_dir}/{id}.md` (or a subdirectory based on type if the project uses type-based organization)
   - Use `cache.config.paths.docs_dir` and `cache.config.paths.logs_dir`

6. Build frontmatter dict:
   ```python
   fm = {
       "id": id,
       "type": type,
       "status": "scaffold",
       "depends_on": depends_on or [],
   }
   ```
   Serialize using `serialize_frontmatter()` from `ontos/core/schema.py`.

7. Write the file: `---\n{fm_yaml}\n---\n\n# {title}\n`

8. Return:
   ```python
   {"success": True, "path": rel_path, "id": id, "type": type, "status": "scaffold", "curation_level": "L0"}
   ```

**Wraps:** Draws on logic from `ontos/commands/scaffold.py` but does NOT call the CLI scaffold command directly. The CLI command scans for untagged files; the MCP tool creates a single document with explicit parameters. Shared logic: `create_scaffold()` from `ontos/core/curation.py` for type inference heuristics, and `serialize_frontmatter()` from `ontos/core/schema.py`.

#### 4.8.2 `rename_document()` [Track B]

**Purpose:** Rename a document ID and update all references across the workspace. This is an **ID-only rename** -- file paths are not changed.

```python
def rename_document(
    cache: Any,
    *,
    document_id: str,
    new_id: str,
    workspace_id: Optional[str] = None,
) -> dict[str, Any]:
    """Rename a document ID and update all references."""
```

**Implementation steps:**

1. Validate `document_id` exists in `cache.snapshot.documents`. Error: `E_DOCUMENT_NOT_FOUND`.

2. Validate `new_id` format (same regex as scaffold). Error: `E_INVALID_ID`.

3. Validate `new_id` not already in use. Error: `E_DUPLICATE_ID`.

4. **Precondition: git clean state.** Before proceeding, check that the workspace has no uncommitted changes to tracked `.md` files (via `git status --porcelain`). If dirty, return `isError: true` with `E_DIRTY_WORKSPACE` and message: "Workspace has uncommitted changes. Commit or stash before renaming so you can recover with `git checkout -- .` if needed." This ensures the recovery path (Step 8) is always available.

5. Adapt the rename command's `_prepare_plan()` function (at `ontos/commands/rename.py:278`, signature: `_prepare_plan(options: RenameOptions, *, mode: str) -> Tuple[Optional[_PreparedPlan], Optional[RenameError]]`) for MCP use:
   - Construct a `RenameOptions(old_id=document_id, new_id=new_id, apply=True)` 
   - Call `_prepare_plan(options, mode="apply")` to compute the edit plan
   - If the function returns a `RenameError`, convert to `isError: true` with the error message
   - The plan contains: frontmatter edits (`id:` field in target document, `depends_on:` references in dependents) and body reference edits (via `scan_body_references()` from `ontos/core/body_refs.py`)

6. Apply the edit plan using `SessionContext`:
   - `SessionContext.buffer_write()` for each modified file
   - `SessionContext.commit()` to write all changes
   - **Note:** `commit()` uses best-effort sequential write with temp-file cleanup. It is NOT atomic -- if the process crashes mid-commit, some files may be written and others not. The git clean-state precondition (Step 4) ensures recovery via `git checkout -- .`.

7. The existing CLI rename does NOT perform filesystem file renames -- there are zero calls to `os.rename()`, `Path.rename()`, or `buffer_move()` in the rename module. The MCP tool matches this behavior: ID and references are updated in file contents, but file paths remain unchanged.

8. Return:
   ```python
   {
       "success": True,
       "old_id": document_id,
       "new_id": new_id,
       "path": rel_path,           # file path (unchanged by rename)
       "references_updated": count,
       "updated_files": [rel_path_1, rel_path_2, ...],
   }
   ```

**Recovery path:** If the rename produces unexpected results, the agent should run `git checkout -- .` to revert all file changes. This is possible because of the git clean-state precondition in Step 4. The response includes `updated_files` so the agent can `git diff` to verify the scope of changes before committing.

**Safety:** This is the highest-risk write tool because it modifies multiple files. The `updated_files` list is critical for agent verification.

**Reuse plan:** Reuses `_prepare_plan()` and the `RenameOptions`/`_PreparedPlan` data structures from `ontos/commands/rename.py`. The `scan_body_references()` function from `ontos/core/body_refs.py` is reused unchanged. The CLI command's `--apply` flag maps to immediate execution in MCP. Adaptation needed: construct `RenameOptions` from MCP parameters and convert `RenameError` to `isError: true` response.

#### 4.8.3 `log_session()` [Track B]

**Purpose:** Create a structured session log document.

```python
def log_session(
    cache: Any,
    *,
    summary: str,
    workspace_id: Optional[str] = None,
    branch: Optional[str] = None,
    event_type: str = "session",
) -> dict[str, Any]:
    """Create a structured session log."""
```

**Implementation steps:**

1. Validate `summary` is non-empty. Error: `E_EMPTY_SUMMARY`.

2. Validate `event_type` against known types. Accept aliases from `EVENT_TYPE_ALIASES` in `ontos/commands/log.py:24-29`.

3. Resolve git branch if `branch` is not provided: attempt `git rev-parse --abbrev-ref HEAD` from workspace root. If git is unavailable, use `"unknown"`.

4. Call `create_session_log()` from `ontos/commands/log.py:64-68`:
   ```python
   content, output_path = create_session_log(
       project_root=cache.workspace_root,
       options=EndSessionOptions(
           event_type=event_type,
           branch=branch,
           topic=summary,  # summary serves as the topic
       ),
       git_info={"branch": branch or resolved_branch},
   )
   ```

5. Write the log file to disk.

6. Return:
   ```python
   {"success": True, "path": rel_path, "id": log_id, "date": date_str}
   ```

**Wraps:** `ontos/commands/log.py` -- specifically `create_session_log()`. The CLI command has additional interactive features (auto-mode, impact suggestion); the MCP tool takes explicit parameters.

#### 4.8.4 `promote_document()` [Track B]

**Purpose:** Promote a document's curation level.

```python
def promote_document(
    cache: Any,
    *,
    document_id: str,
    target_level: str,
    workspace_id: Optional[str] = None,
) -> dict[str, Any]:
    """Promote a document's curation level."""
```

**Implementation steps:**

1. Validate `document_id` exists. Error: `E_DOCUMENT_NOT_FOUND`.

2. Validate `target_level` is `"L1"` or `"L2"`. Error: `E_INVALID_LEVEL`.

3. Read the document's current frontmatter via `load_frontmatter()` from `ontos/io/files.py`.

4. Get curation info via `get_curation_info(frontmatter)` from `ontos/core/curation.py:22-28`.

5. Check if promotion is valid:
   - Current level must be less than target level
   - If target is L2, check `curation_info.promotable`. If not promotable, return `isError: true` with `E_PROMOTION_BLOCKED` and `validation_warnings = curation_info.promotion_blockers` in the `fix` field. Do NOT modify the document.

6. If promotion is valid, call `promote_to_full()` from `ontos/core/curation.py` (for L2) or construct L1 frontmatter manually:
   - L0 -> L1: Add `status: draft`, ensure `depends_on` exists (empty list is OK for kernel/log types)
   - L0/L1 -> L2: Call `promote_to_full(frontmatter, depends_on=..., concepts=...)` which adds all L2-required fields

7. Write updated document using `SessionContext`.

8. Return on success:
   ```python
   {
       "success": True,
       "document_id": document_id,
       "old_level": "L0",  # or "L1"
       "new_level": "L2",  # or "L1"
   }
   ```
   Return on validation failure: `isError: true` with `E_PROMOTION_BLOCKED`. The `fix` field lists specific missing fields/blockers so the agent can address them.

**Reuse plan:** Reuses `get_curation_info()` and `promote_to_full()` from `ontos/core/curation.py`. The CLI command (`ontos/commands/promote.py`) has interactive prompts for `depends_on` and `concepts`; the MCP tool returns `isError: true` with specific blockers if requirements aren't met (no interactivity).

### 4.9 Workspace File Locking [Shared — Track A substrate]

**Purpose:** Prevent concurrent write operations (MCP + MCP, or MCP + CLI) from corrupting workspace state. This is **Track A substrate** — Track B's write tools depend on it, so the locking mechanism ships in Track A.

**Files:**
| Action | Path |
|--------|------|
| CREATE | `ontos/mcp/locking.py` |
| MODIFY | `ontos/core/context.py` (`SessionContext._acquire_lock()`, ~line 224) |
| MODIFY | `.gitignore` (add `.ontos.lock`) |

**Architecture: Unified `flock`-based locking**

- **Single lock file:** `<workspace>/.ontos.lock`
- **Mechanism:** `fcntl.flock(fd, LOCK_EX | LOCK_NB)` — kernel-managed advisory file lock
- **Stale detection:** Not needed. `flock` is released automatically by the OS on process exit or crash. No PID-reuse vulnerability.
- **Scope:** Both MCP write tools (via `workspace_lock()` context manager in `locking.py`) and CLI commands (via `SessionContext._acquire_lock()` in `context.py`) acquire the **same** `.ontos.lock` file using the **same** `flock` mechanism. This eliminates the dual-lock coordination problem identified in UB-3.
- **Platform:** Unix only (macOS + Linux). No Windows users in the current user base.
**Implementation:**

1. Create `ontos/mcp/locking.py`:

```python
import fcntl
from contextlib import contextmanager
from pathlib import Path

@contextmanager
def workspace_lock(workspace_root: Path, timeout: float = 5.0):
    """Acquire exclusive flock on <workspace>/.ontos.lock.

    Raises OntosUserError(E_WORKSPACE_BUSY) if lock cannot be acquired.
    Lock is released automatically when the context manager exits,
    or when the process crashes (OS guarantee).
    """
    lock_path = workspace_root / ".ontos.lock"
    fd = open(lock_path, "w")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fd.close()
        raise OntosUserError(
            "Workspace is locked by another process. "
            "If no other process is running, delete .ontos.lock manually.",
            code="E_WORKSPACE_BUSY",
        )
    try:
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()
```

2. Modify `SessionContext._acquire_lock()` in `ontos/core/context.py` (~line 224):
   - Replace the current PID-based `.ontos/write.lock` mechanism with `flock`-based `.ontos.lock`
   - Use `fcntl.flock(fd, LOCK_EX | LOCK_NB)` — same mechanism as `workspace_lock()` above
   - Remove PID file writing, stale-PID detection, and `.ontos/write.lock` references
   - This is a ~30-line change that replaces existing lock logic, not an addition
   - The lock file path changes from `.ontos/write.lock` to `.ontos.lock` (workspace root)

**Usage pattern:**

```python
with workspace_lock(cache.workspace_root):
    # perform file mutations via SessionContext
    # ...
    cache.force_refresh()
    if portfolio_index:
        portfolio_index.rebuild_workspace(slug, cache.workspace_root)
```

**Recovery path (UB-2):**

Write tools use `SessionContext.commit()` which performs best-effort sequential writes with temp-file cleanup. This is NOT atomic. If the process crashes mid-commit:
- Files already written will have new content
- Files not yet written will have old content
- Temp files (`.tmp` suffix) may remain and should be cleaned up
- The `flock` lock is released automatically by the OS — no stale lock file to worry about

**Recovery procedure:**
1. `git checkout -- .` to revert all uncommitted changes (works because `rename_document()` requires git clean state as precondition)
2. Delete any `.tmp` files in the workspace

This recovery path is documented in `rename_document()` error responses and should be included in MCP server instructions.

**Constraints:**
- Lock file is `.ontos.lock` in workspace root (not in `~/.config/ontos/`). This is per-workspace.
- Lock files are safe to delete manually (the OS releases the advisory lock on process exit regardless).
- Add `.ontos.lock` to the project's `.gitignore` template. Implementation step: modify `.gitignore` or document in release notes.
- The `SessionContext._acquire_lock()` change is part of **Track A scope** — it must ship before Track B so that CLI commands and MCP write tools use the same locking mechanism from day one.

### 4.10 `workspace_id` Parameter Threading [Shared]

**Purpose:** Add optional `workspace_id` parameter to all existing tools.

**Files:**
| Action | Path |
|--------|------|
| MODIFY | `ontos/mcp/server.py` (handler signatures) |
| MODIFY | `ontos/mcp/tools.py` (tool signatures) |

**Implementation:**

1. Add `workspace_id: Optional[str] = None` to every existing tool handler in `server.py` and tool function in `tools.py`.

2. In single-workspace mode: `workspace_id` is accepted but ignored. The parameter exists in the schema so clients that always pass it don't get errors.

3. In portfolio mode: if `workspace_id` is provided and differs from the primary workspace, the tool must load the appropriate workspace's snapshot. This is a future enhancement -- for v4.1, portfolio mode tools that receive a non-primary `workspace_id` should return an `isError: true` with `E_CROSS_WORKSPACE_NOT_SUPPORTED` and direct the user to start a separate `ontos serve` in that workspace. Exception: `project_registry()` and `search()` handle `workspace_id` natively via the portfolio DB; `get_context_bundle()` accepts `workspace_id` and uses it to scope a fresh snapshot in portfolio mode (see §4.7), while in single-workspace mode `workspace_id` is ignored per the §4.10 contract.

4. Update all 8 existing Pydantic schemas to accept `workspace_id` as an optional input field. Since `workspace_id` is an input parameter (not a response field), this doesn't affect output schemas -- it only affects the input schema advertised by FastMCP.

**Constraints:**
- Adding `workspace_id` to existing tool signatures must NOT change their output format. This is a strict backward-compatibility requirement.
- In single-workspace mode, `tools/list` must show `workspace_id` as an optional parameter on each tool.

### 4.11 Pydantic Schema Updates [Shared]

**Purpose:** Add response schemas for all 7 new tools.

**Files:**
| Action | Path |
|--------|------|
| MODIFY | `ontos/mcp/schemas.py` |

**Implementation:**

Add the following models (listed in Sections 4.5-4.8) to `schemas.py`:

**Portfolio tools:**
- `ProjectItem`, `ProjectRegistryResponse`
- `SearchResultItem`, `SearchResponse`
- `BundleDocumentItem`, `StaleDocumentItem`, `GetContextBundleResponse`

**Write tools:**
```python
class ScaffoldDocumentResponse(StrictModel):
    success: Literal[True]
    path: str
    id: str
    type: str
    status: str
    curation_level: str

class RenameDocumentResponse(StrictModel):
    success: Literal[True]
    old_id: str
    new_id: str
    path: str                # file path (unchanged by ID-only rename)
    references_updated: int
    updated_files: List[str]

class LogSessionResponse(StrictModel):
    success: Literal[True]
    path: str
    id: str
    date: str

class PromoteDocumentResponse(StrictModel):
    success: Literal[True]
    document_id: str
    old_level: str
    new_level: str
    # Note: validation failures return isError: true with E_PROMOTION_BLOCKED,
    # not success: false. This model is only used for successful promotions.
```

**Write tool error schema (shared across all 4 write tools):**

```python
class WriteToolError(StrictModel):
    error_code: str
    what: str
    why: str
    fix: str

class WriteToolErrorEnvelope(StrictModel):
    isError: Literal[True]
    error: WriteToolError
    content: List[ToolErrorTextItem]
```

Update `TOOL_SUCCESS_MODELS` dict to include all 7 new tools. Add `WriteToolErrorEnvelope` to `TOOL_ERROR_SCHEMA` mapping.

**Constraints:**
- All new models must extend `StrictModel` (`extra="forbid"`) to match existing pattern.
- All write tool failures use `isError: true` with `WriteToolErrorEnvelope`. No mixed `success: false` / `isError: false` patterns.

### 4.12 Track A -> B Handoff State [Shared]

**Purpose:** Explicitly define what state Track A leaves for Track B to build on (US-13).

Track B (PR #2) assumes Track A (PR #1) has been **merged to main** with the following state:

1. **`portfolio.db` schema exists** with tables: `projects`, `documents`, `edges`, `scan_state`, `fts_content` (standalone mode). Schema version = 1.
2. **`PortfolioIndex` class is merged** at `ontos/mcp/portfolio.py` with methods: `open()`, `close()`, `rebuild_all()`, `rebuild_workspace()`, `is_workspace_stale()`, `get_projects()`, `search_fts()`.
3. **`PortfolioConfig` is merged** at `ontos/mcp/portfolio_config.py` with `load_portfolio_config()`.
4. **`ontos serve --portfolio` flag works** and the server starts with portfolio tools registered.
5. **Tool-availability matrix** from §4.4 is implemented: 8 v4.0 tools + `project_registry` + `search` + `get_context_bundle` registered.
6. **`_invoke_read_tool()` and `_invoke_portfolio_tool()`** wrappers exist in `server.py`.
7. **`workspace_id` optional parameter** is accepted (and ignored) on all v4.0 tools.
8. **Unified `flock`-based locking** is merged: `ontos/mcp/locking.py` provides `workspace_lock()` context manager; `SessionContext._acquire_lock()` in `ontos/core/context.py` uses the same `.ontos.lock` file with `flock`. Both CLI and MCP share the same lock.
9. **`ontos verify --portfolio` flag** is merged: `verify_portfolio()` added to `ontos/commands/verify.py`, `--portfolio` flag added to `_register_verify()` in `ontos/cli.py`, `_cmd_verify` extended with portfolio branch.
10. **All Track A tests pass** (estimated ~84 new tests from §6).

Track B adds:
- `_invoke_write_tool()` wrapper (builds on the invocation pattern from Track A)
- 4 write tools registered via `_register_write_tools()`
- `ontos/mcp/write_tools.py` (new file)
- `--read-only` flag support
- Index invalidation hooks calling `portfolio_index.rebuild_workspace()` after writes
- Write tools acquire the lock via `workspace_lock()` from the Track A-provided `locking.py` — no lock-specific code in Track B beyond using the context manager

### 4.13 `verify --portfolio` Extension [Track A]

**Purpose:** Extend the existing `ontos verify` CLI command with a `--portfolio` flag that reads the portfolio DB and `~/Dev/.dev-hub/registry/projects.json`, diffs them, and reports discrepancies. This is the validation tool for the `.dev-hub` transition — it must ship before the transition begins (planned within 4 weeks).

**Existing behavior (preserved verbatim):** The current `ontos verify` command performs document staleness verification — it checks `describes`/`describes_verified` frontmatter fields and lets users mark stale documents as current. It supports `ontos verify <path>` (single file) and `ontos verify --all` (interactive batch mode). This behavior is unchanged when `--portfolio` is not passed.

**Files:**
| Action | Path |
|--------|------|
| MODIFY | `ontos/commands/verify.py` (add `verify_portfolio()` function) |
| MODIFY | `ontos/cli.py` (add `--portfolio` flag to existing `_register_verify` at line 411; extend `_cmd_verify` at line 1291) |

**Implementation:**

1. Add `--portfolio` flag to the existing `_register_verify()` in `ontos/cli.py:411-434`:

```python
def _register_verify(subparsers, parent):
    """Register verify command."""
    p = subparsers.add_parser(
        "verify",
        help="Verify document describes dates",
        parents=[parent]
    )
    p.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="Specific file to verify"
    )
    p.add_argument(
        "--all", "-a",
        action="store_true",
        help="Verify all stale documents interactively"
    )
    p.add_argument(
        "--date", "-d",
        help="Verification date (YYYY-MM-DD, default: today)"
    )
    p.add_argument(
        "--portfolio",
        action="store_true",
        help="Compare portfolio DB against projects.json and report discrepancies"
    )
    _add_scope_argument(p)
    p.set_defaults(func=_cmd_verify)
```

2. Extend `_cmd_verify()` in `ontos/cli.py:1291-1310` with an early-return branch for `--portfolio`:

```python
def _cmd_verify(args) -> int:
    """Handle verify command."""
    # Portfolio verification mode — independent of document staleness verification
    if getattr(args, "portfolio", False):
        from ontos.commands.verify import verify_portfolio
        from ontos.mcp.portfolio_config import load_portfolio_config
        config = load_portfolio_config()
        exit_code = verify_portfolio(
            portfolio_db_path=Path.home() / ".config" / "ontos" / "portfolio.db",
            registry_path=Path(config.registry_path).expanduser(),
            json_output=args.json,
        )
        return exit_code

    # Existing document staleness verification (unchanged)
    from ontos.commands.verify import VerifyOptions, _run_verify_command
    options = VerifyOptions(
        path=args.path,
        all=args.all,
        date=args.date,
        quiet=args.quiet or args.json,
        json_output=args.json,
        scope=getattr(args, "scope", None),
    )
    exit_code, message = _run_verify_command(options)
    if args.json:
        _emit_handler_result_json(
            command="verify",
            exit_code=exit_code,
            message=message,
        )
    return exit_code
```

3. Add `verify_portfolio()` function to `ontos/commands/verify.py`:

```python
def verify_portfolio(
    *,
    portfolio_db_path: Path,
    registry_path: Path,
    json_output: bool = False,
) -> int:
    """Compare portfolio DB against projects.json and report discrepancies.

    Returns exit code: 0 if clean, 1 if discrepancies found, 2 on error.
    """
    ...
```

4. Algorithm:
   - **Load portfolio DB:** Open `~/.config/ontos/portfolio.db`, query `SELECT slug, path, status, doc_count, has_ontos FROM projects`. Build a dict keyed by `slug`.
   - **Load projects.json:** Read `~/Dev/.dev-hub/registry/projects.json` (path from `PortfolioConfig.registry_path`). Parse JSON. Build a dict keyed by a slugified version of each project's directory name (same `slugify()` from §4.3).
   - **Compute symmetric difference:**
     - `missing_in_db`: projects in `projects.json` but not in portfolio DB
     - `missing_in_json`: projects in portfolio DB but not in `projects.json`
     - `field_mismatches`: projects in both but with differing field values (compare `path`, `status`, `has_ontos`)
   - **Format output:**
     - **Human-readable (default):** Print a summary line, then list each discrepancy category with project slugs and details. Use colored output if stdout is a terminal.
     - **JSON (`--json` flag):** Output a single JSON object (uses the existing `--json` flag inherited from the global parent parser):
       ```json
       {
         "clean": false,
         "missing_in_db": ["project-a", "project-b"],
         "missing_in_json": ["project-c"],
         "field_mismatches": [
           {"slug": "project-d", "field": "status", "db_value": "documented", "json_value": "partial"}
         ],
         "summary": "3 discrepancies found"
       }
       ```
   - **Exit codes:**
     - `0`: No discrepancies (clean)
     - `1`: Discrepancies found
     - `2`: Error (DB not found, `projects.json` not found, parse error)

5. Error handling:
   - If portfolio DB does not exist: print "Portfolio DB not found. Run `ontos serve --portfolio` first." and exit 2.
   - If `projects.json` does not exist: print "Registry file not found at {path}. Check portfolio.toml registry_path." and exit 2.
   - If either source is malformed: print error details and exit 2.

**Constraints:**
- **Read-only on both sources.** `verify --portfolio` never modifies the portfolio DB or `projects.json`.
- **Existing behavior preserved.** When `--portfolio` is not passed, the command behaves identically to v4.0: document staleness verification via `_run_verify_command()`.
- This is a CLI-only command — it is NOT exposed as an MCP tool.
- The `--json` flag is already available on the existing `verify` parser via the global parent parser — no new flag needed for JSON output.

---

## 5. Open Questions

### OQ-1: Portfolio tool availability in single-workspace mode — RESOLVED

**Question:** Should `get_context_bundle()` be available in single-workspace mode (without `--portfolio`)?

**Resolution: (B) Available in both modes.** Cross-platform consensus from Phase B review. Claude Code traced the crash path (UB-7) and demonstrated it's a localized logic fix. The tool provides genuine value in single-workspace mode -- token budgeting, structured JSON output, staleness detection -- that `context_map` does not offer. The UB-7 guard (§4.7) ensures `workspace_id` is silently ignored in single-ws mode per §4.10's contract. `project_registry()` and `search()` remain portfolio-only since they require cross-project data. See tool-availability matrix in §4.4. **Status: RESOLVED (v1.1).**

### OQ-2: Rename tool -- file path rename vs. ID-only rename — RESOLVED

**Question:** When renaming a document ID, should the tool also rename the file on disk (e.g., `old_id.md` -> `new_id.md`)?

**Resolution: (A) ID-only rename.** Cross-platform consensus from Phase B review. Decisive codebase evidence: the existing CLI rename command (`ontos/commands/rename.py`, 1,362 lines) contains zero calls to `os.rename()`, `Path.rename()`, or `SessionContext.buffer_move()`. The v1.0 spec's claim that "the existing `ontos rename` CLI command already handles file renaming" was factually incorrect. Implementing file rename would be entirely new functionality requiring path construction rules, case-sensitivity handling (macOS APFS), date-prefix conventions for logs, and git history considerations -- unacknowledged scope creep pushing Track B risk toward HIGH. The `RenameDocumentResponse` schema has been updated to include `path` (unchanged file path) instead of `old_path`/`new_path`. **Status: RESOLVED (v1.1).**

### OQ-3: FTS5 content sync strategy

**Question:** When rows in `documents` change, the standalone FTS5 table must be explicitly updated. Should we use triggers or manual sync?

**Options:**
- (A) SQLite triggers (`AFTER INSERT/UPDATE/DELETE ON documents`)
- (B) Manual sync in `rebuild_workspace()` -- delete old FTS rows, insert new ones

**Recommendation:** **(B) Manual sync.** We always rebuild per-workspace atomically (`BEGIN IMMEDIATE`, delete all, reinsert all). Triggers add complexity for incremental updates we don't do. The rebuild-all-rows-for-workspace approach is simpler and matches our "rebuildable cache" philosophy. With standalone FTS5 mode, sync is straightforward: delete FTS5 rows for the workspace, reinsert from `documents`. **Status: RESOLVED -- proceeding with (B).**

---

## 6. Test Strategy

### Baseline

**Current test count:** 941 tests collected (13 MCP-related tests error during collection due to optional `mcp` dependency). Located in `tests/` (main suite) and `tests/mcp/` (MCP-specific).

**Existing MCP test files (13 files in `tests/mcp/`):**
- `test_cache.py`, `test_context_map.py`, `test_error_paths.py`, `test_export_graph.py`, `test_get_document.py`, `test_health.py`, `test_list_documents.py`, `test_parity.py`, `test_query.py`, `test_refresh.py`, `test_schemas.py`, `test_server_integration.py`, `test_workspace_overview.py`

**Test helpers** (in `tests/mcp/__init__.py`): `create_workspace(tmp_path)`, `build_cache(root)`, `list_tools(server)`, `call_payload(result)`, `parse_json_text(result)`.

### Track A Tests

**Unit tests** (in `tests/mcp/`):

| File | Tests | What it covers |
|------|-------|---------------|
| `test_portfolio.py` | ~17 | `PortfolioIndex`: open/close, schema creation, `rebuild_all`, `rebuild_workspace`, `is_workspace_stale`, `get_projects`, `search_fts`, PRAGMA block, `user_version` check, corrupt DB rebuild, FTS5 ranking order, FTS5 standalone row count equals `documents` row count after rebuild, FTS5 snippet returns correct column data (not cross-column) |
| `test_portfolio_config.py` | ~5 | `load_portfolio_config`: default values, custom config, missing file, invalid TOML |
| `test_scanner.py` | ~8 | `discover_projects`: registry + filesystem discovery, slugification, status classification, exclude patterns |
| `test_project_registry.py` | ~5 | `project_registry()` tool: output format, schema validation, empty portfolio |
| `test_search.py` | ~10 | `search()` tool: basic query, workspace filter, pagination, empty results, invalid workspace, FTS5 query syntax errors, snippet generation, BM25 ordering |
| `test_context_bundle.py` | ~12 | `get_context_bundle()` tool: kernel priority, in-degree ranking, token budget respect, lost-in-the-middle ordering, log window, undocumented workspace error, budget bounds validation, stale document detection |
| `test_bundler.py` | ~8 | `build_context_bundle()`: scoring, greedy packing, edge cases (empty workspace, all-kernel workspace, budget smaller than one kernel doc) |
| `test_locking.py` | ~3 | `workspace_lock()`: flock acquisition succeeds, concurrent acquisition raises `E_WORKSPACE_BUSY`, lock released on context manager exit (Track A substrate) |
| `test_verify.py` | ~6 | `verify_portfolio()`: clean case (exit 0), missing-in-db (exit 1), missing-in-json (exit 1), field mismatch (exit 1), missing DB file (exit 2), missing projects.json (exit 2), JSON output format |

**Integration tests:**

| File | Tests | What it covers |
|------|-------|---------------|
| `test_portfolio_integration.py` | ~5 | End-to-end: create multi-workspace fixture, build portfolio, call `project_registry` -> `search` -> `get_context_bundle` in sequence. Verify cross-tool consistency. |
| `test_server_portfolio_mode.py` | ~5 | `create_server()` with `portfolio_index` parameter: verify all 11 tools (8 existing + 3 new) appear in `tools/list`. Verify `workspace_id` parameter appears on all tools. |

**Estimated Track A test additions:** ~84 new tests (unit: ~74, integration: ~10; includes lock substrate: ~3, verify: ~6, FTS5 standalone tests: +2).

### Track B Tests

**Unit tests:**

| File | Tests | What it covers |
|------|-------|---------------|
| `test_scaffold_document.py` | ~8 | Input validation (type, id format, duplicate, invalid depends_on), file creation, frontmatter content, path conventions |
| `test_rename_document.py` | ~10 | ID validation, reference updates (frontmatter + body), ID-only rename with best-effort sequential commit, git clean-state precondition, non-existent doc error |
| `test_log_session.py` | ~6 | Summary validation, event_type aliases, branch resolution, file creation, frontmatter content |
| `test_promote_document.py` | ~8 | Level validation, L0->L1, L0->L2, L1->L2, validation failure (missing fields), already-at-target error |
| `test_locking_write_tools.py` | ~4 | Write tool lock integration: write tool acquires lock via `workspace_lock()`, concurrent write tool call returns `E_WORKSPACE_BUSY`, lock released after write+refresh cycle, `SessionContext._acquire_lock()` uses same `.ontos.lock` as MCP |
| `test_write_tool_errors.py` | ~5 | All write tools return `isError: true` (not exceptions) for every error path. Verify `CallToolResult.isError` is True and structured content contains (what, why, fix). |

**Integration tests:**

| File | Tests | What it covers |
|------|-------|---------------|
| `test_write_tools_integration.py` | ~6 | Scaffold -> list_documents (appears), scaffold -> rename -> list_documents (updated), scaffold -> promote -> get_document (level changed), log_session -> list_documents (appears) |
| `test_read_only_mode.py` | ~3 | `--read-only` flag: verify write tools absent from `tools/list`, read tools still present, attempt to call write tool returns error |
| `test_write_invalidation.py` | ~4 | After write tool in portfolio mode: verify `cache.snapshot` updated, verify `portfolio.db` rows updated, verify `search()` finds newly created document |

**Estimated Track B test additions:** ~56 new tests.

### Shared Tests

| File | Tests | What it covers |
|------|-------|---------------|
| Modify `test_schemas.py` | +7 | Schema validation for all 7 new tool response types |
| Modify `test_server_integration.py` | +3 | Backward compat: single-workspace mode produces identical `tools/list` to v4.0 |

**Total estimated new tests:** ~150 (Track A: ~84, Track B: ~56, Shared: ~10).

### Manual Testing Steps

**Track A:**
1. Run `ontos serve --portfolio` from a project with `.ontos.toml`
2. Call `project_registry()` -- verify all 23 projects listed with correct status
3. Call `search("simhash")` -- verify results with snippets and scores
4. Call `search("simhash", workspace_id="canary-work")` -- verify filtered results
5. Call `search("xyznonexistent")` -- verify empty results
6. Call `get_context_bundle(workspace_id="canary-work")` -- verify bundle within 8192 token budget
7. Call `get_context_bundle(workspace_id="undocumented-project")` -- verify error directing to `ontos init`
8. Delete `~/.config/ontos/portfolio.db`, restart `ontos serve --portfolio` -- verify DB rebuilt
9. Run `ontos verify --portfolio` -- verify clean output (exit 0) when DB and projects.json are in sync
10. Run `ontos verify --portfolio --json` -- verify JSON output format
11. Manually add a dummy entry to projects.json, re-run verify -- verify discrepancy reported (exit 1)

**Track B:**
1. Call `scaffold_document(type="atom", id="test_spec", title="Test Spec")` -- verify file created
2. Call `list_documents()` -- verify `test_spec` appears
3. Call `rename_document(document_id="test_spec", new_id="renamed_spec")` -- verify rename + reference updates
4. Call `log_session(summary="Testing write tools")` -- verify log created
5. Call `promote_document(document_id="renamed_spec", target_level="L2")` -- verify validation failure (missing L2 fields)
6. Start server with `ontos serve --read-only` -- verify write tools absent from `tools/list`

---

## 7. Migration / Compatibility

### Backward Compatibility Guarantees

| Guarantee | Verification |
|-----------|-------------|
| CLI fully preserved | Existing CLI test suite passes unchanged |
| `pip install ontos` (no extras) works on Python 3.9+ | No new base dependencies added |
| All 8 v4.0 MCP tools work identically | Existing `tests/mcp/` tests pass unchanged |
| Existing MCP client configs require no changes | `ontos serve` (no flags) behaves identically to v4.0 |
| `.ontos.toml` backward compatible | No new required sections |
| Per-project document storage unchanged | Markdown files with YAML frontmatter |

### What Changes

| Change | Impact | Mitigation |
|--------|--------|-----------|
| New `workspace_id` optional parameter on all tools | Clients that inspect tool schemas may notice new parameter | Parameter is optional with `None` default; ignored in single-workspace mode |
| MCP SDK pin: `mcp>=1.2` -> `mcp>=1.27.0,<2.0` | Users with `mcp<1.27.0` will see pip resolution error on upgrade | Document in release notes; `pip install --upgrade 'ontos[mcp]'` resolves it |
| Python MCP extra: 3.9+ -> 3.10+ | Users on Python 3.9 can't install `ontos[mcp]` | Base package unchanged. Document in release notes. Add `python_requires=">=3.10"` to the `[mcp]` extra metadata. |
| New files: `portfolio.db`, `portfolio.toml`, `.ontos.lock` | Gitignore, cleanup | Add `.ontos.lock` to `.gitignore` template. `portfolio.db` and `portfolio.toml` are in `~/.config/ontos/` (outside repo). |

### Rollback Plan

Downgrade: `pip install ontos==4.0.0`. The portfolio database is ignored by v4.0. Write tools are not present. No data migration needed. Lock files can be safely deleted.

### pyproject.toml Changes

```toml
# Current:
[project.optional-dependencies]
mcp = [
    "mcp>=1.2",
    "pydantic>=2.0",
]

# v4.1:
[project.optional-dependencies]
mcp = [
    "mcp>=1.27.0,<2.0",
    "pydantic>=2.0",
]
```

Note: `pyproject.toml` does not support per-extra `python_requires`. The MCP SDK itself declares `python_requires>=3.10`, so pip will fail to resolve the dependency on Python 3.9 automatically. Document this in release notes.

---

## 8. Risk Assessment

### Track A: MEDIUM

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| SQLite FTS5 not available on user's Python build | Low | High (feature broken) | FTS5 is included in all standard Python builds since 3.7. Test for availability at import time and fail fast with clear error message. |
| Portfolio DB corruption | Low | Low (rebuildable cache) | Delete and rebuild from scratch. Startup check validates `user_version`. |
| FTS5 query injection | Medium | Medium (error, not security) | `_sanitize_fts_query()` escapes user input. Catch `OperationalError` and return `isError: true`. |
| Cross-project snapshot loading is slow | Low | Medium (poor UX) | 400 docs across 23 projects at ~2KB avg = ~800KB. SQLite handles this in <1s. Benchmark during implementation. |
| `workspace_id` parameter breaks existing client integrations | Low | High | Parameter is optional with `None` default. Existing calls without it are unchanged. Integration tests verify this. |

**Would I bet my weekend?** Not quite -- the SQLite layer is new and the FTS5 integration has edge cases (query syntax, content sync). But the blast radius is bounded: the DB is rebuildable and the tools are read-only. The `verify` subcommand and `flock` lock substrate added to Track A scope are both low-risk (read-only verification, well-understood OS primitive). Track A risk remains **MEDIUM**.

### Track B: MEDIUM-HIGH

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| `rename_document()` corrupts references | Medium | High (data loss) | Comprehensive test coverage for multi-file edits. Leverage existing rename logic from `ontos/commands/rename.py` which is battle-tested. Agent can `git checkout` to recover. |
| File lock races on NFS/network drives | Low | Medium | Not a concern for local `~/Dev/` paths. Document that network drives are unsupported. |
| Write tool leaves workspace in inconsistent state on crash | Medium | Medium | `SessionContext` provides best-effort sequential commit (not atomic). Portfolio DB is rebuildable. Locks are released by the kernel on process exit (flock). Recovery: `git checkout -- .`. |
| Index invalidation after write tool is not atomic with the write | Medium | Medium | Write tool holds workspace lock for the entire duration including `force_refresh()` and `rebuild_workspace()`. No gap for inconsistency. |
| Write tools interact poorly with concurrent `ontos` CLI usage | Low | Medium | CLI `SessionContext._acquire_lock()` and MCP `workspace_lock()` both use unified `flock` on `.ontos.lock`. Concurrent CLI + MCP writes are safely serialized. |

**Would I bet my weekend?** No. `rename_document()` updating references across multiple files via best-effort sequential commit is inherently risky. The existing rename CLI command mitigates some of this, but the MCP wrapper adds a new execution path. Git clean-state precondition and recovery via `git checkout -- .` are the primary safety nets.

### Shared: LOW

Registration plumbing, schema additions, and config changes are mechanical. Risk is limited to missed backward-compatibility regressions, mitigated by existing test suite.

---

## 9. Exclusion List

### What This Spec Does NOT Do

| Exclusion | Rationale |
|-----------|-----------|
| No HTTP/Streamable HTTP transport | Deferred to v4.2 per proposal re-scope |
| No daemon mode or background indexer | Stdio sessions are short-lived; startup rebuild <1s |
| No bearer token, audit logging, CORS | Coupled to HTTP transport |
| No calibrated 5-signal bundle scoring | Needs v4.1 usage data to calibrate |
| No Personalized PageRank | Part of 5-signal scoring, deferred |
| No MCP Resources or Prompts primitives | No consumer demand |
| No cross-workspace `depends_on` validation | Schema supports it; UI/validation deferred |
| No `starlette`, `uvicorn`, `cachetools` dependencies | All downstream of HTTP |
| No `tiktoken` dependency | Character heuristic is sufficient for v4.1 |
| No modifications to existing 8 v4.0 tool implementations | Only add optional `workspace_id` parameter |
| No modifications to CLI commands beyond `serve` flag additions and `verify --portfolio` extension | CLI is fully preserved; `verify` gains an additive `--portfolio` flag; existing `verify` behavior is unchanged |
| No modifications to `.ontos.toml` schema | Per-project config unchanged |
| No modifications to per-project document storage format | Markdown + YAML frontmatter unchanged |

### Files NOT to Touch

| Path | Reason |
|------|--------|
| `ontos/commands/map.py` | Context map generation is not part of v4.1 |
| `ontos/commands/doctor.py` | Health check is not part of v4.1 |
| `ontos/commands/hook.py` | Git hooks are not part of v4.1 |
| `ontos/commands/init.py` | Project initialization is not part of v4.1 |
| `ontos/core/graph.py` | Graph algorithms unchanged |
| `ontos/core/validation.py` | Validation logic unchanged |
| `ontos/core/frontmatter.py` | Frontmatter parsing unchanged |
| `ontos/core/snapshot.py` | Snapshot data model unchanged |
| `ontos/io/snapshot.py` | Snapshot I/O unchanged |
| `ontos/ui/` | UI layer unchanged (MCP tools don't use UI) |
| `.ontos-internal/` | Internal strategy docs, not code |

### Approaches NOT to Take

| Anti-pattern | Why not |
|-------------|---------|
| Per-project tool namespacing (e.g., `canary_work_search`) | LLM tool selection degrades above ~20 tools. Research consensus item #9. |
| Connection pooling for SQLite | Connections take microseconds to open. Pooling adds complexity without benefit. Research consensus. |
| `PRAGMA synchronous = FULL` | `NORMAL` is corruption-safe in WAL mode and much faster. Research consensus. |
| Deferred transactions for writes | Must use `BEGIN IMMEDIATE`. Deferred read-to-write upgrade causes `SQLITE_BUSY`. Research consensus. |
| Throwing exceptions from write tool handlers | Must return `isError: true` with structured error. Exceptions become JSON-RPC -32xxx errors that never reach the LLM. Research consensus area 2. |
| Preview+confirm pattern for write tools | Proposal Section D5 decided on immediate writes with detailed response. The `--read-only` flag is the safety boundary. |
| Background indexer thread in stdio mode | Stdio sessions are interactive and short-lived. Startup rebuild is sufficient. |

---

## 10. Diagrams

### 10.1 Architecture / Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MCP Client (Claude Code / Cursor)                │
│                              stdio transport                            │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ JSON-RPC over stdin/stdout
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         OntosFastMCP Server                             │
│                        (ontos/mcp/server.py)                            │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Tool Registration Layer                       │   │
│  │  ┌─────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │   │
│  │  │ Read Tools   │ │ Portfolio  │ │ Write Tools│ │ Shared     │  │   │
│  │  │ (v4.0, 8ea) │ │ Tools (3)  │ │ (4)        │ │ Plumbing   │  │   │
│  │  │             │ │ [Track A]  │ │ [Track B]  │ │            │  │   │
│  │  │ workspace_  │ │            │ │            │ │ _invoke_   │  │   │
│  │  │  overview   │ │ project_   │ │ scaffold_  │ │  tool()    │  │   │
│  │  │ context_map │ │  registry  │ │  document  │ │            │  │   │
│  │  │ get_document│ │ search     │ │ rename_    │ │ _log_usage │  │   │
│  │  │ list_docs   │ │ get_context│ │  document  │ │            │  │   │
│  │  │ export_graph│ │  _bundle   │ │ log_session│ │ schemas.py │  │   │
│  │  │ query       │ │            │ │ promote_   │ │            │  │   │
│  │  │ health      │ │            │ │  document  │ │            │  │   │
│  │  │ refresh     │ │            │ │            │ │            │  │   │
│  │  └──────┬──────┘ └─────┬──────┘ └─────┬──────┘ └────────────┘  │   │
│  └─────────┼──────────────┼───────────────┼────────────────────────┘   │
│            │              │               │                             │
│            ▼              ▼               ▼                             │
│  ┌─────────────────┐ ┌────────────┐ ┌────────────────────────────┐     │
│  │  SnapshotCache   │ │ Portfolio  │ │  Workspace Lock            │     │
│  │  (cache.py)      │ │ Index      │ │  (locking.py) [Shared/A]   │     │
│  │  [v4.0, unchanged│ │(portfolio. │ │                            │     │
│  │   except refresh  │ │ py)        │ │  .ontos.lock per workspace│     │
│  │   hook for writes]│ │ [Track A]  │ │  flock-based (kernel-mgd)  │     │
│  └────────┬─────────┘ └─────┬──────┘ └───────────┬────────────────┘    │
│           │                  │                     │                     │
└───────────┼──────────────────┼─────────────────────┼─────────────────────┘
            │                  │                     │
            ▼                  ▼                     ▼
┌───────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐
│   Filesystem       │  │  portfolio.db   │  │  Filesystem (WRITE)      │
│   (READ)           │  │  (SQLite+FTS5)  │  │  ════════════════════    │
│                    │  │  [Track A]      │  │  TRUST BOUNDARY          │
│  ~/Dev/*/docs/*.md │  │                 │  │                          │
│  .ontos.toml       │  │  ~/.config/     │  │  Creates/modifies .md    │
│  README.md         │  │   ontos/        │  │  files in workspace      │
│                    │  │   portfolio.db  │  │  docs/ directory         │
│  Per-project       │  │   portfolio.toml│  │                          │
│  document storage  │  │   usage.jsonl   │  │  Rename updates refs     │
│  (authoritative)   │  │                 │  │  across multiple files   │
└───────────────────┘  └─────────────────┘  └──────────────────────────┘
                                                  ▲
                                                  │
                                            ══════╧══════
                                            TRUST BOUNDARY
                                            Write tools mutate
                                            user's filesystem.
                                            --read-only flag
                                            removes this surface.
```

**Legend:**
- Solid boxes = components
- `[Track A]` / `[Track B]` = implementation track labels
- `═══` double lines = trust boundary (filesystem write surface)
- Arrows = data flow direction
- `v4.0, unchanged` = existing component preserved from v4.0

### 10.2 Sequence Diagram: `get_context_bundle()` (Read Path)

```
Client              Server              SnapshotCache/         Bundler            portfolio.db
  │                   │                 PortfolioIndex            │                    │
  │  get_context_     │                      │                    │                    │
  │  bundle(ws_id,    │                      │                    │                    │
  │  budget=8192)     │                      │                    │                    │
  │──────────────────>│                      │                    │                    │
  │                   │                      │                    │                    │
  │                   │  validate ws_id      │                    │                    │
  │                   │─────────────────────>│                    │                    │
  │                   │                      │  get_projects()    │                    │
  │                   │                      │───────────────────────────────────────>│
  │                   │                      │  projects list     │                    │
  │                   │                      │<───────────────────────────────────────│
  │                   │                      │                    │                    │
  │                   │  [ws not found]      │                    │                    │
  │                   │  isError: true       │                    │                    │
  │                   │  E_UNKNOWN_WORKSPACE │                    │                    │
  │<─ ─ ─ ─ ─ ─ ─ ─ ─│  (with valid slugs) │                    │                    │
  │                   │                      │                    │                    │
  │                   │  [ws undocumented]   │                    │                    │
  │                   │  isError: true       │                    │                    │
  │<─ ─ ─ ─ ─ ─ ─ ─ ─│  E_UNDOCUMENTED     │                    │                    │
  │                   │                      │                    │                    │
  │                   │  [ws valid]          │                    │                    │
  │                   │  create_snapshot()   │                    │                    │
  │                   │─────────────────────>│                    │                    │
  │                   │  snapshot            │                    │                    │
  │                   │<─────────────────────│                    │                    │
  │                   │                      │                    │                    │
  │                   │  build_context_bundle(snapshot, budget)   │                    │
  │                   │─────────────────────────────────────────>│                    │
  │                   │                      │                    │                    │
  │                   │                      │    1. Classify docs│                    │
  │                   │                      │       (kernel,     │                    │
  │                   │                      │        in-degree,  │                    │
  │                   │                      │        recent logs)│                    │
  │                   │                      │                    │                    │
  │                   │                      │    2. Score & rank │                    │
  │                   │                      │                    │                    │
  │                   │                      │    3. Greedy pack  │                    │
  │                   │                      │       (kernel first│                    │
  │                   │                      │        then by     │                    │
  │                   │                      │        score desc) │                    │
  │                   │                      │                    │                    │
  │                   │                      │    4. Lost-in-the- │                    │
  │                   │                      │       middle order │                    │
  │                   │                      │                    │                    │
  │                   │                      │    5. Render text  │                    │
  │                   │                      │                    │                    │
  │                   │                      │    6. Detect stale │                    │
  │                   │                      │                    │                    │
  │                   │  bundle result       │                    │                    │
  │                   │<─────────────────────────────────────────│                    │
  │                   │                      │                    │                    │
  │                   │  validate_success_   │                    │                    │
  │                   │  payload()           │                    │                    │
  │                   │                      │                    │                    │
  │  CallToolResult   │                      │                    │                    │
  │  (structuredContent│                     │                    │                    │
  │   + text fallback) │                     │                    │                    │
  │<──────────────────│                      │                    │                    │
```

**Error paths shown:** Unknown workspace (returns `isError: true` with valid slugs list), undocumented workspace (returns `isError: true` directing to `ontos init`). Normal path: validate -> snapshot -> bundle -> return.

### 10.3 State Diagram: Write Tool Lifecycle (Write Path)

```
                         ┌─────────┐
                         │  IDLE   │
                         └────┬────┘
                              │ tool call received
                              ▼
                     ┌────────────────┐
                     │   VALIDATING   │
                     │                │
                     │ - Check params │
                     │ - Check doc    │
                     │   exists/unique│
                     │ - Check type   │
                     └───┬────────┬───┘
                         │        │
              validation │        │ validation
              passes     │        │ fails
                         │        │
                         │        ▼
                         │  ┌───────────────┐
                         │  │ ERROR RETURN  │
                         │  │               │
                         │  │ isError: true │
                         │  │ {what, why,   │
                         │  │  how to fix}  │──────────> back to IDLE
                         │  └───────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ LOCK ACQUIRING  │
                │                 │
                │ workspace_lock()│
                └───┬─────────┬───┘
                    │         │
             acquired│        │ timeout
                    │         │
                    │         ▼
                    │  ┌───────────────┐
                    │  │ ERROR RETURN  │
                    │  │               │
                    │  │ isError: true │
                    │  │ E_WORKSPACE_  │
                    │  │ BUSY          │──────────> back to IDLE
                    │  └───────────────┘
                    │
                    ▼
           ┌────────────────┐
           │   EXECUTING    │
           │                │
           │ - Write files  │
           │ - SessionContext│
           │   .commit()    │
           │ (best-effort   │
           │  sequential)   │
           └───┬────────┬───┘
               │        │
        success│        │ OS error /
               │        │ write failure
               │        │
               │        ▼
               │  ┌───────────────┐
               │  │ ERROR RETURN  │
               │  │               │
               │  │ isError: true │
               │  │ E_WRITE_FAILED│
               │  │ (lock released│
               │  │  in finally)  │──────────> back to IDLE
               │  └───────────────┘
               │
               ▼
      ┌─────────────────┐
      │   REFRESHING    │
      │                 │
      │ cache.force_    │
      │  refresh()      │
      │                 │
      │ portfolio_index │
      │  .rebuild_      │
      │  workspace()    │
      │ (if portfolio   │
      │  mode)          │
      └───────┬─────────┘
              │
              ▼
      ┌─────────────────┐
      │  LOCK RELEASED  │
      │                 │
      │ flock released  │
      │ (OS-managed)    │
      └───────┬─────────┘
              │
              ▼
      ┌─────────────────┐
      │ SUCCESS RETURN  │
      │                 │
      │ {success: true, │
      │  path, details} │──────────> back to IDLE
      └─────────────────┘
```

**Key transitions:**
- Every error state returns `isError: true` to the MCP client (not exceptions)
- Lock is ALWAYS released in the `finally` block (context manager guarantee)
- Cache refresh and portfolio index update happen INSIDE the lock hold
- The lock ensures that `list_documents()` called immediately after a write tool returns will see the updated state

---

## Self-Review Checklist (v1.1 final, post-B.4 cleanup)

- [x] Every Section 8.3 section present (1-Overview through 10-Diagrams, plus 4.12 Track A->B Handoff, 4.13 verify)
- [x] Every Technical Design block labeled `[Track A]`, `[Track B]`, or `[Shared]`
- [x] Three diagrams present -- exceeds the 2-diagram gate
- [x] File paths verified against codebase (v1.1: `_prepare_plan()` at `rename.py:278`, `_acquire_lock()` at `context.py:224`, zero `os.rename`/`buffer_move` in rename.py, existing `verify.py` at `ontos/commands/verify.py`, existing `_register_verify` at `cli.py:411`, existing `_cmd_verify` at `cli.py:1291` -- all confirmed)
- [x] Function signatures checked against existing patterns
- [x] OQ-1 RESOLVED to (B), OQ-2 RESOLVED to (A), OQ-3 RESOLVED (v1.0)
- [x] Architecture constraints not violated
- [x] Risk assessment confirmed: A=MEDIUM (with verify + lock substrate), B=MEDIUM-HIGH, Shared=LOW
- [x] Exclusion List updated: `verify` removed (now in scope), no stale entries
- [x] Test count baseline: 941 tests; estimated new: ~150
- [x] Research consensus items implemented concretely
- [x] All 3 `[PENDING C.0 RESOLUTION]` placeholders RESOLVED and removed
- [x] FTS5 mode: Standalone. No "external content" or "ordinal" references remain (in active design)
- [x] Lock architecture: Unified flock. No dual-lock or PID-based stale detection references remain (except in migration instructions describing what to change FROM)
- [x] `verify --portfolio`: §4.13 is MODIFY of existing files (not CREATE), uses `_cmd_verify`, preserves existing behavior
- [x] No unverified factual claims about codebase behavior
- [x] Tool-availability matrix (§4.4) is single authoritative MCP surface contract
- [x] §4.4/§4.7/§4.10 prose consistent with matrix and `get_context_bundle()` implementation
- [x] Typed write-error schema defined (§4.8)
- [x] Track A->B handoff state documented (§4.12), includes lock substrate and verify
- [x] Atomicity claims downgraded everywhere; no stale "atomic" or "file rename" language in §1/§6/§8
- [x] All write tools use uniform `isError: true` for failures
- [x] Registry path normalized to `~/Dev/.dev-hub/registry/projects.json` throughout
- [x] Spec version header: v1.1 final, dated 2026-04-11
