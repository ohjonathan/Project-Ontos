---
id: v3_1_0_spec_review_claude
type: review
status: complete
depends_on: [v3_1_0_implementation_spec, v3_1_0_audit_triage_chief_architect]
concepts: [spec-review, alignment-review, v3.1.0]
---

# v3.1.0 Spec Review — Claude (Alignment/Technical Reviewer)

**Spec Version:** 1.1
**Reviewer:** Claude Opus 4.5 (Technical/Alignment)
**Date:** 2026-01-21
**Review Type:** Spec Review (Phase B)

---

## Part 1: Findings Verification

### Finding 1: Legacy Wrapper Architecture

**My original finding:** The `_cmd_wrapper` pattern shelling out to `_scripts/*.py` via subprocess is technical debt that breaks `.ontos.toml` configuration, creates two execution paths, and makes debugging harder.

**CA's disposition:** ✅ Addressed in v3.1.0 (Track B: CMD-1 through CMD-7)

**CA's interpretation:** "Track B eliminates wrappers entirely" — 7 wrapper commands migrated to native implementations.

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | CA accurately identified this as the top priority |
| Severity assessment? | ✅ Agree | Correctly marked as P0 Critical |
| Scope decision? | ✅ Accept | Full native migration is the right approach |
| Rationale valid? | ✅ | "All 3 reviewers agree legacy wrapper debt is the top issue" |

**Verdict:** Accept

---

### Finding 2: MCP Placeholder Module Confusion

**My original finding:** `ontos/mcp/__init__.py` is empty (512 bytes), `[mcp]` optional dependency exists but no implementation. The gap between v4.0 vision and current state is large.

**CA's disposition:** ❌ Deferred to v4.0

**CA's interpretation:** "MCP is explicitly v4.0 scope. FutureWarning (v3.0.5) mitigates confusion."

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | CA understood the concern |
| Severity assessment? | ⚠️ Disagree | I rated as P0 adoption risk; CA rated as deferrable |
| Scope decision? | ✅ Accept | Given v3.1.0 is focused on fixing existing commands, deferral is reasonable |
| Rationale valid? | ✅ | FutureWarning is appropriate mitigation |

**Verdict:** Accept with note

**Note:** The competitive window concern remains valid. The FutureWarning is good mitigation, but shipping even a read-only MCP server in v3.2 should be considered to maintain competitive position. Appendix A correctly targets this for v4.0, but the timeline pressure is real.

---

### Finding 3: Magic Defaults / Implicit Config Resolution

**My original finding:** `load_project_config()` and implicit config resolution make it hard to debug. Users can't see what paths Ontos actually resolved.

**CA's disposition:** ✅ Addressed in v3.1.0 (DOC-1: `doctor -v`)

**CA's interpretation:** "Add `ontos doctor -v` verbose output showing resolved paths (repo_root, config_path, docs_dir)"

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | CA correctly identified this as a UX/debugging issue |
| Severity assessment? | ✅ Agree | P1 is appropriate |
| Scope decision? | ✅ Accept | `doctor -v` is the right place for this |
| Rationale valid? | ✅ | "Low effort, immediate value" — correct |

**Verdict:** Accept

The implementation in §3.6 is clean:
```python
def _print_config_paths(ctx: SessionContext, verbose: bool) -> None:
    """Print resolved configuration paths in verbose mode."""
    if not verbose:
        return
    print("Configuration:")
    print(f"  repo_root:    {ctx.repo_root}")
    print(f"  config_path:  {ctx.config_path or 'default'}")
    # ...
```

This directly addresses my concern. Good.

---

### Finding 4: AGENTS.md Activation Flow is Fragile

**My original finding:** Manual activation via AGENTS.md relies on agents voluntarily following instructions. No programmatic verification. Competes with built-in context systems.

**CA's disposition:** ❌ Deferred to v4.0

**CA's interpretation:** "Manual activation works. MCP server (v4.0) provides programmatic alternative. Research §2.1 confirms sidecar pattern is correct direction."

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | CA understood the fragility concern |
| Severity assessment? | ✅ Agree | Medium risk, not blocking |
| Scope decision? | ✅ Accept | MCP is the right long-term fix |
| Rationale valid? | ✅ | Research validation strengthens the deferral |

