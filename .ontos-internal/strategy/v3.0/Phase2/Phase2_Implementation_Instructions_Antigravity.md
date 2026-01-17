---
id: phase2_implementation_instructions_antigravity
type: strategy
status: active
depends_on: [v3_0_technical_architecture, v3_0_implementation_roadmap, chief_architect_round2_critical_analysis]
---

# Ontos v3.0 Phase 2: Implementation Instructions for Antigravity

**Date:** 2026-01-12
**Spec Version:** 1.2 (Approved)
**Target:** Decompose God Scripts into modular components
**Constraint:** Golden Master tests must pass (exact behavioral parity)

---

## Executive Summary

You are implementing Phase 2 of the Ontos v3.0 restructuring — the **highest-risk phase**. Your job is to:

1. Extract 11 new modules from the two "God Scripts":
   - `ontos_end_session.py` (1,905 lines)
   - `ontos_generate_context_map.py` (1,296 lines)
2. Fix pre-existing architecture violations (PyYAML in core, subprocess in core)
3. Migrate 7 minor commands to `commands/` package
4. Reduce God Scripts to <200 lines each (argparse + deprecation only)
5. Maintain exact behavioral parity (Golden Master tests MUST pass)

**Critical Rules:**
- Run Golden Master tests after EVERY extraction
- `core/` modules MUST NOT import `subprocess`, `io/`, or call `print()`
- Type normalization happens ONCE at io/core boundary
- If Golden Master fails, STOP and diagnose before continuing

---

## Reference Documents (MUST READ)

Before starting, read these documents for full context:

| Document | Location | Purpose |
|----------|----------|---------|
| **Phase 2 Spec v1.2** | `.ontos-internal/strategy/v3.0/Phase2/Phase2-Implementation-Spec.md` | Primary spec with all module details |
| **Technical Architecture v1.4** | `.ontos-internal/strategy/v3.0/V3.0-Technical-Architecture.md` | Layer constraints, dependency rules |
| **Implementation Roadmap v1.4** | `.ontos-internal/strategy/v3.0/V3.0-Implementation-Roadmap.md` | Phase 2 tasks (Section 4) |
| **Chief Architect Analysis** | `.ontos-internal/strategy/v3.0/Phase2/Chief_Architect_Round2_Critical_Analysis.md` | Subprocess violation details |

---

## Pre-Implementation Checklist

Before starting, verify:

```bash
# 1. You're in the correct directory
pwd  # Should show: /Users/jonathanoh/Dev/Project-Ontos

# 2. You're on the correct branch
git branch --show-current  # Should show: Phase2_V3.0_beta

# 3. Git is clean
git status  # Should show no uncommitted changes

# 4. Package is installed
pip list | grep ontos  # Should show ontos 3.0.0a1

# 5. Golden Master baseline passes
python tests/golden/compare_golden_master.py --fixture all
# Expected: 16/16 PASS

# 6. All unit tests pass
pytest tests/ -v --tb=short
# Expected: 303+ tests pass
```

---

## Architecture Constraints (ENFORCED)

These constraints are non-negotiable:

| Layer | May Import From | MUST NOT Import |
|-------|-----------------|-----------------|
| `core/` | stdlib, `core/types` | `io/`, `commands/`, `subprocess`, PyYAML |
| `io/` | stdlib, `core/types`, third-party | `commands/` |
| `commands/` | All layers | — |

**CI Enforcement Added in v1.2:**
```bash
# This check will run in CI — ensure it passes:
if grep -r "import subprocess" ontos/core/; then
    echo "ERROR: subprocess import found in core/"
    exit 1
fi
```

---

## Day 1: Foundation (No Dependencies)

### Task 1.1: Create `ontos/core/types.py`

**Purpose:** Central type definitions with ZERO new internal imports (except re-exports).

**File:** `ontos/core/types.py`

**Reference:** See Phase2-Implementation-Spec.md Section 4.1 (lines 310-443) for complete code.

