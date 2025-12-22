<!--
Ontos Context Map
Generated: 2025-12-22 14:29:31 UTC
Mode: Contributor
Scanned: .ontos-internal
-->
> **Note for users:** This context map documents Project Ontos's own development.
> When you run `python3 ontos_init.py` or `python3 .ontos/scripts/ontos_generate_context_map.py`
> in your project, this file will be overwritten with your project's context.

# Ontos Context Map
Generated on: 2025-12-22 23:29:31
Scanned Directory: `/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal, docs`

## 1. Hierarchy Tree
### KERNEL
- **mission** [L2] (mission.md) ~377 tokens
  - Status: active
  - Depends On: None
- **ontos_agent_instructions** [L2] (Ontos_Agent_Instructions.md) ~2,100 tokens
  - Status: active
  - Depends On: ontos_manual
- **ontos_manual** [L2] (Ontos_Manual.md) ~3,400 tokens
  - Status: active
  - Depends On: None

### STRATEGY
- **antigravity_v2_9_instructions** [L2] (v2.9_antigravity_instructions.md) ~4,600 tokens
  - Status: active
  - Depends On: v2_9_implementation_plan, master_plan_v4
- **codex_2_6_v1_review** [L2] [draft] (Codex_2.6_v1.md) ~766 tokens
  - Status: draft
  - Depends On: v2_6_proposals_and_tooling
- **codex_2_6_v2_review** [L2] [draft] (Codex_2.6_v2.md) ~995 tokens
  - Status: draft
  - Depends On: v2_6_proposals_and_tooling
- **codex_2_6_v3_review** [L2] [draft] (Codex_2.6_v3.md) ~600 tokens
  - Status: draft
  - Depends On: v2_6_proposals_and_tooling
- **codex_v2_7_phil_review_v1** [L1] (Codex_V2.7Phil_v1.md) ~1,100 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **installation_ux_proposal** [L2] [draft] (Installation_UX_Proposal.md) ~7,100 tokens
  - Status: draft
  - Depends On: v2_strategy, mission, ontos_manual
- **installation_ux_proposal_review** [L2] [draft] (Installation_UX_Proposal_Review_Codex.md) ~948 tokens
  - Status: draft
  - Depends On: installation_ux_proposal, v2_strategy, mission, ontos_manual
- **master_plan_v4** [L2] (master_plan.md) ~2,500 tokens
  - Status: active
  - Depends On: mission, v2_strategy
- **s3_archive_analysis** [L2] [draft] (s3-archive-analysis.md) ~2,600 tokens
  - Status: draft
  - Depends On: v2_strategy
- **s3_archive_implementation_plan** [L2] [draft] (s3-archive-implementation-plan.md) ~8,200 tokens
  - Status: draft
  - Depends On: s3_archive_analysis
- **v2_5_promises_implementation_plan** [L2] [draft] (v2.5_promises_implementation_plan.md) ~9,100 tokens
  - Status: draft
  - Depends On: v2_strategy, mission
- **v2_6_proposals_and_tooling** [L2] (v2.6_proposals_and_tooling.md) ~11,100 tokens
  - Status: complete
  - Depends On: v2_strategy
- **v2_7_1_implementation_plan** [L1] (v2.7.1_implementation_plan.md) ~2,600 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **v2_7_1_patch_plan** [L1] (v2.7.1_patch_plan.md) ~994 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **v2_7_documentation_ontology** [L1] (v2.7_documentation_ontology.md) ~3,800 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **v2_7_implementation_plan** [L1] (v2.7_implementation_plan.md) ~8,300 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **v2_7_implementation_plan_review_codex** [L1] (v2.7_implementation_plan_review_codex.md) ~1,000 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **v2_8_implementation_plan** [L2] (v2.8_implementation_plan.md) ~12,800 tokens
  - Status: active
  - Depends On: master_plan_v4, v2_7_1_implementation_plan
- **v2_8_implementation_plan_review_codex** [L2] [draft] (v2.8_implementation_plan_review_codex.md) ~789 tokens
  - Status: draft
  - Depends On: v2_8_implementation_plan
- **v2_9_implementation_plan** [L2] (v2.9_implementation_plan.md) ~26,000 tokens
  - Status: active
  - Depends On: master_plan_v4, v2_8_implementation_plan
- **v2_strategy** [L2] (v2_strategy.md) ~2,600 tokens
  - Status: active
  - Depends On: mission
