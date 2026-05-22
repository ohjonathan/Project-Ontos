---
id: project-ontos-github-issues-115-117-B.1-gemini-adversarial
deliverable_id: project-ontos-github-issues-115-117
phase: B.1
role: adversarial
family: gemini
status: completed
---

# B.1 Adversarial Review — gemini

## Verdict

Request changes

## Summary

The spec is comprehensive and addresses the core issues effectively, particularly in reducing false positives from the link-checker and improving warning context. However, one blocking security vulnerability and two potential maintenance/state issues require remediation before implementation. The proposed path-based dependency resolution introduces a path traversal risk that must be mitigated.

## Findings

### [F1] Path traversal vulnerability in `depends_on` resolution
- **Severity:** blocker
- **Evidence:** static-inspection
- **Where:** Spec §2.1.2, §2.1.3
- **Issue:** The contract for `depends_on` resolution proposes treating dependency IDs as workspace-relative or document-relative file paths. It does not specify that these paths must be validated to exist *within* the workspace boundary. A malicious `depends_on: "../../../../etc/passwd"` entry could cause the system to read arbitrary files from the filesystem, as `workspace_root / dep_id` would resolve outside the project.
- **Recommendation:** The implementation contract must be amended to require path sanitization. After resolving a path candidate (e.g., via `(workspace_root / dep_id).resolve()`), the implementation MUST verify that the resolved absolute path is a child of the workspace root's own resolved absolute path. Any path resolving outside the workspace must be treated as a broken link, not an external dependency.

### [F2] Brittle `rule_id` generation from string prefixes
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** Spec §2.2.3
- **Issue:** The spec proposes deriving a structured `rule_id` for bare-string warnings by matching known string prefixes (e.g., `"Log missing fields:"` → `rule_id="schema.log_missing_fields"`). This is brittle; any future change to the human-readable warning message will break the `rule_id` mapping. This creates a tight, non-obvious coupling between distant parts of the codebase.
- **Recommendation:** Modify the implementation contract. Instead of reverse-engineering the `rule_id` from a string, the code locations that generate these warnings should be modified to emit a structured object containing both the message and the appropriate `rule_id` from the outset.

### [F3] Unspecified side effects of `ontos doctor` running activation
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** Spec §2.6
- **Issue:** The spec proposes that `ontos doctor` run the full activation pipeline to check for errors. This could significantly slow down a command intended as a quick health check. More critically, the spec does not state whether this activation run is isolated. If it modifies any persistent state (e.g., caches, logs), it could produce unintended side effects that influence subsequent commands like `ontos activate`.
- **Recommendation:** The implementation contract in §2.6.3 should explicitly state that the activation pipeline invoked by `ontos doctor` must be run in a "dry-run" or "read-only" mode that does not persist any state changes to the filesystem or any long-lived cache. The performance degradation should be acknowledged as an acceptable trade-off for a more accurate report.
