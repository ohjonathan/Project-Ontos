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
