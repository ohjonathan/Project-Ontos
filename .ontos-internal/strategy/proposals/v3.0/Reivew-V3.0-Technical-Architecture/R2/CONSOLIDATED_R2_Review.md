# Ontos v3.0 Architecture Review: Round 2 Consolidation

**Generated:** 2026-01-12
**Reviews Consolidated:** 4 Peer Architects
**Architecture Version:** 1.1 / 1.3

---

## 1. Final Recommendation Summary

| Reviewer | Recommendation | Conditions (if any) |
|----------|----------------|---------------------|
| A (Codex/GPT-5.2) | Approve with Minor Changes | Fix hook PATH dependency, fix v2/v3 command mix, define file overwrite safety |
| B (Claude Opus 4.5) | **Approve** | None required |
| C (Gemini Architectural) | Approve with Minor Changes | Refactor paths.py status, add hook collision safety, define legacy cleanup |
| D (Gemini DeepThink) | Approve with Minor Changes | Add `find_project_root` interface, add `write_text_file` interface |

**Consensus:**
- Full Approve: 1/4
- Approve with Changes: 3/4
- Request Revision: 0/4

**Overall Verdict:** Ready for Implementation with Minor Fixes

---

## 2. New Feature 1: Global CLI + Local Data

### 2a. Quality Assessment

| Aspect | A | B | C | D | Consensus |
|--------|---|---|---|---|-----------|
| Correctness | ⚠️ Issues | ✅ Sound | ⚠️ Issues | ⚠️ Issues | 3/4 Minor Issues |
| Completeness | ⚠️ Gaps | ⚠️ Gaps | ⚠️ Gaps | ⚠️ Gaps | 4/4 Minor Gaps |
| Consistency | ⚠️ Minor | ✅ Aligned | ✅ Aligned | ✅ Aligned | 3/4 Aligned |
| Ready for Implementation | ⚠️ Minor fixes | ✅ Yes | ⚠️ Conditions | ⚠️ Minor fixes | 4/4 Ready |

**Overall Quality:** Strong — 3/4 rate Strong, 1/4 Adequate

### 2b. Issues Found

| Issue | Severity | Flagged By | Consensus |
|-------|----------|------------|-----------|
| Missing `find_project_root` interface | Major | A, C, D | 3/4 |
| Nested repository handling unclear | Minor | A, B, C | 3/4 |
| PATH dependency for shim hooks | Major | A, D | 2/4 |
| `paths.py` needs REFACTOR status | Major | C | 1/4 |
| `ontos` not in PATH edge case | Minor | B | 1/4 |

#### Missing `find_project_root` Interface — Flagged by: A, C, D (3/4)

**Problem:** Section 2.6 Constraint 8 ("Working Directory Independence") mandates CLI detect repo root by walking up from CWD. However, no module in Section 4 (`io/files.py` or `core/paths.py`) exposes a `find_project_root(cwd: Path) -> Path` function.

**Proposed Fixes:**
- A suggests: Define root resolution precedence: 1) nearest `.ontos.toml` walking up, 2) git root, 3) error with actionable hint
- C suggests: Add function to `io/files.py` interface spec
- D suggests: Explicitly specify `find_project_root(start_path: Path) -> Path` in `io/files.py`

---

#### PATH Dependency for Shim Hooks — Flagged by: A, D (2/4)

**Problem:** The Python shim hook invokes `ontos` by name, relying on it being in PATH. In GUI git clients, CI environments, and `--user` pip installs, PATH may not include the binary location.

**Proposed Fixes:**
- A suggests: Generate shim that runs `sys.executable -m ontos` using interpreter captured at `ontos init` time; keep warn/skip as fallback
- D suggests: Shim should fall back to `sys.executable -m ontos` if binary not found; especially important on Windows where `pip install` places binaries in non-PATH locations

---

#### `paths.py` Needs REFACTOR Status — Flagged by: C (1/4)

**Problem:** Constraint 2.6.8 mandates dynamic repo root detection. Section 3.2 lists `ontos/core/paths.py` as "EXISTS" (reuse as-is). The v2.x `paths.py` typically relies on `__file__` (script location) or static relative paths. Reusing it "as-is" in a global package will resolve to library installation path, not user's project path.

