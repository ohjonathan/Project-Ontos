# Phase 4 Spec Review: Consolidation

**Date:** 2026-01-13
**Spec Version:** 1.0
**Reviews Consolidated:** 3 (Peer, Alignment, Adversarial)

---

## 1. Verdict Summary

| Reviewer | Role | Model | Verdict | Blocking Issues |
|----------|------|-------|---------|-----------------|
| Gemini | Peer | Gemini 2.5 Pro | Approve | 0 |
| Claude | Alignment | Claude Opus 4.5 | Request changes | 3 |
| Codex | Adversarial | Codex (OpenAI) | Request changes | 2 |

**Consensus:** 1/3 Approve. **Needs Revision.**

**Overall Recommendation:** Needs revision to align with Roadmap Section 6 and harden the legacy deletion/Windows hook plans.

---

## 2. Open Questions Resolution

### 2.1 Doctor Command Scope

**Gemini Research:**
Aligns with `npm doctor` model: check environment + integrity. 7 checks are appropriate.

**Codex Attack:**
Fragile if git is missing or permissions are restricted.

**Recommendations:**
| Reviewer | Recommendation | Confidence |
|----------|----------------|------------|
| Gemini | Option B (Standard) | High |
| Claude | Option B (Standard) | High |
| Codex | Option B (Standard) | High |

**Consolidation Recommendation:** **Option B (Standard)**
**Reasoning:** All reviewers agree Option B provides the best balance of utility vs. effort for v3.0.

---

### 2.2 Wrapper Command Migration

**Gemini Research:**
Supports "Strangler Fig" pattern; deferring to v4.0 reduces release risk.

**Codex Attack:**
Legacy scripts remain a risk, but immediate migration is a high-scope risk.

**Recommendations:**
| Reviewer | Recommendation | Confidence |
|----------|----------------|------------|
| Gemini | Option A (Keep wrappers) | High |
| Claude | Option A (Keep wrappers) | High |
| Codex | Option A (Keep wrappers) | High |

**Consolidation Recommendation:** **Option A (Keep wrappers)**
**Reasoning:** Unanimous agreement to prioritize release stability and focus on new core CLI features.

---

### 2.3 JSON Output for Wrappers

**Recommendations:**
| Reviewer | Recommendation | Confidence |
|----------|----------------|------------|
| Gemini | Option A (Passthrough) | Medium |
| Claude | Option A (Passthrough) | Medium |
| Codex | Option A (Passthrough) | Medium |

**Consolidation Recommendation:** **Option A with strict fallback.**
**Reasoning:** Attempt passthrough; return explicit error JSON if legacy script fails to emit JSON.

---

### 2.4 Exit Code for Warnings

**Recommendations:**
| Reviewer | Recommendation | Confidence |
|----------|----------------|------------|
| Gemini | Option A (Exit 0) | High |
| Claude | Option A (Exit 0) | High |
| Codex | Option A (Exit 0) | High |

**Consolidation Recommendation:** **Option A (Exit 0)**
**Reasoning:** Standard linter/CI practice. Warnings should not block unless `--strict` is enabled.

---

### 2.5 Legacy Script Deprecation Timing

**Recommendations:**
| Reviewer | Recommendation | Confidence |
|----------|----------------|------------|
| Gemini | Option A/B (Mixed) | High |
| Claude | Option B (v3.1) | High |
| Codex | Option B (v3.1) | High |

**Consolidation Recommendation:** **Option B (v3.1) for user-visible scripts; Option A for internal-only.**
**Reasoning:** Immediate deletion of user-facing scripts risks breaking established workflows. Archive them first (per Roadmap 6.10).

---

## 3. Blocking Issues

| # | Issue | Flagged By | Category | Impact |
|---|-------|------------|----------|--------|
| B1 | Exit code mapping mismatch | Claude | Alignment | CI/CD integrations break across phases |
| B2 | Deletion plan incomplete/risky | Claude, Codex | Alignment/Adversarial | Breaks workflows; Roadmap non-compliance |
| B3 | Windows hook execution uncertainty | Codex | Adversarial | Hooks may fail silently on Windows |
| B4 | Export scope expansion vs Q2 | Claude | Alignment | Unauthorized scope expansion |

