---
id: log_20260712_ontos-v5-0-0-structural-release
type: log
status: active
event_type: release
source: codex
branch: codex/ontos-v5.0.0
created: '2026-07-12'
depends_on: [project-ontos-v5-0-0-spec]
concepts: [release, cli, frontmatter, mcp, hardening, external-review]
---

# ontos-v5-0-0-structural-release

## Summary

Prepared the verified Ontos 5.0.0 product branch and preserved an honest,
provider-blocked lifecycle disposition with D.6 withheld.

## Goal

Build Ontos 5.0.0 from the shipped 4.7.1 mainline while applying only the
contract-changing and structural delta, retire the legacy script fork, provide
a complete migration guide, and run product and lifecycle gates without
granting any release authority.

## Key Decisions

- Used a fresh worktree from `origin/main@454b102`; PR #161 was prior art, not
  a rebase source of truth.
- Kept schema `4.0` intentional and separated command outcome under `result`.
- Stored verbose lifecycle material on a sibling evidence ref and committed
  only a hash index to the product branch.
- Withheld D.6 because the genuine provider dispatch produced no verdict or
  receipt; no fallback receipt was fabricated.

## Alternatives Considered

- Rebasing the dirty PR #161 branch was rejected because its v4.7.1 overlap
  diverged from the shipped implementation.
- Declaring provider-limited completion was rejected because that verifier also
  failed with an empty receipt inventory.

## Changes Made

- Implemented schema-4 CLI/JSON and declarative command dispatch contracts.
- Consolidated parsing/writes, physical link diagnostics, iterative graph
  traversal, MCP dispatch, and durable rename recovery.
- Removed `.ontos/scripts/`, rewired hooks/CI, bumped all version/golden
  metadata to 5.0.0, and added the migration guide.
- Reduced fresh documentation validation from the measured main baseline to
  zero findings and added evidence-ref integrity verification.

## Impacts

Consumers must migrate JSON parsing, exit-code handling, physical line-number
interpretation, and changed CLI flag semantics. Release approval remains
maintainer-deferred and currently withheld pending a genuine lifecycle rerun.

## Testing

- Full suite: 1,500 passed, one expected deprecation warning.
- Coverage: 82.36% against the 82% gate.
- Golden capture/compare: small and medium fixtures pass at 5.0.0.
- Package: sdist/wheel build, `twine check`, and non-editable wheel import pass.
- Docs: 199 documents, zero validation errors/warnings; link-check clean.
- Evidence-ref verifier passes; strict P3, provider-limited lifecycle, and D.6
  gates fail as recorded because no genuine external receipt exists.