**Proposed Fix:**
- C suggests: Mark `paths.py` as "REFACTOR". It must be updated to accept an injected `repo_root` from `cli.py` → `OntosConfig`.

---

### 2c. Gaps Found

| Gap | Impact | Flagged By |
|-----|--------|------------|
| Uninstallation flow not specified | Low | A, B, D |
| Nested repo behavior undefined | Medium | A, B, C |
| Upgrade expectations unclear | Low | A |

#### Uninstallation Flow — Flagged by: A, B, D (3/4)

**What's Missing:** What happens when user does `pip uninstall ontos`? Global CLI removed, but per-repo data remains.

**Proposed Additions:**
- A suggests: Add `ontos deinit` or `ontos init --remove` to remove hooks and optionally archive `.ontos/`
- B suggests: Add Section 2.7 documenting that per-repo data remains; provide manual cleanup steps
- D suggests: Note that hooks will warn "ontos not found" but not error

---

### 2d. Risks Identified

| Risk | Likelihood | Impact | Flagged By |
|------|------------|--------|------------|
| Hook silently not enforcing due to PATH | High | High | A |
| Nested repo/submodule root mis-detection | Medium | High | A |
| CWD path confusion in output | Medium | High | C |
| PATH visibility on Windows | High | Medium | D |
| Global CLI version skew | Low | Low | B |

### 2e. Overall Assessment

**Quality:** Strong
**Ready for Implementation:** Yes with minor fixes

The Global CLI + Local Data model follows a proven pattern (git). All 4 reviewers agree it's implementation-ready with minor additions (find_project_root interface, nested repo handling).

---

## 3. New Feature 2: Consistent Ontos Activation

### 3a. Quality Assessment

| Aspect | A | B | C | D | Consensus |
|--------|---|---|---|---|-----------|
| Correctness | ⚠️ Issues | ✅ Sound | ⚠️ Issues | ⚠️ Issues | 3/4 Minor Issues |
| Completeness | ⚠️ Gaps | ⚠️ Gaps | ⚠️ Gaps | ⚠️ Gaps | 4/4 Gaps |
| Consistency | ❌ Conflicts | ⚠️ Minor | ✅ Aligned | ⚠️ Minor | Split |
| UX / "Just Works" | ❌ Tension | ✅ Aligned | ✅ Aligned | ✅ Aligned | 3/4 Aligned |
| Ready for Implementation | ❌ No | ⚠️ Minor fixes | ⚠️ Conditions | ⚠️ Minor fixes | 3/4 Ready |

**Overall Quality:** Adequate — Split assessment (A: Needs Work; B, C, D: Strong/Adequate)

**Note:** Reviewer A is notably more critical of this feature, rating it "Needs Work" and "Not Ready" while others rate it Strong/Adequate and Ready.

### 3b. Issues Found

| Issue | Severity | Flagged By | Consensus |
|-------|----------|------------|-----------|
| Mixed v2/v3 commands in export template | Major | A, C | 2/4 |
| File overwrite/collision safety unclear | Major | A, C | 2/4 |
| Hook collision safety not defined | Critical | C | 1/4 |
| Missing `write_text_file` interface | Major | D | 1/4 |
| Strategy Q2 deviation (export was deferred) | Minor | D | 1/4 |
| Template content too minimal | Minor | B | 1/4 |

#### Mixed v2/v3 Commands in Export Template — Flagged by: A, C (2/4)

**Problem:** The `ontos export` output includes both v2 (`python3 ontos.py map`) and v3 (`ontos map`) command guidance. v3.0 explicitly removes `ontos.py` from repos. Directing users to run non-existent scripts is confusing.

**Proposed Fixes:**
- A suggests: Output must be v3-only. Detect v2 vs v3 repo by presence of `.ontos.toml` and emit one correct instruction set
- C suggests: Remove v2 command reference entirely; only reference `ontos map`
- B agrees: v3 syntax only in template — if they can run `ontos export`, they have v3

