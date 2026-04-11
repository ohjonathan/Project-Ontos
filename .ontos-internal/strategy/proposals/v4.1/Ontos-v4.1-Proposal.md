---
id: ontos_v41_proposal
type: strategy
status: draft
depends_on: [ontos_manual]
---

# Ontos v4.1 Proposal: Portfolio Authority

**Date:** 2026-04-10
**Revised:** 2026-04-11 (v3 -- re-scoped per review verdict: stdio-only, defer HTTP/security to v4.2, simplify bundle algorithm, add missing sections)
**Author:** Claude (synthesized from v4.0 deferred scope, consumer brief, and codebase analysis)
**Status:** PROPOSAL -- revised per review, requires CA decision to proceed
**Audience:** Johnny (project owner), LLMs reviewing for correctness and gaps

**Research:** See [ontos-v4.1-research-consolidated.md](ontos-v4.1-research-consolidated.md) -- consolidated findings from 3 parallel deep-research runs (Models A, G, O) validating design decisions against MCP ecosystem best practices.

**Prior revisions:** v2: applied 8 research corrections (Streamable HTTP, ASGI, PRAGMAs, FTS5, PageRank, DNS rebinding). v1: initial draft with full scope including HTTP transport.

**Review:** PR #84 review verdict (2026-04-11) recommended re-scoping. R1 (adversarial/product) flagged premature HTTP scope and unvalidated demand. R2 (alignment/technical) confirmed architecture is sound but identified 4 specification gaps. Author accepted the split: v4.1.0 = stdio-only with write tools + portfolio; v4.2 = HTTP transport when JohnnyOS validates the demand.

---

## 1. What Is This

Ontos v4.1 is the **portfolio authority** release. It extends the v4.0 single-project MCP bridge into a multi-workspace server that indexes all 23 projects in `~/Dev/`, provides cross-project search, generates token-budgeted context bundles, and exposes write-capable MCP tools -- all over **stdio transport**.

Concretely, v4.1 adds:

- **Portfolio index** -- a SQLite database (`~/.config/ontos/portfolio.db`) spanning all workspaces, with FTS5 full-text search
- **3 new portfolio tools** -- `project_registry()`, `search()`, `get_context_bundle()`
- **4 new write tools** -- `scaffold_document()`, `rename_document()`, `log_session()`, `promote_document()`
- **Undocumented project handling** -- thin metadata entries for the 13 projects without Ontos coverage
- **Multi-workspace identity** -- optional `workspace_id` parameter on all tools

What v4.1 **does not** add (deferred to v4.2, see Section 13):

- HTTP/Streamable HTTP transport
- Security model (bearer token, audit logging, rate limiting)
- Daemon mode and background indexer
- Calibrated 5-signal context bundle scoring

The CLI remains fully functional. All 8 existing v4.0 tools remain unchanged. Stdio transport is preserved. MCP is still additive.

---

## 2. Why Now

### Write Tools Have Immediate Demand

Claude Code and Cursor users currently leave the MCP session to run CLI commands for document creation (`ontos scaffold`), renaming (`ontos rename`), and logging (`ontos log`). These are the most common MCP-adjacent operations. Wrapping them as MCP tools eliminates context switching for the primary consumer that exists today.

### The Single-Workspace Ceiling Is Real

Claude Code and Cursor users currently spawn one `ontos serve` process per project. When working across projects (e.g., "what does canary.work depend on that finance-engine also uses?"), the agent has no cross-project query path. It falls back to reading `~/.dev-hub/registry/projects.json` or asking the user. v4.1 removes this ceiling by loading the portfolio index at stdio server startup.

### The MCP Ecosystem Supports This Scope

The Python MCP SDK (`mcp >= 1.27.0`) is stable for stdio transport. Write tool patterns are well-established in production MCP servers (GitHub MCP, filesystem server, Notion). SQLite FTS5 is stdlib and massively over-provisioned for 400 documents. No new architectural risk is introduced beyond what v4.0 already established.

---

## 3. Current State

### What v4.0.0 Ships

Ontos v4.0.0 (tagged, released on PyPI) is a thin MCP bridge wrapping single-project capabilities:

| Capability | Implementation |
|-----------|----------------|
| 8 MCP tools | `workspace_overview`, `context_map`, `get_document`, `list_documents`, `export_graph`, `query`, `health`, `refresh` |
| Stdio transport | Single transport, launched via `ontos serve` |
| In-memory cache | `SnapshotCache` with file-mtime fingerprint invalidation |
| Single workspace | One `ontos serve` process per project |
| Read-only tools | No file creation, modification, or deletion via MCP |
| Optional dependency | `pip install ontos[mcp]` adds `mcp>=1.2`, `pydantic>=2.0` |
| Usage logging | Tool name + timestamp to `~/.config/ontos/usage.jsonl` |
| Output schemas | `OntosFastMCP` subclass advertises JSON Schema per tool |

### What v4.0.0 Does NOT Do

| Gap | v4.0 Proposal Reference |
|-----|------------------------|
| No portfolio-level index | Section 5 (v4.1 Scope), Section 7 |
| No cross-project tools (`project_registry`, `search`, `get_context_bundle`) | Section 4 (Consumer 3), D8 |
| No context bundle algorithm | D5 |
| No full-text search | D8 |
| No write-capable MCP tools | D7, D8 |
| No multi-workspace identity | D9 (v4.1 definition) |

