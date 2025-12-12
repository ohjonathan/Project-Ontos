---
id: schema
type: atom
status: draft
depends_on: [v2_architecture]
---

# Project Ontos: Schema Specification

## 1. Architecture Link
Defines data structures for [v2_architecture](architecture.md).

## 2. Common Fields (All Types)
| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | Unique identifier (snake_case) |
| `type` | enum | Yes | `kernel`, `strategy`, `product`, `atom`, `log` |
| `status` | enum | Yes | `active`, `draft`, `deprecated`, `archived` |
| `depends_on` | list | Yes | List of `id`s this document references |

## 3. Type-Specific Fields

### 3.1 Type: `log`
| Field | Type | Required | Description |
|---|---|---|---|
| `event_type` | enum | Yes | `exploration`, `decision`, `implementation`, `chore` |
| `concepts` | list | No | Abstract concepts discussed (e.g., `v2-migration`) |
| `impacts` | list | No | `id`s of documents modified in this session |

## 4. Validation Rules
1.  **ID Unicity:** IDs must be unique across the entire project.
2.  **Dependency Existence:** All IDs in `depends_on` must exist.
3.  **No Cycles:** The dependency graph (excluding logs) must be acyclic.
4.  **No Orphans:** All documents (except allowed types) must have a dependent.
