# Phase 0 Implementation Spec Review

**Reviewer:** Gemini CLI (powered by Gemini 2.0 Flash)
**Date:** 2026-01-12
**Spec Version:** 1.0

---

## 1. Roadmap Alignment

### 1.1 Deliverables Check

| Roadmap Deliverable | Present in Spec? | Adequate? | Notes |
|---------------------|------------------|-----------|-------|
| Golden Master fixtures (small/medium/large) | Yes | Yes | All three sizes are defined with specific directory structures and content examples. |
| Capture scripts | Yes | Yes | `capture_golden_master.py` is provided in full. |
| Comparison harness | Yes | Yes | `compare_golden_master.py` is provided in full. |
| Baseline documentation | Yes | Yes | Included in the `tests/golden/README.md` section. |

### 1.2 Tasks Check

| Roadmap Task | Present in Spec? | Adequate Detail? | Notes |
|--------------|------------------|------------------|-------|
| Create `tests/fixtures/golden/small/` | Yes | Yes | Explicit directory structure provided. |
| Create `tests/fixtures/golden/medium/` | Yes | Yes | Structure outlined, though less granular than small (acceptable). |
| Create `tests/fixtures/golden/large/` | Yes | Yes | High-level structure provided (acceptable for large fixture). |
| Create `.ontos.toml` for each fixture | Yes | Yes | Included in fixture definitions. |
| Write `capture_golden_master.py` | Yes | Yes | Full code provided. |
| Write `compare_golden_master.py` | Yes | Yes | Full code provided. |
| Document baseline in README | Yes | Yes | `tests/golden/README.md` content provided. |
| Add to CI | Yes | Yes | `.github/workflows/golden-master.yml` provided. |

### 1.3 Exit Criteria Check

| Roadmap Exit Criterion | Spec Addresses? | How Verified? |
|------------------------|-----------------|---------------|
| All three fixture sizes created | Yes | Section 6.3 Checklist explicitly includes this. |
| Capture script records v2.9.x behavior | Yes | The script logic copies the *current* `ontos.py` and `.ontos/` into the fixture to run, ensuring it captures the current state. |
| Comparison harness runs clean | Yes | Section 6.2 Manual Verification steps include confirming this. |
| Baseline documentation complete | Yes | Section 5.2 defines the README content. |
| CI integration configured | Yes | Section 5.1 defines the workflow file. |

### 1.4 Alignment Verdict

**Roadmap Alignment:** **Strong**

The spec meticulously follows the Roadmap requirements for Phase 0. Every deliverable and task is accounted for with concrete implementation details.

---

## 2. Architecture Alignment

### 2.1 Relevant Architecture Sections

| Architecture Section | Relevance to Phase 0 | Spec Respects? |
|---------------------|---------------------|----------------|
| Section 1.3 (Core Principles) | Fixtures should reflect principles | **Yes** - Fixtures use the standard directory structure. |
| Section 3 (Package Structure) | Fixture paths should align | **N/A** - Phase 0 captures *v2.9.x* behavior, so it correctly uses the *old* structure (`.ontos/scripts`) to establish the baseline. |
| Section 5 (Data Flows) | Capture should cover these flows | **Yes** - Captures `map` and `log` command outputs and side effects. |
| Section 6 (Configuration) | `.ontos.toml` in fixtures | **Yes** - Fixtures include `.ontos.toml` to test forward compatibility of config loading or at least its presence. |
| Section 13 (Migration Strategy) | Golden Master supports this | **Yes** - Explicitly designed as the safety net for migration. |

### 2.2 Architectural Concerns

The spec correctly uses the *v2.9.x* execution model (copying `ontos.py` and `.ontos/` into the fixture) to capture the baseline. This is architecturally sound for a Golden Master test: strict adherence to the *current* state is required to detect regressions in the *future* state.

One minor point: The spec uses `sys.executable` to run `ontos.py`. This aligns with the v2.x invocation method and ensures the test runs in the correct Python environment.

### 2.3 Alignment Verdict

**Architecture Alignment:** **Strong**

---

## 3. Strategy Alignment

### 3.1 Relevant Strategy Decisions

| Decision | How Spec Supports | Adequate? |
|----------|-------------------|-----------|
| Q1: JSON output mode | Capture should include `--json` output | **No** - The spec currently captures stdout/stderr but doesn't explicitly mention capturing a separate JSON baseline. |
| Q4: Git-based detection | Fixtures should include git state | **Yes** - `setup_fixture` explicitly initializes a git repo and commits files. |
| Q8: Large project handling | Large fixture tests this | **Yes** - "Large" fixture with 100+ documents is defined. |
| Q11: Script reorganization | Golden Master enables safe refactoring | **Yes** - This is the primary purpose of the spec. |

### 3.2 Strategy Concerns

**Q1 (JSON Output):** Strategy Q1 prioritizes JSON output for v3.0. While v2.9.x might not have full JSON support yet, if any exists or if v3.0 adds it immediately, the Golden Master might need to account for it eventually. However, since this is capturing *v2.9.x* behavior, and v2.9.x is primarily text-based, the current spec is correct for the *baseline*.

**Q4 (Git Detection):** The spec's `capture_log_command` modifies a file and commits it before running `log`. This accurately simulates the conditions needed for v3.0's git-based detection logic to be tested against the v2 behavior (which relied on `git status` / `git log` differently).

### 3.3 Alignment Verdict

**Strategy Alignment:** **Strong**

