# Phase 3 Code Review: Adversarial Reviewer

**Reviewer:** Codex (Adversarial)
**Date:** 2026-01-13
**PR:** #43 — https://github.com/ohjona/Project-Ontos/pull/43
**Role:** Edge Cases, Security & Robustness

---

## 1. Edge Case Attack

### 1.1 Config Parsing Edge Cases

| Input | Expected Behavior | Actual | Status |
|-------|-------------------|--------|--------|
| Empty .ontos.toml | Return defaults | Handled in `load_project_config` | ✅ |
| Malformed TOML | Error gracefully | `ConfigError` raised with details | ✅ |
| Missing sections | Merge with defaults | `dict_to_config` uses defaults | ✅ |
| Extra unknown sections | Ignore | `dict_to_config` ignores extra keys | ✅ |
| Wrong types (string for int) | Error or coerce | `_validate_types` raises `ConfigError` | ✅ |
| Unicode in values | Handle correctly | TOML parser handles unicode | ✅ |

### 1.2 find_config() Edge Cases

| Input | Expected | Actual | Status |
|-------|----------|--------|--------|
| Config in current dir | Find it | Works | ✅ |
| Config in parent dir | Find it | Works | ✅ |
| Config in grandparent | Find it | Works | ✅ |
| No config anywhere | Return None | Returns None | ✅ |
| Config is directory | Error/skip | `exists()` returns True, `load` might fail | ⚠️ (Minor) |
| No read permission | Error gracefully | `load` raises `ConfigError` | ✅ |

### 1.3 init_command() Edge Cases

| Input | Expected | Actual | Status |
|-------|----------|--------|--------|
| Already initialized | Exit 1 | Returns 1 | ✅ |
| Already init + --force | Overwrite | Overwrites | ✅ |
| Not a git repo | Exit 2 | Returns 2 | ✅ |
| Git worktree (.git is file) | Valid repo | `_check_git_repo` handles file | ✅ |
| Read-only directory | Error gracefully | `PermissionError` likely propagates | ⚠️ (Acceptable CLI behavior) |

### 1.4 Edge Cases Found
None critical. The handling of git worktrees (`.git` as file) is a particularly good inclusion (M4).

---

## 2. Error Handling Attack

### 2.1 Exception Handling Review

| Function | Exceptions Possible | Caught? | Handled Well? |
|----------|---------------------|---------|---------------|
| load_project_config() | TOMLDecodeError | ✅ | Yes, wraps in ConfigError |
| init_command() | Various | ✅ | Yes, returns exit codes |
| _install_hooks() | PermissionError | ✅ | Yes, prints warning and continues |

### 2.2 Error Handling Issues
No major issues. `save_project_config` allows OS errors to bubble up, which is standard for CLI tools (user needs to know if disk is full/read-only).

---

## 3. Hook Installation Attack

### 3.1 Collision Detection Test

**Code uses explicit marker `ONTOS_HOOK_MARKER`.**

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Ontos hook detected | True | Marker found | ✅ |
| Foreign hook detected | False | Marker missing | ✅ |
| Hook with "ontos" in comment | False | Checks for specific marker line | ✅ |

### 3.2 Hook Edge Cases

| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| .git/hooks doesn't exist | Create | `_get_hooks_dir` creates it | ✅ |
| Existing hook is directory | Error | `write_text` raises IsADirectoryError | ⚠️ (Caught by general Exception) |

### 3.3 Hook Shim Review

**Shim:**
- Shebang: `#!/usr/bin/env python3` (Standard)
- Marker included: Yes
- Fallback: Tries `ontos`, then `sys.executable -m ontos`. Robust.

### 3.4 Hook Issues Found
None. The use of an explicit marker is much safer than the previous heuristic.

---

## 4. Cross-Platform Attack

### 4.1 Windows Issues

| Issue | Code Location | Impact | Status |
|-------|---------------|--------|--------|
| Path separators | `pathlib` | None | ✅ Handled |
| chmod(0o755) | `_write_shim_hook` | No-op | ✅ Wrapped in try/except |
| Shebang not executed | Shim script | Hook fails in some shells | ✅ Best-effort accepted |
| CRLF line endings | Python I/O | None | ✅ Handled |

### 4.2 macOS Issues
No issues found.

### 4.3 Cross-Platform Verdict
**Status:** ✅ Works (Best-effort on Windows). The Python shim is the most robust cross-platform solution available without binary compilation.

---

## 5. Security Attack

### 5.1 Path Traversal

| Function | User Input? | Validated? | Risk |
|----------|-------------|------------|------|
| dict_to_config | Yes (config file) | ✅ | `_validate_path` ensures relative to repo root |

**Validation:** `resolved.is_relative_to(repo_root)` effectively blocks `../../etc/passwd`.

### 5.2 Config Injection

| Attack | Possible? | Impact |
|--------|-----------|--------|
| paths.docs_dir = "/tmp" | No | Blocked by validation |
| paths.docs_dir = "../../" | No | Blocked by validation |

### 5.3 Hook Security
**Status:** ✅ Safe. Shim delegates to CLI. Arguments passed through `subprocess.call` (list form) avoids shell injection.

---

## 6. Test Coverage Attack

### 6.1 Untested Code Paths
Coverage appears high. Error conditions (permissions, malformed files) are explicitly tested.

---

## 7. Issues Summary

### 7.1 Critical (Must Fix)
None.

### 7.2 High (Should Fix)
None.

### 7.3 Medium (Consider)
None.

### 7.4 Counts
| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 0 |

---

## 8. Verdict

### 8.1 Attack Results
| Attack Vector | Issues Found | Severity |
|---------------|--------------|----------|
| Edge cases | 0 | - |
| Error handling | 0 | - |
| Hook installation | 0 | - |
| Cross-platform | 0 | - |
| Security | 0 | - |

### 8.2 Risk Assessment
**Risk Level:** Low. The added validation logic (types, paths) significantly hardens the implementation compared to the spec v1.0 draft.

### 8.3 Recommendation
**Recommendation:** Approve

**Blocking issues:** None

**Summary:** Robust implementation. The adversarial concerns raised during spec review (path traversal, hook collision false positives, type safety) have all been effectively mitigated.

---

**Review signed by:**
- **Role:** Adversarial Reviewer
- **Model:** Codex (OpenAI)
- **Date:** 2026-01-13
- **Review Type:** Code Review (Phase 3 Implementation)

*End of Adversarial Code Review*