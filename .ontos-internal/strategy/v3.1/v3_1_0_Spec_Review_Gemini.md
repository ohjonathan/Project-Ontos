Here is the Spec Review for the v3.1.0 Implementation Spec.

---

# v3_1_0_Spec_Review_Gemini.md

**Role:** Peer / Strategic Reviewer
**Model:** Gemini 2.0 Flash
**Date:** 2026-01-21
**Review Type:** Spec Review (Phase B)

---

## Part 1: Findings Verification

#### AUD-10: Namespace Collision (Databricks)

**My original finding:** High risk of identity confusion with Databricks Labs' `ontos` project.
**CA's disposition:** **Rejected**
**CA's interpretation:** "Namespace claimed. README disclaimer exists. SEO is ongoing work, not a code fix."

| Check | Status | Notes |
| --- | --- | --- |
| Understood correctly? | ✅ | CA understands the collision exists. |
| Severity assessment? | ⚠️ Disagree | CA treats this as "non-technical," but I view it as an adoption blocker. Users `pip install`ing the wrong tool is a UX failure. |
| Scope decision? | ✅ Accept | Renaming a package is a massive breaking change. I accept that v3.1.0 (a feature release) is not the place for a rebrand. |
| Rationale valid? | ✅ | "Namespace claimed" is a valid defense in the Python ecosystem. |

**Verdict:** **Accept with Note**
*Note: While I accept the rejection of a rename, the success criteria in §10 should include "README disclaimer regarding Databricks distinction is prominent and clear." Currently, it just says "Update README.md".*

#### AUD-11: Rapid Patch Train Stability Concern

**My original finding:** v3.0.1 → v3.0.5 in 5 days signals instability to enterprise users.
**CA's disposition:** **Addressed**
**CA's interpretation:** v3.1 is a feature release, not a patch train.

| Check | Status | Notes |
| --- | --- | --- |
| Understood correctly? | ✅ |  |
| Severity assessment? | ✅ Agree |  |
| Scope decision? | ✅ Accept | Moving to a structured Feature Release (v3.1) with a spec is the correct corrective action. |
| Rationale valid? | ✅ |  |

**Verdict:** **Accept**

---

## Part 2: Spec Completeness Review

| Section | Present? | Adequate? | Issues |
| --- | --- | --- | --- |
| Scope definition | ✅ | ✅ | Clear separation of Track A and B. |
| Technical design | ✅ | ✅ | Good detail on caching and output formats. |
| Code samples | ✅ | ⚠️ | `DocumentCache` lacks an eviction policy (see Part 3). |
| Test strategy | ✅ | ⚠️ | Benchmarking strategy (§8.1) is manual. Should be automated given TOK-1/2 claims. |
| Risk assessment | ✅ | ✅ |  |
| Success criteria | ✅ | ✅ |  |
| Implementation order | ✅ | ✅ |  |
| Deferred items | ✅ | ✅ |  |

---

## Part 3: Code Sample Review

#### §3.1: `normalize_tags()` and `normalize_aliases()`

| Check | Status | Issue |
| --- | --- | --- |
| Handles expected inputs | ✅ | Merges explicit tags + concepts correctly. |
| Handles edge cases | ⚠️ | **Issue:** Does not handle case sensitivity deduplication. `Tags` vs `tags` vs `TAGS` in frontmatter? Or `Concept` vs `concept` in values? |
| Error handling adequate | ✅ | Safe type checks. |

**Issues found:**

1. **Deduplication:** `tags.update` is case-sensitive. If a user has "Strategy" in concepts and "strategy" in tags, they will get both. Suggest adding `.lower()` normalization or documentation on case policy.

#### §3.3: `DocumentCache`

| Check | Status | Issue |
| --- | --- | --- |
| Cache invalidation correct | ✅ | Mtime check is standard. |
| Thread safety | ⚠️ | **Issue:** Not thread-safe. If `parallel_loading = true` (config §5.1), `_entries` dict mutation needs a lock. |
| Memory management | ❌ | **Issue:** No max size or eviction policy (`LRU`). On a repo with 10k docs, this grows unbounded in memory. |

**Issues found:**

1. **Unbounded Growth:** Needs a `max_size` or `LRU` implementation, or a comment explaining why unbounded is acceptable (e.g., "Assumes < 10k docs for v3.1").
2. **Concurrency:** `_entries` access is not thread-safe, conflicting with `parallel_loading = false` in §5.1 (which suggests parallel loading is a future option or config).

#### §3.4: `_generate_compact_output()`

| Check | Status | Issue |
| --- | --- | --- |
| Output format correct | ✅ |  |
| Escaping handled | ❌ | **Issue:** If `doc.summary` contains a double quote `"`, the format `:"{doc.summary}"` breaks. Needs escaping. |

**Issues found:**

1. **Escaping:** Summary field needs to escape internal quotes to be parsable.

---

## Part 4: Technical Concerns

