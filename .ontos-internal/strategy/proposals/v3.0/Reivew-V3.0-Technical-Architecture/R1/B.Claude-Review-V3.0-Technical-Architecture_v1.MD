# Ontos v3.0 Architecture Review

## Peer Architect: Claude Opus 4.5 (LLM C — Original Reviewer)
## Date: 2026-01-11

---

## 1. Decision Alignment Check

| Q# | Decision | Implemented? | Notes |
|----|----------|--------------|-------|
| Q1 | JSON output mode | ✅ Yes | `ui/json_output.py` specified with `JsonOutputHandler` class; `--json` global flag in CLI |
| Q2 | Export templates (DEFERRED) | ✅ Correctly deferred | Not present in v3.0 architecture; mentioned as v4.0 extension point |
| Q3 | Context slicing (DEFERRED) | ✅ Correctly deferred | Lazy loading with `ontos://` URIs not in v3.0; mentioned as v4.0 extension point |
| Q4 | Git-based change detection | ⚠️ Partial | `io/git.py` includes `get_changed_files_since_push()`, but integration with `commands/log.py` not fully specified |
| Q5 | Version pinning (warn-only) | ❌ No | `.ontos.toml` schema has `version = "3.0"` but no `required_version` field or version checking logic specified |
| Q6 | Shim hooks | ✅ Yes | Section 7.1 fully specifies shim pattern with correct implementation |
| Q7 | MCP client docs (DEFERRED) | ✅ Correctly deferred | No auto-config; `mcp/` directory is stub |
| Q8 | Progressive complexity / auto-summary | ✅ Yes | Section 8 specifies thresholds (>100 docs, >50k tokens) and `--depth` flags |
| Q9 | MCP security (DEFERRED) | ✅ Correctly deferred | No security implementation in v3.0; noted as v3.x/v4 item |
| Q10 | Pydantic in MCP layer | ✅ Yes | Section 11.1 specifies `[project.optional-dependencies] mcp = ["mcp>=1.0", "pydantic>=2.0"]` |
| Q11 | Script reorganization | ✅ Yes | Comprehensive decomposition in Section 3.2; clear module structure |
| Q12 | Stay Python | ✅ Yes | Architecture is entirely Python |
| Q13 | Markdown primary, JSON optional | ✅ Yes | Explicit in principles and output handling |

### Missing Decision Implementations

**Q4 Detail Gap:** The strategy says "Use `git diff` for change detection, require confirmation." The architecture specifies the git function but doesn't show how it integrates into the `ontos log` flow. Need: sequence showing user confirmation step after detection.

**Q5 Not Implemented:** Version pinning with warn-only was a v3.0 LOW priority item. The `.ontos.toml` schema doesn't include `required_version` and no version-checking logic is specified. This should either be added or explicitly documented as "deferred to v3.0.x."

---

## 2. Correctness Review

### 2a. Package Structure (Section 2)

**Issue:** Missing `core/suggestions.py` module

**Location:** Section 3.2 God Script Decomposition

**Severity:** Minor

**Problem:** The decomposition table for `ontos_end_session.py` lists "Impact suggestion (1193-1400) → `core/suggestions.py` (NEW) ~200 lines." However, `core/suggestions.py` doesn't appear in the Section 2.1 package structure or the Section 2.2 module specifications.

**Proposed Fix:** Add `core/suggestions.py` to the package structure:
```
├── core/
│   └── suggestions.py       # Impact suggestion logic (NEW)
```

---

**Issue:** `io/toml.py` responsibility overlap with config resolution

**Location:** Section 2.2 and Section 5

**Severity:** Minor

**Problem:** `io/toml.py` is listed as "`.ontos.toml` parsing" but Section 5.2 describes config resolution order (CLI flags → env vars → `.ontos.toml` → defaults). It's unclear whether `io/toml.py` handles just TOML parsing or the full resolution cascade.

**Proposed Fix:** Clarify in module description:
```
io/toml.py              # TOML file parsing only (uses tomllib/tomli)
core/config.py          # Config resolution cascade, merges all sources
```

---

### 2b. Module Specifications (Section 3)

**Issue:** `ValidationOrchestrator` missing method for curation-level validation

**Location:** Section 3.1, `core/validation.py`

**Severity:** Major