---

#### File Overwrite/Collision Safety — Flagged by: A, C (2/4)

**Problem:** Behavior when `CLAUDE.md` or `AGENTS.md` already exists isn't fully specified. Silent overwrite would lose user customizations.

**Proposed Fixes:**
- A suggests: Default non-destructive: append "Ontos" block with markers, or create `.ontos/CLAUDE.ontos.md` and print include snippet. Only overwrite with `--force`
- C suggests: `init` must detect existing hooks. If found and not Ontos shim: warn and abort, or prompt to backup (`pre-push.old`)

---

#### Hook Collision Safety — Flagged by: C (1/4) — **Critical**

**Problem:** `commands/init.py` states it will "Install shim hooks" but doesn't specify behavior if hooks already exist (husky, pre-commit, user scripts). Silent overwrite causes data loss.

**Proposed Fix:**
- C suggests: `init` must detect existing hooks. If found and not Ontos shim: warn and abort, OR prompt to backup and overwrite

---

### 3c. Gaps Found

| Gap | Impact | Flagged By |
|-----|--------|------------|
| `init` + `export` integration unclear | Medium | B, D |
| Legacy `.ontos/` directory cleanup | Medium | C |
| Missing `write_text_file` in io/files.py | Medium | D |
| Upgrade/migration for activation artifacts | Medium | A |

#### `init` + `export` Integration — Flagged by: B, D (2/4)

**What's Missing:** Should `ontos init` automatically generate `CLAUDE.md`? If not, how do users discover `ontos export`?

**Proposed Additions:**
- B suggests: Add `--with-bootstrap` flag to `ontos init`, OR add tip in output: "Run `ontos export` for AI assistant integration"
- D suggests: `ontos init` should prompt or automatically run `export` to close bootstrap loop

---

#### Legacy `.ontos/` Cleanup — Flagged by: C (1/4)

**What's Missing:** Activation flow doesn't address cleaning up v2 `.ontos/` script directory. Users get "zombie scripts" in repo.

**Proposed Addition:**
- C suggests: Add step to `commands/init.py`: "Detect legacy `.ontos/` directory and prompt to remove/archive"

---

### 3d. UX Assessment

| Aspect | A | B | C | D | Consensus |
|--------|---|---|---|---|-----------|
| Friction Level | Medium | Low | Low | Low | 3/4 Low |
| Error Clarity | Unclear | Clear | Clear | Clear | 3/4 Clear |
| Progressive Disclosure | Yes | Yes | Yes | Yes | 4/4 Yes |

**UX Concerns Raised:**

- A: Two similar-sounding steps (`init` vs `export`) without a single canonical path creates confusion
- A: Collision handling for existing files needs explicit contract
- A: Mixed v2/v3 instructions will cause foot-guns

### 3e. Risks Identified

| Risk | Likelihood | Impact | Flagged By |
|------|------------|--------|------------|
| Hook overwrite destroys existing hooks | High | Critical | C |
| Users lose custom CLAUDE.md content | Medium | High | A |
| Agents follow wrong command (v2 vs v3) | High | Medium | A |
| "Activation" concept becomes muddled | Medium | Medium | A |
| Zombie scripts after partial migration | Medium | Medium | C |
| Windows shebang incompatibility | Medium | Medium | D |

### 3f. Overall Assessment

**Quality:** Adequate (split — A rates Needs Work)
**Ready for Implementation:** 3/4 Yes with fixes, 1/4 No

Reviewer A's "Needs Work / No" assessment focuses on UX issues: mixed commands, unclear file collision handling, and activation flow confusion. Other reviewers (B, C, D) rate the feature higher but still flag gaps.

---

## 4. Round 1 Feedback Verification

### 4a. Resolution Summary

| Category | Fully Resolved | Partially Resolved | Unresolved | Still Disagree |
|----------|----------------|--------------------|-----------:|----------------|
| Reviewer A's concerns | 3 | 2 | 1 | 1 |
| Reviewer B's concerns | 10 | 1 | 0 | 0 |
| Reviewer C's concerns | 4 | 0 | 0 | 0 |
| Reviewer D's concerns | 5 | 0 | 0 | 0 |
| **Total** | 22 | 3 | 1 | 1 |

