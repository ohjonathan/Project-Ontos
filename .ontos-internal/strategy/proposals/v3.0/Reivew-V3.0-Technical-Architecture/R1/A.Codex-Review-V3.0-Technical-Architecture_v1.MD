According to the v3.0 Technical Architecture draft dated **January 11, 2026**, the structure is solid but a few critical mismatches and missing specs will bite you during implementation if you don’t tighten them now. 

# Ontos v3.0 Architecture Review

## Peer Architect: GPT-5.2 Thinking (ChatGPT)

## Date: 2026-01-10

---

## 1. Decision Alignment Check

| Q#  | Decision                                            | Implemented?         | Notes                                                                                                                    |
| --- | --------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Q1  | JSON output mode                                    | ✅ Yes                | Architecture includes `--json` mode and JSON formatting layer.                                                           |
| Q2  | Export templates (DEFERRED)                         | ✅ Correctly deferred | Not implemented as a v3 feature, only future-facing prep.                                                                |
| Q3  | Context slicing (DEFERRED)                          | ✅ Correctly deferred | Not implemented as a v3 feature.                                                                                         |
| Q4  | `git diff` change detection + require confirmation  | ⚠️ Partial           | `git diff` change detection exists, but the “require confirmation” mechanism is not specified end-to-end.                |
| Q5  | Version pinning (warn only)                         | ⚠️ Partial           | `.ontos.toml` has a version field, but there’s no explicit “warn-only” behavior spec and no compatibility policy story.  |
| Q6  | Shim hooks delegating to global CLI                 | ✅ Yes                | Shim-hook strategy is consistent with the decisions.                                                                     |
| Q7  | MCP client auto-config (docs-only)                  | ⚠️ Partial           | Architecture creates an MCP stub area, but doesn’t define the “docs-only” deliverable details.                           |
| Q8  | Progressive complexity + auto-summary + depth flags | ✅ Yes                | Depth flags + auto-threshold behavior are present.                                                                       |
| Q9  | MCP security model (DEFERRED)                       | ✅ Yes                | No premature security scheme baked in.                                                                                   |
| Q10 | Pydantic optional dependency for MCP                | ✅ Yes                | Optional deps align with the decision.                                                                                   |
| Q11 | Script reorg into proper package                    | ✅ Yes                | Package structure + decomposition plan aligns with decision intent.                                                      |
| Q12 | Python-first                                        | ✅ Yes                | Implementation stays in Python.                                                                                          |
| Q13 | Markdown primary, JSON optional                     | ✅ Yes                | Matches the strategy direction.                                                                                          |

---

## 2. Correctness Review

### 2a. Package Structure (Section 2)

**Issue:** Scope creep hidden inside the command list
**Location:** Section 2.1, `commands/` list includes `verify/query/migrate/consolidate/promote/scaffold/stub`
**Severity:** Major
**Problem:** The architecture frames v3.0 as “Distribution & Polish,” but the CLI surface suggests a much broader product expansion. That increases build time, QA surface area, and backwards-compat risk for zero user value if these aren’t in the v3 “must ship” set.
**Proposed Fix:** Make v3.0 CLI minimal: `init`, `map`, `log`, `doctor`, `hook`, plus `--json`. Everything else either:

* moves to v3.1+ explicitly, or
* ships as “hidden/experimental” commands not advertised in `--help`.

**Issue:** “Functional core” principle is contradicted by `SessionContext` being in `core/` while doing transactional writes
**Location:** Layering rules vs `core/context.py` described as transactional file ops
**Severity:** Major
**Problem:** You’ve defined core as pure and stdlib-only. Purity is already being softened with “IMPURE” callouts, but the core definition is doing too much work rhetorically. This will cause architectural drift and dependency-rule violations over time.
**Proposed Fix:** Pick one of these and write it down as law:

* **Option A:** Core can include “impure but local” primitives (filesystem allowed) but must be deterministic and network-free.
* **Option B:** Move `SessionContext` to `io/session.py` and keep `core/` purely transformational.

### 2b. Module Specifications (Section 3)

**Issue:** Referenced modules exist in the decomposition plan but are missing from the package structure and/or lack public interfaces
**Location:** God script decomposition tables mention `core/tokens.py`, `core/suggestions.py` but Section 2.1 doesn’t list them and Section 3 doesn’t spec them
**Severity:** Major
**Problem:** Implementation will stall because engineers won’t know what these modules return, how they’re tested, and what “core vs io” boundary they obey.
**Proposed Fix:** Add specs for:

