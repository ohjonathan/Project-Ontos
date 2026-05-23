---
id: project-ontos-github-issues-115-117-B.3-verdict
type: review
deliverable_id: project-ontos-github-issues-115-117
phase: B.3
role: meta-consolidator
family: claude-opus
status: complete
---

# B.3 Meta-Consolidation — claude-opus

## Verdict

Concur

## Summary

B.1's three-lens board (claude-opus peer / claude-sonnet alignment / gemini adversarial) reviewed the Phase A spec. Two blocker-grade findings landed: claude-opus F1 (resolver never wires the resolved doc-id into the graph — edges contain both raw path and doc-id) and gemini F1 (path traversal vulnerability through `Path.resolve` follow-symlinks behavior). Both were addressed in commit `dd68231` with regression tests; 1321/1321 tests pass.

Six should-fix findings (claude-opus F2-F5, claude-sonnet F1-F2, gemini F2-F3) and three nits are recorded below as preserved blockers for D.2 to re-verify against the landed implementation. None block advancing to Phase C reconciliation: Phase C is already complete and the blocker fixes have landed.

## Blocker closure summary

| Lens | Finding | Disposition | Commit |
|---|---|---|---|
| claude-opus | F1 (§2.1.3 resolver never wires resolved doc-id into graph) | **Closed** — `build_graph` now pre-resolves each dep_id and passes a doc-id-only list to `add_node`. Test enforces no raw-path bleed. | `dd68231` |
| gemini | F1 (path traversal via `Path.resolve` symlink-follow) | **Closed** — `_resolve_depends_on_path` now rejects candidates whose `.resolve()` escapes `workspace_root.resolve()`. Test exercises a `../secrets/vault.md` traversal. | `dd68231` |

## Preserved blockers

(All retained for D.2 — the D.2 board re-applies the lens against the landed implementation. None of these is blocker-grade in B.3 because Phase C is already in.)

- **claude-opus F2** — `_normalize_warnings` blast radius: `workspace_overview` consumed the old `{severity, message}` shape; warning-enrichment change must be checked there too.
- **claude-opus F3** — New lifecycle types not reconciled with `allowed_orphan_types`: a `tracker` doc with no incoming deps will fire an orphan warning.
- **claude-opus F4** — `body_refs._find_unsupported_spans` semantic shift: callers passing `known_ids` plus the default `include_generic_bare_id_token=True` may now double-emit on wikilinks.
- **claude-opus F5** — `export_graph` and other non-`READ_WARNING_TOOL_NAMES` tools silently drop the pre-activate reminder; verify-lifecycle smoke should confirm this is intended.
- **claude-sonnet F1** — Snapshot warning classifier unrecognized-prefix fallback: spec didn't specify behavior; implementation falls back to generic `rule_id: snapshot`.
- **claude-sonnet F2** — `validation_excluded` architectural placement: implementation uses a per-loader-call check, no sentinel on `DocumentData`. Clean but undocumented in spec.
- **gemini F2** — `rule_id` derivation from message-string prefixes is brittle: a localized or reworded message would fall back to generic.
- **gemini F3** — `ontos doctor` running activation may have side effects (cache priming) under repeated runs.

## Nits

- claude-opus F6 (`COMPLETED` vs `COMPLETE` are distinct values, not "aliases").
- claude-opus F7 (G-cardinality-1 cannot fail on a broken #115 — gate verifies the model field exists but #115's bug was a runtime injection).
- claude-sonnet F3 (opt-in flag for `_iter_generic_id_candidates` is underspecified).

## Phase advance

B.3 endorses advance to **Phase D.1 (peer pre-review of implementation)** → **D.2 (review board on implementation)** → D.3/D.4/D.5/D.6/E. Implementation is committed (12 commits ahead of main); B.1 blockers are closed in commit `dd68231`. The preserved should-fix items above re-enter D.2's adversarial / peer / alignment scope.

## Sources

- `docs/reviews/project-ontos-github-issues-115-117/B.1-claude-opus-peer.md`
- `docs/reviews/project-ontos-github-issues-115-117/B.1-claude-sonnet-alignment.md`
- `docs/reviews/project-ontos-github-issues-115-117/B.1-gemini-adversarial.md`
- Blocker-fix commit: `dd68231`
