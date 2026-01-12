# Phase 0 Implementation Spec Review

**Reviewer:** Codex (GPT-5)
**Date:** 2026-01-12
**Spec Version:** 1.0

---

## 1. Roadmap Alignment

### 1.1 Deliverables Check

| Roadmap Deliverable | Present in Spec? | Adequate? | Notes |
|---------------------|------------------|-----------|-------|
| Golden Master fixtures (small/medium/large) | Yes | Yes | Structures and key behaviors defined. |
| Capture scripts | Yes | Mostly | Script exists, but path differs from roadmap (`tests/golden/` vs `scripts/`). |
| Comparison harness | Yes | Mostly | Exists, but does not compare stderr or session_log. |
| Baseline documentation | Yes | Yes | `tests/golden/README.md` is detailed. |

### 1.2 Tasks Check

| Roadmap Task | Present in Spec? | Adequate Detail? | Notes |
|--------------|------------------|------------------|-------|
| Create `tests/fixtures/golden/small/` | Partial | Mostly | Spec uses `tests/golden/fixtures/small/` instead of roadmap path. |
| Create `tests/fixtures/golden/medium/` | Partial | Mostly | Same path mismatch. |
| Create `tests/fixtures/golden/large/` | Partial | Mostly | Same path mismatch. |
| Create `.ontos.toml` for each fixture | Partial | No | Only small fixture includes `.ontos.toml`. |
| Write `capture_golden_master.py` | Yes | Mostly | Spec locates in `tests/golden/`, roadmap expects `scripts/`. |
| Write `compare_golden_master.py` | Yes | Mostly | Path mismatch; comparison is incomplete. |
| Document baseline in README | Yes | Yes | Clear steps and normalization rules. |
| Add to CI | Yes | Yes | Workflow provided. |

### 1.3 Exit Criteria Check

| Roadmap Exit Criterion | Spec Addresses? | How Verified? |
|------------------------|-----------------|---------------|
| All three fixture sizes created | Yes | Section 2 + checklist. |
| Capture script records v2.9.x behavior | Yes | Section 3 + verification steps. |
| Comparison harness runs clean | Partial | Compare script ignores stderr and session_log. |
| Baseline documentation complete | Yes | README. |
| CI integration configured | Yes | GitHub Actions workflow. |

### 1.4 Alignment Verdict

**Roadmap Alignment:** Adequate

**Gaps:** Path mismatch for fixture/capture/compare locations; missing `.ontos.toml` for medium/large; comparison harness doesn’t validate stderr/session log.

---

## 2. Architecture Alignment

### 2.1 Relevant Architecture Sections

| Architecture Section | Relevance to Phase 0 | Spec Respects? |
|---------------------|---------------------|----------------|
| Section 1.3 (Core Principles) | Fixtures should reflect principles | Yes |
| Section 3 (Package Structure) | Fixture paths should align | N/A |
| Section 5 (Data Flows) | Capture should cover these flows | Yes |
| Section 6 (Configuration) | `.ontos.toml` in fixtures | Partial |
| Section 13 (Migration Strategy) | Golden Master supports this | Yes |

### 2.2 Architectural Concerns

- The capture/compare scripts assume `ontos.py` exists at project root. That aligns with v2.9.x, but once Phase 1 begins (package layout), this invocation may need to move to `python -m ontos` or `ontos`. The spec should clarify how the harness is expected to run after packaging changes.

### 2.3 Alignment Verdict

**Architecture Alignment:** Adequate

---

## 3. Strategy Alignment

### 3.1 Relevant Strategy Decisions

| Decision | How Spec Supports | Adequate? |
|----------|-------------------|-----------|
| Q1: JSON output mode | No JSON capture/compare included | No |
| Q4: Git-based detection | Fixtures initialize git and commit | Yes |
| Q8: Large project handling | Large fixture defined | Yes |
| Q11: Script reorganization | Golden Master enables safe refactoring | Yes |

### 3.2 Strategy Concerns

- Missing JSON output coverage weakens Q1 validation and risks regressions in machine-readable mode.

### 3.3 Alignment Verdict

**Strategy Alignment:** Adequate

---

## 4. Spec Quality Assessment

### 4.1 Completeness