### 4b. Critical Issues Resolution

| Critical Issue (Round 1) | Addressed? | How |
|--------------------------|------------|-----|
| Core purity violations (I/O in EXISTS modules) | ✅ Yes | Modules marked REFACTOR in Section 3.2 |
| Windows hook incompatibility | ✅ Yes | Python-based shim adopted (Section 8.1) |
| Circular config dependency | ✅ Yes | IoC pattern documented (Section 6.4) |
| Missing modules (`suggestions.py`, `tokens.py`) | ✅ Yes | Added to Sections 3.1 and 4.1 |
| Q5 version pinning not implemented | ✅ Yes | `required_version` field and checking logic added |
| Q4 confirmation not in data flow | ✅ Yes | Step 5 "CONFIRM CHANGES" added to Section 5.3 |
| Algorithm complexity (O(n²) cycle detection) | ✅ Yes | Constraint added: "Do NOT use path.index() pattern" |
| Line count gap (~500-750 unaccounted) | ✅ Yes | Acknowledged in Section 4.2 with explicit note |

**All 8 critical issues from Round 1 consolidation have been addressed.**

### 4c. Unresolved Issues

| Original Issue | Reviewer | Status | Notes |
|----------------|----------|--------|-------|
| Mixed v2/v3 commands in docs | A | Not addressed | Export template still contains both command variants |

### 4d. Persistent Disagreements

#### Hook PATH Dependency — Reviewer: A

**Round 1 Concern:** Hooks should be reliable without users "remembering" to have the right environment active.

**Architect's Response:** Add Python shim hook that calls `ontos` and skips with warning if missing.

**Why Reviewer Still Disagrees:** Skipping hook enforcement is the common case in GUI git clients and CI unless PATH is carefully managed. That violates "it just works" and makes enforcement non-deterministic.

**Reviewer's Recommendation:** Generate shim that runs `sys.executable -m ontos` using interpreter captured at `ontos init` time.

**Other Reviewers' Position:** D also flags PATH as a risk; B and C do not flag this as a concern.

---

#### Q8 Summarization Interface — Reviewer: C

**Round 1 Concern:** Q8 (Progressive Complexity) was marked CRITICAL in Strategy. Interface to execute summarization was missing from `core/graph.py`.

**Architect's Response:** "Defer... Address during implementation."

**Why Reviewer Still Disagrees:** Q8 is strategic critical path. Leaving API undefined risks logic leakage into Command layer, violating "Thin Command" principle.

**Reviewer's Recommendation:** Add placeholder signature to `core/graph.py` now: `def summarize_graph(graph: DependencyGraph, depth: int) -> DependencyGraph`.

**Other Reviewers' Position:** Not flagged by A, B, D.

---

### 4e. Improvement Assessment

| Reviewer | v1.0 → v1.3 Improvement |
|----------|-------------------------|
| A | Moderate |
| B | Significant |
| C | Significant |
| D | Significant |

**Consensus:** Significant improvement — 3/4 rate Significant, 1/4 rates Moderate

---

## 5. Regression Check Results

### 5a. Cross-Reference Issues

| Issue | Flagged By |
|-------|------------|
| Version mismatch: doc labeled v1.1 vs v1.3 in different places | A |
| Footer version wrong (1.2 vs 1.3) | B |
| `commands/export.py` missing from migration Phase 4 | B |

### 5b. New Inconsistencies

| Inconsistency | Flagged By |
|---------------|------------|
| Mixed v2/v3 command guidance in export template | A |
| Strategy Q2 conflict (export was deferred, now included) | D |
| Constraint 2.6.8 conflicts with paths.py EXISTS status | C |

### 5c. Integration Issues

| Issue | Flagged By |
|-------|------------|
| Export needs integration into migration story | A |
| `init` doesn't mention or prompt for `export` | B, D |

**Regression Summary:** Minor issues only — no critical regressions introduced