The spec focuses on locking in current behavior to enable the strategic refactoring.

---

## 4. Spec Quality Assessment

### 4.1 Completeness

| Aspect | Rating | Notes |
|--------|--------|-------|
| File specifications complete | **Complete** | Full file contents provided for fixtures and scripts. |
| Code provided is runnable | **Mostly** | `capture_golden_master.py` imports `normalize_output` which is defined in the same file, but `compare_golden_master.py` tries to import it from `capture_golden_master`. This assumes they are in the same directory and `capture_golden_master` is importable (valid if run as script from that dir). |
| Task ordering clear | **Yes** | Section 7.2 provides a clear recommended order. |
| Dependencies explicit | **Yes** | Standard library usage is emphasized; `pytest` mentioned for CI. |
| Verification steps clear | **Yes** | Section 6 provides manual and CI verification steps. |

### 4.2 Clarity

| Aspect | Rating | Notes |
|--------|--------|-------|
| Instructions unambiguous | **Yes** | Very clear distinction between what is fixture data and what is test logic. |
| No design decisions left to implementer | **Yes** | Normalization regexes are provided, file structures are defined. |
| Edge cases addressed | **Mostly** | Timestamps and paths are handled. Git initialization handling is robust. |

### 4.3 Implementability

- [x] File paths are specific
- [x] Code is copy-paste ready
- [x] Order of operations is clear
- [x] Success criteria are testable
- [x] No blocking ambiguities

### 4.4 Quality Verdict

**Spec Quality:** **High**

The code provided is robust, handling setup/teardown of fixtures and normalization of output effectively.

---

## 5. Missing Elements

### 5.1 Required but Missing

None. The spec is actionable as-is.

### 5.2 Should Have but Missing

| Missing Item | Why Useful | Severity |
|--------------|------------|----------|
| `.gitignore` for `tests/golden/` | To prevent accidental commit of generated fixture temp dirs or baselines if the user workflow differs from the script's strict paths. | Minor |

### 5.3 Not Missing

No significant gaps found.

---

## 6. Suggested Additions

### 6.1 Recommendations

| Suggestion | Benefit | Effort | Priority |
|------------|---------|--------|----------|
| Add `__init__.py` to `tests/golden/` | Ensures `capture_golden_master.py` is importable by `compare_golden_master.py` without `sys.path` hacks. | Low | High |
| Add explicit `.gitignore` entry | Keeps the repo clean from test artifacts. | Low | Medium |

### 6.2 Rationale

1.  **`__init__.py`**: The `compare_golden_master.py` script imports from `capture_golden_master`. Depending on how these scripts are invoked (e.g., `python tests/golden/compare...` vs `cd tests/golden && python compare...`), Python import mechanics might fail without the directory being treated as a package or explicit path manipulation. Adding an empty `__init__.py` makes it a package, simplifying imports.
2.  **`.gitignore`**: Standard hygiene for test directories generating artifacts.

### 6.3 Explicitly NOT Suggesting

*   **Mocking Git**: The spec uses real git commands. I am *not* suggesting mocking this, as the interplay between the python scripts and the git subprocess calls is exactly what needs to be regression-tested.
*   **Performance Benchmarks**: The spec explicitly excludes them. I agree; strict output comparison is hard enough without adding timing variance.

---

## 7. Concerns and Risks

### 7.1 Implementation Risks

| Risk | Likelihood | Impact | Mitigation in Spec? |
|------|------------|--------|---------------------|
| **Normalization Fragility** | Medium | Medium | **Yes** - Regexes are provided, but heavily dependent on exact output format. If v2.9.x output varies slightly (e.g., different terminal width wrapping), comparisons might fail. |
| **Git Version Differences** | Low | Low | **No** - `git status` or `diff` output might vary slightly between git versions. Not explicitly handled but low risk for the specific commands used. |

### 7.2 Spec-Specific Concerns

*   **Normalization Logic Duplication:** The `compare_golden_master.py` script imports normalization logic from `capture_golden_master.py`. This is good for consistency but creates a runtime dependency. The implementation team must ensure `capture_golden_master.py` is available in the environment where `compare_golden_master.py` runs (CI). The Spec handles this by placing them in the same directory, which is sufficient.

---

## 8. Summary Assessment

### 8.1 Verdicts

| Area | Verdict |
|------|---------|
| Roadmap Alignment | **Strong** |
| Architecture Alignment | **Strong** |
| Strategy Alignment | **Strong** |
| Spec Quality | **High** |

### 8.2 Overall Recommendation

**Recommendation:** **Ready to Implement**

This is a high-quality spec that provides exactly what is needed to build the safety net for the v3.0 refactor. The code is pragmatic, the scope is well-defined, and the verification steps are clear.

### 8.3 Blocking Issues

None.

### 8.4 Top 3 Improvements

1.  Add `tests/golden/__init__.py` to ensure imports work smoothly.
2.  Add a `.gitignore` for `tests/golden/fixtures/` and `tests/golden/baselines/` (if baselines aren't committed immediately).
3.  Double-check `normalize_output` regexes against actual `ontos` output on the dev machine before committing the first baseline.

### 8.5 Strengths

*   **Code-Complete:** The provided Python scripts are substantial and look logic-complete.
*   **Normalization Strategy:** The regex-based normalization strategy is the correct approach for snapshot testing CLI tools.
*   **Fixture Isolation:** The `setup_fixture` function correctly isolates tests in temp directories and handles git initialization, which is crucial for this tool.

---

*End of Review*