### The 23-Project Portfolio

From `.dev-hub/registry/projects.json`:

| Category | Count | Examples |
|----------|-------|---------|
| **Documented** (Ontos context map + README) | 10 | canary.work (46 docs), role-evaluator-bot (76 docs), finance-engine-2.0 (55 docs), Ontos-dev (57 docs), folio.love (50 docs) |
| **Partial** (README only or context map only) | 5 | Vibing, ohjonathan.com, NPOLabDev |
| **Undocumented** (neither) | 8 | Career, agent-skills, claude-code-monitoring, engineering-strategy, strategy-eng |

Total tracked documents across documented projects: ~400. 5-6 projects are actively developed.

### Architectural Starting Point

The v4.0 MCP implementation lives in `ontos/mcp/`:

| File | Role | Lines |
|------|------|-------|
| `server.py` | `OntosFastMCP` subclass, `serve()` entry point, tool registration, `_invoke_tool()` wrapper | ~400 |
| `tools.py` | Tool implementations: 8 read-only tools + canonical view builder | ~410 |
| `cache.py` | `SnapshotCache` with file-mtime fingerprinting, thread-safe rebuild, `SnapshotCacheView` | ~285 |
| `schemas.py` | Pydantic response models, `validate_success_payload()`, `output_schema_for()` | ~230 |

Key patterns established in v4.0 that v4.1 must preserve:
- **Canonical snapshot view**: `CanonicalSnapshotView` provides sorted, indexed document data
- **View-based concurrency**: `SnapshotCacheView` is a frozen read view; tools never mutate cache state directly
- **Tool wrapper pattern**: `_invoke_tool()` handles logging, freshness, error enveloping
- **Schema validation**: Every tool response is validated against a Pydantic model before returning
- **Structured output**: `CallToolResult` with both `structuredContent` and `content` (text fallback)
- **Single-worker constraint**: The MCP SDK session store is process-local. Do not run multiple server workers. Single-process, single-worker only.

---

## 4. Consumer Requirements

### Consumer 1: Claude Code / Cursor / IDE Agents (Primary -- v4.1)

**How it connects:** MCP client via stdio (same as v4.0).

**New tools beyond v4.0:**

| Tool | Purpose |
|------|---------|
| `scaffold_document(workspace_id?, type, id, title)` | Create new documents from templates without leaving the MCP session |
| `rename_document(workspace_id?, document_id, new_id)` | Rename with automatic reference updates |
| `log_session(workspace_id?, summary, branch?)` | Record session work as a structured log |
| `promote_document(workspace_id?, document_id, target_level)` | Promote document curation level (L0->L1->L2). Note: promotion is a deliberate quality gate -- this tool automates the mechanical steps, not the judgment. |
| `search(query_string, workspace_id?)` | Cross-project search when connected to portfolio server |
| `project_registry()` | Discover other projects when working cross-project |
| `get_context_bundle(workspace_id?)` | Token-budgeted context package for a workspace |

**Multi-workspace behavior:** When connected to a single-project stdio server (v4.0 mode via `ontos serve`), tools behave exactly as today -- `workspace_id` is omitted and implicit. When connected to a portfolio-aware server (v4.1 mode via `ontos serve --portfolio`), the optional `workspace_id` parameter enables cross-project operations.

### Consumer 2: Vibing MCP (Same as Consumer 1)

Same tools as Claude Code. Uses Ontos during its own development for codebase context. No special requirements.

### Consumer 3: JohnnyOS Orchestrator (Future -- v4.2)

JohnnyOS does not exist today. When it does, it will need Streamable HTTP transport for process-to-process communication. The portfolio tools built in v4.1 (`project_registry`, `search`, `get_context_bundle`) will serve JohnnyOS's needs; the transport layer is the only gap. See Section 13 for v4.2 planned scope.

---

## 5. New MCP Tools

### 5.1 Portfolio Tools

#### `project_registry()`

Returns the complete project inventory with metadata for routing and discovery.

| Field | Value |
|-------|-------|
| **Input** | None |
| **Output** | `{project_count, projects: [{slug, path, status, doc_count, last_updated, tags, has_ontos}], summary}` |
| **Wraps** | Net-new. Reads from `portfolio.db` `projects` table |
| **Cacheable** | Yes, TTL-based (5 min default, configurable) |
| **Annotations** | `readOnlyHint=true, destructiveHint=false, idempotentHint=true` |

**`status` classification:**
- `documented` -- has `.ontos.toml` and indexed documents
- `partial` -- has README but no `.ontos.toml`, or has `.ontos.toml` but <5 documents
- `undocumented` -- neither
- `archived` -- explicitly marked archived in registry

**`tags`:** Derived from project metadata: language, framework, active/dormant, etc.

#### `search(query_string, workspace_id?)`

Full-text search across the portfolio or a single workspace.

| Field | Value |
|-------|-------|
| **Input** | `query_string: str` (required), `workspace_id: str` (optional -- limits to one workspace) |
| **Output** | `{total_hits, results: [{doc_id, workspace_slug, type, status, path, snippet, score}]}` |
| **Wraps** | Net-new. Queries `portfolio.db` FTS5 virtual table |
| **Cacheable** | No |
| **Annotations** | `readOnlyHint=true, destructiveHint=false, idempotentHint=true` |

