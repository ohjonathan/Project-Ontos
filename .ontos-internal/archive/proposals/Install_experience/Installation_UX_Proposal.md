---
id: installation_ux_proposal
type: strategy
status: draft
depends_on: [philosophy, mission]
concepts: [ux, installation, dx, onboarding]
---

# Installation UX Proposal

**Author:** Claude (Opus 4.5)
**Date:** 2025-12-19
**Revised:** 2025-12-19 (Post Multi-LLM Review)
**Status:** Draft for v3.0 Planning
**Related:** Ontos_Installation_Experience_Report.md, Architect_Synthesis_InstallUX.md

---

## Executive Summary

The current Ontos installation experience requires **7+ manual steps**, **multiple file copy operations from different source locations**, and **post-installation commands that should be automatic**. This friction directly contradicts Ontos's mission to reduce cognitive load and provide persistent context.

This proposal documents the problems in detail and outlines a two-phase solution:

1. **v2.x Quick Fixes** — Documentation corrections, discoverability improvements, and essential scripts that can ship incrementally without breaking changes.

2. **v3.0 Infrastructure Redesign** — A proper `ontos` CLI tool distributed via PyPI that achieves single-command installation rivaling modern developer tools.

---

# SECTION I: CURRENT STATE & PROBLEM ANALYSIS

This section thoroughly documents the friction, issues, and problems with the current installation experience. Understanding these problems is essential context for the v3.0 strategy.

---

## 1. The Installation Experience Today

### 1.1 What Users Must Do (Step-by-Step)

Based on the Installation Experience Report and current documentation, here is the complete installation journey:

#### Step 1: Clone the Ontos Repository
```bash
git clone https://github.com/ohjona/Project-Ontos.git /tmp/Project-Ontos
```
**Friction:** Low — standard git operation.

#### Step 2: Identify Files to Copy
**Friction:** HIGH — There is no manifest file listing what to copy. Users must manually inspect the repository structure.

The user must somehow discover they need to copy:
- `.ontos/` folder
- `ontos_init.py`
- `docs/reference/Ontos_Agent_Instructions.md`
- `.ontos-internal/reference/Common_Concepts.md` OR `docs/reference/Common_Concepts.md` (unclear which!)

**Evidence from Experience Report:**
> "Required `ls -la` commands to understand what to copy... there was no canonical list of required files."

#### Step 3: Copy Core Tooling
```bash
cp -r /tmp/Project-Ontos/.ontos /path/to/my-project/
cp /tmp/Project-Ontos/ontos_init.py /path/to/my-project/
```
**Friction:** Medium — Manual copy, but straightforward once files are identified.

#### Step 4: Copy Documentation Files
```bash
mkdir -p docs/reference
cp /tmp/Project-Ontos/docs/reference/Ontos_Agent_Instructions.md docs/reference/
cp /tmp/Project-Ontos/.ontos-internal/reference/Common_Concepts.md docs/reference/
```
**Friction:** HIGH — Files come from DIFFERENT source locations:
- Agent instructions: `docs/reference/`
- Common concepts: `.ontos-internal/reference/` (NOT `docs/reference/`!)

**Evidence from Experience Report:**
> "The repo had `Common_Concepts.md` in TWO locations... An installer doesn't know which is authoritative. The stub version in `docs/reference/` appears to be a simplified copy, but this isn't documented anywhere."

#### Step 5: Run Initialization Script
```bash
python3 ontos_init.py
```
**Friction:** CRITICAL — The script requires interactive input with no clear documentation of what will be asked.

**Evidence from Experience Report — Three Failed Attempts:**

**Attempt 1: FAILED**
```bash
python3 ontos_init.py
# Result: EOFError: EOF when reading a line
```
> "Script requires interactive input but was run non-interactively."

**Attempt 2: FAILED**
```bash
echo "2" | python3 ontos_init.py
# Result: EOFError: EOF when reading a line
```
> "Script requires MULTIPLE inputs... The first `input()` consumed the '2', then the second `input()` hit EOF."

**Attempt 3: SUCCESS**
```bash
printf "2\nClaude\n" | python3 ontos_init.py
```

**Root Cause:** The `--non-interactive` flag EXISTS but is not discoverable. The `--help` output does not show:
- How many inputs are required
- What order they're asked in
- What valid values are

