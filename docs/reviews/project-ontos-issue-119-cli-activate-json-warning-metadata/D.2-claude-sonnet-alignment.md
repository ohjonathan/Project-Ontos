---
id: project-ontos-issue-119-D.2-claude-sonnet-alignment
type: review
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
phase: D.2
role: alignment
family: claude-sonnet
status: complete
---

# D.2 Alignment Review — claude-sonnet

## Verdict

Approve

## Summary

The landed implementation faithfully executes the spec across all three touched files, honors every §0 invariant, closes the B.1 gemini F1 blocker with the tightened type hint, and documents the deliberate breaking change in both the spec and the release note exactly as §1.2.1 required.

## Findings

No findings.

## Notes

Each §0 invariant was checked against the landed diff:

**MCP behavior bit-for-bit.** The old `_validation_issues` loop and `to_dict()` are logically identical for any `ValidationError` instance. The old code used `getattr(issue, "error_type", None)` defensively (typed as `list[Any]`); `to_dict()` uses `self.error_type` directly. Because `error_type` is a dataclass field and the only call sites always supplied `validation.errors`/`validation.warnings` (both `List[ValidationError]`), the two expressions evaluate identically — the "bit-for-bit" claim holds. The parity test (Case 8) provides a runtime regression anchor.

**MCP schema unchanged.** `ontos/mcp/schemas.py` is absent from the diff.

**Human-readable path untouched.** `format_activation_output()` (lines 144–168) does not appear in the diff; only lines 104–105 were swapped.

**`_not_usable()` unchanged.** Lines 181–205 are absent from the diff; the Case 7 integration test verifies the empty-list contract end-to-end.

**Snapshot classifier MCP-only.** `_snapshot_issue()` and `_SNAPSHOT_RULE_PREFIXES` are absent from the diff.

**B.1 gemini F1 honored.** Parameter type tightened from `list[Any]` to `list[ValidationError]` in the landed `_validation_issues` signature.

**§1.2.1 schema-break call-out.** `docs/releases/v4.6.0.md` contains a clearly marked breaking-change section with before/after JSON examples; the spec carries the same call-out at §1.2.1.

All eight spec cases (§1.4.1) are present in `tests/commands/test_activate_json_warning_metadata.py`, and the full test suite reports 1330 passed at HEAD.
