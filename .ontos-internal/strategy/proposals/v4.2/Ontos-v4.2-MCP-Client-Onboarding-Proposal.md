---
id: ontos_v42_mcp_client_onboarding_proposal
type: strategy
status: draft
depends_on: [ontos_manual, v4_roadmap, v412, v413]
concepts: [mcp, onboarding, antigravity, cursor, claude-code, codex, vscode, print-config]
---

# Ontos v4.2 Proposal: MCP Client Onboarding

**Date:** 2026-04-13  
**Author:** Codex (revised per CA response after cross-platform proposal review)  
**Status:** Draft -- revised for re-review  
**Audience:** Johnny (project owner), future implementers, review-board LLMs

## 1. What This Is

Ontos v4.2 is the **narrowed MCP client onboarding** release.

It keeps the shipped `v4.1.3` Antigravity onboarding support, adds
**Cursor** as the only new first-class managed client, and introduces a
universal **`ontos mcp print-config`** fallback so users can bridge the
remaining client surfaces without Ontos taking ownership of all of their
configs at once.

Concretely, v4.2 adds:

- managed onboarding for **Cursor**
- `ontos mcp uninstall` for the managed JSON clients
- `ontos mcp print-config` for **Antigravity, Cursor, Claude Code,
  Codex, and VS Code**
- a contract-drift policy for any client Ontos manages directly

What v4.2 does **not** add:

- HTTP / Streamable HTTP transport
- daemon mode or background indexers
- a Python version floor bump
- third-party CLI delegation (`codex mcp add`, `claude mcp add`, etc.)
- Codex or VS Code managed install / doctor support
- malformed-config auto-repair

## 2. Evidence

The evidence for broader onboarding is **real but weak**, so the release
is narrowed accordingly.

Evidence that supports continuing the line:

1. Issue [#99](https://github.com/ohjonathan/Project-Ontos/issues/99)
   proved the onboarding problem for Antigravity: `ontos serve` could be
   healthy while the user still had no tools because the client config
   was missing.
2. `v4.1.3` shipped Antigravity install + doctor support and closed that
   issue, proving that Ontos-owned onboarding can remove a real setup
   failure class.
3. The maintainer explicitly asked on 2026-04-13 to apply the same
   philosophy to other CLIs and IDEs.
4. Current customer-facing docs already position Cursor as manually
   configured today and call out Claude Code / Codex as likely next
   clients once the contract is stable enough.

Evidence that does **not** support a 5-client managed rollout yet:

- there is no repo-local issue history showing distinct onboarding bugs
  for Cursor, Claude Code, Codex, and VS Code
- there is no usage or install telemetry showing that all five should be
  owned at once
- there is no existing success metric proving multi-client automation is
  the right `v4.2` bet

This proposal therefore treats the evidence as sufficient for **one more
managed client**, not for immediate 5-client ownership.

## 3. Product Decision

### 3.1 Release Theme

`v4.2.0` is the release where Ontos stabilizes the onboarding pattern
proven in `v4.1.3` without overextending into every promising client at
once.

### 3.2 Support Tiers For v4.2

**Managed in `v4.2`**

- Antigravity (existing)
- Cursor (new)

These clients get:

- `ontos mcp install --client ...`
- `ontos mcp uninstall --client ...`
- client-aware `ontos doctor` coverage
- exact docs for the managed config path(s)

**`print-config` only in `v4.2`**

- Claude Code
- Codex
- VS Code

These clients get:

- `ontos mcp print-config --client ...`
- explicit manual setup guidance
- no Ontos-managed install or doctor promises in this release

**Docs-only in `v4.2`**

- Claude Desktop
- Windsurf

### 3.3 Why Cursor Is The Only New Managed Client

Cursor is the right single new managed client because:

- the repo already documents it manually
- it uses a straightforward JSON manifest shape
- it exercises both project and user scope without requiring third-party
  CLI delegation or TOML config ownership
- it is the closest next step to the Antigravity pattern without adding
  a new dependency or unstable adapter class

## 4. Success Metric

`v4.2` is successful if, within 4 weeks of release:

1. Cursor onboarding produces at least one confirmed non-Antigravity
   real-world use / ask beyond the original Antigravity repro path, and
2. no contract-drift or config-corruption bug is reported for the
   managed adapters (Antigravity and Cursor).

Expansion from `print-config` to managed automation for another client
requires either:

- one concrete issue / bug / ask for that specific client, or
- two separate maintainer / user asks plus stable official docs for the
  target contract.

## 5. Alternatives Considered

### 5.1 Five-Client Managed Automation Now

Rejected for `v4.2`.

Reason: the evidence supports the direction but not that much immediate
ownership. It would add multiple contract shapes, delegation logic, and
support burden without repo-local proof that all five need to be managed
now.

### 5.2 Docs-Only / Manual Setup

Rejected as the sole `v4.2` answer.

Reason: `v4.1.3` already proved that installer + doctor support removes
real onboarding failure. Going back to docs-only for every follow-on
client would ignore that learning.

### 5.3 `print-config` Only

Partially accepted, but not as the whole release.

Reason: `print-config` is the right universal fallback and should exist
for every candidate client. It does not fully replace managed onboarding
for Cursor, which is already manually documented and has a simple enough
JSON contract to justify first-class ownership.

## 6. Public Interface

### 6.1 Managed Commands

`v4.2` managed CLI surface:

```bash
ontos mcp install --client {antigravity,cursor}
ontos mcp uninstall --client {antigravity,cursor}
```

Both commands support:

- `--workspace PATH` where relevant
- `--write-enabled` on install
- `--scope {project,user}` for Cursor
- `--config-path PATH`
- `--json`

### 6.2 Fallback Command

Universal snippet output:

```bash
ontos mcp print-config --client {antigravity,cursor,claude-code,codex,vscode}
```

`print-config` supports:

- `--workspace PATH`
- client-appropriate `--scope`
- `--write-enabled`
- `--config-path PATH`
- `--json`

`print-config` never writes files. It returns the exact minimal snippet
the user can paste into the target config.

### 6.3 Supported Scope Matrix

| Client | Managed in v4.2 | `print-config` in v4.2 | Supported Scope(s) |
|--------|------------------|------------------------|--------------------|
| Antigravity | Yes | Yes | `user` |
| Cursor | Yes | Yes | `project`, `user` |
| Claude Code | No | Yes | `project` |
| Codex | No | Yes | `user` |
| VS Code | No | Yes | `project` |
| Claude Desktop | No | No | manual docs only |
| Windsurf | No | No | manual docs only |

Unsupported client / scope combinations return exit code `2` with
actionable remediation.

### 6.4 Output Contract

Successful managed commands report:

- `client`
- `scope`
- `action` (`created`, `updated`, `removed`, `noop`)
- `config_path`
- `workspace`
- `mode` (`read-only`, `write-enabled`)

`print-config` reports:

- `client`
- `scope`
- `config_path`
- `format` (`json`, `toml`)
- `snippet`

## 7. Managed Client Contracts

### 7.1 Antigravity

Managed path:

- `~/.gemini/antigravity/mcp_config.json`

Managed root key:

- `mcpServers`

Source of truth:

- existing shipped `v4.1.3` contract validated from the native config
  path and bundled schema during issue [#99](https://github.com/ohjonathan/Project-Ontos/issues/99)

Last verified:

- 2026-04-13

### 7.2 Cursor

Managed paths:

- project: `.cursor/mcp.json`
- user: `~/.cursor/mcp.json`

Managed root key:

- `mcpServers`

Source of truth:

- official Cursor MCP docs / CLI docs

Last verified:

- 2026-04-13

Cursor remains the only new managed adapter in `v4.2`.

## 8. Fallback Client Contracts

These clients are explicitly **not** managed in `v4.2`. Ontos only
prints the right snippet for them.

### 8.1 Claude Code

- project path: `.mcp.json`
- root key: `mcpServers`
- mode in `v4.2`: `print-config` only

### 8.2 Codex

- user path: `~/.codex/config.toml`
- root table: `[mcp_servers.ontos]`
- mode in `v4.2`: `print-config` only

Codex is removed from managed scope even though future support is
feasible. Ontos already has Python 3.9-compatible TOML read support via
`tomli`; the deferral is about product scope, not runtime feasibility.

### 8.3 VS Code

- project path: `.vscode/mcp.json`
- root key: `servers`
- mode in `v4.2`: `print-config` only

VS Code remains out of managed scope until a separate stability decision
justifies treating its MCP file as a first-class contract.

## 9. Contract-Drift Policy

For each managed adapter:

1. The proposal and customer-facing docs must record the source of truth
   and a `last verified` date.
2. Ontos validates the expected root shape before writing.
3. If the root shape is malformed or unknown, Ontos fails with exit `2`.
4. On failure, Ontos prints the exact `print-config` fallback snippet and
   a message that automation could not proceed safely.
5. Ontos never silently rewrites malformed or unknown config shapes.
6. Patch target after a reproduced drift report is 72 hours for either:
   - corrected docs / snippet output, or
   - an explicit incompatibility error that prevents unsafe writes.

This policy applies only to the managed JSON adapters in `v4.2`.

## 10. Install / Uninstall / Refresh Semantics

### 10.1 Install

`install` is idempotent.

- It creates the file if missing.
- It upserts only the `ontos` entry.
- It preserves unrelated server entries and unknown top-level keys.
- Re-running install acts as refresh / re-register and updates the Ontos
  entry only when command / args differ.

### 10.2 Uninstall

`uninstall` removes only the Ontos entry from the managed config.

- unrelated entries remain untouched
- if the Ontos entry is absent, uninstall returns success with `action =
  noop`
- uninstall does not delete the config file
- if the config is malformed or drifted, uninstall fails closed and
  points the user to manual cleanup

### 10.3 Stale Launcher Refresh

Ontos resolves the launcher path at install time. If the user changes
Python environments or Ontos install prefixes, the documented refresh
path is to rerun `ontos mcp install --client ...`, which rewrites only
the Ontos entry.

## 11. `print-config` Design

`print-config` is the universal escape hatch.

It should output the exact minimal snippet needed for the target client:

- JSON object for Antigravity / Cursor / Claude Code / VS Code
- TOML block for Codex

`--config-path` overrides only the target path metadata; it does not
change the required client-specific syntax.

This command exists for two reasons:

1. it gives users a zero-write path even for managed clients
2. it gives Ontos a safe fallback whenever automated install or uninstall
   cannot proceed

## 12. Architecture

### 12.1 Shared JSON Adapter Layer

`v4.2` only needs one new adapter class beyond Antigravity:

- shared launcher / workspace / mode generation
- shared JSON load / merge / write helpers for `mcpServers`
- shared failure handling and snippet fallback

This is intentionally narrower than the old proposal. `v4.2` does not
need:

- third-party CLI delegation support
- TOML ownership
- multiple doctor adapter families

### 12.2 Config Preservation Policy

For managed JSON clients:

- preserve unrelated server entries
- preserve unknown top-level keys
- fail on invalid JSON or incompatible root shape
- never auto-repair malformed files in this release

## 13. Doctor Design

### 13.1 Check Names

Managed doctor checks in `v4.2`:

- `antigravity_mcp`
- `cursor_mcp`

No new doctor checks are added for Claude Code, Codex, or VS Code in
this release.

### 13.2 Detection Policy

Doctor detection must key on the Ontos entry, not just file presence.

That means:

- `antigravity_mcp` inspects only when `mcpServers.ontos` is present or
  the managed Antigravity config exists and is expected to contain it
- `cursor_mcp` inspects project and/or user config only when
  `mcpServers.ontos` is present

Generic `.cursor/mcp.json` or `.mcp.json` files for unrelated servers do
not justify an Ontos warning.

### 13.3 Status Rules

`success`:

- no Ontos-managed entry is present, so the check is skipped
- or the entry is valid and the initialize probe passes

`warning`:

- the Ontos entry is malformed
- the command is not executable
- the workspace path is invalid
- the initialize probe fails

Remediation points to:

- `ontos mcp install --client ...` for managed clients
- `ontos mcp print-config --client ...` for manual recovery

## 14. Upgrade Idempotency

Cross-version behavior must remain predictable.

### 14.1 Antigravity (`v4.1.3` -> `v4.2`)

Re-running Antigravity install under `v4.2`:

- must not inject extra metadata into the client config
- must only rewrite `mcpServers.ontos` if command / args differ
- must preserve all unrelated entries exactly as before

### 14.2 Cursor

Cursor follows the same rule:

- only `mcpServers.ontos` is owned
- install is safe to rerun
- uninstall removes only that entry

## 15. Test Plan

### 15.1 CLI Coverage

- help output includes `install`, `uninstall`, and `print-config`
- install / uninstall support only `{antigravity,cursor}`
- `print-config` supports `{antigravity,cursor,claude-code,codex,vscode}`
- unsupported client / scope combinations return exit `2`
- `--config-path` overrides the target path metadata

### 15.2 Managed Adapter Coverage

- Antigravity install remains idempotent across `v4.1.3` -> `v4.2`
- Cursor install creates fresh project / user config
- install merges with unrelated entries
- uninstall removes only `ontos`
- uninstall on missing entry is `noop`
- malformed config fails closed and prints fallback guidance
- `--write-enabled` removes `--read-only`

### 15.3 `print-config` Coverage

- prints valid JSON snippets for Antigravity / Cursor / Claude Code / VS Code
- prints valid TOML snippet for Codex
- does not require third-party CLIs in CI
- can be snapshot-tested as pure output

### 15.4 Doctor Coverage

- `antigravity_mcp` and `cursor_mcp` only
- detection keys on `mcpServers.ontos`, not file presence alone
- warnings for malformed Ontos entry, bad command, bad workspace, and
  probe failure
- success when valid entry + probe pass

## 16. Acceptance Criteria

`v4.2` is complete when:

1. Antigravity remains supported with no regression from `v4.1.3`
2. Cursor has first-class install / uninstall / doctor coverage
3. `print-config` works for Antigravity, Cursor, Claude Code, Codex,
   and VS Code
4. managed installs fail closed on drift and provide manual fallback
5. cross-version idempotency is explicit for Antigravity and Cursor

## 17. Non-Goals

Not in `v4.2`:

- managed Claude Code onboarding
- managed Codex onboarding
- managed VS Code onboarding
- any new doctor checks for print-config-only clients
- roadmap reshuffling inside this proposal document
- HTTP / Streamable HTTP transport
- daemon mode
- security middleware

## 18. Expected Outcome

If approved, this proposal should produce an implementation prompt that
is intentionally narrow:

- extend the existing Antigravity pattern to Cursor
- add `print-config`
- add `uninstall`
- update docs for the narrowed support tiers

The broader release-sequencing question (`v4.2` vs `v4.3`, plus the
status of the old `v4.1.1` backlog) is handled in the separate roadmap
decision doc, not here.
