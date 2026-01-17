---
id: ontos_codebase_map
type: atom
status: draft
depends_on: [philosophy]
concepts: [architecture, codebase, reference, technical]
---

# Project Ontos: Codebase Map

**Purpose:** Technical architecture reference for deep codebase analysis
**Generated:** 2026-01-08
**Version:** 2.9.5
**Total:** ~11,500 lines Python across 25+ scripts + 6 test files (132 tests)

---

## I. DIRECTORY STRUCTURE

```
Project-Ontos/
├── ontos.py                         # Unified CLI dispatcher (NEW in v2.8)
├── install.py                       # Curl-bootstrapped installer (NEW in v2.9.3)
├── ontos_init.py                    # Bootstrap script (563 lines)
├── checksums.json                   # SHA256 checksums per version
│
├── .ontos/                          # Core toolkit (portable)
│   ├── scripts/                     # Python scripts (25+ total)
│   │   ├── ontos/                   # NEW: Core package (v2.8+)
│   │   │   ├── __init__.py          # Package exports
│   │   │   ├── core/                # Pure logic layer
│   │   │   │   ├── __init__.py
│   │   │   │   ├── context.py       # SessionContext (271 lines)
│   │   │   │   ├── schema.py        # Schema versioning (421 lines)
│   │   │   │   ├── curation.py      # Curation levels (489 lines)
│   │   │   │   ├── staleness.py     # Describes validation (353 lines)
│   │   │   │   ├── history.py       # Decision history (263 lines)
│   │   │   │   ├── paths.py         # Path helpers (345 lines)
│   │   │   │   ├── frontmatter.py   # Pure parsing (122 lines)
│   │   │   │   ├── config.py        # Config helpers (83 lines)
│   │   │   │   └── proposals.py     # Proposal management (134 lines)
│   │   │   └── ui/                  # I/O layer
│   │   │       ├── __init__.py
│   │   │       └── output.py        # OutputHandler (108 lines)
│   │   │
│   │   ├── ontos_lib.py             # Re-export shim (95 lines, deprecated)
│   │   ├── ontos_config_defaults.py # Mode presets, constants (282 lines)
│   │   ├── ontos_config.py          # Generated user config
│   │   ├── ontos_generate_context_map.py  # Graph builder (1,043 lines)
│   │   ├── ontos_end_session.py     # Session archival (1,625 lines)
│   │   ├── ontos_consolidate.py     # Log consolidation (396 lines)
│   │   ├── ontos_pre_push_check.py  # Pre-push hook logic (385 lines)
│   │   ├── ontos_pre_commit_check.py # Pre-commit hook logic (252 lines)
│   │   ├── ontos_query.py           # Graph queries (308 lines)
│   │   ├── ontos_maintain.py        # Maintenance orchestrator (298 lines)
│   │   ├── ontos_update.py          # Self-update from GitHub (521 lines)
│   │   ├── ontos_verify.py          # Staleness verification (316 lines)
│   │   ├── ontos_scaffold.py        # L0 scaffold generation (275 lines)
│   │   ├── ontos_stub.py            # L1 stub creation (280 lines)
│   │   ├── ontos_promote.py         # L0/L1 → L2 promotion (NEW)
│   │   ├── ontos_migrate_schema.py  # Schema migration (NEW)
│   │   ├── ontos_create_bundle.py   # Bundle for releases (NEW)
│   │   ├── ontos_migrate_frontmatter.py # Find untagged files (183 lines)
│   │   ├── ontos_migrate_v2.py      # v1 to v2 migration (127 lines)
│   │   ├── ontos_summarize.py       # Doc summarizer (175 lines)
│   │   └── tests/                   # Pytest test suite (6 files, 132 tests)
│   │       ├── conftest.py          # Fixtures, mode selection
│   │       ├── test_context.py      # SessionContext tests (20 tests)
│   │       ├── test_schema.py       # Schema versioning (42 tests)
│   │       ├── test_curation.py     # Curation levels (48 tests)
│   │       ├── test_promote.py      # Promotion tests (16 tests)
│   │       └── test_deprecation.py  # Deprecation warnings (7 tests)
│   │
│   ├── hooks/                       # Git hook scripts
│   │   ├── pre-push                 # Bash wrapper calls Python
│   │   └── pre-commit               # Bash wrapper calls Python
│   └── templates/                   # Starter doc templates
│       ├── templates.py             # Template loader module
│       └── *.template               # Various templates
│
├── .ontos-internal/                 # Contributor-mode docs (Ontos itself)
│   ├── kernel/
│   │   └── mission.md
│   ├── strategy/
│   │   ├── master_plan.md           # v4.0 Strategic Plan
│   │   ├── v2_strategy.md
│   │   ├── decision_history.md      # Generated ledger
│   │   └── proposals/               # Draft proposals
│   │       ├── v3.0/                # v3.0 planning
│   │       └── Install_experience/  # Installation UX
│   ├── atom/
│   │   └── schema.md
│   ├── reference/
│   │   ├── Common_Concepts.md
│   │   └── Dual_Mode_Matrix.md
│   ├── archive/                     # Completed/rejected work
│   │   ├── logs/                    # Historical logs
│   │   ├── proposals/               # Archived proposals
│   │   └── strategy/                # Completed version plans
│   └── logs/                        # Active session logs
│
├── docs/                            # User-mode docs (when installed in project)
│   └── [mirrors .ontos-internal structure]
│
├── Ontos_Context_Map.md             # Generated knowledge graph index
├── Ontos_CHANGELOG.md               # Version history
└── README.md                        # Public documentation
```

