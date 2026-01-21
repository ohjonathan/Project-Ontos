---
id: v3_1_0_track_a_implementation_prompt
type: implementation
status: ready
depends_on: [v3_1_0_implementation_spec, v3_1_0_final_decision_chief_architect]
concepts: [implementation-prompt, track-a, obsidian, token-efficiency, antigravity]
---

# Antigravity: Track A Implementation — Obsidian + Token Efficiency

**Project:** Ontos v3.1.0
**Track:** A
**Branch:** `feat/v3.1.0-track-a`
**Spec Reference:** v3.1.0 Implementation Spec v1.2, §3
**Author:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-21

---

## Overview

Track A implements Obsidian compatibility and token efficiency features for `ontos map`.

**Scope:**
- New files: 2 (`ontos/core/cache.py`, `ontos/io/obsidian.py`)
- Modified files: 4 (`frontmatter.py`, `map.py`, `doctor.py`, `cli.py`)
- New flags: 4 (`--obsidian`, `--compact`, `--filter`, `--no-cache`)
- Enhanced flags: 1 (`doctor -v` verbose mode — already registered)

**Risk Level:** MEDIUM
**Dependencies:** None (Track B is parallel)

---

## Pre-Implementation Checklist

- [ ] Create branch: `git checkout -b feat/v3.1.0-track-a`
- [ ] Verify clean state: `git status`
- [ ] Run baseline tests: `pytest tests/ -v` (all must pass)
- [ ] Read spec §3.1 through §3.7 completely

**Codebase state (verified by Chief Architect on 2026-01-21):**

| File | Lines | Key Component | Insertion Point |
|------|-------|---------------|-----------------|
| `ontos/core/frontmatter.py` | 239 | `parse_frontmatter()` at L23 | After L239 (end of file) |
| `ontos/commands/map.py` | 397 | `MapOptions` at L288-294 | Modify L288-294, add helpers after L285 |
| `ontos/commands/doctor.py` | 515 | `DoctorOptions` at L26-30 | Add helper before L456 |
| `ontos/cli.py` | 504 | `_register_map()` at L115-122 | Add flags at L118-121 |

---

## Architecture Constraints

**Layer rules (MUST follow):**

| Layer | Location | Can Import From | Cannot Import From |
|-------|----------|-----------------|-------------------|
| Core | `ontos/core/` | stdlib only | `io/`, `commands/` |
| IO | `ontos/io/` | `core/`, stdlib | `commands/` |
| Commands | `ontos/commands/` | `core/`, `io/`, stdlib | — |

**New file placement:**
- `ontos/core/cache.py` — DocumentCache is pure logic, no file I/O
- `ontos/io/obsidian.py` — File reading utilities (leniency, vault detection)

**Verify after each file:**
```bash
grep -n "from ontos.io" ontos/core/*.py      # Must be empty
grep -n "from ontos.commands" ontos/core/*.py # Must be empty
```

---

## Task Sequence

### Task A.1: `normalize_tags()` function

**Spec Reference:** §3.1
**Priority:** P0
**File:** `ontos/core/frontmatter.py` — MODIFY

---

**Current code (end of file, L239):**
```python
    return concepts
```

**Add after line 239:**
```python


def normalize_tags(frontmatter: dict) -> list[str]:
    """Extract tags from frontmatter, merging concepts + explicit tags.

    Priority:
    1. Explicit 'tags' field (if present)
    2. 'concepts' field (Ontos standard)

    Args:
        frontmatter: Parsed YAML frontmatter dictionary.

    Returns:
        List of unique tag strings, sorted alphabetically.
    """
    tags = set()

    if 'tags' in frontmatter:
        raw_tags = frontmatter['tags']
        if isinstance(raw_tags, list):
            tags.update(str(t).strip() for t in raw_tags if t)
        elif isinstance(raw_tags, str):
            stripped = raw_tags.strip()
            if stripped:
                tags.add(stripped)

    if 'concepts' in frontmatter:
        concepts = frontmatter['concepts']
        if isinstance(concepts, list):
            tags.update(str(c).strip() for c in concepts if c)

    return sorted(tags)
```

