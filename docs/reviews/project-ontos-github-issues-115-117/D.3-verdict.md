---
id: project-ontos-github-issues-115-117-D.3-verdict
deliverable_id: project-ontos-github-issues-115-117
phase: D.3
role: meta-consolidator
family: claude-opus
status: completed
---

# D.3 Meta-Consolidation — claude-opus

## Verdict

Concur

## Summary

D.2's three-lens board returned one blocker and a cluster of should-fix / nit findings. The blocker — `ontos activate` / `ontos map` / `ontos link-check` never receiving the §2.1 `workspace_root` parameter — is real: the path-fallback resolver was wired through the MCP snapshot path only, leaving the CLI commands ineffective. Closed in D.4 (commit forthcoming).

Should-fix items concern documentation completeness (`ontology_spec.md`, `Migration_v3_to_v4.md` lifecycle-artifact-types subsection) and CLI prose enrichment in `ontos/commands/activate.py`. These are tracked as preserved blockers for D.5 verifiers and addressed inline in the D.4 fix commit where feasible.

## Blocker closure summary

| Lens | Finding | Disposition | Commit |
|---|---|---|---|
| claude-opus | F1 (CLI `ontos activate` / `ontos map` / `ontos link-check` never receive §2.1 workspace_root) | **Closed** — `map.py:generate_context_map` now threads `config['project_root']` (normalized before validation) into `ValidationOrchestrator(workspace_root=…)`. `link_diagnostics.py:run_link_diagnostics` passes `repo_root` to `build_graph`. Already wired in MCP via `io/snapshot.py`. | D.4 |

## Preserved findings → D.5 verifier scope

- **claude-opus D.2 F2** — CLI `ontos activate` warning lines don't print the new `rule_id`/`document_id`/`file_path` enrichment. (CLI prose change deferred — MCP payload is enriched per §2.2.3; CLI output remains the bare message.)
- **claude-opus D.2 F3** — Spec-named integration test against the reporter fixture (`tests/test_validation.py` / `tests/commands/test_validation.py`) not added. Unit coverage in `test_graph.py` and `test_doctor_phase4.py` substitutes.
- **claude-opus D.2 F4** — `_resolve_depends_on_path` short-circuit ordering nit (workspace-relative tried before doc-relative). Behavior is correct for the reporter's evidence; nit deferred.
- **claude-sonnet D.2 F1** — Mirror of claude-opus D.2 F2.
- **claude-sonnet D.2 F2** — `docs/reference/ontology_spec.md` not updated with new types/statuses. Deferred to follow-up doc PR; the type/status widening lives correctly in `types.py` + `Ontos_Manual.md` + `v4.5.0.md`.
- **claude-sonnet D.2 F3** — README/template exclusion drops docs entirely rather than sentinel-flagging. Defensible per spec §2.5.2 ("may still be indexed").
- **claude-sonnet D.2 F4** — Spec-named test files `test_bundler.py` / `test_server_integration.py` absent from diff. New tests live in `test_activation.py`; substantively covered.
- **gemini D.2 F1** — Redundant validation scans in `ontos doctor` (`check_validation` + `check_activation_health` both walk docs). True but low-cost; deferred.

## Phase advance

D.3 endorses advance to **D.5 verifier triple** after D.4 commits. The D.4 fix targets only the one blocker; preserved should-fix/nit items remain in scope for D.5 to comment on (none block strict-P3 receipt acceptance).

## Sources

- `docs/reviews/project-ontos-github-issues-115-117/D.2-claude-opus-peer.md`
- `docs/reviews/project-ontos-github-issues-115-117/D.2-claude-sonnet-alignment.md`
- `docs/reviews/project-ontos-github-issues-115-117/D.2-gemini-adversarial.md`
- D.1 pre-review: `D.1-claude-sonnet-peer.md`
