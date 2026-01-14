---
type: generated
generator: ontos_generate_context_map
generated: "2026-01-14 02:29:38 UTC"
mode: Contributor
scanned: .ontos-internal
---

> **Note for users:** This context map documents Project Ontos's own development.
> When you run `ontos map` in your project, this file will be overwritten with your project's context.

# Ontos Context Map
Generated on: 2026-01-13 21:29:38
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
- **ontos_manual** [L2] (Ontos_Manual.md) ~3,900 tokens
  - Status: active
  - Depends On: None
- **philosophy** [L2] (philosophy.md) ~1,700 tokens
  - Status: active
  - Depends On: mission

### STRATEGY
- **chief_architect_phase3_response** [L2] (Chief_Architect_Phase3_Response.md) ~3,200 tokens
  - Status: active
  - Depends On: phase3_implementation_spec, phase3_review_consolidation
- **install_experience_technical_debt_proposal** [L2] [draft] (Install_Experience_Technical_Debt_Proposal.md) ~2,000 tokens
  - Status: draft
  - Depends On: v3_0_implementation_roadmap, installation_ux_proposal, architect_synthesis_install_ux
- **installation_ux_proposal** [L2] [draft] (Installation_UX_Proposal.md) ~7,100 tokens
  - Status: draft
  - Depends On: philosophy, mission, ontos_manual
- **installation_ux_proposal_review** [L2] [draft] (Installation_UX_Proposal_Review_Codex.md) ~948 tokens
  - Status: draft
  - Depends On: installation_ux_proposal, philosophy, mission, ontos_manual
- **obsidian_compatibility_proposal** [L2] [draft] (Obsidian_Compatibility_Proposal.md) ~2,200 tokens
  - Status: draft
  - Depends On: v3_0_implementation_roadmap
- **phase0_golden_master_spec** [L2] (phase0_implementation_spec.md) ~10,300 tokens
  - Status: active
  - Depends On: v3_0_implementation_roadmap, v3_0_technical_architecture
- **phase1_package_structure_spec** [L2] [draft] (phase1_implementation_spec.md) ~7,300 tokens
  - Status: draft
  - Depends On: phase0_golden_master_spec, v3_0_implementation_roadmap
- **phase2_godscript_reduction_instructions_antigravity** [L2] (Phase2_GodScript_Reduction_Instructions_Antigravity.md) ~4,900 tokens
  - Status: active
  - Depends On: phase2_implementation_spec, phase2_implementation_instructions_antigravity
- **phase2_implementation_instructions_antigravity** [L2] (Phase2_Implementation_Instructions_Antigravity.md) ~3,500 tokens
  - Status: active
  - Depends On: phase2_implementation_spec, v3_0_technical_architecture, v3_0_implementation_roadmap, chief_architect_round2_critical_analysis
- **phase3_final_approval_chief_architect** [L2] (Phase3_Final_Approval_Chief_Architect.md) ~933 tokens
  - Status: complete
  - Depends On: phase3_code_verification_codex, phase3_fix_summary_antigravity, phase3_code_review_consolidation
- **phase3_implementation_prompt_antigravity** [L2] (Phase3_Implementation_Prompt_Antigravity.md) ~8,000 tokens
  - Status: active
  - Depends On: phase3_implementation_spec, chief_architect_phase3_response
- **phase3_implementation_spec** [L2] (Phase3-Implementation-Spec.md) ~7,500 tokens
  - Status: active
  - Depends On: v3_0_implementation_roadmap, v3_0_technical_architecture, phase2_implementation_spec
- **phase3_pr_review_chief_architect** [L2] (Phase3_PR_Review_Chief_Architect.md) ~3,600 tokens
  - Status: active
  - Depends On: phase3_implementation_spec, phase3_implementation_prompt_antigravity
- **phase3_review_consolidation** [L2] (Phase3-Review-Consolidation.md) ~5,100 tokens
  - Status: complete
  - Depends On: phase3_implementation_spec, phase3_review_report_gemini, claude_opus_4_5_phase3_alignment_review, phase3_implementation_spec_review_codex
- **phase4_chief_architect_response** [L2] (Phase4_Chief_Architect_Response.md) ~3,700 tokens
  - Status: complete
  - Depends On: phase4_spec_review_consolidation
- **phase4_code_review_claude** [L2] (Phase4_Code_Review_Claude.md) ~2,100 tokens
  - Status: complete
  - Depends On: phase4_implementation_spec
