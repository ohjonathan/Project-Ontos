# Ontos v4.0 MCP Proposal

**Date:** 2026-04-04
**Revised:** 2026-04-04 (v7 — pick one story: retrieval-first P0, graph-query P1)
**Author:** Claude (synthesized from prior research and board decisions)
**Status:** PROPOSAL — requires review and decision by Johnny
**Audience:** Johnny (project owner), LLMs reviewing for correctness and gaps

**Revision notes (v7):** Seventh draft, resolving the "two stories" problem. The proposal now cleanly separates P0 (retrieval-first, wrapping existing CLI outputs) from P1 (new graph-query APIs). P0 = `context_map(compact?)` calling `generate_context_map()` and returning the proven Tier 1/2/3 markdown, `get_document()`, `list_documents()`. P1 = `export_graph()` (full JSON dump via `_snapshot_to_json()`), `query(entity_id)` (net-new single-entity lookup), `health()`, `refresh()`. The thin bridge story is now coherent: P0 wraps existing outputs; P1 is honestly new.

**Prior revisions:** v6: renamed context_map→export_graph, acknowledged query is new, kind→type. v5: stale map-json ref, validation gap, "no new layer" overclaim. v4: fingerprint, P0/P1, strategic bet. v3: CLI Paradox, file-mtime, implicit workspace. v2: consumer flip, scope split. v1: initial.

---

## 1. What Is This

Ontos v4.0 is a phased initiative to expose the Ontos knowledge graph via the Model Context Protocol (MCP). **v4.0.0** is a thin MCP bridge: it wraps existing single-project Ontos capabilities as MCP tools so that Claude Code, Cursor, and other MCP-compatible clients can query a project's documentation graph programmatically instead of reading static files. It adds no new data structures, no new storage layer, and no cross-project capabilities — it exposes what Ontos v3.4.0 already does through a protocol that agents can call as tools. **v4.1** (planned, not specified here) extends the MCP server with a portfolio-level index, cross-project search, and a context bundle algorithm for multi-workspace orchestration. The CLI remains fully functional in both phases; MCP is additive.

---

## 2. Why Now

**An honest framing: this is a strategic bet, not a burning pain-point.** Claude Code can already run `ontos query --json` via shell. The existing `AGENTS.md` + `ontos export data --json` workflow is functional. v4.0.0 does not fix a broken workflow — it bets that MCP will become the standard interface between agents and developer tools, and positions Ontos to be accessible through that standard before it matters.

The bet is grounded in three observations: (1) Claude Code, Cursor, Windsurf, Cline, and every major IDE agent framework now support MCP servers natively — this is where tool integration is converging; (2) shipping an MCP server makes Ontos accessible to all of them without per-client integration work, whereas CLI shelling only serves tools that can execute shell commands; (3) the architecture was designed for this (see below), so the implementation cost is low relative to the positioning value.

MCP also provides concrete capabilities that CLI shelling cannot: **schema auto-discovery** (agents see available tools and their typed signatures via `tools/list`, without needing `AGENTS.md` or prompt instructions), **structured typed responses** (no text parsing or exit code interpretation), and **persistent process state** (the server holds a cached snapshot across calls, avoiding cold-start rebuilds on every CLI invocation).

If this bet is wrong — if MCP doesn't converge as expected, or if Ontos's user base remains Claude Code-only — the cost is a small `ontos/mcp/` package that wraps existing capabilities. The CLI remains fully functional regardless.

**The architecture was designed for this.** The v3.0 architecture explicitly prepared for MCP. The core/IO separation (documented in `.ontos-internal/analysis/Ontos-Technical-Architecture-Map-Codex.md`, Section 11) reserves `ontos/mcp/` as an extension point. All CLI commands emit structured JSON via `--json` flags. The graph engine (`ontos/core/graph.py`) builds dependency graphs with cycle detection and depth calculation. The `ontos export data` command produces a complete graph export in `ontos-export-v1` schema. The plumbing exists; what's missing is the protocol layer.

**The MCP ecosystem has matured.** When the 5-LLM review board assessed MCP in January 2026 (`.ontos-internal/archive/v3.0-planning/V3.0-Board-Review-Analysis.md`), they noted "installation UX is bad," "security model inadequate," and "Python is second-class." Three months later: the official Python MCP SDK is stable, Claude Code and Cursor both support MCP servers natively, and the ecosystem has crossed critical adoption thresholds. The "wait for maturity" rationale from the board's deferral has been satisfied.

**JohnnyOS will need this, but it doesn't drive the timeline.** The Mac Mini orchestrator is planned but has no concrete artifacts in the workspace today. When JohnnyOS is built, it will need cross-project capabilities (portfolio registry, context bundles, cross-repo search) — those are v4.1 scope. v4.0.0 is justified by the MCP ecosystem case, with Claude Code as the first and most frequent client.

**Competitive pressure is real but secondary.** CTX, Claude Code memory, and Cursor context are shipping MCP integrations. Ontos's differentiation is its deterministic, graph-based approach. But differentiation only matters if the tool is accessible. An MCP server makes Ontos accessible to every MCP-compatible client without custom integration.

---

## 3. Current State

### What Ontos v3.4.0 Does

Ontos is a Python CLI (`pip install ontos`) that manages documentation as a knowledge graph. It:

- **Scans** markdown files with YAML frontmatter, validating against a 5-type ontology (kernel, strategy, product, atom, log) with enforced dependency direction rules
- **Builds** a dependency graph with cycle detection, orphan detection, and depth calculation (`ontos/core/graph.py`)
- **Generates** context maps in tiered format (Tier 1: ~2k tokens essential context; Tier 2: full document index; Tier 3: graph details, validation, staleness)
- **Validates** at three curation levels (L0 scaffold, L1 stub, L2 full) with progressive strictness
- **Tracks** staleness via `describes`/`describes_verified` fields that flag docs whose underlying code has changed
- **Exports** the full graph as JSON (`ontos-export-v1` schema) with content hashing, deterministic mode, and filtering by type/status/concept

CLI commands: `map`, `log`, `doctor`, `agents`, `query`, `hook`, `verify`, `migrate`, `consolidate`, `promote`, `scaffold`, `stub`, `init`, `env`, `link-check`, `rename`, `maintain`, `export`. All support `--json` output.

### What Ontos v3.4.0 Does NOT Do

- No programmatic API — agents must read files or shell out to CLI commands
- No cross-project queries — every command operates within a single project root
- No full-text search — `ontos query` supports structured queries (by ID, dependency, staleness) but not free-text
- No persistent index — the graph is rebuilt from the filesystem on every command invocation
- No subscription or notification model — agents cannot be notified when context changes

### The 23-Project Portfolio

The `~/Dev/` directory contains 23 projects tracked by `.dev-hub/registry/projects.json`:

| Category | Count | Projects (examples) |
|----------|-------|---------------------|
| **Documented** (Ontos context map + README) | 10 | canary.work (46 docs), role-evaluator-bot (76 docs), finance-engine-2.0 (55 docs), Ontos-dev (50 docs), folio.love (50 docs) |
| **Partial** (README only or context map only) | 5 | Vibing, ohjonathan.com, NPOLabDev |
| **Undocumented** (neither) | 8 | Career, agent-skills, claude-code-monitoring, engineering-strategy, strategy-eng |

Total tracked documents across documented projects: ~396. 5-6 projects are actively developed.

**Cross-project orchestration today** is handled by `.dev-hub/` — a manually-maintained, read-only index (`registry/projects.json`) with no automated refresh, no search, and no programmatic access. This is a ceiling that v4.1 will address. v4.0.0 does not attempt to solve the cross-project problem.

### Architectural Readiness

**In place:**
- Core/IO separation validated across v3.0-v3.4. The core layer (~3,812 LOC, 16 files) is pure logic with zero external dependencies.
- Extension point reserved at `ontos/mcp/` (architectural map lists it; directory not yet created on disk).
- JSON output on all CLI commands via `--json` flag and `OutputHandler` pattern.
- `ontos-export-v1` JSON schema with content hashing and deterministic output.
- Performance baselines established: CLI startup <100ms, context map generation <500ms (100 docs), <2s (100-500 docs).

**Not in place:**
- No `ontos/mcp/` directory or stub files exist on disk.
- No `[mcp]` extra in `pyproject.toml` (planned: `pip install ontos[mcp]` with pydantic dependency).
- No portfolio-level index beyond the manual `projects.json`.
- No full-text search capability.
- No MCP security model defined.

---

## 4. Consumer Requirements

### Consumer 1: Claude Code / Codex CLI / Cursor / MCP-Compatible Clients (Primary — v4.0.0)

**What it is:** Any MCP-compatible agent client working on a specific project. Claude Code is the most frequent client today; Cursor, Windsurf, Cline, and future MCP clients are also served. The LLM needs project context to be effective.

**How it connects:** MCP client in the IDE or terminal, connected via stdio. Human-in-the-loop — responses must be <1s for cached queries.

**What it replaces:** Today, the agent reads `Ontos_Context_Map.md` (up to 87KB) and `AGENTS.md` at session start, or shells out to `ontos query --json`. With MCP, the agent discovers available tools automatically via `tools/list`, calls them with typed inputs, and receives structured responses — no documentation, no parsing, no cold-start CLI invocation per query.

**Tools it needs (v4.0.0 — single-project scope):**

All tools operate on the server's configured workspace. No `workspace_id` parameter is needed — the workspace is implicit (see D9).

Tools are split into two tiers with a clear design rationale:
- **P0 (retrieval-first):** Wrap existing CLI outputs. These are the thin bridge — they expose validated, production-proven capabilities via MCP.
- **P1 (new capabilities):** Add graph-query APIs that don't exist in the current CLI. These are honest extensions, not CLI wrappers. Included in v4.0.0 because the underlying data is in the snapshot and the adapter code is small, but droppable if the MVP needs to be smaller.

