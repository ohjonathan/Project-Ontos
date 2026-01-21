---
id: v3_1_0_implementation_spec
type: strategy
status: draft
depends_on: [v3_0_5_implementation_spec, v3_1_0_implementation_plan, v3_1_tech_debt_wrapper_commands]
concepts: [implementation-spec, native-migration, obsidian, token-efficiency, wrapper-commands]
---

# Ontos v3.1.0 Implementation Spec

**Version:** 1.1
**Author:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-21
**Status:** Draft — Ready for Review Board

**Changelog:**
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
| OBS-4 | Wikilink output | P0 | Medium | `[[doc_id]]` format in context map |
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

### 3.2 OBS-3/OBS-4: Obsidian Mode for Map Command

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
    compact: bool = False   # NEW (TOK-2)
    filter: Optional[str] = None  # NEW (TOK-3)
```

**Wikilink Output Logic:**
```python
def _format_doc_link(doc_id: str, obsidian_mode: bool) -> str:
    """Format document link based on output mode."""
    if obsidian_mode:
        return f"[[{doc_id}]]"
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

---

### 3.4 TOK-2: Compact Output Format

**File:** `ontos/commands/map.py`

**Compact Format Implementation:**
```python
def _generate_compact_output(docs: Dict[str, Document], rich: bool = False) -> str:
    """Generate compact context map format.

    Standard compact: id:type:status
    Rich compact: id:type:status:"summary"

    Args:
        docs: Document dictionary
        rich: Include summary field if True

    Returns:
        Compact format string, one doc per line
    """
    lines = []
    for doc_id, doc in sorted(docs.items()):
        if rich and doc.summary:
            lines.append(f'{doc_id}:{doc.type}:{doc.status}:"{doc.summary}"')
        else:
            lines.append(f'{doc_id}:{doc.type}:{doc.status}')
    return '\n'.join(lines)
```

**CLI Flag:**
```python
p.add_argument("--compact", nargs="?", const=True, default=False,
               help="Compact output format (use --compact=rich for summaries)")
```

---