**Test:**
```bash
python -c "from ontos.core.frontmatter import normalize_tags; print(normalize_tags({'concepts': ['auth', 'api'], 'tags': ['security']}))"
# Expected: ['api', 'auth', 'security']
```

**Commit:**
```
feat(frontmatter): add normalize_tags function

- Merges concepts and explicit tags fields
- Returns sorted, deduplicated list
- Handles string and list inputs

Ref: v3.1.0 §3.1
```

---

### Task A.2: `normalize_aliases()` function

**Spec Reference:** §3.1
**Priority:** P0
**File:** `ontos/core/frontmatter.py` — MODIFY

---

**Add after `normalize_tags()` (after Task A.1 code):**
```python


def normalize_aliases(frontmatter: dict, doc_id: str) -> list[str]:
    """Extract aliases from frontmatter, auto-generating from id.

    Args:
        frontmatter: Parsed YAML frontmatter dictionary.
        doc_id: Document ID for auto-generation.

    Returns:
        List of alias strings including auto-generated variants.
    """
    aliases = set()

    if 'aliases' in frontmatter:
        raw = frontmatter['aliases']
        if isinstance(raw, list):
            aliases.update(str(a).strip() for a in raw if a)
        elif isinstance(raw, str):
            stripped = raw.strip()
            if stripped:
                aliases.add(stripped)

    # Auto-generate aliases from id
    if doc_id:
        # snake_case → Title Case
        aliases.add(doc_id.replace('_', ' ').title())
        # snake_case → kebab-case
        aliases.add(doc_id.replace('_', '-'))

    return sorted(aliases)
```

**Test:**
```bash
python -c "from ontos.core.frontmatter import normalize_aliases; print(normalize_aliases({}, 'auth_flow'))"
# Expected: ['Auth Flow', 'auth-flow']
```

**Commit:**
```
feat(frontmatter): add normalize_aliases function

- Extracts explicit aliases from frontmatter
- Auto-generates Title Case and kebab-case from ID
- Returns sorted list

Ref: v3.1.0 §3.1
```

---

### Task A.3: `DocumentCache` class

**Spec Reference:** §3.3
**Priority:** P0
**File:** `ontos/core/cache.py` — CREATE

---

**Create new file `ontos/core/cache.py`:**
```python
"""Document caching with mtime-based invalidation.

PURE: This module contains no I/O operations. Callers must provide
mtime values from their own file operations.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


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

        # Check cache (caller provides current mtime)
        if (cached := cache.get(path, current_mtime)) is not None:
            return cached

        # Parse and store
        data = parse_document(path)
        cache.set(path, data, current_mtime)
        return data
    """
    _entries: Dict[Path, CacheEntry] = field(default_factory=dict)
    _hits: int = 0
    _misses: int = 0

    def get(self, path: Path, current_mtime: float) -> Optional[Any]:
        """Get cached document if mtime unchanged.

        Args:
            path: Resolved file path.
            current_mtime: Current file modification time.

        Returns:
            Cached data if valid, None if cache miss or invalidated.
        """
        path = path.resolve()

        if path not in self._entries:
            self._misses += 1
            return None

        entry = self._entries[path]
        if current_mtime == entry.mtime:
            self._hits += 1
            return entry.data

        # Invalidated
        del self._entries[path]
        self._misses += 1
        return None

    def set(self, path: Path, data: Any, mtime: float) -> None:
        """Store document in cache.

        Args:
            path: Resolved file path.
            data: Parsed document data.
            mtime: File modification time at parse time.
        """
        path = path.resolve()
        self._entries[path] = CacheEntry(mtime=mtime, data=data)

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

**Test:**
```bash
python -c "from ontos.core.cache import DocumentCache; c = DocumentCache(); c.set(Path('/tmp/test.md'), {'id': 'test'}, 123.0); print(c.get(Path('/tmp/test.md'), 123.0))"
# Expected: {'id': 'test'}
```

**Commit:**
```
feat(core): add DocumentCache with mtime invalidation

