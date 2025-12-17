<!--
Ontos Context Map
Generated: 2025-12-17 13:45:09 UTC
Mode: Contributor
Scanned: .ontos-internal
-->
> **Note for users:** This context map documents Project Ontos's own development.
> When you run `python3 ontos_init.py` or `python3 .ontos/scripts/ontos_generate_context_map.py`
> in your project, this file will be overwritten with your project's context.

# Ontos Context Map
Generated on: 2025-12-17 22:45:09
Scanned Directory: `/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal, docs`

## 1. Hierarchy Tree
### KERNEL
- **mission** (mission.md) ~377 tokens
  - Status: active
  - Depends On: None
- **ontos_agent_instructions** (Ontos_Agent_Instructions.md) ~1,800 tokens
  - Status: active
  - Depends On: ontos_manual
- **ontos_manual** (Ontos_Manual.md) ~2,500 tokens
  - Status: active
  - Depends On: None

### STRATEGY
- **codex_2_6_v1_review** [draft] (Codex_2.6_v1.md) ~766 tokens
  - Status: draft
  - Depends On: v2_6_proposals_and_tooling
- **codex_2_6_v2_review** [draft] (Codex_2.6_v2.md) ~995 tokens
  - Status: draft
  - Depends On: v2_6_proposals_and_tooling
- **codex_2_6_v3_review** [draft] (Codex_2.6_v3.md) ~600 tokens
  - Status: draft
  - Depends On: v2_6_proposals_and_tooling
- **decision_history** (decision_history.md) ~424 tokens
  - Status: active
  - Depends On: mission
- **s3_archive_analysis** [draft] (s3-archive-analysis.md) ~2,600 tokens
  - Status: draft
  - Depends On: v2_strategy
- **s3_archive_implementation_plan** [draft] (s3-archive-implementation-plan.md) ~8,200 tokens
  - Status: draft
  - Depends On: s3_archive_analysis
- **v2_5_promises_implementation_plan** [draft] (v2.5_promises_implementation_plan.md) ~9,100 tokens
  - Status: draft
  - Depends On: v2_strategy, mission
- **v2_6_proposals_and_tooling** [draft] (v2.6_proposals_and_tooling.md) ~11,100 tokens
  - Status: draft
  - Depends On: v2_strategy
- **v2_strategy** (v2_strategy.md) ~2,600 tokens
  - Status: active
  - Depends On: mission

### ATOM
- **claude_2_6_v1_review** (Claude_2.6_v1.md) ~2,400 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling
- **claude_2_6_v2_review** (Claude_2.6_v2.md) ~1,300 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling, claude_2_6_v1_review
- **claude_2_6_v3_review** (Claude_2.6_v3.md) ~1,400 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling, claude_2_6_v2_review
- **common_concepts** (Common_Concepts.md) ~107 tokens
  - Status: active
  - Depends On: None
- **dual_mode_matrix** (Dual_Mode_Matrix.md) ~1,500 tokens
  - Status: active
  - Depends On: schema
- **gemini_2_6_v1_review** (Gemini_2.6_v1.md) ~1,400 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling
- **gemini_2_6_v2_review** (Gemini_2.6_v2.md) ~1,300 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling
- **gemini_2_6_v3_review** (Gemini_2.6_v3.md) ~1,200 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling
- **schema** (schema.md) ~451 tokens
  - Status: active
  - Depends On: v2_strategy
- **v2_5_architectural_review_claude** (V1_Claude_on_v2.5.md) ~4,600 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan
- **v2_5_architectural_review_claude_v2** (V2_Claude_on_v2.5.md) ~1,900 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan

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
- **log_20251215_v2_4_config_automation** (2025-12-15_v2-4-config-automation.md) ~137 tokens
  - Status: active
  - Impacts: None
- **log_20251215_v2_4_proposal_v1_4** (2025-12-15_v2-4-proposal-v1-4.md) ~1,000 tokens
  - Status: active
  - Impacts: v2_strategy
- **log_20251216_v2_5_promises_implementation_plan** (2025-12-16_v2-5-promises-implementation-plan.md) ~621 tokens
  - Status: active
  - Impacts: v2_strategy
- **log_20251217_ci_orphan_fix** (2025-12-17_ci-orphan-fix.md) ~110 tokens
  - Status: active
  - Impacts: None
- **log_20251217_ci_strict_mode_fixes** (2025-12-17_ci-strict-mode-fixes.md) ~122 tokens
  - Status: active
  - Impacts: v2_5_promises_implementation_plan
- **log_20251217_pr_18_feedback_fixes** (2025-12-17_pr-18-feedback-fixes.md) ~114 tokens
  - Status: active
  - Impacts: None
- **log_20251217_pr_18_staging_fix** (2025-12-17_pr-18-staging-fix.md) ~112 tokens
  - Status: active
  - Impacts: None
