---
id: v2_architecture
type: atom
status: draft
depends_on: [v2_strategy]
---

# Project Ontos v2.0 Technical Architecture

*Implementation specification for the Dual Ontology system*

---

## 1. System Overview

Ontos v2.0 implements the Dual Ontology model defined in the Strategy document:

- **Space Ontology (The Graph):** Static knowledge — what IS true about the project
- **Time Ontology (The Timeline):** Temporal knowledge — what HAPPENED during development

The two ontologies are connected by the `impacts` field, which anchors History to Truth.

```
┌─────────────────────────────────────────────────────────────────┐
│                        SPACE (Truth)                            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  kernel  │───▶│ strategy │───▶│ product  │───▶│   atom   │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│        ▲              ▲               ▲               ▲        │
│        │              │               │               │        │
│        └──────────────┴───────────────┴───────────────┘        │
│                              │                                  │
│                         impacts: []                             │
│                              │                                  │
│  ┌───────────────────────────┴───────────────────────────────┐ │
│  │                      TIME (History)                        │ │
│  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐    │ │
│  │  │ log │  │ log │  │ log │  │ log │  │ log │  │ log │    │ │
│  │  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘    │ │
│  │  ────────────────────────────────────────────────────▶   │ │
│  │                        time                               │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Schema Specification

### 2.1 Type Definitions

```python
# .ontos/scripts/ontos_config_defaults.py

TYPE_DEFINITIONS = {
    # Space Ontology (hierarchical)
    'kernel': {'level': 0, 'allowed_deps': []},
    'strategy': {'level': 1, 'allowed_deps': ['kernel']},
    'product': {'level': 2, 'allowed_deps': ['kernel', 'strategy']},
    'atom': {'level': 3, 'allowed_deps': ['kernel', 'strategy', 'product', 'atom']},

    # Time Ontology (non-hierarchical)
    'log': {'level': None, 'allowed_deps': []},  # logs don't use depends_on
}
```

**Key distinction:** `log` has `level: None` — it exists outside the dependency hierarchy. Logs connect to Space through `impacts`, not `depends_on`.

### 2.2 Frontmatter Schema

**Space Types (kernel, strategy, product, atom):**

```yaml
---
id: <string>           # Required. Unique identifier. Snake_case.
type: <string>         # Required. One of: kernel, strategy, product, atom
status: <string>       # Required. One of: active, draft, deprecated
depends_on: [<ids>]    # Optional. List of IDs this document depends on.
summary: <string>      # Optional (v2.1+). 50-word summary for progressive disclosure.
---
```

**Time Type (log):**

```yaml
---
id: <string>           # Required. Format: log_YYYYMMDD_<slug>
type: log              # Required. Literal "log"
status: <string>       # Required. One of: active, archived
event_type: <string>   # Required. One of: feature, fix, refactor, exploration, chore
concepts: [<strings>]  # Optional. Freeform tags for searchability.
impacts: [<ids>]       # Required. List of Space document IDs affected by this session.
---
```

### 2.3 Event Type Taxonomy

| Event Type | Intent | Example |
|------------|--------|---------|
| `feature` | Adding new capability | "Implemented OAuth login flow" |
| `fix` | Correcting broken behavior | "Fixed refresh token expiration bug" |
| `refactor` | Restructuring without behavior change | "Split auth module into services" |
| `exploration` | Research, spikes, prototypes | "Evaluated database options" |
| `chore` | Maintenance, dependencies, config | "Updated Python dependencies" |

**Design rationale:** This taxonomy captures *intent*, not *output*. A session that explores AND implements would be tagged by primary intent.

---

## 3. Validation Rules

### 3.1 Existing Rules (v1.x)

These rules remain unchanged:

| Rule | Description | Error |
|------|-------------|-------|
| Required fields | `id`, `type`, `status` must exist | `[MISSING FIELD]` |
| Valid type | `type` must be in TYPE_DEFINITIONS | `[INVALID TYPE]` |
| Valid status | `status` must be in STATUS_VALUES | `[INVALID STATUS]` |
| Unique IDs | No duplicate `id` values across all docs | `[DUPLICATE ID]` |
| Dependency exists | IDs in `depends_on` must exist | `[BROKEN LINK]` |
| No cycles | Dependency graph must be acyclic | `[CYCLE DETECTED]` |
| Hierarchy respected | Dependencies must flow kernel → atom | `[INVALID DEPENDENCY]` |

### 3.2 New Rules (v2.0)

**Rule: Log Type Validation**

```python
def validate_log(doc: Document) -> list[Error]:
    errors = []

    # Logs must have event_type
    if doc.type == 'log' and 'event_type' not in doc.frontmatter:
        errors.append(Error('[MISSING FIELD]', f'{doc.id}: log requires event_type'))

    # Logs must have impacts
    if doc.type == 'log' and 'impacts' not in doc.frontmatter:
        errors.append(Error('[MISSING FIELD]', f'{doc.id}: log requires impacts'))

    # Logs should not have depends_on
    if doc.type == 'log' and 'depends_on' in doc.frontmatter:
        errors.append(Error('[INVALID FIELD]', f'{doc.id}: log should not use depends_on'))

    # event_type must be valid
    valid_events = {'feature', 'fix', 'refactor', 'exploration', 'chore'}
    if doc.frontmatter.get('event_type') not in valid_events:
        errors.append(Error('[INVALID VALUE]', f'{doc.id}: invalid event_type'))

    return errors
