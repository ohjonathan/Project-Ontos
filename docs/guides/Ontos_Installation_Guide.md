---
id: ontos_installation_guide
title: Ontos Installation Guide
type: product
status: active
depends_on: []
---

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
