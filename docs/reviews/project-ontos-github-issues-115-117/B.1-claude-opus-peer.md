---
id: project-ontos-github-issues-115-117-B.1-claude-opus-peer
type: review
deliverable_id: project-ontos-github-issues-115-117
phase: B.1
role: peer
family: claude-opus
status: complete
---

# B.1 Peer Review — claude-opus

## Verdict

Approve

## Summary

The spec is well-structured, evidence-grounded, and decomposes three issues into a coherent integrated track with a thorough per-section test strategy; it is implementable as written. Findings below are spec-text precision and design-clarity gaps (should-fix / nit) that the implementers had to resolve by guessing — none are design-fatal.

## Findings

### [F1] `COMPLETED` "alias" is asserted but never made to behave as an alias
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** Spec §2.3.2 / §2.3.3
- **Issue:** §2.3.2 introduces `COMPLETED = "completed"` and calls it a "sibling alias of `COMPLETE`," but §2.3.3 only says "add the new enum members." A distinct enum member with value `"completed"` is **not** an alias — Python value-aliasing (`COMPLETED = "complete"`) would make the member an alias but would also make the literal frontmatter string `"completed"` unmappable. To both *accept* `status: completed` and *treat it equivalently to* `complete`, an explicit canonicalization mapping in `normalize_status()` is required, and every status-equality consumer (`status == DocumentStatus.COMPLETE`, list/query filters, staleness, context-map grouping) must use a status-group set. The spec specifies none of this. Confirmed latent in the shipped code: no `completed`→`complete` canonicalization exists anywhere, so the two values will silently diverge.
- **Recommendation:** Either (a) drop the "alias" framing and document `completed` and `complete` as genuinely distinct statuses, or (b) keep the alias intent and add to §2.3.3 an explicit canonicalization step plus an audit of status-equality call sites, with a test that a `status: completed` doc is treated identically to `status: complete`.

### [F2] §2.2 Contract and Implementation disagree on field presence
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** Spec §2.2.2 vs §2.2.3
- **Issue:** §2.2.2 (Contract) says `document_id`/`file_path` are carried "when the warning originates from a known document" — conditional presence. §2.2.3 (Implementation) emits `"document_id": issue.doc_id, # always present (may be empty string)` — unconditional, empty-string-valued. These are mutually exclusive payload shapes (missing key vs `""` key), and §2.2.3 simultaneously says "keep them optional," which contradicts its own "always present" snippet. The implementer is forced to guess (the shipped code chose conditional / omit-empty).
- **Recommendation:** Pick one shape. If conditional (recommended — keeps the payload compact and matches "optional"), correct the §2.2.3 snippet to omit empty values rather than emit `""`.

### [F3] `_resolve_depends_on_path` return-tuple labels resolution kind as "severity"
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** Spec §2.1.3
- **Issue:** The helper is specified to return `(resolved_doc_id, severity)` with the second element taking values `"edge"`, `"external"`, `"broken"`. Those are resolution *outcomes*, not severities — the §2.1.2 contract separately maps outcomes to `warning`/`error` severity. Overloading the word "severity" conflates two concepts and makes the helper contract ambiguous (the actual implementation used a cleaner `(Optional[str], Optional[Path])` shape, evidence the spec contract was loose).
- **Recommendation:** Rename the second element to `outcome`/`kind` in §2.1.3, or specify the concrete return shape unambiguously.

### [F4] `IN_LIFECYCLE` status introduced with no semantic definition
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** Spec §2.3.2
- **Issue:** `IN_LIFECYCLE = "in-lifecycle"` is added alongside `proposed`/`ready`/`revised` (which are self-evident) but is never defined — when does a doc carry this status, and how does it differ from existing `in_progress`/`active`? §2.3.3 mandates extending the ontology/manual status tables, but without a definition that documentation update will be hollow.
- **Recommendation:** Add a one-line semantic definition for `in-lifecycle` (or drop it if it is redundant with `in_progress`).

## Notes

Scrutiny performed: cross-checked every §x.1 "current behavior" claim against the live tree (`server.py:_invoke_read_tool`, `schemas.py` `READ_WARNING_TOOL_NAMES`/`GetContextBundleResponse`, `graph.py:build_graph`, `types.py` enums, `tools.py:_validation_issues`, `body_refs.py:_scan_normal_text_segment`). The §1 design (append to the already-declared `warnings` list rather than inject `_ontos_warning`) is correct and schema-safe — the post-`validate_success_payload` mutation appends a string to a `List[str]` field and stays inside `additionalProperties: false`. The per-section test strategy is genuinely thorough (regression + positive + negative cases each). Path-containment hardening of the §2.1 filesystem resolver is left to the Adversarial lens and deliberately not raised here. The fact that the deliverable's implementation exists and cleared D.5 corroborates that the spec was implementable; F1/F2 are precisely the spots where implementers had to silently diverge from the spec text.
