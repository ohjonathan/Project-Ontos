<!--
Ontos Context Map
Generated: 2025-12-15 04:47:37 UTC
Mode: Contributor
Scanned: .ontos-internal
-->
> **Note for users:** This context map documents Project Ontos's own development.
> When you run `python3 ontos_init.py` or `python3 .ontos/scripts/ontos_generate_context_map.py`
> in your project, this file will be overwritten with your project's context.

# Ontos Context Map
Generated on: 2025-12-15 13:47:37
Scanned Directory: `/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal, docs`

## 1. Hierarchy Tree
### KERNEL
- **mission** (mission.md) ~377 tokens
  - Status: active
  - Depends On: None
- **ontos_agent_instructions** (Ontos_Agent_Instructions.md) ~1,500 tokens
  - Status: active
  - Depends On: ontos_manual
- **ontos_manual** (Ontos_Manual.md) ~2,200 tokens
  - Status: active
  - Depends On: None

### STRATEGY
- **decision_history** (decision_history.md) ~424 tokens
  - Status: active
  - Depends On: mission
- **v2_3_ux_improvements** (2.3_ux_improvement_ideas.md) ~1,900 tokens
  - Status: draft
  - Depends On: v2_strategy
- **v2_4_config_automation_proposal** (v2.4_config_automation_proposal.md) ~12,700 tokens
  - Status: draft
  - Depends On: v2_strategy, mission
- **v2_strategy** (v2_strategy.md) ~2,600 tokens
  - Status: active
  - Depends On: mission

### ATOM
- **common_concepts** (Common_Concepts.md) ~654 tokens
  - Status: active
  - Depends On: None
- **schema** (schema.md) ~314 tokens
  - Status: active
  - Depends On: v2_strategy

### LOG
- **log_20251213_agent_no_verify_rule** (2025-12-13_agent-no-verify-rule.md) ~248 tokens
  - Status: active
  - Impacts: None
- **log_20251213_cleanup_broken_links** (2025-12-13_cleanup-broken-links.md) ~417 tokens
  - Status: active
  - Impacts: schema
- **log_20251213_context_map_notice** (2025-12-13_context-map-notice.md) ~296 tokens
  - Status: active
  - Impacts: schema
- **log_20251213_documentation_compaction** (2025-12-13_documentation-compaction.md) ~902 tokens
  - Status: active
  - Impacts: schema, v2_strategy, mission
- **log_20251213_gemini_feedback_fixes** (2025-12-13_gemini-feedback-fixes.md) ~416 tokens
  - Status: active
  - Impacts: schema
- **log_20251213_pr_12_fixes** (2025-12-13_pr-12-fixes.md) ~306 tokens
  - Status: active
  - Impacts: None
- **log_20251213_smart_memory_implementation** (2025-12-13_smart-memory-implementation.md) ~444 tokens
  - Status: active
  - Impacts: decision_history, v2_strategy
- **log_20251213_v22_ux_planning** (2025-12-13_v22-ux-planning.md) ~429 tokens
  - Status: active
  - Impacts: v2_strategy
- **log_20251213_version_fix** (2025-12-13_version-fix.md) ~217 tokens
  - Status: active
  - Impacts: None
- **log_20251214_v2_2_implementation** (2025-12-14_v2-2-implementation.md) ~984 tokens
  - Status: active
  - Impacts: common_concepts
- **log_20251214_v2_3_1_cleanup** (2025-12-14_v2-3-1-cleanup.md) ~200 tokens
  - Status: active
  - Impacts: None
- **log_20251214_v2_3_curation_not_ceremony** (2025-12-14_v2-3-curation-not-ceremony.md) ~461 tokens
  - Status: active
  - Impacts: ontos_manual, ontos_agent_instructions
- **log_20251214_v2_4_config_design** (2025-12-14_v2-4-config-design.md) ~1,100 tokens
  - Status: active
  - Impacts: v2_strategy
- **log_20251215_v2_4_config_automation** (2025-12-15_v2-4-config-automation.md) ~145 tokens
  - Status: active
  - Impacts: v2_4_config_automation_proposal
- **log_20251215_v2_4_proposal_v1_4** (2025-12-15_v2-4-proposal-v1-4.md) ~1,000 tokens
  - Status: active
  - Impacts: v2_4_config_automation_proposal, v2_strategy


## 2. Recent Timeline
- **2025-12-15** [decision] **V2 4 Proposal V1 4** (`log_20251215_v2_4_proposal_v1_4`)
  - Impacted: `v2_4_config_automation_proposal`, `v2_strategy`
  - Concepts: ux, config, tooling, architectural-review
