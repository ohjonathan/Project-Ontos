# v3.1.0 Implementation Spec Review (Phase B)

**Project:** Ontos v3.1.0  
**Phase:** B (Spec Review)  
**Role:** Review Board member (Adversarial / edge-cases focus)  
**Model:** GPT-5.2 Thinking  
**Date:** January 21, 2026

**Inputs reviewed:**
- v3.1.0 Implementation Spec v1.1
- v3.1.0 Audit Triage (Chief Architect)
- v3.1.0 Research Review (Chief Architect)

---

## Part 1: Findings Verification

> Note: My “original finding” summaries are reconstructed from the Audit Triage issue-extraction list, since my standalone v3.0.5 review doc was not included in the provided inputs.

#### AUD-01: Wrapper command architecture causes drift and tech debt

**My original finding:** Wrapper commands created a second implementation surface that drifts from core logic and increases maintenance and bug risk.  
**CA's disposition:** Addressed in v3.1.0 (Track B native migrations).  
**CA's interpretation:** Wrapper pattern is a root cause; migrate wrappers to native implementations.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Matches the core concern: wrapper debt drives drift. |
| Severity assessment? | ✅ Agree | Architectural debt + user-facing inconsistency is high leverage to fix. |
| Scope decision? | ✅ Accept | Track B directly targets the debt within a 4-week window. |
| Rationale valid? | ✅ | “Remove wrappers” is the most direct mitigation. |

**Verdict:** Accept with note  
- **Note:** Track B sections still need explicit “behavior parity” definitions per command, otherwise you can remove wrappers and still ship drift.

---

#### AUD-02: Wrapper commands do not honor `.ontos.toml`

**My original finding:** Some wrappers bypassed config resolution, producing behavior different from native commands.  
**CA's disposition:** Addressed in v3.1.0 (Track B native migrations).  
**CA's interpretation:** Fix by making wrappers native and reusing canonical config load.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Correctly identified: config resolution path divergence. |
| Severity assessment? | ✅ Agree | Silent config ignore is a credibility killer. |
| Scope decision? | ✅ Accept | Migration is the clean fix. |
| Rationale valid? | ✅ | Centralizing config load is the right approach. |

**Verdict:** Accept with note  
- **Note:** Spec should explicitly require an integration test: create `.ontos.toml`, run each migrated command, assert config is observed.

---

#### AUD-03: `scaffold` is broken / not functional

**My original finding:** `scaffold` failed or produced incorrect outputs in common usage, undermining trust.  
**CA's disposition:** Addressed in v3.1.0 (CMD-1: scaffold marked CRITICAL).  
**CA's interpretation:** Re-implement scaffold natively and ensure parity.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Clear. |
| Severity assessment? | ✅ Agree | A broken “starter” command poisons first impressions. |
| Scope decision? | ✅ Accept | Marking CRITICAL is appropriate. |
| Rationale valid? | ✅ | Fixing is aligned with release theme (compat + credibility). |

**Verdict:** Accept with note  
- **Note:** The spec is thin on expected scaffold outputs, directory structure, and overwrite behavior. This is implementable only if the dev already knows the intended scaffold contract.

---

#### AUD-04: Wrapper commands accept inconsistent flags / behavior

**My original finding:** Flag sets and semantics varied across commands due to wrapper drift.  
**CA's disposition:** Addressed in v3.1.0 (native migrations + shared option classes).  
**CA's interpretation:** Standardize options through core dataclasses and shared parsing.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Yes. |
| Severity assessment? | ✅ Agree | UX inconsistency causes support burden. |
| Scope decision? | ✅ Accept | Fits Track B. |
| Rationale valid? | ✅ | Shared option classes reduce drift. |

**Verdict:** Accept with note  
- **Note:** “Consistent flags” should be documented as an explicit matrix in the spec to avoid re-introducing inconsistency during implementation.

---

#### AUD-05: MCP implementation incomplete / unclear value

**My original finding:** MCP story was incomplete, confusing, and at risk of being “half-shipped.”  
**CA's disposition:** Deferred (Appendix A).  
**CA's interpretation:** Defer to v4 when there’s time to do it properly.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Accurately captured as incompleteness/credibility risk. |
| Severity assessment? | ✅ Agree | Half-features are a long-term drag. |
| Scope decision? | ✅ Accept | Deferral is reasonable under 4-week constraint. |
| Rationale valid? | ✅ | “Do it properly later” is better than incremental confusion now. |

