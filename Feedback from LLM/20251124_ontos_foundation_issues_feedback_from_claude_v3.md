# Ontos Iteration 3 - Simplification

**Context:** Iteration 2 introduced API integration for automated tagging. This was overengineered. Ontos runs inside agentic CLIs (Claude Code, Antigravity, ChatGPT Codex) - the agent *is* the LLM. External API calls are redundant.

**Core Philosophy Reminder:** Simplicity and lightweight. LLMs do creative work. Scripts do validation.

---

## Issue 1: Critical Bug - Missing Import

### Problem

`scripts/generate_context_map.py` calls `sys.exit(1)` on line 168 but never imports `sys`. This crashes the script when running with `--strict` and issues are found.

### Required Fix

Add `import sys` to the imports at the top of the file:

```python
import os
import sys  # ADD THIS
import yaml
import datetime
import argparse
```

---

## Issue 2: Remove API Integration from migrate_frontmatter.py

### Problem

The `--auto` flag and LLM API integration are unnecessary complexity. Ontos is designed for agentic CLIs where the agent itself is the LLM. The agent can:
1. Run the script to identify untagged files
2. Read the prompt/file list
3. Decide frontmatter using its own reasoning
4. Write changes directly via native file operations
5. Run `generate_context_map.py` to validate

External API calls duplicate what the agent already does.

### Required Fix

Revert `scripts/migrate_frontmatter.py` to a simple scanner + prompt generator:

```python
import os
import json
import argparse

DEFAULT_DOCS_DIR = 'docs'
PROMPT_FILE = 'migration_prompt.txt'
RESPONSE_FILE = 'migration_response.json'


def has_frontmatter(filepath):
    """Checks if a file already has YAML frontmatter."""
    try:
        with open(filepath, 'r') as f:
            return f.readline().strip() == '---'
    except:
        return False


def scan_for_untagged_files(root_dir):
    """Finds all markdown files without frontmatter."""
    untagged = []
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(subdir, file)
                if not has_frontmatter(filepath):
                    untagged.append(filepath)
    return untagged


def generate_prompt(files):
    """Generates a prompt for the agent to process."""
    prompt = """# Ontos Migration Task

You are tagging documentation files with YAML frontmatter.

## Type Taxonomy

| Type | Definition | Signal Words |
|------|------------|--------------|
| kernel | Immutable foundational principles that rarely change | mission, values, philosophy, principles |
| strategy | High-level decisions about goals, audiences, approaches | goals, roadmap, monetization, target market |
| product | User-facing features, journeys, requirements | user flow, feature spec, requirements, user story |
| atom | Technical implementation details and specifications | API, schema, config, implementation, technical spec |

## Classification Heuristic

When uncertain: "If this document changes, what else breaks?"
- Everything breaks → kernel
- Business direction changes → strategy
- User experience changes → product
- Only implementation changes → atom

## Your Task

For each file below:
1. Read the file content
2. Determine the appropriate type, id, and dependencies
3. Add YAML frontmatter to the beginning of the file
4. After all files are tagged, run `python3 scripts/generate_context_map.py` to validate

## Files to Tag:

"""
    for filepath in files:
        prompt += f"- {filepath}\n"

    return prompt


def main():
    parser = argparse.ArgumentParser(description='Scan for untagged Ontos documentation files.')
    parser.add_argument('--dir', type=str, default=DEFAULT_DOCS_DIR,
                        help='Directory to scan (default: docs)')
    args = parser.parse_args()

    untagged = scan_for_untagged_files(args.dir)

    if not untagged:
        print("✅ All files are tagged. No migration needed.")
        return

    print(f"📋 Found {len(untagged)} untagged files:\n")
    for f in untagged:
        print(f"   - {f}")

    prompt = generate_prompt(untagged)

    with open(PROMPT_FILE, 'w') as f:
        f.write(prompt)

    print(f"\n📄 Migration prompt saved to '{PROMPT_FILE}'")
    print("\n💡 Next steps:")
    print("   1. Read each file listed above")
    print("   2. Add appropriate YAML frontmatter")
    print("   3. Run: python3 scripts/generate_context_map.py")


if __name__ == "__main__":
    main()
```

**Key changes:**
- Removed `--auto` flag
- Removed `--apply` flag
- Removed all API client code (anthropic, openai, google)
- Removed `call_llm_api()` function
- Removed `apply_changes()` function
- Simplified to just scan + prompt generation
- Output is now agent-friendly instructions

