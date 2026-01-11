# Ontos v3.0 Architecture Review: Round 2

## Peer Architect: LLM [Gemini DeepThink]

## Date: 2026-01-12

## Architecture Version Reviewed: 1.1 (incorporating v1.3 updates)

---

## 1. New Feature Review: Global CLI + Local Data

### Correctness

* [x] Pattern is technically sound
* [x] Edge cases handled (Graceful degradation, Offline-first)
* [ ] Path resolution logic is correct

**Issues Found:**

* **Severity: Major** | **Issue: `paths.py` Status Mismatch**
* **Problem:** Constraint 2.6.8 mandates dynamic repo root detection ("walking up from CWD"). However, Section 3.2 lists `ontos/core/paths.py` as **"EXISTS"** (reuse as-is). The v2.x `paths.py` typically relies on `__file__` (script location) or static relative paths. Reusing it "as-is" in a global package will resolve to the library installation path, not the user's project path.
* **Proposed Fix:** Mark `paths.py` as **"REFACTOR"**. It must be updated to accept an injected `repo_root` (from `cli.py` -> `OntosConfig`) rather than inferring paths itself.


* **Severity: Minor** | **Issue: Nested Repository Ambiguity**
* **Problem:** Section 2.6.8 describes walking up to find `.git/` or `.ontos.toml`. In nested scenarios (e.g., a monorepo where a subdir is an Ontos project), the precedence isn't defined.
* **Proposed Fix:** Explicitly state precedence: stop at the *first* (closest) marker found.



### Completeness

* [x] Installation flow defined
* [x] Initialization flow defined
* [x] Usage patterns covered
* [ ] Uninstallation/cleanup defined
* [x] Upgrade path defined

**Gaps Found:**

* **Missing Interface:** Section 1.4 tasks `cli.py` with finding the root, but `io/files.py` (Section 4.1) does not define the public function `find_project_root(start_path: Path) -> Path` required to implement this.

### Consistency

* [x] Aligns with `.ontos.toml` config design
* [x] Aligns with shim hooks design
* [x] Aligns with CLI architecture
* [x] No conflicts with other sections

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation Suggestion |
| --- | --- | --- | --- |
| **CWD Path Confusion** | Medium | High | Users running `ontos log` from a subdirectory (`docs/`) may get relative paths in output. Ensure `OutputHandler` normalizes paths relative to the detected `repo_root`. |

### Overall Assessment

**Quality:** Strong
**Ready for Implementation:** Yes, pending `paths.py` refactor status update.

---

## 2. New Feature Review: Consistent Ontos Activation

### Correctness

* [x] Activation flow is technically sound
* [x] Error handling is appropriate
* [x] Idempotency handled

**Issues Found:**

* **Severity: Critical** | **Issue: Hook Collision Safety**
* **Problem:** `commands/init.py` (Section 4.1) states it will "Install shim hooks". It does not specify behavior if hooks already exist (e.g., `husky`, `pre-commit`, or user scripts). Silent overwrite causes data loss.
* **Proposed Fix:** `init` must detect existing hooks. If found and not an Ontos shim: Warn and abort, or prompt to backup (`pre-push.old`) and overwrite.


* **Severity: Minor** | **Issue: Legacy Command Reference**
* **Problem:** `commands/export.py` (Section 4.1) generates a `CLAUDE.md` that tells users to run: `"python3 ontos.py map (v2)"`. v3.0 explicitly removes `ontos.py` from the repo. Directing users to run a non-existent script is a regression.
* **Proposed Fix:** Remove the v2 command reference. Only reference `ontos map`.



### Completeness

* [x] First-time activation covered
* [x] Re-initialization covered
* [x] Upgrade from v2.x covered
* [x] Error states defined
* [x] Success confirmation defined

**Gaps Found:**

* **Legacy Cleanup:** The activation flow does not address cleaning up the v2 `.ontos/` script directory. If `ontos init` succeeds but leaves the old scripts, users have "zombie scripts" in their repo.
* **Proposed Fix:** Add a step to `commands/init.py`: "Detect legacy `.ontos/` directory and prompt to remove/archive."



### Consistency

* [x] Aligns with Global CLI + Local Data feature
* [x] Aligns with config migration design
* [x] Aligns with hooks setup
* [x] Terminology consistent with rest of doc

### UX Assessment

| Aspect | Assessment | Notes |
| --- | --- | --- |
| Friction level | Low | Auto-detection in `init` is excellent. |
| Error clarity | Clear | `doctor` command provides safety net. |
| Progressive disclosure | Yes | `export` is discoverable but optional. |
| "Just works" philosophy | Aligned | Smart defaults match philosophy. |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation Suggestion |
| --- | --- | --- | --- |
| **Hook Overwrite** | High | Critical | See "Hook Collision Safety" above. |
| **Zombie Scripts** | Medium | Medium | See "Legacy Cleanup" above. |

