# v3.1.0 Implementation Spec Verification Review (Round 2)

**Project:** Ontos v3.1.0  
**Phase:** B.4 (Verification Review)  
**Role:** Review Board member (Adversarial / edge-cases focus)  
**Model:** GPT-5.2 Thinking  
**Date:** January 21, 2026  

**Docs reviewed:**
- `v3_1_0_Chief_Architect_Response.md`
- `v3_1_0_Implementation_Spec_v1.2.md`
- My Round 1 review: `v3_1_0_Spec_Review_GPT-5.2_Thinking.md`

---

## Part 1: Blocking Issue Verification

#### B-1: Quote/newline escaping and typing clarity in compact output

**What I flagged:** Compact output breaks if summaries contain quotes/newlines. `--compact` typing was ambiguous.  
**CA's response:** Accept  
**CA's fix:** Add escaping rules and a `CompactMode` enum, update CLI parsing.

**Verification:**

| Check | Status |
|------|--------|
| Issue understood correctly? | ✅ |
| Fix addresses root cause? | ✅ |
| Fix implemented correctly in spec? | ⚠️ |
| No new issues introduced? | ✅ |

**Verdict:** ⚠️ Partially resolved

**Remaining problem:**
- The spec’s code sample still contains ellipses inside the code block. The escaping logic is described correctly, but the snippet is not copy-paste implementable as written.

**Recommended action:**
- Replace the `...` in §3.4 with the full, runnable `_generate_compact_output()` snippet (at least the full `summary_safe = ...` chain). Keep the “illustrative” disclaimer only where needed.

---

#### B-2: Obsidian wikilink logic must be filename-based

**What I flagged:** Obsidian resolves links by filename; ID-only links are wrong for vault behavior.  
**CA's response:** Accept  
**CA's fix:** `[[filename|id]]` link formatting with filename-based resolution.

**Verification:**

| Check | Status |
|------|--------|
| Issue understood correctly? | ✅ |
| Fix addresses root cause? | ✅ |
| Fix implemented correctly in spec? | ✅ |
| No new issues introduced? | ✅ |

**Verdict:** ✅ Resolved

---

#### B-3: `--filter` needed a real design section

**What I flagged:** `--filter` was in scope and success criteria but had no design, forcing devs to guess.  
**CA's response:** Accept  
**CA's fix:** Add §3.7: syntax and matching logic.

**Verification:**

| Check | Status |
|------|--------|
| Issue understood correctly? | ✅ |
| Fix addresses root cause? | ⚠️ |
| Fix implemented correctly in spec? | ❌ |
| No new issues introduced? | ✅ |

**Verdict:** ❌ Not resolved

**Remaining problem:**
- §3.7 exists, but it is not complete enough to implement without guessing:
  - Grammar uses `EXPR EXPR` with no explicit operator definition.
  - No examples are actually present in the spec body.
  - Quoting and tokenization rules are not defined.
  - The code sample is truncated with `...`, so it does not pin down parsing.

**Recommended action:**
- Update §3.7 to match the CA response intent, minimally:
  - Explicit semantics: “multiple fields = AND, multiple values = OR”.
  - At least 6 concrete examples (type, status, concept, id glob, multi-field AND, multi-value OR).
  - Tokenization rules: split on spaces unless inside quotes; commas separate values; escaping in quotes is out-of-scope for v3.1.
  - Explicit error behavior: unknown field, empty value, unmatched quote.

---

#### B-4: Obsidian frontmatter leniency for BOM and leading whitespace

**What I flagged:** Obsidian compatibility will hit BOM/whitespace cases; “known limitations” would feel like bugs.  
**CA's response:** Accept (revise AUD-12 approach)  
**CA's fix:** In `--obsidian` mode, strip UTF-8 BOM and allow leading whitespace/newlines before delimiter.

**Verification:**

| Check | Status |
|------|--------|
| Issue understood correctly? | ✅ |
| Fix addresses root cause? | ✅ |
| Fix implemented correctly in spec? | ⚠️ |
| No new issues introduced? | ⚠️ |

**Verdict:** ⚠️ Partially resolved

**Remaining problem:**
- The sample `read_file_lenient()` returns the fully `lstrip()`’d text when it finds frontmatter. That changes the file content returned to callers, which could unintentionally change summaries or downstream behavior in `--obsidian` mode.

