# Phase 1 Implementation Spec: Chief Architect Response

**Date:** 2026-01-12
**Author:** Chief Architect (Claude Opus 4.5)
**Spec Version:** 1.0 → 1.1
**Review Consolidation Date:** 2026-01-12

---

## 1. Overall Assessment

### 1.1 Reaction to Review

The reviewers found a fundamental flaw that I missed: **the CLI delegation model is broken for distribution**. I designed a package that depends on files not included in the package itself. This is embarrassing but important to catch.

All three reviewers independently identified the same core issue — the `cli.py` subprocess delegation to repo-local `ontos.py` creates a package that only works in editable install mode within the source repository. This directly contradicts the v3.0 theme of "Distribution & Polish."

I was focused on preserving backward compatibility and minimizing code changes, and missed that the package structure itself is incompatible with `pip install ontos` from PyPI.

### 1.2 Verdict Acceptance

**Do you agree with the "Major Revisions Required" verdict?**

[x] Yes — The reviewers are correct. Major changes needed.

**Reasoning:** The CLI cannot work as designed for any installation mode other than editable install in the source repo. This isn't a minor issue — it's a fundamental architecture flaw that makes the package non-functional for its intended purpose.

### 1.3 Key Insight

The most important thing I learned: **Package structure and distribution structure are different problems.** I designed for how files look in the repository, not how they look in `site-packages`. The reviewers correctly identified that `pyproject.toml` with `include = ["ontos"]` explicitly excludes the legacy scripts that the CLI depends on.

---

## 2. Critical Issues Response

### C1: CLI Depends on Unpackaged Files

**Flagged by:** All three reviewers
**Location:** `ontos/cli.py`
**Issue:** CLI uses subprocess to call `ontos.py` which isn't packaged. Fresh `pip install ontos` will crash.

**Decision:** [x] Accept

**Analysis:**

This is the core issue. The current design has cli.py doing:
```python
unified_cli = scripts_dir.parent.parent / "ontos.py"
result = subprocess.run([sys.executable, str(unified_cli)] + sys.argv[1:])
```

This path resolution assumes the package is installed in a repo with `ontos.py` at the root. For a PyPI install to `site-packages/ontos/`, there is no `../ontos.py`.

**Options Considered:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A | Bundle all scripts in package | True global CLI, clean | Large scope increase |
| B | Editable install only | Minimal changes | Violates distribution goal |
| C | Hybrid delegation | Works both ways | Complex, two code paths |
| D | Bundle scripts, delegate to bundled | Works globally, minimal code changes | Small scope increase |

**Selected Solution:** Option D — Bundle legacy scripts inside package, CLI delegates to bundled copy

This approach:
1. Moves `.ontos/scripts/` to `ontos/_scripts/` (inside package)
2. CLI looks for scripts in package first
3. Maintains "no code changes" — scripts unchanged, just relocated
4. Both editable and non-editable installs work

**Changes to Spec:**

- Section 3.1: Update directory layout to show `ontos/_scripts/`
- Section 4.4: Rewrite `cli.py` to use `importlib.resources` or `__file__` relative paths within package
- Section 4.1: Update `pyproject.toml` to include `ontos._scripts` subpackage
- Section 5.1: Add task to copy `.ontos/scripts/` to `ontos/_scripts/`

---

### C2: Public API Mismatch

**Flagged by:** Claude (Peer)
**Location:** Section 4.2 `__init__.py`
**Issue:** Proposed exports differ from v2.8, breaking backward compatibility.

**Decision:** [x] Accept

**Analysis:**

I verified the current v2.8 exports. The proposed spec removes many symbols and adds `normalize_frontmatter` which doesn't exist. This would break any code doing `from ontos import normalize_depends_on`.

