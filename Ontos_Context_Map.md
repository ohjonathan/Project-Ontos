<!--
Ontos Context Map
Generated: 2025-12-19 15:45:55 UTC
Mode: Contributor
Scanned: .ontos-internal
-->
> **Note for users:** This context map documents Project Ontos's own development.
> When you run `python3 ontos_init.py` or `python3 .ontos/scripts/ontos_generate_context_map.py`
> in your project, this file will be overwritten with your project's context.

# Ontos Context Map
Generated on: 2025-12-20 00:45:55
Scanned Directory: `/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal, docs`

## 1. Hierarchy Tree
### KERNEL
- **mission** (mission.md) ~377 tokens
  - Status: active
  - Depends On: None
- **ontos_agent_instructions** (Ontos_Agent_Instructions.md) ~2,100 tokens
  - Status: active
  - Depends On: ontos_manual
- **ontos_manual** (Ontos_Manual.md) ~2,900 tokens
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
- **codex_v2_7_phil_review_v1** (Codex_V2.7Phil_v1.md) ~1,100 tokens
  - Status: complete
  - Depends On: None
- **installation_ux_proposal** [draft] (Installation_UX_Proposal.md) ~7,100 tokens
  - Status: draft
  - Depends On: v2_strategy, mission, ontos_manual
- **installation_ux_proposal_review** [draft] (Installation_UX_Proposal_Review_Codex.md) ~948 tokens
  - Status: draft
  - Depends On: installation_ux_proposal, v2_strategy, mission, ontos_manual
- **master_plan_v4** (master_plan.md) ~2,500 tokens
  - Status: active
  - Depends On: mission, v2_strategy
- **s3_archive_analysis** [draft] (s3-archive-analysis.md) ~2,600 tokens
  - Status: draft
  - Depends On: v2_strategy
- **s3_archive_implementation_plan** [draft] (s3-archive-implementation-plan.md) ~8,200 tokens
  - Status: draft
  - Depends On: s3_archive_analysis
- **v2_5_promises_implementation_plan** [draft] (v2.5_promises_implementation_plan.md) ~9,100 tokens
  - Status: draft
  - Depends On: v2_strategy, mission
- **v2_6_proposals_and_tooling** (v2.6_proposals_and_tooling.md) ~11,100 tokens
  - Status: complete
  - Depends On: v2_strategy
- **v2_7_1_implementation_plan** (v2.7.1_implementation_plan.md) ~2,600 tokens
  - Status: complete
  - Depends On: None
- **v2_7_1_patch_plan** (v2.7.1_patch_plan.md) ~994 tokens
  - Status: complete
  - Depends On: None
- **v2_7_documentation_ontology** (v2.7_documentation_ontology.md) ~3,800 tokens
  - Status: complete
  - Depends On: None
- **v2_7_implementation_plan** (v2.7_implementation_plan.md) ~8,300 tokens
  - Status: complete
  - Depends On: None
- **v2_7_implementation_plan_review_codex** (v2.7_implementation_plan_review_codex.md) ~1,000 tokens
  - Status: complete
  - Depends On: None
- **v2_strategy** (v2_strategy.md) ~2,600 tokens
  - Status: active
  - Depends On: mission
- **v3_master_plan_context_kernel_review_codex** [draft] (v3_master_plan_context_kernel_review_codex.md) ~968 tokens
  - Status: draft
  - Depends On: master_plan_v4
- **v3_master_plan_context_kernel_review_codex_v2** [draft] (v3_master_plan_context_kernel_review_codex_v2.md) ~1,000 tokens
  - Status: draft
  - Depends On: master_plan_v4
- **v3_master_plan_context_kernel_review_codex_v3** [draft] (v3_master_plan_context_kernel_review_codex_v3.md) ~1,000 tokens
  - Status: draft
  - Depends On: master_plan_v4

### ATOM
- **architect_synthesis_install_ux** [draft] (Architect_Synthesis_InstallUX.md) ~4,000 tokens
  - Status: draft
  - Depends On: installation_ux_proposal, claude_install_ux_review, gemini_install_ux_review, installation_ux_proposal_review
- **architect_v2_7_phil_synthesis** (Architect_V2.7Phil_Synthesis.md) ~3,500 tokens
  - Status: complete
  - Depends On: None
