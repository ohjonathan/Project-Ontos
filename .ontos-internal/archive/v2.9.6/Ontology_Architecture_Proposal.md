---
id: ontology_architecture_proposal
type: strategy
status: draft
depends_on: [technical_architecture, constitution]
concepts: [schema, docs, architecture, v2.9.6]
---

# Ontos Ontology Architecture: Research Document

**Author:** Claude Opus 4.5 (Chief Architect)
**Date:** 2026-01-11
**Status:** DRAFT — For LLM Review Board
**Purpose:** Define unified approach to ontology specification, documentation, and enforcement

---

## Executive Summary

This document proposes a unified architecture for Ontos ontology management that combines:

1. **Schema as Code** — The ontology is defined in Python (`ontology.py`), making it both human-readable and machine-enforceable
2. **Generated Documentation** — Human-facing docs are generated from code, eliminating drift
3. **Layered References** — Applied docs (Manual, Agent Instructions) reference the spec, never redefine

**Core Insight:** The ontology specification and its enforcement mechanism should be the same artifact.

---

## Part 1: Problem Statement

### 1.1 The Founder's Observation

During a research session on the Ontos ontology hierarchy, the following concern was raised:

> "I feel like we should have one source of truth. Have all this main document reference the main ontology rules. The main doc for that right now is not only just writing an ontology reference doc, but we should think about how we can restructure this so it's easy to maintain. Everything sounds the same because right now I'm concerned that all this doc may say slightly different things from one way or the other."

This observation identifies a core architectural issue: **the documentation that defines Ontos doesn't follow Ontos principles.**

### 1.2 Current State: Where Ontology Rules Live

Ontos ontology rules are currently distributed across multiple files:

| Location | What It Defines | Document Type | Lines |
|----------|-----------------|---------------|-------|
| `schema.py` | Required/optional fields per schema version | Code (enforcement) | ~420 |
| `schema.md` | Field definitions, validation rules | atom | ~45 |
| `Ontos_Manual.md` | Type descriptions, hierarchy, workflows | kernel | ~639 |
| `Ontos_Agent_Instructions.md` | Type hierarchy, validation errors | kernel | ~323 |
| `v2_strategy.md` | Philosophy, dual ontology concept | strategy | ~281 |
| `Common_Concepts.md` | Concepts vocabulary | atom | ~84 |

**Total:** 6 files defining overlapping aspects of the same ontology.

### 1.3 Concrete Examples of Inconsistency

#### Example 1: Document Type Definitions

**In `Ontos_Manual.md` (lines 53-60):**
```markdown
| Type | Rank | Use For |
|------|------|---------|
| `kernel` | 0 | Mission, values, principles (rarely changes) |
| `strategy` | 1 | Goals, roadmap, audience (business decisions) |
| `product` | 2 | Features, user flows, requirements |
| `atom` | 3 | Technical specs, API, implementation |
| `log` | 4 | Session history (what happened) |
```

**In `Ontos_Agent_Instructions.md` (lines 134-143):**
```markdown
| Type | Rank | Depends On |
|------|------|-----------|
| kernel | 0 | nothing |
| strategy | 1 | kernel |
| product | 2 | kernel, strategy |
| atom | 3 | kernel, strategy, product, atom |
| log | 4 | uses `impacts`, not `depends_on` |
```

**In `v2_strategy.md` (lines 70-78):**
```markdown
**Space Ontology (The Graph)**
- `kernel` — foundational principles
- `strategy` — goals and direction
- `product` — user-facing specs
- `atom` — technical implementation
```

**In `schema.md` (line 17):**
```markdown
| `type` | enum | Yes | `kernel`, `strategy`, `product`, `atom`, `log` |
```

**The Problem:** Each file describes types differently:
- Manual focuses on "Use For"
- Agent Instructions focuses on "Depends On"
- v2_strategy gives philosophical framing
- schema.md just lists the enum

None is wrong, but together they create **fragmented understanding**. A reader must synthesize 4 sources to get the full picture.

#### Example 2: Validation Rules

**In `Ontos_Manual.md` (lines 436-443):**
```markdown
| Error | Cause | Fix |
|-------|-------|-----|
| `[BROKEN LINK]` | Reference to nonexistent ID | Create doc or remove reference |
| `[CYCLE]` | A → B → A | Remove one dependency |
| `[ORPHAN]` | No dependents | Connect it or delete |
| `[DEPTH]` | Chain > 5 levels | Flatten hierarchy |
| `[ARCHITECTURE]` | Kernel depends on atom | Invert or retype |
```

**In `Ontos_Agent_Instructions.md` (lines 147-154):**
```markdown
| Error | Fix |
|-------|-----|
| `[BROKEN LINK]` | Create referenced doc or remove from depends_on |
| `[CYCLE]` | Remove one dependency in the loop |
| `[ORPHAN]` | Add to another doc's depends_on |
| `[ARCHITECTURE]` | Lower-rank can't depend on higher-rank |
| `[STALE]` | Document's `describes` targets were modified... |
```

**In `schema.md` (lines 39-44):**
```markdown
## 4. Validation Rules
1. **ID Unicity:** IDs must be unique across the entire project.
2. **Dependency Existence:** All IDs in `depends_on` must exist.
3. **No Cycles:** The dependency graph (excluding logs) must be acyclic.
4. **No Orphans:** All documents (except allowed types) must have a dependent.
5. **Type-Status Matrix:** Only valid (type, status) combinations are allowed (v2.6+).
```

**The Problem:**
- Manual has 5 errors, Agent Instructions has 5 (different set), schema.md has 5 (different again)
- `[DEPTH]` appears only in Manual
- `[STALE]` appears only in Agent Instructions
- `Type-Status Matrix` appears only in schema.md
- The ARCHITECTURE error is described differently in each

