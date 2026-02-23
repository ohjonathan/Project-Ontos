---
id: ontos_manual
type: kernel
status: active
depends_on: []
---

# Ontos Manual v3.3

*The complete reference for Project Ontos*

---

## Quick Start

```bash
# Install Ontos via pip
pip install ontos
ontos init

# Activate
# Tell your AI: "Ontos"
```

> **v3.0 Note:** Ontos is now a proper Python package. See the [Migration Guide](Migration_v2_to_v3.md) for v2.x users.

---

## 1. Core Concepts

### Configuration Modes (v2.5)

Ontos offers three workflow modes, each with a clear promise:

| Mode | Promise | Archiving | Consolidation |
|------|---------|-----------|---------------|
| **automated** | "Zero friction — just works" | Auto on push | Auto on commit |
| **prompted** | "Keep me in the loop" | Blocks push | Agent reminder |
| **advisory** | "Maximum flexibility" | Warning only | Manual only |

**Choosing Your Mode:** During installation, `ontos init` shows each mode's promise. Change later with:
```bash
ontos init --force
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
ontos query --depends-on auth_flow
ontos query --stale 30
ontos query --health
```

### Archive Session
Say **"Archive Ontos"** at end of session:
```bash
# Basic (interactive)
ontos log

# Advanced (one-liner)
ontos log -e feature -t "Session summary"
```

**Automated Mode:** Sessions are auto-archived on push. One log per branch per day—subsequent pushes append to the same log.

**Auto-generated logs:** Logs created by `--auto` are marked `status: auto-generated`.

**The "Left Behind" Paradox:** Auto-generated logs are created during push but aren't included in *that* push (Git limitation). They'll be in your next commit. To include immediately: `git add . && git commit --amend`

Flags: `--auto` (hook mode), `--dry-run` (preview)
Event types: `feature`, `fix`, `refactor`, `exploration`, `chore`, `decision`

### Maintain Graph
Say **"Maintain Ontos"** weekly:
```bash
ontos maintain
```
This runs nine tasks:
1. **migrate_untagged** — Tag untagged files (includes scaffold)
2. **regenerate_map** — Regenerate context map
3. **health_check** — Run `ontos doctor`
4. **curation_stats** — Report curation stats (L0/L1/L2)
5. **promote_check** — Report documents ready for promotion (ready count)
6. **consolidate_logs** — Archive old logs (if `AUTO_CONSOLIDATE=True`)
7. **review_proposals** — Report draft proposals for manual graduation
8. **check_links** — Validate dependency links
9. **sync_agents** — Regenerate `AGENTS.md` when stale

Useful flags:
- `--dry-run` — Preview tasks without executing
- `--verbose` — Show detailed output per task
- `--skip TASK_NAME` — Skip specific tasks

---

## 3. Proposal Workflow (v2.6+)

Proposals live in `strategy/proposals/` until approved or rejected.

### Creating a Proposal
1. Create file in `strategy/proposals/` with `status: draft`
2. Review and iterate
3. When ready, either **approve** or **reject**

### Approving a Proposal (v2.6.1 - Automated)

**Option A: Automatic graduation (recommended)**
When you implement a proposal and run Archive Ontos, it detects implementation:
```
💡 Detected: This session may implement proposal 'v2_6_proposals'
   Graduate to strategy/? [y/N]: y
```
Answering `y` automatically:
- Moves proposal from `proposals/` to `strategy/`
- Changes `status: draft` → `status: active`
- Adds entry to `decision_history.md`

**Option B: Manual graduation**
1. Change `status: draft` → `status: active`
2. **Move file** from `proposals/` to `strategy/` (graduate up)
3. Add entry to `decision_history.md` with APPROVED outcome

**Fallback:** Maintain Ontos reports missed graduation candidates that match the current Ontos version for manual graduation

### Rejecting a Proposal
1. Change `status: draft` → `status: rejected`
2. Add required metadata:
   ```yaml
   status: rejected
   rejected_reason: "Detailed explanation of why"  # Required, min 10 chars
   rejected_date: 2025-12-17                       # Recommended
   ```
3. **Move file** from `proposals/` to `archive/proposals/`
4. Add entry to `decision_history.md` with REJECTED outcome

