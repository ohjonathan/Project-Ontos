---
id: v3_1_consolidated_remediation_plan
type: strategy
status: approved
depends_on: [v3_2_backlog, gemini_analysis_response, chatgpt_analysis_response, claude_analysis_response]
concepts: [remediation, roadmap, v3.2, architecture, code-quality, layer-boundaries, frontmatter-pipeline, document-index]
---

# Consolidated Remediation Plan v2: v3.1 Review Board

## Overview

Revised plan incorporating feedback from all 7 review rounds:
- Gemini DeepThink (product/positioning)
- ChatGPT R1 (code quality), R2 (acceptance criteria), R3 (plan review)
- Claude R1 (UX/onboarding), R2 (refinements), R3 (plan review)

**Key revision:** Fixed sequencing errors, added API specifications,
cut scope to match single-user reality. Every P2 item now has
acceptance criteria with both structural AND correctness checks.

---

## Step 0: Resolve Layer Contradictions (Before Coding)

**Source:** ChatGPT R3 gap #1, #2

Before implementing anything, decide the module layout:

### Config Split
- `core/config.py` -> **config schema/types** (dataclasses, defaults, validation)
- `io/config.py` -> **config loading** (read `.ontos.toml`, decode into schema)

### YAML Codec Placement
**Decision: Option A** — Move `io/yaml.py` to `core/_yaml.py` (underscore = internal helper).

`io/yaml.py` is a codec (parsing), not I/O (filesystem). Moving it to
`core/_yaml.py` makes the boundary rule clean: commands import
`core/frontmatter.py` only. No exceptions needed in architecture tests.
`io/` is reserved strictly for filesystem concerns (file reading, config loading).

### Layer Diagram (Target State)
```
commands/ → core/ → io/     ✓ (layered)
commands/ → io/             ✗ (skip layer)
io/ → commands/             ✗ (reverse)
io/ → core/                 ✗ (reverse)
core/ → core/               ✓ (same layer)
```

Transitive imports allowed: if `core/frontmatter.py` imports `core/_yaml.py`,
and `commands/map.py` imports `core/frontmatter.py`, that's compliant.
`core/_yaml.py` is internal — commands must not import it directly.

---

## Priority 1: Immediate Fixes (v3.1.x patch)

### P1-1: PyPI License Classifier

**File:** `pyproject.toml`
**Change:** Add `"License :: OSI Approved :: Apache Software License"` to classifiers.
**Done when:** PyPI page shows "Apache-2.0."

---

### P1-2: Skip Generated Files (Config-Aware)

**Files:** `ontos/commands/map.py`, `ontos/commands/doctor.py`
**Problem:** Generated files appear in graph.
**Fix:** Dynamically exclude based on config:
```python
generated_paths = [
    config.paths.context_map,  # Resolved to project-relative POSIX
    "AGENTS.md",
    ".cursorrules",
]
```
**Path normalization:** Convert all candidates to project-root-relative
POSIX paths with basename fallback. Treat generated exclusions separately
from glob-based `skip_patterns`.
**Done when:** `ontos map` AND `ontos doctor` never include generated files,
regardless of `context_map` path config. Test with both default and custom
context_map paths.

---

## Priority 2: v3.2 Core (Architecture & Consistency)

### Revised Execution Order

```
P2-0  Error handling convention (defines exit codes first)
P2-7  Dead code removal (quick win, reduces noise)
P2-1  Unify project root (foundation for everything)
P2-2  .ontos.toml authoritative (foundation)
P2-8  Centralize scanning + DocumentIndex (reduces io/ imports)
P2-3  Frontmatter pipeline (major refactor, uses P2-8)
P2-4  Architecture guardrails (NOW code is compliant, prevents regression)
P2-5  Log YAML safety (uses P2-3 pipeline)
P2-6  Type coercion audit (graph/index stable)
P2-9  Orphan policy (uses P2-8 index)
```

**Rationale (from Claude R3):** Dead code first (less noise). Foundation
items (root, config) before restructuring. P2-8 before P2-3 (scanning
abstraction makes pipeline refactor cleaner). P2-4 AFTER restructuring
(tests will actually pass).

---

### P2-0: Error Handling Convention (NEW)

**Source:** ChatGPT R3, Claude R3
**Fix:** Define before any refactoring:
```
Exit codes:
  0 = success (no errors)
  1 = runtime error (file not found, parse failure, command error)
  2 = validation error (strict/lint mode)
  130 = interrupted (Ctrl+C)

All errors to stderr.
--format json: {"status": "error"|"warning"|"ok", "code": "E_...", "message": "..."}
JSON output schema versioned: {"output_schema": 1, ...}
```
**Done when:** Exit codes documented in code. `ontos doctor` and future
`ontos lint` return these codes consistently. JSON output includes
`output_schema` version.