**Search targets:** Document title (from frontmatter `id`), body content, concepts. Weighted: title 10x, concepts 3x, body 1x (persistent rank via `INSERT INTO fts_content(fts_content, rank) VALUES('rank', 'bm25(10.0, 3.0, 1.0)')`).

**Ranking:** SQLite FTS5 BM25. Results **must** be sorted by `ORDER BY rank` (any other sort forces a temp B-tree sort that is 10-50x slower). Snippet extraction via FTS5 `snippet()` function with `<mark>` delimiters.

**Pagination:** `offset: int = 0`, `limit: int = 20`, max 100.

**Error on invalid `workspace_id`:** Returns `isError: true` with the full list of valid workspace slugs and a pointer to `project_registry()`.

#### `get_context_bundle(workspace_id?)`

Returns a token-budgeted context package for a workspace.

| Field | Value |
|-------|-------|
| **Input** | `workspace_id: str` (optional -- defaults to primary workspace), `token_budget: int` (optional -- defaults to 8192) |
| **Output** | `{workspace_id, workspace_slug, token_estimate, document_count, bundle_text, included_documents: [{id, type, score, token_estimate}], excluded_count, stale_documents: [{id, reason}], warnings}` |
| **Wraps** | Net-new. Implements the context bundle algorithm (Section 7) |
| **Cacheable** | Yes, invalidated when workspace snapshot changes |
| **Annotations** | `readOnlyHint=true, destructiveHint=false, idempotentHint=false` (output depends on freshness state) |

**Error on undocumented projects:** If `workspace_id` resolves to a project with `status: "undocumented"`, returns a structured error directing the user to run `ontos init`. No fallback bundle generation.

### 5.2 Write Tools

All write tools share these properties:
- `readOnlyHint=false, destructiveHint=false, idempotentHint=false`
- Allowed by default over stdio (user has local filesystem access)
- A `--read-only` startup flag strips write tools from the MCP surface entirely (strongest safety primitive, following the GitHub MCP server pattern)
- Return a structured result with `success: bool`, `path: str`, and a `diff` or `summary` field describing what changed
- Validate inputs against the Ontos ontology before writing (type must be valid, dependency direction must be legal, etc.)
- Errors returned with `isError: true` include: what happened, why, and how to fix

#### `scaffold_document(workspace_id?, type, id, title, depends_on?)`

Creates a new document from template at L0 curation level.

| Field | Value |
|-------|-------|
| **Input** | `workspace_id?: str`, `type: str` (kernel/strategy/product/atom/log), `id: str`, `title: str`, `depends_on?: list[str]` |
| **Output** | `{success, path, id, type, status, curation_level}` |
| **Wraps** | `ontos scaffold` CLI command -- calls existing scaffold logic in `ontos/commands/scaffold.py` |

**Validation:**
- `type` must be one of the 5 ontology types
- `id` must be unique within the workspace
- `depends_on` targets must exist
- Dependency direction must be legal per ontology rules

#### `rename_document(workspace_id?, document_id, new_id)`

Renames a document and updates all references across the workspace. This is a **compound tool** -- it performs multiple file modifications atomically server-side rather than asking the client to orchestrate multiple calls.

| Field | Value |
|-------|-------|
| **Input** | `workspace_id?: str`, `document_id: str`, `new_id: str` |
| **Output** | `{success, old_id, new_id, old_path, new_path, references_updated: int, updated_files: list[str]}` |
| **Wraps** | `ontos rename` CLI command -- calls existing rename logic in `ontos/commands/rename.py` |

**Safety:** This is the most impactful write tool. It modifies multiple files (the document itself plus all documents that reference it). The response includes `updated_files` so the agent can verify the scope of changes.

#### `log_session(workspace_id?, summary, branch?, event_type?)`

Creates a structured session log document.

| Field | Value |
|-------|-------|
| **Input** | `workspace_id?: str`, `summary: str`, `branch?: str`, `event_type?: str` (default: "session") |
| **Output** | `{success, path, id, date}` |
| **Wraps** | `ontos log` CLI command -- calls existing log logic in `ontos/commands/log.py` |

#### `promote_document(workspace_id?, document_id, target_level)`

Promotes a document's curation level.

| Field | Value |
|-------|-------|
| **Input** | `workspace_id?: str`, `document_id: str`, `target_level: str` ("L1" or "L2") |
| **Output** | `{success, document_id, old_level, new_level, validation_warnings: list[str]}` |
| **Wraps** | `ontos promote` CLI command -- calls existing promote logic in `ontos/commands/promote.py` |

**Validation:** Promotion to L2 requires all L2-mandatory fields to be present. If validation fails, the tool returns `success: false` with `validation_warnings` listing what's missing, without modifying the document.

---

## 6. Architecture: Portfolio Index

### 6.1 SQLite Database

**Location:** `~/.config/ontos/portfolio.db`

**Role:** Rebuildable cache, not source of truth. Can be deleted and reconstructed from the filesystem at any time. The filesystem remains authoritative for per-project document content.

**Connection PRAGMA block** (applied on every connection open):

