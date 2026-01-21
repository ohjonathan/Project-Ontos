---
id: v3_1_0_spec_review_consolidation
type: review
status: complete
depends_on: [v3_1_0_spec_review_claude, v3_1_0_spec_review_gemini, v3_1_0_spec_review_gpt5]
concepts: [consolidation, spec-review, v3.1.0]
---

# v3.1.0 Spec Review Consolidation

**Project:** Ontos v3.1.0  
**Phase:** B.2 (Consolidation)  
**Date:** 2026-01-21  
**Consolidator:** Antigravity (Gemini 2.5 Pro)

---

## Part 1: Verdict Summary

| Reviewer | Role | Verdict | Blocking Issues | Challenges to CA Decisions |
|----------|------|---------|-----------------|---------------------------|
| Claude | Alignment/Technical | CONDITIONAL APPROVAL | 1 | 0 |
| GPT-5.2 Thinking | Adversarial | NEEDS REVISION | 3 | 1 (AUD-12) |
| Gemini | Peer/Strategic | NEEDS REVISION | 1 | 1 (Obsidian Wikilink) |

**Consensus:** 0/3 Approve unconditionally  
**Overall Status:** Needs revision — 3-4 blocking issues must be addressed before implementation

---

## Part 2: v3.0.5 Findings Resolution

| Original Finding | CA Disposition | Claude | GPT-5.2 | Gemini | Consensus |
|------------------|----------------|--------|---------|--------|-----------|
| Legacy wrapper debt | Track B addresses (CMD-1–CMD-7) | ✅ | ✅ | ✅ | Accepted |
| MCP incompleteness | Defer to v4.0 | ✅ | ✅ | N/A | Accepted |
| Config fragmentation | Defer + existing path consistency | ✅ | ✅ | N/A | Accepted |
| Magic defaults | DOC-1 addresses (`doctor -v`) | ✅ | ✅ | N/A | Accepted |
| Frontmatter edge cases | ERR-1 partial + defer | ✅ | ⚠️ | N/A | Disputed |
| Schema versioning | Defer to v3.2 | ✅ | N/A | N/A | Accepted |
| SessionContext scope | Defer to v3.2 | ✅ | ✅ | N/A | Accepted |
| Test sdist failures | Defer to v3.2 | ✅ | ⚠️ | N/A | Accepted (with note) |
| Namespace collision | Not in scope | ✅ | ✅ | ✅ | Accepted |
| Patch train stability | Addressed via v3.1 framing | ✅ | ✅ | ✅ | Accepted |

**Disputed items requiring CA response:**

| Finding | Disputed By | Nature of Dispute |
|---------|-------------|-------------------|
| AUD-12: Frontmatter edge cases | GPT-5.2 | CA treats BOM/whitespace as "rare," but GPT-5.2 argues Obsidian compatibility makes these common. Recommends lenient mode implementation in v3.1.0 rather than deferral. |

---

## Part 3: Blocking Issues

Issues that reviewers explicitly marked as must-fix before implementation:

| # | Issue | Flagged By | Section | Impact | Suggested Fix |
|---|-------|------------|---------|--------|---------------|
| B-1 | **Quote escaping in compact output** | Claude, Gemini, GPT-5.2 | §3.4 | Malformed output when summaries contain `"` | Escape quotes/newlines or switch to JSONL |
| B-2 | **Obsidian Wikilink logic** | Gemini | §3.2 | `[[id]]` links broken — Obsidian resolves by filename, not frontmatter ID | Generate `[[filename\|id]]` or enforce filename==id |
| B-3 | **TOK-3 `--filter` lacks design** | GPT-5.2 | §2/§10 | In scope and success criteria but no technical section | Add §3.7: filter syntax, matching semantics, examples |
| B-4 | **Frontmatter leniency for Obsidian** | GPT-5.2 | §3.5 | BOM/whitespace issues break real Obsidian vaults | Implement `yaml_mode=lenient` or `--obsidian` leniency |

