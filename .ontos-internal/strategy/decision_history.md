---
id: decision_history
type: strategy
status: active
depends_on: [mission]
---

# Decision History

Permanent ledger of project decisions and their archival locations.

## For Agents

1. **Search** this file to understand *why* a decision was made
2. **Retrieve** full context by reading the Archive Path if necessary (see Historical Recall in Agent Instructions)

## For Humans

Before archiving a log, record its key decision here. This ensures institutional knowledge survives consolidation.

---

## History Ledger

| Date | Slug | Event | Decision / Outcome | Impacted | Archive Path |
|:-----|:-----|:------|:-------------------|:---------|:-------------|
| 2025-12-13 | documentation-compaction | chore | Consolidated 5 guides into single Manual. 68% markdown reduction. | schema, v2_strategy | `.ontos-internal/archive/2025-12-13_documentation-compaction.md` |
| 2025-12-12 | blocking-hook | feature | Pre-push hook blocks until session archived. Rejected advisory-only. | v2_architecture | `.ontos-internal/archive/2025-12-12_blocking-hook-implementation.md` |
| 2025-12-12 | configurable-workflow | feature | Added ENFORCE_ARCHIVE_BEFORE_PUSH and REQUIRE_SOURCE_IN_LOGS config options. | v2_architecture | `.ontos-internal/archive/2025-12-12_configurable-workflow.md` |
| 2025-12-12 | v2-implementation | feature | Completed Dual Ontology implementation (Space + Time separation). | schema, v2_strategy, mission | `.ontos-internal/archive/2025-12-12_v2-implementation-complete.md` |

---

## Consolidation Log

| Date | Sessions Reviewed | Sessions Archived | Performed By |
|:-----|:------------------|:------------------|:-------------|
| 2025-12-13 | 8 | 8 | Johnny (initial setup) |
