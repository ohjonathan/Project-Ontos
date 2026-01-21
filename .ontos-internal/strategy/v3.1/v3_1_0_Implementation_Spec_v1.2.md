---
id: v3_1_0_implementation_spec
type: strategy
status: approved
depends_on: [v3_0_5_implementation_spec, v3_1_0_implementation_plan, v3_1_tech_debt_wrapper_commands]
concepts: [implementation-spec, native-migration, obsidian, token-efficiency, wrapper-commands]
---

# Ontos v3.1.0 Implementation Spec

**Version:** 1.2
**Author:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-21
**Status:** Approved — Implementation Authorized

**Changelog:**
- v1.2 (2026-01-21): Incorporated Review Board feedback. Fixed B-1 (compact escaping), B-2 (wikilink logic), B-3 (filter design), B-4 (Obsidian leniency). Added §3.7, §4.8, §11.1. Revised AUD-12 disposition. See Appendix B for full traceability.
- v1.1 (2026-01-21): Incorporated audit triage and research findings. Added DOC-1 (`doctor -v`), documented ERR-1 known limitations, added Appendix C with 28 open research questions. See Appendix A for deferred items.
- v1.0 (2026-01-20): Initial draft.

---

## 1. Executive Summary

v3.1.0 is a **major feature release** combining two workstreams:

| Track | Theme | Deliverables |
|-------|-------|--------------|
| **A** | Obsidian Compatibility + Token Efficiency | `--obsidian`, `--compact`, `--filter`, caching, `doctor -v` |
| **B** | Native Command Migration | 7 wrapper commands → native implementations |

**Impact Summary:**

| Category | Count | Action |
|----------|-------|--------|
| New Files | ~12 | Command modules, cache, obsidian utilities, tests |
| Modified Files | ~9 | `cli.py`, `frontmatter.py`, `map.py`, `doctor.py`, `README.md`, etc. |
| Lines Changed | ~2,000+ | New implementations + tests |
| Known Issues Resolved | 7 | All wrapper command issues |

---

## 2. Scope Items Overview

### Track A: Obsidian Compatibility + Token Efficiency

| ID | Feature | Priority | Effort | Summary |
|----|---------|----------|--------|---------|
| OBS-1 | `tags` field | P0 | Low | Mirror `concepts` for Obsidian tag pane |
| OBS-2 | `aliases` field | P0 | Low | Alternative names for wikilink resolution |
| OBS-3 | `--obsidian` flag | P0 | Medium | Enable Obsidian output mode |
| OBS-4 | Wikilink output | P0 | Medium | `[[filename\|id]]` format in context map [AMENDED: B-2] |
| TOK-1 | Document cache | P0 | Medium | mtime-based invalidation for faster `ontos map` |
| TOK-2 | `--compact` flag | P0 | Medium | 30-50% token reduction in output |
| TOK-3 | `--filter` flag | P1 | Medium | Selective document loading |
| ERR-1 | YAML error messages | P0 | Low | Actionable parse errors with line numbers |
| DOC-1 | `doctor -v` verbose | P1 | Low | Show resolved paths in verbose mode [AMENDED: AUD-07] |

### Track B: Native Command Migration

| ID | Command | Priority | Effort | Current Issue |
|----|---------|----------|--------|---------------|
| CMD-1 | `scaffold` | P0 | Low | ❌ Broken: rejects positional arguments |
| CMD-2 | `verify` | P0 | Medium | ⚠️ Limited: lacks positional argument support |
| CMD-3 | `query` | P0 | Medium | ⚠️ Limited: requires legacy flags |
| CMD-4 | `consolidate` | P1 | Low | ⚠️ Limited: requires specific file |
| CMD-5 | `stub` | P1 | Low | ✅ Working (subprocess overhead) |
| CMD-6 | `promote` | P1 | Low | ✅ Working (subprocess overhead) |
| CMD-7 | `migrate` | P1 | Medium | ✅ Working (subprocess overhead) |

---

## 3. Track A: Exact Code Changes

### 3.1 OBS-1/OBS-2: Tags and Aliases Fields

**File:** `ontos/core/frontmatter.py`

**New Functions:**
```python
def normalize_tags(frontmatter: dict) -> list[str]:
    """Extract tags from frontmatter, merging concepts + explicit tags.

    Priority:
    1. Explicit 'tags' field (if present)
    2. 'concepts' field (Ontos standard)

    Returns:
        List of unique tag strings, sorted alphabetically.
    """
    tags = set()

    if 'tags' in frontmatter:
        raw_tags = frontmatter['tags']
        if isinstance(raw_tags, list):
            tags.update(str(t) for t in raw_tags if t)
        elif isinstance(raw_tags, str):
            tags.add(raw_tags)

    if 'concepts' in frontmatter:
        concepts = frontmatter['concepts']
        if isinstance(concepts, list):
            tags.update(str(c) for c in concepts if c)

    return sorted(tags)


def normalize_aliases(frontmatter: dict, doc_id: str) -> list[str]:
    """Extract aliases from frontmatter, auto-generating from id.

    Returns:
        List of alias strings including auto-generated variants.
    """
    aliases = set()

    if 'aliases' in frontmatter:
        raw = frontmatter['aliases']
        if isinstance(raw, list):
            aliases.update(str(a) for a in raw if a)
        elif isinstance(raw, str):
            aliases.add(raw)

    # Auto-generate aliases from id
    if doc_id:
        # snake_case → Title Case
        aliases.add(doc_id.replace('_', ' ').title())
        # snake_case → kebab-case
        aliases.add(doc_id.replace('_', '-'))

    return sorted(aliases)
```

