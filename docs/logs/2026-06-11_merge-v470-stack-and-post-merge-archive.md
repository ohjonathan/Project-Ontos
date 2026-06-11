---
id: log_20260611_merge-v470-stack-and-post-merge-archive
type: log
status: active
event_type: release
source: cli
branch: main
created: 2026-06-11
concepts: [devops, workflow, docs]
impacts: []
---

# Merge v4.7.0 stack (PRs 137-141) and post-merge archive

## Summary

Merged the issue #131–#136 stacked PR chain into main after Codex review
fixes and two pre-merge polish items (migration-guide support-policy
version references; precise link-check orphan-basis labeling). Verified
the merged tree (1442 tests passing, version 4.7.0), then archived the
session: dropped empty hook-generated init logs, and regenerated the
context map so it carries its own v4.7.0 generator provenance.

## Key Decisions

- Merged bottom-up (#137 → #141), retargeting each PR to main immediately
  before its merge after GitHub closed #138 on base-branch deletion
  (restored the base from its commit and reopened rather than rewriting
  history).
- Discarded the auto-generated `*_init.md` logs: empty templates with no
  session content (and a wrong branch field) — noise, not records.

## Impacts

Release v4.7.0 is on main; remaining release steps are tagging and PyPI
publish.

## Testing

Full suite on merged main: 1442 passed, 2 skipped. `ontos doctor` and the
regenerated map verified post-merge.