- **2025-12-15** [feature] **V2 4 Config Automation** (`log_20251215_v2_4_config_automation`)
  - Impacted: `v2_4_config_automation_proposal`
  - Concepts: config, ux, automation
- **2025-12-14** [decision] **V2 4 Config Design** (`log_20251214_v2_4_config_design`)
  - Impacted: `v2_strategy`
  - Concepts: ux, config, tooling
- **2025-12-14** [feature] **V2 3 Curation Not Ceremony** (`log_20251214_v2_3_curation_not_ceremony`)
  - Impacted: `ontos_manual`, `ontos_agent_instructions`
  - Concepts: v2.3, ux, tooling, testing
- **2025-12-14** [chore] **V2 3 1 Cleanup** (`log_20251214_v2_3_1_cleanup`)
  - Concepts: cleanup, tooling
- **2025-12-14** [feature] **V2 2 Implementation** (`log_20251214_v2_2_implementation`)
  - Impacted: `common_concepts`
  - Concepts: data-quality, lint, workflow
- **2025-12-13** [fix] **Version Fix** (`log_20251213_version_fix`)
  - Concepts: versioning, release
- **2025-12-13** [exploration] **V22 Ux Planning** (`log_20251213_v22_ux_planning`)
  - Impacted: `v2_strategy`
  - Concepts: ux, friction, activation, summaries, workflow
- **2025-12-13** [feature] **Smart Memory Implementation** (`log_20251213_smart_memory_implementation`)
  - Impacted: `decision_history`, `v2_strategy`
  - Concepts: memory, consolidation
- **2025-12-13** [fix] **Pr 12 Fixes** (`log_20251213_pr_12_fixes`)
  - Concepts: cleanup, ci, documentation

*Showing 10 of 15 sessions*

## 3. Dependency Audit
No issues found.

## 4. Index
| ID | Filename | Type |
|---|---|---|
| common_concepts | [Common_Concepts.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/reference/Common_Concepts.md) | atom |
| decision_history | [decision_history.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/decision_history.md) | strategy |
| log_20251213_agent_no_verify_rule | [2025-12-13_agent-no-verify-rule.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-13_agent-no-verify-rule.md) | log |
| log_20251213_cleanup_broken_links | [2025-12-13_cleanup-broken-links.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-13_cleanup-broken-links.md) | log |
| log_20251213_context_map_notice | [2025-12-13_context-map-notice.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-13_context-map-notice.md) | log |
| log_20251213_documentation_compaction | [2025-12-13_documentation-compaction.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-13_documentation-compaction.md) | log |
| log_20251213_gemini_feedback_fixes | [2025-12-13_gemini-feedback-fixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-13_gemini-feedback-fixes.md) | log |
| log_20251213_pr_12_fixes | [2025-12-13_pr-12-fixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-13_pr-12-fixes.md) | log |
| log_20251213_smart_memory_implementation | [2025-12-13_smart-memory-implementation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-13_smart-memory-implementation.md) | log |
| log_20251213_v22_ux_planning | [2025-12-13_v22-ux-planning.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-13_v22-ux-planning.md) | log |
| log_20251213_version_fix | [2025-12-13_version-fix.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-13_version-fix.md) | log |
| log_20251214_v2_2_implementation | [2025-12-14_v2-2-implementation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-14_v2-2-implementation.md) | log |
| log_20251214_v2_3_1_cleanup | [2025-12-14_v2-3-1-cleanup.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-14_v2-3-1-cleanup.md) | log |
| log_20251214_v2_3_curation_not_ceremony | [2025-12-14_v2-3-curation-not-ceremony.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-14_v2-3-curation-not-ceremony.md) | log |
| log_20251214_v2_4_config_design | [2025-12-14_v2-4-config-design.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-14_v2-4-config-design.md) | log |
| log_20251215_v2_4_config_automation | [2025-12-15_v2-4-config-automation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-15_v2-4-config-automation.md) | log |
| log_20251215_v2_4_proposal_v1_4 | [2025-12-15_v2-4-proposal-v1-4.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-15_v2-4-proposal-v1-4.md) | log |
| mission | [mission.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/mission.md) | kernel |
| ontos_agent_instructions | [Ontos_Agent_Instructions.md](docs/reference/Ontos_Agent_Instructions.md) | kernel |
| ontos_manual | [Ontos_Manual.md](docs/reference/Ontos_Manual.md) | kernel |
| schema | [schema.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/schema.md) | atom |
| v2_3_ux_improvements | [2.3_ux_improvement_ideas.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/2.3_ux_improvement_ideas.md) | strategy |
| v2_4_config_automation_proposal | [v2.4_config_automation_proposal.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.4/v2.4_config_automation_proposal.md) | strategy |
| v2_strategy | [v2_strategy.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2_strategy.md) | strategy |