#### Step 6: "Initiate Ontos" (Post-Installation)
After `ontos_init.py` completes, users are expected to "Initiate Ontos" — but this is NOT a command. It's a **6-step manual process** documented in prose:

From `Ontos_Agent_Instructions.md`:
```markdown
### "Ontos" (Activate)
1. Check for `Ontos_Context_Map.md`
2. If missing: `python3 .ontos/scripts/ontos_generate_context_map.py`
3. Read map, identify relevant IDs for user's request
4. Check consolidation status (prompted/advisory modes only)
5. Read ONLY those files
6. print("Loaded: [id1, id2]")
```

**Friction:** HIGH — Users expect a command to run. Instead, they get instructions to follow manually.

**Evidence from Experience Report:**
> "Command not self-evident — Had to read `Ontos_Agent_Instructions.md` to understand what 'Initiate Ontos' means... This should be a single command: `python3 .ontos/scripts/ontos_activate.py`"

#### Step 7: "Migrate Ontos" (If Existing Docs)
If the project has existing markdown documentation, users should "Migrate Ontos" — but this is ambiguous.

Multiple migration scripts exist:
- `ontos_migrate_frontmatter.py` — for untagged files
- `ontos_migrate_v2.py` — for v1→v2 schema

**Friction:** HIGH — Users don't know which script to run, or if they should run both.

**Evidence from Experience Report:**
> "No 'migrate' command documented — Had to explore `.ontos/scripts/` directory to find migration scripts... Multiple migration scripts with unclear purposes."

---

### 1.2 Summary: Installation Friction Map

| Step | Action | Friction Level | Root Cause |
|------|--------|----------------|------------|
| 1 | Clone repo | Low | Standard git |
| 2 | Identify files to copy | **HIGH** | No manifest, no clear list |
| 3 | Copy `.ontos/` and `ontos_init.py` | Medium | Manual but straightforward |
| 4 | Copy docs from different locations | **HIGH** | Files scattered across repo |
| 5 | Run `ontos_init.py` | **CRITICAL** | Interactive prompts not documented, `--non-interactive` not discoverable |
| 6 | "Initiate Ontos" | **HIGH** | Not a script, 6 manual steps |
| 7 | "Migrate Ontos" | **HIGH** | Ambiguous, multiple scripts |

**Total: 7+ steps with 5 high-friction points.**

---

## 2. Specific Problems Documented

### 2.1 Problem: Duplicate Files with Different Content

**Location of Issue:** `Common_Concepts.md`

**Current State:**
```
/docs/reference/Common_Concepts.md          (~430 bytes, STUB)
/.ontos-internal/reference/Common_Concepts.md  (~2,627 bytes, FULL VERSION)
```

**Impact:**
- Users don't know which file is authoritative
- If they copy the wrong one, they get incomplete vocabulary
- Creates confusion about what `.ontos-internal/` is for

**Evidence:**
> "Why this is bad: An installer doesn't know which is authoritative."

---

### 2.2 Problem: Uninstall Documentation Is Wrong

**Location of Issue:** `Ontos_Manual.md`, Section 4 (Installation)

**Current Documentation:**
```bash
rm -rf .ontos/
rm -f Ontos_Context_Map.md Ontos_Agent_Instructions.md
python3 .ontos/scripts/ontos_remove_frontmatter.py --yes
```

**Why This Is Broken:**
- Line 1 deletes `.ontos/`
- Line 3 tries to run a script FROM `.ontos/` — but it was just deleted!

**Additional Missing Steps:**
- `ontos_init.py` not mentioned
- `ontos_config.py` not mentioned
- Git hooks (`.git/hooks/pre-push`, `.git/hooks/pre-commit`) not mentioned
- Created directories (`docs/logs`, `docs/strategy`, etc.) not mentioned

---

### 2.3 Problem: `--non-interactive` Flag Exists But Is Not Discoverable

**Location of Issue:** `ontos_init.py`

**Current `--help` Output:**
```
usage: ontos_init.py [-h] [--reconfig] [--non-interactive]
                     [--mode {automated,prompted,advisory}] [--source SOURCE]

Initialize or reconfigure Project Ontos
```

**What's Missing:**
1. No indication that interactive mode asks 2 questions
2. No examples of non-interactive usage
3. No explanation of what each mode does
4. No "quick start" guidance

