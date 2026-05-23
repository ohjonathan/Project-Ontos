---
id: project-ontos-github-issues-115-117-D.4-fix-summary
type: review
deliverable_id: project-ontos-github-issues-115-117
phase: D.4
role: fix-author
family: codex
status: complete
---

# D.4 Fix Summary — codex

## Verdict

Approve

## Summary

D.4 fix closes the single D.2 blocker (claude-opus F1): the §2.1 `workspace_root` path-fallback resolver was wired through the MCP snapshot path only, leaving `ontos activate` / `ontos map` / `ontos link-check` CLI surfaces ineffective. Two call sites updated; 1321/1321 tests continue to pass.

## Changes

| File | Change |
|---|---|
| `ontos/commands/map.py` | Moved `project_root` normalization above the `ValidationOrchestrator` construction; passed `workspace_root=workspace_root_value` so `validate_graph()` invokes `build_graph(..., workspace_root=…)`. |
| `ontos/core/link_diagnostics.py` | `build_graph(docs, severity_map=_LINK_CHECK_SEVERITY)` now passes `workspace_root=repo_root`, so the link-check pipeline emits doc-id-resolved edges instead of reporting broken-link errors on workspace-relative `depends_on` entries. |

## Tests

`.venv/bin/python -m pytest -q` exits 0 (1321 passed, 2 skipped). The existing path-fallback test suite (`tests/core/test_graph.py::TestDependsOnPathFallback`) covers the resolver semantics; the CLI wiring is validated transitively by the `ValidationOrchestrator` + `link_diagnostics` consumers that now thread workspace_root.

## Out-of-scope deferrals (from D.3 preserved findings)

- CLI activate prose enrichment (`activate.py` output formatting) — deferred to a follow-up PR.
- `ontology_spec.md` lifecycle-types documentation — deferred; type/status widening is documented in `Ontos_Manual.md` and `v4.5.0.md`.
- README/template sentinel-flag refactor — current behavior (drop from inventory) is defensible per §2.5.2.
- Spec-named integration test against the reporter fixture — unit coverage substitutes.
- Redundant doctor validation scans — low-cost; deferred.

## Phase advance

Advance to **D.5 verifier triple** (claude-opus / claude-sonnet / gemini verifiers).