- **v3_master_plan_context_kernel_review_codex** [L2] [draft] (v3_master_plan_context_kernel_review_codex.md) ~968 tokens
  - Status: draft
  - Depends On: master_plan_v4
- **v3_master_plan_context_kernel_review_codex_v2** [L2] [draft] (v3_master_plan_context_kernel_review_codex_v2.md) ~1,000 tokens
  - Status: draft
  - Depends On: master_plan_v4
- **v3_master_plan_context_kernel_review_codex_v3** [L2] [draft] (v3_master_plan_context_kernel_review_codex_v3.md) ~1,000 tokens
  - Status: draft
  - Depends On: master_plan_v4

### ATOM
- **architect_synthesis_install_ux** [L2] [draft] (Architect_Synthesis_InstallUX.md) ~4,000 tokens
  - Status: draft
  - Depends On: installation_ux_proposal, claude_install_ux_review, gemini_install_ux_review, installation_ux_proposal_review
- **architect_v2_7_phil_synthesis** [L1] (Architect_V2.7Phil_Synthesis.md) ~3,500 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **claude_2_6_v1_review** [L2] (Claude_2.6_v1.md) ~2,400 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling
- **claude_2_6_v2_review** [L2] (Claude_2.6_v2.md) ~1,300 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling, claude_2_6_v1_review
- **claude_2_6_v3_review** [L2] (Claude_2.6_v3.md) ~1,400 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling, claude_2_6_v2_review
- **claude_2_7_phil_v1_review** [L1] (Claude_V2.7Phil_v1.md) ~2,400 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **claude_2_7_phil_v2_review** [L1] (Claude_V2.7Phil_v2.md) ~2,700 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **claude_install_ux_review** [L2] (Claude_InstallUX_Review.md) ~3,500 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **claude_v2_7_implementation_review** [L1] (Claude_v2.7_Implementation_Review.md) ~3,100 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **claude_v2_8_implementation_review** [L2] (Claude_v2.8_Implementation_Review.md) ~3,000 tokens
  - Status: complete
  - Depends On: v2_8_implementation_plan, master_plan_v4
- **claude_v2_9_implementation_review** [L2] (Claude_v2.9_Implementation_Review.md) ~3,600 tokens
  - Status: complete
  - Depends On: v2_9_implementation_plan
- **claude_v2_9_implementation_review_v2** [L2] (Claude_v2.9_Implementation_Review_v2.md) ~2,200 tokens
  - Status: complete
  - Depends On: v2_9_implementation_plan
- **claude_v2_9_implementation_review_v3** [L2] (Claude_v2.9_Implementation_Review_v3.md) ~1,000 tokens
  - Status: complete
  - Depends On: v2_9_implementation_plan
- **claude_v3_master_plan_review** [L2] (Claude_v3_Master_Plan_Review.md) ~3,300 tokens
  - Status: complete
  - Depends On: v2_strategy
- **claude_v3_master_plan_review_v2** [L2] (Claude_v3_Master_Plan_Review_v2.md) ~3,100 tokens
  - Status: complete
  - Depends On: v2_strategy
- **codex_2_5_v1_review** [L2] (V1_Codex on v2.5.md) ~621 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan
- **codex_2_5_v2_review** [L2] (V2_Codex on V2.5.md) ~340 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan, codex_2_5_v1_review
- **codex_v2_7_phil_review_v2** [L1] (Codex_V2.7Phil_v2.md) ~872 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **codex_v2_9_implementation_review** [L2] (Codex_v2.9_Implementation_Review.md) ~3,200 tokens
  - Status: complete
  - Depends On: v2_9_implementation_plan
- **common_concepts** [L1] (Common_Concepts.md) ~654 tokens  ⚠️ active
  - Status: active
  - Depends On: None
- **dual_mode_matrix** [L2] (Dual_Mode_Matrix.md) ~1,500 tokens
  - Status: active
  - Depends On: schema
- **gemini_2_5_v1_review** [L2] (V1_Gemini on v2.5.md) ~941 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan
- **gemini_2_5_v2_review** [L2] (V2_Gemini on v2.5.md) ~619 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan, gemini_2_5_v1_review
- **gemini_2_6_v1_review** [L2] (Gemini_2.6_v1.md) ~1,400 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling
- **gemini_2_6_v2_review** [L2] (Gemini_2.6_v2.md) ~1,300 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling
- **gemini_2_6_v3_review** [L2] (Gemini_2.6_v3.md) ~1,200 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling
- **gemini_install_ux_review** [L2] (Gemini_Review_Installation_UX_Proposal.md) ~2,800 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **gemini_v2_7_phil_v1** [L1] (Gemini_V2.7Phil_v1.md) ~1,200 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **gemini_v2_7_phil_v2** [L1] (Gemini_V2.7Phil_v2.md) ~823 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **gemini_v3_master_plan_review_v1** [L2] (v3_master_plan_review_gemini.md) ~1,900 tokens
  - Status: complete
  - Depends On: master_plan_v4
