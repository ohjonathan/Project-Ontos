---
id: phase3_review_consolidation
type: strategy
status: complete
depends_on: [phase3_implementation_spec]
concepts: [review, consolidation, phase3, configuration, init]
---

# Phase 3 Implementation Spec: Review Consolidation

**Date:** 2026-01-13
**Reviews Consolidated:** 3 (Peer, Alignment, Adversarial)
**Spec Version:** 1.0

---

## 1. Open Questions Resolution

### 1.1 Config File Location

**Question:** Should Ontos use `.ontos.toml`, `ontos.toml`, `.ontos/config.toml`, or `pyproject.toml [tool.ontos]`?

#### Research Summary

| Tool | Config Location | Hidden? | Source |
|------|-----------------|---------|--------|
| Prettier | `.prettierrc`, `prettier.config.js` | Mixed | Gemini research |
| ESLint | `eslint.config.js|mjs|cjs|ts` | No | Codex research |
| Black | `pyproject.toml` `[tool.black]` | No | Gemini/Codex research |
| Ruff | `pyproject.toml`, `ruff.toml`, `.ruff.toml` | Mixed | Gemini/Codex research |
| Cargo | `Cargo.toml` | No | Gemini/Codex research |
| Poetry | `pyproject.toml` `[tool.poetry]` | No | Codex research |

**Patterns observed:**
- Visible root config is common (Cargo, ESLint)
- Python tooling converges on `pyproject.toml` with `[tool.*]` sections
- Non-Python tools favor dedicated config files

#### Reviewer Recommendations

| Reviewer | Recommendation | Reasoning |
|----------|----------------|-----------|
| Gemini (Peer) | `.ontos.toml` | Language-agnostic, mimics `.gitignore`; allow `ontos.toml` as fallback |
| Claude (Alignment) | N/A (spec compliant) | Defers to spec's choice |
| Codex (Adversarial) | `.ontos.toml` | Language-agnostic, aligns with roadmap, avoids Python-only coupling |

#### Adversarial Concerns

| Option | Downside (from Codex) |
|--------|----------------------|
| `.ontos.toml` | Hidden; discoverability fair |
| `ontos.toml` | Visible but nonstandard |
| `.ontos/config.toml` | Lowest discoverability |
| `pyproject.toml` | Python-centric; conflicts for non-Python projects |

#### Consensus

**Reviewers agree:** Yes

**Recommendation:** **`.ontos.toml`**

**Confidence:** High

**Reasoning:** All reviewers agree on `.ontos.toml`. Ontos is language-agnostic, so coupling to `pyproject.toml` would limit adoption in non-Python projects. The hidden file convention matches `.gitignore` and other repo-root config files. Gemini's suggestion to allow `ontos.toml` as fallback could be a future enhancement.

---

### 1.2 Init Failure Behavior

**Question:** When `ontos init` is run in an already-initialized project, should it error, succeed silently, or prompt?

#### Research Summary

| Tool | Behavior | Exit Code | Source |
|------|----------|-----------|--------|
| git init | Reinitializes existing repo (safe/idempotent) | 0 | Gemini/Codex research |
| npm init | Creates/updates package.json (interactive) | 0 | Codex research |
| cargo init | Creates package in existing dir | 0 | Codex research |
| poetry init | Interactive creation of pyproject.toml | 0 | Codex research |

#### Reviewer Recommendations

| Reviewer | Recommendation | Reasoning |
|----------|----------------|-----------|
| Gemini (Peer) | Exit 1 with helpful message | Overwriting configuration is destructive; silent success is confusing |
| Claude (Alignment) | Exit 1 (Roadmap 5.3 mandates this) | Roadmap specifies exit code 1 for "Already initialized" |
| Codex (Adversarial) | Error + `--force` | Silent success has highest confusion risk; error + force is safest |

#### Adversarial Concerns

| Option | Risk (from Codex) |
|--------|-------------------|
| Error + exit 1 | Low — clear failure; user knows to use `--force` |
| Silent success | High — confusion about what changed |
| Interactive prompt | Medium — blocks automation |

#### Roadmap Constraint

**Note:** Roadmap 5.3 specifies exit code 1 for "Already initialized."

- [x] Yes — Must error per Roadmap

#### Consensus

**Reviewers agree:** Yes

