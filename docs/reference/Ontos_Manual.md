# Ontos Manual v2.0

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
3. Confirm: "Loaded: [id1, id2]"

### Archive Session
Say **"Archive Ontos"** at end of session:
```bash
python3 .ontos/scripts/ontos_end_session.py "topic-slug" -s "Claude Code" -e feature
```
Event types: `feature`, `fix`, `refactor`, `exploration`, `chore`

**Important:** The pre-push hook blocks push until you archive. This is intentional—no context loss.

### Maintain Graph
Say **"Maintain Ontos"** weekly:
```bash
python3 .ontos/scripts/ontos_migrate_frontmatter.py  # Tag new files
python3 .ontos/scripts/ontos_generate_context_map.py  # Rebuild map
```

---


## 3. Monthly Consolidation

When `logs/` exceeds ~15 files, perform consolidation to keep context lean.

### The Ritual

1. **Review** — Scan the oldest 5-10 logs in `logs/`

2. **Verify Absorption** — For each log, check: have the key decisions been captured in Space documents?
   - If NO: Update the relevant `strategy` or `atom` doc first
   - If YES: Proceed to record

3. **Record** — Add an entry to `docs/strategy/decision_history.md`:
   - Date, slug, event type
   - One-line decision summary (what was decided, what was rejected)
   - Impacted documents
   - Archive path

4. **Cite** — Update impacted Space documents with a breadcrumb:
   ```markdown
   **Decision (2025-12-10):** Chose OAuth2 over session-based auth. See `decision_history.md`.
   ```

5. **Archive** — Move the log file:
   ```bash
   mv .ontos-internal/logs/2025-12-10_auth.md .ontos-internal/archive/logs/
   ```

6. **Commit** — Single commit: "chore: consolidate sessions from [date range]"

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

# Copy agent instructions
cp /path/to/ontos/docs/reference/Ontos_Agent_Instructions.md your-project/

# Initialize (installs hooks, generates context map)
cd your-project
python3 ontos_init.py
```

### Configuration

Edit `.ontos/scripts/ontos_config.py` (never auto-updated):

```python
# Custom docs directory
DOCS_DIR = os.path.join(PROJECT_ROOT, 'documentation')

# Relaxed mode (solo devs)
ENFORCE_ARCHIVE_BEFORE_PUSH = False
REQUIRE_SOURCE_IN_LOGS = False
```

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
| `ontos_migrate_frontmatter.py` | Find untagged files |
| `ontos_update.py` | Pull latest from GitHub |
| `ontos_install_hooks.py` | Install git hooks |
| `ontos_remove_frontmatter.py` | Strip YAML headers |

### Common flags
- `--strict` — Exit 1 on any issue
- `--quiet` / `-q` — Suppress output
- `--dry-run` — Preview without changes
- `--version` / `-V` — Show version
