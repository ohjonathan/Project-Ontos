<!--
Ontos Context Map
Generated: 2026-01-11 19:15:18 UTC
Mode: Contributor
Scanned: .ontos-internal
-->
> **Note for users:** This context map documents Project Ontos's own development.
> When you run `python3 ontos_init.py` or `python3 .ontos/scripts/ontos_generate_context_map.py`
> in your project, this file will be overwritten with your project's context.

# Ontos Context Map
Generated on: 2026-01-11 14:15:18
Scanned Directory: `/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal, docs`

## 1. Hierarchy Tree
### KERNEL
- **constitution** [L2] (constitution.md) ~292 tokens
  - Status: active
  - Depends On: mission
- **mission** [L2] (mission.md) ~377 tokens
  - Status: active
  - Depends On: None
- **ontos_agent_instructions** [L2] (Ontos_Agent_Instructions.md) ~2,500 tokens
  - Status: active
  - Depends On: ontos_manual
- **ontos_manual** [L2] (Ontos_Manual.md) ~4,200 tokens
  - Status: active
  - Depends On: None
- **philosophy** [L2] (philosophy.md) ~1,700 tokens
  - Status: active
  - Depends On: mission

### STRATEGY
- **installation_ux_proposal** [L2] [draft] (Installation_UX_Proposal.md) ~7,100 tokens
  - Status: draft
  - Depends On: philosophy, mission, ontos_manual
- **installation_ux_proposal_review** [L2] [draft] (Installation_UX_Proposal_Review_Codex.md) ~948 tokens
  - Status: draft
  - Depends On: installation_ux_proposal, philosophy, mission, ontos_manual
- **roadmap** [L2] (roadmap.md) ~1,400 tokens
  - Status: active
  - Depends On: mission, philosophy
- **technical_architecture** [L2] (technical_architecture.md) ~790 tokens
  - Status: active
  - Depends On: mission, philosophy, constitution
- **v2_strategy** [L2] (v2_strategy.md) ~907 tokens
  - Status: active
  - Depends On: philosophy
- **v3_0_security_requirements** [L2] [draft] (v3.0_security_requirements.md) ~5,100 tokens
  - Status: draft
  - Depends On: technical_architecture

### ATOM
- **architect_synthesis_install_ux** [L2] [draft] (Architect_Synthesis_InstallUX.md) ~4,000 tokens
  - Status: draft
  - Depends On: installation_ux_proposal, claude_install_ux_review, gemini_install_ux_review, installation_ux_proposal_review
- **chief_architect_v3_0_analysis** [L2] [draft] (Chief_Architect_v3.0_Comprehensive_Analysis.md) ~4,600 tokens
  - Status: draft
  - Depends On: technical_architecture, v3_0_security_requirements
- **claude_install_ux_review** [L2] (Claude_InstallUX_Review.md) ~3,500 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **common_concepts** [L1] (Common_Concepts.md) ~654 tokens  ⚠️ active
  - Status: active
  - Depends On: None
- **dual_mode_matrix** [L2] (Dual_Mode_Matrix.md) ~1,500 tokens
  - Status: active
  - Depends On: schema
- **gemini_install_ux_review** [L2] (Gemini_Review_Installation_UX_Proposal.md) ~2,800 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **installation_experience_report** [L2] (Ontos_Installation_Experience_Report.md) ~2,200 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **llm_b_chief_architect_v3_board_review** [L2] [draft] (Ontos_v3.0_Board_Review_LLM_B_Chief_Architect_Response.md) ~4,400 tokens
  - Status: draft
  - Depends On: chief_architect_v3_0_analysis
- **ontology_architecture_proposal** [L2] [draft] (Ontology_Architecture_Proposal.md) ~10,900 tokens
  - Status: draft
  - Depends On: technical_architecture, constitution, schema
