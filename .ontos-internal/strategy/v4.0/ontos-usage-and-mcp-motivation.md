# Ontos Cross-Repo Usage and MCP Motivation

> Detailed technical reference for how Project Ontos is used across a 23-project portfolio.
> Purpose: Feed to an LLM to write the Ontos MCP server proposal.
> Last updated: 2026-04-04

---

## 1. Executive Summary

**Project Ontos** is a local-first documentation management system for AI-assisted development. It is a Python CLI tool published on PyPI as `ontos` (v3.4.0, Apache-2.0). Ontos creates portable knowledge graphs using markdown files with YAML frontmatter — no cloud service, no vendor lock-in, no database.

**Portfolio scale:** 23 projects in `/Users/jonathanoh/Dev`, tracked by a central `.dev-hub/` orchestration layer. 11 projects have active Ontos context maps, collectively managing ~400+ tracked documents. The `.dev-hub/registry/projects.json` provides a machine-readable index of all projects, extracting Tier 1 metadata from each project's `Ontos_Context_Map.md`.

**Current cross-repo orchestration** is read-only and file-scanning-based. There is no programmatic API. Agents must read file artifacts (AGENTS.md, CLAUDE.md, Ontos_Context_Map.md) manually for each project.

**v4.0 roadmap** targets MCP (Model Context Protocol) as the primary interface, replacing file-based context loading with a programmatic server that exposes Resources and Tools. This document captures the full current state to inform that proposal.

---

## 2. Ontos Core Architecture

### 2.1 Document Type Hierarchy

Every Ontos document belongs to one of five types, organized in a strict dependency hierarchy. Dependencies flow downward — higher-rank documents can depend on lower-rank ones, not vice versa.

Source: `Ontos-dev/ontos/core/ontology.py`

```python
TYPE_DEFINITIONS = {
    "kernel": TypeDefinition(
        name="kernel", rank=0,
        description="Foundational principles - mission, values, core identity",
        can_depend_on=("kernel",),
        valid_statuses=("active", "draft", "deprecated", "scaffold", "pending_curation"),
    ),
    "strategy": TypeDefinition(
        name="strategy", rank=1,
        description="Goals, direction, roadmap - business decisions",
        can_depend_on=("kernel",),
        valid_statuses=("active", "draft", "deprecated", "rejected", "complete", "scaffold", "pending_curation"),
    ),
    "product": TypeDefinition(
        name="product", rank=2,
        description="User-facing specifications - features, requirements",
        can_depend_on=("kernel", "strategy"),
        valid_statuses=("active", "draft", "deprecated", "scaffold", "pending_curation"),
    ),
    "atom": TypeDefinition(
        name="atom", rank=3,
        description="Technical specs, architecture, implementation details",
        can_depend_on=("kernel", "strategy", "product", "atom"),
        valid_statuses=("active", "draft", "deprecated", "complete", "scaffold", "pending_curation"),
    ),
    "log": TypeDefinition(
        name="log", rank=4,
        description="Session history - temporal records of work",
        can_depend_on=(),
        valid_statuses=("active", "archived", "auto-generated", "scaffold", "pending_curation"),
        uses_impacts=True,
    ),
}
```

**Key constraints:**
- `kernel` can only depend on other `kernel` documents
- `strategy` can only depend on `kernel`
- `product` can depend on `kernel` or `strategy`
- `atom` can depend on anything except `log`
- `log` has no `depends_on` — it uses `impacts` instead (what documents it affected)

### 2.2 Document Data Model

Source: `Ontos-dev/ontos/core/types.py`

