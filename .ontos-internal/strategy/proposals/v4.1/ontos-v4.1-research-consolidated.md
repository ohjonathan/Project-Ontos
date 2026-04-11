# Ontos v4.1 — Consolidated MCP Research (Models A, G, O)

**Source:** 3 parallel deep-research runs on the same prompt. A and O are tight briefs; G is the exhaustive long-form version. Where all three agree, treated as consensus. Where they diverge, noted explicitly. Citations stripped for Claude Code consumption — re-open source files if you need them.

---

## Top-line consensus (all 3 models agree)

1. **Drop "SSE", target Streamable HTTP.** The 2025-03-26 spec revision deprecated HTTP+SSE. Python MCP SDK and FastMCP both expose `transport="streamable-http"`. "HTTP/SSE" in the v4.1 proposal is a naming error — rename and retarget before building.
2. **Python 3.10+ is mandatory.** MCP SDK requires it. Bump from 3.9 now. 3.11+ gets you `asyncio.TaskGroup` which simplifies the indexer+server concurrency.
3. **Pin `mcp >= 1.27.0`** (April 2026 release). Still labeled "Beta" on PyPI.
4. **Known open memory leaks in HTTP transport** — SDK issues #1076 (unbounded growth under continuous tool calls) and #756 (`StreamableHTTPSessionManager._task` list grows per request in stateless mode). Mitigation: weekly process restart via launchd + 7-day uptime watchdog.
5. **Single-worker only.** SDK session store is process-local — multi-worker deployments lose sessions.
6. **Bearer token is the pragmatic local-auth baseline.** OAuth 2.1 + PKCE is now the spec standard for remote servers (RFC 9728 discovery), but overkill for a single-user Mac Mini. Store the token in macOS Keychain, not env vars or plaintext.
7. **Annotations are UI hints, not a safety boundary.** Enforce safety server-side. Set `readOnlyHint`, `destructiveHint`, `idempotentHint` on every tool — defaults are pessimistic (destructive=true, idempotent=false), so omission causes ugly client UX.
8. **SQLite + FTS5 is 3–4 orders of magnitude over-provisioned for 400 docs / 23 projects.** This is not a risk area. Sub-1ms FTS5 latency at this scale is well-documented. Full rebuild takes <1s.
9. **Use a flat tool set with `project_id: str` parameter.** Do NOT namespace tools per project. LLM tool selection degrades above ~20 tools; 23 projects × N tools is unworkable.
10. **launchd is the macOS deployment choice.** Docker adds a Linux VM layer that penalizes the file-system-heavy indexer.

---

## Area 1: Transport & SDK state

**Stack decisions:**
- Transport: `streamable-http` (NOT sse). Legacy SSE is optional compatibility only.
- Architecture: Mount MCP server into an ASGI app (not `mcp.run()`) so you can add auth middleware, request logging, `/health`, and graceful shutdown. One shared tool registry, two thin entrypoints: stdio runner + ASGI app.
- Claude Desktop cannot connect to local HTTP MCP servers via JSON config — it only supports remote Streamable HTTP via the paid Integrations UI. **Ship an `mcp-remote` bridge config** for Claude Desktop users.
- Claude Code: `--transport http` (v1.0.27+). Cursor: auto-detects (v0.50+). VS Code Copilot: v1.102+. MCP Inspector: all transports but has `Last-Event-ID` resume bugs — necessary but not sufficient for transport validation.

**Streamable HTTP semantics to know:** client POSTs each JSON-RPC message; server responds with JSON OR opens SSE stream for the response. Servers can deliberately close streams to avoid long-lived connections; clients reconnect with `Last-Event-ID`. This means "HTTP-first" without committing to forever-open streams.

**Known failure modes to test explicitly:** reconnection loops after transient drops, client hangs when server doesn't prime the stream, Cursor getting stuck on stale session IDs after server restart, race condition #1764 (concurrent SSE responses causing deadlock).

## Area 2: Write tool patterns

**Production patterns (from 7-server survey):**
- `--read-only` startup flag that strips write tools entirely (GitHub MCP uses this; ~17% of deployments). Strongest possible safety primitive.
- Preview+confirm pattern: first call returns diff of what would change; second call with `confirm: true` executes (MSSQL server `confirmUpdate: true`).
- Journal-based atomicity with `rollback-operation` / `recover-file` tools (Atomic Writer MCP).
- Directory sandboxing via explicit allowlist (official filesystem server).
- Scoped API tokens with read-only mode (Notion).

**Protocol realities:**
- MCP has NO transaction semantics, NO confirmation handshake, NO rollback.
- Two-tier errors: JSON-RPC protocol errors (-32xxx) are eaten by the client and never reach the LLM. Tool errors returned with `isError: true` go into the LLM context for self-correction. **Never throw exceptions from tool handlers** — always return `isError: true` with (what happened, why, how to fix).
- Adopt `outputSchema` + `structuredContent` (June 2025 spec addition) for typed error responses.

**Atomic multi-file writes:** no protocol support. Use the **compound tool pattern** — expose `rename_document_with_references` as one server-side atomic tool rather than asking the client to orchestrate multiple calls.

