---
id: v3_2_candidate_suggestions_exploration
type: strategy
status: draft
depends_on: []
concepts: [validation, suggestions, llm-integration, ux, broken-references]
---

# v3.2 Exploration: Candidate Suggestions for Broken References

**Author:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-25
**Status:** Research / Exploration
**Triggered by:** "Maintain Ontos" UX gap in finance-engine project

---

## 1. Problem Statement

### Current Behavior

When a user runs "Maintain Ontos" (`ontos agents && ontos map && ontos doctor`), broken `depends_on` references are **flagged but not fixed**:

```
- ❌ **finance_spec**: Broken dependency: 'finance_arch' does not exist
  Suggestion: Remove 'finance_arch' from depends_on or create the missing document
```

### User Expectation

"Maintain Ontos" should leave the project **healthy**, not just diagnosed. Users expect:
1. Auto-fix for unambiguous cases (ID moved but still exists)
2. Guided suggestions for ambiguous cases ("did you mean X?")
3. LLM-friendly output that enables delegation ("just fix them")

### Gap

| Command | Current Behavior | Expected Behavior |
|---------|------------------|-------------------|
| `ontos agents` | Regenerates (fixes) | ✅ |
| `ontos map` | Flags broken refs | Should suggest candidates |
| `ontos doctor` | Flags issues | Should have `--fix` mode |

---

## 2. Technical Analysis

### Data Available at Validation Time

When `build_graph()` in `ontos/core/graph.py` detects a broken reference, it has access to:

| Data | Source | Available? |
|------|--------|------------|
| All valid document IDs | `existing_ids` set | ✅ |
| Document aliases | `doc.aliases` (auto-generated) | ✅ |
| Document concepts/tags | `doc.tags` | ✅ |
| Document file paths | `doc.filepath` | ✅ |
| Full document content | `doc.content` | ✅ |
| Referencing doc context | `doc` object | ✅ |

### Existing Infrastructure

| Component | Location | Relevant? |
|-----------|----------|-----------|
| Suggestion algorithms | `ontos/core/suggestions.py` | ✅ Yes - add function here |
| String similarity | `difflib.SequenceMatcher` (stdlib) | ✅ Already used in tests |
| Substring matching | `suggestions.py:101-109` | ✅ Pattern exists |
| ValidationError type | `ontos/core/types.py` | ✅ Has `fix_suggestion` field |
| Error display | `ontos/commands/map.py:175-191` | ✅ Already formats suggestions |

---

## 3. Candidate Generation Strategies

### Strategy Comparison

| Strategy | Implementation | Confidence | Catches |
|----------|----------------|------------|---------|
| **Substring match** | `'arch' in doc_id.lower()` | 85%+ | Partial names, abbreviations |
| **Alias match** | Match against auto-aliases | 85%+ | Case/format variations |
| **Levenshtein distance** | `difflib.SequenceMatcher` | 75%+ | Typos, minor edits |
| **Concept overlap** | Jaccard similarity on tags | 60%+ | Semantic similarity |
| **Path inference** | Match filename to ID | 70%+ | File moves |

### Recommended MVP

Implement strategies 1-3 (low effort, high confidence):

```python
def suggest_candidates_for_broken_ref(
    broken_ref: str,
    all_docs: Dict[str, DocumentData],
    referencing_doc: DocumentData,
    threshold: float = 0.5
) -> List[Tuple[str, float, str]]:
    """
    Returns: [(doc_id, confidence, reason), ...]
    """
    candidates = []

    for doc_id, doc in all_docs.items():
        # Strategy 1: Substring match
        if broken_ref.lower() in doc_id.lower():
            candidates.append((doc_id, 0.85, "substring match"))
            continue

        # Strategy 2: Alias match
        if any(broken_ref.lower() in alias.lower() for alias in doc.aliases):
            candidates.append((doc_id, 0.85, "alias match"))
            continue

        # Strategy 3: Levenshtein distance
        ratio = difflib.SequenceMatcher(None, broken_ref, doc_id).ratio()
        if ratio >= threshold:
            candidates.append((doc_id, ratio, f"similarity: {ratio:.0%}"))

    return sorted(candidates, key=lambda x: -x[1])[:3]  # Top 3
```