---

## 6. Reviewer Agreement Matrix

### 6a. Strong Agreement (3-4 reviewers aligned)

| Topic | Agreement | Who Agrees |
|-------|-----------|------------|
| Architecture significantly improved from v1.0 | Round 1 issues properly addressed | A, B, C, D |
| Global CLI + Local Data model is sound | Git-like pattern is correct approach | A, B, C, D |
| Python shim for hooks is correct | Solves Windows compatibility | A, B, C, D |
| Ready for implementation | With minor fixes | A, B, C, D |
| Missing `find_project_root` interface | Must be added to spec | A, C, D |
| Nested repo handling needs clarification | Document behavior | A, B, C |
| Uninstallation flow should be documented | User guidance needed | A, B, D |

### 6b. Split Opinions

| Topic | Position 1 | Position 2 |
|-------|------------|------------|
| Feature 2 readiness | A: "Needs Work / Not Ready" | B, C, D: "Strong/Adequate / Ready" |
| Hook PATH dependency severity | A, D: Major concern | B, C: Minor or not flagged |
| v2/v3 command mix severity | A: Critical (blocking) | B, C, D: Minor |

### 6c. Unique Concerns (only 1 reviewer)

| Concern | From | Validity Assessment |
|---------|------|---------------------|
| Q8 summarization interface gap | C | Valid — strategic feature without API spec |
| Hook collision safety (husky/pre-commit) | C | Valid — real scenario for many repos |
| `paths.py` REFACTOR status | C | Valid — architectural correctness |
| Template content too minimal | B | Valid but minor — can expand later |
| Strategy Q2 deviation | D | Valid but acceptable scope expansion |

---

## 7. Required Changes Before Implementation

### 7a. Critical (Must Fix)

| Issue | Feature/Section | Consensus | Source |
|-------|-----------------|-----------|--------|
| None identified as unanimous critical | — | — | — |

**Note:** No issue was flagged as Critical by 3+ reviewers. Reviewer A and C each flag items they consider critical, but without broader consensus.

### 7b. Major (Should Fix)

| Issue | Feature/Section | Consensus | Source |
|-------|-----------------|-----------|--------|
| Add `find_project_root` interface to `io/files.py` | Feature 1 | 3/4 | Round 2 |
| Document nested repository handling | Feature 1 | 3/4 | Round 2 |
| Define uninstallation flow | Feature 1 | 3/4 | Round 2 |
| Remove v2 command references from export template | Feature 2 | 2/4 | Round 2 |
| Define file overwrite/collision safety | Feature 2 | 2/4 | Round 2 |
| Add `write_text_file` to `io/files.py` | Feature 2 | 1/4 | Round 2 |
| Mark `paths.py` as REFACTOR | Feature 1 | 1/4 | Round 2 |

### 7c. Minor (Can Fix During Implementation)

| Issue | Feature/Section | Flagged By |
|-------|-----------------|------------|
| Expand bootstrap template content | Feature 2 | B |
| Standardize terminology (Session/Agent Bootstrap) | Feature 2 | B |
| Fix footer version (1.2 → 1.3) | Documentation | B |
| Add `export.py` to migration Phase 4 | Migration | B |
| Sync Strategy Q2 to reflect export inclusion | Strategy | D |
| Define Q8 `summarize_graph` interface | core/graph.py | C |
| Link `init` output to `export` command | Feature 2 | B, D |
| Add legacy `.ontos/` cleanup to `init` | Feature 2 | C |

### 7d. No Action Needed

- Global CLI distribution model — All reviewers aligned
- Python shim hook approach — All reviewers aligned
- IoC pattern for config loading — All reviewers confirmed
- ValidationOrchestrator pattern — No new issues
- Core module REFACTOR status — All reviewers confirmed

---

## 8. Conditions for Approval

From "Approve with Changes" reviewers (A, C, D):

