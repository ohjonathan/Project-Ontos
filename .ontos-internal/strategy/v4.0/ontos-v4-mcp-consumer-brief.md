# Ontos v4 MCP: Consumer Requirements Brief

> Take this into a dedicated session to write the Ontos v4 MCP proposal.
> This brief defines what downstream consumers need from Ontos. It does not prescribe internal architecture.

---

## What Is Ontos

Ontos is Johnny's knowledge graph system for managing codebase structure, architecture docs, dependency graphs, and curated reference knowledge across ~23 projects. It currently exists as a Python CLI/package (v3.x on PyPI) with document types, graph structure, YAML frontmatter, and an explicit "Space vs Time" separation.

Ontos v4 is the next version. The primary addition is an MCP (Model Context Protocol) server mode so that multiple consumers can query the knowledge graph programmatically.

---

## Why It Matters

Ontos v4 MCP is the first thing that gets built in the entire Johnny OS ecosystem. It's the foundation that everything else stands on:

1. **JohnnyOS** uses it for L1 (reference knowledge) queries: "what is this project?", "what does canary.work depend on?", "give me the architecture context for role-evaluator-bot."
2. **Vibing MCP** (built second) uses it during its own development for codebase context.
3. **Claude Code / Codex CLI** use it during manual development sessions for project context.
4. **The human orchestrator** (Johnny doing manual workflows before JohnnyOS exists) uses it for the same.

If Ontos v4 MCP doesn't exist, nothing else can start.

---

## Consumers and What They Need

### Consumer 1: JohnnyOS Orchestrator

**How it connects:** MCP client running on Mac Mini, calling Ontos v4 MCP over stdio or local socket.

**Tools it expects to call:**

| Tool | Purpose | When Called |
|------|---------|-------------|
| `get_context_bundle(workspace_id)` | Return the full curated context for a workspace: architecture docs, key dependencies, recent decisions, codebase structure summary. Used to assemble LLM prompts for domain work. | Every time the orchestrator routes a task to a domain supervisor (~5-20x/day) |
| `query(entity_id)` | Return metadata and relationships for a specific entity (repo, service, doc). | Ad-hoc, during task context assembly |
| `context_map(workspace_id)` | Return the dependency graph / relationship map for a workspace. | During dev feature planning (Journey 2) |
| `project_registry()` | Return list of all workspaces with their status, kind, and entity counts. Used by the routing model to classify incoming messages by workspace. | On every routing call (~20-50x/day, but response is cached) |
| `search(query_string)` | Full-text search across document titles, content, and metadata. Deterministic (FTS), not vector search. | Ad-hoc, during "find the doc about X" queries |

**What it does NOT expect from Ontos:**
- No task state (that's JohnnyOS's Workflow Ledger)
- No runtime health (that's JohnnyOS's Runtime Registry)
- No raw activity logs or transcripts (that's JohnnyOS's Artifact Store)
- No vector/semantic search (banned in v1, deterministic only)

**Write path:** JohnnyOS never writes to Ontos directly. The promotion pipeline works by writing promoted documents as Markdown files into Ontos-indexed workspace directories. Ontos picks them up on its next index sweep. The boundary is the filesystem, not an API write call.

### Consumer 2: Claude Code / Codex CLI / Manual Orchestration

**How it connects:** MCP client in the IDE or terminal.

**What it needs:** Same tools as JohnnyOS, plus possibly:
- `get_document(document_id or path)` — return the full content of a specific doc
- `list_documents(entity_id, kind?)` — list docs for an entity, optionally filtered by kind

These consumers are interactive. They're a human (Johnny) using an LLM tool to ask "what is this project?" or "show me the architecture doc for canary.work." Response times should be fast (< 1 second for cached queries).

### Consumer 3: Vibing MCP

**How it connects:** MCP client, during its own development phase.

**What it needs:** Same as Claude Code. Vibing MCP uses Ontos to pull codebase context when generating specs or running review boards during its own build process. No special tools beyond what's already listed.

---

## What Ontos v4 MCP Must Own

**Workspace and entity indexing.** Ontos reads `.johnny-os.yaml` manifests (or its own equivalent manifest format) and builds a graph of workspaces → entities → documents → relationships. The index must stay in sync with the filesystem.

**Document management.** Ontos tracks documents with their kind (kernel, strategy, product, atom, runbook, decision, manifest), status (draft, approved, superseded, archived), content hash, and provenance.

**Dependency graph.** Relationships between entities: depends_on, supersedes, fork_of, runs_on, owns. Queryable in both directions.