- **ontos_codebase_map** [L2] [draft] (Ontos_Codebase_Map.md) ~6,300 tokens
  - Status: draft
  - Depends On: philosophy, technical_architecture
- **ontos_deep_analysis_brief** [L2] [draft] (Ontos_Deep_Analysis_Brief.md) ~4,700 tokens
  - Status: draft
  - Depends On: philosophy, mission, technical_architecture
- **schema** [L2] (schema.md) ~450 tokens
  - Status: active
  - Depends On: philosophy

### LOG
- **log_20251218_v2_6_1_graduation** [L1] (2025-12-18_v2-6-1-graduation.md) ~971 tokens  ⚠️ active
  - Status: active
  - Impacts: ontos_agent_instructions, ontos_manual
- **log_20251219_chore_maintenance_consolidate_logs_add_frontma** [L2] (2025-12-19_chore-maintenance-consolidate-logs-add-frontma.md) ~332 tokens
  - Status: active
  - Impacts: schema
- **log_20251219_docs_graduate_master_plan_to_strategy_reorganize** [L2] (2025-12-19_docs-graduate-master-plan-to-strategy-reorganize.md) ~562 tokens
  - Status: active
  - Impacts: roadmap, technical_architecture, philosophy
- **log_20251220_v2_7_1** [L1] (2025-12-20_v2-7-1.md) ~383 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260107_v2_9_5_quality_release** [L1] (2026-01-07_v2-9-5-quality-release.md) ~265 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260108_housekeeping_archive_docs** [L2] (2026-01-08_housekeeping-archive-docs.md) ~465 tokens
  - Status: active
  - Impacts: ontos_codebase_map, ontos_deep_analysis_brief, roadmap, technical_architecture
- **log_20260111_ontology_architecture_research** [L2] (2026-01-11_docs-v3-0-add-technical-architecture-and-finaliz.md) ~1,300 tokens
  - Status: active
  - Impacts: ontology_architecture_proposal, constitution, philosophy, technical_architecture, v2_strategy, schema


## 2. Recent Timeline
- **2026-01-11** [decision] **Docs V3 0 Add Technical Architecture And Finaliz** (`log_20260111_ontology_architecture_research`)
  - Impacted: `ontology_architecture_proposal`, `constitution`, `philosophy`, `technical_architecture`, `v2_strategy`, `schema`
  - Concepts: schema, docs, architecture
- **2026-01-08** [chore] **Housekeeping Archive Docs** (`log_20260108_housekeeping_archive_docs`)
  - Impacted: `ontos_codebase_map`, `ontos_deep_analysis_brief`, `roadmap`, `technical_architecture`
  - Concepts: housekeeping, archival, documentation
- **2026-01-07** [feature] **V2 9 5 Quality Release** (`log_20260107_v2_9_5_quality_release`)
- **2025-12-20** [chore] **V2 7 1** (`log_20251220_v2_7_1`)
- **2025-12-19** [chore] **Docs Graduate Master Plan To Strategy Reorganize** (`log_20251219_docs_graduate_master_plan_to_strategy_reorganize`)
  - Impacted: `roadmap`, `technical_architecture`, `philosophy`
  - Concepts: governance, proposals, graduation
- **2025-12-19** [chore] **Chore Maintenance Consolidate Logs Add Frontma** (`log_20251219_chore_maintenance_consolidate_logs_add_frontma`)
  - Impacted: `schema`
  - Concepts: maintenance, consolidation, frontmatter, type-hierarchy
- **2025-12-18** [feature] **V2 6 1 Graduation** (`log_20251218_v2_6_1_graduation`)
  - Impacted: `ontos_agent_instructions`, `ontos_manual`

## 3. Dependency Audit
No issues found.