**Recommendation:** **Exit code 1 with message "Already initialized. Use --force to reinitialize."**

**Confidence:** High

**Reasoning:** All three reviewers agree. The Roadmap mandates exit code 1. Additionally, `ontos init` writes config + hooks + directories—silent reinit risks clobbering user changes. The `--force` flag provides escape hatch.

---

### 1.3 Init UX Flow

**Question:** Should `ontos init` be minimal, wizard-style, or smart-defaults with optional interactivity?

#### Research Summary

| Tool | Default Behavior | Interactive Option | Source |
|------|------------------|-------------------|--------|
| npm init | Interactive prompts by default | `-y` for defaults | Codex research |
| cargo init | Minimal defaults | Flags | Codex research |
| poetry init | Wizard-style prompts | Flags | Codex research |

#### Reviewer Recommendations

| Reviewer | Recommendation | Reasoning |
|----------|----------------|-----------|
| Gemini (Peer) | Minimal | Ontos v3.0 is for developers who want "standard defaults"; reserve `--interactive` for v3.1 |
| Claude (Alignment) | N/A | Defers to spec |
| Codex (Adversarial) | Smart defaults + optional `--interactive` | Supports automation and discoverable UX |

#### Adversarial Concerns

| Option | Downside (from Codex) |
|--------|----------------------|
| Minimal | Lower discoverability of options |
| Wizard | Worst for automation; blocks CI/CD |
| Smart defaults + --interactive | Slight complexity |

#### Consensus

**Reviewers agree:** Partial (Gemini prefers pure minimal; Codex prefers smart defaults + optional interactive)

**Recommendation:** **Minimal with optional `--interactive` flag for future**

**Confidence:** High

**Reasoning:** Both positions are compatible. The spec implements minimal defaults now, which works for v3.0. The `--interactive` flag is already in the spec's `InitOptions` dataclass but unused. Reserve wizard-style prompts for v3.1 when MCP configuration may require it.

---

### 1.4 Open Questions Summary

| Question | Recommendation | Consensus | Confidence |
|----------|----------------|-----------|------------|
| Config location | `.ontos.toml` | Yes | High |
| Init failure behavior | Error exit 1 + `--force` | Yes | High |
| Init UX flow | Minimal (--interactive future) | Partial | High |

**Action Required:** Chief Architect should adopt these recommendations. All align with current spec; no changes needed.

---

## 2. Overall Verdict Summary

### 2.1 Reviewer Verdicts

| Reviewer | Role | Recommendation | Confidence | Top Concern |
|----------|------|----------------|------------|-------------|
| Gemini | Peer | Approve with minor changes | High | Error handling in config parsing |
| Claude | Alignment | Approve with changes | High | Missing initial context map generation |
| Codex | Adversarial | Request changes | High | Missing config resolution + unsafe hook detection |

### 2.2 Consensus

| Verdict | Count |
|---------|-------|
| Ready for implementation | 0/3 |
| Needs minor fixes | 2/3 |
| Needs major revision | 1/3 |

**Overall Verdict:** **Minor Revisions Required**

### 2.3 Key Takeaway

The Phase 3 spec is architecturally sound with strong alignment to the Roadmap and Strategy documents. All reviewers found the core design (layer separation, config dataclasses, hook collision safety) to be well-structured. However, the spec omits one explicit Roadmap requirement (creating the initial context map during init), lacks error handling for malformed configs, and has edge cases in hook detection that need addressing. These are all straightforward fixes that don't require architectural changes.

---

## 3. Alignment Assessment

### 3.1 Roadmap Section 5 Compliance

| Requirement | Addressed? | Correctly? | Notes |
|-------------|------------|------------|-------|
| `commands/init.py` | Yes | Yes | Section 4.3 |
| Config resolution | Yes | Yes | CLI → env → file → defaults |
| Legacy detection | Yes | Yes | Lines 357-360 |
| Hook collision safety | Yes | Yes | Three scenarios covered |
| Exit codes (0,1,2,3) | Yes | Yes | Matches Roadmap 5.3 |
| Config template | Yes | Partial | Missing `log_retention_count` |
| Export tip | Yes | Yes | Line 375 |
| **Create initial context map** | **No** | — | **Missing from init flow** |

### 3.2 Architecture Compliance

