# Phase 4 Spec Review: Peer Reviewer

**Reviewer:** Gemini (Peer)
**Model:** Gemini 2.5 Pro
**Date:** 2026-01-13
**Spec Version:** 1.0
**Role:** Quality, Completeness & UX

---

## 1. Overall Assessment

| Aspect | Rating | Notes |
|--------|--------|-------|
| Completeness | Good | Covers all deliverables, including new commands and UI. |
| Clarity | Good | Technical design for each component is detailed. |
| Implementability | Ready | Code snippets are high quality and usable. |
| User Experience | Good | Doctor and Export commands add significant value. |

---

## 2. Open Questions Research

### 2.1 Doctor Command Scope

**Research conducted:**
- **npm doctor:** Checks registry, versions, permissions, cache integrity.
- **brew doctor:** Checks overall health, outdated tools, unbrewed files.
- **cargo:** No direct equivalent; `cargo check` is for code.

**Recommendation:** **Option B (Standard)**
**Confidence:** High
**Reasoning:** The 7 checks in the spec (Config, Hooks, Python, Docs, Map, Validation, CLI) perfectly map to `npm doctor`'s "environment + integrity" model. Option C (network/disk) is overkill for v3.0.

### 2.2 Wrapper Command Migration

**Research conducted:**
- **Strangler Fig Pattern:** Incrementally replace legacy systems.
- **SemVer:** Breaking changes (removing wrappers) require major version.

**Recommendation:** **Option A (Keep wrappers)**
**Confidence:** High
**Reasoning:** v3.0 is already a massive architectural shift. Migrating 8 non-critical wrappers adds risk without immediate user value. The "Strangler Fig" approach supports keeping them until v4.0.

### 2.3 JSON Output for Wrappers

**Research conducted:**
- **Best Practices:** Consistent schema is key (`status`, `data`).
- **Passthrough:** Risky if legacy output is unstructured text.

**Recommendation:** **Option A with strict fallback.**
**Confidence:** Medium
**Reasoning:** Attempting to wrap legacy output in JSON is error-prone. Better to pass through the flag if supported, or error out if not. The spec's suggestion to return an error JSON is the safest/cleanest UX for automation tools.

### 2.4 Exit Code for Warnings

**Research conducted:**
- **CI/CD Best Practices:** Exit 0 = Success (proceed). Exit non-zero = Fail (stop).
- **Linters:** Often allow "warn-only" mode (exit 0).

**Recommendation:** **Option A (Exit 0)**
**Confidence:** High
**Reasoning:** Warnings shouldn't break CI builds unless `--strict` is used. This aligns with standard linter behavior.

### 2.5 Legacy Script Deprecation

**Research conducted:**
- **Deprecation Policies:** Mark deprecated before removal.
- **Breaking Changes:** Ontos v3.0 IS a breaking change (Major version).

**Recommendation:** **Option A (Immediate deletion for internal scripts)**
**Confidence:** High
**Reasoning:** `ontos_install_hooks.py` etc. are internal implementation details. Users shouldn't be calling them directly. For `ontos.py` (entry point), keep it until v4.0 to support the wrappers.

---

## 3. CLI Design Review

### 3.1 Command Structure

| Command | Specified? | Clear? | Issues |
|---------|------------|--------|--------|
| ontos init | ✅ | ✅ | None |
| ontos map | ✅ | ✅ | None |
| ontos doctor | ✅ | ✅ | None |
| ontos export | ✅ | ✅ | None |
| ontos hook | ✅ | ✅ | None |

### 3.2 Global Options

| Option | Specified? | Behavior Clear? |
|--------|------------|-----------------|
| --version | ✅ | ✅ |
| --help | ✅ | ✅ |
| --json | ✅ | ✅ |
| --quiet | ✅ | ✅ |

### 3.3 UX Coherence

| Question | Answer |
|----------|--------|
| Is command naming consistent? | Yes (verb-noun style) |
| Are flags consistent? | Yes (--force, --json) |
| Is help text adequate? | Yes |
| Are error messages user-friendly? | Yes (JsonOutputHandler helps) |

---

## 4. New Commands Review

### 4.1 doctor.py

| Aspect | Assessment |
|--------|------------|
| Purpose clear | ✅ |
| Checks specified | ✅ (7 checks) |
| Output format defined | ✅ |
| Exit codes defined | ✅ |
| Useful to users | Yes |

**Issues:**
| Issue | Severity |
|-------|----------|
| Missing network check | Minor |

**Suggestions:**
- Consider checking if `git` executable is actually available (not just `.git` dir).

### 4.2 export.py

| Aspect | Assessment |
|--------|------------|
| Purpose clear | ✅ |
| Output format defined | ✅ |
| Template specified | ✅ |
| Useful to users | Yes |

**Issues:**
| Issue | Severity |
|-------|----------|
| Single template | Minor |

**Suggestions:**
- The template should explicitly list **Commands** and **Project Structure** sections to be filled in, or auto-generate them if possible.

### 4.3 hook.py

| Aspect | Assessment |
|--------|------------|
| Purpose clear | ✅ |
| Routing logic defined | ✅ |
| Exit code handling | ✅ |

**Issues:**
None.

---

## 5. JSON Output Review

| Aspect | Assessment |
|--------|------------|
| Schema defined | ✅ |
| Consistent across commands | ✅ |
| Error representation | ✅ |
| Follows conventions | ✅ |

**Schema issues:**
None. The `{status, message, data, error_code}` schema is standard and robust.

---

## 6. Migration Guide Review

| Question | Answer |
|----------|--------|
| Covers all legacy scripts | Yes |
| Clear upgrade path | Yes |
| Examples provided | Yes |
| Breaking changes documented | Yes |

**Missing from guide:**
- Explicit mention of `ontos_config.py` being ignored/replaced by `.ontos.toml` (needs emphasis).

---

## 7. Test Strategy Review

| Aspect | Assessment |
|--------|------------|
| Unit tests specified | ✅ |
| Integration tests specified | ✅ |
| Cross-platform tests specified | ✅ |
| Deletion verification specified | ✅ |

---

## 8. Issues Summary

### Critical (Blocks Implementation)
None.

### Major (Should Fix)
None.

### Minor (Consider)

| # | Issue | Section | Suggestion |
|---|-------|---------|------------|
| P-m1 | Migration guide visibility | 11 | Emphasize `ontos_config.py` deprecation more strongly. |
| P-m2 | Doctor check robustness | 4.2 | Check `git --version` execution, not just `.git` folder presence. |

---

## 9. Positive Observations

| Strength | Section |
|----------|---------|
| **Doctor Command** | 4.2 | The 7-point health check is excellent for reducing support burden. |
| **JSON Schema** | 4.5 | The `JsonOutputHandler` design ensures consistency across the CLI. |
| **Shim Design** | 4.6 | The 3-method fallback in the python shim is extremely robust. |
| **Strangler Pattern** | 2.3 | The deletion plan is safe and methodical. |

---

## 10. Verdict

**Recommendation:** Approve

**Open questions answered:** 5/5

**Blocking issues:** 0

**Summary:** This is a high-quality spec. The "Ship it" theme is well-supported by robust designs for `doctor` and `hook` commands. The JSON output strategy is mature. The legacy deletion plan manages risk effectively. I strongly support the decision to keep wrapper commands for v3.0 to reduce risk.

---

**Review signed by:**
- **Role:** Peer Reviewer
- **Model:** Gemini 2.5 Pro
- **Date:** 2026-01-13
- **Review Type:** Spec Review (Phase 4 Implementation)

*End of Peer Spec Review*