- Pure cache class with no I/O dependencies
- Mtime-based invalidation
- Stats tracking for debugging

Ref: v3.1.0 §3.3
```

---

### Task A.4: `CompactMode` enum

**Spec Reference:** §3.4
**Priority:** P0
**File:** `ontos/commands/map.py` — MODIFY

---

**Current imports (L10-15):**
```python
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
```

**Replace with:**
```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
```

**Add after imports, before `GenerateMapOptions` (before L22):**
```python


class CompactMode(Enum):
    """Compact output mode for context map."""
    OFF = "off"
    BASIC = "basic"
    RICH = "rich"
```

**Test:**
```bash
python -c "from ontos.commands.map import CompactMode; print(CompactMode.RICH.value)"
# Expected: rich
```

**Commit:**
```
feat(map): add CompactMode enum

- OFF: standard markdown output
- BASIC: id:type:status format
- RICH: id:type:status:"summary" format

Ref: v3.1.0 §3.4
```

---

### Task A.5: `_generate_compact_output()` function

**Spec Reference:** §3.4
**Priority:** P0
**File:** `ontos/commands/map.py` — MODIFY

---

**Add after `_generate_lint_section()` (after L285):**
```python


def _generate_compact_output(docs: Dict[str, Any], mode: CompactMode) -> str:
    """Generate compact context map format.

    Standard compact (BASIC): id:type:status
    Rich compact (RICH): id:type:status:"summary"

    Args:
        docs: Document dictionary (DocumentData objects).
        mode: CompactMode (BASIC or RICH).

    Returns:
        Compact format string, one doc per line.
    """
    if mode == CompactMode.OFF:
        return ""

    lines = []
    for doc_id, doc in sorted(docs.items()):
        doc_type = doc.type.value if hasattr(doc.type, 'value') else str(doc.type)
        doc_status = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)

        if mode == CompactMode.RICH:
            summary = doc.frontmatter.get('summary', '')
            if summary:
                # Escape backslashes, quotes, and newlines
                summary_safe = (summary
                    .replace('\\', '\\\\')
                    .replace('"', '\\"')
                    .replace('\n', '\\n'))
                lines.append(f'{doc_id}:{doc_type}:{doc_status}:"{summary_safe}"')
            else:
                lines.append(f'{doc_id}:{doc_type}:{doc_status}')
        else:
            lines.append(f'{doc_id}:{doc_type}:{doc_status}')

    return '\n'.join(lines)
```

**Test:**
```bash
python -c "
from ontos.commands.map import _generate_compact_output, CompactMode
from collections import namedtuple
Doc = namedtuple('Doc', ['type', 'status', 'frontmatter'])
docs = {'test': Doc(type='atom', status='active', frontmatter={'summary': 'Test \"doc\"'})}
print(_generate_compact_output(docs, CompactMode.RICH))
"
# Expected: test:atom:active:"Test \"doc\""
```

**Commit:**
```
feat(map): add compact output with escaping

- BASIC format: id:type:status
- RICH format: id:type:status:"summary"
- Escapes quotes, backslashes, newlines in summaries

Ref: v3.1.0 §3.4
```

---

### Task A.6: `_format_doc_link()` wikilink function

**Spec Reference:** §3.2
**Priority:** P0
**File:** `ontos/commands/map.py` — MODIFY

---

**Add after `_generate_compact_output()` (after Task A.5 code):**
```python


def _format_doc_link(doc_id: str, doc_path: Path, obsidian_mode: bool) -> str:
    """Format document link based on output mode.

    In Obsidian mode, uses [[filename|display]] format since Obsidian
    resolves links by filename, not frontmatter ID.

    Args:
        doc_id: Document ID from frontmatter.
        doc_path: Path to the document file.
        obsidian_mode: Whether to use Obsidian wikilink format.

    Returns:
        Formatted link string.
    """
    if obsidian_mode:
        filename = doc_path.stem  # filename without extension
        if filename == doc_id:
            return f"[[{doc_id}]]"  # No alias needed
        return f"[[{filename}|{doc_id}]]"  # Alias for display
    return f"`{doc_id}`"