```

**Rule: Impacts Validation (The Bridge)**

```python
def validate_impacts(doc: Document, all_docs: dict[str, Document]) -> list[Error]:
    """Ensure all IDs in impacts[] exist in Space Ontology."""
    errors = []

    if doc.type != 'log':
        return errors

    impacts = doc.frontmatter.get('impacts', [])
    space_ids = {d.id for d in all_docs.values() if d.type != 'log'}

    for impact_id in impacts:
        if impact_id not in space_ids:
            errors.append(Error(
                '[BROKEN LINK]',
                f'{doc.id}: impacts references non-existent document "{impact_id}"'
            ))

    return errors
```

**Design rationale:** History must always anchor to Truth. If a log claims to impact `auth_flow`, but `auth_flow.md` doesn't exist, that's a broken link — same severity as a broken `depends_on`.

### 3.3 Validation Modes

```bash
# Standard mode: warnings for issues, continues processing
python3 .ontos/scripts/ontos_generate_context_map.py

# Strict mode: exits non-zero on any error (for CI)
python3 .ontos/scripts/ontos_generate_context_map.py --strict
```

---

## 4. Context Map Generation

### 4.0 Generation Pipeline

The generator follows a strict sequence:

```
1. SCAN & PARSE
   └── Read all .md files from DOCS_DIR
   └── Extract YAML frontmatter
   └── Build document objects

2. TOKEN ESTIMATION
   └── Calculate len(content) // 4 for each file
   └── Store as metadata

3. SPLIT
   └── Separate into space_docs (kernel, strategy, product, atom)
   └── Separate into time_docs (log)

4. VALIDATE
   └── Run hierarchy checks on space_docs (depends_on flows downward)
   └── Run integrity checks on time_docs (impacts must exist in space_docs)

5. RENDER
   └── Section 1: Document Registry (grouped by type, with token counts)
   └── Section 2: Dependency Graph (tree view)
   └── Section 3: Recent Timeline (reverse-chronological logs)
   └── Section 4: Status Overview (summary table)
```

### 4.1 Structure (v2.0)

The context map gains a fourth section for Timeline:

```markdown
<!-- Generated by Ontos | Mode: Contributor | Root: .ontos-internal/ | 2025-12-11T14:32:00Z -->

# Ontos Context Map

## 1. Document Registry

### KERNEL
- **mission** (kernel/mission.md) ~450 tokens
  - Status: active

### STRATEGY
- **v2_strategy** (strategy/v2_strategy.md) ~1,800 tokens
  - Status: active
  - Depends On: mission

