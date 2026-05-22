---
id: project-ontos-github-issues-115-117-D.5-claude-opus-verifier
deliverable_id: project-ontos-github-issues-115-117
phase: D.5
role: verifier
family: claude-opus
status: completed
---

# D.5 Verifier — claude-opus

## Verdict

Approve

## Summary

The landed `ontos/` diff satisfies the binding contracts of all three issues (#115/#116/#117); the test suite passes 1321/1321 (2 skipped) and every B.1/D.2 blocker the packet names is closed. Two residual divergences from spec implementation sketches remain — both explicitly classified non-blocking by the D.3 verdict and confirmed cosmetic/doc-only here.

## Findings

**F1 — §2.2.3 CLI rendering bullet not implemented (non-blocking, per D.3).**
`ontos/commands/activate.py:104-105` and `:127-128` emit `validation.warnings` as bare `issue.message` strings; `format_activation_output` (`:144-168`) never renders `rule_id`/`document_id`/`file_path`. The orphan/depth/log-field message strings (`ontos/core/validation.py:160,174,195`) also do not embed doc context. So `ontos activate --json` — issue #117's literal reproduction command — still surfaces anonymous orphan/depth/log-field warnings on the CLI surface. The agent-facing structured channel is fully enriched: `ontos/mcp/tools.py:_validation_issues` populates `rule_id`/`document_id`/`file_path` from the `ValidationError` struct fields, satisfying contract §2.2.2 for the MCP `activate` tool. D.3 preserved this as claude-opus D.2 F2 / claude-sonnet D.2 F1, "CLI prose change deferred." Recommendation: at D.6, run the §5.5 smoke item ("orphan/depth/log-field warnings carry document_id and file_path") against the MCP `activate` tool, not `ontos activate --json`, or land the follow-up PR first — otherwise that one smoke bullet will read as failed on the CLI.

**F2 — §2.3.3 `ontology_spec.md` not updated (non-blocking, per D.3).**
The diff stat updates `docs/reference/Ontos_Manual.md` and adds `docs/releases/v4.5.0.md`, but `docs/reference/ontology_spec.md` is untouched, despite §2.3.3 naming it as a doc target for the new lifecycle type/status vocabulary. The enum members themselves are correctly added (`ontos/core/types.py:47-78`). D.3 preserved this as claude-sonnet D.2 F2, "deferred to follow-up doc PR."

Both items would be cleaner if spec §4 ("Out of scope") were amended to formally record the deferrals, so the spec and the landed code stop disagreeing. Neither blocks strict-P3 receipt acceptance, consistent with the D.3 ruling.

## Notes

Independently confirmed end-to-end:
- **#115** — `WARNINGS_LIST_TOOL_NAMES = {"get_context_bundle"}` (`schemas.py`) + `_attach_pre_activate_warning` (`server.py`) routes the pre-activate reminder into the declared `warnings` list, never an undeclared `_ontos_warning` key. Contract §1.2 met.
- **claude-opus B.1 F1 (graph-edge cleanliness)** — `graph.py` resolves all deps into `resolved_depends_on` (doc-ids only) before `graph.add_node(...)`; out-of-scope/broken entries are dropped from the edge list, no synthetic nodes. Closed.
- **gemini B.1 F1 (path-traversal containment)** — `_resolve_depends_on_path` rejects any candidate whose `resolve(strict=False)` (symlink-following) escapes `workspace_root_resolved` via `relative_to`. Closed.
- **claude-opus D.2 F1 (CLI workspace_root threading)** — D.4 commit `462a484` threads `workspace_root` through `map.py` → `ValidationOrchestrator` and `link_diagnostics.py` → `build_graph`. The §2.1 path-fallback resolver is now effective on `ontos activate`/`map`/`link-check`, not just the MCP path. Closed.
- §2.4 (`include_generic_bare_id_token=False` default in link-check), §2.5 (README/`*_template.md` skip with explicit-`id:` escape hatch), §2.6 (`check_activation_health` contributes `failed` on error-severity entries) all match their contracts. `workspace_root=None` preserves byte-identical legacy `build_graph` behavior.

`.venv/bin/python -m pytest -q` → 1321 passed, 2 skipped, in 49.30s.
