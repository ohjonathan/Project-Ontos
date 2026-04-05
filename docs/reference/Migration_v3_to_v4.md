---
id: migration_v3_to_v4
type: reference
status: active
depends_on: [ontos_manual]
---

# Migration Guide: v3.x → v4.0

This guide covers the new capabilities in Ontos v4.0 and how to enable them. **There are no breaking changes** — all existing CLI commands, configuration, and frontmatter schemas are preserved.

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
pip install 'ontos[mcp]'    # Adds mcp>=1.2 and pydantic>=2.0
```

> **Note:** MCP requires Python 3.10+. All other Ontos commands continue to work on Python 3.9+.

### 8 MCP Tools

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

All tools are read-only (except `export_graph` with `export_to_file`, which writes within the workspace root).

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

**If you installed with pipx:**
```bash
pipx upgrade ontos
```

### 2. Verify

```bash
ontos --version  # Should show 4.0.0
ontos doctor     # Check graph health
```

### 3. Enable MCP (Optional)

Requires Python 3.10+.

**If you installed with pip:**
```bash
pip install 'ontos[mcp]'
```

**If you installed with pipx:**
```bash
pipx inject ontos mcp pydantic
```
> `pipx inject` adds packages into an existing pipx-managed environment.
> `pipx upgrade` alone will not add the new MCP dependencies.

Test the server:
```bash
ontos serve
# Press Ctrl+C to stop
```

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

### 5. Enable Usage Logging (Optional)

Add to `.ontos.toml`:
```toml
[mcp]
usage_logging = true
```

Tool invocations are logged to `~/.config/ontos/usage.jsonl`. No document content is logged.

## Known Limitations (v4.0)

- **Read-only tools only** — Write tools (scaffold, rename) deferred to v4.1
- **Single workspace per server** — Each `ontos serve` process serves one project
- **Stdio transport only** — HTTP/SSE transport deferred to v4.1
- **Python 3.10+** required for MCP (base package remains 3.9+)
- **No cross-project search** — Portfolio index deferred to v4.1

## Getting Help

- Run `ontos doctor` for diagnostics
- Check [Ontos Manual](Ontos_Manual.md) for complete reference
- Open an issue at [GitHub](https://github.com/ohjonathan/Project-Ontos/issues)
