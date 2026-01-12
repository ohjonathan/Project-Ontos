# Phase 1 Implementation Spec Review - Gemini

**Reviewer:** Gemini (Alignment Reviewer)
**Date:** 2026-01-12
**Spec Version:** 1.0

---

## 1. Alignment Verification

### 1.1 Roadmap Alignment

| Roadmap Requirement (Section 3) | Spec Addresses? | Correctly? | Notes |
|--------------------------------|-----------------|------------|-------|
| `pyproject.toml` with metadata | Yes | Yes | Correctly defines deps and entry points. |
| Package root `ontos/__init__.py` | Yes | Yes | Defines version and exports. |
| Entry point `ontos/__main__.py` | Yes | Yes | Enables `python -m ontos`. |
| Move `core/` modules | Yes | Yes | Moves from `.ontos/scripts/`. |
| Move `ui/` modules | Yes | Yes | Moves from `.ontos/scripts/`. |
| `pip install -e .` works | Yes | **Partial** | Installs, but CLI functionality is compromised (see below). |
| 303 tests pass | Yes | Yes | Includes update tasks for tests. |
| Golden Master tests pass | Yes | Yes | Includes verification step. |

### 1.2 Architecture Alignment

| Architecture Constraint | Spec Compliant? | Evidence |
|------------------------|-----------------|----------|
| Zero-dep core (stdlib only) | Yes | Dependencies are correctly isolated in `pyproject.toml`. |
| Layered architecture respected | Yes | `core/` and `ui/` separation is preserved. |
| Core cannot import from commands/ui/io | Yes | Existing constraint maintained. |
| Package structure matches Section 3 | **Deviation** | Spec implements an *intermediate* state (shim CLI) rather than the final v3.0 structure. This aligns with the phased Roadmap but deviates from the final Architecture reference. |

### 1.3 Strategy Alignment

| Relevant Strategy Decision | Spec Implements? | Notes |
|---------------------------|------------------|-------|
| Q11: Modular structure | Partial | Starts the move to `ontos/` but leaves logic in `scripts/`. |
| Q12: Python (not Node) | Yes | Pure Python. |
| Q13: Markdown primary | N/A | No functional change. |

### 1.4 Alignment Verdict

**Overall Alignment:** **Weak**

**Deviations Found:**
1.  **Global CLI Promise:** Strategy and Architecture v1.4 promise a "Global CLI" (`pip install ontos`). This spec implements a CLI that *only* works when the repository root is present, because it delegates to `ontos.py` and `.ontos/scripts/` which are not included in the package. This violates the core distribution goal of v3.0.

---

## 2. Spec Quality

### 2.1 Completeness

| Aspect | Complete? | Gaps |
|--------|-----------|------|
| All files specified | Yes | `pyproject.toml`, `__init__.py`, `cli.py` defined. |
| All tasks listed | Yes | Step-by-step migration is detailed. |
| All tests defined | Yes | Coverage of existing + Golden Master. |
| All risks identified | No | Missing risk of "package installed but CLI broken". |
| Verification steps clear | Yes | Commands provided. |

### 2.2 Implementability

- [x] File paths are specific
- [x] Code is complete
- [x] Order of operations is clear
- [ ] **Success criteria are testable:** The criterion "`ontos` command available in PATH" is testable but will fail behaviorally if run outside the repo.
- [ ] **Ambiguities:** How does `ontos/cli.py` find `ontos.py` if installed globally? (It relies on `Path(__file__).parent.parent`, which breaks if installed to `site-packages`).

### 2.3 Technical Correctness

| Technical Aspect | Correct? | Issues |
|------------------|----------|--------|
| `pyproject.toml` syntax | Yes | Standard setuptools configuration. |
| Entry point configuration | Yes | Correctly points to `ontos.cli:main`. |
| Import statements | Yes | Re-exports look correct. |
| Python version compatibility | Yes | 3.9+ specified. |
| **Package discovery** | **NO** | `pyproject.toml` includes `ontos/` but logic depends on root files (`ontos.py`, `.ontos/`) which are excluded. |

---

## 3. Adversarial Analysis

### 3.1 Assumptions to Challenge

| Assumption in Spec | Why It Might Be Wrong | Impact If Wrong |
|--------------------|----------------------|-----------------|
| `ontos.py` is available at `../ontos.py` | When installed via pip (even editable), the package lives in `site-packages` (or src link). The root scripts are NOT packaged. | CLI crashes immediately upon execution. |
| `.ontos/scripts/` is available | Same as above. Not included in `pyproject.toml`. | CLI cannot delegate; functionality missing. |
| "Zero behavior change" implies "Keep code where it is" | Keeping code in root scripts makes packaging impossible. | Conflict between Phase 1 goal (Packaging) and Constraint (Zero Change). |