* `core/tokens.py` (token estimation API and approximation method)
* `core/suggestions.py` (input: commits + doc graph, output: ranked impact suggestions)
* `io/toml.py` (load/write + schema validation strategy)
* `io/files.py` (scan/read APIs + ignore rules)

**Issue:** Validation error model is slightly confused
**Location:** `core/validation.py` spec uses `ValidationError.severity` plus `errors` and `warnings` lists
**Severity:** Minor
**Problem:** Two sources of truth for severity is how you get weird edge cases like “warning stored in errors list.”
**Proposed Fix:** Either:

* keep a single `issues: list[ValidationIssue]` with severity, or
* keep `errors/warnings` lists and remove severity from the item.

### 2c. Data Flows (Section 4)

**Issue:** No data flow defined for the most important automation path: hooks
**Location:** Section 4 omits `ontos hook pre-push` end-to-end behavior
**Severity:** Critical
**Problem:** Q4 and Q6 live or die in hooks. Without a flow, you’ll implement it ad hoc and accidentally violate decisions. Q4 explicitly requires confirmation, which is not represented in any flow. 
**Proposed Fix:** Add a `4.4 pre-push hook` diagram showing:

* identify repo root
* detect changed files (with edge cases like no upstream)
* run check/validation
* enforce “confirmation” policy
* return exit code

### 2d. ValidationOrchestrator vs Maintainability Findings

The orchestrator direction is correct: centralized error collection and no hard exits directly addresses the maintainability critique about fragmented validation and side effects.

**Issue:** Orchestrator phases are under-specified vs the real set of validations you already have
**Location:** `ValidationOrchestrator.validate_status()` and overall phase list
**Severity:** Major
**Problem:** “status” is carrying too much ambiguity. In the current system, you have multiple categories: schema validity, status rules, staleness, architecture rules, log schema rules, etc. If you don’t name validators explicitly, you will recreate the 28-function sprawl under a new label.
**Proposed Fix:** Make validators first-class:

* `validators/frontmatter.py`
* `validators/schema.py`
* `validators/graph.py`
* `validators/status.py`
* `validators/staleness.py`
* `validators/logs.py`
  Then orchestrator is just sequencing and aggregation.

---

## 3. Completeness Review

### 3a. Missing Modules

**Gap:** `core/tokens.py` and `core/suggestions.py` are referenced but not defined as first-class modules in the structure/spec
**Impact:** Blocks `ontos map` thresholds and `ontos log` “impact suggestion” step from being implemented cleanly
**Proposed Addition:** Add both to the package tree and Section 3 with explicit public APIs.

### 3b. Undefined Interfaces

**Gap:** `ContextMap` type referenced in JSON conversion helpers isn’t defined in the module specs
**Impact:** Breaks `--json` contract assumptions for CI and MCP readiness
**Proposed Addition:** Define `core/types.py: ContextMap` or return a plain dict consistently and document its shape.

### 3c. Missing Data Flows

**Gap:** No flow for `ontos doctor` and no flow for hook execution
**Impact:** These are where user friction lives. Without flows you’ll end up with inconsistent output, exit codes, and error reporting.
**Proposed Addition:** Add diagrams for `doctor` and `hook pre-push`.

### 3d. Configuration Gaps

**Gap:** `.ontos.toml` schema does not include knobs for the documented scalability behavior
**Impact:** You’ve declared thresholds and auto-behaviors, but users can’t tune them, and you can’t stabilize behavior across repos
**Proposed Addition:** Add `[scalability]` settings like `auto_summary_doc_threshold`, `max_tokens_before_truncate`, `default_depth`, `max_docs_fast_path`.

### 3e. Migration Gaps

**Gap:** Backward compatibility story for existing “repo-injected scripts” users is not described as a user journey
**Impact:** v2.9.5 workflows will break in practice unless you provide a clear “upgrade path” with safety rails
**Proposed Addition:** A migration doc path:

* “install ontos globally”
* run `ontos init --migrate`
* verify with `ontos doctor`
* remove old scripts safely

---

## 4. Consistency Review

### 4a. Terminology

**Inconsistency:** “Core is pure” vs “core contains transactional file operations”
**Location A:** Principle section describing functional core
**Location B:** `core/context.py` responsibility
**Resolution:** Redefine “core” as “stdlib-only, deterministic, offline-only” rather than “pure,” or move write primitives to `io/`.

### 4b. Module Specs vs Data Flows

**Inconsistency:** Data flows reference modules that are not in the package structure list
**Location A:** Decomposition tables and `ontos log` flow mention `core/suggestions.py`, `core/tokens.py`
**Location B:** Section 2.1 tree missing them
**Resolution:** Add them to Section 2.1 and spec them in Section 3.