**Impact:**
- AI agents (and CI/CD pipelines) can't figure out how to automate installation
- Users attempt interactive mode in non-TTY environments and fail
- 3 failed attempts documented in Experience Report before success

---

### 2.4 Problem: Files Created Without Warning or Preview

**User Complaint:**
> "errors to a lot of different files being generated in the existing folder"

**What `ontos_init.py` Creates:**
```
project-root/
├── ontos_config.py              # Generated config
├── Ontos_Context_Map.md         # Generated context map
├── .git/hooks/
│   ├── pre-push                 # Git hook (may conflict!)
│   └── pre-commit               # Git hook (may conflict!)
└── docs/
    ├── logs/                    # New directory
    ├── strategy/
    │   ├── proposals/           # New directory
    │   └── decision_history.md  # New file
    ├── archive/
    │   ├── logs/                # New directory
    │   └── proposals/           # New directory
    └── reference/
        └── Common_Concepts.md   # New file
```

**Impact:**
- Users with existing `docs/` get unexpected subdirectories
- Users with existing git hooks may have them overwritten
- No preview of what will be created before it happens
- No way to "dry run" the installation

---

### 2.5 Problem: Post-Installation Commands Are Not Commands

**"Initiate Ontos"** is not a command — it's 6 steps documented in Agent Instructions that the AI agent must perform manually.

**"Migrate Ontos"** is not a command — it's an ambiguous reference to one of several migration scripts.

**"Archive Ontos"** is a command (`ontos_end_session.py`) — this works correctly.

**"Maintain Ontos"** is a command (`ontos_maintain.py`) — this works correctly.

**Impact:**
- Inconsistent UX: some "commands" are scripts, others are procedures
- Confusion about what to do after installation
- Extra friction before the user gets value from Ontos

---

### 2.6 Problem: No Single Source of Truth for Installation

**Files needed for installation are scattered:**

| File | Location | Purpose |
|------|----------|---------|
| `.ontos/` | Root | Core tooling |
| `ontos_init.py` | Root | Initialization script |
| `Ontos_Agent_Instructions.md` | `docs/reference/` | Agent protocol |
| `Common_Concepts.md` (full) | `.ontos-internal/reference/` | Tag vocabulary |
| `Common_Concepts.md` (stub) | `docs/reference/` | ??? |

**Impact:**
- No `install.sh` or manifest to automate copying
- Users must read documentation to know what to copy
- Easy to miss files or copy from wrong location

---

## 3. Comparison with Industry Standards

### 3.1 Installation Command Count

| Tool | Installation | Post-Install | Total |
|------|--------------|--------------|-------|
| **create-react-app** | `npx create-react-app my-app` | None | **1** |
| **Vite** | `npm create vite@latest` | None | **1** |
| **pre-commit** | `pipx install pre-commit && pre-commit install` | None | **2** |
| **Husky** | `npx husky-init && npm install` | None | **2** |
| **ESLint** | `npm init @eslint/config` | None | **1** |
| **Ontos (current)** | 7+ manual steps | "Initiate", "Migrate" | **10+** |

### 3.2 Key Patterns Ontos Is Missing

| Pattern | Industry Standard | Ontos Current State |
|---------|-------------------|---------------------|
| Single entry point | `npx`, `pipx install`, `curl \| bash` | Copy 4+ items manually |
| Interactive by default, scriptable by flag | `--yes`, `--non-interactive` | Flag exists but not discoverable |
| Preview before changes | `--dry-run` | Not available |
| Graceful conflict handling | Detect, backup, merge options | Overwrites without warning |
| Immediate value | Works right after install | Requires "Initiate Ontos" manually |
| Idempotent | Re-running is safe | Untested behavior |

---

## 4. User Personas and Their Pain Points

### 4.1 Solo Developer (Target User)

**Goal:** Set up Ontos in a personal project quickly.

**Current Pain:**
- Must read documentation to understand what to copy
- Trial-and-error with `ontos_init.py` interactive prompts
- Confused by "Initiate Ontos" not being a script
- ~15 minutes to working state

**Expected Experience:**
- One command to install
- Works immediately
- <1 minute to working state

### 4.2 AI Agent (Primary User)

**Goal:** Install Ontos programmatically when instructed by user.

