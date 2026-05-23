---
id: project-ontos-issue-119-B.1-codex-peer
deliverable_id: project-ontos-issue-119-cli-activate-json-warning-metadata
phase: B.1
role: peer
family: codex
status: completed
---

# B.1 Peer Review — codex

## Verdict

Approve

## Summary

The spec is focused, implementable, and chooses the right shared-serialization design by moving the MCP/CLI record shape onto `ValidationError.to_dict()`. I found no blocking design issue, but the test plan should be tightened so Phase C implementers do not create brittle or impossible fixtures.

## Findings

### [F1] Tighten Required Test Fixtures To Match Validator Behavior
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** `docs/specs/project-ontos-issue-119-cli-activate-json-warning-metadata-spec.md:195-200`
- **Issue:** Several required test cases are directionally right but under-specified or misleading against the current activation pipeline. The orphan case does not state that the fixture must use a non-allowed orphan type or override `allowed_orphan_types`; default config allows `atom` orphans. The schema case suggests invalid `type:` / `status:`, but those are loader diagnostics, not `validation.warnings`; the reliable validation-schema fixture is a `log` missing required fields. The error-parity case suggests a broken `depends_on`, but `generate_context_map()` currently downgrades broken links to warning severity; a cycle or synthetic/monkeypatched `ValidationError(severity="error")` is the reliable error fixture.
- **Recommendation:** Revise the test plan to name concrete fixtures: use a non-allowed document type for orphan, use missing log fields for `rule_id == "schema"`, and use a dependency cycle or controlled synthetic validation result for the error-path assertion.

### [F2] Release-Note Requirement Conflicts With “Exactly Three Files”
- **Severity:** nit
- **Evidence:** static-inspection
- **Where:** `docs/specs/project-ontos-issue-119-cli-activate-json-warning-metadata-spec.md:117-121` and `docs/specs/project-ontos-issue-119-cli-activate-json-warning-metadata-spec.md:177-185`
- **Issue:** The spec correctly requires documenting the intentional CLI JSON shape break in release notes, but later says the implementation surface is “exactly three files” plus tests. Since `docs/releases/` exists in this repo, that wording can be read as excluding the release-note edit the spec already requires.
- **Recommendation:** Change the “exactly three files” statement to “runtime implementation surface” and explicitly allow the release-note/documentation touchpoint.

## Notes

No blocker found. The core contract, shared serializer placement, MCP preservation invariant, and verification gates are coherent.