**Verdict:** Accept

---

### Finding 5: Schema Version Confusion (2.2 vs 3.0)

**My original finding:** 5 schema versions defined (1.0-3.0), current schema is 2.2, package version is 3.0.5. Schema 3.0 references fields (`implements`, `tests`, `deprecates`) not found elsewhere. Users may be confused.

**CA's disposition:** ❌ Deferred to v3.2 (AUD-06)

**CA's interpretation:** "Schema 3.0 fields can be added in v3.2 without breaking changes. Low impact currently."

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | CA understood the version mismatch concern |
| Severity assessment? | ⚠️ Disagree slightly | I saw this as confusion risk; CA sees as low impact |
| Scope decision? | ✅ Accept | Non-breaking addition can wait |
| Rationale valid? | ✅ | Fair point — these fields aren't used yet |

**Verdict:** Accept with note

**Note:** Consider updating `CURRENT_SCHEMA_VERSION` to 3.0 when the package ships v3.1.0, or document why schema versions are independent of package versions.

---

### Finding 6: SessionContext Mixed Responsibilities

**My original finding:** SessionContext handles both transaction state (pending_writes) and repo configuration. Comment says "should NOT cache parsed documents" but also "single source of truth for repository configuration." Two responsibilities.

**CA's disposition:** ❌ Deferred to v3.2 (AUD-14)

**CA's interpretation:** "Internal tech debt; no user impact."

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | CA understood the SRP concern |
| Severity assessment? | ✅ Agree | Internal refactor, not user-facing |
| Scope decision? | ✅ Accept | Correct priority — fix user-facing issues first |
| Rationale valid? | ✅ | No user impact is true |

**Verdict:** Accept

---

### Finding 7: Incomplete Type Hints

**My original finding:** `__init__.py` re-exports many functions but several lack complete type hints. For a Python 3.9+ package, full typing helps IDE users.

**CA's disposition:** ❌ Deferred to v3.2 (AUD-15)

**CA's interpretation:** "Code quality; not blocking adoption."

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | CA understood this is about code quality |
| Severity assessment? | ✅ Agree | Low priority |
| Scope decision? | ✅ Accept | Correct to defer |
| Rationale valid? | ✅ | Not blocking is accurate |

**Verdict:** Accept

---

### Finding 8: No --dry-run on Many Commands

**My original finding:** Users want to preview changes before writes.

**CA's disposition:** ⚠️ Partial — `--dry-run` added to scaffold/consolidate in v3.1.0

**CA's interpretation:** "scaffold/consolidate covered in v3.1. Other commands can get it in v3.2."

| Check | Status | Notes |
|-------|--------|-------|
| Understood correctly? | ✅ | CA understood the UX concern |
| Severity assessment? | ✅ Agree | P1 for critical commands |
| Scope decision? | ✅ Accept | Covering the two most impactful commands is reasonable |
| Rationale valid? | ✅ | scaffold and consolidate are the ones where dry-run matters most |

**Verdict:** Accept

---

## Part 2: Spec Completeness Review

| Section | Present? | Adequate? | Issues |
|---------|----------|-----------|--------|
| Scope definition | ✅ | ✅ | Clear Track A/B split, prioritized items |
| Technical design | ✅ | ✅ | Code samples for all major changes |
| Code samples | ✅ | ⚠️ | See Part 3 for specific issues |
| Test strategy | ✅ | ⚠️ | §8.3 mentions >90% coverage but no test structure spec |
| Risk assessment | ✅ | ✅ | §9 is appropriately cautious |
| Success criteria | ✅ | ✅ | §10 has measurable, verifiable criteria |
| Implementation order | ✅ | ✅ | §7 phasing is logical |
| Deferred items | ✅ | ✅ | Appendix A is thorough with rationale |

**Overall:** Spec is implementation-ready. Minor gaps in test strategy details.

---

## Part 3: Code Sample Review

### §3.1: `normalize_tags()` and `normalize_aliases()`

