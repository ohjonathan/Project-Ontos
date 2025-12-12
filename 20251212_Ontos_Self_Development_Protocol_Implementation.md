# Project Ontos: Self-Development Protocol Implementation Plan

**Document Type:** Implementation Specification  
**Status:** Pending Review  
**Target Reviewers:** Gemini CLI, Claude Code, Codex  
**Author:** Claude (Anthropic) + Johnny  
**Date:** 2025-12-11  
**Revision:** 1.3 (incorporates Codex review: context-map ownership, cross-project safety, testing cadence)

---

## Executive Summary

This document specifies how to configure Project Ontos to manage its own development — "eating your own dogfood." The goal is to use Ontos's context management system while building Ontos v2.0, capturing the full decision history of the v2 development process.

**Key design decisions:**
- Use `.ontos-internal/` (hidden folder) for project documentation
- Add `.ontos-internal/` to default skip patterns for user safety
- **Smart conditional config** that detects its environment (Contributor vs User Mode)
- Separate user docs (`docs/`) from project docs (`.ontos-internal/`)

---

## Part 1: Context and Background

### 1.1 What is Project Ontos?

Project Ontos is a documentation system that creates structured knowledge graphs for AI-native development teams. It uses:

- **YAML frontmatter** on markdown files to define metadata (id, type, dependencies)
- **Python scripts** to generate context maps and validate the graph
- **A type hierarchy:** `kernel` → `strategy` → `product` → `atom`
- **Activation phrases** ("Ontos" to start, "Archive Ontos" to end sessions)

The output is a portable, git-tracked knowledge base that any AI agent can navigate.

### 1.2 The Problem: Self-Reference Conflict

The Ontos repository contains two kinds of documentation:

| Documentation Type | Purpose | Example Files |
|--------------------|---------|---------------|
| **User Documentation** | Teaches people how to USE Ontos | `docs/guides/Ontos_Installation_Guide.md`, `docs/reference/Ontos_Manual.md` |
| **Project Documentation** | Captures decisions about BUILDING Ontos | Currently doesn't exist in structured form |

Currently, all documentation lives in `docs/` with `Ontos_` filename prefixes. The `SKIP_PATTERNS` configuration excludes files matching `Ontos_` from the context map.

**Why the skip pattern exists:**

When someone installs Ontos in their project, they don't want Ontos's own documentation cluttering their context map. The skip pattern ensures only the USER's documentation appears.

**The conflict:**

When building Ontos itself, we NEED project documentation in the context map. But the skip pattern excludes it. We could remove the skip pattern, but then user documentation would appear in the context map — which is wrong because user docs describe the PRODUCT (how to use Ontos), not the PROJECT (how to build it).

### 1.3 The Solution: Hidden Internal Directory

Create a `.ontos-internal/` directory for PROJECT documentation (building Ontos), distinct from `docs/` which contains USER documentation (using Ontos).

**Why `.ontos-internal/` instead of `project/`?**

1. **Hidden by default:** Folders starting with `.` are hidden in file explorers on Unix/Linux/macOS
2. **Signals "system folder":** Users intuitively understand dot-folders are internal
3. **Consistent convention:** Matches `.ontos/` naming pattern
4. **Reduces cognitive load:** Users don't wonder "Do I need this folder?"

```
Repository Root
├── docs/                    # USER-FACING DOCUMENTATION (shipped with Ontos)
│   ├── guides/
│   │   ├── Ontos_Installation_Guide.md
│   │   ├── Ontos_Initiation_Guide.md
│   │   ├── Ontos_Maintenance_Guide.md
│   │   ├── Ontos_Migration_Guide.md
│   │   └── Ontos_Uninstallation_Guide.md
│   ├── reference/
│   │   ├── Ontos_Agent_Instructions.md
│   │   └── Ontos_Manual.md
│   ├── logs/                # Example logs for users (can remain)
│   └── _template.md
│
├── .ontos-internal/         # PROJECT DOCUMENTATION (hidden, for building Ontos)
│   ├── kernel/
│   │   └── mission.md
│   ├── strategy/
│   │   └── v2_strategy.md
│   ├── product/
│   │   └── v2_roadmap.md
│   ├── atom/
│   │   ├── architecture.md
│   │   ├── schema.md
│   │   └── self_development_protocol.md
│   └── logs/
│       └── (session logs go here)
│
├── .ontos/
│   └── scripts/
│       ├── ontos_config.py           # MODIFIED: points to .ontos-internal/
│       ├── ontos_config_defaults.py  # MODIFIED: adds .ontos-internal/ to skip patterns
│       ├── ontos_generate_context_map.py
│       ├── ontos_end_session.py
│       └── ...
│
├── Ontos_Context_Map.md     # Generated from .ontos-internal/, not docs/
└── ...
```

### 1.4 Why This Approach?

1. **Hidden from users:** Dot-prefix folders are invisible in most file explorers
2. **Skip pattern safety net:** Even if scanned, `.ontos-internal/` is ignored by default
3. **Dogfooding works:** Ontos manages its own development
4. **Contributors benefit:** Config is committed, so contributors get full context immediately
5. **Minimal code changes:** Only configuration and file organization

