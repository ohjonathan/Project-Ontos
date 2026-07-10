You are the Gemini adversarial implementation reviewer for `project-ontos-audit-doctor-rce`, Phase D.2. Evidence cap: static inspection. Claude is the substantive implementation author family and cannot count as an independent reviewer.

Do not edit files, execute code, run tests, or claim direct-run evidence. Inspect only the immutable seven-file delta at commit `03c36e6ac999d2c411c13252baa2e8fcff60e6ed` plus the revised spec and audit addendum. Do not substitute live working-tree product files. If immutable object access is unavailable, return `Request changes` with that blocker.

Attack the actual code paths: executable/path equivalence, symlink or PATH replacement, prefix construction, exact list comparison, `build_ontos_stdio_entry` behavior for both modes, duplicated/reordered/hidden tokens, workspace canonicalization, user-scope trust assumptions, default propagation across `inspect_cursor_ontos_config`, `check_cursor_mcp`, `_inspect_cursor_scope`, and `_run_doctor_command`, plus warning details. Inspect whether each of the five tests would fail under the prior vulnerable behaviors and whether untested variants remain. Treat test results from other families as external claims, not your evidence.

Record that Codex plus Gemini provide only two countable non-author families and GPT-auto is wrapper-blocked. That is a lifecycle blocker even if code is sound.

Emit exactly one Markdown artifact to stdout, no preamble or code fence. The first body line after frontmatter must be the H1 below. Use this exact frontmatter:

---
id: project-ontos-audit-doctor-rce-D.2-gemini-adversarial
deliverable_id: project-ontos-audit-doctor-rce
phase: D.2
role: adversarial
family: gemini
implementation_commit: 03c36e6ac999d2c411c13252baa2e8fcff60e6ed
evidence_labels_used: [static-inspection]
status: completed
---

# Adversarial Implementation Review - project-ontos-audit-doctor-rce / D.2 / gemini

## Commit Binding

## Attack Matrix

| Attack | Code path | Static result |
|--------|-----------|---------------|

## Issues Found

### Blocking

| ID | Description | Location | Evidence | Suggested action |
|----|-------------|----------|----------|------------------|

### Should-fix

| ID | Description | Location | Evidence | Suggested action |
|----|-------------|----------|----------|------------------|

### Minor

| ID | Description | Location | Evidence | Suggested action |
|----|-------------|----------|----------|------------------|

## Evidence-Cap And Certification Notes

## Verdict
Approve

Replace `Approve` with `Request changes` or `Reject` if warranted. The first non-blank line under `## Verdict` must be exactly `Approve`, `Request changes`, `Reject`, or `Concur`.

## Notes