```sql
PRAGMA journal_mode = WAL;            -- concurrent readers
PRAGMA synchronous = NORMAL;          -- safe in WAL mode, much faster than FULL
PRAGMA cache_size = -16000;           -- 16 MB page cache
PRAGMA mmap_size = 67108864;          -- 64 MB memory-mapped I/O
PRAGMA temp_store = MEMORY;           -- temp tables in memory
PRAGMA busy_timeout = 5000;           -- 5s wait on lock contention
```

Run `PRAGMA optimize = 0x10002` on connection open; run `PRAGMA optimize` periodically.

**Critical concurrency rules:**
- **`BEGIN IMMEDIATE` for ALL write transactions.** Deferred transactions that upgrade from read to write cause instant `SQLITE_BUSY` regardless of `busy_timeout`. This is the #1 source of SQLite concurrency bugs.
- Serialize writes through an application-level lock (Python `threading.Lock` or `asyncio.Lock`).
- Disable `wal_autocheckpoint` on the writer process (`PRAGMA wal_autocheckpoint = 0`), run `PRAGMA wal_checkpoint(PASSIVE)` every 5 minutes to avoid latency spikes.
- **Do not use connection pooling** -- SQLite connections take microseconds to open; pooling adds no value at this scale.

**Schema versioning:** `PRAGMA user_version = 1` on creation. Check on startup; if mismatch, rebuild from scratch (the DB is a rebuildable cache -- at 400 docs, rebuild takes <1 second). Use atomic file replacement (`write to temp, os.replace()`) for zero-downtime rebuilds.

#### Schema

```sql
-- Project-level metadata
CREATE TABLE projects (
    slug        TEXT PRIMARY KEY,    -- e.g. "canary-work"
    path        TEXT NOT NULL UNIQUE, -- e.g. "/Users/jonathanoh/Dev/canary.work"
    status      TEXT NOT NULL,        -- documented | partial | undocumented | archived
    doc_count   INTEGER DEFAULT 0,
    has_ontos   BOOLEAN DEFAULT FALSE,
    has_readme  BOOLEAN DEFAULT FALSE,
    last_scanned TEXT,                -- ISO 8601 timestamp
    last_modified TEXT,               -- most recent file mtime in project
    tags        TEXT,                 -- JSON array: ["python", "web", "active"]
    metadata    TEXT                  -- JSON object for extensible fields
);

-- Document-level metadata (one row per tracked document across all projects)
CREATE TABLE documents (
    id           TEXT NOT NULL,
    workspace    TEXT NOT NULL REFERENCES projects(slug),
    type         TEXT NOT NULL,       -- kernel | strategy | product | atom | log
    status       TEXT NOT NULL,       -- active | draft | scaffold | archived
    path         TEXT NOT NULL,       -- workspace-relative path
    title        TEXT,                -- humanized from id
    curation     TEXT,                -- L0 | L1 | L2
    content_hash TEXT,
    word_count   INTEGER,
    last_modified TEXT,               -- file mtime
    PRIMARY KEY (workspace, id)
);

-- Full-text search index
CREATE VIRTUAL TABLE fts_content USING fts5(
    doc_id,
    workspace,
    title,
    body,
    concepts,
    content=documents,
    content_rowid=rowid,
    tokenize='porter unicode61',
    prefix='2,3'
);

-- Persistent BM25 rank configuration (title 10x, concepts 3x, body 1x)
INSERT INTO fts_content(fts_content, rank) VALUES('rank', 'bm25(10.0, 3.0, 1.0)');

-- Run after bulk inserts to optimize the FTS index
-- INSERT INTO fts_content(fts_content) VALUES('optimize');

-- Dependency edges (cross-workspace possible in future)
CREATE TABLE edges (
    from_workspace TEXT NOT NULL,
    from_id        TEXT NOT NULL,
    to_workspace   TEXT NOT NULL,
    to_id          TEXT NOT NULL,
    type           TEXT NOT NULL DEFAULT 'depends_on',
    PRIMARY KEY (from_workspace, from_id, to_workspace, to_id, type)
);

-- Scan state for incremental refresh
CREATE TABLE scan_state (
    workspace    TEXT PRIMARY KEY REFERENCES projects(slug),
    fingerprint  TEXT NOT NULL,       -- JSON: {path: [mtime_ns, size], ...}
    scanned_at   TEXT NOT NULL        -- ISO 8601
);
```

**Indexes:**
```sql
CREATE INDEX idx_documents_workspace ON documents(workspace);
CREATE INDEX idx_documents_type ON documents(type);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_edges_to ON edges(to_workspace, to_id);
```

### 6.2 Scan Strategy

**Discovery:** The portfolio scanner needs to know which directories are projects. Source hierarchy:

1. **`.dev-hub/registry/projects.json`** -- the current human-maintained registry. Seeded on first run.
2. **`~/.config/ontos/portfolio.toml`** -- persistent Ontos portfolio config:
   ```toml
   [portfolio]
   scan_roots = ["~/Dev"]
   exclude = ["~/Dev/.dev-hub", "~/Dev/archive"]
   ```
3. **Filesystem heuristic** -- any directory under `scan_roots` containing `.git/` is a candidate project. Directories matching `exclude` patterns are skipped.

**Initial seed:** On first run, if `portfolio.db` does not exist:
1. Read `projects.json` for known projects with paths and metadata
2. Walk `scan_roots` for any `.git/` directories not in `projects.json`
3. For each discovered project, check for `.ontos.toml` (documented), `README.md` (partial), or neither (undocumented)
4. Build the `projects` table
5. For documented projects, run `create_snapshot()` and populate `documents`, `edges`, and `fts_content`
6. Run `INSERT INTO fts_content(fts_content) VALUES('optimize')` after bulk load