```

**Test:**
```bash
python -c "
from ontos.commands.map import _format_doc_link
from pathlib import Path
print(_format_doc_link('auth_flow', Path('docs/auth_flow.md'), True))
print(_format_doc_link('auth_flow', Path('docs/authentication.md'), True))
print(_format_doc_link('auth_flow', Path('docs/auth.md'), False))
"
# Expected:
# [[auth_flow]]
# [[authentication|auth_flow]]
# `auth_flow`
```

**Commit:**
```
feat(map): add Obsidian wikilink formatting

- Uses [[filename|id]] format for Obsidian
- Falls back to `id` code format for standard output
- Handles filename != id case correctly

Ref: v3.1.0 §3.2
```

---

### Task A.7: `read_file_lenient()` function

**Spec Reference:** §3.5
**Priority:** P0
**File:** `ontos/io/obsidian.py` — CREATE

---

**Create new file `ontos/io/obsidian.py`:**
```python
"""Obsidian-specific file utilities.

Handles Obsidian vault edge cases like BOM and leading whitespace.
"""

from pathlib import Path
from typing import Optional


def read_file_lenient(path: Path) -> str:
    """Read file with Obsidian-compatible leniency.

    Handles common Obsidian vault edge cases:
    1. UTF-8 BOM (Byte Order Mark) at file start
    2. Leading whitespace/newlines before frontmatter delimiter

    Args:
        path: Path to the markdown file.

    Returns:
        File content with BOM stripped and leading whitespace
        normalized for frontmatter detection.
    """
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


def detect_obsidian_vault(path: Path) -> bool:
    """Detect if path is within an Obsidian vault.

    Args:
        path: Path to check.

    Returns:
        True if .obsidian directory found in path or parents.
    """
    current = path.resolve()
    while current != current.parent:
        if (current / '.obsidian').is_dir():
            return True
        current = current.parent
    return False
```

**Test:**
```bash
python -c "from ontos.io.obsidian import read_file_lenient, detect_obsidian_vault; print('OK')"
```

**Commit:**
```
feat(io): add Obsidian leniency utilities

- read_file_lenient(): handles BOM and leading whitespace
- detect_obsidian_vault(): checks for .obsidian directory

Ref: v3.1.0 §3.5
```

---

### Task A.8: `FilterExpression` and `parse_filter()`

**Spec Reference:** §3.7
**Priority:** P1
**File:** `ontos/commands/map.py` — MODIFY

---

**Add after `_format_doc_link()` (after Task A.6 code):**
```python


@dataclass
class FilterExpression:
    """Single filter expression."""
    field: str
    values: list


def parse_filter(expr: str) -> list:
    """Parse filter expression string.

    Syntax: FIELD:VALUE | FIELD:VALUE,VALUE | EXPR EXPR
    - Multiple values for same field: OR (match any)
    - Multiple fields: AND (match all)

    Args:
        expr: Filter string like "type:strategy status:active"

    Returns:
        List of FilterExpression objects.
    """
    if not expr or not expr.strip():
        return []

    filters = []
    for part in expr.split():
        if ':' not in part:
            continue  # Skip invalid parts
        field, _, value = part.partition(':')
        field = field.strip().lower()
        if not field or not value:
            continue  # Skip empty field or value
        values = [v.strip() for v in value.split(',') if v.strip()]
        if values:
            filters.append(FilterExpression(field=field, values=values))
    return filters
```

**Test:**
```bash
python -c "
from ontos.commands.map import parse_filter
filters = parse_filter('type:strategy,kernel status:active')
for f in filters:
    print(f'{f.field}: {f.values}')
