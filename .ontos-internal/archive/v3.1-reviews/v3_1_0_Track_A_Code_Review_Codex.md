# Phase D.2a: Review Board — Track A Code Review

**Project:** Ontos v3.1.0  
**Phase:** D.2a (Code Review)  
**Track:** A — Obsidian Compatibility + Token Efficiency  
**Branch:** `feat/v3.1.0-track-a`  
**PR:** #54 — https://github.com/ohjona/Project-Ontos/pull/54  
**Date:** 2026-01-21

---

## Part 1: Spec Compliance Review

### §3.1 Tags and Aliases

| Requirement | Code Location | Implemented? | Correctly? | Notes |
|-------------|---------------|--------------|------------|-------|
| `normalize_tags()` merges concepts + tags | `frontmatter.py` | ✅ | ✅ | Uses set merge of `tags` + `concepts`. |
| Tags deduplicated and sorted | `frontmatter.py` | ✅ | ✅ | `set()` + `sorted()`. |
| Handles string input (not just list) | `frontmatter.py` | ✅ | ✅ | `tags` supports `str`. |
| Whitespace stripped | `frontmatter.py` | ✅ | ✅ | `strip()` on tag/alias entries. |
| `normalize_aliases()` auto-generates | `frontmatter.py` | ✅ | ✅ | Adds Title Case + kebab-case. |
| Title Case variant from id | `frontmatter.py` | ✅ | ✅ | `doc_id.replace('_', ' ').title()`. |
| kebab-case variant from id | `frontmatter.py` | ✅ | ✅ | `doc_id.replace('_', '-')`. |

### §3.2 Obsidian Mode

| Requirement | Code Location | Implemented? | Correctly? | Notes |
|-------------|---------------|--------------|------------|-------|
| `--obsidian` flag registered | `cli.py` | ✅ | ✅ | `_register_map()`. |
| `MapOptions.obsidian` field | `map.py` | ✅ | ✅ | In `MapOptions` + `GenerateMapOptions`. |
| `_format_doc_link()` function | `map.py` | ✅ | ✅ | Present. |
| `[[filename\|id]]` when filename ≠ id | `map.py` | ✅ | ✅ | Uses `doc_path.stem`. |
| `[[id]]` when filename == id | `map.py` | ✅ | ✅ | Matches spec. |
| Uses `doc_path.stem` for filename | `map.py` | ✅ | ✅ | Implemented. |

### §3.3 Document Cache

| Requirement | Code Location | Implemented? | Correctly? | Notes |
|-------------|---------------|--------------|------------|-------|
| `DocumentCache` class exists | `cache.py` | ✅ | ✅ | Present. |
| `CacheEntry` dataclass | `cache.py` | ✅ | ✅ | Present. |
| mtime-based invalidation | `cache.py` | ✅ | ❌ | API requires caller to pass mtime; spec shows internal `stat()` with OSError handling. |
| `get()` returns None on miss | `cache.py` | ✅ | ✅ | Returns `None` when not cached. |
| `get()` returns None on stale | `cache.py` | ✅ | ✅ | Mismatch in mtime invalidates. |
| `set()` stores with mtime | `cache.py` | ✅ | ✅ | Caller provides mtime. |
| `invalidate()` removes entry | `cache.py` | ✅ | ✅ | `pop()`. |
| `clear()` removes all | `cache.py` | ✅ | ✅ | Resets entries/hits/misses. |
| `stats` property | `cache.py` | ✅ | ✅ | Provides hit rate. |
| `--no-cache` flag | `cli.py` | ✅ | ✅ | Registered. |
| Cache integrated into map command | `map.py` | ✅ | ✅ | `DocumentCache` used in `map_command()`. |

### §3.4 Compact Output

| Requirement | Code Location | Implemented? | Correctly? | Notes |
|-------------|---------------|--------------|------------|-------|
| `CompactMode` enum (OFF, BASIC, RICH) | `map.py` | ✅ | ✅ | Present. |
| `--compact` flag accepts basic/rich | `cli.py` | ✅ | ✅ | `choices=["basic", "rich"]`. |
| `_generate_compact_output()` function | `map.py` | ✅ | ✅ | Present. |
| Basic format: `id:type:status` | `map.py` | ✅ | ✅ | Implemented. |
| Rich format: `id:type:status:"summary"` | `map.py` | ✅ | ✅ | Implemented. |
| Backslash escaped: `\` → `\\` | `map.py` | ✅ | ✅ | First replacement. |
| Quote escaped: `"` → `\"` | `map.py` | ✅ | ✅ | Implemented. |
| Newline escaped: `\n` → `\\n` | `map.py` | ✅ | ✅ | Implemented. |
| Escaping order correct (backslash first) | `map.py` | ✅ | ✅ | Order matches spec. |