---

### 3.2 OBS-3/OBS-4: Obsidian Mode for Map Command [AMENDED: B-2]

**File:** `ontos/commands/map.py`

**CLI Flag Addition:**
```python
# In _register_map() in cli.py
p.add_argument("--obsidian", action="store_true",
               help="Enable Obsidian-compatible output (wikilinks, tags)")
```

**Options Update:**
```python
@dataclass
class MapOptions:
    output: Optional[Path] = None
    strict: bool = False
    json_output: bool = False
    quiet: bool = False
    obsidian: bool = False  # NEW
    compact: CompactMode = CompactMode.OFF  # NEW (TOK-2) [AMENDED: Code fix]
    filter: Optional[str] = None  # NEW (TOK-3)
    no_cache: bool = False  # NEW [AMENDED: OQ-14]
```

**Wikilink Output Logic:** [AMENDED: B-2]
```python
def _format_doc_link(doc_id: str, doc_path: Path, obsidian_mode: bool) -> str:
    """Format document link based on output mode.

    In Obsidian mode, uses [[filename|display]] format since Obsidian
    resolves links by filename, not frontmatter ID.
    """
    if obsidian_mode:
        filename = doc_path.stem  # filename without extension
        if filename == doc_id:
            return f"[[{doc_id}]]"  # No alias needed
        return f"[[{filename}|{doc_id}]]"  # Alias for display
    return f"`{doc_id}`"
```

---

### 3.3 TOK-1: Document Cache

**File:** `ontos/core/cache.py` (NEW)

```python
"""Document caching with mtime-based invalidation."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import time


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    mtime: float
    data: Any


@dataclass
class DocumentCache:
    """In-memory document cache with mtime invalidation.

    Usage:
        cache = DocumentCache()

        # Check cache
        if (cached := cache.get(path)) is not None:
            return cached

        # Parse and store
        data = parse_document(path)
        cache.set(path, data)
        return data
    """
    _entries: Dict[Path, CacheEntry] = field(default_factory=dict)
    _hits: int = 0
    _misses: int = 0

    def get(self, path: Path) -> Optional[Any]:
        """Get cached document if mtime unchanged."""
        path = path.resolve()

        if path not in self._entries:
            self._misses += 1
            return None

        entry = self._entries[path]
        try:
            current_mtime = path.stat().st_mtime
            if current_mtime == entry.mtime:
                self._hits += 1
                return entry.data
        except OSError:
            pass

        # Invalidated
        del self._entries[path]
        self._misses += 1
        return None

    def set(self, path: Path, data: Any) -> None:
        """Store document in cache."""
        path = path.resolve()
        try:
            mtime = path.stat().st_mtime
            self._entries[path] = CacheEntry(mtime=mtime, data=data)
        except OSError:
            pass  # Don't cache if we can't stat

    def invalidate(self, path: Path) -> None:
        """Remove specific path from cache."""
        path = path.resolve()
        self._entries.pop(path, None)

    def clear(self) -> None:
        """Clear entire cache."""
        self._entries.clear()
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> dict:
        """Return cache statistics."""
        total = self._hits + self._misses
        return {
            "entries": len(self._entries),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0,
        }
```

**CLI Flag:** [AMENDED: OQ-14]
```python
p.add_argument("--no-cache", action="store_true",
               help="Bypass document cache (for debugging)")
```

---

### 3.4 TOK-2: Compact Output Format [AMENDED: B-1, Code fix]

**File:** `ontos/commands/map.py`

**CompactMode Enum:** [AMENDED: Code fix]
```python
from enum import Enum

class CompactMode(Enum):
    OFF = "off"
    BASIC = "basic"
    RICH = "rich"
```

**Compact Format Implementation:** [AMENDED: B-1]
```python
def _generate_compact_output(docs: Dict[str, Document], mode: CompactMode) -> str:
    """Generate compact context map format.

    Standard compact (BASIC): id:type:status
    Rich compact (RICH): id:type:status:"summary"

    Args:
        docs: Document dictionary
        mode: CompactMode (OFF, BASIC, RICH)

    Returns:
        Compact format string, one doc per line
    """
    if mode == CompactMode.OFF:
        return None  # Use standard output

    lines = []
    for doc_id, doc in sorted(docs.items()):
        if mode == CompactMode.RICH and doc.summary:
            # Escape backslashes, quotes, and newlines [AMENDED: B-1]
            summary_safe = (doc.summary
                .replace('\\', '\\\\')
                .replace('"', '\\"')
                .replace('\n', '\\n'))
            lines.append(f'{doc_id}:{doc.type}:{doc.status}:"{summary_safe}"')
        else:
            lines.append(f'{doc_id}:{doc.type}:{doc.status}')
    return '\n'.join(lines)
```

**CLI Flag:** [AMENDED: Code fix]
```python
p.add_argument("--compact", nargs="?", const="basic", default="off",
               choices=["basic", "rich"],
               help="Compact output: 'basic' (default) or 'rich' (with summaries)")
```

---

