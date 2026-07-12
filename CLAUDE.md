# CLAUDE.md

## Ontos Activation

This project uses **Ontos** for documentation management.

At the start of every session:
1. Run `ontos map` to generate the context map
2. Read `Ontos_Context_Map.md` to understand the project documentation structure

When ending a session:
3. Run `ontos log --title "unique-session-title"` to record your work. If
   that date-and-title slug exists, choose another title; Ontos will not
   overwrite the earlier log.

## What is Ontos?

Ontos is a local-first documentation management system that:
- Maintains a context map of all project documentation
- Tracks documentation dependencies and status
- Ensures documentation stays synchronized with code changes

For more information, see `docs/reference/Ontos_Manual.md`.