| Constraint | Respected? | Notes |
|------------|------------|-------|
| core/ no io imports | Yes | Section 9 explicit |
| core/ stdlib-only | Yes | Only dataclasses, typing |
| io/ may import core | Yes | io/config.py imports from core |

### 3.3 io/toml.py Integration

| Check | Status |
|-------|--------|
| Uses existing functions | Yes (`load_config_if_exists`, `write_config`) |
| No duplication | Yes |

### 3.4 Alignment Verdict

**Roadmap compliance:** Partial — One missing requirement (initial context map)
**Architecture compliance:** Full
**Blocking alignment issues:** 1 (initial context map generation)

---

## 4. Critical Risk Areas

### 4.1 Config Parsing

| Aspect | Gemini | Claude | Codex | Consensus |
|--------|--------|--------|-------|-----------|
| Malformed config handled | ⚠️ | ✅ | ❌ | ⚠️ Needs attention |
| Partial config handled | ⚠️ | ✅ | ⚠️ | ⚠️ Needs type validation |
| Config validation | ⚠️ | ✅ | ❌ | ⚠️ Missing validation |

**Config parsing risks:**
- Gemini: `io/toml.py` raises `TOMLDecodeError` but `io/config.py` doesn't catch it
- Codex: `dict_to_config` assumes types match; runtime failures possible with `max_dependency_depth = "five"`
- **Fix:** Add try/except around TOML loading; add type validation in `dict_to_config`

---

### 4.2 Hook Installation

| Aspect | Gemini | Claude | Codex | Consensus |
|--------|--------|--------|-------|-----------|
| Collision detection reliable | ✅ | ✅ | ⚠️ | ⚠️ Edge cases |
| Edge cases handled | ⚠️ | ✅ | ❌ | ⚠️ Needs work |
| Cross-platform | ⚠️ | ✅ | ⚠️ | ⚠️ Windows concerns |

**Hook installation risks:**
- Codex: Substring match for "ontos" + "shim" may false positive if user linter checks Ontos compatibility
- Codex: `.git/hooks` missing or symlink not handled; `.git` as file (worktrees/submodules) not detected
- Gemini: `PermissionError` on root-owned `.git/hooks` not caught
- **Fix:** Consider explicit marker comment; handle worktrees; add try/except on permissions

---

### 4.3 Cross-Platform

| Platform | Issues Found | Severity |
|----------|--------------|----------|
| Windows | Shebang ignored in CMD, chmod ineffective, CRLF/long paths | Medium |
| macOS | Quarantine, case-insensitive FS | Low |
| Linux | SELinux context | Low |

**Cross-platform verdict:** Needs attention — Windows hook execution is best-effort (Python shim mitigates this)

---

### 4.4 User Experience

| Aspect | Assessment |
|--------|------------|
| Error messages clear | ✅ Good — exit codes well-defined |
| Next steps obvious | ✅ Good — "Run 'ontos export'" tip |
| Failure recovery clear | ⚠️ — Hook skip message could be more explicit |

**UX verdict:** Good (minor improvements possible)

---

## 5. Reviewer Agreement Matrix

### 5.1 Strong Agreement (All 3 reviewers)

| Topic | Agreement |
|-------|-----------|
| Config location = `.ontos.toml` | All agree this is the right choice |
| Init failure = error + `--force` | All agree; aligns with Roadmap |
| Layer separation correct | All confirm architecture compliance |
| Exit codes correct | All confirm match Roadmap 5.3 |
| io/toml.py integration correct | All confirm no duplication |

### 5.2 Majority Agreement (2 of 3)

| Topic | Majority | Dissent |
|-------|----------|---------|
| Spec is approvable with changes | Gemini + Claude | Codex (requests more significant changes) |
| Error handling is minor issue | Gemini + Claude (minor) | Codex (major blocking) |

### 5.3 Split Opinions

| Topic | Gemini | Claude | Codex |
|-------|--------|--------|-------|
| Severity of missing context map | Not mentioned | **Major/Blocking** | **Major/Blocking** |
| Hook detection approach | Acceptable | Acceptable | Needs explicit marker |

### 5.4 Unique Concerns (1 reviewer only)

