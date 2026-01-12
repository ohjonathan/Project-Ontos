# Ontos v3.0 Architecture Review Consolidation

**Generated:** 2026-01-11
**Reviews Consolidated:** 4 Peer Architects

---

## 1. Review Summary Overview

| Reviewer | Overall Assessment | Recommendation | Critical Issues | Major Concerns | Minor Suggestions |
|----------|-------------------|----------------|-----------------|----------------|-------------------|
| A (Codex/GPT-5.2) | Adequate | Approve with Changes | 3 | 2 | 2 |
| B (Claude Opus 4.5) | Strong | Approve with Changes | 3 | 4 | 5 |
| C (Gemini Architectural) | Strong | Approve with Changes | 4 | 2 | 0 |
| D (Gemini DeepThink) | Strong | Approve with Changes | 3 | 0 | 0 |

**Consensus Summary:**
- Approvals: 0/4
- Requests for changes: 4/4
- Requests for revision: 0/4

**Unanimous verdict: Architecture is sound but requires changes before implementation.**

---

## 2. Decision Alignment Consolidation (Q1-Q13)

| Q# | Decision | A | B | C | D | Issues Found |
|----|----------|---|---|---|---|--------------|
| Q1 | JSON output mode | ✅ | ✅ | ✅ | ✅ | None |
| Q2 | Export templates (DEFERRED) | ✅ | ✅ | ✅ | ✅ | None |
| Q3 | Context slicing (DEFERRED) | ✅ | ✅ | ✅ | ✅ | None |
| Q4 | Git diff + require confirmation | ⚠️ | ⚠️ | ✅ | ⚠️ | A,B,D: Confirmation step not in data flow |
| Q5 | Version pinning (warn only) | ⚠️ | ❌ | ❌ | ⚠️ | All: Missing `required_version` field and checking logic |
| Q6 | Shim hooks | ✅ | ✅ | ⚠️ | ⚠️ | C,D: Windows incompatibility (`#!/bin/sh` only) |
| Q7 | MCP client docs (DEFERRED) | ⚠️ | ✅ | ✅ | ✅ | A: "docs-only" deliverable details missing |
| Q8 | Progressive complexity + auto-summary | ✅ | ✅ | ⚠️ | ✅ | C: Summarization interface missing from `core/graph.py` |
| Q9 | MCP security (DEFERRED) | ✅ | ✅ | ✅ | ✅ | None |
| Q10 | Pydantic optional for MCP | ✅ | ✅ | ✅ | ✅ | None |
| Q11 | Script reorg into package | ✅ | ✅ | ✅ | ✅ | None |
| Q12 | Python-first | ✅ | ✅ | ✅ | ✅ | None |
| Q13 | Markdown primary, JSON optional | ✅ | ✅ | ✅ | ✅ | None |

**Markers:**
- ✅ Correctly implemented / deferred
- ⚠️ Partially implemented (minor gap)
- ❌ Missing or incorrectly implemented

**Alignment Issues Requiring Attention:**

1. **Q4 (3/4 flagged):** Confirmation mechanism not represented in data flows
2. **Q5 (4/4 flagged):** Version pinning decision not implemented
3. **Q6 (2/4 flagged):** Windows support missing from shim hooks

---

## 3. Correctness Issues Consolidation

| Issue | Severity | A | B | C | D | Consensus | Location |
|-------|----------|---|---|---|---|-----------|----------|
| Core purity violations (I/O in "EXISTS" modules) | Critical | — | — | ✓ | ✓ | 2/4 | Sec 2.2, 12.1 |
| Circular config dependency (`core/` importing `io/`) | Critical | — | — | ✓ | — | 1/4 | Sec 1.4 vs 2.2 |
| Windows hook incompatibility | Critical | — | — | ✓ | ✓ | 2/4 | Sec 7.1 |
| Q4 confirmation not in data flow | Major | ✓ | ✓ | — | ✓ | 3/4 | Sec 4.3 |
| Scope creep in CLI commands | Major | ✓ | — | — | — | 1/4 | Sec 2.1 |
| `input()` in core blocks MCP | Major | — | — | ✓ | — | 1/4 | Sec 4.3 |
| Algorithm complexity mismatch (O(n²) cycle detection) | Major | — | — | — | ✓ | 1/4 | `core/graph.py` |
| ValidationOrchestrator missing curation method | Major | — | ✓ | — | — | 1/4 | Sec 3.1 |
| Config fragmentation not resolved | Major | — | ✓ | — | — | 1/4 | Sec 5 |
| Validation error model double severity | Minor | ✓ | — | — | — | 1/4 | `core/validation.py` |

