# Ontos v3.0 Architecture Review

## Peer Architect: LLM [Architectural Integration]

## Date: 2026-01-11

---

## 1. Decision Alignment Check

| Q# | Decision | Implemented? | Notes |
| --- | --- | --- | --- |
| Q1 | JSON output mode | ✅ Yes | `ui/json_output.py` and global flag included. |
| Q2 | Export templates (DEFERRED) | ✅ Correct |  |
| Q3 | Lazy loading (DEFERRED) | ✅ Correct |  |
| Q4 | Git-based change detection | ✅ Yes | `io/git.py` handles diffs. |
| Q5 | Version Pinning (Warn only) | ❌ **No** | **Missing.** `.ontos.toml` schema (5.1) lists `version` (format version) but missing `required_version` field. Logic to check it at startup is absent from `cli.py`. |
| Q6 | Shim Hooks | ⚠️ Partial | Shim script (7.1) is `sh` only. Fails on Windows (Q6 implied cross-platform support). |
| Q7 | Auto-configure MCP (DEFERRED) | ✅ Correct |  |
| Q8 | Progressive Complexity | ⚠️ Partial | Thresholds defined (8.1), but the **interface** to execute summarization is missing from `core/graph.py` and `commands/map.py`. |
| Q9 | MCP Security (DEFERRED) | ✅ Correct |  |
| Q10 | Pydantic (MCP only) | ✅ Yes | Core is stdlib only. |
| Q11 | Script Reorganization | ✅ Yes | Structure is sound, but decomposition plan has gaps (see Section 3). |
| Q12 | Stay with Python | ✅ Yes |  |
| Q13 | Markdown Primary | ✅ Yes |  |

---

## 2. Correctness Review

### 2a. Package Structure (Critical Layering Violations)

**Issue:** Circular Dependency in Configuration
**Location:** Section 1.4 vs 2.2
**Severity:** **Critical**
**Problem:** The architecture states `core/` MUST NOT import `io/`. However, `core/config.py` is tasked with configuration. If it attempts to load `.ontos.toml` using `io/toml.py`, it violates the layering rule. If it duplicates the parsing logic, it violates DRY.
**Proposed Fix:** **Inversion of Control.** `cli.py` (Shell) must load the raw config using `io/toml.py` and inject the data (as a Dict or Dataclass) into `core`. `core` must remain passive and config-agnostic.

**Issue:** Impure Modules in Pure Core
**Location:** Section 2.2 (`staleness.py`, `proposals.py`)
**Severity:** **Major**
**Problem:** The architecture lists these modules as "EXISTS" in `core/`. Currently, they contain direct I/O calls (`subprocess` for git, file reads). Moving them to `core/` without refactoring violates the "Zero I/O" principle immediately.
**Proposed Fix:** The Migration Strategy must include a "Purification" phase. Logic must be refactored to accept data arguments (e.g., `check_staleness(doc, git_mtimes)`) rather than fetching it.

### 2c. Data Flows (Interactive Pollution)

**Issue:** `input()` calls in Core
**Location:** Section 4.3 (`ontos log`)
**Severity:** **Major**
**Problem:** The flow implies `commands/log.py` orchestrates logic, but doesn't explicitly strip the interactive prompts (`input()`) currently embedded in the "God Script" logic (e.g., confirming graduation). If this logic moves to `core/proposals.py` as-is, the core is not "Headless," blocking future MCP usage.
**Proposed Fix:** Explicitly ban `input()` in `core/`. The Command layer must handle all user interaction and pass results to Core.

---

## 3. Completeness Review

### 3a. Missing Modules

**Gap:** `core/suggestions.py` & `core/tokens.py`
**Impact:** These are listed as targets in the "God Script Decomposition" table (3.2) but are missing from the Section 2.2 Package Structure.
**Proposed Addition:** Add specifications for these modules.

**Gap:** `core/constants.py`
**Impact:** `ontos_config_defaults.py` contains hardcoded constants (`VALID_STATUS`, etc.). The architecture doesn't specify where these go.
**Proposed Addition:** Define `core/constants.py` to house immutable definitions.

### 3b. Undefined Interfaces

**Gap:** Graph Summarization Interface (Q8)
**Impact:** Q8 is CRITICAL. Section 8.2 defines flags, but `core/graph.py` has no method to actually produce a summarized/truncated graph.
**Proposed Addition:** Add `summarize_graph(graph: DependencyGraph, depth: int) -> DependencyGraph` to `core/graph.py`.

### 3c. Missing Data Flows

**Gap:** Windows Hook Support
**Impact:** The shim hook (7.1) is `#!/bin/sh`. This provides no solution for Windows users, failing the "Distribution & Polish" promise.
**Proposed Addition:** `ontos init` must install platform-appropriate hooks or a Python-based shim (`#!/usr/bin/env python3`).

