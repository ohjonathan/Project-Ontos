---
id: log_20260412_fix-mcp-stdio-stream-misrouting
type: log
status: active
event_type: fix
source: Claude Code
branch: fix/mcp-stdio-stream-routing
created: 2026-04-12
---

# Fix MCP stdio stream misrouting (v4.1.1 blocker)

## Summary

Root-caused and fixed a v4.1.0 blocker where `ontos serve` routed every JSON-RPC
response to stderr, breaking the initialize handshake for all stdio MCP clients
(Claude Code, Claude Desktop, Cursor, Continue, Zed). Scoped the defensive
stdout redirect to the setup phase only, and pinned `serverInfo.version` to the
installed ontos package version.

## Goal

Restore MCP stdio compatibility for v4.1.0 PyPI consumers without regressing
the original intent (protecting the JSON-RPC wire from stray prints during
server bootstrap).

## Changes Made

- `ontos/cli.py` (`_cmd_serve`) — replaced unconditional `sys.stdout = sys.stderr`
  + `finally:` restoration with `contextlib.redirect_stdout(sys.stderr)` scoped
  to the import/workspace-resolution block. The redirect now ends before
  `serve()` invokes FastMCP's `server.run(transport="stdio")`, so the stdio
  transport snapshots the real stdout.
- `ontos/mcp/server.py` (`OntosFastMCP.__init__`) — accept a `version` kwarg and
  assign it to `self._mcp_server.version` after `super().__init__(...)`, because
  `FastMCP.__init__` does not forward `version` to its inner `MCPServer`.
- `ontos/mcp/server.py` (`create_server`) — pass `version=ontos.__version__` when
  constructing `OntosFastMCP`.
- `tests/mcp/test_stream_routing.py` — new subprocess-level regression test with
  three cases: JSON-RPC response lands on stdout, stderr carries no JSON-RPC,
  and `serverInfo.version` equals `ontos.__version__`.

## Key Decisions

- Chose `contextlib.redirect_stdout` scoped to setup over removing the redirect
  entirely. Reason: current `ontos/mcp/` call sites already route prints via
  `file=sys.stderr`, but the scoped redirect preserves defense against future
  drift without breaking the stdio transport.
- Overrode `OntosFastMCP.__init__` to set `self._mcp_server.version` rather than
  passing `version=` directly to `FastMCP(...)`. Reason: `FastMCP.__init__`
  (mcp SDK 1.27.0) has no `version` parameter and rejects the kwarg with
  `TypeError`. The external memo's suggested fix was literally incorrect on
  this point.
- Kept the memo's "hide behind read-only `--version`" out of scope — that would
  be a behavior change to ship with the v4.1.1 release notes, not a bugfix.

## Alternatives Considered

- **Option A from the memo** (restore `sys.stdout` before `serve()` inside the
  existing try/finally). Rejected — functionally equivalent but less readable
  than a scoped context manager, and keeps the "two stdout swaps" mental model
  when one is enough.
- **Remove the redirect entirely.** Rejected — all present prints already route
  to stderr, but `from ontos.mcp import serve` transitively imports ~30 modules
  and any future `print(...)` without `file=` would silently corrupt the wire.
- **Pass `version=` to `FastMCP(...)`** directly. Rejected — not supported; see
  Key Decisions above.

## Testing

- Minimal reproduction (pre-fix, via `python3.14`-venv install of the dev
  checkout):
  - STDOUT bytes: `0`
  - STDERR bytes: `1151` (contained the JSON-RPC response)
  - `serverInfo.version`: `"1.27.0"` (mcp SDK version)
- Minimal reproduction (post-fix):
  - STDOUT bytes: `1150` (JSON-RPC response)
  - STDERR bytes: `0`
  - `serverInfo.version`: `"4.1.0"`
- `pytest tests/mcp/` via Python 3.14 venv: `168 passed` (includes the 3 new
  `test_stream_routing.py` cases).
- `pytest tests/ --ignore=tests/mcp` via system Python 3.9: `965 passed, 2
  skipped, 3 pre-existing failures` in `tests/commands/test_verify_portfolio.py`
  confirmed unrelated by re-running on clean `main`.

## Impacts

- Every stdio MCP client that connects to `ontos serve` now completes the
  initialize handshake against an ontos 4.1.1 install.
- `serverInfo.version` now reflects the installed ontos version, unblocking
  version-sensitive client behavior and making future version-skew issues
  easier to diagnose.
- No behavior change for CLI commands other than `ontos serve`.

## Follow-ups

- Cut v4.1.1 release with this as the sole change; draft release notes cover
  the blocker and the secondary version fix.
- Investigate pre-existing `test_verify_portfolio` failures under system Python
  3.9 (separate concern, not blocking this release).
