# Ontos v3.0 Architecture Review: Round 2

## Peer Architect: Claude Opus 4.5 (Reviewer B)
## Date: 2026-01-12
## Architecture Version Reviewed: 1.3

---

## 1. New Feature Review: Global CLI + Local Data

### Feature Summary

Section 2 "Distribution Model: Global CLI + Local Data" defines the fundamental v3.0 distribution architecture. This is the "defining architectural choice" per the document — everything flows from this decision.

### Correctness

- [x] Pattern is technically sound — git-like model is well-understood and proven
- [x] Edge cases mostly handled (see issues below)
- [x] Path resolution logic is correct (repo root detection from subdirectory)

**Issues Found:**

**Issue 1: Nested Repository Handling Not Specified**

**Severity:** Minor

**Problem:** Section 2.6 mentions "Repo Root Detection" but doesn't specify behavior for nested git repositories. Example: a monorepo with submodules, each potentially having their own `.ontos.toml`.

**Proposed Fix:** Add to Section 2.6 constraints:
```
8. Nested Repository Handling: CLI uses the nearest `.ontos.toml` walking up from CWD.
   If multiple `.ontos.toml` exist in nested repos, innermost wins. Submodules with
   their own `.ontos.toml` are treated as independent Ontos projects.
```

---

**Issue 2: `ontos` Not in PATH Edge Case**

**Severity:** Minor

**Problem:** Section 8.1 shows the shim hook exits 0 if `ontos` not found, with a warning. This is correct for hooks. But what happens if a user manually runs `ontos` and it's not in PATH? The architecture assumes pip installation puts it in PATH, but `--user` installs may not.

**Proposed Fix:** Add note to Section 2.3 or Section 7:
```
Note: `pip install ontos` typically adds the CLI to PATH. If installed with `--user`
on some systems, users may need to add `~/.local/bin` to their PATH. `ontos doctor`
checks for this and provides guidance.
```

---

### Completeness

- [x] Installation flow defined (pip install ontos)
- [x] Initialization flow defined (ontos init)
- [x] Usage patterns covered
- [ ] Uninstallation/cleanup partially defined
- [x] Upgrade path defined (pip install --upgrade)

**Gaps Found:**

**Gap 1: Uninstallation Flow Not Specified**

**Impact:** Low — users can figure it out, but completeness suggests documenting it

**What's Missing:** What happens when a user does `pip uninstall ontos`? The global CLI is removed, but per-repo data remains. This is correct (docs travel with repo), but should be explicitly stated.

**Proposed Addition:** Add to Section 2:
```
### 2.7 Uninstallation

`pip uninstall ontos` removes the global CLI. Per-repository data remains:
- `.ontos.toml` — keep (project config)
- `Ontos_Context_Map.md` — keep (generated, but valuable)
- `docs/` — keep (project documentation)
- `.git/hooks/pre-push` — keep but becomes no-op (shim warns "ontos not found")

To fully remove Ontos from a repo:
1. Delete `.ontos.toml`
2. Delete shim hooks: `rm .git/hooks/pre-push .git/hooks/pre-commit`
3. Optionally delete generated files (`Ontos_Context_Map.md`)
```

---

### Consistency

- [x] Aligns with `.ontos.toml` config design
- [x] Aligns with shim hooks design
- [x] Aligns with CLI architecture
- [x] No conflicts with other sections

**Inconsistencies Found:** None

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation Suggestion |
|------|------------|--------|----------------------|
| PATH issues on non-standard pip installs | Medium | Low | Document in `ontos doctor` and README |
| Nested repo confusion | Low | Medium | Document behavior; innermost wins |
| Global CLI version skew across machines | Low | Low | Q5 version warning addresses this |
| Stale hooks after uninstall | Low | Low | Hooks self-recover (exit 0 with warning) |

### Overall Assessment

**Quality:** Strong

**Ready for Implementation:** Yes

The Global CLI + Local Data model is well-designed and follows a proven pattern (git). The documentation is comprehensive. Minor gaps (uninstallation, nested repos) can be addressed during implementation or documentation phase without architectural changes.

---

## 2. New Feature Review: Session Bootstrap (Agent Activation)

### Feature Summary

