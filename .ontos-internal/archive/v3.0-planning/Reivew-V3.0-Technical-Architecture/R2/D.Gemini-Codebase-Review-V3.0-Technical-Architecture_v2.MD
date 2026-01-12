# Ontos v3.0 Architecture Review: Round 2

## Peer Architect: LLM [D] (Gemini DeepThink)

## Date: 2026-01-12

## Architecture Version Reviewed: 1.3

---

## 1. New Feature Review: Global CLI + Local Data

### Correctness

* [x] Pattern is technically sound (Git analogy holds up).
* [x] Edge cases handled (Repo root detection specified via "walking up").
* [ ] Path resolution logic is correct.

**Issues Found:**

* **Missing Root Detection Interface (Major):** Section 2.6 Constraint 8 ("Working Directory Independence") is critical for a global tool. The architecture states the CLI must "detect repo root by walking up," but no module in Section 4 (`io/files.py` or `core/paths.py`) exposes a `find_project_root(cwd: Path) -> Path` function. Without this specific implementation detail, commands run from subdirectories (e.g., `cd docs/strategy; ontos log`) will likely fail or create `.ontos.toml` in the wrong place.

### Completeness

* [x] Installation flow defined.
* [x] Initialization flow defined.
* [x] Usage patterns covered.
* [ ] Uninstallation/cleanup defined.
* [x] Upgrade path defined.

**Gaps Found:**

* **Hook Cleanup:** No mechanism defined to remove shim hooks. If a user uninstalls the pip package, the git hooks remain and will error out (or warn) on every push.

### Consistency

* [x] Aligns with `.ontos.toml` config design.
* [x] Aligns with shim hooks design.
* [x] Aligns with CLI architecture.

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation Suggestion |
| --- | --- | --- | --- |
| **PATH Visibility** | High (Windows) | Medium | The Python shim relies on `ontos` being in the system PATH. `pip install` often places binaries in non-PATH locations (e.g., `%APPDATA%\Python\Scripts`). **Mitigation:** Shim should fall back to `sys.executable -m ontos` if the binary is not found. |

### Overall Assessment

**Quality:** Strong
**Ready for Implementation:** Yes with minor fixes (Add `find_project_root` to spec).

---

## 2. New Feature Review: Consistent Ontos Activation (`init` + `export`)

### Correctness

* [x] Activation flow is technically sound.
* [x] Error handling is appropriate.
* [x] Idempotency handled.

**Issues Found:**

* **Write Interface Missing:** `commands/export.py` needs to write `CLAUDE.md`. The `io/files.py` interface (Section 4.1) only lists `scan_documents` and `read_document`. It lacks a safe `write_file` primitive.
* **Strategy Deviation (Minor):** Strategy Decision Q2 explicitly stated "Defer export to CLAUDE.md to v4". v1.3 adds this feature. While valuable as a "Session Bootstrap," it technically conflicts with the Strategy document.

### Completeness

* [x] First-time activation covered.
* [x] Re-initialization covered.
* [x] Upgrade from v2.x covered.
* [x] Error states defined.

**Gaps Found:**

* **Integration of `export`:** The `commands/init.py` spec does not explicitly mention running or prompting for `export`. If `init` doesn't generate `CLAUDE.md`, the "Session Bootstrap" feature requires manual discovery, reducing its value.

### Consistency

* [x] Aligns with Global CLI + Local Data feature.
* [x] Aligns with config migration design.
* [x] Aligns with hooks setup.

### UX Assessment

| Aspect | Assessment | Notes |
| --- | --- | --- |
| Friction level | Low | Single command setup. |
| Error clarity | Clear | Exit codes defined. |
| Progressive disclosure | Yes | `export` hidden until needed. |
| "Just works" philosophy | Aligned | Smart defaults in `init`. |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation Suggestion |
| --- | --- | --- | --- |
| **Windows Binary Name** | Medium | Medium | The Python shim uses `#!/usr/bin/env python3`. On Windows, the binary is often `python.exe` or `py.exe`, and `python3` may not exist. **Mitigation:** `ontos init` should detect OS and write the appropriate shebang or wrapper. |

### Overall Assessment

