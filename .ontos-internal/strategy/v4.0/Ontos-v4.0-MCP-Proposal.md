# Ontos v4.0 MCP Proposal

**Date:** 2026-04-04
**Author:** Claude (synthesized from prior research and board decisions)
**Status:** PROPOSAL — requires review and decision by Johnny
**Audience:** Johnny (project owner), LLMs reviewing for correctness and gaps

---

## 1. What Is This

Ontos v4.0 MCP is a Model Context Protocol server that wraps the existing Ontos v3.x knowledge graph, exposing it as a set of queryable tools for LLM agents. Where v3.x produces static files that agents must read in full (burning context window tokens on orientation), v4.0 lets agents ask targeted questions — "what are the key documents in canary.work?", "show me all stale docs across the portfolio", "give me a sized context bundle for this workspace" — and receive precisely scoped responses. It adds a portfolio-level index spanning all 23 projects in `~/Dev/`, a deterministic full-text search capability, and a context bundle generator that assembles right-sized context packages using graph centrality and document type ranking. The CLI remains fully functional; v4.0 is additive, not a replacement.

---

## 2. Why Now

**The file-based approach has hit its ceiling.** Every agent session begins by reading `Ontos_Context_Map.md` — a file that is 87KB for Ontos-dev alone. Across 10 documented projects with ~396 documents, there is no way for an agent to ask "which projects have stale documentation?" without manually parsing `projects.json`, which is itself a manually-maintained snapshot that was 13 days stale at time of writing (generated 2026-03-22). Cross-project queries — the bread and butter of the JohnnyOS orchestrator's routing model — simply cannot be done with the current architecture.

**JohnnyOS requires it.** The Mac Mini orchestrator needs to call `project_registry()` 20-50 times per day to route incoming tasks to the right workspace. It needs `get_context_bundle(workspace_id)` on every routing decision. These are tool calls, not file reads. Without MCP, JohnnyOS cannot use Ontos programmatically — it would have to shell out to `ontos map --json`, parse the output, and manage its own caching. That's a fragile integration that duplicates logic Ontos already owns.

**The architecture is ready.** The v3.0 architecture was explicitly designed for this moment. The core/IO separation (documented in `.ontos-internal/analysis/Ontos-Technical-Architecture-Map-Codex.md`, Section 11) reserves `ontos/mcp/` as an extension point. All CLI commands already emit structured JSON via `--json` flags. The `ontos export data` command produces a complete graph export in `ontos-export-v1` schema. The graph engine (`ontos/core/graph.py`) builds dependency graphs with cycle detection and depth calculation. The plumbing exists; what's missing is the protocol layer.

**The MCP ecosystem has matured.** When the 5-LLM review board assessed MCP in January 2026 (`.ontos-internal/archive/v3.0-planning/V3.0-Board-Review-Analysis.md`), they noted "installation UX is bad," "security model inadequate," and "Python is second-class." Three months later: the official Python MCP SDK is stable, Claude Code and Cursor both support MCP servers natively, and the ecosystem has 8M+ npm downloads with 2,000+ community servers. The "wait for maturity" rationale from the board's deferral has been satisfied.

**Competitive pressure is real but secondary.** CTX, Claude Code memory, and Cursor context are shipping MCP integrations. Ontos's differentiation is its deterministic, graph-based approach — no vector search, no stochastic retrieval failures. But differentiation only matters if the tool is accessible. An MCP server makes Ontos accessible to every MCP-compatible client without custom integration work.

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
- No portfolio-level view — no single tool can answer "what projects exist and what state are they in?"

### The 23-Project Portfolio

The `~/Dev/` directory contains 23 projects tracked by `.dev-hub/registry/projects.json`:

| Category | Count | Projects (examples) |
|----------|-------|---------------------|
| **Documented** (Ontos context map + README) | 10 | canary.work (46 docs), role-evaluator-bot (76 docs), finance-engine-2.0 (55 docs), Ontos-dev (50 docs), folio.love (50 docs) |
| **Partial** (README only or context map only) | 5 | Vibing, ohjonathan.com, NPOLabDev |
| **Undocumented** (neither) | 8 | Career, agent-skills, claude-code-monitoring, engineering-strategy, strategy-eng |

Total tracked documents across documented projects: ~396.

5-6 projects are actively developed: canary.work, role-evaluator-bot, finance-engine-2.0, folio.love, Ontos-dev, ohjonathan.com. The remaining documented projects (Personal-ERP, Project-Ontos-OLD, oh.gold) have older v1-format context maps with limited metadata.

### Current Cross-Project Orchestration

The `.dev-hub/` directory (documented in `.dev-hub/README.md`) is a lightweight, read-only index:

- `registry/projects.json` — manually generated snapshot of all 23 projects with status classification, doc counts, and tags
- `registry/schema.json` — JSON Schema for project entries
- `snapshots/` — reserved directory for future Tier 1 caches (currently empty)

