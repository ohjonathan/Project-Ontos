---
id: ontos_v41_proposal
type: strategy
status: draft
depends_on: [ontos_manual]
---

# Ontos v4.1 Proposal: Portfolio Authority

**Date:** 2026-04-10
**Revised:** 2026-04-10 (v2 -- research corrections applied: Streamable HTTP, ASGI mounting, SQLite PRAGMAs, FTS5 tuning, bundle algorithm refinements, DNS rebinding mitigations, Python 3.10+ requirement, Claude Desktop limitation)
**Author:** Claude (synthesized from v4.0 deferred scope, consumer brief, and codebase analysis)
**Status:** PROPOSAL -- requires review and decision by Johnny
**Audience:** Johnny (project owner), LLMs reviewing for correctness and gaps

**Research:** See [ontos-v4.1-research-consolidated.md](ontos-v4.1-research-consolidated.md) -- consolidated findings from 3 parallel deep-research runs (Models A, G, O) validating design decisions against MCP ecosystem best practices.

---

## 1. What Is This

Ontos v4.1 is the **portfolio authority** release. It extends the v4.0 single-project MCP bridge into a multi-workspace server that indexes all 23 projects in `~/Dev/`, provides cross-project search, generates token-budgeted context bundles, and exposes write-capable MCP tools. Where v4.0 asked "what can one project's knowledge graph do over MCP?", v4.1 asks "what can the entire development portfolio do?"

Concretely, v4.1 adds:

- **Portfolio index** -- a SQLite database (`~/.config/ontos/portfolio.db`) spanning all workspaces, with FTS5 full-text search
- **3 new portfolio tools** -- `project_registry()`, `search()`, `get_context_bundle()`
- **4 new write tools** -- `scaffold_document()`, `rename_document()`, `log_session()`, `promote_document()`
- **Streamable HTTP transport** -- alongside stdio, for process-to-process communication (JohnnyOS)
- **Context bundle algorithm** -- a 5-signal scoring function that assembles right-sized context packages per workspace
- **Undocumented project handling** -- thin metadata entries for the 13 projects without Ontos coverage
- **Security model** -- bearer token auth, audit logging, rate limiting for the HTTP transport

The CLI remains fully functional. All 8 existing v4.0 tools remain unchanged. MCP is still additive.

---

## 2. Why Now

### v4.0 Usage Data Is Available

v4.0.0 shipped with `usage_logging = true` writing tool call patterns to `~/.config/ontos/usage.jsonl`. This data reveals which tools agents call, how often, and what parameters they use. The context bundle algorithm (Section 7) was explicitly deferred to v4.1 pending this data. The data now exists.

### JohnnyOS Is the Next Build Target

The JohnnyOS orchestrator is the next artifact in the ecosystem. Its architecture requires three capabilities that v4.0 cannot provide: `project_registry()` for task routing (called 20-50x/day), `get_context_bundle()` for domain supervisor initialization (5-20x/day per workspace), and `search()` for ad-hoc knowledge retrieval. These are not nice-to-haves -- they are blocking dependencies for JohnnyOS Phase 3.

### The Single-Workspace Ceiling Is Real

Claude Code and Cursor users currently spawn one `ontos serve` process per project. When working across projects (e.g., "what does canary.work depend on that finance-engine also uses?"), the agent has no cross-project query path. It falls back to reading `~/.dev-hub/registry/projects.json` or asking the user. v4.1 removes this ceiling.

### The MCP Ecosystem Has Matured Further