### ATOM
- **auth_flow** (atom/auth_flow.md) ~1,200 tokens
  - Status: active
  - Depends On: api_spec

## 2. Dependency Graph
mission
└── v2_strategy
    └── v2_architecture

## 3. Recent Timeline
- **2025-12-10** [refactor] **Auth Refactor** (log_20251210_auth)
  - Impacted: `auth_flow`, `api_spec`
- **2025-12-09** [exploration] **DB Research** (log_20251209_db)
  - Concepts: postgres, sqlite
- **2025-12-08** [feature] **OAuth Implementation** (log_20251208_oauth)
  - Impacted: `auth_flow`

## 4. Status Overview
| Status | Count | Documents |
|--------|-------|-----------|
| active | 3 | mission, v2_strategy, auth_flow |
| draft | 1 | v2_architecture |
```

### 4.2 Token Estimation (v2.1+)

```python
def estimate_tokens(content: str) -> int:
    """Approximate token count using character-based heuristic.

    Formula: tokens ≈ characters / 4
    Simple, fast, good enough for budgeting context.
    """
    return len(content) // 4

def format_token_count(tokens: int) -> str:
    """Format token count for display."""
    if tokens < 1000:
        return f"~{tokens} tokens"
    else:
        return f"~{tokens // 100 * 100:,} tokens"  # Round to nearest 100
```

### 4.3 Provenance Header

Every generated context map includes a provenance header:

```python
def generate_provenance_header() -> str:
    """Generate metadata header for audit trail."""
    mode = "Contributor" if is_ontos_repo() else "User"
    root = DOCS_DIR.replace(PROJECT_ROOT, '').lstrip(os.sep) or 'docs'
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    return f"<!-- Generated by Ontos | Mode: {mode} | Root: {root} | {timestamp} -->\n"
```

---

## 5. Project Initialization

### 5.1 Unified Init Script

v2.0 combines "install" and "initiate" into a single `ontos_init.py` script:

```bash
# Run from your project root
python3 /path/to/ontos/ontos_init.py

# Or if you cloned the Ontos repo
python3 ../project-ontos/ontos_init.py
```

### 5.2 What `ontos_init.py` Does

```python
def init_ontos(project_root: str, docs_dir: str = 'docs') -> None:
    """Initialize Ontos in a project directory.

    Steps:
    1. Create .ontos/scripts/ directory
    2. Copy all Ontos scripts
    3. Create docs/ structure (kernel/, strategy/, product/, atom/, logs/)
    4. Create starter mission.md with template
    5. Generate initial context map
    6. Print success message
    """

    # Step 1-2: Copy scripts
    ontos_dir = os.path.join(project_root, '.ontos', 'scripts')
    os.makedirs(ontos_dir, exist_ok=True)
    copy_scripts(source=ONTOS_SCRIPTS_PATH, dest=ontos_dir)

    # Step 3: Create docs structure
    docs_path = os.path.join(project_root, docs_dir)
    for subdir in ['kernel', 'strategy', 'product', 'atom', 'logs']:
        os.makedirs(os.path.join(docs_path, subdir), exist_ok=True)

    # Step 4: Create starter mission.md
    mission_path = os.path.join(docs_path, 'kernel', 'mission.md')
    if not os.path.exists(mission_path):
        create_mission_template(mission_path)

    # Step 5: Generate initial context map
    generate_context_map(project_root)

    # Step 6: Success
    print(f"✓ Ontos initialized in {project_root}")
    print(f"  - Scripts: .ontos/scripts/")
    print(f"  - Docs: {docs_dir}/")
    print(f"  - Context map: Ontos_Context_Map.md")
    print()
    print("Next: Edit docs/kernel/mission.md, then run 'Activate Ontos' in your AI agent.")
```

### 5.3 Mission Template

```markdown
---
id: mission
type: kernel
status: draft
---

# Project Mission

## Why This Project Exists

[What problem does this project solve?]

## Core Principles

[What values guide technical decisions?]

## Success Looks Like