### Critical Issues (must address)

#### Core Purity Violations — Flagged by: C, D (2/4)

**Problem:** Architecture lists modules like `staleness.py`, `proposals.py`, `history.py` as "EXISTS" (reuse as-is) in `core/`. In v2.9 codebase, these modules perform direct I/O (subprocess git calls, file reads). Moving them to `core/` without refactoring violates the "Functional Core" principle immediately.

**Location:** Section 2.2 vs Section 1.3 (Principles)

**Proposed Fixes:**
- C suggests: Add "Purification" phase to migration. Logic must accept data arguments (DTOs) rather than fetching data.
- D suggests: Mark these modules as "REFACTOR" in Sec 2.2/12.1. Create corresponding `io/` modules to handle side effects.

---

#### Windows Hook Incompatibility — Flagged by: C, D (2/4)

**Problem:** The shim hook (Section 7.1) is defined as `#!/bin/sh`. This fails for Windows users (Command Prompt/PowerShell), breaking the "Distribution & Polish" promise of v3.0.

**Location:** Section 7.1

**Proposed Fixes:**
- C suggests: Install Python-based shim (`#!/usr/bin/env python3`) for cross-platform support
- D suggests: Detect OS in `commands/init.py` and write `pre-push.cmd` wrapper for Windows alongside shell script

---

#### Circular Config Dependency — Flagged by: C (1/4)

**Problem:** Architecture states `core/` MUST NOT import `io/`. However, `core/config.py` is tasked with configuration loading. If it attempts to load `.ontos.toml` using `io/toml.py`, it violates the layering rule. If it duplicates parsing logic, it violates DRY.

**Location:** Section 1.4 vs Section 2.2

**Proposed Fix:**
- C suggests: **Inversion of Control.** `cli.py` (Shell) must load raw config using `io/toml.py` and inject the data (as Dict or Dataclass) into `core`. `core` must remain passive and config-agnostic.

---

### Major Issues (should address)

#### Q4 Confirmation Not in Data Flow — Flagged by: A, B, D (3/4)

**Problem:** Strategy decision for Q4 says "Use `git diff` for change detection, require confirmation." The data flow (Section 4.3) shows `io/git.py` detection but no user confirmation step. This contradicts the "curation over ceremony" philosophy.

**Location:** Section 4.3

**Proposed Fixes:**
- A suggests: Add `ontos check` command with `--confirm` flag that writes a stamp artifact
- B suggests: Add confirmation step to data flow with `--auto` flag to skip for CI
- D suggests: Define explicit "Detect → Flag → Confirm" interaction step

---

#### Algorithm Complexity Mismatch — Flagged by: D (1/4)

**Problem:** Spec mandates "O(V+E) DFS" for cycle detection. Existing implementation uses `path[path.index(neighbor):]` inside traversal loop, creating O(N²) complexity.

**Location:** `core/graph.py`

**Proposed Fix:**
- D suggests: Acknowledge `core/graph.py` requires a rewrite of cycle detection algorithm, not just extraction

---

### Minor Issues (nice to address)

- A: Validation error model uses both `ValidationError.severity` and `errors/warnings` lists (double source of truth)
- B: `io/toml.py` responsibility overlap with config resolution unclear

---

## 4. Completeness Gaps Consolidation

