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

The spec is comprehensive and addresses the root causes of the reported issues with sound logic. However, a potential path traversal vulnerability exists in the proposed `depends_on` resolution logic, which could leak information about files outside the workspace. A minor clarification on case-insensitivity for file exclusion rules is also recommended.

## Findings

### [F1] Path traversal risk in `depends_on` path resolution
- **Severity:** blocker
- **Evidence:** static-inspection
- **Where:** Spec section 2.1.2 and 2.1.3
- **Issue:** The contract for resolving `depends_on` entries as paths does not mandate that the resolved file path must exist within the workspace root. An entry like `../.env` or `../../../../etc/passwd` could resolve to a file outside the project directory. While the spec proposes not loading the file, Rule #4 would still confirm its existence via an "external resolved dependency" warning, creating an information leak vulnerability about the host file system.
- **Recommendation:** The implementation (e.g., in `_resolve_depends_on_path`) must verify that the fully resolved candidate path is a subpath of the workspace root. If `candidate.resolve()` is not within `workspace_root.resolve()`, the dependency should be treated as `broken` (Rule #5), not `external` (Rule #4).

### [F2] Case-insensitivity for README/template exclusion rule
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** Spec section 2.5
- **Issue:** The contract specifies that files with a stem of `README` should be excluded from validation. On case-sensitive filesystems, this would exclude `README.md` but not `readme.md` or `Readme.txt`. This behavior could be surprising and lead to unexpected validation errors.
- **Recommendation:** Explicitly state that the `README` stem check must be case-insensitive. The implementation in the proposed `_is_validation_excluded` helper should normalize the stem to lowercase before comparison (e.g., `path.stem.lower() == 'readme'`).

## Notes

The planned changes for issues #115, #116, and the other sub-items of #117 appear robust and well-considered from an adversarial standpoint, with clear back-compatibility paths and conservative fallbacks. The findings above are the only points of concern identified.