---

## II. UNIFIED CLI (v2.8+)

### ontos.py — Command Dispatcher

Located at project root. Single entry point for all Ontos commands.

**Commands:**

| Command | Script | Purpose |
|---------|--------|---------|
| `log` | ontos_end_session.py | Create/enhance session logs |
| `map` | ontos_generate_context_map.py | Generate context map |
| `verify` | ontos_verify.py | Update describes_verified dates |
| `maintain` | ontos_maintain.py | Run maintenance tasks |
| `consolidate` | ontos_consolidate.py | Archive old logs |
| `query` | ontos_query.py | Query the graph |
| `update` | ontos_update.py | Update Ontos from GitHub |
| `migrate` | ontos_migrate_schema.py | Migrate schema versions |
| `scaffold` | ontos_scaffold.py | Generate L0 scaffolds |
| `stub` | ontos_stub.py | Create L1 stubs |
| `promote` | ontos_promote.py | Promote L0/L1 to L2 |

**Aliases (11 total):**

| Alias | Maps To | Natural Language |
|-------|---------|------------------|
| `archive` | `log` | "Archive this session" |
| `context` | `map` | "Generate context" |
| `check` | `verify` | "Check staleness" |
| `health` | `maintain` | "Health check" |
| `cleanup` | `consolidate` | "Clean up logs" |
| `search` | `query` | "Search the graph" |
| `upgrade` | `update` | "Upgrade Ontos" |
| `schema` | `migrate` | "Check schema" |
| `curate` | `scaffold` | "Curate documents" |
| `init` | `stub` | "Initialize doc" |
| `level-up` | `promote` | "Level up docs" |

**Usage:**
```bash
python3 ontos.py map              # Generate context map
python3 ontos.py log -e feature   # Archive session
python3 ontos.py promote --check  # Check promotable docs
python3 ontos.py --help           # Show all commands
```

---

## III. CORE PACKAGE (ontos/)

### Architecture Overview

```
ontos/
├── core/          # Pure logic (no I/O)
│   ├── context.py      # SessionContext — transactional file ops
│   ├── schema.py       # Schema versioning and validation
│   ├── curation.py     # Curation level detection and validation
│   ├── staleness.py    # Describes field staleness detection
│   ├── history.py      # Decision history generation
│   ├── paths.py        # Mode-aware path resolution
│   ├── frontmatter.py  # Pure YAML parsing
│   ├── config.py       # Configuration resolution
│   └── proposals.py    # Proposal management
└── ui/            # I/O layer
    └── output.py       # OutputHandler for display
```

### 1. context.py (271 lines) — SessionContext

Transactional file operations with two-phase commit.

**Key Classes:**

```python
class FileOperation(Enum):
    WRITE = "write"
    DELETE = "delete"
    MOVE = "move"

@dataclass
class PendingWrite:
    path: Path
    operation: FileOperation
    content: Optional[str] = None
    destination: Optional[Path] = None

@dataclass
class SessionContext:
    repo_root: Path
    config: Dict
    pending_writes: List[PendingWrite] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def buffer_write(self, path: Path, content: str) -> None
    def buffer_delete(self, path: Path) -> None
    def buffer_move(self, src: Path, dest: Path) -> None
    def commit(self) -> List[Path]  # Two-phase commit
    def rollback(self) -> None
    def warn(self, message: str) -> None
    def error(self, message: str) -> None

    @classmethod
    def from_repo(cls, repo_root: Path) -> "SessionContext"
```