[How will you know when it's working?]
```

### 5.4 Idempotency

The script is safe to run multiple times:
- Existing files are not overwritten
- Existing directories are preserved
- Only missing pieces are created

```bash
# Safe to run again
python3 ontos_init.py
# Output: "✓ Ontos already initialized. No changes made."
```

### 5.5 Custom Docs Directory

```bash
# Use 'documentation' instead of 'docs'
python3 ontos_init.py --docs-dir documentation
```

---

## 6. Session Archival

### 6.1 Archive Script Enhancement

```bash
# Current (v1.x)
python3 .ontos/scripts/ontos_end_session.py "session-slug"

# Enhanced (v2.0)
python3 .ontos/scripts/ontos_end_session.py "session-slug" \
    --event-type "refactor" \
    --concepts "auth,oauth" \
    --impacts "auth_flow,api_spec"
```

### 6.2 Auto-Suggested Impacts Algorithm

When `--impacts` is not provided, the script suggests impacts based on git state:

```python
def suggest_impacts() -> list[str]:
    """Suggest document IDs that may have been impacted by recent changes.

    Algorithm:
    1. Get list of changed files from git status
    2. Load the context map to get file → ID mapping
    3. Match changed files to known document paths
    4. Return matching IDs as suggestions
    """
    # Step 1: Get changed files
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True, text=True
    )
    changed_files = []
    for line in result.stdout.strip().split('\n'):
        if line:
            # Format: "XY filename" or "XY original -> renamed"
            parts = line[3:].split(' -> ')
            changed_files.append(parts[-1])  # Use final name if renamed

    # Step 2: Load context map index
    doc_index = load_document_index()  # Returns {filepath: doc_id}

    # Step 3: Match changed files to documents
    suggestions = []
    for filepath in changed_files:
        # Check if file itself is a doc
        if filepath in doc_index:
            suggestions.append(doc_index[filepath])

        # Check if file is in same directory as a doc (code change near doc)
        dir_path = os.path.dirname(filepath)
        for doc_path, doc_id in doc_index.items():
            if os.path.dirname(doc_path) == dir_path:
                suggestions.append(doc_id)

    return list(set(suggestions))  # Deduplicate

def prompt_for_impacts(suggestions: list[str]) -> list[str]:
    """Interactive prompt for impact confirmation."""
    if suggestions:
        print(f"Suggested impacts based on git changes: {', '.join(suggestions)}")
        print("Accept suggestions? [Y/n/edit]: ", end='')
        response = input().strip().lower()

        if response in ('', 'y', 'yes'):
            return suggestions
        elif response in ('n', 'no'):
            return prompt_manual_impacts()
        else:
            # Edit mode
            print(f"Enter impacts (comma-separated, starting with: {', '.join(suggestions)}): ")
            return [i.strip() for i in input().split(',')]
    else:
        return prompt_manual_impacts()
```

### 6.3 Generated Log Format

```markdown
---
id: log_20251210_auth_refactor
type: log
status: active
event_type: refactor
concepts: [auth, oauth, security]
impacts: [auth_flow, api_spec]
---

# Session: Auth Refactor

**Date:** 2025-12-10
**Duration:** ~2 hours
**Event Type:** refactor

## Summary

Refactored authentication module to separate concerns...

## Key Decisions

1. Split monolithic auth.py into auth_service.py and token_manager.py
2. Chose to keep refresh tokens in Redis rather than PostgreSQL

## Artifacts

- Modified: `src/auth/auth_service.py`
- Created: `src/auth/token_manager.py`
- Updated: `docs/atom/auth_flow.md`

## Next Steps

- [ ] Add unit tests for token_manager
- [ ] Update API documentation
```

---

## 7. Environment Detection (Smart Config)

### 7.1 Mode Detection

```python
# .ontos/scripts/ontos_config.py

INTERNAL_DIR = os.path.join(PROJECT_ROOT, '.ontos-internal')
ONTOS_REPO_MARKER = os.path.join(INTERNAL_DIR, 'kernel', 'mission.md')

