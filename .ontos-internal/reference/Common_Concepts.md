---
id: common_concepts
type: atom
status: active
depends_on: []
---

# Common Concepts

Reference vocabulary for `concepts` field in Session Logs.

## Usage

When tagging a log, check this list first. Use existing terms over synonyms to ensure graph connectivity.

**Example:**
```yaml
# Good - uses standard vocabulary
concepts: [auth, api, db]

# Bad - creates orphan nodes in the graph
concepts: [authentication, endpoints, database-stuff]
```

---

## Vocabulary

### Core Domains

| Concept | Covers | Avoid Using |
|:--------|:-------|:------------|
| `auth` | Authentication, authorization, login, identity, OAuth, JWT | `authentication`, `login`, `identity`, `oauth` |
| `api` | Endpoints, REST, GraphQL, routes, controllers | `endpoints`, `routes`, `rest`, `graphql` |
| `db` | Database, storage, SQL, queries, migrations | `database`, `storage`, `sql`, `postgres` |
| `ui` | Frontend, components, CSS, styling, layout | `frontend`, `components`, `styling`, `css` |
| `schema` | Data models, types, validation, structure | `models`, `types`, `validation`, `data-model` |

### Process Domains

| Concept | Covers | Avoid Using |
|:--------|:-------|:------------|
| `devops` | CI/CD, deployment, hosting, Docker, infrastructure | `deployment`, `ci`, `infrastructure`, `docker` |
| `testing` | Unit tests, integration tests, QA, test coverage | `tests`, `qa`, `test`, `unit-tests` |
| `perf` | Performance, optimization, caching, speed | `performance`, `optimization`, `speed`, `caching` |
| `security` | Vulnerabilities, encryption, access control, secrets | `vulnerabilities`, `encryption`, `secrets` |
| `docs` | Documentation, guides, references, READMEs | `documentation`, `guides`, `readme` |

### Workflow

| Concept | Covers |
|:--------|:-------|
| `cleanup` | Refactoring, dead code removal, organization |
| `config` | Configuration, settings, environment variables |
| `workflow` | Process changes, rituals, automation |

### Documentation Tracking (v2.7)

| Concept | Covers |
|:--------|:-------|
| `describes` | Documentation relationship tracking — marks which atoms a doc describes |
| `staleness` | Detection of outdated documentation when described atoms change |
| `immutable-history` | Auto-generated decision_history.md from session logs |

### Ontos CLI

| Concept | Covers |
|:--------|:-------|
| `activation` | Agent activation phase and `ontos activate` command surface |
| `agents` | `ontos agents` generation and `AGENTS.md` / `.cursorrules` sync |
| `doctor` | `ontos doctor` health check and environment diagnostics |
| `link-check` | `ontos link-check` reference and orphan validation |
| `maintain` | `ontos maintain` weekly maintenance routines and consolidation |
| `print-config` | `ontos print-config` configuration introspection output |
| `promote` | `ontos promote` document promotion across status tiers |
| `rename` | `ontos rename` atomic ID rename across frontmatter and references |
| `retrofit` | `ontos retrofit` bulk frontmatter backfill across documents |

### Ontos Internals

| Concept | Covers |
|:--------|:-------|
| `agentic-activation` | Agentic activation resilience subsystem (v4.4 line) |
| `context-map` | Context map generation, tiered output, summary rendering |
| `frontmatter` | YAML frontmatter parsing, diagnostics, and schema enforcement |
| `mcp` | Model Context Protocol integration (server and tools) |
| `mcp-write-tools` | Write-capable MCP tool surface and authorization |
| `obsidian` | Obsidian-compatible output, wikilinks, vault integration |
| `scanner` | Document scanner, discovery, and load pipeline |
| `serverinfo` | MCP `serverInfo` handshake and capability advertisement |
| `tools-list` | MCP `tools/list` endpoint and tool registration |
| `outputschema` | MCP `outputSchema` definitions and validation |
| `fastmcp` | FastMCP library integration and lifecycle |
| `unified-loader` | Unified document loader pipeline |

### Project Lifecycle

| Concept | Covers |
|:--------|:-------|
| `command-safety` | Command safety hardening, validation, allowlists |
| `curation` | Document curation, selection, archive policy |
| `external-review` | External reviewer feedback cycles and remediation |
| `hardening` | Code/feature hardening, defensive fixes, edge-case closure |
| `onboarding` | User/agent onboarding flows and first-run experience |
| `packaging` | Python packaging, distribution, PyPI release plumbing |
| `portfolio` | Portfolio-level changes spanning multiple repos or projects |
| `proposals` | Project proposal documents and pre-implementation specs |
| `release` | Release coordination, tagging, version bumps |

### Surface & Output

| Concept | Covers |
|:--------|:-------|
| `bundle-config` | Context bundle configuration and assembly |
| `client-config` | Client-side configuration (e.g., MCP client setup) |
| `cli` | CLI surface, command interface, argument parsing |
| `cli-surface` | Public CLI surface contract and compatibility |
| `compact` | Compact output mode (`basic` / `rich` / `tiered`) |
| `tiered` | Tiered output formatting and token-budget rendering |
| `exports` | Document and graph export functionality |

### Integrations

| Concept | Covers |
|:--------|:-------|
| `antigravity` | Antigravity tool integration and onboarding hooks |
| `claude-code` | Claude Code CLI integration and instructions |
| `cursor` | Cursor IDE integration via `.cursorrules` and AGENTS |

### Building Blocks

| Concept | Covers |
|:--------|:-------|
| `flock-locks` | File-lock concurrency primitives via `flock(2)` |
| `fts` | Full-Text Search backend and indexing |
| `registry-path` | Tool/plugin registry path resolution |
| `stdio` | Standard I/O transport (e.g., MCP stdio mode) |
| `unicode` | Unicode handling, normalization, encoding |

---

## Adding New Concepts

If no existing concept fits:

1. **Check first** — Can a broader existing concept work?
2. **Be conservative** — Fewer concepts with clear scope > many overlapping concepts
3. **Follow conventions:**
   - Lowercase
   - Single words preferred
   - Hyphens for multi-word (`data-model` not `dataModel`)
4. **Document it** — Add to this file with clear scope
5. **Update existing logs** — If applicable to past work

---

## Why This Matters (v3.0)

This vocabulary enables subgraph queries:

```bash
# Future capability (v3.0)
python3 .ontos/scripts/ontos_query.py --concept auth --hops 2
```

**Consistent tagging now = accurate retrieval later.**