---

## 4. Implementation Plan

### Entry Points

| File | Line(s) | Change |
|------|---------|--------|
| `ontos/core/suggestions.py` | (new) | Add `suggest_candidates_for_broken_ref()` |
| `ontos/core/graph.py` | 62-72 | Call suggestion function, enrich `fix_suggestion` |
| `ontos/commands/doctor.py` | (new flag) | Add `--fix` mode (Phase 2) |
| `tests/test_cycle_detection.py` | (new tests) | Verify candidate suggestions |

### Phase 1: Suggestions in Context Map

Modify `graph.py` to include candidates in validation output:

**Before:**
```python
errors.append(ValidationError(
    message=f"Broken dependency: '{dep_id}' does not exist",
    fix_suggestion=f"Remove '{dep_id}' from depends_on or create the missing document",
))
```

**After:**
```python
candidates = suggest_candidates_for_broken_ref(dep_id, docs_by_id, doc)
if candidates:
    suggestion = f"Did you mean: {candidates[0][0]} ({candidates[0][1]:.0%})?"
    if len(candidates) > 1:
        suggestion += f" Or: {candidates[1][0]} ({candidates[1][1]:.0%})?"
else:
    suggestion = f"Remove '{dep_id}' from depends_on or create the missing document"

errors.append(ValidationError(
    message=f"Broken dependency: '{dep_id}' does not exist",
    fix_suggestion=suggestion,
))
```

### Phase 2: `ontos doctor --fix`

Add auto-fix capability for unambiguous cases:

```bash
ontos doctor --fix
```

Behavior:
1. Run all health checks
2. For broken references with high-confidence candidates (>80%):
   - Show proposed fix
   - Apply if `--yes` flag or user confirms
3. For ambiguous cases: show candidates, ask user to choose
4. Update files atomically (frontmatter edit only)

---

## 5. Example Output

### Current (Diagnostic Only)

```markdown
## Validation

### Errors
- ❌ **finance_spec**: Broken dependency: 'finance_arch' does not exist
  Suggestion: Remove 'finance_arch' from depends_on or create the missing document
```

### Proposed (With Candidates)

```markdown
## Validation

### Errors
- ❌ **finance_spec**: Broken dependency: 'finance_arch' does not exist
  Candidates:
    - finance_engine_architecture (87% - substring + alias match)
    - finance_api_architecture (72% - substring only)
  Suggestion: Replace with 'finance_engine_architecture' or remove reference
```

### JSON Output (LLM-Friendly)

```json
{
  "error_type": "BROKEN_LINK",
  "doc_id": "finance_spec",
  "broken_ref": "finance_arch",
  "candidates": [
    {"id": "finance_engine_architecture", "confidence": 0.87, "reason": "substring + alias match"},
    {"id": "finance_api_architecture", "confidence": 0.72, "reason": "substring only"}
  ],
  "fix_suggestion": "Replace with 'finance_engine_architecture' or remove reference"
}
```

---

## 6. Relationship to Other v3.2 Features

| Feature | Dependency |
|---------|------------|
| `ontos doctor --fix` | Requires candidate suggestions (this) |
| `ontos move` / rename tracking | Orthogonal - could feed candidates |
| AGENTS.md staleness false positive | Separate bug fix |
| Exit code documentation | Separate docs update |

---

## 7. Open Questions

1. **Threshold tuning:** What confidence level should auto-fix require? (Proposal: 80%)
2. **Multiple candidates:** If two candidates have similar scores, should we refuse to auto-fix?
3. **Destructive fix:** Should `--fix` ever remove broken refs (as opposed to replacing)?
4. **Scope:** Should `--fix` also handle orphaned documents? Cycles?

---

## 8. Next Steps

1. [ ] Review this exploration with stakeholders
2. [ ] Decide on MVP scope (Phase 1 vs Phase 1+2)
3. [ ] Write implementation spec if approved
4. [ ] Estimate effort (rough: 2-3 days for Phase 1)
