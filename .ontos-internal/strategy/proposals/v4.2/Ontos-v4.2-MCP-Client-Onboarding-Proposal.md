---
id: ontos_v42_mcp_client_onboarding_proposal
type: strategy
status: draft
depends_on: [ontos_manual, v4_roadmap, v412, v413]
concepts: [mcp, onboarding, antigravity, cursor, claude-code, codex, vscode, roadmap]
---

# Ontos v4.2 Proposal: MCP Client Onboarding

**Date:** 2026-04-13  
**Author:** Codex (synthesized from shipped `v4.1.3`, current codebase analysis, internal roadmap review, and current client-contract research)  
**Status:** Draft -- ready for review  
**Audience:** Johnny (project owner), future implementers, review-board LLMs

## 1. What This Is

Ontos v4.2 is the **MCP client onboarding** release.

It expands the `v4.1.3` Antigravity-native onboarding work into a
general client-install and client-diagnostics layer for the major MCP
CLIs and IDEs that now have stable enough local configuration contracts
to support first-class automation.

Concretely, v4.2 adds:

- first-class onboarding for **Cursor**, **Claude Code**, **Codex**, and
  **VS Code**, while preserving the shipped **Antigravity** support
- a shared client-adapter layer for install and doctor flows
- a clearer client support policy that separates:
  - first-class install + doctor automation
  - supported manual setup
  - docs-only / evolving surfaces

What v4.2 does **not** add:

- HTTP / Streamable HTTP transport
- daemon mode or background indexers
- a Python version floor bump
- malformed-config auto-repair
- the deferred breaking `export_graph` schema redesign from `v4.1.2`

Those items move to **v4.3**.

## 2. Why Now

`v4.1.3` proved the problem is real: a healthy `ontos serve` is not
enough if the client-side MCP manifest is missing or wrong. Antigravity
now works because Ontos owns the install and doctor path for that
client. The same product logic applies to other major agent tools.

The current repo already says this direction out loud:

- Antigravity is first-class today
- Cursor and Claude Desktop are documented manually
- Claude Code and Codex are explicitly called out as likely next clients

The gap is that the docs, support policy, and implementation are not yet
aligned. There is also a roadmap mismatch:

- shipped reality: `v4.1.x` already delivered write tools, portfolio
  indexing, schema fixes, and Antigravity onboarding
- stale internal roadmap: still treats `v4.1` as proposed and `v4.2` as
  transport-first

The correct next step is not to mix transport work into this onboarding
expansion. The correct next step is to finish the user-facing MCP story
for the major clients that now have sufficiently stable native contracts.

## 3. Current State

### 3.1 What `v4.1.3` Ships

Current code surfaces:

- `ontos mcp install --client antigravity`
- `ontos doctor` check: `antigravity_mcp`
- Antigravity helpers in `ontos/core/antigravity_mcp.py`
- installer logic in `ontos/commands/mcp.py`

Current behavior:

- resolves the Ontos launcher via `shutil.which("ontos")`, falling back
  to `sys.executable -m ontos`
- writes `~/.gemini/antigravity/mcp_config.json`
- preserves unrelated `mcpServers` entries
- defaults to `--read-only`
- validates the config and runs a lightweight stdio `initialize` probe

### 3.2 Why The Current Shape Cannot Scale As-Is

The current implementation is Antigravity-specific rather than
client-generic:

- config discovery is hard-coded to Antigravity
- JSON shape rules are Antigravity-specific
- doctor only knows the Antigravity check name and semantics
- install only allows one client

Expanding by adding more `if client == ...` branches directly into the
Antigravity helpers would create the wrong architecture. The shared logic
already exists conceptually:

- resolve Ontos launcher
- resolve workspace root
- generate read-only vs write-enabled args
- inspect command and workspace validity
- probe a configured stdio server

That shared layer should be explicit in v4.2, with client-specific
adapters sitting on top of it.

### 3.3 Roadmap Conflict To Resolve

The internal `v4.x` roadmap still frames `v4.2` as HTTP transport and
daemon mode. That plan is now stale for two reasons:

1. `v4.1` shipped much more than the old roadmap still claims
2. the immediate, validated customer need is client onboarding, not
   transport infrastructure

This proposal therefore **reassigns `v4.2` to MCP client onboarding**
and moves the previous transport/daemon/security work, plus the deferred
breaking `export_graph` contract cleanup, to **v4.3**.

## 4. Product Decision

### 4.1 v4.2 Release Theme

`v4.2.0` is the release where Ontos becomes opinionated and reliable
about **getting connected** to the major local MCP clients.

The principle is:

> If a client has a stable enough native contract, Ontos should own the
> install path and the doctor path for that client.

### 4.2 Support Tiers For v4.2

**First-class in v4.2**

- Antigravity
- Cursor
- Claude Code
- Codex
- VS Code

These clients get:

- `ontos mcp install --client ...`
- client-aware `ontos doctor` coverage
- docs with exact managed path / scope

**Supported, but not automated in v4.2**

- Claude Desktop

Claude Desktop remains documented, but its recommended transport story is
not the same local native-manifest path that Ontos can safely automate
in this release.

**Docs-only / evolving in v4.2**

- Windsurf

Windsurf remains out of first-class automation until its local config
contract is stable enough to trust and document confidently.

## 5. Public Interface

### 5.1 CLI Surface

Expand:

```bash
ontos mcp install --client ...
```

to:

```bash
ontos mcp install --client {antigravity,cursor,claude-code,codex,vscode}
```

with:

- `--workspace PATH` optional, defaulting to the resolved Ontos project root
- `--write-enabled` optional, preserving read-only as the default
- `--scope {project,user}` for clients that support more than one managed scope
- `--json` preserving the existing command-envelope pattern

### 5.2 Supported Scope Matrix

`v4.2` supports only the scopes Ontos can automate safely with clear,
stable paths:

| Client | Managed Scope(s) | Default | Notes |
|--------|------------------|---------|-------|
| Antigravity | `user` | `user` | Existing `~/.gemini/antigravity/mcp_config.json` path |
| Cursor | `project`, `user` | `project` | Project config is repo-local and shareable; user config supported for personal installs |
| Claude Code | `project` | `project` | Managed via project `.mcp.json` only in v4.2 |
| Codex | `user` | `user` | Installed via native CLI path; user-scoped only |
| VS Code | `project` | `project` | Managed via project `.vscode/mcp.json` only in v4.2 |

Unsupported client/scope combinations return exit code `2` with an
actionable remediation message.

### 5.3 Install Output Contract

Successful installs should report:

- `client`
- `scope`
- `action` (`created` / `updated`)
- `config_path`
- `workspace`
- `mode` (`read-only` / `write-enabled`)
- `managed_by` (`direct-config` / `native-cli`)

This is additive to the current JSON envelope shape.

## 6. Client Contracts

### 6.1 Antigravity

Keep the shipped behavior:

- config path: `~/.gemini/antigravity/mcp_config.json`
- top-level key: `mcpServers`
- direct JSON management by Ontos

No scope broadening in v4.2.

### 6.2 Cursor

Manage:

- project config: `.cursor/mcp.json`
- user config: `~/.cursor/mcp.json`

Shape:

```json
{
  "mcpServers": {
    "ontos": {
      "command": "...",
      "args": ["serve", "--workspace", "...", "--read-only"]
    }
  }
}
```

Rules:

- preserve unrelated server entries
- fail clearly on malformed JSON or non-object roots
- default to project scope

### 6.3 Claude Code

Manage **project scope only** in v4.2:

- config path: `.mcp.json`
- top-level key: `mcpServers`

Shape:

```json
{
  "mcpServers": {
    "ontos": {
      "command": "...",
      "args": ["serve", "--workspace", "...", "--read-only"],
      "env": {}
    }
  }
}
```

Rules:

- direct JSON management for project scope only
- reject `--scope user` in v4.2 with guidance to use Claude Code's own
  CLI if a user-level install is desired
- preserve unrelated server entries

### 6.4 Codex

Codex is different because its user config is TOML and the repo does not
currently carry a round-trip TOML writer. v4.2 should avoid brittle TOML
string manipulation.

Install strategy:

- use the native CLI install path: `codex mcp add ...`
- manage **user scope only**
- return `managed_by = native-cli`

Doctor strategy:

- inspect `~/.codex/config.toml`
- validate `[mcp_servers.ontos]`
- validate command, args, workspace, and initialize probe using the same
  shared inspection logic

If the `codex` executable is not present, install returns exit `2` with
clear remediation.

### 6.5 VS Code

Manage **project scope only** in v4.2:

- config path: `.vscode/mcp.json`
- top-level key: `servers`

Shape:

```json
{
  "servers": {
    "ontos": {
      "command": "...",
      "args": ["serve", "--workspace", "...", "--read-only"]
    }
  }
}
```

Rules:

- direct JSON management for project scope only
- do not attempt to manage profile-level user config in v4.2
- reject `--scope user` with actionable remediation

## 7. Architecture

### 7.1 Shared Adapter Layer

Split the current Antigravity-specific helpers into:

1. **Shared client-install primitives**
   - resolve Ontos launcher
   - resolve workspace root
   - build Ontos stdio command args
   - validate command and workspace
   - stdio initialize probe

2. **Per-client adapters**
   - config discovery
   - config parser / writer or native CLI installer
   - Ontos entry upsert rules
   - doctor detection and inspection logic

This should live as a new client-generic onboarding layer rather than as
incremental expansion of `antigravity_mcp.py`.

### 7.2 Write Policy

Default generated config remains:

```text
serve --workspace ABS_PATH --read-only
```