Section 5.6 "ontos export — Agent Bootstrap Generation" and the new `commands/export.py` module address the "Session Bootstrap" problem: AI assistants may forget about Ontos during long sessions or after context compaction. The feature generates bootstrap files (CLAUDE.md) that instruct agents to activate Ontos.

### Correctness

- [x] Activation flow is technically sound
- [x] Error handling is appropriate (exit codes defined)
- [x] Idempotency handled (--force flag for overwrite)

**Issues Found:**

**Issue 1: Template Content Too Minimal**

**Severity:** Minor

**Problem:** The template shown in Section 5.6 is very brief:
```
## Ontos Activation
This project uses Ontos. At session start:
1. Run `ontos map` to generate context map
2. Read `Ontos_Context_Map.md`
3. End sessions with `ontos log`
```

This doesn't explain *why* to use Ontos or what value it provides. An AI agent encountering this for the first time has no context.

**Proposed Fix:** Expand the hardcoded v3.0 template to include:
```markdown
# CLAUDE.md

## Ontos Documentation System

This project uses **Ontos** for structured documentation management.

### Why Ontos?
Ontos maintains a semantic knowledge graph of project documentation, ensuring
context persists across sessions and preventing "AI amnesia" from repeated
context loss.

### Session Start
1. Run `ontos map` to regenerate the context map
2. Read `Ontos_Context_Map.md` for project overview and document relationships
3. Reference specific docs in `docs/` as needed

### Session End
Run `ontos log -e <type> -t "<title>"` to record what you worked on.
Event types: feature, fix, refactor, exploration, chore

### Key Files
- `Ontos_Context_Map.md` — Auto-generated project overview
- `.ontos.toml` — Project configuration
- `docs/` — Structured documentation
```

---

**Issue 2: Command-Line Invocation Ambiguity**

**Severity:** Minor

**Problem:** The template shows `ontos map` but the architecture mentions v2 compatibility. Should the template include both v2 (`python3 ontos.py map`) and v3 (`ontos map`) invocations?

**Proposed Fix:** Use v3 syntax only in the template. If detecting a v2-only repo, either:
- Don't generate CLAUDE.md (require upgrade first), or
- Generate with v2 syntax and a note about upgrading

Recommendation: v3 syntax only. `ontos export` is a v3 command; if they can run it, they have v3.

---

### Completeness

- [x] First-time generation covered
- [x] Re-generation with --force covered
- [ ] Integration with `ontos init` not specified
- [x] Error states defined
- [x] Success confirmation defined

**Gaps Found:**

**Gap 1: `ontos init` Integration Not Defined**

**Impact:** Medium — affects first-time UX

**What's Missing:** Should `ontos init` automatically generate CLAUDE.md? The Section 5.6 mentions "Integrating with `ontos init` to optionally create bootstrap files" as a v4.0 feature, but the v3.0 stub could at least prompt the user.

**Proposed Addition:** Either:
- Add `--with-bootstrap` flag to `ontos init` for v3.0, or
- Add note to `ontos init` output: "Tip: Run `ontos export` to generate CLAUDE.md for AI assistant integration"

---

**Gap 2: Detection of AI Environment**

**Impact:** Low — nice-to-have

**What's Missing:** If Ontos could detect it's running in an AI-assisted environment (via env vars like `CLAUDE_CODE` or similar), it could suggest `ontos export` automatically.

**Recommendation:** Defer to v4.0 — this is over-engineering for v3.0.

---

### Consistency

- [x] Aligns with Global CLI + Local Data feature
- [x] Aligns with config migration design
- [x] Aligns with hooks setup
- [x] Terminology mostly consistent

**Inconsistencies Found:**

**Issue: Terminology Drift**

**Severity:** Minor

The feature is called different things in different places:
- Section 5.6: "Agent Bootstrap Generation"
- Section 11: "Agent Bootstrap Export"
- commands/export.py description: "Session Bootstrap"
- Glossary: "Session Bootstrap" and "Agent Bootstrap Export"

**Proposed Fix:** Settle on one term. Recommendation: "Agent Bootstrap" (what it is) with "Session Bootstrap Problem" describing the problem it solves. Update:
- Section 5.6 title: `ontos export` — Agent Bootstrap Generation
- commands/export.py docstring: "Generate agent bootstrap files"
- Glossary: Keep both entries but clarify relationship

---

### UX Assessment