### Overall Assessment

**Quality:** Strong
**Ready for Implementation:** Yes with minor fixes.

---

## 3. Round 1 Feedback Verification

### My Concerns Addressed?

| My Round 1 Issue | Chief Architect Decision | Verified? | Notes |
| --- | --- | --- | --- |
| **Core Purity Violations** | Accept (Refactor) | ✅ Verified | Modules marked **REFACTOR** in Section 3.2. |
| **Windows Hook Incompatibility** | Accept (Python Shim) | ✅ Verified | Section 8.1 replaced shell shim with Python shim. |
| **Circular Config Dependency** | Accept (IoC) | ✅ Verified | Section 6.4 confirms `cli.py` loads config. |
| **Missing Modules (`suggestions`)** | Accept | ✅ Verified | Added to specs. |

### Issues I Still Have Concerns About

#### Issue: Q8 Summarization Interface Gap

**Original Concern:** Q8 (Progressive Complexity) was marked **CRITICAL** in Strategy. I flagged that the interface to execute this was missing from `core/graph.py`.

**Architect's Response:** "Defer... Address during implementation."

**Why I Still Have Concerns:** Q8 is strategic critical path. Leaving the API undefined risks logic leakage into the Command layer (`commands/map.py`), violating the "Thin Command" principle.

**Recommendation:** Add a placeholder signature to `core/graph.py` now: `def summarize_graph(graph: DependencyGraph, depth: int) -> DependencyGraph`.

### Critical Issues from Consolidation

| Critical Issue | Addressed? | Notes |
| --- | --- | --- |
| Windows Hook Support | ✅ Yes | Python shim adopted. |
| Core Purity Violations | ✅ Yes | Refactor plan is explicit. |
| Q4 Confirmation Missing | ✅ Yes | Added to data flow. |

---

## 4. Regression Check

### Cross-Reference Integrity

* [x] Section numbers still accurate
* [x] Module references still valid
* [x] No dangling references to removed content

### New Inconsistencies

* [x] No new terminology conflicts
* [ ] No new constraint violations
* [x] New features don't conflict with existing sections

**Issues Found:**

* **Constraint Violation:** Constraint 2.6.8 (Dynamic Root Detection) conflicts with Section 3.2 status of `paths.py` (EXISTS).

### Integration Check

* [x] New features integrate with existing data flows
* [x] New features covered in migration strategy
* [x] New features have test coverage requirements defined

---

## 5. Summary Assessment

### New Features Assessment

| Feature | Quality | Ready for Implementation | Critical Issues |
| --- | --- | --- | --- |
| Global CLI + Local Data | Strong | Yes (with conditions) | 0 |
| Consistent Ontos Activation | Strong | Yes (with conditions) | 1 (Hook Safety) |

### Round 1 Resolution Assessment

| Category | Fully Resolved | Partially Resolved | Unresolved | Still Disagree |
| --- | --- | --- | --- | --- |
| My concerns | 4 | 0 | 0 | 0 |
| Critical (all reviewers) | 3 | 0 | 0 | — |

### Overall Architecture v1.1 Assessment

**Improvement from v1.0:** Significant. The architecture has evolved from a clean-up plan to a robust distributed system design. The explicit "Global vs Local" ownership model and the Python-based hooks solve the primary v3.0 challenges effectively.

**Ready for Implementation:** Yes, with specific conditions.

**Conditions:**

1. **Refactor `paths.py`:** Update Section 3.2 to mark `ontos/core/paths.py` as **REFACTOR**. It cannot be reused as-is in a Global CLI.
2. **Hook Safety:** Update `commands/init.py` spec to mandate detection of existing hooks (warn/backup), forbidding silent overwrite.

### Remaining Issues

**Major (should fix):**

1. **Legacy Cleanup:** `init` should prompt to remove the v2 `.ontos/` directory.
2. **Q8 Interface:** Define `summarize_graph` in `core/graph.py` to lock in the Critical feature API.
3. **Root Detection:** Define `find_project_root` in `io/files.py`.

**Minor (can fix during implementation):**

1. **Export Content:** Remove v2 command reference from `commands/export.py`.

### Final Recommendation

[x] **Approve with Minor Changes**

**Required Changes:**

1. **Update `paths.py` Status:** Mark as **REFACTOR** in Section 3.2; note requirement to support dynamic root injection.
2. **Define Hook Safety:** Update `commands/init.py` spec to include "Backup or Warn if hook exists."
3. **Define Legacy Cleanup:** Update `commands/init.py` to include legacy `.ontos/` detection.