---
id: log_20260111_ontology_architecture_research
type: log
status: active
event_type: decision
concepts:
- schema
- docs
- architecture
impacts:
- constitution
- philosophy
- schema
branch: unknown
source: Claude Opus 4.5
---

# Session Log: Ontology Architecture Research & Documentation Reorganization
Date: 2026-01-11 06:52 EST
Source: Claude Opus 4.5
Event Type: decision

## 1. Goal
Research and document the Ontos ontology hierarchy, identify documentation inconsistencies, and propose a unified architecture where the ontology specification and its enforcement mechanism are the same artifact ("Schema as Code").

## 2. Key Decisions

### 2.1 Ontology Architecture Proposal (v2.9.6)
- **Decision:** Adopt hybrid approach combining Option D (Layered Docs with Strict Roles) + Option B (Schema as Code)
- **Core insight:** The ontology specification and its enforcement mechanism should be the same artifact
- **Implementation:** Create `ontology.py` as THE source of truth, generate `ontology_spec.md` from code, have applied docs (Manual, Agent Instructions) reference spec without redefining

### 2.2 Version Classification
- **Decision:** This is v2.9.6 (quality improvement), not v3.0 (major feature)
- **Rationale:** Consolidating documentation is maintenance/quality work, not a new feature. Follows semantic versioning principles.

### 2.3 Documentation Reorganization
- **Decision:** Reorganize internal docs to better reflect the ontology hierarchy
- Created `kernel/constitution.md` and `kernel/philosophy.md` for foundational principles
- Moved `decision_history.md` from `strategy/` to `reference/`
- Created `strategy/technical_architecture.md` and `strategy/roadmap.md`

## 3. Alternatives Considered

### For Ontology Architecture:
- **Option A (Canonical Kernel + Derived):** Single master doc, others derived — rejected because readers must jump between docs
- **Option B (Schema as Code only):** All in code — rejected as too sterile without narrative
- **Option C (Single Unified Doc):** One massive document — rejected as too large for agent context
- **Option D (Layered Docs):** Strict role separation — selected as foundation
- **Option E (Hierarchical Reference):** Mirror ontology structure — elements incorporated

### For Version Number:
- **v3.0:** Considered because of significant architectural change — rejected because this is quality/maintenance, not feature
- **v2.9.6:** Selected — follows the v2.9.x quality release pattern established in previous work

## 4. Changes Made

### New Files:
- `.ontos-internal/strategy/proposals/v2.9.6/Ontology_Architecture_Proposal.md` — Comprehensive research document (~45KB, 1100+ lines) detailing the problem, proposed solution, technical requirements, and migration path
- `.ontos-internal/kernel/constitution.md` — Core invariants that define Ontos
- `.ontos-internal/kernel/philosophy.md` — Foundational philosophy and principles
- `.ontos-internal/strategy/technical_architecture.md` — Technical architecture documentation
- `.ontos-internal/strategy/roadmap.md` — Project roadmap
- `.ontos-internal/reference/decision_history.md` — Moved from strategy/

### Modified Files:
- `.ontos-internal/strategy/v2_strategy.md` — Refactored, philosophy content extracted
- Various `depends_on` references updated across proposal and log files
- `Ontos_Context_Map.md` — Regenerated to reflect new structure

### Deleted Files:
- `.ontos-internal/strategy/decision_history.md` — Moved to reference/
- `.ontos-internal/strategy/master_plan.md` — Content distributed to technical_architecture.md and other docs

## 5. Next Steps
1. LLM Review Board review of the Ontology Architecture Proposal
2. If approved, implement `ontology.py` with rich metadata (TypeDefinition, FieldDefinition, ValidationRule dataclasses)
3. Create doc generator for `ontology_spec.md`
4. Refactor validation scripts to read from `ontology.py`
5. Update Manual and Agent Instructions to reference generated spec

---
## Research Summary

### Problem Identified
Ontos ontology rules are distributed across 6 files (schema.py, schema.md, Ontos_Manual.md, Ontos_Agent_Instructions.md, v2_strategy.md, Common_Concepts.md) with overlapping and inconsistent content. Examples:
- Document types described differently in 4 files
- Validation rules differ across 3 files
- Status values: docs list 6, code has 7 (`auto-generated` missing from docs)

### Solution Proposed
```
ontology.py (THE Source of Truth)
    │
    ├──► ontology_spec.md (GENERATED)
    │
    └──► Validation Engine (reads ontology.py directly)
            │
            ▼
    Applied Docs (Manual, Agent Instructions)
    Reference spec, never redefine
```

### Key Dataclasses Proposed
- `TypeDefinition` — name, rank, description, can_depend_on, valid_statuses, philosophy
- `FieldDefinition` — name, type, required, description, validation_pattern, valid_values
- `ValidationRule` — id, name, description, severity, rationale
- `StatusTransition` — from_status, to_status, allowed_types, description
- `ConceptDefinition` — name, covers, avoid_using

---
## Raw Session History
```text
65c7d08 - docs(v3.0): add Technical Architecture and finalize strategy decisions
```
