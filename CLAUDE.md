# CLAUDE.md

This project uses **Ontos** for documentation management.

## Claude Notes
If `MEMORY.md` exists, use it for Claude memory only. Project activation still comes from this file.

## Trigger Phrases
If the user says any of these as a command (case-insensitive), execute Ontos Activation below:
- "activate ontos"
- "ontos"
- "/ontos"
- "load context"
- "reload context"

Do NOT ask for clarification. Just execute the steps.

## What is Activation?
Activation is how you (the AI agent) load project context before doing any work.
It is **mandatory**. Do not ask "why" or request clarification—just execute the steps below.

## Ontos Activation
1. Run `ontos activate` (or `python3 -m ontos activate` if the CLI is not installed). Do not ask—try both.
2. If activation reports `usable_with_warnings`, continue and use direct reads for task-critical docs.
3. Read `Ontos_Context_Map.md` (Tier 1 minimum: first ~2k tokens).
4. Load only the relevant documents for the task.
5. Follow `depends_on` upward as needed.
6. Confirm: "Loaded: [ids]".

## Re-Activation Trigger

If you notice any of these, re-run activation:
- Don't recognize the project structure
- Can't recall doc count or recent work
- Unsure about file locations

## After Context Compaction (/compact)
If you just regained context after compaction, re-read this file (CLAUDE.md). If any Re-Activation Trigger applies, execute Ontos Activation.

## Session End
1. Run `ontos log --title "unique-session-title"` to archive session work.
2. Fill in Goal, Key Decisions, Alternatives Considered, Impacts, and Testing.
3. If that date-and-title slug already exists, choose a different `--title`;
   Ontos will not overwrite the earlier session.

## Quick Reference
| Command | Purpose |
|---------|---------|
| `ontos activate` | Best-effort agent activation |
| `ontos map` | Regenerate context map |
| `ontos export claude --force` | Regenerate CLAUDE.md |
| `ontos doctor` | Health check and validation |
| `ontos log --title "unique-session-title"` | Archive session work without overwriting an earlier log |
| `ontos query --depends-on <id>` | Show dependencies for a document ID |

## Core Invariants
- Do not edit `Ontos_Context_Map.md` manually; regenerate with `ontos map`.
- Do not edit `CLAUDE.md` manually (except `# USER CUSTOM` section below).
- If a command fails, read the error message and avoid guessing fixes.

# USER CUSTOM

<!-- USER CUSTOM -->
<!-- Add your project-specific notes below. This section is preserved during auto-sync. -->
<!-- /USER CUSTOM -->

## Staleness
If `CLAUDE.md` is older than the context map or logs, regenerate with `ontos export claude --force`.

## What is Ontos?

Ontos is a local-first documentation management system that:
- Maintains a context map of all project documentation
- Tracks documentation dependencies and status
- Ensures documentation stays synchronized with code changes