- **phase4_implementation_spec** [L2] (Phase4-Implementation-Spec.md) ~7,800 tokens
  - Status: approved
  - Depends On: phase3_final_approval_chief_architect
- **phase5_code_review_claude** [L2] (Phase5_Code_Review_Claude.md) ~1,500 tokens
  - Status: complete
  - Depends On: phase5_implementation_spec
- **phase5_implementation_spec** [L2] (Phase5-Implementation-Spec.md) ~1,000 tokens
  - Status: active
  - Depends On: phase4_final_approval_chief_architect
- **phase5_spec_review_claude** [L2] (Phase5_Spec_Review_Claude.md) ~1,200 tokens
  - Status: complete
  - Depends On: phase5_implementation_spec
- **v3_0_implementation_roadmap** [L2] (V3.0-Implementation-Roadmap.md) ~10,000 tokens
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
- **v3_1_0_obsidian_compatibility_spec** [L2] [draft] (V3.1.0-Obsidian-Compatibility-Spec.md) ~1,900 tokens
  - Status: draft
  - Depends On: v3_0_implementation_roadmap

### ATOM
- **architect_synthesis_install_ux** [L2] [draft] (Architect_Synthesis_InstallUX.md) ~4,000 tokens
  - Status: draft
  - Depends On: installation_ux_proposal, claude_install_ux_review, gemini_install_ux_review, installation_ux_proposal_review
- **chief_architect_round2_critical_analysis** [L2] (Chief_Architect_Round2_Critical_Analysis.md) ~1,800 tokens
  - Status: complete
  - Depends On: phase2_implementation_spec, phase2_spec_verification_review_gemini, phase2_implementation_spec_verification_review_codex_round2, claude_opus_4_5_phase2_verification_review
- **claude_install_ux_review** [L2] (Claude_InstallUX_Review.md) ~3,500 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **claude_opus_4_5_phase1_review** [L2] (Claude_Opus_4.5_Phase1_Review.md) ~2,900 tokens
  - Status: complete
  - Depends On: phase1_package_structure_spec
- **claude_opus_4_5_phase1_review_round2** [L2] (Claude_Opus_4.5_Phase1_Review_Round2.md) ~895 tokens
  - Status: complete
  - Depends On: phase1_package_structure_spec, claude_opus_4_5_phase1_review
- **claude_opus_4_5_phase2_alignment_review** [L2] (Claude_Opus_4.5_Phase2_Alignment_Review.md) ~3,100 tokens
  - Status: complete
  - Depends On: phase2_implementation_spec, v3_0_implementation_roadmap, v3_0_technical_architecture, v3_0_strategy_decisions
- **claude_opus_4_5_phase2_verification_review** [L2] (Claude_Opus_4.5_Phase2_Verification_Review.md) ~1,000 tokens
  - Status: complete
  - Depends On: phase2_implementation_spec, phase2_implementation_spec_review_consolidation, chief_architect_phase2_response
- **claude_opus_4_5_phase3_alignment_review** [L2] (Claude_Opus_4.5_Phase3_Alignment_Review.md) ~3,200 tokens
  - Status: complete
  - Depends On: phase3_implementation_spec, v3_0_implementation_roadmap, v3_0_technical_architecture, v3_0_strategy_decisions
- **common_concepts** [L1] (Common_Concepts.md) ~737 tokens  ⚠️ active
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
- **log_20260112_phase1_package_structure_complete** [L1] (2026-01-12_phase1-package-structure-complete.md) ~115 tokens  ⚠️ active
  - Status: active
  - Impacts: ontos, packaging, CLI
- **log_20260112_phase1_v3_0_alpha** [L2] (2026-01-12_phase1-v3-0-alpha.md) ~455 tokens
  - Status: active
  - Impacts: v3_0_implementation_roadmap
- **log_20260112_phase2_core_decomposition** [L1] (2026-01-12_phase2-core-decomposition.md) ~107 tokens  ⚠️ active
  - Status: active
  - Impacts: ontos
- **log_20260112_v2_9_6_cleanup** [L2] (2026-01-12_chore-v2-9-6-cleanup.md) ~312 tokens
  - Status: active
  - Impacts: None
- **log_20260113_phase2_v3_0_beta** [L1] (2026-01-13_phase2-v3-0-beta.md) ~192 tokens  ⚠️ auto-generated
  - Status: auto-generated
  - Impacts: None
