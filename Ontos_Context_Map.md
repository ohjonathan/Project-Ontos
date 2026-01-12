<!--
Ontos Context Map
Generated: 2026-01-12 18:04:08 UTC
Mode: Contributor
Scanned: .ontos-internal
-->
> **Note for users:** This context map documents Project Ontos's own development.
> When you run `python3 ontos_init.py` or `python3 .ontos/scripts/ontos_generate_context_map.py`
> in your project, this file will be overwritten with your project's context.

# Ontos Context Map
Generated on: 2026-01-12 13:04:08
Scanned Directory: `/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal, docs`

## 1. Hierarchy Tree
### KERNEL
- **constitution** [L2] (constitution.md) ~292 tokens
  - Status: active
  - Depends On: mission
- **mission** [L2] (mission.md) ~377 tokens
  - Status: active
  - Depends On: None
- **ontology_spec** [L2] (ontology_spec.md) ~702 tokens
  - Status: active
  - Depends On: mission
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
- **phase0_golden_master_spec** [L2] (phase0_implementation_spec.md) ~10,300 tokens
  - Status: active
  - Depends On: v3_0_implementation_roadmap, v3_0_technical_architecture
- **phase1_package_structure_spec** [L2] [draft] (phase1_implementation_spec.md) ~7,300 tokens
  - Status: draft
  - Depends On: phase0_golden_master_spec, v3_0_implementation_roadmap
- **v3_0_implementation_roadmap** [L2] (V3.0-Implementation-Roadmap.md) ~9,800 tokens
  - Status: active
  - Depends On: v3_0_technical_architecture, v3_0_strategy_decisions
- **v3_0_security_requirements** [L2] [draft] (v3.0_security_requirements.md) ~5,100 tokens
  - Status: draft
  - Depends On: v3_0_technical_architecture
- **v3_0_strategy_decisions** [L2] (V3.0-Strategy-Decisions-Final.md) ~1,900 tokens
  - Status: active
  - Depends On: mission, philosophy
- **v3_0_technical_architecture** [L2] (V3.0-Technical-Architecture.md) ~14,000 tokens
  - Status: active
  - Depends On: mission, philosophy, constitution

### ATOM
- **architect_synthesis_install_ux** [L2] [draft] (Architect_Synthesis_InstallUX.md) ~4,000 tokens
  - Status: draft
  - Depends On: installation_ux_proposal, claude_install_ux_review, gemini_install_ux_review, installation_ux_proposal_review
- **claude_install_ux_review** [L2] (Claude_InstallUX_Review.md) ~3,500 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **claude_opus_4_5_phase1_review** [L2] (Claude_Opus_4.5_Phase1_Review.md) ~2,900 tokens
  - Status: complete
  - Depends On: phase1_package_structure_spec
- **claude_opus_4_5_phase1_review_round2** [L2] (Claude_Opus_4.5_Phase1_Review_Round2.md) ~895 tokens
  - Status: complete
  - Depends On: phase1_package_structure_spec, claude_opus_4_5_phase1_review
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
- **log_20251219_docs_graduate_master_plan_to_strategy_reorganize** [L2] (2025-12-19_docs-graduate-master-plan-to-strategy-reorganize.md) ~553 tokens
  - Status: active
  - Impacts: philosophy
- **log_20251220_v2_7_1** [L1] (2025-12-20_v2-7-1.md) ~383 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260107_v2_9_5_quality_release** [L1] (2026-01-07_v2-9-5-quality-release.md) ~265 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260108_housekeeping_archive_docs** [L2] (2026-01-08_housekeeping-archive-docs.md) ~446 tokens
  - Status: active
  - Impacts: None
- **log_20260111_chore_pre_v3_0_documentation_cleanup** [L1] (2026-01-11_chore-pre-v3-0-documentation-cleanup.md) ~110 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260111_fix_v2_9_6_correct_false_implemented_status_cl** [L1] (2026-01-11_fix-v2-9-6-correct-false-implemented-status-cl.md) ~115 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260111_ontology_architecture_research** [L2] (2026-01-11_docs-v3-0-add-technical-architecture-and-finaliz.md) ~1,200 tokens
  - Status: active
  - Impacts: constitution, philosophy, schema
- **log_20260111_v2_9_6** [L1] (2026-01-11_v2-9-6.md) ~126 tokens  ⚠️ active
  - Status: active
  - Impacts: ontology_spec
