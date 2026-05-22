---
id: project-ontos-github-issues-115-117-B.1-claude-opus-peer
deliverable_id: project-ontos-github-issues-115-117
phase: B.1
role: peer
family: claude-opus
status: completed
---

# B.1 Peer Review — claude-opus

## Verdict

Request changes

## Summary

The spec is unusually disciplined — every line reference I checked against the spec commit (`23a423f`) lands within ±2 lines, the three issues are cleanly decomposed, and the cross-cutting invariants are real and well chosen. But §2.1's implementation section omits the one step that fulfills its own contract (resolved path-deps never reach the graph), and three other sections under-specify shared-surface blast radii that an implementer working strictly from the spec will miss.

## Findings

### [F1] §2.1.3 resolver never wires the resolved doc-id into the graph
- **Severity:** blocker
- **Evidence:** static-inspection
- **Where:** spec §2.1.2 (rules 2/3) vs §2.1.3; `ontos/core/graph.py:79` (`graph.add_node(..., depends_on)`), `graph.py:92-99` (`add_node` builds `edges`/`reverse_edges` from the raw list)
- **Issue:** §2.1.2 contract states rules 2/3 mean "edge **resolves to that doc's id**." §2.1.3 describes `_resolve_depends_on_path` returning `(target_id, "edge")` but never says what to do with `target_id`. `build_graph` still calls `graph.add_node(doc_id, ..., depends_on)` with the *raw* `depends_on` list, and `add_node` derives `edges`/`reverse_edges` from it verbatim. An implementer following §2.1.3 literally computes `target_id` and discards it: the path string stays in the graph, `reverse_edges` never gets an entry for the real target, and `detect_orphans` (`graph.py:255`) / `calculate_depths` still see no edge. The contract's central promise is unimplemented — exactly the gap B.1 exists to catch before D-phase.
- **Recommendation:** Add an explicit step to §2.1.3: build a per-doc `resolved_depends_on` list where each `(target_id, "edge")` result substitutes `target_id` for the raw `dep_id`, and pass that list to `graph.add_node`. State that rule-4 "external" entries are dropped from the list (no synthetic node, per §2.1.2) so they never reach `edges`/`reverse_edges`.

### [F2] §2.2.3 names a non-existent model and ignores the shared-function blast radius
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** spec §2.2.3; `ontos/mcp/schemas.py:16` (`ValidationIssue`), `schemas.py:21-23,94,103,109,162`; `ontos/mcp/tools.py:613-627` (`_validation_payload` / `_validation_issues`)
- **Issue:** There is no `WarningEntry` model. The actual model is `ValidationIssue` (StrictModel), and it is shared by `ActivateResponse.warnings`, `WorkspaceOverviewResponse.warnings`, and `ValidationPayload` (consumed by `ContextMapResponse` and `ExportGraphFullResponse`). `_validation_issues` is likewise shared via `_validation_payload`. Once `_validation_issues` always emits `rule_id`/`document_id`/`file_path`, **all four** response types receive the new keys and will fail `additionalProperties: false` unless `ValidationIssue` is extended. §2.2 frames the change as `activate`-only and §2.2.4 only tests `test_activation.py`.
- **Recommendation:** Replace `WarningEntry` with `ValidationIssue` (the parenthetical hedge is not enough in an otherwise name-precise spec). Add a sentence noting the 4-response blast radius, and add regression assertions to §2.2.4 that `context_map`, `workspace_overview`, and `export_graph` payloads still validate after the enrichment.

### [F3] New lifecycle types are not reconciled with `allowed_orphan_types`
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** spec §2.3.2; `ontos/core/validation.py:152` (`allowed_orphans = set(config.get("allowed_orphan_types", ["atom", "log"]))`)
- **Issue:** §2.3 promotes `handoff`, `retro`, `review`, `report`, `tracker`, `adr`, `policy`, `spec` to first-class types but says nothing about orphan detection. The default `allowed_orphan_types` is `["atom", "log"]`. Retros, handoffs, reviews, and reports are inherently terminal leaf documents with no dependents — each will now emit an orphan warning. Issue #117 explicitly lists "anonymous orphan … warnings" as the noise to reduce, so widening the vocabulary without touching the allowlist can *increase* the very noise the deliverable targets.
- **Recommendation:** §2.3 should explicitly decide: either extend the default `allowed_orphan_types` to include the leaf-like lifecycle types, or document why they remain orphan-flagged. Add an orphan-interaction case to §2.3.4.