**Current Pain:**
- Can't discover `--non-interactive` flag without reading source
- Fails with `EOFError` when running non-interactively
- Must perform 6-step "Initiate Ontos" manually
- Documentation says "Migrate Ontos" but doesn't specify which script

**Expected Experience:**
- Clear flags in `--help` for scripted installation
- Single script to activate context
- Unified migration command

### 4.3 Team Lead (Enterprise User)

**Goal:** Set up Ontos for a team with consistent configuration.

**Current Pain:**
- No way to version-pin Ontos installation
- No checksum verification for security
- Hook conflicts not handled gracefully
- No "dry run" to preview changes before applying

**Expected Experience:**
- Version pinning (`--version=2.8`)
- Checksum verification
- Conflict detection with backup options
- Dry run mode

---

## 5. Impact Assessment

### 5.1 Adoption Impact

The installation friction directly impacts Ontos adoption:

| Friction Point | Drop-off Risk | Evidence |
|----------------|---------------|----------|
| 7+ manual steps | High | Users expect 1-2 commands |
| `EOFError` on first attempt | High | Experience Report: 3 attempts needed |
| "Initiate Ontos" confusion | Medium | Not obvious it's not a script |
| Unexpected file creation | Medium | User complaint about files |
| Wrong uninstall docs | Low | Only affects uninstall |

### 5.2 Mission Alignment

**Ontos Mission:** "Eliminate context death in AI-assisted development."

**Installation Friction Contradiction:**
- Ontos promises to reduce cognitive load
- But installation ADDS cognitive load
- First impression is friction, not flow

---

## 6. Root Cause Analysis

| Problem | Surface Issue | Root Cause |
|---------|---------------|------------|
| Can't automate installation | `--non-interactive` not discoverable | Poor `--help` documentation |
| Files from multiple locations | User must copy from 3+ places | No single source / no manifest |
| "Initiate Ontos" not a script | 6 manual steps | Missing `ontos_activate.py` |
| "Migrate Ontos" ambiguous | Multiple scripts, unclear which | Missing unified `ontos_migrate.py` |
| Duplicate Common_Concepts.md | Two versions exist | Design debt, not cleaned up |
| Wrong uninstall order | Docs say delete .ontos first | Documentation error |
| No preview mode | Files created without warning | Missing `--dry-run` flag |

---

# SECTION II: PROPOSED SOLUTIONS

## 7. Solution Strategy

Based on the problem analysis, we propose a two-phase approach:

### Phase 1: v2.x Quick Fixes
Fix documentation, add discoverability, create essential scripts. These changes:
- Require no new infrastructure
- Can ship incrementally
- Address highest-friction issues immediately

### Phase 2: v3.0 Infrastructure
Build a proper CLI tool with PyPI distribution. This change:
- Achieves single-command installation
- Matches industry standards
- Requires significant development investment

---

## 8. v2.x Quick Fixes (Detailed)

### 8.1 v2.8: Documentation & Discoverability

#### 8.1.1 Fix Uninstall Documentation

**File:** `docs/reference/Ontos_Manual.md`

**Current (BROKEN):**
```bash
rm -rf .ontos/
rm -f Ontos_Context_Map.md Ontos_Agent_Instructions.md
python3 .ontos/scripts/ontos_remove_frontmatter.py --yes
```

**Fixed:**
```bash
# 1. Remove frontmatter FIRST (requires .ontos/)
python3 .ontos/scripts/ontos_remove_frontmatter.py --yes

# 2. Remove git hooks
rm -f .git/hooks/pre-push .git/hooks/pre-commit

# 3. Remove Ontos files
rm -rf .ontos/
rm -f Ontos_Context_Map.md ontos_init.py ontos_config.py

# 4. Optionally remove created directories
rm -rf docs/logs docs/archive docs/strategy/proposals
```

**Effort:** 10 minutes | **Impact:** High

---

#### 8.1.2 Delete Duplicate `Common_Concepts.md`

**Action:** Delete `/docs/reference/Common_Concepts.md` (the stub version)

**Keep:** `/.ontos/templates/common_concepts_template.md` as single source of truth

**Update:** `ontos_init.py` to copy from templates, not from docs

**Effort:** 5 minutes | **Impact:** Medium

---

#### 8.1.3 Improve `--help` Output

**File:** `ontos_init.py`

