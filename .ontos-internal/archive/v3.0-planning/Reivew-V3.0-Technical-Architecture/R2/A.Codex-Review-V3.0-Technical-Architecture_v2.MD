# Ontos v3.0 Architecture Review: Round 2

## Peer Architect: GPT-5.2 Thinking

## Date: 2026-01-11

## Architecture Version Reviewed: 1.1 (document appears to be v1.3)

---

## 1. New Feature Review: Global CLI + Local Data

## New Feature 1: Global CLI + Local Data

### Correctness

* [x] Pattern is technically sound
* [ ] Edge cases handled (multiple repos, nested repos, no git, etc.)
* [ ] Path resolution logic is correct

**Issues Found:**

* **Issue:** Hook execution path is brittle if `ontos` isn’t on `PATH` at hook-time (common with venvs, CI, GUI git clients).
  **Severity:** Major
  **Proposed fix:** Make the shim invoke Ontos via the interpreter that installed it: `sys.executable -m ontos hook pre-push` (store `sys.executable` in the generated hook at init-time). Keep the current “warn + skip” as a last-resort fallback, but don’t make it the primary path.
  Evidence: shim currently shells out to `ontos` and explicitly skips if missing. 
* **Issue:** Repo-root detection edge cases aren’t explicitly handled (git worktrees/submodules where `.git` is a file, nested repos, “no git” directories).
  **Severity:** Major
  **Proposed fix:** Define root resolution precedence explicitly:

  1. nearest `.ontos.toml` walking up, 2) git root walking up treating `.git` as file or dir, 3) error with actionable hint. Add tests for: worktree `.git` file, submodule `.git` file, nested repo, and “mono-repo with nested `.ontos.toml`”.
     Evidence: doc states “discover repo root from any subdirectory” but doesn’t spell out precedence/edge handling. 

### Completeness

* [x] Installation flow defined
* [x] Initialization flow defined
* [x] Usage patterns covered
* [ ] Uninstallation/cleanup defined
* [ ] Upgrade path defined

**Gaps Found:**

* **Gap:** No explicit “repo cleanup” story. Global uninstall is easy, but repos will still have `.ontos/` data and installed hooks.
  **Impact:** Users will ask “how do I remove this from a repo” and CI workflows will get messy if hooks persist.
  **Proposed addition:** Add `ontos deinit` (or `ontos init --remove`) to remove `.git/hooks` shims and optionally archive `.ontos/`. Keep it simple: no deep deletes by default, just remove hooks + print what remains.
* **Gap:** Upgrade expectations are implied but not specified.
  **Impact:** Version skew between global CLI and per-repo expectations becomes a support trap.
  **Proposed addition:** Document the contract: `.ontos.toml` contains `required_version`; CLI warns (or errors if configured) when incompatible. The schema already includes this field, but the behavior contract should be explicit.

### Consistency

* [x] Aligns with `.ontos.toml` config design
* [x] Aligns with shim hooks design
* [x] Aligns with CLI architecture
* [ ] No conflicts with other sections

**Inconsistencies Found:**

* **Inconsistency:** The design goal is “just works”, but hook enforcement currently depends on PATH state. That’s a UX contradiction unless you shift the shim to `python -m ontos`. 

### Risk Assessment

| Risk                                                       | Likelihood | Impact | Mitigation Suggestion                                                                       |
| ---------------------------------------------------------- | ---------- | ------ | ------------------------------------------------------------------------------------------- |
| Hook silently not enforcing due to missing `ontos` on PATH | H          | H      | Generate shim that runs `sys.executable -m ontos …` and only fall back to PATH              |
| Nested repo/submodule/worktree root mis-detection          | M          | H      | Define precedence + add tests for `.git` file + nested `.ontos.toml`                        |
| “No git repo” users blocked unnecessarily                  | M          | M      | Allow `.ontos.toml` to define root even without git, and gate hook install behind `--hooks` |

### Overall Assessment

**Quality:** Adequate
**Ready for Implementation:** Yes with minor fixes

---

## 2. New Feature Review: Consistent Ontos Activation

## New Feature 2: Consistent Ontos Activation

### Correctness

* [ ] Activation flow is technically sound
* [ ] Error handling is appropriate
* [ ] Idempotency handled (re-running init)

**Issues Found:**

* **Issue:** The new “Session Bootstrap / export” content includes mixed v2/v3 command guidance (“python3 ontos.py map” vs “ontos map”). That will confuse users and agents, and it’s self-inflicted.
  **Severity:** Major
  **Proposed fix:** Output must be v3-only. If you want backward compatibility, detect v2 vs v3 repo by presence of `.ontos.toml` and emit one correct instruction set, not both.
  Evidence: export template explicitly contains both command variants.
