---
id: install_experience_technical_debt_proposal
type: strategy
status: draft
depends_on: [v3_0_implementation_roadmap, installation_ux_proposal]
concepts: [installation, ux, technical-debt, documentation, v3-transition]
---

# Chief Architect Briefing: Install Experience Technical Debt

**To:** Chief Architect (Claude Opus 4.5)
**From:** Research Assistant
**Date:** 2026-01-13
**Subject:** Install Experience - Remaining Technical Debt from Dec 2025 Proposals

---

## 1. Executive Summary

**Situation:** In December 2025, a comprehensive Install Experience proposal was created and reviewed by 3 LLMs (Claude, Gemini, Codex). The reviews reached strong consensus on prioritized fixes. When v3.0 planning began, Phase 2-3 items were intentionally superseded by the new distribution model. However, Phase 0 "quick win" documentation fixes were accidentally forgotten and remain as technical debt.

**Current State:**
- Broken uninstall documentation in `Ontos_Manual.md` (commands in wrong order)
- Duplicate `Common_Concepts.md` files (stub vs full version)
- No single "activate" command for AI agents (6-step manual process)
- `--dry-run` flag never added to `ontos_init.py`

**Chief Architect Tasks:**
1. Decide if Phase 0 fixes should be done immediately (10 min total)
2. Determine if `ontos_activate.py` concept should be added to v3.0 or v4.0
3. Update roadmap if needed

---

## 2. Historical Context

### 2.1 The Original Proposal (Dec 2025)

**File:** `.ontos-internal/strategy/proposals/Install_experience/Installation_UX_Proposal.md`

A 907-line proposal identified significant friction in Ontos installation:
- 7+ manual steps required
- 3 failed attempts needed to run `ontos_init.py` due to poor discoverability
- Broken uninstall documentation (wrong command order)
- Duplicate files creating confusion

### 2.2 The Multi-LLM Review

Three LLMs reviewed the proposal and reached consensus:

| Reviewer | Key Finding |
|----------|-------------|
| Claude (Opus 4.5) | "Fix the docs first" - Phase 0 is highest priority |
| Gemini 2.5 Pro | Idempotency and `--dry-run` critical |
| Codex GPT-5 | Security concerns, but Phase 0 valid |

**Synthesis Document:** `.ontos-internal/strategy/proposals/Install_experience/Architect_Synthesis_InstallUX.md`

### 2.3 What Was Supposed to Happen

The Architect Synthesis proposed a phased approach:

| Phase | Timeline | Items |
|-------|----------|-------|
| Phase 0 | "Do This Week" | Fix docs, delete duplicates (5-30 min each) |
| Phase 1 | v2.8 | `ontos_activate.py`, `--dry-run` |
| Phase 2 | v2.9 | `install.sh`, checksums |
| Phase 3 | v3.0 | PyPI, unified CLI (only if demanded) |

### 2.4 What Actually Happened

The project pivoted directly to v3.0 before Phase 0 was completed:

| Phase | Status | Reason |
|-------|--------|--------|
| Phase 0 | **SKIPPED** | Accidentally forgotten during v3.0 pivot |
| Phase 1 | **Partial** | `ontos export` exists but not `ontos_activate.py` |
| Phase 2 | **Superseded** | v3.0 `pip install` replaces `install.sh` |
| Phase 3 | **In Progress** | v3.0 core work |

---

## 3. Remaining Technical Debt

### 3.1 Broken Uninstall Documentation (CRITICAL)

**File:** `docs/reference/Ontos_Manual.md` lines 399-404

**Current (BROKEN):**
```bash
rm -rf .ontos/
rm -f Ontos_Context_Map.md Ontos_Agent_Instructions.md
# Optional: remove frontmatter
python3 .ontos/scripts/ontos_remove_frontmatter.py --yes  # ← Fails! .ontos/ deleted
```

**Correct Order:**
```bash
# 1. Remove frontmatter FIRST (requires .ontos/)
python3 .ontos/scripts/ontos_remove_frontmatter.py --yes
# 2. Remove git hooks
rm -f .git/hooks/pre-push .git/hooks/pre-commit
# 3. Remove Ontos files
rm -rf .ontos/
rm -f Ontos_Context_Map.md ontos_init.py ontos_config.py
```

**Effort:** 5 minutes
**Impact:** High - Users following docs will get errors

### 3.2 Duplicate Common_Concepts.md

Two versions exist:
- `docs/reference/Common_Concepts.md` (~430 bytes, stub)
- `.ontos-internal/reference/Common_Concepts.md` (~2,627 bytes, full)