- **claude_2_6_v1_review** (Claude_2.6_v1.md) ~2,400 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling
- **claude_2_6_v2_review** (Claude_2.6_v2.md) ~1,300 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling, claude_2_6_v1_review
- **claude_2_6_v3_review** (Claude_2.6_v3.md) ~1,400 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling, claude_2_6_v2_review
- **claude_2_7_phil_v1_review** (Claude_V2.7Phil_v1.md) ~2,400 tokens
  - Status: complete
  - Depends On: None
- **claude_2_7_phil_v2_review** (Claude_V2.7Phil_v2.md) ~2,700 tokens
  - Status: complete
  - Depends On: None
- **claude_install_ux_review** (Claude_InstallUX_Review.md) ~3,500 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **claude_v2_7_implementation_review** (Claude_v2.7_Implementation_Review.md) ~3,100 tokens
  - Status: complete
  - Depends On: None
- **claude_v3_master_plan_review** (Claude_v3_Master_Plan_Review.md) ~3,300 tokens
  - Status: complete
  - Depends On: v2_strategy
- **claude_v3_master_plan_review_v2** (Claude_v3_Master_Plan_Review_v2.md) ~3,100 tokens
  - Status: complete
  - Depends On: v2_strategy
- **codex_2_5_v1_review** (V1_Codex on v2.5.md) ~621 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan
- **codex_2_5_v2_review** (V2_Codex on V2.5.md) ~340 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan, codex_2_5_v1_review
- **codex_v2_7_phil_review_v2** (Codex_V2.7Phil_v2.md) ~872 tokens
  - Status: complete
  - Depends On: None
- **common_concepts** (Common_Concepts.md) ~654 tokens
  - Status: active
  - Depends On: None
- **dual_mode_matrix** (Dual_Mode_Matrix.md) ~1,500 tokens
  - Status: active
  - Depends On: schema
- **gemini_2_5_v1_review** (V1_Gemini on v2.5.md) ~941 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan
- **gemini_2_5_v2_review** (V2_Gemini on v2.5.md) ~619 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan, gemini_2_5_v1_review
- **gemini_2_6_v1_review** (Gemini_2.6_v1.md) ~1,400 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling
- **gemini_2_6_v2_review** (Gemini_2.6_v2.md) ~1,300 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling
- **gemini_2_6_v3_review** (Gemini_2.6_v3.md) ~1,200 tokens
  - Status: complete
  - Depends On: v2_6_proposals_and_tooling
- **gemini_install_ux_review** (Gemini_Review_Installation_UX_Proposal.md) ~2,800 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **gemini_v2_7_phil_v1** (Gemini_V2.7Phil_v1.md) ~1,200 tokens
  - Status: complete
  - Depends On: None
- **gemini_v2_7_phil_v2** (Gemini_V2.7Phil_v2.md) ~823 tokens
  - Status: complete
  - Depends On: None
- **gemini_v3_master_plan_review_v1** (v3_master_plan_review_gemini.md) ~1,900 tokens
  - Status: complete
  - Depends On: master_plan_v4
- **gemini_v3_master_plan_review_v2** (v3_master_plan_review_gemini_2.md) ~1,500 tokens
  - Status: complete
  - Depends On: master_plan_v4, gemini_v3_master_plan_review_v1
- **installation_experience_report** (Ontos_Installation_Experience_Report.md) ~2,200 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **ontos_codebase_map** [draft] (Ontos_Codebase_Map.md) ~6,800 tokens
  - Status: draft
  - Depends On: v2_strategy
- **ontos_deep_analysis_brief** [draft] (Ontos_Deep_Analysis_Brief.md) ~4,500 tokens
  - Status: draft
  - Depends On: v2_strategy, mission
- **pr22_chief_architect_review** (PR22_Chief_Architect_Review.md) ~2,700 tokens
  - Status: complete
  - Depends On: None
- **pr22_chief_architect_review_v2** (PR22_Chief_Architect_Review_v2.md) ~1,700 tokens
  - Status: complete
  - Depends On: None
- **schema** (schema.md) ~451 tokens
  - Status: active
  - Depends On: v2_strategy
- **v2_5_architectural_review_claude** (V1_Claude_on_v2.5.md) ~4,600 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan
- **v2_5_architectural_review_claude_v2** (V2_Claude_on_v2.5.md) ~1,900 tokens
  - Status: complete
  - Depends On: v2_5_promises_implementation_plan
