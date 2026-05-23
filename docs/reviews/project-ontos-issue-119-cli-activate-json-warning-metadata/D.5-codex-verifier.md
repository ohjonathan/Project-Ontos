---
id: project-ontos-issue-119-D.5-codex-verifier
type: review
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
phase: D.5
role: verifier
family: codex
status: complete
---

# D.5 Verifier — codex

## Verdict

Request changes

## Summary

The production diff matches the serialization contract, and the targeted and full pytest gates pass. One D.2 should-fix item is still not fully closed because the schema CLI integration test can pass without proving a schema warning is emitted through the CLI JSON path.

## Findings

### F1 — Schema CLI integration coverage is still not load-bearing

- **Severity:** blocker
- **Where:** [tests/commands/test_activate_json_warning_metadata.py](/Users/jonathanoh/workspaces/Project-Ontos/tests/commands/test_activate_json_warning_metadata.py:461)
- **Issue:** Spec §1.4.1 case 3 requires the CLI JSON path to assert a warning record with `rule_id == "schema"` plus populated `document_id` / `file_path`. The landed test filters only by `document_id`, then conditionally asserts only if records exist; in the current fixture the first matching record can be the log doc's orphan warning, so this test would still pass if the schema warning disappeared.
- **Fix:** Filter/assert for the schema-class record explicitly, e.g. `w.get("rule_id") == "schema"` with `assert schema_records`, then assert `document_id` and `file_path`.

## Notes

Verified: `scripts/llm-dev doctor` PASS, `scripts/llm-dev verify ...` PASS, targeted suite `28 passed`, full suite `1334 passed, 2 skipped`. `verify-lifecycle --mode strict-p3` is still pending D.5 verifier receipts, which is expected before this verifier result is recorded.
