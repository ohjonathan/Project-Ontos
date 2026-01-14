---
type: generated
generator: ontos_generate_context_map
generated: "<TIMESTAMP>"
mode: Contributor
scanned: .ontos-internal
---

> **Note for users:** This context map documents Project Ontos's own development.
> When you run `ontos map` in your project, this file will be overwritten with your project's context.

# Ontos Context Map
Generated on: <TIMESTAMP>
Scanned Directory: `<FIXTURE_ROOT>/.ontos-internal, docs`

## 1. Hierarchy Tree
### KERNEL
- **constitution** [L2] (constitution.md) ~38 tokens
  - Status: active
  - Depends On: mission, philosophy
- **mission** [L2] (mission.md) ~33 tokens
  - Status: active
  - Depends On: None
- **philosophy** [L2] (philosophy.md) ~36 tokens
  - Status: active
  - Depends On: mission

### STRATEGY
- **api_design** [L2] (api_design.md) ~34 tokens
  - Status: active
  - Depends On: core_architecture
- **complete_feature** [L2] (complete_feature.md) ~36 tokens
  - Status: complete
  - Depends On: api_design
- **core_architecture** [L2] (core_architecture.md) ~37 tokens
  - Status: active
  - Depends On: mission
- **database_schema** [L2] (database_schema.md) ~35 tokens
  - Status: active
  - Depends On: core_architecture
- **deployment_strategy** [L2] (deployment_strategy.md) ~38 tokens
  - Status: active
  - Depends On: core_architecture
- **deprecated_idea** [L2] [deprecated] (deprecated_idea.md) ~43 tokens
  - Status: deprecated
  - Depends On: core_architecture
- **documentation_guide** [L2] (documentation_guide.md) ~35 tokens
  - Status: active
  - Depends On: mission
- **feature_a** [L2] [draft] (feature_a.md) ~33 tokens
  - Status: draft
  - Depends On: api_design
- **feature_b** [L2] (feature_b.md) ~33 tokens
  - Status: active
  - Depends On: api_design, security_model
- **security_model** [L2] (security_model.md) ~43 tokens
  - Status: active
  - Depends On: core_architecture, api_design
- **testing_plan** [L2] (testing_plan.md) ~37 tokens
  - Status: active
  - Depends On: api_design, database_schema

### ATOM
- **common_concepts** [L2] (common_concepts.md) ~42 tokens
  - Status: active
  - Depends On: mission
- **dual_mode_matrix** [L2] (dual_mode_matrix.md) ~36 tokens
  - Status: active
  - Depends On: core_architecture
- **medium_schema** [L2] (schema.md) ~33 tokens
  - Status: active
  - Depends On: database_schema
- **validation_rules** [L2] (validation_rules.md) ~34 tokens
  - Status: active
  - Depends On: medium_schema

### LOG
- **log_20250101_initial_setup** [L2] (2025-01-01_initial-setup.md) ~79 tokens
  - Status: active
  - Impacts: core_architecture
- **log_20250115_api_design** [L2] (2025-01-15_api-design.md) ~73 tokens
  - Status: active
  - Impacts: api_design, security_model
- **log_20250201_security** [L2] (2025-02-01_security-hardening.md) ~72 tokens
  - Status: active
  - Impacts: security_model
- **log_20250215_rejected** [L2] (2025-02-15_rejected-exploration.md) ~78 tokens
  - Status: active
  - Impacts: rejected_proposal
- **log_20250301_complete** [L2] (2025-03-01_feature-complete.md) ~68 tokens
  - Status: active
  - Impacts: complete_feature


## 2. Recent Timeline
- **2025-03-01** [feature] **Feature Complete** (`log_20250301_complete`)
  - Impacted: `complete_feature`
  - Concepts: release
- **2025-02-15** [exploration] **Rejected Exploration** (`log_20250215_rejected`)
  - Impacted: `rejected_proposal`
  - Concepts: graphql, api
- **2025-02-01** [feature] **Security Hardening** (`log_20250201_security`)
  - Impacted: `security_model`
  - Concepts: security, auth
- **2025-01-15** [feature] **Api Design** (`log_20250115_api_design`)
  - Impacted: `api_design`, `security_model`
  - Concepts: api, rest