### 3.5 ERR-1: Better YAML Error Messages [AMENDED: B-4]

**File:** `ontos/core/frontmatter.py`

```python
@dataclass
class FrontmatterParseError:
    """Structured YAML parse error with location."""
    filepath: str
    line: int
    column: int
    message: str
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        loc = f"{self.filepath}:{self.line}:{self.column}"
        msg = f"{loc}: {self.message}"
        if self.suggestion:
            msg += f"\n  Suggestion: {self.suggestion}"
        return msg


def parse_frontmatter_safe(content: str, filepath: str = "<string>") -> Tuple[dict, list]:
    """Parse frontmatter with detailed error reporting.

    Returns:
        Tuple of (frontmatter_dict, list of FrontmatterParseError)

    Note: The following is illustrative pseudocode. Full implementation will
    handle YAML parsing errors and construct appropriate FrontmatterParseError
    objects. [AMENDED: Code fix]
    """
    errors = []
    # ... implementation with error collection
    return frontmatter, errors
```

**Schema Version Error Message:** [AMENDED: OQ-17]
```python
# When schema version is newer than supported:
raise SchemaVersionError(
    f"Document uses schema {doc_schema}, but ontos {ONTOS_VERSION} only supports up to {MAX_SCHEMA}.\n"
    f"Upgrade: pip install --upgrade ontos"
)
```

**Known Limitations:** [AMENDED: AUD-12]

The following edge cases are documented but not fully handled in v3.1.0:

| Case | Behavior | Target |
|------|----------|--------|
| BOM (Byte Order Mark) | Handled in `--obsidian` mode only | v3.2.0 (full) |
| `---` inside content | May cause false delimiter detection | v3.2.0 |
| Leading whitespace before `---` | Handled in `--obsidian` mode only | v3.2.0 (full) |

**Obsidian Leniency Mode:** [AMENDED: B-4]

When `--obsidian` flag is active, apply minimal leniency:

1. **BOM Handling:** Strip UTF-8 BOM (U+FEFF) if present at file start
2. **Leading Whitespace:** Skip leading whitespace/newlines before `---` delimiter

```python
def read_file_lenient(path: Path) -> str:
    """Read file with Obsidian-compatible leniency."""
    content = path.read_bytes()

    # Strip UTF-8 BOM if present
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]

    text = content.decode('utf-8')

    # Find first --- after stripping leading whitespace
    stripped = text.lstrip()
    if stripped.startswith('---'):
        return stripped
    return text
```

---

### 3.6 DOC-1: Doctor Verbose Mode [AMENDED: AUD-07, Code fix]

**File:** `ontos/commands/doctor.py`

**Enhancement:** Add `--verbose` / `-v` flag to show resolved configuration paths.

**CLI Flag Addition:**
```python
# In _register_doctor() in cli.py
p.add_argument("--verbose", "-v", action="store_true",
               help="Show resolved configuration paths")
```

**Verbose Output:**
- `repo_root`: Resolved repository root path
- `config_path`: Location of `.ontos.toml` (or "default" if not found)
- `docs_dir`: Configured documentation directory
- `context_map`: Path to generated context map

**Implementation:** [AMENDED: Code fix]
```python
def _get_config_path(ctx: SessionContext) -> Optional[Path]:
    """Get config path from SessionContext or find it."""
    # Check standard locations
    toml_path = ctx.repo_root / ".ontos.toml"
    if toml_path.exists():
        return toml_path
    return None


def _print_config_paths(ctx: SessionContext, verbose: bool) -> None:
    """Print resolved configuration paths in verbose mode."""
    if not verbose:
        return

    config_path = _get_config_path(ctx)
    print("Configuration:")
    print(f"  repo_root:    {ctx.repo_root}")
    print(f"  config_path:  {config_path or 'default'}")
    print(f"  docs_dir:     {ctx.docs_dir}")
    print(f"  context_map:  {ctx.context_map_path}")
    print()
```

**Example output:**
```
$ ontos doctor -v
Configuration:
  repo_root:    /Users/dev/myproject
  config_path:  /Users/dev/myproject/.ontos.toml
  docs_dir:     /Users/dev/myproject/docs
  context_map:  /Users/dev/myproject/Ontos_Context_Map.md

Health Checks:
  ✅ Repository structure valid
  ✅ Configuration loaded
  ✅ Context map exists
  ...
```

---

### 3.7 TOK-3: Filter Flag Design [AMENDED: B-3]

**File:** `ontos/commands/map.py`

**CLI Flag:**
```python
p.add_argument("--filter", "-f", metavar="EXPR",
               help="Filter documents by expression (e.g., 'type:strategy')")
```

**Filter Syntax:**
```
EXPR := FIELD:VALUE | FIELD:VALUE,VALUE | EXPR EXPR
FIELD := type | status | concept | id
VALUE := string (no spaces) | "quoted string"
```

**Examples:**
```bash
ontos map --filter "type:strategy"           # Single field
ontos map --filter "type:strategy,kernel"    # Multiple values (OR)
ontos map --filter "type:strategy status:active"  # Multiple fields (AND)
ontos map --filter "concept:auth"            # By concept/tag
ontos map --filter "id:auth_*"               # Glob matching on ID
```

**Matching Semantics:**
- Multiple values for same field: OR (match any)
- Multiple fields: AND (match all)
- Glob patterns (`*`, `?`) supported for `id` field
- Case-insensitive matching

