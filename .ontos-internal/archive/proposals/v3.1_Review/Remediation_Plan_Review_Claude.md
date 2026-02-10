## Comprehensive Final Review

This plan is thorough and well-organized. It correctly consolidates inputs from multiple reviewers. However, there are sequencing errors, under-specified items, scope issues given your single-user context, and some contradictions that will cause implementation friction.

---

## Critical Issues (Must Address Before Implementation)

### Issue 1: P2-4 Architecture Guardrails Has a Bootstrap Problem

The plan says "P2-4 FIRST -- prevents regression."

**Problem:** Your current code already violates the proposed boundary. Look at `commands/map.py`:

```python
from ontos.io.files import find_project_root, scan_documents, load_document
from ontos.io.config import load_project_config
from ontos.io.yaml import parse_frontmatter_content
from ontos.io.obsidian import read_file_lenient
```

If you add architecture tests first, they fail immediately. You can't prevent regression on code that's already non-compliant.

**Fix:** Change implementation order:
```
v3.2.0:
  P2-3  Frontmatter pipeline (restructure io/ access pattern)
  P2-1  Unify project root (reduces io/ imports)
  P2-8  Centralize scanning (reduces io/ imports)
  P2-4  Architecture guardrails (NOW tests pass, prevents regression)
  ... rest
```

Or: Add P2-4 tests with `@pytest.mark.xfail` initially, fix violations, then remove xfail markers.

**Update the plan to acknowledge this sequencing dependency.**

---

### Issue 2: P2-3 Frontmatter Pipeline is Under-Specified

This is the highest-risk item. Three-stage pipeline touching 4+ files with no API specification.

**Missing decisions:**

1. **Function signatures** — What do these actually look like?
```python
# Proposal - add to plan:
def parse_frontmatter(raw_text: str) -> tuple[dict | None, str, list[ParseError]]
def normalize_frontmatter(raw: dict, mode: NormalizeMode) -> tuple[FrontmatterNormalized, list[Issue]]
def validate_frontmatter(norm: FrontmatterNormalized, policy: ValidationPolicy) -> list[Violation]
```

2. **What's in FrontmatterNormalized?** — Is it a dict? A dataclass? Does it have typed fields or is it still stringly-typed?

3. **Error accumulation vs. fail-fast** — Does normalization stop on first error or collect all? (Collect all is better for user feedback.)

4. **Who calls this pipeline?** — Is there a single `load_document()` that orchestrates all three stages? Or do commands call stages individually?

**Add a "P2-3 API Specification" subsection with these decisions.**

---

### Issue 3: P2-4 Boundary Rule is Ambiguous

> "commands/ can import core/, NOT io/"

**Questions:**
- Commands need to write files eventually. How? Does `core/` expose a `write_document()` that internally calls `io/`?
- Are transitive imports allowed? If `core/frontmatter.py` imports `io/yaml.py`, and `commands/map.py` imports `core/frontmatter.py`, is that compliant?
- What about `io/config.py`? Every command needs config. Does that go through `core/`?

**My interpretation of what you probably want:**
```
commands/ → core/ → io/     ✓ (layered)
commands/ → io/             ✗ (skip layer)
io/ → commands/             ✗ (reverse dependency)
io/ → core/                 ✗ (reverse dependency)
core/ → core/               ✓ (same layer)
```

**Add this diagram or equivalent to P2-4.**

---

### Issue 4: P2-8 Centralize Scanning Has No Specification

> "Single document index builder that commands receive pre-built."

**Unanswered:**
- Who builds it? A new orchestration layer? The CLI main()?
- When is it built? Eagerly on startup? Lazily on first access?
- Is it cached across commands in a single CLI invocation?
- What's the API? `get_document_index() -> Dict[str, DocumentData]`?

**Proposal to add:**
```python
# New: ontos/core/index.py
class DocumentIndex:
    def __init__(self, project_root: Path, config: OntosConfig):
        self._docs: Dict[str, DocumentData] = {}
        self._loaded = False
    
    def load(self) -> None:
        """Scan and parse all documents once."""
        ...
    
    def get(self, doc_id: str) -> DocumentData | None: ...
    def all(self) -> Iterable[DocumentData]: ...
    def filter(self, predicate: Callable) -> Iterable[DocumentData]: ...
```