**Total blocking issues:** 4 (B-1 is same issue flagged by all 3 reviewers)

---

## Part 4: Code Sample Issues

| Code Sample | Section | Issue | Severity | Flagged By |
|-------------|---------|-------|----------|------------|
| `normalize_tags()` | §3.1 | No case-sensitivity deduplication; numeric tags silently ignored; no Obsidian-safe validation | Low-Med | Claude, Gemini, GPT-5.2 |
| `normalize_aliases()` | §3.1 | Same issues as tags; deprecated `tag`/`alias` keys not supported | Low-Med | GPT-5.2 |
| `DocumentCache` | §3.3 | Unbounded growth (no max_entries); not thread-safe if parallel_loading enabled; no `--no-cache` flag | Medium | Claude, Gemini, GPT-5.2 |
| `_generate_compact_output()` | §3.4 | **Quotes not escaped — CRITICAL** | High | Claude, Gemini, GPT-5.2 |
| `FrontmatterParseError` | §3.5 | No severity level field | Low | Claude |
| `doctor -v` | §3.6 | `ctx.config_path` undefined on SessionContext | Medium | Claude |
| `MapOptions` | §3.2/§3.4 | `--compact` typing ambiguity: `nargs="?"` can be string `"rich"` but typed as `bool` | High | GPT-5.2 |
| `parse_frontmatter_safe()` | §3.5 | Incomplete/non-runnable code; should be labeled as pseudocode | Low | GPT-5.2 |

**Code samples requiring fixes before implementation:** 3 (B-1 compact output, config_path, --compact typing)

---

## Part 5: Technical Concerns (Non-Blocking)

| # | Concern | Flagged By | Section | Recommendation |
|---|---------|------------|---------|----------------|
| T-1 | JSON vs Compact overlap — custom DSL vs JSONL standard | Gemini | §3.4 | Consider JSONL for robustness |
| T-2 | Cache success criteria implies cross-run speedups, but cache is in-memory only | GPT-5.2, Gemini | §3.3/§10 | Clarify "within-run" or add disk cache design |
| T-3 | No cache size limit documented | Claude, Gemini, GPT-5.2 | §3.3 | Add `cache_max_entries` config or document expectation |
| T-4 | No `--no-cache` flag | Claude | §3.3 | Add for debugging |
| T-5 | Obsidian deprecated keys (`tag`/`alias`) not handled | GPT-5.2 | §3.1 | Accept as input, emit modern keys only |
| T-6 | Track B migrations lack parity contracts | GPT-5.2 | §4/§8 | Add golden fixtures and parity checklist per command |
| T-7 | Test strategy lacks expected outputs and golden fixtures | GPT-5.2 | §8 | Add specific test structure |
| T-8 | Benchmarking strategy is manual; should be automated | Gemini | §8.1 | Automate given TOK-1/2 claims |
| T-9 | MCP competitive window risk | Claude | Appendix A | Consider accelerating to v3.2 |

---

## Part 6: Spec Completeness Assessment

| Aspect | Claude | GPT-5.2 | Gemini | Consensus |
|--------|--------|---------|--------|-----------|
| Scope definition | ✅ | ✅ | ✅ | Adequate |
| Technical design | ✅ | ⚠️ (Track B high-level, TOK-3 missing) | ✅ | Needs work |
| Code samples | ⚠️ | ⚠️ | ⚠️ | Needs work |
| Test strategy | ⚠️ | ⚠️ | ⚠️ | Needs work |
| Risk assessment | ✅ | ⚠️ | ✅ | Adequate |
| Success criteria | ✅ | ⚠️ (cache timing mismatch) | ✅ | Needs work |
| Deferred items | ✅ | ✅ | ✅ | Adequate |

---

## Part 7: Agreement Analysis

**Strong Agreement (All 3 reviewers):**