## 4. Index
| ID | Filename | Type |
|---|---|---|
| architect_synthesis_install_ux | [Architect_Synthesis_InstallUX.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Architect_Synthesis_InstallUX.md) | atom |
| chief_architect_v3_0_analysis | [Chief_Architect_v3.0_Comprehensive_Analysis.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0-Components/Chief_Architect_v3.0_Comprehensive_Analysis.md) | atom |
| claude_install_ux_review | [Claude_InstallUX_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Claude_InstallUX_Review.md) | atom |
| common_concepts | [Common_Concepts.md](docs/reference/Common_Concepts.md) | atom |
| constitution | [constitution.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/constitution.md) | kernel |
| dual_mode_matrix | [Dual_Mode_Matrix.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/reference/Dual_Mode_Matrix.md) | atom |
| gemini_install_ux_review | [Gemini_Review_Installation_UX_Proposal.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Gemini_Review_Installation_UX_Proposal.md) | atom |
| installation_experience_report | [Ontos_Installation_Experience_Report.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Ontos_Installation_Experience_Report.md) | atom |
| installation_ux_proposal | [Installation_UX_Proposal.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Installation_UX_Proposal.md) | strategy |
| installation_ux_proposal_review | [Installation_UX_Proposal_Review_Codex.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Installation_UX_Proposal_Review_Codex.md) | strategy |
| llm_b_chief_architect_v3_board_review | [Ontos_v3.0_Board_Review_LLM_B_Chief_Architect_Response.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0-Components/Ontos_v3.0_Board_Review_LLM_B_Chief_Architect_Response.md) | atom |
| log_20251218_v2_6_1_graduation | [2025-12-18_v2-6-1-graduation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-18_v2-6-1-graduation.md) | log |
| log_20251219_chore_maintenance_consolidate_logs_add_frontma | [2025-12-19_chore-maintenance-consolidate-logs-add-frontma.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-19_chore-maintenance-consolidate-logs-add-frontma.md) | log |
| log_20251219_docs_graduate_master_plan_to_strategy_reorganize | [2025-12-19_docs-graduate-master-plan-to-strategy-reorganize.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-19_docs-graduate-master-plan-to-strategy-reorganize.md) | log |
| log_20251220_v2_7_1 | [2025-12-20_v2-7-1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-20_v2-7-1.md) | log |
| log_20260107_v2_9_5_quality_release | [2026-01-07_v2-9-5-quality-release.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-07_v2-9-5-quality-release.md) | log |
| log_20260108_housekeeping_archive_docs | [2026-01-08_housekeeping-archive-docs.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-08_housekeeping-archive-docs.md) | log |
| log_20260111_ontology_architecture_research | [2026-01-11_docs-v3-0-add-technical-architecture-and-finaliz.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-11_docs-v3-0-add-technical-architecture-and-finaliz.md) | log |
| mission | [mission.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/mission.md) | kernel |
| ontology_architecture_proposal | [Ontology_Architecture_Proposal.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v2.9.6/Ontology_Architecture_Proposal.md) | atom |
| ontos_agent_instructions | [Ontos_Agent_Instructions.md](docs/reference/Ontos_Agent_Instructions.md) | kernel |
| ontos_codebase_map | [Ontos_Codebase_Map.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0-Components/Ontos_Codebase_Map.md) | atom |
| ontos_deep_analysis_brief | [Ontos_Deep_Analysis_Brief.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/V3.0-Components/Ontos_Deep_Analysis_Brief.md) | atom |
| ontos_manual | [Ontos_Manual.md](docs/reference/Ontos_Manual.md) | kernel |
| philosophy | [philosophy.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/philosophy.md) | kernel |
| roadmap | [roadmap.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/roadmap.md) | strategy |
| schema | [schema.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/schema.md) | atom |
| technical_architecture | [technical_architecture.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/technical_architecture.md) | strategy |
| v2_strategy | [v2_strategy.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v2_strategy.md) | strategy |
| v3_0_security_requirements | [v3.0_security_requirements.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/v3.0/security/v3.0_security_requirements.md) | strategy |


## 5. Documentation Staleness Audit
No documents use the `describes` field.