```python
@dataclass
class DocumentData:
    id: str                              # Unique snake_case identifier, immutable
    type: DocumentType                   # kernel|strategy|product|atom|log
    status: DocumentStatus               # draft|active|deprecated|rejected|complete|scaffold|pending_curation|in_progress
    filepath: Path                       # Absolute path to the markdown file
    frontmatter: Dict[str, Any]          # Raw YAML frontmatter dict
    content: str                         # Markdown body text
    depends_on: List[str] = []           # IDs of documents this depends on
    impacts: List[str] = []              # IDs of documents this impacts (log only)
    tags: List[str] = []                 # Concept tags for filtering
    aliases: List[str] = []              # Alternative IDs for discovery
    describes: List[str] = []            # File paths this document describes

class CurationLevel(IntEnum):
    SCAFFOLD = 0   # Auto-generated placeholder (minimal validation)
    STUB = 1       # User provides goal only (no dependencies required)
    FULL = 2       # Complete Ontos document (all fields required, strict validation)

class DocumentType(str, Enum):
    KERNEL = "kernel"
    STRATEGY = "strategy"
    PRODUCT = "product"
    ATOM = "atom"
    LOG = "log"
    REFERENCE = "reference"
    CONCEPT = "concept"
    UNKNOWN = "unknown"

class ValidationErrorType(Enum):
    DUPLICATE_ID = "duplicate_id"
    BROKEN_LINK = "broken_link"
    CYCLE = "cycle"
    ORPHAN = "orphan"
    ARCHITECTURE = "architecture"    # Dependency direction violation
    SCHEMA = "schema"
    STATUS = "status"
    STALENESS = "staleness"
    CURATION = "curation"
    IMPACTS = "impacts"
    DEPTH = "depth"
```

### 2.3 Frontmatter Schema

Every Ontos document requires YAML frontmatter between `---` delimiters. Real example from `canary.work/docs/kernel/soul.md`:

```yaml
---
id: soul
type: kernel
status: draft
ontos_schema: "2.2"
curation_level: 2
generated_by: ontos scaffold
---
```

Required fields: `id`, `type`, `status`. Optional: `depends_on`, `impacts`, `tags`, `aliases`, `describes`, `ontos_schema`, `curation_level`, `summary`, `date`, `decision_summary`, `decision_rationale`, `alternatives_rejected`, `migration_status`.

### 2.4 Dependency Graph Engine

Source: `Ontos-dev/ontos/core/graph.py`

```python
@dataclass
class DependencyGraph:
    nodes: Dict[str, GraphNode] = {}           # doc_id -> GraphNode
    edges: Dict[str, List[str]] = {}           # doc_id -> [depends_on IDs]
    reverse_edges: Dict[str, List[str]] = {}   # doc_id -> [depended_by IDs]
```

- `build_graph(docs)` returns `Tuple[DependencyGraph, List[ValidationError]]`
- Cycle detection uses O(V+E) DFS
- Severity levels: `depends_on` = error (structural), `impacts`/`describes` = warning (informational)
- Broken link detection includes fuzzy candidate suggestions (v3.2+)

### 2.5 Configuration

Source: `Ontos-dev/ontos/core/config.py`

```python
@dataclass
class OntosConfig:
    ontos: OntosSection          # version, required_version
    paths: PathsConfig           # docs_dir, logs_dir, context_map
    scanning: ScanningConfig     # skip_patterns, scan_paths, default_scope
    validation: ValidationConfig # max_dependency_depth, allowed_orphan_types
    workflow: WorkflowConfig     # log_retention_count
    hooks: HooksConfig           # pre_push, pre_commit, strict
```

Real `.ontos.toml` example (standard across most projects):

```toml
[ontos]
version = "3.0"

[paths]
docs_dir = "docs"
logs_dir = "docs/logs"
context_map = "Ontos_Context_Map.md"

[scanning]
skip_patterns = ["_template.md", "archive/*", ".git/*", "node_modules/*"]

[validation]
max_dependency_depth = 5
allowed_orphan_types = ["atom"]

[workflow]
log_retention_count = 20

[hooks]
pre_push = true
pre_commit = true
strict = false
```

---

## 3. CLI Commands Reference

Source: `Ontos-dev/ontos/cli.py`

All commands support global flags: `--quiet` (`-q`), `--json` (JSON envelope output). Most commands support `--scope [docs|library]` to optionally include `.ontos-internal/` documents.