**Quality:** Strong
**Ready for Implementation:** Yes with minor fixes.

---

## 3. Round 1 Feedback Verification

### My Concerns Addressed?

| My Round 1 Issue | Chief Architect Decision | Verified? | Notes |
| --- | --- | --- | --- |
| **Core Purity Violations** | **Accept** | ✅ Verified | Modules `staleness.py`, `proposals.py`, `history.py` marked **REFACTOR**. I/O extraction plan explicit in Section 3.2. |
| **Windows Hooks** | **Accept** | ✅ Verified | Switched to Python-based shim (`#!/usr/bin/env python3`). |
| **Missing Modules** | **Accept** | ✅ Verified | `suggestions.py` and `tokens.py` added to Section 3.1. |
| **Algo Complexity** | **Accept** | ✅ Verified | Constraint added to `core/graph.py` spec. |
| **Missing Config Fields** | **Accept** | ✅ Verified | `required_version` added to `OntosConfig`. |

### Issues I Still Have Concerns About

None. The Chief Architect's response was comprehensive and the v1.3 document reflects the changes accurately.

### Critical Issues from Consolidation

| Critical Issue | Addressed? | Notes |
| --- | --- | --- |
| **Circular Config Dependency** | ✅ Yes | Solved via Inversion of Control pattern in Section 6.2 (referenced). |
| **Q4 Confirmation** | ✅ Yes | Confirmed in Response (Data Flow update accepted). |
| **Windows Hook Support** | ✅ Yes | Python shim pattern adopted. |

---

## 4. Regression Check

### Cross-Reference Integrity

* [x] Section numbers still accurate.
* [x] Module references still valid.
* [x] No dangling references to removed content.

### New Inconsistencies

* [x] No new terminology conflicts.
* [x] No new constraint violations.
* [x] New features don't conflict with existing sections.

**Note:** As mentioned in Section 2, the addition of `ontos export` technically conflicts with Strategy Q2 ("Defer"), but this is an acceptable scope expansion for usability.

### Integration Check

* [x] New features integrate with existing data flows.
* [x] New features covered in migration strategy.
* [x] New features have test coverage requirements defined.

---

## 5. Summary Assessment

### New Features Assessment

| Feature | Quality | Ready for Implementation | Critical Issues |
| --- | --- | --- | --- |
| Global CLI + Local Data | Strong | Yes | 0 |
| Consistent Ontos Activation | Strong | Yes | 0 |

### Round 1 Resolution Assessment

| Category | Fully Resolved | Partially Resolved | Unresolved | Still Disagree |
| --- | --- | --- | --- | --- |
| My concerns | 5 | 0 | 0 | 0 |
| Critical (all reviewers) | 3 | 0 | 0 | — |

### Overall Architecture v1.1 Assessment

**Improvement from v1.0:** Significant.
The architecture has matured from "conceptually sound but technically flawed" to a robust implementation plan. The decision to mark legacy modules as **REFACTOR** rather than **EXISTS** saved the project from immediate technical debt, and the Python-based shim resolves the distribution block.

**Ready for Implementation:** **Yes**

**Conditions:**

1. **Add Root Detection:** Explicitly specify `find_project_root` in `io/files.py` to satisfy Constraint 8.
2. **Add Write Primitive:** Explicitly specify `write_text_file` in `io/files.py` to support `ontos export`.

### Remaining Issues

**Critical (must fix before implementation):**

* None.

**Major (should fix):**

* **Missing Root Detection Logic:** Without this, CLI operations from subdirectories are undefined.
* **Shim Robustness:** Ensure the shim handles `python` vs `python3` naming on Windows and falls back gracefully if `ontos` isn't in PATH.

**Minor (can fix during implementation):**

* **Link `init` and `export`:** `ontos init` should prompt or automatically run `export` to close the bootstrap loop.
* **Strategy Document Sync:** Update Strategy Q2 to reflect the inclusion of `ontos export` as a "Bootstrap" feature.

### Final Recommendation

[x] **Approve with Minor Changes**

* Add `find_project_root` to `io/files.py` spec.
* Add `write_text_file` to `io/files.py` spec.
* Update `commands/init.py` spec to include `export` integration.