**Problem:** The `ValidationOrchestrator` interface includes:
- `validate_frontmatter()`
- `validate_graph()`
- `validate_status()`
- `validate_staleness()`

But curation-level validation (`curation.py:validate_at_level()`) is not represented. The Validation-Maintainability analysis identifies curation as a distinct validation category (14% of validation logic). The orchestrator should invoke curation validation.

**Proposed Fix:** Add method to interface:
```python
class ValidationOrchestrator:
    # ... existing methods ...
    def validate_curation(self) -> None  # Invoke tiered curation validation
```

---

**Issue:** `graph.py` public interface incomplete

**Location:** Section 3.1, `core/graph.py`

**Severity:** Minor

**Problem:** The interface defines `detect_orphans()` but requires `allowed_types: Set[str]` parameter. The Validation-Maintainability analysis notes that orphan detection has "hardcoded skip conditions" (lines 498-507) including skip for kernel, strategy, draft proposals, and archived documents. This business logic is not captured in the interface.

**Proposed Fix:** Document the parameter or extract configuration:
```python
def detect_orphans(
    graph: DependencyGraph,
    allowed_orphan_types: Set[str] = {'atom', 'molecule'},  # kernel/strategy always allowed as orphan
    skip_archived: bool = True,
    skip_draft_proposals: bool = True
) -> List[str]
```

---

**Issue:** Missing `get_orphans()` function referenced implicitly

**Location:** Cross-reference between Section 3 and Section 4

**Severity:** Minor

**Problem:** The data flow diagram in Section 4.2 shows "5. Validate all ← core/validation.py" calling `ValidationOrchestrator.validate_all()`. This implies orphan detection is invoked, but the exact function call path isn't specified. `detect_orphans()` exists in `graph.py` but there's no `get_orphans()` mentioned anywhere (I may have misread earlier).

**Proposed Fix:** Confirm the call path in the orchestrator:
```python
# In ValidationOrchestrator.validate_graph()
orphans = graph.detect_orphans(self.graph, self.config.allowed_orphan_types)
```

---

### 2c. Data Flows (Section 4)

**Issue:** `ontos log` data flow missing confirmation step

**Location:** Section 4.3

**Severity:** Major

**Problem:** The strategy decision for Q4 says "Use `git diff` for change detection, require confirmation." The data flow shows step 4 as "Suggest impacts ← core/suggestions.py" but no user confirmation step. This contradicts the "curation over ceremony" philosophy — auto-detection without confirmation is what we decided against.

**Proposed Fix:** Add confirmation step to data flow:
```
│  4. Suggest impacts ◀──────── core/suggestions.py   │
│  5. Present suggestions, await user confirmation    │ ← ADD THIS
│  6. Validate concepts ◀────── core/validation.py    │
```

---

**Issue:** Missing `ontos doctor` data flow

**Location:** Section 4

**Severity:** Minor

**Problem:** `ontos doctor` is a v3.0 deliverable (adopted in strategy), and `commands/doctor.py` is specified in Section 3, but there's no data flow diagram for it. Given `doctor` is a diagnostic command, the flow should show what checks happen and in what order.

**Proposed Fix:** Add Section 4.4:
```
### 4.4 `ontos doctor` — Health Check

User runs: ontos doctor
           │
           ▼
┌─────────────────────────────────────────────────────┐
│ commands/doctor.py                                   │
│                                                      │
│  1. Check .ontos.toml ◀────── io/toml.py            │
│  2. Check git hooks ◀──────── io/git.py             │
│  3. Check Python version                             │
│  4. Check docs directory ◀─── io/files.py           │
│  5. Parse context map ◀────── core/frontmatter.py   │
│  6. Run validation ◀───────── core/validation.py    │
│  7. Check CLI in PATH                                │
└─────────────────────────────────────────────────────┘
```

---

### 2d. ValidationOrchestrator Analysis

**Does the pattern address issues in Validation-Maintainability analysis?**

**Addressed:**
- ✅ Hard-exit pattern → Replaced with error collection (`MUST collect all errors before returning`)
- ✅ Sequential coupling → Orchestrator can run all validators and collect
- ✅ No unified error format → `ValidationError` dataclass standardizes format

**Not Addressed:**

**Issue:** Configuration fragmentation not resolved

**Location:** Validation-Maintainability §3.2.1, Architecture §5

**Severity:** Major

