---
id: project_ontos_v5_0_3_built_in_status_alias_proposal
type: spec
status: proposed
created: 2026-07-15
owner: Project Ontos Maintainers
depends_on:
  - project_ontos_v5_remediation_release_plan_proposal
concepts:
  - proposals
  - release
  - frontmatter
  - schema
  - testing
---

# Project Ontos v5.0.3 Built-In Status Alias Proposal

## 1. Decision Requested

Approve this narrow child to proceed to Phase A for a scope-locked
specification. The child adds one protected, built-in status repair to the
existing conservative frontmatter plan/apply workflow. It does not authorize
implementation in this governance PR, and it does not approve any other part of
the workspace-vocabulary program.

Requested Template 16 disposition: **Proceed to Phase A**.

## 2. Authority and Evidence

This child is authorized for independent Pre-A review by the accepted parent
release-plan proposal, especially its v5.0.3 contract in §11.4 and child split
in §21.2. The review baseline is `main@bd04620376ed6a8d0024e990e04a86da402b9398`.

Direct inspection of the baseline establishes that:

- `ontos/core/frontmatter_repair.py` already has protected `TYPE_REPAIRS` and
  `STATUS_REPAIRS` tables;
- `build_enum_repair_plan()` turns known invalid enum diagnostics into explicit
  `EnumRepairEdit` records and leaves unknown values unresolved;
- `apply_enum_repair_plan()` uses the existing `SessionContext` buffered-write
  transaction;
- `_apply_file_edits()` preserves a pre-existing `original_status` and uses the
  formatting-aware frontmatter patch pipeline; and
- `tests/core/test_frontmatter_repair.py` already exercises planning,
  unresolved values, original-value preservation, BOM, comments, quoting, and
  CRLF behavior.

