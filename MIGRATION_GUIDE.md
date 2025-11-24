# Auto-Tagging Migration Guide

This guide explains how to use the `scripts/migrate_frontmatter.py` script to automatically add YAML frontmatter to your documentation using an LLM.

## Why Migrate?
Autonomous Agents (like Claude Code or Cursor) need structured metadata to navigate your codebase. This script adds that structure to your existing docs.

## Overview

The script works in two steps:
1.  **Export**: Scans your `docs/` folder for untagged files and generates a prompt.
2.  **Import**: Takes the JSON response from the LLM and updates your files.

## Step 1: Generate the Prompt

Run the script to scan your documentation:

```bash
python3 scripts/migrate_frontmatter.py
# Or specify a custom directory:
python3 scripts/migrate_frontmatter.py --dir ./my-docs
```

**Output:**
- It will find all markdown files missing the `---` frontmatter.
- It generates a file named `migration_prompt.txt`.

## Step 2: Ask the LLM

1.  Open `migration_prompt.txt` and copy the entire content.
2.  Paste it into a smart LLM (Claude 3.5 Sonnet or GPT-4o are recommended).
3.  **Important:** The LLM should reply with a raw JSON block.

## Step 3: Save the Response

1.  Copy the JSON response from the LLM.
2.  Create a new file named `migration_response.json` in the root of your project.
3.  Paste the JSON into this file.

**Example `migration_response.json`:**
```json
{
  "docs/architecture/auth.md": {
    "id": "auth_architecture",
    "type": "atom",
    "status": "active",
    "depends_on": ["system_overview"]
  },
  "docs/roadmap.md": {
    "id": "product_roadmap",
    "type": "strategy",
    "status": "active",
    "depends_on": []
  }
}
```

## Step 4: Apply Changes

Run the script with the `--apply` flag:

```bash
python3 scripts/migrate_frontmatter.py --apply
```

**Result:**
- The script reads `migration_response.json`.
- It prepends the correct YAML frontmatter to each file.
- Your docs are now ready for Ontos!

## Troubleshooting

-   **Invalid JSON**: If the script complains about invalid JSON, check `migration_response.json`. Ensure the LLM didn't wrap it in markdown code blocks (```json ... ```). If it did, remove the backticks.
-   **File Not Found**: Ensure the file paths in the JSON match your actual directory structure.