- **log_20251217_pr_19_review_fixes** (2025-12-17_pr-19-review-fixes.md) ~113 tokens
  - Status: active
  - Impacts: None
- **log_20251217_v2_5_1_proposals_architecture** (2025-12-17_v2-5-1-proposals-architecture.md) ~1,200 tokens
  - Status: active
  - Impacts: v2_strategy, ontos_manual
- **log_20251217_v2_5_2_dual_mode_implementation** (2025-12-17_v2-5-2-dual-mode-implementation.md) ~135 tokens
  - Status: active
  - Impacts: None
- **log_20251217_v2_5_2_shipped_cleanup** (2025-12-17_v2-5-2-shipped-cleanup.md) ~352 tokens
  - Status: active
  - Impacts: v2_strategy
- **log_20251217_v2_5_architectural_review** (2025-12-17_v2-5-architectural-review.md) ~533 tokens
  - Status: active
  - Impacts: v2_5_promises_implementation_plan
- **log_20251217_v2_5_plan_finalization** (2025-12-17_v2-5-plan-finalization.md) ~581 tokens
  - Status: active
  - Impacts: v2_5_promises_implementation_plan
- **log_20251217_v2_5_promises_implementation** (2025-12-17_v2-5-promises-implementation.md) ~558 tokens
  - Status: active
  - Impacts: v2_5_promises_implementation_plan, ontos_manual, ontos_agent_instructions
- **log_20251217_v2_5_promises_implementation_plan** (2025-12-17_v2-5-promises-implementation-plan.md) ~141 tokens
  - Status: active
  - Impacts: None
- **log_20251217_v2_6_bugfixes** (2025-12-17_v2-6-bugfixes.md) ~117 tokens
  - Status: active
  - Impacts: v2_6_proposals_and_tooling
- **log_20251217_v2_6_codex_fixes** (2025-12-17_v2-6-codex-fixes.md) ~119 tokens
  - Status: active
  - Impacts: v2_6_proposals_and_tooling
- **log_20251217_v2_6_docs** (2025-12-17_v2-6-docs.md) ~105 tokens
  - Status: active
  - Impacts: ontos_manual, ontos_agent_instructions
- **log_20251217_v2_6_implementation** (2025-12-17_v2-6-implementation.md) ~136 tokens
  - Status: active
  - Impacts: v2_6_proposals_and_tooling
- **log_20251217_v2_6_verification** (2025-12-17_v2-6-verification.md) ~135 tokens
  - Status: active
  - Impacts: v2_6_proposals_and_tooling


## 2. Recent Timeline
- **2025-12-17** [feature] **V2 6 Verification** (`log_20251217_v2_6_verification`)
  - Impacted: `v2_6_proposals_and_tooling`
- **2025-12-17** [feature] **V2 6 Implementation** (`log_20251217_v2_6_implementation`)
  - Impacted: `v2_6_proposals_and_tooling`
- **2025-12-17** [chore] **V2 6 Docs** (`log_20251217_v2_6_docs`)
  - Impacted: `ontos_manual`, `ontos_agent_instructions`
- **2025-12-17** [fix] **V2 6 Codex Fixes** (`log_20251217_v2_6_codex_fixes`)
  - Impacted: `v2_6_proposals_and_tooling`
- **2025-12-17** [fix] **V2 6 Bugfixes** (`log_20251217_v2_6_bugfixes`)
  - Impacted: `v2_6_proposals_and_tooling`
- **2025-12-17** [feature] **V2 5 Promises Implementation** (`log_20251217_v2_5_promises_implementation`)
  - Impacted: `v2_5_promises_implementation_plan`, `ontos_manual`, `ontos_agent_instructions`
  - Concepts: config, ux, tooling, hooks
- **2025-12-17** [refactor] **V2 5 Promises Implementation Plan** (`log_20251217_v2_5_promises_implementation_plan`)
- **2025-12-17** [decision] **V2 5 Plan Finalization** (`log_20251217_v2_5_plan_finalization`)
  - Impacted: `v2_5_promises_implementation_plan`
  - Concepts: architecture, planning
- **2025-12-17** [decision] **V2 5 Architectural Review** (`log_20251217_v2_5_architectural_review`)
  - Impacted: `v2_5_promises_implementation_plan`
  - Concepts: architecture, review, ux
- **2025-12-17** [chore] **V2 5 2 Shipped Cleanup** (`log_20251217_v2_5_2_shipped_cleanup`)
  - Impacted: `v2_strategy`
  - Concepts: cleanup, release, v2.5.2

*Showing 10 of 33 sessions*

## 3. Dependency Audit
No issues found.