Commands receive `index: DocumentIndex` from CLI orchestration layer.

---

## Scope Issues (Single-User Reality Check)

You told me the user base is just you. This plan includes work for hypothetical users.

### Items to Cut or Defer to "Maybe Never"

| Item | Why Cut |
|------|---------|
| P3-1 LLM-Assisted Scaffold | Scope creep. You don't need AI to write frontmatter. |
| P3-2 GitHub Action | You're the only user. Just run `ontos doctor` locally. |
| P3-4 Init Template | You know the system. You don't need a starter doc. |
| P3-6 Integration Guides | No users to guide. |
| P3-7 Staleness Docs | You know how it works. |
| P3-8 Version FAQ | You understand the versioning. |
| P1-3 README Messaging | If no one reads it, cosmetic changes don't matter. |

### Items to Keep Despite Single User

| Item | Why Keep |
|------|----------|
| P1-2 Skip Generated Files | Bug that affects you |
| P2-1 through P2-9 | Technical debt reduction that helps *your* velocity |
| P3-3 ontos lint | Useful for your own CI |
| P3-5 sdist Smoke Tests | Catches real bugs |

**Recommendation:** Move P3-1, P3-2, P3-4, P3-6, P3-7, P3-8 to a "Post-Users" section. Don't schedule them for v3.2.

---

## Acceptance Criteria Gaps

### P2-2: "One-Time Deprecation Warning"

> "emit one-time deprecation warning with migration hint"

How is "one-time" implemented? Options:
- Write a marker file (`.ontos-internal/.config-warning-shown`)
- Warn every invocation (simpler, slightly noisier)

For single user, just warn every time. Don't over-engineer state tracking.

**Change to:** "emit deprecation warning on each invocation when legacy config detected"

---

### P2-3: Missing Correctness Criterion

> "Done when: No command imports from ontos.io.yaml directly."

This checks structure, not correctness. Add:
> "Done when: [...] AND `test_frontmatter_pipeline.py` passes, covering: empty frontmatter, missing required fields, string vs list `describes`, malformed YAML, special characters in values."

---

### P2-6: What Happens When Audit Finds Non-Enum Types?

> "Audit all DocumentData instantiation sites -- ensure type is always DocumentType enum"

When you find a site creating `DocumentData(type="atom")` instead of `DocumentData(type=DocumentType.ATOM)`, what do you do?

Options:
- Fix the call site to use enum
- Add a normalizing constructor that accepts string or enum
- Raise TypeError if string passed

**Decision needed.** I recommend: Fix call sites, add runtime check in `DocumentData.__post_init__` that raises if type isn't enum.

---

### P2-8: Missing Behavior Criterion

> "Done when: grep shows at most one coordinating call site"

Grep is a structure check. Add behavior:
> "Done when: [...] AND running `ontos map` then `ontos doctor` in sequence only scans documents once (verified via log or counter)."

---

## Missing Items

### 1. Error Handling Strategy

None of the items specify error behavior. For P2-3 especially:
- What exit code on parse failure? (1)
- What exit code on validation failure? (2? configurable?)
- Does `--json` mode change error output?

**Add a "P2-0: Error Handling Convention" item:**
```
Exit codes:
  0 = success
  1 = runtime error (file not found, parse failure)
  2 = validation error (in strict mode)
  130 = interrupted (Ctrl+C)

All errors to stderr. JSON mode wraps errors in {"status": "error", "message": "...", "code": "E_..."}.
```

---

### 2. Backwards Compatibility Check

You have existing projects using Ontos. Will P2-3 (frontmatter pipeline refactor) break them?

**Add verification step:**
> "Before merging P2-3: run `ontos map` and `ontos doctor` on Project-Ontos repo itself. All existing documents must parse without regression."

---

### 3. Type Coercion Resolution

P2-6 says audit, but doesn't say what to do when you find problems.

