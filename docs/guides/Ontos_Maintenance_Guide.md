---
id: ontos-maintenance-guide
type: product
status: active
depends_on: []
---

# Ontos Maintenance Guide

This guide covers how to keep your Ontos-powered documentation healthy over time: the weekly ritual, context hygiene, error remediation, and updating to new versions.

## Why Maintenance Matters

Ontos transforms your documentation into a living knowledge graph. Like any system, it needs care to stay useful:

- **Broken links** → Agents get confused, load wrong context
- **Orphaned nodes** → Documentation becomes invisible, forgotten
- **Cycles** → Infinite loops break dependency resolution
- **Architectural violations** → The hierarchy loses meaning

A few minutes of maintenance prevents hours of debugging context issues.

---

## The Weekly Ritual

> **Trigger:** Tell your agent "Maintain Ontos" or "Ontos maintenance"

### What Happens

1. **Frontmatter check** — Tags any new markdown files without YAML headers
2. **Graph integrity** — Rebuilds the context map and runs all validators
3. **Issue report** — Lists any problems found
4. **Commit** — Saves the updated context map

### Manual Steps

```bash
# 1. Tag untagged files
python3 .ontos/scripts/ontos_migrate_frontmatter.py

# 2. Rebuild and validate the graph
python3 .ontos/scripts/ontos_generate_context_map.py

# 3. Review Ontos_Context_Map.md for issues

# 4. Commit
git add Ontos_Context_Map.md
git commit -m "chore: weekly Ontos maintenance"
```

### When to Run

- **Weekly** — Scheduled maintenance to catch drift
- **After large refactors** — Documentation structure changes
- **Before releases** — Ensure graph is clean for production
- **When agents seem confused** — Often a sign of graph issues

---

## Context Hygiene During Sessions

Good habits prevent maintenance debt.

### When Creating Files

Always add YAML frontmatter immediately:

```yaml
---
id: unique-doc-id
type: atom  # or kernel, strategy, product
status: active
depends_on:
  - parent-doc-id
---
```

### When Deleting Files

1. Search for references: `grep -r "deleted-doc-id" docs/`
2. Remove from other files' `depends_on` lists
3. Regenerate the context map

### When Renaming IDs

1. Update the `id` field in the file
2. Find all references: `grep -r "old-id" docs/`
3. Update all `depends_on` references
4. Regenerate the context map

---

## Error Types & How to Fix Them

### Broken Links

**Symptom:** `[BROKEN LINK] doc-a references missing ID: doc-b`

**Causes:**
- Referenced document was deleted
- Typo in the `depends_on` ID
- Document exists but lacks frontmatter

**Fixes:**
```bash
# Option A: Remove the reference
# Edit doc-a.md, remove "doc-b" from depends_on

# Option B: Create the missing document
# Create doc-b.md with proper frontmatter including id: doc-b

# Option C: Fix the typo
# Edit doc-a.md, correct the ID spelling
```

### Cycles

**Symptom:** `[CYCLE] Circular dependency: doc-a -> doc-b -> doc-a`

**Cause:** Documents depend on each other in a loop

**Fix:**
Decide which dependency is "primary" and remove the other:

```yaml
# doc-a.md - KEEP this dependency
depends_on:
  - doc-b

# doc-b.md - REMOVE this dependency
depends_on: []  # Remove doc-a
```

**Heuristic:** Lower-layer types (atoms) should depend on higher-layer types (strategy, kernel), not the reverse.

### Orphaned Nodes

**Symptom:** `[ORPHAN] doc-a has no dependents`

**Causes:**
- New document not yet integrated
- Document became disconnected after refactor
- Document is genuinely standalone (logs, archives)

**Fixes:**
```bash
# Option A: Connect it to a parent
# Edit another document to add doc-a to its depends_on

# Option B: It's intentionally standalone
# Orphan detection ignores: kernel, strategy, product types, and /logs/ directory
# Change the type if appropriate

# Option C: Delete if unused
rm docs/path/to/doc-a.md
```

### Architectural Violations

**Symptom:** `[ARCHITECTURE] kernel-doc (kernel) depends on atom-doc (atom)`

**Cause:** A foundational document depends on an implementation detail (violates the hierarchy)

**The Rule:** Dependencies flow DOWN the stack:
- `atom` → `product` → `strategy` → `kernel` ✅
- `kernel` → `atom` ❌

**Fixes:**
```bash
# Option A: Invert the dependency
# Remove atom-doc from kernel-doc's depends_on
# Add kernel-doc to atom-doc's depends_on

# Option B: Reclassify the document
# If kernel-doc is actually implementation detail, change type to atom
```

