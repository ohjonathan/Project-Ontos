---
id: log_20260713_audit-tail-docs
type: log
status: active
event_type: chore
source: Codex
branch: codex/audit-tail-docs
created: '2026-07-13'
concepts: [docs, cli, workflow, testing]
depends_on: [project_ontos_audit_tail_docs_spec]
---

# audit-tail-docs

## Goal

Resolve the seven PR A documentation-accuracy findings from the v5 audit tail on a
fresh `origin/main@bbbad203ee826a1994f609890e6a70fb7dbe7a34` worktree. Bring the
human references, generated agent instructions, architecture documentation, and
Recent Activity output into agreement with the shipped v5 CLI and configuration
surface without taking release actions or entering a later remediation phase.

## Key Decisions

- Treat the parser registry and typed configuration models as the authoritative v5
  contract, including documenting current quirks that later PRs are assigned to
  change.
- Generate the quick-reference query as `ontos query --depends-on <id>` and update
  all root instruction artifacts through Ontos commands, preserving USER CUSTOM
  content.
- Share one Recent Activity summary policy: explicit frontmatter first, then the
  first substantive body text, then `No summary`, normalized and capped at 200
  characters; sort deterministically by `date`, `created`, and ID.
- Make timestamp-only instruction regeneration a semantic no-op, retain backups for
  material changes, and mark only the context map as generated. Regeneration is the
  documented conflict-resolution policy.
- Keep this patch scoped to the seven `D8-docs-clarity-*` findings and the PR A slice
  of inherited generated-artifact cleanup. Versioning, release, config, count, and
  dead-code changes remain assigned to later PRs.

## Alternatives Considered

- Hand-editing `AGENTS.md`, `.cursorrules`, `CLAUDE.md`, or
  `Ontos_Context_Map.md` was rejected because these are Ontos-managed artifacts.
- A custom Git merge driver for generated instructions was rejected in favor of
  deterministic regeneration after conflicts.
- Updating the documented portfolio defaults and consolidate retention count to
  their planned values was deferred because PR D owns the corresponding behavior
  changes; the manual describes the behavior actually shipped at this baseline.
- Reworking the detailed timeline map was left out because the finding concerns the
  Tier 1 Recent Activity summary and the tiered map already reuses that renderer.

## Impacts

- Replaced the Agent Instructions and Manual with v5-accurate command, flag,
  configuration, migration, MCP, hooks, and upgrade guidance.
- Added `docs/reference/Architecture.md` and linked it from contributor-facing
  material.
- Corrected the generated query example and regenerated the root instruction files
  without losing the llm-dev USER CUSTOM block.
- Improved Recent Activity summaries and stable ordering, with a reusable helper for
  the later consolidation dogfood PR.
- Suppressed timestamp-only instruction rewrites and unnecessary backups while
  preserving material-write safety.

## Testing

- Focused command, map, instruction-artifact, maintain, and golden-baseline tests
  passed.
- Three canonical full-suite runs produced the same known
  `test_read_only_portfolio_queries_existing_snapshot_without_mutation` WAL/SHM
  isolation failure. The final run passed 1,572 tests (the earlier runs passed 1,571
  before the last regression was added), and the failing test passed alone. The
  Phase 0 review explicitly accepted this pre-existing flake as non-blocking and
  assigned its natural fix to PR C.
- `scripts/llm-dev verify` and review-seat checks passed; strict external lifecycle
  review evidence remains intentionally pending for the draft PR.
- Final Ontos regeneration/no-op validation, doctor/link checks, scope checks, and
  `git diff --check` are recorded in the PR verification report.

## Testing