| Priority | Tool | Input | Output Shape | Wraps |
|----------|------|-------|-------------|-------|
| **P0** | `context_map(compact?)` | `compact?: str` (optional: `"basic"`, `"rich"`, `"tiered"`) | Markdown string: the same Tier 1/2/3 context map that `ontos map` writes to `Ontos_Context_Map.md`, plus a `validation` object with errors/warnings | `generate_context_map()` in `map.py` — existing function, proven output |
| **P0** | `get_document(document_id)` | `document_id: str` or `path: str` | `{id, type, status, frontmatter, content, metadata: {content_hash, word_count, depended_by}}` | Reads from `snapshot.documents[id]` — new adapter (~50 lines) but data is in existing structures |
| **P0** | `list_documents(type?, status?)` | Optional filters | `[{id, type, status, path}]` | Filters `snapshot.documents` — thin adapter |
| **P1** | `export_graph()` | None | `ontos-export-v1` JSON schema: `{summary, documents, graph: {nodes, edges}, validation}` | `_snapshot_to_json()` in `export_data.py` — existing serializer, extended with validation field |
| **P1** | `query(entity_id)` | `entity_id: str` | `{id, type, status, depends_on, depended_by, depth, content_hash}` | **Net-new adapter.** Current `ontos query` CLI only supports `--depends-on`/`--depended-by`/`--concept`/`--stale`/`--health`/`--list-ids`, not single-entity lookup. Data is in `snapshot.documents[id]` + `snapshot.graph.reverse_edges[id]`; adapter is ~50 lines. |
| **P1** | `health()` | None | `{server_uptime, workspace, doc_count, last_indexed, ontos_version}` | New — no CLI equivalent |
| **P1** | `refresh()` | None | `{refreshed: true, doc_count, duration_ms}` | New — triggers cache rebuild |

**Why `context_map()` is P0 and `export_graph()` is P1:** The primary orientation use case is an agent joining a session and asking "what is this project?" The Tier 1 context map (~2k tokens) answers that — it's the proven, token-capped summary with key documents, recent activity, and critical paths. The full `ontos-export-v1` JSON dump is useful for structured graph queries, but it's not what an agent needs for orientation. By making `context_map()` the P0 entry point, the thin bridge story is coherent: P0 wraps existing CLI outputs; P1 adds new structured APIs.

**What it does NOT need from Ontos:**
- Cross-project queries (works on one project at a time)
- Context bundles (the agent assembles its own context from the tools above)
- Full-text search (uses `query` for structured lookups; grep/glob for text search)
- Task state, runtime state, prompt templates

### Consumer 2: Vibing MCP (Secondary — v4.0.0)

**What it is:** A separate MCP server for spec generation that uses Ontos as a context source during its own development.

**How it connects:** MCP client during development sessions, connected via stdio. Same interaction pattern as Consumer 1.

**Tools it needs:** Same as Consumer 1. No special requirements.

### Consumer 3: JohnnyOS Orchestrator (Future — v4.1)

**What it is:** A planned daemon running on a Mac Mini that routes incoming tasks to workspace-specific supervisors. No concrete JohnnyOS artifact exists in the workspace today.

**How it connects:** MCP client calling Ontos MCP server over stdio (initially) or local socket (when HTTP/SSE transport is added).

**Tools it will need (v4.1 scope — cross-project):**

| Tool | Input | Output Shape | Frequency | Cacheable |
|------|-------|-------------|-----------|-----------|
| `project_registry()` | None | `{project_count, projects: [{slug, status, doc_count, last_updated, tags}], summary}` | 20-50x/day | Yes (TTL-based) |
| `get_context_bundle(workspace_id?)` | `workspace_id?: str` (optional, defaults to primary) | `{workspace_id, context_text, token_estimate, warnings, stale_docs}` | 5-20x/day per workspace | Yes (mtime-invalidated) |
| `search(query_string, workspace_id?)` | `query_string: str`, optional `workspace_id?: str` | `[{doc_id, workspace, type, path, snippet, matched_fields}]` | Ad-hoc | No |

Plus all v4.0.0 tools.

**What it does NOT need from Ontos:**
- Task state (blocked PRs, review queues) — owned by JohnnyOS Workflow Ledger
- Runtime state (service health, cron status) — owned by JohnnyOS Runtime Registry
- Raw activity (session transcripts, event streams) — owned by JohnnyOS Artifact Store
- Prompt templates (playbook content, reviewer instructions) — owned by Vibing MCP

---

## 5. What Ontos v4.0 Must Own

### v4.0.0 Scope (Single-Project MCP Bridge)

**Document Management** — the 5-type document ontology (kernel, strategy, product, atom, log) with YAML frontmatter parsing, curation levels (L0/L1/L2), status lifecycle, and content hashing. Exposed via `get_document`, `list_documents`, and `query` tools.

**Dependency Graph** — structural relationships between documents: `depends_on`, `impacts`, `describes` edges. Cycle detection, orphan detection, depth calculation, reverse edge traversal. Exposed via `query` (per-entity) and `export_graph` (full graph).

**Context Map Generation (P0)** — the `context_map` tool calls `generate_context_map()` from `ontos/commands/map.py` and returns the resulting markdown string — the same Tier 1/2/3 content that `ontos map` writes to `Ontos_Context_Map.md`. This is the proven, production-validated orientation artifact. The optional `compact` parameter maps to existing compact modes (`basic`, `rich`, `tiered`). The response also includes the `ValidationResult` from `generate_context_map()` as a structured `validation` object.

**Graph Export (P1)** — the `export_graph` tool calls `create_snapshot()` and formats the response using `_snapshot_to_json()` from `ontos/commands/export_data.py` — the same pipeline that `ontos export data` uses to produce the `ontos-export-v1` schema. This is a full structured JSON dump for agents that need graph data programmatically, not the orientation artifact.

