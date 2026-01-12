---
id: log_20260112_feat_v2_9_6_ontology_single_source_of_truth
type: log
status: active
event_type: feature
impacts:
  - ontology_spec
  - v2_technical_architecture
concepts:
  - ontology
  - single-source-of-truth
  - immutability
  - import-safety
ontos_schema: "2.2"
curation_level: L2
---

# v2.9.6: Ontology Single Source of Truth (PR #38)

## Summary

Merged PR #38 implementing the ontology single source of truth architecture for v2.9.6. This establishes `ontology.py` as the canonical definition for all Ontos type and field definitions.

## Key Changes

### 1. Import Safety
- Removed `sys.path` mutation from all files
- Implemented `importlib.util.spec_from_file_location` pattern
- Affected files:
  - `ontos_config_defaults.py`
  - `ontos_generate_ontology_spec.py`
  - `test_ontology.py`

### 2. True Immutability
- Changed `List[str]` to `Tuple[str, ...]` in frozen dataclasses
- `TypeDefinition.can_depend_on` and `valid_statuses` now tuples
- `FieldDefinition.valid_values` and `applies_to` now tuples
- `_CURATION_STATUSES` now tuple

### 3. Semantic Alignment
- `depends_on.required = False` (matches schema.py v2.2)
- `event_type.required = False` (not enforced by validation)
- `depends_on.applies_to` excludes kernel (matches curation.py)
- Added clarifying docstring about FIELD_DEFINITIONS being metadata-only

### 4. Generated Spec Improvements
- Added "Schema Requirements by Version" section (v1.0–v3.0)
- Fixed header from "v2.2+" to "v1.0–v3.0"
- Split fields into three categories: Required (All), Required (Type-Specific), Optional

### 5. Test Coverage
- 21 new tests in `test_ontology.py`
- Drift detection tests to prevent schema/ontology divergence
- Immutability tests for tuple fields

## Review Process

6 rounds of review with Codex (strict reviewer) and Claude Opus 4.5 (architect):
1. Generator logic bug (depends_on shown as Optional)
2. Semantic drift (kernel/event_type)
3. depends_on.required alignment
4. sys.path mutation + lists vs tuples
5. Header fix + missing tests
6. Codex caught sys.path.insert in Claude's test instructions

## Files Changed

```
.ontos/scripts/ontos/core/ontology.py
.ontos/scripts/ontos_config_defaults.py
.ontos/scripts/ontos_generate_ontology_spec.py
.ontos/scripts/tests/test_ontology.py (NEW)
docs/reference/ontology_spec.md
```

## Verification

All 21 tests pass:
```
============================== 21 passed in 0.04s ==============================
```

## Source

Claude Code (Claude Opus 4.5) with Antigravity (developer agent)