**Two-Phase Commit Algorithm:**
```python
def commit(self) -> List[Path]:
    """Atomic commit: temp-then-rename for each file."""
    modified = []
    temp_files = []

    # Phase 1: Write to temp files
    for op in self.pending_writes:
        if op.operation == FileOperation.WRITE:
            temp_path = op.path.with_suffix(op.path.suffix + '.tmp')
            temp_path.write_text(op.content)
            temp_files.append((temp_path, op.path))

    # Phase 2: Atomic rename
    try:
        for temp_path, final_path in temp_files:
            temp_path.rename(final_path)  # Atomic on POSIX
            modified.append(final_path)
    except Exception:
        # Cleanup temp files on failure
        for temp_path, _ in temp_files:
            temp_path.unlink(missing_ok=True)
        raise

    self.pending_writes.clear()
    return modified
```

**Lock Management:**
```python
def _acquire_lock(self, lock_path: Path, timeout: float = 5.0) -> bool:
    """Acquire lock with stale detection (PID liveness check)."""
    # If lock exists, check if PID is alive
    # If PID dead, remove stale lock
    # Create lock with current PID

def _release_lock(self, lock_path: Path) -> None:
    """Release lock file."""
```

### 2. schema.py (421 lines) — Schema Versioning

Forward compatibility for v3.0 migration.

**Schema Version Definitions:**

| Schema | Required Fields | Introduced |
|--------|-----------------|------------|
| 1.0 | `id` | Legacy |
| 2.0 | `id`, `type` | v2.0 |
| 2.1 | `id`, `type` | v2.7 (describes) |
| 2.2 | `id`, `type`, `status` | v2.9 (curation) |
| 3.0 | `id`, `type`, `status`, `ontos_schema` | v3.0 |

**Key Functions:**

```python
def parse_version(version_str: str) -> Tuple[int, int]
def detect_schema_version(frontmatter: Dict) -> str
def check_compatibility(tool_version: str, doc_version: str) -> SchemaCheckResult
def validate_frontmatter(frontmatter: Dict, schema_version: str) -> List[str]
def serialize_frontmatter(frontmatter: Dict) -> str
```

**Compatibility Matrix:**

| Tool | Can Read |
|------|----------|
| v2.9 | 1.0, 2.0, 2.1, 2.2 |
| v3.0 | 1.0, 2.0, 2.1, 2.2, 3.0 |

### 3. curation.py (489 lines) — Curation Levels

Tiered validation to lower adoption friction.

**Curation Levels:**

| Level | Name | Required | Status |
|-------|------|----------|--------|
| 0 | Scaffold | `id`, `type` | `scaffold` |
| 1 | Stub | `id`, `type`, `status`, `goal` | `pending_curation` |
| 2 | Full | All + `depends_on`/`concepts` | `draft`, `active`... |

**Key Functions:**

```python
class CurationLevel(Enum):
    SCAFFOLD = 0
    STUB = 1
    FULL = 2

def detect_curation_level(frontmatter: Dict) -> CurationLevel
def validate_at_level(frontmatter: Dict, level: CurationLevel) -> List[str]
def create_scaffold(filepath: Path, doc_type: str) -> Dict
def create_stub(filepath: Path, doc_type: str, goal: str) -> Dict
def infer_type_from_path(filepath: Path) -> str
def infer_type_from_content(content: str) -> str
```

**Level Detection Algorithm:**
```python
def detect_curation_level(fm: Dict) -> CurationLevel:
    if fm.get('status') in ('scaffold',):
        return CurationLevel.SCAFFOLD
    if fm.get('status') in ('pending_curation',):
        return CurationLevel.STUB
    if 'depends_on' in fm or 'concepts' in fm:
        return CurationLevel.FULL
    if 'goal' in fm:
        return CurationLevel.STUB
    return CurationLevel.SCAFFOLD
```

### 4. staleness.py (353 lines) — Describes Validation

Track when documentation becomes stale after code changes.

**Key Concepts:**

```yaml
# Document declares what it describes:
---
id: ontos_manual
type: atom
describes: [ontos_end_session, ontos_maintain]
describes_verified: 2025-12-20
---
```

