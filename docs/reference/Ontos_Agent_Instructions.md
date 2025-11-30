# Ontos Agent Instructions

You are an intelligent agent operating within the **Ontos Protocol**. Your goal is to maintain context integrity and avoid hallucinations by strictly following the Context Map.

## The Protocol

### 1. Context Discovery (Start of Task)
When the user says **"Ontos"** (or "Activate Ontos"), you MUST:
1.  First, check if `CONTEXT_MAP.md` exists.
2.  If not, run: `python3 scripts/generate_context_map.py`.
3.  Read `CONTEXT_MAP.md` completely.
4.  Based on the user's next request, identify relevant doc IDs from the map.
5.  Read ONLY those specific files from their paths.
6.  Confirm what context you've loaded with: "Loaded: [list of doc IDs]".

## Document Type Reference

| Type | Rank | Use For |
|------|------|---------|
| kernel | 0 | Foundational principles (mission, values) |
| strategy | 1 | Business decisions (goals, roadmap) |
| product | 2 | User-facing specs (features, journeys) |
| atom | 3 | Technical details (API, schemas) |

**Dependency Rule:** Higher ranks depend on lower ranks. `atom` → `product` → `strategy` → `kernel`.

For full definitions, see [The Manual](Ontos_Manual.md).

### 2. Context Maintenance (During Task)
If you create a new file or change dependencies:
1.  Update the YAML frontmatter in the file.
2.  Run `python3 scripts/generate_context_map.py` to update the map.
3.  Check the output for errors (Cycles, Orphans, Architectural Violations).
    *   **Violation**: A **Kernel** (0) cannot depend on an **Atom** (3). Dependencies must flow DOWN the stack.

### 3. Session Archival
When the user says **"Ontos archive"** (or "Archive our session"):
1.  **Final Polish**: Run `python3 scripts/generate_context_map.py` one last time to ensure the graph is clean and up-to-date. Fix any issues found.
2.  Run `python3 scripts/end_session.py "slug-for-session" --changelog` to create a session log AND prompt for changelog entries.
3.  **READ** the generated log file.
4.  **OVERWRITE** the placeholders in the file with a high-quality summary of the session (Goal, Decisions, Changes, Next Steps).
5.  Commit the changes.

### Changelog Guidelines

**Two types of changelogs exist:**

| File | Purpose | When to Update |
|------|---------|----------------|
| `POCHANGELOG.md` | Changes to Project Ontos tooling itself | Only when modifying Ontos scripts, protocol, or docs |
| `CHANGELOG.md` | Changes to the project using Ontos | During normal development sessions |

**Important**: When working on a project that *uses* Ontos as its documentation system, update that project's `CHANGELOG.md` via the `--changelog` flag in `end_session.py`. **Never** update `POCHANGELOG.md` unless you are directly modifying Project Ontos itself.

### 4. Maintenance (Weekly Ritual)
When the user says **"Maintain Ontos"** (or "Ontos maintenance"):
1.  **Frontmatter Check**: Run `python3 scripts/migrate_frontmatter.py` to tag any new files.
2.  **Graph Integrity**: Run `python3 scripts/generate_context_map.py`.
3.  **Fix Issues**: If the script reports errors (Broken Links, Cycles, Orphans), fix them immediately.
4.  **Commit**: Commit the updated `CONTEXT_MAP.md` and any fixed files.
