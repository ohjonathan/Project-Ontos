# Adversarial Verification: v4.3.0 Retrofit Fixes

**Date:** 2026-04-15
**PR:** #110
**Branch / HEAD:** `feature/v4.3.0-obsidian-retrofit` @ `982216d`
**Verifier:** Claude (Opus 4.6, 1M context)
**Test results after verification:** `tests/commands/test_retrofit.py` 21 passed, `tests/commands/test_rename.py` 25 passed.

## Summary

| Fix | Issue | Verdict |
|---|---|---|
| V1 | Comment preservation (CB1) | **Resolved** |
| V2 | Merge-key / tag-prefix detection (CB3) | **Resolved** |
| V3 | Date-like quoting (CB6) | **Resolved** |
| V4 | Stale block removal (CB2) | **Resolved** |
| V5 | CRLF preservation (CB4) | **Resolved** (one documented limitation) |
| V6 | Loader issue surfacing (CB8) | **Resolved** |
| V7 | RetrofitEdit.path + noop reporting (CS1) | **Resolved** |
| V8 | Documentation (CB7 + CS4) | **Resolved** |

**Overall: Approve.**

---

## Detailed Findings

### V1 — Comment Preservation During Replace (CB1) — **Resolved**

**Code under review:** `ontos/core/frontmatter_edit.py:118-124` (back-walk loop) and `:93-95` (`_is_blank_or_comment_line`).

The back-walk runs `end_line_index -= 1` while the previous line is blank or starts with `#`, stopping above the run of trailing comments/blanks before the next top-level field.

**Test:** `test_retrofit_apply_replace_preserves_inter_field_comment` PASSED.

**Break attempts (all preserved correctly):**

1. **Three consecutive comment lines between fields.** `tags` block end_line_index=2 (stops after `- a`); the comments live at lines 2–4 outside the block. Replacement leaves them intact. ✓
2. **Comment immediately after last value (no blank separator).** `tags` block end=2, `# inline-after-value` at line 2 outside the block. ✓
3. **Comment that looks like a YAML field (`# tags: legacy`).** Indexer skips the comment via the `stripped.startswith("#")` guard at L107 *before* regex matching, so the look-alike never registers as a field. ✓
4. **Inline comment on field line itself (`tags: # legacy`).** This case is a known acceptable behavior: the inline comment lives on the field line, so it is part of `block_lines[0]` and is replaced along with the value. The fix is scoped to *inter-field* comments, which matches the spec. Not a regression.
5. **Blank + comment + blank trailing run.** Back-walk consumes all three lines; `tags` block ends cleanly. ✓
6. **Rename suite cross-check.** All 25 rename tests still pass — the shared helper change in `_index_top_level_fields` did not regress the rename path.

---

### V2 — Merge-Key / YAML Tag-Prefix Detection (CB3) — **Resolved**

**Code under review:** `_TOP_LEVEL_FIELD_RE` at `frontmatter_edit.py:18` (regex requires `[A-Za-z_]` start, so `<<:` is rejected); `_has_nonempty_parsed_value` at `retrofit.py:529-542`; `_build_file_plan` branch at `retrofit.py:359-373` (zero-occurrence + non-empty parsed → blocking `REASON_UNPATCHABLE_FORMAT`).

**Tests:** `test_retrofit_dry_run_warns_on_merge_derived_tags_without_duplicate_insert` and `test_retrofit_dry_run_warns_on_tag_prefixed_tags_field` PASSED.

**Break attempts:**

1. **Both merge-key AND explicit `tags:` present.** The explicit field is the one indexed (regex matches it). Computed value drove a `remove` action on the explicit block. Merge-key line `<<: *shared` was ignored by the indexer (regex non-match), so no duplicate edit. ✓
2. **Merge key where shared does NOT define `tags`.** `parsed_frontmatter` has no `tags` key, so `_has_nonempty_parsed_value` returns False; computed value is empty (no concepts); no insert, no warning. ✓
3. **Idempotency on merge-key document.** Two consecutive `_build_file_plan` calls produce identical empty edits + identical blocking warning `unpatchable_field_format`. Apply is correctly blocked, no error. ✓

---

### V3 — Date-Like Scalar Quoting (CB6) — **Resolved**