Key contents:
- Re-export `CurationLevel` from `core/curation.py`
- Define `DocumentType`, `DocumentStatus`, `ValidationErrorType` enums
- Define `DocumentData`, `ValidationError`, `ValidationResult` dataclasses
- Define `TEMPLATES`, `SECTION_TEMPLATES` constants

**Verify:**
```bash
python -c "from ontos.core.types import DocumentType, CurationLevel; print('OK')"
```

---

### Task 1.2: Create `ontos/core/tokens.py`

**Purpose:** Token estimation for context maps (stdlib only).

**Source:** `ontos/_scripts/ontos_generate_context_map.py` lines 71-102

**Reference:** See Phase2-Implementation-Spec.md Section 4.2 (lines 447-502) for complete code.

Key functions:
- `estimate_tokens(content: str) -> int`
- `format_token_count(tokens: int) -> str`

**Verify:**
```bash
python -c "from ontos.core.tokens import estimate_tokens, format_token_count; print(format_token_count(estimate_tokens('hello world')))"
```

---

### Task 1.3: Create `ontos/io/yaml.py`

**Purpose:** Isolate PyYAML from core modules.

**Reference:** See Phase2-Implementation-Spec.md Section 4.9 (lines 1513-1563) for complete code.

Key functions:
- `parse_yaml(content: str) -> dict`
- `dump_yaml(data: dict, default_flow_style: bool = False) -> str`

**Verify:**
```bash
python -c "from ontos.io.yaml import parse_yaml; print(parse_yaml('key: value'))"
```

---

### Task 1.4: Update `ontos/io/__init__.py`

Add yaml exports to the io package.

**Day 1 Checkpoint:**
```bash
python -c "import ontos; import ontos.core.types; import ontos.core.tokens; import ontos.io.yaml"
```

---

## Day 2: I/O Layer

### Task 2.1: Create `ontos/io/git.py`

**Purpose:** All git subprocess operations (isolates subprocess from core).

**Reference:** See Phase2-Implementation-Spec.md Section 4.6 (lines 1059-1223) for complete code.

Key functions:
- `get_current_branch() -> Optional[str]`
- `get_commits_since_push(fallback_count: int = 5) -> List[str]`
- `get_changed_files_since_push() -> List[str]`
- `get_file_mtime(filepath: Path) -> Optional[datetime]`
- `is_git_repo() -> bool`
- `get_git_root() -> Optional[Path]`

**Verify:**
```bash
python -c "from ontos.io.git import get_current_branch; print(get_current_branch())"
```

---

### Task 2.2: Create `ontos/io/files.py`

**Purpose:** File system operations with type normalization at io/core boundary.

**Reference:** See Phase2-Implementation-Spec.md Section 4.7 (lines 1226-1403) for complete code.

Key functions:
- `find_project_root(start_path: Path = None) -> Path`
- `scan_documents(dirs: List[Path], skip_patterns: List[str] = None) -> List[Path]`
- `load_document(path: Path, frontmatter_parser: Callable) -> DocumentData`
- `write_text_file(path: Path, content: str, encoding: str = "utf-8") -> None`

**CRITICAL:** `load_document()` is the type normalization boundary. String→Enum conversion happens HERE.

---

### Task 2.3: Create `ontos/io/toml.py`

**Purpose:** TOML config loading (prepares for Phase 3).

**Reference:** See Phase2-Implementation-Spec.md Section 4.8 (lines 1406-1510) for complete code.

**Note:** Uses `tomllib` (Python 3.11+) or `tomli` fallback (3.9-3.10).

---

## Day 3: Core Graph Modules

### Task 3.1: Create `ontos/core/graph.py`

**Purpose:** Dependency graph building, cycle detection (O(V+E) DFS).

**Source:** `ontos/_scripts/ontos_generate_context_map.py` lines 428-560

**Reference:** See Phase2-Implementation-Spec.md Section 4.3 (lines 505-695) for complete code.

Key components:
- `@dataclass GraphNode`
- `@dataclass DependencyGraph`
- `build_graph(docs) -> Tuple[DependencyGraph, List[ValidationError]]`
- `detect_cycles(graph) -> List[List[str]]`
- `detect_orphans(graph, allowed_orphan_types) -> List[str]`
- `calculate_depths(graph) -> Dict[str, int]`

