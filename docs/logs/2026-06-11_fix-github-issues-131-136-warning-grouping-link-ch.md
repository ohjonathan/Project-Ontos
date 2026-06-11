---
id: log_20260611_fix-github-issues-131-136-warning-grouping-link-ch
type: log
status: active
event_type: chore
source: cli
branch: feat/133-health-consistency
created: 2026-06-11
concepts: [validation, link-check, activation, health, mcp]
impacts: []
---

# Fix GitHub issues 131-136: warning grouping, link-check envelope and perf, external file deps, health consistency, map provenance (PRs 137-141, v4.7.0)

## Summary

Closed the six open "Ontos feels unstable" RCA issues (#131–#136) as a
stacked chain of five PRs (#137–#141) targeting v4.7.0, then applied a
round of review fixes from Codex feedback.

## Changes Made

- #137: context map renders the installed package version and provenance
  frontmatter (generator_version, scope, documents_loaded); doctor checks
  generator provenance.
- #138: activate groups warnings by rule_id with bounded samples by
  default; new --warnings/--warning-rule/--limit flags; new paginated
  list_validation_warnings MCP tool.
- #139: link-check emits the standard JSON envelope (schema_version 3.4),
  gains --summary/--limit/--no-suggestions/--frontmatter-only/--no-orphans,
  per-phase timings, stderr progress; known-ID body scan and suggestion
  engine optimized losslessly (709-doc run: 13+ min -> 3.3 s).
- #140: [validation] allowed_external_dependency_paths allowlist; resolved
  on-disk deps classified external_file_dependency at info severity;
  link-check file_dependencies re-bucketing.
- #141: shared core/health.py; query --health and doctor unified with the
  activation pipeline counts; connectivity n/a marker; config discovery
  contained to repo_root; v4.7.0 bump + CHANGELOG.

## Testing

Full suite green at each step (1354 -> 1433+ tests). Cross-command
count-consistency integration test added as the #133 regression guarantee.
