---
id: schema
type: atom
status: active
depends_on: [v2_strategy]
---

# Project Ontos: Schema Specification

## 1. Strategy Link
Defines data structures for the Ontos protocol as specified in [v2_strategy](../strategy/v2_strategy.md).

## 2. Common Fields (All Types)
| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | Unique identifier (snake_case) |
| `type` | enum | Yes | `kernel`, `strategy`, `product`, `atom`, `log` |
| `status` | enum | Yes | `active`, `draft`, `deprecated`, `archived`, `rejected`, `complete` |
| `depends_on` | list | Yes | List of `id`s this document references |

## 3. Type-Specific Fields

### 3.1 Type: `log`
| Field | Type | Required | Description |
|---|---|---|---|
| `event_type` | enum | Yes | `feature`, `fix`, `refactor`, `exploration`, `chore`, `decision` |
| `concepts` | list | No | Abstract concepts discussed (e.g., `v2-migration`) |
| `impacts` | list | No | `id`s of documents modified in this session |

### 3.2 Type: `strategy` (when status: rejected)
| Field | Type | Required | Description |
|---|---|---|---|
| `rejected_date` | string | Recommended | Date of rejection (YYYY-MM-DD) |
| `rejected_reason` | string | Required | Explanation of why proposal was rejected |
| `rejected_by` | string | Optional | Who made the rejection decision |
| `revisit_when` | string | Optional | Conditions under which to reconsider |

## 4. Validation Rules
1.  **ID Unicity:** IDs must be unique across the entire project.
2.  **Dependency Existence:** All IDs in `depends_on` must exist.
3.  **No Cycles:** The dependency graph (excluding logs) must be acyclic.
4.  **No Orphans:** All documents (except allowed types) must have a dependent.
5.  **Type-Status Matrix:** Only valid (type, status) combinations are allowed (v2.6+).

