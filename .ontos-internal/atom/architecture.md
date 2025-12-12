---
id: v2_architecture
type: atom
status: draft
depends_on: [v2_roadmap]
---

# Project Ontos: v2 Architecture

*Documented: December 2025*

## 1. Roadmap Link
Technical implementation of [v2_roadmap](v2_roadmap.md).

## 2. Core Concept: Dual Ontology

Ontos v2 introduces a formal distinction between **Space** (Documentation) and **Time** (Log).

### 2.1 Space (The Graph)
The current state of the project.
-   **Types:** `kernel`, `strategy`, `product`, `atom`
-   **Structure:** DAG (Directed Acyclic Graph)
-   **Validation:** Strict dependency checking

### 2.2 Time (The Log)
The history of how we got here.
-   **Types:** `log`
-   **Structure:** Linear / Timeline
-   **Validation:** Loose (mostly chronological)

## 3. Data Structures

### 3.1 Document Frontmatter (Space)
```yaml
id: [unique_id]
type: [kernel|strategy|product|atom]
status: [active|draft|deprecated]
depends_on: [list_of_ids]
```

### 3.2 Log Frontmatter (Time - NEW)
```yaml
id: log_YYYYMMDD_slug
type: log
event_type: [exploration|decision|implementation|chore]
status: archived
depends_on: []
concepts: [list_of_concepts_modified]
impacts: [list_of_doc_ids_changed]
```

## 4. Context Map Generation
The context map generator will be updated to produce two distinct sections:
1.  **Hierarchy Tree:** Nested view of the `Space` graph.
2.  **Timeline:** Chronological view of `type: log` entries, showing what changed.