- **v2_7_implementation_synthesis** (v2.7_implementation_synthesis.md) ~3,900 tokens
  - Status: complete
  - Depends On: None

### LOG
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
- **log_20251217_v2_6_changelog** (2025-12-17_v2-6-changelog.md) ~99 tokens
  - Status: active
  - Impacts: None
- **log_20251217_v2_6_codex_fixes** (2025-12-17_v2-6-codex-fixes.md) ~119 tokens
  - Status: active
  - Impacts: v2_6_proposals_and_tooling
- **log_20251217_v2_6_docs** (2025-12-17_v2-6-docs.md) ~105 tokens
  - Status: active
  - Impacts: ontos_manual, ontos_agent_instructions
- **log_20251217_v2_6_implementation** (2025-12-17_v2-6-implementation.md) ~136 tokens
  - Status: active
  - Impacts: v2_6_proposals_and_tooling
- **log_20251217_v2_6_maintenance** (2025-12-17_v2-6-maintenance.md) ~172 tokens
  - Status: active
  - Impacts: None
- **log_20251217_v2_6_verification** (2025-12-17_v2-6-verification.md) ~135 tokens
  - Status: active
  - Impacts: v2_6_proposals_and_tooling
- **log_20251218_v2_6_1_graduation** (2025-12-18_v2-6-1-graduation.md) ~971 tokens
  - Status: active
  - Impacts: ontos_agent_instructions, ontos_manual
- **log_20251218_v2_7_documentation_ontology** (2025-12-18_v2-7-documentation-ontology.md) ~572 tokens
  - Status: active
  - Impacts: v2_7_documentation_ontology
- **log_20251218_v2_7_philosophy_proposal** (2025-12-18_v2-7-philosophy-proposal.md) ~904 tokens
  - Status: active
  - Impacts: v2_strategy, v2_7_documentation_ontology
- **log_20251219_chore_maintenance_consolidate_logs_add_frontma** (2025-12-19_chore-maintenance-consolidate-logs-add-frontma.md) ~332 tokens
  - Status: active
  - Impacts: schema
- **log_20251219_docs_graduate_master_plan_to_strategy_reorganize** (2025-12-19_docs-graduate-master-plan-to-strategy-reorganize.md) ~558 tokens
  - Status: active
  - Impacts: master_plan_v4, v2_strategy
- **log_20251219_fix_resolve_all_context_map_validation_errors** (2025-12-19_fix-resolve-all-context-map-validation-errors.md) ~419 tokens
  - Status: active
  - Impacts: schema, architect_v2_7_phil_synthesis, architect_synthesis_install_ux
- **log_20251219_v2_7** (2025-12-19_v2-7.md) ~599 tokens
  - Status: active
  - Impacts: v2_7_documentation_ontology, master_plan_v4, schema
- **log_20251219_v2_7_1** (2025-12-19_v2-7-1.md) ~128 tokens
  - Status: active
  - Impacts: None
- **log_20251219_v2_7_1_plan** (2025-12-19_v2-7-1-plan.md) ~385 tokens
  - Status: active
  - Impacts: v2_7_1_implementation_plan
- **log_20251220_v2_7_1** (2025-12-20_v2-7-1.md) ~383 tokens
  - Status: active
  - Impacts: None


## 2. Recent Timeline
- **2025-12-20** [chore] **V2 7 1** (`log_20251220_v2_7_1`)
- **2025-12-19** [feature] **V2 7** (`log_20251219_v2_7`)
  - Impacted: `v2_7_documentation_ontology`, `master_plan_v4`, `schema`
  - Concepts: describes, staleness, immutable-history, implementation-plan, llm-review
- **2025-12-19** [chore] **V2 7 1** (`log_20251219_v2_7_1`)
- **2025-12-19** [chore] **V2 7 1 Plan** (`log_20251219_v2_7_1_plan`)
  - Impacted: `v2_7_1_implementation_plan`
  - Concepts: testing, documentation
- **2025-12-19** [fix] **Fix Resolve All Context Map Validation Errors** (`log_20251219_fix_resolve_all_context_map_validation_errors`)
  - Impacted: `schema`, `architect_v2_7_phil_synthesis`, `architect_synthesis_install_ux`
  - Concepts: validation, schema, type-hierarchy