def is_ontos_repo() -> bool:
    """Check if we're in the actual Ontos repository.

    Requires BOTH:
    1. .ontos-internal/ directory exists
    2. The expected structure exists (kernel/mission.md as marker)

    This prevents false positives if a user accidentally copies .ontos-internal/
    """
    return os.path.isdir(INTERNAL_DIR) and os.path.isfile(ONTOS_REPO_MARKER)
```

### 7.2 Configuration Behavior

| Condition | Mode | DOCS_DIR | LOGS_DIR | SKIP_PATTERNS |
|-----------|------|----------|----------|---------------|
| `.ontos-internal/` + marker exists | Contributor | `.ontos-internal/` | `.ontos-internal/logs/` | `['_template.md', 'Ontos_']` |
| Otherwise | User | `docs/` | `docs/logs/` | `['_template.md', 'Ontos_', '.ontos-internal/']` |

### 7.3 Warning on Partial Structure

```python
if os.path.isdir(INTERNAL_DIR) and not os.path.isfile(ONTOS_REPO_MARKER):
    import warnings
    warnings.warn(
        f"Found .ontos-internal/ but it doesn't appear to be the Ontos repo "
        f"(missing {ONTOS_REPO_MARKER}). Using default docs/ directory.",
        stacklevel=2
    )
```

---

## 8. File Structure

### 8.1 Ontos Repository (Contributor Mode)

```
project-ontos/
├── ontos_init.py                        # Standalone initializer (run from any project)
├── .ontos/
│   └── scripts/
│       ├── ontos_config.py              # Smart configuration
│       ├── ontos_config_defaults.py     # Default values
│       ├── ontos_generate_context_map.py
│       ├── ontos_end_session.py         # Enhanced with --event-type, --impacts
│       ├── ontos_validate.py
│       ├── ontos_migrate_v2.py          # Optional: explicit v1→v2 migration
│       └── ontos_summarize.py           # New (v2.1+)
│
├── .ontos-internal/                     # PROJECT documentation
│   ├── kernel/
│   │   └── mission.md                   # Marker file
│   ├── strategy/
│   │   └── v2_strategy.md
│   ├── product/
│   │   └── v2_roadmap.md
│   ├── atom/
│   │   ├── v2_architecture.md
│   │   └── schema.md
│   └── logs/
│       └── log_20251211_v2_planning.md
│
├── docs/                                # USER documentation (shipped)
│   ├── guides/
│   ├── reference/
│   └── _template.md
│
├── Ontos_Context_Map.md                 # Generated from .ontos-internal/
└── ...
```

### 8.2 User Project (User Mode)

```
user-project/
├── .ontos/
│   └── scripts/
│       └── ...                          # Copied from Ontos repo
│
├── docs/                                # User's documentation
│   ├── kernel/
│   │   └── mission.md
│   ├── strategy/
│   ├── product/
│   ├── atom/
│   └── logs/
│
├── Ontos_Context_Map.md                 # Generated from docs/
└── ...
```

---

## 9. Script Modifications Summary

### 9.1 Files to Modify

| File | Changes |
|------|---------|
| `ontos_config_defaults.py` | Add `log` to TYPE_DEFINITIONS, add `.ontos-internal/` to DEFAULT_SKIP_PATTERNS |
| `ontos_config.py` | Add smart configuration logic (is_ontos_repo, mode detection) |
| `ontos_generate_context_map.py` | Add Timeline section, token estimates, provenance header |
| `ontos_end_session.py` | Add `--event-type`, `--concepts`, `--impacts` flags; add auto-suggest |
| `ontos_validate.py` | Add log validation rules, impacts validation |

### 9.2 Files to Create

| File | Purpose |
|------|---------|
| `ontos_init.py` | Unified initialization: copies scripts + creates docs structure |
| `ontos_migrate_v2.py` | Optional: explicitly migrate v1.x logs to v2.0 schema |
| `ontos_summarize.py` | Generate 50-word summaries for documents (v2.1+) |

---

## 10. Backward Compatibility

### 10.1 Auto-Normalization of v1.x Logs

The parser automatically upgrades legacy logs without requiring manual migration:

```python
def normalize_document(doc: Document) -> Document:
    """Auto-normalize v1.x logs to v2.0 schema.

    Detection: type == 'atom' AND id starts with 'log_'
    """
    if doc.type == 'atom' and doc.id.startswith('log_'):
        # Upgrade to v2.0 log type
        doc.type = 'log'

        # Apply sensible defaults for missing fields
        if 'event_type' not in doc.frontmatter:
            doc.frontmatter['event_type'] = 'chore'  # Safe default

        if 'impacts' not in doc.frontmatter:
            doc.frontmatter['impacts'] = []  # Empty, but valid

        # Remove depends_on if present (logs don't use it)
        doc.frontmatter.pop('depends_on', None)

    return doc