**Incremental refresh:** On subsequent runs:
1. Compare `scan_state.fingerprint` against current filesystem state (same file-mtime approach as v4.0 `SnapshotCache`)
2. Only re-index workspaces whose fingerprint has changed
3. For changed workspaces, rebuild the full `documents`/`edges`/`fts_content` for that workspace (atomic: `BEGIN IMMEDIATE`, delete old rows, insert new, commit)

### 6.3 Refresh Mechanism

**Server startup (stdio, single-workspace mode):** Same as v4.0 -- load one workspace into `SnapshotCache`. Portfolio DB is not used.

**Server startup (stdio, portfolio mode via `ontos serve --portfolio`):** Load portfolio from `portfolio.db`. If the database is missing or corrupt, rebuild from scratch (<1 second for 23 projects, ~400 documents). The portfolio DB is opened as an in-process SQLite database, queried during the session, and closed on exit. No background daemon.

**Manual refresh:** The existing `refresh()` tool is extended to accept an optional `workspace_id` parameter. Without it, refreshes the current workspace (v4.0 behavior). With `workspace_id="*"`, triggers a full portfolio re-index.

**Write tool coordination:** Write tools and the portfolio index both modify workspace state. To prevent races:
- Write tools acquire a per-workspace file lock (`<workspace>/.ontos.lock`) before modifying files.
- Lock files include the PID of the holding process. On acquisition, if a lock file exists, check if the PID is still alive (`os.kill(pid, 0)`). If not, break the stale lock and log a warning.
- After a write tool completes, it triggers an immediate re-index of the affected workspace (within the same lock hold) so the portfolio DB is consistent before the lock is released.
- This ensures that `list_documents()` called immediately after `scaffold_document()` returns the new document.

---

## 7. Architecture: Context Bundle Algorithm

### 7.1 The Problem

An agent initializing work on a project needs context. The v4.0 `context_map(compact="tiered")` tool returns the full Tier 1/2/3 markdown -- useful for orientation, but not optimized for token budgets or structured consumption. The Tier 1 section (~2k tokens) is a reasonable default bundle, but it outputs markdown prose, not a structured JSON response with explicit document rankings and token accounting.

The context bundle algorithm produces a **purpose-built context package** that:
- Respects a configurable token budget (default 8192 tokens)
- Ranks documents by structural importance
- Includes document content (not just IDs), pre-formatted for LLM consumption
- Reports staleness and exclusion reasons

### 7.2 Simple Bundling Strategy

v4.1 ships with a straightforward ranking that leverages data already computed by `SnapshotCache`:

**Document selection priority:**

1. **Kernel documents** -- always included first (foundational principles, always relevant). Budget reserved before packing other documents.
2. **Top-N by in-degree** -- documents with the most incoming `depends_on` edges are structural hubs. Already computed via `snapshot.graph.reverse_edges`. Sorted by in-degree descending.
3. **Recent logs** -- session logs from the last 14 days, capped at 5 most recent. Provides "what happened recently" context.
4. **Remaining documents** -- sorted by type rank (strategy > product > atom), then by in-degree within type.

**Token budget packing:**

1. Reserve kernel budget first -- the workspace's top-ranked kernel document is always included, even if it exceeds 50% of the total budget.
2. Estimate token count per document: `tokens = len(content) / 4` (character heuristic).
3. Greedily add documents from the priority list until the budget is exhausted.
4. **Lost-in-the-middle ordering:** When rendering the final bundle, place the highest-scored documents at the **beginning and end** of the assembled text (Stanford TACL 2024 confirmed LLMs attend most to start and end of context window). Mid-priority documents go in the middle.
5. For each included document, render a section with: `## {title} ({type}, {status})\n\n{content}`
6. Append a metadata footer: included document count, excluded count, stale document warnings.

### 7.3 Kill Criterion for Advanced Algorithm

The 5-signal scoring function (type rank, graph centrality, status freshness, recency, curation level) with Personalized PageRank and calibrated weights is **deferred to v4.2**. It will only be built if:

- v4.1 usage data (from `usage.jsonl`) shows agents calling `get_document()` for documents NOT included in the simple bundle -- indicating the bundle is missing relevant content
- An A/B comparison shows the simple bundle underperforms `context_map(compact="tiered")` for agent task completion

If agents perform equally well with the simple bundling over 4 weeks of v4.1 usage, the advanced algorithm is not built.

### 7.4 Bundle Format

```json
{
  "workspace_id": "canary-work",
  "workspace_slug": "canary-work",
  "token_estimate": 7840,
  "document_count": 8,
  "bundle_text": "## Canary Architecture (kernel, active)\n\n...",
  "included_documents": [
    {"id": "canary_architecture", "type": "kernel", "score": 0.92, "token_estimate": 1200},
    {"id": "auth_flow", "type": "strategy", "score": 0.78, "token_estimate": 800}
  ],
  "excluded_count": 38,
  "stale_documents": [
    {"id": "old_api_spec", "reason": "describes target modified since last verification"}
  ],
  "warnings": []
}
```

---

## 8. Dependencies

