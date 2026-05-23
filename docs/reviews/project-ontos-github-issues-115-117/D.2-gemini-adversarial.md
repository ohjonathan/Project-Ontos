---
id: project-ontos-github-issues-115-117-D.2-gemini-adversarial
type: review
deliverable_id: project-ontos-github-issues-115-117
phase: D.2
role: adversarial
family: gemini
status: complete
---

# D.2 Adversarial Review — gemini

## Verdict

Request changes

## Summary

The implementation correctly closes the specified issues and addresses the B.1 blockers from the previous phase, with robust handling of path-traversal and schema validation. However, a performance issue was identified in `ontos doctor` where redundant validation scans occur on the workspace, which should be addressed.

## Findings

### [F1] Redundant validation scans in `ontos doctor`
- **Severity:** should-fix
- **Evidence:** static-inspection
- **Where:** `ontos/commands/doctor.py`
- **Issue:** The `_run_doctor_command` function executes a series of checks, including the pre-existing `check_validation` and the newly added `check_activation_health`. Both of these functions internally call `ontos.io.snapshot.create_snapshot`, which performs a full document load and validation scan of the workspace. This results in the same expensive operation being performed twice, leading to unnecessary I/O and CPU consumption that will significantly slow down `ontos doctor` on large workspaces.
- **Recommendation:** Refactor `_run_doctor_command` to perform the snapshot and validation operation only once. The result of this single scan should be cached and passed to the individual check functions (`check_validation`, `check_activation_health`), which can then inspect the result and format their `CheckResult` accordingly without triggering new scans.

## Notes

My review confirmed that the two blockers identified in phase B.1 have been successfully resolved in commit `dd68231`:
1.  **Path-traversal containment (gemini B.1-F1):** The `depends_on` path resolver in `ontos/core/graph.py` now correctly constrains resolved paths to the workspace root, preventing access to arbitrary filesystem locations.
2.  **Graph-edge cleanliness (claude-opus B.1-F1):** Out-of-scope file dependencies are correctly reported as warnings without creating spurious edges in the dependency graph.

The implementation of all other requirements appears robust against the edge cases I examined.
