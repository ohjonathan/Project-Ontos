---
id: project-ontos-github-issues-115-117-D.2-claude-opus-peer
deliverable_id: project-ontos-github-issues-115-117
phase: D.2
role: peer
family: claude-opus
status: completed
---

# D.2 Peer Review — claude-opus

## Verdict

Request changes

## Summary

Issue #115, #116, the type/status widening (#117 §2.3), README/template skip (§2.5), `body.bare_id_token` tightening (§2.4) and doctor severity alignment (§2.6) are implemented cleanly, and both B.1 blockers remain closed. However, the §2.1 `depends_on` path-fallback fix is wired *only* through `create_snapshot` (the MCP path) and never reaches the CLI `ontos activate` / `ontos map` orchestration — which is the exact surface the acceptance criteria measure.

## Findings

### [F1] CLI `ontos activate` / `ontos map` never receive the §2.1 path-fallback fix
- **Severity:** blocker
- **Evidence:** static-inspection
- **Where:** `ontos/commands/map.py:121`, `ontos/commands/activate.py:99-105`
- **Issue:** `build_graph` and `ValidationOrchestrator` both gained an optional `workspace_root`, but it was threaded only via `ontos/io/snapshot.py:78,83` (the MCP `activate` tool path) and `ontos/core/validation.py:130`. The CLI command `ontos activate` (`activate_command` → `run_activation` → `generate_context_map`) constructs `ValidationOrchestrator(docs, {...})` at `map.py:121` with **no `workspace_root`**, so `build_graph` runs in legacy mode and still emits `BROKEN_LINK` for every path-style `depends_on`. `ontos/commands/activate.py` was not touched at all, despite spec §2.1.3 explicitly naming it as the wiring point ("`ontos/commands/activate.py` already knows the workspace root; pass it down to `build_graph`"). Net effect: acceptance check §5.5.1 — "`ontos activate --json` no longer reports the 10 false-positive broken-dependency errors" — fails, because the CLI path is unchanged. (`ontos link-check` is similarly unwired at `ontos/core/link_diagnostics.py:264`, though that surface is not an explicit acceptance item.)
- **Recommendation:** Thread the project root into `generate_context_map` (it already receives `config["project_root"]`) and pass it as `ValidationOrchestrator(docs, {...}, workspace_root=Path(config["project_root"]))` at `map.py:121`; verify `ontos activate --json` against the company-os reproduction tree resolves the path-style `depends_on` entries.

### [F2] CLI activation warnings are not enriched (§2.2 contract / §2.5.2 unmet for the CLI)
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** `ontos/commands/activate.py:104-105`, `ontos/commands/activate.py:144-168`
- **Issue:** `run_activation` flattens validation issues to bare strings (`validation_warnings = [issue.message for issue in validation.warnings]`), dropping `rule_id`, `document_id`, `file_path`. `format_activation_output` prints only summary counts and enum diagnostics — it never renders per-warning context. Spec §2.2.3 explicitly requires the CLI to print `[{rule_id}] {message} ({document_id} @ {file_path})`. The enrichment was implemented only in the MCP layer (`ontos/mcp/tools.py:_validation_issues`). Acceptance §5.5.2 ("orphan / depth / log-field warnings now carry `document_id` and `file_path`") is therefore at risk for the `ontos activate --json` CLI surface — its `validation.warnings` payload is still a bare-string list.
- **Recommendation:** Emit enriched dicts (or `issue.to_dict()`) into the CLI `validation.warnings`/`errors` payload and add the `[{rule_id}] {message} (…)` rendering to `format_activation_output`, matching the MCP shape.

### [F3] Missing the §2.1.4 / §2.2.4 integration test against the reporter fixture
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** `tests/core/test_validation.py` (no `git log main..HEAD` entry)
- **Issue:** Spec §2.1.4 asks for "an integration test against a fixture mimicking the `company-os` reporter case (a doc with `depends_on:` pointing at `.llm-dev/framework/framework.md` / `docs/strategy/...`)", and §2.2.4 asks for `test_validation.py` serialization assertions. No `test_validation.py` was added or modified. `tests/core/test_graph.py` exercises `build_graph(workspace_root=…)` directly and `tests/mcp/test_activation.py` exercises the snapshot path — but nothing exercises the CLI `run_activation`/`generate_context_map` path end-to-end. That is precisely the gap that let F1 land green at 1321 passed.
- **Recommendation:** Add an integration test that runs `run_activation` (or `generate_context_map`) over a fixture with a path-style `depends_on` and asserts it resolves to an edge / `OUT_OF_SCOPE_DEPENDENCY` warning rather than `BROKEN_LINK`.

### [F4] `_resolve_depends_on_path` can short-circuit to "external" before trying the doc-relative candidate
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** `ontos/core/graph.py` — `_resolve_depends_on_path` candidate loop
- **Issue:** Candidates are ordered `[workspace_root / raw, doc_dir / raw]`, and the loop returns `(None, candidate)` (external) on the first candidate that merely `.exists()`. If the workspace-relative candidate exists on disk but is not a loaded doc, the function returns "external" without ever testing whether the declaring-doc-relative candidate (rule 3) resolves to a *loaded* doc. Spec rules 2/3 (doc match) are both meant to be exhausted before rule 4 (external). The misclassification is narrow and safe (a real edge degrades to a soft warning), but it deviates from the specified rule order.
- **Recommendation:** Make two passes — check all candidates for a loaded-doc match first, then fall back to the first existing-but-not-loaded candidate as external.

## Notes

- B.1 blockers re-verified closed in `dd68231`: claude-opus F1 (graph-edge cleanliness) — `resolved_depends_on` is now built before `graph.add_node`, so edges/`reverse_edges` record doc-ids, not raw path strings; gemini F1 (path-traversal containment) — `workspace_root_resolved` + `resolved.relative_to(...)` rejects escaping candidates after `resolve()` follows symlinks.
- Issue #115 is correct: `_attach_pre_activate_warning` routes via the schema-declared channel, `GetContextBundleResponse.warnings` is required so `setdefault` is benign, and the dedup guard prevents double-append.
- §2.4 / §2.5 / §2.6 are clean; doctor's `check_activation_health` correctly inherits the §2.1 fix because it routes through `create_snapshot` (the one path that *was* wired) — the same wiring that F1 shows the CLI activate path is missing.
- Minor: in `_iter_wikilink_id_candidates`, `inner` is always a substring of `raw_inner` (it is `raw_inner.strip()`), so the `else 0` branch of `offset = raw_inner.index(inner) if inner in raw_inner else 0` is unreachable — harmless dead code.
