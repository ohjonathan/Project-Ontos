I can’t do a true line-by-line code review because you didn’t upload the repo itself, just the maps and briefs. But those docs are detailed enough to make real calls about the architecture, UX friction, and what v3.0 should be.

## What you’ve already got that’s legit

* **Clear product promise + workflow**. The README nails the “install, say Activate Ontos, it works” loop. 
* **Functional core / imperative shell is the right foundation for MCP**. You explicitly call out that separation as a prerequisite for API exposure and v3 MCP server work. 
* **Unified CLI was a big step**. Central dispatcher + aliases is exactly what you want before turning it into a packaged binary and MCP tools. 
* **Installer security is unusually good for a curl-bootstrap**. SHA256 verification, traversal and symlink protections, rollback, offline bundle story. Keep that standard even if you move away from per-repo installs. 
* **You’re already designing for migration**. Schema versioning explicitly reserves a v3.0 schema and compatibility rules. 

## The core problem with your v2 distribution model

Right now the “Quick Start” literally installs Ontos **into the repo** via `install.py` pulled from GitHub. 
That’s great for “it worked in 60 seconds”, but it scales poorly:

* Every repo vendors the tooling. Updates become repo work.
* You now have “tooling code” mixed into “project code”, and it grows over time.
* MCP wants “a server the client connects to”, not “copy scripts into every project”.

So yes, your instinct is right: **v3 should split “project memory” from “tool runtime.”** The memory stays in-repo. The runtime becomes global and pluggable.

## What MCP actually gives you, and the trap to avoid

MCP is basically a standardized way for a server to expose **tools, resources, and prompts** over a JSON-RPC protocol with defined transports. ([Model Context Protocol][1])
Cursor and others expect you to configure servers and pass auth via env vars, etc. ([Cursor][2])
There’s an official Python SDK that already implements the spec and transports. ([GitHub][3])

Trap: “MCP” is not automatically “less friction”. If you require users to run a daemon, manage ports, auth, config files, and workspace switching, you can easily make the product worse.

Your north star should be:

* **One-time install, one-time MCP config**
* **Zero per-repo tool installation**
* **Still works from the CLI without MCP**

## My recommendation: v3 as two front-doors on one core

### 1) Global CLI as the default runtime

Ship Ontos as a normal Python package with a real executable:

* `pipx install ontos` (best UX for a global tool)
* Command becomes `ontos …` not `python3 ontos.py …`

Then Ontos operates on “the repo you’re standing in”:

* Walk up to find `.git` root.
* If no git, treat current dir as root.
* Detect Ontos presence by looking for `Ontos_Context_Map.md` or docs structure and offer `ontos init` only when missing.

This directly solves your “don’t install in each folder/directory” complaint without involving MCP at all.

### 2) MCP server as the integration layer for agentic clients

Expose the exact same actions via MCP so Cursor/Claude Desktop/others can call it as tools.

MCP primitives you should use:

* **Resources**: let clients fetch `Ontos_Context_Map.md`, specific doc bodies, decision history, health report, etc. ([Model Context Protocol][1])
* **Tools**: `map`, `query`, `verify`, `maintain`, `log/archive`, `scaffold/stub/promote`, `migrate`. Your existing command surface maps cleanly. 
* **Prompts**: ship “Activate Ontos”, “Archive Ontos”, “Maintain Ontos” as first-class prompt templates so users don’t have to copy magic incantations. ([Model Context Protocol][4])

Security matters a lot here. MCP explicitly calls out that servers create arbitrary data access and code execution paths, so implementors need hard guardrails. ([Model Context Protocol][5])

## The critical v3 features I’d add

These are the things that reduce friction *and* make the system scale without turning into a heavy platform.

### A) A workspace model that is explicit and safe

For MCP, the server needs to know what it’s allowed to read/write.

* Require a **repo_root** on server start or via a `set_workspace` tool.
* Enforce “all paths must resolve under repo_root” with real path checks.
* Default to **read-only** mode. Writes require either:

  * starting the server with `--write`, or
  * a per-call `allow_write=true` plus an obvious confirmation string.