**CRITICAL:** Cycle detection MUST use O(V+E) DFS. Do NOT use `path.index()` pattern.

---

### Task 3.2: Create `ontos/core/suggestions.py`

**Purpose:** Impact and concept suggestion algorithms.

**Source:** `ontos/_scripts/ontos_end_session.py` lines 1193-1400

**Reference:** See Phase2-Implementation-Spec.md Section 4.4 (lines 698-860) for complete code.

Key functions:
- `load_document_index(context_map_content: str) -> Dict[str, str]`
- `load_common_concepts(context_map_content: str) -> Set[str]`
- `suggest_impacts(changed_files, document_index, commit_messages) -> List[str]`
- `validate_concepts(concepts, known_concepts) -> Tuple[List[str], List[str]]`

---

## Day 4: Validation and Architecture Fixes

### Task 4.1: Create `ontos/core/validation.py`

**Purpose:** Unified validation orchestration with error collection (no hard exits).

**Reference:** See Phase2-Implementation-Spec.md Section 4.5 (lines 863-1056) for complete code.

Key class:
```python
class ValidationOrchestrator:
    def __init__(self, docs, config)
    def validate_all(self) -> ValidationResult
    def validate_graph(self)
    def validate_log_schema(self)
    def validate_impacts(self)
    def validate_describes(self)
```

**CRITICAL:** MUST collect all errors before returning. No `sys.exit()` or `print()` calls.

---

### Task 4.2: Update `ontos/core/__init__.py`

Add exports for all new core modules (types, tokens, graph, suggestions, validation).

---

### Task 4.3: Fix `ontos/core/frontmatter.py` (Remove PyYAML)

**Issue:** Direct PyYAML import violates core's stdlib-only constraint.

**Fix:** Accept YAML parser as parameter, inject from `io/yaml.py`.

**Verify:**
```bash
grep "import yaml" ontos/core/frontmatter.py  # Should return nothing
```

---

### Task 4.4: Refactor `ontos/core/staleness.py` (Remove subprocess)

**Issue:** `subprocess.run()` calls for git operations.

**Fix:** Add parameters for git data, inject from `io/git.py`.

**Verify:**
```bash
grep "import subprocess" ontos/core/staleness.py  # Should return nothing
```

---

### Task 4.5: Refactor `ontos/core/config.py` (Remove subprocess)

**Issue:** `subprocess.run()` calls for git config.

**Fix:** Same pattern as staleness.py.

**Verify:**
```bash
grep "import subprocess" ontos/core/config.py  # Should return nothing
```

**Day 4 Checkpoint (CRITICAL):**
```bash
# Architecture enforcement check
grep -r "import subprocess" ontos/core/ && echo "FAIL" || echo "PASS"

# Run Golden Master
python tests/golden/compare_golden_master.py --fixture all
```

---

## Day 5: Command Modules

### Task 5.1: Create `ontos/commands/map.py`

**Purpose:** Context map generation orchestration (~200 lines).

**Reference:** See Phase2-Implementation-Spec.md Section 4.10 (lines 1566-1717) for complete code.

Orchestrates: config loading → document scanning → frontmatter parsing → graph building → validation → output generation.

---

### Task 5.2: Create `ontos/commands/log.py`

**Purpose:** Session log creation orchestration (~250 lines).

**Reference:** See Phase2-Implementation-Spec.md Section 4.11 (lines 1720-1855) for complete code.

Orchestrates: git info → suggestions → log generation → file writing.

---

## Day 6: God Script Refactoring

### Tasks 6.1-6.3: Refactor `ontos_generate_context_map.py`

**Goal:** Reduce to <200 lines (argparse + deprecation + calls to `commands/map.py`)

1. Update imports to use new modules
2. Replace inline functions with `commands/map.py` calls
3. Keep only: argparse wrapper, deprecation notice