* **Issue:** Overwrite/merge behavior for `CLAUDE.md` / `AGENTS.md` isn’t fully nailed down. If you clobber user content, you’ll lose trust fast.
  **Severity:** Major
  **Proposed fix:** Default to non-destructive:

  * If file exists, append an “Ontos” block delimited by markers, or create `.ontos/CLAUDE.ontos.md` and print “include this snippet”.
  * Only overwrite with `--force`.
    Evidence: `ontos export` is specified, but the collision/merge contract is not fully spelled out.

### Completeness

* [ ] First-time activation covered
* [ ] Re-initialization covered
* [ ] Upgrade from v2.x covered
* [ ] Error states defined
* [ ] Success confirmation defined

**Gaps Found:**

* **Gap:** “Activation” is split between repo init (`ontos init`) and session bootstrap (`ontos export`). The doc doesn’t clearly define the intended user journey, so users will do the wrong thing first.
  **Impact:** Increased friction and support burden.
  **Proposed addition:** A single “Getting started” flow in the architecture:

  1. `pip install ontos`
  2. `cd repo && ontos init`
  3. optional: `ontos export --tool claude`
  4. `ontos map`
     Tie that directly to the repo markers (`.ontos.toml`, `.ontos/`) and the hook install. 
* **Gap:** Upgrade/migration behavior from v2 repos for activation artifacts is not defined.
  **Impact:** Existing users will be the first to hit this.
  **Proposed addition:** `ontos init --migrate` can: detect legacy `ontos.py`, migrate config into `.ontos.toml`, and optionally generate the bootstrap snippet without touching user-managed docs unless requested.

### Consistency

* [x] Aligns with Global CLI + Local Data feature
* [ ] Aligns with config migration design
* [ ] Aligns with hooks setup
* [ ] Terminology consistent with rest of doc

**Inconsistencies Found:**

* **Inconsistency:** If the strategy doc still considers export templates “deferred”, the presence of `ontos export` is a scope/decision mismatch. If the decision changed, it needs to be reflected explicitly in the “decisions implemented” section of the architecture.
  Evidence: architecture change history calls out “Session Bootstrap Feature (ontos export + v4 extension points)” as a new addition. 

### UX Assessment

| Aspect                  | Assessment | Notes                                                                             |
| ----------------------- | ---------- | --------------------------------------------------------------------------------- |
| Friction level          | Medium     | Two similar-sounding steps (`init` vs `export`) without a single canonical path   |
| Error clarity           | Unclear    | Collision handling for existing `CLAUDE.md` / `AGENTS.md` needs explicit contract |
| Progressive disclosure  | Yes        | Making export optional is good, but the doc needs a clearer “when to use it”      |
| "Just works" philosophy | Tension    | Mixed v2/v3 instructions and unclear overwrite behavior will cause foot-guns      |

### Risk Assessment

| Risk                                   | Likelihood | Impact | Mitigation Suggestion                                           |
| -------------------------------------- | ---------- | ------ | --------------------------------------------------------------- |
| Users lose custom `CLAUDE.md` content  | M          | H      | Non-destructive default, marker-based insertion, `--force` only |
| Agents follow wrong command (v2 vs v3) | H          | M      | Emit v3-only instructions, detect repo type if needed           |
| “Activation” concept becomes muddled   | M          | M      | Add one canonical onboarding flow and link commands to it       |

### Overall Assessment

**Quality:** Needs Work
**Ready for Implementation:** No — needs revision

---

## 3. Round 1 Feedback Verification

## Round 1 Feedback Verification

### My Concerns Addressed?

| My Round 1 Issue                                          | Chief Architect Decision | Verified?              | Notes                                                                                 |
| --------------------------------------------------------- | ------------------------ | ---------------------- | ------------------------------------------------------------------------------------- |
| Global CLI + per-repo data model should be explicit       | Accept                   | ✅ Properly addressed   | Now clearly specified as global install + local `.ontos/` + `.ontos.toml`.            |
| Add shim hooks that degrade gracefully                    | Accept                   | ✅ Properly addressed   | Python shim + warn/skip behavior is specified.                                        |
| But shim must not rely on PATH                            | Modify (implied)         | ⚠️ Partially addressed | Still shells out to `ontos`; needs `python -m ontos` for “just works”.                |
| Add `required_version` in config schema                   | Accept                   | ✅ Properly addressed   | Field appears in schema section.                                                      |
| Add missing data flows (doctor, confirmation, hook flows) | Accept                   | ⚠️ Partially addressed | `doctor` and confirmation now appear, but I’d re-check hook flow coverage end-to-end. |
| Keep v3 doc v3-only, avoid mixed legacy instructions      | Accept (should be)       | ❌ Not addressed        | Export template still mixes v2/v3 commands.                                           |