| Command | Purpose | Key Flags |
|---------|---------|-----------|
| `init` | Initialize Ontos in a project | `--force`, `--scaffold`, `--skip-hooks`, `--yes` |
| `map` | Generate Ontos_Context_Map.md | `--compact [basic\|rich\|tiered]`, `--strict`, `--obsidian`, `--filter EXPR`, `--sync-agents` |
| `log` | End-of-session logging | `--event-type`, `--source`, `--title`, `--auto` |
| `doctor` | Health check (7 diagnostics) | `--verbose` |
| `maintain` | Weekly maintenance (8 tasks) | `--dry-run`, `--skip TASK`, `--verbose` |
| `link-check` | Validate internal references | (scope only) |
| `rename` | Atomic ID rename across graph | `old_id new_id`, `--apply` (dry-run default) |
| `scaffold` | Add frontmatter to markdown files | `--apply` (dry-run default), paths |
| `promote` | Promote documents to Level 2 | `--check`, `--all-ready`, files |
| `query` | Graph queries | `--depends-on ID`, `--depended-by ID`, `--concept TAG`, `--stale DAYS`, `--health`, `--list-ids` |
| `export data` | JSON graph export | `--type`, `--status`, `--concept`, `--no-content`, `--deterministic` |
| `export claude` | Generate CLAUDE.md | `--force` |
| `agents` | Generate AGENTS.md + .cursorrules | `--force`, `--all`, `--format [agents\|cursor]` |
| `verify` | Verify describes dates | `--all`, `--date` |
| `consolidate` | Archive old session logs | `--count N`, `--by-age`, `--days N`, `--dry-run` |
| `schema-migrate` | Migrate schema versions | `--check`, `--dry-run`, `--apply` |
| `env` | Detect environment manifests | `--write`, `--format [text\|json]` |
| `stub` | Create stub documents | (scaffolding variant) |
| `migration-report` | Migration status report | (filtering) |

Hidden commands (internal): `agent-export`, `hook`, `tree`, `validate`.

**JSON envelope output:** Every command with `--json` emits a structured envelope:
```json
{
  "status": "success|error",
  "command": "map",
  "exit_code": 0,
  "message": "Context map generated",
  "data": { ... }
}
```

---

## 4. Context Map Generation — The Core Output

Source: `Ontos-dev/ontos/commands/map.py` (32KB, the largest command module)

The context map (`Ontos_Context_Map.md`) is the single most important artifact for AI agent consumption. It is auto-generated by `ontos map` and provides a tiered index of the project's knowledge graph.

### 4.1 The 3-Tier Architecture

**Tier 1: Essential Context (~2k token hard cap)**
- Project Summary: name, doc count, last updated timestamp
- Recent Activity: 3 most recent logs (sorted by date frontmatter)
- In Progress: documents with status `in_progress` (max 5)
- Key Documents: top 3 by in-degree in dependency graph (most depended-on)
- Critical Paths: docs root, logs directory

Token budgeting: sections are added sequentially; if the running token count exceeds 2,000, remaining sections are truncated with a notice.

**Tier 2: Document Index**
Full table of every tracked document:
```
| Path | ID | Type | Status |
|------|-----|------|--------|
```

**Tier 3: Full Graph Details**
- Validation section (errors, warnings by category)
- Dependency tree visualization (hierarchical, by type groups: KERNEL, STRATEGY, PRODUCT, ATOM)
- Recent Activity timeline (all logs)
- Staleness check (documents with `describes` field)
- Optional lint warnings

### 4.2 Context Map YAML Frontmatter

```yaml
---
id: ontos_context_map
type: reference
status: generated
ontos_map_version: 2
generated_by: ontos map
generated_at: 2026-03-22 16:23:17
---
```

### 4.3 Compact Output Modes

For token-constrained agents, `ontos map --compact` provides compressed alternatives:

- **BASIC**: One line per doc: `id:type:status`
- **RICH**: One line per doc: `id:type:status:"summary"`
- **TIERED** (v3.4.0): Tier 1 prose summary + type-ranked compact. Kernel+strategy get RICH format, product+atom get BASIC, logs get count + latest only.

### 4.4 Real Examples

