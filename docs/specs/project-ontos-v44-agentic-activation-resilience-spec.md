---
id: project_ontos_v44_agentic_activation_resilience_spec
type: atom
status: active
depends_on:
  - ontos_agent_instructions
  - ontos_manual
---

# Project Ontos v4.4 Agentic Activation Resilience Spec

## Scope

This release is additive. It changes Ontos CLI, MCP, docs, and tests without removing existing commands or tool contracts.

## Activation Model

`ontos activate` scans the configured scope, refreshes the context map when documents load, and returns:

- `usable`: documents loaded with no validation or load warnings.
- `usable_with_warnings`: actionable context exists, but load or validation warnings should be visible.
- `not_usable`: no actionable context can be produced.

Human output ends with `Loaded: [...]`. JSON output uses the standard command envelope.

## MCP Session State

The MCP server registers `activate` as a read tool. It sets per-server-session activation state on the live cache. Read tools that run before activation add `_ontos_warning` to their structured response. Server instructions tell agents to call `activate` first.

Writable servers also register `session_end`, which writes a structured log with Goal, Key Decisions, Alternatives Considered, Impacts, and Testing. Read-only servers omit write tools and instruct agents to use `ontos log -e "slug"` as the fallback.

## Frontmatter Diagnostics

Invalid `type` and `status` diagnostics include:

- path
- line when available
- field
- observed value
- allowed values
- severity
- blocking flag
- suggested fix

`ontos doctor --frontmatter` surfaces these diagnostics. `ontos maintain --fix-frontmatter-enums` plans or applies conservative repairs.

## Repair Workflow

Known lifecycle artifact values map to valid Ontos enums. Previous values are preserved as `original_type` or `original_status`. Unknown values remain unresolved and block `--apply` so the command never silently rewrites ambiguous metadata.

## Scan-Scope Consistency

`map`, `doctor`, `verify --all`, and frontmatter repair use configured scan exclusions. Generated lifecycle review folders can be excluded with absolute-style patterns such as `*/docs/reviews/*`.

## Test Anchors

| Anchor | Evidence |
|--------|----------|
| ACT-001 | CLI `activate` JSON and generated context-map status |
| MCP-001 | MCP `activate`, skipped-read warning, read-only omission |
| FM-001 | structured diagnostics and enum repair |
| SCAN-001 | scan exclusions shared by verify/map/repair paths |
| GIT-001 | linked git worktree detection |
