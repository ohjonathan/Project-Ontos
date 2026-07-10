---
id: ontos_manual
type: kernel
status: active
depends_on: []
---

# Ontos Manual v4.7

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

```bash
# Install with MCP server support (Python 3.10+)
pip install 'ontos[mcp]'
ontos serve
```

> **v4.7 Note:** v4.0 added MCP server mode for native AI IDE integration. v4.1 added write tools, portfolio index, and advisory flock locking. v4.2 added Cursor MCP onboarding plus `print-config` fallback for the remaining supported client surfaces. v4.3 adds `ontos retrofit --obsidian`, the dry-run-first write path that lands computed `tags` and `aliases` in on-disk frontmatter for Obsidian. v4.4 adds agentic activation. v4.5 widens lifecycle artifact tagging and hardens activation diagnostics. v4.6 makes CLI `activate --json` validation metadata match MCP. v4.7 groups activation warnings by default, wraps `link-check --json` in the standard envelope with output controls and ~200x faster scans, adds the `allowed_external_dependency_paths` allowlist, and makes health counts consistent (and basis-labeled) across doctor/activate/query/link-check. See the [Migration Guide v3→v4](Migration_v3_to_v4.md). For v2.x users, see [Migration v2→v3](Migration_v2_to_v3.md).

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
| `reference` | 5 | Reference material outside the core hierarchy |
| `concept` | 5 | Vocabulary, taxonomy, or glossary material |
| `handoff` | 5 | Agent or maintainer handoff packet |
| `tracker` | 5 | Workstream, issue, or release gate tracker |
| `retro` | 5 | Retrospective or lessons-learned record |
| `review` | 5 | Peer, alignment, adversarial, or verification review |
| `spec` | 5 | Implementation or behavior specification |
| `report` | 5 | Final report, status report, or synthesis |
| `adr` | 5 | Architecture decision record |
| `policy` | 5 | Policy, rule, or operating constraint |

**Rule:** Dependencies flow DOWN. Atoms depend on products, not vice versa.
Rank-5 documents are lifecycle/support artifacts: they are valid Ontos
documents, but they do not participate in the core kernel-to-atom hierarchy.

### Frontmatter Schema

