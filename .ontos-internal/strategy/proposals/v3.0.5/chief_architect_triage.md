# v3.0.5 Chief Architect Triage & Assessment

**Project:** Ontos v3.0.5
**Phase:** Pre-A (Research Synthesis)
**Theme:** Tech Debt Patching + UX Improvement
**Model:** Claude Opus 4.5
**Date:** 2026-01-20

---

## Executive Summary

Three independent review boards (Claude, ChatGPT, Gemini) audited the v3.0.4 codebase. This document consolidates findings, resolves disagreements, and scopes v3.0.5 as a **Patch/Polish release** with a 1-2 week implementation window.

**Key Constraints:**
- No breaking changes
- Backward compatibility is paramount
- Patch phase, not Feature phase

---

## Part 1: Consolidated Issue Assessment

### Theme 1: Version and Configuration Consistency

#### [VER-1]: Version String Mismatch

**Flagged by:** Claude
**Reviewer's Claim:** ONTOS_VERSION="3.0.3" in config_defaults.py is stale vs __version__="3.0.4"

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | High | Yes | Trivial |

**Rationale:** Confirmed at `ontos/_scripts/ontos_config_defaults.py:56`. Causes incorrect version reporting in legacy scripts. Single-line fix with zero risk.

**If IN scope:** Update constant to "3.0.4", add CI check to prevent drift.
**Dependencies:** None

---

#### [CFG-1]: Legacy Script Config Bypass ("Two Ontos")

**Flagged by:** Claude (High), ChatGPT (Technical Risk)
**Reviewer's Claim:** Multiple wrapper commands ignore `.ontos.toml` configuration.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Medium | No | High |

**Rationale:** Confirmed. Legacy scripts in `_scripts/` import from `ontos_config.py` (hardcoded paths), while native commands use `ontos/io/config.py` (reads `.ontos.toml`). This is architectural tech debt, not a quick fix.

**If OUT of scope:** Already tracked in `.ontos-internal/strategy/v3.1/tech-debt-wrapper-commands.md` as P1 for v3.1 native migration.
**Dependencies:** Requires native command migration (v3.1)

---

### Theme 2: Wrapper Command Architecture

#### [WRP-1]: Broken Wrapper Commands

**Flagged by:** Claude (High), ChatGPT
**Reviewer's Claim:** verify, query, consolidate, migrate, promote, scaffold, stub are broken.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Partial | Medium | Partial | Medium |

**Rationale:** v3.0.4 PR #50 fixed the import/PYTHONPATH issue. Commands now execute. However, CLI arg signatures may differ from legacy script expectations (e.g., `ontos verify --all` won't work because `--all` isn't registered in CLI). Need investigation to determine actual breakage scope.

**If IN scope:** Test each wrapper command, document limitations, fix obvious arg-passing bugs.
**If OUT of scope:** Full native migration deferred to v3.1.
**Dependencies:** Testing should complete before any wrapper changes.

---

### Theme 3: MCP Module Status

#### [MCP-1]: MCP Extra is a No-op

**Flagged by:** Claude (High)
**Reviewer's Claim:** `pip install ontos[mcp]` installs pydantic but provides zero functionality.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Medium | Yes | Low |

**Rationale:** Confirmed. `ontos/mcp/__init__.py` contains only `"""MCP module - Placeholder for Phase 2."""`. Users pay for pydantic dependency with no benefit. This is a UX bug.

**If IN scope:** Add import warning: `warnings.warn("MCP module is a placeholder for Phase 2. No functionality available.", stacklevel=2)`
**Dependencies:** None

---

#### [MCP-2]: MCP Strategic Priority

**Flagged by:** Gemini (Critical), ChatGPT (Defer), Claude (Remove)
**Reviewer's Claims:**
- Gemini: "high risk strategic miscalculation" to ignore MCP
- ChatGPT: "future SaaS option, don't worry now"
- Claude: MCP is no-op, should warn or remove

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Strategic | N/A | No | High |

**Rationale:** MCP **feature development** is out of scope for a patch release. This is a v4.0 roadmap item. The no-op extra is addressed by [MCP-1] warning.

**Chief Architect Resolution:** Neither "remove" nor "implement now" is appropriate. Warning addresses UX; feature work deferred to roadmap.
**Dependencies:** None for patch

---

### Theme 4: UX and CLI Polish

#### [UX-1]: Init Installs Hooks by Default