```python
def normalize_tags(frontmatter: dict) -> list[str]:
    tags = set()
    if 'tags' in frontmatter:
        raw_tags = frontmatter['tags']
        if isinstance(raw_tags, list):
            tags.update(str(t) for t in raw_tags if t)
        elif isinstance(raw_tags, str):
            tags.add(raw_tags)
    # ...
```

| Check | Status | Issue |
|-------|--------|-------|
| Handles expected inputs | ✅ | Lists and strings handled |
| Handles edge cases | ⚠️ | See below |
| Error handling adequate | ✅ | Graceful type coercion |
| Type safety | ✅ | `list[str]` return type |

**Edge cases to consider:**
1. `tags: null` — `frontmatter['tags']` would be `None`, which fails `isinstance` checks but doesn't raise. ✅ Safe.
2. `tags: 123` (numeric) — Not a list or string, so ignored. May want to coerce `str(123)` for robustness.
3. `tags: ""` (empty string) — `if t` filters it. ✅ Safe.
4. `concepts: tag-with-special/chars` — Passed through as-is. Obsidian may choke on slashes.

**Issues found:** 
- Minor: Numeric tags silently ignored. Consider `str()` coercion for all non-list values.
- Minor: No validation that tags are Obsidian-safe (no slashes, no spaces). Could cause issues in OBS-1.

---

### §3.3: `DocumentCache`

```python
@dataclass
class DocumentCache:
    _entries: Dict[Path, CacheEntry] = field(default_factory=dict)
    
    def get(self, path: Path) -> Optional[Any]:
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
```

| Check | Status | Issue |
|-------|--------|-------|
| Cache invalidation correct | ✅ | mtime comparison is standard |
| Thread safety (if relevant) | ⚠️ | Not thread-safe; OK for CLI |
| Memory management | ⚠️ | No size limit; could grow unbounded |
| Edge cases handled | ⚠️ | See below |

**Edge cases:**
1. **Race condition:** File modified between `stat()` and read. Cache would return stale data on next call, but that's acceptable for CLI.
2. **Float precision:** `st_mtime` is float; direct `==` comparison should be fine for POSIX.
3. **No cache limit:** Large repos could accumulate entries. Consider LRU or max_entries.

**Issues found:**
- Medium: No `--no-cache` flag specified for debugging. Users may want to bypass cache.
- Low: No max_entries limit. For v3.1.0 scope this is probably fine, but should be documented.

**Recommendation:** Add to §5.1 config:
```toml
[performance]
cache_max_entries = 1000  # Optional limit
```

---

### §3.4: `_generate_compact_output()`

```python
def _generate_compact_output(docs: Dict[str, Document], rich: bool = False) -> str:
    lines = []
    for doc_id, doc in sorted(docs.items()):
        if rich and doc.summary:
            lines.append(f'{doc_id}:{doc.type}:{doc.status}:"{doc.summary}"')
        else:
            lines.append(f'{doc_id}:{doc.type}:{doc.status}')
    return '\n'.join(lines)
```

| Check | Status | Issue |
|-------|--------|-------|
| Output format correct | ✅ | Matches spec |
| Escaping handled | ❌ | Quotes in summary not escaped |
| Edge cases handled | ⚠️ | See below |

**Issues found:**
- **Critical:** If `doc.summary` contains a `"` character, the output becomes malformed:
  ```
  auth_flow:atom:active:"User says "hello" here"
  ```
  This breaks parsing.
  
**Recommendation:** Escape quotes or use a different delimiter:
```python
summary_escaped = doc.summary.replace('"', '\\"')
lines.append(f'{doc_id}:{doc.type}:{doc.status}:"{summary_escaped}"')
```

Or use single quotes for the outer wrapper and escape appropriately.

---

### §3.5: `FrontmatterParseError`

```python
@dataclass
class FrontmatterParseError:
    filepath: str
    line: int
    column: int
    message: str
    suggestion: Optional[str] = None
```

| Check | Status | Issue |
|-------|--------|-------|
| Structure correct | ✅ | All needed fields |
| Error format standard | ✅ | `file:line:col` is universal |
| Complete | ⚠️ | No severity level |