### Status Values (v2.6)
| Status | Meaning |
|--------|---------|
| `draft` | Work in progress |
| `active` | Current truth (approved, in use) |
| `deprecated` | Past truth (superseded) |
| `archived` | Historical record (logs) |
| `rejected` | Considered but NOT approved |
| `complete` | Finished work (reviews) |

### Viewing Rejected Proposals
Rejected docs are excluded from context map by default.

---

## 4. Curation Levels (v2.9+)

To lower the barrier to adoption, Ontos v2.9 supports tiered validation.

### The Levels

| Level | Name | Description | Validation |
|-------|------|-------------|------------|
| **0** | **Scaffold** | Auto-generated placeholder | Minimal (ID + Type only) |
| **1** | **Stub** | User provided goal | Relaxed (No deps required) |
| **2** | **Full** | Complete Ontos document | Strict (All fields required) |

### Curation Workflow

1. **Scaffold:** Generate placeholders for untagged files.
   ```bash
   ontos scaffold --apply
   ```

2. **Stub:** Identify the goal of a document.
   ```bash
   ontos stub --goal "Explain the payment flow" --type product
   ```

3. **Promote:** Add dependencies and concepts to reach Level 2.
   ```bash
   ontos promote --check
   ontos promote docs/payments.md
   ```

### Validation Modes

- **Standard:** `ontos map` (Includes L0/L1 documents)
- **Strict:** `ontos map --strict` (Fails if L0/L1 documents exist)

Use strict mode in CI/CD to ensure your knowledge graph is fully curated.

### Schema Versioning (v2.9.0)

Ontos v2.9 introduces explicit schema versioning to track document evolution.

**The Schema Field:**
```yaml
---
id: my_document
type: product
ontos_schema: "2.2"  # Indicates v2.2 schema
---
```

**Schema Versions:**
| Version | Features |
|---------|----------|
| 1.0 | ID only (legacy) |
| 2.0 | ID + Type |
| 2.1 | Staleness tracking (`describes`, `describes_verified`) |
| 2.2 | Curation levels (`curation_level`, `ontos_schema`) |

**Check Migration Status:**
```bash
ontos migrate --check
```

### Deprecation Warnings (v2.9.2)

Direct script execution is deprecated. Use the unified CLI:

```bash
# Deprecated (removed in v3.0)
# python3 .ontos/scripts/ontos_end_session.py

# Preferred
ontos log
```

**Note:** v3.0 no longer supports legacy script paths.

---

## 5. Monthly Consolidation

When `logs/` exceeds ~15 files, perform consolidation to keep context lean.

### The Ritual

1. **Review & Consolidate**
   Run the consolidation tool:
   ```bash
   ontos consolidate --days 30
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

## 6. Installation

### Prerequisites
- Python 3.9+
- Git

### Standard Install (v3.0+)

```bash
pip install ontos
ontos init
```

For development:
```bash
git clone https://github.com/ohjonathan/Project-Ontos.git
cd Project-Ontos
pip install -e .
ontos init
```

### What `ontos init` Creates (v3.1.1+)

**Directory Structure:**
```
your-project/
├── .ontos.toml           # Configuration
├── Ontos_Context_Map.md  # Document graph
├── AGENTS.md             # AI agent instructions
└── docs/
    ├── kernel/           # Core principles (rank 0)
    ├── strategy/         # Strategic documents (rank 1)
    ├── product/          # Product specifications (rank 2)
    ├── atom/             # Atomic utilities (rank 3)
    ├── logs/             # Session logs (rank 4)
    ├── reference/        # Reference materials
    └── archive/          # Archived documents
