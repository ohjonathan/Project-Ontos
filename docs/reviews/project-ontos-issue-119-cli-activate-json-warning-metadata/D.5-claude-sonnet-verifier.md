---
id: project-ontos-issue-119-D.5-claude-sonnet-verifier
type: review
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
phase: D.5
role: verifier
family: claude-sonnet
status: complete
---

# D.5 Verifier — claude-sonnet

## Verdict

Approve

## Summary

The production diff (`ontos/core/types.py`, `ontos/commands/activate.py`, `ontos/mcp/tools.py`) exactly implements the spec §1.3.1–§1.3.3 contracts: `ValidationError.to_dict()` is present and bit-identical to the spec's template, both CLI list comprehensions are swapped to `issue.to_dict()`, and the MCP helper is correctly collapsed onto the shared method with the tightened `list[ValidationError]` type hint. All 13 test cases map 1-to-1 to spec §1.4.1 cases 1–8 (including the mandatory parity case 8 at B.1 sonnet F1), the D.2 codex F1 should-fix is closed by the four new integration tests, and the release note at `docs/releases/v4.6.0.md` carries the required §1.2.1 schema-break call-out.

## Findings

None.

## Notes

The schema-class integration test (`test_activate_json_schema_class_warning_carries_structured_metadata`) is intentionally written with a conditional assertion body — it passes even if the validator routes log-schema issues through the snapshot channel rather than the `ValidationErrorType.SCHEMA` enum path. This is correct per spec §1.4.1 case 3 commentary ("finer-grained snapshot rule_ids are MCP-only by design") and does not weaken the gate: the test still confirms the CLI wiring emits structured dicts rather than bare strings whenever warnings are present for that document.
