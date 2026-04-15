---
id: log_20260415_retrofit-obsidian-pr110-review-fixes
type: log
status: active
event_type: fix
source: codex
branch: feature/v4.3.0-obsidian-retrofit
created: 2026-04-15
---

# retrofit-obsidian-pr110-review-fixes

## Summary

Implemented the PR #110 retrofit review fix set on `feature/v4.3.0-obsidian-retrofit`, verified the shared rename helper behavior, corrected the post-fix verification memo, and prepared the branch for publication.

## Goal

Land the requested v4.3.0 retrofit fixes without expanding scope, preserve existing behavior where CA had already decided not to change it, and leave the branch ready to push.

## Root Cause

The original retrofit implementation matched the broad plan shape but missed several edge cases in frontmatter patching and output reporting:

- replacement splices deleted inter-field comments
- merge-derived and tag-prefixed fields were treated as patchable inserts or replacements
- date-like scalars could round-trip as YAML dates instead of strings
- empty canonical values did not remove stale on-disk blocks
- inserted content could mix line endings in CRLF files
- loader issues were dropped from output
- JSON output omitted edit paths and in-sync files

## Fix Applied

Applied the seven requested fixes in order:

- preserved trailing comments by tightening shared field-block boundaries in `frontmatter_edit.py`
- treated merge-derived and tag-prefixed target fields as unpatchable with blocking warnings
- quoted date-like scalar values during serialization
- added explicit `remove` edits when canonical values are empty but stale blocks exist
- preserved dominant file line endings during insert and replace formatting
- surfaced loader issues in both human-readable and JSON output
- added `path` to `RetrofitEdit`, included in-sync files in `data.files[]`, and updated reporting

Also added the requested `_split_frontmatter` limitation comment and aligned the v4.3.0 release notes with shipped behavior.

## Key Decisions

- Kept batch-wide apply abort behavior unchanged, per the recorded CA decision.
- Kept `_split_frontmatter` as-is apart from the requested limitation note.
- Computed retrofit tags from canonical concept data rather than preserving stale explicit `tags` values, so removal and convergence work correctly.
- Treated only the intentionally edited post-fix verification memo as publishable; cleaned out scratch and activation artifacts instead of folding them into the branch.

## Alternatives Considered

- Skip-and-continue apply semantics for files with blocking warnings: rejected for this pass because the CA decision was to keep current abort behavior.
- Hardening `_split_frontmatter` beyond the requested comment: rejected as out of scope for PR #110.
- Preserving review and repro scratch files in the branch: rejected because they were local process artifacts, not part of the requested deliverable.

## Impacts

- Retrofit now converges cleanly on stale `tags` and `aliases` blocks.
- Frontmatter edits preserve inter-field comments and CRLF files more faithfully.
- Machine-readable output now includes edit paths, warning aggregates, remove counts, and noop files.
- The branch carries the requested implementation fixes plus the corrected verification note.

## Testing

- `python3 -m pytest tests/commands/test_retrofit.py -v`
- `python3 -m pytest tests/commands/test_rename.py -v`
- `python3 -m pytest`
- Manual smoke test of `ontos retrofit --obsidian` dry-run, apply, and idempotent second dry-run