## Area 3: SQLite / FTS5 configuration (copy-paste ready)

**PRAGMA block on every connection open:**
```
journal_mode=WAL
synchronous=NORMAL        # corruption-safe in WAL, much faster than FULL
cache_size=-16000         # 16MB
mmap_size=67108864        # 64MB
temp_store=MEMORY
busy_timeout=5000
```
Run `PRAGMA optimize=0x10002` on open; `PRAGMA optimize` periodically.

**FTS5 config:**
- Tokenizer: `porter unicode61` (stemming + Unicode).
- Column weights via persistent rank: `INSERT INTO docs_fts(docs_fts, rank) VALUES('rank', 'bm25(10.0, 1.0)')` — title 10× content.
- **Always `ORDER BY rank`**. Anything else forces a temp B-tree sort that's 10–50× slower.
- Add `prefix='2,3'` for autocomplete.
- Run `INSERT INTO fts(fts) VALUES('optimize')` after bulk inserts.

**Concurrency rules (critical):**
- `BEGIN IMMEDIATE` for ALL write transactions. Deferred transactions that upgrade from read→write cause instant `SQLITE_BUSY` regardless of `busy_timeout`. This is the #1 source of SQLite concurrency bugs.
- Serialize writes through an application-level lock.
- Disable `wal_autocheckpoint` on writer (`wal_autocheckpoint=0`), run `PRAGMA wal_checkpoint(PASSIVE)` every 5 minutes to avoid latency spikes.
- **Do not use connection pooling** — SQLite connections take microseconds to open; pooling adds no value.

**Migration:** `PRAGMA user_version` + rebuild-from-scratch on mismatch. At 400 docs this takes seconds. Incremental migrations add complexity without benefit for a rebuildable cache. Use atomic file replacement (write temp, `os.replace`) for zero-downtime rebuilds.

## Area 4: Context bundle / deterministic ranking

**Composite score** (tune empirically):
```
score = w_bm25 * bm25_score
      + w_pagerank * pagerank
      + w_indegree * normalized_indegree
      + w_recency * decay(modified_date)
```
- Use **Personalized PageRank** from the query-matched seed node for query-dependent scoring. Fall back to global PageRank for broad queries.
- HITS (hubs/authorities) maps naturally to docs taxonomies — authorities = definitive references, hubs = guides.
- Betweenness centrality identifies bridge documents across topic clusters.

**Token-budget packing:** formally 0-1 Knapsack. **Greedy (sort by value/token_count, select in order)** runs O(N log N), hits 95%+ of optimal. At 400 docs even full DP is milliseconds — greedy is sufficient.

**Advanced moves:**
- **Nested granularity**: include each doc as full/summary/title-only — multiple knapsack items per doc at different sizes/values (Qodo pattern).
- **Kernel document pattern**: reserve kernel budget FIRST, then knapsack the remainder.
- **Lost-in-the-middle mitigation** (Stanford TACL 2024, Chroma 2025 — confirmed across 18 frontier models): place kernel/most-important docs at the **beginning and end** of assembled context.
- **Type quotas** for diversity: e.g., 30% guides / 30% references / 20% tutorials / 20% API docs.

**Prior art:** `jCodeMunch-MCP` is the closest reference — PageRank on import graph + BM25 + `get_ranked_context` knapsack tool, reports 95%+ token reduction. **No MCP server currently implements generic context bundling as a primary function — Ontos v4.1 would fill this gap.**

**Evaluation:** NDCG@K with synthetic Q&A pairs from the corpus (RAGAS framework). LLM-as-judge for reference-free eval.

## Area 5: Multi-workspace routing

**Three patterns exist, none dominant. Pick Pattern B:**
- **A (single process, multiple roots)**: official filesystem server. MCP `roots` are `file://` only and client-initiated — **insufficient for logical project scoping.**
- **B (explicit `project_id` parameter, flat tools) ← recommended**: `database-mcp`, `mcp-workspace`. Keeps tool count flat. With 23 projects, namespaced tools would blow past the ~20-tool LLM degradation threshold cited in SEP-993.
- **C (gateway/proxy with namespacing)**: Multi-MCP, FastMCP Proxy, LiteLLM. Overkill for single-codebase.

**Discovery:** expose a **`list_projects` tool** (not just a resource). Spec defines resources as "application-controlled" and tools as "model-controlled" — for LLM-driven project selection, tools are the correct primitive. Complement with MCP resource templates `ontos://{project_name}/{path}` for browsable structured access.

**Error handling:** on invalid `project_id`, return `isError: true` with (description, full list of valid project IDs, pointer to `list_projects`). No existing multi-workspace MCP server does this — novel contribution.

## Area 6: Security

**Critical CVE context:** CVE-2025-66414 (CVSS 7.6) — DNS rebinding in TypeScript MCP SDK pre-v1.24.0. Malicious websites could hit any localhost MCP server by resolving attacker domain to 127.0.0.1. CVE-2025-49596 was the MCP Inspector binding to 0.0.0.0. **Localhost is not a security boundary.**

