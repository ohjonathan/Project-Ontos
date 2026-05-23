---
id: project-ontos-issue-119-B.1-claude-sonnet-alignment
type: review
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
phase: B.1
role: alignment
family: claude-sonnet
status: complete
---

# B.1 Alignment Review — claude-sonnet

## Verdict

Approve

## Summary

The spec is correctly scoped to the D.6-recorded deferral, carries the MCP parity contract from §2.2.2 of the prior spec forward to the CLI without re-litigating settled decisions, and preserves all architectural invariants established in PR #118. No blocking findings.

## Findings

### [F1] Parity assertion in §1.4.1 uses advisory language ("can include") instead of normative language
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** §1.4.1, final paragraph
- **Issue:** "The same test file *can* include a parity assertion: feeding a `ValidationResult` to `ValidationError.to_dict()` (CLI path) and to `_validation_issues()` (MCP path) yields identical lists." The "can" makes this optional, but the bit-identical claim in §0 cross-cutting invariants is load-bearing. If the parity assertion is not implemented, the primary guarantee in §0 has no direct regression coverage — the separate MCP regression (§1.4.2) and CLI tests (§1.4.1 cases 1–7) cover outputs indirectly but not the identity of the two serialization paths.
- **Recommendation:** Change "can include" to "must include" (or number it as Case 8) so that the parity assertion is a required test, not aspirational. This closes the gap between the §0 invariant and the test surface without adding scope.

## Notes

All other alignment checks pass:

- **D.6 deferral scope**: The implementation surface (three files, §1.3.4) is exactly what D.6 deferred — no snapshot classifier, no MCP schema, no human-readable output path, no validation rule changes.
- **MCP wire format bit-identical**: The `to_dict()` logic in §1.3.1 replicates `_validation_issues()` field by field (squashing rule, `doc_id` → `document_id`, `filepath` → `file_path`, `error_type.value` → `rule_id`). The `getattr` guard is defensively correct and does not alter behavior for well-formed enum values.
- **`_not_usable()` path unchanged**: The two-line swap in §1.3.2 is inside the `if docs:` block, so the empty-list path is structurally untouched. §1.4.1 Case 7 provides explicit regression coverage.
- **Schema break properly adjudicated**: §1.2.1 records the deliberate `list[str]` → `list[dict]` break with rationale (rejection of dual-emit alternative), call-out obligations, and consumer impact — consistent with the prior spec's handling of similarly scoped breaking changes.
- **`DocumentLoadIssue.to_dict()` pattern**: The choice to place serialization on the dataclass follows the existing convention at `ontos/io/files.py:36`, which CLI already consumes at `activate.py:125`. This is architecturally consistent.
- **MCP regression guard (§1.4.2)**: Existing `test_validation_issues_enriches_*` and `test_validation_issues_drops_empty_context_fields` cases are correctly identified as must-pass-unchanged, providing the load-bearing check that the MCP refactor (§1.3.3) is wire-identical.