**Implementation:**
```python
@dataclass
class FilterExpression:
    """Single filter expression."""
    field: str
    values: list[str]


def parse_filter(expr: str) -> list[FilterExpression]:
    """Parse filter expression string.

    Args:
        expr: Filter string like "type:strategy status:active"

    Returns:
        List of FilterExpression objects
    """
    filters = []
    for part in expr.split():
        if ':' in part:
            field, value = part.split(':', 1)
            values = value.split(',')
            filters.append(FilterExpression(field=field.lower(), values=values))
    return filters


def matches_filter(doc: Document, filters: list[FilterExpression]) -> bool:
    """Check if document matches all filter expressions.

    Args:
        doc: Document to check
        filters: List of filter expressions (AND)

    Returns:
        True if document matches all filters
    """
    import fnmatch

    for f in filters:
        if f.field == 'type':
            if doc.type.lower() not in [v.lower() for v in f.values]:
                return False
        elif f.field == 'status':
            if doc.status.lower() not in [v.lower() for v in f.values]:
                return False
        elif f.field == 'concept':
            if not any(c.lower() in [v.lower() for v in f.values] for c in doc.concepts):
                return False
        elif f.field == 'id':
            if not any(fnmatch.fnmatch(doc.id.lower(), v.lower()) for v in f.values):
                return False
    return True
```

---

## 4. Track B: Native Command Implementations

### 4.1 CMD-1: scaffold (CRITICAL) [AMENDED: Missing item]

**File:** `ontos/commands/scaffold.py` (NEW)

**Purpose:** Add Ontos frontmatter to untagged markdown files

**Options:**
```python
@dataclass
class ScaffoldOptions:
    path: Optional[Path] = None  # File or directory (positional)
    dry_run: bool = False
    interactive: bool = True
    json_output: bool = False
    quiet: bool = False
```

**CLI Registration:**
```python
def _register_scaffold(subparsers, parent):
    """Register scaffold command."""
    p = subparsers.add_parser("scaffold", help="Add frontmatter to markdown files", parents=[parent])
    p.add_argument("path", nargs="?", type=Path,
                   help="File or directory to scaffold")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would be changed without modifying files")
    p.add_argument("--yes", "-y", action="store_true",
                   help="Non-interactive mode")
    p.set_defaults(func=_cmd_scaffold)
```

**Core Logic:** Extract and refactor from `ontos/_scripts/ontos_scaffold.py`

**Key Functions:**
- `find_untagged_files(path: Path) -> List[Path]`
- `scaffold_file(path: Path, dry_run: bool) -> bool`
- `scaffold_command(options: ScaffoldOptions) -> Tuple[int, str]`

**Expected scaffold output:** [AMENDED: Missing item]
```yaml
---
id: <filename_without_extension>
type: atom
status: draft
depends_on: []
concepts: []
---
```

**Directory structure after `ontos scaffold docs/`:**
- Each `.md` file without frontmatter receives Ontos frontmatter
- Files with existing frontmatter are skipped
- `--dry-run` shows what would be added without modifying

---

### 4.2 CMD-2: verify

**File:** `ontos/commands/verify.py` (enhance existing)

**Options:**
```python
@dataclass
class VerifyOptions:
    path: Optional[Path] = None  # Specific file (positional)
    all: bool = False            # Verify all stale
    days: int = 30               # Staleness threshold
    interactive: bool = True
    json_output: bool = False
    quiet: bool = False
```

**CLI Registration:**
```python
def _register_verify(subparsers, parent):
    p = subparsers.add_parser("verify", help="Verify document describes dates", parents=[parent])
    p.add_argument("path", nargs="?", type=Path,
                   help="Specific file to verify")
    p.add_argument("--all", "-a", action="store_true",
                   help="Verify all stale documents")
    p.add_argument("--days", "-d", type=int, default=30,
                   help="Staleness threshold in days (default: 30)")
    p.set_defaults(func=_cmd_verify)
```

---

### 4.3 CMD-3: query

**File:** `ontos/commands/query.py` (NEW)

**Options:**
```python
@dataclass
class QueryOptions:
    depends_on: Optional[str] = None
    depended_by: Optional[str] = None
    concept: Optional[str] = None
    stale: Optional[int] = None
    health: bool = False
    list_ids: bool = False
    json_output: bool = False
    quiet: bool = False
```

**CLI Registration:**
```python
def _register_query(subparsers, parent):
    p = subparsers.add_parser("query", help="Query document graph", parents=[parent])
    p.add_argument("--depends-on", metavar="ID",
                   help="Show dependencies of document")
    p.add_argument("--depended-by", metavar="ID",
                   help="Show documents that depend on this")
    p.add_argument("--concept", metavar="TAG",
                   help="Find documents with concept")
    p.add_argument("--stale", metavar="DAYS", type=int,
                   help="Find documents older than N days")
    p.add_argument("--health", action="store_true",
                   help="Show graph health metrics")
    p.add_argument("--list-ids", action="store_true",
                   help="List all document IDs")
    p.set_defaults(func=_cmd_query)
```

---

### 4.4 CMD-4: consolidate

**File:** `ontos/commands/consolidate.py` (NEW)