**Staleness Detection** — `describes`/`describes_verified` field tracking, content hash comparison, stale document warnings. The `create_snapshot()` function in `ontos/io/snapshot.py` already computes a `validation_result` (via `ValidationOrchestrator`) that includes staleness warnings. However, the existing `_snapshot_to_json()` serializer in `export_data.py` does not include this validation result in its output — it only emits parse warnings from the scan phase. **Phase A must extend the serializer** to include `validation_result.errors` and `validation_result.warnings` in the `export_graph()` response, likely as a top-level `validation` field alongside the existing `summary`, `documents`, and `graph` fields. This is a small addition (~20 lines) to the existing pipeline, not a new serialization layer.

**Workspace Identity** — see Section 8, D9 for the formal definition. In v4.0.0, the workspace is implicit — determined by the server's configured project root. No `workspace_id` parameter on tool inputs. The agent discovers the workspace via `health()` or via tool descriptions that dynamically include the workspace name.

### v4.1 Scope (Portfolio Authority — Planned, Not Specified Here)

The following capabilities are deferred to v4.1. They are listed here to show the intended evolution, not to define their implementation.

**Portfolio-Level Index** — a persistent, queryable index spanning all workspaces in `~/Dev/`. Requires a storage backend (SQLite is the likely candidate — see Section 7), a scan strategy, and a refresh mechanism. Exposed via `project_registry()`.

**Context Bundle Generation** — a scoring algorithm that assembles right-sized context packages from a workspace's document graph. The v1 proposal described a 5-signal scoring function (type rank, in-degree centrality, status freshness, recency, curation level). This algorithm is the highest-value and least-proven component. It must be validated against real usage data before committing to a specific implementation. See Section 8, D5 for the deferral rationale.

**Cross-Project Search** — deterministic full-text search across the portfolio via SQLite FTS5. Requires the portfolio index to exist first. Exposed via `search()`.

**Undocumented Project Handling** — thin metadata entries for projects without Ontos coverage (the 13 partial/undocumented projects). Deferred because it depends on the portfolio index and adds scope without serving v4.0.0's primary consumer.

---

## 6. What Ontos v4.0 Must NOT Own

| Excluded Responsibility | Owner | Rationale |
|------------------------|-------|-----------|
| **Task state** (blocked features, PR reviews, sprint status) | JohnnyOS Workflow Ledger | Task lifecycle is JohnnyOS's domain. Ontos tracks documentation, not work items. |
| **Runtime state** (service health, cron job status, deployment state) | JohnnyOS Runtime Registry | Ontos has no visibility into whether services are running or deployed. |
| **Raw activity** (session transcripts, chat logs, event streams) | JohnnyOS Artifact Store | Ontos captures structured session logs (`ontos log`), not raw transcripts. |
| **Prompt templates** (playbook content, reviewer instructions) | Vibing MCP / consumer-specific | Ontos exposes context; consumers decide how to prompt with it. |
| **Vector / semantic search** | Excluded entirely | Deterministic retrieval only. Graph traversal and (in v4.1) FTS. No stochastic failure modes. |
| **Code intelligence** (AST parsing, symbol resolution) | IDE / language servers | Ontos indexes documentation about code, not the code itself. |

---

## 7. The Cross-Project Indexing Problem

> **Scope note:** This section describes architecture for **v4.1**, not v4.0.0. It is included because the cross-project problem shaped the original proposal and must be understood to draw the v4.0.0/v4.1 boundary correctly.

### Why This Is Architecturally Distinct from v4.0.0

Ontos v3.x is fundamentally single-project. Every command takes a `project_root` path and operates within it. The graph engine builds a `DependencyGraph` from one project's documents. v4.0.0 preserves this model — the MCP server serves one workspace at a time, just like the CLI.

The cross-project capabilities that JohnnyOS needs (`project_registry()`, cross-repo search, `get_context_bundle(workspace_id)` with portfolio-aware routing) require a **portfolio-level index** that does not exist and cannot be built by "wrapping CLI commands in MCP."

### What a Portfolio-Level Index Requires

1. **A persistent store** — the index must survive process restarts. Rebuilding from scratch means scanning 23 project directories and parsing ~396 documents.
2. **A scan strategy** — detection of which directories are projects, how to extract metadata, what constitutes "coverage."
3. **A refresh mechanism** — detecting when project state has changed. See Section 8, D4 for invalidation semantics.
4. **A query interface** — list all projects, filter by status/tags, full-text search, look up a workspace by slug.

### Storage Recommendation: SQLite (for v4.1)

Keep per-project storage as filesystem (the current model). Add a single SQLite database (`~/.config/ontos/portfolio.db`) for the portfolio-level index only.

**Why SQLite:** `sqlite3` is Python stdlib (zero new dependencies). Supports concurrent readers via WAL mode. FTS5 provides full-text search without additional libraries. Makes `project_registry()` a constant-time indexed query instead of a filesystem scan.

**Why NOT full SQLite for per-project data:** The filesystem is the authoritative source for individual projects. Duplicating it in SQLite creates a synchronization problem. Per-project graph builds are already fast (<500ms for 100 docs).

**SQLite's role:** The portfolio database is a **rebuildable cache**, not a source of truth. It can be deleted and reconstructed from disk at any time. `.dev-hub/registry/projects.json` remains the human-readable reference during the v4.0.0 period.

### Authority Transition: `.dev-hub` During Migration

- **v4.0.0:** `.dev-hub/registry/projects.json` remains the authoritative cross-project index. Ontos does not read or write it. Cross-project queries are not in scope.
- **v4.1:** The portfolio database (`~/.config/ontos/portfolio.db`) becomes the authoritative cross-project index, seeded from `projects.json` on first run. `projects.json` becomes a human-readable export, regenerated from the database on demand.
- **Transition criterion:** `.dev-hub` authority transfers to Ontos only when v4.1 ships and the portfolio database is proven correct against `projects.json` for all 23 projects.

