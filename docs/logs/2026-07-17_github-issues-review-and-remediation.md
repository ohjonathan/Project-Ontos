---
id: log_20260717_github-issues-review-and-remediation
type: log
status: active
event_type: feature
source: cli
branch: claude/ontos-github-issues-review-s88zbm
created: '2026-07-17'
depends_on:
  - project-ontos-github-issues-review-2026-07-proposal
concepts:
  - proposals
  - activation
  - link-check
  - config
---

# github-issues-review-and-remediation

## Summary

Reviewed all ten open GitHub issues (#149, #158, #165, #173–#178, #181)
against the v5.0.2 codebase with independent code-grounded investigations,
adversarial verification of every verdict, and end-to-end reproductions of
every bug claim. Wrote the consolidated disposition and design document
`docs/specs/project-ontos-github-issues-review-2026-07-proposal.md` and
implemented the four highest-value slices.

## Goal

Determine which open issues are real defects, which feature requests are
worth building for a multi-worktree/multi-device agentic workflow, and land
the confirmed fixes.

## Key Decisions

- **Implement now:** #176 fix (bare root-file dependency resolution),
  #181 slice-0 (nested archive layouts excluded from scans — a new bug
  found during review), #178 alias MVP (`[frontmatter.aliases.*]` +
  built-in `in-progress -> in_progress`), #173 slice-A (instruction-file
  ownership guard + content-based AGENTS.md staleness).
- **Design only (in the proposal):** #175 `map --check`/`merge-check`
  (common-dir lock and CAS leases rejected as protecting nothing real),
  #177 wikilink namespaces (full 4-mode policy matrix rejected), #174
  finding IDs + `findings diff --base` (sequenced after #177/#178 per the
  merged v5 plan), #173 digest core (batched with its payload consumers,
  not shipped unconsumed), #181 archive manifest/verify (backends gated on
  plan §18.3 Phase C), #165 registry (own session).
- **Board maintenance for #158/#149 enumerated but not executed** —
  GitHub issue mutations left for maintainer approval.

## Alternatives Considered

- Shipping the #173 digest fields this session — rejected: additive changes
  to the parity-frozen activate/MCP payloads must batch with
  `mcp/schemas.py` and parity-test updates in one focused commit.
- A git-common-dir coordination lock for worktrees (#175) — rejected:
  worktrees share no mutable Ontos on-disk state today.
- Full vocabulary extension for #178 (custom types/statuses) — deferred:
  ~98 enum-comparison call sites; `original_*` retention already preserves
  domain semantics.

## Impacts

- `ontos/core/graph.py` — bare-token dependency probe (fail-closed).
- `ontos/io/files.py` — segment-suffix skip-pattern matching.
- `ontos/core/config.py` — new `[frontmatter]` section with fail-closed
  alias validation.
- `ontos/core/frontmatter_repair.py` — config/built-in alias resolution
  with per-edit `source`.
- `ontos/core/instruction_artifacts.py`, `ontos/commands/{maintain,doctor,map}.py`
  — ownership classification, content-based staleness, no implicit
  overwrite of non-Ontos instruction files.
- Behavior notes recorded in `CHANGELOG.md` (Unreleased): doc counts drop
  for nested-archive repos; bare-dep classifications change in the fixed
  direction.

## Testing

Full suite green at every commit: 1568 baseline → 1613 tests
(45 added/rewritten). End-to-end verifications: issue #176's exact
scenario through `activate`/`doctor`/`link-check`; a fresh `git clone`
agreeing with its source checkout on AGENTS.md freshness; hand-authored
AGENTS.md surviving `ontos maintain` and `ontos map --sync-agents`
byte-identical; alias repair round-trip preserving `original_*` values.