**Recommendation from original proposal:** Delete the stub, keep only the full version.

**Effort:** 5 minutes
**Impact:** Medium - Reduces confusion for installers

### 3.3 Missing `ontos_activate.py` Concept

**Original Proposal:** Create single command that executes the 6-step "Initiate Ontos" process:
1. Check for context map
2. Generate if missing
3. Read map
4. Check consolidation status
5. Read relevant files
6. Print "Loaded: [id1, id2, ...]"

**v3.0 Alternative:** `ontos export` generates CLAUDE.md that *tells* agents to run `ontos map`

**Gap:** v3.0 doesn't eliminate the 6-step process - it just reminds agents about it.

**Effort:** 2 hours
**Impact:** High for AI agent UX

### 3.4 Missing `--dry-run` Flag

All three reviewers recommended adding `--dry-run` to `ontos_init.py`.

**Current state:** Not implemented in v2.x `ontos_init.py`
**v3.0 state:** Not mentioned in Technical Architecture

**Effort:** 1 hour
**Impact:** Medium - Helps users preview changes

---

## 4. What v3.0 Already Addresses

These items from the original proposal are **intentionally superseded** by v3.0:

| Original Item | v3.0 Replacement | Reference |
|---------------|------------------|-----------|
| `install.sh` bootstrap | `pip install ontos && ontos init` | Tech Arch §2.5 |
| PyPI packaging | v3.0 core deliverable | Strategy §2 |
| Unified CLI | v3.0 core deliverable | Tech Arch §7 |
| TOML configuration | `.ontos.toml` | Tech Arch §6 |
| Hook collision detection | `ontos init` warns and skips | Tech Arch §4.1 |
| Contributor detection | `ontos init` detects `.ontos/scripts/` | Tech Arch §4.1 |

**No action needed** on these items.

---

## 5. Open Questions for Chief Architect

### 5.1 Phase 0 Documentation Fixes

| Option | Pros | Cons |
|--------|------|------|
| Fix immediately | 10 min total, clears debt | None |
| Wait for v3.0 | Batch with v3.0 docs update | Users hit bugs until then |
| Delete v2.x docs | v3.0 will have new docs | Breaking for current users |

**Recommendation:** Fix immediately (10 min)

### 5.2 `ontos_activate.py` Concept

| Option | Pros | Cons |
|--------|------|------|
| Add to v3.0 | Addresses AI agent friction | Scope creep |
| Defer to v4.0 | v4.0 is "Agent-First" release | Gap persists |
| Close as "won't fix" | `ontos export` is sufficient | 6-step process remains |

**Recommendation:** Defer to v4.0 with explicit tracking

### 5.3 `--dry-run` Flag

| Option | Pros | Cons |
|--------|------|------|
| Add to v3.0 `ontos init` | User confidence | Minor scope addition |
| Already planned? | Check Tech Arch | — |

**Note:** Tech Arch §5.6 mentions `--force` for `ontos export` but not `--dry-run` for `ontos init`.

---

## 6. Recommended Actions

### Immediate (Before v3.0 Release)

1. **Fix uninstall docs** in `docs/reference/Ontos_Manual.md:399-404` (5 min)
2. **Delete stub** `docs/reference/Common_Concepts.md` (5 min)

### Add to v3.0 Roadmap

3. **Consider `--dry-run`** for `ontos init` command

### Track for v4.0

4. **`ontos activate` command** - Single command for AI agent session initialization

---

## 7. Reference Files

| Document | Path |
|----------|------|
| Original Proposal | `.ontos-internal/strategy/proposals/Install_experience/Installation_UX_Proposal.md` |
| Experience Report | `.ontos-internal/strategy/proposals/Install_experience/Ontos_Installation_Experience_Report.md` |
| Architect Synthesis | `.ontos-internal/strategy/proposals/Install_experience/Architect_Synthesis_InstallUX.md` |
| Claude Review | `.ontos-internal/strategy/proposals/Install_experience/Claude_InstallUX_Review.md` |
| Gemini Review | `.ontos-internal/strategy/proposals/Install_experience/Gemini_Review_Installation_UX_Proposal.md` |
| Codex Review | `.ontos-internal/strategy/proposals/Install_experience/Installation_UX_Proposal_Review_Codex.md` |
| v3.0 Strategy | `.ontos-internal/strategy/v3.0/V3.0-Strategy-Decisions-Final.md` |
| v3.0 Tech Arch | `.ontos-internal/strategy/v3.0/V3.0-Technical-Architecture.md` |
| Broken Docs | `docs/reference/Ontos_Manual.md:399-404` |

---

*End of Briefing*