---

## 8. Key Decisions

### D1: MCP Transport

**Options:** (A) stdio only, (B) HTTP/SSE only, (C) stdio first, HTTP/SSE in v4.1+

**Recommendation: (C) stdio first, HTTP/SSE deferred.**

All v4.0.0 consumers (Claude Code, Vibing) connect via stdio — it's the standard MCP transport for local tools. Claude Code and Cursor connect to MCP servers via stdio natively. No port management, no auth needed.

HTTP/SSE adds complexity (port binding, auth tokens, CORS) that only matters for process-to-process communication. JohnnyOS is the consumer that needs it, and JohnnyOS is a v4.1 concern. Even then, JohnnyOS can initially connect via stdio by spawning Ontos as a child process.

The prior board decision (`.ontos-internal/archive/v3.0-planning/V3.0-Board-Review-Analysis.md`) recommended both transports. This recommendation stands for the full v4.x lifecycle; the question is sequencing.

**Implication:** `ontos serve` launches an stdio MCP server. HTTP/SSE is a v4.1+ feature.

### D2: Manifest Format

**Options:** (A) Adopt `.johnny-os.yaml`, (B) Extend `.ontos.toml` with `[mcp]` section, (C) New `ontos-mcp.toml`

**Recommendation: (B) Extend `.ontos.toml`.**

`.ontos.toml` already exists in 6+ projects. It is the canonical configuration file, parsed by `ontos/io/config.py`. Adding an `[mcp]` section is minimal-friction.

Adopting `.johnny-os.yaml` creates coupling that contradicts the architectural independence constraint. The consumer brief states: "Independent service with own repo, versioning, process lifecycle" and "Must survive JohnnyOS being down."

**v4.0.0 config surface:**
```toml
[mcp]
# No required fields. Presence of section enables MCP features.
# All values below are optional with sensible defaults.
```

Portfolio-level configuration (`scan_roots`, etc.) is deferred to v4.1 since v4.0.0 operates on a single workspace.

**Implication:** Ontos reads `.johnny-os.yaml` only as a data source (extracting metadata for undocumented projects in v4.1). It never treats it as its own configuration.

### D3: Storage Backend

**Options:** (A) Pure filesystem, (B) SQLite for portfolio index + filesystem for per-project, (C) Full SQLite

**Recommendation: (A) Pure filesystem for v4.0.0. (B) for v4.1.**

v4.0.0 is a single-project MCP bridge. It reads from the same filesystem the CLI reads, using the same `create_snapshot()` path. No persistent store is needed — the in-memory snapshot is rebuilt on server startup and invalidated via mtime checks (see D4).

SQLite is deferred to v4.1 because: (1) v4.0.0 has no cross-project queries that require an index; (2) introducing SQLite in a "thin bridge" release adds architecture and failure modes that the primary consumer (Claude Code) doesn't need; (3) the filesystem-only approach can be shipped and validated faster.

**Implication:** v4.0.0 adds zero new storage infrastructure. The MCP server holds an in-memory cache of the current workspace's snapshot, rebuilt from disk when stale.

### D4: Indexing and Invalidation Strategy

**Options:** (A) Full rescan on startup, (B) Filesystem watcher, (C) Startup scan + mtime-based cache invalidation

**Recommendation: (C) Startup scan + file-mtime cache invalidation.**

**Startup behavior:** On `ontos serve`, the server calls `create_snapshot()` for the configured workspace, building the in-memory document graph. This is the cold-start cost (~500ms for typical projects). The snapshot is the single source of truth for all tool responses.

**Invalidation semantics (corrected from v2):**

> **v2 flaw acknowledged:** The v2 proposal checked `os.stat(docs_dir).st_mtime` (directory mtime). On POSIX systems, directory `st_mtime` only updates when directory entries are added or removed — NOT when existing file content changes. This means editing a document mid-session would be silently missed. The mechanism below corrects this.

The server tracks a **snapshot fingerprint**: a set of `(relative_path, st_mtime_ns, st_size)` tuples for every tracked document file, computed at snapshot build time. Using nanosecond-resolution mtime (`st_mtime_ns`) and file size together makes false negatives vanishingly unlikely on modern filesystems (APFS, ext4).

**Exact staleness check procedure (runs on every tool call):**

1. Walk the workspace's configured doc paths (same scan logic as `create_snapshot()`).
2. For each file found, record `(relative_path, os.stat(f).st_mtime_ns, os.stat(f).st_size)`.
3. Compare the resulting set against the stored fingerprint.
4. If identical: serve from cache.
5. If different (any file added, removed, renamed, or modified): rebuild snapshot, replace fingerprint, serve fresh data.

**What this catches:**
- **Content edit** (most common): file's `st_mtime_ns` changes. Detected.
- **New file created**: new path appears in the set. Detected.
- **File deleted**: path disappears from the set. Detected.
- **File renamed** (`mv old.md new.md`): old path disappears, new path appears. Detected.
- **Atomic replace** (write to temp, `os.rename()` over original): new file gets new `st_mtime_ns`. Detected.

**Theoretical edge case:** A file replaced with identical `st_mtime_ns` AND identical `st_size` would be missed. On APFS (nanosecond mtime resolution), this requires a replacement to complete within the same nanosecond with identical byte count. This is not a practical concern.