- **gemini_v3_master_plan_review_v2** [L2] (v3_master_plan_review_gemini_2.md) ~1,500 tokens
  - Status: complete
  - Depends On: master_plan_v4, gemini_v3_master_plan_review_v1
- **installation_experience_report** [L2] (Ontos_Installation_Experience_Report.md) ~2,200 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **ontos_codebase_map** [L2] [draft] (Ontos_Codebase_Map.md) ~6,800 tokens
  - Status: draft
  - Depends On: v2_strategy
- **ontos_deep_analysis_brief** [L2] [draft] (Ontos_Deep_Analysis_Brief.md) ~4,500 tokens
  - Status: draft
  - Depends On: v2_strategy, mission
- **pr22_chief_architect_review** [L1] (PR22_Chief_Architect_Review.md) ~2,700 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **pr22_chief_architect_review_v2** [L1] (PR22_Chief_Architect_Review_v2.md) ~1,700 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **schema** [L2] (schema.md) ~451 tokens
  - Status: active
  - Depends On: v2_strategy
- **v2_5_architectural_review_claude** [L2] (V1_Claude_on_v2.5.md) ~4,600 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan
- **v2_5_architectural_review_claude_v2** [L2] (V2_Claude_on_v2.5.md) ~1,900 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan
- **v2_7_implementation_synthesis** [L1] (v2.7_implementation_synthesis.md) ~3,900 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **v2_9_implementation_plan_review_codex** [L2] [draft] (v2.9_implementation_plan_review_codex.md) ~1,700 tokens
  - Status: draft
  - Depends On: v2_9_implementation_plan
- **v2_9_implementation_plan_review_codex_v2** [L2] [draft] (v2.9_implementation_plan_review_codex_v2.md) ~1,200 tokens
  - Status: draft
  - Depends On: v2_9_implementation_plan
- **v2_9_implementation_plan_review_codex_v3** [L2] [draft] (v2.9_implementation_plan_review_codex_v3.md) ~988 tokens
  - Status: draft
  - Depends On: v2_9_implementation_plan
- **v2_9_implementation_plan_review_gemini** [L2] (v2.9_implementation_plan_review_gemini.md) ~2,200 tokens
  - Status: complete
  - Depends On: v2_9_implementation_plan

### LOG
- **log_20251217_v2_5_plan_finalization** [L2] (2025-12-17_v2-5-plan-finalization.md) ~581 tokens
  - Status: active
  - Impacts: v2_5_promises_implementation_plan
- **log_20251217_v2_5_promises_implementation** [L2] (2025-12-17_v2-5-promises-implementation.md) ~558 tokens
  - Status: active
  - Impacts: v2_5_promises_implementation_plan, ontos_manual, ontos_agent_instructions
- **log_20251217_v2_5_promises_implementation_plan** [L1] (2025-12-17_v2-5-promises-implementation-plan.md) ~141 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20251217_v2_6_bugfixes** [L1] (2025-12-17_v2-6-bugfixes.md) ~117 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_6_proposals_and_tooling
- **log_20251217_v2_6_changelog** [L1] (2025-12-17_v2-6-changelog.md) ~99 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20251217_v2_6_codex_fixes** [L1] (2025-12-17_v2-6-codex-fixes.md) ~119 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_6_proposals_and_tooling
- **log_20251217_v2_6_docs** [L1] (2025-12-17_v2-6-docs.md) ~105 tokens  ⚠️ active
  - Status: active
  - Impacts: ontos_manual, ontos_agent_instructions
- **log_20251217_v2_6_implementation** [L1] (2025-12-17_v2-6-implementation.md) ~136 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_6_proposals_and_tooling
- **log_20251217_v2_6_maintenance** [L1] (2025-12-17_v2-6-maintenance.md) ~172 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20251217_v2_6_verification** [L1] (2025-12-17_v2-6-verification.md) ~135 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_6_proposals_and_tooling
- **log_20251218_v2_6_1_graduation** [L1] (2025-12-18_v2-6-1-graduation.md) ~971 tokens  ⚠️ active
  - Status: active
  - Impacts: ontos_agent_instructions, ontos_manual