```

**Init Flags:**
| Flag | Effect |
|------|--------|
| `--scaffold` | Auto-scaffold untagged files in docs/ without prompting |
| `--no-scaffold` | Skip scaffold prompt entirely |
| `--skip-hooks` | Don't install git hooks |
| `--yes` / `-y` | Accept all defaults (non-interactive) |
| `--force` / `-f` | Overwrite existing config and hooks |

**Interactive Scaffold Prompt:**
If untagged markdown files exist in `docs/`, init prompts:
1. "Would you like to scaffold them? [y/N]"
2. Scope selection: (1) docs/ only, (2) entire repo, (3) custom path

**Safety:** The following directories are never scaffolded:
`node_modules`, `.venv`, `venv`, `vendor`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `dist`, `build`, `.tox`, `.eggs`

### Upgrading from v2.x

See the [Migration Guide](Migration_v2_to_v3.md) for step-by-step instructions.

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

**Complete removal** (removes Ontos AND all frontmatter from your docs):
```bash
# 1. Remove frontmatter FIRST (requires .ontos/ to exist)
python3 .ontos/scripts/ontos_remove_frontmatter.py --yes
# 2. Remove git hooks
rm -f .git/hooks/pre-push .git/hooks/pre-commit
# 3. Remove Ontos files
rm -rf .ontos/ .ontos.toml
rm -f Ontos_Context_Map.md CLAUDE.md
```

**Keep frontmatter** (preserves YAML headers in your docs):
```bash
# 1. Remove git hooks
rm -f .git/hooks/pre-push .git/hooks/pre-commit
# 2. Remove Ontos files only
rm -rf .ontos/ .ontos.toml
rm -f Ontos_Context_Map.md CLAUDE.md
```

---

## 7. Migrating Existing Docs

### Auto-scaffold untagged files (v2.9+)

Use the scaffold command to generate Level 0 frontmatter for all markdown files:

```bash
ontos scaffold --apply
```

This replaces the old `ontos_migrate_frontmatter.py` workflow.

### Tag via AI
Give your agent the generated `migration_prompt.txt`. It will:
1. Read each file
2. Determine type based on content
3. Add frontmatter
4. Run validation

### Validate
```bash
ontos map --strict
```

---

## 8. Error Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `[BROKEN LINK]` | Reference to nonexistent ID | Create doc or remove reference. (v3.2: See candidate suggestions) |
| `[CYCLE]` | A → B → A | Remove one dependency |
| `[ORPHAN]` | No dependents | Connect it or delete |
| `[DEPTH]` | Chain > 5 levels | Flatten hierarchy |
| `[ARCHITECTURE]` | Kernel depends on atom | Invert or retype |

---

## 9. CI/CD Integration

### Strict validation
```yaml
- name: Validate Ontos
  run: ontos map --strict --quiet
```

### Pre-commit hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ontos-validate
        name: Validate Ontos
        entry: ontos map --strict --quiet
        language: system
        pass_filenames: false
```

---

## 10. Unified CLI (v3.0)

Ontos v3.0 introduces a unified command interface:

```bash
ontos <command> [options]
```

### Available Commands

| Command     | Description            | Old Syntax (removed in v3.0)                          |
|-------------|------------------------|-------------------------------------------------------|
| `log`       | Archive a session      | `python3 .ontos/scripts/ontos_end_session.py`        |
| `map`       | Generate context map   | `python3 .ontos/scripts/ontos_generate_context_map.py` |
| `env`       | Detect environment     | (New in v3.2)                                         |
| `verify`    | Verify describes dates | `python3 .ontos/scripts/ontos_verify.py`             |
| `maintain`  | Run maintenance tasks  | `python3 .ontos/scripts/ontos_maintain.py`           |
| `link-check` | Scan for broken refs | (New in v3.3)                                         |
| `rename`    | Rename a document ID   | (New in v3.3)                                         |
| `consolidate` | Archive old logs     | `python3 .ontos/scripts/ontos_consolidate.py`        |
| `query`     | Search documents       | `python3 .ontos/scripts/ontos_query.py`              |
| `scaffold`  | Generate scaffolds     | `python3 .ontos/scripts/ontos_scaffold.py`           |
| `stub`      | Create stub            | `python3 .ontos/scripts/ontos_stub.py`               |
| `promote`   | Promote documents      | `python3 .ontos/scripts/ontos_promote.py`            |
| `migrate`   | Migrate schema         | `python3 .ontos/scripts/ontos_migrate_schema.py`     |

### Examples

```bash
# Archive a feature session
ontos log -e feature

# Generate context map with strict validation
ontos map --strict

# Verify all stale documents
ontos verify --all

# Search for a concept
ontos query --concept caching

# Check graph health
ontos query --health
```

### 10.1 Environment Detection (v3.2)

The `env` command automatically detects project environment manifests (like `pyproject.toml` or `package.json`) and generates onboarding documentation.

```bash
# Preview detected manifests
ontos env

# preview in JSON format
ontos env --format json

# Write results to .ontos/environment.md
ontos env --write

# Overwrite existing environment.md
ontos env --write --force
```