---

### P2-7: Dead Code Removal

**Files:** `ontos/cli.py`
**Fix:**
- Delete `_cmd_wrapper()` function and `script_map` dict
- Delete `_get_subprocess_env()` (PYTHONPATH injection)
- `_scripts/` directory: add deprecation docstring, do NOT install in wheels
**Done when:** `grep -R "_cmd_wrapper\|_get_subprocess_env" ontos/` is empty.
`_scripts/` excluded from wheel via pyproject.toml package-data.
**Packaging decision:** `_scripts/` NOT installed in wheels (add exclude).

---

### P2-1: Unify Project Root Resolution

**Files:** All commands using `Path.cwd()`
**Fix:** Single helper with defined precedence:
```
--root flag > ONTOS_ROOT env > nearest .ontos.toml (walk up) > git root (walk up) > error
```
**Done when:**
- Every command uses unified resolver
- `grep -r "Path.cwd()" ontos/commands/` returns nothing
- Tests verify: run from subdirectory, run outside repo (clean error),
  `--root` override works

---

### P2-2: `.ontos.toml` Authoritative Config

**Files:** `ontos/commands/log.py:112`, any `ontos_config` imports
**Fix:** Remove all `from ontos_config` imports. Warn on every invocation
(not one-time -- simpler, no state tracking needed for sole user).
**Done when:** `grep -r "ontos_config" ontos/commands/` returns nothing.
Warning fires when `ontos_config.py` exists in project root.
**Note:** P2-2 is about config SOURCE (toml vs python file). Orthogonal
to P2-3 (frontmatter parsing). No conflict.

---

### P2-8: Centralize Scanning + DocumentIndex

**Files:** New `ontos/core/index.py`, all commands that call `scan_documents`
**Spec:**
```python
class DocumentIndex:
    def __init__(self, project_root: Path, config: OntosConfig):
        self._docs: Dict[str, DocumentData] = {}
        self._errors: List[ParseError] = []
        self._skipped: List[Tuple[Path, str]] = []  # (path, reason)

    def load(self) -> None:
        """Scan, parse, normalize all documents once.
        Applies skip_patterns + generated_paths exclusions.
        Deterministic ordering (path sort)."""

    def get(self, doc_id: str) -> DocumentData | None: ...
    def all(self) -> Iterable[DocumentData]: ...
    def filter(self, predicate: Callable) -> Iterable[DocumentData]: ...

    @property
    def errors(self) -> List[ParseError]: ...
    @property
    def skipped(self) -> List[Tuple[Path, str]]: ...
```
**Contract:**
- Inputs: `(project_root, config)`
- All skip patterns (including generated file exclusions) applied HERE
- Documents in deterministic order (path sort)
- Parse errors collected, not raised -- bad docs become `DocError` entries
- One scan per CLI invocation (commands receive pre-built index)

**Done when:**
- `grep -r "scan_documents" ontos/commands/` shows zero direct calls
- Running `ontos map` then `ontos doctor` only scans once (verified via
  test with monkeypatched scanner counting invocations)

---

### P2-3: Frontmatter Pipeline

**Files:** `ontos/core/frontmatter.py` (canonical), `ontos/core/_yaml.py` (moved from `io/yaml.py`),
`ontos/core/validation.py`, `ontos/core/staleness.py`

**API Specification:**
```python
@dataclass
class ParseError:
    file: Path
    message: str
    line: int | None = None

@dataclass
class Issue:
    field: str
    message: str
    severity: str  # "warning" | "error"

@dataclass
class Violation:
    rule: str
    message: str
    severity: str

def parse_frontmatter(raw_text: str) -> tuple[dict | None, str, list[ParseError]]:
    """Lossless parse. Syntax only. Preserves unknown fields."""

def normalize_frontmatter(raw: dict, mode: str = "default") -> tuple[dict, list[Issue]]:
    """Canonicalize types:
    - describes: always list
    - concepts: always list
    - type: resolve to DocumentType or UNKNOWN + issue
    - Preserve unknown fields in 'extras' key
    Error accumulation: collect all issues, don't fail-fast."""

def validate_frontmatter(norm: dict, policy: str = "default") -> list[Violation]:
    """Pure business rules. No I/O, no mutation.
    Policy controls strictness (warn vs error for edge cases)."""
```