| Aspect | Rating | Notes |
|--------|--------|-------|
| File specifications complete | Partial | Medium/large `.ontos.toml` not specified. |
| Code provided is runnable | Mostly | Git commit needs user.name/email in some environments. |
| Task ordering clear | Yes | Step-by-step order is reasonable. |
| Dependencies explicit | Mostly | Assumes `git` + `python` + v2.9.x layout. |
| Verification steps clear | Yes | Commands + expected outcomes provided. |

### 4.2 Clarity

| Aspect | Rating | Notes |
|--------|--------|-------|
| Instructions unambiguous | Mostly | Path mismatch vs roadmap introduces ambiguity. |
| No design decisions left to implementer | Mostly | Fixture location decision is still open. |
| Edge cases addressed | Partial | Git config + stderr/session log comparisons not covered. |

### 4.3 Implementability

- [x] File paths are specific
- [x] Code is copy-paste ready
- [x] Order of operations is clear
- [x] Success criteria are testable
- [ ] No blocking ambiguities

### 4.4 Quality Verdict

**Spec Quality:** Adequate

---

## 5. Missing Elements

### 5.1 Required but Missing

| Missing Item | Why Required | Severity |
|--------------|--------------|----------|
| Compare stderr and session_log outputs | Roadmap requires capturing generated files and stderr; harness currently ignores them | Major |
| `.ontos.toml` defined for medium/large fixtures | Roadmap task requires config for each fixture | Major |
| JSON output mode capture/compare | Strategy Q1 requires JSON behavior preservation | Major |

### 5.2 Should Have but Missing

| Missing Item | Why Useful | Severity |
|--------------|------------|----------|
| Git user config setup in scripts | Avoids failures on fresh environments/CI | Minor |
| Clarify post-Phase1 command invocation (`ontos` vs `ontos.py`) | Reduces churn when package layout changes | Minor |

### 5.3 Not Missing

No other significant gaps found.

---

## 6. Suggested Additions

### 6.1 Recommendations

| Suggestion | Benefit | Effort | Priority |
|------------|---------|--------|----------|
| Add stderr + session_log comparisons | Completes regression coverage | Low | High |
| Add JSON capture/compare path (e.g., `ontos map --json`, `ontos log --json`) | Protects Q1 decision | Low | High |
| Specify `.ontos.toml` for medium/large fixtures | Ensures config path coverage | Low | High |
| Standardize path to match roadmap (`tests/fixtures/golden/`) or update roadmap | Removes ambiguity | Low | Med |
| Configure git user in scripts (`git -c user.name=...`) | Prevents environment failures | Low | Med |

### 6.2 Rationale

Each suggestion strengthens coverage without expanding scope: they are still Phase 0 safety-net tasks, align with the approved roadmap and strategy (especially Q1), and reduce implementation surprises.

### 6.3 Explicitly NOT Suggesting

- Not suggesting performance benchmarks or extra commands beyond `map` and `log`; this would expand Phase 0 scope.

---

## 7. Concerns and Risks

### 7.1 Implementation Risks

| Risk | Likelihood | Impact | Mitigation in Spec? |
|------|------------|--------|---------------------|
| Git commits fail due to missing user config | M | M | No |
| Regression in stderr/session log output goes undetected | M | M | No |
| JSON output regressions undetected | M | M | No |
| `ontos.py` path breaks after packaging changes | M | M | Partial |

### 7.2 Spec-Specific Concerns

- Path mismatch (tests/golden vs tests/fixtures/golden, scripts vs tests) could lead to parallel implementations or partial coverage.

---

## 8. Summary Assessment

### 8.1 Verdicts

| Area | Verdict |
|------|---------|
| Roadmap Alignment | Adequate |
| Architecture Alignment | Adequate |
| Strategy Alignment | Adequate |
| Spec Quality | Adequate |

### 8.2 Overall Recommendation

**Recommendation:** Minor Revisions

### 8.3 Blocking Issues

- Compare stderr and session_log outputs.
- Add JSON output capture/compare.
- Define `.ontos.toml` for medium and large fixtures.

### 8.4 Top 3 Improvements

1. Complete comparison harness (stderr + session_log).
2. Add JSON output baselines.
3. Align fixture/script paths with roadmap (or update roadmap explicitly).

### 8.5 Strengths

- Clear fixture design with realistic coverage of status types and dependencies.
- Scripts are detailed and implementable with minimal guesswork.
- Baseline documentation and CI integration are well specified.

---

*End of Review (Codex)*
