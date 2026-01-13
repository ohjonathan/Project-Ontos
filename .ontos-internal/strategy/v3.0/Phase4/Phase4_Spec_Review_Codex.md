# Phase 4 Spec Review: Adversarial Reviewer

**Reviewer:** Codex (Adversarial)
**Model:** Codex (OpenAI)
**Date:** 2026-01-13
**Spec Version:** 1.0
**Role:** Edge Cases, Security & Robustness

---

## 1. Legacy Deletion Attack

### 1.1 Deletion Inventory

| File to Delete | Spec Verifies No Deps? | I Verified? | Risk |
|----------------|------------------------|-------------|------|
| ontos_lib.py | ❌ | ❌ | High |
| install.py | ❌ | ❌ | High |
| .ontos/scripts/*.py | ⚠️ | ❌ | Med |
| ontos.py dispatcher | ❌ | ❌ | High |

### 1.2 Deletion Risks

| Risk | Likelihood | Impact | Addressed in Spec? |
|------|------------|--------|-------------------|
| External scripts import ontos_lib | Med | High | ❌ |
| Users have aliases to old scripts | Med | Med | ❌ |
| CI/CD pipelines reference old names | Med | High | ❌ |
| Removal without archive/warn window | Med | High | ❌ |

### 1.3 Deletion Attack Result

**Verdict:** Risks not addressed

**Missing from spec:**
- Explicit archive plan for `.ontos/scripts/` (Roadmap 6.10)
- Deprecation warnings and timeline for user-visible removals

---

## 2. Cross-Platform Attack

### 2.1 Shim Hook Attack (Windows)

| Issue | Addressed? | How? |
|-------|------------|------|
| No shebang execution | ❌ | Spec assumes Python shim works, no Windows-specific guidance |
| Path separators (\ vs /) | ⚠️ | Not discussed |
| chmod not available | ❌ | Spec does not address chmod behavior |
| Python not in PATH | ⚠️ | Method 2 uses sys.executable, but hook execution itself may fail |
| Long path names (>260 chars) | ❌ | Not discussed |

### 2.2 Shim Hook Attack (macOS)

| Issue | Addressed? | How? |
|-------|------------|------|
| Gatekeeper/quarantine | ❌ | Not discussed |
| Case-insensitive filesystem | ❌ | Not discussed |

### 2.3 Cross-Platform Verdict

| Platform | Will Work? | Confidence |
|----------|------------|------------|
| Linux | Maybe | Medium |
| macOS | Maybe | Medium |
| Windows | Maybe | Low |

---

## 3. Doctor Command Attack

### 3.1 Edge Cases

| Scenario | Spec Handles? | What Happens? |
|----------|---------------|---------------|
| Git not installed | ❌ | Not specified; likely fails in hook check |
| Not in a git repo | ❌ | Not specified |
| Config file corrupt | ⚠️ | "Missing or malformed" mentioned, no behavior detail |
| Config file missing | ⚠️ | Mentioned, no UX flow for recover |
| No write permissions | ❌ | Not specified |
| Network unavailable | ✅ | Not required (local-first) |
| Huge repository | ❌ | No performance guidance |

### 3.2 Doctor Attack Result

**Robustness:** Fragile

**Missing error handling:**
- Git executable missing
- Non-repo invocation
- Permission and filesystem errors

---

## 4. Export Command Attack

### 4.1 Security Concerns

| Concern | Risk Level | Addressed? |
|---------|------------|------------|
| Exports sensitive file paths | Low | ⚠️ Template is static; no mention of redaction |
| Exports internal implementation details | Low | ✅ |
| Exports credentials/secrets accidentally | Med | ❌ No guidance for safe content or redaction |
| Output location traversal | Med | ❌ No explicit path validation |

### 4.2 Edge Cases

| Scenario | Spec Handles? |
|----------|---------------|
| No documents to export | ✅ (static template) |
| Huge context map | ✅ (not included) |
| Unicode in file names | ❌ (not discussed) |
| Circular dependencies | ✅ (not included) |

---

## 5. Hook Dispatcher Attack

### 5.1 Input Attack

| Input | Expected Behavior | Specified? |
|-------|-------------------|------------|
| Unknown hook type | Warn + allow | ⚠️ Returns 0, warns on stderr |
| Empty arguments | Allow | ✅ |
| Malformed arguments | Allow | ❌ Not specified |
| Hook called outside git repo | Fail or allow? | ❌ Not specified |

### 5.2 Exit Code Attack

| Scenario | Exit Code | Specified? |
|----------|-----------|------------|
| Hook succeeds | 0 | ✅ |
| Hook fails | 1 | ✅ |
| Hook command not found | 0 | ✅ (shim fallback) |
| Hook times out | ? | ❌ |

---

## 6. JSON Output Attack

### 6.1 Malformed Data

| Input | JSON Output Handles? |
|-------|---------------------|
| Unicode in all fields | ✅ (json.dumps default=str) |
| Very long strings | ⚠️ Not specified |
| Deeply nested structures | ⚠️ Not specified |
| Null/empty values | ⚠️ Not specified |
| Special characters | ✅ |

### 6.2 Schema Consistency Attack

| Question | Answer |
|----------|--------|
| Is error format consistent? | No (examples omit fields) |
| Are all commands using same schema? | No (export/hook no JSON) |
| Is schema versioned? | No |

---

## 7. Open Questions Attack

### 7.1 Doctor Command Scope

**Option A downsides:**
- Misses key failures (hooks/config validation)
- Users still need manual troubleshooting

**Option B downsides:**
- Slightly more work now, more tests
- Some checks may be noisy without clear remediation

**Option C downsides:**
- Scope creep with network/deps/disk checks
- Cross-platform reliability problems

**Worst option:** C
**Least-bad option:** B

### 7.2 Wrapper Command Migration

**Option A downsides:**
- Legacy scripts remain a security/maintenance risk
- JSON inconsistencies across wrapper/native commands

**Option B downsides:**
- High scope risk for v3.0 release
- Regression risk without deeper test coverage

**Option C downsides:**
- Partial migration complicates UX and docs
- Still leaves legacy risks

**Worst option:** C
**Least-bad option:** A

### 7.3 JSON Output for Wrappers

**Option A downsides:**
- Passthrough can emit non-JSON output, breaking callers

**Option B downsides:**
- Requires parsing arbitrary legacy text; brittle

**Option C downsides:**
- Inconsistent behavior vs roadmap, surprise for CI users

**Worst option:** B
**Least-bad option:** A (with explicit error JSON fallback)

### 7.4 Exit Code for Warnings

**Option A downsides:**
- Warnings can be ignored in CI unless `--strict` used

**Option B downsides:**
- Too aggressive; warnings may block pipelines

**Option C downsides:**
- Adds a new exit code semantics not in roadmap 6.3

**Worst option:** C
**Least-bad option:** A

### 7.5 Legacy Script Deprecation Timing

**Option A downsides:**
- Immediate deletion can break hidden workflows

**Option B downsides:**
- Extends maintenance for legacy scripts

**Option C downsides:**
- Permanent legacy code carries ongoing risk

**Worst option:** A (for user-facing scripts)
**Least-bad option:** B

---

## 8. Issues Summary

### Critical (Adversarial)

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-C1 | Deletion plan lacks archive/deprecation safety | Legacy deletion | High likelihood of breaking pipelines |
| X-C2 | Windows hook execution uncertain | Cross-platform hooks | Hooks may never run on Windows |

### High (Adversarial)

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-H1 | JSON schema inconsistency | JSON output | CI integrations break on schema drift |
| X-H2 | Doctor lacks git missing/error handling | Doctor edge cases | Misleading diagnostics |

### Medium (Adversarial)

| # | Issue | Attack Vector | Impact |
|---|-------|---------------|--------|
| X-M1 | Export path safety not specified | Export command | Accidental overwrite outside repo |

---

## 9. Verdict

**Spec Robustness:** Fragile

**Recommendation:** Request changes

**Highest risks:**
1. Legacy deletion without deprecation/archival plan
2. Windows hook execution ambiguity
3. JSON schema inconsistency for automation users

**Summary:** The spec is close but still risky in the deletion and cross-platform areas. Fix the deletion plan, harden hook behavior on Windows, and stabilize JSON schema before implementation.

---

**Review signed by:**
- **Role:** Adversarial Reviewer
- **Model:** Codex (OpenAI)
- **Date:** 2026-01-13
- **Review Type:** Spec Review (Phase 4 Implementation)

*End of Adversarial Spec Review*