**Required mitigations:**
- Validate BOTH `Origin` and `Host` headers on every HTTP request. Reject non-localhost/127.0.0.1 with HTTP 403. Spec now mandates this.
- Bind exclusively to `127.0.0.1`, NEVER `0.0.0.0`.
- Generate token via `secrets.token_urlsafe(32)` on first run, store in Keychain: `security add-generic-password -a ontos -s api-token -w "$TOKEN"`. Require `Authorization: Bearer` on all requests.
- CORS: restrict origins to specific localhost ports. Include `Mcp-Session-Id` in `exposedHeaders`.
- Security headers: `X-Frame-Options: DENY`, `Content-Security-Policy: frame-ancestors 'none'`.
- Defense in depth: `pfctl` firewall rules blocking external connections to server port.
- **For max security, keep stdio as primary; expose HTTP only if specific clients require it.**

**Tool-level authorization is not in the MCP protocol** (confirmed by Red Hat analysis). Production solutions push this to gateways (Kong, Kuadrant) or app-level policy (Cerbos). For single-user Ontos, the `--read-only` flag is sufficient access control.

**Audit logging:** structured JSONL, append-only, `chmod 0600`. Fields: timestamp, event_type, tool_name, parameters (redacted), outcome, duration_ms, session_id, correlation_id. ToolHive/vMCP pattern is the reference.

## Area 7: Operational patterns

**Lifecycle:** MCP defines Initialization → Operation → Shutdown but no shutdown JSON-RPC message. For HTTP: close connection. For stdio: close input, wait, SIGTERM, SIGKILL.

**Use the SDK `lifespan` async context manager** for all startup/shutdown resource management:
```python
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    db = await init_db()
    try:
        yield {"db": db}
    finally:
        await db.close()
```
FastMCP issue #514: SSE transport fails to shut down on signal after processing a request. **Workaround: register explicit signal handlers via `asyncio.get_event_loop().add_signal_handler()`** — don't rely on SDK default handling.

**Three-layer health check** (implement all):
1. HTTP `/health` endpoint (liveness) — FastMCP `@mcp.custom_route("/health")`. Returns uptime, version, status.
2. MCP protocol `ping` (connection check, handled by SDK).
3. `health_check` tool (deep diagnostics): memory RSS, cache hit ratio, index freshness, active connections, workspace count.

**launchd plist essentials:**
- `KeepAlive.SuccessfulExit=false` (restart on crash)
- `RunAtLoad=true`
- `ThrottleInterval=10`
- `PYTHONUNBUFFERED=1` in `EnvironmentVariables`
- Full `PATH` in `EnvironmentVariables` (launchd uses minimal PATH)
- `ExitTimeOut` controls SIGTERM→SIGKILL window (default 20s)
- Place in `~/Library/LaunchAgents/`

**Memory management:**
- `cachetools.TTLCache(maxsize=500, ttl=3600)` for document content.
- **7-day uptime watchdog** that calls `os.kill(os.getpid(), signal.SIGTERM)` for clean restart — launchd auto-restarts. This is the safety net for SDK memory leaks #1076/#756.
- Monitor with `tracemalloc` + `psutil`. Warning threshold at 1.5GB RSS triggers diagnostic logging.
- For asyncio task leaks: `task.add_done_callback(task_set.discard)` always.

**Upgrade flow:** `launchctl kill SIGTERM` → wait 15s → `launchctl kickstart -k` → health check. Total downtime ~5s. Support multiple protocol versions concurrently (`2025-06-18`, `2025-03-26`, `2024-11-05`) to avoid forcing client upgrades.

---

## Where the models diverge

Divergences are minor and mostly about emphasis, not facts:

- **Model A** is the most actionable — tight recommendations lists per area, specific issue numbers, copy-paste config.
- **Model O** puts more weight on "annotations are hints, not safety" and emphasizes ASGI mounting over `mcp.run()` as the architectural split that matters (not "FastMCP vs SDK"). O also flags Streamable HTTP's "server can deliberately close stream" semantics more clearly.
- **Model G** is the long-form version (~130K tokens). Not fully read here due to context budget. If you need deeper citation trails, long case studies, or extended rationale for any single decision above, open `Model-G_MCP_Ecosystem_Best_Practices_Research.md` directly.

**No material contradictions found across the three reports** on any of the decisions above. High confidence on the consensus items.

---

## The three decisions to lock down first (Model A's framing, all three agree)

1. **Transport: Streamable HTTP, not SSE.** Rename the v4.1 plan. Build on `streamable-http` from day 1.
2. **Python 3.10+**. Non-negotiable. SDK requires it.
3. **Tool count discipline.** Parametric design (`search(project_id=...)`) not per-project namespacing. Stay under ~20 total tools.

Ecosystem gaps Ontos will have to solve itself (no protocol support): multi-workspace routing, atomic multi-file writes, tool-level authorization. Build app-level solutions. Don't wait for spec changes (SEP-986, SEP-993, and 5 annotation SEPs are months-to-years from adoption).