**Flagged by:** ChatGPT (Blocker)
**Reviewer's Claim:** `ontos init` installs git hooks, creating "side effects" that trigger distrust.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Partial | Low | Yes | Trivial |

**Rationale:** `--skip-hooks` flag already exists. The issue is documentation/visibility, not behavior. Default hooks are intentional design (enforce documentation hygiene).

**If IN scope:** Clarify hook behavior in README and `ontos init --help`. Document `--skip-hooks` prominently.
**Dependencies:** None

---

#### [UX-2]: Broken Commands Visible in CLI

**Flagged by:** ChatGPT
**Reviewer's Claim:** New users see "some commands are broken" in Known Issues - trust killer.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Medium | Yes | Low |

**Rationale:** README Known Issues section references v3.0.3 even though v3.0.4 is released. Need to update documentation to reflect current reality.

**If IN scope:** Update Known Issues to match v3.0.4 state. Document any remaining wrapper limitations discovered during testing.
**Dependencies:** [WRP-1] testing should inform this.

---

#### [UX-3]: Error Messages Leak Internal Paths

**Flagged by:** Claude (Low)
**Reviewer's Claim:** Errors show internal paths like `/usr/local/lib/python3.12/dist-packages/ontos/_scripts/...`

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Low | No | Medium |

**Rationale:** Minor UX issue. Requires auditing multiple error paths. Not critical for patch.

**If OUT of scope:** Polish item for v3.1.
**Dependencies:** None

---

### Theme 5: Code Quality and Safety

#### [CQ-1]: Global Mutable State (Git Cache)

**Flagged by:** Claude (Medium)
**Reviewer's Claim:** Module-level `_git_date_cache` in staleness.py without thread safety.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Low | No | Medium |

**Rationale:** Works correctly for CLI use. Only problematic for library use or daemon mode. `clear_git_cache()` exists for testing.

**If OUT of scope:** Daemon mode prep for v3.2+.
**Dependencies:** None

---

#### [CQ-2]: Transactional Writes Not Atomic (Deletes)

**Flagged by:** Claude (Medium)
**Reviewer's Claim:** Two-phase commit uses atomic rename for writes but inline deletes.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Low | No | Medium |

**Rationale:** Theoretical atomicity gap. Would require staging deletes to temp locations then batch-removing. Low-probability failure mode.

**If OUT of scope:** Robustness improvement for v3.2+.
**Dependencies:** None

---

#### [CQ-3]: Lock File PID Race Condition

**Flagged by:** Claude (Medium)
**Reviewer's Claim:** TOCTOU race between checking stale lock and removing it.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Very Low | No | Medium |

**Rationale:** Requires concurrent Ontos processes racing on same repo. Extremely unlikely in practice.

**If OUT of scope:** Overengineering for unlikely scenario.
**Dependencies:** None

---

#### [CQ-4]: TOML Writer is Naive

**Flagged by:** Claude (Medium)
**Reviewer's Claim:** `None`→`""`, no multiline, no datetime handling.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Low | No | Medium |

**Rationale:** Works for current config use cases. Full TOML compliance would require `tomlkit` dependency.

**If OUT of scope:** Enhancement for v3.1+ if needed.
**Dependencies:** Would add new dependency

---

#### [CQ-5]: Type System Inconsistency

**Flagged by:** Claude (Medium)
**Reviewer's Claim:** `doc.type` sometimes enum, sometimes string - defensive code everywhere.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Low | No | High |

**Rationale:** Defensive handling works. Changing risks regressions across codebase.

**If OUT of scope:** Architectural cleanup for v3.1+.
**Dependencies:** Would touch many files

---

#### [CQ-6]: YAML Serialization Hand-Rolled

**Flagged by:** Claude (Medium)
**Reviewer's Claim:** Custom YAML serializer instead of PyYAML.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| No | N/A | No | N/A |

