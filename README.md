# Ontos: The Context Protocol for Agents

**Give your AI Agents a map, not just files.**

Ontos is a lightweight framework for managing project context in the age of Agentic AI. It structures your documentation with YAML frontmatter, allowing autonomous agents (like Claude Code, Cursor, or Google Antigravity) to "discover" the right context before they start coding.

## 🤖 The Problem: Agents are Blind
When you ask an agent to "fix the login bug", it has two bad options:
1.  **Guessing**: It searches for "login" and misses the `auth_provider.ts` file.
2.  **Overloading**: It reads *everything*, wasting tokens and confusing itself.

## 💡 The Solution: A Context Map
Ontos generates a `CONTEXT_MAP.md` that serves as a **Sitemap for Agents**.

Instead of guessing, the Agent reads the map first. It sees:
> "Feature: Login Flow (ID: `feature_login`) depends on `auth_architecture` and `user_model`."

The Agent then autonomously reads *only* those files, getting perfect context every time.

## ⚡️ Session Activation
To start a session, simply tell your Agent:
> **"Activate Ontos."** (or "Ontos Activate", "Ontos")

This triggers the standard protocol:
1.  **Check Map**: The Agent looks for `CONTEXT_MAP.md`.
2.  **Generate**: If missing, it runs `scripts/generate_context_map.py`.
3.  **Read**: It reads the map to understand the project structure.
4.  **Identify**: It identifies relevant documentation IDs for your request.
5.  **Load**: It reads *only* the specific files needed.
6.  **Confirm**: It confirms with "Loaded: [list of doc IDs]".

(If the Agent asks "What is Ontos?", tell it: **"Read `AGENT_INSTRUCTIONS.md`"**)

## 🚀 Getting Started

> **Tip:** See [DEPLOYMENT.md](DEPLOYMENT.md) for a step-by-step guide on adding Ontos to your repository.

### 1. The "Database" Record (YAML Frontmatter)
Every markdown file in `docs/` starts with a standard header. This links your knowledge atoms together.

```yaml
---
id: unique_slug_name  # e.g. 'auth_flow'
type: atom            # Options: [kernel, strategy, product, atom]
status: active
depends_on: []        # e.g. ['strategy_monetization']
---
```

> **Automation:** Use [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) and `scripts/migrate_frontmatter.py` to automatically tag your existing docs using an LLM.

### 2. The Context Map
Run the script to generate the map:

```bash
python3 scripts/generate_context_map.py
# Or specify a custom directory:
python3 scripts/generate_context_map.py --dir ./my-docs
```

This generates `CONTEXT_MAP.md`. **Commit this file.**

### Automated Audits
The script performs 5 integrity checks on your documentation graph:
1.  **Broken Links**: IDs that don't exist.
2.  **Circular Dependencies**: Infinite loops (A -> B -> A).
3.  **Orphaned Nodes**: Files disconnected from the graph.
4.  **Dependency Depth**: Chains deeper than 5 layers.
5.  **Architectural Violations**: Higher-layer docs (Atoms) depending on Lower-layer docs (Kernel).

## 📖 The Agentic Workflow

### Phase 1: Context Discovery
When you assign a task to your Agent:

**User:** "Update the Login flow to support 2FA."

**Agent (Internal Monologue):**
1.  "I need to understand the Login flow."
2.  *Reads `CONTEXT_MAP.md`*
3.  "I see `feature_login` depends on `auth_architecture`."
4.  *Reads `docs/auth/login.md` and `docs/arch/auth.md`*
5.  "I now have the full context. Starting work."

### Phase 2: The Update Loop (Write-Back)
If the Agent makes a decision (e.g., "We will use TOTP for 2FA"), it should update the documentation.

**User:** "Make sure to update the docs."

**Agent:**
1.  *Finds `feature_login` in the map.*
2.  *Updates `docs/auth/login.md` with the new 2FA details.*
3.  *Re-runs `scripts/generate_context_map.py` to verify links.*

### Phase 3: Session Commit (Archival)
At the end of a session, ask the Agent to archive its decisions.

**User:** "We are done. Archive our decisions." (or "Ontos archive", "Archive our session")

**Agent:**
1.  *Runs `python3 scripts/end_session.py "auth-update"` to scaffold the log file.*
2.  *Fills in the "Decisions" and "Summary" sections in the newly created file.*
3.  *Commits the log file to git.*

## 📂 Repository Structure

- `docs/`: Your knowledge base.
- `scripts/`: Automation tools.
- `CONTEXT_MAP.md`: The map for your Agent.