### 3.5 ERR-1: Better YAML Error Messages

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
    """
    errors = []
    # ... implementation with error collection
    return frontmatter, errors
```

**Known Limitations:** [AMENDED: AUD-12]

The following edge cases are documented but not fully handled in v3.1.0:

| Case | Behavior | Target |
|------|----------|--------|
| BOM (Byte Order Mark) | May fail to parse frontmatter | v3.2.0 |
| `---` inside content | May cause false delimiter detection | v3.2.0 |
| Leading whitespace before `---` | May skip frontmatter | v3.2.0 |

These edge cases are rare in practice. ERR-1 catches most common errors.

---

### 3.6 DOC-1: Doctor Verbose Mode [AMENDED: AUD-07]

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

**Implementation:**
```python
def _print_config_paths(ctx: SessionContext, verbose: bool) -> None:
    """Print resolved configuration paths in verbose mode."""
    if not verbose:
        return

    print("Configuration:")
    print(f"  repo_root:    {ctx.repo_root}")
    print(f"  config_path:  {ctx.config_path or 'default'}")
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

## 4. Track B: Native Command Implementations

### 4.1 CMD-1: scaffold (CRITICAL)

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

### Modified Files

| File | Changes |
|------|---------|
| `ontos/core/frontmatter.py` | `normalize_tags()`, `normalize_aliases()`, `FrontmatterParseError` |
| `ontos/commands/map.py` | `--obsidian`, `--compact`, `--filter` flags, cache integration |
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
# Verify: wikilinks in output, tags normalized

# Compact output
ontos map --compact
wc -c Ontos_Context_Map.md  # Should be 30-50% smaller

ontos map --compact=rich
# Verify: summaries included

# Caching
time ontos map  # First run
time ontos map  # Second run (should be <100ms)

# Filtering
ontos map --filter "type:strategy"
# Verify: only strategy docs in output

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
```

---

## 9. Risk Assessment

**Overall Risk: MEDIUM**

| Risk Factor | Assessment | Mitigation |
|-------------|------------|------------|
| Scope size | Large (2 tracks) | Clear phase boundaries |
| Breaking changes | Low | Native commands preserve behavior |
| Regression | Medium | Comprehensive tests |
| Timeline | 4 weeks | Prioritized implementation order |

---

## 10. Success Criteria

### Track A
- [ ] `ontos map --obsidian` generates wikilinks
- [ ] `ontos map --compact` produces 30-50% smaller output
- [ ] `ontos map --filter "type:strategy"` works
- [ ] Cache improves repeat `ontos map` to <100ms
- [ ] YAML errors include line numbers
- [ ] `ontos doctor -v` shows resolved paths [AMENDED: AUD-07]

### Track B
- [ ] All 7 commands work as native implementations
- [ ] `ontos scaffold docs/` accepts positional argument
- [ ] `ontos verify file.md` accepts positional argument
- [ ] All existing functionality preserved
- [ ] `.ontos.toml` configuration honored
- [ ] No subprocess/PYTHONPATH manipulation

### Quality
- [ ] Test coverage >90% for new code
- [ ] README Known Issues section cleared or "No known issues"
- [ ] All golden master tests pass

---

## 11. Post-Release

### Documentation Updates
- [ ] Update README.md (remove Known Issues)
- [ ] Update Ontos_Manual.md with new flags
- [ ] Update CHANGELOG.md

### Cleanup
- [ ] Deprecate legacy scripts (add warnings)
- [ ] Consider removing `ontos/_scripts/` in v3.2

---

## Appendix A: Deferred Items [AMENDED: Audit Triage Part 8]

Items considered but explicitly excluded from v3.1.0 scope:

### v3.2 Candidates

| ID | Item | Source | Effort | Rationale |
|----|------|--------|--------|-----------|
| AUD-06 | Schema 3.0 field implementation | Claude audit | Medium | Non-breaking addition; low impact currently |
| AUD-09 | Tests in sdist or separate package | Claude, Codex | Low | Packaging decision; document "run from repo" |
| AUD-12 | Full frontmatter parsing robustness | Codex audit | Medium | ERR-1 covers most cases; edge cases rare |
| AUD-13 | Versioned documentation (ReadTheDocs) | Codex audit | Medium | Infrastructure concern; not blocking |
| AUD-14 | SessionContext refactor | Claude audit | Medium | Internal tech debt; no user impact |
| AUD-15 | Complete type hints | Claude audit | Low | Code quality; not blocking adoption |
| AUD-16 | `--dry-run` on remaining commands | Claude audit | Low | scaffold/consolidate covered in v3.1 |
| RES-01 | `intent` field in schema | Research review | Low | Non-breaking schema addition |
| RES-02 | `--format xml` flag | Research review | Medium | Alternative output format |
| RES-03 | Hash verification for staleness | Research review | Medium | Stronger than date-based verification |

### v4.0 Candidates

| ID | Item | Source | Effort | Rationale |
|----|------|--------|--------|-----------|
| AUD-05 | MCP server implementation | Claude, Codex | High | Requires infrastructure; v4.0 scope |
| AUD-08 | Programmatic activation (replaces AGENTS.md) | Claude audit | High | MCP provides programmatic alternative |
| RES-04 | Navigator pattern (cheap model filter) | Research review | High | Requires MCP infrastructure |
| RES-05 | Automated metadata refresh GitHub Action | Research review | Medium | CI/CD integration |

---

## Appendix B: Amendment Traceability

| Amendment | Source | Section(s) Modified |
|-----------|--------|---------------------|
| DOC-1: `doctor -v` | AUD-07 | §2, §3.6, §6, §7, §8.1, §10 |
| ERR-1 known limitations | AUD-12 | §3.5 |
| Deferred items backlog | Audit Triage Part 8 | Appendix A |

---

## Appendix C: Open Questions

Questions requiring additional research, clarification, or validation. Designed to trigger substantive investigation from other LLMs or domain experts.

---

### C.1 Token Efficiency (TOK-1/TOK-2 Validation)

| ID | Question | Context | Research Angle |
|----|----------|---------|----------------|
| OQ-01 | **What is the actual token cost comparison between our Markdown table format, compact format, and JSON?** | Research §3.1 claims 40-60% JSON overhead, but we lack benchmarks for our specific output. | Measure with `tiktoken` (GPT) and Claude's tokenizer. Compare 10/50/100/500 document context maps. |
| OQ-02 | **At what document count does compact format become essential vs nice-to-have?** | Small repos may not benefit; large repos may require it. Where's the inflection point? | Profile `ontos map` output size vs LLM context windows (128k, 200k). |
| OQ-03 | **How do different LLMs tokenize our colon-delimited compact format?** | BPE tokenization varies. `:` may tokenize differently in Claude vs GPT-4 vs Gemini. | Test identical compact output across models. Look for pathological cases. |
| OQ-04 | **Is our `id:type:status` delimiter optimal, or would pipe `\|` or tab be more token-efficient?** | Research §3.1 mentions colon as "familiar" but doesn't benchmark alternatives. | Tokenize same content with different delimiters. Measure variance. |

---

### C.2 Agent Interaction Patterns

| ID | Question | Context | Research Angle |
|----|----------|---------|----------------|
| OQ-05 | **What is the optimal cardinality for `concepts` (tags) to enable deterministic agent filtering?** | Research §2.1.1 mentions "keyword triggers" but doesn't specify how many. Too few = no discrimination. Too many = noise. | Survey existing agent systems (Claude Code, Cursor, Copilot). Analyze their tag/keyword limits. |
| OQ-06 | **When `summary` and `intent` fields conflict, which should agents prioritize?** | Research §2.1.2 recommends `intent` but we have existing `summary` fields. Migration path? | Test agent retrieval accuracy with conflicting metadata. A/B test intent-only vs summary-only. |
| OQ-07 | **What error message patterns do agents parse most reliably?** | ERR-1 adds line numbers, but what format? `file:line:col`? JSON? | Test error message parsing across Claude, GPT-4, Gemini with different formats. |
| OQ-08 | **Do agents benefit from explicit "use this for X" instructions in frontmatter, or is it noise?** | Research §2.1.2 claims instruction-phrased descriptions outperform passive ones. Is this universal? | Benchmark retrieval accuracy with/without intent-style descriptions. |

---

### C.3 Obsidian Compatibility Edge Cases

| ID | Question | Context | Research Angle |
|----|----------|---------|----------------|
| OQ-09 | **How should we resolve wikilink ambiguity when multiple documents have similar IDs?** | E.g., `auth_flow` vs `auth_flow_v2`. Does `[[auth_flow]]` match both? First? Exact only? | Study Obsidian's resolution algorithm. Test with ambiguous vaults. |
| OQ-10 | **Should we support Obsidian's `[[doc\|display text]]` alias syntax in output?** | OBS-4 specifies `[[doc_id]]` but Obsidian supports `[[doc_id\|Pretty Name]]`. | Survey Obsidian user expectations. Measure adoption of alias syntax in the wild. |
| OQ-11 | **How do vault-level `.obsidian/` settings interact with repo-level `.ontos.toml`?** | Users may have Obsidian defaults that conflict with Ontos config. Precedence? | Document conflict scenarios. Test with real Obsidian vaults. |
| OQ-12 | **What happens when a repo spans multiple Obsidian vaults?** | Monorepos may have `/docs` and `/wiki` as separate vaults. How should Ontos handle cross-vault links? | Research cross-vault linking patterns. Survey monorepo Obsidian users. |

---

### C.4 Cache & Performance Architecture

| ID | Question | Context | Research Angle |
|----|----------|---------|----------------|
| OQ-13 | **Should we support persistent (disk) cache in addition to in-memory?** | TOK-1 is in-memory only. Large repos may benefit from disk cache surviving process exit. | Benchmark cold start with/without disk cache. Measure cache file size growth. |
| OQ-14 | **What is the document count "performance cliff" where caching becomes critical?** | At 10 docs, caching may be overhead. At 1000 docs, it's essential. Where's the threshold? | Profile `ontos map` at 10/50/100/500/1000 documents. Measure parse time vs cache lookup. |
| OQ-15 | **How do Obsidian and Notion handle incremental indexing?** | Both have fast re-index on file change. What's their architecture? | Reverse-engineer Obsidian's indexing (it's Electron/local). Study Notion's sync protocol. |
| OQ-16 | **Is mtime-based invalidation sufficient, or should we use content hashing?** | mtime can be unreliable (git checkout, rsync). Hash is slower but deterministic. | Measure false invalidation rate with mtime in real git workflows. |

---

### C.5 Schema Evolution Strategy

| ID | Question | Context | Research Angle |
|----|----------|---------|----------------|
| OQ-17 | **How should Ontos handle documents with schema versions newer than the installed package?** | User has v3.1.0 installed but opens doc with `ontos_schema: 4.0`. Fail? Warn? Best-effort? | Study how databases handle forward compatibility. Survey JSON Schema evolution patterns. |
| OQ-18 | **Should we support "schema coercion" (auto-upgrade on read)?** | Old doc has `ontos_schema: 2.0`. Should `ontos map` silently upgrade it, or require explicit `ontos migrate`? | Study Jekyll/Hugo migration patterns. Survey user preferences on auto-upgrade. |
| OQ-19 | **What's the best UX pattern for breaking schema changes?** | If v4.0 removes a field, how do we communicate this to users? Error? Warning? Auto-fix? | Research semver in data schemas. Study Prisma/TypeORM migration UX. |
| OQ-20 | **Should schema version be in frontmatter or inferred from field presence?** | Current: explicit `ontos_schema` field. Alternative: detect version from which fields exist. | Analyze robustness of each approach. Test with malformed documents. |

---

### C.6 Frontmatter Robustness (AUD-12 Follow-up)

| ID | Question | Context | Research Angle |
|----|----------|---------|----------------|
| OQ-21 | **What is the real-world frequency of BOM, leading whitespace, and `---` edge cases?** | AUD-12 flags these but we don't know how common they are. Worth fixing in v3.1 or defer? | Scan public GitHub repos with YAML frontmatter. Measure edge case frequency. |
| OQ-22 | **Should we adopt a stricter parser (fail-fast) or more lenient one (best-effort)?** | Strict = fewer surprises but more friction. Lenient = more forgiving but silent failures. | Survey user preferences. Study how Hugo/Jekyll/Docusaurus handle edge cases. |
| OQ-23 | **How do Hugo, Jekyll, and Docusaurus handle frontmatter delimiter detection?** | They've solved this at scale. What's their algorithm? | Read their source code. Document their approaches. |
| OQ-24 | **Should we support TOML frontmatter (`+++`) as an alternative to YAML?** | Hugo supports both. Some users prefer TOML's stricter typing. | Survey user demand. Measure adoption of TOML frontmatter in the wild. |

---

### C.7 Competitive Landscape & Standards

| ID | Question | Context | Research Angle |
|----|----------|---------|----------------|
| OQ-25 | **How does CTX (context-hub) approach context management compared to Ontos?** | CTX is a competitor mentioned in Claude audit. What's their architecture? | Deep-dive CTX documentation and source. Compare feature matrix. |
| OQ-26 | **What patterns are emerging in MCP-native documentation tools?** | MCP is becoming standard for agent tooling. Are there MCP-first doc tools we should study? | Survey MCP server registry. Identify documentation-focused servers. |
| OQ-27 | **Is there a de facto standard emerging for agent-readable project metadata?** | `.github/`, `AGENTS.md`, `.cursor/`, `.claude/` — is one winning? | Survey AI coding tool adoption. Track which metadata patterns get used. |
| OQ-28 | **What's the trajectory of context window sizes, and how does it affect Ontos's value proposition?** | If context windows grow to 10M tokens, does token efficiency still matter? | Track context window growth across models. Model when efficiency becomes irrelevant. |

---

### C.8 Research Validation Priorities

If resources are limited, prioritize these questions for immediate research:

| Priority | Question ID | Rationale |
|----------|-------------|-----------|
| **P0** | OQ-01, OQ-02 | Token efficiency is core value prop. Need hard numbers. |
| **P0** | OQ-05, OQ-06 | Agent interaction patterns directly affect adoption. |
| **P1** | OQ-13, OQ-14 | Cache architecture affects v3.1 implementation. |
| **P1** | OQ-21, OQ-22 | Informs v3.2 frontmatter robustness work. |
| **P2** | OQ-25, OQ-27 | Competitive intelligence for roadmap. |

---

*Chief Architect (Claude Opus 4.5) — 2026-01-21*