### 3e. Migration Gaps

**Gap:** Legacy `.ontos` Directory
**Impact:** v3.0 `init` creates `.ontos.toml` but leaves the old `.ontos/` folder. Users may unknowingly run old scripts.
**Proposed Addition:** `ontos init` should detect legacy directory and prompt to archive/delete.

---

## 4. Consistency Review

### 4c. Constraints vs Implementation

**Inconsistency:** `tomli` vs Zero-Dep
**Location:** Section 11.1 vs 1.3
**Resolution:** `tomli` is required for Python < 3.11. The "Zero-Dep" claim needs a caveat: "Zero-Dep (except vendor-bundled tomli)".

### 4d. Line Counts

**Inconsistency:** Decomposition Math
**Location:** Section 3.2
**Observation:** `ontos_end_session.py` is ~1,900 lines. The breakdown targets sum to ~1,350. ~550 lines are unaccounted for.
**Resolution:** Increase estimate for `commands/log.py`. It will likely contain significant glue code for arguments, prompting, and git interactions.

---

## 5. Risk Assessment

### 5a. Implementation Risks

**Risk:** **CWD vs Git Root Resolution**
**Likelihood:** High
**Impact:** High
**Description:** v2 scripts assumed CWD = Repo Root. v3 CLI runs globally. If `io/files.py` relies on `os.getcwd()`, commands run from subdirectories (`cd docs/logs; ontos log`) will fail or create files in the wrong place.
**Mitigation:** `cli.py` must reliably find the project root (via `.ontos.toml` or `.git` search) and anchor `SessionContext` to it.

### 5b. God Script Decomposition Risk

**Risk:** **Validation Refactoring Complexity**
**Likelihood:** High
**Impact:** High
**Description:** Extracting 3,850 lines of validation into the new `ValidationOrchestrator` pattern is complex. The logic is currently deeply interleaved with "hard exits."
**Mitigation:** Create a "Golden Master" test suite for existing validation output before refactoring to ensure parity.

---

## 6. Proposed Changes

#### Change Proposal: Invert Config Loading Control

**Problem:** `core/config.py` loading `.ontos.toml` creates a circular dependency with `io/`.
**Proposed Change:**

1. Define `OntosConfig` dataclass in `core/types.py`.
2. `cli.py` calls `io.toml.load_config()` to hydrate the dataclass.
3. `cli.py` injects `OntosConfig` into `commands` and `core` functions.
**Rationale:** Preserves Functional Core purity. Core receives config; it does not fetch it.
**Impact:** Section 1.4, 2.2, 4.1. Effort: Medium.

#### Change Proposal: Cross-Platform Hooks

**Problem:** Shim hooks fail on Windows.
**Proposed Change:**
Update `commands/init.py` spec to install a Python-based shim:

```python
#!/usr/bin/env python3
import sys, subprocess
# ... delegation logic ...

```

**Rationale:** Essential for v3.0 goals.
**Impact:** Section 7.1. Effort: Low.

#### Change Proposal: Explicit Purity Refactor

**Problem:** `staleness.py` and `proposals.py` contain I/O but are slated for "Move to Core."
**Proposed Change:**
Update Migration Strategy (Phase 2) to include "Purify Modules":

1. Extract git subprocess calls to `io/git.py`.
2. Refactor `core` modules to accept data objects (Inversion of Control).
**Rationale:** Prevents architectural corruption from day one.
**Impact:** Section 12. Effort: Medium.

---

## 7. Summary Assessment

**Overall Quality:** **Strong**

**Strengths:**

* **Architecture Pattern:** The Functional Core / Imperative Shell approach is the correct strategic move.
* **ValidationOrchestrator:** Excellent pattern for fixing the UX issues identified in the analysis.
* **Decomposition:** Aggressive breakdown of "God Scripts" is necessary and well-targeted.

**Critical Issues:** (Must fix before implementation)

1. **Circular Config Dependency:** Must implement Inversion of Control for config loading.
2. **Windows Incompatibility:** Shim hooks need a cross-platform strategy.
3. **Missing Modules:** `suggestions.py` and `tokens.py` need specs.
4. **Interactive Core Risk:** Explicitly ban `input()` in `core/` modules to ensure v4 readiness.

**Major Concerns:**

1. **CWD Resolution:** CLI must robustly handle running from subdirectories.
2. **Missing Q5/Q8 Logic:** Version pinning and graph summarization interfaces are undefined.

**Recommendation:** **Approve with Changes**
(Implement the Inversion of Control proposals and add missing module specs/Windows support).