**Supported Manifests:**
-   **Python:** `pyproject.toml` (Poetry/PDM/Pip), `requirements.txt`, `setup.py`, `environment.yml` (Conda)
-   **Node.js:** `package.json`
-   **Generic:** `.tool-versions` (asdf), `Makefile`, `Dockerfile`

### 10.2 Link Check (v3.3)

The `link-check` command scans all documents for broken references, duplicate IDs, and orphaned documents.

```bash
# Check for broken references
ontos link-check

# JSON output for CI
ontos link-check --json

# Limit scan scope
ontos link-check --scope docs
```

**Exit codes:**
| Code | Meaning |
|------|---------|
| `0`  | No issues found |
| `1`  | Broken references or duplicates detected |
| `2`  | Orphan-only findings (no broken references or duplicates) |

### 10.3 Rename (v3.3)

The `rename` command safely renames a document ID across the entire graph, updating all `depends_on` references.

```bash
# Dry-run (default) — preview changes without applying
ontos rename old_id new_id

# Apply the rename
ontos rename old_id new_id --apply

# JSON output
ontos rename old_id new_id --json
```

**Safety features:**
- Dry-run by default — requires `--apply` to write changes
- Collision detection — refuses to rename if `new_id` already exists
- Automatic `depends_on` propagation across all documents

---

## 11. Candidate Suggestions (v3.2)

Ontos v3.2 introduces intelligent candidate suggestions for broken references. When a document ID is referenced but not found, Ontos uses three strategies to find the intended target:

1.  **Substring Match:** Checks if the broken ID is a partial match for an existing ID.
2.  **Alias Match:** Matches against the `aliases` field in document frontmatter.
3.  **Fuzzy Match:** Uses Levenshtein distance for near-miss typos.

Suggestions appear in:
-   `ontos map` validation output
-   `ontos doctor` validation checks

Example output:
`❌ broken_doc: Broken dependency: 'auth_servidce' does not exist. Did you mean: auth_service?`

---

## 12. Scripts Reference

| Script | Purpose |
|--------|---------|
| `ontos_generate_context_map.py` | Build graph, validate, generate map |
| `ontos_end_session.py` | Create session log |
| `ontos_query.py` | Query the graph (deps, concepts, stale) |
| `ontos_maintain.py` | Run weekly maintenance workflow |
| `ontos_consolidate.py` | Consolidate old logs into history |
| `ontos_migrate_frontmatter.py` | Find untagged files |
| `ontos_pre_push_check.py` | Pre-push hook logic |
| `ontos_remove_frontmatter.py` | Strip YAML headers |
| `ontos_verify.py` | Mark documentation as current (v2.7) |

### Common flags
- `--quiet` / `-q` — Suppress output (global)
- `--version` / `-V` — Show version (global)
- `--strict` — Exit 1 on any issue (`map`)
- `--dry-run` — Preview without changes (`maintain`, `consolidate`, `schema-migrate`)

---

## 13. Documentation Staleness Tracking (v2.7)

Track when documentation becomes outdated after code changes.

### Adding Staleness Tracking

Add `describes` to your documentation frontmatter:

```yaml
---
id: my_readme
type: atom
describes:
  - cli_module
  - api_handler
describes_verified: 2025-12-19
---
```

### Checking for Stale Docs

Staleness is checked automatically:
- When generating context map (Section 5: Staleness Audit)
- When archiving sessions (Archive Ontos warning)

### Marking Documentation Current

After reviewing and updating your docs:

```bash
# Single file
ontos verify docs/readme.md

# All stale docs interactively
ontos verify --all
```

### Example: Documentation Chain

```yaml
# Manual describes scripts
# docs/reference/Ontos_Manual.md
describes:
  - ontos_end_session
  - ontos_verify
describes_verified: 2025-12-19

# Agent Instructions describes Manual
# docs/reference/Ontos_Agent_Instructions.md
describes:
  - ontos_manual
describes_verified: 2025-12-19
```

---

## 14. Advanced Topics

### Schema Versioning (v2.9+)

Ontos v2.9 introduces explicit schema versioning to support future upgrades.

- **v1.0**: Legacy (ID only)
- **v2.0**: Standard (ID + Type)
- **v2.1**: Staleness tracking (describes)
- **v2.2**: Curation levels (curation_level, ontos_schema)
- **v3.0**: Future (Typed edges)

To check your documents:
```bash
ontos migrate --check
```