**Add explicit resolution:**
```python
# In DocumentData.__post_init__:
if not isinstance(self.type, DocumentType):
    raise TypeError(f"type must be DocumentType enum, got {type(self.type).__name__}")
```

This makes the failure loud and immediate during development.

---

## Contradictions

### 1. Deferred Table: "Rename package: Monitoring"

Earlier we agreed this is deprioritized because you own PyPI. "Monitoring" suggests ongoing attention. Change to:

> "Rename package | Noted | No action unless Databricks publishes to PyPI"

---

### 2. P2-2 vs P2-3 Overlap

P2-2 says remove `from ontos_config` imports. P2-3 restructures frontmatter handling.

If `log.py` imports `ontos_config` for frontmatter-related defaults, fixing P2-2 and P2-3 might conflict. 

**Clarify:** P2-2 is about config file source (`.ontos.toml` vs `ontos_config.py`). P2-3 is about frontmatter parsing. They're orthogonal. Add a note confirming this to prevent implementer confusion.

---

## Implementation Order (Revised)

Your current order:
```
P2-4 → P2-1 → P2-2 → P2-3 → P2-5 → P2-6 → P2-7 → P2-8 → P2-9
```

**Corrected order:**
```
v3.2.0:
  P2-7  Dead code removal (quick win, reduces noise)
  P2-1  Unify project root (foundation)
  P2-2  .ontos.toml authoritative (foundation)
  P2-8  Centralize scanning (reduces io/ imports in commands)
  P2-3  Frontmatter pipeline (major refactor, depends on P2-8)
  P2-4  Architecture guardrails (NOW code is compliant)
  P2-5  Log YAML safety (uses P2-3 pipeline)
  P2-6  Type coercion audit (can happen anytime)
  P2-9  Orphan policy (uses centralized index from P2-8)
```

**Rationale:**
- P2-7 first: removes dead code before you refactor anything
- P2-1, P2-2: establish foundation before restructuring
- P2-8 before P2-3: scanning abstraction makes frontmatter refactor cleaner
- P2-4 after restructuring: tests now pass
- P2-5 after P2-3: log command uses the new pipeline

---

## Testing Strategy (Missing Section)

Add a section:

### Testing Strategy

| Item | Test Type | Location |
|------|-----------|----------|
| P2-3 | Unit tests for parse/normalize/validate | `tests/core/test_frontmatter.py` |
| P2-4 | AST boundary checks | `tests/test_architecture.py` |
| P2-5 | Parametrized round-trip | `tests/commands/test_log.py` |
| P2-6 | Grep-based (CI script) | `.github/workflows/ci.yml` |
| P2-8 | Integration test (scan-once verification) | `tests/test_integration.py` |
| P3-5 | Smoke tests on installed package | `tests/test_installed.py` (runs in CI only) |

**Coverage target:** P2-3 should have >90% branch coverage given it's the core parsing logic.

---

## Summary of Required Changes

| Section | Change |
|---------|--------|
| Implementation Order | Fix bootstrap problem: P2-4 must come after code restructuring |
| P2-3 | Add API specification (signatures, types, error handling) |
| P2-4 | Add boundary diagram clarifying transitive imports |
| P2-8 | Add `DocumentIndex` API specification |
| P2-6 | Add resolution: what to do when audit finds violations |
| Acceptance Criteria | Add correctness tests to P2-3, P2-8 |
| Scope | Move P3-1, P3-2, P3-4, P3-6, P3-7, P3-8 to "Post-Users" |
| New Section | Add Testing Strategy |
| New Item | Add P2-0 Error Handling Convention |
| New Item | Add backwards compatibility verification step |
| Deferred Table | Change "Monitoring" to "Noted, no action" for rename |

---

## Final Verdict

The plan is 80% there. The critical gap is the **P2-4 sequencing error** — if you implement as written, your first PR adds tests that immediately fail. The secondary gap is **P2-3 under-specification** — it's the riskiest refactor with the least detail.

Fix those two, cut the user-facing features you don't need yet, and this becomes a solid implementation roadmap.