---
id: migration_v3_to_v4
type: reference
status: active
depends_on: [ontos_manual]
---

# Migration Guide: v3.x → v4.x

This guide covers the new capabilities in Ontos v4.0 and v4.1 and how to enable them. **There are no breaking changes** — all existing CLI commands, configuration, and frontmatter schemas are preserved.

## What's New in v4.0

### MCP Server Mode

Ontos v4.0 adds an MCP (Model Context Protocol) server that exposes your knowledge graph directly to AI agents and IDEs. Instead of agents shelling out to CLI commands, they connect to a persistent `ontos serve` process and call structured tools.

**Before (v3.x):** Agents run CLI commands and parse text output.
```bash
ontos map --compact tiered
ontos query --depends-on auth_flow
```

**After (v4.0):** Agents call MCP tools and receive structured JSON.
```
workspace_overview()  → project orientation, key docs, graph stats
get_document("auth_flow")  → full content, frontmatter, dependencies
```

### New Command: `ontos serve`

Starts a stdio MCP server for the current workspace:
```bash
ontos serve                    # Serve current directory
ontos serve --workspace /path  # Serve a specific project
```

### Optional Dependency Extra

MCP support is opt-in. The base package is unchanged:
```bash
pip install ontos            # Same as before — no new dependencies
pip install 'ontos[mcp]'    # Adds mcp>=1.27.0 and pydantic>=2.0
```

> **Note:** MCP requires Python 3.10+. All other Ontos commands continue to work on Python 3.9+.

### 8 Core MCP Tools (v4.0)

| Tool | Purpose |
|------|---------|
| `workspace_overview` | Structured orientation — key documents, graph stats, warnings |
| `context_map` | Full context map markdown (supports compact modes: basic, rich, tiered, full) |
| `get_document` | Read one document by ID or path, with full frontmatter and metadata |
| `list_documents` | Paginated listing with optional type/status filters |
| `export_graph` | Structured graph export (summary or full, optional file output) |
| `query` | Dependency details for a single document |
| `health` | Server uptime, document count, index freshness, version |
| `refresh` | Force cache rebuild after bulk changes |

### 7 New MCP Tools (v4.1)

**Bundle tool (always available):**

| Tool | Purpose |
|------|---------|
| `get_context_bundle` | Token-budgeted context bundle for a workspace |

`get_context_bundle` is always registered. In portfolio mode it queries the portfolio index; otherwise it builds a bundle from the served workspace.

**Portfolio tools (requires `--portfolio` flag):**

| Tool | Purpose |
|------|---------|
| `project_registry` | Inventory of all known workspaces |
| `search` | FTS5 full-text search across workspaces |

**Write tools (mutable mode only — omitted when `--read-only`):**

| Tool | Purpose |
|------|---------|
| `scaffold_document` | Create a new markdown file with scaffold frontmatter |
| `log_session` | Create a dated session log |
| `promote_document` | Change curation level without moving the file |
| `rename_document` | Rename an ID across all referencing files |

All write tools use advisory flock locking (`workspace_lock()`) for cross-process safety and perform rollback-then-rebuild recovery on commit failure.

All tools are read-only except `export_graph` with `export_to_file` (writes within workspace root) and the four write tools above.

### File-Mtime Cache Invalidation

The MCP server detects document changes automatically using file-mtime fingerprinting. When you edit a document, the next tool call serves fresh data — no manual refresh needed.

### Configuration

An optional `[mcp]` section in `.ontos.toml` controls usage logging:
```toml
[mcp]
usage_logging = true
usage_log_path = "~/.config/ontos/usage.jsonl"  # default
```

## What's NOT Changed

Everything else works the same:

- ✅ All CLI commands (`map`, `log`, `doctor`, `maintain`, `link-check`, `rename`, etc.)
- ✅ `pip install ontos` (without extras) — no new dependencies on Python 3.9+
- ✅ `.ontos.toml` configuration — existing settings preserved
- ✅ Frontmatter schema — no changes to document metadata
- ✅ Context map format — same output from `ontos map`
- ✅ Git hooks behavior
- ✅ `AGENTS.md` and `.cursorrules` generation
- ✅ Session logs, archives, and decision history

## Upgrade Steps

### 1. Upgrade the Package

**If you installed with pip:**
```bash
pip install --upgrade ontos
```

**If you installed with pipx (without MCP):**
```bash
pipx upgrade ontos
```

**If you installed with pipx (with MCP):**
```bash
pipx install --force 'ontos[mcp]'
```
> `pipx upgrade` does not add new extras. Use `pipx install --force` to
> reinstall with the `[mcp]` extra. This also ensures future `pipx upgrade`
> calls will keep MCP installed. Requires Python 3.10+ in the pipx venv.

### 2. Verify

```bash
ontos --version  # Should show 4.1.x
ontos doctor     # Check graph health
```