### [F4] §2.4 leaves the `occupied`/`_find_unsupported_spans` interaction under-specified
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** spec §2.4.3; `ontos/core/body_refs.py:387-389` (`occupied.extend(_find_unsupported_spans(...))`), `body_refs.py:708-710` (`_find_unsupported_spans` iterates `_WIKILINK_RE`), `body_refs.py:425-430` (`_overlaps_any` filter)
- **Issue:** `_find_unsupported_spans` unconditionally adds every `[[…]]` span to `occupied`, and the bare-candidate loop skips any candidate that `_overlaps_any(occupied)`. If the generic branch is simply swapped to `_iter_wikilink_id_candidates`, every new candidate sits inside an `occupied` wikilink span and is filtered out — yielding zero matches and failing §2.4.4's "explicit `[[my-doc-id]]` → one match" test. §2.4.3 says "wikilink spans are no longer treated as unsupported in generic mode" but `_find_unsupported_spans` takes no mode argument, so the spec states the *what* without the *how*.
- **Recommendation:** Specify the mechanism: make `_find_unsupported_spans` mode-aware (or build `occupied` conditionally) so wikilink spans are excluded from `occupied` in generic mode, while reference-style / HTML / autolink spans remain.

### [F5] §1.3 `else: emit nothing` silently drops the pre-activate reminder from `export_graph`
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** spec §1.3; `ontos/mcp/schemas.py:332-341` (`READ_WARNING_TOOL_NAMES`)
- **Issue:** Of the read tools, `export_graph` is the only one in neither `READ_WARNING_TOOL_NAMES` nor the proposed `WARNINGS_LIST_TOOL_NAMES`. Today it receives the `_ontos_warning` injection (post-validation); under §1.3's `else: emit nothing` it receives no pre-activate reminder at all. This is a behavior change the spec does not acknowledge.
- **Recommendation:** Either route `export_graph` into one of the sets, or add an explicit sentence to §1.3 stating the drop is intentional (defensible, since `output_schema_for` already returns `None` for `export_graph`).

### [F6] `COMPLETED` vs `COMPLETE` are distinct values, not aliases
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** spec §2.3.2 (`COMPLETED = "completed"` "sibling alias of `COMPLETE`"); `ontos/core/types.py:50` (`COMPLETE = "complete"`)
- **Issue:** A Python `Enum` member with a different string value is a separate member, not an alias. Any logic branching on `DocumentStatus.COMPLETE` (staleness, archival, reporting) will silently miss `completed` docs.
- **Recommendation:** Either make `COMPLETED` a true alias (`_missing_` value mapping), or drop the word "alias" and add a §2.3.3 step to audit/enumerate `DocumentStatus.COMPLETE` consumers.

### [F7] §1.5 "Acceptance check" gate cannot fail on a broken #115
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** spec §1.5; `ontos/mcp/schemas.py:258` (`warnings: List[str]` already declared)
- **Issue:** `G-cardinality-1` only asserts `'warnings' in GetContextBundleResponse.model_fields` — already true at the spec commit. It passes whether or not #115 is fixed, so it is not an acceptance signal. The real verification is the §1.4 `test_bundler.py` case.
- **Recommendation:** Relabel §1.5 as a structural precondition, or point the acceptance gate at the actual fix behavior.

## Notes

- Line-reference accuracy is high — `server.py`, `schemas.py`, `graph.py`, `types.py`, `frontmatter.py`, `tools.py`, `body_refs.py`, and `doctor.py` all verified against commit `23a423f` within ±2 lines.
- Minor inconsistency: §0 invokes `verify-lifecycle.sh --mode strict-p3 …` while §5.2 invokes `scripts/llm-dev verify-lifecycle --mode strict-p3 …`. Pick one form.
- §2.3.3 / §0 nuance: `normalize_type`/`normalize_status` currently pass the *normalized* `type_str` (stripped + lowercased) to `on_error`, not the raw `value`. To honor the §0 "original raw value is surfaced" invariant, §2.3.3 should explicitly say to pass the raw `value`.
- §2.3.3 and §3.2 route v4.5-era content into `docs/reference/Migration_v3_to_v4.md` (a v3→v4 guide). Consider whether a v4.x migration/changelog home is more appropriate, or rename the touchpoint.
