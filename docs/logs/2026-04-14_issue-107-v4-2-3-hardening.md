---
id: log_20260414_issue-107-v4-2-3-hardening
type: log
status: active
event_type: fix
source: codex
branch: codex/v4-2-3-issue-107-hardening
created: 2026-04-14
concepts: [portfolio, registry-path, fts, scanner, hardening]
---

# issue-107-v4-2-3-hardening

## Goal

Implement the `v4.2.3` hardening slice for Issue #107 on top of the shipped
`v4.2.2` baseline without adding new CLI or MCP surface area.

## Key Decisions

- Treated this as a patch release focused on MCP portfolio contract pinning:
  `registry_path` helper coercion, FTS invalid-query classification, and
  scanner stderr resilience.
- Accepted `os.PathLike` values for programmatic `registry_path` callers via
  `os.fspath(...)` while keeping missing-key behavior, explicit `None`, and
  other invalid values on the documented default-fallback path.
- Trimmed leading and trailing zero-width/BOM edge characters in addition to
  normal whitespace, while preserving interior characters.
- Kept literal-colon FTS queries such as `user:alice` on the known
  `E_INVALID_QUERY` path and documented that limitation inline and in the
  release notes.
- Preserved scanner warning format and re-emission policy, adding only
  `BrokenPipeError` / `EPIPE` resilience.

## Alternatives Considered

- Broadening FTS heuristics beyond the existing SQLite fragment set:
  rejected for this patch because the goal was to pin the current contract,
  not redesign query parsing.
- Introducing scanner warning dedupe:
  rejected because Issue #107 only called for hardening the stderr path, not
  changing the per-pass warning policy.
- Changing TOML-facing `registry_path` semantics:
  rejected because the ambiguity only exists for programmatic helper callers,
  and the patch needed to keep the shipped missing-key behavior intact.

## Impacts

- `portfolio.registry_path` now accepts `PathLike` inputs and handles
  zero-width edge trimming explicitly.
- The SQLite invalid-query fragment list is centralized and directly tested,
  including the `"no such column"` branch.
- Repeated discovery-pass warning tests now assert collision-policy
  invariants without depending on exact stderr equality.
- `v4.2.3` release scaffolding is in place: version bump, changelog entry,
  release note, and refreshed context map.

## Testing

- `python3 -m pytest tests/mcp/test_portfolio_config.py tests/mcp/test_portfolio.py tests/mcp/test_scanner.py tests/mcp/test_bundler.py tests/commands/test_verify_portfolio.py tests/mcp/test_portfolio_integration.py -q`
- `python3 -m pytest tests/ -q` (shows pre-existing unrelated CLI/parity
  import-path failures outside this patch area; MCP-targeted suites passed)
