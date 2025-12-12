<!--
Ontos Context Map
Generated: 2025-12-12 08:21:36 UTC
Mode: Contributor
Scanned: .ontos-internal
-->
# Ontos Context Map
Generated on: 2025-12-12 17:21:36
Scanned Directory: `/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal`

## 1. Hierarchy Tree
### KERNEL
- **mission** (mission.md) ~377 tokens
  - Status: active
  - Depends On: None

### STRATEGY
- **v2_strategy** (v2_strategy.md) ~2,600 tokens
  - Status: active
  - Depends On: mission

### ATOM
- **schema** (schema.md) ~306 tokens
  - Status: draft
  - Depends On: v2_architecture
- **self_dev_protocol** (self_development_protocol.md) ~330 tokens
  - Status: draft
  - Depends On: v2_architecture
- **self_dev_protocol_spec** (self_development_protocol_spec.md) ~10,700 tokens
  - Status: active
  - Depends On: self_dev_protocol
- **v2_architecture** (v2_technical_architecture.md) ~6,800 tokens
  - Status: draft
  - Depends On: v2_strategy
- **v2_implementation_plan** (v2_implementation_plan.md) ~22,100 tokens
  - Status: draft
  - Depends On: v2_architecture

### LOG
- **log_20251212_pr10_review_and_fixes** (2025-12-12_pr10-review-and-fixes.md) ~478 tokens
  - Status: archived
  - Impacts: schema, v2_architecture, self_dev_protocol
- **log_20251212_v2_planning** (2025-12-12_v2-planning.md) ~491 tokens
  - Status: archived
  - Impacts: mission, v2_strategy, v2_roadmap, v2_architecture, schema, self_dev_protocol
- **log_20251212_v2_strategy_architecture_rewrite** (2025-12-12_v2-strategy-architecture-rewrite.md) ~580 tokens
  - Status: archived
  - Impacts: v2_strategy, v2_architecture


## 2. Recent Timeline
- **2025-12-12** [refactor] **V2 Strategy Architecture Rewrite** (`log_20251212_v2_strategy_architecture_rewrite`)
  - Impacted: `v2_strategy`, `v2_architecture`
  - Concepts: v2-strategy, dual-ontology, architecture, documentation-consolidation
- **2025-12-12** [implementation] **V2 Planning** (`log_20251212_v2_planning`)
  - Impacted: `mission`, `v2_strategy`, `v2_roadmap`, `v2_architecture`, `schema`, `self_dev_protocol`
  - Concepts: v2-migration, self-development, contributor-mode, dual-ontology
- **2025-12-12** [implementation] **Pr10 Review And Fixes** (`log_20251212_pr10_review_and_fixes`)
  - Impacted: `schema`, `v2_architecture`, `self_dev_protocol`
  - Concepts: pr-review, log-type, type-hierarchy, version-bump, self-development

## 3. Dependency Audit
- [INVALID VALUE] **log_20251212_v2_planning** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-12_v2-planning.md) has invalid event_type: 'implementation'
  Fix: Use one of: chore, exploration, feature, fix, refactor
- [INVALID VALUE] **log_20251212_pr10_review_and_fixes** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-12_pr10-review-and-fixes.md) has invalid event_type: 'implementation'
  Fix: Use one of: chore, exploration, feature, fix, refactor
- [INFO] **log_20251212_v2_planning** references deleted document `v2_roadmap` (archived log, no action needed)

## 4. Index
| ID | Filename | Type |
|---|---|---|
| log_20251212_pr10_review_and_fixes | [2025-12-12_pr10-review-and-fixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-12_pr10-review-and-fixes.md) | log |
| log_20251212_v2_planning | [2025-12-12_v2-planning.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-12_v2-planning.md) | log |
| log_20251212_v2_strategy_architecture_rewrite | [2025-12-12_v2-strategy-architecture-rewrite.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-12_v2-strategy-architecture-rewrite.md) | log |
| mission | [mission.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/mission.md) | kernel |
| schema | [schema.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/schema.md) | atom |
| self_dev_protocol | [self_development_protocol.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/self_development_protocol.md) | atom |
| self_dev_protocol_spec | [self_development_protocol_spec.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/self_development_protocol_spec.md) | atom |
| v2_architecture | [v2_technical_architecture.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/v2_technical_architecture.md) | atom |
| v2_implementation_plan | [v2_implementation_plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/v2_implementation_plan.md) | atom |
| v2_strategy | [v2_strategy.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2_strategy.md) | strategy |