### v4.1 Dependency Changes

| Dependency | Version | Source | Notes |
|-----------|---------|--------|-------|
| `mcp` | `>=1.27.0, <2.0` | PyPI (Beta) | Pinned upper bound given Beta status. v1.27.0 required for Streamable HTTP support (future v4.2), but also contains stdio fixes. |
| `pydantic` | `>=2.0` | PyPI | Unchanged from v4.0 |
| `sqlite3` | stdlib | Python 3.x | No new dependency -- stdlib module |

**No new PyPI dependencies beyond v4.0.** The portfolio index uses `sqlite3` (stdlib). No starlette, no uvicorn, no cachetools -- those are deferred to v4.2 with HTTP transport.

### Python Version Boundary

- **Base package** (`pip install ontos`): Python 3.9+. Unchanged.
- **MCP extra** (`pip install ontos[mcp]`): **Python 3.10+ required.** The MCP SDK mandates 3.10+. Installing `ontos[mcp]` on Python 3.9 will fail with a dependency resolution error. Python 3.11+ is recommended for `asyncio.TaskGroup` benefits.

---

## 9. Key Decisions

### D1: Portfolio Storage Backend

**Options:** (A) Pure filesystem scan on every query, (B) SQLite for portfolio + filesystem for per-project, (C) Full SQLite for everything

**Recommendation: (B) SQLite portfolio + filesystem per-project.**

This was already recommended in v4.0's Section 7 and D3. The rationale is unchanged:
- Per-project data is authoritative on the filesystem. Duplicating it in SQLite creates a sync problem.
- The portfolio index is a rebuildable cache. SQLite's `sqlite3` is stdlib (zero new dependencies). WAL mode handles concurrent readers. FTS5 provides full-text search.
- `project_registry()` becomes a constant-time indexed query instead of scanning 23 directories.

**Implication:** New dependency: none (sqlite3 is stdlib). New file: `~/.config/ontos/portfolio.db`.

### D2: Multi-Workspace Identity

**Options:** (A) Required `workspace_id` on all tools, (B) Optional `workspace_id` defaulting to primary, (C) Separate single-workspace and portfolio server modes

**Recommendation: (B) + (C). Optional `workspace_id` on all tools, with server mode determining behavior.**

In **single-workspace mode** (`ontos serve`): `workspace_id` is ignored. Tools operate on the configured workspace. This preserves perfect backward compatibility with v4.0 clients.

In **portfolio mode** (`ontos serve --portfolio`):
- `workspace_id` is optional on all existing v4.0 tools. If omitted, uses a configured primary workspace.
- `workspace_id` is optional on new portfolio tools. `project_registry()` always returns all workspaces. `search()` without `workspace_id` searches all workspaces.
- `get_context_bundle()` requires `workspace_id` in portfolio mode (no default -- the caller must specify which project).

**Slugification rule (from v4.0 D9):** Directory name, lowercased, dots and spaces replaced by hyphens. `canary.work` -> `canary-work`. No aliases.

**Resolution order:**
1. Exact match against `projects.slug` in portfolio DB
2. If not found, return `isError: true` with `known_slugs` list and pointer to `project_registry()`

### D3: Context Bundle -- Simple vs. Calibrated

**Options:** (A) Ship with simple bundling (kernel + in-degree + recent logs), (B) Ship with calibrated 5-signal scoring, (C) Ship tiered context map as the bundle

**Recommendation: (A) Ship with simple bundling.**

The simple strategy (Section 7.2) uses data already computed by `SnapshotCache` -- no new algorithms, no weight calibration, no usage data dependency. It provides a structured JSON alternative to `context_map(compact="tiered")` with token budgeting and document-level accounting.

The 5-signal scoring with Personalized PageRank is deferred to v4.2, gated on a kill criterion (Section 7.3). This avoids building an unvalidated algorithm.

**Fallback:** If the simple bundle underperforms for a specific workspace, the agent can fall back to `context_map(compact="tiered")`.

### D4: Token Estimation

**Options:** (A) Character heuristic (1 token per ~4 chars), (B) tiktoken library, (C) Configurable with heuristic default

**Recommendation: (C) Configurable with heuristic default.**

The heuristic is fast and dependency-free. tiktoken adds a PyPI dependency. Start with the heuristic; if it consistently misses budgets by >20% (measurable from v4.1 usage data), switch to tiktoken as an optional dependency in v4.2.

### D5: Write Tool Safety Model

**Options:** (A) All writes are immediate, (B) Dry-run default with explicit `confirm=true`, (C) Immediate writes with detailed response, (D) `--read-only` startup flag

**Recommendation: (C) + (D). Immediate writes with detailed response, plus `--read-only` flag.**

- Write tools return detailed `{success, path, diff/summary}` responses
- The agent inspects the response and can undo if needed (e.g., `git checkout -- <path>`)
- `rename_document()` returns `updated_files` so the agent sees the full blast radius
- `promote_document()` returns `validation_warnings` if promotion requirements aren't met (and does NOT modify the document in that case)
- `--read-only` startup flag strips write tools from the MCP surface entirely. This is the strongest safety primitive (GitHub MCP server pattern).

### D6: FTS Configuration

**Options:** (A) FTS5 with default tokenizer, (B) FTS5 with porter stemmer + unicode61, (C) External search library

