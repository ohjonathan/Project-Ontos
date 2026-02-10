---
id: log_20260210_github-releases-auth-fix
type: log
status: active
event_type: feat
source: Antigravity
branch: main
created: 2026-02-10
---

# GitHub Releases & Auth Fix

## Summary

Created GitHub releases for all 10 tagged versions (v3.0.0–v3.2.1) with detailed release notes sourced from the Ontos knowledge graph, CHANGELOG, commit history, and proposal docs. Root-caused and fixed a GitHub PAT authentication issue that was blocking CLI-based release creation.

## Key Decisions

- Created releases for ALL tagged versions (v3.0.0–v3.2.1), not just major ones
- v3.2.1 marked as "Latest" release
- Release notes stored in `docs/releases/vX.Y.Z.md` for future reference

## Implementation

- Wrote 9 release notes files in `docs/releases/` (v3.2.1 already existed)
- Created batch script `docs/releases/create_releases.sh`
- Root-caused HTTP 403: fine-grained PAT missing `Contents: write` permission
- User updated PAT permissions; remaining releases created via `gh` CLI
- Created `.agent/workflows/github-release.md` for future use

## Impacts

- `docs/releases/v3.0.0.md` through `docs/releases/v3.2.1.md`
- `docs/releases/create_releases.sh`
- `.agent/workflows/github-release.md`
- GitHub fine-grained PAT now has `Contents: write` scope