#### Example 3: Status Values

**In `Ontos_Manual.md` (lines 176-184):**
```markdown
| Status | Meaning |
|--------|---------|
| `draft` | Work in progress |
| `active` | Current truth (approved, in use) |
| `deprecated` | Past truth (superseded) |
| `archived` | Historical record (logs) |
| `rejected` | Considered but NOT approved |
| `complete` | Finished work (reviews) |
```

**In `schema.md` (line 16):**
```markdown
| `status` | enum | Yes | `active`, `draft`, `deprecated`, `archived`, `rejected`, `complete` |
```

**In code (`schema.py` lines 236-238):**
```python
"status": FieldDefinition(
    ...
    valid_values=["active", "draft", "deprecated", "archived", "rejected", "complete", "auto-generated"],
)
```

**The Problem:**
- Manual lists 6 statuses
- schema.md lists 6 statuses (same set)
- But code has 7 statuses (includes `auto-generated`)
- `auto-generated` is used in practice but not documented in the "official" docs

### 1.4 Core Ontos Values Being Violated

| Ontos Principle | What It Means | How Current Docs Violate It |
|-----------------|---------------|----------------------------|
| **"Never explain twice"** | Document once, use everywhere | Same concepts explained in 4+ files |
| **Single source of truth** | One authoritative definition | Multiple overlapping definitions |
| **Explicit dependencies** | `depends_on` makes relationships clear | Docs have implicit, undeclared dependencies |
| **Structure over search** | Navigate by structure, not by guessing | Must search multiple files to understand ontology |
| **Curation over ceremony** | Intentional structure creates signal | Duplication is the opposite of curation |

### 1.5 Why This Matters

#### Maintenance Burden
When you need to update a rule (e.g., add a new status), you must:
1. Update `schema.py` (code)
2. Update `schema.md` (docs)
3. Update `Ontos_Manual.md` (if status is mentioned)
4. Update `Ontos_Agent_Instructions.md` (if status is mentioned)
5. Hope you didn't miss anything

**There is no automated check for consistency.** Files can drift silently.

#### Agent Confusion
When an agent loads context, it may get:
- `Ontos_Manual.md` which says one thing
- `Ontos_Agent_Instructions.md` which says almost the same thing, slightly differently
- Which is authoritative? The agent can't know.

#### Trust Erosion
If a user notices that docs contradict each other (even slightly), they lose trust in the documentation. They start checking the code directly, bypassing the docs entirely.

#### Onboarding Friction
New users/agents must read multiple files to understand the ontology. There's no single document that says "here is the complete, authoritative definition."

### 1.6 The Root Cause

The documentation evolved organically:
1. `Ontos_Manual.md` was written first as comprehensive user guide
2. `Ontos_Agent_Instructions.md` was extracted for agent consumption
3. `schema.md` was created for formal validation reference
4. Each evolved independently, with no single source

**There was never a deliberate decision about which file is authoritative.**

The `depends_on` relationships exist in frontmatter:
- `ontos_agent_instructions` depends_on `ontos_manual`
- `schema` depends_on `v2_strategy`

But these dependencies don't prevent content duplication. The `depends_on` is structural, not semantic.

### 1.7 The Irony