**Recommended action:**
- Keep lenient *detection* but do not mutate the returned content:
  - Detect delimiter after whitespace, then parse frontmatter using offsets, but preserve original text for non-frontmatter content.

---

## Part 2: Code Sample Fix Verification

#### §3.2: Wikilink resolution

**Original issue:** Wikilinks not aligned with Obsidian filename resolution.  
**CA's fix:** `_format_doc_link()` uses `doc_path.stem` and emits `[[filename|id]]`.

**Verification:**
- [x] Fix is syntactically correct
- [x] Fix addresses the edge case
- [x] No new edge cases introduced
- [x] Code is implementable as written

**Verdict:** ✅ Fixed

---

#### §3.3: DocumentCache adds `--no-cache`

**Original issue:** No escape hatch for cache debugging; unclear invalidation expectations.  
**CA's fix:** Add `--no-cache` flag and clarify cache scope as within-run.

**Verification:**
- [x] Fix is syntactically correct
- [x] Fix addresses the edge case
- [x] No new edge cases introduced
- [x] Code is implementable as written

**Verdict:** ✅ Fixed

---

#### §3.4: Compact output escaping and CompactMode

**Original issue:** Compact output breaks on quotes/newlines; typing ambiguous.  
**CA's fix:** `CompactMode` enum; escape backslashes/quotes/newlines; CLI flag returns strings.

**Verification:**
- [ ] Fix is syntactically correct
- [x] Fix addresses the edge case
- [x] No new edge cases introduced
- [x] Code is implementable as written

**Verdict:** ⚠️ Partial

**Why partial:** The code block contains ellipses, so it’s not syntactically correct as a snippet, even though the logic is clear.

---

#### §3.6: config_path resolution in doctor verbose

**Original issue:** config_path resolution unclear and easy to misreport.  
**CA's fix:** `_get_config_path()` checks `.ontos.toml` in repo root; prints resolved paths.

**Verification:**
- [x] Fix is syntactically correct
- [x] Fix addresses the edge case
- [x] No new edge cases introduced
- [x] Code is implementable as written

**Verdict:** ✅ Fixed

---

## Part 3: New Section Review

#### §3.7: Filter Flag Design (NEW)

| Check | Status | Notes |
|-------|--------|-------|
| Syntax is clear and unambiguous | ❌ | Grammar is underspecified and missing operators. |
| Examples cover common use cases | ❌ | No concrete examples included in spec body. |
| Edge cases documented | ⚠️ | Unknown fields and quoting behavior not specified. |
| Implementable without questions | ❌ | Parser behavior must be guessed. |

**Issues found:**
- This section is still too incomplete to treat as an implementation blueprint.

---

#### §4.8: Behavioral Parity Contracts (NEW)

| Check | Status | Notes |
|-------|--------|-------|
| Parity requirements are testable | ✅ | Golden fixtures per command is a workable approach. |
| Coverage is comprehensive | ⚠️ | Covers big items, but needs clarity on acceptable diffs (whitespace, ordering). |
| Deviation handling is clear | ⚠️ | “Identical or superset” is vague without defining equivalence. |

**Issues found:**
- Exit code “2 = user abort” must match legacy or it should be stated as “if legacy uses it.” Otherwise it risks creating a parity mismatch.

---

#### §11.1: Backward Compatibility Notes (NEW)

| Check | Status | Notes |
|-------|--------|-------|
| Breaking changes identified | ✅ | “Must NOT change” list is useful. |
| Migration path clear | ⚠️ | Very short; ok for this phase. |
| User impact documented | ⚠️ | Adequate but minimal. |

**Issues found:**
- Mentions `--json` as an available flag for output changes, but `--json` is not designed elsewhere in v3.1.2 spec. Either remove the mention or explicitly confirm it is already an existing flag.

---

#### §4.1: Scaffold Expected Outputs (Expanded)

| Check | Status | Notes |
|-------|--------|-------|
| Output format specified | ⚠️ | Shows canonical frontmatter block; good. |
| Edge cases covered | ⚠️ | Skips existing frontmatter; mentions dry-run. Missing collision/overwrite rules. |
| Implementable without questions | ⚠️ | Still includes `...` placeholders; needs a bit more specificity. |