Issue [#178](https://github.com/ohjonathan/Project-Ontos/issues/178) is the
custody authority. This child completes only its safe built-in-alias checkbox.

## 3. Problem and Product Value

`in-progress` is a common historical spelling of Ontos's canonical
`in_progress` status. Today it is diagnosed as an invalid enum with no known
repair, even though the intended canonical meaning is unambiguous. Users must
edit affected frontmatter manually, which is slower and more error-prone than
the existing reviewed repair workflow.

The useful product change is deliberately small: recognize this one historical
spelling as a protected built-in repair while retaining every existing safety
property. General workspace vocabulary belongs to the separate v5.1 #178
children and must not leak into this patch.

## 4. Goals

- Make the one approved historical spelling appear as repairable in a
  deterministic enum-repair plan.
- Apply the repair only through the existing explicit apply workflow.
- Preserve the source value in `original_status` when that field is absent.
- Never overwrite a pre-existing `original_status` value.
- Preserve comments, quoting style where the patcher permits, UTF-8 BOM, and
  LF/CRLF line endings under the existing formatting-safety contract.
- Keep unresolved statuses unresolved and visibly diagnostic.
- Add focused unit and command-level regression coverage.

## 5. Non-Goals

- No arbitrary normalization or guessing for unknown statuses.
- No custom or workspace-defined vocabulary.
- No dynamic mutation or replacement of `DocumentStatus`.
- No type aliases and no second status alias.
- No new CLI command, MCP mutation tool, or implicit repair during activation,
  doctor, map, query, or link-check.
- No change to the public `EnumRepairPlan` shape unless Phase A finds an
  unavoidable compatibility need and sends the proposal back for re-review.
- No closure of #178.

## 6. Owned, Composed, and Forbidden Scope

### 6.1 Owned implementation surface

- `ontos/core/frontmatter_repair.py` for the protected mapping only;
- `tests/core/test_frontmatter_repair.py` for plan/apply and byte-preservation
  tests;
- `tests/commands/test_maintain.py` for the existing plan/apply command path;
  and
- `docs/reference/Ontos_Manual.md` for the user-facing repair note.

The child also owns its proposal, future Phase A spec, tracker, manifest,
review packet, and retrospective.

### 6.2 Composed authority

The child reads but does not own
`docs/specs/project-ontos-v5-remediation-release-plan-proposal.md`. The parent
defines the v5/v6 boundary and #178 custody.

### 6.3 Forbidden sibling scope

The child must not edit configuration parsing, the required-version preflight,
the canonical enum definitions, MCP schemas/tools, the dependency resolver,
log-path resolution, or any other v5.0.3 child's implementation surface.

## 7. Proposed Contract

The complete mapping inventory owned by this child is exactly:

```text
in-progress -> in_progress
```

The Phase A specification must preserve these rules:

1. Matching is limited to the existing invalid-enum diagnostic for the literal
   status spelling shown above after the repair engine's existing value
   extraction. It does not create fuzzy, punctuation-insensitive, or
   case-guessing behavior beyond current protected-table semantics.
2. A plan entry identifies `field=status`, the observed value, canonical target,
   `original_field=original_status`, repairability, source path, and source line
   when available.
3. Plan ordering remains deterministic under the existing scanner and repair
   plan contracts.
4. Plan mode performs no writes, creates no lockfile, and changes no Git state.
5. Apply reuses the exact reviewed plan and the existing buffered transaction;
   it does not rescan and silently broaden its target set after user review.
6. When `original_status` is absent, apply records the source status there.
   When it is already present, apply leaves it byte-for-byte unchanged.
7. The frontmatter patch must retain unrelated keys, comments, quoting,
   document body, BOM, and line endings under the existing patcher contract.
8. Every other unknown status remains non-repairable and continues to report a
   deterministic explanation rather than a guessed target.
9. Human and JSON plan output remain derived from the same `EnumRepairPlan`.
10. Apply failure is transactional: no subset of a multi-file plan is presented
    as successful.

## 8. Issue Custody and Dependencies

- #178 remains open after this child ships.
- The child records completion against only the built-in-alias checklist item.
- The full v5.1 workspace alias, extension, frozen-path, receipt, query/export,
  CLI, and MCP work remains with later #178 children.
- This child can be specified and implemented independently of the dependency,
  log-path, and required-version children, subject to normal shared-file
  serialization.
- This child owns its code, tests, and manual update through merge-readiness.
  Version bumps, packaging, publication, and the final v5.0.3 release decision
  remain with Project Ontos Maintainers under the existing release process
  after all four v5.0.3 children complete; no unscaffolded integration child is
  implied.

## 9. Safety, Migration, and Rollback

No automatic migration occurs. Users first inspect a plan and must explicitly
request apply. The source spelling is retained in `original_status`, so the
semantic history remains visible after repair.

Rollback is a normal patch revert of the mapping and focused tests. Documents
already repaired remain valid because `in_progress` is canonical. Rollback must
not reverse user documents automatically or remove their provenance field.

## 10. Acceptance Outline for Phase A

Phase A must turn the following outline into executable, source-anchored
acceptance criteria:

| Area | Required evidence |
|---|---|
| Mapping cardinality | Exactly one new `STATUS_REPAIRS` entry and no type mapping |
| Plan | Literal historical spelling is repairable; unrelated unknown spellings are not |
| Provenance | `original_status` is added only when absent and never overwritten |
| Formatting | Fixtures cover comments, single/double quotes, BOM, LF, and CRLF |
| Safety | Plan is read-only; apply uses the existing transaction and reports failures honestly |
| Surface | Existing maintain human/JSON output remains coherent; no implicit repair path appears |
| Custody | #178 stays open and records only this slice as complete |

## 11. Categorized Unknowns

### 11.1 `must-resolve-pre-A`

None. The problem, single mapping, safety posture, and custody boundary are
sufficiently narrow for a specification pass.

### 11.2 `resolve-during-A`

- Freeze the exact human and JSON reason text for this protected mapping without
  changing the established plan schema unnecessarily.
- Specify behavior when a document already contains a conflicting
  `original_status`; the default direction is preserve it and report enough
  context for the user, never overwrite it.
- Name the complete formatting fixture matrix and the failure-injection point
  for transaction tests.
- Decide whether command-level coverage belongs entirely in the existing
  maintain suite or needs one new focused test module inside the same scope.

### 11.3 `defer`

- Workspace-configured aliases, alias precedence, custom semantic extensions,
  frozen paths, and cross-surface vocabulary rendering defer to v5.1 #178.
- Any second historical spelling requires its own evidence and governance; it
  is not implicitly approved by this proposal.

## 12. Review Questions

### 12.1 Product lens

1. Is a single protected repair the smallest useful way to remove this manual
   cleanup burden without implying general vocabulary support?
2. Is plan-first explicit apply sufficiently clear to prevent users from
   mistaking activation or doctor for a mutating command?
3. Does retaining `original_status` provide enough provenance without adding a
   new public model?
4. Are the #178 custody and release-integration boundaries understandable to a
   user reading only this child?

### 12.2 Technical lens

1. Can the change remain a one-entry extension of the existing repair table and
   reuse the current planner, formatting patcher, and transaction unchanged?
2. Do the proposed tests falsify accidental fuzzy matching, provenance
   overwrite, formatting damage, and partial apply?
3. Are any current scanner normalization steps capable of widening the literal
   match beyond the approved mapping?
4. Does any CLI or MCP surface reconstruct repair data instead of consuming the
   shared plan object?

## 13. Exact Template 16 Verdict Set

The non-author GLM reviewer must select exactly one:

- **Proceed to Phase A** — direction and boundary are ready for a detailed
  specification;
- **Revise and re-review** — amend this proposal and repeat Pre-A review;
- **Split into multiple proposals** — split again and send every resulting
  child through Pre-A; or
- **Abandon direction** — stop this child and record why.

No abbreviated verdict is valid lifecycle evidence.

## 14. Recommendation

Return **Proceed to Phase A**. The user value is concrete, the change composes an
existing conservative mechanism, and the scope is independently reversible.
Phase A should then freeze the exact plan/apply and formatting contract before
any production edit begins.
