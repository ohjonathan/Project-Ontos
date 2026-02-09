# ontos/commands/claude_template.py
"""Shared CLAUDE.md template for export commands."""

CLAUDE_MD_TEMPLATE = '''# CLAUDE.md

## Ontos Activation

This project uses **Ontos** for documentation management.

At the start of every session:
1. Run `ontos map` to generate the context map
2. Read `Ontos_Context_Map.md` to understand the project documentation structure

When ending a session:
3. Run `ontos log` to record your work

## What is Ontos?

Ontos is a local-first documentation management system that:
- Maintains a context map of all project documentation
- Tracks documentation dependencies and status
- Ensures documentation stays synchronized with code changes
'''