**Minor:** Consider adding `severity: Literal["error", "warning"]` for graduated feedback.

---

### §3.6: `doctor -v` Implementation

```python
def _print_config_paths(ctx: SessionContext, verbose: bool) -> None:
    if not verbose:
        return
    print("Configuration:")
    print(f"  repo_root:    {ctx.repo_root}")
    print(f"  config_path:  {ctx.config_path or 'default'}")
    # ...
```

| Check | Status | Issue |
|-------|--------|-------|
| Logic correct | ✅ | Clean conditional |
| Output format clear | ✅ | Indented key-value pairs |

**Issue:** `ctx.config_path` isn't defined in the existing `SessionContext` dataclass. Either:
1. Add `config_path: Optional[Path] = None` to SessionContext, or
2. Compute it in the doctor command

**Recommendation:** Update §3.6 to show where `config_path` comes from.

---

### §4.x: Track B Native Command Options

Reviewed CMD-1 through CMD-7 dataclass definitions. All look correct:
- Positional arguments properly handled (`path: Optional[Path] = None`)
- `--dry-run` included where promised (scaffold, consolidate)
- Options match documented behavior

**No issues found in Track B specifications.**

---

## Part 4: Technical Concerns

| # | Concern | Section | Severity | Recommendation |
|---|---------|---------|----------|----------------|
| T-1 | Quote escaping in compact output | §3.4 | High | Escape `"` in summaries |
| T-2 | `config_path` not on SessionContext | §3.6 | Medium | Clarify source or add field |
| T-3 | No cache size limit | §3.3 | Low | Document or add config option |
| T-4 | No `--no-cache` flag | §3.3 | Low | Add for debugging |

---

## Part 5: Decisions I Challenge

| Issue | CA Decision | My Challenge | Recommended Change |
|-------|-------------|--------------|-------------------|
| T-1: Quote escaping | Not addressed in spec | Compact output will produce malformed data | Add escaping logic to §3.4 before implementation |

**This is the only blocking issue.** The compact format with rich summaries will break if any summary contains a quote character. This should be fixed in the spec before implementation.

---

## Part 6: Decisions I Accept (With Notes)

| Issue | CA Decision | My Note |
|-------|-------------|---------|
| MCP deferred to v4.0 | AUD-05 deferred | Competitive pressure remains; consider accelerating to v3.2 if resources allow |
| Schema 3.0 fields deferred | AUD-06 deferred | Document why schema != package version in README |
| SessionContext refactor deferred | AUD-14 deferred | Track as technical debt; don't let it grow |

---

## Part 7: Items Not Addressed

| My Finding | Status |
|------------|--------|
| Legacy wrapper architecture | ✅ Addressed (Track B) |
| MCP placeholder confusion | ✅ Addressed (deferred with FutureWarning) |
| Magic defaults | ✅ Addressed (DOC-1) |
| AGENTS.md fragility | ✅ Addressed (deferred to v4.0 MCP) |
| Schema version confusion | ✅ Addressed (deferred with rationale) |
| SessionContext responsibilities | ✅ Addressed (deferred to v3.2) |
| Incomplete type hints | ✅ Addressed (deferred to v3.2) |
| No --dry-run | ✅ Addressed (partial, scaffold/consolidate) |

**All my findings were addressed in the triage.**

---

## Part 8: Open Questions Research

### OQ-13: Should we support persistent (disk) cache in addition to in-memory?

**Research conducted:** Analyzed typical CLI tool patterns and Python caching libraries.

**Findings:**
- In-memory cache is appropriate for v3.1.0 scope. CLI tools typically don't persist cache across invocations.
- Disk cache introduces complexity: invalidation on git operations, stale data if .ontos.toml changes, disk I/O overhead for small repos.
- Python's `functools.lru_cache` and `joblib.Memory` patterns suggest disk cache is valuable only when parse time >> disk I/O time.

**Recommendation:** Keep in-memory for v3.1.0. If `ontos map` profiling shows parse time >500ms for typical repos (50-100 docs), consider disk cache for v3.2.

**Confidence:** High