| Gap | Impact | A | B | C | D | Consensus |
|-----|--------|---|---|---|---|-----------|
| `core/suggestions.py` missing from structure | Blocks implementation | ✓ | ✓ | ✓ | ✓ | 4/4 |
| `core/tokens.py` missing from structure | Blocks implementation | ✓ | ✓ | ✓ | ✓ | 4/4 |
| `io/files.py` interface not specified | Causes confusion | ✓ | ✓ | — | — | 2/4 |
| `io/toml.py` interface not specified | Causes confusion | ✓ | ✓ | ✓ | — | 3/4 |
| `ontos doctor` data flow missing | UX gap | ✓ | ✓ | ✓ | — | 3/4 |
| `ontos hook pre-push` data flow missing | Critical path gap | ✓ | ✓ | — | — | 2/4 |
| `.ontos.toml` missing `required_version` | Q5 incomplete | ✓ | ✓ | ✓ | ✓ | 4/4 |
| Missing `user.name` config field | Attribution broken | — | — | — | ✓ | 1/4 |
| Missing scalability config knobs | Behavior not tunable | ✓ | — | — | — | 1/4 |
| `ContextMap` type not defined | JSON contract unclear | ✓ | — | — | — | 1/4 |
| Graph summarization interface (Q8) | Feature incomplete | — | — | ✓ | — | 1/4 |
| `core/constants.py` not specified | Config fragmentation | — | — | ✓ | — | 1/4 |

### High-Impact Gaps (2+ reviewers)

#### Missing Modules: `core/suggestions.py`, `core/tokens.py` — Flagged by: A, B, C, D (4/4)

**What's Missing:** These modules are referenced in God Script Decomposition tables (Section 3.2) and data flows (Section 4.3) but do not appear in the package structure (Section 2.1) or module specifications (Section 2.2/3.1).

**Impact:** Implementation will stall. Engineers won't know what these modules return, how they're tested, or what core/io boundary they obey.

**Proposed Additions:**
- A suggests: Add specs with explicit public APIs for token estimation and impact suggestion
- B suggests: Add to Section 2.1 with line count estimates (~200 for suggestions, ~50 for tokens)
- C suggests: Add specifications defining input/output contracts
- D suggests: Add to file tree with clear interface definitions

---

#### Missing Interface: `io/toml.py` — Flagged by: A, B, C (3/4)

**What's Missing:** Module is referenced but no public interface defined. Additionally, `tomllib` (Python 3.11+) is read-only; writing TOML requires separate strategy.

**Impact:** Config loading flow depends on this; `commands/init.py` needs to write config.

**Proposed Additions:**
- A suggests: Define `load/write + schema validation strategy`
- B suggests: Define `load_toml()`, `write_toml()`, `merge_configs()` functions
- C suggests: Specify write strategy (likely manual template filling to preserve comments)

---

#### Missing Data Flow: `ontos doctor` — Flagged by: A, B, C (3/4)

**What's Missing:** Command exists in CLI structure but no data flow diagram.

**Impact:** This is a key v3.0 feature for user support. Without flow, inconsistent output, exit codes, and error reporting likely.

**Proposed Additions:**
- A suggests: Add diagram showing identify repo root → detect changed files → run checks → enforce confirmation → return exit code
- B suggests: Add Section 4.4 with checks for .ontos.toml, git hooks, Python version, docs directory, context map, validation, CLI in PATH
- C suggests: Add flow showing access to `io/` (check hooks), `core/` (validate schema), `ui/` (print report)

---

### Single-Reviewer Gaps (may still be valid)

- D: Missing `user.name` config field for session attribution
- A: Missing scalability config knobs (`auto_summary_doc_threshold`, etc.)
- A: `ContextMap` type not defined for JSON contract
- C: Graph summarization interface missing for Q8
- C: `core/constants.py` needed for validation constants

---

## 5. Consistency Issues Consolidation

| Inconsistency | A | B | C | D | Consensus | Locations |
|---------------|---|---|---|---|-----------|-----------|
| "Core is pure" vs core contains transactional writes | ✓ | — | ✓ | ✓ | 3/4 | Sec 1.3 vs 2.2 |
| Module specs reference missing modules | ✓ | ✓ | ✓ | — | 3/4 | Sec 3.2/4.3 vs 2.1 |
| Line counts don't add up (~500-750 unaccounted) | ✓ | ✓ | ✓ | ✓ | 4/4 | Sec 3.2 |
| `tomli` vs zero-dep claim | — | ✓ | ✓ | — | 2/4 | Sec 11.1 vs 1.3 |
| Q4 confirmation in strategy but not in architecture | ✓ | — | — | — | 1/4 | Strategy vs Sec 4 |
| "molecule" vs "product" terminology | — | ✓ | — | — | 1/4 | Codebase vs Strategy |
| Line count (1,625 vs 1,904) | — | ✓ | — | — | 1/4 | Exec Summary vs Appendix |

### Inconsistencies Requiring Resolution