**Code under review:** `_DATE_LIKE_RE = re.compile(r"^\d{4}-\d{2}(-\d{2})?")` at `retrofit.py:48` and `_serialize_item` at `:588-607`.

**Test:** `test_retrofit_apply_quotes_date_like_tag_values` PASSED.

**Break attempts (regex behavior validated against PyYAML round-trip semantics):**

| Input | Regex match | Quoted? | PyYAML parse | Verdict |
|---|---|---|---|---|
| `2026-01` | yes | yes | str (regardless) | safe |
| `2026-01-01` | yes | yes | date if unquoted | **needs quote — caught ✓** |
| `2026-1-1` | no | no | str (PyYAML strict ISO) | safe — no quote needed |
| `2026-01-1` | no | no | str | safe |
| `2026-1-01` | no | no | str | safe |
| `26-01-01` | no | no | str | safe |
| `12:30:00` | no | yes (via `:` check at L592) | **int 45000 (sexagesimal!) if unquoted** | safe — caught by punctuation check |
| `2026-01-01T00:00:00Z` | yes | yes | str when quoted | safe ✓ |
| `not-a-date-2026-01-01` | no (anchored) | no | str | safe |
| `2026` | no | yes (via `float()` at L599) | int if unquoted | safe ✓ |
| `2026-13-99` | yes | yes | error if unquoted | safe (over-match is harmless) |
| `2026/01/01` | no | no | str | safe |

**Notable:** I initially flagged `2026-1-1` as a regex gap, but PyYAML's strict ISO 8601 conformance means single-digit month/day variants are parsed as plain strings — no quoting needed. The regex is exactly tight enough. The `12:30:00` case (PyYAML sexagesimal int) is already caught by the `:` punctuation check, not the date regex.

**Round-trip:** `tags: ["2026-01-01"]` (quoted) → `parsed['tags']` returns `[str]`. Unquoted `tags: - 2026-01-01` → returns `[datetime.date]`. Confirms the bug existed pre-fix and is now caught.

---

### V4 — Empty Computed Values Remove Stale Blocks (CB2) — **Resolved**

**Code under review:** `should_remove` gate at `retrofit.py:375-377`; remove branch at `:438-450`. `RetrofitEdit.action` accepts `"remove"` per `:66`. Line splice uses `lines[occurrence.line_index : occurrence.end_line_index]`, which honors the V1 back-walk.

**Test:** `test_retrofit_removes_stale_tags_when_computed_value_is_empty` PASSED.

**Break attempts:**

1. **Field with trailing comment removed.** Constructed `tags: - stale\n# trailing comment after tags\naliases: ...`. Result: tags block removed, `# trailing comment after tags` survives in output. V1+V4 interaction works. ✓
2. **Remove first field after opening `---`.** Tags as first field; removed cleanly, `title` and `id` shift up to first position. ✓
3. **Remove last field before closing `---`.** Tags as last field; removed cleanly, frontmatter terminates at `id` + `title`. ✓
4. **Idempotency.** After removing stale tags and writing back, second `_build_file_plan` returns empty edits and empty warnings. ✓

---

### V5 — CRLF Line Ending Preservation (CB4) — **Resolved** (one documented limitation)

**Code under review:** `_detect_dominant_line_ending` at `retrofit.py:571-578`; called once per file at `:334`. Used by both replace path (`_format_field_block` at L455) and insert path (`_format_field_block` at L471 + trailing-newline normalization at L472-473).

**Test:** `test_retrofit_apply_preserves_crlf_line_endings` PASSED.

**Break attempts:**

| Case | Detector output | Verdict |
|---|---|---|
| Majority CRLF (3 CRLF + 1 LF) | `\r\n` | ✓ |
| Majority LF (1 CRLF + 3 LF) | `\n` | ✓ |
| Equal split (1+1) | `\n` | ✓ (sensible default — strict majority required for CRLF) |
| Single CRLF line | `\r\n` | ✓ |
| Single LF line | `\n` | ✓ |
| **Old Mac `\r` only** | `\n` | **Limitation:** detector counts only `\r\n` and `\n`-not-`\r\n`. Bare `\r` files would get LF inserted. Acceptable in 2026 (Old Mac classic is effectively extinct); document if you want absolute coverage. |
| Empty file | `\n` | ✓ |

Insert path was verified via the existing CRLF test (which exercises insert into a CRLF file). Both paths use the same `line_ending` variable.