`--write-enabled` omits `--read-only`; it does not add any other changes.

This preserves the shipping `v4.1.3` safety model and makes writable
installs explicit.

### 7.3 Config Preservation Policy

For direct-config clients:

- preserve unrelated server entries
- preserve unknown top-level keys
- do not silently rewrite malformed configs
- fail on invalid JSON / TOML / root shape mismatches

For native-CLI clients:

- do not hand-edit the config file in this release
- use the client's native install command and inspect the resulting
  persisted config during doctor flows

## 8. Doctor Design

### 8.1 Check Names

Keep the shipped:

- `antigravity_mcp`

Add:

- `cursor_mcp`
- `claude_code_mcp`
- `codex_mcp`
- `vscode_mcp`

This keeps the JSON output additive and readable.

### 8.2 Detection Policy

Doctor should remain **user-scoped and opt-in**, not app-bundle-scoped.

A client check should run when Ontos has evidence the user opted into
that client surface, such as:

- the managed project config file exists
- the managed user config file exists
- a previously installed Ontos entry exists in the relevant config

Doctor should not nag users merely because an IDE or CLI app is present
on the machine.

### 8.3 Status Rules

`success`:

- client not detected / not configured, so the check is skipped
- or valid Ontos entry + successful initialize probe

`warning`:

- config exists but is empty, malformed, or unreadable
- config shape is invalid
- Ontos entry missing
- command not executable
- workspace missing or invalid
- initialize probe fails

Human remediation should point to `ontos mcp install --client ...`
whenever Ontos can manage that client directly.

## 9. Docs And Release Positioning

v4.2 requires customer-facing docs to say the same thing everywhere:

- instruction artifacts and MCP client config are separate setup steps
- first-class clients get exact install commands and doctor coverage
- supported/manual clients keep explicit config examples
- evolving clients remain docs-only until the contract stabilizes

This proposal also establishes the versioning decision:

- `v4.2`: client onboarding
- `v4.3`: Streamable HTTP / daemon / security / deferred `export_graph`
  contract cleanup

## 10. Test Plan

### 10.1 CLI Coverage

- top-level help lists the expanded client set
- invalid client/scope combinations return exit `2`
- install creates fresh config for each direct-config client
- install merges with unrelated entries
- install defaults to read-only
- `--write-enabled` removes `--read-only`
- launcher fallback still works when `ontos` is not on `PATH`
- malformed existing config returns non-zero and leaves the file untouched
- Codex install invokes the native CLI with the expected arguments

### 10.2 Doctor Coverage

- skipped success before client opt-in
- warning for missing Ontos entry
- warning for malformed config
- warning for bad command
- warning for bad workspace
- warning for initialize probe failure
- success when the entry is valid and the probe passes
- `--json` output includes the new additive check objects

### 10.3 Docs Coverage

- command and help snapshots include the expanded client matrix
- doc assertions verify the exact config paths and key shapes for:
  - Antigravity (`mcpServers`)
  - Cursor (`mcpServers`)
  - Claude Code (`mcpServers`)
  - Codex (`mcp_servers`)
  - VS Code (`servers`)

## 11. Acceptance Criteria

v4.2 is complete when:

1. Ontos can install and diagnose all first-class clients defined in
   this proposal
2. all managed config writes preserve unrelated entries and fail safely
   on malformed input
3. doctor checks are additive, opt-in, and do not produce false-positive
   nags for merely installed applications
4. customer-facing docs and the internal roadmap all agree on the
   `v4.2` / `v4.3` split

## 12. Non-Goals

Not in v4.2:

- HTTP / Streamable HTTP serving
- daemon or launchd work
- background indexing or portfolio daemons
- new security middleware
- automatic config repair
- full user-scope management for Claude Code or VS Code
- Windsurf automation

## 13. Defaults Chosen Here

This proposal intentionally locks these defaults so implementation does
not have to guess:

- `v4.2.0` is the onboarding release
- `v4.3.0` inherits the old transport/daemon/security lane
- Codex installs via native CLI, not direct TOML editing
- Claude Code and VS Code user-scope automation are deferred
- read-only remains the default generated mode
- doctor remains opt-in and user-scoped

## 14. Implementation Risk Areas To Review

The review board should pressure-test:

- JSON vs TOML preservation strategy
- project vs user scope defaults
- Codex native-CLI install behavior and fallbacks
- doctor detection thresholds for each client
- whether the proposed check names are the right long-term surface
- whether any client here should be demoted back to manual-only support

## 15. Expected Outcome

If approved, this proposal should produce a revised implementation spec
that can be handed directly to an implementation agent without needing
new product decisions.

That implementation spec should stay narrow:

- create the shared adapter layer
- extend `ontos mcp install`
- extend `ontos doctor`
- update customer-facing docs
- update the internal roadmap

and should explicitly avoid transport work in the same patch train.