**Issues found:**
- Specify overwrite behavior and ID collision handling:
  - what happens if `id` already exists in repo
  - whether to prompt, auto-suffix, or error
  - whether `--dry-run` shows exact diffs

---

## Part 4: Research Integration Verification

| Question | CA Action | Correctly Integrated? | Notes |
|----------|-----------|----------------------|-------|
| OQ-02 | Integrate (compact default) | ✅ | `--compact` defaults to BASIC when flag provided; rich is opt-in. |
| OQ-05 | Implementation note (cardinality) | ❌ | Only marked answered in Appendix C; not reflected in any design constraints. |
| OQ-13 | Integrate (cache scope) | ✅ | Success criteria now explicitly say within-run only. |
| OQ-14 | Integrate (--no-cache) | ✅ | `--no-cache` flag added and listed in success criteria. |
| OQ-17 | Integrate (schema error) | ✅ | Schema version error message added in §3.5. |

---

## Part 5: Disputed Decision Verification

#### AUD-12: Frontmatter Edge Cases

**Original disposition:** Accept risk and defer to v3.2  
**Your challenge:** Obsidian scope makes BOM/whitespace common enough for v3.1  
**CA's revision:** Partial implementation in v3.1 (`--obsidian` leniency for BOM/whitespace)

**Verification:**

| Check | Status |
|------|--------|
| Revision addresses my concern? | ✅ |
| Implementation is adequate? | ⚠️ |
| Remaining deferral is acceptable? | ✅ |

**Verdict:** ⚠️ Partially satisfied

**Note:** The direction is right. The only concern is avoiding content mutation as a side effect of lenient detection.

---

## Part 6: New Issues (Critical Only)

| Issue | Section | Severity | Description |
|-------|---------|----------|-------------|
| None |  |  |  |

---

## Part 7: Deferred Items Review

| Deferred Item | Target | Acceptable? | Notes |
|---------------|--------|-------------|-------|
| CODE-01: Case normalization | v3.2 | ✅ | Fine to defer; needs user expectation input. |
| CODE-02: Cache max_entries | v3.2 | ✅ | Within-run cache makes it less urgent. |
| CODE-03: Deprecated Obsidian keys | v3.2 | ✅ | Acceptable as long as BOM/whitespace is handled now. |
| CODE-04: Full yaml_mode=lenient | v3.2 | ✅ | Partial `--obsidian` leniency is adequate for v3.1. |
| CODE-05: Flags matrix | v3.2 | ✅ | Useful, but parity contracts + fixtures cover the main risk in v3.1. |

---

## Part 8: Overall Verdict

**Round 1 Issues Resolution:**

| Category | Total | Resolved | Partial | Unresolved |
|----------|-------|----------|---------|------------|
| Blocking issues | 4 | 2 | 2 | 1 |
| Code sample fixes | 4 | 3 | 1 | 0 |
| Disputed decisions | 1 | 0 | 1 | 0 |

**New Sections Quality:**

| Section | Status |
|---------|--------|
| §3.7 Filter design | ❌ Blocking |
| §4.8 Parity contracts | ✅ Adequate (with notes) |
| §11.1 Backward compat | ✅ Adequate (with notes) |
| §4.1 Scaffold outputs | ⚠️ Needs work (not blocking) |

**Final Verdict:** REQUEST FURTHER REVISION

**Summary:**
- v1.2 fixes B-2 and the cache scope concern cleanly.
- B-1 and B-4 are directionally correct but still have spec-level implementation sharp edges due to ellipses and content mutation risk.
- B-3 remains a blocker: §3.7 is not complete enough to implement without guessing, and CA response claims examples exist but they are not present in the spec.

**Blocking issues remaining:** 1 (B-3: §3.7 filter design completeness)

**Implementation recommendation:**
- [ ] Proceed with implementation
- [ ] Proceed with noted concerns
- [x] Requires another revision cycle

---

**Review signed by:**
- **Role:** Adversarial Reviewer  
- **Model:** GPT-5.2 Thinking  
- **Date:** January 21, 2026  
- **Review Type:** Verification Review (Phase B.4)