### Depth Violations

**Symptom:** `[DEPTH] doc-a has dependency depth 6 (max: 5)`

**Cause:** Too many layers of dependencies

**Fixes:**
```bash
# Option A: Flatten the hierarchy
# Remove intermediate dependencies

# Option B: Increase the limit (if justified)
# Edit ontos_config.py:
MAX_DEPENDENCY_DEPTH = 7
```

---

## Updating Ontos

When new versions of Ontos are released, use the update script to pull the latest.

### Check for Updates

```bash
python3 .ontos/scripts/ontos_update.py --check
```

### Preview Changes

```bash
python3 .ontos/scripts/ontos_update.py --dry-run
```

### Apply Update

```bash
python3 .ontos/scripts/ontos_update.py
```

### What Gets Updated

| Category | Files | Your customizations? |
|----------|-------|---------------------|
| Scripts | `ontos_*.py` (except `ontos_config.py`) | **Preserved** |
| Defaults | `ontos_config_defaults.py` | N/A (no customizations here) |
| Docs | Manual, Agent Instructions, Guides | Overwritten |

**Important:** Your `ontos_config.py` is NEVER touched. All your customizations (custom `DOCS_DIR`, `SKIP_PATTERNS`, etc.) are safe.

### Backups

Before any update, backups are saved to `.ontos/backups/`. If something goes wrong:

```bash
# Restore a backup
cp .ontos/backups/ontos_generate_context_map.py.bak .ontos/scripts/ontos_generate_context_map.py
```

### Manual Update (Alternative)

If you prefer manual control:

```bash
# 1. Clone latest Ontos
git clone --depth 1 https://github.com/ohjona/project-ontos /tmp/ontos-latest

# 2. Compare versions
diff .ontos/scripts/ontos_config_defaults.py /tmp/ontos-latest/.ontos/scripts/ontos_config_defaults.py

# 3. Copy updated scripts (except your config)
cp /tmp/ontos-latest/.ontos/scripts/ontos_config_defaults.py .ontos/scripts/
cp /tmp/ontos-latest/.ontos/scripts/ontos_generate_context_map.py .ontos/scripts/
# ... etc

# 4. Cleanup
rm -rf /tmp/ontos-latest
```

---

## CI/CD Integration

### Strict Mode

Add graph validation to your pipeline:

```yaml
# .github/workflows/ci.yml
- name: Validate Ontos Graph
  run: python3 .ontos/scripts/ontos_generate_context_map.py --strict
```

The `--strict` flag exits with code 1 if any issues are found, failing the build.

### Pre-commit Hook

Validate before every commit:

```bash
# .git/hooks/pre-commit
#!/bin/sh
python3 .ontos/scripts/ontos_generate_context_map.py --strict --quiet
```

---

## Troubleshooting

### "No files with frontmatter found"

Your docs directory might be misconfigured. Check `ontos_config.py`:

```python
DOCS_DIR = 'docs'  # Make sure this matches your actual directory
```

### "ModuleNotFoundError: No module named 'yaml'"

Install PyYAML:

```bash
pip install pyyaml
```

### Agent Loads Wrong Context

1. Regenerate the context map
2. Check for broken links or orphans
3. Verify the agent is reading `Ontos_Context_Map.md` first

### Context Map is Stale

The context map is a generated artifact. If it seems outdated:

```bash
python3 .ontos/scripts/ontos_generate_context_map.py
```

Never edit `Ontos_Context_Map.md` directly — your changes will be overwritten.

---

## Quick Reference

| Task | Command |
|------|---------|
| Weekly maintenance | `python3 .ontos/scripts/ontos_migrate_frontmatter.py && python3 .ontos/scripts/ontos_generate_context_map.py` |
| Check for updates | `python3 .ontos/scripts/ontos_update.py --check` |
| Apply update | `python3 .ontos/scripts/ontos_update.py` |
| Validate strictly | `python3 .ontos/scripts/ontos_generate_context_map.py --strict` |
| Tag new files | `python3 .ontos/scripts/ontos_migrate_frontmatter.py` |
| Archive session | `python3 .ontos/scripts/ontos_end_session.py "session-slug"` |

---

## Next Steps

- 👉 [Ontos Manual](../reference/Ontos_Manual.md) — Full protocol reference
- 👉 [Ontos Agent Instructions](../reference/Ontos_Agent_Instructions.md) — What your AI agent follows