### 3. Enable MCP on an Existing Install (Optional)

If you upgraded without MCP in step 1 and want to add it later:

**pip:**
```bash
pip install 'ontos[mcp]'    # Requires Python 3.10+
```

**pipx:**
```bash
pipx install --force 'ontos[mcp]'
```

Test the server:
```bash
ontos serve
# Press Ctrl+C to stop
```

## What's New in v4.1

### Portfolio Index

v4.1 introduces a per-session SQLite portfolio index with FTS5 full-text search. Three new MCP tools (`project_registry`, `search`, `get_context_bundle`) let agents discover and search across workspaces.

Configure in `~/.config/ontos/portfolio.toml`:
```toml
[portfolio]
scan_roots = ["~/Dev"]
exclude = ["~/Dev/.dev-hub", "~/Dev/archive"]
registry_path = "~/Dev/.dev-hub/registry/projects.json"

[bundle]
token_budget = 8000
max_logs = 20
log_window_days = 30
```

### Write Tools

Four write-capable MCP tools ship in v4.1: `scaffold_document`, `log_session`, `promote_document`, and `rename_document`. They are registered only when the server runs without `--read-only`.

### Advisory Flock Locking

All write paths (CLI and MCP) now use `workspace_lock()` with advisory flock on `<workspace>/.ontos.lock`. Ensure `.ontos.lock` is in your `.gitignore`.

### Verify Subcommand

`ontos verify --portfolio` audits portfolio consistency (slug collisions, malformed TOML).

### Shared Rename Orchestrator

`build_rename_plan` is now the single plan-builder used by both `ontos rename --apply` and MCP `rename_document`.

### 4. Configure Your IDE (Optional)

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "ontos": {
      "command": "ontos",
      "args": ["serve"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

**Cursor** (`.cursor/mcp.json` in your project):
```json
{
  "mcpServers": {
    "ontos": {
      "command": "ontos",
      "args": ["serve"]
    }
  }
}
```

**Antigravity native agents** (`~/.gemini/antigravity/mcp_config.json`):

```bash
ontos mcp install --client antigravity
```

This command creates or updates the native Antigravity config with an `mcpServers.ontos` entry:

```json
{
  "mcpServers": {
    "ontos": {
      "command": "/absolute/path/to/ontos",
      "args": ["serve", "--workspace", "/absolute/path/to/your/project", "--read-only"]
    }
  }
}
```

Use `--write-enabled` if you want mutable MCP tools. This native config is separate from `AGENTS.md` / `.cursorrules` and from any editor-level MCP manifest.

**Cursor** (`.cursor/mcp.json` in your project, `~/.cursor/mcp.json` for user scope):

```bash
ontos mcp install --client cursor --scope project
ontos mcp install --client cursor --scope user
ontos mcp uninstall --client cursor --scope project
ontos mcp print-config --client codex
```

Rerunning `ontos mcp install --client cursor ...` refreshes the launcher path if Ontos moves on your shell `PATH`. Managed install, uninstall, and doctor support are POSIX-only in `v4.2`; Windows users should use `print-config`.

### Client Support Policy

Ontos now treats MCP enablement as two separate jobs:

- **Server health** — `ontos serve` works.
- **Client onboarding** — the client discovers Ontos tools through its own config contract.

That philosophy should stay consistent across clients, while the automation level stays client-specific:

- **First-class** clients get `ontos mcp install --client ...`, `ontos mcp uninstall --client ...`, and `ontos doctor` checks once their native config contract is stable. Antigravity and Cursor are the first examples in `v4.2`.
- **Print-config only** clients keep explicit manual setup docs plus a copy-pastable fallback document. Claude Code, Codex, and VS Code fit here.
- **Docs-only** clients remain manual in this release. Claude Desktop and Windsurf are the examples here.

The managed MCP client config is separate from `AGENTS.md` / `.cursorrules` and from any editor-level MCP manifest.

### 5. Enable Usage Logging (Optional)

Add to `.ontos.toml`:
```toml
[mcp]
usage_logging = true
```

Tool invocations are logged to `~/.config/ontos/usage.jsonl`. No document content is logged.

## Known Limitations (v4.1)

- ~~**Read-only tools only** — Write tools (scaffold, rename) deferred to v4.1~~ ✅ Shipped in v4.1
- **Single workspace per server** — Each `ontos serve` process serves one project
- **Stdio transport only** — HTTP/SSE transport deferred to a future release
- **Python 3.10+** required for MCP (base package remains 3.9+)
- ~~**No cross-project search** — Portfolio index deferred to v4.1~~ ✅ Shipped in v4.1
- **No cross-workspace writes** — Write tools target the served workspace only

## Getting Help

- Run `ontos doctor` for diagnostics
- Check [Ontos Manual](Ontos_Manual.md) for complete reference
- Open an issue at [GitHub](https://github.com/ohjonathan/Project-Ontos/issues)