**Limitations that block v4.0 consumers:**
- The registry is a static JSON file with no automated refresh. It was 13 days stale at time of writing.
- No cross-project dependency tracking exists.
- No search capability across projects.
- No programmatic access — agents must read and parse the JSON file directly.

### Architectural Readiness

**In place:**
- Core/IO separation validated across v3.0-v3.4 (documented in `.ontos-internal/analysis/Ontos-Technical-Architecture-Map-Codex.md`). The core layer (~3,812 LOC, 16 files) is pure logic with zero external dependencies.
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

### Consumer 1: JohnnyOS Orchestrator

**What it is:** A daemon running on a Mac Mini that routes incoming tasks to workspace-specific supervisors. It is the primary consumer of Ontos v4.0 MCP.

**How it connects:** MCP client calling Ontos MCP server over stdio (initial) or local socket (when HTTP/SSE transport is added in v4.0.x). Runs on the same machine as the Ontos server.

**Tools it calls:**

| Tool | Input | Output Shape | Frequency | Cacheable |
|------|-------|-------------|-----------|-----------|
| `project_registry()` | None | `{project_count, projects: [{slug, status, doc_count, last_updated, tags}], summary: {documented, partial, undocumented}}` | 20-50x/day | Yes (TTL 5min) |
| `get_context_bundle(workspace_id)` | `workspace_id: str` (e.g., `"canary-work"`) | `{workspace_id, context_text, token_estimate, warnings, stale_docs, generated_at}` | 5-20x/day per workspace | Yes (mtime-invalidated) |
| `query(entity_id)` | `entity_id: str` | `{id, type, status, depends_on, depended_by, depth, last_updated, content_hash}` | Ad-hoc during task assembly | No |
| `context_map(workspace_id)` | `workspace_id: str` | `{graph: {nodes, edges, depths}, validation: {errors, warnings}}` | During feature planning | No |
| `search(query_string)` | `query_string: str`, optional `workspace_id: str` | `[{doc_id, workspace, type, path, snippet, matched_fields}]` | Ad-hoc | No |

**What it does NOT need from Ontos:**
- Task state (blocked PRs, review queues) — owned by JohnnyOS Workflow Ledger
- Runtime state (service health, cron status) — owned by JohnnyOS Runtime Registry
- Raw activity (session transcripts, event streams) — owned by JohnnyOS Artifact Store
- Prompt templates (playbook content, reviewer instructions) — owned by Vibing MCP

### Consumer 2: Claude Code / Codex CLI / Manual Sessions

**What it is:** Interactive agent sessions where Johnny works with an LLM on a specific project. The LLM needs project context to be effective.

**How it connects:** MCP client in the IDE or terminal, connected via stdio. Human-in-the-loop — responses must be <1s for cached queries.

**Tools it calls:** All tools from Consumer 1, plus:

| Tool | Input | Output Shape | Frequency | Cacheable |
|------|-------|-------------|-----------|-----------|
| `get_document(document_id)` | `document_id: str` or `path: str` | `{id, type, status, frontmatter, content, metadata: {content_hash, word_count, depended_by}}` | Interactive, on-demand | No |
| `list_documents(workspace_id, kind?, status?)` | `workspace_id: str`, optional filters | `[{id, type, status, path}]` | Interactive, on-demand | No |

**What it does NOT need:** Nothing beyond the 7 tools. The full tool set serves this consumer.

### Consumer 3: Vibing MCP

**What it is:** A separate MCP server for spec generation that uses Ontos as a context source during its own development.

**How it connects:** MCP client during development sessions, connected via stdio. Same interaction pattern as Consumer 2.

**Tools it calls:** Same as Consumer 2. No special requirements beyond what Claude Code needs.

**What it does NOT need from Ontos:**
- Spec generation logic — that's Vibing's own domain
- Template rendering — Vibing owns its own output format

---

## 5. What Ontos v4.0 Must Own

### Workspace and Entity Indexing

Ontos owns the canonical index of all workspaces in the portfolio. This means:
- Scanning `~/Dev/` for project directories
- Detecting Ontos coverage (`.ontos.toml`, `Ontos_Context_Map.md`, `README.md`)
- Extracting Tier 1 metadata from context maps (project name, doc count, last updated)
- Maintaining the portfolio-level index with per-project status classification

### Document Management

Ontos owns the 5-type document ontology (kernel, strategy, product, atom, log) with:
- YAML frontmatter parsing and validation
- Three-tier curation levels (L0/L1/L2)
- Status lifecycle (draft, active, deprecated, archived, scaffold, pending_curation)
- Content hashing for change detection

### Dependency Graph