**Options:**
```python
@dataclass
class ConsolidateOptions:
    keep: int = 15               # Number of logs to keep
    dry_run: bool = False
    json_output: bool = False
    quiet: bool = False
```

---

### 4.5 CMD-5: stub

**File:** `ontos/commands/stub.py` (NEW)

**Options:**
```python
@dataclass
class StubOptions:
    doc_type: str = "reference"
    id: Optional[str] = None
    output: Optional[Path] = None
    interactive: bool = True
    json_output: bool = False
    quiet: bool = False
```

---

### 4.6 CMD-6: promote

**File:** `ontos/commands/promote.py` (NEW)

**Options:**
```python
@dataclass
class PromoteOptions:
    path: Optional[Path] = None
    interactive: bool = True
    json_output: bool = False
    quiet: bool = False
```

---

### 4.7 CMD-7: migrate

**File:** `ontos/commands/migrate.py` (NEW)

**Options:**
```python
@dataclass
class MigrateOptions:
    path: Optional[Path] = None
    check: bool = False
    dry_run: bool = False
    apply: bool = False
    json_output: bool = False
    quiet: bool = False
```

---

### 4.8 Behavioral Parity Contracts [AMENDED: Missing item]

Each migrated command must preserve:

| Aspect | Contract |
|--------|----------|
| Exit codes | 0 = success, 1 = error, 2 = user abort |
| Stdout format | Identical to legacy (or superset) |
| Stderr format | Identical error messages |
| File outputs | Same paths, same content |
| Flag semantics | Same behavior for same flags |

**Verification:** Add golden fixture tests per command comparing legacy vs native output.

**Test Structure:**
```
tests/
  commands/
    golden/
      scaffold_output.txt
      verify_output.txt
      query_health.txt
      ...
    test_scaffold_parity.py
    test_verify_parity.py
    ...
```

---

## 5. Configuration Additions

### 5.1 `.ontos.toml` Schema Updates

```toml
[obsidian]
enabled = false              # Opt-in to Obsidian mode
generate_tags = true         # Mirror concepts → tags
generate_aliases = true      # Auto-generate from id
wikilink_format = true       # [[wikilinks]] in output

[frontmatter]
preserve_unknown_fields = true  # Keep Jekyll/Hugo fields

[validation]
yaml_mode = "standard"       # lenient | standard | strict

[performance]
cache_enabled = true         # Document caching
parallel_loading = false     # Concurrent file scanning
# cache_max_entries = 1000   # Placeholder for v3.2 [AMENDED: Code fix deferred]
```

---

## 6. Files Summary

### New Files

| File | Purpose |
|------|---------|
| `ontos/core/cache.py` | Document cache with mtime invalidation |
| `ontos/io/obsidian.py` | Wikilink utilities, vault detection |
| `ontos/commands/scaffold.py` | Native scaffold implementation |
| `ontos/commands/query.py` | Native query implementation |
| `ontos/commands/consolidate.py` | Native consolidate implementation |
| `ontos/commands/stub.py` | Native stub implementation |
| `ontos/commands/promote.py` | Native promote implementation |
| `ontos/commands/migrate.py` | Native migrate implementation |
| `tests/core/test_cache.py` | Cache unit tests |
| `tests/test_obsidian.py` | Obsidian unit tests |
| `tests/commands/test_scaffold.py` | Scaffold tests |
| `tests/commands/test_query.py` | Query tests |
| `tests/commands/golden/` | Golden fixture files [AMENDED: Missing item] |

### Modified Files

| File | Changes |
|------|---------|
| `ontos/core/frontmatter.py` | `normalize_tags()`, `normalize_aliases()`, `FrontmatterParseError`, `read_file_lenient()` |
| `ontos/commands/map.py` | `--obsidian`, `--compact`, `--filter`, `--no-cache` flags, cache integration, `CompactMode` enum |
| `ontos/commands/verify.py` | Enhance to full native implementation |
| `ontos/commands/doctor.py` | Add `--verbose` flag for resolved paths [AMENDED: AUD-07] |
| `ontos/cli.py` | Update all command registrations |
| `README.md` | Remove Known Issues section |

---

## 7. Implementation Order

### Phase 1: Critical Fixes (Week 1)

| Priority | Item | Effort |
|----------|------|--------|
| P0 | CMD-1: `scaffold` native | Low |
| P0 | CMD-2: `verify` native | Medium |
| P0 | OBS-1/2: Tags & aliases | Low |

### Phase 2: Core Features (Week 2)

| Priority | Item | Effort |
|----------|------|--------|
| P0 | CMD-3: `query` native | Medium |
| P0 | CMD-4: `consolidate` native | Low |
| P0 | TOK-1: Document cache | Medium |
| P0 | OBS-3/4: `--obsidian` flag | Medium |

### Phase 3: Remaining Commands (Week 3)

| Priority | Item | Effort |
|----------|------|--------|
| P1 | CMD-5: `stub` native | Low |
| P1 | CMD-6: `promote` native | Low |
| P1 | CMD-7: `migrate` native | Medium |
| P0 | TOK-2: `--compact` flag | Medium |

### Phase 4: Polish (Week 4)

| Priority | Item | Effort |
|----------|------|--------|
| P1 | TOK-3: `--filter` flag | Medium |
| P0 | ERR-1: YAML error messages | Low |
| P1 | DOC-1: `doctor -v` verbose mode | Low | [AMENDED: AUD-07]
| P1 | Obsidian auto-detection | Low |
| - | Documentation updates | Low |