#### "Core is Pure" vs Transactional Writes in Core — Flagged by: A, C, D (3/4)

**Conflict:** Architecture principle says "Core logic... Pure functions (no I/O)." However, `core/context.py` is described as doing transactional file operations, and existing modules marked "EXISTS" contain I/O.

**Location A:** Section 1.3 (Principles)
**Location B:** Section 2.2 (`core/` modules)

**Proposed Resolutions:**
- A suggests: Redefine "core" as "stdlib-only, deterministic, offline-only" rather than "pure," OR move write primitives to `io/`
- C suggests: Mandate that `core/` functions accept data objects (DTOs), not fetch data
- D suggests: Move `SessionContext` to `io/session.py` and keep `core/` purely transformational

---

#### Line Counts Don't Add Up — Flagged by: A, B, C, D (4/4)

**Conflict:** `ontos_end_session.py` is ~1,904 lines. The decomposition targets account for ~1,150-1,350 lines. Gap of ~500-750 lines unaccounted.

**Location:** Section 3.2 (God Script Decomposition)

**Proposed Resolutions:**
- A suggests: Add "must extract" checklist to prevent `commands/log.py` becoming "god script 2.0"
- B suggests: Review actual script to confirm decomposition is complete; some code may be duplicated
- C suggests: Increase estimate for `commands/log.py` (will contain significant glue code)
- D suggests: More granular audit of God Script needed

---

#### `tomli` vs Zero-Dep Claim — Flagged by: B, C (2/4)

**Conflict:** Section 11.1 states "Core: Stdlib only" but also allows `tomli` for Python 3.9-3.10.

**Location A:** Section 1.3 (Zero-Dep principle)
**Location B:** Section 11.1 (dependency allowance)

**Proposed Resolutions:**
- B suggests: Clarify that `tomli` is conditional dependency (only installed on Python <3.11); consistent with zero-dep since 3.11+ uses stdlib
- C suggests: Update claim to "Zero-Dep (except vendor-bundled tomli)"
- D suggests: Vendor `tomli` in `ontos/vendor/` directory

---

## 6. Risk Assessment Consolidation

| Risk | Likelihood | Impact | A | B | C | D | Consensus |
|------|------------|--------|---|---|---|---|-----------|
| Q4 confirmation unusable or meaningless | High | High | ✓ | — | — | — | 1/4 |
| Hidden coupling in God Script decomposition | High | High | ✓ | ✓ | — | — | 2/4 |
| Purity refactoring underestimated | High | High | — | — | ✓ | ✓ | 2/4 |
| Validation refactoring complexity | High | High | — | — | ✓ | — | 1/4 |
| CWD vs Git Root resolution breaks commands | High | High | — | — | ✓ | — | 1/4 |
| `@{push}` diff breaks on edge cases | Medium | Medium | ✓ | — | — | — | 1/4 |
| Performance on large doc sets | Medium | Medium | ✓ | ✓ | — | — | 2/4 |
| CLI startup time > 100ms | Low | Low | — | ✓ | — | — | 1/4 |
| Output coupling blocks MCP | Medium | High | — | — | — | ✓ | 1/4 |
| ValidationOrchestrator becomes dumping ground | — | — | ✓ | — | — | — | 1/4 |
| Hook breakage during migration | 100% | Medium | — | — | — | ✓ | 1/4 |

### High-Priority Risks (High likelihood OR High impact, 2+ reviewers)

#### Hidden Coupling in God Script Decomposition — Flagged by: A, B (2/4)

**Risk:** The 1,904-line script likely has internal function calls and shared state not visible in decomposition table. Decomposition will reveal unexpected dependencies.

**Likelihood:** High
**Impact:** High

**Mitigations Proposed:**
- A: Write characterization tests for context map and log generation on fixtures before refactor
- B: Generate function call graph, identify shared variables/state, create integration tests that exercise full flow, decompose with continuous test verification

---

#### Purity Refactoring Underestimated — Flagged by: C, D (2/4)

**Risk:** Effort to separate logic from I/O in existing scripts (`staleness.py`, `proposals.py`) is underestimated. Architecture assumes "reuse as-is."

**Likelihood:** High
**Impact:** High (Architectural Rot)