**Context bundles.** The highest-value tool. A context bundle is a curated, pre-assembled package of the most relevant information about a workspace, sized to fit in an LLM context window. This is what makes Ontos more than a file index — it's a context compiler.

**Staleness detection.** Ontos should know when a document's content hash has changed since last index, when a document hasn't been updated in N months, and when a relationship may be stale.

---

## What Ontos v4 MCP Must NOT Own

**Task state.** No concept of "this feature is blocked" or "this PR needs review." That's JohnnyOS's Workflow Ledger.

**Runtime state.** No concept of "this service is healthy" or "this cron job last ran at 3pm." That's JohnnyOS's Runtime Registry.

**Raw activity.** No session logs, chat transcripts, or event streams. That's JohnnyOS's Workflow Ledger and Artifact Store.

**Prompt templates.** No playbook content, reviewer instructions, or quality gates. That's the Vibing MCP.

The rule from the JohnnyOS proposal: "If you dump everything into Ontos, you'll turn a clean knowledge graph into a landfill."

---

## Architectural Constraints (from JohnnyOS decisions)

| Constraint | Source |
|------------|--------|
| Deterministic retrieval only. No vector search in v1. FTS + graph traversal. | JohnnyOS D6 |
| Independent service with own repo, versioning, process lifecycle. Not a JohnnyOS component. | JohnnyOS D14 |
| Runs on Mac Mini hub. Must be lightweight and reliable (uptime over compute). | JohnnyOS hardware topology |
| Multiple concurrent consumers (JohnnyOS daemon, Claude Code, Codex CLI). Must handle concurrent reads. | JohnnyOS architecture |
| Read-only from consumers' perspective. Writes happen via filesystem (promotion pipeline writes Markdown files to workspace directories). | JohnnyOS promotion pipeline |
| Must survive JohnnyOS being down. Must function as a standalone service. | JohnnyOS D14 |
| Registered as a `runtime_asset` in JohnnyOS with health checks. | JohnnyOS external dependencies spec |

---

## What Exists Today (Starting Point)

Ontos v3.x exists on PyPI as a Python package/CLI. It already has:
- Document types and YAML frontmatter parsing
- Graph structure (entities and relationships)
- "Space vs Time" conceptual separation
- CLI tools including `ontos scaffold`
- Coverage on ~10 of Johnny's 23 projects

What it lacks for v4:
- MCP server mode (the primary v4 deliverable)
- Context bundle generation (the highest-value tool)
- Multi-consumer concurrent access
- Full coverage across all active workspaces
- Integration with the `.johnny-os.yaml` manifest format (or an Ontos-native equivalent)

---

## Questions the Proposal Session Should Answer

1. **Does Ontos use its own manifest format or adopt `.johnny-os.yaml`?** The JohnnyOS manifest contains workspace, entity, and runtime_asset definitions. Ontos only cares about workspace and entity data. Options: read the same manifest and ignore runtime fields, or maintain a separate Ontos-specific manifest.

2. **How does Ontos serve the MCP protocol?** stdio (for Claude Code/Codex), HTTP/SSE (for JohnnyOS daemon), or both? What's the transport?

3. **What's the indexing strategy?** Full re-index on startup? Filesystem watcher for incremental updates? Manual re-index command? How often does the graph refresh?

4. **What's the context bundle algorithm?** This is the core intellectual problem. Given a workspace_id, how does Ontos decide what goes in the bundle? What's the size budget? How does it rank document relevance without vector search?

5. **What's the storage backend?** Ontos v3 uses the filesystem. Does v4 add SQLite for the graph index? Or stay pure filesystem?

6. **What's the migration path from v3 to v4?** Existing Ontos-managed workspaces need to continue working. The MCP server is additive, not a rewrite.

7. **How does Ontos handle the 13 undocumented projects?** Johnny has ~10 projects with Ontos coverage and ~13 without. Does v4 bootstrap from `.johnny-os.yaml` manifests for the undocumented ones, or does it require full Ontos onboarding?

---

## Acceptance Criteria (from JohnnyOS Phase 3)

The Ontos v4 MCP is done when:
1. `ontos serve --mcp` runs and responds to MCP tool calls.
2. A client can call `get_context_bundle("canary-work")` and receive a coherent, sized context package.
3. A client can call `project_registry()` and get all active workspaces with metadata.
4. A client can call `search("simhash")` and get relevant document hits via FTS.
5. All 5-6 active workspaces (canary.work, role-evaluator-bot, finance-engine, ohjonathan.com, folio, ontos-dev) are indexed and queryable.
6. The server handles concurrent read requests from multiple clients without corruption or blocking.
7. The server runs as a persistent process on the Mac Mini with health-check endpoint.