---

## 8. Verification Protocol

### 8.1 Track A Verification

```bash
# Obsidian mode
ontos map --obsidian
# Verify: wikilinks in output with [[filename|id]] format, tags normalized

# Compact output
ontos map --compact
wc -c Ontos_Context_Map.md  # Should be 30-50% smaller

ontos map --compact=rich
# Verify: summaries included with proper escaping

# Caching
time ontos map  # First run
time ontos map  # Second run (should be faster within same invocation)

# No cache
ontos map --no-cache
# Verify: cache bypassed

# Filtering
ontos map --filter "type:strategy"
# Verify: only strategy docs in output

ontos map --filter "type:strategy,kernel"
# Verify: strategy OR kernel docs

ontos map --filter "type:strategy status:active"
# Verify: strategy AND active docs

# Doctor verbose mode [AMENDED: AUD-07]
ontos doctor -v
# Verify: shows repo_root, config_path, docs_dir, context_map
```

### 8.2 Track B Verification

```bash
# scaffold (CRITICAL - currently broken)
ontos scaffold docs/ --dry-run
ontos scaffold docs/new_file.md
# Verify: positional argument works
# Verify: output matches expected scaffold format

# verify
ontos verify docs/some_file.md
ontos verify --all --days 30
# Verify: positional argument works

# query
ontos query --health
ontos query --depends-on some_doc_id
ontos query --concept auth
# Verify: all query modes work

# consolidate
ontos consolidate --dry-run
# Verify: works without decision_history.md requirement

# stub
ontos stub --type reference
# Verify: generates stub

# promote
ontos promote
# Verify: interactive flow works

# migrate
ontos migrate --check
# Verify: schema check works
```

### 8.3 Full Test Suite

```bash
pytest tests/ -v
# Expected: All tests pass, >90% coverage on new code

# Parity tests [AMENDED: Missing item]
pytest tests/commands/test_*_parity.py -v
# Expected: Native output matches legacy golden fixtures
```

---

## 9. Risk Assessment

**Overall Risk: MEDIUM**

| Risk Factor | Assessment | Mitigation |
|-------------|------------|------------|
| Scope size | Large (2 tracks) | Clear phase boundaries |
| Breaking changes | Low | Native commands preserve behavior |
| Regression | Medium | Comprehensive tests + parity contracts |
| Timeline | 4 weeks | Prioritized implementation order |

---

## 10. Success Criteria [AMENDED: OQ-13, Gemini]

### Track A
- [ ] `ontos map --obsidian` generates wikilinks with `[[filename|id]]` format
- [ ] `ontos map --compact` produces 30-50% smaller output
- [ ] `ontos map --compact=rich` properly escapes quotes/newlines in summaries
- [ ] `ontos map --filter "type:strategy"` works
- [ ] Cache improves repeat `ontos map` **within same invocation** to <100ms [AMENDED: OQ-13]
- [ ] `ontos map --no-cache` bypasses cache
- [ ] YAML errors include line numbers
- [ ] `ontos doctor -v` shows resolved paths [AMENDED: AUD-07]

### Track B
- [ ] All 7 commands work as native implementations
- [ ] `ontos scaffold docs/` accepts positional argument
- [ ] `ontos scaffold` produces expected output format
- [ ] `ontos verify file.md` accepts positional argument
- [ ] All existing functionality preserved
- [ ] `.ontos.toml` configuration honored
- [ ] No subprocess/PYTHONPATH manipulation

### Quality
- [ ] Test coverage >90% for new code
- [ ] README Known Issues section cleared or "No known issues"
- [ ] All golden master tests pass
- [ ] README includes prominent Databricks distinction disclaimer [AMENDED: Gemini]

---

## 11. Post-Release

### 11.1 Backward Compatibility Notes [AMENDED: Missing item]

**Must NOT change:**
- `ontos map` default output format
- Exit codes for all commands
- `.ontos.toml` schema (additive only)
- Frontmatter field names and types
- `Ontos_Context_Map.md` location and basic structure

**May change (with flag):**
- Output format (via `--compact`, `--obsidian`, `--json`)
- Frontmatter fields (via schema migration)

### 11.2 Documentation Updates
- [ ] Update README.md (remove Known Issues)
- [ ] Update Ontos_Manual.md with new flags
- [ ] Update CHANGELOG.md

### 11.3 Cleanup
- [ ] Deprecate legacy scripts (add warnings)
- [ ] Consider removing `ontos/_scripts/` in v3.2

---

## Appendix A: Deferred Items [AMENDED: Audit Triage Part 8, Code fixes]

Items considered but explicitly excluded from v3.1.0 scope:

### v3.2 Candidates