### §3.5 YAML Errors and Leniency

| Requirement | Code Location | Implemented? | Correctly? | Notes |
|-------------|---------------|--------------|------------|-------|
| `FrontmatterParseError` dataclass | `frontmatter.py` | ❌ | ❌ | Missing. |
| filepath, line, column, message fields | `frontmatter.py` | ❌ | ❌ | Missing. |
| Optional suggestion field | `frontmatter.py` | ❌ | ❌ | Missing. |
| `__str__` formats as `file:line:col: message` | `frontmatter.py` | ❌ | ❌ | Missing. |
| `read_file_lenient()` function | `obsidian.py` | ✅ | ✅ | Present. |
| Strips UTF-8 BOM (`\xef\xbb\xbf`) | `obsidian.py` | ✅ | ✅ | Implemented. |
| Handles leading whitespace before `---` | `obsidian.py` | ✅ | ✅ | Implemented. |
| Schema version error includes upgrade hint | `frontmatter.py` | ❌ | ❌ | No schema version error type/message; CA marked this low severity. |

### §3.6 Doctor Verbose

| Requirement | Code Location | Implemented? | Correctly? | Notes |
|-------------|---------------|--------------|------------|-------|
| `-v`/`--verbose` flag registered | `cli.py` | ✅ | ✅ | Present. |
| `_get_config_path()` helper | `doctor.py` | ✅ | ❌ | Uses `cwd` instead of repo root. |
| Checks `.ontos.toml` in repo root | `doctor.py` | ❌ | ❌ | `cwd` only; wrong when run from subdir. |
| `_print_config_paths()` function | `doctor.py` | ✅ | ✅ | Implemented as `_print_verbose_config()`. |
| Shows repo_root | `doctor.py` | ✅ | ✅ | Printed. |
| Shows config_path (or "default") | `doctor.py` | ✅ | ❌ | Can report wrong path due to `cwd`. |
| Shows docs_dir | `doctor.py` | ✅ | ✅ | Printed. |
| Shows context_map path | `doctor.py` | ✅ | ✅ | Printed. |

### §3.7 Filter Flag

| Requirement | Code Location | Implemented? | Correctly? | Notes |
|-------------|---------------|--------------|------------|-------|
| `--filter` / `-f` flag registered | `cli.py` | ✅ | ✅ | Present. |
| `FilterExpression` dataclass | `map.py` | ✅ | ✅ | Present. |
| `parse_filter()` function | `map.py` | ✅ | ✅ | Present. |
| Splits on whitespace | `map.py` | ✅ | ✅ | Uses `expr.split()`. |
| Splits field:value on `:` | `map.py` | ✅ | ✅ | Uses `partition(':')`. |
| Splits values on `,` | `map.py` | ✅ | ✅ | `value.split(',')`. |
| `matches_filter()` function | `map.py` | ✅ | ✅ | Present. |
| `type` field matching | `map.py` | ✅ | ✅ | Case-insensitive. |
| `status` field matching | `map.py` | ✅ | ✅ | Case-insensitive. |
| `concept` field matching | `map.py` | ✅ | ✅ | Uses frontmatter `concepts`. |
| `id` field with glob (fnmatch) | `map.py` | ✅ | ✅ | `fnmatch.fnmatch`. |
| Multiple values = OR | `map.py` | ✅ | ✅ | `any()` across values. |
| Multiple fields = AND | `map.py` | ✅ | ✅ | All filters must match. |
| Case-insensitive matching | `map.py` | ✅ | ✅ | Lowercasing values. |

---

## Part 2: Code Quality Review

### New Files

| File | Lines | Readability | Error Handling | Type Hints | Docstrings | Overall |
|------|-------|-------------|----------------|------------|------------|---------|
| `cache.py` | 96 | Good | Adequate | Good | Good | Adequate |
| `obsidian.py` | 53 | Good | Adequate | Good | Good | Adequate |

### Modified Files

| File | Change Size | Risk | Quality | Notes |
|------|-------------|------|---------|-------|
| `frontmatter.py` | M | Med | Adequate | Missing required error types. |
| `map.py` | L | High | Adequate | Spec gaps in obsidian leniency gating + cache API mismatch. |
| `doctor.py` | M | Low | Adequate | Verbose config path uses `cwd`. |
| `cli.py` | S | Low | Good | Flag registration matches spec. |

---

## Part 3: Architecture Compliance

| Constraint | Check | Status |
|------------|-------|--------|
| No `core/` → `io/` imports | `rg -n "from ontos.io" ontos/core/` | ❌ Violation (`ontos/core/config.py` imports `ontos.io.git`, pre-existing per CA) |
| No `core/` → `commands/` imports | `rg -n "from ontos.commands" ontos/core/` | ✅ Empty |
| `cache.py` in `core/` | File location | ✅ |
| `obsidian.py` in `io/` | File location | ✅ |
| Consistent import style | Match existing patterns | ✅ |