**Problem:** The Validation-Maintainability analysis identifies "Configuration Source Fragmentation" as a critical issue — `VALID_STATUS`, `VALID_EVENT_TYPES`, `TYPE_DEFINITIONS` exist in both `ontos_config.py` and `ontos_config_defaults.py` with no single source of truth.

The v3.0 architecture introduces `.ontos.toml` but doesn't address where these validation constants live. The `OntosConfig` dataclass in `core/types.py` only includes paths and scanning settings, not validation constants.

**Proposed Fix:** Consolidate validation constants into declarative config:
```toml
# .ontos.toml
[validation]
valid_status = ["draft", "active", "deprecated", "rejected", "complete"]
valid_event_types = ["feature", "fix", "refactor", "exploration", "chore"]

[types.kernel]
can_depend_on = []
valid_status = ["draft", "active", "deprecated"]

[types.strategy]
can_depend_on = ["kernel"]
valid_status = ["draft", "active", "deprecated", "rejected", "complete"]
# ...
```

Or explicitly document that these remain in Python code and why.

---

**Issue:** `ontos_lib.py` deprecation timeline unclear

**Location:** Validation-Maintainability §3.2.2, Architecture §12.1

**Severity:** Minor

**Problem:** The Migration Strategy lists "Delete: `ontos_lib.py` (deprecated shim)." But the Validation-Maintainability analysis notes "15+ files still import via `ontos_lib`." The architecture doesn't specify:
1. Which phase handles updating those 15+ files
2. Whether v3.0 ships with `ontos_lib.py` still present (just deprecated)
3. Whether it's removed entirely

**Proposed Fix:** Add explicit note to Migration Strategy:
```
Phase 2: God Script Decomposition (v3.0.0-beta)
├── ...
├── Update all 15 files importing ontos_lib.py to use ontos.core.*
├── Retain ontos_lib.py with deprecation warning (for external scripts)
└── Schedule removal for v3.1.0
```

---

## 3. Completeness Review

### 3a. Missing Modules

**Gap:** `core/suggestions.py` not in package structure

**Impact:** God Script decomposition references this module; implementation will create undocumented file

**Proposed Addition:** Add to Section 2.1:
```
│   ├── suggestions.py       # Impact suggestion from git changes (NEW)
```

---

**Gap:** `core/tokens.py` not in package structure

**Impact:** God Script decomposition table lists "Token estimation (71-104) → `core/tokens.py`" but this module doesn't appear in Section 2.1 or 2.2

**Proposed Addition:** Add to Section 2.1:
```
│   ├── tokens.py            # Token estimation for context map (NEW)
```

---

### 3b. Undefined Interfaces

**Gap:** `io/files.py` interface not specified

**Impact:** Referenced in data flows but no public interface defined

**Proposed Addition:**
```python
# io/files.py
def scan_for_docs(root: Path, skip_patterns: List[str]) -> List[Path]
def read_frontmatter(filepath: Path) -> Tuple[Dict, str]
def atomic_write(filepath: Path, content: str) -> None
def ensure_directory(path: Path) -> None
```

---

**Gap:** `io/toml.py` interface not specified

**Impact:** Config loading flow depends on this but interface undefined

**Proposed Addition:**
```python
# io/toml.py
def load_toml(filepath: Path) -> Dict[str, Any]
def write_toml(filepath: Path, data: Dict[str, Any]) -> None
def merge_configs(base: Dict, override: Dict) -> Dict
```

---

### 3c. Missing Data Flows

**Gap:** `ontos verify` data flow not documented

**Impact:** Command exists in CLI structure but flow unknown

**Gap:** `ontos migrate` data flow not documented

**Impact:** Schema migration is complex; flow needed

**Gap:** `ontos consolidate` data flow not documented

**Impact:** Decision history generation involves multiple modules

**Proposed Addition:** Add Section 4.5-4.7 with these flows, or note them as "lower priority — document post-implementation."

---

### 3d. Configuration Gaps

**Gap:** `.ontos.toml` schema missing several fields

**Impact:** Implementation will diverge from spec

**Missing fields based on current codebase:**
```toml
[ontos]
version = "3.0"
required_version = ">=3.0.0"  # Q5 decision — missing

[validation]
# Missing from current spec:
proposal_stale_days = 60
rejected_reason_min_length = 10

[workflow]
# Missing from current spec:
auto_archive_on_push = true
```

