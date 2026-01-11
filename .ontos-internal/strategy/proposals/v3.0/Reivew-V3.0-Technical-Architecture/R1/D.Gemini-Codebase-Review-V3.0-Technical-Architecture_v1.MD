# Ontos v3.0 Architecture Review

## Peer Architect: LLM [D] (Gemini DeepThink)

## Date: 2026-01-11

---

## 1. Decision Alignment Check

| Q# | Decision | Implemented? | Notes |
| --- | --- | --- | --- |
| Q1 | JSON output mode | ✅ Yes | `ui/json_output.py` defined; CLI global flag `--json`. |
| Q2 | Export templates (DEFERRED) | ✅ Yes | Correctly omitted. |
| Q3 | Context slicing (DEFERRED) | ✅ Yes | `ontos://` URIs absent; simple depth flags present. |
| Q4 | Git-based change detection | ⚠️ Partial | `io/git.py` includes detection, but the `log` data flow (4.3) misses the explicit "Detect -> Flag -> Confirm" interaction step decided in strategy. |
| Q5 | Pin Ontos version | ⚠️ Partial | Strategy decided "Warn on mismatch", but `.ontos.toml` schema (Sec 5.1) lacks `required_version` key to check against. |
| Q6 | Shim Hooks | ⚠️ Partial | Shim logic defined (Sec 7.1), but implementation is Unix-specific (`#!/bin/sh`), ignoring Windows support which is critical for a "Distribution" release. |
| Q7 | Auto-configure MCP clients | ✅ Yes | Omitted as decided. |
| Q8 | Progressive complexity | ✅ Yes | Sec 8.1 defines thresholds and behaviors. |
| Q9 | MCP Security | ✅ Yes | Deferred correctly. |
| Q10 | Zero-dep Core (No Pydantic) | ✅ Yes | `core/` constrained to stdlib. |
| Q11 | Script Reorganization | ✅ Yes | Comprehensive decomposition plan in Sec 2 & 3. |
| Q12 | Python Stack | ✅ Yes | Entire stack is Python. |
| Q13 | Markdown Primary | ✅ Yes | `ui/output.py` is default renderer. |

---

## 2. Correctness Review

**2a. Package Structure (Section 2)**
**Issue:** The "Pure Core" Illusion (Critical)
**Location:** Section 1.3 (Principles) vs. Section 2.2 (`ontos/core/`)
**Severity:** **Critical**
**Problem:** The architecture relies on the "Functional Core" principle ("Core logic... Pure functions (no I/O)"). However, Section 2.2 lists existing modules like `staleness.py`, `history.py`, and `proposals.py` as **"EXISTS"** (reuse as-is). In the current v2.9 codebase, these modules perform direct I/O (subprocess git calls, file reads). Moving them to `core/` without aggressive refactoring violates the architecture immediately.
**Impact:** Developers will import `subprocess` in `core/` to make the "existing" code work, rotting the architecture from day one and creating circular dependencies with `io/`.
**Proposed Fix:** Explicitly mark these modules as **"REFACTOR"**. Define a pattern where `commands/` or `io/` fetches raw data (DTOs) and passes it to `core/`.

**2b. Module Specifications (Section 3)**
**Issue:** Algorithmic Complexity Mismatch
**Location:** `core/graph.py`
**Severity:** Major
**Problem:** The spec mandates "O(V+E) DFS". The *existing* implementation (which Section 3.1 implies reusing logic from) uses `path[path.index(neighbor):]` inside the traversal loop, creating O(N²) complexity.
**Proposed Fix:** Acknowledge that `core/graph.py` requires a rewrite of the cycle detection algorithm, not just extraction.

**2c. Data Flows (Section 4)**
**Issue:** Missing Windows Support in Hooks
**Location:** Section 7.1 (Shim Hook)
**Severity:** Major
**Problem:** The shim hook is defined as `#!/bin/sh`. This will fail for Windows users (Command Prompt/PowerShell), breaking the "Distribution & Polish" promise of v3.0.
**Proposed Fix:** `commands/init.py` must detect OS and write a `pre-push.cmd` wrapper for Windows alongside the shell script.

**2d. ValidationOrchestrator (Section 3)**
**Assessment:** The pattern correctly addresses the maintainability issues (hard exits). However, it needs to explicitly handle the **normalization of error types** since legacy functions return a mix of strings, tuples, and custom objects.

---

## 3. Completeness Review

**3a. Missing Modules**
**Gap:** `ontos/core/suggestions.py` & `ontos/core/tokens.py`
**Impact:** Referenced in God Script Decomposition (Section 3.2) and Data Flows (Section 4.3), but missing from the Package Structure (Section 2.1). Logic assigned to them has nowhere to go.
**Proposed Addition:** Add them to the file tree.

**3b. Undefined Interfaces**
**Gap:** `io/toml.py` Write Interface
**Impact:** `commands/init.py` needs to write the config. `tomllib` (Python 3.11+) is read-only. Writing TOML usually requires `tomli-w` or manual string formatting to preserve comments.
**Proposed Addition:** Specify the write strategy (likely manual template filling for `init` to preserve comments, as libraries strip them).

**3c. Missing Data Flows**
**Gap:** `ontos doctor` data flow
**Impact:** This is a key v3.0 feature for user support.
**Proposed Addition:** Add a data flow diagram for `doctor`. It needs to access `io` (to check hooks), `core` (to validate schema), and `ui` (to print report).

