<!--
Ontos Context Map
Generated: 2025-12-12 12:16:58 UTC
Mode: Contributor
Scanned: .ontos-internal
-->
# Ontos Context Map
Generated on: 2025-12-12 21:16:58
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
- **log_20251212_blocking_hook_implementation** (2025-12-12_blocking-hook-implementation.md) ~444 tokens
  - Status: active
  - Impacts: v2_architecture, self_dev_protocol
- **log_20251212_configurable_workflow** (2025-12-12_configurable-workflow.md) ~440 tokens
  - Status: active
  - Impacts: v2_architecture, self_dev_protocol
- **log_20251212_maintenance_v2_release** (2025-12-12_maintenance-v2-release.md) ~329 tokens
  - Status: active
  - Impacts: v2_architecture, schema
- **log_20251212_pr10_review_and_fixes** (2025-12-12_pr10-review-and-fixes.md) ~472 tokens
  - Status: archived
  - Impacts: schema, v2_architecture, self_dev_protocol
- **log_20251212_pr11_review_fixes** (2025-12-12_pr11-review-fixes.md) ~427 tokens
  - Status: active
  - Impacts: v2_architecture, schema
- **log_20251212_v2_implementation_complete** (2025-12-12_v2-implementation-complete.md) ~529 tokens
  - Status: active
  - Impacts: v2_implementation_plan, v2_architecture, schema, self_dev_protocol, mission, v2_strategy
- **log_20251212_v2_planning** (2025-12-12_v2-planning.md) ~485 tokens
  - Status: archived
  - Impacts: mission, v2_strategy, v2_roadmap, v2_architecture, schema, self_dev_protocol
- **log_20251212_v2_strategy_architecture_rewrite** (2025-12-12_v2-strategy-architecture-rewrite.md) ~580 tokens
  - Status: archived
  - Impacts: v2_strategy, v2_architecture


## 2. Recent Timeline
- **2025-12-12** [refactor] **V2 Strategy Architecture Rewrite** (`log_20251212_v2_strategy_architecture_rewrite`)
  - Impacted: `v2_strategy`, `v2_architecture`
  - Concepts: v2-strategy, dual-ontology, architecture, documentation-consolidation
- **2025-12-12** [feature] **V2 Planning** (`log_20251212_v2_planning`)
  - Impacted: `mission`, `v2_strategy`, `v2_roadmap`, `v2_architecture`, `schema`, `self_dev_protocol`
  - Concepts: v2-migration, self-development, contributor-mode, dual-ontology
- **2025-12-12** [feature] **V2 Implementation Complete** (`log_20251212_v2_implementation_complete`)
  - Impacted: `v2_implementation_plan`, `v2_architecture`, `schema`, `self_dev_protocol`, `mission`, `v2_strategy`
  - Concepts: v2-implementation, dual-ontology, visibility, intelligence
- **2025-12-12** [fix] **Pr11 Review Fixes** (`log_20251212_pr11_review_fixes`)
  - Impacted: `v2_architecture`, `schema`
  - Concepts: pr-review, validation, source-required, strict-mode
- **2025-12-12** [chore] **Pr10 Review And Fixes** (`log_20251212_pr10_review_and_fixes`)
  - Impacted: `schema`, `v2_architecture`, `self_dev_protocol`
  - Concepts: pr-review, log-type, type-hierarchy, version-bump, self-development
- **2025-12-12** [chore] **Maintenance V2 Release** (`log_20251212_maintenance_v2_release`)
  - Impacted: `v2_architecture`, `schema`
  - Concepts: maintenance, version-bump, v2-release
- **2025-12-12** [feature] **Configurable Workflow** (`log_20251212_configurable_workflow`)
  - Impacted: `v2_architecture`, `self_dev_protocol`
  - Concepts: configuration, workflow-enforcement, opt-out, relaxed-mode
- **2025-12-12** [feature] **Blocking Hook Implementation** (`log_20251212_blocking_hook_implementation`)
  - Impacted: `v2_architecture`, `self_dev_protocol`
  - Concepts: pre-push-hook, blocking, marker-file, context-enforcement

## 3. Dependency Audit
- [INFO] **log_20251212_v2_planning** references deleted document `v2_roadmap` (archived log, no action needed)

## 4. Index
| ID | Filename | Type |
|---|---|---|
| log_20251212_blocking_hook_implementation | [2025-12-12_blocking-hook-implementation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-12_blocking-hook-implementation.md) | log |
| log_20251212_configurable_workflow | [2025-12-12_configurable-workflow.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-12_configurable-workflow.md) | log |
| log_20251212_maintenance_v2_release | [2025-12-12_maintenance-v2-release.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-12_maintenance-v2-release.md) | log |
| log_20251212_pr10_review_and_fixes | [2025-12-12_pr10-review-and-fixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-12_pr10-review-and-fixes.md) | log |
| log_20251212_pr11_review_fixes | [2025-12-12_pr11-review-fixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-12_pr11-review-fixes.md) | log |
| log_20251212_v2_implementation_complete | [2025-12-12_v2-implementation-complete.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-12_v2-implementation-complete.md) | log |
| log_20251212_v2_planning | [2025-12-12_v2-planning.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-12_v2-planning.md) | log |
| log_20251212_v2_strategy_architecture_rewrite | [2025-12-12_v2-strategy-architecture-rewrite.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-12_v2-strategy-architecture-rewrite.md) | log |
| mission | [mission.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/mission.md) | kernel |
| schema | [schema.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/schema.md) | atom |
| self_dev_protocol | [self_development_protocol.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/self_development_protocol.md) | atom |
| self_dev_protocol_spec | [self_development_protocol_spec.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/self_development_protocol_spec.md) | atom |
| v2_architecture | [v2_technical_architecture.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/v2_technical_architecture.md) | atom |
| v2_implementation_plan | [v2_implementation_plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/v2_implementation_plan.md) | atom |
| v2_strategy | [v2_strategy.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2_strategy.md) | strategy |
