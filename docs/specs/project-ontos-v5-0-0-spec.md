---
id: project-ontos-v5-0-0-spec
type: strategy
status: active
depends_on: [project-ontos-fable-repo-audit-2026-07]
concepts: [release, cli, outputschema, mcp, context-map]
---

# Ontos 5.0.0 structural release specification

## Goal

Ship the contract-changing #151–#157 work on the released 4.7.1 foundation,
complete #153–#155 rather than carrying PR #161's partial dispositions, and
make the product diff reviewable by keeping raw lifecycle evidence on a sibling
ref. PR #161 is historical input, not product-head certification.

## Normative contract

- Command JSON uses schema `4.0`, retains domain values under `data`, and adds
  `result.status`, `result.kind`, `result.exit_category`, and complete/explicit
  diagnostic counts.
- Exit codes are 0 clean, 1 findings, 2 usage/input, 3 warning-only, 5 internal,
  and 130 interrupted. Code 4 is reserved.
- The declarative command registry is authoritative for parser builders,
  handlers, aliases, visibility, result kinds, and nested command paths.
- `ontos/io/yaml.py` is the canonical frontmatter parser. Mutation paths use
  surgical frontmatter editing and preserve encoding markers, comments,
  quoting, ordering, and line endings.
- Link locations are physical one-based file lines. Wikilink aliases/headings
  resolve by target while retaining display text during rename.
- MCP reads, portfolio tools, and writes share one invocation boundary that
  preserves structured user-error codes and preactivation warnings.
- CLI and MCP rename lock before cleanliness/plan construction, journal exact
  original bytes before writes, and recover only touched paths after failure or
  crash. Unscoped git rollback is forbidden.
- Graph depth/cycle traversal is iterative and path identity respects the
  filesystem's case sensitivity.
- `.ontos/scripts/` and its CI execution are removed; package commands own hook
  and validation behavior.

## Acceptance

The complete test suite, focused contract/safety tests, golden comparison,
package build, non-editable install smoke, link-check, frontmatter diagnostics,
and Python 3.9–3.12 CI must pass. Golden metadata must identify Ontos 5.0.0.
Documentation validation must end with zero broken references, orphans, invalid
statuses, duplicates, and parse-failed candidates.

Strict-P3 is attempted honestly. Provider/framework failure evidence is kept
without reconstruction, and D.6 is withheld unless the framework's own strict
gate succeeds. No merge, tag, release, PyPI publication, or issue closure is
authorized by this deliverable.