### 4c. Constraints vs Implementation

**Inconsistency:** Decision says Q4 requires confirmation, but architecture introduces workflow enforcement toggles without defining how confirmation is represented
**Location A:** Strategy decision language about confirmation 
**Location B:** Architecture’s config and hook behavior (confirmation not modeled)
**Resolution:** Define a concrete confirmation mechanism and map it to config flags.

### 4d. Line Counts

**Inconsistency:** `commands/log.py ~500` is plausible, but only if you aggressively carve out `core/suggestions.py`, `io/git.py`, `io/files.py`, and log formatting helpers
**Resolution:** Add a “must extract” checklist so `commands/log.py` doesn’t become “god script 2.0.”

---

## 5. Risk Assessment

**Risk:** Q4 “confirmation” will be implemented in a way that is either unusable (blocks pushes constantly) or meaningless (always auto-passes)
**Likelihood:** High
**Impact:** High
**Mitigation:** Define confirmation as a real artifact:

* either a stamp file in `.ontos/` with commit hash + timestamp
* or a git note/tag approach
  And define the hook logic around it.

**Risk:** `@{push}` diff strategy breaks on first push, no upstream, detached head, or shallow clones
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:** Implement fallbacks:

* if no upstream, diff against `HEAD~1` or skip with warning
* if shallow clone, run a reduced check

**Risk:** Decomposition reveals hidden coupling and global state assumptions in the god scripts
**Likelihood:** High
**Impact:** High
**Mitigation:** Before refactor, write characterization tests for:

* context map generation on fixtures
* log generation on fixtures
  Then refactor behind those tests.

**Risk:** Performance targets won’t hold as doc counts grow because you read full content for token estimation and link scanning every run
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:** Add a lightweight cache keyed by file path + mtime + size; invalidate on change.

**Risk:** CLI UX becomes inconsistent across commands as features expand
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:** Define an output contract: one place that formats success/warn/error across all commands and guarantees valid JSON when `--json` is set.

---

## 6. Proposed Changes

#### Change Proposal: Make Q4 a First-Class `ontos check` Command (and Hook Flow)

**Problem:** Hooks and “confirmation” are underspecified, and Q4 is currently only half-modeled. 
**Proposed Change:**

* Add `commands/check.py` and a small `core/check.py` that returns a structured result.
* Hook calls `ontos check` and blocks push if check fails or confirmation is missing.
* `ontos check --confirm` writes a stamp artifact.
  **Rationale:**
* Prevents ad hoc hook logic.
* Makes “confirmation” concrete and testable.
  **Impact:**
* Sections affected: Data Flows, Git Integration, CLI commands, Config schema
* Effort: Medium

#### Change Proposal: De-scope v3.0 CLI Surface to the “must ship” set

**Problem:** Too many commands increases risk and delays the real goal: distribution + low friction.
**Proposed Change:**

* v3.0: `init`, `map`, `log`, `doctor`, `hook`, `--json`
* v3.1+: `query`, `consolidate`, etc
  **Rationale:**
* Smaller surface area, fewer regressions, faster ship.
* Keeps the “just works” promise.
  **Impact:**
* Sections affected: Package structure, CLI architecture, Migration phases
* Effort: Low to Medium

#### Change Proposal: Explicit Validator Modules + Plug-in Style Orchestration

**Problem:** Orchestrator could become a dumping ground and recreate today’s maintainability problem under a new name.
**Proposed Change:**

* Split validators by domain and keep orchestrator as sequencing + aggregation only.
  **Rationale:**
* Forces clean boundaries and makes testing straightforward.
  **Impact:**
* Sections affected: Module Specs, Testing architecture
* Effort: Medium

---

## 7. Summary Assessment

## Summary Assessment

**Overall Quality:** Adequate

**Strengths:**

* Clear packaging direction and layer separation are the right move for v3.0. 
* ValidationOrchestrator is the correct response to the maintainability critique.
* Progressive complexity philosophy is consistent with the strategy direction. 

**Critical Issues:** (must fix before implementation)

* Q4 “require confirmation” is not implemented end-to-end and not represented in data flows. 
* Hook execution path lacks a defined flow and contract.
* Referenced modules and types are missing from the package/spec (tokens, suggestions, ContextMap).

**Major Concerns:** (should fix, but not blocking)

* CLI command scope is too large for “Distribution & Polish.”
* Core purity language conflicts with where transactional writes live.

**Minor Suggestions:** (nice to have)

* Simplify the validation issue model to avoid double severity encoding.
* Add scalability knobs to config to match described behavior.

**Recommendation:** Approve with Changes
