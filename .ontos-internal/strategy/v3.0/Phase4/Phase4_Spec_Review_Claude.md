# Phase 4 Spec Review: Alignment Reviewer

**Reviewer:** Claude (Alignment)
**Model:** Claude Opus 4.5
**Date:** 2026-01-13
**Spec Version:** 1.0
**Role:** Roadmap & Architecture Compliance

---

## 1. Roadmap Section 6 Compliance

### 1.1 Deliverables Check

| Roadmap Deliverable | In Spec? | Correctly? | Notes |
|---------------------|----------|------------|-------|
| `cli.py` full argparse | ✅ | ✅ | Spec 4.1 |
| `commands/doctor.py` | ✅ | ✅ | Spec 4.2 |
| `commands/hook.py` | ✅ | ✅ | Spec 4.3 |
| `commands/export.py` | ✅ | ✅ | Spec 4.4 |
| `ui/json_output.py` | ✅ | ⚠️ | Spec 4.5 differs from Roadmap 6.7 method names |
| Shim hooks | ✅ | ✅ | Spec 4.6 |
| Deletion | ✅ | ❌ | Spec 4.7 omits `install.py` and archive requirement |

### 1.2 Command Checklist (Roadmap 6.2)

| Command | Roadmap Status | Spec Status | Match? |
|---------|----------------|-------------|--------|
| ontos init | ✅ rc | Native | ✅ |
| ontos map | ✅ beta | Native | ✅ |
| ontos log | ✅ beta | Native | ✅ |
| ontos doctor | NEW | NEW | ✅ |
| ontos export | NEW | NEW | ✅ |
| ontos verify | Migrate | Wrapper | ✅ |
| ontos query | Migrate | Wrapper | ✅ |
| ontos migrate | Migrate | Wrapper | ✅ |
| ontos consolidate | Migrate | Wrapper | ✅ |
| ontos promote | Migrate | Wrapper | ✅ |
| ontos scaffold | Migrate | Wrapper | ✅ |
| ontos stub | Migrate | Wrapper | ✅ |
| ontos hook | NEW | NEW | ✅ |

### 1.3 JSON Support (Roadmap 6.2)

| Command | Roadmap JSON | Spec JSON | Match? |
|---------|--------------|-----------|--------|
| ontos init | ✅ | Yes | ✅ |
| ontos map | ✅ | Yes | ✅ |
| ontos doctor | ✅ | Yes | ✅ |
| ontos export | ❌ | No | ✅ |
| ontos hook | ❌ | No | ✅ |

---

## 2. Architecture Compliance

### 2.1 Layer Constraints

| Constraint | Spec Respects? | Evidence |
|------------|----------------|----------|
| core/ no io imports | ✅ | Spec maintains layer separation in design |
| core/ stdlib-only | ✅ | No non-stdlib deps in core in spec |
| io/ may import core | ✅ | Consistent with architecture |
| commands/ may import both | ✅ | Spec 4.x commands orchestrate core + io |
| ui/ placement correct | ✅ | Spec 4.5, 4.8 |

### 2.2 New Module Placement

| Module | Proposed Location | Correct? |
|--------|-------------------|----------|
| doctor.py | commands/ | ✅ |
| hook.py | commands/ | ✅ |
| export.py | commands/ | ✅ |
| json_output.py | ui/ | ✅ |

---

## 3. Exit Code Consistency

| Exit Code | Phase 3 Meaning | Phase 4 Meaning | Consistent? |
|-----------|-----------------|-----------------|-------------|
| 0 | Success | Success | ✅ |
| 1 | Already initialized | Validation error / Already exists | ❌ |
| 2 | Not a git repo | Not a git repository / Config error | ❌ |
| 3 | Hooks skipped | Hooks skipped | ⚠️ (Roadmap 6.3 uses 3 = user input error) |
| 4 | N/A | Git error | ⚠️ (Roadmap 6.3 reserves 4 for git error across commands) |
| 5 | N/A | Internal error | ✅ |

---

## 4. Strategy Alignment

| Strategy Decision | Spec Reflects? | Evidence |
|-------------------|----------------|----------|
| Q1: JSON output mode | ✅ | Spec 3.1, 4.5 |
| Q2: Export templates deferred to v4 | ❌ | Spec 4.4 adds CLAUDE.md export (scope expansion) |
| Q6: Shim hooks | ✅ | Spec 4.6 |
| Q13: Markdown primary | ✅ | Spec 4.4 template is Markdown |

---

## 5. Previous Phase Integration

| Phase 3 Output | Phase 4 Uses Correctly? | Notes |
|----------------|-------------------------|-------|
| Config system | ✅ | Uses `.ontos.toml`, config checks in doctor |
| commands/ structure | ✅ | CLI routes to native commands |
| Hook installation | ✅ | Phase 4 extends with dispatcher |

---

## 6. Deviations Found

### 6.1 Roadmap Deviations

| Deviation | Roadmap Says | Spec Says | Severity |
|-----------|--------------|-----------|----------|
| Exit code mapping | 6.3 defines 1=validation, 2=config, 3=user input, 4=git | 7 defines 1=validation/exists, 2=git/config, 3=hooks skipped | Major |
| Deletion tasks | 6.10 delete `install.py`, archive `.ontos/scripts/` | 4.7 omits `install.py` and archive step | Major |
| JSON handler API | 6.7 specifies `result()` + converters | 4.5 specifies `success()` and no converters | Minor |

### 6.2 Architecture Violations

| Violation | Constraint | Spec Section | Severity |
|-----------|------------|--------------|----------|
| None | N/A | N/A | N/A |

### 6.3 Unauthorized Changes

| Change | Why Unauthorized | Severity |
|--------|------------------|----------|
| Export command vs Strategy Q2 | Q2 defers export templates to v4 | Major |

---

## 7. Issues Summary

### Critical (Alignment)

| # | Issue | Reference | Why Critical |
|---|-------|-----------|--------------|
| A-C1 | None | N/A | N/A |

### Major (Alignment)

| # | Issue | Reference | Recommendation |
|---|-------|-----------|----------------|
| A-M1 | Exit code mapping mismatch | Roadmap 6.3 vs Spec 7 | Align exit codes to Roadmap 6.3 definitions |
| A-M2 | Deletion tasks incomplete | Roadmap 6.10 vs Spec 4.7 | Add `install.py` deletion and archive `.ontos/scripts/` |
| A-M3 | Export scope vs Strategy Q2 | Strategy Q2 | Justify scope expansion or defer export to v4 |

### Minor (Alignment)

| # | Issue | Reference | Recommendation |
|---|-------|-----------|----------------|
| A-m1 | JSON handler API deviation | Roadmap 6.7 | Either align API names or update roadmap references |

---

## 8. Verdict

**Alignment Status:** Major Deviations

**Recommendation:** Request changes

**Blocking deviations:** 3

**Summary:** The spec covers required deliverables but diverges from Roadmap exit code definitions, deletion tasks, and Strategy Q2 export scope. Align these items or explicitly update the roadmap/strategy references before implementation.

---

**Review signed by:**
- **Role:** Alignment Reviewer
- **Model:** Claude Opus 4.5
- **Date:** 2026-01-13
- **Review Type:** Spec Review (Phase 4 Implementation)

*End of Alignment Spec Review*