| Topic | Finding |
|-------|---------|
| Compact output escaping | All flagged quotes in summaries breaking the `:id:type:status:"summary"` format |
| Cache unbounded growth | All noted lack of max_entries or eviction policy |
| Track B direction correct | All accept native migrations as the right approach |
| MCP deferral reasonable | All accept v4.0 deferral (Claude notes competitive pressure) |
| Namespace collision accepted | All accept deferral; renaming too disruptive |
| Patch train addressed | All accept v3.1 feature release framing |

**Disagreement:**

| Topic | Claude | GPT-5.2 | Gemini | Consolidation Note |
|-------|--------|---------|--------|-------------------|
| Frontmatter edge cases (AUD-12) | Accept deferral | Challenge — implement leniency in v3.1 | N/A | CA must decide: defer vs implement lenient mode |
| Obsidian Wikilink logic | Not flagged | Not flagged | **BLOCKING** — fundamental assumption wrong | CA must clarify how Obsidian resolves links |
| TOK-3 `--filter` | Not flagged | **BLOCKING** — no design | Not flagged | CA must add design section or descope |
| Cache success criteria | Not flagged | Challenge — in-memory won't meet timing goals | Flagged as issue | CA must clarify within-run vs cross-run |

---

## Part 8: Open Questions Research Summary

| Question ID | Contributors | Key Findings | Actionable for v3.1.0? |
|-------------|--------------|--------------|------------------------|
| OQ-01 (compact format tokens) | GPT-5.2 | Token reduction is tokenizer-dependent; empirical testing needed | Partial — design stable format |
| OQ-02 (rich vs minimal default) | GPT-5.2 | Default to minimal; keep "rich" as opt-in | Yes — spec can adopt |
| OQ-05 (concept cardinality) | Gemini | 10-30 concepts per repo is "Goldilocks zone" | Yes — doctor warning? |
| OQ-06 (summary vs intent) | Gemini | Intent better for retrieval, summary for citation | Partial — guide users |
| OQ-13 (cache persistence) | Claude, GPT-5.2 | In-memory OK; disk cache only if parse time >500ms | Yes — clarify scope |
| OQ-14 (cache invalidation) | GPT-5.2 | mtime+size is good default; add `--no-cache` | Yes — adopt |
| OQ-17 (schema version handling) | Claude | Fail loudly with upgrade command | Yes — enhance error |
| OQ-18 (schema coercion) | Claude | Do NOT auto-upgrade; explicit `migrate` correct | Yes — confirmed |
| OQ-21 (BOM/whitespace) | GPT-5.2 | Implement lenient mode | Disputed — see B-4 |
| OQ-22 (deprecated Obsidian keys) | GPT-5.2 | Accept `tag`/`alias` as input, emit modern keys | Yes — adopt |
| OQ-25 (competitive landscape) | Gemini | Position as "long-term memory" vs CTX "short-term" | Strategy note |
| OQ-27 (agent metadata standards) | Gemini | `AGENTS.md` is emerging standard; stay course | Confirmed |

**High-value contributions:**
1. **GPT-5.2 OQ-21:** BOM/whitespace handling is not "rare" for Obsidian users — implement leniency
2. **Claude OQ-17:** Schema version mismatch error should include `pip install --upgrade ontos`
3. **Gemini OQ-05:** Recommend 10-30 concepts; add doctor warning for cardinality
4. **GPT-5.2 OQ-01:** Don't assume compact format saves tokens — benchmark it
5. **Gemini OQ-27:** `AGENTS.md` is the right bet; don't deviate to hidden folders

**Questions still unanswered:**
- None explicitly listed as unanswered across reviews

---

## Part 9: Missing Items

| Missing Item | Flagged By | Why Needed | Priority |
|--------------|------------|------------|----------|
| `--filter` technical design (§3.7) | GPT-5.2 | In scope but no spec — devs will guess | High |
| Backward compatibility notes section | GPT-5.2 | Needs explicit listing of what must not change | Medium |
| Parity contracts for Track B commands | GPT-5.2 | Risk of accidental breaking changes | High |
| Scaffold expected outputs/directory structure | GPT-5.2 | CMD-1 spec too thin to implement | Medium |
| Consistent flags matrix for commands | GPT-5.2 | Avoid re-introducing inconsistency | Medium |
| Databricks distinction disclaimer prominence | Gemini | Success criteria should note this | Low |