**New `--help` output:**
```
usage: ontos_init.py [-h] [--reconfig] [--non-interactive] [--dry-run]
                     [--mode {automated,prompted,advisory}] [--source SOURCE]

Initialize Project Ontos in your repository.

QUICK START:
  python3 ontos_init.py                    # Interactive wizard (2 prompts)
  python3 ontos_init.py --non-interactive  # Use defaults (prompted mode)
  python3 ontos_init.py --dry-run          # Preview what will be created

OPTIONS:
  -h, --help            Show this help message and exit
  --reconfig            Reconfigure existing installation
  --non-interactive     Skip prompts, use defaults or --mode/--source values
  --dry-run             Show what would be created without making changes
  --mode MODE           Workflow mode (default: prompted)
                          automated - Zero friction, auto-archives on push
                          prompted  - Guides you, blocks push until archived
                          advisory  - Warnings only, maximum flexibility
  --source NAME         Your name for log attribution (e.g., "Claude Code")

INTERACTIVE MODE:
  Without --non-interactive, you'll be asked:
    1. Choose workflow mode [1-3]
    2. Enter your name for logs (optional)

EXAMPLES:
  # Developer workstation (interactive)
  python3 ontos_init.py

  # CI/CD pipeline (non-interactive)
  python3 ontos_init.py --non-interactive --mode=automated --source="GitHub Actions"

  # Preview before installing
  python3 ontos_init.py --dry-run

  # Reconfigure existing installation
  python3 ontos_init.py --reconfig --mode=advisory
```

**Effort:** 30 minutes | **Impact:** High

---

#### 8.1.4 Add `--dry-run` Flag

**File:** `ontos_init.py`

**Behavior:** Show what would be created without making changes.

**Output Example:**
```
DRY RUN: The following would be created:

Directories:
  [CREATE] docs/logs/
  [CREATE] docs/strategy/
  [CREATE] docs/strategy/proposals/
  [CREATE] docs/archive/
  [CREATE] docs/archive/logs/
  [CREATE] docs/archive/proposals/
  [exists] docs/reference/

Files:
  [CREATE] ontos_config.py — Configuration file
  [CREATE] Ontos_Context_Map.md — Knowledge graph
  [CREATE] docs/strategy/decision_history.md — Decision ledger
  [CREATE] docs/reference/Common_Concepts.md — Tag vocabulary

Git Hooks:
  [CREATE] .git/hooks/pre-push
  [CONFLICT] .git/hooks/pre-commit — Existing hook detected

No changes made. Run without --dry-run to proceed.
```

**Effort:** 1 hour | **Impact:** Medium

---

#### 8.1.5 Create `ontos_activate.py`

**Purpose:** Replace the 6-step manual "Initiate Ontos" command with a single script.

**File:** `.ontos/scripts/ontos_activate.py`

**Usage:**
```bash
python3 .ontos/scripts/ontos_activate.py
# Output: Loaded: [mission, ontos_manual, v2_strategy]. Context: 8,500 tokens across 12 documents.
```

**What It Does:**
1. Check for `Ontos_Context_Map.md` — generate if missing
2. Check consolidation status — warn if needed
3. Parse context map — extract document metadata
4. Output loaded IDs — for agent consumption

**Agent Instructions Update:**
```markdown
### "Ontos" (Activate)
Run: `python3 .ontos/scripts/ontos_activate.py`
```

**Effort:** 2 hours | **Impact:** High (eliminates highest post-install friction)

---

#### 8.1.6 Add Contributor Mode Detection

**File:** `ontos_init.py`

**Behavior:** Detect when running inside the Ontos repo itself and warn.

**Detection Logic:**
```python
if os.path.exists('.ontos-internal'):
    print("CONTRIBUTOR MODE DETECTED")
    print("You appear to be inside the Project Ontos repository itself.")
    # Prompt to continue or exit
```

**Effort:** 30 minutes | **Impact:** Low

---

### 8.2 v2.9: Streamlined Installation

#### 8.2.1 Create `install.sh` Bootstrap

**File:** `install.sh` (project root)

**Usage:**
```bash
# Basic installation
curl -fsSL https://raw.githubusercontent.com/ohjona/Project-Ontos/main/install.sh | bash

# With options
curl -fsSL https://raw.githubusercontent.com/ohjona/Project-Ontos/main/install.sh | bash -s -- --mode=automated --source="Claude"

# Dry run
curl -fsSL https://raw.githubusercontent.com/ohjona/Project-Ontos/main/install.sh | bash -s -- --dry-run
```