- **log_20251218_v2_7_documentation_ontology** [L2] (2025-12-18_v2-7-documentation-ontology.md) ~572 tokens
  - Status: active
  - Impacts: v2_7_documentation_ontology
- **log_20251218_v2_7_philosophy_proposal** [L2] (2025-12-18_v2-7-philosophy-proposal.md) ~904 tokens
  - Status: active
  - Impacts: v2_strategy, v2_7_documentation_ontology
- **log_20251219_chore_maintenance_consolidate_logs_add_frontma** [L2] (2025-12-19_chore-maintenance-consolidate-logs-add-frontma.md) ~332 tokens
  - Status: active
  - Impacts: schema
- **log_20251219_docs_graduate_master_plan_to_strategy_reorganize** [L2] (2025-12-19_docs-graduate-master-plan-to-strategy-reorganize.md) ~558 tokens
  - Status: active
  - Impacts: master_plan_v4, v2_strategy
- **log_20251219_fix_resolve_all_context_map_validation_errors** [L2] (2025-12-19_fix-resolve-all-context-map-validation-errors.md) ~419 tokens
  - Status: active
  - Impacts: schema, architect_v2_7_phil_synthesis, architect_synthesis_install_ux
- **log_20251219_v2_7** [L2] (2025-12-19_v2-7.md) ~599 tokens
  - Status: active
  - Impacts: v2_7_documentation_ontology, master_plan_v4, schema
- **log_20251219_v2_7_1** [L1] (2025-12-19_v2-7-1.md) ~128 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20251219_v2_7_1_plan** [L2] (2025-12-19_v2-7-1-plan.md) ~385 tokens
  - Status: active
  - Impacts: v2_7_1_implementation_plan
- **log_20251220_v2_7_1** [L1] (2025-12-20_v2-7-1.md) ~383 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20251220_v2_8** [L2] (2025-12-20_v2-8.md) ~565 tokens
  - Status: active
  - Impacts: v2_8_implementation_plan
- **log_20251220_v2_8_plan_creation** [L1] (2025-12-20_v2-8-plan-creation.md) ~476 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_8_implementation_plan
- **log_20251220_v2_8_pr24_fixes** [L2] (2025-12-20_v2-8-pr24-fixes.md) ~438 tokens
  - Status: active
  - Impacts: v2_8_implementation_plan
- **log_20251220_v2_8_version_bump** [L1] (2025-12-20_v2-8-version-bump.md) ~100 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20251221_v2_8_1_minor_fixes** [L1] (2025-12-21_v2-8-1-minor-fixes.md) ~140 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_8_implementation_plan
- **log_20251221_v2_8_1_sessioncontext** [L1] (2025-12-21_v2-8-1-sessioncontext.md) ~365 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_8_implementation_plan
- **log_20251221_v2_8_2_end_session_refactor** [L1] (2025-12-21_v2-8-2-end-session-refactor.md) ~145 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_8_implementation_plan
- **log_20251221_v2_8_2_phase_1_2_complete** [L1] (2025-12-21_v2-8-2-phase-1-2-complete.md) ~144 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_8_implementation_plan
- **log_20251221_v2_8_2_sessioncontext_fix** [L1] (2025-12-21_v2-8-2-sessioncontext-fix.md) ~144 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_8_implementation_plan
- **log_20251221_v2_8_3_a_plus_grade** [L1] (2025-12-21_v2-8-3-a-plus-grade.md) ~141 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_8_implementation_plan
- **log_20251221_v2_8_3_chief_architect_gaps** [L1] (2025-12-21_v2-8-3-chief-architect-gaps.md) ~145 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_8_implementation_plan
- **log_20251221_v2_8_3_owns_ctx_pattern** [L1] (2025-12-21_v2-8-3-owns-ctx-pattern.md) ~143 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_8_implementation_plan
- **log_20251221_v2_8_3_release** [L1] (2025-12-21_v2-8-3-release.md) ~138 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_8_implementation_plan
- **log_20251221_v2_8_3_setup** [L1] (2025-12-21_v2-8-3-setup.md) ~103 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_8_implementation_plan
- **log_20251222_v285_unified_cli** [L1] (2025-12-22_v285-unified-cli.md) ~418 tokens  ⚠️ active
  - Status: active
  - Impacts: ontos_manual
- **log_20251222_v286_docs_alignment** [L2] (2025-12-22_v286-docs-alignment.md) ~264 tokens
  - Status: active
  - Impacts: ontos_agent_instructions