---

## Part 10: Required Actions for Chief Architect

**Priority 1 — Must address before implementation authorization:**

| # | Action | Addresses |
|---|--------|-----------|
| 1 | Add quote/newline escaping logic to `_generate_compact_output()` in §3.4 | B-1 |
| 2 | Clarify Obsidian wikilink logic in §3.2 — explain how `[[id]]` resolves or change to `[[filename\|display]]` | B-2 |
| 3 | Add §3.7 for `--filter`: define syntax, matching semantics, examples | B-3 |
| 4 | Decide: implement `yaml_mode=lenient` in v3.1.0 OR provide rationale for deferral (AUD-12 dispute) | B-4 / Disputed |
| 5 | Fix `--compact` typing: define `CompactMode = off|basic|rich` or `(compact: bool, compact_rich: bool)` | T-1 (GPT-5.2) |
| 6 | Add `config_path` to SessionContext or clarify source in §3.6 | Claude T-2 |

**Priority 2 — Should address, can proceed if deferred:**

| # | Action | Addresses |
|---|--------|-----------|
| 1 | Clarify cache scope in success criteria: "within-run" vs "cross-run" | T-2, T-3 |
| 2 | Add `--no-cache` flag to bypass cache | T-4 (Claude) |
| 3 | Support deprecated Obsidian keys (`tag`/`alias`) as input | T-5 (GPT-5.2) |
| 4 | Add behavioral parity contracts for Track B commands | T-6 (GPT-5.2) |

**Priority 3 — Consider for spec update:**

| # | Action | Addresses |
|---|--------|-----------|
| 1 | Add explicit backward compatibility notes section | GPT-5.2 suggestion |
| 2 | Define scaffold expected outputs and directory structure | GPT-5.2 suggestion |
| 3 | Document flags matrix for command consistency | GPT-5.2 suggestion |
| 4 | Add cache_max_entries config option | Common suggestion |

---

## Part 11: Decision Summary

**Spec Status:** Needs CA Response Before Implementation

**Blocking issue count:** 4 (deduplicated)

**Disputed triage decisions:** 1 (AUD-12: frontmatter leniency)

**Code sample fixes required:** 3 critical

**Chief Architect must:**
1. Respond to **4 blocking issues** (B-1, B-2, B-3, B-4)
2. Address **1 disputed triage decision** (AUD-12 — GPT-5.2 challenge)
3. Fix or justify **3 code sample issues** (compact escaping, config_path, --compact typing)
4. Decide on **1 missing design section** (§3.7 `--filter`)
5. Update spec to **v1.2** after addressing issues

**Estimated CA response effort:** Medium (half day)
- Most fixes are spec clarifications and code sample updates
- Obsidian wikilink logic may require research/verification
- `--filter` design section is net new work

---

## Appendix: Issue Cross-Reference

| Issue ID | Description | Claude | GPT-5.2 | Gemini |
|----------|-------------|--------|---------|--------|
| B-1 | Compact output escaping | T-1 | T-2 | §3.4 issue |
| B-2 | Obsidian wikilink logic | — | — | Challenge |
| B-3 | `--filter` design missing | — | T-6 | — |
| B-4 | Frontmatter leniency | Accept | Challenge | — |
| T-1 | Compact typing ambiguity | — | T-1 | — |
| T-2 | config_path undefined | T-2 | — | — |
| T-3 | Cache unbounded | T-3 | T-3 | §3.3 issue |
| T-4 | No --no-cache | T-4 | — | — |

---

*Review Consolidation — Phase B.2*
*Consolidator: Antigravity (Gemini 2.5 Pro)*
*Date: 2026-01-21*