- **log_20260111_v2_9_6_ontology_architecture** [L1] (2026-01-11_v2-9-6-ontology-architecture.md) ~135 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260111_v2_9_6_round2_revision** [L1] (2026-01-11_v2-9-6-round2-revision.md) ~341 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260112_feat_v2_9_6_ontology_single_source_of_truth** [L2] (2026-01-12_feat-v2-9-6-ontology-single-source-of-truth.md) ~620 tokens
  - Status: active
  - Impacts: ontology_spec
- **log_20260112_phase0_v3_0_alpha** [L2] (2026-01-12_phase0-v3-0-alpha.md) ~734 tokens
  - Status: active
  - Impacts: phase0_golden_master_spec
- **log_20260112_phase1_v3_0_alpha** [L2] (2026-01-12_phase1-v3-0-alpha.md) ~455 tokens
  - Status: active
  - Impacts: v3_0_implementation_roadmap
- **log_20260112_v2_9_6_cleanup** [L2] (2026-01-12_chore-v2-9-6-cleanup.md) ~312 tokens
  - Status: active
  - Impacts: None


## 2. Recent Timeline
- **2026-01-12** [feature] **Phase1 V3 0 Alpha** (`log_20260112_phase1_v3_0_alpha`)
  - Impacted: `v3_0_implementation_roadmap`
  - Concepts: pip-package, cli, refactoring
- **2026-01-12** [feature] **Phase0 V3 0 Alpha** (`log_20260112_phase0_v3_0_alpha`)
  - Impacted: `phase0_golden_master_spec`
  - Concepts: golden-master, testing, v3.0, refactoring, ci-workflow
- **2026-01-12** [feature] **Feat V2 9 6 Ontology Single Source Of Truth** (`log_20260112_feat_v2_9_6_ontology_single_source_of_truth`)
  - Impacted: `ontology_spec`
  - Concepts: ontology, single-source-of-truth, immutability, import-safety
- **2026-01-12** [chore] **Chore V2 9 6 Cleanup** (`log_20260112_v2_9_6_cleanup`)
  - Concepts: cleanup, v2.9.6, housekeeping
- **2026-01-11** [feature] **V2 9 6** (`log_20260111_v2_9_6`)
  - Impacted: `ontology_spec`
- **2026-01-11** [chore] **V2 9 6 Round2 Revision** (`log_20260111_v2_9_6_round2_revision`)
- **2026-01-11** [feature] **V2 9 6 Ontology Architecture** (`log_20260111_v2_9_6_ontology_architecture`)
- **2026-01-11** [chore] **Fix V2 9 6 Correct False Implemented Status Cl** (`log_20260111_fix_v2_9_6_correct_false_implemented_status_cl`)
- **2026-01-11** [decision] **Docs V3 0 Add Technical Architecture And Finaliz** (`log_20260111_ontology_architecture_research`)
  - Impacted: `constitution`, `philosophy`, `schema`
  - Concepts: schema, docs, architecture
- **2026-01-11** [chore] **Chore Pre V3 0 Documentation Cleanup** (`log_20260111_chore_pre_v3_0_documentation_cleanup`)

*Showing 10 of 16 sessions*

## 3. Dependency Audit
- [DEPTH] **claude_opus_4_5_phase1_review_round2** has dependency depth 7 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **claude_opus_4_5_phase1_review** has dependency depth 6 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py