**canary.work** (46 docs):
```
## Tier 1: Essential Context

### Project Summary
- **Name:** canary.work
- **Doc Count:** 46
- **Last Updated:** 2026-03-22 20:23:17 UTC

### Key Documents
- `soul` (6 dependents) — docs/kernel/soul.md
- `prd_canary_work` (4 dependents) — docs/product/prd-canary-work.md
```

**role-evaluator-bot** (76 docs):
```
## Tier 1: Essential Context

### Project Summary
- **Name:** role-evaluator-bot
- **Doc Count:** 76
- **Last Updated:** 2026-03-31 00:58:07 UTC

### Key Documents
- `prd` (28 dependents) — docs/product/PRD.md
- `yc_company_discovery` (7 dependents) — docs/strategy/proposal/yc_company_discovery.md
- `roadmap` (6 dependents) — docs/product/ROADMAP.md
```

---

## 5. JSON Export Schema

Source: `Ontos-dev/ontos/commands/export_data.py`

The `ontos export data` command produces the richest machine-readable output. An MCP server would likely use this format (or a subset) as its primary data source.

### Schema: `ontos-export-v1`

```json
{
  "schema_version": "ontos-export-v1",
  "provenance": {
    "exported_at": "2026-04-04T12:00:00",
    "ontos_version": "3.4.0",
    "git_commit": "abc1234",
    "project_root": "/Users/jonathanoh/Dev/canary.work"
  },
  "filters": {
    "types": null,
    "status": null,
    "concepts": null
  },
  "summary": {
    "total_documents": 46,
    "by_type": { "kernel": 2, "strategy": 3, "product": 4, "atom": 5, "log": 32 },
    "by_status": { "active": 40, "draft": 4, "deprecated": 2 },
    "warnings": []
  },
  "documents": [
    {
      "id": "soul",
      "type": "kernel",
      "status": "draft",
      "path": "docs/kernel/soul.md",
      "depends_on": [],
      "concepts": ["identity", "values"],
      "decision_summary": null,
      "decision_rationale": null,
      "alternatives_rejected": null,
      "migration_status": null,
      "content": "# Soul\n\ncanary.work is...",
      "content_hash": "sha256:a1b2c3d4e5f6"
    }
  ],
  "graph": {
    "nodes": ["soul", "prd_canary_work", "..."],
    "edges": [
      { "from": "prd_canary_work", "to": "soul", "type": "depends_on" }
    ]
  }
}
```

Key features:
- Content hashing via SHA256 (truncated to 16 chars) for change detection
- Deterministic mode (`--deterministic`) for reproducible output (sorted keys, stable timestamps)
- Filter support: `--type strategy,product`, `--status active`, `--concept auth`
- `--no-content` flag to exclude document body (metadata-only export)
- Migration status classification integrated from `ontos.core.migration`

---

## 6. Dev-Hub Cross-Repo Orchestration Layer

The `.dev-hub/` directory at the Dev root is a read-only orchestration layer that maintains a machine-readable index of all 23 projects without modifying them.

### 6.1 Registry Architecture

Source: `.dev-hub/registry/schema.json` (`dev-hub-registry-v1`)

**Root object:**
```json
{
  "$schema": "./schema.json",
  "version": 1,
  "generated_at": "2026-03-22T20:57:00-04:00",
  "dev_root": "/Users/jonathanoh/Dev",
  "project_count": 23,
  "projects": [ ... ]
}
```

**ProjectEntry schema:**
```json
{
  "slug": "string",                          // Directory name
  "path": "string",                          // Relative path from Dev root
  "has_readme": "boolean",
  "has_context_map": "boolean",
  "readme_path": "string|null",
  "context_map_path": "string|null",
  "ontos_project_name": "string|null",       // Extracted from context map Tier 1
  "ontos_doc_count": "integer|null",         // Extracted from context map Tier 1
  "ontos_last_updated": "ISO8601|null",      // Extracted from context map
  "status": "documented|partial|undocumented",
  "tags": ["array", "of", "strings"],
  "notes": "string|null"
}
```

Status classification:
- `documented`: Both README.md and Ontos_Context_Map.md exist
- `partial`: One but not the other
- `undocumented`: Neither exists

### 6.2 Data Flow (Registry Regeneration)