"
# Expected:
# type: ['strategy', 'kernel']
# status: ['active']
```

**Commit:**
```
feat(map): add filter expression parsing

- Parses FIELD:VALUE syntax
- Supports comma-separated values (OR)
- Supports multiple fields (AND)

Ref: v3.1.0 §3.7
```

---

### Task A.9: `matches_filter()` function

**Spec Reference:** §3.7
**Priority:** P1
**File:** `ontos/commands/map.py` — MODIFY

---

**Add after `parse_filter()` (after Task A.8 code):**
```python


def matches_filter(doc: Any, filters: list) -> bool:
    """Check if document matches all filter expressions.

    Args:
        doc: Document to check (DocumentData).
        filters: List of FilterExpression objects (AND).

    Returns:
        True if document matches all filters.
    """
    import fnmatch

    for f in filters:
        doc_type = doc.type.value if hasattr(doc.type, 'value') else str(doc.type)
        doc_status = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)

        if f.field == 'type':
            if doc_type.lower() not in [v.lower() for v in f.values]:
                return False
        elif f.field == 'status':
            if doc_status.lower() not in [v.lower() for v in f.values]:
                return False
        elif f.field == 'concept':
            concepts = doc.frontmatter.get('concepts', [])
            if not any(c.lower() in [v.lower() for v in f.values] for c in concepts):
                return False
        elif f.field == 'id':
            if not any(fnmatch.fnmatch(doc.id.lower(), v.lower()) for v in f.values):
                return False
        # Unknown fields: ignore (per CA guidance)

    return True
```

**Test:**
```bash
python -c "
from ontos.commands.map import matches_filter, FilterExpression
from collections import namedtuple
Doc = namedtuple('Doc', ['id', 'type', 'status', 'frontmatter'])
doc = Doc(id='auth_flow', type='strategy', status='active', frontmatter={'concepts': ['auth', 'api']})
filters = [FilterExpression('type', ['strategy']), FilterExpression('concept', ['auth'])]
print(matches_filter(doc, filters))
"
# Expected: True
```

**Commit:**
```
feat(map): add filter matching logic

- Supports type, status, concept, id fields
- Case-insensitive matching
- Glob patterns for id field
- Unknown fields ignored (pass-through)

Ref: v3.1.0 §3.7
```

---

### Task A.10: Update `MapOptions` dataclass

**Spec Reference:** §3.2
**Priority:** P0
**File:** `ontos/commands/map.py` — MODIFY

---

**Current code (L288-294):**
```python
@dataclass
class MapOptions:
    """CLI-level options for map command."""
    output: Optional[Path] = None
    strict: bool = False
    json_output: bool = False
    quiet: bool = False
```

**Replace with:**
```python
@dataclass
class MapOptions:
    """CLI-level options for map command."""
    output: Optional[Path] = None
    strict: bool = False
    json_output: bool = False
    quiet: bool = False
    obsidian: bool = False
    compact: CompactMode = CompactMode.OFF
    filter_expr: Optional[str] = None
    no_cache: bool = False
```

**Commit:**
```
feat(map): extend MapOptions with Track A fields

- obsidian: Enable Obsidian-compatible output
- compact: CompactMode enum for token efficiency
- filter_expr: Filter expression string
- no_cache: Bypass document cache

Ref: v3.1.0 §3.2
```

---

### Task A.11: Register new map flags in CLI

**Spec Reference:** §3.2, §3.3, §3.4, §3.7
**Priority:** P0
**File:** `ontos/cli.py` — MODIFY

---

**Current code (L115-122):**
```python
def _register_map(subparsers, parent):
    """Register map command."""
    p = subparsers.add_parser("map", help="Generate context map", parents=[parent])
    p.add_argument("--strict", action="store_true",
                   help="Treat warnings as errors")
    p.add_argument("--output", "-o", type=Path,
                   help="Output path (default: Ontos_Context_Map.md)")
    p.set_defaults(func=_cmd_map)
