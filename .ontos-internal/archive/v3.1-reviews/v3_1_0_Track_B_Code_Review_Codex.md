# D.2b: Adversarial Code Review — Track B

**Phase:** D.2b (Code Review — Review Board)  
**PR:** #55 `feat(cli): Ontos v3.1.0 Track B - Native Command Migration`  
**Branch:** `feat/v3.1.0-track-b`  
**Role:** Adversarial Reviewer (Codex / OpenAI)  
**Date:** 2026-01-21

---

## Part 1: Regression Hunt

**Test suite:**
```bash
python3 -m pytest tests/ -v
```
Result: **463 passed, 2 skipped**

**Legacy vs Native (help parity comparisons):**

| Command | Legacy Still Works? | Native Matches Legacy? | Differences |
|---------|---------------------|------------------------|-------------|
| scaffold | ✅ (help) | ⚠️ | Help text changed; adds `--quiet/--json`, removes legacy description/examples. |
| verify | ✅ (help) | ⚠️ | Help text changed; adds `--quiet/--json`; arg name `path` vs `filepath`; examples removed. |
| query | ✅ (help) | ⚠️ | Help text changed; adds `--quiet/--json`; `--dir` description differs; examples removed. |
| consolidate | ✅ (help) | ⚠️ | Help text changed; adds `--quiet/--json`; examples removed; wording changes. |
| stub | ✅ (help) | ⚠️ | Help text changed; adds `--quiet/--json`; type arg no longer enumerated in help. |
| promote | ✅ (help) | ⚠️ | Help text changed; adds `--quiet/--json`. |
| migrate | ✅ (help via `ontos_migrate_schema.py`) | ⚠️ | Help text changed; adds `--quiet/--json`; short flag `-n` for dry-run. |

**Regressions found:**

| Regression | Command | How Discovered | Impact |
|------------|---------|----------------|--------|
| Native consolidate crashes due to missing `ontos_config_defaults` import | consolidate | `python3 -m ontos consolidate --dry-run` → `Error: No module named 'ontos_config_defaults'` | Command unusable in normal CLI invocation. |
| Absolute path promotion can crash on macOS `/tmp` symlink | promote | `python3 -m ontos promote /tmp/.../no_status.md --check` → `ValueError` from `Path.relative_to` | Hard crash when absolute paths use `/tmp` vs `/private/tmp`. |

---

## Part 2: Edge Case Analysis (Actual Behavior)

### scaffold

| Edge Case | Input | Expected | Actual | Pass? |
|-----------|-------|----------|--------|-------|
| No markdown files | empty dir | Graceful message | `✅ No files need scaffolding` | ✅ |
| Already has frontmatter | `docs/has_frontmatter.md` | Skip file | `✅ No files need scaffolding` | ✅ |
| Invalid path | nonexistent dir | Error with message | `✅ No files need scaffolding` | ❌ |
| Permission denied | dir chmod 000 | Error, no crash | `✅ No files need scaffolding` (silent) | ❌ |
| Very long filename | 260 chars | Handle or error | OS error on file creation (`Errno 63`) | ⚠️ (OS limit) |
| Special characters | `file (1).md`, `file's.md` | Handle correctly | Scaffolded; IDs `file_1`, `files` | ✅ |
| Symlinks | symlinked `.md` | Follow or skip? | Scaffolded symlink | ⚠️ (implicit follow) |
| Binary `.md` | bytes file | Skip or error | Skipped silently | ⚠️ |

### verify

| Edge Case | Input | Expected | Actual | Pass? |
|-----------|-------|----------|--------|-------|
| No stale documents | `--all` in temp repo | “Nothing to verify” | `✅ No stale documents found.` | ✅ |
| File doesn't exist | `verify missing.md` | Error message | `❌ File not found: ...` | ✅ |
| Invalid frontmatter | malformed YAML | Error with line number | `❌ No frontmatter in ...` | ❌ |
| `--days 0` | `verify --days 0` | Error or handle | Argparse error: unrecognized `--days` | ❌ |
| `--days -1` | `verify --days -1` | Error or handle | Same as above | ❌ |

### query

