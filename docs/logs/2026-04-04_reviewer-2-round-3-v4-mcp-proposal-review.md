---
id: log_20260404_reviewer-2-round-3-v4-mcp-proposal-review
type: log
status: active
event_type: exploration
source: codex
branch: proposal/v4.0-mcp
created: 2026-04-04
---

# reviewer-2-round-3-v4-mcp-proposal-review

## Objective

Review the revised v4.0 MCP proposal as Reviewer 2, round 3, strictly through the Technical lens.

## Goal

Determine whether the narrowed v4.0.0 proposal is architecturally coherent and feasible against the current Ontos codebase, with special attention to tool grounding, cache invalidation, workspace identity, and serialization claims.

## Findings

The split to a thin single-workspace MCP bridge materially reduced scope and removed the largest speculative elements from v4.0.0. Deferring SQLite, FTS, context bundles, and cross-project tools leaves a plausible stdio server around existing snapshot and graph primitives.

The proposal still overstates how directly current CLI JSON can be reused. `ontos map --json` only returns a small success envelope, while the only existing rich graph JSON is the custom `ontos-export-v1` assembly in `export_data.py`. The proposed `context_map()` shape therefore still requires a new adapter and serializer contract.

The revised invalidation approach is better than directory mtime and directionally correct, but `max(file.st_mtime)` plus file-count checks is not a complete fingerprint. It depends on an unstated rescan step to notice new files and can still miss path-set substitutions where count and max mtime do not change.

Implicit workspace identity fixes the immediate UX problem from round 2. It is technically coherent for a one-process-per-workspace stdio model, but it should be treated as an explicit v4.0 limitation rather than a generally solved identity model.

## Conclusions

The proposal is now close to viable at the architectural level, but it still needs language tightened around serialization parity and cache invalidation before approval. The remaining work is mostly contract clarification rather than a rethink of the whole direction.

## Key Decisions

- Treat v4.0.0 as a single-project MCP bridge only.
- Accept implicit workspace identity for stdio single-workspace serving.
- Reject the current "serialization parity with `ontos map --json`" claim as inaccurate.
- Require a stronger snapshot fingerprint description than `max(mtime) + count`.

## Alternatives Considered

- Keep the broader v4.0 scope including portfolio indexing and context bundles. Rejected because it reintroduced new storage, ranking, and search subsystems with weak grounding.
- Keep explicit `workspace_id` on v4.0.0 tools. Rejected because it imposed avoidable discovery friction on the primary single-workspace use case.
- Accept the proposal's current serialization wording at face value. Rejected because it does not match the live CLI output shape.

## Impacts

- If the architect corrects the serialization and invalidation claims, v4.0.0 can likely proceed as a thin adapter release.
- If those claims remain overstated, implementation planning will underestimate the amount of new response-shaping and cache logic still required.

## Next Steps

Revise the proposal to ground `context_map()` against either a new explicit serializer contract or the existing export pipeline, and replace the current invalidation fingerprint with one that captures file-path set changes as well as mtimes.