**Mitigations Proposed:**
- C: Adopt Inversion of Control pattern
- D: Adopt "Strict IO/Core Separation Plan" — extract git subprocess calls to `io/git.py`, refactor `core` modules to accept data objects

---

#### Performance on Large Doc Sets — Flagged by: A, B (2/4)

**Risk:** Performance targets (500ms, 2s) won't hold as doc counts grow because full content is read for token estimation and link scanning every run.

**Likelihood:** Medium
**Impact:** Medium

**Mitigations Proposed:**
- A: Add lightweight cache keyed by file path + mtime + size; invalidate on change
- B: Profile early and optimize cycle detection to O(V+E) as specified

---

### Other Risks Worth Noting

- A: Q4 confirmation will be either unusable (blocks constantly) or meaningless (always auto-passes)
- A: `@{push}` diff strategy breaks on first push, no upstream, detached head, or shallow clones
- B: CLI startup time may exceed 100ms target if imports are deep
- C: CWD vs Git Root — commands run from subdirectories may fail or create files in wrong place
- C: Validation refactoring complexity is high due to "hard exits" interleaved with logic
- D: Output coupling (`sys.stdout` hardcoded) blocks MCP server capturing output
- D: Hook breakage is 100% likely during migration; need explicit replacement strategy

---

## 7. Proposed Changes Consolidation

| Proposal | From | Severity | Similar Proposals From |
|----------|------|----------|------------------------|
| Add missing modules to package structure | A | Major | B, C, D (same) |
| Windows-compatible hooks | C | Critical | D (same) |
| Strict IO/Core separation plan | D | Critical | C (same) |
| Invert config loading control | C | Critical | — (unique) |
| Golden Master testing before decomposition | D | Major | A (similar) |
| De-scope v3.0 CLI surface | A | Major | — (unique) |
| Explicit validator modules | A | Major | — (unique) |
| Add Q4 `ontos check` command | A | Major | — (unique) |
| Add user confirmation step to log flow | B | Major | A (related) |
| Consolidate validation constants | B | Major | — (unique) |
| Version pinning (Q5) spec | B | Low | — (unique) |

### Major Change Proposals (or 2+ reviewers proposing similar)

#### Proposal: Add Missing Modules to Package Structure

**Proposed By:** A (also B, C, D — unanimous)

**Problem Addressed:** Several modules referenced in decomposition tables and data flows don't appear in package structure.

**Proposed Change:**
- Add `core/suggestions.py` with impact suggestion API
- Add `core/tokens.py` with token estimation API
- Add specs with explicit public interfaces

**Estimated Impact:** Sections 2.1, 2.2, 3.1 affected; Effort: Low (documentation)

---

#### Proposal: Windows-Compatible Hooks

**Proposed By:** C, D (2/4)

**Problem Addressed:** Shim hook is `#!/bin/sh`, fails on Windows.

**Proposed Change:**
- C's version: Install Python-based shim (`#!/usr/bin/env python3`)
- D's version: Detect OS in `commands/init.py`, write `pre-push.cmd` for Windows alongside shell script

**Estimated Impact:** Section 7.1 affected; Effort: Low

---

#### Proposal: Strict IO/Core Separation Plan

**Proposed By:** D (also C — similar)

**Problem Addressed:** Modules marked "EXISTS" in `core/` currently contain I/O, violating architecture immediately.

**Proposed Change:**
- Mark `staleness.py`, `proposals.py`, `history.py` as "REFACTOR" in Section 2.2/12.1
- Create corresponding `io/` modules to handle side effects
- Mandate that `core/` functions accept data objects (DTOs), not fetch data

**Estimated Impact:** Sections 2.2, 12.1 affected; Effort: Medium (Critical)

---

#### Proposal: Invert Config Loading Control

**Proposed By:** C (unique)

**Problem Addressed:** `core/config.py` loading `.ontos.toml` creates circular dependency with `io/`.

**Proposed Change:**
1. Define `OntosConfig` dataclass in `core/types.py`
2. `cli.py` calls `io.toml.load_config()` to hydrate the dataclass
3. `cli.py` injects `OntosConfig` into `commands` and `core` functions

**Estimated Impact:** Sections 1.4, 2.2, 4.1 affected; Effort: Medium

---

#### Proposal: Golden Master Testing Before Decomposition

**Proposed By:** D (A proposes similar characterization tests)