| Concern | From | Seems Valid? |
|---------|------|--------------|
| Schema versioning (handling v4.0 config) | Gemini | Yes — should be specified |
| Global config (~/.ontos/config) | Gemini | Maybe — future enhancement |
| Unused `shutil` import | Claude | Yes — dead import, cleanup |
| Git worktrees/submodules (`.git` as file) | Codex | Yes — real edge case |
| Path traversal via config values | Codex | Yes — security concern |
| SELinux context on hooks | Codex | Low priority — rare scenario |

---

## 6. Consolidated Issues

### 6.1 Critical Issues (Must Fix)

| # | Issue | Flagged By | Category | Suggested Fix |
|---|-------|------------|----------|---------------|
| C1 | **Init missing initial context map generation** | Claude, Codex | Roadmap compliance | Add `from ontos.commands.map import run` call after step 5 in init_command() |

**Critical Issue Count:** 1

---

### 6.2 Major Issues (Should Fix)

| # | Issue | Flagged By | Category | Suggested Fix |
|---|-------|------------|----------|---------------|
| M1 | Missing `log_retention_count` in WorkflowConfig | Claude | Roadmap compliance | Add `log_retention_count: int = 20` to WorkflowConfig |
| M2 | No error handling for malformed TOML | Gemini, Codex | Error handling | Catch `TOMLDecodeError` in io/config.py, return clean error |
| M3 | No type validation in `dict_to_config` | Gemini, Codex | Error handling | Validate types before assignment; raise on mismatch |
| M4 | Config paths not sanitized (path traversal risk) | Codex | Security | Validate that `docs_dir` etc. resolve within repo root |

**Major Issue Count:** 4

---

### 6.3 Minor Issues (Consider)

| # | Issue | Flagged By | Recommendation |
|---|-------|------------|----------------|
| m1 | Unused `shutil` import | Claude | Remove |
| m2 | Schema versioning behavior not defined | Gemini | Document handling of future config versions |
| m3 | Hook detection could use explicit marker | Codex | Consider adding `# ontos-managed-hook` marker |
| m4 | Git worktrees/submodules not detected | Codex | Check if `.git` is file; adjust detection |
| m5 | `.git/hooks` directory creation not handled | Codex | Create hooks dir if missing |
| m6 | PermissionError on hook write not caught | Gemini, Codex | Add try/except around hook writes |
| m7 | Project type detection not implemented | Claude, Codex | Lower priority — roadmap mentions but not critical |
| m8 | Config resolution tests missing | Codex | Add CLI → env → file → default precedence tests |
| m9 | Windows hook permissions edge case | Codex | chmod is no-op on Windows; document as best-effort |

**Minor Issue Count:** 9

---

### 6.4 Issues Summary

| Severity | Count | Consensus (2+) | Single Reviewer |
|----------|-------|----------------|-----------------|
| Critical | 1 | 1 | 0 |
| Major | 4 | 2 | 2 |
| Minor | 9 | 3 | 6 |

---

## 7. Adversarial Findings

### 7.1 Edge Cases Not Addressed

| Edge Case | Module | Severity | From Codex |
|-----------|--------|----------|------------|
| Git worktrees/submodules (`.git` as file) | commands/init.py | Medium | False "not a git repo" for submodules |
| Bare repos | commands/init.py | Low | Not a typical use case |
| Read-only directories | commands/init.py | Medium | PermissionError on mkdir/write |
| Concurrent init | commands/init.py | Low | Race condition; acceptable |
| `.git/hooks` missing or symlink | commands/init.py | Medium | mkdir not called |
| Hook file is dir or symlink | commands/init.py | Low | Would crash on write |
| Invalid TOML in config | io/config.py | High | Uncaught exception |
| Wrong types in config | core/config.py | High | Runtime failure later |
| Unknown sections in config | core/config.py | Low | Silently ignored — acceptable |

### 7.2 Security Concerns

| Concern | Risk Level | Addressed? |
|---------|------------|------------|
| Path traversal via config paths | Medium | No — `docs_dir = "../../../"` not validated |
| Hook overwrites on false detection | Low | Partially — "ontos" + "shim" check is specific enough |

### 7.3 Cross-Platform Issues

