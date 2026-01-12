---
id: ontology_spec
type: kernel
status: active
depends_on: [mission]
---

# Ontos Ontology Specification

> **GENERATED FILE - DO NOT EDIT DIRECTLY**
>
> Generated: 2026-01-12T00:02:36Z
> Source: `.ontos/scripts/ontos/core/ontology.py`
> Schema: v1.0–v3.0 (see schema.py for version differences)

---

## 1. Document Types

| Type | Rank | Can Depend On | Valid Statuses |
|------|------|---------------|----------------|
| `kernel` | 0 | kernel | active, draft, deprecated, scaffold, pending_curation |
| `strategy` | 1 | kernel | active, draft, deprecated, rejected, complete, scaffold, pending_curation |
| `product` | 2 | kernel, strategy | active, draft, deprecated, scaffold, pending_curation |
| `atom` | 3 | kernel, strategy, product, atom | active, draft, deprecated, complete, scaffold, pending_curation |
| `log` | 4 | (none) | active, archived, auto-generated, scaffold, pending_curation |

### Type Descriptions

- **kernel**: Foundational principles - mission, values, core identity
- **strategy**: Goals, direction, roadmap - business decisions
- **product**: User-facing specifications - features, requirements
- **atom**: Technical specs, architecture, implementation details
- **log**: Session history - temporal records of work

---

## 2. Frontmatter Fields

### Required Fields (All Types)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (snake_case, immutable) |
| `type` | enum | Document type in hierarchy |
| `status` | enum | Document lifecycle state |

### Required Fields (Type-Specific)

| Field | Type | Applies To | Description |
|-------|------|------------|-------------|

### Optional Fields

| Field | Type | Applies To | Description |
|-------|------|------------|-------------|
| `depends_on` | list | strategy, product, atom | Referenced document IDs (required at L2 for strategy/product/atom) |
| `impacts` | list | log | Document IDs modified in this session |
| `event_type` | enum | log | Session type |
| `concepts` | list | all | Abstract concepts discussed |
| `ontos_schema` | string | all | Schema version |
| `curation_level` | enum | all | Level of human curation |
| `describes` | list | atom | Source files this doc describes |

---

## 3. Schema Requirements by Version

### Schema v1.0
- Required: id
- Optional: type, depends_on

### Schema v2.0
- Required: id, type
- Optional: status, depends_on, concepts, event_type, impacts

### Schema v2.1
- Required: id, type
- Optional: status, depends_on, concepts, describes, describes_verified

### Schema v2.2
- Required: id, type, status
- Optional: depends_on, concepts, ontos_schema, curation_level

### Schema v3.0
- Required: id, type, status, ontos_schema
- Optional: depends_on, concepts, implements, tests, deprecates

---

*End of Specification*
