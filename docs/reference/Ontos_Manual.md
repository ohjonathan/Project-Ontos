---
id: ontos_manual
type: kernel
status: active
depends_on: []
---

# Ontos Manual v2.4

*The complete reference for Project Ontos*

---

## Quick Start

```bash
# 1. Clone Ontos
git clone https://github.com/ohjona/Project-Ontos.git /tmp/ontos

# 2. Copy to your project
cp -r /tmp/ontos/.ontos your-project/
cp /tmp/ontos/ontos_init.py your-project/
cp /tmp/ontos/docs/reference/Ontos_Agent_Instructions.md your-project/

# 3. Initialize (installs hooks, generates context map)
cd your-project
python3 ontos_init.py

# 4. Activate
# Tell your AI: "Ontos"
```

---

## 1. Core Concepts

### Configuration Modes (v2.4)

Ontos offers three workflow modes to match your preferences:

| Mode | Behavior | Best For |
|------|----------|----------|
| **automated** | Auto-archives on push, no blocking | Solo devs, rapid prototyping |
| **prompted** | Blocks push until archived | Teams, audit trails |
| **advisory** | Reminders only, no blocking | Maximum flexibility |

**Choosing Your Mode:** During installation, `ontos_init.py` asks for your preference. Change later with:
```bash
python3 ontos_init.py --reconfig
```

**Environment Variables:** For CI/CD, set `ONTOS_SOURCE` to override the default source:
```bash
ONTOS_SOURCE="GitHub Actions" git push
```

### Document Types

| Type | Rank | Use For |
|------|------|---------|
| `kernel` | 0 | Mission, values, principles (rarely changes) |
| `strategy` | 1 | Goals, roadmap, audience (business decisions) |
| `product` | 2 | Features, user flows, requirements |
| `atom` | 3 | Technical specs, API, implementation |
| `log` | 4 | Session history (what happened) |

**Rule:** Dependencies flow DOWN. Atoms depend on products, not vice versa.

### Frontmatter Schema

```yaml
---
id: unique_snake_case      # Required. Never change.
type: atom                  # Required. kernel|strategy|product|atom|log
status: active              # Optional. draft|active|deprecated
depends_on: [parent_id]     # Optional. List of dependency IDs
---
```

### Classification Heuristic

When uncertain: "If this doc changes, what else breaks?"
- Everything → `kernel`
- Business direction → `strategy`  
- User experience → `product`
- Only implementation → `atom`

---

## 2. Daily Workflow

### Activate Context
Say **"Ontos"** to your AI agent. It will:
1. Read `Ontos_Context_Map.md`
2. Load relevant files based on your request
    print("Loaded: [id1, id2]")
    
### Query Graph
Say **"Query Ontos"** to find connections:
```bash
python3 .ontos/scripts/ontos_query.py --depends-on auth_flow
python3 .ontos/scripts/ontos_query.py --stale 30
python3 .ontos/scripts/ontos_query.py --health
```

### Archive Session
Say **"Archive Ontos"** at end of session:
```bash
# Basic (interactive)
python3 .ontos/scripts/ontos_end_session.py

# Advanced (one-liner)
python3 .ontos/scripts/ontos_end_session.py -e feature -s "Claude"
```

**Automated Mode:** Sessions are auto-archived on push. One log per branch per day—subsequent pushes append to the same log.

**Auto-generated logs:** Logs created by `--auto` are marked `status: auto-generated`. Enrich them with:
```bash
python3 .ontos/scripts/ontos_end_session.py --enhance
```

**The "Left Behind" Paradox:** Auto-generated logs are created during push but aren't included in *that* push (Git limitation). They'll be in your next commit. To include immediately: `git add . && git commit --amend`

Flags: `--auto` (hook mode), `--enhance` (enrich log), `--dry-run` (preview), `--list-concepts` (vocabulary)
Event types: `feature`, `fix`, `refactor`, `exploration`, `chore`, `decision`

### Maintain Graph
Say **"Maintain Ontos"** weekly:
```bash
python3 .ontos/scripts/ontos_maintain.py
```
This runs three steps:
1. **Migrate** — Tag untagged files
2. **Generate** — Validate and regenerate context map  
3. **Consolidate** — Archive old logs (if `AUTO_CONSOLIDATE=True`)

Use `--lint` to check for data quality issues.

---


## 3. Monthly Consolidation

When `logs/` exceeds ~15 files, perform consolidation to keep context lean.

### The Ritual

1. **Review & Consolidate**
   Run the consolidation tool:
   ```bash
   python3 .ontos/scripts/ontos_consolidate.py --days 30
   ```
   This script will:
   - Find old logs
   - Extract/prompt for summaries
   - Archive the log file
   - Update `decision_history.md`

2. **Verify Absorption**
   The tool updates the ledger, but **you** must clear technical debt.
   Check impacted documents: does the code match the decision?

