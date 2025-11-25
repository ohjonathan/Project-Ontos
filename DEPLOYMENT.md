# 🛠️ Deployment & Installation

This guide covers how to install and configure Project Ontos for your repository.

## Prerequisites

*   **Python 3.x** (for the automation scripts)
*   **Git** (for version control)
*   **An AI Agent** (Cursor, Claude Code, etc.)

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
1.  Copy `AGENT_INSTRUCTIONS.md` to your project root.
2.  (Optional) If using Cursor, copy the content of `AGENT_INSTRUCTIONS.md` into your `.cursorrules` file.

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
  run: python3 scripts/generate_context_map.py
```

If the script encounters "Cycles" or "Architectural Violations", it will output them to the map (and you can modify the script to exit with error code 1 if strictness is desired).