| Issue | Platform | Impact |
|-------|----------|--------|
| Shebang ignored | Windows CMD | Hook may not execute; Python shim mitigates |
| chmod no-op | Windows | Permissions not set; git handles this |
| Long paths | Windows | May fail if path > 260 chars |
| CRLF line endings | Windows | Python handles this; low impact |
| Quarantine attribute | macOS | First run may prompt; low impact |
| SELinux context | Linux | May block hook execution in strict environments |

### 7.4 Adversarial Verdict

**Spec survivability:** Needs hardening

The core design is solid, but error handling and edge case coverage need improvement before production. The critical and major issues identified are straightforward to fix during implementation.

---

## 8. Strengths Identified

| Strength | Noted By | Why It's Good |
|----------|----------|---------------|
| Clean layer separation (core/io/commands) | All 3 | Maintains architecture integrity; no circular imports |
| Exit codes match Roadmap exactly | All 3 | Predictable CLI behavior for automation |
| Hook shim with fallback to `python -m ontos` | Gemini, Codex | Robust cross-environment execution |
| Legacy detection with warning | All 3 | Smooth migration path for v2.x users |
| `--force` flag for reinit | All 3 | Intentional overwrite, not accidental |
| Collision detection for foreign hooks | All 3 | Doesn't clobber user's existing hooks |
| Uses existing io/toml.py | Claude | No duplication; DRY principle |
| Proper use of `field(default_factory=...)` | Gemini | Avoids mutable default bugs |
| Config dataclasses are stdlib-only | All 3 | Pure, testable, no external deps |
| Config resolution order documented | Gemini, Claude | CLI → env → file → defaults is standard |

---

## 9. Decision-Ready Summary

### 9.1 Open Questions Decisions

| Question | Recommendation | Adopt? |
|----------|----------------|--------|
| Config location | `.ontos.toml` | [x] Yes — Aligns with spec and all reviewers |
| Init failure | Exit 1 + `--force` | [x] Yes — Roadmap mandates; all agree |
| Init UX | Minimal (--interactive future) | [x] Yes — Matches spec; reserve wizard for v3.1 |

**Action:** All open questions are resolved. No Chief Architect decision needed.

---

### 9.2 Alignment Verdict

| Area | Verdict |
|------|---------|
| Roadmap Section 5 | Partial — 1 missing requirement |
| Architecture v1.4 | Full |
| Strategy Decisions | Full |

---

### 9.3 Quality Verdict

| Aspect | Verdict |
|--------|---------|
| Completeness | Gaps — Missing context map generation, log_retention_count |
| Implementability | Ready — Code snippets are detailed and usable |
| Test coverage | Gaps — Missing config resolution tests, hook edge case tests |
| UX design | Good — Clear messages, good tips |

---

### 9.4 Overall Spec Verdict

**Status:** Minor Revisions Required

**Blocking Issues:** 1 (missing initial context map generation)

**Non-Blocking Issues:** 13 (4 major, 9 minor)

---

### 9.5 Recommended Actions

**For Chief Architect:**

**Minor Revisions (v1.1):**

1. **Add initial context map generation** to `init_command()` after step 5:
   ```python
   # 6. Generate initial context map
   from ontos.commands.map import run as run_map
   run_map(config)
   ```

2. **Add `log_retention_count` to `WorkflowConfig`:**
   ```python
   @dataclass
   class WorkflowConfig:
       enforce_archive_before_push: bool = True
       require_source_in_logs: bool = True
       log_retention_count: int = 20  # ADD THIS
   ```

3. **Add error handling to `io/config.py`:**
   - Catch `TOMLDecodeError` and return friendly error message
   - Add type validation in `dict_to_config()`

4. **Add path validation:**
   - Ensure `docs_dir`, `logs_dir` resolve within repo root

5. **Remove unused `shutil` import** from commands/init.py

**No re-review needed for these changes.** Fix and proceed to implementation.

---

### 9.6 Next Steps

| Step | Owner | Action |
|------|-------|--------|
| 1 | Founder | Review consolidation, confirm open question decisions (already aligned) |
| 2 | Chief Architect | Update spec (v1.1) with 5 fixes above |
| 3 | — | No re-review needed — fixes are straightforward |
| 4 | Developer | Begin Phase 3 implementation per updated spec |
| 5 | Dev + Adversarial | Add edge case tests during implementation |

---

*End of Consolidation*

**Consolidated by:** Antigravity (powered by Gemini 2.5 Pro)
**Date:** 2026-01-13