**What It Does:**
1. Clone Ontos repo to temp directory
2. Copy `.ontos/`, `ontos_init.py`, docs to target
3. Run `ontos_init.py` with passed arguments
4. Clean up temp directory

**Security:** Provide SHA256 checksum file for verification.

**Effort:** 3 hours | **Impact:** Medium

---

#### 8.2.2 Create Unified `ontos_migrate.py`

**File:** `.ontos/scripts/ontos_migrate.py`

**Usage:**
```bash
python3 .ontos/scripts/ontos_migrate.py              # Interactive menu
python3 .ontos/scripts/ontos_migrate.py --all        # Run all migrations
python3 .ontos/scripts/ontos_migrate.py --frontmatter  # Tag untagged files only
python3 .ontos/scripts/ontos_migrate.py --dry-run    # Preview only
```

**What It Does:**
- Combines `ontos_migrate_frontmatter.py` and `ontos_migrate_v2.py`
- Single entry point for all migration operations
- Interactive menu for users who don't know which to run

**Effort:** 2 hours | **Impact:** Medium

---

#### 8.2.3 Add Post-Install Summary

**Enhancement to `ontos_init.py`**

After successful installation, print:
```
═══════════════════════════════════════════════════════════════
  ONTOS INSTALLED SUCCESSFULLY
═══════════════════════════════════════════════════════════════

Configuration:
  Mode:   prompted
  Source: Claude

Files created:
  ontos_config.py          — Your configuration
  Ontos_Context_Map.md     — Knowledge graph
  docs/strategy/           — Strategic documents
  docs/logs/               — Session logs

Git hooks installed:
  .git/hooks/pre-push
  .git/hooks/pre-commit

Quick start:
  1. Tell your AI agent: "Ontos"
  2. At session end: "Archive Ontos"

To uninstall:
  python3 .ontos/scripts/ontos_remove_frontmatter.py --yes
  rm -rf .ontos/ ontos_config.py Ontos_Context_Map.md
```

**Effort:** 30 minutes | **Impact:** Medium

---

## 9. v3.0 Infrastructure (New Architecture)

### 9.1 Design Principles

1. **Single binary, multiple commands:** `ontos init`, `ontos activate`, `ontos archive`
2. **PyPI distribution:** `pipx install ontos` or `pip install ontos`
3. **Backward compatible:** v3.0 CLI can manage v2.x installations
4. **Offline-first:** Core functionality works without network
5. **Idempotent:** All commands safe to re-run
6. **Scriptable:** Every interactive prompt has a flag equivalent

### 9.2 Target Installation Experience

```bash
# Method 1: pipx (recommended)
pipx install ontos
ontos init

# Method 2: pip
pip install ontos
ontos init

# Method 3: curl | bash
curl -fsSL https://ontos.dev/install.sh | bash
```

**Comparison:**

| Metric | Current | v2.9 | v3.0 |
|--------|---------|------|------|
| Installation commands | 7+ | 4 | 1-2 |
| Post-install manual steps | 2+ | 0 | 0 |
| Time to working state | ~15 min | ~3 min | <1 min |

### 9.3 CLI Command Structure

```
$ ontos --help

Usage: ontos [OPTIONS] COMMAND [ARGS]...

  Ontos — Portable context for AI-assisted development.

Commands:
  init       Initialize Ontos in current directory.
  activate   Activate context (generate map, load IDs).
  archive    Create session log.
  maintain   Run maintenance tasks.
  migrate    Migrate existing documentation.
  query      Query the knowledge graph.
  update     Update Ontos to latest version.
  uninstall  Remove Ontos from current project.
  doctor     Diagnose installation issues.
```

### 9.4 Package Structure

```
ontos/                           # PyPI package
├── pyproject.toml
├── src/
│   └── ontos/
│       ├── __init__.py
│       ├── cli.py               # Main CLI (Click)
│       ├── commands/
│       │   ├── init.py
│       │   ├── activate.py
│       │   ├── archive.py
│       │   ├── maintain.py
│       │   ├── migrate.py
│       │   ├── query.py
│       │   ├── update.py
│       │   └── uninstall.py
│       ├── core/
│       │   ├── config.py
│       │   ├── context_map.py
│       │   ├── frontmatter.py
│       │   └── hooks.py
│       └── templates/
└── tests/
```