---

## Part 4: Test Coverage Assessment

| Test File | Exists? | Coverage | Quality | Missing Cases |
|-----------|---------|----------|---------|---------------|
| `tests/core/test_cache.py` | ✅ | Adequate | Adequate | No OSError/delete/permission scenarios; no stat mismatch beyond mtime. |
| `tests/test_frontmatter_tags.py` | ✅ | Adequate | Adequate | No null/whitespace edge cases for tags/aliases. |
| `tests/test_map_compact.py` | ✅ | Adequate | Adequate | No non-string summary or combined escaping edge cases. |
| `tests/test_map_filter.py` | ✅ | Adequate | Adequate | No empty/whitespace/invalid field cases. |
| `tests/test_map_obsidian.py` | ❌ | Poor | Poor | Missing entirely (wikilink formatting + leniency behavior). |
| CA full test run | N/A | N/A | N/A | CA reports `pytest tests/ -v` passed (440/2 skipped); I did not run tests. |

---

## Part 5: Edge Case & Failure Mode Analysis

### normalize_tags / normalize_aliases

| Edge Case | Expected Behavior | Handled? | Test? |
|-----------|-------------------|----------|-------|
| Empty frontmatter `{}` | Return `[]` | ✅ | ✅ |
| `tags: null` | Return `[]` or skip | ✅ | ❌ |
| `tags: ""` (empty string) | Return `[]` | ✅ | ❌ |
| `tags: "single"` (string not list) | Return `["single"]` | ✅ | ✅ |
| `tags: [null, "", "valid"]` | Filter out null/empty | ✅ | ❌ |
| `tags: [" spaced "]` | Strip whitespace | ✅ | ❌ |
| Duplicate between tags and concepts | Deduplicate | ✅ | ✅ |
| `doc_id` is empty/None | Don't crash on alias generation | ✅ | ✅ (empty string only) |
| `doc_id` with special chars | Handle gracefully | ✅ | ❌ |

### DocumentCache

| Edge Case | Expected Behavior | Handled? | Test? |
|-----------|-------------------|----------|-------|
| `get()` on empty cache | Return `None` | ✅ | ✅ |
| `get()` after file deleted | Return `None`, don't crash | ❌ | ❌ |
| `get()` after file permission denied | Return `None`, don't crash | ❌ | ❌ |
| `set()` on unreadable file | Don't store, don't crash | ❌ | ❌ |
| Path with symlinks | Resolve consistently | ✅ | ❌ |
| Concurrent access (theoretical) | No corruption | ❌ | ❌ |
| Very large file (mtime precision) | Correct invalidation | ⚠️ | ❌ |

### Compact Output Escaping

| Edge Case | Input | Expected Output | Handled? | Test? |
|-----------|-------|-----------------|----------|-------|
| Quote in summary | `He said "hello"` | `He said \"hello\"` | ✅ | ✅ |
| Newline in summary | `Line1\nLine2` | `Line1\\nLine2` | ✅ | ✅ |
| Backslash in summary | `path\to\file` | `path\\to\\file` | ✅ | ✅ |
| All three combined | `"a\nb\\c"` | `\"a\\nb\\\\c\"` | ✅ | ❌ |
| Already escaped input | `already \"escaped\"` | `already \\\"escaped\\\"` | ✅ | ❌ |
| Empty summary | `""` | Use basic format | ✅ | ❌ |
| Unicode in summary | `日本語 émojis 🎉` | Pass through unchanged | ✅ | ❌ |
| Very long summary | 10KB string | Handle without crash | ✅ | ❌ |

### Filter Parsing

| Edge Case | Input | Expected Behavior | Handled? | Test? |
|-----------|-------|-------------------|----------|-------|
| Empty string | `""` | No filters (match all) | ✅ | ❌ |
| Whitespace only | `"   "` | No filters (match all) | ✅ | ❌ |
| Missing colon | `"type"` | Ignore or error | ✅ (ignored) | ❌ |
| Empty value | `"type:"` | Match nothing or error | ✅ (ignored) | ❌ |
| Unknown field | `"unknown:value"` | Ignore (per CA guidance) | ✅ | ❌ |
| Multiple colons | `"type:a:b"` | Split on first only | ✅ | ❌ |
| Trailing comma | `"type:a,b,"` | Ignore empty | ✅ | ❌ |
| Case variations | `"TYPE:Strategy"` | Case-insensitive | ✅ | ✅ |
| Glob characters | `"id:auth_*"` | fnmatch pattern | ✅ | ✅ |
| Special regex chars | `"id:file[1].md"` | Treat as literal (fnmatch) | ✅ | ❌ |

