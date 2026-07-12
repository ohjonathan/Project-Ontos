---
id: log_20260711_project-ontos-v4-7-1-hotfix
type: log
status: active
event_type: chore
source: cli
branch: audit/v4.7.1-hotfix
created: '2026-07-11'
---

# project-ontos-v4-7-1-hotfix

## Summary

Split PR #161 by observable contract, reconstructed a focused v4.7.1 hotfix
from `main`, closed the live serializer/data-integrity and filesystem-safety
findings, and ran the llm-dev lifecycle through D.5. External verifier dispatch
remained provider/framework limited, so D.6 is explicitly withheld.

## Goal

Ship only behavior-preserving bug fixes in a focused draft v4.7.1 PR while
holding schema, exit-code, CLI, and graph contract changes for v5.0.0.

## Key Decisions

- Kept the non-breaking `ontos/io/yaml.py` parser/serializer foundation in the
  patch because the P0 fix depends on it.
- Retained replacement decoding for general reads; mutation paths decode strict
  UTF-8 and fail without rewriting bytes.
- Kept command envelopes byte-compatible with `main`: schema 3.4, the baseline
  eight-key set, and no schema-4 `result` object.
- Preserved failed dispatches and raw evidence; no receipts were reconstructed.
- Used the maintainer-authorized provider-limited process label while recording
  the framework's actual `provider_limited_fallback_incomplete` result.

## Alternatives Considered

- Moving all parser work to v5 would have broken the P0 serializer dependency;
  rejected.
- Making the broad loader strict UTF-8 in 4.7.1 would drop documents that
  previously loaded; deferred to v5 with migration guidance.
- Pointing fallback declarations at empty expected artifacts would mechanically
  satisfy one v2.0.1 path but falsify the real stderr evidence; rejected.
- Using plain SQLite `mode=ro` would follow WAL correctly but may create sidecar
  files; the hotfix publishes a truncating snapshot and records versioned
  immutable snapshots as the stronger follow-up.

## Changes Made

- Safe YAML serialization with exact semantic round trips and ID validation.
- Symlink-safe, exclusive, durable transaction staging and cross-platform locks.
- Configured, collision-refusing CLI log creation and strict mutation decoding.
- Read-only MCP write suppression and self-contained portfolio snapshots.
- Quoted-key-aware frontmatter surgery with full-mapping postconditions.
- v4.7.1 version/docs/manifest/tracker and D.1–D.5 lifecycle evidence.

## Testing

- Focused final D.4 set: 82 passed.
- Complete suite: 1572 passed, 2 skipped, 2 warnings; pre/post porcelain equal.
- Inherited doctor RCE regressions: 5 passed.
- Manifest conformance: 4/4; re-adjudication queue: 3/3 valid.
- Envelope remains schema 3.4; v5 paths and tracked goldens match `bf91b42`.
- Strict lifecycle: `review_pending` (12 issues).
- Provider-limited lifecycle: `provider_limited_fallback_incomplete` (12 issues).

## Impacts

The patch stops active frontmatter corruption and unsafe overwrites without
changing JSON shape, normal success exits, or golden command output. Log
collisions and unsafe mutation paths now fail closed. PR #161 remains untouched
until this hotfix merges, after which it can be rebased and converted to v5.0.0.