The 4-step process documented in `.dev-hub/README.md`:

1. **Scan** all non-hidden subdirectories in Dev/
2. **Check** for `README.md` and `Ontos_Context_Map.md` at each project root
3. **Extract** Tier 1 metadata from context maps (project name, doc count, last updated)
4. **Write** `registry/projects.json` following `registry/schema.json`

This process is currently manual. There is no automation (no cron, no CI, no file watcher).

### 6.3 Live Portfolio Snapshot

From `projects.json` (generated 2026-03-22):

| Project | Status | Doc Count | Last Updated | Tags |
|---------|--------|-----------|--------------|------|
| Ontos-dev | documented | 50 | 2026-03-22 | production, tooling |
| canary.work | documented | 46 | 2026-03-22 | production |
| finance-engine | documented | 88 | 2026-02-02 | production |
| finance-engine-2.0 | documented | 55 | 2026-03-22 | production |
| folio.love | documented | 50 | 2026-03-16 | production |
| role-evaluator-bot | documented | 76 | 2026-03-22 | production |
| ohjonathan.com-sandbox | documented | 14 | 2026-02-17 | demo |
| Personal-ERP | documented | null | 2025-12-11 | personal, production |
| Project-Ontos-OLD | documented | null | 2026-01-19 | archived |
| oh.gold | documented | 1 | 2026-01-05 | personal |
| ohjonathan.com | partial | 16 | 2026-02-17 | production |
| NPOLabDev | partial | — | — | production |
| NPOLabDevAB | partial | — | — | production |
| OntosNPOLabTest | partial | — | — | test |
| Vibing | partial | — | — | demo |
| Career | undocumented | — | — | personal |
| agent-skills | undocumented | — | — | tooling |
| claude-code-monitoring | undocumented | — | — | tooling |
| engineering-strategy | undocumented | — | — | personal |
| strategy-eng | undocumented | — | — | personal |
| Test-Personal-ERP | undocumented | — | — | test |
| TestOntos | undocumented | — | — | test |
| temp | undocumented | — | — | temp |

**Aggregates:** 10 documented, 5 partial, 8 undocumented. ~396 tracked documents across all projects with counts.

### 6.4 Lineage Tracking

The registry tracks project evolution chains in the `notes` field:

- `Project-Ontos-OLD` -> `Ontos-dev` (proprietary v3.0.x -> Apache-2.0 v3.3.1+)
- `finance-engine` -> `finance-engine-2.0` (Python -> TypeScript rewrite)
- `Personal-ERP` -> `Test-Personal-ERP` (production -> test fork)
- `ohjonathan.com` -> `ohjonathan.com-sandbox` (main site -> sandbox)
- `NPOLabDev` -> `NPOLabDevAB` -> `OntosNPOLabTest` (primary -> A/B variant -> Ontos integration test)

### 6.5 Hard Constraint: Read-Only

From `.dev-hub/README.md`: "This orchestrator is **read-only** with respect to all project subfolders. It never creates, modifies, or deletes any file outside `.dev-hub/`."

An MCP server must also respect this constraint for cross-project operations.

### 6.6 Human-Readable Outputs

- `docs/portfolio-overview.md` (19KB) — Detailed summaries of all 23 projects, tech stacks, relationships
- `docs/architecture-diagrams.md` (1,021 lines) — Mermaid diagrams for all major projects
- `backlog.md` — Curated list of undocumented projects, lineage candidates, future enhancement ideas

---

## 7. Per-Project Ontos Adoption Matrix