**Staleness Detection:**
```python
def check_staleness(doc_path: Path, frontmatter: Dict) -> List[StaleResult]:
    """Compare describes_verified against atom modification dates."""
    verified_date = frontmatter.get('describes_verified')
    describes = frontmatter.get('describes', [])

    stale = []
    for atom_id in describes:
        atom_mtime = get_file_modification_date(atom_id)
        if atom_mtime > verified_date:
            stale.append(StaleResult(
                doc_id=frontmatter['id'],
                atom_id=atom_id,
                verified=verified_date,
                atom_modified=atom_mtime
            ))
    return stale
```

### 5. history.py (263 lines) — Decision History

Immutable, deterministically generated decision ledger.

**Generation Algorithm:**
```python
def regenerate_decision_history(logs_dir: Path, archive_dir: Path) -> str:
    """Generate decision_history.md from archived logs."""
    entries = []

    # Scan archived logs
    for log_path in archive_dir.glob('*.md'):
        fm = parse_frontmatter(log_path)
        entries.append({
            'date': extract_date(log_path.name),
            'slug': extract_slug(log_path.name),
            'event': fm.get('event_type', 'chore'),
            'summary': extract_summary(log_path),
            'impacts': fm.get('impacts', []),
            'archive_path': str(log_path)
        })

    # Sort deterministically
    entries.sort(key=lambda e: (e['date'], e['event'], e['slug']), reverse=True)

    # Generate markdown table
    return render_history_table(entries)
```

### 6. paths.py (345 lines) — Path Resolution

Mode-aware path helpers with deprecation warnings.

**Key Functions:**

```python
def is_ontos_repo() -> bool
def get_logs_dir() -> Path
def get_proposals_dir() -> Path
def get_decision_history_path() -> Path
def get_archive_logs_dir() -> Path
def get_archive_proposals_dir() -> Path
def get_concepts_path() -> Path
```

**Mode Detection:**
```python
def is_ontos_repo() -> bool:
    """True if .ontos-internal/ exists (contributor mode)."""
    return (PROJECT_ROOT / '.ontos-internal').exists()

def get_logs_dir() -> Path:
    if is_ontos_repo():
        return PROJECT_ROOT / '.ontos-internal' / 'logs'
    else:
        docs_dir = resolve_config('DOCS_DIR', 'docs')
        return PROJECT_ROOT / docs_dir / 'logs'
```

### 7. output.py (108 lines) — OutputHandler

Centralized output formatting for pure/impure separation.

```python
class OutputHandler:
    def __init__(self, quiet: bool = False):
        self.quiet = quiet

    def info(self, message: str) -> None
    def success(self, message: str) -> None
    def warning(self, message: str) -> None
    def error(self, message: str) -> None
    def detail(self, message: str) -> None  # Indented context
    def display_errors(self, errors: List[str]) -> None
```

---

## IV. MAJOR SCRIPTS

### 1. ontos_generate_context_map.py (1,043 lines) — Graph Engine

**Main Flow:**
```python
def main():
    files_data = scan_docs(docs_dir)      # 1. Scan all .md files
    files_data = validate_and_filter()     # 2. Filter by status
    errors = validate_graph(files_data)    # 3. Run integrity checks
    regenerate_history()                   # 4. Rebuild decision_history.md
    check_staleness()                      # 5. Check describes field
    output = generate_output(files_data)   # 6. Build markdown output
    write_context_map(output)              # 7. Write to file
```

**Validation Checks (6 total):**

| Check | Function | Error Type |
|-------|----------|------------|
| Broken Links | `check_broken_links()` | `[BROKEN LINK]` |
| Cycles | `detect_cycles()` | `[CYCLE]` |
| Orphans | `find_orphans()` | `[ORPHAN]` |
| Depth | `check_depth()` | `[DEPTH]` |
| Architecture | `check_architecture_violations()` | `[ARCHITECTURE]` |
| Staleness | `check_staleness()` | `[STALE]` |

**Type Hierarchy:**
```python
TYPE_HIERARCHY = {
    'kernel': 0,    # Highest (depends on nothing)
    'strategy': 1,
    'product': 2,
    'atom': 3,
    'log': 4        # Lowest (logs use impacts, not depends_on)
}
```

**Context Map Sections:**
1. Hierarchy Tree (by type with [L0]/[L1]/[L2] markers)
2. Recent Timeline (last 5 logs)
3. Dependency Audit (errors)
4. Index (ID → File mapping)
5. Documentation Staleness Audit