- **log_20251222_v290_schema_versioning** [L1] (2025-12-22_v290-schema-versioning.md) ~141 tokens  ⚠️ active
  - Status: active
  - Impacts: v2_9_implementation_plan, ontos_manual
- **log_20251222_v2_9_architectural_review** [L2] (2025-12-22_v2-9-architectural-review.md) ~132 tokens
  - Status: active
  - Impacts: v2_9_implementation_plan, v2_9_implementation_plan_review_gemini


## 2. Recent Timeline
- **2025-12-22** [feature] **V290 Schema Versioning** (`log_20251222_v290_schema_versioning`)
  - Impacted: `v2_9_implementation_plan`, `ontos_manual`
- **2025-12-22** [chore] **V286 Docs Alignment** (`log_20251222_v286_docs_alignment`)
  - Impacted: `ontos_agent_instructions`
  - Concepts: cli, documentation
- **2025-12-22** [feature] **V285 Unified Cli** (`log_20251222_v285_unified_cli`)
  - Impacted: `ontos_manual`
- **2025-12-22** [chore] **V2 9 Architectural Review** (`log_20251222_v2_9_architectural_review`)
  - Impacted: `v2_9_implementation_plan`, `v2_9_implementation_plan_review_gemini`
  - Concepts: architecture, planning, v2.9, review
- **2025-12-21** [chore] **V2 8 3 Setup** (`log_20251221_v2_8_3_setup`)
  - Impacted: `v2_8_implementation_plan`
- **2025-12-21** [refactor] **V2 8 3 Release** (`log_20251221_v2_8_3_release`)
  - Impacted: `v2_8_implementation_plan`
- **2025-12-21** [refactor] **V2 8 3 Owns Ctx Pattern** (`log_20251221_v2_8_3_owns_ctx_pattern`)
  - Impacted: `v2_8_implementation_plan`
- **2025-12-21** [refactor] **V2 8 3 Chief Architect Gaps** (`log_20251221_v2_8_3_chief_architect_gaps`)
  - Impacted: `v2_8_implementation_plan`
- **2025-12-21** [refactor] **V2 8 3 A Plus Grade** (`log_20251221_v2_8_3_a_plus_grade`)
  - Impacted: `v2_8_implementation_plan`
- **2025-12-21** [refactor] **V2 8 2 Sessioncontext Fix** (`log_20251221_v2_8_2_sessioncontext_fix`)
  - Impacted: `v2_8_implementation_plan`

*Showing 10 of 38 sessions*

## 3. Dependency Audit
No issues found.