- **2025-12-19** [chore] **Docs Graduate Master Plan To Strategy Reorganize** (`log_20251219_docs_graduate_master_plan_to_strategy_reorganize`)
  - Impacted: `master_plan_v4`, `v2_strategy`
  - Concepts: governance, proposals, graduation
- **2025-12-19** [chore] **Chore Maintenance Consolidate Logs Add Frontma** (`log_20251219_chore_maintenance_consolidate_logs_add_frontma`)
  - Impacted: `schema`
  - Concepts: maintenance, consolidation, frontmatter, type-hierarchy
- **2025-12-18** [feature] **V2 7 Philosophy Proposal** (`log_20251218_v2_7_philosophy_proposal`)
  - Impacted: `v2_strategy`, `v2_7_documentation_ontology`
  - Concepts: ontology, bidirectional, documentation
- **2025-12-18** [feature] **V2 7 Documentation Ontology** (`log_20251218_v2_7_documentation_ontology`)
  - Impacted: `v2_7_documentation_ontology`
  - Concepts: ontology, documentation, synthesis, architecture
- **2025-12-18** [feature] **V2 6 1 Graduation** (`log_20251218_v2_6_1_graduation`)
  - Impacted: `ontos_agent_instructions`, `ontos_manual`

*Showing 10 of 20 sessions*

## 3. Dependency Audit
No issues found.

## 4. Index
| ID | Filename | Type |
|---|---|---|
| architect_synthesis_install_ux | [Architect_Synthesis_InstallUX.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Architect_Synthesis_InstallUX.md) | atom |
| architect_v2_7_phil_synthesis | [Architect_V2.7Phil_Synthesis.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Architect_V2.7Phil_Synthesis.md) | atom |
| claude_2_6_v1_review | [Claude_2.6_v1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Claude_2.6_v1.md) | atom |
| claude_2_6_v2_review | [Claude_2.6_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Claude_2.6_v2.md) | atom |
| claude_2_6_v3_review | [Claude_2.6_v3.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Claude_2.6_v3.md) | atom |
| claude_2_7_phil_v1_review | [Claude_V2.7Phil_v1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Claude_V2.7Phil_v1.md) | atom |
| claude_2_7_phil_v2_review | [Claude_V2.7Phil_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Claude_V2.7Phil_v2.md) | atom |
| claude_install_ux_review | [Claude_InstallUX_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Claude_InstallUX_Review.md) | atom |
| claude_v2_7_implementation_review | [Claude_v2.7_Implementation_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Claude_v2.7_Implementation_Review.md) | atom |
| claude_v3_master_plan_review | [Claude_v3_Master_Plan_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/Claude_v3_Master_Plan_Review.md) | atom |
| claude_v3_master_plan_review_v2 | [Claude_v3_Master_Plan_Review_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/Claude_v3_Master_Plan_Review_v2.md) | atom |
| codex_2_5_v1_review | [V1_Codex on v2.5.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.5/V1_Codex on v2.5.md) | atom |
| codex_2_5_v2_review | [V2_Codex on V2.5.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.5/V2_Codex on V2.5.md) | atom |
| codex_2_6_v1_review | [Codex_2.6_v1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Codex_2.6_v1.md) | strategy |
| codex_2_6_v2_review | [Codex_2.6_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Codex_2.6_v2.md) | strategy |
| codex_2_6_v3_review | [Codex_2.6_v3.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2.6/Codex_2.6_v3.md) | strategy |
| codex_v2_7_phil_review_v1 | [Codex_V2.7Phil_v1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Codex_V2.7Phil_v1.md) | strategy |
| codex_v2_7_phil_review_v2 | [Codex_V2.7Phil_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.7/Codex_V2.7Phil_v2.md) | atom |
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
| v2_strategy | [v2_strategy.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2_strategy.md) | strategy |
| v3_master_plan_context_kernel_review_codex | [v3_master_plan_context_kernel_review_codex.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/v3_master_plan_context_kernel_review_codex.md) | strategy |
| v3_master_plan_context_kernel_review_codex_v2 | [v3_master_plan_context_kernel_review_codex_v2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/v3_master_plan_context_kernel_review_codex_v2.md) | strategy |
| v3_master_plan_context_kernel_review_codex_v3 | [v3_master_plan_context_kernel_review_codex_v3.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0 Components/v3_master_plan_context_kernel_review_codex_v3.md) | strategy |


## 5. Documentation Staleness Audit
No documents use the `describes` field.