Ontos owns the structural relationships between documents:
- `depends_on` edges (enforced by type hierarchy — atoms can depend on products, not vice versa)
- `impacts` edges (log-specific — what documents a session affected)
- `describes` edges (atom-specific — what source files a doc covers)
- Cycle detection, orphan detection, depth calculation
- Reverse edge traversal (who depends on this document?)

### Context Bundle Generation

This is the highest-value capability in v4.0 and the primary reason the MCP server exists.

**The intellectual problem:** Given a `workspace_id`, assemble a context package that gives an LLM sufficient understanding of the project to do useful work — without vector search, without embeddings, using only the deterministic signals already present in the knowledge graph.

**The algorithm: Priority-Weighted Graph Traversal with Token Budget**

The algorithm scores every document in a workspace using five deterministic signals, then greedily selects documents by score until the token budget is exhausted.

**Scoring function (5 signals):**

1. **Type rank weight** — derived from the document type hierarchy in `ontos/core/ontology.py`. Higher-ranked types are more architecturally central:
   - kernel (rank 0): 50 points
   - strategy (rank 1): 40 points
   - product (rank 2): 30 points
   - atom (rank 3): 20 points
   - log (rank 4): 5 points

2. **In-degree centrality** — the number of other documents that depend on this document, computed from `DependencyGraph.reverse_edges`. The context map's "Key Documents" section (Tier 1) already uses this signal to identify structurally central docs.
   - Score contribution: `in_degree * 10`
   - Example: canary.work's `soul` doc has 6 dependents = 60 points

3. **Status freshness** — documents that are actively being worked on are more relevant than stable or deprecated ones:
   - `in_progress`: +15
   - `active`: +10
   - `draft`: +5
   - `scaffold`: -10
   - `deprecated`: -20
   - `archived`: -30