This keeps “it just works” while making the security posture defensible.

### B) “Doctor” command and MCP health resource

You already have complexity: modes, hooks, schema versions, curation levels, staleness, etc. 
Add:

* `ontos doctor` prints:

  * repo root detected
  * docs dir detected
  * config loaded and from where
  * schema versions found and compatibility issues
  * lockfile status
  * any broken invariants
* MCP exposes the same as a `health_report` resource

This one feature prevents 80 percent of “why isn’t it working”.

### C) JSON output for machine consumption

You’ll want this the minute people start scripting around Ontos or consuming it from MCP clients:

* `ontos map --json` outputs the graph index in JSON
* `ontos query --json`
* `ontos doctor --json`

Keep markdown as the human default. JSON is optional and stable.

### D) Make SessionContext truly cross-platform and concurrency-safe

Your codebase map shows a temp-then-rename pattern using `path.with_suffix(path.suffix + '.tmp')` then `rename`. 
I would harden this before you expose it through MCP where concurrency is more likely:

* temp file names must be unique, not deterministic `.tmp` that can collide
* use `os.replace` semantics to overwrite atomically on more platforms
* be careful about rename across filesystems
* locks: PID-liveness checks are fine, but add timestamp + host, and a clear stale policy

You’ve added tests around SessionContext already, which is good. 
In v3, expand tests specifically for:

* concurrent lock acquisition
* crash mid-commit leaving temp files
* Windows path edge cases

### E) Kill “python3 ontos.py …” in favor of a real executable

This seems small, but it’s the difference between “tooling project” and “product”.

* `ontos` should be the canonical entrypoint.
* Keep `ontos.py` as a thin compatibility shim for one release, then remove.

Your changelog already frames v3 as the time to remove direct script execution. 

### F) One config file, not generated code

Right now there’s a generated `ontos_config.py` in the installed toolkit. 
For v3, I’d move to a single, tiny text config:

* `.ontos.toml` or `.ontos.yml` at repo root
* optional, with good defaults
* no executable config file by default

Generated python configs are powerful, but they scare teams and complicate tooling and security. This is one of the biggest “make it scale” moves while staying lightweight.

## The distribution plan I’d actually ship

* **v3.0 recommended path**: `pipx install ontos`, then `ontos init` once per repo.
* **MCP**: `ontos mcp` (stdio transport) so Cursor/Claude Desktop can spawn it directly. The official docs emphasize servers used by desktop clients and standard transports, and the Python SDK supports these patterns. ([GitHub][3])
* **Legacy path**: keep `install.py` for a while for air-gapped and “curl it” users, but stop making it the main Quick Start. Your current README Quick Start is optimized for agents pasting commands, not for long-term maintainability. 

If you want “as little friction as possible”, the best move is: **global install + repo-local memory**. MCP becomes an additional integration, not the primary distribution mechanism.

## One blunt product call

If you try to make v3 “MCP-only”, you’ll lose a bunch of users who just want a CLI that works anywhere. MCP is great, but it’s still another configuration surface. The win is offering MCP *without requiring it*.

If you upload the actual repo tree or a zip of the code, I’ll do the real code review next: modules, dependency boundaries, error handling, and a concrete v3 refactor plan with an MCP tool/resource/prompt schema that matches the spec.

[1]: https://modelcontextprotocol.io/docs/learn/architecture?utm_source=chatgpt.com "Architecture overview"
[2]: https://cursor.com/docs/context/mcp?utm_source=chatgpt.com "Model Context Protocol (MCP) | Cursor Docs"
[3]: https://github.com/modelcontextprotocol/python-sdk?utm_source=chatgpt.com "The official Python SDK for Model Context Protocol servers ..."
[4]: https://modelcontextprotocol.io/specification/2025-06-18/server/prompts?utm_source=chatgpt.com "Prompts"
[5]: https://modelcontextprotocol.io/specification/2025-11-25?utm_source=chatgpt.com "Specification"