```

**Replace with:**
```python
def _register_map(subparsers, parent):
    """Register map command."""
    p = subparsers.add_parser("map", help="Generate context map", parents=[parent])
    p.add_argument("--strict", action="store_true",
                   help="Treat warnings as errors")
    p.add_argument("--output", "-o", type=Path,
                   help="Output path (default: Ontos_Context_Map.md)")
    p.add_argument("--obsidian", action="store_true",
                   help="Enable Obsidian-compatible output (wikilinks, tags)")
    p.add_argument("--compact", nargs="?", const="basic", default="off",
                   choices=["basic", "rich"],
                   help="Compact output: 'basic' (default) or 'rich' (with summaries)")
    p.add_argument("--filter", "-f", metavar="EXPR",
                   help="Filter documents by expression (e.g., 'type:strategy')")
    p.add_argument("--no-cache", action="store_true",
                   help="Bypass document cache (for debugging)")
    p.set_defaults(func=_cmd_map)
```

**Commit:**
```
feat(cli): register Track A map flags

- --obsidian: Obsidian-compatible output
- --compact[=rich]: Token-efficient format
- --filter EXPR: Selective document loading
- --no-cache: Bypass cache for debugging

Ref: v3.1.0 §3.2-3.7
```

---

### Task A.12: Update `_cmd_map()` handler

**Spec Reference:** §3.2-3.7
**Priority:** P0
**File:** `ontos/cli.py` — MODIFY

---

**Find `_cmd_map()` function and update to pass new options.**

**Add import at top of file (after L15):**
```python
from ontos.commands.map import CompactMode
```

**Update `_cmd_map()` to construct MapOptions with new fields:**

Find the line that creates `MapOptions` and update it to include:
```python
    options = MapOptions(
        output=args.output,
        strict=args.strict,
        json_output=args.json,
        quiet=args.quiet,
        obsidian=args.obsidian,
        compact=CompactMode(args.compact) if args.compact != "off" else CompactMode.OFF,
        filter_expr=getattr(args, 'filter', None),
        no_cache=getattr(args, 'no_cache', False),
    )
```

**Commit:**
```
feat(cli): pass Track A options to map command

- Converts --compact string to CompactMode enum
- Passes all new flags to MapOptions

Ref: v3.1.0 §3.2-3.7
```

---

### Task A.13: Add verbose config output to doctor

**Spec Reference:** §3.6
**Priority:** P1
**File:** `ontos/commands/doctor.py` — MODIFY

---

**Note:** The `-v` flag is already registered in cli.py (L146-147). We need to add the verbose output logic.

**Add helper function before `doctor_command()` (before L456):**
```python

def _get_config_path() -> Optional[Path]:
    """Get config path if it exists."""
    config_path = Path.cwd() / ".ontos.toml"
    if config_path.exists():
        return config_path
    return None


def _print_verbose_config(options: DoctorOptions) -> None:
    """Print resolved configuration paths in verbose mode."""
    if not options.verbose:
        return

    from ontos.io.files import find_project_root
    from ontos.io.config import load_project_config

    try:
        project_root = find_project_root()
        config = load_project_config(repo_root=project_root)

        print("Configuration:")
        print(f"  repo_root:    {project_root}")
        print(f"  config_path:  {_get_config_path() or 'default'}")
        print(f"  docs_dir:     {project_root / config.paths.docs_dir}")
        print(f"  context_map:  {project_root / config.paths.context_map}")
        print()
    except Exception as e:
        print(f"Configuration: Unable to load ({e})")
        print()
```

**Update `doctor_command()` to call verbose output at start:**

Find the start of `doctor_command()` and add after the docstring:
```python
    # Print verbose config if requested
    _print_verbose_config(options)
```

**Commit:**
```
feat(doctor): add verbose mode with config paths

- Shows repo_root, config_path, docs_dir, context_map
- Only displays when -v flag is used