| Project | .ontos.toml | Context Map | Doc Count | Last Updated | AGENTS.md | CLAUDE.md |
|---------|:-----------:|:-----------:|:---------:|:------------:|:---------:|:---------:|
| Ontos-dev | Yes | Yes (87KB) | 50 | 2026-04-04 | Yes | Yes |
| canary.work | Yes | Yes | 46 | 2026-03-22 | Yes | Yes |
| finance-engine | Yes | Yes | 88 | 2026-02-02 | Yes | Yes |
| finance-engine-2.0 | Yes | Yes | 55 | 2026-03-22 | Yes | Yes |
| folio.love | No | Yes | 50 | 2026-03-16 | Unknown | Unknown |
| role-evaluator-bot | Yes | Yes | 76 | 2026-03-22 | Yes | Yes |
| ohjonathan.com | Yes | Yes | 16 | 2026-02-17 | Unknown | Unknown |
| ohjonathan.com-sandbox | Yes | Yes | 14 | 2026-02-17 | Unknown | Unknown |
| Personal-ERP | Unknown | Yes (v1) | null | 2025-12-11 | Unknown | Unknown |
| Project-Ontos-OLD | Unknown | Yes (v1) | null | 2026-01-19 | Unknown | Unknown |
| oh.gold | Unknown | Yes (v1) | 1 | 2026-01-05 | Unknown | Unknown |

