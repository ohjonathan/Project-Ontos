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

The landed implementation is high-quality and the core contracts of #115/#116/#117 are met — schema-safe pre-activate warning, `depends_on` path-fallback resolution, vocabulary widening, `bare_id_token` tightening, and doctor exit-code alignment all check out, and both B.1 blockers remain closed. However, the §2.2 warning enrichment was landed only on the MCP surface; the spec-named CLI touchpoint `ontos/commands/activate.py` is entirely untouched, and the §2.6.3 structured `activation` block was not implemented.

## Findings

### [F1] §2.2 warning enrichment missing on the CLI `ontos activate` surface
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** `ontos/commands/activate.py:104-105`, `ontos/commands/activate.py:144-168`
- **Issue:** §2.2.2 contract states "Every activation warning that originates from a known document carries `rule_id`, `document_id`, and `file_path`", and §2.2.3 explicitly names `ontos/commands/activate.py` as a touchpoint. `activate.py` is unchanged on this branch (`git log main..HEAD -- activate.py` is empty). The CLI command flattens warnings via `validation_warnings = [issue.message for issue in validation.warnings]`, discarding the `ValidationError.doc_id` / `.filepath` fields. The orphan/depth/log-field messages do not embed doc context (`validation.py:160` `"Document has no incoming dependencies"`, `:174` `"Dependency depth …"`, `:195` `"Log missing fields: …"`), so `ontos activate --json` emits these as bare strings with no way to identify which document is affected — the exact "low-signal" complaint of #117, unaddressed for the CLI path. The MCP `activate` tool *is* correctly enriched via `tools.py:_validation_issues`. Note §5 D.6 verification step 5.2 exercises `ontos activate --json` specifically.
- **Recommendation:** Enrich the `activate.py` payload to carry `rule_id`/`document_id`/`file_path` per warning (reuse the `_validation_issues` shape from `tools.py`) and update `format_activation_output` to print `[{rule_id}] {message} ({document_id} @ {file_path})` per §2.2.3.

### [F2] doctor `activation` JSON block not structured
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** `ontos/commands/doctor.py:349-398`
- **Issue:** §2.6.3 specifies the doctor JSON output gain an `activation: {status, error_count, warning_count}` block. The implementation instead returns a generic `CheckResult` named `activation_health` with the counts embedded in a prose `message` (`"{n} activation error(s), {m} warning(s) …"`) and `details` string — no discrete machine-readable `error_count`/`warning_count` fields. This is at odds with the deliverable's central theme (making warnings parseable). The exit-code contract §2.6.2 *is* satisfied (`status="failed"` increments `result.failed`, driving non-zero exit at `doctor.py:863`).
- **Recommendation:** Emit a structured `activation` block (or add `error_count`/`warning_count` integer fields to the check result) so consumers don't have to regex the message string.

### [F3] Rule-4 external-dependency check uses `exists()` instead of `is_file()`
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** `ontos/core/graph.py` — `_resolve_depends_on_path` (`if candidate.exists(): return None, candidate`)
- **Issue:** §2.1.2 rule 4 says the edge is an external dependency when the candidate "exists on disk as a real file." `candidate.exists()` is also true for directories, so a `depends_on` entry pointing at a directory would be reported as `OUT_OF_SCOPE_DEPENDENCY` with the message "…exists at '{path}' but is not a loaded document" rather than falling through to broken-link. Low impact (directory `depends_on` entries are rare) but the downgrade-to-warning is more lenient than spec.
- **Recommendation:** Use `candidate.is_file()` for the rule-4 branch.

## Notes

**B.1 blockers re-verified closed:**
- claude-opus B.1 F1 (graph-edge cleanliness): confirmed. `build_graph` now resolves every `depends_on` entry into `resolved_depends_on` (doc-ids only) *before* calling `graph.add_node(doc_id, doc_type, …, resolved_depends_on)`; raw path strings and broken/external entries never enter the edge list.
- gemini B.1 F1 (path-traversal containment): confirmed. `_resolve_depends_on_path` resolves each candidate with `Path.resolve` (symlink-following) and rejects any whose resolved path is not `relative_to(workspace_root_resolved)`, so `../../etc/passwd`-style entries cannot leak filesystem state through the warnings channel.

**Verified good:** #115 `_attach_pre_activate_warning` routes correctly per channel, is idempotent, and the warning string is byte-exact; §2.4 wires `include_generic_bare_id_token=False` into `link_diagnostics` and `_find_unsupported_spans(include_wikilinks=False)` correctly converts wikilink spans into the opt-in candidate source; §2.3 enum members and `frontmatter_repair` alias remap are consistent; the lowercase `_SNAPSHOT_RULE_PREFIXES` entries (`"invalid frontmatter field 'type'"`) correctly match `report_enum_error`'s emitted text at `files.py:412` (not a bug). Suite is green (1321 passed, 2 skipped).

**Minor observations (not findings):** §2.5 README/template exclusion is implemented by fully dropping the file (`continue` in `load_documents`) rather than the §2.5.3-prescribed "load with `validation_excluded=True` sentinel" — Contract §2.5.1 permits non-indexing ("may still be indexed"), so this is acceptable, but a README that is a legitimate `depends_on` path target now resolves as `OUT_OF_SCOPE_DEPENDENCY` rather than a clean edge. Test coverage for §2.3.4 (original-value-in-warning-message) and §2.5.4 (README-exclusion) did not land in the spec-named `tests/core/test_validation.py` / `tests/io/test_files.py`; the touched suites (`test_frontmatter_repair.py` +152, `test_agentic_activation_resilience.py` +29) plausibly absorb it — worth a D.5 verifier confirmation.