| Aspect | Assessment | Notes |
|--------|------------|-------|
| Friction level | Low | Simple `ontos export` command |
| Error clarity | Clear | Exit codes well-defined |
| Progressive disclosure | Yes | v3.0 = stub, v4.0 = templates |
| "Just works" philosophy | Aligned | Single command, sensible defaults |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation Suggestion |
|------|------------|--------|----------------------|
| Template becomes stale vs actual workflow | Medium | Low | Template references actual commands; keep in sync |
| Users don't know about `ontos export` | High | Low | Mention in `ontos init` output; document prominently |
| AI assistants ignore CLAUDE.md | Medium | Medium | This is a convention problem, not Ontos's to solve |
| Conflict with project's existing CLAUDE.md | Low | Medium | `ontos export` checks for existing file; --force to overwrite |

### Overall Assessment

**Quality:** Adequate (approaching Strong with minor fixes)

**Ready for Implementation:** Yes with minor fixes

The Session Bootstrap feature is a smart addition that addresses a real problem. The v3.0 stub approach is appropriate — establish the pattern, expand in v4.0. The template content could be richer, and the terminology should be standardized, but these are minor issues.

---

## 3. Round 1 Feedback Verification

### My Concerns Addressed?

| My Round 1 Issue | Chief Architect Decision | Verified? | Notes |
|------------------|--------------------------|-----------|-------|
| Q4 confirmation not in data flow | Accept | ✅ Properly addressed | Section 5.3 now shows step 5 "CONFIRM CHANGES" with --auto flag |
| Q5 version pinning missing | Accept | ✅ Properly addressed | Section 6.1 shows `required_version` field; version checking logic described |
| Missing `core/suggestions.py` | Accept | ✅ Properly addressed | Section 3.1 includes it; Section 4.1 has full interface spec |
| Missing `core/tokens.py` | Accept | ✅ Properly addressed | Section 3.1 includes it; Section 4.1 has full interface spec |
| ValidationOrchestrator missing curation | Accept | ✅ Properly addressed | Section 4.1 shows `validate_curation()` method and `CURATION` error type |
| Config fragmentation not resolved | Partial (IoC pattern) | ⚠️ Partially addressed | IoC pattern documented (Section 6.4), but validation constants location still not explicit |
| `ontos_lib.py` deprecation timeline unclear | Accept | ✅ Properly addressed | Section 13.1 lists it under "Delete" |
| Line count discrepancy (1,625 vs 1,904) | Accept | ✅ Properly addressed | Appendix C confirms 1,904; Section 4.2 acknowledges gap |
| `io/toml.py` interface missing | Accept | ✅ Properly addressed | Section 4.1 has full interface spec |
| `io/files.py` interface missing | Accept | ✅ Properly addressed | Section 4.1 has full interface spec |
| `ontos doctor` data flow missing | Accept | ✅ Properly addressed | Section 5.4 has complete data flow |

### Issues I Still Have Concerns About

#### Issue: Configuration Constants Location

**Original Concern:** The Validation-Maintainability analysis identified config fragmentation as critical. Where do `VALID_STATUS`, `TYPE_DEFINITIONS`, etc. live?

**Architect's Response:** Adopted IoC pattern (Section 6.4) for config loading. Documented that `core/config.py` "only defines `OntosConfig` dataclass and default values."

**Why I Still Have Concerns:** The IoC pattern addresses *how* config is loaded, not *where* validation constants are defined. The `OntosConfig` dataclass (Section 4.1) shows path/log settings but not validation constants like `VALID_STATUS` or `TYPE_DEFINITIONS`.

**Current Status:** This is acceptable for v3.0. The IoC pattern is the right approach. Validation constants can remain in `core/types.py` as module-level constants. My concern was about loading, which is now addressed.

**Recommendation:** No change needed. Mark as resolved.

### Critical Issues from Consolidation

