---
id: log_20260124_fix-blocking-scaffold-issues-from-adversarial-revi
type: log
status: active
event_type: fix
source: Antigravity (Gemini 2.5 Pro)
branch: feature/init-improvements-v3.1.1
created: 2026-01-24
---

# Fix blocking scaffold issues from adversarial review

## Summary

Implemented critical fixes for the scaffold feature in `ontos init` to address issues X-H1 and X-H2 from the adversarial review. These fixes ensure that the scaffold prompt appears correctly when untagged files exist anywhere in the repository and that file count warnings are accurate based on the selected scope.

## Root Cause

- **X-H1**: `_prompt_scaffold()` was only checking `docs_dir` for untagged files, causing the prompt to be skipped if `docs/` was empty even if other untagged files existed in the repo.
- **X-H2**: The "Large file count" warning was triggered based on the `docs_dir` scan before the user selected a scope, potentially leading to inaccurate warnings.

## Fix Applied

- **Repo-wide Check**: Modified `_prompt_scaffold()` to use `project_root` for initial untagged file detection.
- **Scope-aware Warning**: Relocated the file count warning to after scope selection.
- **API Enhancement**: Updated `find_untagged_files()` in `scaffold.py` to support an explicit `root` parameter for better reliability.

## Testing

- Added `test_prompt_shows_when_docs_empty_but_repo_has_files` to verify repo-wide detection.
- Added `test_warning_count_matches_selected_scope` to verify accurate threshold warnings.
- Verified all 25 scaffold-related tests pass.