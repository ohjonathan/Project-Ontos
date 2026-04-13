---
id: log_20260413_fix-mcp-export-graph-output-schema
type: log
status: active
event_type: fix
source: Claude Code
branch: fix/mcp-export-graph-output-schema
created: 2026-04-13
---

# Fix MCP export_graph outputSchema (issue #97, PR #98)

## Summary

Fixed a v4.1.1 defect where the `export_graph` tool advertised a root
`{"oneOf": [...]}` outputSchema, violating the MCP spec (outputSchema
describes `CallToolResult.structuredContent`, which must be an object).
Claude Code's MCP client Zod-validates the entire `tools/list` response
as one unit, so this single bad schema caused it to silently drop **all
9** Ontos tools while the server still reported `Connected`.

## Goal

Ship the minimum point-release patch (Option B per issue #97) to unblock
strict MCP clients, without touching runtime payload validation or the
three-shape polymorphic return of `export_graph`. Defer the proper
discriminated-union refactor (Option A) to 4.2.0.

## Changes Made

- `ontos/mcp/schemas.py` — `output_schema_for("export_graph")` now returns
  `None` and has return type `Optional[Dict[str, Any]]`. Explanatory
  docstring added. `EXPORT_GRAPH_ADAPTER`, `validate_success_payload`,
  `ExportGraphResponse`, and `TOOL_SUCCESS_MODELS` untouched.
- `ontos/mcp/server.py` (`register`) — skips `server.set_output_schema`
  when the schema is `None`. `OntosFastMCP.list_tools()` already maps a
  missing entry to `outputSchema=None` via `dict.get()`.
- `tests/mcp/test_schemas.py` — replaced `test_export_graph_schema_is_one_of`
  with `test_export_graph_schema_is_omitted`; loosened the validation-loop
  assertion to accept `None`; added `test_every_advertised_output_schema_is_object_typed`
  as a schema-layer regression guard over `TOOL_SUCCESS_MODELS`.
- `tests/mcp/test_server_integration.py` — added two guards:
  `test_list_tools_output_schemas_are_object_or_absent` (inspects
  `list_tools()` return values) and `test_tools_list_wire_payload_has_object_typed_or_absent_output_schemas`
  (a transport-level round-trip that mirrors the MCP SDK's exact wire
  serialization at `mcp/shared/session.py:346` — `model_dump_json(by_alias=True,
  exclude_none=True)` — re-parses the JSON, and asserts every tool entry
  either omits `outputSchema` or types it as `object`, plus pins that
  `export_graph` has no `outputSchema` key on the wire).

## Key Decisions

- **Option B over Option A in this PR.** The issue recommended the two-step
  remediation; Option A requires a breaking change to the raw three-shape
  response and belongs in a minor bump (4.2.0). Option B is a ~30-line
  change that preserves runtime behavior identically.
- **Omit the key vs. advertise an empty `{"type": "object"}`.** Chose
  omission. Advertising `{"type": "object"}` with no properties would
  disable structured validation on the client for `export_graph` but
  imply *some* structured content is coming — omission is the more
  honest signal until Option A lands.
- **Transport-level wire test.** Added after reviewer flagged residual
  coverage gap. The higher-level `list_tools()` assertion misses
  serializer-layer regressions (e.g. a future Pydantic config change
  that emits `outputSchema: null` instead of omitting the key — some
  strict clients treat `null` as a validation failure). Test mirrors
  the MCP SDK's exact `model_dump_json(by_alias=True, exclude_none=True)`
  call so it pins the actual bytes Claude Code parses.

## Alternatives Considered

- **Option A now.** Rejected — breaking for any direct consumer of the
  raw three-shape `export_graph` response; bundling it in a point
  release would violate semver. Flagged as follow-up.
- **Version bump + PyPI yank of 4.1.1 in this PR.** Out of scope.
  `ontos/__init__.py` and `pyproject.toml` on `main` read `4.0.0`, so
  the release train needs maintainer confirmation before tagging 4.1.2.

## Testing

- `pytest tests/mcp/test_schemas.py tests/mcp/test_server_integration.py`
  → 13 passed (including the three new guards).
- `pytest tests/mcp/` → 171 passed (was 170 pre-PR).
- `pytest` (full repo) → 1138 passed, 2 skipped.
- **Protocol-level repro** (from issue #97 appendix): JSON-RPC stdio
  round-trip against `python3 -m ontos serve` on a freshly initialized
  workspace. Every tool serialized `outputSchema.type == "object"`
  except `export_graph`, which omitted the key entirely. Matches the
  expected-fix output verbatim.
- **Regression-catching verification** for the wire test: temporarily
  force-restored the `oneOf` schema and re-ran the serializer; confirmed
  the new guard would have failed.

## Impacts

- Claude Code (and any other strict-Zod MCP client) can now list and
  call Ontos tools against an `ontos serve` instance that carries this
  fix.
- No behavior change for tool runtime or for lenient clients.
- Future tools that reintroduce a non-object root outputSchema will be
  caught at three layers: schema unit test, `list_tools()` integration
  test, and serialized-wire round-trip.

## Follow-ups

- **4.2.0 Option A refactor.** Convert `ExportGraphResponse` to a
  discriminated-union object (`mode: Literal["summary","full","file"]`
  + optional payloads), re-advertise a proper object schema, update
  `tools.export_graph()` callers. Breaking for direct consumers of the
  raw three-shape response.
- **Release-train reconciliation.** Confirm whether HEAD should ship
  as 4.1.2 (point) or fold into 4.2.0 (minor bundled with Option A),
  then yank 4.1.1 from PyPI.