## 4. Index
| ID | Filename | Type |
|---|---|---|
| architect_synthesis_install_ux | [Architect_Synthesis_InstallUX.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Architect_Synthesis_InstallUX.md) | atom |
| claude_install_ux_review | [Claude_InstallUX_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Claude_InstallUX_Review.md) | atom |
| claude_opus_4_5_phase1_review | [Claude_Opus_4.5_Phase1_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase1/Claude_Opus_4.5_Phase1_Review.md) | atom |
| claude_opus_4_5_phase1_review_round2 | [Claude_Opus_4.5_Phase1_Review_Round2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase1/Claude_Opus_4.5_Phase1_Review_Round2.md) | atom |
| common_concepts | [Common_Concepts.md](docs/reference/Common_Concepts.md) | atom |
| constitution | [constitution.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/constitution.md) | kernel |
| dual_mode_matrix | [Dual_Mode_Matrix.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/reference/Dual_Mode_Matrix.md) | atom |
| gemini_install_ux_review | [Gemini_Review_Installation_UX_Proposal.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Gemini_Review_Installation_UX_Proposal.md) | atom |
| installation_experience_report | [Ontos_Installation_Experience_Report.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Ontos_Installation_Experience_Report.md) | atom |
| installation_ux_proposal | [Installation_UX_Proposal.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Installation_UX_Proposal.md) | strategy |
| installation_ux_proposal_review | [Installation_UX_Proposal_Review_Codex.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Installation_UX_Proposal_Review_Codex.md) | strategy |
| log_20251218_v2_6_1_graduation | [2025-12-18_v2-6-1-graduation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-18_v2-6-1-graduation.md) | log |
| log_20251219_chore_maintenance_consolidate_logs_add_frontma | [2025-12-19_chore-maintenance-consolidate-logs-add-frontma.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-19_chore-maintenance-consolidate-logs-add-frontma.md) | log |
| log_20251219_docs_graduate_master_plan_to_strategy_reorganize | [2025-12-19_docs-graduate-master-plan-to-strategy-reorganize.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-19_docs-graduate-master-plan-to-strategy-reorganize.md) | log |
| log_20251220_v2_7_1 | [2025-12-20_v2-7-1.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2025-12-20_v2-7-1.md) | log |
| log_20260107_v2_9_5_quality_release | [2026-01-07_v2-9-5-quality-release.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-07_v2-9-5-quality-release.md) | log |
| log_20260108_housekeeping_archive_docs | [2026-01-08_housekeeping-archive-docs.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-08_housekeeping-archive-docs.md) | log |
| log_20260111_chore_pre_v3_0_documentation_cleanup | [2026-01-11_chore-pre-v3-0-documentation-cleanup.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-11_chore-pre-v3-0-documentation-cleanup.md) | log |
| log_20260111_fix_v2_9_6_correct_false_implemented_status_cl | [2026-01-11_fix-v2-9-6-correct-false-implemented-status-cl.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-11_fix-v2-9-6-correct-false-implemented-status-cl.md) | log |
| log_20260111_ontology_architecture_research | [2026-01-11_docs-v3-0-add-technical-architecture-and-finaliz.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-11_docs-v3-0-add-technical-architecture-and-finaliz.md) | log |
| log_20260111_v2_9_6 | [2026-01-11_v2-9-6.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-11_v2-9-6.md) | log |
| log_20260111_v2_9_6_ontology_architecture | [2026-01-11_v2-9-6-ontology-architecture.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-11_v2-9-6-ontology-architecture.md) | log |
| log_20260111_v2_9_6_round2_revision | [2026-01-11_v2-9-6-round2-revision.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-11_v2-9-6-round2-revision.md) | log |
| log_20260112_feat_v2_9_6_ontology_single_source_of_truth | [2026-01-12_feat-v2-9-6-ontology-single-source-of-truth.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-12_feat-v2-9-6-ontology-single-source-of-truth.md) | log |
| log_20260112_phase0_v3_0_alpha | [2026-01-12_phase0-v3-0-alpha.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-12_phase0-v3-0-alpha.md) | log |
| log_20260112_phase1_v3_0_alpha | [2026-01-12_phase1-v3-0-alpha.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-12_phase1-v3-0-alpha.md) | log |
| log_20260112_v2_9_6_cleanup | [2026-01-12_chore-v2-9-6-cleanup.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-12_chore-v2-9-6-cleanup.md) | log |
| mission | [mission.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/mission.md) | kernel |
| ontology_spec | [ontology_spec.md](docs/reference/ontology_spec.md) | kernel |
| ontos_agent_instructions | [Ontos_Agent_Instructions.md](docs/reference/Ontos_Agent_Instructions.md) | kernel |
| ontos_manual | [Ontos_Manual.md](docs/reference/Ontos_Manual.md) | kernel |
| phase0_golden_master_spec | [phase0_implementation_spec.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase0/phase0_implementation_spec.md) | strategy |
| phase1_package_structure_spec | [phase1_implementation_spec.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase1/phase1_implementation_spec.md) | strategy |
| philosophy | [philosophy.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/philosophy.md) | kernel |
| schema | [schema.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/schema.md) | atom |
| v3_0_implementation_roadmap | [V3.0-Implementation-Roadmap.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/V3.0-Implementation-Roadmap.md) | strategy |
| v3_0_security_requirements | [v3.0_security_requirements.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/v3.0_security_requirements.md) | strategy |
| v3_0_strategy_decisions | [V3.0-Strategy-Decisions-Final.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/V3.0-Strategy-Decisions-Final.md) | strategy |
| v3_0_technical_architecture | [V3.0-Technical-Architecture.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/V3.0-Technical-Architecture.md) | strategy |


## 5. Documentation Staleness Audit
No documents use the `describes` field.