---

### 3e. Migration Gaps

**Gap:** Migration strategy doesn't specify test migration

**Impact:** 303 tests currently exist; they likely import from old paths

**Proposed Addition:**
```
Phase 2: God Script Decomposition (v3.0.0-beta)
├── ...
├── Migrate tests/test_*.py to new import paths
├── Update test fixtures for new module locations
└── Verify: 303 tests pass with new structure
```

---

**Gap:** Hook migration not specified

**Impact:** Existing repos have full hook scripts; need to replace with shims

**Proposed Addition:**
```
Phase 4: CLI & Hooks (v3.0.0)
├── ...
├── `ontos init --migrate` replaces existing hooks with shims
├── Backup existing hooks to .git/hooks/*.backup
└── Warn user if custom hook logic detected
```

---

## 4. Consistency Review

### 4a. Terminology

**Inconsistency:** "molecule" vs "product"

**Location A:** Validation-Maintainability Appendix B shows `TYPE_DEFINITIONS` with `'molecule'`

**Location B:** Strategy Decisions and Architecture use `'product'` (e.g., "kernel → strategy → product → atom")

**Resolution:** Determine canonical type name. If `product` is v3.0 rename, add migration note. If `molecule` is legacy, update architecture to clarify.

---

**Inconsistency:** Line count for `ontos_end_session.py`

**Location A:** Architecture Executive Summary says "1,625 lines"

**Location B:** Architecture Appendix C says "1,904 lines"

**Location C:** Strategy Decisions says "1,625-line God Script"

**Resolution:** Verify actual line count. Update all references to consistent value.

---

### 4b. Module Specs vs Data Flows

**Inconsistency:** Data flow references `core/suggestions.py` but module not in spec

**Location A:** Section 4.3 (ontos log flow) step 4

**Location B:** Section 2.1 package structure (missing)

**Resolution:** Add `core/suggestions.py` to package structure (see §3a)

---

**Inconsistency:** `commands/hook.py` vs CLI `hook` command

**Location A:** Section 2.1 lists `commands/hook.py`

**Location B:** Section 6.1 lists `hook` command as "Git hook dispatcher (internal)"

**Resolution:** Consistent, but clarify in hook.py spec that this is internal-only (not user-facing).

---

### 4c. Constraints vs Implementation

**Inconsistency:** Zero-dep constraint vs `tomli` allowance

**Location A:** Section 11.1 states "Core: Stdlib only (no external dependencies)"

**Location B:** Section 11.1 also states "Allowed for 3.9-3.10: `tomli` (TOML parsing)"

