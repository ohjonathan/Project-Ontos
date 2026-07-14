---
id: project_ontos_audit_tail_docs_spec
type: spec
status: active
depends_on:
  - project_ontos_audit_remediation_release_line_tracker
  - ontos_agent_instructions
  - ontos_manual
---

# Audit-tail PR A — documentation accuracy

## Goal

Resolve the seven documentation-accuracy findings assigned to PR A without changing
the v5 command or configuration contracts. The resulting human reference, generated
agent instructions, contributor architecture guide, and context-map orientation must
all describe the same shipped behavior.

## Baseline and release boundary

This deliverable starts from `origin/main@bbbad203ee826a1994f609890e6a70fb7dbe7a34`,
the merge of Phase 0 PR #166. It is patch-safe v5.0.1 work. It does not change package
metadata, publish artifacts, close issues, or perform release actions.

## Finding contracts

### `D8-docs-clarity-1` and `D8-docs-clarity-5`

Rewrite the Agent Instructions and Manual against the actual v5 parser and typed
configuration model. Cover the command registry, global output controls,
`.ontos.toml` schema/defaults/precedence, migration, MCP, hooks, and supported upgrade
workflows. Remove nonexistent workflow modes, retired scripts, obsolete installers,
and commands or flag combinations the parser rejects.

### `D8-docs-clarity-2` and `D8-docs-clarity-8`

Render the generated quick-reference query as `ontos query --depends-on <id>`.
Regenerate `AGENTS.md`, `.cursorrules`, and `CLAUDE.md` through Ontos while preserving
each supported USER CUSTOM section. Generated instruction files are the common
activation protocol; no root file may retain the pre-v4.4 ritual.

### `D8-docs-clarity-3`

Document the existing age-based consolidation contract precisely:
`ontos consolidate --by-age --days 30`. This PR does not change consolidate flag
semantics.

### `D8-docs-clarity-4`

Use one reusable Recent Activity summary extractor for Tier 1 (including the
tiered map's reuse of Tier 1), so the later consolidation slice can consume the
same policy:

1. An explicit non-null frontmatter `summary` wins, including an intentional empty value.
2. Otherwise use the first substantive body text, skipping headings, HTML comments,
   and untouched scaffold/session placeholders.
3. Otherwise render `No summary`.
4. Normalize the result to one line and cap it at 200 characters.

Order recent logs deterministically by `date`, then `created`, then document ID, with
newer dates first and ID as the final stable tie-breaker.

### `D8-docs-clarity-6`

Add an indexed `docs/reference/Architecture.md` explaining package boundaries,
parser/dispatch flow, document-to-map and MCP data flow, safe writes, supported
extension points, test layers, and generated-artifact policy. Make it discoverable
from contributor-facing material.

## Inherited generated-artifact cleanup

Begin the `D5a-repo-redundancy-7` tail in this PR:

- A timestamp-only instruction regeneration is a no-op and creates no backup.
- A material forced rewrite still preserves the prior user file as required.
- Only `Ontos_Context_Map.md` is marked as generated for repository presentation.
- Regeneration after conflict is the policy; no custom merge driver is introduced.
- Activation's map-writer routing remains assigned to PR C.

## Acceptance

- Focused regressions cover summary precedence/filtering/truncation/order and
  material-versus-timestamp-only instruction writes.
- All three generated root instruction artifacts contain the valid query form and the
  current activation/session-end contract.
- The architecture reference is present in the regenerated context map.
- The complete suite, Ontos doctor/link validation, llm-dev gates, and
  `git diff --check` pass.
- The PR remains reviewable and contains no version, release, archive-slimming,
  dead-code, config, provenance, or breaking-path work from later phases.