| ID | Item | Source | Effort | Rationale |
|----|------|--------|--------|-----------|
| AUD-06 | Schema 3.0 field implementation | Claude audit | Medium | Non-breaking addition; low impact currently |
| AUD-09 | Tests in sdist or separate package | Claude, Codex | Low | Packaging decision; document "run from repo" |
| AUD-12 | Full frontmatter parsing robustness | Codex audit | Medium | Partial fix in B-4; full `yaml_mode=lenient` deferred |
| AUD-13 | Versioned documentation (ReadTheDocs) | Codex audit | Medium | Infrastructure concern; not blocking |
| AUD-14 | SessionContext refactor | Claude audit | Medium | Internal tech debt; no user impact |
| AUD-15 | Complete type hints | Claude audit | Low | Code quality; not blocking adoption |
| AUD-16 | `--dry-run` on remaining commands | Claude audit | Low | scaffold/consolidate covered in v3.1 |
| RES-01 | `intent` field in schema | Research review | Low | Non-breaking schema addition |
| RES-02 | `--format xml` flag | Research review | Medium | Alternative output format |
| RES-03 | Hash verification for staleness | Research review | Medium | Stronger than date-based verification |
| CODE-01 | Case normalization for tags | Review (Code fix) | Low | Design decision; needs user input |
| CODE-02 | Cache max_entries config | Review (Code fix) | Low | Per-invocation cache; not critical |
| CODE-03 | Deprecated Obsidian keys (`tag`/`alias`) | Review (B-4) | Low | Scope creep; BOM/whitespace more important |
| CODE-04 | Full `yaml_mode=lenient` config | Review (B-4) | Medium | Partial leniency in `--obsidian` mode |
| CODE-05 | Flags matrix for command consistency | Review (GPT-5.2) | Low | Useful but not blocking |

### v4.0 Candidates

| ID | Item | Source | Effort | Rationale |
|----|------|--------|--------|-----------|
| AUD-05 | MCP server implementation | Claude, Codex | High | Requires infrastructure; v4.0 scope |
| AUD-08 | Programmatic activation (replaces AGENTS.md) | Claude audit | High | MCP provides programmatic alternative |
| RES-04 | Navigator pattern (cheap model filter) | Research review | High | Requires MCP infrastructure |
| RES-05 | Automated metadata refresh GitHub Action | Research review | Medium | CI/CD integration |

---

## Appendix B: Amendment Traceability [AMENDED: Review cycle]

| Amendment | Source | Section(s) Modified |
|-----------|--------|---------------------|
| DOC-1: `doctor -v` | AUD-07 | §2, §3.6, §6, §7, §8.1, §10 |
| ERR-1 known limitations | AUD-12 | §3.5 |
| Deferred items backlog | Audit Triage Part 8 | Appendix A |
| B-1: Compact escaping | Review consensus | §3.4 |
| B-2: Wikilink logic | Gemini review | §3.2 |
| B-3: Filter design | GPT-5.2 review | §3.7 (new) |
| B-4: Obsidian leniency | GPT-5.2 review | §3.5 |
| Code fix: CompactMode enum | GPT-5.2 review | §3.2, §3.4 |
| Code fix: config_path | Claude review | §3.6 |
| Code fix: pseudocode label | GPT-5.2 review | §3.5 |
| OQ-13: Cache scope | Claude, GPT-5.2 | §10 |
| OQ-14: --no-cache flag | GPT-5.2 | §3.3 |
| OQ-17: Schema error message | Claude | §3.5 |
| Missing: Parity contracts | GPT-5.2 review | §4.8 (new) |
| Missing: Backward compat | GPT-5.2 review | §11.1 (new) |
| Missing: Scaffold outputs | GPT-5.2 review | §4.1 |
| Note: Databricks disclaimer | Gemini review | §10 |

---

## Appendix C: Open Questions [AMENDED: Mark answered]

Questions requiring additional research, clarification, or validation. Designed to trigger substantive investigation from other LLMs or domain experts.

---

### C.1 Token Efficiency (TOK-1/TOK-2 Validation)

| ID | Question | Context | Status |
|----|----------|---------|--------|
| OQ-01 | **What is the actual token cost comparison between our Markdown table format, compact format, and JSON?** | Research §3.1 claims 40-60% JSON overhead, but we lack benchmarks for our specific output. | Open |
| OQ-02 | **At what document count does compact format become essential vs nice-to-have?** | Small repos may not benefit; large repos may require it. | **ANSWERED:** Default to minimal; keep "rich" as opt-in |
| OQ-03 | **How do different LLMs tokenize our colon-delimited compact format?** | BPE tokenization varies. `:` may tokenize differently in Claude vs GPT-4 vs Gemini. | Open |
| OQ-04 | **Is our `id:type:status` delimiter optimal, or would pipe `\|` or tab be more token-efficient?** | Research §3.1 mentions colon as "familiar" but doesn't benchmark alternatives. | Open |

---

### C.2 Agent Interaction Patterns

| ID | Question | Context | Status |
|----|----------|---------|--------|
| OQ-05 | **What is the optimal cardinality for `concepts` (tags) to enable deterministic agent filtering?** | Research §2.1.1 mentions "keyword triggers" but doesn't specify how many. | **ANSWERED:** 10-30 concepts per repo is "Goldilocks zone" |
| OQ-06 | **When `summary` and `intent` fields conflict, which should agents prioritize?** | Research §2.1.2 recommends `intent` but we have existing `summary` fields. | Open |
| OQ-07 | **What error message patterns do agents parse most reliably?** | ERR-1 adds line numbers, but what format? `file:line:col`? JSON? | Open |
| OQ-08 | **Do agents benefit from explicit "use this for X" instructions in frontmatter, or is it noise?** | Research §2.1.2 claims instruction-phrased descriptions outperform passive ones. | Open |