4. **Recency** (logs only) — recent session logs capture current work context. Older logs are historical noise:
   - Score contribution: `max(0, 30 - age_in_days)`
   - Only the 3 most recent logs are eligible for inclusion (matching Tier 1's "Recent Activity" pattern)
   - Logs older than 30 days score 0 on this signal

5. **Curation level** — higher curation means more human investment and more reliable content:
   - L2 (full): +10
   - L1 (stub): +5
   - L0 (scaffold): +0

**Composite score:** `type_weight + (in_degree * 10) + status_score + recency_score + curation_score`

**Selection process:**

1. Build workspace snapshot (reuse existing `create_snapshot()` from `ontos/io/snapshot.py`)
2. Score every document
3. Sort by composite score descending
4. Iterate through ranked list, adding documents until token budget is hit:
   - If the full document fits within remaining budget: include with full content
   - If only metadata fits: include as metadata-only (frontmatter fields, no body)
   - If neither fits: skip, but record in `excluded_high_value` list
5. Assemble the bundle with a summary header, included documents, graph edges between included documents, and the excluded list

**Token budget:** Default 8,000 tokens (~32KB). This fits comfortably in any modern context window (128k-200k) while leaving ample room for the task prompt and agent reasoning. Configurable via `.ontos.toml`:

```toml
[mcp]
context_bundle_token_budget = 8000
```

**Why this works without vector search:** The 5 signals are all structural properties of the knowledge graph, not semantic properties of content. Type rank captures architectural importance. In-degree captures structural centrality. Status and recency capture temporal relevance. Curation captures quality. Together, they reliably select the documents an agent needs to understand a project — kernel docs (mission, values), high-centrality product docs (PRDs that many atoms depend on), and recent logs (what's actively happening).

**Known limitation:** This algorithm does not handle focused queries ("show me context relevant to authentication"). The initial `get_context_bundle` returns a general-purpose bundle. A `focus` parameter (e.g., `get_context_bundle("canary-work", focus="authentication")`) that filters by concept tags or dependency subgraph is a natural extension but is deferred from the initial implementation.

### Staleness Detection

Ontos owns the determination of whether documentation is current:
- `describes`/`describes_verified` field tracking
- Content hash comparison across snapshots
- Stale document warnings in context bundles and health checks

### Cross-Project Search

Ontos owns deterministic full-text search across the portfolio:
- Indexed on document `id`, `concepts`, and content (first 500 characters)
- Deterministic ranking (no stochastic retrieval)
- Scoped to single workspace or across entire portfolio
- Implementation via SQLite FTS5 in the portfolio database (see Section 7)

---

## 6. What Ontos v4.0 Must NOT Own

| Excluded Responsibility | Owner | Rationale |
|------------------------|-------|-----------|
| **Task state** (blocked features, PR reviews, sprint status) | JohnnyOS Workflow Ledger | Task lifecycle is JohnnyOS's domain. Ontos tracks documentation, not work items. Mixing them creates coupling that breaks Ontos's independence constraint. |
| **Runtime state** (service health, cron job status, deployment state) | JohnnyOS Runtime Registry | Ontos is a documentation system. It has no visibility into whether services are running, healthy, or deployed. |
| **Raw activity** (session transcripts, chat logs, event streams) | JohnnyOS Artifact Store | Ontos captures structured session logs (`ontos log`), not raw transcripts. The distinction matters: logs are curated artifacts in the knowledge graph; transcripts are ephemeral records. |
| **Prompt templates** (playbook content, reviewer instructions, system prompts) | Vibing MCP / consumer-specific | Ontos exposes context; consumers decide how to prompt with it. Embedding prompt templates in Ontos creates consumer-specific coupling. |
| **Vector / semantic search** | Excluded from v4.0 entirely | The consumer brief explicitly bans vector search in v1 (JohnnyOS D6: "Deterministic retrieval only"). Ontos uses graph traversal and FTS. This is a feature, not a limitation — deterministic retrieval has no stochastic failure modes. |
| **Code intelligence** (AST parsing, symbol resolution, type checking) | IDE / language servers | Ontos documents are markdown with YAML frontmatter. It indexes documentation about code, not the code itself. |

---

## 7. The Cross-Project Indexing Problem

### Why This Is Architecturally Distinct

Ontos v3.x is fundamentally single-project. Every command takes a `project_root` path and operates within it. The graph engine builds a `DependencyGraph` from one project's documents. The context map is generated for one project. The configuration is read from one `.ontos.toml`.

The v4.0 consumer requirements are fundamentally cross-project. `project_registry()` returns all 23 workspaces. `get_context_bundle(workspace_id)` requires knowing where workspace "canary-work" lives on disk. `search(query_string)` must search across all documented projects. These cannot be implemented by "wrapping CLI commands in MCP" — there is no CLI command that operates across projects.

This gap requires a new architectural component: a **portfolio-level index**.

### What a Portfolio-Level Index Requires

1. **A persistent store** — the index must survive process restarts. Rebuilding it from scratch on every MCP server startup means scanning 23 project directories, parsing frontmatter in ~396 documents, and building graphs. This takes seconds, not milliseconds, and violates the <1s response time requirement for cached queries.

2. **A scan strategy** — the index must know which directories under `~/Dev/` are projects, how to detect Ontos coverage, and how to extract metadata without running a full `ontos map` in each project.

3. **A refresh mechanism** — the index must detect when project state has changed and update accordingly, without requiring a manual re-run.

4. **A query interface** — the index must support the queries consumers need: list all projects, filter by status/tags, full-text search across documents, look up a workspace by slug.

### Storage Recommendation: SQLite

**Recommendation:** Keep per-project storage as filesystem (the current model). Add a single SQLite database for the portfolio-level index only, stored at `~/.config/ontos/portfolio.db`.

**Why SQLite, not a filesystem index:**

- The portfolio has 23 projects and ~396 documents. Scanning all project directories on every `project_registry()` call is O(projects * docs_per_project) in filesystem reads. With `project_registry()` called 20-50x/day by JohnnyOS (even cached, the first call and every cache miss would be expensive), this is unacceptable.
- SQLite makes `project_registry()` a single indexed query: `SELECT * FROM projects`. Constant time, regardless of how many documents exist on disk.
- Full-text search (`search(query_string)`) requires an inverted index. SQLite FTS5 provides this with no additional dependencies — `sqlite3` is part of Python's standard library.
- Concurrent readers are handled natively by SQLite's WAL mode. Multiple MCP clients (JohnnyOS + Claude Code + Vibing) can read simultaneously without corruption or blocking.

**Why NOT full SQLite for per-project data:**

- Per-project document storage in SQLite would duplicate the filesystem as source of truth, creating a synchronization problem.
- The filesystem IS the database for individual projects — this is a core Ontos principle. The graph is built from markdown files on disk. Adding SQLite as a parallel store creates two sources of truth.
- Per-project graph builds are already fast: <500ms for 100 docs, <2s for 100-500 docs (documented performance baselines). Caching the in-memory snapshot with mtime invalidation is sufficient.

**Portfolio database schema (conceptual, not DDL):**

- **projects table:** slug (primary key), path, status (documented/partial/undocumented), has_readme, has_context_map, doc_count, last_updated, tags (JSON array), notes, indexed_at, docs_dir_mtime
- **project_documents table:** project_slug + doc_id (composite primary key), doc_type, doc_status, filepath, content_hash, depends_on (JSON array), concepts (JSON array), summary (first ~200 chars of content)
- **FTS5 virtual table:** indexed on doc_id, concepts, and summary for full-text search

### How Existing Context Maps Relate to the Portfolio Index

The portfolio index does NOT replace per-project context maps. The relationship is:

- **Context maps** are generated artifacts (`Ontos_Context_Map.md`) — human-readable, tiered, produced by `ontos map`. They remain the primary output for human consumption and for agents that read files directly.
- **The portfolio index** is a machine-queryable cache of metadata extracted from context maps and project directories. It enables cross-project queries that no single context map can answer.
- On initial seeding, the portfolio index reads from the existing `.dev-hub/registry/projects.json` data.
- On subsequent updates, the MCP server maintains the portfolio index independently via mtime-based change detection on each project's `docs/` directory and `.ontos.toml`.

### Relationship to `.dev-hub/`

The `.dev-hub/registry/projects.json` file currently serves as the manual cross-project index. With v4.0:

- The portfolio database (`~/.config/ontos/portfolio.db`) becomes the authoritative cross-project index.
- `projects.json` becomes a human-readable export — regenerated from the database on demand, but no longer the source of truth.
- The `.dev-hub/` directory continues to exist for human reference but is not a runtime dependency of the MCP server.

---

## 8. Key Decisions

### D1: MCP Transport

**Options:**
- (A) stdio only
- (B) HTTP/SSE only
- (C) stdio first, HTTP/SSE added in v4.0.x

**Recommendation: (C) stdio first, HTTP/SSE in v4.0.x.**

All three consumers (JohnnyOS, Claude Code, Vibing) can use stdio — it's the standard MCP transport for local tools. Claude Code and Cursor connect to MCP servers via stdio natively. JohnnyOS, while architecturally a daemon, is not yet built; when it is, it can initially connect via stdio by spawning the Ontos MCP server as a child process.

HTTP/SSE adds port management, auth token handling, and CORS configuration. These are meaningful for process-to-process communication when JohnnyOS runs as a persistent daemon on the Mac Mini. But shipping HTTP/SSE in v4.0.0 means building and testing infrastructure for a consumer that doesn't exist yet.

The prior board decision (`.ontos-internal/archive/v3.0-planning/V3.0-Board-Review-Analysis.md`) recommended "JSON-RPC 2.0 over stdio (local) and HTTP+SSE (remote)." This recommendation stands — both transports are needed eventually. The question is sequencing. stdio first unblocks all current consumers immediately. HTTP/SSE follows in v4.0.x when JohnnyOS daemon mode is built.

**Implication:** `ontos serve` launches an stdio MCP server. Future `ontos serve --http --port 8400` adds HTTP/SSE transport.

### D2: Manifest Format

**Options:**
- (A) Adopt `.johnny-os.yaml` as the workspace manifest
- (B) Extend `.ontos.toml` with an `[mcp]` section
- (C) Create a new `ontos-mcp.toml` file

**Recommendation: (B) Extend `.ontos.toml` with an `[mcp]` section.**

`.ontos.toml` already exists in 6+ projects. It is the canonical configuration file, parsed by `ontos/io/config.py` and mapped to the `OntosConfig` dataclass. Adding an `[mcp]` section is the minimal-friction path.

Adopting `.johnny-os.yaml` creates a coupling between Ontos and JohnnyOS that contradicts the architectural independence constraint. The consumer brief (`.ontos-internal/strategy/v4.0/ontos-v4-mcp-consumer-brief.md`) states: "Independent service with own repo, versioning, process lifecycle." If Ontos reads JohnnyOS's manifest format, it cannot function when JohnnyOS is down or absent. The consumer brief also states: "Must survive JohnnyOS being down."

A separate `ontos-mcp.toml` adds configuration sprawl for no benefit. MCP config belongs in the existing Ontos config file.

For the portfolio-level index, a separate `~/.config/ontos/portfolio.toml` lists the workspace scan root(s):

```toml
[portfolio]
scan_roots = ["~/Dev"]
```

**Implication:** Ontos reads `.johnny-os.yaml` only as a data source for undocumented projects (extracting metadata like project name and tags). It never treats it as its own configuration.

### D3: Storage Backend

**Options:**
- (A) Pure filesystem — rebuild index from disk on every query
- (B) SQLite for portfolio index + filesystem for per-project data
- (C) Full SQLite for everything

**Recommendation: (B) SQLite for portfolio index, filesystem for per-project data.**

Full rationale in Section 7. Summary: per-project rebuilds are fast (<1s) and the filesystem is the authoritative source; cross-project queries need an indexed, persistent store; SQLite's `sqlite3` module is Python stdlib, adding zero new dependencies.

**Implication:** New file at `~/.config/ontos/portfolio.db`. Per-project data continues to be read from the filesystem via existing `create_snapshot()` path. The SQLite database is a cache that can be rebuilt from disk at any time.

### D4: Indexing Strategy

**Options:**
- (A) Full rescan of all projects on MCP server startup
- (B) Filesystem watcher (watchdog/fsnotify) for incremental updates
- (C) Manual re-index command + mtime-based cache invalidation

**Recommendation: (C) Manual re-index + mtime cache invalidation.**

The access pattern is 5-50 calls/day. This does not justify a persistent filesystem watcher, which adds a background process with OS-specific edge cases (macOS FSEvents quirks, high-churn directories, recursive watch limits).

The existing `DocumentCache` pattern in the codebase uses mtime-based invalidation — a proven approach within Ontos. The same pattern extends to the portfolio level:

- **Per-project:** On first `get_context_bundle(workspace_id)` call, build snapshot, cache in memory with mtime of `docs/` directory and `.ontos.toml`. On subsequent calls, check mtimes. If unchanged, return cached snapshot. If changed, rebuild.
- **Portfolio level:** On `project_registry()`, check SQLite cache. If any project's `docs_dir_mtime` has changed (checked via a lightweight `os.stat()` call per project), re-index that project only.
- **Manual override:** `ontos serve --refresh` forces a full re-index. A `refresh()` tool (MCP-callable) allows agents to trigger re-indexing when they know state has changed.

**Implication:** No background processes, no filesystem watchers. The MCP server is reactive, not proactive. This matches Ontos's existing philosophy: deterministic, user-controlled, no magic.

### D5: Context Bundle Algorithm

Fully described in Section 5 under "Context Bundle Generation." Summary of the recommendation:

- **Scoring function:** 5 deterministic signals (type rank, in-degree centrality, status freshness, recency, curation level)
- **Selection:** Greedy by score, with fallback to metadata-only for documents that don't fit in full
- **Token budget:** 8,000 tokens default, configurable
- **Output:** JSON bundle with summary, included documents (full or metadata-only), graph edges, and `excluded_high_value` list

**Implication:** This is the most complex new code in v4.0. It requires a new module (`ontos/mcp/bundle.py`) that calls into the existing core for graph building and document loading, then applies the scoring and selection algorithm.

### D6: The 13 Undocumented Projects

**Options:**
- (A) Bootstrap from `.johnny-os.yaml` manifests (lightweight metadata only)
- (B) Require full Ontos onboarding before inclusion in the registry
- (C) Include as "visible but empty" — thin entries with slug, path, and filesystem metadata

**Recommendation: (C) Visible but empty, with (A) as enrichment where available.**

The portfolio index should include all 23 projects regardless of Ontos coverage. Undocumented projects appear in `project_registry()` with `status: "undocumented"`, `doc_count: null`, and whatever metadata can be derived without Ontos:
- `slug` (directory name)
- `path` (filesystem path)
- `has_readme` (boolean)
- `tags` (from `.johnny-os.yaml` if present, else empty)
- `notes` (from `projects.json` if present, else null)

For `get_context_bundle()` on an undocumented project: return a minimal bundle containing the README.md content (if it exists) plus filesystem metadata (file count, primary language inferred from file extensions, last git commit message/date). This is useful without requiring full Ontos adoption.

Requiring full onboarding (option B) creates a chicken-and-egg problem: the orchestrator can't route to a project it can't see, but onboarding requires focused attention on each project. Option C makes all projects visible immediately.

**Implication:** The portfolio database stores entries for all 23 projects. The `project_documents` table is empty for undocumented projects. The `get_context_bundle` tool has a fallback path for projects without Ontos coverage.

### D7: Security Model

**Options:**
- (A) No security (trust the local environment)
- (B) Read-only default with opt-in write tools
- (C) Full defense-in-depth (auth tokens, audit logging, path allowlists)

**Recommendation: (B) Read-only default, with elements of (C) for HTTP transport.**

The 7 specified MCP tools are ALL read operations. No consumer brief requires write access via MCP. The consumer brief explicitly states: "Read-only from consumers' perspective. Writes happen via filesystem (promotion pipeline)." JohnnyOS "never writes to Ontos directly."

**v4.0.0 security model (stdio):**
- All 7 tools are read-only. No tool can modify files, create documents, or alter the graph.
- The MCP server reads only from directories under configured `scan_roots` (default: `~/Dev/`). It cannot access files outside this scope.
- Write-capable tools (`log_session`, `scaffold`, `rename`, `promote`) exist in the CLI but are NOT exposed as MCP tools in v4.0.0.
- If write tools are added in a future version, they require explicit opt-in via `.ontos.toml`:
  ```toml
  [mcp.security]
  allow_write_tools = ["log_session"]
  ```

**v4.0.x security model (HTTP/SSE transport, when added):**
- Localhost binding only (127.0.0.1) — prevents network exposure
- Bearer token authentication — token stored at `~/.config/ontos/auth.token`, required for every HTTP request
- Audit logging — all operations logged to `~/.config/ontos/audit.log` (append-only, JSON lines)
- Rate limiting — configurable per-tool call rate to prevent runaway agents

This aligns with the board's 4/5 consensus on defense-in-depth (`.ontos-internal/archive/v3.0-planning/V3.0-Board-Review-Analysis.md`, Q9) while being pragmatic about what's needed for stdio transport (where the client is a trusted local process).

**Implication:** v4.0.0 ships with zero security configuration required. The server is read-only over stdio. Security complexity is added only when HTTP transport introduces a network attack surface.

### D8: Version Scope

**Options:**
- (A) MCP server only (7 tools + portfolio index + stdio transport)
- (B) MCP server + daemon mode
- (C) MCP server + daemon + template system + lazy loading + auto-configuration

**Recommendation: (A) MCP server only.**

The v3.0 roadmap (`.ontos-internal/strategy/v3.0/V3.0-Implementation-Roadmap.md`, Section 10) explicitly deferred daemon mode, template system, lazy loading, and auto-configuration to v4.0+. But "v4.0+" does not mean "v4.0.0." These are distinct features that can ship independently.

The MCP server running via `ontos serve` IS effectively a daemon — it's a long-lived process. There is no need for a separate "daemon mode" abstraction. The template system (export formats beyond markdown/JSON) and lazy loading (URI-based document loading via `ontos://atom/{id}`) are valuable but orthogonal to the core MCP capability.

Auto-configuration (patching `claude_desktop_config.json`, `.cursor/mcp.json`) is a polish feature that can ship in v4.0.1 after the core server is stable.

Scope for v4.0.0:
- `ontos serve` command (stdio MCP server)
- 7 MCP tools (get_context_bundle, query, context_map, project_registry, search, get_document, list_documents)
- Portfolio index (SQLite, seeded from `projects.json`)
- Context bundle algorithm
- Full-text search via FTS5
- `[mcp]` section in `.ontos.toml`
- `pip install ontos[mcp]` with pydantic dependency

Not in v4.0.0 (deferred to v4.0.x or v4.1):
- HTTP/SSE transport
- Write-capable MCP tools
- Auto-configuration of MCP clients
- `ontos://` URI scheme for lazy loading
- MCP Resource/Prompt primitives (v4.0.0 uses Tools only)
- Template system for custom export formats
- Subscription/notification model for context changes

**Implication:** Tight scope, deliverable as a single release. The deferred items are planned, not abandoned — they have clear extension points in the v4.0.0 architecture.

---

## 9. Migration Path

### What Stays the Same

- **CLI is fully preserved.** Every existing command (`ontos map`, `ontos doctor`, `ontos log`, etc.) works identically. The MCP server is a new entry point, not a replacement.
- **`pip install ontos` (without extras) is unchanged.** No new dependencies. The package installs exactly as v3.4.0 does today.
- **`.ontos.toml` without an `[mcp]` section works as before.** The section is optional and ignored by the CLI.
- **`ontos-export-v1` JSON schema is stable.** The MCP server uses it internally but does not alter the format.
- **Per-project document storage is unchanged.** Markdown files with YAML frontmatter in `docs/`. No migration of existing documents required.
- **Context map generation is unchanged.** `Ontos_Context_Map.md` continues to be produced by `ontos map` with the same tiered format.

### What Changes

- **New package extra:** `pip install ontos[mcp]` adds `mcp>=1.0` and `pydantic>=2.0` as dependencies.
- **New command:** `ontos serve` launches the MCP server (requires `ontos[mcp]` install).
- **New config section:** Optional `[mcp]` in `.ontos.toml` for server-specific configuration (token budget, scan roots, security settings).
- **New files at `~/.config/ontos/`:** `portfolio.toml` (scan root configuration), `portfolio.db` (SQLite index). Created automatically on first `ontos serve` run.
- **New package directory:** `ontos/mcp/` containing server, tools, portfolio index, and bundle algorithm modules.

### How Existing Coverage Is Preserved

The MCP server's portfolio index is seeded from the existing `.dev-hub/registry/projects.json` on first run. Every project currently documented in the registry appears in the portfolio database with the same slug, path, status, and metadata.

Per-project data is read directly from the filesystem — the same files the CLI reads. No data migration is required. The MCP server calls the same core functions (`create_snapshot()`, `build_graph()`, etc.) that the CLI uses.

### Why v4.0 and Not v3.5

The v3.0 roadmap and board review consistently frame MCP as a major version boundary:
- "v4.0: Agents primary, humans secondary" — a fundamental persona shift (`.ontos-internal/analysis/Ontos-Technical-Architecture-Map-Codex.md`)
- "MCP as primary interface" is listed under "Deferred to v4.0" (`.ontos-internal/strategy/v3.0/V3.0-Implementation-Roadmap.md`, Section 10)
- The addition of a portfolio-level index, SQLite storage, and pydantic dependency constitute meaningful architectural additions beyond a point release

Semver justification: v4.0 adds new capabilities (MCP tools, portfolio index, FTS) without breaking existing ones. The CLI is backward-compatible. A strict reading of semver might argue this is a minor version (no breaking changes). But the project's convention treats major versions as capability milestones, and the shift to agent-first interaction is significant enough to warrant v4.0.

---

## 10. Acceptance Criteria

Ontos v4.0 MCP is done when all of the following are true:

1. **`ontos serve` launches and responds.** Running `ontos serve` starts an stdio MCP server that responds to the MCP `initialize` handshake and lists all 7 tools via `tools/list`.

2. **`get_context_bundle("canary-work")` returns coherent, sized context.** The response includes `context_text` (readable prose with document content), `token_estimate` (within 8,000 default budget), `warnings` (any stale docs or graph issues), and `stale_docs` (list). The context text includes canary.work's kernel doc (`soul`), its highest-centrality product docs, and the 3 most recent logs.

3. **`get_context_bundle("role-evaluator-bot")` returns coherent context.** Same as above, but for role-evaluator-bot. The `prd` document (28 dependents — the highest in-degree doc in any documented project) appears in the bundle. The context reflects the project's 76 documents.

4. **`project_registry()` returns all 23 workspaces.** The response includes all projects from `~/Dev/` with correct status classification (documented/partial/undocumented), doc counts for documented projects, and tags. The 10 documented projects show accurate `doc_count` and `last_updated` values.

5. **`search("simhash")` returns relevant results.** A search for a term known to exist in at least one documented project returns matching documents with `doc_id`, `workspace`, `path`, and `snippet` showing the matching context. Results are ranked deterministically.

6. **`query("soul")` returns correct metadata.** For canary.work's `soul` document: returns `type: "kernel"`, correct `depends_on` and `depended_by` lists, accurate `depth`, and valid `content_hash`.

7. **`get_document("prd")` returns full content.** For role-evaluator-bot's PRD: returns the complete markdown content, full frontmatter, word count, and list of documents that depend on it.

8. **`list_documents("ontos-dev", kind="kernel")` returns filtered results.** Returns only kernel-type documents from the Ontos-dev workspace.

9. **Concurrent reads succeed without corruption.** Two MCP clients connected simultaneously (e.g., Claude Code + a test harness) can both call `project_registry()` and `get_context_bundle()` without blocking, deadlocking, or returning inconsistent results.

10. **The server runs as a persistent process with health reporting.** The server stays alive between tool calls (does not exit after each response). A `health` tool returns server uptime, portfolio index age, and count of indexed workspaces.

11. **`pip install ontos` (without `[mcp]`) still works identically to v3.4.0.** All CLI commands pass existing test suite. No new dependencies introduced for the base install.

12. **Portfolio index survives server restart.** Stop and restart `ontos serve`. The second startup reads from `portfolio.db` and responds to `project_registry()` without a full rescan (unless mtimes have changed).

13. **Undocumented projects appear in the registry.** The 8 undocumented projects (Career, agent-skills, claude-code-monitoring, etc.) appear in `project_registry()` with `status: "undocumented"` and whatever metadata is available (has_readme, path).

---

## 11. Open Questions

**Q1: Portfolio scan root configuration.** The proposal assumes `~/Dev/` as the single scan root. Should the portfolio support multiple scan roots (e.g., `~/Dev/` + `~/Work/`)? This affects the `portfolio.toml` design and the `project_registry()` output. Johnny to decide based on actual directory layout.

**Q2: `workspace_id` resolution for projects with non-slug names.** The proposal defines `workspace_id` as the directory name (slug). canary.work's directory is `canary.work` but the `ontos_project_name` in the registry is also `canary.work`. For projects where the directory name and project name differ (e.g., `ohjonathan.com-sandbox` vs. the site it represents), should the MCP server support alias resolution? This is a convenience feature that may not be needed at 23 projects but could matter if the portfolio grows.

**Q3: Token estimation accuracy.** The context bundle algorithm relies on token estimation to enforce the budget. The current `estimate_tokens()` function (if it exists in the codebase) may use a simple character-count heuristic. For v4.0, should the MCP server use a proper tokenizer (tiktoken or similar) for accurate estimation? The trade-off is accuracy vs. adding a dependency. A character-count heuristic (1 token per ~4 characters) may be sufficient given the 8k budget has margin.

**Q4: MCP SDK choice.** The proposal assumes the official `mcp` Python SDK (maintained by Anthropic). An alternative is FastMCP, a higher-level wrapper. The official SDK is more stable and has better long-term support guarantees. FastMCP may offer faster development. This is an implementation decision that doesn't affect the proposal's architecture — either SDK produces the same MCP-compatible server.

**Q5: Log retention in context bundles.** The algorithm includes the 3 most recent logs. For projects with high session frequency (multiple sessions per day), this may be insufficient. For projects with low frequency (sessions weeks apart), 3 logs may include irrelevant historical content. Should the log count be configurable per project, or should the algorithm use a time window (e.g., "logs from the last 7 days") instead of a count? This can be determined during implementation based on testing with real project data.
