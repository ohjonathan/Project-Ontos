# Project Ontos: Codebase Map

**Purpose:** Technical architecture reference for deep codebase analysis
**Generated:** 2025-12-18
**Version:** 2.6.2
**Total:** ~6,800 lines Python across 16 scripts + 16 test files

---

## I. DIRECTORY STRUCTURE

```
Project-Ontos/
├── .ontos/                          # Core toolkit (portable)
│   ├── scripts/                     # Python scripts (16 total)
│   │   ├── ontos_lib.py             # Shared library (679 lines)
│   │   ├── ontos_config_defaults.py # Mode presets, constants (282 lines)
│   │   ├── ontos_config.py          # Generated user config (imports defaults)
│   │   ├── ontos_generate_context_map.py  # Graph builder (1,043 lines)
│   │   ├── ontos_end_session.py     # Session archival (1,625 lines)
│   │   ├── ontos_consolidate.py     # Log consolidation (396 lines)
│   │   ├── ontos_pre_push_check.py  # Pre-push hook logic (385 lines)
│   │   ├── ontos_pre_commit_check.py # Pre-commit hook logic (252 lines)
│   │   ├── ontos_query.py           # Graph queries (308 lines)
│   │   ├── ontos_maintain.py        # Maintenance orchestrator (298 lines)
│   │   ├── ontos_update.py          # Self-update from GitHub (508 lines)
│   │   ├── ontos_install_hooks.py   # Hook installer (182 lines)
│   │   ├── ontos_migrate_frontmatter.py # Find untagged files (183 lines)
│   │   ├── ontos_migrate_v2.py      # v1 to v2 migration (127 lines)
│   │   ├── ontos_summarize.py       # Doc summarizer (175 lines)
│   │   └── ontos_remove_frontmatter.py # Strip YAML headers (167 lines)
│   ├── hooks/                       # Git hook scripts
│   │   ├── pre-push               # Bash wrapper calls Python
│   │   └── pre-commit             # Bash wrapper calls Python
│   └── templates/                   # Starter doc templates
│       ├── templates.py             # Template loader module
│       ├── ontos_config.py.template # Config template with placeholders
│       ├── decision_history_template.md
│       └── common_concepts_template.md
│
├── .ontos-internal/                 # Contributor-mode docs (Ontos itself)
│   ├── kernel/
│   │   └── mission.md
│   ├── strategy/
│   │   ├── v2_strategy.md
│   │   ├── decision_history.md
│   │   └── proposals/              # Draft proposals
│   │       └── v2.7/
│   ├── atom/
│   │   └── schema.md
│   ├── reference/
│   │   ├── Common_Concepts.md
│   │   └── Dual_Mode_Matrix.md
│   ├── archive/
│   │   ├── logs/                   # Consolidated logs
│   │   └── proposals/              # Rejected proposals
│   └── logs/                        # Active session logs
│
├── docs/                            # User-mode docs (when installed in project)
│   └── [mirrors .ontos-internal structure]
│
├── tests/                           # Pytest test suite
│   ├── conftest.py                  # Fixtures, mode selection
│   └── test_*.py                    # 16 test files
│
├── ontos_init.py                    # Bootstrap script
├── Ontos_Context_Map.md             # Generated knowledge graph index
├── Ontos_CHANGELOG.md               # Version history
└── README.md                        # Public documentation
```

---

## II. CORE MODULES

### 1. ontos_lib.py (679 lines) — Shared Library

The utility backbone. All other scripts import from here.

**Key Functions:**

| Function | Purpose | Used By |
|----------|---------|---------|
| `parse_frontmatter(filepath)` | Extract YAML frontmatter from markdown | All scripts |
| `normalize_type(type_value)` | Normalize doc type strings | Context map, query |
| `normalize_depends_on(deps)` | Normalize dependency lists | Context map, query |
| `resolve_config(key, default)` | Mode-aware config resolution | All scripts |
| `get_logs_dir()` | Mode-aware path to logs directory | Consolidate, hooks |
| `get_proposals_dir()` | Mode-aware path to proposals | End session, maintain |
| `get_decision_history_path()` | Mode-aware path to history file | Consolidate, maintain |
| `get_archive_dir()` | Mode-aware path to archive | Consolidate, hooks |
| `is_ontos_repo()` | Detect contributor vs user mode | All scripts |
| `load_common_concepts()` | Load concept vocabulary from file | End session |
| `find_last_session_date()` | Find most recent log date | End session |
| `get_git_last_modified(path)` | Get file's last commit date | Query (stale detection) |
| `find_draft_proposals()` | Find status:draft proposals | Maintain |
| `get_log_count()` | Count active logs | Pre-commit hook |
| `get_source()` | Get source from env/config chain | End session |