## 4. Index
| ID | Filename | Type |
|---|---|---|
| antigravity_v2_9_instructions | [v2.9_antigravity_instructions.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.9/v2.9_antigravity_instructions.md) | strategy |
| architect_synthesis_install_ux | [Architect_Synthesis_InstallUX.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Architect_Synthesis_InstallUX.md) | atom |
| architect_v2_7_phil_synthesis | [Architect_V2.7Phil_Synthesis.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Architect_V2.7Phil_Synthesis.md) | atom |
| claude_2_6_v1_review | [Claude_2.6_v1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Claude_2.6_v1.md) | atom |
| claude_2_6_v2_review | [Claude_2.6_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Claude_2.6_v2.md) | atom |
| claude_2_6_v3_review | [Claude_2.6_v3.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Claude_2.6_v3.md) | atom |
| claude_2_7_phil_v1_review | [Claude_V2.7Phil_v1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Claude_V2.7Phil_v1.md) | atom |
| claude_2_7_phil_v2_review | [Claude_V2.7Phil_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Claude_V2.7Phil_v2.md) | atom |
| claude_install_ux_review | [Claude_InstallUX_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Claude_InstallUX_Review.md) | atom |
| claude_v2_7_implementation_review | [Claude_v2.7_Implementation_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Claude_v2.7_Implementation_Review.md) | atom |
| claude_v2_8_implementation_review | [Claude_v2.8_Implementation_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.8/Claude_v2.8_Implementation_Review.md) | atom |
| claude_v2_9_implementation_review | [Claude_v2.9_Implementation_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.9/Claude_v2.9_Implementation_Review.md) | atom |
| claude_v2_9_implementation_review_v2 | [Claude_v2.9_Implementation_Review_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.9/Claude_v2.9_Implementation_Review_v2.md) | atom |
| claude_v2_9_implementation_review_v3 | [Claude_v2.9_Implementation_Review_v3.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.9/Claude_v2.9_Implementation_Review_v3.md) | atom |
| claude_v3_master_plan_review | [Claude_v3_Master_Plan_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/Claude_v3_Master_Plan_Review.md) | atom |
| claude_v3_master_plan_review_v2 | [Claude_v3_Master_Plan_Review_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/Claude_v3_Master_Plan_Review_v2.md) | atom |
| codex_2_5_v1_review | [V1_Codex on v2.5.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.5/V1_Codex on v2.5.md) | atom |
| codex_2_5_v2_review | [V2_Codex on V2.5.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.5/V2_Codex on V2.5.md) | atom |
| codex_2_6_v1_review | [Codex_2.6_v1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Codex_2.6_v1.md) | strategy |
| codex_2_6_v2_review | [Codex_2.6_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Codex_2.6_v2.md) | strategy |
| codex_2_6_v3_review | [Codex_2.6_v3.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Codex_2.6_v3.md) | strategy |
| codex_v2_7_phil_review_v1 | [Codex_V2.7Phil_v1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Codex_V2.7Phil_v1.md) | strategy |
| codex_v2_7_phil_review_v2 | [Codex_V2.7Phil_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Codex_V2.7Phil_v2.md) | atom |
| codex_v2_9_implementation_review | [Codex_v2.9_Implementation_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.9/Codex_v2.9_Implementation_Review.md) | atom |
| common_concepts | [Common_Concepts.md](docs/reference/Common_Concepts.md) | atom |
| dual_mode_matrix | [Dual_Mode_Matrix.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/reference/Dual_Mode_Matrix.md) | atom |
| gemini_2_5_v1_review | [V1_Gemini on v2.5.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.5/V1_Gemini on v2.5.md) | atom |
| gemini_2_5_v2_review | [V2_Gemini on v2.5.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.5/V2_Gemini on v2.5.md) | atom |
| gemini_2_6_v1_review | [Gemini_2.6_v1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Gemini_2.6_v1.md) | atom |
| gemini_2_6_v2_review | [Gemini_2.6_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Gemini_2.6_v2.md) | atom |
| gemini_2_6_v3_review | [Gemini_2.6_v3.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Gemini_2.6_v3.md) | atom |
| gemini_install_ux_review | [Gemini_Review_Installation_UX_Proposal.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Gemini_Review_Installation_UX_Proposal.md) | atom |
| gemini_v2_7_phil_v1 | [Gemini_V2.7Phil_v1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Gemini_V2.7Phil_v1.md) | atom |
| gemini_v2_7_phil_v2 | [Gemini_V2.7Phil_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Gemini_V2.7Phil_v2.md) | atom |
| gemini_v3_master_plan_review_v1 | [v3_master_plan_review_gemini.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/v3_master_plan_review_gemini.md) | atom |
| gemini_v3_master_plan_review_v2 | [v3_master_plan_review_gemini_2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/v3_master_plan_review_gemini_2.md) | atom |
| installation_experience_report | [Ontos_Installation_Experience_Report.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Ontos_Installation_Experience_Report.md) | atom |
| installation_ux_proposal | [Installation_UX_Proposal.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Installation_UX_Proposal.md) | strategy |
| installation_ux_proposal_review | [Installation_UX_Proposal_Review_Codex.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Installation_UX_Proposal_Review_Codex.md) | strategy |
| log_20251217_v2_5_plan_finalization | [2025-12-17_v2-5-plan-finalization.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-5-plan-finalization.md) | log |
| log_20251217_v2_5_promises_implementation | [2025-12-17_v2-5-promises-implementation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-5-promises-implementation.md) | log |
| log_20251217_v2_5_promises_implementation_plan | [2025-12-17_v2-5-promises-implementation-plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-5-promises-implementation-plan.md) | log |
| log_20251217_v2_6_bugfixes | [2025-12-17_v2-6-bugfixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-6-bugfixes.md) | log |
| log_20251217_v2_6_changelog | [2025-12-17_v2-6-changelog.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-6-changelog.md) | log |
| log_20251217_v2_6_codex_fixes | [2025-12-17_v2-6-codex-fixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-6-codex-fixes.md) | log |
| log_20251217_v2_6_docs | [2025-12-17_v2-6-docs.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-6-docs.md) | log |
| log_20251217_v2_6_implementation | [2025-12-17_v2-6-implementation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-6-implementation.md) | log |
| log_20251217_v2_6_maintenance | [2025-12-17_v2-6-maintenance.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-6-maintenance.md) | log |
| log_20251217_v2_6_verification | [2025-12-17_v2-6-verification.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-17_v2-6-verification.md) | log |
| log_20251218_v2_6_1_graduation | [2025-12-18_v2-6-1-graduation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-18_v2-6-1-graduation.md) | log |
| log_20251218_v2_7_documentation_ontology | [2025-12-18_v2-7-documentation-ontology.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-18_v2-7-documentation-ontology.md) | log |
| log_20251218_v2_7_philosophy_proposal | [2025-12-18_v2-7-philosophy-proposal.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-18_v2-7-philosophy-proposal.md) | log |
| log_20251219_chore_maintenance_consolidate_logs_add_frontma | [2025-12-19_chore-maintenance-consolidate-logs-add-frontma.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-19_chore-maintenance-consolidate-logs-add-frontma.md) | log |
| log_20251219_docs_graduate_master_plan_to_strategy_reorganize | [2025-12-19_docs-graduate-master-plan-to-strategy-reorganize.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-19_docs-graduate-master-plan-to-strategy-reorganize.md) | log |
| log_20251219_fix_resolve_all_context_map_validation_errors | [2025-12-19_fix-resolve-all-context-map-validation-errors.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-19_fix-resolve-all-context-map-validation-errors.md) | log |
| log_20251219_v2_7 | [2025-12-19_v2-7.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-19_v2-7.md) | log |
| log_20251219_v2_7_1 | [2025-12-19_v2-7-1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-19_v2-7-1.md) | log |
| log_20251219_v2_7_1_plan | [2025-12-19_v2-7-1-plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-19_v2-7-1-plan.md) | log |
| log_20251220_v2_7_1 | [2025-12-20_v2-7-1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-20_v2-7-1.md) | log |
| log_20251220_v2_8 | [2025-12-20_v2-8.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-20_v2-8.md) | log |
| log_20251220_v2_8_plan_creation | [2025-12-20_v2-8-plan-creation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-20_v2-8-plan-creation.md) | log |
| log_20251220_v2_8_pr24_fixes | [2025-12-20_v2-8-pr24-fixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-20_v2-8-pr24-fixes.md) | log |
| log_20251220_v2_8_version_bump | [2025-12-20_v2-8-version-bump.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-20_v2-8-version-bump.md) | log |
| log_20251221_v2_8_1_minor_fixes | [2025-12-21_v2-8-1-minor-fixes.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-21_v2-8-1-minor-fixes.md) | log |
| log_20251221_v2_8_1_sessioncontext | [2025-12-21_v2-8-1-sessioncontext.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-21_v2-8-1-sessioncontext.md) | log |
| log_20251221_v2_8_2_end_session_refactor | [2025-12-21_v2-8-2-end-session-refactor.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-21_v2-8-2-end-session-refactor.md) | log |
| log_20251221_v2_8_2_phase_1_2_complete | [2025-12-21_v2-8-2-phase-1-2-complete.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-21_v2-8-2-phase-1-2-complete.md) | log |
| log_20251221_v2_8_2_sessioncontext_fix | [2025-12-21_v2-8-2-sessioncontext-fix.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-21_v2-8-2-sessioncontext-fix.md) | log |
| log_20251221_v2_8_3_a_plus_grade | [2025-12-21_v2-8-3-a-plus-grade.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-21_v2-8-3-a-plus-grade.md) | log |
| log_20251221_v2_8_3_chief_architect_gaps | [2025-12-21_v2-8-3-chief-architect-gaps.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-21_v2-8-3-chief-architect-gaps.md) | log |
| log_20251221_v2_8_3_owns_ctx_pattern | [2025-12-21_v2-8-3-owns-ctx-pattern.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-21_v2-8-3-owns-ctx-pattern.md) | log |
| log_20251221_v2_8_3_release | [2025-12-21_v2-8-3-release.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-21_v2-8-3-release.md) | log |
| log_20251221_v2_8_3_setup | [2025-12-21_v2-8-3-setup.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-21_v2-8-3-setup.md) | log |
| log_20251222_v285_unified_cli | [2025-12-22_v285-unified-cli.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-22_v285-unified-cli.md) | log |
| log_20251222_v286_docs_alignment | [2025-12-22_v286-docs-alignment.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-22_v286-docs-alignment.md) | log |
| log_20251222_v290_schema_versioning | [2025-12-22_v290-schema-versioning.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-22_v290-schema-versioning.md) | log |
| log_20251222_v2_9_architectural_review | [2025-12-22_v2-9-architectural-review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-22_v2-9-architectural-review.md) | log |
| master_plan_v4 | [master_plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/master_plan.md) | strategy |
| mission | [mission.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/mission.md) | kernel |
| ontos_agent_instructions | [Ontos_Agent_Instructions.md](docs/reference/Ontos_Agent_Instructions.md) | kernel |
| ontos_codebase_map | [Ontos_Codebase_Map.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/Ontos_Codebase_Map.md) | atom |
| ontos_deep_analysis_brief | [Ontos_Deep_Analysis_Brief.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/Ontos_Deep_Analysis_Brief.md) | atom |
| ontos_manual | [Ontos_Manual.md](docs/reference/Ontos_Manual.md) | kernel |
| pr22_chief_architect_review | [PR22_Chief_Architect_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/PR22_Chief_Architect_Review.md) | atom |
| pr22_chief_architect_review_v2 | [PR22_Chief_Architect_Review_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/PR22_Chief_Architect_Review_v2.md) | atom |
| s3_archive_analysis | [s3-archive-analysis.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/s3-archive-analysis.md) | strategy |
| s3_archive_implementation_plan | [s3-archive-implementation-plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/s3-archive-implementation-plan.md) | strategy |
| schema | [schema.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/schema.md) | atom |
| v2_5_architectural_review_claude | [V1_Claude_on_v2.5.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.5/V1_Claude_on_v2.5.md) | atom |
| v2_5_architectural_review_claude_v2 | [V2_Claude_on_v2.5.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.5/V2_Claude_on_v2.5.md) | atom |
| v2_5_promises_implementation_plan | [v2.5_promises_implementation_plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.5/v2.5_promises_implementation_plan.md) | strategy |
| v2_6_proposals_and_tooling | [v2.6_proposals_and_tooling.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/v2.6_proposals_and_tooling.md) | strategy |
| v2_7_1_implementation_plan | [v2.7.1_implementation_plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/v2.7.1_implementation_plan.md) | strategy |
| v2_7_1_patch_plan | [v2.7.1_patch_plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/v2.7.1_patch_plan.md) | strategy |
| v2_7_documentation_ontology | [v2.7_documentation_ontology.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/v2.7_documentation_ontology.md) | strategy |
| v2_7_implementation_plan | [v2.7_implementation_plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/v2.7_implementation_plan.md) | strategy |
| v2_7_implementation_plan_review_codex | [v2.7_implementation_plan_review_codex.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/v2.7_implementation_plan_review_codex.md) | strategy |
| v2_7_implementation_synthesis | [v2.7_implementation_synthesis.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/v2.7_implementation_synthesis.md) | atom |
| v2_8_implementation_plan | [v2.8_implementation_plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.8/v2.8_implementation_plan.md) | strategy |
| v2_8_implementation_plan_review_codex | [v2.8_implementation_plan_review_codex.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.8/v2.8_implementation_plan_review_codex.md) | strategy |
| v2_9_implementation_plan | [v2.9_implementation_plan.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.9/v2.9_implementation_plan.md) | strategy |
| v2_9_implementation_plan_review_codex | [v2.9_implementation_plan_review_codex.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.9/v2.9_implementation_plan_review_codex.md) | atom |
| v2_9_implementation_plan_review_codex_v2 | [v2.9_implementation_plan_review_codex_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.9/v2.9_implementation_plan_review_codex_v2.md) | atom |
| v2_9_implementation_plan_review_codex_v3 | [v2.9_implementation_plan_review_codex_v3.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.9/v2.9_implementation_plan_review_codex_v3.md) | atom |
| v2_9_implementation_plan_review_gemini | [v2.9_implementation_plan_review_gemini.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.9/v2.9_implementation_plan_review_gemini.md) | atom |
| v2_strategy | [v2_strategy.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2_strategy.md) | strategy |
| v3_master_plan_context_kernel_review_codex | [v3_master_plan_context_kernel_review_codex.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/v3_master_plan_context_kernel_review_codex.md) | strategy |
| v3_master_plan_context_kernel_review_codex_v2 | [v3_master_plan_context_kernel_review_codex_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/v3_master_plan_context_kernel_review_codex_v2.md) | strategy |
| v3_master_plan_context_kernel_review_codex_v3 | [v3_master_plan_context_kernel_review_codex_v3.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/v3_master_plan_context_kernel_review_codex_v3.md) | strategy |


## 5. Documentation Staleness Audit
No documents use the `describes` field.