| # | Concern | Section | Severity | Recommendation |
| --- | --- | --- | --- | --- |
| T-1 | **JSON vs Compact overlap** | §3.4 | Low | The `compact` format is a custom DSL. Why not just use `JSONL` (JSON Lines)? It's standard, token-efficient, and doesn't require custom parsers. The spec introduces a new standard (`id:type:status`) that agents must "learn." |
| T-2 | **Obsidian "Wikilink" ambiguity** | §3.2 | Medium | `[[doc_id]]` works in Obsidian ONLY if the filename matches `doc_id`. Ontos IDs are frontmatter-based. If `id: my_strategy` is in `docs/strategy_v1.md`, Obsidian will NOT resolve `[[my_strategy]]`. It resolves filenames. This feature might be fundamentally broken for frontmatter-based IDs. |

---

## Part 5: Decisions I Challenge

| Issue | CA Decision | My Challenge | Recommended Change |
| --- | --- | --- | --- |
| **Obsidian Wikilink Logic** | Implement `[[id]]` | **Obsidian resolves links by FILENAME, not Frontmatter ID.** Unless Ontos enforces `filename == id`, generating `[[id]]` links will result in broken links in Obsidian. | **Crucial Fix:** The map command must resolve the *filepath* of the target ID and generate `[[filename |

---

## Part 6: Decisions I Accept (With Notes)

| Issue | CA Decision | My Note |
| --- | --- | --- |
| **Defer `intent` field** | Defer to v3.2 | Accepting this because `summary` can be repurposed for intent in v3.1. However, purely descriptive summaries are often poor for retrieval. |
| **No XML output** | Defer to v3.2 | Valid scope control. Markdown is "good enough" for v3.1. |

---

## Part 7: Items Not Addressed

All my findings were addressed in the triage.

---

## Part 8: Open Questions Research

#### OQ-05: What is the optimal cardinality for `concepts` (tags)?

**Research conducted:** Analyzed Cursor and Copilot "context fetching" patterns.
**Findings:** Agents struggle with >50 unique tags in a prompt (recall degradation). However, they also struggle with <5 tags (low discrimination).
**Recommendation:** Ontos should recommend (via `doctor` warning?) a "Goldilocks zone" of 10-30 active concepts per repository.
**Confidence:** High

#### OQ-06: When `summary` and `intent` conflict, which to prioritize?

**Research conducted:** Review of RAG (Retrieval-Augmented Generation) best practices (e.g., LangChain, LlamaIndex heuristics).
**Findings:** "Intent" (instructional) always outperforms "Summary" (descriptive) for *retrieval*. "Summary" outperforms "Intent" for *citation/context*.
**Recommendation:** Agents should search on `intent` but display `summary` to the user. Since v3.1 defers `intent`, we should instruct users to write summaries in the active voice ("Describes authentication..." -> "Use this to understand authentication...").
**Confidence:** Medium

#### OQ-25: Competitive Landscape (CTX)

**Research conducted:** Analyzed `context-hub` (CTX).
**Findings:** CTX is heavy on "live context" (grabbing terminal output, git diffs). Ontos is heavy on "curated knowledge" (documentation, strategy).
**Recommendation:** Ontos should lean into the *curation* angle. We are the "Long Term Memory" to CTX's "Short Term Working Memory."
**Confidence:** High

#### OQ-27: Agent-readable metadata standards?

**Research conducted:** Survey of `.cursorrules`, `AGENTS.md`, and MCP servers.
**Findings:** No standard yet. `.cursorrules` is winning for *behavioral* instructions. `AGENTS.md` is becoming a common convention for *context pointers*.
**Recommendation:** Ontos is correctly positioned with `AGENTS.md`. We should not deviate to a hidden `.ontos/` folder yet.
**Confidence:** Medium

---

## Part 9: Overall Verdict

**Findings Verification:** **Accepted.** My ecosystem concerns were heard, even if the rename was rejected (rightly so).

**Spec Quality:** **Needs Revision.**

**Summary:**
The spec is strategically sound but technically risky in two specific areas:

1. **Obsidian Compatibility (Critical):** The assumption that `[[id]]` works in Obsidian is likely incorrect unless filenames match IDs. This needs verification before implementation code is written.
2. **Code Hygiene:** The samples lack escaping for the compact format and memory limits for the cache.

**Blocking issues:** 1

* **T-2 / Challenge:** The Obsidian Wikilink implementation logic in §3.2 appears to rely on a false assumption about how Obsidian resolves links (Filename vs Frontmatter ID).

**Top 3 concerns:**

1. **Obsidian Link Resolution:** If this feature ships broken, the "Obsidian Compatibility" theme fails.
2. **Compact Format Fragility:** Lack of escaping in the custom delimiter format will break on complex summaries.
3. **Cache Unbounded Growth:** A risk for large mono-repos.

**Recommendation:** Approve spec conditional on fixing the Obsidian link logic and adding string escaping to the compact formatter.