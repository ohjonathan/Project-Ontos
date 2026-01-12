<!--
Ontos Context Map
Generated: <TIMESTAMP>
Mode: <MODE>
Scanned: .ontos-internal
-->
> **Note for users:** This context map documents Project Ontos's own development.
> When you run `python3 ontos_init.py` or `python3 .ontos/scripts/ontos_generate_context_map.py`
> in your project, this file will be overwritten with your project's context.

# Ontos Context Map
Generated on: <TIMESTAMP>
Scanned Directory: `<FIXTURE_ROOT>/.ontos-internal, docs`

## 1. Hierarchy Tree
### KERNEL
- **mission** [L2] (mission.md) ~31 tokens
  - Status: active
  - Depends On: None

### STRATEGY
- **project_plan** [L2] (project_plan.md) ~55 tokens
  - Status: active
  - Depends On: mission

### ATOM
- **schema** [L2] (schema.md) ~56 tokens
  - Status: active
  - Depends On: mission

### LOG
- **log_20250101_initial_setup** [L2] (2025-01-01_initial-setup.md) ~84 tokens
  - Status: active
  - Impacts: project_plan


## 2. Recent Timeline
- **2025-01-01** [feature] **Initial Setup** (`log_20250101_initial_setup`)
  - Impacted: `project_plan`
  - Concepts: setup, architecture

## 3. Dependency Audit
No issues found.

## 4. Index
| ID | Filename | Type |
|---|---|---|
| log_20250101_initial_setup | [2025-01-01_initial-setup.md](<FIXTURE_ROOT>/.ontos-internal/logs/2025-01-01_initial-setup.md) | log |
| mission | [mission.md](<FIXTURE_ROOT>/.ontos-internal/kernel/mission.md) | kernel |
| project_plan | [project_plan.md](<FIXTURE_ROOT>/.ontos-internal/strategy/project_plan.md) | strategy |
| schema | [schema.md](<FIXTURE_ROOT>/.ontos-internal/atom/schema.md) | atom |


## 5. Documentation Staleness Audit
No documents use the `describes` field.