**Cost:** For 50-100 files, the walk is ~50-100 `stat()` syscalls. On macOS APFS this completes in <1ms — negligible compared to the tool response itself.

**Why not directory mtime:** As noted above, directory `st_mtime` only updates when entries are added or removed, not when existing file content changes. The file-walk approach is correct for all modification types.

**Concurrent rebuild protection:** The MCP server runs on an asyncio event loop. Although stdio is inherently sequential, the `mcp` SDK may dispatch tool calls concurrently. To prevent duplicate rebuilds when two calls detect staleness simultaneously, the rebuild is guarded by an `asyncio.Lock`. The first caller acquires the lock and rebuilds; any concurrent callers wait for the lock and then serve from the freshly rebuilt cache.

**Concurrent access model (single-process, single-workspace):**

v4.0.0 runs as a single-process stdio server serving one workspace. If multiple IDE sessions need Ontos MCP for different projects, each spawns its own `ontos serve` process. There is no shared state between processes, so no locking or coordination is needed.

**Why not a filesystem watcher:** The access pattern (a few tool calls per session) does not justify a persistent watcher. The file-walk staleness check is correct, fast, and adds no dependencies.

**Manual refresh:** A `refresh()` tool is also exposed to let the agent explicitly trigger a rescan. This is a convenience for cases where the agent knows it just modified files and wants to avoid the mtime check latency. With the corrected auto-invalidation, `refresh()` is a manual override, not the primary freshness mechanism — agents that forget to call it will still get correct data on the next tool call.

**v4.1 extension:** When the portfolio index (SQLite) is introduced, the invalidation model extends to per-project fingerprint tracking in the database. The full concurrency model for v4.1 (including `SQLITE_BUSY` handling under concurrent re-indexing) will be specified in the v4.1 proposal.

### D5: Context Bundle Algorithm

**Recommendation: Defer to v4.1.**

The v1 proposal presented a 5-signal scoring algorithm (type rank, in-degree centrality, status freshness, recency, curation level) as the highest-value capability. Both reviewers flagged it as the weakest and most speculative component:

- **No validation data.** There is no dataset or A/B test showing that the proposed scoring function produces better bundles than simply serving the existing Tier 1 context map.
- **Token budget assumptions are untested.** The 8k default was chosen by heuristic, not measurement. Different projects may need very different budgets.
- **The algorithm doesn't handle focused queries.** The v1 proposal acknowledged this limitation but didn't address it.
- **Tier 1 already exists.** The context map's Tier 1 section (~2k tokens) is a hand-tuned, production-proven context bundle. It selects key documents by in-degree, includes recent activity, and respects a hard token cap. It's not perfect, but it's real.

**v4.0.0 approach:** The P0 `context_map(compact?)` tool calls `generate_context_map()` and returns the existing Tier 1/2/3 markdown — the same content `ontos map` produces and writes to `Ontos_Context_Map.md`. Tier 1 is already a hand-tuned, token-capped (~2k tokens) orientation bundle that selects key documents by in-degree and includes recent activity. No new ranking or selection algorithm is needed. The P1 `export_graph()` tool separately provides the full structured JSON dump for agents that need graph data.

**v4.1 approach:** Implement the bundle algorithm after collecting real usage data from v4.0.0. Specifically:
- Instrument v4.0.0 tool calls to measure which tools agents call, how often, and what data they request after receiving the context map.
- Use this data to calibrate the scoring function weights and token budget.
- Define a calibration dataset: for each documented workspace, what documents should a well-formed bundle include? Validate the algorithm against this dataset before shipping.

The v1 proposal's 5-signal scoring function remains a reasonable starting point for v4.1. The signals (type rank, in-degree, status, recency, curation) are structurally sound. What's missing is evidence that the specific weights and selection strategy produce useful results.

### D6: The 13 Undocumented Projects

**Recommendation: Defer to v4.1.**

v4.0.0 operates on a single workspace. Undocumented project handling is a cross-project concern that depends on the portfolio index. Including it in v4.0.0 adds scope (fallback bundle generation, language detection from file extensions, README parsing) for a consumer (JohnnyOS) that doesn't exist yet.

**v4.1 approach:** When the portfolio index ships, undocumented projects appear in `project_registry()` as thin entries: `status: "undocumented"`, `slug`, `path`, `has_readme`. No fallback bundles — `get_context_bundle()` on an undocumented project returns an error directing the user to run `ontos init`. This avoids the scope expansion of generating bundles from README.md content and filesystem metadata, which is weakly specified and hard to validate.

### D7: Security Model

**Options:** (A) No security, (B) Read-only default + opt-in write, (C) Full defense-in-depth

**Recommendation: (B) Read-only default for v4.0.0.**

The v4.0.0 tools (`context_map`, `get_document`, `list_documents`, `export_graph`, `query`, `health`, `refresh`) are ALL read operations, plus one cache-management operation (`refresh`). No tool modifies files, creates documents, or alters the graph.

**v4.0.0 security model (stdio):**
- All tools are read-only. The server reads only from the configured workspace root.
- Write-capable tools (`log_session`, `scaffold`, `rename`, `promote`) exist in the CLI but are NOT exposed as MCP tools.
- `refresh()` triggers a cache rebuild from the filesystem — it re-reads existing files, not writes.
- The stdio transport inherently limits access to the spawning process. No network exposure, no authentication needed.