| Critical Issue | Addressed? | Notes |
|----------------|------------|-------|
| Core purity violations (I/O in EXISTS modules) | ✅ Yes | Section 3.2 marks `staleness.py`, `proposals.py`, `history.py` as REFACTOR with clear note |
| Windows hook incompatibility | ✅ Yes | Section 8.1 shows Python-based shim; explicit note about why |
| Circular config dependency | ✅ Yes | Section 6.4 documents IoC pattern explicitly |
| Missing modules (`suggestions.py`, `tokens.py`) | ✅ Yes | Both in Section 3.1 and 4.1 |
| Q5 version pinning not implemented | ✅ Yes | Section 6.1 shows `required_version` field and checking logic |
| Q4 confirmation not in data flow | ✅ Yes | Section 5.3 shows full confirmation flow |
| Algorithm complexity (O(n²) cycle detection) | ✅ Yes | Section 4.1 `core/graph.py` constraints explicitly state "Do NOT use `path.index()` pattern" |
| Line count gap (~500-750 unaccounted) | ✅ Yes | Section 4.2 has explicit note acknowledging gap |

**All critical issues from Round 1 have been addressed.**

---

## 4. Regression Check

### Cross-Reference Integrity

- [x] Section numbers updated and consistent
- [x] Module references valid
- [x] No dangling references to removed content

**Issues Found:** None

### New Inconsistencies

- [x] No new terminology conflicts (except Session Bootstrap/Agent Bootstrap noted above)
- [x] No new constraint violations
- [x] New features don't conflict with existing sections

**Issues Found:**

**Minor: Version Number in Document Title vs Footer**

The document header says "Version: 1.3" but the footer says "v1.2". Should be consistent.

**Fix:** Update footer to "v1.3"

### Integration Check

- [x] New features integrate with existing data flows
- [x] New features covered in migration strategy (implicitly — `export` is new command)
- [ ] `commands/export.py` not explicitly in migration phases

**Issues Found:**

**Minor: `commands/export.py` Not in Migration Phases**

Section 13.2 doesn't explicitly mention creating `commands/export.py`. It's implied under "Create commands/..." but other new commands (`doctor.py`, `hook.py`) are explicitly listed.

**Fix:** Add to Phase 4:
```
├── Create commands/doctor.py, commands/hook.py, commands/export.py
```

---

## 5. Summary Assessment

### New Features Assessment

| Feature | Quality | Ready for Implementation | Critical Issues |
|---------|---------|--------------------------|-----------------|
| Global CLI + Local Data | Strong | Yes | 0 |
| Session Bootstrap (Agent Activation) | Adequate | Yes with minor fixes | 0 |

### Round 1 Resolution Assessment

| Category | Fully Resolved | Partially Resolved | Unresolved | Still Disagree |
|----------|----------------|--------------------|-----------:|----------------|
| My concerns | 10 | 1 | 0 | 0 |
| Critical (all reviewers) | 8 | 0 | 0 | — |

### Overall Architecture v1.3 Assessment

**Improvement from v1.0:** Significant

The architecture has improved substantially. Every critical issue from Round 1 was addressed. The new features (Global CLI model and Session Bootstrap) are well-designed and fill genuine gaps. The document is now comprehensive enough to guide implementation.

**Ready for Implementation:** Yes

**Conditions (if any):** None required; minor suggestions below

### Remaining Issues

**Critical (must fix before implementation):**
- None

**Major (should fix):**
- None

**Minor (can fix during implementation):**
1. Expand Session Bootstrap template content for better AI agent comprehension
2. Standardize terminology (Session Bootstrap vs Agent Bootstrap)
3. Add nested repository behavior to constraints
4. Document uninstallation flow
5. Fix version number in footer (1.2 → 1.3)
6. Add `commands/export.py` to migration Phase 4 explicitly

### Final Recommendation

[x] **Approve** — Architecture is ready for implementation planning

**Comments:**

The v1.3 architecture is a significant improvement over v1.0. The Chief Architect addressed all critical and major feedback from Round 1. The new features (Global CLI + Local Data model, Session Bootstrap) are well-conceived and properly integrated.

The architecture is now:
- **Complete:** All Q1-Q13 decisions implemented or correctly deferred
- **Consistent:** No internal contradictions; terminology mostly aligned
- **Correct:** Technical patterns are sound; edge cases considered
- **Implementation-ready:** Clear module specs, data flows, and migration phases

The remaining issues are all minor documentation improvements that can be addressed during implementation or in a quick doc pass before coding begins. There are no architectural concerns that would block starting implementation.

**Recommended next steps:**
1. Quick doc polish (5 items above)
2. Proceed to Phase 0: Golden Master Testing
3. Begin Phase 1: Package Structure

---

*End of Round 2 Review*

*Reviewed by Claude Opus 4.5 (Reviewer B) — 2026-01-12*