**Problem Addressed:** High risk of regression when splitting 1,904-line script.

**Proposed Change:**
- Add "Phase 0" to Migration Strategy
- Create integration tests that run v2 scripts, capture stdout and file artifacts
- Assert v3 commands produce identical output

**Estimated Impact:** Section 9 affected; Effort: Medium

---

### Minor / Unique Proposals

- A: De-scope v3.0 CLI to minimal surface (`init`, `map`, `log`, `doctor`, `hook`, `--json`); move others to v3.1+
- A: Split validators by domain (`validators/frontmatter.py`, `validators/schema.py`, etc.); orchestrator does sequencing only
- A: Add `ontos check` command with `--confirm` flag for Q4
- B: Add user confirmation step to `ontos log` data flow with `--auto` flag for CI
- B: Specify Q5 version pinning with `required_version` field and checking logic
- B: Consolidate validation constants (keep in Python or move to TOML, but document decision)
- C: Ban `input()` in `core/` modules explicitly
- D: Vendor `tomli` in `ontos/vendor/` for zero-dep claim

---

## 8. Reviewer Agreement Matrix

### 8a. Strong Agreement (3-4 reviewers aligned)

| Topic | Agreement | Who Agrees |
|-------|-----------|------------|
| Architecture direction is correct | ValidationOrchestrator, layer separation, God Script decomposition are the right moves | A, B, C, D |
| Missing modules must be added | `core/suggestions.py` and `core/tokens.py` need specs | A, B, C, D |
| Line counts need verification | Decomposition doesn't account for all code | A, B, C, D |
| Q5 version pinning incomplete | Need `required_version` field and checking logic | A, B, C, D |
| Q4 confirmation needs definition | Data flow missing confirmation step | A, B, D |
| Data flows incomplete | Missing `ontos doctor` and hook flows | A, B, C |
| `io/toml.py` interface needed | Write strategy unclear | A, B, C |

### 8b. Split Opinions (2 vs 2 or similar)

| Topic | Position 1 | Position 2 |
|-------|------------|------------|
| Core purity severity | C, D: Critical (architectural rot from day one) | A, B: Not explicitly flagged as critical |
| Windows support urgency | C, D: Critical for v3.0 | A, B: Not flagged |
| Config loading pattern | C: Inversion of Control required | A, B, D: Not explicitly addressed |

### 8c. Unique Concerns (only 1 reviewer)

| Concern | From | Validity Assessment |
|---------|------|---------------------|
| CWD vs Git Root resolution | C | Valid — global CLI running from subdirectories is real risk |
| CLI scope creep | A | Valid — more commands = more QA surface |
| Async variants for MCP | B | Valid for v4 readiness — but may be premature |
| `input()` in core blocks MCP | C | Valid — headless core is v4 requirement |
| Output stream injection | D | Valid — dependency injection needed for MCP |
| `user.name` config field | D | Valid — attribution needs source |
| `ContextMap` type definition | A | Valid — JSON contract needs clarity |

---

## 9. Architecture Strengths

| Strength | Noted By |
|----------|----------|
| Clear layering (CLI → Commands → Core → IO) | A, B, C, D |
| ValidationOrchestrator pattern solves hard-exit problem | A, B, C, D |
| God Script decomposition is necessary and well-targeted | A, B, C, D |
| Strategy alignment (10+ of 13 decisions correctly implemented) | A, B |
| Extension points for v4.0 (MCP, daemon, exports) | A, B |
| Performance targets specified (500ms, 2s, 100ms) | B |
| Migration phases are incremental | B |
| Shim hooks bridge global install and local enforcement | D |
| Distribution model correctly separates System from Repo | D |

**All reviewers praised the fundamental architecture direction. The ValidationOrchestrator and layer separation are considered excellent patterns. The issues identified are primarily about completeness and consistency, not fundamental design flaws.**

---

## 10. Decision-Ready Summary

### Critical (Must Fix Before Implementation)

| Issue/Gap/Risk | Consensus | Type |
|----------------|-----------|------|
| Add `core/suggestions.py`, `core/tokens.py` to package structure | 4/4 | Gap |
| Define Q5 version pinning (`required_version` + checking logic) | 4/4 | Gap |
| Add Q4 confirmation step to `ontos log` data flow | 3/4 | Correctness |
| Windows hook support (cross-platform shim) | 2/4 | Correctness |
| Mark impure `core/` modules as "REFACTOR" not "EXISTS" | 2/4 | Correctness |
| Define `io/toml.py` write strategy | 3/4 | Gap |