**Verify:**
```bash
wc -l ontos/_scripts/ontos_generate_context_map.py  # Must be <200
python tests/golden/compare_golden_master.py --fixture all  # MUST PASS
```

---

### Tasks 6.4-6.6: Refactor `ontos_end_session.py`

**Goal:** Reduce to <200 lines

Same pattern: update imports, replace with `commands/log.py` calls, verify Golden Master.

---

## Day 7-8: Minor Command Migration

| Source Script | Target |
|--------------|--------|
| `ontos_verify.py` (315 lines) | `commands/verify.py` |
| `ontos_query.py` (326 lines) | `commands/query.py` |
| `ontos_migrate_schema.py` (337 lines) | `commands/migrate.py` |
| `ontos_consolidate.py` (465 lines) | `commands/consolidate.py` |
| `ontos_promote.py` (453 lines) | `commands/promote.py` |
| `ontos_scaffold.py` (274 lines) | `commands/scaffold.py` |
| `ontos_stub.py` (279 lines) | `commands/stub.py` |

For each: copy logic → extract I/O → update original → verify Golden Master.

---

## Day 9: Final Integration

### Task 9.1: Update all `__init__.py` exports

### Task 9.2: Run Full Golden Master Suite
```bash
python tests/golden/compare_golden_master.py --all
```

### Task 9.3: Run All Unit Tests
```bash
pytest tests/ -v --cov=ontos --cov-report=term-missing
```

### Task 9.4: Run Circular Import Test
```bash
pytest tests/test_circular_imports.py -v
```

---

## Final Verification Checklist

| # | Check | Command | Expected |
|---|-------|---------|----------|
| 1 | All 11 modules exist | `ls ontos/core/*.py ontos/io/*.py` | 11+ new files |
| 2 | No subprocess in core | `grep -r "import subprocess" ontos/core/` | No matches |
| 3 | No PyYAML in core | `grep -r "import yaml" ontos/core/` | No matches |
| 4 | God Scripts <200 lines | `wc -l ontos/_scripts/ontos_end_session.py ontos/_scripts/ontos_generate_context_map.py` | Both <200 |
| 5 | Golden Master passes | `python tests/golden/compare_golden_master.py --all` | 16/16 PASS |
| 6 | Unit tests pass | `pytest tests/ -v` | 303+ pass |
| 7 | No circular imports | `python -c "import ontos; import ontos.core; import ontos.io; import ontos.commands"` | No error |

---

## Success Criteria

Phase 2 is complete when:

- [ ] 11 new modules created with specified interfaces
- [ ] God Scripts < 200 lines each
- [ ] 7 minor commands migrated
- [ ] Pre-existing PyYAML violation fixed
- [ ] Pre-existing subprocess violations fixed (staleness.py, config.py)
- [ ] 303+ existing tests pass
- [ ] 16/16 Golden Master tests pass
- [ ] No circular imports
- [ ] Architecture constraints enforced
- [ ] Tag `v3.0.0-beta` created

---

## Troubleshooting

### Golden Master Fails After Extraction
1. Check exact diff with `--diff` flag
2. Compare original vs extracted function line-by-line
3. Revert logic changes, keep only structural moves

### Circular Import Error
1. Ensure `core/types.py` has no new internal imports
2. Use `from __future__ import annotations`
3. Use lazy imports inside functions if needed

### Subprocess in Core Detected
1. Find file: `grep -r "import subprocess" ontos/core/`
2. Extract call to `io/git.py`
3. Pass result as parameter to core function

---

*End of Phase 2 Implementation Instructions*

**Prepared by:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-12

**Reference Documents:**
- Spec: `.ontos-internal/strategy/v3.0/Phase2/Phase2-Implementation-Spec.md` (v1.2)
- Architecture: `.ontos-internal/strategy/v3.0/V3.0-Technical-Architecture.md` (v1.4)
- Roadmap: `.ontos-internal/strategy/v3.0/V3.0-Implementation-Roadmap.md` (v1.4)
- Analysis: `.ontos-internal/strategy/v3.0/Phase2/Chief_Architect_Round2_Critical_Analysis.md`