**Mode Detection Algorithm:**
```python
def is_ontos_repo():
    """True if .ontos-internal/ exists (contributor mode)."""
    return os.path.exists(os.path.join(PROJECT_ROOT, '.ontos-internal'))
```

**Config Resolution Chain:**
```
1. User's ontos_config.py (if exists)
2. Environment variable ONTOS_{KEY}
3. Mode preset from ontos_config_defaults.py
4. Hardcoded default
```

---

### 2. ontos_config_defaults.py (282 lines) — Configuration System

Defines mode presets and default values.

**Mode Presets:**

```python
MODE_PRESETS = {
    'automated': {
        'ENFORCE_ARCHIVE_BEFORE_PUSH': False,   # Auto-archive instead
        'AUTO_ARCHIVE_ON_PUSH': True,           # Create logs automatically
        'AUTO_CONSOLIDATE_ON_COMMIT': True,     # Consolidate on commit
        'REQUIRE_SOURCE_IN_LOGS': False,        # Don't require source
    },
    'prompted': {  # DEFAULT
        'ENFORCE_ARCHIVE_BEFORE_PUSH': True,    # Block until archived
        'AUTO_ARCHIVE_ON_PUSH': False,          # Manual archive
        'AUTO_CONSOLIDATE_ON_COMMIT': False,    # Manual consolidation
        'REQUIRE_SOURCE_IN_LOGS': True,         # Require source
    },
    'advisory': {
        'ENFORCE_ARCHIVE_BEFORE_PUSH': False,   # Warning only
        'AUTO_ARCHIVE_ON_PUSH': False,          # Manual
        'AUTO_CONSOLIDATE_ON_COMMIT': False,    # Manual
        'REQUIRE_SOURCE_IN_LOGS': False,        # Optional
    }
}
```

**Key Constants:**

| Constant | Value | Purpose |
|----------|-------|---------|
| `ONTOS_VERSION` | "2.6.2" | Current version |
| `LOG_RETENTION_COUNT` | 10 | Keep newest N logs |
| `LOG_WARNING_THRESHOLD` | 20 | Warn when exceeds |
| `CONSOLIDATION_THRESHOLD_DAYS` | 30 | Age-based fallback |
| `HOOK_TIMEOUT_SECONDS` | 10 | Max hook runtime |
| `SMALL_CHANGE_THRESHOLD` | 20 | Lines for "small" |
| `BLOCKED_BRANCH_NAMES` | ['main', 'master', 'develop', 'dev'] | Skip auto-slug |

---

### 3. ontos_generate_context_map.py (1,043 lines) — Graph Engine

The core graph builder and validator.

**Main Entry Point:**
```python
def main():
    files_data = scan_docs(docs_dir)      # 1. Scan all .md files
    files_data = validate_and_filter()     # 2. Filter by status
    errors = validate_graph(files_data)    # 3. Run integrity checks
    output = generate_output(files_data)   # 4. Build markdown output
    write_context_map(output)              # 5. Write to file
```

**Graph Validation Checks:**

| Check | Function | Error Type |
|-------|----------|------------|
| Broken Links | `check_broken_links()` | `[BROKEN LINK]` |
| Cycles | `detect_cycles()` | `[CYCLE]` |
| Orphans | `find_orphans()` | `[ORPHAN]` |
| Depth | `check_depth()` | `[DEPTH]` |
| Architecture | `check_architecture_violations()` | `[ARCHITECTURE]` |

**Type Hierarchy (Rank):**
```python
TYPE_HIERARCHY = {
    'kernel': 0,    # Highest (depends on nothing)
    'strategy': 1,
    'product': 2,
    'atom': 3,
    'log': 4        # Lowest (logs use impacts, not depends_on)
}
```