### 2. ontos_end_session.py (1,625 lines) — Session Archival

The most complex script. Uses v2.8 transactional architecture.

**Main Workflows:**

```
Normal Mode:
  1. Auto-generate or prompt for slug
  2. Validate slug format
  3. Get event type (feature/fix/refactor/etc.)
  4. Suggest impacts from git diff
  5. Validate concepts against vocabulary
  6. Create log file via buffer_write()
  7. Detect and optionally graduate proposals
  8. Commit all changes atomically

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

**Transaction Pattern (_owns_ctx):**
```python
def create_log_file(ctx: SessionContext = None, _owns_ctx: bool = False):
    """Create log file with optional transaction ownership."""
    if ctx is None:
        ctx = SessionContext.from_repo(PROJECT_ROOT)
        _owns_ctx = True

    # Buffer all writes
    ctx.buffer_write(log_path, log_content)

    # Only commit if we own the context
    if _owns_ctx:
        ctx.commit()
```

### 3. install.py (Root) — Bootstrap Installer

Curl-bootstrapped installation with SHA256 verification.

**Usage:**
```bash
curl -sO https://raw.githubusercontent.com/ohjona/Project-Ontos/v2.9.5/install.py
python3 install.py
```

**Security Features:**

| Protection | Implementation |
|------------|----------------|
| Checksum verification | SHA256 from tag-aligned checksums.json |
| Path traversal | Rejects `..` and absolute paths |
| Symlink attacks | Rejects symlinks/hardlinks in archive |
| HTTPS only | No HTTP fallback |
| Retry logic | Exponential backoff on failures |

**Modes:**
- Fresh install: Downloads bundle, verifies checksums, extracts
- Upgrade (`--upgrade`): Merges config, rollback on failure
- Offline (`--bundle` + `--checksum`): Air-gapped installation

---

## V. DATA FORMATS

### Frontmatter Schema (v2.9.5)

**Space Documents (kernel, strategy, product, atom):**
```yaml
---
id: unique_identifier           # Required, snake_case
type: atom                      # Required: kernel|strategy|product|atom
status: active                  # Required: active|draft|deprecated|scaffold|pending_curation
depends_on: [parent_id]         # Optional, list of IDs
concepts: [auth, security]      # Optional, list of tags
describes: [atom_id]            # Optional (v2.7+), docs this describes
describes_verified: 2025-12-20  # Optional, last verification date
ontos_schema: "2.2"             # Optional (v3.0 will require)
---
```

**Time Documents (logs):**
```yaml
---
id: log_20251210_auth_refactor
type: log
status: active                  # active|auto-generated|archived
event_type: feature             # feature|fix|refactor|exploration|chore|decision
branch: feat/feature-x          # Optional, for validation
concepts: [auth]                # Optional
impacts: [auth_flow, api_spec]  # Connects to Space documents
---
```

### Curation Level Status Values

| Status | Level | Meaning |
|--------|-------|---------|
| `scaffold` | L0 | Auto-generated, minimal |
| `pending_curation` | L1 | Has goal, needs completion |
| `draft` | L2 | Work in progress |
| `active` | L2 | Current truth |
| `deprecated` | L2 | Past truth |
| `rejected` | L2 | Considered, not approved |
| `complete` | L2 | Finished (reviews) |

### Configuration Modes

```python
MODE_PRESETS = {
    'automated': {
        'ENFORCE_ARCHIVE_BEFORE_PUSH': False,
        'AUTO_ARCHIVE_ON_PUSH': True,
        'AUTO_CONSOLIDATE_ON_COMMIT': True,
        'REQUIRE_SOURCE_IN_LOGS': False,
    },
    'prompted': {  # DEFAULT
        'ENFORCE_ARCHIVE_BEFORE_PUSH': True,
        'AUTO_ARCHIVE_ON_PUSH': False,
        'AUTO_CONSOLIDATE_ON_COMMIT': False,
        'REQUIRE_SOURCE_IN_LOGS': True,
    },
    'advisory': {
        'ENFORCE_ARCHIVE_BEFORE_PUSH': False,
        'AUTO_ARCHIVE_ON_PUSH': False,
        'AUTO_CONSOLIDATE_ON_COMMIT': False,
        'REQUIRE_SOURCE_IN_LOGS': False,
    }
}
```

---

## VI. TESTING INFRASTRUCTURE

### Test Files (6 files, 132 tests)

| Test File | Tests | Coverage Area |
|-----------|-------|---------------|
| `test_context.py` | 20 | SessionContext, two-phase commit, locking |
| `test_schema.py` | 42 | Schema versioning, validation, serialization |
| `test_curation.py` | 48 | Curation levels, scaffolding, promotion |
| `test_promote.py` | 16 | L0/L1 → L2 promotion |
| `test_deprecation.py` | 7 | FutureWarning, CLI dispatch |
| `conftest.py` | - | Fixtures, mode selection |

### Key Test Patterns

**Transaction Testing:**
```python
def test_commit_creates_file(self, tmp_path):
    """commit() creates file with buffered content."""
    ctx = SessionContext(repo_root=tmp_path, config={})
    test_file = tmp_path / 'test.md'
    ctx.buffer_write(test_file, 'hello world')

    modified = ctx.commit()

    assert test_file.exists()
    assert test_file.read_text() == 'hello world'
    assert test_file in modified