**Verdict:** Accept

---

#### AUD-06: Config fragmentation and loading ambiguity

**My original finding:** Config sourcing and precedence were unclear, leading to non-deterministic behavior.  
**CA's disposition:** Deferred (Appendix A).  
**CA's interpretation:** Needs a dedicated design pass; not safe in v3.1.0.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Yes. |
| Severity assessment? | ✅ Agree | Config ambiguity becomes “bugs you can’t reproduce.” |
| Scope decision? | ✅ Accept | Too risky to refactor config under a feature window. |
| Rationale valid? | ✅ | Sensible to defer. |

**Verdict:** Accept with note  
- **Note:** Track B migrations must still use the *existing* config resolution path consistently, even if fragmentation is deferred.

---

#### AUD-07: Magic defaults reduce debuggability

**My original finding:** Users can’t tell which paths, configs, and defaults were chosen, making issues hard to debug.  
**CA's disposition:** Addressed partially via `doctor -v` (DOC-1).  
**CA's interpretation:** Add verbose doctor output to surface effective settings.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Doctor verbosity targets the right pain point. |
| Severity assessment? | ✅ Agree | Debuggability is a trust feature. |
| Scope decision? | ✅ Accept | Adds clarity without breaking CLI behavior. |
| Rationale valid? | ✅ | Good low-risk fix. |

**Verdict:** Accept with note  
- **Note:** Make `doctor -v` output testable. A stable set of keys and formatting matters if this becomes a support tool.

---

#### AUD-08: AGENTS.md / agent-doc activation is fragile

**My original finding:** Agent documentation was not reliably discoverable or applied, risking “it works on my machine.”  
**CA's disposition:** Deferred (Appendix A).  
**CA's interpretation:** Needs more research and a stronger contract.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Yes. |
| Severity assessment? | ⚠️ Disagree | I view this as medium-high if agent workflows are a core audience. |
| Scope decision? | ✅ Accept | OK to defer if Track A still improves Obsidian + token efficiency. |
| Rationale valid? | ✅ | Reasonable. |

**Verdict:** Accept with note  
- **Note:** Even deferred, align naming with ecosystem reality: Codex reads `AGENTS.md`; other tools use other files. Consolidate guidance to avoid user confusion.

---

#### AUD-09: `sdist` tests failing / packaging trust issues

**My original finding:** Packaging or distribution tests failing undermines release credibility.  
**CA's disposition:** Deferred (Appendix A).  
**CA's interpretation:** Needs a focused packaging hardening pass.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Clear. |
| Severity assessment? | ✅ Agree | Shipping broken distributions damages adoption. |
| Scope decision? | ⚠️ Challenge | This is the one deferral that can still hurt v3.1 adoption immediately. |
| Rationale valid? | ✅ | It’s believable that fixing properly needs time. |

**Verdict:** Accept with note (non-blocking)  
- **Note:** At minimum, add a CI gate that asserts `pip install .` from sdist works before releasing v3.1.0.

---

#### AUD-10: Namespace collision risk (“ontos” is a crowded name)

**My original finding:** Package name may collide with other libraries or user expectations.  
**CA's disposition:** Deferred (Appendix A).  
**CA's interpretation:** Not actionable within v3.1 scope.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Yes. |
| Severity assessment? | ✅ Agree | Real risk, but mostly branding/discoverability. |
| Scope decision? | ✅ Accept | Renaming is breaking and out of scope. |
| Rationale valid? | ✅ | Fine. |

**Verdict:** Accept with note  
- **Note:** Mitigate short-term via clearer project description and install docs, even if name stays.

---

#### AUD-11: Rapid patch train / version inflation risk

**My original finding:** Too-frequent releases can look unstable and reduce user trust.  
**CA's disposition:** Addressed (changelog and release framing).  
**CA's interpretation:** Slow the train and set clearer release expectations.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Yes. |
| Severity assessment? | ✅ Agree | Perception matters. |
| Scope decision? | ✅ Accept | This is mostly process + comms. |
| Rationale valid? | ✅ | OK. |

**Verdict:** Accept

---

#### AUD-12: Frontmatter parsing edge cases (BOM / whitespace / delimiters)

