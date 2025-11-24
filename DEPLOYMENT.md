# Deploying Ontos to Your Repository

This guide explains how to integrate the Ontos "Context Protocol" into an existing project to supercharge your AI Agents.

## 1. Prerequisites (Critical)

**Ontos requires an Agentic CLI.**
Because Ontos relies on the agent autonomously reading files from your local disk, it **will not work** with standard web-based chat interfaces (like the basic ChatGPT website).

You must use an Agentic CLI tool that has file system access, such as:
-   **Google Antigravity**
-   **Claude Code**
-   **ChatGPT Codex / Advanced Data Analysis**
-   **Cursor**

## 2. Installation

### A. Copy Files
Copy the following files from the Ontos repository to your project root:

1.  `scripts/generate_context_map.py` -> `scripts/generate_context_map.py`
2.  `docs/template.md` -> `docs/template.md` (Optional, for reference)

### B. Setup Directory
Ensure you have a `docs/` directory. We recommend the following structure:
```bash
mkdir -p docs/kernel docs/strategy docs/product docs/atom
```

### C. Dependencies
Ensure you have Python 3 installed. You will need the `PyYAML` library:
```bash
pip install pyyaml
```

## 3. Configuration (The Migration)

The core of Ontos is the **YAML Frontmatter**. You need to add this to your existing documentation.

### Step 1: Inventory
Identify your key documentation files (README, Architecture docs, API specs).

### Step 2: Add Frontmatter
Add the following header to the top of each markdown file:

```yaml
---
id: unique_id_for_this_file  # e.g., 'auth_flow', 'database_schema'
type: atom                   # Options: kernel, strategy, product, atom
status: active
depends_on: []               # e.g., ['system_architecture']
---
```

**Tips:**
- **IDs** must be unique across the project.
- **depends_on** is where the magic happens. Link "Feature Specs" to "Product Requirements".

## 4. Usage Workflow

### A. Generate the Map
Run the script to index your knowledge base:
```bash
python3 scripts/generate_context_map.py
# Or for a custom directory:
python3 scripts/generate_context_map.py --dir ./knowledge
```
This creates `CONTEXT_MAP.md`. **Commit this file.** It serves as the "Sitemap" for the LLM.

> **Note:** The script will output a "Dependency Audit". Fix any **Cycles**, **Broken Links**, or **Architectural Violations** immediately.

### B. The Agentic Workflow
When you assign a task to an Agent (Claude Code, Cursor, Antigravity):

1.  **Activation**: Tell the Agent: **"Activate Ontos"** (or "Ontos Activate", "Ontos").
2.  **Discovery**: The Agent checks/generates `CONTEXT_MAP.md` and reads it.
3.  **Targeting**: It identifies relevant IDs and reads *only* those files.
4.  **Confirmation**: It responds with "Loaded: [doc IDs]".
5.  **Execution**: The Agent writes code with full awareness of your architectural decisions.
5.  **Archival**: At the end, ask the Agent to "archive decisions". It should run `scripts/end_session.py` to create a log, then fill it with a summary of changes.

### C. Maintenance
- **New File**: Add frontmatter, then run `python3 scripts/generate_context_map.py`.
- **Changed Logic**: Update the doc, then run `python3 scripts/generate_context_map.py`.

## 5. Enforcing the Protocol

To ensure your Agents actually follow these rules, you should "install" the instructions into their system prompt.

### Option A: Cursor (Automatic)
If you use Cursor, simply copy `.cursorrules` to your project root. Cursor will automatically read this file and follow the Ontos protocol.

### Option B: General Agents (Manual)
For other agents (Claude Code, ChatGPT, etc.), you need to "install" the protocol into their context.

**Best Practice:** Copy and paste the content of **this file (`DEPLOYMENT.md`)** directly into the chat. This teaches the Agent the full context of the Ontos system.
> **Tip:** For best results, paste the guide section-by-section (e.g., "Here is Section 4: Usage Workflow...") to ensure the Agent fully processes each rule.

## 6. CI/CD Integration (Optional)
You can add a GitHub Action to ensure `CONTEXT_MAP.md` is always up to date:

```yaml
# .github/workflows/ontos.yml
name: Update Context Map
on:
  push:
    paths:
      - 'docs/**/*.md'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - name: Install dependencies
        run: pip install pyyaml
      - name: Generate Map
        run: python scripts/generate_context_map.py
      - name: Commit changes
        uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: "chore: update context map"
          file_pattern: CONTEXT_MAP.md
```