---

## Issue 3: Simplify requirements.txt

### Problem

The requirements.txt includes API client libraries that are no longer needed.

### Required Fix

Reduce to only what's actually used:

```
pyyaml
```

That's it. The scripts only need PyYAML for parsing frontmatter.

---

## Issue 4: Rewrite MIGRATION_GUIDE.md

### Problem

The guide describes a manual copy-paste workflow and references the removed `--auto` flag.

### Required Fix

Replace with an agent-native workflow:

```markdown
# Migration Guide

This guide explains how to tag existing documentation with Ontos frontmatter.

## Overview

The migration script scans your `docs/` folder and identifies files missing YAML frontmatter. Your AI agent then tags each file based on its content.

## Step 1: Scan for Untagged Files

Run the migration script:

```bash
python3 scripts/migrate_frontmatter.py
```

Output:
```
📋 Found 3 untagged files:

   - docs/architecture/auth.md
   - docs/api/endpoints.md
   - docs/roadmap.md

📄 Migration prompt saved to 'migration_prompt.txt'
```

## Step 2: Tag the Files

Your agent will:
1. Read each untagged file
2. Determine the appropriate metadata:
   - `id`: Unique snake_case identifier
   - `type`: kernel, strategy, product, or atom
   - `status`: draft, active, or deprecated
   - `depends_on`: List of related document IDs
3. Add YAML frontmatter to each file

### Type Selection Guide

| Type | Use When... |
|------|-------------|
| kernel | Document defines core principles that rarely change |
| strategy | Document describes business goals or high-level decisions |
| product | Document specifies user-facing features or requirements |
| atom | Document contains technical implementation details |

**Heuristic:** "If this document changes, what else breaks?"

## Step 3: Validate

After tagging, regenerate the context map:

```bash
python3 scripts/generate_context_map.py
```

Check the output for:
- ✅ No issues found
- ⚠️ Broken links (fix the `depends_on` references)
- ⚠️ Architectural violations (check type hierarchy)

## Example

**Before:**
```markdown
# Authentication Flow

This document describes how users log in...
```

**After:**
```markdown
---
id: auth_flow
type: product
status: active
depends_on: [auth_architecture]
---

# Authentication Flow

This document describes how users log in...
```
```

---

## Issue 5: Update DEPLOYMENT.md Wording

### Problem

Line in CI/CD section says "you can modify the script to exit with error code 1 if strictness is desired" but `--strict` already exists.

### Required Fix

Replace:
```markdown
If the script encounters "Cycles" or "Architectural Violations", it will output them to the map (and you can modify the script to exit with error code 1 if strictness is desired).
```

With:
```markdown
The `--strict` flag causes the script to exit with error code 1 if any issues are found, failing the pipeline.
```

---

## Issue 6: Update The Manual Reference

### Problem

The Manual references `scripts/migrate_frontmatter.py --auto` which no longer exists.

### Required Fix

In `20251124_Project Ontos The Manual.md`, change:

```markdown
> **Automation:** Use `scripts/migrate_frontmatter.py --auto` to automatically tag existing documents using an LLM.
```

To:

```markdown
> **Automation:** Use `scripts/migrate_frontmatter.py` to scan for untagged files, then tag them using your AI agent.
```

---

## Deliverables Summary

| # | File | Action |
|---|------|--------|
| 1 | `scripts/generate_context_map.py` | Add `import sys` |
| 2 | `scripts/migrate_frontmatter.py` | Remove API integration, simplify to scanner |
| 3 | `requirements.txt` | Reduce to just `pyyaml` |
| 4 | `MIGRATION_GUIDE.md` | Rewrite for agent-native workflow |
| 5 | `DEPLOYMENT.md` | Fix `--strict` wording |
| 6 | `20251124_Project Ontos The Manual.md` | Remove `--auto` reference |

---

## Verification Checklist

After changes:

- [ ] `python3 scripts/generate_context_map.py --strict` exits 1 on issues (no crash)
- [ ] `python3 scripts/migrate_frontmatter.py` outputs file list and prompt
- [ ] No `--auto` or `--apply` flags exist
- [ ] `requirements.txt` contains only `pyyaml`
- [ ] All docs reference the simplified workflow