```yaml
---
id: unique_snake_case      # Required. Never change.
type: atom                  # Required. See Document Types above.
status: active              # Optional. See Status Values below.
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
1. Run `ontos activate` or call the MCP `activate` tool
2. Read `Ontos_Context_Map.md`
3. Load relevant files based on your request
    print("Loaded: [id1, id2]")

`ontos activate --json` returns `usable`, `usable_with_warnings`, or `not_usable`. Warnings are non-blocking when the command can still produce actionable context. Since v4.7 warnings are grouped by rule by default (`warning_groups` with counts and bounded samples); use `--warnings full` for inline records, `--warning-rule <rule_id>` to filter, and `--limit N` to cap inline output. The MCP equivalent pages full records through the `list_validation_warnings` tool.
    
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

Frontmatter-focused maintenance:
```bash
ontos doctor --frontmatter
ontos maintain --fix-frontmatter-enums --dry-run
ontos maintain --fix-frontmatter-enums --apply
```

`doctor --frontmatter` reports exact path, line, field, observed value, allowed values, severity, blocking status, and suggested fix for invalid `type` / `status` frontmatter. The repair command preserves old values as `original_type` or `original_status` when applying known lifecycle-artifact mappings.

Scan exclusions are shared across `map`, `doctor`, `verify --all`, and frontmatter repair. Use absolute-style patterns such as `*/docs/reviews/*` to exclude generated review artifacts regardless of workspace location.

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

### Status Values (v4.7)
| Status | Meaning |
|--------|---------|
| `draft` | Work in progress |
| `active` | Current truth (approved, in use) |
| `deprecated` | Past truth (superseded) |
| `archived` | Historical record (logs) |
| `rejected` | Considered but NOT approved |
| `complete` | Finished work (reviews) |
| `completed` | Finished work, preserved as a common lifecycle variant |
| `auto-generated` | Generated by automation |
| `scaffold` | Auto-generated placeholder awaiting curation |
| `pending_curation` | Known document that still needs human curation |
| `in_progress` | Work actively underway |
| `proposed` | Proposal or lifecycle artifact awaiting approval |
| `ready` | Handoff or review packet ready for the next phase |
| `revised` | Updated after review or correction |
| `in-lifecycle` | Managed by a lifecycle/review process |

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
- Python 3.9+ (3.10+ for MCP server features)
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

### MCP Server Install (v4.0)

To enable MCP server mode for IDE integration:

```bash
pip install 'ontos[mcp]'
```

This adds `mcp>=1.27.0` and `pydantic>=2.0` as dependencies. Python 3.10+ is required.

For pipx users (fresh install):
```bash
pipx install 'ontos[mcp]'
```

If you already have `ontos` installed via pipx, reinstall with the extra:
```bash
pipx install --force 'ontos[mcp]'
```

### Upgrading

- **From v3.x:** See the [Migration Guide v3→v4](Migration_v3_to_v4.md) for what's new.
- **From v2.x:** See the [Migration Guide v2→v3](Migration_v2_to_v3.md) for step-by-step instructions.

#### Restarting MCP hosts after upgrade

Long-lived MCP hosts (Claude Code, Cursor, Antigravity) spawn `ontos serve` once and keep that child process alive across upgrades. After any of:

```bash
pipx upgrade ontos
pip install --upgrade ontos
pipx install --force 'ontos[mcp]'
```

**restart the MCP host** (or reload the Ontos plugin) so it picks up the new version. Until the host process is recycled, MCP `health` responses and `serverInfo.version` will continue reporting the old version.

Verify the new binary independently with a fresh CLI invocation — each CLI run is its own process, so `ontos --version` reflects the upgrade immediately:

```bash
ontos --version
ontos serve --workspace . --read-only   # fresh child reports new serverInfo.version
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
| `retrofit`  | Sync Obsidian frontmatter | (New in v4.3)                                      |
| `consolidate` | Archive old logs     | `python3 .ontos/scripts/ontos_consolidate.py`        |
| `query`     | Search documents       | `python3 .ontos/scripts/ontos_query.py`              |
| `scaffold`  | Generate scaffolds     | `python3 .ontos/scripts/ontos_scaffold.py`           |
| `stub`      | Create stub            | `python3 .ontos/scripts/ontos_stub.py`               |
| `promote`   | Promote documents      | `python3 .ontos/scripts/ontos_promote.py`            |
| `migrate`   | Migrate schema         | `python3 .ontos/scripts/ontos_migrate_schema.py`     |
| `serve`     | Start MCP server       | (New in v4.0)                                         |

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

# Preview Obsidian frontmatter retrofit
ontos retrofit --obsidian
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

### 10.2 Link Check (v3.3, expanded v4.7)

The `link-check` command scans all documents for broken references, duplicate IDs, and orphaned documents.

```bash
# Check for broken references
ontos link-check

# JSON output for CI (standard envelope since v4.7; counts under .data.summary)
ontos link-check --json

# Limit scan scope
ontos link-check --scope docs

# v4.7 output controls
ontos link-check --summary            # counters only, skips suggestions
ontos link-check --limit 20           # cap each findings list (JSON and human)
ontos link-check --no-suggestions     # skip fix-suggestion generation
ontos link-check --frontmatter-only   # skip body reference scanning
ontos link-check --no-orphans         # skip orphan detection (removes exit 3)
```

Since v4.7 the JSON output uses the standard command envelope: top-level
`status` is transport status, result quality lives in `data.result_status`
(`clean` | `warnings` | `incomplete` | `failing`), and per-phase timings
appear under `data.timings_ms`. Since schema 4.0, usage and diagnostic outcomes
use distinct exit codes.

`depends_on` entries that resolve to real files outside the doc scope are
reported under `data.file_dependencies` instead of broken references. Mark
intentional doc-to-file edges with workspace-relative globs:

```toml
[validation]
allowed_external_dependency_paths = ["apps/**", "manifests/**"]
```

Allowlisted entries become info-severity `external_file_dependency` records
and never affect exit codes; unallowlisted ones keep the historical exit-1
behavior.

**Exit codes:**
| Code | Meaning |
|------|---------|
| `0`  | No issues found |
| `1`  | Broken references, duplicates, or unallowlisted file dependencies detected |
| `3`  | Orphan-only warnings (no broken references or duplicates) |

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

### 10.4 Retrofit (v4.3)

The `retrofit` command writes canonical Obsidian-facing frontmatter into existing documents so vaults can browse Ontos-managed docs without hand-editing every file. It computes `tags` from `concepts` and `aliases` from explicit aliases plus an ID-derived alias, then inserts, replaces, removes stale blocks, or no-ops depending on drift.

```bash
# Dry-run (default)
ontos retrofit --obsidian

# Apply frontmatter updates
ontos retrofit --obsidian --apply

# Include .ontos-internal documents
ontos retrofit --obsidian --scope library

# JSON output
ontos retrofit --obsidian --json
```

**Safety features:**
- Dry-run by default — requires `--apply` to write changes
- Clean-git check before apply — writes only when the worktree is clean
- Blocking warnings for unpatchable frontmatter — batch apply aborts rather than partially writing
- Surgical field updates — preserves unrelated frontmatter and removes stale `tags` / `aliases` blocks when canonical values are empty

### 10.5 MCP Server Mode (v4.0)

The `serve` command starts a stdio MCP server that exposes the Ontos knowledge graph to AI agents and IDEs via the Model Context Protocol.

#### Starting the Server

```bash
ontos serve                    # Serve current directory
ontos serve --workspace /path  # Serve a specific project
```

The server runs in the foreground and communicates via stdin/stdout. Press Ctrl+C to stop.

#### IDE Configuration

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "ontos": {
      "command": "ontos",
      "args": ["serve"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

**Cursor** (`.cursor/mcp.json` in your project):
```json
{
  "mcpServers": {
    "ontos": {
      "command": "ontos",
      "args": ["serve"]
    }
  }
}
```

**Antigravity native agents** (`~/.gemini/antigravity/mcp_config.json`):

```bash
ontos mcp install --client antigravity
```

Ontos writes or updates `mcpServers.ontos` in the native Antigravity config:

```json
{
  "mcpServers": {
    "ontos": {
      "command": "/absolute/path/to/ontos",
      "args": ["serve", "--workspace", "/absolute/path/to/your/project", "--read-only"]
    }
  }
}
```

Use `--write-enabled` to expose mutable MCP tools. This native config is separate from repo-local instruction artifacts such as `AGENTS.md` and `.cursorrules`.

**Cursor** (`.cursor/mcp.json` in your project, `~/.cursor/mcp.json` for user scope):

```bash
ontos mcp install --client cursor --scope project
ontos mcp install --client cursor --scope user
ontos mcp uninstall --client cursor --scope project
ontos mcp print-config --client codex
```

Rerunning `ontos mcp install --client cursor ...` refreshes the launcher path if Ontos moves on your shell `PATH`. Managed install, uninstall, and doctor support remain POSIX-only in `v4.7`; Windows users should use `print-config`.

#### Client Support Policy

Ontos treats MCP support as two layers:

- **Server health** — `ontos serve` is healthy and answers MCP requests.
- **Client onboarding** — the client actually discovers Ontos tools through its own config format.

Apply the same philosophy across clients, but not the same installer blindly:

- **First-class** clients have a stable native config contract, so Ontos can ship `ontos mcp install --client ...`, `ontos mcp uninstall --client ...`, and `ontos doctor` validation. Antigravity and Cursor currently fit here in `v4.7`.
- **Print-config only** clients get a copy-pastable config document but no managed install / doctor promises in `v4.7`. Claude Code, Codex, and VS Code currently fit here.
- **Docs-only** clients stay manual in this release. Claude Desktop and Windsurf currently fit here.

The managed MCP client config is separate from repo-local instruction artifacts such as `AGENTS.md` and `.cursorrules`.

#### Available Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `activate` | Mandatory best-effort session activation with loaded IDs and warnings | `workspace_id` |
| `workspace_overview` | Structured orientation — key documents, graph stats, top warnings | — |
| `context_map` | Full context map markdown | `compact`: basic, rich, tiered, or full |
| `get_document` | Read one document with full frontmatter and metadata | `document_id` or `path`, `include_content` |
| `list_documents` | Paginated listing of canonical documents | `type`, `status`, `offset`, `limit` |
| `list_validation_warnings` | Paginated full validation warning records (v4.7) | `rule_id`, `severity`, `offset`, `limit` |
| `export_graph` | Structured graph export (nodes, edges, summary) | `summary_only`, `export_to_file` |
| `query` | Dependency details for a single document | `entity_id` |
| `health` | Server uptime, document count, index freshness | — |
| `refresh` | Force cache rebuild | — |
| `get_context_bundle` | Token-budgeted context bundle for a workspace | `workspace_id`, `token_budget` |

#### Portfolio Tools (v4.1)

When the server runs with `--portfolio`, it also registers:

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `project_registry` | Inventory of all indexed workspaces | `workspace_id` |
| `search` | FTS5 full-text search across portfolio documents | `query_string`, `workspace_id`, `offset`, `limit` |

#### Write Tools (v4.1)

When the server runs without `--read-only`, it also registers:

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `scaffold_document` | Create a new markdown document with scaffold frontmatter | `path`, `content`, `workspace_id` |
| `log_session` | Create a dated log entry in the workspace logs directory | `title`, `event_type`, `source`, `branch`, `body`, `workspace_id` |
| `session_end` | Create a structured session-end log | `title`, `goal`, `key_decisions`, `alternatives_considered`, `impacts`, `testing`, `workspace_id` |
| `promote_document` | Change a document `curation_level` without renaming or moving it | `document_id`, `new_level`, `workspace_id` |
| `rename_document` | Rename one document ID and rewrite references across the served workspace | `document_id`, `new_id`, `workspace_id` |

Write-tool contracts:
- `read_only=True` omits write tools from discovery.
- `workspace_id` is optional and defaults to the served workspace.
- In read-only mode, archive with the CLI fallback `ontos log -e "slug"`.
- Cross-workspace writes are not supported; start a separate `ontos serve` in the target workspace.
- `rename_document` always uses library scope.

All tools return structured JSON. Start with `activate`; if a read tool is used first, the response includes `_ontos_warning` reminding the agent to activate the session.

#### Cache Behavior

The server uses file-mtime fingerprinting to detect document changes automatically. On each tool call, it compares `(path, st_mtime_ns, st_size)` fingerprints against the cached state. If any file has changed, the snapshot is rebuilt transparently.

Use `refresh` to force a manual cache rebuild after bulk changes (e.g., `git pull`).

#### Configuration

Add an optional `[mcp]` section to `.ontos.toml`:

```toml
[mcp]
usage_logging = true                              # Log tool invocations
usage_log_path = "~/.config/ontos/usage.jsonl"    # Default path
```

No document content is logged — only tool names and timestamps.

#### Limitations (v4.1)

- **Single workspace per server** — One `ontos serve` process per project
- **No cross-workspace writes** — Write tools target the served workspace only
- **Stdio transport only** — HTTP/SSE transport deferred to a future release
- **Python 3.10+** required — Install with `pip install 'ontos[mcp]'`

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
- `--strict` — Exit 3 when `map` has warnings but no errors
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