### Wikilink Formatting

| Edge Case | Filename | doc_id | Expected | Handled? | Test? |
|-----------|----------|--------|----------|----------|-------|
| Match | `auth_flow.md` | `auth_flow` | `[[auth_flow]]` | ✅ | ❌ |
| Mismatch | `auth-flow.md` | `auth_flow` | `[[auth-flow\|auth_flow]]` | ✅ | ❌ |
| Spaces in filename | `my file.md` | `my_file` | `[[my file\|my_file]]` | ✅ | ❌ |
| Special chars | `file (1).md` | `file_1` | Correct escaping | ⚠️ | ❌ |
| Unicode filename | `日本語.md` | `japanese` | Handle correctly | ✅ | ❌ |
| Very long filename | 200+ chars | Any | Don't crash | ✅ | ❌ |

### Obsidian Leniency

| Edge Case | Input | Expected | Handled? | Test? |
|-----------|-------|----------|----------|-------|
| UTF-8 BOM present | `\xef\xbb\xbf---\n...` | Strip BOM, parse | ✅ | ❌ |
| Leading newlines | `\n\n---\n...` | Skip newlines, parse | ✅ | ❌ |
| Leading spaces | `  ---\n...` | Skip spaces, parse | ✅ | ❌ |
| Mixed whitespace | `\n  \t---\n...` | Skip all, parse | ✅ | ❌ |
| No frontmatter | `Just content` | Return unchanged | ✅ | ❌ |
| UTF-16 BOM | `\xff\xfe...` | Not handled (OK) | N/A | N/A |
| Non-UTF8 file | Binary data | Error gracefully | ❌ | ❌ |

---

## Part 6: Issues Found

### Critical (Blocking — Must fix before merge)

| # | Issue | File | Line(s) | Description | Suggested Fix |
|---|-------|------|---------|-------------|---------------|
| C-1 | Missing structured YAML errors | `ontos/core/frontmatter.py` | 1 | Spec §3.5 requires `FrontmatterParseError` and detailed parsing; missing entirely (CA noted as low severity). | Implement `FrontmatterParseError` + safe parsing entry point per spec, wire into YAML parsing. |

### Major (Should fix before merge)

| # | Issue | File | Line(s) | Description | Suggested Fix |
|---|-------|------|---------|-------------|---------------|
| M-1 | Obsidian leniency applied unconditionally | `ontos/commands/map.py` | 507 | `read_file_lenient()` is used regardless of `--obsidian`, contradicting spec and potentially altering non-Obsidian frontmatter detection. | Gate lenient reads behind `options.obsidian`, use strict read otherwise. |
| M-2 | Cache API diverges from spec + missing OSError handling | `ontos/core/cache.py` | 39 | `get()`/`set()` require caller mtime; spec expects internal stat + OSError handling. Current flow fails on deleted/permission-denied files before cache gets a chance. | Align with spec (internal stat + OSError handling) or update spec; add handling in map if keeping pure cache. |
| M-3 | Schema version upgrade hint not implemented | `ontos/io/yaml.py` | 1 | Spec §3.5 requires error with upgrade hint for newer schema versions; no SchemaVersionError or message present. | Implement schema version check + error message per spec. |

### Minor (Consider fixing)

| # | Issue | File | Line(s) | Description | Suggested Fix |
|---|-------|------|---------|-------------|---------------|
| m-1 | Verbose config path uses `cwd`, not repo root | `ontos/commands/doctor.py` | 456 | Running `doctor -v` from subdir may report wrong `.ontos.toml` path. | Pass `project_root` into `_get_config_path()` or resolve via `find_project_root()`. |
| m-2 | Rich compact summary assumes string | `ontos/commands/map.py` | 323 | Non-string `summary` values will raise at `.replace()` in rich mode. | Coerce to `str` or guard by `isinstance(summary, str)`. |

---

## Part 7: Verdict

**Spec Compliance:** Major gaps  
**Code Quality:** Adequate  
**Test Coverage:** Adequate  
**Risk Assessment:** Medium  
**Recommendation:** Request revision  
**Blocking issues:** 1

**Summary:**
Spec compliance is incomplete for §3.5 and partially off for §3.3/§3.6. The biggest risk is missing structured YAML parse errors and schema-version handling, which are explicit requirements (CA marked these low severity). Obsidian leniency is applied globally, which changes strict-mode behavior and can alter frontmatter detection unexpectedly. Tests cover core happy paths but miss Obsidian output and edge/error cases; CA reports the full suite passing, but I did not run them.

---

**Review signed by:**
- **Role:** Adversarial Reviewer
- **Model:** Codex (GPT-5)
- **Date:** 2026-01-21
- **Review Type:** Code Review (Phase D.2a)
- **PR:** #54
