---
id: log_20260511_v4-4-agentic-activation-resilience
type: log
status: active
event_type: chore
source: codex
branch: codex/project-ontos-v44-agentic-activation-resilience
created: 2026-05-11
concepts: [agentic_activation, mcp, frontmatter_diagnostics]
impacts:
  - project_ontos_v44_agentic_activation_resilience_spec
  - v440
---

# v4.4 agentic activation resilience

## Goal

Implement the v4.4 Agentic Activation Resilience plan across CLI, MCP, diagnostics, docs, tests, and llm-dev lifecycle artifacts.

## Key Decisions

- Add explicit `ontos activate` and MCP `activate` instead of relying only on prompt convention.
- Treat `usable_with_warnings` as actionable context so large lifecycle repos remain usable.
- Preserve previous enum values as `original_type` and `original_status` during conservative repair.
- Keep MCP `session_end` mutable-only and document `ontos log -e "slug"` as the read-only fallback.

## Alternatives Considered

- Blocking activation on every warning was rejected because legacy lifecycle repos can have many non-blocking warnings.
- Broad automatic enum repair was rejected in favor of known lifecycle artifact mappings only.
- Advertising `_ontos_warning` on all schemas was narrowed to read tools after the full suite caught write-schema drift.

## Impacts

- GitHub #103: MCP activation is harder to skip through instructions, tool state, and skipped-read warnings.
- GitHub #111: activation is best-effort and scan exclusions are consistent across maintenance paths.
- GitHub #112: frontmatter diagnostics and repair are structured and test-covered.
- GitHub #109: local full suite now passes with `1300 passed, 2 skipped, 2 warnings`; CI remains the final closure gate.

## Testing

- `bash scripts/llm-dev verify manifests/project-ontos-v44-agentic-activation-resilience.yaml`
- `.venv/bin/python -m pytest -q tests/mcp/test_activation.py tests/mcp/test_server_integration.py tests/mcp/test_read_only_registration.py tests/mcp/test_refresh.py tests/mcp/test_server_portfolio_mode.py tests/mcp/test_schemas.py tests/mcp/test_write_tools.py tests/commands/test_agentic_activation_resilience.py tests/core/test_frontmatter_repair.py tests/commands/test_agents.py tests/commands/test_instruction_protocol.py`
- `.venv/bin/python -m pytest -q`