**v4.1 security model (when HTTP/SSE is added):**
- Localhost binding only (127.0.0.1)
- Bearer token authentication (token at `~/.config/ontos/auth.token`)
- Audit logging (append-only JSON lines at `~/.config/ontos/audit.log`)
- Rate limiting per-tool
- Write tools require explicit `[mcp.security] allow_write_tools = [...]` opt-in

This aligns with the board's 4/5 consensus on defense-in-depth (`.ontos-internal/archive/v3.0-planning/V3.0-Board-Review-Analysis.md`, Q9) while being pragmatic about stdio-only scope.

### D8: Version Scope

**v4.0.0 ships exactly:**
- `ontos serve` command (stdio MCP server, single workspace)
- 7 tools total — P0: `context_map`, `get_document`, `list_documents`; P1: `export_graph`, `query`, `health`, `refresh`
- No `workspace_id` parameter on any tool — workspace is implicit (see D9)
- `[mcp]` section support in `.ontos.toml` (optional, no required fields)
- `pip install ontos[mcp]` with `mcp>=1.0` and `pydantic>=2.0` as extras
- In-memory snapshot cache with file-mtime invalidation (see D4)
- **Serialization approach:** P0 tools wrap existing outputs: `context_map()` calls `generate_context_map()` and returns its markdown string; `get_document()` and `list_documents()` require new adapter code (~50 lines each) that reads from `DocumentData` structures. P1 tools: `export_graph()` reuses the `_snapshot_to_json()` pipeline from `ontos export data` (extended with a `validation` field); `query()` requires ~50 lines of new adapter code for single-entity lookup. All adapters are lightweight, but `query()` and the per-tool response shapes are new code — not zero-work CLI reuse.

**v4.0.0 explicitly does NOT ship:**
- Portfolio-level index (SQLite)
- Cross-project tools (`project_registry`, `search`, `get_context_bundle`)
- Context bundle algorithm
- Full-text search
- HTTP/SSE transport
- Write-capable MCP tools
- Auto-configuration of MCP clients (`claude_desktop_config.json`, `.cursor/mcp.json`)
- `ontos://` URI scheme for lazy loading
- MCP Resource/Prompt primitives (v4.0.0 uses Tools only)
- Undocumented project handling

**v4.1 planned scope (for separate proposal):**
- Portfolio index (SQLite at `~/.config/ontos/portfolio.db`)
- `project_registry()`, `search()`, `get_context_bundle()` tools
- Context bundle algorithm (calibrated from v4.0.0 usage data)
- FTS via SQLite FTS5
- Undocumented project thin entries
- HTTP/SSE transport (if JohnnyOS needs it)

**Rationale for the split:** Both reviewers agreed that v4.0.0 as originally proposed was too large. The split draws the line at "wrapping existing capabilities" (v4.0.0) vs. "building new capabilities" (v4.1). Every tool in v4.0.0 maps directly to an existing CLI command or core function. Nothing in v4.0.0 requires new algorithms, new storage, or new data structures.

### D9: Workspace Identity (Responding to Review)

**The problem (v2):** v2 required a `workspace_id` parameter on tool calls, forcing the agent to know the correct slug before it could call any tool. Reviewers flagged this as severe UX friction — the agent would have to guess the slug or burn turns discovering it.

**v4.0.0 solution: implicit workspace, no `workspace_id` parameter.**

In v4.0.0, the MCP server is configured for a single workspace at startup:
```
ontos serve                          # uses current directory as workspace
ontos serve --workspace ~/Dev/canary.work  # explicit workspace path
```

Tools do not accept a `workspace_id` parameter. The workspace is implicit — every tool call operates on the server's configured workspace. The agent discovers which workspace it's connected to by calling `health()`, which returns the workspace name and path.

This eliminates all identity resolution ambiguity. There is exactly one workspace, and the server knows where it is. The agent never has to guess.

**Server tool description includes the workspace.** The MCP server dynamically includes the workspace name in the tool descriptions returned by `tools/list`. For example: `"Returns the context map for the canary.work workspace."` This gives the agent immediate context without requiring a separate discovery call.

**v4.1 definition (multi-workspace model):**

When the portfolio index ships in v4.1, tools gain an optional `workspace_id` parameter that defaults to a configured primary workspace. Resolution:
1. Look up `slug` in the portfolio database `projects` table.
2. If found, resolve `path` to the filesystem location.
3. If not found, return an error with a list of known slugs.

**Slugification rule (for v4.1):** Directory name, lowercased, with dots and spaces replaced by hyphens. `canary.work` → `canary-work`. `finance-engine-2.0` → `finance-engine-2-0`.

**No aliases in v4.0.0 or v4.1.** Each workspace has exactly one canonical slug. Aliases add complexity for marginal convenience at 23 projects.

---

## 9. Migration Path

### What Stays the Same

- **CLI is fully preserved.** Every existing command works identically. The MCP server is a new entry point.
- **`pip install ontos` (without extras) is unchanged.** No new dependencies.
- **`.ontos.toml` without an `[mcp]` section works as before.** The section is optional.
- **`ontos-export-v1` JSON schema is stable.** The MCP server uses it internally but does not alter the format.
- **Per-project document storage is unchanged.** Markdown files with YAML frontmatter.
- **Context map generation is unchanged.** `Ontos_Context_Map.md` continues to be produced by `ontos map`.