**Recommendation: (B) FTS5 with porter stemmer + unicode61.**

Porter stemming handles English morphology. Unicode61 handles non-ASCII. Both built into SQLite FTS5 -- no additional dependencies.

**Column weights:** Title 10x, concepts 3x, body 1x. Configured via FTS5 persistent rank. Results **must** be sorted by `ORDER BY rank`. Add `prefix='2,3'` for prefix-search/autocomplete. Run `INSERT INTO fts_content(fts_content) VALUES('optimize')` after bulk index operations.

### D7: Refresh Strategy (Stdio-Only)

**Options:** (A) Refresh only on tool call (lazy), (B) Rebuild portfolio DB at startup

**Recommendation: (B) Rebuild at startup for portfolio mode.**

In single-workspace mode, the v4.0 behavior is preserved: check staleness on every tool call, rebuild if stale.

In portfolio mode, rebuild the portfolio DB from scratch on startup (<1 second). During the session, check workspace fingerprints lazily on tool calls that target a specific workspace. No background task needed -- stdio sessions are interactive and short-lived.

### D8: Authority Transition from `.dev-hub`

**Options:** (A) Portfolio DB replaces `.dev-hub` immediately, (B) Coexist permanently, (C) Gradual transition

**Recommendation: (C) Gradual transition.**

- **v4.1.0:** Portfolio DB is seeded from `projects.json` on first run. Both sources coexist. `project_registry()` reads from the portfolio DB. A `verify` subcommand compares the DB against `projects.json` and reports discrepancies.
- **v4.1.x (after validation):** If the portfolio DB is proven correct for all 23 projects, `.dev-hub/registry/projects.json` becomes a human-readable export generated from the DB on demand.
- **Transition criterion:** Zero discrepancies between portfolio DB and `projects.json` for 2 consecutive weeks of usage.

---

## 10. Migration Path

### What Stays the Same

- **CLI is fully preserved.** Every existing command works identically.
- **`pip install ontos` (without extras) is unchanged.** No new dependencies for the base package. Python 3.9+.
- **All 8 v4.0 MCP tools work identically.** `workspace_overview`, `context_map`, `get_document`, `list_documents`, `export_graph`, `query`, `health`, `refresh` -- same inputs, same outputs.
- **Stdio transport works identically.** Existing MCP client configs (`claude_desktop_config.json`, `.cursor/mcp.json`) require no changes.
- **`.ontos.toml` is backward compatible.** No new required sections.
- **Per-project document storage is unchanged.** Markdown files with YAML frontmatter.

### What Changes

- **New portfolio config:** `~/.config/ontos/portfolio.toml` for portfolio-level settings (scan roots, bundle config).
- **New database:** `~/.config/ontos/portfolio.db` created on first `--portfolio` run.
- **New CLI flags:** `ontos serve --portfolio`, `ontos serve --read-only`.
- **New tools:** 7 new tools (3 portfolio + 4 write) added to the MCP surface.
- **Optional `workspace_id` parameter:** Added to all tools but ignored in single-workspace mode.
- **MCP SDK pin bump:** `mcp>=1.27.0,<2.0` (from `mcp>=1.2`).

### Python Version Note

The `[mcp]` extra requires **Python 3.10+**. Installing `ontos[mcp]` on Python 3.9 will fail with a dependency resolution error. The base package (`pip install ontos`) continues to work on Python 3.9+.

### Upgrade Steps

1. **Upgrade the package:**
   ```bash
   pip install --upgrade 'ontos[mcp]'
   ```

2. **Verify v4.0 behavior is preserved:**
   ```bash
   ontos --version       # Should show 4.1.0
   ontos serve           # Stdio mode works as before
   ontos doctor          # Check graph health
   ```

3. **(Optional) Enable portfolio mode:**
   ```bash
   # Create portfolio config
   mkdir -p ~/.config/ontos
   cat > ~/.config/ontos/portfolio.toml << 'EOF'
   [portfolio]
   scan_roots = ["~/Dev"]
   exclude = ["~/Dev/.dev-hub", "~/Dev/archive"]
   EOF

   # Start portfolio server (stdio)
   ontos serve --portfolio
   ```

### Rollback Plan

Downgrade: `pip install ontos==4.0.0`. The portfolio database (`portfolio.db`) is ignored by v4.0. Write tools are not present in v4.0's MCP surface. No data migration is needed in either direction because `portfolio.db` is a rebuildable cache. Per-workspace lock files (`.ontos.lock`) can be safely deleted.

---

## 11. Acceptance Criteria

Ontos v4.1.0 is done when all of the following are true:

### Portfolio Tools

1. **`project_registry()` returns all 23 workspaces** with correct `status` classification (documented/partial/undocumented), accurate `doc_count` for documented projects, and valid `slug` values matching the slugification rule.

2. **`search("simhash")` returns relevant results** via FTS5 across all documented projects. Results include document ID, workspace slug, snippet with match highlighting, and BM25 score. Searching with `workspace_id` restricts results to that workspace.

3. **`get_context_bundle("canary-work")` returns a coherent context package** within the default 8192-token budget. The bundle includes kernel documents first, then top-N by in-degree, then recent logs. Token estimate is within 20% of actual token count.

4. **`get_context_bundle()` on an undocumented project returns a structured error** directing the user to run `ontos init`.