**Total Blocking:** 4

---

## 4. Required Actions for Chief Architect

| Priority | Action | From Issue | Complexity |
|----------|--------|------------|------------|
| 1 | Align exit codes to Roadmap 6.3 definitions | B1 | Low |
| 2 | Add `install.py` deletion and archive `.ontos/scripts/` per Roadmap 6.10 | B2 | Low |
| 3 | Add deprecation/warning window for user-facing legacy scripts | B2 | Low |
| 4 | Clarify/Harden Windows hook execution logic | B3 | Medium |
| 5 | Justify `export` command scope expansion or defer | B4 | Low |

---

<details>
<summary><strong>5. Full Issue Analysis (click to expand)</strong></summary>

### 5.1 Critical Issues

| # | Issue | From | Category | Recommendation |
|---|-------|------|----------|----------------|
| C1 | Deletion plan lacks archive safety | Codex | Adversarial | Implement Roadmap 6.10 archive step |
| C2 | Windows hook execution uncertain | Codex | Adversarial | Verify python execution logic on Windows |

### 5.2 Major Issues

| # | Issue | From | Category | Recommendation |
|---|-------|------|----------|----------------|
| M1 | Exit code mismatch | Claude | Alignment | Align with Roadmap 6.3 |
| M2 | JSON API mismatch | Claude | Alignment | Align `JsonOutputHandler` with Roadmap 6.7 |
| M3 | Export path safety | Codex | Adversarial | Ensure `export` can't traverse outside repo |

### 5.3 Minor Issues

| # | Issue | From | Category | Recommendation |
|---|-------|------|----------|----------------|
| m1 | Migration guide visibility | Gemini | UX | Emphasize `.toml` transition |
| m2 | Doctor robustness | Gemini, Codex | UX/Adv | Check `git --version` output |

</details>

---

<details>
<summary><strong>6. Reviewer Agreement Matrix (click to expand)</strong></summary>

### 6.1 Strong Agreement (All 3)

| Topic | Agreement |
|-------|-----------|
| Open Question Choices | Consensus on B, A, A, A, B |
| Architecture Integrity | All agree core/io separation is maintained |

### 6.2 Majority Agreement (2 of 3)

| Topic | Majority | Dissent |
|-------|----------|---------|
| Deletion plan risk | Claude + Codex (Critical) | Gemini (Adequate) |

### 6.3 Unique Concerns

| Concern | From | Valid? |
|---------|------|--------|
| JSON API names | Claude | Yes (Roadmap sync) |
| Export path traversal | Codex | Yes (Security) |

</details>

---

## 7. Decision Summary

### 7.1 Open Question Decisions Needed

| Question | Consolidation Recommendation | Confidence | Needs Research? |
|----------|------------------------------|------------|-----------------|
| Doctor Scope | Option B (Standard) | High | No |
| Wrapper Migration | Option A (Keep wrappers) | High | No |
| JSON for Wrappers | Option A + Fallback | Medium | No |
| Exit for Warnings | Option A (Exit 0) | High | No |
| Deprecation | Option B (Archive/v3.1) | High | No |

### 7.2 Spec Readiness

| Criterion | Status |
|-----------|--------|
| Open questions have recommendations | ✅ |
| No blocking Roadmap deviations | ❌ (Exit codes, Deletion) |
| Legacy deletion verified safe | ❌ (Needs archive step) |
| Cross-platform addressed | ⚠️ (Windows hook detail needed) |

### 7.3 Recommendation

**Status:** Needs Major Revision

**Chief Architect must:**
1. Decide open questions (recommendations provided)
2. Align exit codes and deletion plan with Roadmap Section 6
3. Harden Windows hook execution logic
4. Update JSON API names to match Roadmap 6.7
5. Update spec to v1.1

---

**Consolidation signed by:**
- **Role:** Review Consolidator
- **Model:** Gemini 2.5 Pro
- **Date:** 2026-01-13
- **Review Type:** Spec Review Consolidation (Phase 4)