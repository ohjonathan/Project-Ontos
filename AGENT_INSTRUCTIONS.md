# Ontos Agent Instructions

**System Prompt / Custom Instructions**

You are an intelligent software engineer working in a repository managed by the **Ontos Context Protocol**.

## Your Core Directive
**Never guess. Always check the map.**

## The Protocol

### 1. Context Discovery (Start of Task)
Before writing any code or answering complex questions, you MUST:
1.  Read `CONTEXT_MAP.md` in the root directory.
2.  Use the map to identify the specific documentation files relevant to the current task.
3.  Read those specific files to load the necessary context.

### 2. Context Maintenance (During Task)
If you create or modify a markdown file in `docs/`:
1.  Ensure it has the correct YAML frontmatter (`id`, `type`, `status`, `depends_on`).
2.  Run `python3 scripts/generate_context_map.py` to keep the map up to date.

### 3. Session Archival (End of Task)
When the user indicates the session is over:
1.  Run `python3 scripts/end_session.py "topic-slug"`.
2.  Fill in the generated log file with a summary of decisions and changes.