Since v4.0 shipped:
- Streamable HTTP transport is stable in the Python MCP SDK (`mcp >= 1.27.0`, April 2026). The 2025-03-26 spec revision deprecated the legacy HTTP+SSE transport in favor of Streamable HTTP.
- FastMCP (already used in v4.0's `OntosFastMCP` subclass) supports `transport="streamable-http"` and ASGI mounting for middleware integration
- Multiple production MCP servers now expose write tools with safety patterns (dry-run, confirmation, `--read-only` startup flag)
- The MCP auth specification has adopted OAuth 2.1 + PKCE (RFC 9728) for remote servers; bearer token remains the pragmatic baseline for single-user local servers
- **Python 3.10+ is mandatory** for the MCP SDK (confirmed across all SDK releases). Python 3.11+ is recommended for `asyncio.TaskGroup`, which simplifies the portfolio indexer's concurrent scan/serve architecture

### Competitive Pressure

CTX, Claude Code memory, and Cursor context are shipping portfolio-level features. Ontos's differentiation remains deterministic, graph-based retrieval -- but that differentiation requires portfolio scope to matter beyond single-project contexts.

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
| Optional dependency | `pip install ontos[mcp]` adds `mcp>=1.2`, `pydantic>=2.0` (v4.1 will pin `mcp>=1.27.0` for Streamable HTTP support; Python 3.10+ required, 3.11+ recommended) |
| Usage logging | Tool name + timestamp to `~/.config/ontos/usage.jsonl` |
| Output schemas | `OntosFastMCP` subclass advertises JSON Schema per tool |

### What v4.0.0 Does NOT Do

These are the explicit v4.1 deferrals from the v4.0 proposal (Sections 5, 7, 8):

| Gap | v4.0 Proposal Reference |
|-----|------------------------|
| No portfolio-level index | Section 5 (v4.1 Scope), Section 7 |
| No cross-project tools (`project_registry`, `search`, `get_context_bundle`) | Section 4 (Consumer 3), D8 |
| No context bundle algorithm | D5 |
| No full-text search | D8 |
| No write-capable MCP tools | D7, D8 |
| No Streamable HTTP transport | D1 |
| No undocumented project handling | D6 |
| No multi-workspace identity | D9 (v4.1 definition) |
| No security beyond stdio isolation | D7 (v4.1 security model) |

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
| `tools.py` | Tool implementations: `workspace_overview`, `context_map`, `get_document`, `list_documents`, `export_graph`, `query`, `health`, `refresh` | ~410 |
| `cache.py` | `SnapshotCache` with file-mtime fingerprinting, thread-safe rebuild, `SnapshotCacheView` | ~285 |
| `schemas.py` | Pydantic response models, `validate_success_payload()`, `output_schema_for()` | ~230 |

Key patterns established in v4.0 that v4.1 must preserve:
- **Canonical snapshot view**: `CanonicalSnapshotView` provides sorted, indexed document data
- **View-based concurrency**: `SnapshotCacheView` is a frozen read view; tools never mutate cache state directly
- **Tool wrapper pattern**: `_invoke_tool()` handles logging, freshness, error enveloping
- **Schema validation**: Every tool response is validated against a Pydantic model before returning
- **Structured output**: `CallToolResult` with both `structuredContent` and `content` (text fallback)

---

## 4. Consumer Requirements

### Consumer 1: JohnnyOS Orchestrator (Primary -- v4.1)

**How it connects:** MCP client running on Mac Mini, calling Ontos v4.1 over Streamable HTTP (persistent daemon) or stdio (child process fallback).

**Tools it expects to call:**

| Tool | Purpose | Frequency | Cacheable |
|------|---------|-----------|-----------|
| `project_registry()` | Route incoming tasks to the correct workspace supervisor by matching keywords/project names against the registry | 20-50x/day | Yes (TTL-based, 5min) |
| `get_context_bundle(workspace_id)` | Initialize domain supervisors with right-sized project context | 5-20x/day per workspace | Yes (mtime-invalidated) |
| `search(query_string, workspace_id?)` | Ad-hoc cross-project knowledge retrieval ("find the doc about simhash") | Ad-hoc | No |
| `workspace_overview(workspace_id?)` | Quick orientation after routing | Ad-hoc | Yes |
| `health()` | Registered as `runtime_asset` in JohnnyOS with health checks | Periodic | No |

**What it does NOT need from Ontos:**
- Task state (JohnnyOS Workflow Ledger)
- Runtime state (JohnnyOS Runtime Registry)
- Raw activity (JohnnyOS Artifact Store)
- Prompt templates (Vibing MCP)

**Write path:** JohnnyOS writes promoted documents as Markdown files into Ontos-indexed workspace directories. Ontos picks them up on the next index sweep. The boundary is the filesystem, not an API write call. However, `log_session()` may be called by JohnnyOS to record orchestrator activity as structured session logs.

### Consumer 2: Claude Code / Cursor / IDE Agents (Enhanced -- v4.1)

**How it connects:** MCP client via stdio (same as v4.0). May optionally connect to a running Streamable HTTP server if one is available.

**New tools beyond v4.0:**

| Tool | Purpose |
|------|---------|
| `scaffold_document(workspace_id?, type, id, title)` | Create new documents from templates without leaving the MCP session |
| `rename_document(workspace_id?, document_id, new_id)` | Rename with automatic reference updates |
| `log_session(workspace_id?, summary, branch?)` | Record session work as a structured log |
| `promote_document(workspace_id?, document_id, target_level)` | Promote document curation level (L0->L1->L2) |
| `search(query_string, workspace_id?)` | Cross-project search when connected to portfolio server |
| `project_registry()` | Discover other projects when working cross-project |

**Multi-workspace behavior:** When connected to a single-project stdio server (v4.0 mode), tools behave exactly as today -- `workspace_id` is omitted and implicit. When connected to a portfolio-aware server (v4.1 mode), the optional `workspace_id` parameter enables cross-project operations.

### Consumer 3: Vibing MCP (Same as Consumer 2)

Same tools as Claude Code. Uses Ontos during its own development for codebase context. No special requirements.

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
| **Frequency** | 20-50x/day (JohnnyOS routing), cached |
| **Cacheable** | Yes, TTL-based (5 min default, configurable) |
| **Annotations** | `readOnlyHint=true, idempotentHint=true` |

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
| **Frequency** | Ad-hoc |
| **Cacheable** | No |
| **Annotations** | `readOnlyHint=true, idempotentHint=true` |

**Search targets:** Document title (from frontmatter `id`), body content, concepts, type, status. Weighted: title 10x, concepts 3x, body 1x (persistent rank via `INSERT INTO fts_content(fts_content, rank) VALUES('rank', 'bm25(10.0, 3.0, 1.0)')`).

**Ranking:** SQLite FTS5 BM25. Results sorted by score descending. Snippet extraction via FTS5 `snippet()` function with `<mark>` delimiters.

**Pagination:** `offset: int = 0`, `limit: int = 20`, max 100.

#### `get_context_bundle(workspace_id?)`

Returns a token-budgeted context package for a workspace.

| Field | Value |
|-------|-------|
| **Input** | `workspace_id: str` (optional -- defaults to primary workspace), `token_budget: int` (optional -- defaults to 8192) |
| **Output** | `{workspace_id, workspace_slug, token_estimate, document_count, bundle_text, included_documents: [{id, type, score, token_estimate}], excluded_count, stale_documents: [{id, reason}], warnings}` |
| **Wraps** | Net-new. Implements the context bundle algorithm (Section 7) |
| **Frequency** | 5-20x/day per workspace |
| **Cacheable** | Yes, invalidated when workspace snapshot changes |
| **Annotations** | `readOnlyHint=true, idempotentHint=false` (output depends on freshness state) |

**Error on undocumented projects:** If `workspace_id` resolves to a project with `status: "undocumented"`, returns a structured error directing the user to run `ontos init`. No fallback bundle generation.

### 5.2 Write Tools

All write tools share these properties:
- `readOnlyHint=false, destructiveHint=false, idempotentHint=false`
- Require explicit opt-in via `[mcp.security] allow_write_tools = true` in `.ontos.toml` (HTTP transport) or are allowed by default (stdio transport)
- Return a structured result with `success: bool`, `path: str`, and a `diff` or `summary` field describing what changed
- Validate inputs against the Ontos ontology before writing (type must be valid, dependency direction must be legal, etc.)

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

Renames a document and updates all references across the workspace.

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
- Serialize writes through an application-level lock (Python `asyncio.Lock`).
- Disable `wal_autocheckpoint` on the writer process (`PRAGMA wal_autocheckpoint = 0`), run `PRAGMA wal_checkpoint(PASSIVE)` every 5 minutes to avoid latency spikes.
- **Do not use connection pooling** -- SQLite connections take microseconds to open; pooling adds no value at this scale.

Multiple MCP server processes can read from the same database simultaneously (JohnnyOS + Claude Code) thanks to WAL mode.

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

**Incremental refresh:** On subsequent runs:
1. Compare `scan_state.fingerprint` against current filesystem state (same file-mtime approach as v4.0 `SnapshotCache`)
2. Only re-index workspaces whose fingerprint has changed
3. For changed workspaces, rebuild the full `documents`/`edges`/`fts_content` for that workspace (atomic: delete old rows, insert new, within a transaction)

### 6.3 Refresh Mechanism

**Server startup:** Load portfolio from `portfolio.db`. If the database is missing or corrupt, rebuild from scratch (2-5 seconds for 23 projects, ~400 documents).

**Background refresh:** A background task periodically checks workspace fingerprints (configurable interval, default 60 seconds). Only re-indexes workspaces that have changed. This ensures portfolio tools serve fresh data without requiring explicit `refresh()` calls.

**Manual refresh:** The existing `refresh()` tool is extended to accept an optional `workspace_id` parameter. Without it, refreshes the current workspace (v4.0 behavior). With `workspace_id="*"`, triggers a full portfolio re-index.

**Concurrency:** SQLite WAL mode allows concurrent readers. Writes are serialized by SQLite's internal locking. The re-index task acquires a Python-level lock to prevent concurrent rebuilds of the same workspace. `SQLITE_BUSY` is handled with a 5-second timeout and retry.

**Background refresh + write tool coordination:** The background refresh task and write tools both modify workspace state. To prevent races:
- Write tools acquire a per-workspace file lock (`<workspace>/.ontos.lock`) before modifying files.
- The background refresh task checks this lock before re-indexing a workspace. If locked, it skips that workspace and retries on the next cycle.
- After a write tool completes, it triggers an immediate re-index of the affected workspace (within the same lock hold) so the portfolio DB is consistent before the lock is released.
- This ensures that `list_documents()` called immediately after `scaffold_document()` returns the new document.

---

## 7. Architecture: Context Bundle Algorithm

### 7.1 The Problem

An agent initializing work on a project needs context. The v4.0 `context_map(compact="tiered")` tool returns the full Tier 1/2/3 markdown -- useful for orientation, but not optimized for token budgets or focused queries. The Tier 1 section (~2k tokens) is a reasonable default bundle, but it's hand-tuned to the context map format, not to agent consumption patterns.

The context bundle algorithm produces a **purpose-built context package** that:
- Respects a configurable token budget (default 8192 tokens)
- Ranks documents by structural importance, not just in-degree
- Includes document content (not just IDs), pre-formatted for LLM consumption
- Reports staleness and exclusion reasons

### 7.2 The 5-Signal Scoring Function

Each document in a workspace receives a composite score from 5 signals:

```
score(doc) = w1 * type_rank(doc)
           + w2 * centrality(doc)
           + w3 * freshness(doc)
           + w4 * recency(doc)
           + w5 * curation(doc)
```

#### Signal 1: Type Rank

Documents are ranked by ontological type. Higher types are structurally more important.

| Type | Rank | Rationale |
|------|------|-----------|
| kernel | 1.0 | Foundational principles -- always relevant |
| strategy | 0.8 | Goals and roadmap -- sets direction |
| product | 0.6 | User-facing specs -- practical context |
| atom | 0.4 | Technical implementation -- detail-level |
| log | 0.2 | Session history -- recent activity signal |

#### Signal 2: Graph Centrality

**Base implementation:** In-degree centrality -- how many other documents depend on this document. Normalized to [0, 1] by dividing by the maximum in-degree in the workspace.

```
centrality(doc) = in_degree(doc) / max_in_degree(workspace)
```

Documents with high in-degree are structural hubs -- many other docs reference them. This is already computed by `SnapshotCache.depths` and `snapshot.graph.reverse_edges`.

**Planned enhancement: Personalized PageRank.** For query-dependent scoring (when the agent requests a bundle focused on a specific topic), use Personalized PageRank seeded from the query-matched document. For broad "give me the project context" queries, fall back to global PageRank. Research confirms this outperforms raw in-degree for topic-focused retrieval. Additionally, HITS (hubs/authorities) maps naturally to the Ontos document taxonomy -- authorities = definitive reference docs (kernel), hubs = docs that link many others together (strategy). Betweenness centrality can identify bridge documents across topic clusters.

#### Signal 3: Status Freshness

| Status | Score | Rationale |
|--------|-------|-----------|
| active | 1.0 | Current and maintained |
| draft | 0.6 | Work in progress -- still relevant |
| scaffold | 0.3 | Placeholder -- low information value |
| archived | 0.0 | Superseded -- exclude by default |

#### Signal 4: Recency

How recently the document was modified, normalized to [0, 1] using exponential decay:

```
recency(doc) = exp(-days_since_modified / half_life)
```

Where `half_life = 30` days (configurable). A document modified today scores 1.0; modified 30 days ago scores 0.5; modified 90 days ago scores 0.125.

#### Signal 5: Curation Level

| Level | Score | Rationale |
|-------|-------|-----------|
| L2 (full) | 1.0 | Fully curated -- highest signal-to-noise |
| L1 (stub) | 0.5 | Partially curated |
| L0 (scaffold) | 0.2 | Minimal content |

### 7.3 Weight Calibration

**Default weights** (starting point, to be calibrated from v4.0 usage data):

| Weight | Signal | Default | Rationale |
|--------|--------|---------|-----------|
| w1 | Type rank | 0.25 | Structural hierarchy matters |
| w2 | Centrality | 0.30 | Hub documents are most referenced |
| w3 | Freshness | 0.15 | Active > archived |
| w4 | Recency | 0.15 | Recent work is more relevant |
| w5 | Curation | 0.15 | Higher curation = higher quality |

**Calibration plan:**
1. Analyze v4.0 `usage.jsonl` to identify which documents agents request via `get_document()` after calling `context_map()`
2. For each documented workspace, define a human-curated "ideal bundle" of 5-10 documents
3. Score all documents with the algorithm and compare top-N against the ideal bundle
4. Adjust weights to maximize overlap (precision@k metric)
5. Publish weights in `~/.config/ontos/portfolio.toml` so they can be tuned per-deployment

### 7.4 Token Budget Packing

After scoring, documents are selected for the bundle using a greedy knapsack approach:

1. **Reserve kernel budget first.** The workspace's top-ranked kernel document is always included, even if it exceeds 50% of the total budget. Reserve its token cost before packing other documents.
2. Sort remaining documents by `score / token_count` (value density) descending.
3. Estimate token count per document: `tokens = len(content) / 4` (character heuristic, switchable to tiktoken if accuracy matters -- see D4).
4. Greedily add documents until the budget is exhausted.
5. **Lost-in-the-middle ordering:** When rendering the final bundle, place the highest-scored documents at the **beginning and end** of the assembled text. Stanford TACL 2024 and Chroma 2025 confirmed across 18 frontier models that LLMs attend most to the start and end of their context window. Mid-ranked documents go in the middle.
6. For each included document, render a section with: `## {title} ({type}, {status})\n\n{content}`
7. Append a metadata footer: included document count, total score, excluded count, stale document warnings.

**Planned enhancement: Nested granularity.** Instead of including each document as full-content-or-nothing, generate multiple knapsack items per document at different sizes: full content, summary (first 200 words + heading structure), or title-only. This allows the packer to include more documents at lower fidelity when the budget is tight. The Qodo pattern demonstrates this approach in production. Deferred to post-v4.1.0 -- the base greedy knapsack ships first.

### 7.5 Bundle Format

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

## 8. Architecture: Transport and Security

### 8.1 Dual Transport

v4.1 supports both stdio and Streamable HTTP transports:

**Stdio (preserved from v4.0):**
```bash
ontos serve                         # stdio, current directory
ontos serve --workspace ~/Dev/foo   # stdio, specific workspace
```

Behavior is identical to v4.0. Single workspace, spawned as a child process by the IDE client.

**Streamable HTTP (new in v4.1):**
```bash
ontos serve --http                  # Streamable HTTP on http://127.0.0.1:9400/mcp
ontos serve --http --port 9401      # custom port
ontos serve --http --portfolio      # portfolio mode: all workspaces indexed
```

The `--portfolio` flag is the key differentiator. Without it, the HTTP server serves a single workspace (same as stdio but over HTTP). With it, the server loads the portfolio index and enables cross-project tools (`project_registry`, `search`, `get_context_bundle`).

**Process model:**
- **Stdio:** One process per workspace (same as v4.0). Short-lived, spawned by IDE.
- **HTTP + portfolio:** One long-running daemon serving all workspaces. This is the JohnnyOS deployment mode.
- **HTTP without portfolio:** One process per workspace, reachable over HTTP. For cases where JohnnyOS needs to connect to a specific project without the full portfolio.

**Client compatibility (Streamable HTTP):**
- **Claude Code:** `--transport http` (v1.0.27+). Full support.
- **Cursor:** Auto-detects transport (v0.50+). Full support.
- **VS Code Copilot:** v1.102+. Full support.
- **Claude Desktop:** Cannot connect to local HTTP MCP servers via `claude_desktop_config.json` -- it only supports remote Streamable HTTP via the paid Integrations UI. **Workaround:** Ship an `mcp-remote` bridge configuration that proxies the local HTTP server for Claude Desktop users. Alternatively, Claude Desktop users continue to use stdio transport (single-workspace mode).
- **MCP Inspector:** All transports supported, but has known `Last-Event-ID` resume bugs. Useful for development, not sufficient for transport validation.

### 8.2 Security Model

**Stdio transport (unchanged):** No authentication needed. Stdio is inherently limited to the spawning process. All v4.0 security properties are preserved.

**HTTP transport (new):**

> **Threat context:** CVE-2025-66414 (CVSS 7.6) demonstrated DNS rebinding against the MCP TypeScript SDK -- malicious websites could hit any localhost MCP server by resolving an attacker-controlled domain to 127.0.0.1. **Localhost is not a security boundary.** The mitigations below are defense-in-depth, not optional hardening.

| Layer | Mechanism |
|-------|-----------|
| **Network binding** | `127.0.0.1` only. No external network exposure. Binding to `0.0.0.0` requires explicit `--bind 0.0.0.0` flag with a warning. |
| **DNS rebinding protection** | Validate **both** `Origin` and `Host` headers on every HTTP request. Reject requests where `Host` is not `localhost` or `127.0.0.1` with HTTP 403. This is now mandated by the MCP specification. |
| **Authentication** | Bearer token. Token generated via `secrets.token_urlsafe(32)` on first `ontos serve --http`. **Stored in macOS Keychain** (`security add-generic-password -a ontos -s ontos-mcp-token -w "$TOKEN"`), not as a plaintext file. Retrieved at startup via `security find-generic-password -a ontos -s ontos-mcp-token -w`. Clients pass `Authorization: Bearer <token>` header. |
| **CORS** | Restrict origins to specific localhost ports. Include `Mcp-Session-Id` in `Access-Control-Expose-Headers`. |
| **Security headers** | `X-Frame-Options: DENY`, `Content-Security-Policy: frame-ancestors 'none'` on all responses. Prevents iframe-based attacks. |
| **Write tool authorization** | Write tools (`scaffold_document`, `rename_document`, `log_session`, `promote_document`) require `[mcp.security] allow_write_tools = true` in the workspace's `.ontos.toml`. Default is `false` for HTTP. Stdio always allows write tools (user has local access). Additionally, a `--read-only` startup flag strips write tools from the MCP surface entirely (strongest safety primitive, following the GitHub MCP server pattern). |
| **Audit logging** | Append-only JSON lines at `~/.config/ontos/audit.log` (`chmod 0600`). Fields: timestamp, event_type, tool_name, parameters (redacted), outcome, duration_ms, session_id, correlation_id. No document content logged. |
| **Rate limiting** | Per-tool, configurable. Default: 60 calls/min for read tools, 10 calls/min for write tools. Implemented as a token bucket per tool name. |

**HTTP auth integration with `_invoke_tool()`:** The v4.0 `_invoke_tool()` function handles logging, freshness, and error enveloping. For HTTP transport, auth is handled as **middleware outside the MCP tool layer**, not inside `_invoke_tool()`. The request pipeline is:

1. HTTP request arrives at the ASGI application (Streamable HTTP endpoint)
2. **Auth middleware** extracts and validates the bearer token. Rejects with 401 if invalid.
3. **Audit middleware** logs the request (timestamp, tool name, client IP, auth status).
4. **Rate limit middleware** checks per-tool token bucket. Rejects with 429 if exceeded.
5. **Write authorization middleware** (for write tools only) checks `[mcp.security] allow_write_tools` in the target workspace's `.ontos.toml`. Rejects with 403 if not enabled.
6. Request reaches the MCP tool handler, which calls `_invoke_tool()` unchanged from v4.0.

This preserves the v4.0 tool handler code without modification. Auth context (client identity, workspace permissions) is resolved before the tool layer sees the request. The middleware stack is implemented as ASGI middleware wrapping the mounted MCP application (see D6 for the ASGI architecture).

### 8.3 Configuration

Portfolio-level config in `~/.config/ontos/portfolio.toml`:

```toml
[portfolio]
scan_roots = ["~/Dev"]
exclude = ["~/Dev/.dev-hub", "~/Dev/archive"]

[server]
default_port = 9400
bind = "127.0.0.1"

[server.rate_limits]
read_tools = 60     # calls per minute
write_tools = 10

[bundle]
default_token_budget = 8192
weights = { type_rank = 0.25, centrality = 0.30, freshness = 0.15, recency = 0.15, curation = 0.15 }
recency_half_life_days = 30
```

Per-workspace config remains in `.ontos.toml` with an extended `[mcp]` section:

```toml
[mcp]
usage_logging = true
usage_log_path = "~/.config/ontos/usage.jsonl"

[mcp.security]
allow_write_tools = true   # default false for HTTP, ignored for stdio
```

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

In **single-workspace mode** (stdio or HTTP without `--portfolio`): `workspace_id` is ignored. Tools operate on the configured workspace. This preserves perfect backward compatibility with v4.0 clients.

In **portfolio mode** (HTTP with `--portfolio`):
- `workspace_id` is optional on all existing v4.0 tools. If omitted, uses a configured primary workspace.
- `workspace_id` is optional on new portfolio tools. `project_registry()` always returns all workspaces. `search()` without `workspace_id` searches all workspaces.
- `get_context_bundle()` requires `workspace_id` in portfolio mode (no default -- the caller must specify which project).

**Slugification rule (from v4.0 D9):** Directory name, lowercased, dots and spaces replaced by hyphens. `canary.work` -> `canary-work`. No aliases.

**Resolution order:**
1. Exact match against `projects.slug` in portfolio DB
2. If not found, return error with `known_slugs` list for discovery

### D3: Context Bundle Algorithm -- Calibrated vs. Heuristic

**Options:** (A) Ship with heuristic weights, calibrate post-launch, (B) Block on calibration before shipping, (C) Ship Tier 1 context map as the bundle, defer algorithm entirely

**Recommendation: (A) Ship with heuristic weights, calibrate post-launch.**

The 5-signal scoring function (Section 7.2) uses structurally sound signals. The default weights are reasonable starting points. Blocking on perfect calibration delays JohnnyOS, which needs `get_context_bundle()` to function.

**Calibration data:** v4.0's `usage.jsonl` provides the input. The calibration plan (Section 7.3) defines the process. Weights are stored in `portfolio.toml` and can be tuned without code changes.

**Fallback:** If the algorithm produces poor bundles for a specific workspace, the agent can fall back to `context_map(compact="tiered")` -- the Tier 1 output that works today.

### D4: Token Estimation

**Options:** (A) Character heuristic (1 token per ~4 chars), (B) tiktoken library, (C) Configurable with heuristic default

**Recommendation: (C) Configurable with heuristic default.**

The heuristic is fast and dependency-free. tiktoken adds a PyPI dependency. Start with the heuristic; if it consistently misses budgets by >20% (measurable from usage data), switch to tiktoken as an optional dependency.

### D5: Write Tool Safety Model

**Options:** (A) All writes are immediate (fire-and-forget), (B) Dry-run default with explicit `confirm=true`, (C) Immediate writes with detailed response for agent verification

**Recommendation: (C) Immediate writes with detailed response.**

MCP tools are called by agents that can inspect the response and take corrective action. A dry-run mode adds a round-trip that doubles the cost of every write operation. Instead:
- Write tools return detailed `{success, path, diff/summary}` responses
- The agent inspects the response and can undo if needed (e.g., `git checkout -- <path>`)
- `rename_document()` returns `updated_files` so the agent sees the full blast radius
- `promote_document()` returns `validation_warnings` if promotion requirements aren't met (and does NOT modify the document in that case)

**HTTP transport restriction:** Write tools require `[mcp.security] allow_write_tools = true` in the workspace's `.ontos.toml`. This prevents remote write access to workspaces that haven't opted in. Stdio always allows writes (the user has local filesystem access anyway).

### D6: HTTP Transport Implementation

**Options:** (A) Implement from scratch with aiohttp, (B) Use `server.run(transport="streamable-http")`, (C) Mount MCP server into an ASGI app with middleware

**Recommendation: (C) ASGI mounting with middleware.**

Using `server.run()` directly does not allow inserting auth, audit, rate limiting, or `/health` middleware. Instead, mount the MCP server as an ASGI application and wrap it with middleware layers. This is the pattern recommended by all three research models (A, G, O) and is how production MCP servers handle cross-cutting concerns.

**Architecture:** One shared tool registry, two thin entrypoints:

```python
from starlette.applications import Starlette
from starlette.routing import Mount

# Shared tool registry (same OntosFastMCP as v4.0)
server = create_server(cache)

# Stdio entrypoint (v4.0 behavior, unchanged)
if args.stdio:
    server.run(transport="stdio")

# Streamable HTTP entrypoint (v4.1)
if args.http:
    mcp_app = server.streamable_http_app()
    app = Starlette(routes=[Mount("/mcp", app=mcp_app)])
    app.add_middleware(BearerTokenAuthMiddleware, token=load_token())
    app.add_middleware(AuditLogMiddleware, log_path=audit_path)
    app.add_middleware(RateLimitMiddleware, config=rate_config)
    # Custom /health endpoint outside MCP
    app.add_route("/health", health_endpoint)
    uvicorn.run(app, host=bind, port=port)
```

**Why not `server.run()`:** It starts its own event loop and HTTP server with no middleware hooks. Auth, logging, and rate limiting would have to be implemented inside tool handlers, violating the v4.0 pattern where `_invoke_tool()` is transport-agnostic.

**Known SDK issues to mitigate:**
- SDK issue #1076: unbounded memory growth under continuous tool calls. Mitigate with 7-day uptime watchdog (launchd auto-restarts).
- SDK issue #756: `StreamableHTTPSessionManager._task` list grows in stateless mode. Same mitigation.
- FastMCP issue #514: SSE transport fails to shut down on signal after processing a request. Mitigate with explicit `asyncio.get_event_loop().add_signal_handler()` registration.

**Lifecycle management:** Use FastMCP's `lifespan` async context manager for startup/shutdown resource management (DB connections, background tasks):

```python
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    db = await init_portfolio_db()
    indexer = start_background_indexer(db)
    try:
        yield {"db": db, "indexer": indexer}
    finally:
        indexer.cancel()
        await db.close()
```

### D7: FTS Configuration

**Options:** (A) FTS5 with default tokenizer, (B) FTS5 with porter stemmer + unicode61, (C) External search library (Whoosh, etc.)

**Recommendation: (B) FTS5 with porter stemmer + unicode61.**

Porter stemming handles English morphology (searching "documenting" matches "documentation"). Unicode61 handles non-ASCII characters. Both are built into SQLite FTS5 -- no additional dependencies.

**Column weights:** Title 10x, concepts 3x, body 1x. Configured via FTS5 persistent rank: `INSERT INTO fts_content(fts_content, rank) VALUES('rank', 'bm25(10.0, 3.0, 1.0)')`. Results **must** be sorted by `ORDER BY rank` -- any other sort order forces a temp B-tree sort that is 10-50x slower. Add `prefix='2,3'` to the FTS5 table definition for prefix-search/autocomplete support. Run `INSERT INTO fts_content(fts_content) VALUES('optimize')` after bulk index operations.

### D8: Background Refresh Strategy

**Options:** (A) Refresh only on tool call (lazy), (B) Periodic background task, (C) Filesystem watcher (fsevents/inotify)

**Recommendation: (B) Periodic background task for portfolio mode. (A) Lazy refresh for single-workspace mode.**

In single-workspace stdio mode, the v4.0 behavior is preserved: check staleness on every tool call, rebuild if stale. This is correct and fast for 50-100 files.

In portfolio HTTP mode, checking 23 projects on every tool call is too expensive. A background task runs every 60 seconds (configurable), checking fingerprints and re-indexing only changed workspaces. Tool calls read from the portfolio DB, which is always "recent enough" (worst case: 60 seconds stale).

Filesystem watchers (fsevents) are more responsive but add complexity and platform dependencies. Deferred unless the 60-second polling proves insufficient.

### D9: Authority Transition from `.dev-hub`

**Options:** (A) Portfolio DB replaces `.dev-hub` immediately, (B) Portfolio DB and `.dev-hub` coexist permanently, (C) Gradual transition with validation period

**Recommendation: (C) Gradual transition.**

- **v4.1.0:** Portfolio DB is seeded from `projects.json` on first run. Both sources coexist. `project_registry()` reads from the portfolio DB. A `verify` subcommand compares the DB against `projects.json` and reports discrepancies.
- **v4.1.x (after validation):** If the portfolio DB is proven correct for all 23 projects, `.dev-hub/registry/projects.json` becomes a human-readable export generated from the DB on demand. `.dev-hub` authority transfers to Ontos.
- **Transition criterion:** Zero discrepancies between portfolio DB and `projects.json` for 2 consecutive weeks of usage.

---

## 10. Migration Path

### What Stays the Same

- **CLI is fully preserved.** Every existing command works identically.
- **`pip install ontos` (without extras) is unchanged.** No new dependencies for the base package.
- **All 8 v4.0 MCP tools work identically.** `workspace_overview`, `context_map`, `get_document`, `list_documents`, `export_graph`, `query`, `health`, `refresh` -- same inputs, same outputs.
- **Stdio transport works identically.** Existing MCP client configs (`claude_desktop_config.json`, `.cursor/mcp.json`) require no changes.
- **`.ontos.toml` is backward compatible.** New `[mcp.security]` section is optional.
- **Per-project document storage is unchanged.** Markdown files with YAML frontmatter.

### What Changes

- **New portfolio config:** `~/.config/ontos/portfolio.toml` for portfolio-level settings (scan roots, server config, bundle weights).
- **New database:** `~/.config/ontos/portfolio.db` created on first portfolio-mode run.
- **New auth token:** Bearer token stored in macOS Keychain on first HTTP-mode run (key: `ontos-mcp-token`).
- **New CLI flags:** `ontos serve --http`, `--port`, `--portfolio`, `--bind`.
- **New tools:** 7 new tools (3 portfolio + 4 write) added to the MCP surface.
- **Optional `workspace_id` parameter:** Added to all tools but ignored in single-workspace mode.

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

   # Start portfolio server
   ontos serve --http --portfolio
   ```

4. **(Optional) Enable write tools for a workspace:**
   Add to the workspace's `.ontos.toml`:
   ```toml
   [mcp.security]
   allow_write_tools = true
   ```

---

## 11. Acceptance Criteria

Ontos v4.1.0 is done when all of the following are true:

### Portfolio Tools

1. **`project_registry()` returns all 23 workspaces** with correct `status` classification (documented/partial/undocumented), accurate `doc_count` for documented projects, and valid `slug` values matching the slugification rule.

2. **`search("simhash")` returns relevant results** via FTS5 across all documented projects. Results include document ID, workspace slug, snippet with match highlighting, and BM25 score. Searching with `workspace_id` restricts results to that workspace.

3. **`get_context_bundle("canary-work")` returns a coherent context package** within the default 8192-token budget. The bundle includes the top-scored documents, respects the 5-signal ranking, and reports stale documents. Token estimate is within 20% of actual token count.

4. **`get_context_bundle()` on an undocumented project returns a structured error** directing the user to run `ontos init`.

5. **Portfolio index survives server restart.** After stopping and restarting `ontos serve --http --portfolio`, `project_registry()` returns results immediately (reads from `portfolio.db`, no full rescan).

### Write Tools

6. **`scaffold_document(type="atom", id="test_doc", title="Test")` creates a valid document** at the correct path with L0 frontmatter, and the document appears in subsequent `list_documents()` calls.

7. **`rename_document(document_id="old_id", new_id="new_id")` renames and updates references.** All documents that previously referenced `old_id` now reference `new_id`. The response includes the count and list of updated files.

8. **`log_session(summary="Test session")` creates a valid session log** with correct date-stamped filename and frontmatter.

9. **`promote_document(document_id="test_doc", target_level="L2")` fails gracefully** when L2 requirements are not met, returning `success: false` with specific `validation_warnings`.

### Transport and Security

10. **`ontos serve --http` starts a Streamable HTTP server** on `http://127.0.0.1:9400/mcp` that responds to MCP tool calls from an HTTP client. Clients POST JSON-RPC messages; server responds with JSON or opens an SSE stream per-response.

11. **Bearer token authentication works.** Requests without a valid `Authorization: Bearer <token>` header receive a 401 response. The token is auto-generated via `secrets.token_urlsafe(32)` on first run and stored in macOS Keychain. DNS rebinding protection rejects requests with non-localhost `Host` headers.

12. **Audit log captures tool calls.** After calling tools via HTTP, `~/.config/ontos/audit.log` contains entries with timestamp, tool name, and auth status.

13. **Write tools are blocked by default on HTTP.** Calling `scaffold_document()` over HTTP without `allow_write_tools = true` returns an authorization error.

### Backward Compatibility

14. **All 8 v4.0 tools work identically in stdio mode.** Existing test suite passes without modification.

15. **`pip install ontos` (without `[mcp]`) still works on Python 3.9+.** No new base dependencies.

16. **Existing MCP client configurations require no changes.** Stdio-mode `ontos serve` with no flags behaves identically to v4.0.

### Portfolio Index

17. **Incremental refresh re-indexes only changed workspaces.** After modifying a document in one workspace, only that workspace is re-indexed on the next background refresh cycle. Other workspaces' data is untouched.

18. **Portfolio DB can be deleted and rebuilt.** Deleting `portfolio.db` and restarting the server reconstructs the full index within 5 seconds for 23 projects.

---

## 12. Open Questions

**Q1: Portfolio DB schema versioning.** Should `portfolio.db` include a `schema_version` table for future migrations? **Recommendation:** Yes. Add a `meta` table with `key TEXT PRIMARY KEY, value TEXT`. Set `schema_version = "1"` on creation. Check on startup; if mismatch, rebuild from scratch (the DB is a rebuildable cache).

**Q2: Token estimation accuracy.** The character heuristic (1 token per ~4 chars) is fast but imprecise for code-heavy documents. Should v4.1 include tiktoken as an optional dependency? **Recommendation:** Defer. Measure accuracy during v4.1 beta. If bundles consistently miss their budget by >20%, add `tiktoken` as an optional extra (`pip install ontos[mcp,tiktoken]`).

**Q3: Cross-workspace dependencies.** The `edges` table supports `from_workspace != to_workspace`, but no Ontos documents currently declare cross-workspace dependencies. Should v4.1 support this? **Recommendation:** Schema supports it, but the UI and validation are deferred. No cross-workspace `depends_on` in v4.1 frontmatter. The table structure is forward-compatible.

**Q4: MCP Resources and Prompts.** v4.0 uses Tools only. Should v4.1 also expose MCP Resources (for lazy document loading) and Prompts (for guided workflows)? **Recommendation:** Defer to v4.2. Tools are sufficient for all defined consumer workflows. Resources add complexity (URI schemes, subscription semantics) without clear consumer demand.

**Q5: Log retention in bundles.** How many session logs should be included in context bundles? Count-based (N most recent) vs. time-window (last 7 days)? **Recommendation:** Time-window with a count cap. Include logs from the last 14 days, capped at 5 most recent. This captures active work without flooding the bundle with old sessions. Configurable in `portfolio.toml`.

**Q6: Concurrent write safety.** If two agents call `rename_document()` on the same document simultaneously, what happens? **Recommendation:** Write tools acquire a per-workspace file lock (`<workspace>/.ontos.lock`). Second caller receives a `BUSY` error with retry guidance. Lock timeout: 10 seconds.

**Q7: Portfolio server as a system service.** Should v4.1 include a launchd plist (macOS) or systemd unit for running the portfolio server as a persistent daemon? **Recommendation:** Include a `ontos service install` command that generates and installs the appropriate service file. This is a convenience, not a blocker.

---

## 13. Deep Research Prompt

The following prompt is designed to be run in a separate deep-research session. It is self-contained and does not require prior conversation context. The findings should be used to validate and refine the architectural decisions in this proposal before implementation begins.

---

### Research Prompt: MCP Ecosystem Best Practices for Ontos v4.1

**Context:** Ontos is a local-first documentation management system that exposes a knowledge graph via the Model Context Protocol (MCP). Version 4.0 shipped as a thin stdio MCP bridge with 8 read-only tools wrapping single-project CLI capabilities (context map, document retrieval, graph export, health). Version 4.1 will extend this into a portfolio-level server with cross-project search, write tools, Streamable HTTP transport, and a context bundle algorithm.

The codebase is Python 3.9+ (MCP requires 3.10+), uses FastMCP (a wrapper around the official `mcp` Python SDK), Pydantic for response schemas, and SQLite (stdlib) for the planned portfolio index. The deployment target is a single Mac Mini serving 23 projects with ~400 total documents.

**Research Objective:** Validate the v4.1 design decisions against current MCP ecosystem practices, identify risks, and surface alternatives we may have missed. Each research area should produce actionable findings -- not general overviews, but specific patterns, anti-patterns, and configuration recommendations.

---

#### Area 1: MCP SDK and Transport State (April 2026)

1. What is the current state of the Python MCP SDK's Streamable HTTP transport? Is it production-stable or still experimental? Are there known issues with long-running SSE connections (memory leaks, reconnection handling)?
2. How does FastMCP's `server.run(transport="sse")` compare to using the official SDK's HTTP transport directly? Are there feature gaps (auth middleware, request logging, graceful shutdown)?
3. What is the client compatibility matrix for Streamable HTTP transport? Specifically: does Claude Code connect to Streamable HTTP MCP servers? Does Cursor? Does the official MCP Inspector?
4. Has the MCP specification stabilized its auth model? What is the current state of the MCP auth specification -- is bearer token the recommended pattern, or has OAuth/PKCE been adopted?
5. Is there a standard MCP pattern for dual-transport servers (stdio + Streamable HTTP from the same codebase)?

#### Area 2: Write Tool Patterns in Production MCP Servers

1. Survey 5-10 production MCP servers that expose write tools (file creation, modification, deletion). How do they handle safety? Patterns to look for: dry-run modes, confirmation flows, undo/rollback, idempotency keys.
2. What are the MCP `ToolAnnotations` conventions for write tools? How do production servers set `readOnlyHint`, `destructiveHint`, `idempotentHint`? Are there de facto standards emerging?
3. How do MCP servers handle write tool errors? Do they return structured error objects with recovery guidance, or just error strings?
4. Is there a pattern for write tools that modify multiple files atomically (like `rename_document` updating references across a workspace)?

#### Area 3: SQLite as a Portfolio Index

1. Best practices for SQLite in long-running Python processes: WAL mode configuration, connection pooling (or lack thereof), VACUUM scheduling, database size monitoring.
2. FTS5 configuration for a ~400 document corpus: tokenizer selection (porter vs. trigram), column weight syntax, snippet extraction performance, BM25 tuning.
3. How do production applications handle SQLite concurrent access from multiple processes (e.g., a background indexer + request handler)? What `PRAGMA` settings are recommended?
4. SQLite performance at the target scale (400-500 documents, 23 projects, FTS5 with porter stemming): are there benchmarks or case studies? Expected query latency for `search()` and `project_registry()`?
5. Schema migration patterns for SQLite databases that are "rebuildable caches" -- is a simple `schema_version` + rebuild-from-scratch sufficient, or do production systems use incremental migrations even for cache databases?

#### Area 4: Context Bundle / RAG-Free Retrieval

1. Academic and industry approaches to deterministic document ranking without vector search. Specifically: graph centrality metrics (PageRank, in-degree, betweenness) applied to documentation graphs, TF-IDF on structured metadata, and hybrid scoring functions.
2. Token-budget packing algorithms: how do existing LLM context assembly systems decide what to include when space is limited? Look for: greedy knapsack, priority queue, type-quota approaches.
3. Is there prior art on "context bundles" or "context packages" in the MCP ecosystem? Do any MCP servers implement a scoring/ranking/bundling tool?
4. What evaluation metrics are used for context bundle quality? Precision@k, recall@k, downstream task performance, user satisfaction scores?
5. How do existing systems handle the "always include" constraint (e.g., "kernel documents are always included regardless of score")? Are there patterns for mandatory inclusion with budget reservation?

#### Area 5: Multi-Workspace MCP Server Patterns

1. How do existing MCP servers handle multi-project or multi-workspace routing? Single process serving multiple workspaces vs. one process per workspace behind a proxy?
2. What is the recommended pattern for MCP tool parameters that optionally scope to a workspace? Is `workspace_id?: str` the standard, or do servers use resource URIs, namespaced tool names, or other patterns?
3. How do multi-workspace MCP servers handle workspace discovery? Do clients call a discovery tool, or does the server advertise available workspaces in its initialization response?
4. What happens when a multi-workspace MCP server can't find the requested workspace? Best practices for error responses that guide the client to valid options.

#### Area 6: Security for Local MCP Servers

1. Current state of MCP auth specification: has bearer token been formally specified, or is it a community convention? Is there an official recommendation for local-only servers?
2. How do production local MCP servers implement authentication? Bearer tokens, Unix domain sockets, OS-level keychain integration?
3. Audit logging patterns for MCP servers: what fields are logged, what format is used, how is log rotation handled?
4. How do MCP servers restrict which tools are available to which clients? Is there a standard authorization model beyond "all tools or no tools"?
5. What are the known attack vectors for localhost-bound MCP servers? (DNS rebinding, browser-based SSRF, etc.) What mitigations are standard?

#### Area 7: Operational Patterns for Long-Running MCP Servers

1. How do production MCP servers handle graceful shutdown (SIGTERM, SIGINT)? Is there a standard shutdown handshake in the MCP protocol?
2. Health check patterns: do MCP servers expose health endpoints via the MCP protocol (a `health()` tool), via HTTP `/health`, or both?
3. Service management: do any MCP servers ship with launchd plists, systemd units, or Docker configurations? What's the recommended deployment pattern for persistent MCP servers on macOS?
4. Memory management for long-running MCP servers with in-memory caches: garbage collection, memory limits, cache eviction strategies.
5. How do MCP servers handle version upgrades without client disruption? Is there a standard reconnection or version negotiation pattern?

---

**Output Format:** For each area, provide:
1. **Key findings** -- 3-5 specific, actionable findings with citations or source references
2. **Risks** -- any risks to the v4.1 design that the findings surface
3. **Recommendations** -- specific changes or confirmations to the v4.1 proposal

**Scale:** This is a ~400 document, 23 project, single-machine deployment. Do not optimize for distributed systems or enterprise scale. Focus on patterns that work well at this scale with minimal operational overhead.