**Pipeline entrypoint:**
```python
def load_document(path: Path, mode: str = "default", policy: str = "default") -> DocumentData:
    """Orchestrates: read -> parse -> normalize -> validate.
    Called by DocumentIndex.load(), not by commands directly."""
```

**Invariants:**
- Commands MUST NOT call `parse_frontmatter` directly. They use
  DocumentIndex or the pipeline entrypoint.
- A doc that fails YAML parse still appears as `DocError` with stable error code.
- Unknown frontmatter keys survive parse->normalize->write round-trip
  (preserved in extras, not dropped).
- Default: parse + normalize ALWAYS. Validation: policy-driven.

**Done when:**
- No command imports `ontos.io.yaml` directly
- One `validate_describes` exists (in validate stage)
- `test_frontmatter_pipeline.py` covers: empty frontmatter, missing
  required fields, string vs list `describes`, malformed YAML, special
  chars, unknown fields round-trip
- P2-3 branch coverage > 90%

**Backwards compatibility check:** Before merging, run `ontos map` and
`ontos doctor` on THIS repo. All 469 existing documents must parse
without regression.

---

### P2-4: Architecture Guardrails

**File:** `tests/test_architecture.py` (new)
**Implementation:** AST-based import boundary test.

**Rules enforced:**
```python
RULES = {
    "commands/ -> io/": FORBIDDEN,      # Must go through core
    "io/ -> commands/": FORBIDDEN,       # Reverse dependency
    "io/ -> core/": FORBIDDEN,           # Reverse dependency
    "core/ -> commands/": FORBIDDEN,     # Reverse dependency
    # Allowed:
    "commands/ -> core/": ALLOWED,
    "core/ -> io/": ALLOWED,             # Core reads files via io/
    "core/ -> core/": ALLOWED,           # Same layer (incl. core/_yaml.py)
}

# Also forbid backdoors:
FORBIDDEN_PATTERNS = [
    "importlib.import_module",
    "__import__",
    "sys.path.insert",
    "sys.path.append",
]
```

**Done when:** `pytest tests/test_architecture.py` passes. Adding
`from ontos.io.files import X` to any command causes test failure.
All forbidden patterns absent from package code. `ontos/io/yaml.py`
no longer exists (moved to `core/_yaml.py`).

**Note:** This comes AFTER P2-8 and P2-3 so the code is already
compliant when tests are added. No xfail needed.

---

### P2-5: Fix Log Frontmatter Writing (YAML Safety)

**File:** `ontos/commands/log.py`
**Fix:** Reuse `core/schema.serialize_frontmatter()` (or the new pipeline's
write path).
**Test cases (parametrized):**
- Spaces: `"user authentication"`
- Colons: `"auth: oauth2"`
- Brackets: `"list [a, b]"`
- Commas: `"one, two"`
- Unicode: `"오지승"`, smart quotes
- YAML-like scalars: `"yes"`, `"no"`, `"2026-01-22"`, `"1e3"`
- Multiline strings
- Leading/trailing whitespace

**Serialization determinism:** Output order stable (sorted keys or
explicit field order).
**Done when:** All parametrized tests pass. Round-trip: write -> read
produces identical data.

---

### P2-6: Type Coercion Audit + Graduated Validation

**Files:** `ontos/core/types.py`, all `DocumentData` instantiation sites
**Fix:**
1. Add `UNKNOWN = "unknown"` to `DocumentType` enum (as sentinel)
2. Normalization maps unrecognized strings to `UNKNOWN` + issue
3. Add to `DocumentData.__post_init__`:
   ```python
   if not isinstance(self.type, DocumentType):
       raise TypeError(f"type must be DocumentType enum, got {type(self.type).__name__}")
   ```
4. Graduated validation:
   - Doctor: UNKNOWN type = warning
   - `map --strict` / `lint`: UNKNOWN type = error
5. Remove all `hasattr(doc.type, 'value')` patterns

**Done when:**
- `grep -r "hasattr.*type.*value" ontos/` returns nothing
- No runtime `AttributeError` possible from `doc.type`
- Bad types produce clear diagnostic in doctor output
- `DocumentData(type="atom")` raises TypeError (must use enum)

---

### P2-9: Orphan Policy (Structural + Severity)

**Files:** `ontos/core/graph.py`, `ontos/commands/doctor.py`, `ontos/commands/map.py`

**Edge definition (one place, in core/graph.py):**
- `depends_on` = structural edge (primary)
- `describes` = reference edge (secondary)
- Markdown links = NOT edges (too noisy)

**Orphan = "no incoming edges of any type"**