**3d. Configuration Gaps**
**Gap:** `user.name` / `source`
**Impact:** v2.9 used `DEFAULT_SOURCE` in `ontos_config.py`. v3.0 `.ontos.toml` schema (Section 5.1) lacks a field for User Identity. Without this, `ontos log` cannot attribute sessions correctly without prompting (violating "magic defaults").
**Proposed Addition:** Add `[user] name = "..."` to schema.

**3e. Migration Gaps**
**Gap:** Safe Config Migration
**Impact:** Moving from executable Python (`ontos_config.py`) to static TOML (`.ontos.toml`) is risky. The migration strategy (Section 12.2) says "Implement config resolution" but doesn't explain how to safely extract values from a user's Python script without side effects.
**Proposed Addition:** Specify an AST-based extraction approach or a "Import & Dump" subprocess strategy.

---

## 4. Consistency Review

**4b. Module Specs vs Constraints**
**Inconsistency:** `core/validation.py` spec claims "MUST NOT call `print()`". The existing `validate_dependencies` logic (which it consumes) prints heavily.
**Resolution:** Explicitly state that extracted logic must be stripped of `print()` calls, with messages returned in `ValidationError` objects.

**4c. Line Counts**
**Suspicious Estimate:** `ontos_end_session.py` is 1,904 lines. The decomposition targets (Section 3.2) account for ~1,150 lines.
**Gap:** ~750 lines unaccounted for.
**Resolution:** This suggests significant logic might be dropped or the estimation is overly optimistic. A more granular audit of the "God Script" is needed.

---

## 5. Risk Assessment

**5a. Implementation Risks**
**Risk:** **Purity Refactoring.** The effort to separate logic from I/O in existing scripts (`staleness.py`, `proposals.py`) is underestimated.
**Likelihood:** High
**Impact:** High (Architectural Rot)
**Mitigation:** Adopt the "Strict IO/Core Separation Plan" (see Section 6).

**5c. Backward Compatibility Risk**
**Risk:** **Hook Breakage.** Existing repos have legacy hooks calling `.ontos/scripts/...`.
**Likelihood:** 100%
**Impact:** Medium
**Mitigation:** `ontos init` must explicitly **replace** (overwrite) legacy hooks with the new shim, rather than just installing if missing.

**5d. v4.0 Readiness Risk**
**Risk:** **Output Coupling.** If `ui/output.py` hardcodes `sys.stdout`, the future MCP server cannot capture output to send back to the client.
**Likelihood:** Medium
**Impact:** High for v4
**Mitigation:** Ensure `OutputHandler` accepts a stream argument (Dependency Injection).

---

## 6. Proposed Changes

#### Change Proposal: Strict IO/Core Separation Plan

**Problem:** Section 12.1 assumes "Reuse As-Is" for `core/` modules, but they currently contain I/O, violating Section 1.3 constraints.
**Proposed Change:**

1. Mark `staleness.py`, `proposals.py`, `history.py` as **"REFACTOR"** in Section 2.2/12.1.
2. Create corresponding `io/` modules (e.g., `io/git_history.py`) to handle side effects.
3. Mandate that `core/` functions accept data objects (DTOs), not fetch data.
**Rationale:** Preserves architectural integrity and enables unit testing.
**Impact:** Section 2.2, 12.1. Effort: Medium (Critical).

#### Change Proposal: Windows-Compatible Hooks

**Problem:** Shim hook is Unix-only (`#!/bin/sh`).
**Proposed Change:**
Update `commands/init.py` spec to:

1. Detect OS.
2. If Windows, write `pre-push.cmd` alongside the sh script.
3. Content: `@ontos hook pre-push %*`
**Rationale:** Real "Distribution" support requires Windows compatibility.
**Impact:** Section 7.1. Effort: Low.

#### Change Proposal: Vendor `tomli`

**Problem:** "Zero-Dep" rule clashes with Python 3.9/3.10 support (no `tomllib`).
**Proposed Change:**
Add `ontos/vendor/` directory containing `tomli` (and `tomli-w` if needed). Update Section 2.1 to include it.
**Rationale:** Pragmatic solution to "Zero-Dep" while supporting older Python versions without requiring users to install separate packages via pip (keeping install fast/light).
**Impact:** Section 2.1. Effort: Low.

#### Change Proposal: Golden Master Testing

**Problem:** High risk of regression when splitting 1,904-line script.
**Proposed Change:**
Add "Phase 0" to Migration Strategy: Create integration tests that run v2 scripts, capture `stdout` and file artifacts (logs, map), and assert v3 commands produce identical output.
**Rationale:** Safety net for the "Polish" release.
**Impact:** Section 9. Effort: Medium.

---

## 7. Summary Assessment

**Overall Quality:** **Strong**
The architecture is well-aligned with the strategic decisions and correctly identifies the "God Script" decomposition as the primary challenge. The `ValidationOrchestrator` and `Package Structure` are excellent implementations of the "Distribution & Polish" theme.

**Strengths:**

* **Layering:** Clear separation of concerns (CLI / Command / Core / IO).
* **Orchestration:** Solving the "Hard Exit" problem with `ValidationResult`.
* **Distribution:** Shim hooks bridge the gap between global install and local enforcement.

**Critical Issues:** (Must fix before implementation)

1. **The "Pure Core" Illusion:** Listing I/O-heavy modules as "Reuse As-Is" is a trap. They must be refactored.
2. **Windows Incompatibility:** Hooks must support Windows/Cmd.
3. **Missing Config Fields:** `required_version` and `user.name` are missing from the schema.

**Recommendation:** **Approve with Changes**
(Specifically: Adopt the IO/Core Separation Plan, Windows Hooks proposal, and Golden Master testing strategy).