| Edge Case | Input | Expected | Actual | Pass? |
|-----------|-------|----------|--------|-------|
| Nonexistent ID | `--depends-on fake` | “Not found” | `⚠️ fake has no dependencies (or doesn't exist)` | ✅ |
| Circular dependency | c1↔c2 then `--health` | Detect/report | No cycle detection; just health stats | ❌ |
| Empty graph | `--health` in empty repo | Graceful handling | `❌ No documents found in ...` | ✅ |
| Multiple flags | `--depends-on c1 --health` | Error | Argparse error (mutually exclusive) | ✅ |
| Glob in concept | `--concept "auth*"` | Works or clear error | Treated literal: `No documents tagged with 'auth*'` | ⚠️ |

### consolidate

| Edge Case | Input | Expected | Actual | Pass? |
|-----------|-------|----------|--------|-------|
| No logs exist | empty repo | “Nothing to consolidate” | **Crash:** `Error: No module named 'ontos_config_defaults'` | ❌ |
| `--keep 0` | `--count 0 --dry-run` | Consolidate all | `✅ Nothing to consolidate.` (even with logs) | ❌ |
| `--keep -1` | `--count -1 --dry-run` | Error | Consolidates unexpected log from contributor repo | ❌ |
| Log file locked | locked file | Error, no corruption | Not tested | — |

### stub

| Edge Case | Input | Expected | Actual | Pass? |
|-----------|-------|----------|--------|-------|
| Invalid doc_type | `--type faketype` | Error | Created stub successfully | ❌ |
| Output path exists | existing file | Overwrite? Prompt? | Overwrites without warning | ❌ |
| Invalid ID characters | `--id "my doc"` | Error/sanitize | Writes `id: my doc` | ❌ |

### promote

| Edge Case | Input | Expected | Actual | Pass? |
|-----------|-------|----------|--------|-------|
| Already promoted | file with `curation_level: 2` | “Already promoted” | `✅ No documents need promotion - all at Level 2!` | ⚠️ |
| No status field | file missing status | Add or error | `--check` shows blockers (missing status/depends_on) | ✅ |
| Absolute path in /tmp | `--check /tmp/...` | Works | **Crash:** `ValueError` from `relative_to` | ❌ |

### migrate

| Edge Case | Input | Expected | Actual | Pass? |
|-----------|-------|----------|--------|-------|
| Already current schema | `--check` | “Nothing to migrate” | OK (reports already migrated) | ✅ |
| `--check` + `--apply` | conflicting flags | Error | Argparse error (mutually exclusive) | ✅ |
| Unsupported schema version | `ontos_schema: 99.0` | Error message | Counted as “Already migrated” | ❌ |

---

## Part 3: Error Handling Deep Dive

| Error Condition | Command | Error Message Clear? | Exit Code Correct? | Stack Trace Suppressed? |
|-----------------|---------|---------------------|--------------------|-------------------------|
| Invalid arguments | query, migrate | ✅ (argparse) | ✅ (2) | ✅ |
| File not found | verify | ✅ | ✅ (1) | ✅ |
| Permission denied | scaffold | ❌ (silent) | ❌ (0) | ✅ |
| Malformed YAML | verify | ❌ (no line/col) | ✅ (1) | ✅ |
| Missing config module | consolidate | ❌ (`No module named 'ontos_config_defaults'`) | ❌ (5) | ✅ |
| Keyboard interrupt | consolidate/verify interactive | Not tested | — | — |

**Bad error handling patterns found:**
| Pattern | Location | Fix |
|---------|----------|-----|
| Hard failure on missing `ontos_config_defaults` | `ontos/core/paths.py:15` | Wrap import with fallback or package module properly. |
| Silent skip on unreadable paths | `ontos/commands/scaffold.py` | Emit warning when path unreadable or nonexistent. |

---

## Part 4: Test Adequacy Analysis

**Parity tests summary:** all 14 parity tests pass but are shallow and often don’t validate parity or exit codes.

| Test | What It Claims | What It Actually Tests | Gap? |
|------|----------------|------------------------|------|
| `test_consolidate_count_parity` | Consolidation moves logs | No assertions (commented out) | ✅ |
| `test_scaffold_help_parity` | Help matches legacy | Only checks flags in stdout | ✅ |
| `test_verify_single_file_parity` | Updates describes_verified | Doesn’t assert JSON/exit codes in error cases | ⚠️ |
| `test_query_health_parity` | Health metrics | Uses controlled files but no legacy comparison | ✅ |
| `test_stub_file_creation_parity` | Stub content parity | Checks some fields only; no overwrite/type validation | ⚠️ |
| `test_promote_check_parity` | Parity | Only checks `--check` output basics | ⚠️ |
| `test_migrate_check_parity` | Parity | Doesn’t cover unsupported schema or missing dirs | ⚠️ |