- **2025-01-01** [feature] **Initial Setup** (`log_20250101_initial_setup`)
  - Impacted: `core_architecture`
  - Concepts: setup, architecture

## 3. Dependency Audit
- [BROKEN LINK] **log_20250215_rejected** (<FIXTURE_ROOT>/.ontos-internal/logs/2025-02-15_rejected-exploration.md) impacts non-existent document: `rejected_proposal`
  Fix: Create `rejected_proposal`, correct the reference, or archive this log
- [LINT] **feature_b**: Active document in proposals/. Graduate to strategy/.

## 4. Index
| ID | Filename | Type |
|---|---|---|
| api_design | [api_design.md](<FIXTURE_ROOT>/.ontos-internal/strategy/api_design.md) | strategy |
| common_concepts | [common_concepts.md](<FIXTURE_ROOT>/.ontos-internal/atom/common_concepts.md) | atom |
| complete_feature | [complete_feature.md](<FIXTURE_ROOT>/.ontos-internal/strategy/proposals/complete_feature.md) | strategy |
| constitution | [constitution.md](<FIXTURE_ROOT>/.ontos-internal/kernel/constitution.md) | kernel |
| core_architecture | [core_architecture.md](<FIXTURE_ROOT>/.ontos-internal/strategy/core_architecture.md) | strategy |
| database_schema | [database_schema.md](<FIXTURE_ROOT>/.ontos-internal/strategy/database_schema.md) | strategy |
| deployment_strategy | [deployment_strategy.md](<FIXTURE_ROOT>/.ontos-internal/strategy/deployment_strategy.md) | strategy |
| deprecated_idea | [deprecated_idea.md](<FIXTURE_ROOT>/.ontos-internal/strategy/proposals/deprecated_idea.md) | strategy |
| documentation_guide | [documentation_guide.md](<FIXTURE_ROOT>/.ontos-internal/strategy/documentation_guide.md) | strategy |
| dual_mode_matrix | [dual_mode_matrix.md](<FIXTURE_ROOT>/.ontos-internal/atom/dual_mode_matrix.md) | atom |
| feature_a | [feature_a.md](<FIXTURE_ROOT>/.ontos-internal/strategy/proposals/feature_a.md) | strategy |
| feature_b | [feature_b.md](<FIXTURE_ROOT>/.ontos-internal/strategy/proposals/feature_b.md) | strategy |
| log_20250101_initial_setup | [2025-01-01_initial-setup.md](<FIXTURE_ROOT>/.ontos-internal/logs/2025-01-01_initial-setup.md) | log |
| log_20250115_api_design | [2025-01-15_api-design.md](<FIXTURE_ROOT>/.ontos-internal/logs/2025-01-15_api-design.md) | log |
| log_20250201_security | [2025-02-01_security-hardening.md](<FIXTURE_ROOT>/.ontos-internal/logs/2025-02-01_security-hardening.md) | log |
| log_20250215_rejected | [2025-02-15_rejected-exploration.md](<FIXTURE_ROOT>/.ontos-internal/logs/2025-02-15_rejected-exploration.md) | log |
| log_20250301_complete | [2025-03-01_feature-complete.md](<FIXTURE_ROOT>/.ontos-internal/logs/2025-03-01_feature-complete.md) | log |
| medium_schema | [schema.md](<FIXTURE_ROOT>/.ontos-internal/atom/schema.md) | atom |
| mission | [mission.md](<FIXTURE_ROOT>/.ontos-internal/kernel/mission.md) | kernel |
| philosophy | [philosophy.md](<FIXTURE_ROOT>/.ontos-internal/kernel/philosophy.md) | kernel |
| security_model | [security_model.md](<FIXTURE_ROOT>/.ontos-internal/strategy/security_model.md) | strategy |
| testing_plan | [testing_plan.md](<FIXTURE_ROOT>/.ontos-internal/strategy/testing_plan.md) | strategy |
| validation_rules | [validation_rules.md](<FIXTURE_ROOT>/.ontos-internal/atom/validation_rules.md) | atom |


## 5. Documentation Staleness Audit
No documents use the `describes` field.
