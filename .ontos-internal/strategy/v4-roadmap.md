---
id: v4_roadmap
type: strategy
status: active
depends_on: [ontos_manual]
---

# Ontos v4.x Roadmap

**Updated:** 2026-04-11
**Status:** Active -- tracks the v4.x release series

This document is the single reference for the v4.x version plan. Each version has a full proposal in its own directory; this file captures the high-level scope, sequencing rationale, and trigger criteria in one place.

---

## v4.0.0 -- MCP Bridge (SHIPPED)

**Released:** 2026-04-05
**Proposal:** `.ontos-internal/strategy/v4.0/Ontos-v4.0-MCP-Proposal.md`
**PR:** #81

Thin stdio MCP bridge wrapping single-project CLI capabilities as 8 read-only tools.

| Capability | Detail |
|-----------|--------|
| 8 MCP tools | `workspace_overview`, `context_map`, `get_document`, `list_documents`, `export_graph`, `query`, `health`, `refresh` |
| Transport | Stdio only |
| Scope | Single workspace per server |
| Tools | Read-only (no writes) |
| Install | `pip install ontos[mcp]` (mcp>=1.2, pydantic>=2.0) |

---

## v4.1.0 -- Write Tools + Read-Only Discovery (PROPOSED)

**Proposal:** `.ontos-internal/strategy/proposals/v4.1/Ontos-v4.1-Proposal.md`
**Research:** `.ontos-internal/strategy/proposals/v4.1/ontos-v4.1-research-consolidated.md`
**PR:** #84
**Review status:** Re-scoped twice per review. Awaiting CA decision on v4 revision.

Adds two write tools and read-only project discovery to the existing stdio MCP server. Minimal scope -- no new storage, no new dependencies beyond MCP SDK pin bump.

| Capability | Detail |
|-----------|--------|
| 2 new write tools | `scaffold_document` (wraps `scaffold --apply`), `log_session` (wraps `log --auto`) |
| 1 new read tool | `project_registry()` -- reads directly from `.dev-hub/registry/projects.json`, no SQLite |
| Transport | Stdio only |
| Scope | Single-workspace (write tools) + read-only multi-project discovery |
| Storage | None new -- reads existing `projects.json` |
| Install | `pip install ontos[mcp]` (mcp>=1.27.0,<2.0) |

**Write tool contracts (verified against CLI):**
- `scaffold_document`: Always-apply (MCP tools are imperative). Wraps `scaffold --apply`. No git precondition.
- `log_session`: Wraps `log --auto`. Maps `summary` to topic, `branch` auto-detected. Requires git repo.
- `--read-only` startup flag strips write tools from MCP surface entirely.

**Success metric:** Justified if `scaffold_document` + `log_session` are called >5x/week within 4 weeks of release.

---

## v4.1.1 -- Search + Complex Write Tools (PLANNED)

**Proposal:** Not yet written. Triggered by v4.1.0 usage validation.

Adds FTS5 cross-project search and the two write tools that need contract decisions before implementation.

| Capability | Detail |
|-----------|--------|
| 2 new write tools | `rename_document`, `promote_document` |
| 1 new read tool | `search(query_string, workspace_id?)` via SQLite FTS5 |
| Storage | `~/.config/ontos/portfolio.db` -- non-authoritative rebuildable cache. `.dev-hub` remains sole authority. |
| FTS config | Contentless FTS5 (`content=''`), porter+unicode61 tokenizer, title 10x / concepts 3x / body 1x persistent rank, `prefix='2,3'` |

**Write tool contract decisions needed (CA):**

`rename_document` -- the CLI (`ontos rename --apply`) requires a clean git working tree. MCP agents may not have clean state. Options:
- **(a)** Enforce clean git: check state, return error if dirty (safest, matches CLI)
- **(b)** Skip git check: MCP agents operate in their own context (most permissive)
- **(c)** Add `force: bool` parameter: default checks git, `force=true` skips (explicit opt-out)

`promote_document` -- the CLI is interactive by default (prompts for missing `depends_on`, `concepts`). MCP cannot be interactive. Options:
- **(a)** Read-only only: expose `--check` mode, report readiness but never modify (safest)
- **(b)** Non-interactive batch: wraps `--all-ready --yes`, promotes everything that's ready
- **(c)** Require fields as input: MCP tool accepts `depends_on` and `concepts` as parameters, filling what the interactive prompt would ask