Ref: v3.1.0 §3.6
```

---

## Test Requirements

### New Test Files

| File | Coverage |
|------|----------|
| `tests/core/test_cache.py` | DocumentCache |
| `tests/test_frontmatter_tags.py` | normalize_tags, normalize_aliases |
| `tests/test_map_compact.py` | CompactMode, _generate_compact_output |
| `tests/test_map_filter.py` | FilterExpression, parse_filter, matches_filter |

### Required Test Cases

**normalize_tags():**
- [ ] Empty frontmatter → `[]`
- [ ] Only `concepts` field → concepts as tags
- [ ] Only `tags` field → tags only
- [ ] Both fields → merged, deduplicated, sorted
- [ ] String input (not list) → single-item list
- [ ] Empty/None values → filtered out

**DocumentCache:**
- [ ] `get()` on empty cache → `None`
- [ ] `set()` then `get()` (mtime unchanged) → returns data
- [ ] `get()` after mtime changed → `None` (invalidated)
- [ ] `invalidate()` removes entry
- [ ] `clear()` removes all entries
- [ ] `stats` property returns correct counts

**Compact output:**
- [ ] Basic format: `id:type:status`
- [ ] Rich format: `id:type:status:"summary"`
- [ ] Quote in summary → `\"` escaped
- [ ] Newline in summary → `\n` escaped
- [ ] Backslash in summary → `\\` escaped

**Filter:**
- [ ] Single field: `type:strategy` matches strategy docs
- [ ] Multiple values (OR): `type:strategy,kernel` matches either
- [ ] Multiple fields (AND): `type:strategy status:active` matches both
- [ ] Concept filter: `concept:auth` matches docs with auth concept
- [ ] Glob pattern: `id:auth_*` matches auth_flow, auth_config
- [ ] Case insensitivity: `TYPE:Strategy` works
- [ ] Unknown field → ignored (pass-through)

---

## Regression Testing Protocol

**After EACH task:**
```bash
pytest tests/ -v --tb=short
```

**If any test fails:**
1. STOP — do not proceed to next task
2. Identify regression cause
3. Fix before continuing
4. Re-run full suite

**After ALL tasks:**
```bash
# Full test suite
pytest tests/ -v

# Manual smoke tests (spec §8.1)
ontos map --obsidian
ontos map --compact
ontos map --compact=rich
ontos map --filter "type:strategy"
ontos map --no-cache
ontos doctor -v
```

---

## PR Preparation

**Branch:** `feat/v3.1.0-track-a`

**PR Title:** `feat: Track A — Obsidian compatibility + token efficiency`

**PR Description Template:**
```markdown
## Summary

Implements v3.1.0 Track A: Obsidian compatibility and token efficiency features.

## Changes

### New Files
- `ontos/core/cache.py` — Document cache with mtime invalidation
- `ontos/io/obsidian.py` — Obsidian-specific utilities

### Modified Files
- `ontos/core/frontmatter.py` — normalize_tags(), normalize_aliases()
- `ontos/commands/map.py` — CompactMode, compact output, wikilinks, filter
- `ontos/commands/doctor.py` — verbose config output
- `ontos/cli.py` — Flag registrations

### New Flags
- `--obsidian` — Obsidian-compatible output (wikilinks, tags)
- `--compact[=rich]` — Token-efficient output format
- `--filter EXPR` — Selective document loading
- `--no-cache` — Bypass document cache

## Testing

- [ ] All existing tests pass
- [ ] New tests for cache, tags, compact, filter
- [ ] Manual verification per spec §8.1

## Spec Reference

v3.1.0 Implementation Spec v1.2, §3
```

---

## CA Guidance Reminders

Per the v3.1.0 Final Decision (Phase B.6):

1. **Filter error handling:**
   - Unknown fields: ignore (pass-through)
   - Empty values: match nothing
   - Unmatched quotes: syntax error — report and reject

2. **Obsidian leniency:**
   - `read_file_lenient()` behavior (returning stripped content) is intentional
   - Only affects leading whitespace before frontmatter

---

*Track A Implementation Prompt — Phase C.1a*
*Chief Architect (Claude Opus 4.5) — 2026-01-21*
