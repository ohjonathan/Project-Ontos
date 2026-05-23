---
id: project-ontos-issue-119-D.2-codex-peer
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
phase: D.2
role: peer
family: codex
status: completed
---

# D.2 Peer Review — codex

## Verdict

Request changes

## Summary

The runtime implementation is small, clear, and appears correct: `ValidationError.to_dict()` centralizes the record shape, CLI JSON now uses it, and MCP `_validation_issues()` honors the amended `list[ValidationError]` type hint. The test file does not fully cover the required CLI JSON cases from the amended spec, so I am requesting changes on coverage adequacy rather than production behavior.

## Findings

### [F1] Required CLI JSON cases are only unit-tested through `to_dict()`
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** tests/commands/test_activate_json_warning_metadata.py:79
- **Issue:** Spec §1.4.1 requires the depth, schema, out-of-scope dependency, and error-severity cases to exercise the CLI JSON path by invoking `ontos --json activate`, `activate_command`, or `run_activation` and parsing/asserting the JSON envelope. The landed tests for those cases construct synthetic `ValidationError` objects and call `to_dict()` directly at lines 79, 98, 120, and 160, so they do not verify that real validator outputs land under `data.validation.warnings` / `data.validation.errors` with the enriched shape.
- **Recommendation:** Add CLI-path tests for depth, schema, and out-of-scope dependency using temp workspaces or direct `run_activation`, and add an error-path test via monkeypatched `generate_context_map` or a natural cycle fixture that asserts the structured record appears under `data.validation.errors`.

## Notes

I verified the B.1 gemini blocker is closed in the landed code: `ontos/mcp/tools.py:620` now types `_validation_issues(issues: list[ValidationError])`. I also re-ran the targeted review tests in two chunks: `tests/commands/test_activate_json_warning_metadata.py`, `tests/mcp/test_activation.py`, `tests/commands/test_agentic_activation_resilience.py`, and `tests/mcp/test_context_map.py`; all 24 passed.