**My original finding:** Current YAML/frontmatter parsing breaks on common real-world edge cases, creating hard-to-diagnose failures.  
**CA's disposition:** Partially addressed (ERR-1 better errors + “known limitations”), deeper fixes deferred.  
**CA's interpretation:** Treat as rare; document limitations and add error clarity.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ⚠️ | The issue is not just “bad YAML.” It’s “valid docs fail due to strict delimiter assumptions.” |
| Severity assessment? | ⚠️ Disagree | For Obsidian compatibility, this becomes higher severity than framed. |
| Scope decision? | ⚠️ Challenge | A minimal fix for BOM + leading whitespace is small and aligned with Track A. |
| Rationale valid? | ❌ | “Rare” is the weak link if Obsidian vaults and common static-site frontmatter patterns are in scope. |

**Verdict:** Challenge (narrow, implementation-focused)

**What was misunderstood:**
- The breaking cases are not exotic YAML. They’re file-level realities: BOM, whitespace, and frontmatter delimiter placement.

**Correct interpretation:**
- “Obsidian compatibility” implies you will encounter vault files with properties/frontmatter in the wild, plus migrations from older keys.

**Recommended action:**
- Implement a **lenient frontmatter detector** at least for `--obsidian` mode or `yaml_mode = lenient`:
  - Strip UTF-8 BOM safely on read.
  - Allow leading whitespace/newlines before the first `---` delimiter.
  - Support Obsidian’s modern `tags`/`aliases` and optionally accept deprecated `tag`/`alias` as input.

---

#### AUD-13: Documentation mismatch vs current behavior

**My original finding:** Docs did not match actual CLI behavior, leading to user confusion.  
**CA's disposition:** Deferred (Appendix A).  
**CA's interpretation:** Needs docs pass once behavior stabilizes post-migration.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Yes. |
| Severity assessment? | ✅ Agree | Adoption friction. |
| Scope decision? | ✅ Accept | Docs can churn during command migrations. |
| Rationale valid? | ✅ | Fine. |

**Verdict:** Accept with note  
- **Note:** Still add “minimum doc” updates for newly introduced flags (`--obsidian`, `--compact`) or users will guess.

---

#### AUD-14: `SessionContext` responsibilities unclear

**My original finding:** SessionContext was doing too much and lacked a clean boundary, increasing coupling.  
**CA's disposition:** Deferred (Appendix A).  
**CA's interpretation:** Architectural refactor, target v4.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Yes. |
| Severity assessment? | ✅ Agree | Medium-high but not required for v3.1 scope. |
| Scope decision? | ✅ Accept | Out of 4-week window. |
| Rationale valid? | ✅ | Reasonable. |

**Verdict:** Accept

---

#### AUD-15: Missing / inconsistent type hints

**My original finding:** Lack of types increases regressions and slows refactors.  
**CA's disposition:** Deferred (Appendix A).  
**CA's interpretation:** Not a release theme item.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Yes. |
| Severity assessment? | ✅ Agree | But secondary to user-facing fixes. |
| Scope decision? | ✅ Accept | Good candidate for a hardening release. |
| Rationale valid? | ✅ | Fine. |

**Verdict:** Accept

---

#### AUD-16: No dry-run mode for destructive ops

**My original finding:** Commands that write/modify files need a dry-run mode to reduce foot-guns.  
**CA's disposition:** Deferred (Appendix A), partial mitigations (e.g., `--diff-only` in migrate).  
**CA's interpretation:** Safety is desirable but wide-scope across commands.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | Yes. |
| Severity assessment? | ✅ Agree | Strong UX win, but broad to implement. |
| Scope decision? | ✅ Accept | Deferral is reasonable under constraints. |
| Rationale valid? | ✅ | Yes. |

**Verdict:** Accept with note  
- **Note:** If `migrate` is in-scope, it should at least support “no-write” flows consistently (preview + exit code contract).

---

## Part 2: Spec Completeness Review

| Section | Present? | Adequate? | Issues |
|---------|----------|-----------|--------|
| Scope definition | ✅ | ✅ | Scope overview is clear; priorities are visible. |
| Technical design | ✅ | ⚠️ | Track A is mostly implementable; TOK-3 `--filter` lacks a dedicated design section. Track B is too high-level for parity-critical migrations. |
| Code samples | ✅ | ⚠️ | Several samples are illustrative but not runnable. At least one sample (`parse_frontmatter_safe`) is a stub and returns an undefined variable in its current form. |
| Test strategy | ✅ | ⚠️ | Verification Protocol exists but lacks expected outputs, golden fixtures, and explicit backward-compat parity tests for migrated commands. |
| Risk assessment | ✅ | ⚠️ | Risks listed but shallow. Missing risks: delimiter/BOM realities, compact output escaping, cache scope mismatch. |
| Success criteria | ✅ | ⚠️ | Measurable, but a few are mismatched to current design (cache timing and `--filter`). |
| Implementation order | ✅ | ✅ | Order is sensible. |
| Deferred items | ✅ | ✅ | Appendix A is present and aligned with triage. |