5. **Portfolio index survives session restart.** After stopping and restarting `ontos serve --portfolio`, `project_registry()` returns results immediately (reads from `portfolio.db`).

### Write Tools

6. **`scaffold_document(type="atom", id="test_doc", title="Test")` creates a valid document** at the correct path with L0 frontmatter, and the document appears in subsequent `list_documents()` calls.

7. **`rename_document(document_id="old_id", new_id="new_id")` renames and updates references.** All documents that previously referenced `old_id` now reference `new_id`. The response includes the count and list of updated files.

8. **`log_session(summary="Test session")` creates a valid session log** with correct date-stamped filename and frontmatter.

9. **`promote_document(document_id="test_doc", target_level="L2")` fails gracefully** when L2 requirements are not met, returning `success: false` with specific `validation_warnings`.

10. **`--read-only` flag strips write tools.** Starting the server with `ontos serve --read-only` removes all 4 write tools from `tools/list`.

### Backward Compatibility

11. **All 8 v4.0 tools work identically in single-workspace mode.** Existing test suite passes without modification.

12. **`pip install ontos` (without `[mcp]`) still works on Python 3.9+.** No new base dependencies.

13. **Existing MCP client configurations require no changes.** `ontos serve` with no flags behaves identically to v4.0.

### Portfolio Index

14. **Incremental refresh re-indexes only changed workspaces.** After modifying a document in one workspace, only that workspace is re-indexed on the next `refresh()` call.

15. **Portfolio DB can be deleted and rebuilt.** Deleting `portfolio.db` and restarting the server reconstructs the full index within 2 seconds for 23 projects.

---

## 12. Open Questions

**Q1: Cross-workspace dependencies.** The `edges` table supports `from_workspace != to_workspace`, but no Ontos documents currently declare cross-workspace dependencies. Should v4.1 support this? **Recommendation:** Schema supports it, but the UI and validation are deferred. No cross-workspace `depends_on` in v4.1 frontmatter. The table structure is forward-compatible.

**Q2: MCP Resources and Prompts.** v4.0 uses Tools only. Should v4.1 also expose MCP Resources (for lazy document loading) and Prompts (for guided workflows)? **Recommendation:** Defer to v4.2. Tools are sufficient for all defined consumer workflows. Resources add complexity (URI schemes, subscription semantics) without clear consumer demand.

**Q3: Log retention in bundles.** How many session logs should be included in context bundles? **Recommendation:** Time-window with a count cap. Include logs from the last 14 days, capped at 5 most recent. Configurable in `portfolio.toml`.

**Q4: Concurrent write safety.** If two agents call `rename_document()` on the same document simultaneously, what happens? **Recommendation:** Write tools acquire a per-workspace file lock (`<workspace>/.ontos.lock`) with PID tracking. Second caller receives a `BUSY` error with retry guidance. Lock timeout: 10 seconds. Stale locks (dead PID) are broken automatically.

**Q5: Portfolio server as `ontos serve --portfolio`.** Should portfolio mode require the `--portfolio` flag, or should it auto-detect based on `portfolio.toml` presence? **Recommendation:** Require the flag. Explicit is better than implicit, and it preserves v4.0 behavior as the default.

---

## 13. Deferred to v4.2: HTTP Transport and Daemon Mode

The following capabilities are deferred to a separate v4.2 proposal, to be triggered when JohnnyOS (or another concrete consumer) demonstrates the need for persistent HTTP transport.

### v4.2 Planned Scope

| Capability | Details |
|-----------|---------|
| **Streamable HTTP transport** | `ontos serve --http` on `127.0.0.1:9400/mcp`. ASGI mounting with middleware stack (not `server.run()`). |
| **Security model** | Bearer token (macOS Keychain storage), DNS rebinding protection (Origin/Host validation, CVE-2025-66414), CORS, security headers, audit logging (`chmod 0600` JSONL), rate limiting. |
| **Daemon mode** | Long-running portfolio server with background indexer (60s polling). launchd plist with KeepAlive, ThrottleInterval, PYTHONUNBUFFERED, PATH, ExitTimeOut. |
| **Memory management** | 7-day uptime watchdog (launchd auto-restart). `cachetools.TTLCache` for document content. `tracemalloc` + `psutil` monitoring with 1.5GB RSS warning threshold. |
| **Advanced bundle algorithm** | 5-signal scoring (type rank, Personalized PageRank, status freshness, recency, curation level). Calibrated from v4.1 usage data. Nested granularity (full/summary/title-only). |
| **New dependencies** | `starlette`, `uvicorn`, `cachetools` (all downstream of HTTP transport). |

### v4.2 Trigger Criteria

v4.2 is proposed when **any** of the following are true:
- JohnnyOS development begins and requires HTTP transport for process-to-process communication
- A concrete consumer demonstrates the need for a persistent portfolio server (not session-scoped)
- v4.1 usage data shows cross-project search is called frequently enough that startup-time DB rebuilds become a bottleneck

### Research Findings Preserved for v4.2

The [consolidated research](ontos-v4.1-research-consolidated.md) findings on Streamable HTTP semantics, ASGI mounting patterns, SDK memory leaks (#1076, #756), FastMCP shutdown bugs (#514), Keychain-from-launchd interactions, and production MCP security patterns are preserved in the research document and will inform the v4.2 proposal when it is written.