| Condition | Required By | Blocking? |
|-----------|-------------|-----------|
| Fix hook PATH (use `sys.executable -m ontos`) | A | Yes |
| Fix export v2/v3 command mix | A | Yes |
| Define non-destructive file overwrite contract | A | Yes |
| Mark `paths.py` as REFACTOR | C | Yes |
| Add hook collision safety (warn/backup) | C | Yes |
| Define legacy `.ontos/` cleanup in `init` | C | Yes |
| Add `find_project_root` to `io/files.py` | D | Yes |
| Add `write_text_file` to `io/files.py` | D | Yes |
| Link `init` and `export` integration | D | Yes |

**Reviewer B (Full Approve):** No blocking conditions; only minor documentation suggestions.

---

## 9. Architecture Strengths (Round 2)

| Strength | Noted By |
|----------|----------|
| Git-like distribution model (global CLI + local data) | B, C, D |
| Python shim solution for cross-platform hooks | A, B, C, D |
| Comprehensive response to Round 1 feedback | A, B, C, D |
| Clear layering preserved (CLI → Commands → Core → IO) | B, C, D |
| Smart defaults in `ontos init` | C, D |
| Progressive disclosure (export is optional) | A, B, C, D |
| IoC pattern for config loading | B, C, D |
| Graceful degradation (hooks warn but don't block) | A, B |
| REFACTOR status for impure modules (architectural honesty) | C, D |

**Notable Improvement:** The decision to mark legacy modules as REFACTOR rather than EXISTS "saved the project from immediate technical debt" (D).

---

## 10. Decision-Ready Summary

### New Features Verdict

| Feature | Quality | Ready? | Critical Issues | Action Needed |
|---------|---------|--------|-----------------|---------------|
| Global CLI + Local Data | Strong | Yes | 0 | Add `find_project_root`, document nested repos, PATH fallback |
| Consistent Ontos Activation | Adequate | Mostly (3/4) | 0-1 | Fix v2/v3 mix, file safety, hook collision |

### Round 1 Resolution Verdict

| Assessment | Count |
|------------|-------|
| Concerns fully resolved | 22/26 (85%) |
| Concerns partially resolved | 3/26 |
| Concerns unresolved | 1/26 |
| Persistent disagreements | 2 (PATH, Q8) |
| Regressions introduced | 0 critical, 3 minor |

### Overall v1.3 Verdict

**Architecture Status:** Ready for Implementation with Minor Fixes

**Confidence Level:** High — 4/4 recommend approval (1 full, 3 with changes)

**Blocking Issues:** 0 unanimous; ~3 individual (PATH handling, file safety, find_project_root)

**Non-Blocking Issues:** ~8 (documentation, templates, interface specs)

---

## 11. Recommended Next Steps

**Verdict: Minor Fixes Needed**

### 1. Chief Architect Quick Fix Pass

Address the following before implementation begins (no full Round 3 needed):

**High Priority (3/4 consensus):**
1. Add `find_project_root(start_path: Path) -> Path` to `io/files.py` interface spec
2. Document nested repository handling (innermost `.ontos.toml` wins)
3. Add uninstallation guidance to documentation

**Medium Priority (2/4 consensus):**
4. Remove v2 command references from `ontos export` template (v3-only)
5. Define file overwrite contract: check existence, warn, require `--force`
6. Consider `sys.executable -m ontos` fallback in shim (A's persistent concern)

**Low Priority (1/4, still valid):**
7. Mark `paths.py` as REFACTOR in Section 3.2
8. Add hook collision safety (detect husky/pre-commit, warn or backup)
9. Add `write_text_file` to `io/files.py` if missing
10. Define Q8 `summarize_graph` signature in `core/graph.py`

### 2. Quick Verification

After fixes, a brief check (not full round) to confirm:
- Interface specs are complete
- No v2 references remain in v3 outputs
- File collision behavior is explicit

### 3. Proceed to Implementation

1. Begin Phase 0: Golden Master Testing
2. Begin Phase 1: Package Structure
3. Track Round 2 minor items in implementation backlog

---

*End of Round 2 Consolidated Review*

*Consolidation performed: 2026-01-12*
*Source reviews: A (Codex), B (Claude), C (Gemini Architectural), D (Gemini DeepThink)*