**Architecture Violation Rule:**
```python
def is_architecture_violation(from_type, to_type):
    """Lower rank cannot depend on higher rank."""
    from_rank = TYPE_HIERARCHY.get(from_type, 99)
    to_rank = TYPE_HIERARCHY.get(to_type, 99)
    return from_rank < to_rank  # e.g., atom (3) depends on log (4) = violation
```

**Type-Status Matrix (v2.6):**
```python
VALID_TYPE_STATUS = {
    'kernel': ['active'],
    'strategy': ['active', 'draft', 'deprecated'],
    'product': ['active', 'draft', 'deprecated'],
    'atom': ['active', 'draft', 'deprecated'],
    'log': ['active', 'auto-generated', 'archived'],
    'review': ['complete', 'draft'],
}
```

**Cycle Detection Algorithm (Tarjan's):**
```python
def detect_cycles(graph):
    """Detect cycles using DFS with coloring."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    cycles = []

    def dfs(node, path):
        color[node] = GRAY
        for neighbor in graph.get(node, []):
            if color[neighbor] == GRAY:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
            elif color[neighbor] == WHITE:
                dfs(neighbor, path + [neighbor])
        color[node] = BLACK

    for node in graph:
        if color[node] == WHITE:
            dfs(node, [node])

    return cycles
```

**Token Estimation:**
```python
def estimate_tokens(filepath):
    """Estimate token count (word_count * 1.3)."""
    with open(filepath) as f:
        content = f.read()
    word_count = len(content.split())
    return int(word_count * 1.3)
```

**Output Sections Generated:**
1. Hierarchy Tree (by type)
2. Dependency Audit (errors)
3. Index (ID → File mapping)
4. Stats (doc counts, token estimates)

---

### 4. ontos_end_session.py (1,625 lines) — Session Archival

The most complex script. Handles session logging and changelog integration.

**Main Workflows:**

```
Normal Mode:
  1. Auto-generate or prompt for slug
  2. Validate slug format
  3. Get event type (feature/fix/refactor/etc.)
  4. Suggest impacts from git diff
  5. Validate concepts against vocabulary
  6. Create log file with adaptive template
  7. Detect and optionally graduate proposals

Auto Mode (--auto, called by pre-push hook):
  1. Get current branch
  2. Infer event type from branch prefix
  3. Get commits since last push
  4. Create or append to today's log
  5. Create archive marker

Enhance Mode (--enhance):
  1. Find auto-generated log for current branch
  2. Display log content
  3. Print instructions for enrichment
```

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `create_log_file()` | Create new session log with template |
| `auto_archive()` | Create auto-generated log for hook |
| `append_to_log()` | Add commits to existing log |
| `find_existing_log_for_today()` | Find log to append to |
| `validate_branch_in_log()` | Prevent wrong-branch appending |
| `suggest_impacts()` | Auto-detect impacted docs from git |
| `validate_concepts()` | Check concepts against vocabulary |
| `detect_implemented_proposal()` | Find proposals matching branch |
| `graduate_proposal()` | Move proposal from proposals/ to strategy/ |
| `generate_template_sections()` | Adaptive template by event type |

**Adaptive Templates:**

| Event Type | Sections |
|------------|----------|
| `chore` | Goal, Changes Made |
| `fix` | Goal, Changes Made, Next Steps |
| `feature` | Goal, Key Decisions, Changes Made, Next Steps |
| `refactor` | Goal, Key Decisions, Alternatives Considered, Changes Made |
| `exploration` | Goal, Key Decisions, Alternatives Considered, Next Steps |
| `decision` | All five sections |

**Impact Suggestion Algorithm:**
```python
def suggest_impacts():
    """Match changed files to doc IDs."""
    # 1. Get changed files from git status
    # 2. If clean, get today's commits
    # 3. Load doc index from context map
    # 4. Match files to doc IDs by path
    # 5. Filter out log documents
```

**Proposal Graduation Detection:**
```python
def detect_implemented_proposal(branch, impacts):
    """Heuristics for proposal detection."""
    # 1. Extract version patterns from branch (e.g., v2.6, v2-6)
    # 2. Scan proposals/ for status:draft files
    # 3. Match by:
    #    - Branch version matches filepath/ID
    #    - Session impacts the proposal
```

---

### 5. ontos_consolidate.py (396 lines) — Log Archival

Moves old logs to archive and updates decision_history.md.

**Entry Points:**

| Flag | Behavior |
|------|----------|
| `--count N` | Keep newest N logs (default: 15) |
| `--by-age` | Use age-based instead of count |
| `--days N` | Age threshold (default: 30) |
| `--all` | Process without prompting |
| `--dry-run` | Preview only |

**Consolidation Flow:**
```
1. find_excess_logs()           # Find logs exceeding retention count
2. For each log:
   a. extract_summary()         # Get Goal section as summary
   b. archive_log()             # Move to archive/logs/
   c. append_to_decision_history()  # Add row to ledger
```

**Decision History Format:**
```markdown
| Date | Slug | Event | Decision / Outcome | Impacted | Archive Path |
|:-----|:-----|:------|:-------------------|:---------|:-------------|
| 2025-12-17 | v2-6 | feature | Added type-status matrix | schema | archive/... |
```

---

### 6. ontos_pre_push_check.py (385 lines) — Pre-Push Hook

Called by bash hook. Controls push blocking/archiving behavior.

**Decision Flow:**
```python
def main():
    regenerate_context_map()           # 1. Ensure map is current
    check_log_count_warning()          # 2. Warn if logs exceed threshold
    check_version_reminder()           # 3. Remind contributors about changelog

    if marker_exists():                # 4. Session already archived?
        delete_marker()
        return 0  # Allow push

    if AUTO_ARCHIVE_ON_PUSH:           # 5. Automated mode?
        run_auto_archive()
        return 0

    if ENFORCE_ARCHIVE_BEFORE_PUSH:    # 6. Prompted mode?
        print_blocking_message()
        return 1  # Block push
    else:                              # 7. Advisory mode
        print_advisory_message()
        return 0
```

**Marker File System:**
```
.ontos/session_archived
├── archived=2025-12-18T10:30:00
└── log=docs/logs/2025-12-18_feature-x.md
```

---

### 7. ontos_pre_commit_check.py (252 lines) — Pre-Commit Hook

Auto-consolidation on commit (automated mode only).

**Safety Features:**
```python
def should_consolidate():
    # Skip if:
    if mode != 'automated': return False
    if is_ci_environment(): return False
    if is_special_git_operation(): return False  # Rebase, cherry-pick
    if os.environ.get('ONTOS_SKIP_HOOKS'): return False

    # Trigger if:
    log_count = get_log_count()
    return log_count > LOG_WARNING_THRESHOLD  # 20
```

**CI Detection:**
```python
CI_INDICATORS = [
    'CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS',
    'GITLAB_CI', 'JENKINS_URL', 'CIRCLECI', 'BUILDKITE', 'TF_BUILD'
]
```

---

### 8. ontos_query.py (308 lines) — Graph Queries

CLI for querying the knowledge graph.

**Query Types:**

| Query | Command | Returns |
|-------|---------|---------|
| Dependencies | `--depends-on ID` | What ID depends on |
| Reverse deps | `--depended-by ID` | What depends on ID |
| By concept | `--concept TAG` | Docs with concept |
| Stale docs | `--stale DAYS` | Docs not updated in N days |
| Health | `--health` | Graph metrics |
| List | `--list-ids` | All document IDs |

**Health Metrics:**
```python
{
    'total_docs': 42,
    'by_type': {'kernel': 1, 'strategy': 5, 'atom': 20, 'log': 16},
    'orphans': 3,
    'orphan_ids': ['unused_spec', ...],
    'empty_impacts': 5,
    'connectivity': 95.2,  # % reachable from kernel
    'reachable_from_kernel': 40
}
```

---

### 9. ontos_maintain.py (298 lines) — Maintenance Orchestrator

Runs maintenance tasks in sequence.

**Steps:**
```
1. ontos_migrate_frontmatter.py  # Find untagged files
2. ontos_generate_context_map.py # Rebuild graph
3. ontos_consolidate.py          # Consolidate excess logs
4. review_proposals()            # Prompt to graduate proposals
```

---

### 10. ontos_init.py (563 lines) — Bootstrap

Located at project root. Initializes Ontos for new projects.

**Initialization Steps:**
```
1. Verify .ontos/scripts exists
2. Prompt for mode (automated/prompted/advisory)
3. Prompt for default source name
4. Generate ontos_config.py
5. Create directory structure
6. Install git hooks
7. Create starter docs
8. Generate initial context map
```

**Directory Structure Created:**
```
docs/
├── logs/
├── strategy/
│   └── proposals/
├── archive/
│   ├── logs/
│   └── proposals/
└── reference/
```

---

## III. DATA FORMATS

### Frontmatter Schema

**Space Documents (kernel, strategy, product, atom):**
```yaml
---
id: unique_identifier           # Required, snake_case
type: atom                      # Required: kernel|strategy|product|atom
status: active                  # Required: active|draft|deprecated|archived|rejected
depends_on: [parent_id]         # Optional, list of IDs
concepts: [auth, security]      # Optional, list of tags
---
```

**Time Documents (logs):**
```yaml
---
id: log_20251218_feature_x      # Required, includes date
type: log                       # Required
status: active                  # active|auto-generated|archived
event_type: feature             # feature|fix|refactor|exploration|chore|decision
branch: feat/feature-x          # Optional, for validation
concepts: [auth]                # Optional
impacts: [auth_flow, api_spec]  # Connects to Space documents
---
```

**Review Documents:**
```yaml
---
id: claude_v2_7_review
type: review
status: complete                # complete|draft
depends_on: [v2_7_proposal]
---
```

**Rejected Proposals:**
```yaml
---
id: rejected_feature
type: strategy
status: rejected
rejected_reason: "Does not align with v2 philosophy" # Required, min 10 chars
rejected_date: 2025-12-15
---
```

### Configuration Format

**ontos_config.py:**
```python
"""Ontos Configuration."""

ONTOS_MODE = "prompted"         # automated|prompted|advisory
DEFAULT_SOURCE = "Claude"       # Or None to prompt each time

# Custom overrides (optional)
DOCS_DIR = "documentation"      # Default: "docs"
LOG_RETENTION_COUNT = 20        # Default: 10

# Import defaults (required)
from .ontos.scripts.ontos_config_defaults import *
```

### Context Map Format

**Ontos_Context_Map.md:**
```markdown
# Ontos Context Map

## 1. Hierarchy Tree

### KERNEL
- **mission** (mission.md) ~377 tokens
  - Status: active
  - Depends On: None

### STRATEGY
- **v2_strategy** (v2_strategy.md) ~2,600 tokens
  - Status: active
  - Depends On: mission

## 2. Dependency Audit
[BROKEN LINK] doc_a references missing ID: nonexistent
[ARCHITECTURE] atom_doc (atom) depends on log_doc (log)

## 3. Index
| ID | File | Type | Status |
|:---|:-----|:-----|:-------|
| mission | mission.md | kernel | active |

## 4. Stats
- Total: 42 documents
- By type: kernel (1), strategy (5), product (3), atom (20), log (13)
- Estimated tokens: ~45,000
```

---

## IV. DATA FLOW DIAGRAMS

### 1. Session Archival Flow

```
[Developer Work] → [git commit]
        ↓
[git push] → [pre-push hook]
        ↓
[ontos_pre_push_check.py]
        ↓
   ┌────┴────────────────────────────────────┐
   │                                          │
   ▼                                          ▼
[Marker exists?] ──YES──> [Delete marker] → [ALLOW PUSH]
   │
   NO
   ↓
[Mode = automated?] ──YES──> [auto_archive()] → [ALLOW]
   │
   NO
   ↓
[Mode = prompted?] ──YES──> [Block with message] → [BLOCK]
   │
   NO (advisory)
   ↓
[Print reminder] → [ALLOW PUSH]
```

### 2. Context Map Generation Flow

```
[.md files in docs/]
        ↓
[scan_docs()] ──────> Parse frontmatter
        ↓                    ↓
[files_data dict] ────> {id: {type, status, depends_on, ...}}
        ↓
[validate_and_filter()] ──> Filter archived/rejected
        ↓
[validate_graph()]
        ├── check_broken_links()
        ├── detect_cycles()
        ├── find_orphans()
        ├── check_depth()
        └── check_architecture_violations()
        ↓
[generate_output()]
        ├── Hierarchy tree
        ├── Dependency audit
        ├── Index table
        └── Stats
        ↓
[Ontos_Context_Map.md]
```

### 3. Log Consolidation Flow

```
[Active logs in logs/]
        ↓
[find_excess_logs(retention_count=10)]
        ↓
[Logs to consolidate]
        ↓
   For each log:
        ↓
[extract_summary()] ──> Goal section first line
        ↓
[archive_log()] ──> Move to archive/logs/
        ↓
[append_to_decision_history()]
        ↓
   Add row to History Ledger table
        ↓
[decision_history.md updated]
```

### 4. Proposal Lifecycle

```
[New Proposal]
        ↓
[Create in proposals/] ──> status: draft
        ↓
[Work on feature branch]
        ↓
[Archive Ontos] ──> detect_implemented_proposal()
        ↓
[Match found?] ──YES──> [Prompt: Graduate?]
        │                       ↓
        │               [graduate_proposal()]
        │                       ├── Move to strategy/
        │                       ├── Change status: draft → active
        │                       └── Add to decision_history.md
        │
        └──NO──> [Stay as draft]

[Rejection Path]
        ↓
[Add rejected_reason, rejected_date]
        ↓
[Move to archive/proposals/]
```

---

## V. TESTING INFRASTRUCTURE

### Test Files (16 files, ~80KB)

| Test File | Lines | Coverage Area |
|-----------|-------|---------------|
| `test_v26_validation.py` | 730 | Type-status matrix, rejection metadata |
| `test_orphan_detection.py` | 340 | Orphan, depth, architecture checks |
| `test_yaml_edge_cases.py` | 316 | Frontmatter parsing edge cases |
| `test_lint.py` | 268 | Data quality linting |
| `test_cycle_detection.py` | 220 | Graph cycle detection |
| `test_pre_commit_check.py` | 348 | Pre-commit hook logic |
| `test_end_session.py` | 175 | Session archival |
| `test_frontmatter_parsing.py` | 140 | YAML parsing |
| `test_query.py` | 115 | Graph queries |
| `test_config.py` | 137 | Config resolution |
| `test_consolidate.py` | 97 | Log consolidation |
| `test_pre_push_check.py` | 95 | Pre-push hook |
| `test_migrate_frontmatter.py` | 103 | Untagged file detection |
| `test_maintain.py` | 82 | Maintenance orchestrator |
| `test_dual_mode.py` | 79 | Contributor vs user mode |
| `test_lib.py` | 132 | Library functions |

### conftest.py Fixtures

```python
@pytest.fixture
def temp_docs_dir(tmp_path):
    """Create temporary docs structure."""

@pytest.fixture
def mock_git_repo(tmp_path):
    """Create temporary git repository."""

@pytest.fixture
def contributor_mode(monkeypatch):
    """Simulate contributor mode."""

@pytest.fixture
def user_mode(monkeypatch):
    """Simulate user mode."""
```

### Dual-Mode Testing

```bash
# Run as contributor
pytest --mode=contributor

# Run as user
pytest --mode=user

# Default: contributor (since .ontos-internal exists)
pytest
```

---

## VI. KEY ALGORITHMS

### 1. Mode-Aware Path Resolution

```python
def get_logs_dir():
    """Return logs directory based on mode."""
    if is_ontos_repo():
        return PROJECT_ROOT / '.ontos-internal' / 'logs'
    else:
        docs_dir = resolve_config('DOCS_DIR', 'docs')
        return PROJECT_ROOT / docs_dir / 'logs'
```

### 2. Config Resolution Chain

```python
def resolve_config(key, default):
    """
    Resolution order:
    1. User's ontos_config.py
    2. Environment variable ONTOS_{KEY}
    3. Mode preset (from ONTOS_MODE)
    4. Default parameter
    """
    # Try user config
    try:
        import ontos_config
        if hasattr(ontos_config, key):
            return getattr(ontos_config, key)
    except ImportError:
        pass

    # Try environment
    env_key = f'ONTOS_{key}'
    if env_key in os.environ:
        return parse_env_value(os.environ[env_key])

    # Try mode preset
    mode = get_current_mode()
    if mode in MODE_PRESETS and key in MODE_PRESETS[mode]:
        return MODE_PRESETS[mode][key]

    return default
```

### 3. Slug Collision Handling

```python
def find_existing_log_for_today(branch_slug, branch_name):
    """
    Handle multiple branches with same slug:
    1. Try exact match: 2025-12-18_feature-x.md
    2. Validate branch field matches
    3. Try collision variants: 2025-12-18_feature-x-2.md
    """
    today = datetime.now().strftime('%Y-%m-%d')

    exact = f"{today}_{branch_slug}.md"
    if os.path.exists(exact):
        if validate_branch_in_log(exact, branch_name):
            return exact
        # Collision! Different branch

    for i in range(2, 100):
        variant = f"{today}_{branch_slug}-{i}.md"
        if os.path.exists(variant):
            if validate_branch_in_log(variant, branch_name):
                return variant

    return None
```

### 4. Impact Suggestion from Git Diff

```python
def suggest_impacts():
    """
    1. Get changed files from git status (uncommitted)
    2. If clean, get files from today's commits
    3. Load doc index from context map
    4. Match by:
       - Direct path match
       - Directory containment
    5. Filter out log documents
    """
```

---

## VII. EXTENSION POINTS

### Adding a New Document Type

1. Add to `TYPE_HIERARCHY` in `ontos_generate_context_map.py`
2. Add to `VALID_TYPE_STATUS` matrix
3. Update validation logic in `normalize_type()`
4. Add tests in `test_v26_validation.py`

### Adding a New Config Option

1. Add default to `MODE_PRESETS` or constants in `ontos_config_defaults.py`
2. Use `resolve_config()` to read it
3. Document in `Dual_Mode_Matrix.md`
4. Add tests for all three modes

### Adding a New Hook

1. Create `ontos_{hook_name}_check.py` in scripts/
2. Create bash wrapper in `.ontos/hooks/`
3. Add installation logic to `ontos_init.py`
4. Add tests

---

## VIII. DEPENDENCIES

**Runtime:**
- Python 3.9+
- Standard library only (no pip install)

**Used Standard Library Modules:**
- `os`, `sys`, `re` — File operations, paths
- `argparse` — CLI argument parsing
- `datetime` — Date handling
- `subprocess` — Git commands
- `shutil` — File operations
- `collections.defaultdict` — Graph building
- `typing` — Type hints

**Development:**
- `pytest` — Testing framework
- `pytest-cov` — Coverage (optional)

---

## IX. ERROR HANDLING PATTERNS

### 1. Graceful Degradation

```python
# Hooks never crash the workflow
def main():
    try:
        # Hook logic
        return result
    except Exception as e:
        print(f"Warning: {e}")
        return 0  # Never block
```

### 2. Fallback Chains

```python
# Config resolution: user → env → preset → default
value = resolve_config('KEY', 'default')

# Path resolution: mode-aware → fallback
path = get_logs_dir() or 'docs/logs'

# Git operations: try multiple approaches
result = git_log_since_upstream() or git_log_last_n(5)
```

### 3. Validation with Warnings

```python
# Unknown concept = warning, not error
if concept not in known_concepts:
    print(f"⚠️  Unknown concept '{concept}'")
    # Still include it
    validated.append(concept)
```

---

## X. PERFORMANCE CHARACTERISTICS

| Operation | Typical Time | Notes |
|-----------|-------------|-------|
| Context map generation | 50-200ms | Scales with doc count |
| Pre-push hook | <500ms | Includes map regen |
| Pre-commit hook | <100ms | Count check only |
| Log consolidation | 100-500ms | Per log archived |
| Query (--health) | 50-100ms | Full graph traversal |

**Optimization Notes:**
- Token estimation: word_count × 1.3 (fast approximation)
- Git operations: subprocess with timeout
- Frontmatter parsing: only reads first 2KB for status checks
- Cycle detection: O(V+E) using Tarjan's algorithm

---

*End of codebase map. Total: ~5,500 words, ~7,500 tokens.*