### Major (Should Fix)

| Issue/Gap/Risk | Consensus | Type |
|----------------|-----------|------|
| Add `ontos doctor` data flow | 3/4 | Gap |
| Add `ontos hook pre-push` data flow | 2/4 | Gap |
| Verify line counts in decomposition (audit ~500-750 unaccounted lines) | 4/4 | Consistency |
| Resolve "core is pure" vs transactional writes inconsistency | 3/4 | Consistency |
| Define `io/files.py` interface | 2/4 | Gap |
| Address hidden coupling risk (characterization tests) | 2/4 | Risk |

### Minor (Nice to Fix)

| Issue/Gap/Risk | Consensus | Type |
|----------------|-----------|------|
| Clarify `tomli` vs zero-dep claim | 2/4 | Consistency |
| Add scalability config knobs | 1/4 | Gap |
| Define `ContextMap` type | 1/4 | Gap |
| Add `user.name` config field | 1/4 | Gap |
| Add graph summarization interface (Q8) | 1/4 | Gap |
| Resolve "molecule" vs "product" terminology | 1/4 | Consistency |

### No Action Needed (Reviewers Aligned, Architecture Correct)

- Q1 JSON output mode
- Q2 Export templates (correctly deferred)
- Q3 Context slicing (correctly deferred)
- Q7 MCP client docs (correctly deferred)
- Q9 MCP security (correctly deferred)
- Q10 Pydantic optional for MCP
- Q11 Script reorganization into package
- Q12 Python-first stack
- Q13 Markdown primary, JSON optional

---

## 11. Recommended Next Steps

Based on the consolidated review:

### 1. Immediate (before implementation starts)

1. **Add missing modules** to Section 2.1 package structure:
   - `core/suggestions.py` with public interface spec
   - `core/tokens.py` with public interface spec

2. **Define Q4 confirmation mechanism:**
   - Add confirmation step to Section 4.3 data flow
   - Specify `--auto` flag for CI/scripting bypass
   - Consider stamp artifact (A's suggestion)

3. **Specify Q5 version checking:**
   - Add `required_version` to `.ontos.toml` schema
   - Add version check function to `io/toml.py`
   - Define warn-only behavior in CLI startup

4. **Address Windows hook compatibility:**
   - Update Section 7.1 with cross-platform strategy
   - Either Python-based shim OR OS detection with `.cmd` wrapper

### 2. Before Coding Starts

1. **Mark impure modules as "REFACTOR":**
   - Update Section 2.2/12.1 for `staleness.py`, `proposals.py`, `history.py`
   - Define pattern: `io/` fetches data, `core/` transforms data

2. **Audit line counts:**
   - Verify actual line counts in God Scripts
   - Account for missing ~500-750 lines
   - Update decomposition tables

3. **Add missing data flows:**
   - Section 4.4: `ontos doctor`
   - Section 4.5: `ontos hook pre-push`

4. **Define missing interfaces:**
   - `io/files.py` public API
   - `io/toml.py` public API (including write strategy)

### 3. During Implementation

1. **Create Golden Master tests before decomposition:**
   - Capture v2 script outputs on fixtures
   - Assert v3 commands produce identical output

2. **Implement config with Inversion of Control:**
   - `cli.py` loads config, injects into commands/core
   - `core/` remains passive and config-agnostic

3. **Enforce `core/` purity:**
   - Ban `input()`, `print()`, subprocess calls in `core/`
   - All I/O in `io/` layer only

4. **Profile early:**
   - Verify O(V+E) cycle detection
   - Test performance targets on 100+ doc sets

### 4. Deferred (post-v3.0)

1. Scalability config knobs (`auto_summary_doc_threshold`, etc.)
2. Additional data flows (`ontos verify`, `ontos migrate`, `ontos consolidate`)
3. Graph summarization interface refinement
4. Export templates extension point (`ui/formatters/`)

---

*End of Consolidated Review*

*Consolidation performed: 2026-01-11*
*Source reviews: A (Codex), B (Claude), C (Gemini Architectural), D (Gemini DeepThink)*
