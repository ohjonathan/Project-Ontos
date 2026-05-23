---
id: project-ontos-github-issues-115-117-D.2-claude-sonnet-alignment
deliverable_id: project-ontos-github-issues-115-117
phase: D.2
role: alignment
family: claude-sonnet
status: completed
---

# D.2 Alignment Review — claude-sonnet

## Verdict

Request changes

## Summary

The core API/MCP contracts for all three issues are correctly implemented and the B.1 blockers remain closed, but two spec-mandated implementation items are absent from the diff: the `ontos/commands/activate.py` CLI output enrichment (§2.2.3) and the `docs/reference/ontology_spec.md` type/status table update (§2.3.3). All other alignment checks pass.

## Findings

### [F1] CLI output enrichment not implemented in `activate.py`
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** `ontos/commands/activate.py` (absent from diff stat)
- **Issue:** Spec §2.2.3 explicitly requires the human-readable CLI output to print `[{rule_id}] {message} ({document_id} @ {file_path})` when those fields are present. `ontos/commands/activate.py` does not appear in the branch diff at all, so the MCP-layer enrichment (which correctly lands `rule_id`, `document_id`, `file_path` in the JSON channel) is not surfaced in the CLI output that developers interact with most directly.
- **Recommendation:** Update `_run_activate_command` (or its warning-printing loop) in `ontos/commands/activate.py` to render the enriched fields when present, falling back to the bare message as specified.

### [F2] `docs/reference/ontology_spec.md` not updated for new type/status values
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** `docs/reference/ontology_spec.md` (absent from diff stat)
- **Issue:** Spec §2.3.3 requires extending the type/status enumeration tables in both `docs/reference/Ontos_Manual.md` AND `docs/reference/ontology_spec.md`. `Ontos_Manual.md` received 19 lines (✓), but `ontology_spec.md` is untouched. The eight new `DocumentType` values and five new `DocumentStatus` values are therefore undocumented in the canonical ontology reference.
- **Recommendation:** Add the new `handoff`, `tracker`, `retro`, `review`, `spec`, `report`, `adr`, `policy` types and `proposed`, `ready`, `completed`, `revised`, `in-lifecycle` statuses to the relevant enumeration tables in `ontology_spec.md`, matching the treatment already applied to `Ontos_Manual.md`.

### [F3] README/_template exclusion skips docs entirely rather than sentinel-flagging them
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** `ontos/io/files.py:289-293`
- **Issue:** Spec §2.5.3 describes loading excluded files "into the doc inventory with a sentinel `validation_excluded=True`" and then having `validate_log_schema()` / `detect_orphans()` skip sentinel docs. The implementation uses `continue` before the doc is added to the inventory, which means README/_template files never appear in any doc count, completeness report, or future query. The sentinel approach would preserve discoverability; the skip approach is more aggressive.
- **Recommendation:** The noise-reduction goal is fully met either way, so this can stay as-is if the team prefers simplicity. If the inventory completeness matters, migrate to a sentinel field on `DocumentData`.

### [F4] Spec-named test files `test_bundler.py` and `test_server_integration.py` absent from diff
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** `tests/mcp/` (diff stat shows only `test_activation.py +97`)
- **Issue:** Spec §1.4 calls for a new test case in `tests/mcp/test_bundler.py` (pre-activate `get_context_bundle` validation) and a regression in `tests/mcp/test_server_integration.py` (backward-compat `_ontos_warning` for `READ_WARNING_TOOL_NAMES` tools). The 97-line `test_activation.py` addition likely covers this coverage, but because only the stat — not the content — is visible in the packet, consolidation cannot be confirmed.
- **Recommendation:** Verify that `test_activation.py` includes the pre-activate `get_context_bundle` case (schema-valid, no `_ontos_warning` key, `warnings` contains the activation string) and the `READ_WARNING_TOOL_NAMES` regression case. If not, add them; if yes, no action needed.

## Notes

**B.1 preserved blockers confirmed closed:**

- *claude-opus F1 (graph-edge cleanliness):* `graph.add_node` now receives `resolved_depends_on` (the list of doc-id strings after path resolution) rather than the raw `depends_on` strings from frontmatter. Confirmed in the `graph.py` diff at the bottom of the loop — `graph.add_node(doc_id, doc_type, str(doc.filepath), resolved_depends_on)`. ✓

- *gemini F1 (path-traversal containment):* `_resolve_depends_on_path` calls `resolved.relative_to(workspace_root_resolved)` and skips any candidate whose resolved path escapes the workspace. The `strict=False` resolve plus the `ValueError` catch on `relative_to` correctly handles symlinks and missing paths without leaking filesystem state. ✓

**§115 fix alignment:** `WARNINGS_LIST_TOOL_NAMES = {"get_context_bundle"}` is correctly placed adjacent to `READ_WARNING_TOOL_NAMES`. The `_attach_pre_activate_warning` refactor routes the warning through `validated["warnings"]` for `get_context_bundle` (schema-declared field) and through `validated["_ontos_warning"]` for the legacy tools. The warning string matches exactly. The implicit "else: emit nothing" path is correct — the function falls through without modification for any tool not in either set.

**§117 depends_on resolution:** The `_resolve_depends_on_path` return convention uses `(doc_id, None)` / `(None, Path)` / `(None, None)` instead of the spec's `(id, "edge")` / `(None, "external")` / `(None, "broken")` tuples, but the caller logic is semantically equivalent. `workspace_root` is wired through `create_snapshot → build_graph` and `create_snapshot → ValidationOrchestrator → build_graph`. The `ValidationErrorType.OUT_OF_SCOPE_DEPENDENCY = "out_of_scope_dependency"` entry is present in `types.py`.