- **log_20260113_phase4_cli_release** [L2] (2026-01-13_phase4_cli_release.md) ~1,800 tokens
  - Status: active
  - Impacts: ontos_manual, cli, json_output, hook, doctor, export

### UNKNOWN
- **migration_v2_to_v3** [L2] (Migration_v2_to_v3.md) ~760 tokens
  - Status: active
  - Depends On: ontos_manual
- **phase3_implementation_spec_review_codex** [L0] [draft] (Phase3-Implementation-Spec-Review-Codex.md) ~2,100 tokens  ⚠️ draft
  - Status: draft
  - Depends On: None
- **phase4_final_approval_chief_architect** [L2] (Phase4_Final_Approval_Chief_Architect.md) ~776 tokens
  - Status: complete
  - Depends On: phase4_pr_review_chief_architect
- **phase4_pr_review_chief_architect** [L2] (Phase4_PR_Review_Chief_Architect.md) ~1,600 tokens
  - Status: complete
  - Depends On: phase4_chief_architect_response


## 2. Recent Timeline
- **2026-01-13** [None] **Phase4 Cli Release** (`log_20260113_phase4_cli_release`)
  - Impacted: `ontos_manual`, `cli`, `json_output`, `hook`, `doctor`, `export`
  - Concepts: argparse_cli, json_output, shim_hooks, legacy_cleanup
- **2026-01-13** [chore] **Phase2 V3 0 Beta** (`log_20260113_phase2_v3_0_beta`)
- **2026-01-12** [chore] **Phase2 Core Decomposition** (`log_20260112_phase2_core_decomposition`)
  - Impacted: `ontos`
- **2026-01-12** [feature] **Phase1 V3 0 Alpha** (`log_20260112_phase1_v3_0_alpha`)
  - Impacted: `v3_0_implementation_roadmap`
  - Concepts: pip-package, cli, refactoring
- **2026-01-12** [chore] **Phase1 Package Structure Complete** (`log_20260112_phase1_package_structure_complete`)
  - Impacted: `ontos`, `packaging`, `CLI`
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

*Showing 10 of 20 sessions*

## 3. Dependency Audit
- [BROKEN LINK] **phase4_chief_architect_response** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase4/Phase4_Chief_Architect_Response.md) references missing ID: `phase4_spec_review_consolidation`
  Fix: Add a document with `id: phase4_spec_review_consolidation` or remove it from depends_on
- [BROKEN LINK] **phase3_final_approval_chief_architect** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase3/Phase3_Final_Approval_Chief_Architect.md) references missing ID: `phase3_code_verification_codex`
  Fix: Add a document with `id: phase3_code_verification_codex` or remove it from depends_on
- [BROKEN LINK] **phase3_final_approval_chief_architect** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase3/Phase3_Final_Approval_Chief_Architect.md) references missing ID: `phase3_fix_summary_antigravity`
  Fix: Add a document with `id: phase3_fix_summary_antigravity` or remove it from depends_on
- [BROKEN LINK] **phase3_final_approval_chief_architect** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase3/Phase3_Final_Approval_Chief_Architect.md) references missing ID: `phase3_code_review_consolidation`
  Fix: Add a document with `id: phase3_code_review_consolidation` or remove it from depends_on
- [BROKEN LINK] **phase3_implementation_spec** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase3/Phase3-Implementation-Spec.md) references missing ID: `phase2_implementation_spec`
  Fix: Add a document with `id: phase2_implementation_spec` or remove it from depends_on
- [BROKEN LINK] **phase3_review_consolidation** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase3/Phase3-Review-Consolidation.md) references missing ID: `phase3_review_report_gemini`
  Fix: Add a document with `id: phase3_review_report_gemini` or remove it from depends_on
- [BROKEN LINK] **claude_opus_4_5_phase2_alignment_review** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Claude_Opus_4.5_Phase2_Alignment_Review.md) references missing ID: `phase2_implementation_spec`
  Fix: Add a document with `id: phase2_implementation_spec` or remove it from depends_on
- [BROKEN LINK] **claude_opus_4_5_phase2_verification_review** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Claude_Opus_4.5_Phase2_Verification_Review.md) references missing ID: `phase2_implementation_spec`
  Fix: Add a document with `id: phase2_implementation_spec` or remove it from depends_on
