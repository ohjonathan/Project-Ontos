# Ontos Uninstallation Guide

If you decide to stop using Ontos, here's how to cleanly remove it from your project.

## 1. Remove Ontos Files

Delete the Ontos-specific files:

```bash
rm -rf .ontos/                # Remove all Ontos scripts
rm -f Ontos_Context_Map.md
rm -f Ontos_Agent_Instructions.md
rm -f docs/_template.md
rm -rf docs/logs/             # Optional: remove session logs
```

## 2. Remove YAML Frontmatter (Optional)

Your markdown files will still have YAML frontmatter headers. This is valid markdown and won't break anything—most markdown renderers simply ignore it.

**If you want to keep the frontmatter:** Do nothing. It's harmless metadata.

**If you want to remove it:** Use the removal script before deleting the `.ontos/` folder:

```bash
# Preview what will be changed
python3 .ontos/scripts/ontos_remove_frontmatter.py --dry-run

# Remove frontmatter from all docs
python3 .ontos/scripts/ontos_remove_frontmatter.py --yes

# Or remove from a single file
python3 .ontos/scripts/ontos_remove_frontmatter.py --file docs/my-file.md
```

**Alternative (one-liner for Unix systems):**

```bash
# macOS
find docs -name "*.md" -exec sed -i '' '/^---$/,/^---$/d' {} \;

# Linux
find docs -name "*.md" -exec sed -i '/^---$/,/^---$/d' {} \;
```

## 3. Remove CI Integration (If Added)

If you added the Ontos verification step to your CI/CD pipeline, remove it from your workflow file (e.g., `.github/workflows/ci.yml`).

## FAQ

**Q: Will removing Ontos break my documentation?**
A: No. Ontos only adds metadata to your files. Your documentation content remains intact.

**Q: Do I need to remove the frontmatter?**
A: No. YAML frontmatter is valid markdown. GitHub, GitLab, and most documentation tools render it correctly or ignore it. Removing it is purely cosmetic.

**Q: Can I re-install Ontos later?**
A: Yes. If you kept the frontmatter, your files are already tagged and ready. Just re-add the `.ontos/` folder and run `ontos_generate_context_map.py`.