**Trigger criteria:**
1. v4.1.0 ships and `scaffold_document` + `log_session` are validated by usage
2. CA decides the rename/promote contract questions above

---

## v4.2.0 -- HTTP Transport and Daemon Mode (PLANNED)

**Proposal:** Not yet written. To be triggered by criteria below.
**Research:** Findings preserved in `ontos-v4.1-research-consolidated.md` (Areas 1, 2, 6, 7).

Adds Streamable HTTP transport, security model, and persistent daemon mode for process-to-process consumers (JohnnyOS).

| Capability | Detail |
|-----------|--------|
| Streamable HTTP | `ontos serve --http` on `127.0.0.1:9400/mcp`. ASGI mounting with Starlette middleware (not `server.run()`). |
| Security | Bearer token (macOS Keychain), DNS rebinding protection (Origin/Host validation per CVE-2025-66414), CORS, security headers, audit logging, rate limiting. |
| Daemon mode | Long-running portfolio server with background indexer (60s polling). launchd plist for macOS. |
| Memory management | 7-day uptime watchdog (launchd auto-restart). TTLCache, tracemalloc monitoring, 1.5GB RSS threshold. |
| Context bundles | `get_context_bundle()` tool -- only if v4.1 usage shows agents consistently requesting docs NOT in the tiered context map. Kill criterion: if `context_map(compact="tiered")` is sufficient after 4 weeks of v4.1 usage, this is not built. |
| Advanced ranking | 5-signal scoring (type rank, Personalized PageRank, status freshness, recency, curation level). Calibrated from v4.1 usage data. Nested granularity (full/summary/title-only). |
| New dependencies | `starlette`, `uvicorn`, `cachetools` |
| Write tool auth | `[mcp.security] allow_write_tools` opt-in for HTTP. `--read-only` flag from v4.1. |
| Authority transition | `portfolio.db` becomes authoritative for cross-project index, `.dev-hub/registry/projects.json` becomes a generated export. Only after zero discrepancies for 2 consecutive weeks. |

**Trigger criteria** (any one is sufficient):
1. JohnnyOS development begins and requires HTTP transport for process-to-process communication
2. A concrete consumer demonstrates the need for a persistent portfolio server (not session-scoped stdio)
3. v4.1 usage data shows startup-time DB rebuilds are a bottleneck for cross-project workflows

**Known issues to address in v4.2 proposal:**
- SDK memory leaks (#1076, #756) -- mitigated by uptime watchdog
- FastMCP shutdown bug (#514) -- mitigated by explicit signal handlers
- Keychain access from non-interactive launchd contexts -- investigate, document fallback to `chmod 0600` file token
- Single-worker constraint (SDK session store is process-local)
- Audit log rotation (size-based, 10MB cap, 3 rotated files)

---

## Version Sequencing

```
v4.0.0 (shipped)     v4.1.0 (proposed)       v4.1.1 (planned)        v4.2.0 (planned)
───────────────      ─────────────────       ─────────────────       ─────────────────
Single workspace  →  + project discovery  →  + FTS5 search         →  Background indexer
Read-only tools   →  + scaffold, log      →  + rename, promote     →  Write auth (HTTP)
Stdio only        →  Stdio only           →  Stdio only            →  + Streamable HTTP
No search         →  (no search)          →  FTS5 search           →  (preserved)
No bundles        →  (no bundles)         →  (no bundles)          →  Context bundles (if needed)
No security       →  --read-only flag     →  (preserved)           →  Full security model
```

**Sequencing rationale:** Each version is gated on validated demand from the previous. v4.1.0 is the minimum viable write surface. v4.1.1 adds search and the write tools that need contract work. v4.2 adds operational infrastructure when a concrete consumer (JohnnyOS) needs it.

The v4.1.0/v4.1.1 split was decided in the PR #84 Round 2 review (2026-04-11). Reviewers identified that even the v3 proposal bundled portfolio authority, search, and context bundles without evidence that they materially improve daily workflows. The narrowing: ship the two simplest write tools first, validate demand, then build up.
