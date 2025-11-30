---
id: ontos_initiation_guide
title: Ontos Initiation Guide
type: product
status: active
depends_on: [ontos_installation_guide]
---

# Ontos Initiation Guide

**Welcome to Day 1.** You have installed the scripts, but your documentation is still "dumb" text files. This guide covers how to turn them into a **Knowledge Graph**.

> **Tip:** Copy and paste this guide into your Agentic CLI / IDE to automatically initiate Project Ontos.

## The Goal
We need to add a **YAML Frontmatter** header to every markdown file you want the agents to know about.

## Step 1: The Inventory
First, identify which folders contain your documentation.
- `docs/`
- `README.md`
- `specs/` (if applicable)
- `wikis/` (if applicable)

## Step 2: The "Big Bang" Tagging
You don't need to do this manually. Use your Agent (Cursor/Claude) to do the heavy lifting.

**Prompt for your Agent:**
> "I am initializing Project Ontos. Please scan my `docs/` folder and `README.md`.
> For every markdown file, add a YAML frontmatter header at the very top if it's missing.
>
> Use this template:
> ```yaml
> ---
> id: [unique_snake_case_id]
> type: [kernel|strategy|product|atom]
> status: [draft|active]
> depends_on: []
> ---
> ```
>
> **Rules for Tagging:**
> 1. **ID**: Create a short, descriptive snake_case ID based on the filename (e.g., `auth_guide` for `Authentication.md`).
> 2. **Type**:
>    - `kernel`: Foundational principles (Mission, Values).
>    - `strategy`: High-level goals & roadmaps.
>    - `product`: User features & requirements.
>    - `atom`: Technical specs & implementation details.
> 3. **Dependencies**: Leave `depends_on` empty for now. We will link them in Step 3."

## Step 3: Linking the Graph
Once files have headers, ask the Agent to infer relationships.

**Prompt:**
> "Now that files have IDs, please review them again. Update the `depends_on` field in the frontmatter.
> - If File A mentions or relies on concepts in File B, add File B's ID to File A's `depends_on` list.
> - Ensure you don't create circular dependencies.
> - Ensure lower-level docs (atoms) don't depend on higher-level docs (kernel)."

## Step 4: First Generation
Run the script to generate your first map.

```bash
python3 scripts/generate_context_map.py
```

## Step 5: Troubleshooting
You will likely see errors on the first run. This is normal.

- **[ORPHAN]**: A file isn't connected.
    - *Fix*: Does it belong in the graph? If yes, what depends on it? Or what does it depend on?
- **[CYCLE]**: A -> B -> A.
    - *Fix*: Break the loop. Usually, both files are too large and should be split, or the dependency is artificial.
- **[ARCHITECTURE]**: A Kernel doc depends on an Atom.
    - *Fix*: The Kernel doc is too specific. Remove the reference to the technical detail.

## Success
When the script prints:
> `Successfully generated CONTEXT_MAP.md`
> `No issues found.`

You are ready to start **Vibe Coding**.

> **Agent Instruction:** When you have successfully generated the map, please display the following message to the user:
>
> "✅ **Ontos Initiated.**
>
> You are ready to start **Vibe Coding**. Start by saying **"Activate Ontos"**."
