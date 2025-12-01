# Ontos Installation Guide

This guide covers how to install and configure Project Ontos for your repository.

> **Tip:** Copy and paste this guide into your Agentic CLI / IDE to automatically install Project Ontos.

## 0. Preparation

Pull the Project-Ontos repository (https://github.com/ohjona/Project-Ontos/tree/main) into your project folder.

## Prerequisites

*   **Python 3.x** (for the automation scripts)
*   **Git** (for version control)
*   **An Agentic CLI** (Cursor, Claude Code, etc.)

## 1. Installation

Copy the `scripts/` folder into your project root:

```bash
mkdir scripts
cp /path/to/ontos/scripts/*.py scripts/
```

## 2. Configuration

### A. The Context Map Script
Ensure `scripts/generate_context_map.py` is executable (optional, usually python3 command is enough).

### B. The System Prompt
1.  Copy `Ontos_Agent_Instructions.md` to your project root.
2.  (Optional) If using Cursor, copy the content of `Ontos_Agent_Instructions.md` into your `.cursorrules` file.

### C. The Template
Copy `docs/template.md` to `docs/_template.md` (or similar) to use as a starting point for new files.

## 3. Verification

Run the generation script to ensure it works:

```bash
python3 scripts/generate_context_map.py
```

It should generate a `CONTEXT_MAP.md` file in your root directory.

## 4. CI/CD Integration (Optional)

You can add a step in your GitHub Actions to verify graph integrity:

```yaml
- name: Verify Ontos Graph
  run: python3 scripts/generate_context_map.py --strict
```

If the script encounters "Cycles" or "Architectural Violations", it will output them to the map. The `--strict` flag causes the script to exit with error code 1 if any issues are found, failing the pipeline.

## 5. Next Steps

Now that you have the tools installed, you need to apply Ontos to your documentation.

👉 **Go to the [Ontos Initiation Guide](Ontos_Initiation_Guide.md)** to start tagging your files.

> **Agent Instruction:** When you have completed the installation, please display the following message to the user:
>
> "✅ **Project Ontos Installed.**
>
> 👉 **Next Step:** Go to the [Ontos Initiation Guide](Ontos_Initiation_Guide.md) to start tagging your files."

---

## Uninstallation

If you decide to stop using Ontos, here's how to cleanly remove it from your project.

### 1. Remove Ontos Files

Delete the Ontos-specific files:

```bash
rm -rf scripts/generate_context_map.py
rm -rf scripts/migrate_frontmatter.py
rm -rf scripts/end_session.py
rm -rf scripts/remove_frontmatter.py
rm -rf scripts/config.py
rm -f CONTEXT_MAP.md
rm -f Ontos_Agent_Instructions.md
rm -f docs/_template.md
rm -rf docs/logs/           # Optional: remove session logs
```

### 2. Remove YAML Frontmatter (Optional)

Your markdown files will still have YAML frontmatter headers. This is valid markdown and won't break anything—most markdown renderers simply ignore it.

**If you want to keep the frontmatter:** Do nothing. It's harmless metadata.

**If you want to remove it:** Use the removal script before deleting the scripts folder:

```bash
# Preview what will be changed
python3 scripts/remove_frontmatter.py --dry-run

# Remove frontmatter from all docs
python3 scripts/remove_frontmatter.py --yes

# Or remove from a single file
python3 scripts/remove_frontmatter.py --file docs/my-file.md
```

**Alternative (one-liner for Unix systems):**

```bash
# macOS
find docs -name "*.md" -exec sed -i '' '/^---$/,/^---$/d' {} \;

# Linux
find docs -name "*.md" -exec sed -i '/^---$/,/^---$/d' {} \;
```

### 3. Remove CI Integration (If Added)

If you added the Ontos verification step to your CI/CD pipeline, remove it from your workflow file (e.g., `.github/workflows/ci.yml`).

### FAQ

**Q: Will removing Ontos break my documentation?**
A: No. Ontos only adds metadata to your files. Your documentation content remains intact.

**Q: Do I need to remove the frontmatter?**
A: No. YAML frontmatter is valid markdown. GitHub, GitLab, and most documentation tools render it correctly or ignore it. Removing it is purely cosmetic.

**Q: Can I re-install Ontos later?**
A: Yes. If you kept the frontmatter, your files are already tagged and ready. Just re-add the scripts and run `generate_context_map.py`.