Ontos is a system for structured knowledge with explicit dependencies. But its own documentation:
- Has implicit dependencies (content copied, not referenced)
- Duplicates content (same concepts in multiple files)
- Lacks single source of truth (no file is definitively authoritative)
- Violates its own principles (the cobbler's children have no shoes)

**If Ontos can't manage its own documentation properly, why would users trust it to manage theirs?**

This is not just a maintenance issue. It's a credibility issue.

### 1.8 Research Journey: How We Arrived at This Proposal

#### Phase 1: Discovery

The research began with a question about the Ontos ontology hierarchy. While documenting the hierarchy, we identified that:
1. Ontology rules exist in 6 different files
2. Each file has overlapping but different content
3. There's no single source of truth

#### Phase 2: Options Analysis

We evaluated five approaches:

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| **A** | Canonical Kernel + Derived Docs | True single source | Readers must jump between docs |
| **B** | Schema as Code, Docs Generated | No drift possible | Loses narrative quality |
| **C** | Single Unified Document | Truly single source | Too large for agent context |
| **D** | Layered Docs with Strict Roles | Clear separation of concerns | Requires discipline |
| **E** | Hierarchical Reference Pattern | Mirrors ontology structure | Requires creating new kernel doc |

#### Phase 3: Synthesis

The founder's insight:

> "On top of option D, I also like option B. You know, schema is code. If this can be done and we treat these two things as equivalent, because schema.py can just be an enforcing mechanism of ontology, I think that can be pretty cool."

This led to the hybrid approach: **Option D + Option B**

- **Option D:** Layered documentation with strict roles
  - `ontology_spec.md` (generated) = normative definitions
  - `Ontos_Manual.md` = workflows, examples, heuristics
  - `Ontos_Agent_Instructions.md` = agent commands, quick reference

- **Option B:** Schema as Code
  - `ontology.py` = THE source of truth (code)
  - Contains rich metadata (descriptions, philosophy, examples)
  - Drives both doc generation AND validation
  - Docs literally cannot drift from enforcement

#### Phase 4: The Core Insight

**The ontology specification and its enforcement mechanism should be the same artifact.**

Currently:
- `schema.py` (code) defines SOME rules
- `schema.md` (docs) defines OTHER rules
- `Ontos_Manual.md` (docs) defines YET OTHER rules
- Validation code implements a SUBSET of documented rules

With the hybrid approach:
- `ontology.py` defines ALL rules (code)
- `ontology_spec.md` is GENERATED from `ontology.py`
- Validation code READS from `ontology.py`
- **What's documented = What's enforced**

---

## Part 2: Proposed Architecture

### 2.1 The Vision

```
┌─────────────────────────────────────────────────────────────────┐
│                      ontology.py                                │
│                   (THE Source of Truth)                         │
│                                                                 │
│  TYPE_DEFINITIONS    FIELD_DEFINITIONS    VALIDATION_RULES     │
│  STATUS_TRANSITIONS  CONCEPTS_VOCABULARY  HIERARCHY_RULES      │
│                                                                 │
│  Human-readable (rich docstrings, descriptions)                │
│  Machine-executable (drives all validation)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│   ontology_spec.md        │   │   Validation Engine           │
│   (GENERATED)             │   │   (Uses ontology.py directly) │
│                           │   │                               │
│   § Document Types        │   │   • Type hierarchy check      │
│   § Frontmatter Schema    │   │   • Dependency validation     │
│   § Validation Rules      │   │   • Status transitions        │
│   § Status Lifecycle      │   │   • Field requirements        │
│                           │   │                               │
│   "Do not edit directly"  │   │   Single enforcement source   │
└───────────────────────────┘   └───────────────────────────────┘
                │
                │ depends_on (reference, not redefine)
                ▼
┌───────────────────────────────────────────────────────────────┐
│                    Applied Documentation                       │
│                                                                │
│   Ontos_Manual.md              Ontos_Agent_Instructions.md    │
│   ├── Workflows                ├── Command reference          │
│   ├── Examples                 ├── Quick reference tables     │
│   ├── Heuristics               ├── Agent-specific rules       │
│   └── References spec          └── References spec + manual   │
│                                                                │
│   These docs NEVER redefine types, fields, or rules.          │
│   They explain how to USE them.                               │
└───────────────────────────────────────────────────────────────┘
```

### 2.2 Core Principle: Code IS Documentation

The ontology is defined ONCE, in code, with rich metadata:

```python
# ontology.py (NEW FILE - THE source of truth)

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum

# ============================================================
# DOCUMENT TYPES
# ============================================================

@dataclass
class TypeDefinition:
    """Definition of a document type in the Ontos ontology."""
    name: str
    rank: int
    description: str
    can_depend_on: List[str]
    valid_statuses: List[str]
    uses_impacts: bool = False  # True for log type
    examples: List[str] = None
    philosophy: str = ""  # Why this type exists

TYPE_DEFINITIONS: Dict[str, TypeDefinition] = {
    "kernel": TypeDefinition(
        name="kernel",
        rank=0,
        description="Foundational principles — mission, values, core identity. "
                    "Rarely changes. The bedrock of the knowledge graph.",
        can_depend_on=[],
        valid_statuses=["active", "draft", "deprecated"],
        examples=["mission", "ontos_manual", "ontos_agent_instructions"],
        philosophy="Kernels answer 'Who are we?' They ground all other documents. "
                   "If a kernel changes, the entire project's direction may shift.",
    ),
    "strategy": TypeDefinition(
        name="strategy",
        rank=1,
        description="Goals, direction, roadmap — business and product decisions. "
                    "Changes with planning cycles.",
        can_depend_on=["kernel"],
        valid_statuses=["active", "draft", "deprecated", "rejected"],
        examples=["v2_strategy", "master_plan"],
        philosophy="Strategy bridges mission (kernel) and execution (product/atom). "
                   "It answers 'Where are we going?'",
    ),
    "product": TypeDefinition(
        name="product",
        rank=2,
        description="User-facing specifications — features, requirements, user flows. "
                    "Defines what users experience.",
        can_depend_on=["kernel", "strategy"],
        valid_statuses=["active", "draft", "deprecated"],
        examples=["feature_auth", "user_onboarding"],
        philosophy="Product translates strategy into user value. "
                   "It answers 'What will users see?'",
    ),
    "atom": TypeDefinition(
        name="atom",
        rank=3,
        description="Technical implementation details — specs, architecture, APIs. "
                    "The how behind the what.",
        can_depend_on=["kernel", "strategy", "product", "atom"],
        valid_statuses=["active", "draft", "deprecated", "complete"],
        examples=["schema", "api_spec", "common_concepts"],
        philosophy="Atoms are the technical truth. They answer 'How does it work?' "
                   "They can depend on other atoms for modularity.",
    ),
    "log": TypeDefinition(
        name="log",
        rank=4,
        description="Session history — temporal records of work sessions. "
                    "Captures what happened and why.",
        can_depend_on=[],  # Logs don't use depends_on
        uses_impacts=True,  # Logs use 'impacts' instead
        valid_statuses=["active", "auto-generated", "archived"],
        examples=["2026-01-08_feature_auth"],
        philosophy="Logs are the Time dimension. They don't participate in the "
                   "dependency graph; they OBSERVE it via 'impacts'.",
    ),
}

# ============================================================
# FRONTMATTER FIELDS
# ============================================================

@dataclass
class FieldDefinition:
    """Definition of a frontmatter field."""
    name: str
    type: str  # "string", "list[string]", "enum", "date"
    required: bool
    description: str
    default: Optional[str] = None
    validation_pattern: Optional[str] = None
    valid_values: Optional[List[str]] = None
    applies_to: Optional[List[str]] = None  # If None, applies to all types
    examples: List[str] = None

FIELD_DEFINITIONS: Dict[str, FieldDefinition] = {
    "id": FieldDefinition(
        name="id",
        type="string",
        required=True,
        description="Unique identifier for this document. Use snake_case. "
                    "Never change after creation — other documents may reference it.",
        validation_pattern=r"^[a-z][a-z0-9_]*$",
        examples=["mission", "v2_strategy", "api_spec", "log_2026_01_08"],
    ),
    "type": FieldDefinition(
        name="type",
        type="enum",
        required=True,
        description="Document type determining position in hierarchy and valid dependencies.",
        valid_values=["kernel", "strategy", "product", "atom", "log"],
    ),
    "status": FieldDefinition(
        name="status",
        type="enum",
        required=True,
        description="Current state of the document in its lifecycle.",
        valid_values=["active", "draft", "deprecated", "archived", "rejected", "complete", "auto-generated"],
    ),
    "depends_on": FieldDefinition(
        name="depends_on",
        type="list[string]",
        required=True,
        description="List of document IDs this document references. "
                    "Creates edges in the knowledge graph. Can be empty [].",
        default="[]",
        applies_to=["kernel", "strategy", "product", "atom"],
        examples=["[mission]", "[v2_strategy, api_spec]", "[]"],
    ),
    "impacts": FieldDefinition(
        name="impacts",
        type="list[string]",
        required=False,
        description="For logs: document IDs modified or discussed in this session. "
                    "Bridges Time (logs) to Space (other types).",
        applies_to=["log"],
        examples=["[auth_flow, api_spec]"],
    ),
    "concepts": FieldDefinition(
        name="concepts",
        type="list[string]",
        required=False,
        description="Abstract concepts discussed. Use vocabulary from Common_Concepts.md. "
                    "Enables cross-cutting queries.",
        examples=["[auth, api]", "[schema, migration]"],
    ),
    "event_type": FieldDefinition(
        name="event_type",
        type="enum",
        required=True,
        description="For logs: what kind of session this was.",
        valid_values=["feature", "fix", "refactor", "exploration", "chore", "decision"],
        applies_to=["log"],
    ),
    "ontos_schema": FieldDefinition(
        name="ontos_schema",
        type="string",
        required=False,
        description="Schema version this document conforms to. "
                    "Enables forward-compatible parsing.",
        valid_values=["1.0", "2.0", "2.1", "2.2", "3.0"],
        default="2.2",
    ),
    # v2.9.6 fields
    "implements": FieldDefinition(
        name="implements",
        type="list[string]",
        required=False,
        description="For atoms: paths to source files this spec describes. "
                    "Links documentation to code.",
        applies_to=["atom"],
        examples=["[src/api/auth.py]"],
    ),
    "tests": FieldDefinition(
        name="tests",
        type="list[string]",
        required=False,
        description="For atoms: paths to test files that verify this spec.",
        applies_to=["atom"],
        examples=["[tests/test_auth.py]"],
    ),
}

# ============================================================
# VALIDATION RULES
# ============================================================

@dataclass
class ValidationRule:
    """A rule that documents must satisfy."""
    id: str
    name: str
    description: str
    severity: str  # "error", "warning", "info"
    applies_to: Optional[List[str]] = None  # None = all types
    rationale: str = ""

VALIDATION_RULES: List[ValidationRule] = [
    ValidationRule(
        id="ID_UNICITY",
        name="ID Unicity",
        description="Document IDs must be unique across the entire project.",
        severity="error",
        rationale="IDs are the primary key for the knowledge graph. "
                  "Duplicates would create ambiguous references.",
    ),
    ValidationRule(
        id="DEPENDENCY_EXISTS",
        name="Dependency Exists",
        description="All IDs in 'depends_on' must reference existing documents.",
        severity="error",
        rationale="Broken links degrade graph integrity and cause cascading confusion.",
    ),
    ValidationRule(
        id="NO_CYCLES",
        name="No Cycles",
        description="The dependency graph must be acyclic (excluding logs).",
        severity="error",
        applies_to=["kernel", "strategy", "product", "atom"],
        rationale="Cycles create infinite loops in traversal and indicate confused dependencies.",
    ),
    ValidationRule(
        id="HIERARCHY_DIRECTION",
        name="Hierarchy Direction",
        description="Dependencies must flow downward: atom → product → strategy → kernel. "
                    "A document cannot depend on a type with higher rank.",
        severity="error",
        applies_to=["kernel", "strategy", "product", "atom"],
        rationale="The hierarchy enforces architectural layering. "
                  "Foundation (kernel) shouldn't depend on implementation (atom).",
    ),
    ValidationRule(
        id="NO_ORPHANS",
        name="No Orphans",
        description="All atoms must be depended upon by at least one other document.",
        severity="warning",
        applies_to=["atom"],
        rationale="Orphaned atoms suggest disconnected knowledge that may become stale.",
    ),
    ValidationRule(
        id="LOG_HAS_IMPACTS",
        name="Logs Have Impacts",
        description="Log documents should have non-empty 'impacts' field.",
        severity="warning",
        applies_to=["log"],
        rationale="A session that impacts nothing is probably missing attribution.",
    ),
    ValidationRule(
        id="VALID_STATUS_FOR_TYPE",
        name="Valid Status for Type",
        description="Document status must be valid for its type.",
        severity="error",
        rationale="Different types have different lifecycles (e.g., 'rejected' only for strategy).",
    ),
]

# ============================================================
# STATUS TRANSITIONS
# ============================================================

@dataclass
class StatusTransition:
    """Valid status transitions for document lifecycle."""
    from_status: str
    to_status: str
    allowed_types: List[str]
    description: str

STATUS_TRANSITIONS: List[StatusTransition] = [
    StatusTransition("draft", "active", ["kernel", "strategy", "product", "atom"],
                     "Document is approved and becomes current truth"),
    StatusTransition("draft", "rejected", ["strategy"],
                     "Proposal was considered but not approved"),
    StatusTransition("active", "deprecated", ["kernel", "strategy", "product", "atom"],
                     "Document is superseded but retained for reference"),
    StatusTransition("active", "archived", ["log"],
                     "Log is consolidated into decision history"),
    StatusTransition("auto-generated", "active", ["log"],
                     "Auto-generated log is enriched by human"),
    StatusTransition("draft", "complete", ["atom"],
                     "Review or analysis document is finished"),
]

# ============================================================
# CONCEPT VOCABULARY
# ============================================================

@dataclass
class ConceptDefinition:
    """Standard concept for tagging documents."""
    name: str
    covers: str
    avoid_using: List[str]

CONCEPT_VOCABULARY: List[ConceptDefinition] = [
    ConceptDefinition("auth", "Authentication, authorization, login, identity, OAuth, JWT",
                      ["authentication", "login", "identity", "oauth"]),
    ConceptDefinition("api", "Endpoints, REST, GraphQL, routes, controllers",
                      ["endpoints", "routes", "rest", "graphql"]),
    ConceptDefinition("db", "Database, storage, SQL, queries, migrations",
                      ["database", "storage", "sql", "postgres"]),
    ConceptDefinition("ui", "Frontend, components, CSS, styling, layout",
                      ["frontend", "components", "styling", "css"]),
    ConceptDefinition("schema", "Data models, types, validation, structure",
                      ["models", "types", "validation", "data-model"]),
    ConceptDefinition("devops", "CI/CD, deployment, hosting, Docker, infrastructure",
                      ["deployment", "ci", "infrastructure", "docker"]),
    ConceptDefinition("testing", "Unit tests, integration tests, QA, test coverage",
                      ["tests", "qa", "test", "unit-tests"]),
    ConceptDefinition("perf", "Performance, optimization, caching, speed",
                      ["performance", "optimization", "speed", "caching"]),
    ConceptDefinition("security", "Vulnerabilities, encryption, access control, secrets",
                      ["vulnerabilities", "encryption", "secrets"]),
    ConceptDefinition("docs", "Documentation, guides, references, READMEs",
                      ["documentation", "guides", "readme"]),
    ConceptDefinition("cleanup", "Refactoring, dead code removal, organization", []),
    ConceptDefinition("config", "Configuration, settings, environment variables", []),
    ConceptDefinition("workflow", "Process changes, rituals, automation", []),
]
```

### 2.3 Generated Documentation

From `ontology.py`, we generate `ontology_spec.md`:

```bash
python3 ontos.py docs --generate-spec
```

**Output: `docs/reference/ontology_spec.md`**

```markdown
---
id: ontology_spec
type: kernel
status: active
depends_on: [mission]
---

# Ontos Ontology Specification

> **⚠️ GENERATED FILE — DO NOT EDIT DIRECTLY**
>
> This document is auto-generated from `ontology.py`.
> To modify ontology rules, edit `ontology.py` and regenerate.
>
> Last generated: 2026-01-11T14:30:00Z
> Source: .ontos/scripts/ontos/core/ontology.py

---

## 1. Document Types

The Ontos ontology defines five document types arranged in a hierarchy.
Dependencies flow **downward** (atom → product → strategy → kernel).

| Type | Rank | Description | Can Depend On |
|------|------|-------------|---------------|
| **kernel** | 0 | Foundational principles — mission, values, core identity. Rarely changes. | (none) |
| **strategy** | 1 | Goals, direction, roadmap — business and product decisions. | kernel |
| **product** | 2 | User-facing specifications — features, requirements, user flows. | kernel, strategy |
| **atom** | 3 | Technical implementation details — specs, architecture, APIs. | kernel, strategy, product, atom |
| **log** | 4 | Session history — temporal records of work sessions. | (uses `impacts`, not `depends_on`) |

### 1.1 Type: kernel

**Description:** Foundational principles — mission, values, core identity. Rarely changes. The bedrock of the knowledge graph.

**Philosophy:** Kernels answer 'Who are we?' They ground all other documents. If a kernel changes, the entire project's direction may shift.

**Valid Statuses:** `active`, `draft`, `deprecated`

**Examples:** `mission`, `ontos_manual`, `ontos_agent_instructions`

### 1.2 Type: strategy
...

---

## 2. Frontmatter Schema

All Ontos documents require YAML frontmatter with the following fields:

### 2.1 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for this document. Use snake_case. Never change after creation. |
| `type` | enum | Document type: `kernel`, `strategy`, `product`, `atom`, `log` |
| `status` | enum | Current state: `active`, `draft`, `deprecated`, `archived`, `rejected`, `complete`, `auto-generated` |
| `depends_on` | list | List of document IDs this document references. (Not for logs) |

### 2.2 Optional Fields
...

---

## 3. Validation Rules

The following rules are enforced during context map generation:

| ID | Rule | Severity | Description |
|----|------|----------|-------------|
| `ID_UNICITY` | ID Unicity | error | Document IDs must be unique across the entire project. |
| `DEPENDENCY_EXISTS` | Dependency Exists | error | All IDs in 'depends_on' must reference existing documents. |
| `NO_CYCLES` | No Cycles | error | The dependency graph must be acyclic (excluding logs). |
| `HIERARCHY_DIRECTION` | Hierarchy Direction | error | Dependencies must flow downward: atom → product → strategy → kernel. |
| `NO_ORPHANS` | No Orphans | warning | All atoms must be depended upon by at least one other document. |
| `LOG_HAS_IMPACTS` | Logs Have Impacts | warning | Log documents should have non-empty 'impacts' field. |

---

## 4. Status Lifecycle

Valid status transitions by document type:

### 4.1 Standard Lifecycle (kernel, strategy, product, atom)

```
draft ──────► active ──────► deprecated
   │
   └──────► rejected (strategy only)
```

### 4.2 Log Lifecycle

```
auto-generated ──────► active ──────► archived
```

---

## 5. Concepts Vocabulary

Standard concepts for the `concepts` field. Use these instead of synonyms.

| Concept | Covers | Avoid Using |
|---------|--------|-------------|
| `auth` | Authentication, authorization, login, identity, OAuth, JWT | `authentication`, `login`, `identity` |
| `api` | Endpoints, REST, GraphQL, routes, controllers | `endpoints`, `routes`, `rest` |
...
```

### 2.4 Enforcement Integration

The validation engine reads directly from `ontology.py`:

```python
# ontos_generate_context_map.py (simplified)

from ontos.core.ontology import (
    TYPE_DEFINITIONS,
    FIELD_DEFINITIONS,
    VALIDATION_RULES,
)

def validate_document(frontmatter: dict) -> List[str]:
    errors = []
    doc_type = frontmatter.get('type')

    # Validate using TYPE_DEFINITIONS
    type_def = TYPE_DEFINITIONS.get(doc_type)
    if not type_def:
        errors.append(f"Unknown type: {doc_type}")
        return errors

    # Check hierarchy direction using type_def.can_depend_on
    for dep_id in frontmatter.get('depends_on', []):
        dep_type = get_type_for_id(dep_id)
        if dep_type not in type_def.can_depend_on and dep_type != doc_type:
            errors.append(f"[HIERARCHY] {doc_type} cannot depend on {dep_type}")

    # Check valid status using type_def.valid_statuses
    status = frontmatter.get('status')
    if status not in type_def.valid_statuses:
        errors.append(f"[STATUS] '{status}' not valid for type '{doc_type}'")

    return errors
```

**Key Point:** No more scattered validation logic. All rules are in `ontology.py`.

---

## Part 3: Benefits

### 3.1 Single Source of Truth

| Before | After |
|--------|-------|
| Types defined in 4 files | Types defined in 1 file (ontology.py) |
| Rules scattered in code | Rules declared in 1 place |
| Docs may contradict code | Docs generated from code |

### 3.2 No Drift

```
Edit ontology.py
      │
      ├──► Regenerate ontology_spec.md (automatic)
      │
      └──► Validation uses new rules (automatic)
```

Manual and Agent Instructions reference ontology_spec.md. They never redefine rules.

### 3.3 Rich Metadata

Each definition includes:
- **Description** — What it is
- **Philosophy** — Why it exists
- **Examples** — How it's used
- **Rationale** — Why the rule matters

This is documentation and code in one.

### 3.4 Better Agent Experience

Agents can:
1. Load `ontology_spec.md` for complete rules (generated, always accurate)
2. Load `Ontos_Agent_Instructions.md` for commands (references spec)
3. Trust that docs match enforcement

### 3.5 Extensibility

Adding a new type or field:
1. Add to `ontology.py`
2. Regenerate docs
3. Done — validation automatically enforces it

---

## Part 4: Technical Requirements

### 4.1 New Files

| File | Purpose | Type |
|------|---------|------|
| `.ontos/scripts/ontos/core/ontology.py` | THE source of truth | Code |
| `docs/reference/ontology_spec.md` | Generated specification | Kernel doc |
| `.ontos/scripts/ontos_generate_docs.py` | Doc generator | Tool |

### 4.2 Modified Files

| File | Changes |
|------|---------|
| `schema.py` | Import from ontology.py OR merge into ontology.py |
| `ontos_generate_context_map.py` | Use ontology.py for validation |
| `ontos_maintain.py` | Use ontology.py for validation |
| `Ontos_Manual.md` | Reference ontology_spec.md, remove definitions |
| `Ontos_Agent_Instructions.md` | Reference ontology_spec.md, remove definitions |
| `schema.md` | Deprecate or merge into ontology_spec.md |

### 4.3 New CLI Commands

```bash
# Generate ontology_spec.md from ontology.py
python3 ontos.py docs --generate-spec

# Verify generated docs are current
python3 ontos.py docs --check

# Show ontology summary (for agents)
python3 ontos.py ontology --types
python3 ontos.py ontology --fields
python3 ontos.py ontology --rules

# Obsidian integration
python3 ontos.py docs --generate-links    # Add/update Related sections with wikilinks
python3 ontos.py docs --obsidian-init     # Create .obsidian/ vault config
python3 ontos.py docs --check-obsidian    # Validate Obsidian compatibility
```

### 4.4 CI Integration

```yaml
# .github/workflows/validate.yml
- name: Check ontology docs are current
  run: |
    python3 ontos.py docs --generate-spec --output /tmp/ontology_spec.md
    diff docs/reference/ontology_spec.md /tmp/ontology_spec.md
```

### 4.5 Data Structures

```python
@dataclass
class TypeDefinition:
    name: str
    rank: int
    description: str
    can_depend_on: List[str]
    valid_statuses: List[str]
    uses_impacts: bool = False
    examples: List[str] = None
    philosophy: str = ""

@dataclass
class FieldDefinition:
    name: str
    type: str
    required: bool
    description: str
    default: Optional[str] = None
    validation_pattern: Optional[str] = None
    valid_values: Optional[List[str]] = None
    applies_to: Optional[List[str]] = None
    examples: List[str] = None

@dataclass
class ValidationRule:
    id: str
    name: str
    description: str
    severity: str
    applies_to: Optional[List[str]] = None
    rationale: str = ""

@dataclass
class StatusTransition:
    from_status: str
    to_status: str
    allowed_types: List[str]
    description: str

@dataclass
class ConceptDefinition:
    name: str
    covers: str
    avoid_using: List[str]
```

---

## Part 5: Migration Path

### Phase 1: Create ontology.py

1. Create `ontology.py` with all definitions
2. Add doc generator command
3. Generate initial `ontology_spec.md`
4. Validate: generated spec matches current docs

### Phase 2: Integrate Validation

1. Refactor validation code to use `ontology.py`
2. Remove hardcoded rules from validation scripts
3. Verify all tests pass
4. Verify validation behavior unchanged

### Phase 3: Refactor Applied Docs

1. Update `Ontos_Manual.md` to reference spec
2. Update `Ontos_Agent_Instructions.md` to reference spec
3. Deprecate standalone `schema.md`
4. Update `depends_on` frontmatter

### Phase 4: CI/CD Integration

1. Add doc freshness check to CI
2. Add pre-commit hook for doc generation
3. Document the new workflow

### Phase 5: Obsidian Integration (Optional)

1. Run `python3 ontos.py docs --obsidian-init` to create vault config
2. Run `python3 ontos.py docs --generate-links` to add Related sections
3. Add `.obsidian/` to `.gitignore` (user-specific settings)
4. Open `.ontos-internal/` as Obsidian vault
5. Verify:
   - Graph view shows correct hierarchy (kernel at center)
   - Backlinks panel shows reverse dependencies
   - Properties panel displays frontmatter correctly

---

## Part 6: Open Questions for Review

### Q1: Should philosophy content be in code?

**Option A:** Philosophy in ontology.py (proposed)
- Pro: Single source, rich context
- Con: Code becomes prose-heavy

**Option B:** Philosophy in v2_strategy.md, code is minimal
- Pro: Code stays lean
- Con: Philosophy disconnected from enforcement

**Recommendation:** Option A — the philosophy IS the specification's rationale.

### Q2: How to handle Common_Concepts.md?

**Option A:** Concepts in ontology.py, file is generated
- Pro: Truly single source
- Con: Another generated file to maintain

**Option B:** Keep Common_Concepts.md separate
- Pro: Simple, already works
- Con: Vocabulary not in code

**Recommendation:** Option A for v3.0, but low priority.

### Q3: What about schema.py?

**Option A:** Merge into ontology.py
- Pro: One file for all ontology
- Con: Large file

**Option B:** Keep separate, import from ontology.py
- Pro: Separation of concerns
- Con: Two files to understand

**Recommendation:** Option B — schema.py handles schema versioning, imports types from ontology.py.

### Q4: Generated docs in git or gitignore?

**Option A:** Commit generated ontology_spec.md
- Pro: Visible in repo, agents can read without generating
- Con: Must regenerate before commit

**Option B:** Gitignore, generate on demand
- Pro: No sync concerns
- Con: Agents need generation step

**Recommendation:** Option A — commit the generated file, CI validates freshness.

### Q5: How strict on Manual/Agent Instructions references?

**Option A:** Must use exact phrases like "See [Ontology Specification §1]"
- Pro: Traceable references
- Con: Verbose, may hurt readability

**Option B:** Informal references, linting for duplicate definitions
- Pro: Natural prose
- Con: Harder to enforce

**Recommendation:** Option A for normative content, Option B for examples.

### Q6: Should concepts map to Obsidian tags?

**Option A:** Map `concepts` → Obsidian `tags` with prefix
- Example: `concepts: [auth, api]` → `tags: [concept/auth, concept/api]`
- Pro: Graph clusters by concept, enables tag-based navigation
- Con: Duplicates data between frontmatter fields

**Option B:** Keep separate, let users configure
- Pro: No data duplication
- Con: Requires manual Dataview queries for concept-based filtering

**Recommendation:** Option A — the clustering benefit in graph view outweighs duplication concern.

---

## Part 7: Risk Analysis

### Risk 1: Over-Engineering

**Concern:** This adds complexity to solve a problem that may not be severe.

**Mitigation:** Start with core types and fields only. Add advanced features (status transitions, concepts) later.

**Acceptance Criteria:** If this doesn't reduce maintenance burden within 3 months, reconsider.

### Risk 2: Generated Docs Quality

**Concern:** Generated docs may be sterile, lack human warmth.

**Mitigation:** Rich docstrings in ontology.py. Philosophy field. Post-generation review.

**Acceptance Criteria:** Generated spec must be readable without code access.

### Risk 3: Learning Curve

**Concern:** Contributors must now understand ontology.py structure.

**Mitigation:** Clear docstrings. Example changes documented. The structure is self-documenting.

**Acceptance Criteria:** New contributor can add a field in <10 minutes.

### Risk 4: Tooling Dependency

**Concern:** Doc generation becomes required step.

**Mitigation:** CI enforces freshness. Pre-commit hook auto-generates.

**Acceptance Criteria:** Developers never manually edit ontology_spec.md.

---

## Part 8: Success Criteria

### Immediate (v2.9.6)

1. Single source of truth for ontology
2. Generated docs match enforcement
3. Manual and Agent Instructions reference spec
4. No duplicate definitions

### Medium-term (v2.9.7+)

1. Adding new type/field is edit-one-file
2. Validation errors reference spec sections
3. Agents can query ontology programmatically
4. Documents viewable in Obsidian with working graph view
5. Backlinks correctly show reverse dependencies
6. Dataview queries return correct results on frontmatter

### Long-term (v3.0+)

1. JSON Schema generated for MCP
2. TypeScript types generated for tooling
3. Cross-project ontology federation

---

## Part 9: Summary

### The Proposal

1. **Create `ontology.py`** — Single source of truth for all ontology definitions
2. **Generate `ontology_spec.md`** — Human-readable spec from code
3. **Refactor applied docs** — Reference spec, never redefine
4. **Unify validation** — All enforcement reads from ontology.py

### Why This Matters

- **Philosophy alignment:** Ontos finally follows its own principles
- **Maintainability:** One edit, everything updates
- **Correctness:** Docs can't contradict enforcement
- **Agent experience:** Reliable, accurate context

### The Core Insight

> The ontology specification and its enforcement mechanism should be the same artifact.

Code is documentation. Documentation is code. They are one.

---

## Part 10: Obsidian Compatibility

### 10.1 Design Goals

Ontos documents should be viewable in Obsidian as a vault without modification:
- `.ontos-internal/` is the vault root
- Graph view visualizes the dependency hierarchy
- Backlinks show reverse dependencies
- Dataview/Properties queries work on frontmatter

**Reference:** See `proposals/v2.9.6/Obsidian_Compatibility` for complete technical specification.

### 10.2 File Format Compliance

Ontos already generates compliant files, but validation should enforce:

| Requirement | Ontos Status | Enforcement |
|-------------|--------------|-------------|
| UTF-8 encoding | ✅ Default | Validate on write |
| `.md` extension | ✅ Required | Schema validation |
| LF line endings | ⚠️ OS-dependent | Normalize on write |
| Forbidden chars in ID | ✅ `[a-z][a-z0-9_]*` | Regex validation |
| Frontmatter at top | ✅ Required | Schema validation |
| Spaces not tabs | ✅ Default | YAML writer config |

### 10.3 Wikilink Generation Strategy

The `depends_on` field remains the source of truth (document IDs), but for Obsidian graph visualization, we generate a "Related" section with wikilinks:

**Source (frontmatter):**
```yaml
depends_on: [mission, v2_strategy]
```

**Generated section (at document bottom):**
```markdown
---
## Related

**Depends on:** [[mission]], [[v2_strategy]]
**Depended by:** [[auth_flow]], [[api_spec]]
```

**Why this approach:**
- `depends_on` stays as IDs (machine-readable, validated)
- Wikilinks in body create graph edges (Obsidian requirement)
- Frontmatter wikilinks require quotes and are less reliable for graph

Generated by: `python3 ontos.py docs --generate-links`

### 10.4 ontology.py Extensions

Add Obsidian configuration to the ontology definition:

```python
@dataclass
class ObsidianConfig:
    """Configuration for Obsidian vault compatibility."""
    vault_root: str = ".ontos-internal"
    generate_related_section: bool = True
    link_format: Literal["wikilink", "markdown"] = "wikilink"
    normalize_line_endings: bool = True  # Force LF

    # Frontmatter property mapping
    property_mappings: Dict[str, str] = field(default_factory=lambda: {
        "concepts": "tags",  # Map concepts to Obsidian tags
    })

@dataclass
class FieldDefinition:
    # ... existing fields ...
    obsidian_property_type: Optional[str] = None  # text, list, number, checkbox, date
    obsidian_queryable: bool = True  # Include in Dataview index
```

### 10.5 Vault Initialization

Running `python3 ontos.py docs --obsidian-init` creates:

```
.ontos-internal/
├── .obsidian/
│   ├── app.json              # useMarkdownLinks: false
│   ├── appearance.json       # Minimal theme config
│   └── graph.json            # Default graph settings
└── (existing docs...)
```

The `.obsidian/` folder is gitignored by default (user-specific settings).

### 10.6 Graph View Optimization

For optimal graph visualization:

1. **Hub documents (MOC pattern):**
   - `Ontos_Context_Map.md` links to all documents
   - Kernel docs form central nodes

2. **Hierarchical tags:**
   - Map `type` to tag: `ontos/kernel`, `ontos/strategy`, etc.
   - Map `concepts` to nested tags: `concept/auth`, `concept/api`

3. **Backlinks panel:**
   - Shows reverse `depends_on` (what depends on this doc)
   - Powered by the "Related" section wikilinks

---

## Appendix A: File Comparison

### Before

```
.ontos/scripts/ontos/core/schema.py     # Field definitions (code)
.ontos-internal/atom/schema.md          # Field definitions (docs)
docs/reference/Ontos_Manual.md          # Type definitions (docs)
docs/reference/Ontos_Agent_Instructions.md  # Type definitions (docs)
.ontos-internal/strategy/v2_strategy.md # Philosophy (docs)
docs/reference/Common_Concepts.md       # Concepts (docs)
```

### After

```
.ontos/scripts/ontos/core/ontology.py   # ALL definitions (code, THE source)
.ontos/scripts/ontos/core/schema.py     # Schema versioning (imports from ontology.py)
docs/reference/ontology_spec.md         # Generated from ontology.py
docs/reference/Ontos_Manual.md          # References ontology_spec.md
docs/reference/Ontos_Agent_Instructions.md  # References ontology_spec.md
.ontos-internal/strategy/v2_strategy.md # Philosophy (keeps "why", refs spec for "what")
docs/reference/Common_Concepts.md       # Could be generated, or kept separate
```

---

## Appendix B: Example Reference Pattern

### In Ontos_Manual.md (After Refactoring)

```markdown
## 1. Core Concepts

### Document Types

> **Authoritative specification:** [Ontology Specification §1](ontology_spec.md#1-document-types)

Ontos organizes knowledge into five document types. Here's how to choose:

**When to use each type:**

- **kernel** — Ask: "If this changes, does the whole project change?" Yes → kernel
- **strategy** — Business decisions, roadmaps, goals
- **product** — User-facing features, requirements
- **atom** — Technical specs, implementation details
- **log** — Session records (auto-created by Archive Ontos)

For complete field requirements, valid statuses, and dependency rules, see the [Ontology Specification](ontology_spec.md).
```

### In Ontos_Agent_Instructions.md (After Refactoring)

```markdown
## Type Quick Reference

> **Complete definitions:** [Ontology Specification §1](ontology_spec.md#1-document-types)

| Type | Rank | Command |
|------|------|---------|
| kernel | 0 | `type: kernel` — depends on nothing |
| strategy | 1 | `type: strategy` — depends on kernel |
| product | 2 | `type: product` — depends on kernel, strategy |
| atom | 3 | `type: atom` — depends on kernel, strategy, product, atom |
| log | 4 | `type: log` — uses `impacts`, not `depends_on` |

For full field specifications, see Ontology Specification.
```

---

*End of Research Document*

*Prepared for LLM Review Board consideration.*