```

**Curation Level Testing:**
```python
def test_detect_l0_scaffold():
    fm = {'id': 'test', 'type': 'atom', 'status': 'scaffold'}
    assert detect_curation_level(fm) == CurationLevel.SCAFFOLD

def test_detect_l2_with_depends_on():
    fm = {'id': 'test', 'type': 'atom', 'depends_on': ['parent']}
    assert detect_curation_level(fm) == CurationLevel.FULL
```

---

## VII. KEY ALGORITHMS

### 1. Two-Phase Commit

```python
def commit(self) -> List[Path]:
    """
    Phase 1: Write all content to temp files (.tmp suffix)
    Phase 2: Atomic rename to final paths
    On failure: Clean up temp files, raise exception
    """
```

### 2. Stale Lock Detection

```python
def _acquire_lock(self, lock_path: Path, timeout: float) -> bool:
    """
    1. Check if lock file exists
    2. If exists, read PID from lock
    3. Check if PID is alive: os.kill(pid, 0)
    4. If dead, remove stale lock
    5. Create new lock with our PID
    6. Retry with backoff until timeout
    """
```

### 3. Curation Level Inference

```python
def detect_curation_level(fm: Dict) -> CurationLevel:
    """
    1. If status == 'scaffold': return L0
    2. If status == 'pending_curation': return L1
    3. If has 'depends_on' or 'concepts': return L2
    4. If has 'goal': return L1
    5. Default: L0
    """
```

### 4. Schema Version Detection

```python
def detect_schema_version(fm: Dict) -> str:
    """
    1. If 'ontos_schema' field: use explicit version
    2. If 'curation_level' field: return '2.2'
    3. If 'describes' field: return '2.1'
    4. If 'type' field: return '2.0'
    5. Default: '1.0'
    """
```

### 5. Immutable History Generation

```python
def regenerate_decision_history():
    """
    1. Scan archive/logs/ for all .md files
    2. Extract date, slug, event_type, summary from each
    3. Sort by (date DESC, event_type ASC, slug ASC)
    4. Render deterministic markdown table
    5. Write with GENERATED header
    """
```

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
- `pathlib` — Path manipulation
- `dataclasses` — Data structures
- `enum` — Enumerations
- `typing` — Type hints
- `warnings` — Deprecation warnings

**Development:**
- `pytest` — Testing framework
- `pytest-cov` — Coverage (optional)

---

## IX. DOCUMENT LIFECYCLE

| Status | Meaning | Scanned? |
|--------|---------|----------|
| `draft` | Planning phase, open questions | Yes |
| `active` | Being implemented | Yes |
| `complete` | Implemented and released | Yes |
| `deprecated` | Past truth, superseded | Yes |
| `archived` | Historical record | No (by default) |
| `rejected` | Considered, not approved | No (by default) |

**Archival:** Once a major version is released and the next version stabilizes, move its `strategy/` and `proposals/` directories to `archive/`.

---

## X. PERFORMANCE CHARACTERISTICS

| Operation | Typical Time | Notes |
|-----------|-------------|-------|
| Context map generation | 50-200ms | Scales with doc count |
| Pre-push hook | <500ms | Includes map regen + history |
| Pre-commit hook | <100ms | Count check only |
| Log consolidation | 100-500ms | Per log archived |
| Query (--health) | 50-100ms | Full graph traversal |
| Schema migration check | <100ms | Frontmatter scan |
| Curation scaffold | <50ms | Per file |

---

*End of codebase map. Total: ~7,500 words, ~10,000 tokens.*