- [BROKEN LINK] **claude_opus_4_5_phase2_verification_review** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Claude_Opus_4.5_Phase2_Verification_Review.md) references missing ID: `phase2_implementation_spec_review_consolidation`
  Fix: Add a document with `id: phase2_implementation_spec_review_consolidation` or remove it from depends_on
- [BROKEN LINK] **claude_opus_4_5_phase2_verification_review** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Claude_Opus_4.5_Phase2_Verification_Review.md) references missing ID: `chief_architect_phase2_response`
  Fix: Add a document with `id: chief_architect_phase2_response` or remove it from depends_on
- [BROKEN LINK] **chief_architect_round2_critical_analysis** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Chief_Architect_Round2_Critical_Analysis.md) references missing ID: `phase2_implementation_spec`
  Fix: Add a document with `id: phase2_implementation_spec` or remove it from depends_on
- [BROKEN LINK] **chief_architect_round2_critical_analysis** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Chief_Architect_Round2_Critical_Analysis.md) references missing ID: `phase2_spec_verification_review_gemini`
  Fix: Add a document with `id: phase2_spec_verification_review_gemini` or remove it from depends_on
- [BROKEN LINK] **chief_architect_round2_critical_analysis** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Chief_Architect_Round2_Critical_Analysis.md) references missing ID: `phase2_implementation_spec_verification_review_codex_round2`
  Fix: Add a document with `id: phase2_implementation_spec_verification_review_codex_round2` or remove it from depends_on
- [BROKEN LINK] **phase2_godscript_reduction_instructions_antigravity** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Phase2_GodScript_Reduction_Instructions_Antigravity.md) references missing ID: `phase2_implementation_spec`
  Fix: Add a document with `id: phase2_implementation_spec` or remove it from depends_on
- [BROKEN LINK] **phase2_implementation_instructions_antigravity** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Phase2_Implementation_Instructions_Antigravity.md) references missing ID: `phase2_implementation_spec`
  Fix: Add a document with `id: phase2_implementation_spec` or remove it from depends_on
- [ORPHAN] **migration_v2_to_v3** (docs/reference/Migration_v2_to_v3.md) has no dependents
  Fix: Add `migration_v2_to_v3` to another document's depends_on, or delete if unused
- [DEPTH] **claude_opus_4_5_phase1_review_round2** has dependency depth 7 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **phase3_implementation_prompt_antigravity** has dependency depth 8 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **phase3_pr_review_chief_architect** has dependency depth 9 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **phase3_review_consolidation** has dependency depth 6 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **chief_architect_phase3_response** has dependency depth 7 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **claude_opus_4_5_phase1_review** has dependency depth 6 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [ARCHITECTURE] **phase3_review_consolidation** (strategy) depends on **claude_opus_4_5_phase3_alignment_review** (atom)
  Fix: strategy should not depend on atom. Invert the dependency or change document types
- [ARCHITECTURE] **phase3_review_consolidation** (strategy) depends on **phase3_implementation_spec_review_codex** (unknown)
  Fix: strategy should not depend on unknown. Invert the dependency or change document types
- [ARCHITECTURE] **phase2_implementation_instructions_antigravity** (strategy) depends on **chief_architect_round2_critical_analysis** (atom)
  Fix: strategy should not depend on atom. Invert the dependency or change document types
- [ARCHITECTURE] **phase5_implementation_spec** (strategy) depends on **phase4_final_approval_chief_architect** (approval)
  Fix: strategy should not depend on approval. Invert the dependency or change document types
- [ARCHITECTURE] **install_experience_technical_debt_proposal** (strategy) depends on **architect_synthesis_install_ux** (atom)
  Fix: strategy should not depend on atom. Invert the dependency or change document types
- [MISSING FIELD] **log_20260113_phase4_cli_release** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-13_phase4_cli_release.md) is type 'log' but missing required field: event_type
  Fix: Add `event_type: feature|fix|refactor|exploration|chore` to frontmatter