### 1.5 Why Now, Not v2?

The v2 development sessions ARE valuable content. If we wait until v2 is done to start using Ontos, we lose:

- The decision history of WHY v2 is designed the way it is
- Real test data for the Timeline feature
- Proof that the system works in complex, self-referential scenarios

By starting now:
- Current logs use v1.x format (that's fine)
- When v2 ships, we migrate existing logs to add `event_type`, `concepts`, `impacts`
- The Timeline feature immediately has rich, real data

---

## Part 2: Implementation Specification

### 2.1 Directory Structure to Create

```bash
# Create the internal project documentation structure
mkdir -p .ontos-internal/kernel
mkdir -p .ontos-internal/strategy
mkdir -p .ontos-internal/product
mkdir -p .ontos-internal/atom
mkdir -p .ontos-internal/logs
```

### 2.2 Configuration Changes

Two configuration files need to be updated.

#### A. Default Skip Patterns (for all users)

**File:** `.ontos/scripts/ontos_config_defaults.py`

**Current state:**

```python
DEFAULT_SKIP_PATTERNS = ['_template.md', 'Ontos_']
```

**New state:**

```python
# Files/patterns to skip during scanning (defaults)
# - _template.md: Template files
# - Ontos_: Ontos tooling files (Agent Instructions, Manual, Guides, etc.)
# - .ontos-internal/: Internal project documentation (for Ontos development only)
DEFAULT_SKIP_PATTERNS = ['_template.md', 'Ontos_', '.ontos-internal/']
```

**Rationale:** This ensures that even if a user accidentally scans a directory containing `.ontos-internal/`, it will be ignored. Security by default.

#### B. Ontos Repo Config (Smart Configuration)

**File:** `.ontos/scripts/ontos_config.py`

**The Problem (caught by Gemini):**

If we hardcode `DOCS_DIR = '.ontos-internal'`, users who copy `.ontos/` to their project get a broken config — it points to a folder that doesn't exist in their repo.

**The Solution: Conditional Configuration**

The config file detects its environment and adapts:
- If `.ontos-internal/` exists → Contributor Mode (developing Ontos)
- If not → User Mode (using Ontos in another project)

**New state:**

```python
# .ontos/scripts/ontos_config.py
"""Ontos configuration - User customizations.

This file imports defaults and adapts to its environment:
- If .ontos-internal/ exists WITH expected structure, we're developing Project Ontos (Contributor Mode)
- If not, we're using Project Ontos in another project (User Mode)
"""

import os

from ontos_config_defaults import (
    # ... existing imports ...
    DEFAULT_DOCS_DIR,
    DEFAULT_LOGS_DIR,
    DEFAULT_SKIP_PATTERNS,
)

def find_project_root() -> str:
    # ... existing function ...

PROJECT_ROOT = find_project_root()

# Define the internal directory path and a marker file to confirm it's the real Ontos repo
INTERNAL_DIR = os.path.join(PROJECT_ROOT, '.ontos-internal')
ONTOS_REPO_MARKER = os.path.join(INTERNAL_DIR, 'kernel', 'mission.md')

# =============================================================================
# SMART CONFIGURATION
# Adapts to environment: Contributor Mode vs User Mode
# =============================================================================

def is_ontos_repo() -> bool:
    """Check if we're in the actual Ontos repository.
    
    Requires BOTH:
    1. .ontos-internal/ directory exists
    2. The expected structure exists (kernel/mission.md as marker)
    
    This prevents false positives if a user accidentally copies .ontos-internal/
    """
    return os.path.isdir(INTERNAL_DIR) and os.path.isfile(ONTOS_REPO_MARKER)

if is_ontos_repo():
    # -------------------------------------------------------------------------
    # CONTRIBUTOR MODE: Developing Project Ontos itself
    # -------------------------------------------------------------------------
    # Confirmed Ontos repo (marker file exists)
    DOCS_DIR = INTERNAL_DIR
    LOGS_DIR = os.path.join(INTERNAL_DIR, 'logs')
    # Override defaults to allow scanning the internal dir
    SKIP_PATTERNS = ['_template.md', 'Ontos_']
else:
    # -------------------------------------------------------------------------
    # USER MODE: Using Project Ontos in another project
    # -------------------------------------------------------------------------
    # Either no .ontos-internal/, or it exists but lacks expected structure
    DOCS_DIR = os.path.join(PROJECT_ROOT, DEFAULT_DOCS_DIR)
    LOGS_DIR = os.path.join(PROJECT_ROOT, DEFAULT_LOGS_DIR)
    # Use defaults (which safely skip .ontos-internal if it appears by accident)
    SKIP_PATTERNS = DEFAULT_SKIP_PATTERNS
    
    # Warn if .ontos-internal/ exists but doesn't look like Ontos repo
    if os.path.isdir(INTERNAL_DIR) and not os.path.isfile(ONTOS_REPO_MARKER):
        import warnings
        warnings.warn(
            f"Found .ontos-internal/ directory but it doesn't appear to be the Ontos repo "
            f"(missing {ONTOS_REPO_MARKER}). Using default docs/ directory. "
            f"If this is intentional, you can ignore this warning.",
            stacklevel=2
        )

# =============================================================================
# USER OVERRIDES (optional)
# Uncomment and modify to customize for your specific project
# =============================================================================

# DOCS_DIR = os.path.join(PROJECT_ROOT, 'documentation')
# LOGS_DIR = os.path.join(PROJECT_ROOT, 'documentation/session-logs')
# SKIP_PATTERNS = DEFAULT_SKIP_PATTERNS + ['drafts/', 'archive/']
```

**Why this is more defensive (Codex refinement):**

The original check `if os.path.isdir(INTERNAL_DIR)` would trigger Contributor Mode if a user accidentally copied `.ontos-internal/` to their project. The improved check requires:

1. `.ontos-internal/` directory exists, AND
2. `kernel/mission.md` marker file exists (confirms it's the real Ontos repo)

If someone copies `.ontos-internal/` but without the full structure, they get:
- User Mode (correct behavior)
- A warning explaining what happened

### 2.3 Core Documents to Create

#### 2.3.1 Mission Document (Kernel)

**File:** `.ontos-internal/kernel/mission.md`

**Purpose:** Defines WHY Project Ontos exists. This is the root of the dependency graph.

**Content requirements:**
- Frontmatter with `id: mission`, `type: kernel`, `depends_on: []`
- Core problem statement (AI Amnesia, context death)
- Foundational principles (portability, curation over automation, git-native)
- What Ontos is NOT (not a database, not a cloud service, not automatic)

#### 2.3.2 v2 Strategy Document (Strategy)

**File:** `.ontos-internal/strategy/v2_strategy.md`

**Purpose:** Defines the goals, positioning, and approach for v2.0.

**Content requirements:**
- Frontmatter with `id: v2_strategy`, `type: strategy`, `depends_on: [mission]`
- Why v2 (the blind spot in v1.x)
- The core insight (Dual Ontology: Truth vs History)
- Target audience
- Competitive positioning
- What's in scope and out of scope
- Success criteria

**Status:** This document has already been drafted. See `Ontos_v2_Strategy.md` in outputs.

#### 2.3.3 v2 Roadmap Document (Product)

**File:** `.ontos-internal/product/v2_roadmap.md`

**Purpose:** Defines the phased delivery plan for v2.0.

**Content requirements:**
- Frontmatter with `id: v2_roadmap`, `type: product`, `depends_on: [v2_strategy]`
- Phase 1: Structure (v2.0.x) — schema changes
- Phase 2: Visibility (v2.1.x) — context map enhancements
- Phase 3: Intelligence (v2.2.x) — AI-powered features
- Version-by-version feature breakdown
- Dependencies between features

#### 2.3.4 Technical Architecture Document (Atom)

**File:** `.ontos-internal/atom/architecture.md`

**Purpose:** Defines HOW the v2.0 system works technically.

**Content requirements:**
- Frontmatter with `id: v2_architecture`, `type: atom`, `depends_on: [v2_roadmap]`
- Dual Ontology implementation (Space types vs Time type)
- Extended frontmatter schema for `type: log`
- Context map structure (four sections)
- Script changes required
- Data flow diagrams
- Backward compatibility approach

**Status:** A detailed specification exists in `Project_Ontos_v2_Specification.md`. This should be reformatted as a proper atom document.

#### 2.3.5 Schema Document (Atom)

**File:** `.ontos-internal/atom/schema.md`

**Purpose:** Defines the YAML frontmatter schema for all document types.

**Content requirements:**
- Frontmatter with `id: schema`, `type: atom`, `depends_on: [v2_architecture]`
- Complete field definitions for each type
- Required vs optional fields
- Validation rules
- Examples for each document type
- Migration guide for v1.x → v2.0 schema

#### 2.3.6 Self-Development Protocol Document (Atom)

**File:** `.ontos-internal/atom/self_development_protocol.md`

**Purpose:** Codifies how to safely develop Ontos using Ontos.

**Content requirements:**
- Frontmatter with `id: self_dev_protocol`, `type: atom`, `depends_on: [v2_architecture]`
- Known risks and mitigations (see Part 3 of this document)
- Pre-commit checklist
- Testing protocol
- Migration procedures

### 2.4 Initial Session Log

**File:** `.ontos-internal/logs/2025-12-11_v2-planning.md`

After setup, the current planning session should be archived as the first log entry. This captures:
- The decision to implement self-development protocol
- The choice of directory structure
- Initial strategy decisions for v2.0
- Collaboration with multiple AI agents (Claude, Gemini)

**Frontmatter:**

```yaml
---
id: log_20251211_v2_planning
type: atom  # Will become 'log' in v2.0
status: active
depends_on: []
---
```

When v2.0 ships, this log will be migrated to:

```yaml
---
id: log_20251211_v2_planning
type: log
event_type: exploration
concepts: [v2, dual-ontology, strategy, architecture]
impacts: [v2_strategy, v2_roadmap, v2_architecture]
status: active
depends_on: []
---
```

---

## Part 3: Known Risks and Mitigations

### 3.1 Changing the Engine While Running

**Risk:** Editing `ontos_generate_context_map.py` while using it. A bug could break the tool you depend on.

**Mitigation:**
- Run `pytest tests/ -v` before committing script changes
- Run `python3 .ontos/scripts/ontos_generate_context_map.py` after changes to verify it still works
- Keep the test suite comprehensive
- Consider a rollback procedure (git stash or known-good branch)

**Pre-commit checklist:**
```bash
# Before committing changes to .ontos/scripts/
pytest tests/ -v
python3 .ontos/scripts/ontos_generate_context_map.py --quiet
# Only commit if both pass
```

### 3.2 Schema Migration on Self

**Risk:** When adding `type: log` and `event_type`, existing logs won't have those fields. Scripts must handle both old and new formats.

**Mitigation:**
- Write backward compatibility FIRST
- The `normalize_type()` function should treat `atom` with `log_` prefix as `log`
- Missing `event_type` should default to `chore`
- Missing `concepts` and `impacts` should default to empty arrays
- Test against `examples/task-tracker/` before running on main repo

**Compatibility code pattern:**
```python
def normalize_type(value, doc_id: str = '') -> str:
    normalized = # ... existing logic ...
    
    # Backward compatibility: atom with log_ prefix → log
    if normalized == 'atom' and doc_id.startswith('log_'):
        return 'log'
    
    return normalized

def get_event_type(frontmatter: dict) -> str:
    return frontmatter.get('event_type', 'chore')

def get_concepts(frontmatter: dict) -> list:
    return frontmatter.get('concepts', [])

def get_impacts(frontmatter: dict) -> list:
    return frontmatter.get('impacts', [])
```

### 3.3 Version Skew in Documentation

**Risk:** Strategy and architecture docs describe v2.0 features that don't exist yet. An AI agent might think features are already implemented.

**Mitigation:**
- Use `status: draft` for documents describing future state
- Add explicit version markers in document content
- Opening paragraph should state: "This document describes v2.0 TARGET behavior, not current implementation."

**Status field convention:**
| Status | Meaning |
|--------|---------|
| `draft` | Describes future/planned state |
| `active` | Describes current implemented state |
| `deprecated` | Describes past state, no longer accurate |

### 3.4 Self-Referential Logs

**Risk:** When archiving a session about updating `ontos_end_session.py`, you're using the old version to document changes to itself.

**Mitigation:**
- Accept imperfection during transition
- Logs from transition period will use v1.x format — that's fine
- After v2.0 ships, migrate old logs to new schema
- Tag transition-period logs with `concepts: [v2-migration]` for easy identification

### 3.5 Pre-Commit Hook Blocking Its Own Changes

**Risk:** If `--strict` validation runs in pre-commit, and you're changing validation logic:
- Old validation rejects new schema
- You can't commit new validation because old validation blocks it

**Mitigation:**
- Use `git commit --no-verify` when committing schema/validation changes
- Re-enable hook verification immediately after
- Document this exception in commit message

**Command:**
```bash
# When committing validation logic changes
git commit --no-verify -m "feat: add log type support

Note: --no-verify used because new schema validation requires this commit"

# Immediately verify the new validation works
python3 .ontos/scripts/ontos_generate_context_map.py --strict
```

### 3.6 Testing on Production

**Risk:** The main repo IS the test environment. No sandbox.

**Mitigation:**
- Use `examples/task-tracker/` to test changes first
- Consider creating `examples/ontos-self/` that mirrors the `project/` structure
- Run validation on examples before running on main repo

**Testing sequence:**
```bash
# 1. Test on example project
python3 .ontos/scripts/ontos_generate_context_map.py --dir examples/task-tracker/docs

# 2. If that passes, test on internal project docs
python3 .ontos/scripts/ontos_generate_context_map.py --dir .ontos-internal
```

### 3.7 Circular Documentation

**Risk:** The architecture doc describes how the context map is generated. The context map includes the architecture doc. An AI reading the context map to understand Ontos is using the thing it's trying to understand.

**Mitigation:**
- This is bootstrapping, not a bug
- The system is designed to be self-documenting
- First activation on a fresh clone requires trust before understanding
- This is actually a FEATURE — the system demonstrates itself

### 3.8 Config File Conflicts

**Risk:** `ontos_config.py` imports from `ontos_config_defaults.py`. During active development of defaults, the config might import stale values.

**Mitigation:**
- Keep `ontos_config.py` minimal during active development
- Only override what's necessary (DOCS_DIR, LOGS_DIR)
- After changing defaults, restart Python interpreter (or clear cached imports)

### 3.9 The "Poisoned Config" Bug (Critical - Fixed)

**Risk:** ~~Hardcoding `DOCS_DIR = '.ontos-internal'` in the committed config would break every new user installation.~~

**The bug (caught by Gemini during review):**

1. User copies `.ontos/` folder to their project
2. User runs `ontos_generate_context_map.py`
3. Script reads config: "Look for documents in `.ontos-internal`"
4. User doesn't have `.ontos-internal/` folder
5. Script finds nothing, ignores user's `docs/` folder
6. **Result:** Empty map or error. User thinks Ontos is broken.

**The fix: Smart Conditional Configuration**

The config now detects its environment:

```python
if os.path.isdir(INTERNAL_DIR):
    # Contributor Mode - we're in the Ontos repo
    DOCS_DIR = INTERNAL_DIR
else:
    # User Mode - we're in a user's project
    DOCS_DIR = os.path.join(PROJECT_ROOT, DEFAULT_DOCS_DIR)
```

**Status:** Fixed in Revision 1.2. See Section 2.2.B for full implementation.

**Lesson:** This bug was caught BEFORE implementation because we documented the plan first and had it reviewed. This is exactly why Ontos exists — structured review catches issues that "just coding it" misses.

---

## Part 4: Implementation Checklist

### Phase 1: Setup (Do First)

- [ ] Create directory structure
  ```bash
  mkdir -p .ontos-internal/kernel .ontos-internal/strategy .ontos-internal/product .ontos-internal/atom .ontos-internal/logs
  ```

- [ ] Update `.ontos/scripts/ontos_config_defaults.py`
  ```python
  DEFAULT_SKIP_PATTERNS = ['_template.md', 'Ontos_', '.ontos-internal/']
  ```

- [ ] Update `.ontos/scripts/ontos_config.py` with smart configuration
  ```python
  INTERNAL_DIR = os.path.join(PROJECT_ROOT, '.ontos-internal')
  
  if os.path.isdir(INTERNAL_DIR):
      # Contributor Mode
      DOCS_DIR = INTERNAL_DIR
      LOGS_DIR = os.path.join(INTERNAL_DIR, 'logs')
      SKIP_PATTERNS = ['_template.md', 'Ontos_']
  else:
      # User Mode (Default)
      DOCS_DIR = os.path.join(PROJECT_ROOT, DEFAULT_DOCS_DIR)
      LOGS_DIR = os.path.join(PROJECT_ROOT, DEFAULT_LOGS_DIR)
      SKIP_PATTERNS = DEFAULT_SKIP_PATTERNS
  ```

- [ ] Create `.ontos-internal/kernel/mission.md`
  - Define why Ontos exists
  - Core principles
  - What Ontos is NOT

- [ ] Move/create `.ontos-internal/strategy/v2_strategy.md`
  - Use the drafted strategy document
  - Add proper frontmatter

- [ ] Run initial validation
  ```bash
  python3 .ontos/scripts/ontos_generate_context_map.py
  ```

- [ ] Verify context map shows internal docs, not user docs

### Phase 2: Core Documents (Do Second)

- [ ] Create `.ontos-internal/product/v2_roadmap.md`
- [ ] Create `.ontos-internal/atom/architecture.md`
- [ ] Create `.ontos-internal/atom/schema.md`
- [ ] Create `.ontos-internal/atom/self_development_protocol.md`
- [ ] Validate dependency graph
  ```bash
  python3 .ontos/scripts/ontos_generate_context_map.py --strict
  ```

### Phase 3: First Session Archive (Do Third)

- [ ] Archive current session
  ```bash
  python3 .ontos/scripts/ontos_end_session.py "v2-planning" --source "Claude + Gemini"
  ```

- [ ] Fill in session log with actual decisions made
- [ ] Commit all changes
  ```bash
  git add .ontos-internal/ .ontos/scripts/ontos_config.py .ontos/scripts/ontos_config_defaults.py Ontos_Context_Map.md
  git commit -m "feat: implement self-development protocol for Ontos v2"
  ```

### Phase 4: Ongoing Protocol (Do Always)

- [ ] Before each coding session: "Activate Ontos"
- [ ] After each coding session: "Archive Ontos"
- [ ] Before committing script changes: run tests
- [ ] Weekly: "Maintain Ontos" to catch drift

---

## Part 5: Expected Outcome

After implementation, the `Ontos_Context_Map.md` should look like:

```markdown
# Ontos Context Map
Generated on: 2025-12-11 XX:XX:XX
Scanned Directory: `/path/to/project-ontos/.ontos-internal`

## 1. Hierarchy Tree

### KERNEL
- **mission** (mission.md)
  - Status: active
  - Depends On: None

### STRATEGY
- **v2_strategy** (v2_strategy.md)
  - Status: draft
  - Depends On: mission

### PRODUCT
- **v2_roadmap** (v2_roadmap.md)
  - Status: draft
  - Depends On: v2_strategy

### ATOM
- **v2_architecture** (architecture.md)
  - Status: draft
  - Depends On: v2_roadmap
- **schema** (schema.md)
  - Status: draft
  - Depends On: v2_architecture
- **self_dev_protocol** (self_development_protocol.md)
  - Status: draft
  - Depends On: v2_architecture

## 2. Dependency Audit
No issues found.

## 3. Index
| ID | Filename | Type |
|----|----------|------|
| mission | mission.md | kernel |
| v2_strategy | v2_strategy.md | strategy |
| v2_roadmap | v2_roadmap.md | product |
| v2_architecture | architecture.md | atom |
| schema | schema.md | atom |
| self_dev_protocol | self_development_protocol.md | atom |
| log_20251211_v2_planning | 2025-12-11_v2-planning.md | atom |
```

When v2.0 ships with the Timeline feature, the logs will appear in a new section:

```markdown
## 4. Recent Timeline
- **2025-12-11** [exploration] v2 Planning → `v2_strategy`, `v2_architecture`
```

---

## Part 5b: User Experience Verification

**What users see when they clone Ontos repo:**

```
project-ontos/
├── .ontos/              # ← They copy this to their project
├── .ontos-internal/     # ← Hidden, triggers Contributor Mode
├── docs/                # ← User documentation
├── examples/
├── tests/
├── README.md
└── ... (other files)
```

The `.ontos-internal/` folder is hidden by default. Most users won't even know it exists.

**What users see when they install Ontos in their project:**

```
their-project/
├── .ontos/              # ← Copied from Ontos repo
├── docs/                # ← Their documentation (they create this)
├── Ontos_Context_Map.md # ← Generated from their docs/
└── ... (their code)
```

No `.ontos-internal/`. The smart config detects this and falls back to User Mode (scanning `docs/`).

**What contributors see when they clone Ontos repo and run "Activate Ontos":**

```
Loaded: [mission, v2_strategy, v2_roadmap, v2_architecture, schema, self_dev_protocol]
```

The smart config detects `.ontos-internal/` and activates Contributor Mode. Full project context. They're productive immediately.

**The Smart Config Flow:**

```
User runs ontos_generate_context_map.py
           │
           ▼
    Does .ontos-internal/ exist?
           │
    ┌──────┴──────┐
    │ YES         │ NO
    ▼             ▼
Contributor    User Mode
   Mode        
    │             │
    ▼             ▼
Scan          Scan docs/
.ontos-internal/
```

---

## Part 6: Context-Map Ownership Protocol

**Gap identified by Codex:** Who regenerates the context map? When should it be committed?

### 6.1 Ownership Rules

| Scenario | Who Regenerates | When to Commit |
|----------|-----------------|----------------|
| Document created/modified | The contributor who made the change | Same commit as the document change |
| Session archived | The archiving agent | Same commit as the log file |
| Schema/config change | The contributor who changed schema | After verifying no breakage |
| CI/CD validation | Automated (read-only check) | Never (validation only) |

### 6.2 The "Stale Map" Problem

**Risk:** Contributor A modifies `architecture.md`, regenerates map, but forgets to commit the updated map. Contributor B pulls, sees stale map.

**Mitigations:**

1. **Pre-commit hook (recommended):** Automatically regenerate and stage map before commit
   ```bash
   # .git/hooks/pre-commit
   python3 .ontos/scripts/ontos_generate_context_map.py
   git add Ontos_Context_Map.md
   ```

2. **CI check:** Fail if committed map differs from regenerated map
   ```yaml
   # .github/workflows/ontos.yml
   - name: Verify context map is current
     run: |
       python3 .ontos/scripts/ontos_generate_context_map.py
       git diff --exit-code Ontos_Context_Map.md
   ```

3. **Convention:** "If you touch docs, regenerate the map" (weakest, relies on memory)

### 6.3 Recommended Workflow

```
1. Make document changes
2. Run: python3 .ontos/scripts/ontos_generate_context_map.py
3. Review the diff (sanity check)
4. Commit both: git add docs/changed_file.md Ontos_Context_Map.md
5. Push
```

For v2.0, consider adding `--check` flag that exits non-zero if map is stale (for CI integration).

---

## Part 7: Testing Cadence

**Gap identified by Codex:** Need explicit testing for both Contributor and User modes.

### 7.1 Dual-Mode Test Matrix

| Test Scenario | Mode | Setup | Expected Behavior |
|---------------|------|-------|-------------------|
| Clone Ontos repo, run scripts | Contributor | `.ontos-internal/` exists with marker | Scans `.ontos-internal/`, generates project context |
| Copy `.ontos/` to new project | User | No `.ontos-internal/` | Falls back to `docs/`, standard behavior |
| User has empty `.ontos-internal/` | User | Dir exists, no marker file | Falls back to `docs/` + warning |
| User copies partial structure | User | Dir exists, missing `kernel/mission.md` | Falls back to `docs/` + warning |

### 7.2 Test Commands

```bash
# Test Contributor Mode (run from Ontos repo root)
python3 .ontos/scripts/ontos_generate_context_map.py
# Expected: Scans .ontos-internal/, lists project docs

# Test User Mode (run from a project without .ontos-internal/)
cd /tmp && mkdir test-project && cd test-project
cp -r /path/to/ontos/.ontos .
mkdir -p docs && echo "---\nid: test\ntype: atom\n---\n# Test" > docs/test.md
python3 .ontos/scripts/ontos_generate_context_map.py
# Expected: Scans docs/, lists test.md

# Test False Positive Protection (empty .ontos-internal/)
mkdir .ontos-internal
python3 .ontos/scripts/ontos_generate_context_map.py
# Expected: Warning about missing marker, falls back to docs/

# Test Partial Structure Protection
mkdir -p .ontos-internal/kernel
python3 .ontos/scripts/ontos_generate_context_map.py
# Expected: Warning (no mission.md), falls back to docs/
```

### 7.3 CI Integration

```yaml
# .github/workflows/test-modes.yml
jobs:
  test-contributor-mode:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test Contributor Mode
        run: |
          python3 .ontos/scripts/ontos_generate_context_map.py
          grep -q "mission" Ontos_Context_Map.md  # Should find project docs

  test-user-mode:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Simulate User Installation
        run: |
          mkdir /tmp/user-project
          cp -r .ontos /tmp/user-project/
          cd /tmp/user-project
          mkdir -p docs
          echo -e "---\nid: user_doc\ntype: atom\nstatus: active\n---\n# User Doc" > docs/user_doc.md
          python3 .ontos/scripts/ontos_generate_context_map.py
          grep -q "user_doc" Ontos_Context_Map.md  # Should find user docs
          ! grep -q "mission" Ontos_Context_Map.md  # Should NOT find project docs
```

### 7.4 When to Run Tests

| Event | Contributor Mode Test | User Mode Test |
|-------|----------------------|----------------|
| PR to main | ✅ | ✅ |
| Config file changed | ✅ | ✅ |
| New release tag | ✅ | ✅ |
| Daily CI | ✅ | ✅ |

---

## Part 8: Review Questions for AI Agents

Please review this implementation plan and consider:

1. **Completeness:** Are there any gaps in the directory structure or document list?

2. **Risk coverage:** Are there additional risks of self-referential development not covered?

3. **Sequencing:** Is the implementation order correct, or should something be reordered?

4. **Backward compatibility:** Will the proposed changes break existing functionality for users who have already installed Ontos v1.x?

5. **Testing:** Is the testing strategy sufficient? Should there be additional validation steps?

6. **Documentation:** Are the new documents (mission, strategy, architecture, etc.) correctly typed and linked in the dependency graph?

7. **Migration path:** When v2.0 ships, how should existing v1.x logs in `project/logs/` be migrated to the new schema?

8. **Edge cases:** What happens if someone clones the Ontos repo and runs "Activate Ontos"? They should get `.ontos-internal/` docs (contributor experience). Is this clearly documented? What if a user copies `.ontos/` to their project but forgets to change the config — does the skip pattern protect them?

---

## Appendix A: File Contents Summary

| File | Type | Depends On | Status | Purpose |
|------|------|------------|--------|---------|
| `.ontos-internal/kernel/mission.md` | kernel | — | active | Why Ontos exists |
| `.ontos-internal/strategy/v2_strategy.md` | strategy | mission | draft | v2.0 goals and positioning |
| `.ontos-internal/product/v2_roadmap.md` | product | v2_strategy | draft | Phased delivery plan |
| `.ontos-internal/atom/architecture.md` | atom | v2_roadmap | draft | Technical implementation |
| `.ontos-internal/atom/schema.md` | atom | v2_architecture | draft | Frontmatter specification |
| `.ontos-internal/atom/self_development_protocol.md` | atom | v2_architecture | draft | How to develop Ontos safely |

## Appendix B: Configuration Diffs

### B.1 ontos_config_defaults.py

```diff
# .ontos/scripts/ontos_config_defaults.py

- DEFAULT_SKIP_PATTERNS = ['_template.md', 'Ontos_']
+ DEFAULT_SKIP_PATTERNS = ['_template.md', 'Ontos_', '.ontos-internal/']
```

### B.2 ontos_config.py (Smart Configuration with Marker File)

```diff
# .ontos/scripts/ontos_config.py

+ # Define the internal directory path and marker file
+ INTERNAL_DIR = os.path.join(PROJECT_ROOT, '.ontos-internal')
+ ONTOS_REPO_MARKER = os.path.join(INTERNAL_DIR, 'kernel', 'mission.md')
+ 
+ def is_ontos_repo() -> bool:
+     """Check if we're in the actual Ontos repository.
+     Requires BOTH .ontos-internal/ AND the marker file."""
+     return os.path.isdir(INTERNAL_DIR) and os.path.isfile(ONTOS_REPO_MARKER)
+ 
+ # SMART CONFIGURATION:
+ # If marker file exists, we are developing Project Ontos (Contributor Mode).
+ # If not, we are using Project Ontos (User Mode).
+ if is_ontos_repo():
+     # Contributor Mode
+     DOCS_DIR = INTERNAL_DIR
+     LOGS_DIR = os.path.join(INTERNAL_DIR, 'logs')
+     SKIP_PATTERNS = ['_template.md', 'Ontos_']
+ else:
+     # User Mode (Default)
+     DOCS_DIR = os.path.join(PROJECT_ROOT, DEFAULT_DOCS_DIR)
+     LOGS_DIR = os.path.join(PROJECT_ROOT, DEFAULT_LOGS_DIR)
+     SKIP_PATTERNS = DEFAULT_SKIP_PATTERNS
+     
+     # Warn if .ontos-internal/ exists but lacks marker
+     if os.path.isdir(INTERNAL_DIR) and not os.path.isfile(ONTOS_REPO_MARKER):
+         import warnings
+         warnings.warn(
+             f"Found .ontos-internal/ but missing marker file. Using docs/.",
+             stacklevel=2
+         )

- DOCS_DIR = os.path.join(PROJECT_ROOT, DEFAULT_DOCS_DIR)
- LOGS_DIR = os.path.join(PROJECT_ROOT, DEFAULT_LOGS_DIR)
```

## Appendix C: Command Reference

```bash
# Setup
mkdir -p .ontos-internal/kernel .ontos-internal/strategy .ontos-internal/product .ontos-internal/atom .ontos-internal/logs

# Validation
python3 .ontos/scripts/ontos_generate_context_map.py
python3 .ontos/scripts/ontos_generate_context_map.py --strict

# Session management
python3 .ontos/scripts/ontos_end_session.py "session-slug" --source "Agent Name"

# Testing
pytest tests/ -v
python3 .ontos/scripts/ontos_generate_context_map.py --dir examples/task-tracker/docs

# Emergency commit (bypassing hooks)
git commit --no-verify -m "message"
```

## Appendix D: Why Not Other Approaches?

### D.1 Why not use a `scope` field in frontmatter?

**The idea:** Add `scope: user` vs `scope: internal` to frontmatter, then filter by scope.

**Why rejected:**
- Risk of forgetting to filter, leaking internal docs
- Requires code changes to all scripts
- Physical separation (folders) is cleaner and safer

### D.2 Why not use git skip-worktree for config?

**The idea:** Don't commit `ontos_config.py`, use skip-worktree so contributors configure locally.

**Why rejected:**
- Contributors would have to configure manually on every clone
- Defeats the "instant shared brain" value proposition
- The committed config benefits contributors without affecting users

### D.3 Why not keep everything in `docs/` with different naming?

**The idea:** `docs/internal/` instead of `.ontos-internal/`.

**Why rejected:**
- Users might think they need to create `internal/` in their projects
- Not hidden by default
- Mixes concerns in the same directory tree

## Appendix E: Design Evolution (Claude + Gemini + Codex Collaboration)

This implementation plan evolved through collaboration:

**Claude's initial proposal:**
- Separate `project/` directory for internal docs
- Change `ontos_config.py` to point to `project/`
- Identified 10 risks of self-referential development

**Gemini's first refinement:**
- Rename `project/` to `.ontos-internal/` (hidden by default)
- Add `.ontos-internal/` to `DEFAULT_SKIP_PATTERNS` (safety net)
- Suggested NOT using git skip-worktree (commit the config for contributor benefit)
- Added "Profile Strategy" alternative analysis (rejected as riskier)

**Gemini's critical bug catch (The "Poisoned Config"):**
- Identified that hardcoding `DOCS_DIR = '.ontos-internal'` would break user installations
- Users copying `.ontos/` would get a config pointing to a non-existent folder
- **Solution:** Smart conditional configuration that detects its environment:
  - If `.ontos-internal/` exists → Contributor Mode
  - If not → User Mode (default behavior)

**Codex's refinements (Revision 1.3):**
- **Context-map ownership gap:** Who regenerates the map? When to commit? Added Part 6 with ownership rules, pre-commit hook recommendation, and CI check pattern.
- **Cross-project safety edge case:** What if user accidentally copies `.ontos-internal/` without full structure? Strengthened smart config to require marker file (`kernel/mission.md`), not just directory existence. Added warning for partial structures.
- **Testing cadence:** Need explicit dual-mode testing. Added Part 7 with test matrix, commands, CI integration, and test triggers.

**Final synthesis:**
- `.ontos-internal/` naming adopted (Gemini's recommendation)
- Skip pattern safety net adopted (Gemini's recommendation)
- Smart conditional config with marker file adopted (Gemini's bug fix + Codex's hardening)
- Context-map ownership protocol adopted (Codex's gap identification)
- Dual-mode testing cadence adopted (Codex's gap identification)
- Physical separation over logical separation (all agreed)

This collaboration demonstrates Ontos's value proposition: decisions are captured, attributed, and traceable. Multiple bugs and gaps were caught BEFORE implementation because we documented the plan first and had multiple reviewers.
