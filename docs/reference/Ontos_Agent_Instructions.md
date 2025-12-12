# Ontos Agent Instructions

You are an intelligent agent operating within the **Ontos Protocol**. Your goal is to maintain context integrity and avoid hallucinations by strictly following the Context Map.

## The Protocol

### 0. Auto-Activation (v2.2+)
At the start of EVERY conversation, silently check for Ontos:
1.  Look for `Ontos_Context_Map.md` in the project root
2.  If found AND user hasn't disabled auto-activation:
    *   Read the context map
    *   Load relevant context based on user's first message
    *   Do NOT announce "Loaded: [...]" unless explicitly asked
3.  If not found:
    *   Proceed normally (no Ontos in this project)

This makes Ontos invisible when present, reducing friction.

> **User can disable auto-activation:** "Don't auto-load Ontos context" or "Start fresh"

### 1. Context Discovery (Start of Task)
When the user says **"Ontos"** (or "Activate Ontos"), you MUST:
1.  First, check if `Ontos_Context_Map.md` exists.
2.  If not, run: `python3 .ontos/scripts/ontos_generate_context_map.py`.
3.  Read `Ontos_Context_Map.md` completely.
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
2.  Run `python3 .ontos/scripts/ontos_generate_context_map.py` to update the map.
3.  Check the output for errors (Cycles, Orphans, Architectural Violations).
    *   **Violation**: A **Kernel** (0) cannot depend on an **Atom** (3). Dependencies must flow DOWN the stack.

### 3. Session Archival
When the user says **"Ontos archive"** (or "Archive our session"):
1.  **Final Polish**: Run `python3 .ontos/scripts/ontos_generate_context_map.py` one last time to ensure the graph is clean and up-to-date. Fix any issues found.
2.  Run `python3 .ontos/scripts/ontos_end_session.py "slug-for-session" --source "Your LLM Name" --changelog` to create a session log AND prompt for changelog entries. Replace "Your LLM Name" with your actual name (e.g., "Claude Code", "Gemini", "Cursor").
3.  **READ** the generated log file.
4.  **OVERWRITE** the placeholders in the file with a high-quality summary of the session (Goal, Decisions, Changes, Next Steps).
5.  Commit the changes.

### Changelog Guidelines

**Two types of changelogs exist:**

| File | Purpose | When to Update |
|------|---------|----------------|
| `Ontos_CHANGELOG.md` | Changes to Project Ontos tooling itself | Only when modifying Ontos scripts, protocol, or docs |
| `CHANGELOG.md` | Changes to the project using Ontos | During normal development sessions |

**Important**: When working on a project that *uses* Ontos as its documentation system, update that project's `CHANGELOG.md` via the `--changelog` flag in `ontos_end_session.py`. **Never** update `Ontos_CHANGELOG.md` unless you are directly modifying Project Ontos itself.

### 4. Maintenance (Weekly Ritual)
When the user says **"Maintain Ontos"** (or "Ontos maintenance"):
1.  **Frontmatter Check**: Run `python3 .ontos/scripts/ontos_migrate_frontmatter.py` to tag any new files.
2.  **Graph Integrity**: Run `python3 .ontos/scripts/ontos_generate_context_map.py`.
3.  **Fix Issues**: If the script reports errors (Broken Links, Cycles, Orphans), fix them immediately.
4.  **Commit**: Commit the updated `Ontos_Context_Map.md` and any fixed files.

For detailed error remediation guidance, see the [Maintenance Guide](../guides/Ontos_Maintenance_Guide.md).

### 5. Updating Ontos
When the user says **"Update Ontos"**:
1.  Run `python3 .ontos/scripts/ontos_update.py --check` to see if updates are available.
2.  Run `python3 .ontos/scripts/ontos_update.py` to apply the update.
3.  Backups are saved to `.ontos/backups/` automatically.
4.  The user's `ontos_config.py` is never overwritten.

### 6. Version Bumping (Project Ontos Development Only)
**IMPORTANT**: When working on Project Ontos itself (not projects that *use* Ontos), you MUST ask the user about version bumps before pushing to git.

**When to ask**: Before any `git push` that includes changes to files in `.ontos/scripts/`, `.ontos/` config files, or Ontos documentation.

**How to ask**: "Should I bump the Ontos version before pushing? Current version is X.Y.Z. Options:
- **Patch (X.Y.Z+1)**: Bug fixes only
- **Minor (X.Y+1.0)**: New features, backward compatible
- **No change**: Skip version bump"

**Where to update**: `.ontos/scripts/ontos_config_defaults.py` → `ONTOS_VERSION`

**Note**: This only applies when developing Ontos itself. Projects *using* Ontos should manage their own versioning separately.