- [BROKEN LINK] **log_20260112_phase2_core_decomposition** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-12_phase2-core-decomposition.md) impacts non-existent document: `ontos`
  Fix: Create `ontos`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260112_phase1_package_structure_complete** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-12_phase1-package-structure-complete.md) impacts non-existent document: `ontos`
  Fix: Create `ontos`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260112_phase1_package_structure_complete** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-12_phase1-package-structure-complete.md) impacts non-existent document: `packaging`
  Fix: Create `packaging`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260112_phase1_package_structure_complete** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-12_phase1-package-structure-complete.md) impacts non-existent document: `CLI`
  Fix: Create `CLI`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260113_phase4_cli_release** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-13_phase4_cli_release.md) impacts non-existent document: `cli`
  Fix: Create `cli`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260113_phase4_cli_release** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-13_phase4_cli_release.md) impacts non-existent document: `json_output`
  Fix: Create `json_output`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260113_phase4_cli_release** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-13_phase4_cli_release.md) impacts non-existent document: `hook`
  Fix: Create `hook`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260113_phase4_cli_release** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-13_phase4_cli_release.md) impacts non-existent document: `doctor`
  Fix: Create `doctor`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260113_phase4_cli_release** (/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-13_phase4_cli_release.md) impacts non-existent document: `export`
  Fix: Create `export`, correct the reference, or archive this log
- [LINT] **log_20260113_phase2_v3_0_beta**: Invalid status 'auto-generated'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **phase4_implementation_spec**: Invalid status 'approved'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold

## 4. Index
| ID | Filename | Type |
|---|---|---|
| architect_synthesis_install_ux | [Architect_Synthesis_InstallUX.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Architect_Synthesis_InstallUX.md) | atom |
| chief_architect_phase3_response | [Chief_Architect_Phase3_Response.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase3/Chief_Architect_Phase3_Response.md) | strategy |
| chief_architect_round2_critical_analysis | [Chief_Architect_Round2_Critical_Analysis.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Chief_Architect_Round2_Critical_Analysis.md) | atom |
| claude_install_ux_review | [Claude_InstallUX_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Claude_InstallUX_Review.md) | atom |
| claude_opus_4_5_phase1_review | [Claude_Opus_4.5_Phase1_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase1/Claude_Opus_4.5_Phase1_Review.md) | atom |
| claude_opus_4_5_phase1_review_round2 | [Claude_Opus_4.5_Phase1_Review_Round2.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase1/Claude_Opus_4.5_Phase1_Review_Round2.md) | atom |
| claude_opus_4_5_phase2_alignment_review | [Claude_Opus_4.5_Phase2_Alignment_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Claude_Opus_4.5_Phase2_Alignment_Review.md) | atom |
| claude_opus_4_5_phase2_verification_review | [Claude_Opus_4.5_Phase2_Verification_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Claude_Opus_4.5_Phase2_Verification_Review.md) | atom |
| claude_opus_4_5_phase3_alignment_review | [Claude_Opus_4.5_Phase3_Alignment_Review.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase3/Claude_Opus_4.5_Phase3_Alignment_Review.md) | atom |
| common_concepts | [Common_Concepts.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/reference/Common_Concepts.md) | atom |
| constitution | [constitution.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/constitution.md) | kernel |
| dual_mode_matrix | [Dual_Mode_Matrix.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/reference/Dual_Mode_Matrix.md) | atom |
| gemini_install_ux_review | [Gemini_Review_Installation_UX_Proposal.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_experience/Gemini_Review_Installation_UX_Proposal.md) | atom |
| install_experience_technical_debt_proposal | [Install_Experience_Technical_Debt_Proposal.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Install_Experience_Technical_Debt_Proposal.md) | strategy |
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
| log_20260112_phase1_package_structure_complete | [2026-01-12_phase1-package-structure-complete.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-12_phase1-package-structure-complete.md) | log |
| log_20260112_phase1_v3_0_alpha | [2026-01-12_phase1-v3-0-alpha.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-12_phase1-v3-0-alpha.md) | log |
| log_20260112_phase2_core_decomposition | [2026-01-12_phase2-core-decomposition.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-12_phase2-core-decomposition.md) | log |
| log_20260112_v2_9_6_cleanup | [2026-01-12_chore-v2-9-6-cleanup.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-12_chore-v2-9-6-cleanup.md) | log |
| log_20260113_phase2_v3_0_beta | [2026-01-13_phase2-v3-0-beta.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-13_phase2-v3-0-beta.md) | log |
| log_20260113_phase4_cli_release | [2026-01-13_phase4_cli_release.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/logs/2026-01-13_phase4_cli_release.md) | log |
| migration_v2_to_v3 | [Migration_v2_to_v3.md](docs/reference/Migration_v2_to_v3.md) | reference |
| mission | [mission.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/mission.md) | kernel |
| obsidian_compatibility_proposal | [Obsidian_Compatibility_Proposal.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/proposals/Obsidian_Compatibility_Proposal.md) | strategy |
| ontology_spec | [ontology_spec.md](docs/reference/ontology_spec.md) | kernel |
| ontos_agent_instructions | [Ontos_Agent_Instructions.md](docs/reference/Ontos_Agent_Instructions.md) | kernel |
| ontos_manual | [Ontos_Manual.md](docs/reference/Ontos_Manual.md) | kernel |
| phase0_golden_master_spec | [phase0_implementation_spec.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase0/phase0_implementation_spec.md) | strategy |
| phase1_package_structure_spec | [phase1_implementation_spec.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase1/phase1_implementation_spec.md) | strategy |
| phase2_godscript_reduction_instructions_antigravity | [Phase2_GodScript_Reduction_Instructions_Antigravity.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Phase2_GodScript_Reduction_Instructions_Antigravity.md) | strategy |
| phase2_implementation_instructions_antigravity | [Phase2_Implementation_Instructions_Antigravity.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase2/Phase2_Implementation_Instructions_Antigravity.md) | strategy |
| phase3_final_approval_chief_architect | [Phase3_Final_Approval_Chief_Architect.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase3/Phase3_Final_Approval_Chief_Architect.md) | strategy |
| phase3_implementation_prompt_antigravity | [Phase3_Implementation_Prompt_Antigravity.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase3/Phase3_Implementation_Prompt_Antigravity.md) | strategy |
| phase3_implementation_spec | [Phase3-Implementation-Spec.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase3/Phase3-Implementation-Spec.md) | strategy |
| phase3_implementation_spec_review_codex | [Phase3-Implementation-Spec-Review-Codex.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase3/Phase3-Implementation-Spec-Review-Codex.md) | unknown |
| phase3_pr_review_chief_architect | [Phase3_PR_Review_Chief_Architect.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase3/Phase3_PR_Review_Chief_Architect.md) | strategy |
| phase3_review_consolidation | [Phase3-Review-Consolidation.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase3/Phase3-Review-Consolidation.md) | strategy |
| phase4_chief_architect_response | [Phase4_Chief_Architect_Response.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase4/Phase4_Chief_Architect_Response.md) | strategy |
| phase4_code_review_claude | [Phase4_Code_Review_Claude.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase4/Phase4_Code_Review_Claude.md) | strategy |
| phase4_final_approval_chief_architect | [Phase4_Final_Approval_Chief_Architect.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase4/Phase4_Final_Approval_Chief_Architect.md) | approval |
| phase4_implementation_spec | [Phase4-Implementation-Spec.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase4/Phase4-Implementation-Spec.md) | strategy |
| phase4_pr_review_chief_architect | [Phase4_PR_Review_Chief_Architect.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase4/Phase4_PR_Review_Chief_Architect.md) | review |
| phase5_code_review_claude | [Phase5_Code_Review_Claude.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase5/Phase5_Code_Review_Claude.md) | strategy |
| phase5_implementation_spec | [Phase5-Implementation-Spec.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase5/Phase5-Implementation-Spec.md) | strategy |
| phase5_spec_review_claude | [Phase5_Spec_Review_Claude.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/Phase5/Phase5_Spec_Review_Claude.md) | strategy |
| philosophy | [philosophy.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/kernel/philosophy.md) | kernel |
| schema | [schema.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/atom/schema.md) | atom |
| v3_0_implementation_roadmap | [V3.0-Implementation-Roadmap.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/V3.0-Implementation-Roadmap.md) | strategy |
| v3_0_security_requirements | [v3.0_security_requirements.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/v3.0_security_requirements.md) | strategy |
| v3_0_strategy_decisions | [V3.0-Strategy-Decisions-Final.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/V3.0-Strategy-Decisions-Final.md) | strategy |
| v3_0_technical_architecture | [V3.0-Technical-Architecture.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.0/V3.0-Technical-Architecture.md) | strategy |
| v3_1_0_obsidian_compatibility_spec | [V3.1.0-Obsidian-Compatibility-Spec.md](/Users/jonathanoh/Dev/Project-Ontos/.ontos-internal/strategy/v3.1/V3.1.0-Obsidian-Compatibility-Spec.md) | strategy |


## 5. Documentation Staleness Audit
No documents use the `describes` field.
