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

## v4.1.0 -- Portfolio Authority (PROPOSED)

**Proposal:** `.ontos-internal/strategy/proposals/v4.1/Ontos-v4.1-Proposal.md` (v3)
**Research:** `.ontos-internal/strategy/proposals/v4.1/ontos-v4.1-research-consolidated.md`
**PR:** #84
**Review status:** Re-scoped per review verdict. Awaiting CA decision.

Extends the MCP server with portfolio indexing, cross-project search, write tools, and simple context bundling -- all over stdio.

| Capability | Detail |
|-----------|--------|
| 7 new MCP tools | `project_registry`, `search`, `get_context_bundle`, `scaffold_document`, `rename_document`, `log_session`, `promote_document` |
| Transport | Stdio only (HTTP deferred to v4.2) |
| Scope | Multi-workspace via `--portfolio` flag; single-workspace backward compatible |
| Storage | SQLite portfolio index (`~/.config/ontos/portfolio.db`) + FTS5 search |
| Bundle | Simple: kernel + in-degree + recent logs, greedy knapsack |
| Install | `pip install ontos[mcp]` (mcp>=1.27.0,<2.0) |

**Sequencing rationale:** Delivers the highest-value features (write tools, portfolio search) to today's consumers (Claude Code, Cursor) without the operational burden of HTTP transport, security model, and daemon management. Generates real usage data to validate whether the advanced bundle algorithm is needed.

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
| Advanced bundles | 5-signal scoring (type rank, Personalized PageRank, status freshness, recency, curation level). Calibrated from v4.1 usage data. Nested granularity (full/summary/title-only). |
| New dependencies | `starlette`, `uvicorn`, `cachetools` |
| Write tool auth | `[mcp.security] allow_write_tools` opt-in for HTTP. `--read-only` flag already in v4.1. |

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

## Version Sequencing Rationale

```
v4.0.0 (shipped)     v4.1.0 (proposed)       v4.2.0 (planned)
───────────────      ─────────────────       ─────────────────
Single workspace  →  Portfolio index       →  Background indexer
Read-only tools   →  Write tools           →  Write auth (HTTP)
Stdio only        →  Stdio only            →  + Streamable HTTP
No search         →  FTS5 search           →  (preserved)
No bundles        →  Simple bundling       →  Calibrated 5-signal
No security       →  --read-only flag      →  Full security model
```

The split between v4.1 and v4.2 was decided in the PR #84 review (2026-04-11). R1 (adversarial/product lens) identified that HTTP transport, security model, and daemon management are downstream of a consumer (JohnnyOS) that does not yet exist. Building supply-side infrastructure for projected demand is a sequencing risk. R2 (alignment/technical lens) confirmed the architecture is sound regardless of how it's sequenced. The decision: ship validated features first (v4.1), add operational infrastructure when demand materializes (v4.2).
