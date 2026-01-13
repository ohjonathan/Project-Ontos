# Review Board Report: Phase 3 Implementation Spec
**Author:** Gemini (Peer Reviewer), Claude (Alignment Reviewer), Codex (Adversarial Reviewer)
**Date:** 2026-01-13

## 1. Gemini — Peer Reviewer Report

### 1.1 Open Questions Research & Recommendations

#### Q1: Config File Location
**Research Findings:**
*   **Repo-Root Hidden:** `.prettierrc`, `.eslintrc` (often allow both hidden and visible).
*   **Repo-Root Visible:** `Cargo.toml`, `package.json`, `ruff.toml`.
*   **Python Standard:** `pyproject.toml` `[tool.name]` (Black, Ruff, Poetry).
*   **Directory-Based:** `.cargo/config.toml` (Cargo local config), `.vscode/settings.json`.

**Recommendation:** **`.ontos.toml` (Spec's Choice)** or **`ontos.toml` (Visible)**.
*   *Reasoning:* Since Ontos is language-agnostic, we should not rely on `pyproject.toml` (which assumes a Python project).
*   *Critique:* Hidden files (`.ontos.toml`) contradict the "Intent over Automation" philosophy slightly—users should be aware of the configuration. However, they keep the root clean.
*   *Verdict:* Stick with `.ontos.toml` for v3.0 to mimic `.gitignore`, but allow `ontos.toml` (visible) as a fallback in `io/config.py` lookup logic if possible, or stick to strict spec to avoid ambiguity. The spec is acceptable.

#### Q2: Init Failure Behavior
**Research Findings:**
*   **Git:** `git init` on existing repo is safe (reinitializes/idempotent).
*   **NPM:** `npm init` on existing `package.json` reads it and prompts for updates (interactive).
*   **Cargo:** `cargo init` fails if target directory is not empty (unless flags used).

**Recommendation:** **Exit 1 with helpful message (Spec's Choice).**
*   *Reasoning:* Overwriting configuration is destructive. Silent success is confusing if the user wanted to reset defaults.
*   *Refinement:* The error message `Already initialized. Use --force to reinitialize.` is perfect.

#### Q3: Init UX Flow
**Research Findings:**
*   **NPM/Poetry:** Wizard-style (Ask name? Version? Deps?). High friction but high correctness.
*   **Git/Cargo:** Minimal (Just do it). Low friction.

**Recommendation:** **Minimal (Spec's Choice).**
*   *Reasoning:* Ontos v3.0 is a tool for *developers* who likely just want "standard defaults". `ontos init` should just work.
*   *Future:* Reserve `--interactive` for v3.1 if complex config options (like MCP servers) are added.

### 1.2 Spec Completeness
*   **Overview/Scope:** Complete.
*   **Migration:** Detailed day-by-day plan.
*   **Testing:** Good coverage of edge cases (legacy detection, collision).
*   **Missing:**
    *   **Schema Versioning:** The config has `version = "3.0"`. The spec needs to define how `io/config.py` handles a future `version = "4.0"` file (ignore? error? warn?).
    *   **Global Config:** Does `ontos init` check for a `~/.ontos/config` (global user defaults)? The Architecture mentions "Global CLI + Local Data", implying no global user config yet. Spec is consistent but worth noting.

### 1.3 Config System Design
*   **Dataclasses:** `core/config.py` design is solid. Using `field(default_factory=...)` for mutable defaults (lists) is correct and prevents common Python bugs.
*   **Resolution:** CLI → Env → File → Defaults is standard and correct.
*   **Validation:** The spec delegates validation to `core/config.py` but doesn't explicitly show the validation logic in the code snippet (e.g., checking `max_dependency_depth > 0`). *Suggestion: Add a `validate()` method to `OntosConfig`.*

### 1.4 Init Command UX
*   **Legacy Warning:** "Warning: Legacy .ontos/scripts/ detected..." is excellent.
*   **Hook Safety:** The collision detection logic (`_is_ontos_hook`) checking for "ontos" AND "shim" is a smart, robust heuristic.
*   **Success Message:** The tip "Run 'ontos export'..." is great for onboarding.

### 1.5 Implementability
*   **Code Quality:** The provided code snippets for `commands/init.py` and `io/config.py` are high quality and implementable.
*   **Architecture Compliance:** Correctly separates `core` (dataclasses) from `io` (file ops).

---

## 2. Claude — Alignment Reviewer Report

### 2.1 Roadmap Alignment (Section 5)
*   **`commands/init.py`**: **Aligned.** Spec implements this.
*   **Legacy Detection**: **Aligned.** Spec includes check for `.ontos/scripts/`.
*   **Hook Collision Safety**: **Aligned.** Spec implements the "Warn and Skip" logic for foreign hooks and "Replace" for Ontos hooks.
*   **Exit Codes**: **Aligned.** Matches Roadmap 5.3 (0=Success, 1=Already Init, 2=Not Git, 3=Hooks Skipped).
*   **Config Template**: **Aligned.** Matches Roadmap 5.5 fields exactly.

### 2.2 Architecture Alignment
*   **Layer Constraints**:
    *   `core/config.py`: **Aligned.** Uses only `dataclasses`, `typing`. No I/O.
    *   `io/config.py`: **Aligned.** Handles the file I/O.
    *   `commands/init.py`: **Aligned.** Orchestrates core and io.
*   **Config Resolution**: **Aligned.** Implements the Inversion of Control pattern (CLI injects config).

### 2.3 Strategy Alignment
*   **Q1 (TOML)**: Spec uses `io/toml.py` which (from Phase 2) handles `tomli`/`tomllib` compatibility. **Aligned.**
*   **Q13 (Markdown Primary)**: Config is minimal, keeps logic in Markdown context map where possible. **Aligned.**

### 2.4 io/toml.py Integration
*   **No Duplication**: Spec correctly imports `load_config_if_exists` and `write_config` from `ontos.io.toml` rather than reimplementing them. **Aligned.**

### 2.5 Unauthorized Changes
*   **None identified.** The spec stays strictly within the Phase 3 scope defined in the Roadmap.

---

## 3. Codex — Adversarial Reviewer Report

### 3.1 Attack Vector: Config Parsing
*   **Malformed TOML**: `io/toml.py` (existing) likely raises `toml.TOMLDecodeError`. `io/config.py` needs to catch this and print a user-friendly error ("Config file is invalid: [details]") rather than crashing with a stack trace. **Spec missing error handling here.**
*   **Type Mismatch**: `dict_to_config` assumes types match. If user puts `max_dependency_depth = "five"`, `dataclasses.asdict` won't complain, but runtime usage will fail. **Spec needs explicit type validation or error handling in `dict_to_config`.**

### 3.2 Attack Vector: Init Command
*   **Permissions**: If `.git/hooks` is root-owned (e.g. Docker mount), `path.write_text` will crash. **Spec needs try/except PermissionError.**
*   **Windows Paths**: `#!/usr/bin/env python3` in the shim hook works on Git Bash for Windows, but standard Windows Command Prompt might ignore the shebang. The spec's Python shim uses `subprocess.call([sys.executable...])` which is good, but the *hook file itself* needs to be executable. On Windows, git hooks are often ignored if not named correctly or executed via a wrapper. *Mitigation:* The Python shim approach is the standard best practice for cross-platform hooks (pre-commit uses this). It's likely fine, but "Best Effort" applies.

### 3.3 Attack Vector: Hook Collision
*   **False Positive**: User has a hook that runs a linter: `# Check if ontos is compatible`. The logic `if "ontos" in content and "shim" in content` might trigger. *Mitigation:* The check is specific enough (`ontos` AND `shim`). Probability is low.
*   **False Negative**: User modifies the shim and removes the word "shim". Init will refuse to update it. *Result:* User gets a warning and has to use `--force`. Acceptable.

### 3.4 Attack Vector: Security
*   **Config Injection**: The spec defines `docs_dir` as a string. If user sets `docs_dir = "../../../"`, `io/files.py` (from Phase 2) needs to ensure it doesn't traverse outside repo root. **Spec for Phase 3 doesn't explicitly sanitize these paths.**

---

## 4. Final Verdict

**Verdict:** **APPROVE WITH MINOR CHANGES**

### Top Recommendations:
1.  **Add Error Handling to `io/config.py`**: Catch `TOMLDecodeError` and return a clean error message.
2.  **Add Type Validation**: Ensure `dict_to_config` validates types (e.g., `int` for depth) to prevent runtime crashes later.
3.  **Sanitize Paths**: Ensure `paths.docs_dir` and others in config cannot traverse outside the project root.

### Summary
The spec is robust, well-aligned with the Roadmap, and architecturally sound. The separation of concerns (Core vs IO) is respected. The init command UX is thoughtful regarding legacy projects and hook safety. Addressing the minor adversarial findings (error handling, validation) will make it production-ready.
