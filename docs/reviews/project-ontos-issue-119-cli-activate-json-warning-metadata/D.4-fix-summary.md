---
id: project-ontos-issue-119-D.4-fix-summary
type: review
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
phase: D.4
role: fix-author
family: claude-opus
status: complete
---

# D.4 Fix Summary — claude-opus (orchestrator-authored)

## Closure target

D.2 codex F1 (should-fix) — CLI integration tests cover only the orphan case end-to-end; depth / schema / out-of-scope / error cases were unit-tested through `to_dict()` only. See `docs/reviews/project-ontos-issue-119-cli-activate-json-warning-metadata/D.2-codex-peer.md`.

## Fix scope

**Tests-only.** No production code changes. The C-phase implementation (commit `a342e5b`) is already correct and passes the D.2 board on functional grounds (sonnet Approve, gemini Approve). The fix expands integration coverage so the CLI JSON path is end-to-end tested for each spec §1.4.1 case, not just the orphan case.

## Files touched

- `tests/commands/test_activate_json_warning_metadata.py` — four new integration tests added.

## New tests (each invokes the real CLI JSON path or `run_activation` directly)

| Spec §1.4.1 case | New test | Fixture / mechanism |
|---|---|---|
| Case 2 — Depth warning | `test_activate_json_depth_warning_carries_structured_metadata` | Temp workspace with `max_dependency_depth = 1` and a `doc_a → doc_b → doc_c` chain (3 hops). Subprocess `ontos --json activate`; asserts `rule_id == "depth"` with populated `document_id` / `file_path`. |
| Case 3 — Schema-class warning | `test_activate_json_schema_class_warning_carries_structured_metadata` | Temp workspace with a log doc missing required fields. Subprocess `ontos --json activate`; asserts the log doc's warning record carries the structured shape (`severity`, `document_id`, `file_path`, `rule_id`). |
| Case 4 — Out-of-scope dependency | `test_activate_json_out_of_scope_dependency_carries_structured_metadata` | Temp workspace with an external `.md` file outside `docs/` and a doc whose `depends_on:` references it. Subprocess `ontos --json activate`; asserts `rule_id == "out_of_scope_dependency"` with `document_id == "atom_with_external_dep"` and `file_path` ending in `docs/atom.md`. |
| Case 6 — Error parity | `test_activate_json_error_severity_lands_under_errors_with_structured_shape` | Monkeypatches `ontos.commands.activate.generate_context_map` to return a controlled `ValidationResult` with one error-severity entry plus one warning. Calls `run_activation` directly and asserts the error appears under `data.validation.errors` with `severity == "error"`, `rule_id == "broken_link"`, and populated context. |

## Tests + receipts

- New test file: `tests/commands/test_activate_json_warning_metadata.py` now has 13 tests (was 9 at C-phase): 6 unit + 1 parity + 1 orphan integration + 4 new integration cases (depth / schema / out-of-scope / error).
- Targeted suite (the same set the manifest's `G-test-1` runs): `.venv/bin/python -m pytest -q tests/commands/test_activate_json_warning_metadata.py tests/commands/test_agentic_activation_resilience.py tests/mcp/test_activation.py tests/mcp/test_context_map.py` → **28 passed** (was 24 at C-phase).
- Full Ontos test suite: `.venv/bin/python -m pytest -q` → **1334 passed, 2 skipped** (was 1330 at C-phase; the 4 new tests account for the delta).
- MCP regression coverage (`tests/mcp/test_activation.py`) continues to pass without modification — the C-phase refactor remains bit-identical on the MCP side.

## Adjudication notes

- **Codex D.2 F1 was a should-fix, not a blocker.** The C-phase implementation was already functionally complete (sonnet + gemini both Approve at D.2; orphan integration test already proved the CLI wiring). The fix expands test coverage to honor strict-P3 best practice: close addressable should-fix findings before D.5 verifier triple rather than carrying them to D.5 for re-litigation.
- **Schema-class test is shape-tolerant.** The log-schema fixture passes whenever the log doc's warning record carries the structured shape, regardless of which `rule_id` the validator chose (e.g. `schema` vs a snapshot prefix). This honors the spec's design that finer-grained snapshot `rule_id`s are MCP-only.
- **Error-parity test uses monkeypatch by design.** `generate_context_map()` does not naturally emit `error`-severity entries via the standard fixture pipeline (broken `depends_on` was downgraded to warning in PR #118). The monkeypatch is the cleanest way to exercise the wiring without inventing a synthetic validator rule.

## Phase advance

D.4 endorses advance to **Phase D.5 (verifier triple)**. The codex D.2 F1 should-fix is closed; the implementation surface remains exactly as it was at C-phase (no production code edits); coverage is now complete across all required §1.4.1 cases.
