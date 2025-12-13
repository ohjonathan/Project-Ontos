<!--
Ontos Context Map
Generated: 2025-12-13 17:27:10 UTC
Mode: Contributor
Scanned: .ontos-internal
-->
> **Note for users:** This context map documents Project Ontos's own development.
> When you run `python3 ontos_init.py` or `python3 .ontos/scripts/ontos_generate_context_map.py`
> in your project, this file will be overwritten with your project's context.

# Ontos Context Map
Generated on: 2025-12-14 02:27:10
Scanned Directory: `/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal`

## 1. Hierarchy Tree
### KERNEL
- **mission** (mission.md) ~377 tokens
  - Status: active
  - Depends On: None

### STRATEGY
- **decision_history** (decision_history.md) ~424 tokens
  - Status: active
  - Depends On: mission
- **v2_3_ux_improvements** (2.3_ux_improvement_ideas.md) ~1,900 tokens
  - Status: draft
  - Depends On: v2_strategy
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
- **log_20251214_v2_2_implementation** (2025-12-14_v2-2-implementation.md) ~973 tokens
  - Status: active
  - Impacts: common_concepts


## 2. Recent Timeline
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
- **2025-12-13** [fix] **Gemini Feedback Fixes** (`log_20251213_gemini_feedback_fixes`)
  - Impacted: `schema`
  - Concepts: gemini-review, installation, ontos-init, documentation-consistency
- **2025-12-13** [chore] **Documentation Compaction** (`log_20251213_documentation_compaction`)
  - Impacted: `schema`, `v2_strategy`, `mission`
  - Concepts: documentation-compaction, archive, token-reduction, minimal-example
- **2025-12-13** [feature] **Context Map Notice** (`log_20251213_context_map_notice`)
  - Impacted: `schema`
  - Concepts: context-map, documentation, contributor-mode
- **2025-12-13** [chore] **Cleanup Broken Links** (`log_20251213_cleanup_broken_links`)
  - Impacted: `schema`
  - Concepts: cleanup, broken-links, legacy-removal, documentation
- **2025-12-13** [chore] **Agent No Verify Rule** (`log_20251213_agent_no_verify_rule`)
  - Concepts: workflow, agent-behavior, git-hooks

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
| mission | [mission.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/mission.md) | kernel |
| schema | [schema.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/schema.md) | atom |
| v2_3_ux_improvements | [2.3_ux_improvement_ideas.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/2.3_ux_improvement_ideas.md) | strategy |
| v2_strategy | [v2_strategy.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2_strategy.md) | strategy |