**Notable variations:**
- **oh.gold**: Minimal adoption (1 doc), older v1 context map format
- **Personal-ERP** and **Project-Ontos-OLD**: Older v1 context maps with null doc counts in the registry (metadata extraction wasn't available for v1 format)
- **folio.love**: Has a context map but no `.ontos.toml` (possible manual/legacy setup, 50 docs)
- **Ontos-dev**: Uses "Contributor Mode" — a different context map format that scans `.ontos-internal/` in addition to `docs/`, resulting in an 87KB context map

---

## 8. Workflows and Usage Patterns

### 8.1 Session Start/End Protocol

From `Ontos-dev/CLAUDE.md` (the activation protocol used across all Ontos-adopting projects):

```
At the start of every session:
1. Run `ontos map` to generate the context map
2. Read `Ontos_Context_Map.md` to understand the project documentation structure

When ending a session:
3. Run `ontos log` to record your work
```

AI agents (Claude Code, Cursor, ChatGPT) read `AGENTS.md` or respond to the trigger word "Ontos" to activate this protocol. The agent runs `ontos map`, reads the generated context map (Tier 1 minimum, expanding to Tier 2/3 as needed), loads relevant documents via `depends_on` graph traversal, and proceeds with work.

### 8.2 Maintenance Cycle

`ontos maintain` runs 8 tasks (typically weekly):

1. `migrate_untagged` — Scaffold untagged markdown files
2. `regenerate_map` — Regenerate context map
3. `health_check` — Run doctor diagnostics
4. `curation_stats` — Report curation level distribution
5. `consolidate_logs` — Archive old session logs
6. `review_proposals` — Check for pending curation reviews
7. `check_links` — Validate internal references
8. `sync_agents` — Regenerate AGENTS.md and .cursorrules

Each task can be skipped individually with `--skip TASK_NAME`.

### 8.3 Documentation-as-Code Workflow

New documentation follows a curation lifecycle:

1. **Scaffold** (`ontos scaffold`): Auto-generates YAML frontmatter (L0 — minimal validation)
2. **Stub** (`ontos stub`): User provides a goal statement (L1 — no dependencies required)
3. **Promote** (`ontos promote`): Validates and elevates to L2 (full validation — all fields required, dependency constraints enforced)
4. **Validate** (`ontos doctor`, `ontos link-check`): Ongoing health checks

### 8.4 Cross-Project Context Loading (Current Manual Workflow)

Today, to load cross-project context, a human or agent must:

1. Open `.dev-hub/registry/projects.json`
2. Parse the JSON to identify relevant projects (by tags, status, or doc counts)
3. Navigate to each project's `Ontos_Context_Map.md`
4. Read Tier 1 from each context map manually
5. Optionally load specific documents via `depends_on` traversal

There is no automated cross-project querying, no single command to search across repos, and no way to get a unified view without reading multiple files.

### 8.5 Agent Artifact Generation

Ontos generates three types of AI agent activation files:

- **AGENTS.md** (`ontos agents`): Auto-generated with project state, activation protocol, trigger phrases, and Tier 1 context loading instructions
- **.cursorrules** (`ontos agents --all`): Generated rules file for Cursor IDE
- **CLAUDE.md** (`ontos export claude`): Activation instructions for Claude Code sessions

---

## 9. Pain Points and MCP Motivation

These are the specific gaps in the current file-based approach that motivate building an MCP server.

### 9.1 Manual Cross-Project Queries

To answer "which projects have stale documentation?" you must: open `projects.json`, parse 330 lines of JSON, compute date deltas manually. There is no `ontos query --stale` equivalent that works across projects. The `--stale` flag only works within a single project.

The dev-hub `backlog.md` lists these as future work:
- "Cross-project dependency tracking"
- "Staleness detection — flag projects whose Context Maps haven't been updated in 30+ days"
- "Auto-refresh registry"

### 9.2 No Programmatic Activation

AI agents must read file-based artifacts (AGENTS.md, CLAUDE.md, Ontos_Context_Map.md) from the filesystem. There is no API, no server, no programmatic interface. The agent must know the file paths, read them, and parse the markdown manually.

An MCP server would expose these as Resources with URIs, letting agents browse metadata before loading content.

### 9.3 Token Overhead

Each context map is a full markdown file. Even with the `--compact tiered` mode (v3.4.0), the agent must load the entire file to get metadata. The Ontos-dev context map alone is 87KB.

An MCP server could serve metadata-first (resource list with URIs and descriptions), letting agents request only what they need. The existing MCP research doc describes this: "Instead of sending file contents immediately, the MCP server sends a Resource List containing only URIs and metadata."

### 9.4 Registry Staleness

`projects.json` is a manual snapshot (generated_at: 2026-03-22). It is 13+ days stale as of this writing. There is no auto-refresh mechanism — no cron job, no file watcher, no CI pipeline.

An MCP server could regenerate the registry on demand or cache it with TTL-based invalidation.

### 9.5 No Cross-Project Graph Queries

`ontos query --depends-on ID` works within a single project. There is no way to:
- Trace dependencies between projects
- Find cross-repo concept clusters (e.g., "all documents tagged `auth` across all projects")
- Get a unified dependency graph spanning multiple repos
- Search for a document ID across the portfolio

### 9.6 No Subscription/Notification Model

The MCP research doc (Section 4.1.1) describes the MCP subscription model: "The agent can subscribe to a metadata resource. If the underlying file system changes, the sidecar pushes a notification." Currently, agents have no way to know when a context map has gone stale. They must re-read files and compare timestamps manually.

### 9.7 Competitive Pressure

From internal strategy reviews:
- v3.0.5 review: "Competitors in the context engineering space (CTX, Claude Code's built-in memory, Cursor's project context) are shipping MCP integrations now."
- v3.1.0 Spec Review accepted the MCP deferral to v4.0 but noted "competitive pressure remains."

---

## 10. Existing MCP Research Summary

Source: `Ontos-dev/.ontos-internal/strategy/v3.1/20260119_Agent-Optimized Documentation & Metadata.md`

This 200+ line research document establishes the strategic foundation for the MCP server. Key findings:

### 10.1 MCP Sidecar Architecture

The Model Context Protocol (MCP) serves as the industry-standard implementation of the "sidecar pattern" for LLMs. In this architecture:

- **MCP Server** acts as a sidecar process alongside the agent
- **Resources** (files, data) and **Tools** (functions) are exposed to the LLM client
- **Metadata-first retrieval**: The server sends a Resource List containing only URIs and metadata (name, description, MIME type) — not file contents. The agent browses available information without paying the token cost of reading it.
- **Subscription model**: Agents subscribe to metadata resources. If the underlying filesystem changes, the sidecar pushes a notification. This enables "live" maps without constant re-polling.

### 10.2 Deterministic Metadata Filtering over Vector RAG

For small-to-medium repositories (under 50k tokens), the research recommends **Deterministic Metadata Filtering** over vector RAG:

- Vector RAG introduces stochastic failure modes ("retrieval loss" from semantic mismatch)
- Structured queries against metadata fields (`--tag`, `--type`, `--concept`) are more reliable for code tasks
- Code references rely on exact symbol names and structural relationships, better captured by tags and dependency graphs

### 10.3 The Navigator Pattern

A two-phase workflow for cost optimization:

- **Phase 1 (Navigator)**: A lightweight model (e.g., Claude Haiku, Gemini Flash) scans the metadata index to identify candidate files. It does not solve the problem — only locates context.
- **Phase 2 (Orchestrator)**: The capable model (e.g., Claude Opus, Sonnet) receives the curated candidate list and loads only the necessary files for reasoning.

**Economic impact**: Up to ~90% token cost reduction by using a cheap model for high-volume filtering.

### 10.4 Token Efficiency Research

Key findings on representation formats:
- JSON has a ~40-60% "punctuation tax" compared to optimized formats (due to BPE tokenization of braces, quotes, commas)
- XML tags recommended by Anthropic for delimiting sections (more robust than markdown backticks)
- Markdown tables improve reasoning accuracy ~+16% over CSV despite higher token cost
- The "Sparse Metadata Tree" combines visual hierarchy with semantic annotations

### 10.5 Existing Infrastructure for MCP

The current Ontos CLI already provides building blocks:
- **`--json` flag** on all commands: Every CLI command outputs structured JSON envelopes, enabling a thin MCP wrapper that calls CLI commands and serves results as Resources/Tools
- **`ontos export data`**: Produces the `ontos-export-v1` JSON schema (Section 5) — the closest existing analog to MCP Resource content
- **`ontos query`**: Graph query interface that could map directly to MCP Tools
- **`ontos map --compact tiered`**: Token-optimized context output

### 10.6 Strategic Decisions

- MCP was **deferred from v3.1 to v4.0** (accepted by all reviewers)
- v4.0 roadmap items: "MCP as primary interface, full template system, daemon mode"
- The research doc notes: "Competitors shipping MCP integrations now" — urgency acknowledged but quality prioritized
- Planned approach: MCP server as sidecar wrapping existing CLI commands initially, evolving to native MCP resources

---

## Appendix: File Paths Reference

**Ontos source code:**
- `Ontos-dev/ontos/core/ontology.py` — Type hierarchy definitions
- `Ontos-dev/ontos/core/types.py` — Data model (DocumentData, enums)
- `Ontos-dev/ontos/core/graph.py` — Dependency graph engine
- `Ontos-dev/ontos/core/config.py` — Configuration dataclasses
- `Ontos-dev/ontos/core/frontmatter.py` — YAML frontmatter parsing (11KB)
- `Ontos-dev/ontos/core/validation.py` — Schema validation, cycle detection
- `Ontos-dev/ontos/core/body_refs.py` — Internal link detection in document bodies (23KB)
- `Ontos-dev/ontos/core/staleness.py` — Staleness detection via git history (14KB)
- `Ontos-dev/ontos/cli.py` — Unified CLI (1,200+ lines)
- `Ontos-dev/ontos/commands/map.py` — Context map generation (32KB)
- `Ontos-dev/ontos/commands/export_data.py` — JSON export
- `Ontos-dev/ontos/commands/doctor.py` — Health checks (21KB)
- `Ontos-dev/ontos/commands/maintain.py` — Maintenance runner (29KB)
- `Ontos-dev/ontos/commands/rename.py` — Safe ID renaming (44KB)

**Dev-hub orchestration:**
- `.dev-hub/registry/schema.json` — Registry JSON Schema (v1)
- `.dev-hub/registry/projects.json` — Master project index (23 projects)
- `.dev-hub/README.md` — Orchestrator documentation
- `.dev-hub/backlog.md` — Future enhancements
- `.dev-hub/docs/portfolio-overview.md` — Cross-project summaries (19KB)
- `.dev-hub/docs/architecture-diagrams.md` — Mermaid diagrams (1,021 lines)

**MCP research:**
- `Ontos-dev/.ontos-internal/strategy/v3.1/20260119_Agent-Optimized Documentation & Metadata.md` — MCP architecture research

**Project context maps (examples):**
- `canary.work/Ontos_Context_Map.md` — 46 docs
- `role-evaluator-bot/Ontos_Context_Map.md` — 76 docs
- `finance-engine/Ontos_Context_Map.md` — 88 docs
- `Ontos-dev/Ontos_Context_Map.md` — 50 docs (87KB, Contributor Mode)