---

## Part 3: Code Sample Review

### §3.1: `normalize_tags()` and `normalize_aliases()`

| Check | Status | Issue |
|-------|--------|-------|
| Handles expected inputs | ✅ | List inputs are handled; output is sorted and deduped. |
| Handles edge cases | ⚠️ | Does not normalize `#tag` prefixes, whitespace, or deprecated `tag`/`alias` keys. Converts non-strings to strings silently. |
| Error handling adequate | ⚠️ | Silent coercion may hide malformed frontmatter. Consider strict/lenient modes. |
| Type safety | ⚠️ | Signatures imply `list[str]`, but input can be `Any`. Consider `Sequence[str] | str | None` or validate explicitly. |

**Issues found:**
- Recommend supporting deprecated Obsidian keys (`tag`, `alias`) as inputs during migration periods.
- Decide on normalization rules: strip leading `#`, trim whitespace, and optionally preserve user case or enforce consistent casing.
- Consider preserving user ordering when possible. Sorting is stable, but it changes perceived order.

---

### §3.3: `DocumentCache`

| Check | Status | Issue |
|-------|--------|-------|
| Cache invalidation correct | ⚠️ | mtime-based invalidation is OK but can miss changes on low-res filesystems or with preserved mtimes. |
| Thread safety (if relevant) | N/A | CLI appears single-threaded. |
| Memory management | ⚠️ | Unbounded growth for large vaults. No eviction or size cap described. |
| Edge cases handled | ⚠️ | Symlinks, large files, and read failures should be handled predictably. |

**Issues found:**
- The spec’s success criteria imply cross-run speedups, but the sample cache is in-memory. Align expectations or add an optional disk cache.
- Add a max-entries or max-bytes limit, or at least document the current behavior.

---

### §3.4: `_generate_compact_output()`

| Check | Status | Issue |
|-------|--------|-------|
| Output format correct | ⚠️ | Format is human readable but not robustly machine-parseable. |
| Escaping handled | ❌ | Summary is quoted but not escaped. Newlines, quotes, and colons will break consumers. |
| Edge cases handled | ⚠️ | Missing handling for empty summary, multiline summary, or exotic characters. |

**Issues found:**
- Either define an escaping rule (e.g., JSON string escaping for the summary field) or pick a safer format:
  - JSON Lines (`.jsonl`) for maximal robustness, or
  - TSV with strict escaping rules, or
  - YAML block scalars for summaries if you want readability.
- If the goal is token efficiency for LLMs, define the canonical “compact prompt” format and keep it stable.

---

### Other code samples (§3.2, §3.5, Track B stubs)

- **§3.2 MapOptions vs argparse:** `--compact` uses `nargs="?"` and can produce a string (`"rich"`) but `MapOptions.compact` is typed as `bool`. This is a likely implementation bug or at least a spec ambiguity.
- **§3.5 YAML error handling sample:** `parse_frontmatter_safe()` is presented as a code sample but is incomplete, and in its current form would not run. That’s fine as pseudocode, but label it as pseudocode and specify the missing pieces explicitly.
- **Track B (CMD-1..CMD-7):** The spec defines option dataclasses and file placements, but not the behavioral contract. Parity work needs explicit examples and edge-case definitions.

---

## Part 4: Technical Concerns