3. **Commit**
   Single commit: "chore: consolidate sessions"

### Absorption Pattern

Good absorption captures outcome + constraints + citation.

**Before (Space doc says):**
```markdown
## Authentication
Uses OAuth2 with JWT tokens.
```

**After (Space doc says):**
```markdown
## Authentication
Uses OAuth2 with JWT tokens.

**Constraints:**
- Session-based auth rejected (statelessness requirement)
- Firebase Auth rejected (vendor lock-in)

**Decision (2025-12-10):** See `decision_history.md`.
```

### When to Consolidate

| Trigger | Action |
|---------|--------|
| `logs/` has >15 files | Consolidate oldest 5-10 |
| Quarterly review | Consolidate all logs >30 days old |
| Before major release | Consolidate all active logs |

---

## 4. Installation

### Prerequisites
- Python 3.9+
- Git

### Standard Install
```bash
# Copy scripts and init file
cp -r /path/to/ontos/.ontos your-project/
cp /path/to/ontos/ontos_init.py your-project/

# Create docs directory
mkdir -p docs/reference

# Copy agent instructions
cp /path/to/ontos/docs/reference/Ontos_Agent_Instructions.md your-project/docs/reference/

# Copy common concepts (v2.2+)
cp /path/to/ontos/.ontos-internal/reference/Common_Concepts.md your-project/docs/reference/

# Initialize (installs hooks, generates context map)
cd your-project
python3 ontos_init.py
```

### Configuration

Edit `ontos_config.py` in your project root:

```python
# Quick setup: Choose your mode
ONTOS_MODE = "prompted"  # "automated", "prompted", or "advisory"

# Your name for log attribution
DEFAULT_SOURCE = "Claude Code"

# Override individual settings if needed (uncomment to use)
# AUTO_ARCHIVE_ON_PUSH = True
# ENFORCE_ARCHIVE_BEFORE_PUSH = False
# AUTO_CONSOLIDATE = True
```

**Mode Presets:**

| Setting | automated | prompted | advisory |
|---------|-----------|----------|----------|
| AUTO_ARCHIVE_ON_PUSH | True | False | False |
| ENFORCE_ARCHIVE_BEFORE_PUSH | False | True | False |
| REQUIRE_SOURCE_IN_LOGS | False | True | False |
| AUTO_CONSOLIDATE | True | True | False |

### Uninstall
```bash
rm -rf .ontos/
rm -f Ontos_Context_Map.md Ontos_Agent_Instructions.md
# Optional: remove frontmatter
python3 .ontos/scripts/ontos_remove_frontmatter.py --yes
```

---

## 5. Migrating Existing Docs

### Auto-detect untagged files
```bash
python3 .ontos/scripts/ontos_migrate_frontmatter.py
```

### Tag via AI
Give your agent the generated `migration_prompt.txt`. It will:
1. Read each file
2. Determine type based on content
3. Add frontmatter
4. Run validation

### Validate
```bash
python3 .ontos/scripts/ontos_generate_context_map.py --strict
```

---

## 6. Error Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `[BROKEN LINK]` | Reference to nonexistent ID | Create doc or remove reference |
| `[CYCLE]` | A → B → A | Remove one dependency |
| `[ORPHAN]` | No dependents | Connect it or delete |
| `[DEPTH]` | Chain > 5 levels | Flatten hierarchy |
| `[ARCHITECTURE]` | Kernel depends on atom | Invert or retype |

---

## 7. CI/CD Integration

### Strict validation
```yaml
- name: Validate Ontos
  run: python3 .ontos/scripts/ontos_generate_context_map.py --strict --quiet
```

### Pre-commit hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ontos-validate
        name: Validate Ontos
        entry: python3 .ontos/scripts/ontos_generate_context_map.py --strict --quiet
        language: system
        pass_filenames: false
```

---

## 8. Updating Ontos

```bash
# Check for updates
python3 .ontos/scripts/ontos_update.py --check

# Apply update
python3 .ontos/scripts/ontos_update.py

# Your ontos_config.py is never overwritten
```

---

## 9. Scripts Reference

| Script | Purpose |
|--------|---------|
| `ontos_generate_context_map.py` | Build graph, validate, generate map |
| `ontos_end_session.py` | Create session log |
| `ontos_query.py` | Query the graph (deps, concepts, stale) |
| `ontos_maintain.py` | Run migration + regeneration tasks |
| `ontos_consolidate.py` | Consolidate old logs into history |
| `ontos_migrate_frontmatter.py` | Find untagged files |
| `ontos_update.py` | Pull latest from GitHub |
| `ontos_pre_push_check.py` | Pre-push hook logic |
| `ontos_remove_frontmatter.py` | Strip YAML headers |

### Common flags
- `--strict` — Exit 1 on any issue
- `--quiet` / `-q` — Suppress output
- `--dry-run` — Preview without changes
- `--version` / `-V` — Show version
