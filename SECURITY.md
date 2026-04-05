# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 4.0.x   | :white_check_mark: |
| 3.4.x   | :white_check_mark: |
| 3.3.x   | :white_check_mark: |
| < 3.3   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Project Ontos, please report it responsibly:

1. **Do not** open a public issue
2. **Email** the maintainers directly or use GitHub's private vulnerability reporting
3. **Include** details about the vulnerability and steps to reproduce

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Resolution**: Depends on severity and complexity

## Security Considerations

Project Ontos processes local markdown files via the `ontos` Python package. Key security considerations:

### File System Access

- The `ontos` CLI reads/writes within the project root and configured doc directories
- No network requests are made by any CLI command. The MCP server (`ontos serve`) uses stdio transport only — it does not open network sockets or listen on any port. Communication happens exclusively through stdin/stdout with the host IDE process
- File paths are validated against the project root — path traversal outside the repo is rejected

### YAML Parsing

- Uses PyYAML's `safe_load()` exclusively to prevent code execution
- Malformed YAML is handled gracefully with structured error reporting

### MCP Server (`ontos serve`)

- **Stdio transport only** — No TCP/HTTP listeners are opened
- **Read-only tools** — All v4.0 MCP tools are read-only. No tool modifies workspace files (except `export_graph` with `export_to_file`, which writes within the workspace root only)
- **Path validation** — All path parameters are validated to resolve within the workspace root. Path traversal outside the repo is rejected (`E_PATH_OUTSIDE_WORKSPACE`)
- **Single workspace** — Each server instance is bound to one workspace at startup. Cross-workspace access is not possible
- **Usage logging** — When `[mcp] usage_logging = true` in `.ontos.toml`, tool invocations are logged to `~/.config/ontos/usage.jsonl` (configurable). No document content is logged
- **Optional dependency surface** — MCP mode adds `mcp>=1.2` and `pydantic>=2.0`. These are not installed with the base package

### Best Practices for Users

1. **Don't run ontos on untrusted repositories** — Only use Ontos on your own projects
2. **Review generated files** — Always review `Ontos_Context_Map.md` and `AGENTS.md` before committing
3. **Keep dependencies updated** — Run `pip install --upgrade ontos`
4. **Scan for secrets before releases** — Run `gitleaks detect` and `trufflehog git file://. --no-update`

## Scope

This security policy applies to:

- The `ontos` Python package (`ontos/` directory)
  - `ontos/io/yaml.py` — YAML parsing surface
  - `ontos/io/scan.py` — File system scanning and discovery
  - `ontos/cli.py` — CLI entry point and argument handling
- The `ontos` CLI entry point (`ontos <command>`)
- The `ontos/mcp/` package:
  - `ontos/mcp/server.py` — MCP server bootstrap and tool registration
  - `ontos/mcp/tools.py` — MCP tool implementations (read-only adapters)
  - `ontos/mcp/cache.py` — In-memory snapshot cache with file-mtime invalidation
  - `ontos/mcp/schemas.py` — Pydantic schemas for structured output validation
- Generated files: `Ontos_Context_Map.md`, `AGENTS.md`, `.cursorrules`

Third-party dependencies (PyYAML) have their own security policies.