**Tests that could pass even with bugs:**
| Test | Why It Might Miss Bugs |
|------|------------------------|
| `test_consolidate_count_parity` | No asserts; command can fail and test still passes. |
| `test_*_help_parity` | Only checks flags; help content regressions go unnoticed. |
| `test_stub_file_creation_parity` | Doesn’t catch overwrite or invalid ID/type handling. |

**Missing test scenarios:**
| Scenario | Why Important | Effort to Add |
|----------|---------------|---------------|
| consolidate without `ontos_config_defaults` | Prevents command from running in native CLI | Low |
| promote with absolute paths on macOS `/tmp` | Common path mismatch; current crash | Low |
| stub invalid type/id | Prevents invalid docs | Low |
| scaffold invalid path/permission | Prevents silent success on failure | Low |

---

## Part 5: Failure Mode Analysis

| Failure | How It Happens | Detection | Recovery | Graceful? |
|---------|----------------|-----------|----------|-----------|
| consolidate import crash | Missing `ontos_config_defaults` in sys.path | Immediate error | None | ❌ |
| promote absolute path crash | `/tmp` vs `/private/tmp` path mismatch | Unhandled `ValueError` | None | ❌ |
| scaffold silent skip | Permission denied path | No warning, success exit | None | ❌ |
| consolidate partial write | Crash after move before ledger update | Inconsistent history | Manual fix | ⚠️ |

---

## Part 6: Blind Spot Identification

| Area | Suspicion | Why |
|------|-----------|-----|
| Config resolution | Native CLI doesn’t include `ontos_config_defaults` | Actual `ontos consolidate` fails in normal run. |
| Path normalization | `/tmp` symlink path mismatch | `Path.relative_to` used without `resolve()` in `promote`. |
| Input validation | stub and scaffold accept invalid inputs | No validation on type/id/paths. |

**What seems too simple?**

| Feature | Why It Might Be Harder |
|---------|------------------------|
| “Parity” | Tests don’t compare against legacy outputs or exit codes. |
| Consolidation | Relies on module import and path resolution; currently broken. |

---

## Part 7: Issues Found

**Critical (Must Fix):**

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-C1 | Native consolidate crashes on missing `ontos_config_defaults` | `python3 -m ontos consolidate --dry-run` | Command unusable; breaks migration promise. |

**High (Should Fix):**

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-H1 | Promote crashes on absolute `/tmp` paths | `promote /tmp/... --check` | Hard crash on common macOS path usage. |
| X-H2 | consolidate `--count 0` returns no-op | `consolidate --count 0` | Unexpected behavior; cannot consolidate all logs. |

**Medium (Consider):**

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-M1 | Stub accepts invalid type/id | `stub --type faketype --id "my doc"` | Invalid docs created without warning. |
| X-M2 | Scaffold invalid path/permission yields success | nonexistent/permission denied | Silent failure; user thinks it worked. |
| X-M3 | Migrate ignores unsupported schema versions | `ontos_schema: 99.0` | Silent acceptance of invalid schema. |
| X-M4 | Query health doesn’t flag cycles | c1↔c2 | Misses graph integrity issues. |

---

## Part 8: Verdict

**Robustness:** Fragile  
**Edge Case Handling:** Poor  
**Error Handling:** Poor  
**Test Adequacy:** Poor

**Recommendation:** Request changes

**Top 3 Concerns:**
1. `consolidate` hard-crashes due to missing `ontos_config_defaults` import (`ontos/core/paths.py:15`).
2. `promote` crashes on `/tmp` absolute paths due to `Path.relative_to` mismatch (`ontos/commands/promote.py`).
3. Parity tests are superficial; several can pass even when commands fail.

---

**Review signed by:**
- **Role:** Adversarial Reviewer
- **Model:** Codex (OpenAI)
- **Date:** 2026-01-21
- **Review Type:** Code Review — Track B

---

*D.2b — Adversarial Code Review*  
*v3.1.0 Track B — Native Command Migration*