---

### V6 — Surface Loader Issues (CB8) — **Resolved**

**Code under review:** `_loader_issues_to_warnings` at `retrofit.py:545-555` (issues → non-blocking `RetrofitWarning` with the loader's `code` and `message`); consumed at `:253` and folded into `plan.warnings`. JSON envelope emits warnings at `data.warnings[]` (L674, L761) AND at top-level `warnings` (L676, L766) via `emit_command_success`.

**Test:** `test_retrofit_apply_surfaces_loader_issues_without_blocking_valid_files` PASSED.

**Break attempts:**

1. **Two-file scenario (one parse-broken, one valid).** Test asserts `parse_error` appears in both `payload["warnings"]` and `payload["data"]["warnings"]`, AND that the valid file still has its `tags` edit in `payload["data"]["files"][...].edits`. ✓
2. **JSON path location.** Confirmed: top-level `warnings[]` *and* nested `data.warnings[]`. Both contain `path`, `field`, `reason_code`, `reason_message`, `blocking`. ✓
3. **Non-blocking semantics.** `_loader_issues_to_warnings` hardcodes `blocking=False`, so the apply path's `blocking_warnings()` filter at `:173` does not abort. Valid files commit normally. ✓

---

### V7 — `RetrofitEdit.path` and Noop Reporting (CS1) — **Resolved**

**Code under review:** `RetrofitEdit` dataclass at `retrofit.py:62-68` has `path: Path` as the first field. `_file_plan_to_json` at `:636-650` emits `{"path": str(file_plan.path), "edits": [...], "warnings": [...]}` for *every* `FilePlan` — noop or not — and the per-edit dict also serializes `str(edit.path)`.

**Tests:** `test_retrofit_apply_noop_when_fields_match_computed` and `test_retrofit_dry_run_json_envelope` PASSED.

**Break attempts:**

1. **All four action paths populate `path`.** Insert (L478-486), replace (L460-468), remove (L441-449), and noop (FilePlan with `edits=[]`) all carry the document path. The dataclass requires it. ✓
2. **JSON serialization.** `str(edit.path)` and `str(file_plan.path)` produce POSIX strings (verified by the noop test's `endswith("stable.md")` assertion). No `PosixPath(...)` repr leaks. ✓
3. **Noop file in `data.files[]`.** The noop test explicitly does `next(item for item in data["files"] if item["path"].endswith("stable.md"))` and asserts `edits == []`. Confirms in-sync files appear with empty edits array. ✓

---

### V8 — Documentation (CB7 + CS4) — **Resolved**

1. **`_split_frontmatter` limitation comment** present at `frontmatter_edit.py:71-73`:
   > Known limitation: if a YAML block scalar value contains a literal "---" on its own line, this split will be incorrect.

   I confirmed this limitation experimentally: a frontmatter with `desc: |\n  Section A\n  ---\n  Section B` truncates at the literal `---`. The comment correctly characterizes it as a "shared limitation with all `---`-based frontmatter parsers." ✓
2. **Release notes accurately describe abort behavior.** `docs/releases/v4.3.0.md:53`:
   > **Unpatchable frontmatter blocks apply for the batch.** Anchors, aliases, merge-derived target values, YAML tag syntax, block scalars, and duplicate top-level keys raise blocking warnings and abort `--apply`.

   Wording is "abort," not "skip." Per-field behavior at L41-44 also accurately documents the new `remove` action ("Present but canonical value is empty → removes the stale field block"). ✓

---

## New Issues Found During Verification

**None blocking.** One minor observation worth noting (not a regression, not in scope of the 7 fixes):

- **V5 Old Mac `\r`-only files default to LF.** `_detect_dominant_line_ending` only counts `\r\n` and `\n`-not-`\r\n`; bare `\r` line endings (Mac OS Classic, pre-2001) flow through as LF after a retrofit edit. This is acceptable for any modern repo and is consistent with how Python's `splitlines(keepends=True)` handles them. If you want absolute fidelity, add a `\r`-only counter to the detector. Deferrable.

All requested retrofit fixes (CB1-CB4, CB6, CB8), the documentation item for CB7, the unanimous should-fix CS1, and the documentation should-fix CS4 are properly addressed. The verified test suites are passing. Approve for merge.