---

### C.3 Obsidian Compatibility Edge Cases

| ID | Question | Context | Status |
|----|----------|---------|--------|
| OQ-09 | **How should we resolve wikilink ambiguity when multiple documents have similar IDs?** | E.g., `auth_flow` vs `auth_flow_v2`. Does `[[auth_flow]]` match both? | Open |
| OQ-10 | **Should we support Obsidian's `[[doc\|display text]]` alias syntax in output?** | OBS-4 now uses `[[filename\|id]]` format [AMENDED: B-2]. | **RESOLVED:** Using filename-based resolution |
| OQ-11 | **How do vault-level `.obsidian/` settings interact with repo-level `.ontos.toml`?** | Users may have Obsidian defaults that conflict with Ontos config. | Open |
| OQ-12 | **What happens when a repo spans multiple Obsidian vaults?** | Monorepos may have `/docs` and `/wiki` as separate vaults. | Open |

---

### C.4 Cache & Performance Architecture

| ID | Question | Context | Status |
|----|----------|---------|--------|
| OQ-13 | **Should we support persistent (disk) cache in addition to in-memory?** | TOK-1 is in-memory only. Large repos may benefit from disk cache. | **ANSWERED:** In-memory sufficient; disk only if parse >500ms |
| OQ-14 | **What is the document count "performance cliff" where caching becomes critical?** | At 10 docs, caching may be overhead. At 1000 docs, it's essential. | **ANSWERED:** mtime+size good default; add --no-cache |
| OQ-15 | **How do Obsidian and Notion handle incremental indexing?** | Both have fast re-index on file change. | Open |
| OQ-16 | **Is mtime-based invalidation sufficient, or should we use content hashing?** | mtime can be unreliable (git checkout, rsync). | Open |

---

### C.5 Schema Evolution Strategy

| ID | Question | Context | Status |
|----|----------|---------|--------|
| OQ-17 | **How should Ontos handle documents with schema versions newer than the installed package?** | User has v3.1.0 installed but opens doc with `ontos_schema: 4.0`. | **ANSWERED:** Fail loudly with upgrade command |
| OQ-18 | **Should we support "schema coercion" (auto-upgrade on read)?** | Old doc has `ontos_schema: 2.0`. Should `ontos map` silently upgrade it? | Open |
| OQ-19 | **What's the best UX pattern for breaking schema changes?** | If v4.0 removes a field, how do we communicate this to users? | Open |
| OQ-20 | **Should schema version be in frontmatter or inferred from field presence?** | Current: explicit `ontos_schema` field. | Open |

---

### C.6 Frontmatter Robustness (AUD-12 Follow-up)

| ID | Question | Context | Status |
|----|----------|---------|--------|
| OQ-21 | **What is the real-world frequency of BOM, leading whitespace, and `---` edge cases?** | AUD-12 flags these but we don't know how common they are. | **PARTIALLY ADDRESSED:** Leniency in --obsidian mode |
| OQ-22 | **Should we adopt a stricter parser (fail-fast) or more lenient one (best-effort)?** | Strict = fewer surprises but more friction. | Open (v3.2) |
| OQ-23 | **How do Hugo, Jekyll, and Docusaurus handle frontmatter delimiter detection?** | They've solved this at scale. | Open |
| OQ-24 | **Should we support TOML frontmatter (`+++`) as an alternative to YAML?** | Hugo supports both. Some users prefer TOML's stricter typing. | Open |

---

### C.7 Competitive Landscape & Standards

| ID | Question | Context | Status |
|----|----------|---------|--------|
| OQ-25 | **How does CTX (context-hub) approach context management compared to Ontos?** | CTX is a competitor mentioned in Claude audit. | Open |
| OQ-26 | **What patterns are emerging in MCP-native documentation tools?** | MCP is becoming standard for agent tooling. | Open |
| OQ-27 | **Is there a de facto standard emerging for agent-readable project metadata?** | `.github/`, `AGENTS.md`, `.cursor/`, `.claude/` — is one winning? | Open |
| OQ-28 | **What's the trajectory of context window sizes, and how does it affect Ontos's value proposition?** | If context windows grow to 10M tokens, does token efficiency still matter? | Open |

---

### C.8 Research Validation Priorities

If resources are limited, prioritize these questions for immediate research:

| Priority | Question ID | Rationale | Status |
|----------|-------------|-----------|--------|
| **P0** | OQ-01 | Token efficiency is core value prop. Need hard numbers. | Open |
| **P0** | OQ-02 | Threshold for compact format | **ANSWERED** |
| **P0** | OQ-05 | Agent interaction patterns directly affect adoption | **ANSWERED** |
| **P0** | OQ-06 | Metadata priority | Open |
| **P1** | OQ-13 | Cache architecture affects v3.1 implementation | **ANSWERED** |
| **P1** | OQ-14 | Cache invalidation strategy | **ANSWERED** |
| **P1** | OQ-21 | Informs v3.2 frontmatter robustness work | **PARTIALLY ADDRESSED** |
| **P1** | OQ-22 | Parser strictness decision | Open |
| **P2** | OQ-25 | Competitive intelligence for roadmap | Open |
| **P2** | OQ-27 | Agent metadata standards | Open |

---

*Chief Architect (Claude Opus 4.5) — 2026-01-21*
*Implementation Authorized*