**Rationale:** PyYAML IS a dependency (`pyyaml>=6.0,<7.0`). Fallback serializer in `core/schema.py` is for stdlib-only contexts per Constitution (invariant #1).

**If REJECTED:** Not an issue - intentional design.
**Dependencies:** N/A

---

### Theme 6: Platform Compatibility

#### [PLT-1]: Windows Compatibility Concerns

**Flagged by:** Claude (Medium)
**Reviewer's Claim:** Lock file, PID checking, atomic rename may behave differently on Windows.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Medium | No | High |

**Rationale:** Valid concerns but Windows isn't explicitly supported. Requires dedicated test infrastructure.

**If OUT of scope:** Platform expansion for v3.2+.
**Dependencies:** CI/test infrastructure

---

### Theme 7: Strategic/Business Decisions

#### [STR-1]: License Ambiguity

**Flagged by:** Claude (Low), ChatGPT (Blocker), Gemini (Critical)
**Reviewer's Claims:**
- ChatGPT: "Blocking ecosystem adoption, pick interim license"
- Gemini: "Open Core immediately"
- Claude: Notes ambiguity but lists as Low priority

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Strategic | No | N/A |

**Rationale:** This is a **business decision**, not a technical bug. A patch release is not the venue for licensing changes.

**Chief Architect Resolution:** Escalate to product/business stakeholders. Not a v3.0.5 concern.
**Dependencies:** Business decision

---

#### [STR-2]: Brand/Name Collision

**Flagged by:** ChatGPT
**Reviewer's Claim:** "ontos" name conflicts with other projects (Databricks).

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Strategic | No | N/A |

**Rationale:** Business/marketing decision. Not a patch scope item.

**If OUT of scope:** Business decision for stakeholders.
**Dependencies:** Business decision

---

#### [STR-3]: Obsidian Frontmatter Compatibility

**Flagged by:** Gemini
**Reviewer's Claim:** Ontos uses `type`, `tags`, `id` which conflict with Obsidian conventions.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Medium | No | High |

**Rationale:** Valid integration concern but addressing requires schema changes or namespace prefixing. Breaking change risk.

**If OUT of scope:** v3.1+ with migration tooling.
**Dependencies:** Schema versioning, migration path

---

### Theme 8: Documentation and Release Hygiene

#### [DOC-1]: Documentation URLs May Break

**Flagged by:** Claude (Low)
**Reviewer's Claim:** URLs in pyproject.toml point to GitHub tree paths.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Low | No | Low |

**Rationale:** Minor concern. GitHub Pages or dedicated docs site is v3.1+ polish.

**If OUT of scope:** Documentation infrastructure for v3.1+.
**Dependencies:** None

---

#### [DOC-2]: Deprecation Warnings Mixed with JSON

**Flagged by:** Claude (Low)
**Reviewer's Claim:** Deprecation notices go to stderr when `--json` is used.

**Assessment:**
| Valid? | Severity | v3.0.5? | Effort |
|--------|----------|---------|--------|
| Yes | Low | No | Low |

**Rationale:** stderr is the correct place for warnings. Programs should parse stdout only for JSON.

**If OUT of scope:** Minor polish.
**Dependencies:** None

---

## Part 2: v3.0.5 Scope Decision

### IN SCOPE (Will Address)

| ID | Issue | Severity | Effort | Approach |
|----|-------|----------|--------|----------|
| VER-1 | Version string mismatch | High | Trivial | Update `_scripts/ontos_config_defaults.py:56` to "3.0.4" |
| MCP-1 | MCP extra is no-op | Medium | Low | Add import warning in `mcp/__init__.py` |
| UX-1 | Init hooks documentation | Low | Trivial | Document `--skip-hooks` in README |
| UX-2 | Known Issues outdated | Medium | Low | Update README Known Issues for v3.0.4 reality |
| WRP-1 | Wrapper command testing | Medium | Medium | Test all wrappers, document limitations |

### OUT OF SCOPE (Defer)

| ID | Issue | Target Release | Why Defer |
|----|-------|----------------|-----------|
| CFG-1 | Legacy config bypass | v3.1 | Requires native migration architecture |
| WRP-1 (full) | Native wrapper migration | v3.1 | Already tracked as P1 tech debt |
| CQ-1 | Global mutable state | v3.2+ | Daemon mode prep, not patch priority |
| CQ-2 | Transactional atomicity | v3.2+ | Design work needed |
| CQ-4 | TOML writer naive | v3.1+ | Would add dependency |
| CQ-5 | Type system unification | v3.1+ | Architectural, high regression risk |
| PLT-1 | Windows compatibility | v3.2+ | Needs test infrastructure |
| UX-3 | Error path sanitization | v3.1 | Audit needed |
| STR-3 | Obsidian namespace | v3.1+ | Schema changes, migration tooling |
| DOC-1 | Documentation URLs | v3.1+ | Infrastructure |

### REJECTED (Not a Problem)

| ID | Issue | Why Rejected |
|----|-------|--------------|
| CQ-6 | YAML hand-rolled | PyYAML is used; stdlib fallback is intentional design |
| CQ-3 | Lock TOCTOU race | Overengineering for extremely unlikely scenario |
| STR-1 | License change | Business decision, not patch scope |
| STR-2 | Brand collision | Business decision, not patch scope |
| MCP-2 | MCP feature development | Feature scope, not patch |

---

## Part 3: Dependency Map

```
VER-1 (Version Fix)
    └── No dependencies - standalone

MCP-1 (Import Warning)
    └── No dependencies - standalone

UX-1 (Document Hooks)
    └── No dependencies - standalone

WRP-1 (Wrapper Testing)
    │
    └──▶ UX-2 (Known Issues Update)
         └── Testing results inform documentation
```

| Issue | Depends On | Blocks |
|-------|------------|--------|
| VER-1 | None | None |
| MCP-1 | None | None |
| UX-1 | None | None |
| WRP-1 | None | UX-2 |
| UX-2 | WRP-1 | None |

---

## Part 4: Open Questions

| # | Question | Needed For | How to Resolve |
|---|----------|------------|----------------|
| Q1 | Which wrapper commands are actually broken vs working with limitations? | WRP-1, UX-2 | Manual testing of each command |
| Q2 | Should broken wrapper commands emit "disabled" message or fail silently? | UX-2 | Product decision - recommend graceful message |
| Q3 | Should v3.0.5 include test coverage for wrappers? | WRP-1 | Recommend yes - prevents regression |

---

## Part 5: Recommended Implementation Order

1. **VER-1: Version Mismatch Fix** — Trivial, zero risk, immediate win
2. **MCP-1: MCP Import Warning** — Low effort, improves UX
3. **WRP-1: Wrapper Command Testing** — Medium effort, informs documentation
4. **UX-2: Known Issues Update** — Depends on WRP-1 findings
5. **UX-1: Document Hooks** — Documentation polish, can be parallel

**Suggested Timeline:**
- Day 1: VER-1 + MCP-1
- Day 2-4: WRP-1 (testing all 7 wrapper commands)
- Day 5-6: UX-2 + UX-1 (documentation updates)
- Day 7: Review, final testing, release

---

## Part 6: Risk Assessment

| Risk | If We Do It | If We Don't |
|------|-------------|-------------|
| Version mismatch confuses users | Fixed, version reporting consistent | Continued confusion |
| MCP no-op frustrates users | Warning sets expectations | Users install pydantic for nothing |
| Wrapper limitations undocumented | Clear expectations, trust maintained | Users hit unexpected failures |
| Known Issues stale | Documentation matches reality | Trust erosion |
| Scope creep into v3.1 work | N/A - rejected | Clean patch boundary maintained |

---

## Reviewer Disagreement Resolutions

### MCP Strategy
**Position:** Patch release adds warning; feature work deferred to roadmap (v4.0).
- Claude's "warn or remove" → We warn.
- ChatGPT's "don't worry" → We address the UX bug.
- Gemini's "implement now" → Out of patch scope.

### Licensing
**Position:** Out of scope for patch release. Escalate to business stakeholders.
- All reviewers agree it's important; disagree on urgency.
- This is not a code fix. Business decision.

### "Two Ontos" Architecture
**Position:** Acknowledged as tech debt. v3.0.4 fixed immediate breakage. Full resolution in v3.1.
- Claude's "High priority" → Yes, but for v3.1.
- ChatGPT's "pick blessed core" → Already done (native commands are blessed).

---

## Critical Files

| File | Modification |
|------|--------------|
| `ontos/_scripts/ontos_config_defaults.py:56` | Update ONTOS_VERSION to "3.0.4" |
| `ontos/mcp/__init__.py` | Add import warning |
| `README.md` | Update Known Issues, document --skip-hooks |
| `tests/` | Add wrapper command test cases |

---

## Verification Plan

1. **Version Fix:** Run `ontos --version` and verify legacy scripts report correct version
2. **MCP Warning:** Run `python -c "from ontos import mcp"` and verify warning emitted
3. **Wrapper Commands:** Execute each wrapper command with representative args
   - `ontos verify`
   - `ontos query <id>`
   - `ontos consolidate`
   - `ontos migrate`
   - `ontos promote`
   - `ontos scaffold`
   - `ontos stub`
4. **Documentation:** Review README Known Issues matches implementation reality
5. **Run existing test suite:** `pytest tests/`

---

*Chief Architect Triage — v3.0.5 Pre-Spec Assessment*