### Issues I Still Have Concerns About

#### Issue: Hook execution depends on PATH

**Original Concern:** Hooks should be reliable without users “remembering” to have the right environment active.

**Architect's Response:** Add Python shim hook that calls `ontos` and skips with warning if missing.

**Why I Still Have Concerns:** Skipping hook enforcement is the common case in GUI git clients and CI unless PATH is carefully managed. That violates “it just works” and makes enforcement non-deterministic.

**Recommendation:** Generate shim that runs `sys.executable -m ontos …` using the interpreter captured at `ontos init` time. Keep warn/skip only as fallback. 

### Critical Issues from Consolidation

| Critical Issue                                   | Addressed? | Notes                                                                                                 |
| ------------------------------------------------ | ---------- | ----------------------------------------------------------------------------------------------------- |
| Hook behavior should be non-blocking but visible | ✅ Yes      | Warn + skip is documented.                                                                            |
| Clear global install vs per-repo state           | ✅ Yes      | Distribution model is explicit.                                                                       |
| Avoid scope creep / decision drift               | ⚠️ Partial | `ontos export` was added; if that was previously deferred, call it out as a deliberate scope change.  |

---

## 4. Regression Check

## Regression Check

### Cross-Reference Integrity

* [ ] Section numbers still accurate
* [ ] Module references still valid
* [ ] No dangling references to removed content

**Issues Found:** I did not do a full hyperlink-level audit, but I did spot one conceptual regression: the doc is labeled as v1.3 in its own change history while the review packet calls it v1.1, which makes change tracking harder during implementation. 

### New Inconsistencies

* [ ] No new terminology conflicts
* [ ] No new constraint violations
* [ ] New features don't conflict with existing sections

**Issues Found:**

* Mixed v2/v3 command guidance inside a v3 architecture doc (in the export template).

### Integration Check

* [ ] New features integrate with existing data flows
* [ ] New features covered in migration strategy
* [ ] New features have test coverage requirements defined

**Issues Found:**

* Export/activation feature needs explicit integration into migration story (what happens for existing `CLAUDE.md` and how to avoid destructive writes).

---

## 5. Summary Assessment

## Summary Assessment

### New Features Assessment

| Feature                     | Quality    | Ready for Implementation | Critical Issues |
| --------------------------- | ---------- | ------------------------ | --------------- |
| Global CLI + Local Data     | Adequate   | Minor fixes              | 1               |
| Consistent Ontos Activation | Needs Work | No                       | 2               |

### Round 1 Resolution Assessment

| Category                 | Fully Resolved | Partially Resolved | Unresolved | Still Disagree |
| ------------------------ | -------------- | ------------------ | ---------: | -------------- |
| My concerns              | 3              | 2                  |          1 | 1              |
| Critical (all reviewers) | 2              | 1                  |          0 | —              |

### Overall Architecture v1.1 Assessment

**Improvement from v1.0:** Moderate
**Ready for Implementation:** Yes with conditions

**Conditions (if any):**

* Fix hook invocation to not rely on PATH. Use interpreter-based `python -m ontos`.
* Make “activation” non-confusing and non-destructive. Export must be v3-only and safe with existing files.

### Remaining Issues

**Critical (must fix before implementation):**

* `ontos export` template must not mix v2/v3 commands, and must define safe collision behavior for existing `CLAUDE.md` / `AGENTS.md`.

**Major (should fix):**

* Hook shim should invoke Ontos in a PATH-independent way for reliability. 
* Spell out repo-root detection precedence and test the edge cases (worktrees/submodules/nested repos). 

**Minor (can fix during implementation):**

* Align the doc versioning (v1.1 vs v1.3) so reviewers and implementers can diff cleanly. 

### Final Recommendation

* [ ] **Approve** — Architecture is ready for implementation planning
* [x] **Approve with Minor Changes** — Small fixes needed, list below
* [ ] **Request Revision** — Significant issues remain, list below

**If not full approval, required changes:**

1. Change shim hooks to call Ontos via the installing interpreter (`sys.executable -m ontos …`) rather than relying on `ontos` on PATH. 
2. Fix `ontos export` output to be v3-only and define a non-destructive merge/overwrite contract for existing agent instruction files.