**Current v2.8 Exports (verified):**
```python
# From context
SessionContext, FileOperation, PendingWrite
# From frontmatter
parse_frontmatter, normalize_depends_on, normalize_type
# From staleness (many!)
ModifiedSource, normalize_describes, parse_describes_verified,
validate_describes_field, detect_describes_cycles, check_staleness,
get_file_modification_date, clear_git_cache, DescribesValidationError,
DescribesWarning, StalenessInfo
# From history
ParsedLog, parse_log_for_history, sort_logs_deterministically,
generate_decision_history, get_log_date
# From paths
resolve_config, get_logs_dir, get_log_count, get_logs_older_than,
get_archive_dir, get_decision_history_path, get_proposals_dir,
get_archive_logs_dir, get_archive_proposals_dir, get_concepts_path,
find_last_session_date
# From config
BLOCKED_BRANCH_NAMES, get_source, get_git_last_modified
# From proposals
load_decision_history_entries, find_draft_proposals
# From ui
OutputHandler
```

**Proposed v1.0 Spec Exports (wrong):**
Many removed, `normalize_frontmatter` added (doesn't exist!)

**Resolution:**

Copy the existing `.ontos/scripts/ontos/__init__.py` exactly, only changing `__version__` to "3.0.0a1". Do NOT curate exports in Phase 1.

**Changes to Spec:**

- Section 4.2: Replace with actual current `__init__.py` content
- Only change: `__version__ = "3.0.0a1"`

---

### C3: `ontos_init.py` Not Packaged

**Flagged by:** Gemini (Alignment)
**Location:** Root level
**Issue:** `ontos init` calls `ontos_init.py` which isn't in the package.

**Decision:** [x] Accept

**Analysis:**

This is a consequence of C1. The init command currently runs `ontos_init.py` from the repo root, which won't exist in a global install.

**Resolution:**

Part of the bundling solution in C1. `ontos_init.py` will be included in `ontos/_scripts/` along with all other scripts.

**Changes to Spec:**

Covered by C1 resolution — bundle all scripts including `ontos_init.py`.

---

### Critical Issues Summary

| Issue | Decision | Resolution |
|-------|----------|------------|
| C1: CLI depends on unpackaged files | Accept | Bundle scripts in `ontos/_scripts/`, CLI delegates to bundled |
| C2: Public API mismatch | Accept | Copy exact current `__init__.py`, only change version |
| C3: `ontos_init.py` not packaged | Accept | Included in bundled scripts |

---

## 3. Major Issues Response

### M1: Subprocess Delegation Loses TTY/Signals

**Flagged by:** Claude, Gemini
**Decision:** [x] Modify

**Analysis:** Valid concern. subprocess.run() can lose TTY detection and signal handling.

**Resolution:** Keep subprocess delegation for Phase 1 (simpler), but add note that Phase 4 will implement direct function calls. Add `subprocess.run(..., stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)` to preserve streams.

**Changes to Spec:** Update cli.py to pass through stdin/stdout/stderr explicitly.

---

### M2: Missing Architecture Stubs

**Flagged by:** Codex
**Decision:** [x] Modify

**Analysis:** Architecture shows `commands/`, `io/`, `mcp/` but spec omits them. However, these are Phase 2+ concerns.

**Resolution:** Add empty `__init__.py` placeholder files for `ontos/commands/`, `ontos/io/`, `ontos/mcp/` to match architecture. No code, just structure alignment.

**Changes to Spec:** Add Task 1.6 to create placeholder directories.

---

### M3: Hardcoded Relative Paths Break in site-packages

**Flagged by:** Gemini
**Decision:** [x] Accept

**Analysis:** `Path(__file__).parent.parent / ".ontos"` assumes repo layout.

**Resolution:** Covered by C1 — use package-relative paths to bundled scripts.

**Changes to Spec:** Covered by cli.py rewrite in C1.

---

### M4: Version Source Duplication

**Flagged by:** Claude
**Decision:** [x] Accept

**Analysis:** After Phase 1 there will be two version sources: package `__version__` and `ontos_config.__version__`.

**Resolution:** In Phase 1, keep both but document that `ontos_config.__version__` is deprecated. Add task to update `ontos.py` to read from package version.

**Changes to Spec:** Add Section 9.5 on version consolidation.

---

### M5: "Move" vs "Copy" Ambiguity

**Flagged by:** Claude, Codex
**Decision:** [x] Accept

**Analysis:** Spec says "move" but should specify what happens to old location.

**Resolution:** Clarify: COPY files to new location, KEEP old location for backward compatibility during transition. Add deprecation warning to old `__init__.py`.

**Changes to Spec:** Clarify in Section 5.1 that this is a copy, not move. Add task for deprecation warning in old location.

---

### M6: No Repo Root Discovery

**Flagged by:** Codex, Gemini
**Decision:** [x] Accept

**Analysis:** CLI can't find project root from subdirectories.

**Resolution:** Add repo root discovery function that walks up looking for `.ontos/` or `.ontos-internal/`. If not found, show helpful error.

**Changes to Spec:** Add `find_project_root()` function to cli.py.

---

### Major Issues Summary

| Issue | Decision | Resolution |
|-------|----------|------------|
| M1: Subprocess loses TTY | Modify | Pass through streams explicitly |
| M2: Missing architecture stubs | Modify | Add empty placeholder directories |
| M3: Hardcoded paths | Accept | Covered by C1 |
| M4: Version duplication | Accept | Document deprecation, update ontos.py |
| M5: Move vs copy ambiguity | Accept | Clarify as copy, keep old with warning |
| M6: No repo root discovery | Accept | Add find_project_root() function |

---

## 4. Minor Issues Response

| # | Issue | Flagged By | Decision | Action |
|---|-------|------------|----------|--------|
| m1 | Roadmap version v1.3 vs v1.2 | Codex | Ignore | Roadmap IS v1.3 (updated after Phase 0) |
| m2 | CI file name wrong (tests.yml vs ci.yml) | Codex | Accept | Change to `ci.yml` |
| m3 | `tomllib` verification fails on 3.9 | Codex | Accept | Use `tomli` with fallback |
| m4 | Script count wrong (28 vs 23) | Claude | Accept | Change to 23 |
| m5 | Missing YAML frontmatter | Claude | Accept | Add frontmatter to spec |
| m6 | "303 tests pass" scope creep | Codex | Ignore | Tests must pass for Phase 1 |
| m7 | CLI help text simplification | Claude | Ignore | Keep help text, useful |

---

## 5. Fundamental Architecture Decision

### The Core Question

The reviewers identified that the Phase 1 spec assumes a "delegation model" where the global CLI calls into repository-local scripts. This model is broken for `pip install ontos` from PyPI.

**The question:** How should Ontos be structured for Phase 1?

### Selected Option: D — Bundle Scripts, Delegate to Bundled

```
ontos/                    # Package (what pip installs)
├── __init__.py          # Version, public API (unchanged from v2.8)
├── __main__.py          # python -m ontos support
├── cli.py               # CLI entry point (delegates to _scripts/)
├── core/                # Core modules (copied from .ontos/scripts/ontos/core/)
├── ui/                  # UI modules (copied from .ontos/scripts/ontos/ui/)
├── commands/            # Placeholder for Phase 2
├── io/                  # Placeholder for Phase 2
├── mcp/                 # Placeholder for Phase 2
└── _scripts/            # Bundled legacy scripts
    ├── __init__.py      # Makes it importable
    ├── ontos.py         # Unified dispatcher (COPY of root ontos.py)
    ├── ontos_init.py    # Init logic (COPY of root ontos_init.py)
    ├── ontos_generate_context_map.py
    └── ... (all 23 scripts)

.ontos/scripts/          # RETAINED for backward compat, with deprecation warning
└── ontos/               # Old package location
    └── __init__.py      # Deprecation warning on import
```

**Why This Option:**

1. **Works globally** — `pip install ontos` from PyPI will have all scripts
2. **Minimal code changes** — Scripts are copied, not rewritten
3. **Backward compatible** — Old `.ontos/scripts/` still works with warning
4. **Scope contained** — This is file movement, not refactoring
5. **Phase 2 ready** — Structure matches target architecture

**Implications for Spec:**

- Section 3.1: New directory layout with `_scripts/`
- Section 4: Add specifications for bundled scripts
- Section 5: Update migration tasks
- Section 6: Update CI to test both install modes

**Implications for Roadmap:**

- Phase 1 scope slightly increased (bundling scripts)
- Phase 2 unchanged (still extracts god scripts)
- Phase 4 unchanged (still implements full CLI)

---

## 6. Changelog for v1.1

### 6.1 Critical Fixes

| Change | Issue | Section(s) Modified |
|--------|-------|---------------------|
| Bundle scripts in `ontos/_scripts/` | C1 | 3.1, 4.4, 4.7 (new), 5.1 |
| Preserve exact v2.8 `__init__.py` exports | C2 | 4.2 |
| Include `ontos_init.py` in bundle | C3 | 4.7 |

### 6.2 Major Changes

| Change | Issue | Section(s) Modified |
|--------|-------|---------------------|
| Pass streams through subprocess | M1 | 4.4 |
| Add placeholder directories | M2 | 3.1, 5.1 |
| Add `find_project_root()` | M6 | 4.4 |
| Document version deprecation | M4 | 9.5 (new) |
| Clarify copy vs move | M5 | 5.1 |

### 6.3 Minor Updates

| Change | Issue | Section(s) Modified |
|--------|-------|---------------------|
| CI file name: tests.yml → ci.yml | m2 | 6.1 |
| Verification: tomllib → tomli fallback | m3 | 5.1, 7.1 |
| Script count: 28 → 23 | m4 | 2.2 |
| Add YAML frontmatter | m5 | Header |

### 6.4 No Action Taken

| Issue | Reason |
|-------|--------|
| m1: Roadmap version mismatch | Roadmap is v1.3, Codex had outdated info |
| m6: "303 tests pass" scope creep | Tests must pass; this is required |
| m7: CLI help text | Useful, keep as-is |

---

## 7. Lessons Learned

### 7.1 What I Missed

1. **Distribution vs Repository structure** — I focused on how files look in the editor, not in site-packages
2. **Package boundary** — `pyproject.toml` `include` setting defines what ships; I didn't trace through what CLI needs
3. **API stability** — I "curated" exports instead of preserving them exactly

### 7.2 What the Process Caught

The multi-reviewer process caught complementary issues:
- **Gemini (Alignment)** caught the fundamental distribution model flaw
- **Codex (Adversarial)** found edge cases and version mismatches
- **Claude (Peer)** caught the API breakage and implementation details

No single reviewer would have caught everything.

### 7.3 Process Improvement

For future specs:
1. **Trace dependencies** — For any package spec, trace what the entry point needs and verify it's included
2. **Test both install modes** — `pip install -e .` AND `pip install .` in a clean venv
3. **Compare APIs explicitly** — Side-by-side diff of before/after exports

---

## 8. Updated Spec Declaration

### 8.1 Spec Status

| Field | Value |
|-------|-------|
| Version | 1.1 |
| Status | Ready for Verification Review |
| Changes | 3 critical fixes, 6 major changes, 4 minor updates |
| Confidence | Medium (architecture decision needs validation) |

### 8.2 Re-Review Scope

The following sections have substantial changes and need verification:

- [ ] Section 3.1: New directory layout with `_scripts/`
- [ ] Section 4.4: Rewritten `cli.py` with bundled delegation
- [ ] Section 4.7: New section for bundled scripts
- [ ] Section 5.1: Updated migration tasks

### 8.3 Sections Unchanged

- Section 1: Overview (minor scope note added)
- Section 7: Verification (commands updated)
- Section 8: Risks (unchanged)
- Section 10: Post-Phase 1 (unchanged)

### 8.4 Verification Focus

For the verification review, focus on:

1. **Does cli.py correctly locate bundled scripts?**
2. **Is the public API exactly preserved?**
3. **Do both install modes work?** (`pip install -e .` and `pip install .`)

---

*End of Chief Architect Response*

**Reviewed by:** Claude Opus 4.5 (claude-opus-4-5-20251101)
**Response Date:** 2026-01-12
