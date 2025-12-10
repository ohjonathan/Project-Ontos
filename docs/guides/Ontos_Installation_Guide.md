# Ontos Installation Guide

This guide covers how to install and configure Project Ontos for your repository.

## Quick Install (Paste into Your AI Tool)

Copy this entire block and paste it into Claude Code, Cursor, or any agentic CLI:

```
Install Project Ontos in this repository.

1. Clone or download the Ontos scripts from: https://github.com/ohjona/Project-Ontos
2. Copy the `.ontos/` folder into my project root
3. Copy `docs/reference/Ontos_Agent_Instructions.md` to my project root
4. Run `python3 .ontos/scripts/ontos_install_hooks.py` to install git hooks
5. Run `python3 .ontos/scripts/ontos_generate_context_map.py` to verify installation
6. If successful, show me the contents of Ontos_Context_Map.md

Reference the full installation guide if needed:
https://github.com/ohjona/Project-Ontos/blob/main/docs/guides/Ontos_Installation_Guide.md
```

---

## Manual Installation

> **Tip:** The instructions below are for manual installation. If you used the Quick Install above, skip to [Verification](#3-verification).

### 0. Preparation

Pull the Project-Ontos repository (https://github.com/ohjona/Project-Ontos/tree/main) into your project folder.

### Prerequisites

*   **Python 3.x** (for the automation scripts)
*   **Git** (for version control)
*   **An Agentic CLI** (Cursor, Claude Code, etc.)

### 1. Installation

Copy the `.ontos/` folder into your project root:

```bash
mkdir -p .ontos/scripts .ontos/hooks
cp /path/to/ontos/.ontos/scripts/*.py .ontos/scripts/
cp /path/to/ontos/.ontos/hooks/* .ontos/hooks/
```

Install the git hooks:

```bash
python3 .ontos/scripts/ontos_install_hooks.py
```

This installs the pre-push hook, which reminds you to archive your session before pushing.

### 2. Configuration

#### A. Understanding the Config Files

Ontos uses a two-file configuration system:

| File | Purpose | Updated by `ontos_update.py`? |
|------|---------|-------------------------------|
| `ontos_config_defaults.py` | Default settings shipped with Ontos | Yes |
| `ontos_config.py` | Your project-specific overrides | **Never** |

To customize Ontos for your project, edit `ontos_config.py`:

```python
# Example: Change docs directory
DOCS_DIR = 'documentation'  # Instead of default 'docs'

# Example: Add skip patterns
SKIP_PATTERNS = DEFAULT_SKIP_PATTERNS + ['drafts/', 'archive/']
```

#### B. The System Prompt
1.  Copy `Ontos_Agent_Instructions.md` to your project root.
2.  (Optional) If using Cursor, copy the content of `Ontos_Agent_Instructions.md` into your `.cursorrules` file.

#### C. The Template
Copy `docs/template.md` to `docs/_template.md` (or similar) to use as a starting point for new files.

### 3. Verification

Run the generation script to ensure it works:

```bash
python3 .ontos/scripts/ontos_generate_context_map.py
```

It should generate an `Ontos_Context_Map.md` file in your root directory.

### 4. CI/CD Integration (Optional)

You can add a step in your GitHub Actions to verify graph integrity:

```yaml
- name: Verify Ontos Graph
  run: python3 .ontos/scripts/ontos_generate_context_map.py --strict
```

If the script encounters "Cycles" or "Architectural Violations", it will output them to the map. The `--strict` flag causes the script to exit with error code 1 if any issues are found, failing the pipeline.

### 5. Next Steps

Now that you have the tools installed, you need to apply Ontos to your documentation.

👉 **Go to the [Ontos Initiation Guide](Ontos_Initiation_Guide.md)** to start tagging your files.

> **Agent Instruction:** When you have completed the installation, please display the following message to the user:
>
> "✅ **Project Ontos Installed.**
>
> 👉 **Next Step:** Go to the [Ontos Initiation Guide](Ontos_Initiation_Guide.md) to start tagging your files."

---

## Uninstallation

👉 See the [Ontos Uninstallation Guide](Ontos_Uninstallation_Guide.md) for instructions on removing Ontos from your project.
