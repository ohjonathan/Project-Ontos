---
id: log_20260713_v5-b1-finding-remediation
type: log
status: active
event_type: v5-b1-finding-remediation
source: codex
branch: codex/ontos-v5.0.0
created: '2026-07-13'
depends_on: [project-ontos-v5-0-0-spec]
concepts: [release, cli, outputschema, mcp]
---

# Ontos v5 B.1 finding remediation

## Goal

Address all 11 independently reproduced findings from the current-head B.1
adversarial review while preserving the v4.7.1 base, evidence isolation, draft
state, and release hold.

## Key Decisions

- Derive `result.exit_category` exclusively from the numeric process exit code;
  preserve an explicit caller `result_status` independently.
- Treat partial link-check phases as incomplete diagnostics without changing
  their full-run counter semantics.
- Resolve graph paths by exact path and actual device/inode identity so case
  behavior follows the underlying filesystem.
- Bind rename staging artifacts to a random journal token and journaled
  destination, retaining recovery compatibility with schema-v1 journals.
- Keep lifecycle evidence bound to reviewed product head `5678e91`; the fix
  head must undergo a fresh lifecycle before D.6 can be reconsidered.

## Alternatives Considered

- Retaining unconditional graph casefolding was rejected because it hides
  broken case-variant references on case-sensitive filesystems.
- Sweeping every hidden `.tmp` or `.bak` file was rejected because recovery
  must never remove files outside the interrupted rename transaction.
- Reusing the earlier lifecycle verdict for the changed product head was
  rejected because lifecycle receipts are head-bound.

## Impacts

The JSON envelope, migration-report payload, registry result kinds, partial
diagnostic completeness, physical line reporting, CRLF/BOM handling, graph
identity, rename crash recovery, and evidence-ref test coverage now match the
v5 contract. Release approval remains withheld pending a fresh lifecycle run.

## Testing

- Focused contract/safety suite: 332 passed.
- Full suite: 1,553 passed with one expected deprecation warning.
- Coverage: 82.21%, above the 82% gate.
- Golden comparison: small and medium fixtures passed at 5.0.0.
- Documentation: 202 documents, zero broken references, orphans, or load warnings.
- Evidence-ref verifier and pre-commit hooks passed.
- sdist/wheel build, `twine check`, and non-editable wheel `init`/`map` smoke passed.