| # | Concern | Section | Severity | Recommendation |
|---|---------|---------|----------|----------------|
| T-1 | `--compact` value typing ambiguity (`bool` vs `"rich"`) | §3.4 | High | Introduce `CompactMode = off|basic|rich` or parse to `(compact: bool, compact_rich: bool)` explicitly. |
| T-2 | Compact output lacks escaping and can break downstream parsing | §3.4 | High | Define escaping or switch to JSONL. Add tests for quotes/newlines/colons. |
| T-3 | Cache design likely doesn’t meet stated timing goals | §3.3 / §10 | Med | Clarify “within-run cache” vs disk cache. If disk cache desired, specify key, invalidation, size cap, and location. |
| T-4 | Obsidian compatibility needs deprecated key handling and strict list formats | §3.1 / §3.2 | Med | Support input keys `tag`/`alias` optionally, while always outputting `tags`/`aliases` lists. |
| T-5 | Frontmatter delimiter/BOM/whitespace assumptions are treated as “known limitations” but impact real vaults | §3.5 | High | Implement lenient detection under `yaml_mode=lenient` and/or `--obsidian`. |
| T-6 | TOK-3 `--filter` is in scope and success criteria but lacks technical design | §2 / §10 | High | Add a dedicated section specifying filter syntax, matching semantics, and examples. |
| T-7 | Track B migrations lack behavioral parity contract, risking accidental breaking changes | §4 / §8 | High | Add “golden behavior” fixtures and a parity checklist per command: flags, exit codes, stdout/stderr, file writes. |
| T-8 | Backward compatibility notes requested by the review framework are not clearly separated in the spec | Whole doc | Low | Add a short “Backward compatibility notes” section explicitly listing what must not change per command. |

---

## Part 5: Decisions I Challenge

| Issue | CA Decision | My Challenge | Recommended Change |
|-------|-------------|--------------|-------------------|
| AUD-12 (frontmatter edge cases) | Treat as rare; document limitations; defer deeper fix | Obsidian compatibility makes these cases common enough that “known limitation” is a UX cliff | Implement BOM stripping and allow leading whitespace before delimiter under `--obsidian` or `yaml_mode=lenient` in v3.1.0 |
| Cache success criteria | Implicitly expects big speedups | Current cache appears in-memory only; repeat-run speedups won’t happen | Either scope down success criterion to “within-run,” or add a disk cache design |
| TOK-3 `--filter` | In scope + success criteria | No technical section describing behavior; devs will guess | Add §3.7: filter syntax + matching semantics + examples + tests |

---

## Part 6: Decisions I Accept (With Notes)

| Issue | CA Decision | My Note |
|-------|-------------|---------|
| AUD-05 MCP incomplete | Deferred | Correct call. Don’t ship partial MCP. |
| AUD-06 config fragmentation | Deferred | Fine, but ensure migrations don’t create *new* config paths. |
| AUD-14 SessionContext boundary | Deferred | Needs a real refactor window. |
| AUD-15 type hints | Deferred | Good hardening candidate. |
| AUD-16 dry-run | Deferred | OK, but `migrate` should have a crisp no-write contract now. |
| AUD-09 sdist test failures | Deferred | Non-blocking, but add a release gate. |

---

## Part 7: Items Not Addressed

All audit items appear in the triage and are either mapped into v3.1.0 work or deferred in Appendix A.  
**However:** TOK-3 `--filter` is scoped and in success criteria but lacks a design section, which is effectively “not addressed” at the implementation-spec level.

---

## Part 8: Open Questions Research

#### OQ-01: What compact format yields the best token reduction in practice?

**Research conducted:** Reviewed agent-tool patterns and typical consumption behavior; proposed measurement methodology.  
**Findings:** Token reduction claims are highly tokenizer-dependent. A format that is “visually smaller” can still tokenize poorly.  
**Recommendation:** Treat this as an empirical problem:
- Pick 3–5 candidate formats (current `:` format, TSV, JSONL, YAML-min, markdown bullets).
- Benchmark on 20–50 representative vault docs and 5 prompts (map-only, map+doc, query prompts).
- Measure tokens for your target models and publish the results as part of release notes.  
**Confidence:** Medium

---

#### OQ-02: Should compact output be rich or minimal by default?

**Research conducted:** Evaluated how agents consume summaries vs identifiers.  
**Findings:** Most agents benefit from stable identifiers and a short semantic hook. But long summaries can dominate tokens and distract.  
**Recommendation:** Default to **minimal** compact output. Keep “rich” as an opt-in (`--compact=rich`) and cap summary length deterministically.  
**Confidence:** Medium

---

#### OQ-05: What agent-doc file conventions should Ontos support?

**Research conducted:** Checked major tool conventions: Codex reads `AGENTS.md`; Cursor supports project “Rules”; broader ecosystem is converging on predictable instruction files.  
**Findings:** There is no single universal standard, but `AGENTS.md` is explicitly supported by Codex and has an emerging cross-project spec.  
**Recommendation:** Keep Ontos opinionated:
- Produce `AGENTS.md` as the canonical agent-doc output.
- Optionally generate secondary formats behind flags (e.g., `.cursorrules`, `CLAUDE.md`) but avoid making the default confusing.  
**Confidence:** High

---

