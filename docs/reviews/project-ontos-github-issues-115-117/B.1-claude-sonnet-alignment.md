---
id: project-ontos-github-issues-115-117-B.1-claude-sonnet-alignment
type: review
deliverable_id: project-ontos-github-issues-115-117
phase: B.1
role: alignment
family: claude-sonnet
status: complete
---

# B.1 Alignment Review — claude-sonnet

## Verdict

Approve

## Summary

The spec is architecturally consistent, references the correct source locations, and its contracts are enumerated with sufficient precision for implementation. Three should-fix items address contract ambiguities that could lead to divergent implementations; no blockers found.

## Findings

### [F1] §2.2 contract vs. implementation code block inconsistent on absent fields
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** spec §2.2.2 (contract prose) vs. §2.2.3 (implementation code block)
- **Issue:** The contract states: "Bare snapshot warnings carry `rule_id` when available; `document_id` and `file_path` **remain absent** for warnings that genuinely have no doc context." The `_validation_issues()` implementation code block directly below contradicts this with `"document_id": issue.doc_id  # always present (may be empty string)`. These are different code paths (`_validation_issues` handles `ValidationError` objects; `_normalize_warnings` handles bare strings), but the comment "always present" is applied to the shared dict shape, which will confuse implementors about what the MCP `WarningEntry` schema extension must accept vs. what the server always emits.
- **Recommendation:** In §2.2.3, annotate the code block to indicate it applies only to `_validation_issues()`, and add a separate bullet for `_normalize_warnings()` that explicitly states `document_id` and `file_path` keys are **omitted** (not set to empty string) when unavailable, so the schema optional declaration and the runtime dict shape are consistent.

### [F2] `ValidationErrorType.OUT_OF_SCOPE_DEPENDENCY` enum member not listed as an explicit implementation step
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** spec §2.1.3
- **Issue:** The implementation says to "emit a `ValidationError` of a new `error_type` `ValidationErrorType.OUT_OF_SCOPE_DEPENDENCY`" but does not include adding this member to the `ValidationErrorType` enum in `ontos/core/types.py` as an explicit bullet. Every other new type/status enum addition in §2.3 includes an explicit "add the new enum members in `ontos/core/types.py`" step. An implementor who reads §2.1.3 in isolation may miss adding the enum member and produce an `AttributeError` at runtime.
- **Recommendation:** Add an explicit sub-bullet in §2.1.3: "Add `OUT_OF_SCOPE_DEPENDENCY = 'out_of_scope_dependency'` to `ValidationErrorType` in `ontos/core/types.py`."

### [F3] `workspace_root` threading: only `activate.py` caller enumerated; other `build_graph` callers unnamed
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** spec §2.1.3 (last bullet)
- **Issue:** The spec says to wire `workspace_root` through "from the activation / context-map orchestration." `build_graph` is called from at least `activate.py` and likely from `context_map` and `link_check` orchestration paths. Naming only `activate.py` leaves unresolved whether other callers must also be updated. If `link-check` independently calls `build_graph` without `workspace_root`, the false-positive broken-dependency errors will persist in that code path even after the fix ships.
- **Recommendation:** Enumerate every direct caller of `build_graph` and specify whether each should pass `workspace_root` (or explicitly note that `workspace_root=None` is intentional for a given caller and explain why).

### [F4] `COMPLETED` alias semantics underspecified
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** spec §2.3.2
- **Issue:** `COMPLETED = "completed"` is described as a "sibling alias of `COMPLETE`." It is unclear whether both enum members coexist (frontmatter `complete` → `COMPLETE`, `completed` → `COMPLETED`) or whether `completed` is a normalization alias that maps to the existing `COMPLETE` member. The distinction affects whether `COMPLETE` and `COMPLETED` are interchangeable in the validator output and whether downstream code checking `status == DocumentStatus.COMPLETE` would miss docs with `completed` frontmatter.
- **Recommendation:** Clarify: are these two distinct members with two distinct values, or should `normalize_status()` map both `"complete"` and `"completed"` to the single `COMPLETE` member? If two distinct members, note that callers checking `== COMPLETE` must be updated to include `COMPLETED`.

### [F5] `validation_excluded` placement left ambiguous
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** spec §2.5.3
- **Issue:** The spec says "new field on `DocumentData` or recorded in the loader's side state" without committing to one. Adding a field to `DocumentData` is an API change (any code constructing or pattern-matching `DocumentData` must update); using side state avoids that but requires threading a separate dict into validators. The ambiguity could produce two divergent but individually valid implementations.
- **Recommendation:** Pick one. Recommend adding `validation_excluded: bool = False` to `DocumentData` (making it a first-class attribute, consistent with `doc_id` and `filepath`) and note that existing `DocumentData` constructors default the field to `False`.

## Notes

The spec's §0 cross-cutting invariants (conservative repair preservation and `additionalProperties: false` discipline) are well-aligned with the existing `StrictModel` pattern in `ontos/mcp/schemas.py`. The rule-ordering in §2.1.2 (rules 1 → 2 → 3 → 4 → 5) is unambiguous on second reading even though the numbering conflates resolution attempts with outcome categories. The §2.4 generic-mode change (wikilink-only `BARE_ID_TOKEN`) is a meaningful behavioral narrowing but is explicitly opt-in-safe for `known_ids` and `rename_target` modes, preserving all existing callers. No prior-decision conflicts detected against the referenced upstream artifacts (`ontos_manual`, `ontology_spec`, `ontos_agent_instructions`).
