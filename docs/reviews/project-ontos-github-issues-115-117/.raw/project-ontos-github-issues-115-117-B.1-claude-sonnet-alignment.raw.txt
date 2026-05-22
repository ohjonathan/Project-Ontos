---
id: project-ontos-github-issues-115-117-B.1-claude-sonnet-alignment
deliverable_id: project-ontos-github-issues-115-117
phase: B.1
role: alignment
family: claude-sonnet
status: completed
---

# B.1 Alignment Review — claude-sonnet

## Verdict

Approve

## Summary

The spec is architecturally coherent, its contracts are clearly enumerated per issue, and §0 cross-cutting invariants correctly encode the two prior-decision constraints (conservative repair preservation; `additionalProperties: false` for public MCP schemas). Two should-fix gaps in contract precision and one nit on an underspecified abstraction are noted below but do not block implementation.

## Findings

### [F1] Snapshot warning classifier — unrecognized-prefix fallback not specified
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** spec §2.2.3, paragraph beginning "For snapshot bare-string warnings, route through a small helper…"
- **Issue:** The spec names two example prefix mappings (`"Log missing fields:"` → `rule_id="schema.log_missing_fields"`, `"Invalid frontmatter field"` → `rule_id="schema.invalid_frontmatter"`) but does not enumerate all known prefixes and does not specify what `rule_id` is emitted when a snapshot warning matches none of them. The contract in §2.2.2 hedges with "when available," which is technically sufficient, but the implementation leaves the fallback value (absent key vs. `null` vs. `"unknown"`) to the implementer. Different choices will produce an inconsistent `rule_id` namespace across warning types and break any downstream consumer that branches on `rule_id`.
- **Recommendation:** Add one sentence to §2.2.3 specifying the fallback: e.g., "Unrecognized snapshot warning prefixes receive `rule_id=None`; the field is omitted from the serialized dict." Optionally supply an exhaustive list of known prefixes or reference the location in source where they live.

### [F2] `validation_excluded` placement is architecturally ambiguous
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** spec §2.5.3, sentence "Excluded files are loaded into the doc inventory with a sentinel `validation_excluded=True` (new field on `DocumentData` or recorded in the loader's side state)."
- **Issue:** The "or" is load-bearing. Adding `validation_excluded: bool` to `DocumentData` is a core-type schema change that propagates to every constructor call and serialization path; keeping it in loader side state requires `validate_log_schema()` and `detect_orphans()` to accept or query that side channel. The two approaches have different interface contracts for every downstream consumer. Leaving the choice open risks an implementation that is internally inconsistent (e.g., side state in the loader but `DocumentData` field expected by validators).
- **Recommendation:** Commit to one approach in the spec. The `DocumentData` field is preferable for clarity and testability (the skip flag travels with the document, not separately); if so, note the constructor-call impact and confirm `validation_excluded=False` as the default for all existing construction sites.

### [F3] "Opt-in flag" for `_iter_generic_id_candidates` is underspecified
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** spec §2.4.3, sentence "Remove or guard `_iter_generic_id_candidates` so it's only invoked under an opt-in flag."
- **Issue:** "Opt-in flag" could mean a boolean keyword argument to the calling function, a module-level constant, an environment variable, or a passed-in options object. These have different discoverability, testability, and deprecation implications.
- **Recommendation:** Specify the mechanism — e.g., "add `allow_generic_candidates: bool = False` as a keyword argument to `scan_body_references()`" — so the test coverage in §2.4.4 and any future opt-in callers have a clear target.

## Notes

The five sub-issues under #117 are correctly structured as an integrated track rather than independent patches: §2.2 (warning enrichment) is a prerequisite for the diagnostic value of §2.1 (depends_on false-positive reclassification), and both feed §2.6 (doctor severity alignment). This sequencing is architecturally sound and is preserved in the implementation order implied by the spec. No conflicts with the stated prior lifecycle (`project-ontos-v44-agentic-activation-resilience-spec.md`) are evident from the spec text; the conservative-repair and schema-strictness invariants in §0 are consistent with v4.4 patterns as described.