#### OQ-06: Where should agent instructions live and how should they be layered?

**Research conducted:** Reviewed guidance that agent instruction files can be layered by directory.  
**Findings:** Layering by directory is useful when you have subprojects or mixed languages; global-only instructions become noisy.  
**Recommendation:** Support:
- Root `AGENTS.md` (global).
- Optional folder-level `AGENTS.md` overrides for subtrees.  
**Confidence:** Medium

---

#### OQ-13: Should caching be in-memory only or persisted?

**Research conducted:** Compared success criteria with current cache concept.  
**Findings:** CLI tools benefit little from in-memory caches unless the same file is parsed multiple times within a single run. Persisted caches are what unlock “repeat command runs faster.”  
**Recommendation:** Decide explicitly:
- If you only need within-run de-duplication, say so and tune success criteria.
- If you want repeat-run speedups, specify a disk cache (location, keying, invalidation, size cap).  
**Confidence:** High

---

#### OQ-14: How should cache invalidation work?

**Research conducted:** Evaluated mtime vs hash tradeoffs.  
**Findings:** `mtime` is fast but imperfect. Hashing is robust but expensive on large files. Hybrid is common: mtime+size, and hash only on mismatch or for smaller files.  
**Recommendation:** Start with mtime+size. Expose a `--no-cache` escape hatch and document limitations.  
**Confidence:** Medium

---

#### OQ-21: Should frontmatter parsing accept whitespace/BOM before delimiters?

**Research conducted:** Reviewed frontmatter conventions and documented BOM pitfalls; checked Obsidian property expectations.  
**Findings:** Many tools expect frontmatter at the top of the file, delimited by `---`. Some ecosystems warn that BOM breaks parsing. Obsidian also has strict expectations for certain properties and dropped deprecated keys in newer versions.  
**Recommendation:** Add `yaml_mode=lenient` behavior:
- Strip UTF-8 BOM when decoding.
- Skip leading whitespace/newlines before delimiter.
- Always parse modern keys; optionally accept deprecated keys as inputs.  
**Confidence:** High

---

#### OQ-22: Should Ontos support deprecated Obsidian properties (`tag`, `alias`)?

**Research conducted:** Checked Obsidian properties documentation for deprecation behavior.  
**Findings:** Obsidian dropped `tag` and `alias` properties in favor of `tags` and `aliases`. Existing vaults and migrations can still contain the old keys.  
**Recommendation:** For compatibility, accept `tag`/`alias` as *inputs* during parsing but emit only `tags`/`aliases` as outputs. Log a warning in `doctor -v` or `--verbose` when deprecated keys are detected.  
**Confidence:** High

---

#### OQ-23: What delimiter rules should Ontos follow for non-Obsidian frontmatter?

**Research conducted:** Reviewed common doc tool conventions.  
**Findings:** Docusaurus and Jekyll style frontmatter is `---` at top of file. Tools vary in how strict they are about placement, but “top of file” is the dominant convention.  
**Recommendation:** Default `yaml_mode=standard` should require delimiter at file start. `lenient` can tolerate whitespace/BOM, but don’t accept “frontmatter blocks in the middle of a file” by default.  
**Confidence:** Medium

---

## Part 9: Overall Verdict

**Findings Verification:** Mostly accepted; 1 challenged (AUD-12) due to “rare” framing and Obsidian-scope conflict.

**Spec Quality:** Needs revision before implementation is “safe.” The core direction is right, but there are a few gaps that will force developers to guess, which is how breaking changes sneak in.

**Summary:**
- The CA generally understood the audit items and made scope-appropriate decisions.
- Track A is close to implementable but has two sharp edges: frontmatter realities and compact output robustness.
- Track B migration intent is correct, but the spec needs parity contracts and tests to avoid subtle regressions.

**Blocking issues:** 3  
1) TOK-3 `--filter` is scoped but not designed  
2) Compact output escaping / format contract  
3) Frontmatter leniency decision for Obsidian compatibility

**Top 3 concerns:**
1. Frontmatter “known limitations” will feel like bugs in Obsidian mode unless leniency is implemented.
2. Compact output as currently specified will break on real summaries unless escaping rules are defined.
3. Command migrations without parity fixtures risk breaking “no breaking changes” constraint accidentally.

---

**Review signed by:**
- **Role:** Adversarial Reviewer  
- **Model:** GPT-5.2 Thinking  
- **Date:** January 21, 2026  
- **Review Type:** Spec Review (Phase B)