---

### OQ-17: How should Ontos handle documents with schema versions newer than the installed package?

**Research conducted:** Reviewed JSON Schema evolution patterns, database migration UX (Prisma, Alembic), and API versioning best practices.

**Findings:**
- **Best practice:** Fail loudly with actionable message. Silent degradation causes data corruption.
- Current `check_compatibility()` already returns `INCOMPATIBLE` for future major versions and `READ_ONLY` for future minor versions. This is correct.
- Prisma pattern: "Your schema is too new for this version of Prisma. Please upgrade: `pip install --upgrade prisma`"

**Recommendation:** Current implementation is correct. Enhance error message to include upgrade command:
```
Document uses schema 4.0, but ontos 3.1.0 only supports up to 3.x.
Upgrade: pip install --upgrade ontos
```

**Confidence:** High

---

### OQ-18: Should we support "schema coercion" (auto-upgrade on read)?

**Research conducted:** Studied Jekyll/Hugo migration patterns, database auto-migration behavior.

**Findings:**
- **Auto-upgrade is risky:** Silent modification of user files violates principle of least surprise.
- Jekyll approach: Warn about deprecated fields, but don't auto-modify. User runs explicit `jekyll migrate`.
- Hugo approach: Fail with clear instructions for manual migration.
- Ontos already has `ontos migrate --check` for this.

**Recommendation:** Do NOT auto-upgrade. Current explicit `ontos migrate` command is correct. Add `--check` by default (already in CMD-7 spec) to show what would change.

**Confidence:** High

---

### OQ-20: Should schema version be in frontmatter or inferred from field presence?

**Research conducted:** Analyzed robustness of both approaches with malformed documents.

**Findings:**
- **Explicit is better:** Inference fails when fields are optional or removed.
- Current implementation in `detect_schema_version()` uses explicit first, then inference. This is correct.
- Risk: Inference can guess wrong if a legacy doc happens to have a field name that matches a newer schema.

**Recommendation:** Current approach is correct. In v3.1, encourage explicit `ontos_schema` in scaffold templates. Consider warning if inference is used: "Schema version inferred as 2.0 from field presence. Add `ontos_schema: 2.0` to make this explicit."

**Confidence:** High

---

## Part 9: Overall Verdict

**Findings Verification:** All 8 findings addressed — 5 in v3.1.0 scope, 3 appropriately deferred

**Spec Quality:** Ready for implementation with 1 blocking fix

**Summary:**
1. My v3.0.5 findings were properly handled. The CA correctly prioritized Track B (wrapper elimination) as the top issue and addressed my "magic defaults" concern with `doctor -v`.
2. The spec is implementable as written, except for the quote escaping bug in compact output (T-1).
3. The MCP deferral is strategically risky but tactically correct given the v3.1.0 scope.

**Blocking issues:** 1 (T-1: Quote escaping in `_generate_compact_output`)

**Top 3 concerns:**
1. **Quote escaping in compact output** — Will produce malformed output for summaries containing quotes
2. **`config_path` undefined** — §3.6 references a field that doesn't exist on SessionContext
3. **MCP competitive window** — Deferral is correct for scope but the timeline pressure is real

---

## Spec Sign-Off

**Status:** CONDITIONAL APPROVAL

**Condition:** Fix T-1 (quote escaping) before implementation begins.

**Recommended fix for T-1:**
```python
def _generate_compact_output(docs: Dict[str, Document], rich: bool = False) -> str:
    lines = []
    for doc_id, doc in sorted(docs.items()):
        if rich and doc.summary:
            # Escape quotes and newlines in summary
            summary_safe = doc.summary.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            lines.append(f'{doc_id}:{doc.type}:{doc.status}:"{summary_safe}"')
        else:
            lines.append(f'{doc_id}:{doc.type}:{doc.status}')
    return '\n'.join(lines)
```

Once T-1 is fixed, spec is approved for implementation.

---

**Review signed by:**
- **Role:** Alignment/Technical Reviewer
- **Model:** Claude Opus 4.5
- **Date:** 2026-01-21
- **Review Type:** Spec Review (Phase B)