**Severity by type:**
- kernel/strategy: INFO (roots by design)
- product/atom: WARN (default) or ERROR (`--strict`)
- Configurable in `.ontos.toml`: `[validation] orphan_severity = "warn"`

**Distinct from broken references:**
- Broken reference = edge points to missing node (always ERROR)
- Orphan = node exists with no inbound edges (severity varies)

**Done when:**
- `map`, `doctor`, `query --health` all use same orphan definition
- Test fixtures: kernel mission = INFO orphan, unreferenced atom = WARN,
  strict mode flips WARN to ERROR

---

## Priority 3: v3.2 Features (Keep)

### P3-3: `ontos lint` as CI Alias

**Fix:** `ontos lint` = `ontos doctor --ci --format json`
Uses exit codes from P2-0. Same engine, CI defaults.
**Done when:** `ontos lint` exists, returns 0/1/2, outputs versioned JSON.

---

### P3-5: sdist/Packaging Smoke Tests

**Fix:** CI job: build wheel + sdist -> install fresh venv -> smoke suite
(`ontos --version`, `ontos map --help`).
**Done when:** CI has `test-installed` job.

---

### P3-10: Trust Boundary Documentation (NEW)

**Source:** ChatGPT R3
**Fix:** README "Security / Trust Boundary" section:
- "Ontos never executes repo-local Python by default"
- Document that git hooks run in repo context (inherent git trust model)
**Done when:** Section exists in README.

---

### P3-11: Deterministic Map Output (NEW)

**Source:** ChatGPT R3
**Fix:** Map output ordered by path sort. Stable node IDs.
Prevents golden-test flakiness.
**Done when:** Running `ontos map` twice produces identical output.

---

## Deferred to Post-Users (When Adoption Happens)

| Item | Source | Rationale |
|------|--------|-----------|
| P1-3 README Messaging | Gemini | No users reading it yet |
| P3-1 LLM-Assisted Scaffold | Gemini | Scope creep, you don't need AI for frontmatter |
| P3-2 GitHub Action | Gemini, ChatGPT | You're the only user; run doctor locally |
| P3-4 Init Template | Claude | You know the system |
| P3-6 Integration Guides | Claude | No users to guide |
| P3-7 Staleness Docs | Claude | You know how it works |
| P3-8 Version FAQ | Claude | You understand the versioning |
| IDE Extension | Gemini | MCP is the right bet for v4.0 |
| `ontos migrate-config` | ChatGPT R2 | Deprecation warning sufficient |

---

## Rejected

| Item | Decision | Rationale |
|------|----------|-----------|
| `ontos legacy <name>` | Rejected | No users on legacy scripts |
| Rename package | No action | You own PyPI; Databricks isn't on PyPI |
| Schema bump to 3.0 | Rejected | Don't bump for cosmetics |

---

## Testing Strategy

| Item | Test Type | Location |
|------|-----------|----------|
| P2-0 | Exit code assertions | `tests/test_exit_codes.py` |
| P2-3 | Unit: parse/normalize/validate | `tests/core/test_frontmatter_pipeline.py` |
| P2-4 | AST boundary checks | `tests/test_architecture.py` |
| P2-5 | Parametrized round-trip | `tests/commands/test_log_yaml.py` |
| P2-6 | Type safety + grep | `tests/core/test_types.py` |
| P2-8 | Scan-once verification | `tests/test_document_index.py` |
| P2-9 | Fixture-based orphan | `tests/core/test_orphan_policy.py` |
| P3-5 | Smoke on installed pkg | CI-only job |

**Coverage target:** P2-3 > 90% branch coverage.

---

## Backwards Compatibility Verification

Before merging any P2 item: run `ontos map` and `ontos doctor` on
THIS repo (469 documents). All must parse without regression.

---

## Files Modified (Summary)

| Category | Files |
|----------|-------|
| Config | `pyproject.toml`, `ontos/core/config.py` |
| New | `ontos/core/index.py`, `ontos/core/_yaml.py` (moved from `io/yaml.py`), `tests/test_architecture.py`, `tests/core/test_frontmatter_pipeline.py`, `tests/test_document_index.py` |
| Commands | `ontos/commands/doctor.py`, `ontos/commands/hook.py`, `ontos/commands/log.py`, `ontos/commands/map.py`, `ontos/commands/scaffold.py` |
| Core | `ontos/core/frontmatter.py`, `ontos/core/validation.py`, `ontos/core/staleness.py`, `ontos/core/types.py`, `ontos/core/graph.py` |
| CLI | `ontos/cli.py` |
| Docs | `README.md` (trust boundary section only) |
| CI | `.github/workflows/ci.yml` |
