# Ontos Project Roadmap

**Last updated:** 2026-04-11
**Current version:** v4.0.0 (released)
**In development:** v4.1 ("Portfolio Authority")

---

## v4.1 — Portfolio Authority (in development)

**Status:** Spec v1.1 finalized, awaiting B.4 verification then Phase C implementation.

**Tracks:**
- **Track A (PR #1):** Portfolio index, 3 read tools, `verify` subcommand, flock lock substrate
- **Track B (PR #2):** 4 write tools, `--read-only` flag, index invalidation

See `.project-internal/v4.1/phaseA/Ontos-v4.1-Implementation-Spec.md` for full spec.

### Deferred from v4.1

Items explicitly deferred during v4.1 development. Each becomes a candidate for v4.2 scope.

| Item | Deferred Where | Why Deferred | Revisit Trigger |
|------|---------------|--------------|-----------------|
| HTTP/Streamable HTTP transport | Proposal review, PR #84 re-scope | No concrete consumer. JohnnyOS doesn't exist yet. | When JohnnyOS validates HTTP demand or another consumer emerges. |
| Security model (bearer token, audit logging, rate limiting) | Proposal review, PR #84 re-scope | Coupled to HTTP transport — no value without it. | Ships with HTTP transport in v4.2. |
| Daemon mode and background indexer | Proposal review, PR #84 re-scope | Stdio sessions are short-lived; startup rebuild is <1s. Background indexing adds complexity without clear benefit at current scale. | When portfolio size exceeds ~1000 docs or rebuild exceeds 3s. |
| Calibrated 5-signal context bundle scoring | Proposal review, PR #84 re-scope | Needs usage data from v4.1 to calibrate weights. Kill criterion defined in proposal Section 7.3. | After v4.1 has been in use for 2+ weeks and bundle quality feedback is available. |
| Personalized PageRank for bundle scoring | Proposal review, PR #84 re-scope | Part of 5-signal scoring. Deferred with it. | Ships with calibrated scoring in v4.2. |
| MCP Resources and Prompts primitives | Proposal review, PR #84 re-scope | No consumer demand. | When an MCP client requests Resources/Prompts support. |
| Cross-workspace `depends_on` validation | Proposal review, PR #84 re-scope | Schema supports it, but UI/validation adds complexity without clear use case. | When users report cross-project dependency tracking needs. |
| US-9: `rebuild_workspace()` failure handling | Spec review B-verdict, CA Response §3 | Implementation detail — the spec's error-handling framework is sufficient. Specific catch-and-warn logic is a coding decision. | Addressed during Track A implementation. |
| US-12: Risk assessment re-rating | Spec review B-verdict, CA Response §3 | Confirmed unchanged after corrections: A=MEDIUM, B=MEDIUM-HIGH, Shared=LOW. | No action needed unless scope changes. |
| Configurable rename (file path + ID) | Spec review B-verdict, OQ-2 resolution | CLI rename does not do file renames (zero `os.rename()` calls). Implementing file rename is entirely new functionality with case-sensitivity, date-prefix, and git-history concerns. | v4.2, when ID-only rename has been validated in production use and demand for file rename is confirmed. |
| `starlette`, `uvicorn`, `cachetools` dependencies | Proposal review, PR #84 re-scope | All downstream of HTTP transport. | Ships with HTTP transport in v4.2. |

---

## v4.2 — Tentative Scope (planning)

> **Note:** This section is tentative — to be refined before v4.2 proposal phase. Items below are seeds from v4.1 deferrals, not commitments.

### Candidate Features

1. **HTTP/Streamable HTTP transport** — The primary v4.2 feature. Enables remote MCP access, multi-client scenarios, and JohnnyOS integration.
2. **Security model** — Bearer token authentication, audit logging, rate limiting, CORS. Ships with HTTP.
3. **Daemon mode** — Long-running server with background indexer. Enables efficient remote operation.
4. **Calibrated 5-signal bundle scoring** — Replace simple in-degree scoring with the full 5-signal model (freshness, in-degree, concept density, staleness penalty, Personalized PageRank). Requires v4.1 usage data for calibration.
5. **Configurable file rename** — Extend `rename_document()` with opt-in file path rename capability. Requires solving: macOS APFS case sensitivity, log date-prefix conventions, git history preservation.
6. **MCP Resources and Prompts** — If consumer demand materializes by v4.2 planning phase.

### Planning Timeline

- v4.2 proposal phase begins after v4.1 Track B merges
- Priority order will be informed by v4.1 usage patterns and `.dev-hub` transition outcomes

---

## Completed Versions

| Version | Theme | Date |
|---------|-------|------|
| v4.0.0 | MCP Bridge (single-project, stdio, 8 read tools) | 2026-04-05 |
| v3.4.0 | Tiered context map, compact output | 2026-03-01 |
| v3.3.1 | External review remediation | 2026-02-12 |
| v3.3.0 | Unified loader, link-check, rename, command safety | 2026-02-11 |