### What Changes

- **New package extra:** `pip install ontos[mcp]` adds `mcp>=1.0` and `pydantic>=2.0`.
- **New command:** `ontos serve` launches the MCP server (requires `ontos[mcp]` install).
- **New config section:** Optional `[mcp]` in `.ontos.toml`.
- **New package directory:** `ontos/mcp/` containing server and tool handler modules.

### Why v4.0 and Not v3.5

The v3.0 roadmap and board review consistently frame MCP as a major version boundary:
- "v4.0: Agents primary, humans secondary" — a persona shift (`.ontos-internal/analysis/Ontos-Technical-Architecture-Map-Codex.md`)
- "MCP as primary interface" is listed under "Deferred to v4.0" (`.ontos-internal/strategy/v3.0/V3.0-Implementation-Roadmap.md`, Section 10)

Even though v4.0.0 is a thin bridge, it introduces a fundamentally new interaction model (agents calling tools instead of reading files). That justifies the major version bump per the project's convention of treating major versions as capability milestones.

---

## 10. Acceptance Criteria

### v4.0.0 Acceptance Criteria

Ontos v4.0.0 is done when all of the following are true:

1. **`ontos serve` launches and responds.** Running `ontos serve` in a project directory starts an stdio MCP server that responds to the MCP `initialize` handshake and lists the 3 P0 tools via `tools/list` (`context_map`, `get_document`, `list_documents`), plus P1 tools (`export_graph`, `query`, `health`, `refresh`) if included. Tool descriptions dynamically include the workspace name.

2. **`context_map()` returns the Tier 1/2/3 markdown.** The response is the same markdown content that `ontos map` writes to `Ontos_Context_Map.md`, plus a structured `validation` object with errors and warnings. Tier 1 (~2k tokens) includes the project summary, key documents, and recent activity. Calling `context_map(compact="tiered")` returns the compact tiered format.

3. **`query("ontos_manual")` returns correct metadata.** For Ontos-dev's manual document: returns `type: "kernel"`, correct `depends_on` and `depended_by` lists, accurate `depth`, and valid `content_hash`.

4. **`get_document("ontos_manual")` returns full content.** Returns complete markdown content, full frontmatter, word count, and relationship metadata.

5. **`list_documents(type="kernel")` returns filtered results.** Returns only kernel-type documents from the workspace.

6. **`list_documents()` returns all documents.** Returns all 50+ documents with id, type, status, and path.

7. **`health()` returns server status.** Returns server uptime, configured workspace name and path, document count, last index time, and Ontos version.

8. **Auto-invalidation detects file edits.** After modifying an existing document's content on disk, the next tool call (without calling `refresh()`) returns data reflecting the change. This validates the file-mtime staleness check (not directory mtime).

9. **`refresh()` also triggers cache rebuild.** Calling `refresh()` explicitly forces a rescan and returns confirmation with doc count and duration.

10. **`pip install ontos` (without `[mcp]`) still works identically to v3.4.0.** All CLI commands pass existing test suite. No new dependencies for the base install.

11. **The server runs as a persistent process.** The server stays alive between tool calls (does not exit after each response).

### v4.1 Acceptance Criteria (Provisional — For Planning Only)

These criteria will be refined in a separate v4.1 proposal after v4.0.0 ships and provides usage data.

1. `project_registry()` returns all 23 workspaces with correct status classification.
2. `get_context_bundle("canary-work")` returns coherent, token-budgeted context.
3. `search("simhash")` returns relevant results via FTS across documented projects.
4. Portfolio index survives server restart (reads from `portfolio.db`).
5. Undocumented projects appear with `status: "undocumented"` in the registry.

---

## 11. Open Questions

**Q1: MCP SDK choice.** The official `mcp` Python SDK (Anthropic) vs. FastMCP (higher-level wrapper). The official SDK is more stable; FastMCP may offer faster development. This is an implementation decision that doesn't affect architecture. **Recommendation:** Use the official SDK for long-term stability; evaluate FastMCP if it significantly reduces implementation time.

**Q2: v4.0.0 tool call instrumentation.** To calibrate the v4.1 bundle algorithm, v4.0.0 should log tool call patterns (which tools, how often, what parameters). Should this be opt-in logging, always-on, or deferred until v4.1 planning begins? **Recommendation:** Always-on, lightweight logging to `~/.config/ontos/usage.jsonl` — tool name and timestamp per call. No content logged.

**Q3: File-walk cost at scale.** The corrected invalidation (D4) walks all tracked doc files on every tool call. At 50-100 files this is <1ms. If a workspace grows to 500+ files, should the server switch to a cheaper mechanism (e.g., hashing the list of `(path, mtime)` tuples on startup and comparing a single digest)? **Recommendation:** Defer. Measure actual cost during v4.0.0 usage. The current approach is correct and fast at the documented scale.

**Q4: Token estimation for v4.1 bundles.** When the context bundle algorithm ships in v4.1, should it use a character-count heuristic (1 token per ~4 chars) or a proper tokenizer (tiktoken)? **Recommendation:** Start with the heuristic; switch if it consistently misses the budget by >20%.

**Q5: Log retention policy for v4.1 bundles.** Count-based (N most recent) vs. time-window-based (last 7 days) vs. configurable? **Recommendation:** Defer to v4.1 proposal. Instrument v4.0.0 to measure log access patterns first.