### 3.2 Failure Modes

| What Could Fail | How | Detection | Recovery |
|-----------------|-----|-----------|----------|
| **CLI Crash** | User runs `ontos map`. `cli.py` tries to subprocess `../ontos.py`. File not found. | Immediate crash. | Revert to direct script usage. |
| **Fresh Install Fail** | `pip install .` in clean env. `ontos init` fails because `ontos_init.py` isn't packaged. | CI check (if added). | Manually copy script. |

### 3.3 What's the Architect Not Seeing?

The Architect is focused on **repository structure** (how files look in the editor) and ignoring **distribution structure** (how files look in `site-packages`).
-   They assume `pip install -e .` keeps the repo structure intact for the tool's runtime execution. This is true *only* for editable installs *if* the relative paths hold.
-   They missed that `pyproject.toml` configuration `include = ["ontos"]` explicitly excludes the legacy scripts the CLI depends on.

---

## 4. Critical Assessment

### 4.1 Strongest Concerns

1.  **Broken Distribution Model:** The spec claims to create a pip-installable package, but creates one that is non-functional unless you are standing inside the source repository. This satisfies the letter of "install -e ." but fails the spirit of "Phase 1: Package Structure".
2.  **Fragile Delegation:** `ontos/cli.py` shelling out to `sys.executable ... ontos.py` is extremely brittle. It relies on the presence of a file that is not part of the package.
3.  **`ontos_init.py` Orphaned:** Initialization logic is left at the root, meaning a user cannot `pip install ontos` and then `ontos init`. They still need to clone the repo first.

### 4.2 What Would You Do Differently?

| Spec's Approach | Alternative Approach | Why Alternative Might Be Better |
|-----------------|---------------------|--------------------------------|
| Delegate to root `ontos.py` | Move `ontos.py` and `.ontos/scripts` INSIDE `ontos/legacy/` | Makes them part of the package. Ensures they exist wherever the package is installed. |
| Shell out via subprocess | Import and call `main()` | Avoids Python interpreter startup cost. More robust traceback. |
| Keep `ontos_init.py` at root | Move to `ontos/commands/init.py` | Makes `ontos init` available globally. |

### 4.3 Scope Assessment

**Scope creep detected:** No. Actually, the scope is *too narrow* regarding the movement of script logic.

**Items missing that should be added:**
-   Strategy for bundling legacy scripts (e.g., `MANIFEST.in` or moving files).
-   Verification step: `pip install .` (non-editable) and run in a temp dir.

---

## 5. Summary

### 5.1 Verdict

| Aspect | Rating |
|--------|--------|
| Alignment with approved docs | **Weak** (Fails "Global CLI" promise) |
| Spec completeness | **Adequate** |
| Technical correctness | **Weak** (Packaging config excludes dependencies) |
| Implementability | **Strong** (Clear steps) |
| Risk coverage | **Weak** (Misses distribution failure) |

**Overall Recommendation:** **Request Revision**

### 5.2 Blocking Issues

1.  **Package Integrity:** The spec defines a package (`ontos/`) that depends on files (`.ontos/scripts/`, `ontos.py`) that are **not included in the package**. This guarantees the CLI will fail for any non-editable installation or any execution outside the repo root.
2.  **Init Availability:** `ontos_init.py` is not packaged, preventing `ontos init` from working as a global command.

### 5.3 Major Issues

1.  **Hardcoded Relative Paths:** `ontos/cli.py` uses `Path(__file__).parent.parent / ".ontos"` which assumes a specific directory layout that won't exist in `site-packages`.

### 5.4 Top 3 Improvements

1.  **Bundle Legacy Scripts:** Move `.ontos/scripts` into `ontos/_scripts` (or similar) so they travel with the package.
2.  **Internalize Dispatch:** Have `ontos/cli.py` import the legacy logic instead of shelling out.
3.  **Package Init:** Move `ontos_init.py` logic into `ontos/core/` or `ontos/commands/` immediately.

### 5.5 What This Spec Does Well

The migration plan for the `core/` and `ui/` modules is excellent—clean, safe, and well-ordered. The use of Golden Master tests as a safety net is the correct strategy. The `ontos_lib.py` shim is a thoughtful backward-compatibility feature.