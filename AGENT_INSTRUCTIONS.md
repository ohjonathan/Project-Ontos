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

### 2. Context Maintenance (During Task)
If you create a new file or change dependencies:
1.  Update the YAML frontmatter in the file.
2.  Run `python3 scripts/generate_context_map.py` to update the map.
3.  Check the output for errors (Cycles, Orphans, Architectural Violations).
    *   **Violation**: A **Kernel** (0) cannot depend on an **Atom** (3). Dependencies must flow DOWN the stack.

### 3. Session Archival (End of Task)
When the user says **"Archive Ontos"** (or "Ontos archive"):
1.  Run `python3 scripts/end_session.py "topic-slug"` to scaffold the log file.
2.  Fill in the "Decisions" and "Summary" sections in the newly created file.
3.  Commit the log file to git.