**Resolution:** Clarify that `tomli` is a conditional dependency (only installed on Python <3.11 where `tomllib` doesn't exist). This is consistent with zero-dep philosophy since 3.11+ uses stdlib.

---

### 4d. Line Counts

**Issue:** Estimated line counts may not add up

**Analysis:**

God Script decomposition for `ontos_end_session.py` (claimed 1,904 lines):
- Proposal graduation: ~250 → `core/proposals.py` (EXISTS)
- Branch/slug handling: ~100 → `io/git.py`
- Log file operations: ~200 → `commands/log.py`
- Git log/commit tracking: ~100 → `io/git.py`
- Changelog handling: ~220 → `commands/log.py`
- Impact suggestion: ~200 → `core/suggestions.py` (NEW)
- Main orchestration: ~280 → `commands/log.py`
- Deprecation notice: ~16 → DELETE

**Total accounted:** ~1,366 lines
**Claimed:** 1,904 lines
**Gap:** ~538 lines unaccounted

**Resolution:** Either some code is duplicated across targets (intentionally), or there are extraction targets missing. Review the actual script to confirm decomposition is complete.

---

## 5. Risk Assessment

### 5a. Implementation Risks

**Risk:** ValidationOrchestrator integration complexity

**Likelihood:** Medium

**Impact:** High

**Mitigation:** Build ValidationOrchestrator incrementally — start with wrapping existing validation calls, then refactor internals. Don't try to rewrite all 28 validation functions simultaneously.

---

**Risk:** `io/git.py` subprocess reliability

**Likelihood:** Medium

**Impact:** Medium

**Mitigation:** Add comprehensive error handling for git subprocess failures. Document expected behavior when not in a git repo or git is not installed.

---

### 5b. God Script Decomposition Risk

**Risk:** Hidden dependencies in `ontos_end_session.py`

**Likelihood:** High

**Impact:** Medium

**Mitigation:** The 1,904-line script likely has internal function calls and shared state that aren't visible in the decomposition table. Before decomposition:
1. Generate function call graph
2. Identify shared variables/state
3. Create integration tests that exercise full flow
4. Decompose with continuous test verification

---

**Risk:** Line count underestimate for `commands/log.py`

**Likelihood:** Medium

**Impact:** Low

**Mitigation:** The estimate of ~500 lines for `commands/log.py` may be low given it absorbs main orchestration (~280) + log operations (~200) + changelog (~220) = ~700 lines before any refactoring. Accept that initial extraction may be larger, then refactor in subsequent pass.

---

### 5c. Backward Compatibility Risk

**Risk:** Existing hooks break during migration

**Likelihood:** Low (single-user project)

**Impact:** Low

**Mitigation:** Since founder is only user, can do aggressive migration. But document the migration path anyway for future multi-user scenario.

---

**Risk:** v2.x config not detected during init

**Likelihood:** Low

**Impact:** Medium

**Mitigation:** Section 5.3 mentions `ontos init --migrate` detects `ontos_config.py`. Ensure this detection is robust and handles edge cases (partial config, corrupted config).

---

### 5d. Performance Risk

**Risk:** CLI startup time > 100ms target

**Likelihood:** Low

**Impact:** Low

**Mitigation:** The zero-dep core should enable fast startup. Main risk is import time if module structure is too deep. Use lazy imports for optional features (MCP layer).

---

**Risk:** `ontos map` for 100-500 docs exceeds 2s target

**Likelihood:** Medium

**Impact:** Low

**Mitigation:** The Validation-Maintainability analysis notes O(n) path lookup in cycle detection. If graph validation is O(n²), 500 docs could be slow. Profile early and optimize cycle detection to O(V+E) as specified.

---

### 5e. v4.0 Readiness Risk

**Risk:** MCP extension point insufficient

**Likelihood:** Low

**Impact:** Medium

**Mitigation:** The architecture correctly separates `mcp/` as optional layer. JSON output mode (Q1) provides the structured data MCP tools need. Main risk: if core functions need async variants for MCP daemon, that's not prepared. Consider whether `core/` functions need async equivalents.

---

**Risk:** Export templates extension point unclear

**Likelihood:** Medium

**Impact:** Low

**Mitigation:** Section 10 lists "Export Templates → ui/formatters/" but no `ui/formatters/` directory exists in the package structure. Either add stub directory or clarify this is created at v4.0 time.

---

## 6. Proposed Changes

### Change Proposal: Add Missing Modules to Package Structure

**Problem:** Several modules referenced in decomposition tables (`core/suggestions.py`, `core/tokens.py`) are not in the package structure.

**Proposed Change:**

Update Section 2.1 to include:
```
├── core/
│   ├── ...
│   ├── suggestions.py       # Impact suggestion from git diff (NEW ~200)
│   └── tokens.py            # Token estimation for context maps (NEW ~50)
```

**Rationale:**
- Decomposition tables reference these modules
- Implementation will create them; spec should document them

**Impact:**
- Sections affected: 2.1, 2.2
- Effort: Low (documentation only)

---

### Change Proposal: Specify Version Pinning (Q5)

**Problem:** Q5 decision (warn on version mismatch) is not implemented in architecture.

**Proposed Change:**

1. Add to `.ontos.toml` schema:
```toml
[ontos]
version = "3.0"
required_version = ">=3.0.0, <4.0.0"  # Optional, warn if mismatch
```

2. Add to `io/toml.py` interface:
```python
def check_version_compatibility(config: Dict) -> Optional[str]:
    """Returns warning message if installed version doesn't match required_version, None otherwise."""
```

3. Add version check to `cli.py` startup.

**Rationale:**
- Q5 was a v3.0 LOW priority item, but it was decided (warn-only)
- Either implement or explicitly defer to v3.0.x

**Impact:**
- Sections affected: 5.1, 6
- Effort: Low

---

### Change Proposal: Add User Confirmation Step to Log Flow

**Problem:** Q4 decision requires "user confirmation" after git-based change detection, but data flow doesn't show this.

**Proposed Change:**

Update Section 4.3 to include confirmation step:
```
│  4. Get changed files ◀────── io/git.py               │
│  5. Suggest impacts ◀──────── core/suggestions.py     │
│  6. Present suggestions to user                        │
│     └── If --auto flag: skip confirmation             │
│     └── Else: prompt for confirmation/modification    │
│  7. Validate concepts ◀────── core/validation.py      │
```

**Rationale:**
- Strategy decision explicitly requires confirmation
- "Curation over ceremony" means human reviews auto-suggestions
- `--auto` flag preserves option for CI/scripting use

**Impact:**
- Sections affected: 4.3, commands/log.py spec
- Effort: Medium (adds interactive logic)

---

### Change Proposal: Consolidate Validation Constants Configuration

**Problem:** Configuration fragmentation (identified in Validation-Maintainability analysis) is not addressed.

**Proposed Change:**

Option A (Recommended): Keep constants in Python, document the decision

Add to Section 5.1 a note:
```
# Note: Validation constants (VALID_STATUS, TYPE_DEFINITIONS, etc.) remain in
# Python code (core/types.py) rather than .ontos.toml. Rationale:
# 1. These are schema-level constants that shouldn't vary per-project
# 2. They require code changes anyway (validation logic)
# 3. Keeps .ontos.toml focused on project-specific configuration
```

Option B: Move to TOML (more complex)

Add validation constants to `.ontos.toml` schema and create config-driven validation.

**Rationale:**
- The current split between `ontos_config.py` and `ontos_config_defaults.py` is confusing
- v3.0 should at minimum consolidate into one location
- Whether that's Python or TOML is a design choice that should be documented

**Impact:**
- Sections affected: 5.1, core/types.py
- Effort: Low (Option A) or High (Option B)

---

## 7. Summary Assessment

**Overall Quality:** Strong

The architecture is comprehensive, well-structured, and clearly implements the strategy decisions. The layered architecture correctly separates concerns, and the ValidationOrchestrator pattern addresses the critical hard-exit issue from the current codebase.

### Strengths

- **Clear layering:** CLI → Commands → Core → I/O separation is well-defined with explicit dependency rules
- **God Script decomposition is detailed:** Line-by-line mapping from current scripts to target modules
- **Extension points identified:** v4.0 MCP, daemon, and export features have clear integration points
- **Strategy alignment:** 10 of 13 Q decisions are correctly implemented or deferred
- **Performance targets specified:** Concrete numbers (500ms, 2s, 100ms) enable testing
- **Migration phases are incremental:** Five phases allow course-correction

### Critical Issues (must fix before implementation)

1. **Q5 version pinning not implemented** — Either add to spec or explicitly document as "deferred to v3.0.x"
2. **User confirmation step missing from log flow** — Q4 decision requires this; add to data flow
3. **Missing modules in package structure** — `core/suggestions.py`, `core/tokens.py` referenced but not listed

### Major Concerns (should fix, but not blocking)

1. **Configuration fragmentation not resolved** — Validation constants still split across files; document the decision
2. **Curation validation missing from orchestrator** — Add `validate_curation()` method
3. **`ontos_lib.py` deprecation timeline unclear** — Specify which phase updates the 15+ dependent files
4. **Line count discrepancy** — 1,625 vs 1,904 lines for God Script; verify and correct

### Minor Suggestions (nice to have)

1. Add data flows for `ontos doctor`, `ontos verify`, `ontos migrate`
2. Specify `io/files.py` and `io/toml.py` interfaces
3. Resolve "molecule" vs "product" terminology inconsistency
4. Add test migration to Phase 2
5. Add hook migration (backup existing) to Phase 4

### Recommendation: **Approve with Changes**

The architecture is solid and ready for implementation with the following changes:

**Required before implementation:**
- Add Q5 version pinning (or explicit deferral note)
- Add user confirmation step to `ontos log` flow
- Add missing modules to package structure

**Required early in implementation:**
- Verify God Script line counts
- Confirm decomposition accounts for all code
- Build ValidationOrchestrator incrementally with tests

The architecture successfully translates the "Distribution & Polish" theme into concrete specifications. The functional core / imperative shell pattern is preserved and extended. The v4.0 extension points are appropriately stubbed without over-engineering.

---

*End of Peer Review*

*Reviewed by Claude Opus 4.5 (LLM C) — 2026-01-11*