```

**Behavior:**

| v1.x Document | Auto-Normalized To |
|---------------|-------------------|
| `type: atom`, `id: log_20251201_foo` | `type: log`, `event_type: chore`, `impacts: []` |
| `type: atom`, `id: api_spec` | No change (not a log) |
| `type: log` (already v2.0) | No change |

This means existing v1.x projects work immediately — no migration script required.

### 10.2 Existing Space Documents

- v1.x documents (kernel, strategy, product, atom) work unchanged
- No migration required for Space Ontology documents

### 10.3 Existing Context Maps

- v2.0 generator produces v2.0 format (with Timeline section)
- Old context maps are simply overwritten on next generation
- No migration needed — context maps are generated artifacts

### 10.4 Explicit Migration (Optional)

For teams who want explicit v2.0 schema in their files (not just runtime normalization):

**Option A: Use the migration script**

```bash
# Automated migration
python3 .ontos/scripts/ontos_migrate_v2.py

# What it does:
# 1. Finds all type: atom files in logs/ with id: log_*
# 2. Updates type to log
# 3. Sets event_type to chore (safe default)
# 4. Sets impacts to [] (empty, but valid)
# 5. Removes depends_on if present
# 6. Reports which files were modified
```

**Option B: Manual update**

```bash
# Find all legacy logs
find docs/logs -name "log_*.md" -exec grep -l "type: atom" {} \;

# Manual update per file:
# 1. Change type: atom → type: log
# 2. Add event_type: (feature|fix|refactor|exploration|chore)
# 3. Add impacts: [list of affected doc IDs]
# 4. Remove depends_on if present
```

**When to use explicit migration:**
- You want git history to show the schema change
- You want to set meaningful `event_type` values (not just `chore`)
- You want to populate `impacts` with actual document IDs

Auto-normalization handles everything else automatically.

---

## 11. Implementation Phases

### Phase 1: Structure (v2.0.x)

**Deliverables:**
1. ✅ Unified `ontos_init.py` (combines install + initiate)
2. ✅ Add `log` type to TYPE_DEFINITIONS
3. ✅ Implement log validation rules
4. ✅ Implement impacts validation
5. ✅ Add `--event-type`, `--concepts`, `--impacts` to end_session
6. ✅ Add auto-suggest impacts algorithm
7. ✅ Smart configuration (Contributor vs User mode)
8. ✅ Auto-normalization for v1.x logs
9. ✅ Optional `ontos_migrate_v2.py` script

**Exit criteria:** Can initialize project with one command, create logs with valid schema, impacts validate against Space Ontology, v1.x logs work without modification.

### Phase 2: Visibility (v2.1.x)

**Deliverables:**
1. Token estimation in context map
2. Timeline section in context map
3. Provenance header in context map

**Exit criteria:** Context map shows token costs and recent history.

### Phase 3: Intelligence (v2.2.x)

**Deliverables:**
1. `ontos_summarize.py` for frontmatter summaries
2. Auto-activation (check for context map at session start)
3. Pre-commit hook for archival enforcement

**Exit criteria:** Agents can read summaries, sessions are logged by default.

---

## 12. Error Messages Reference

| Code | Message | Resolution |
|------|---------|------------|
| `[MISSING FIELD]` | `{id}: log requires event_type` | Add `event_type` to frontmatter |
| `[MISSING FIELD]` | `{id}: log requires impacts` | Add `impacts` to frontmatter |
| `[INVALID FIELD]` | `{id}: log should not use depends_on` | Remove `depends_on`, use `impacts` instead |
| `[INVALID VALUE]` | `{id}: invalid event_type` | Use one of: feature, fix, refactor, exploration, chore |
| `[BROKEN LINK]` | `{id}: impacts references non-existent document "{ref}"` | Create the referenced document or fix the ID |

---

## 13. Testing Requirements

### 13.1 Unit Tests

```python
# tests/test_log_validation.py