## 4. Index
| ID | Filename | Type |
|---|---|---|
| claude_2_6_v1_review | [Claude_2.6_v1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.6/Claude_2.6_v1.md) | atom |
| claude_2_6_v2_review | [Claude_2.6_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.6/Claude_2.6_v2.md) | atom |
| claude_2_6_v3_review | [Claude_2.6_v3.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.6/Claude_2.6_v3.md) | atom |
| codex_2_6_v1_review | [Codex_2.6_v1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.6/Codex_2.6_v1.md) | strategy |
| codex_2_6_v2_review | [Codex_2.6_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.6/Codex_2.6_v2.md) | strategy |
| codex_2_6_v3_review | [Codex_2.6_v3.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.6/Codex_2.6_v3.md) | strategy |
| common_concepts | [Common_Concepts.md](docs/reference/Common_Concepts.md) | atom |
| decision_history | [decision_history.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/decision_history.md) | strategy |
| dual_mode_matrix | [Dual_Mode_Matrix.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/reference/Dual_Mode_Matrix.md) | atom |
| gemini_2_6_v1_review | [Gemini_2.6_v1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.6/Gemini_2.6_v1.md) | atom |
| gemini_2_6_v2_review | [Gemini_2.6_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.6/Gemini_2.6_v2.md) | atom |
| gemini_2_6_v3_review | [Gemini_2.6_v3.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.6/Gemini_2.6_v3.md) | atom |
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
| log_20251216_v2_5_promises_implementation_plan | [2025-12-16_v2-5-promises-implementation-plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-16_v2-5-promises-implementation-plan.md) | log |
| log_20251217_ci_orphan_fix | [2025-12-17_ci-orphan-fix.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_ci-orphan-fix.md) | log |
| log_20251217_ci_strict_mode_fixes | [2025-12-17_ci-strict-mode-fixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_ci-strict-mode-fixes.md) | log |
| log_20251217_pr_18_feedback_fixes | [2025-12-17_pr-18-feedback-fixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_pr-18-feedback-fixes.md) | log |
| log_20251217_pr_18_staging_fix | [2025-12-17_pr-18-staging-fix.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_pr-18-staging-fix.md) | log |
| log_20251217_pr_19_review_fixes | [2025-12-17_pr-19-review-fixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_pr-19-review-fixes.md) | log |
| log_20251217_v2_5_1_proposals_architecture | [2025-12-17_v2-5-1-proposals-architecture.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-5-1-proposals-architecture.md) | log |
| log_20251217_v2_5_2_dual_mode_implementation | [2025-12-17_v2-5-2-dual-mode-implementation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-5-2-dual-mode-implementation.md) | log |
| log_20251217_v2_5_2_shipped_cleanup | [2025-12-17_v2-5-2-shipped-cleanup.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-5-2-shipped-cleanup.md) | log |
| log_20251217_v2_5_architectural_review | [2025-12-17_v2-5-architectural-review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-5-architectural-review.md) | log |
| log_20251217_v2_5_plan_finalization | [2025-12-17_v2-5-plan-finalization.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-5-plan-finalization.md) | log |
| log_20251217_v2_5_promises_implementation | [2025-12-17_v2-5-promises-implementation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-5-promises-implementation.md) | log |
| log_20251217_v2_5_promises_implementation_plan | [2025-12-17_v2-5-promises-implementation-plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-5-promises-implementation-plan.md) | log |
| log_20251217_v2_6_bugfixes | [2025-12-17_v2-6-bugfixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-6-bugfixes.md) | log |
| log_20251217_v2_6_codex_fixes | [2025-12-17_v2-6-codex-fixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-6-codex-fixes.md) | log |
| log_20251217_v2_6_docs | [2025-12-17_v2-6-docs.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-6-docs.md) | log |
| log_20251217_v2_6_implementation | [2025-12-17_v2-6-implementation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-6-implementation.md) | log |
| log_20251217_v2_6_verification | [2025-12-17_v2-6-verification.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-6-verification.md) | log |
| mission | [mission.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/mission.md) | kernel |
| ontos_agent_instructions | [Ontos_Agent_Instructions.md](docs/reference/Ontos_Agent_Instructions.md) | kernel |
| ontos_manual | [Ontos_Manual.md](docs/reference/Ontos_Manual.md) | kernel |
| s3_archive_analysis | [s3-archive-analysis.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/s3-archive-analysis.md) | strategy |
| s3_archive_implementation_plan | [s3-archive-implementation-plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/s3-archive-implementation-plan.md) | strategy |
| schema | [schema.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/schema.md) | atom |
| v2_5_architectural_review_claude | [V1_Claude_on_v2.5.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.5/V1_Claude_on_v2.5.md) | atom |
| v2_5_architectural_review_claude_v2 | [V2_Claude_on_v2.5.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.5/V2_Claude_on_v2.5.md) | atom |
| v2_5_promises_implementation_plan | [v2.5_promises_implementation_plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.5/v2.5_promises_implementation_plan.md) | strategy |
| v2_6_proposals_and_tooling | [v2.6_proposals_and_tooling.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.6/v2.6_proposals_and_tooling.md) | strategy |
| v2_strategy | [v2_strategy.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2_strategy.md) | strategy |