### 9.5 Key Command Specifications

#### `ontos init`

```
$ ontos init --help

Usage: ontos init [OPTIONS]

  Initialize Ontos in current directory.

Options:
  --mode [automated|prompted|advisory]  Workflow mode. [default: prompted]
  --source TEXT                         Your name for log attribution.
  --docs-dir PATH                       Documentation directory. [default: docs]
  --non-interactive                     Skip all prompts.
  --dry-run                             Preview changes without making them.
  --force                               Overwrite existing installation.
  --skip-hooks                          Don't install git hooks.
```

#### `ontos activate`

```
$ ontos activate --help

Usage: ontos activate [OPTIONS]

  Activate context (generate map, load IDs).

Options:
  --regenerate    Force regenerate context map.
  --json          Output as JSON.
  --quiet, -q     Minimal output.
```

#### `ontos uninstall`

```
$ ontos uninstall --help

Usage: ontos uninstall [OPTIONS]

  Remove Ontos from current project.

Options:
  --keep-docs        Keep documentation, only remove tooling.
  --keep-frontmatter Keep YAML frontmatter in files.
  --force            Skip confirmation prompt.
  --dry-run          Preview what would be removed.
```

### 9.6 Migration Path (v2.x → v3.0)

Users with existing v2.x installations need a smooth upgrade:

1. **Detection:** `ontos init` detects existing v2.x installation
2. **Backup:** Backs up `ontos_config.py` to `ontos_config.py.v2.backup`
3. **Remove obsolete:** Removes `ontos_init.py` (no longer needed)
4. **Update hooks:** Updates hooks to use new CLI
5. **Verify:** Prompts user to run `ontos doctor` to verify

---

## 10. Implementation Roadmap

### v2.8 Checklist
- [ ] Fix uninstall documentation in Ontos_Manual.md
- [ ] Delete duplicate `docs/reference/Common_Concepts.md`
- [ ] Improve `--help` output in `ontos_init.py`
- [ ] Add `--dry-run` flag to `ontos_init.py`
- [ ] Create `ontos_activate.py` script
- [ ] Add contributor mode detection
- [ ] Update README Quick Start

### v2.9 Checklist
- [ ] Create `install.sh` bootstrap script
- [ ] Create `install.sh.sha256` checksum
- [ ] Add idempotency to `ontos_init.py`
- [ ] Create unified `ontos_migrate.py`
- [ ] Add post-install summary
- [ ] Improve hook conflict messaging

### v3.0 Checklist
- [ ] Create Python package structure
- [ ] Implement `ontos` CLI with Click
- [ ] Implement all subcommands
- [ ] Create v2.x → v3.0 migration path
- [ ] Write comprehensive tests
- [ ] Publish to PyPI
- [ ] Update all documentation

---

## 11. Success Metrics

| Metric | Current | v2.9 Target | v3.0 Target |
|--------|---------|-------------|-------------|
| Installation commands | 7+ | 4 | 1-2 |
| Post-install manual steps | 2+ | 0 | 0 |
| Time to working state | ~15 min | ~3 min | <1 min |
| Documentation locations | 3 | 1 | 1 |
| Duplicate files | 1+ | 0 | 0 |
| User errors during install | Common | Rare | Very rare |
| Supported via PyPI | No | No | Yes |

---

## Appendix A: Evidence Sources

- **Ontos_Installation_Experience_Report.md** — Detailed installation walkthrough with friction points
- **Claude_InstallUX_Review.md** — Architectural review identifying over-engineering
- **Gemini_Review_Installation_UX_Proposal.md** — Supportive review with TOML/submodule suggestions
- **Installation_UX_Proposal_Review_Codex.md** — Security and platform concerns
- **Architect_Synthesis_InstallUX.md** — Synthesis of all reviews

## Appendix B: Research Sources

- [Using npx and npm scripts to Reduce the Burden of Developer Tools](https://dev.to/azure/using-npx-and-npm-scripts-to-reduce-the-burden-of-developer-tools-57f9)
- [pre-commit installation via pipx](https://pipx.pypa.io/stable/installation/)
- [Click documentation](https://click.palletsprojects.com/)
- [Python Packaging User Guide](https://packaging.python.org/)