def test_log_requires_event_type():
    doc = Document(id='test_log', type='log', status='active')
    errors = validate_log(doc)
    assert any('[MISSING FIELD]' in str(e) for e in errors)

def test_log_requires_impacts():
    doc = Document(id='test_log', type='log', status='active', event_type='feature')
    errors = validate_log(doc)
    assert any('impacts' in str(e) for e in errors)

def test_impacts_must_exist():
    log = Document(id='test_log', type='log', impacts=['nonexistent'])
    all_docs = {'other': Document(id='other', type='atom')}
    errors = validate_impacts(log, all_docs)
    assert any('[BROKEN LINK]' in str(e) for e in errors)

def test_valid_log_passes():
    log = Document(
        id='test_log',
        type='log',
        status='active',
        event_type='feature',
        impacts=['existing_doc']
    )
    all_docs = {
        'test_log': log,
        'existing_doc': Document(id='existing_doc', type='atom')
    }
    errors = validate_log(log) + validate_impacts(log, all_docs)
    assert len(errors) == 0
```

### 13.2 Integration Tests

```bash
# Test Contributor Mode
cd /path/to/project-ontos
python3 .ontos/scripts/ontos_generate_context_map.py
grep -q "Mode: Contributor" Ontos_Context_Map.md

# Test User Mode
cd /tmp && mkdir test-project && cd test-project
cp -r /path/to/project-ontos/.ontos .
mkdir -p docs/atom
echo -e "---\nid: test\ntype: atom\nstatus: active\n---\n# Test" > docs/atom/test.md
python3 .ontos/scripts/ontos_generate_context_map.py
grep -q "Mode: User" Ontos_Context_Map.md
```

---

## Appendix A: Full Frontmatter Examples

**Kernel Document:**
```yaml
---
id: mission
type: kernel
status: active
---
```

**Strategy Document:**
```yaml
---
id: v2_strategy
type: strategy
status: active
depends_on: [mission]
---
```

**Product Document:**
```yaml
---
id: v2_roadmap
type: product
status: draft
depends_on: [v2_strategy]
---
```

**Atom Document:**
```yaml
---
id: auth_flow
type: atom
status: active
depends_on: [api_spec]
summary: "OAuth 2.0 implementation with JWT tokens. Supports refresh flow."
---
```

**Log Document:**
```yaml
---
id: log_20251210_auth_refactor
type: log
status: active
event_type: refactor
concepts: [auth, oauth, security]
impacts: [auth_flow, api_spec]
---
```

---

## Appendix B: Why Auto-Normalization?

v1.x logs used `type: atom` because `log` wasn't a valid type. v2.0 adds `log` as a first-class type.

**The problem:** Requiring manual migration creates friction. Teams with dozens of logs won't upgrade.

**The solution:** Auto-normalize at parse time. The parser detects `type: atom` + `id: log_*` and internally treats it as `type: log`. The original file is unchanged, but the system behaves as if it were v2.0.

**Why this is safe:**
- Detection is unambiguous (`id` prefix is a strong signal)
- Defaults are conservative (`event_type: chore`, `impacts: []`)
- Original files are never modified
- Users can opt into explicit v2.0 schema whenever they want

**For users who want explicit migration:** Run `ontos_migrate_v2.py` to update files in place. This is optional — auto-normalization handles everything automatically.

This follows the Ontos philosophy: **intent over automation, but zero friction for adoption.**
