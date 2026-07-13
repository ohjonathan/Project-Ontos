---
id: log_20260712_ontos-v5-0-0-contract-fix-round
type: log
status: active
event_type: fix
source: codex
branch: codex/ontos-v5.0.0
created: '2026-07-12'
depends_on: [project-ontos-v5-0-0-spec]
concepts: [release, cli, mcp, hardening]
---

# ontos-v5-0-0-contract-fix-round

## Summary

Closed the six contract-correctness and migration-guide findings from the
independent PR #163 review, then completed an adjacent command-surface audit so
the documented exit taxonomy is true across the v5 CLI. The lifecycle evidence
disposition remains unchanged.

## Goal

Make the v5 command outcomes, warning exits, physical link locations, MCP tool
documentation, configuration compatibility, and migration guide match the
published 5.0.0 contract.

## Root Cause

The structural release introduced the schema-4 envelope and exit taxonomy, but
several legacy handler branches still returned pre-v5 codes. The migration
guide also omitted three observable compatibility surfaces, and the physical
line fallback did not count whitespace preceding a frontmatter fence.

## Key Decisions

- Reserve exit `1` for validation findings, use exit `2` for invalid input,
  exit `3` for warning-only outcomes, and exit `5` for internal failures.
- Clamp legacy numeric configuration bounds instead of rejecting configurations
  that earlier Ontos versions accepted.
- Sanitize unknown explicit JSON exit categories to the documented category
  derived from the numeric exit code.
- Preserve the existing withheld D.6 disposition and sibling evidence ref;
  this product fix round did not manufacture or rerun lifecycle evidence.

## Alternatives Considered

- Retaining an undocumented `error` exit category was rejected because schema
  `4.0` defines a closed category set.
- Documenting the new configuration rejections was rejected in favor of
  compatibility clamps, because rejecting the files on every command was not
  necessary to deliver the v5 structural contract.

## Fix Applied

- Corrected query, doctor, and link-check exit handling and added regression
  coverage for usage, internal-failure, and warning-only paths.
- Counted leading whitespace in the link-diagnostic body fallback so reported
  locations remain physical file lines.
- Updated the rename MCP description to match durable journal recovery and
  touched-path restoration.
- Expanded the migration guide for nested command names, configuration clamps,
  and the open, exhaustive `workspace_overview.graph_stats.by_type` mapping.
- Audited the remaining command handlers and moved legacy execution failures
  off findings code `1`, aligned JSON status/category/envelope behavior, and
  suppressed prompts and human output in JSON mode.

## Impacts

Consumers can now rely on the documented exit table without a stray `error`
category. Existing configurations with `log_retention_count=0` or
`max_dependency_depth<0` continue to load and are normalized to safe minimums.
Lifecycle approval remains withheld pending genuine provider/framework repair.

## Testing

- Full suite and coverage gate: 1,536 passed; 82.22% coverage (82% required).
- Integrated command-contract slice: 195 passed.
- Focused taxonomy suites: 90 map/log/rename tests, 99 direct-command tests,
  92 tuple-command tests, and 80 CLI/envelope contract tests passed.
- Golden comparison: small and medium fixtures pass at version 5.0.0.
- Manifest conformance: 4/4 checks pass.
- Lifecycle evidence-ref hash verification passes; evidence content is
  unchanged on `lifecycle-evidence/project-ontos-v5-0-0`.
