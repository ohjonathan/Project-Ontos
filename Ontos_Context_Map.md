---
type: generated
generator: ontos_generate_context_map
generated: "2026-01-29 05:25:59 UTC"
mode: Contributor
scanned: .ontos-internal
---

> **Note for users:** This context map documents Project Ontos's own development.
> When you run `ontos map` in your project, this file will be overwritten with your project's context.

# Ontos Context Map
Generated on: 2026-01-29 00:25:59
Scanned Directory: `/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal, docs`

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
- **ontos_manual** [L2] (Ontos_Manual.md) ~4,300 tokens
  - Status: active
  - Depends On: None
- **ontos_philosophy_and_ontology** [L2] (Ontos_Philosophy_and_Ontology_v2_draft.md) ~7,300 tokens
  - Status: active
  - Depends On: mission, philosophy, constitution
- **philosophy** [L2] (philosophy.md) ~1,700 tokens
  - Status: active
  - Depends On: mission

### STRATEGY
- **chatgpt_analysis_response** [L2] [draft] (chatgpt_analysis_response.md) ~1,700 tokens
  - Status: draft
  - Depends On: v3_2_backlog
- **chatgpt_round2_response** [L2] [draft] (chatgpt_round2_response.md) ~1,400 tokens
  - Status: draft
  - Depends On: chatgpt_analysis_response, v3_2_backlog
- **chief_architect_phase3_response** [L2] (Chief_Architect_Phase3_Response.md) ~3,200 tokens
  - Status: active
  - Depends On: phase3_implementation_spec
- **claude_analysis_response** [L2] [draft] (claude_analysis_response.md) ~1,400 tokens
  - Status: draft
  - Depends On: v3_2_backlog
- **claude_round2_response** [L2] [draft] (claude_round2_response.md) ~448 tokens
  - Status: draft
  - Depends On: claude_analysis_response, v3_2_backlog
- **gemini_analysis_response** [L2] [draft] (gemini_analysis_response.md) ~1,400 tokens
  - Status: draft
  - Depends On: v3_2_backlog
- **install_experience_technical_debt_proposal** [L2] [draft] (Install_Experience_Technical_Debt_Proposal.md) ~2,000 tokens
  - Status: draft
  - Depends On: v3_0_implementation_roadmap, installation_ux_proposal
- **installation_ux_proposal** [L2] [draft] (Installation_UX_Proposal.md) ~7,100 tokens
  - Status: draft
  - Depends On: philosophy, mission
- **installation_ux_proposal_review** [L2] [draft] (Installation_UX_Proposal_Review_Codex.md) ~944 tokens
  - Status: draft
  - Depends On: installation_ux_proposal, philosophy, mission
- **maintain_command_v3_proposal** [L2] [draft] (Maintain_Command_v3_Proposal.md) ~1,800 tokens
  - Status: draft
  - Depends On: v3_0_implementation_roadmap, v3_0_technical_architecture
- **obsidian_compatibility_proposal** [L2] [draft] (Obsidian_Compatibility_Proposal.md) ~2,200 tokens
  - Status: draft
  - Depends On: v3_0_implementation_roadmap
- **ontos_claude_code_skill_proposal** [L2] [draft] (Ontos_Claude_Code_Skill_Proposal.md) ~1,300 tokens
  - Status: draft
  - Depends On: ontos_manual, ontos_agent_instructions
- **ontos_strategic_analysis** [L2] (Ontos-Strategic-Analysis.md) ~3,400 tokens
  - Status: active
  - Depends On: mission, philosophy, v3_0_technical_architecture
- **ontos_strategic_analysis_codex** [L2] (Ontos-Strategic-Analysis-Codex.md) ~3,200 tokens
  - Status: active
  - Depends On: mission, philosophy, v3_0_technical_architecture
- **phase0_golden_master_spec** [L2] (phase0_implementation_spec.md) ~10,300 tokens
  - Status: active
  - Depends On: v3_0_implementation_roadmap, v3_0_technical_architecture
- **phase1_package_structure_spec** [L2] [draft] (phase1_implementation_spec.md) ~7,300 tokens
  - Status: draft
  - Depends On: v3_0_implementation_roadmap
- **phase2_godscript_reduction_instructions_antigravity** [L2] (Phase2_GodScript_Reduction_Instructions_Antigravity.md) ~4,900 tokens
  - Status: active
  - Depends On: phase2_implementation_instructions_antigravity
- **phase2_implementation_instructions_antigravity** [L2] (Phase2_Implementation_Instructions_Antigravity.md) ~3,500 tokens
  - Status: active
  - Depends On: v3_0_technical_architecture, v3_0_implementation_roadmap, chief_architect_round2_critical_analysis
- **phase3_final_approval_chief_architect** [L1] (Phase3_Final_Approval_Chief_Architect.md) ~909 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **phase3_implementation_prompt_antigravity** [L2] (Phase3_Implementation_Prompt_Antigravity.md) ~8,000 tokens
  - Status: active
  - Depends On: phase3_implementation_spec
- **phase3_implementation_spec** [L2] (Phase3-Implementation-Spec.md) ~7,500 tokens
  - Status: active
  - Depends On: v3_0_implementation_roadmap, v3_0_technical_architecture
- **phase3_pr_review_chief_architect** [L2] (Phase3_PR_Review_Chief_Architect.md) ~3,600 tokens
  - Status: active
  - Depends On: phase3_implementation_spec
- **phase3_review_consolidation** [L2] (Phase3-Review-Consolidation.md) ~5,100 tokens
  - Status: complete
  - Depends On: phase3_implementation_spec
- **phase4_chief_architect_response** [L1] (Phase4_Chief_Architect_Response.md) ~3,700 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
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
- **v3_0_2_cli_legacy_remediation** [L2] [draft] (v3.0.3_CLI_Legacy_Remediation_Proposal.md) ~3,100 tokens
  - Status: draft
  - Depends On: v3_0_technical_architecture
- **v3_0_2_tech_debt_resolution_proposal** [L2] [draft] (v3.0.3_Tech_Debt_Resolution_Proposal.md) ~616 tokens
  - Status: draft
  - Depends On: install_experience_technical_debt_proposal
- **v3_0_4_chief_architect_notes** [L2] (v3.0.4_CA_Notes.md) ~1,300 tokens
  - Status: active
  - Depends On: phase_v3_0_4_implementation_spec
- **v3_0_4_cli_wrapper_fix_proposal** [L2] (v3.0.4_CLI_Wrapper_Fix_Proposal.md) ~2,000 tokens
  - Status: approved
  - Depends On: v3_0_3_implementation_spec
- **v3_0_implementation_roadmap** [L2] (V3.0-Implementation-Roadmap.md) ~10,100 tokens
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
- **v3_1_0_implementation_plan** [L2] [draft] (V3.1.0-Implementation-Plan.md) ~2,600 tokens
  - Status: draft
  - Depends On: v3_0_implementation_roadmap, v3_1_0_obsidian_compatibility_spec
- **v3_1_0_implementation_spec** [L2] (v3_1_0_Implementation_Spec_v1.2.md) ~10,100 tokens
  - Status: approved
  - Depends On: v3_0_5_implementation_spec, v3_1_0_implementation_plan, v3_1_tech_debt_wrapper_commands
- **v3_1_0_obsidian_compatibility_spec** [L2] [draft] (V3.1.0-Obsidian-Compatibility-Spec.md) ~1,900 tokens
  - Status: draft
  - Depends On: v3_0_implementation_roadmap
- **v3_1_0_sidecar_pattern** [L2] [draft] (V3.1.0-Sidecar-Pattern.md) ~994 tokens
  - Status: draft
  - Depends On: v3_1_0_implementation_plan
- **v3_1_1_chief_architect_response** [L2] (v3.1.1_Chief_Architect_Response.md) ~2,100 tokens
  - Status: active
  - Depends On: v3_1_1_init_improvements_proposal
- **v3_1_1_final_approval** [L2] (v3.1.1_Final_Approval_Chief_Architect.md) ~513 tokens
  - Status: approved
  - Depends On: v3_1_1_implementation_spec, v3_1_1_pr_review_chief_architect
- **v3_1_1_implementation_prompt_antigravity** [L2] (v3.1.1_Implementation_Prompt_Antigravity.md) ~9,300 tokens
  - Status: approved
  - Depends On: v3_1_1_implementation_spec
- **v3_1_1_implementation_spec** [L2] (v3.1.1-Implementation-Spec.md) ~3,400 tokens
  - Status: approved
  - Depends On: v3_1_1_init_improvements_proposal, v3_1_1_chief_architect_response
- **v3_1_1_init_improvements_proposal** [L2] [draft] (init_improvements_proposal.md) ~3,400 tokens
  - Status: draft
  - Depends On: mission, philosophy, constitution, v3_0_technical_architecture
- **v3_1_1_pr_review_chief_architect** [L2] (v3.1.1_PR_Review_Chief_Architect.md) ~1,700 tokens
  - Status: active
  - Depends On: v3_1_1_implementation_spec
- **v3_1_consolidated_remediation_plan** [L2] (consolidated_remediation_plan.md) ~4,100 tokens
  - Status: approved
  - Depends On: v3_2_backlog, gemini_analysis_response, chatgpt_analysis_response, claude_analysis_response
- **v3_2_antigravity_implementation_prompt** [L2] (v3.2_Antigravity_Implementation_Prompt.md) ~15,200 tokens
  - Status: active
  - Depends On: v3_2_re_architecture_support_implementation_spec
- **v3_2_backlog** [L2] (v3_2_backlog.md) ~682 tokens
  - Status: active
  - Depends On: v3_1_0_track_b_final_approval_chief_architect
- **v3_2_ca_response_consolidation** [L2] (v3.2_CA_Response_Review_Consolidation.md) ~2,300 tokens
  - Status: active
  - Depends On: v3_2_re_architecture_ca_response
- **v3_2_candidate_suggestions_exploration** [L1] [draft] (candidate_suggestions_exploration.md) ~1,900 tokens  ⚠️ draft
  - Status: draft
  - Depends On: None
- **v3_2_code_review_consolidation** [L2] (v3.2_Code_Review_Consolidation.md) ~1,400 tokens
  - Status: active
  - Depends On: v3_2_pr_review_chief_architect, v3_2_code_review_claude, v3_2_code_review_codex
- **v3_2_environment_manifest_detection_proposal** [L2] [draft] (v3.2_Environment_Manifest_Detection_Proposal.md) ~3,600 tokens
  - Status: draft
  - Depends On: mission, constitution, ontos_agent_instructions
- **v3_2_implementation_spec** [L2] [draft] (v3.2_Re-Architecture_Support_Implementation_Spec.md) ~5,800 tokens
  - Status: draft
  - Depends On: v3_2_proposal_finalization_ca
- **v3_2_pr_review_chief_architect** [L2] (v3.2_PR_Review_Chief_Architect.md) ~1,500 tokens
  - Status: active
  - Depends On: v3_2_antigravity_implementation_prompt
- **v3_2_proposal_finalization_ca** [L2] (v3.2_Proposal_Finalization_CA.md) ~3,500 tokens
  - Status: active
  - Depends On: v3_2_ca_response_consolidation
- **v3_2_re_architecture_ca_response** [L2] (v3.2_Re-Architecture_CA_Response.md) ~3,000 tokens
  - Status: active
  - Depends On: v3_2_re_architecture_support_proposal
- **v3_2_re_architecture_support_proposal** [L2] [draft] (v3.2_Re-Architecture_Support_Proposal.md) ~5,800 tokens
  - Status: draft
  - Depends On: mission, constitution, ontos_agent_instructions

### ATOM
- **architect_synthesis_install_ux** [L2] [draft] (Architect_Synthesis_InstallUX.md) ~4,000 tokens
  - Status: draft
  - Depends On: installation_ux_proposal, claude_install_ux_review, gemini_install_ux_review, installation_ux_proposal_review
- **chief_architect_round2_critical_analysis** [L2] (Chief_Architect_Round2_Critical_Analysis.md) ~1,800 tokens
  - Status: complete
  - Depends On: claude_opus_4_5_phase2_verification_review
- **claude_install_ux_review** [L2] (Claude_InstallUX_Review.md) ~3,500 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **claude_opus_4_5_phase1_review** [L2] (Claude_Opus_4.5_Phase1_Review.md) ~2,900 tokens
  - Status: complete
  - Depends On: phase1_package_structure_spec
- **claude_opus_4_5_phase1_review_round2** [L2] (Claude_Opus_4.5_Phase1_Review_Round2.md) ~887 tokens
  - Status: complete
  - Depends On: phase1_package_structure_spec
- **claude_opus_4_5_phase2_alignment_review** [L2] (Claude_Opus_4.5_Phase2_Alignment_Review.md) ~3,100 tokens
  - Status: complete
  - Depends On: v3_0_implementation_roadmap, v3_0_technical_architecture, v3_0_strategy_decisions
- **claude_opus_4_5_phase2_verification_review** [L1] (Claude_Opus_4.5_Phase2_Verification_Review.md) ~1,000 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **claude_opus_4_5_phase3_alignment_review** [L2] (Claude_Opus_4.5_Phase3_Alignment_Review.md) ~3,200 tokens
  - Status: complete
  - Depends On: phase3_implementation_spec, v3_0_implementation_roadmap, v3_0_technical_architecture, v3_0_strategy_decisions
- **common_concepts** [L1] (Common_Concepts.md) ~737 tokens  ⚠️ active
  - Status: active
  - Depends On: None
- **dual_mode_matrix** [L2] (Dual_Mode_Matrix.md) ~1,600 tokens
  - Status: active
  - Depends On: schema
- **gemini_install_ux_review** [L2] (Gemini_Review_Installation_UX_Proposal.md) ~2,800 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **installation_experience_report** [L2] (Ontos_Installation_Experience_Report.md) ~2,200 tokens
  - Status: complete
  - Depends On: installation_ux_proposal
- **ontos_technical_architecture_map** [L2] (Ontos-Technical-Architecture-Map.md) ~2,300 tokens
  - Status: active
  - Depends On: v3_0_technical_architecture
- **ontos_technical_architecture_map_codex** [L2] (Ontos-Technical-Architecture-Map-Codex.md) ~3,500 tokens
  - Status: active
  - Depends On: v3_0_technical_architecture
- **readme_pypi_links_proposal** [L1] (readme_pypi_links_proposal.md) ~928 tokens  ⚠️ active
  - Status: active
  - Depends On: None
- **schema** [L2] (schema.md) ~450 tokens
  - Status: active
  - Depends On: philosophy
- **v3.0.4_Code_Review_Claude** [L2] (v3.0.4_Code_Review_Claude.md) ~2,600 tokens
  - Status: complete
  - Depends On: phase_v3_0_4_implementation_spec
- **v3_0_2_hybrid_review_alignment_claude** [L2] (v3.0.3_Hybrid_Review_Alignment_Claude.md) ~2,700 tokens
  - Status: complete
  - Depends On: v3.0.3_Implementation_Spec
- **v3_0_2_hybrid_review_consolidation** [L2] (v3.0.3_Hybrid_Review_Consolidation.md) ~2,000 tokens
  - Status: complete
  - Depends On: v3_0_3_hybrid_review_peer_gemini, v3_0_2_hybrid_review_alignment_claude, v3_0_3_hybrid_review_adversarial_codex
- **v3_0_3_hybrid_review_adversarial_codex** [L2] (v3.0.3_Hybrid_Review_Adversarial_Codex.md) ~2,700 tokens
  - Status: complete
  - Depends On: v3.0.3_Implementation_Spec
- **v3_0_3_hybrid_review_peer_gemini** [L2] (v3.0.3_Hybrid_Review_Peer_Gemini.md) ~1,100 tokens
  - Status: complete
  - Depends On: v3.0.3_Implementation_Spec
- **v3_0_4_code_review_consolidation** [L2] (v3.0.4_Code_Review_Consolidation.md) ~1,300 tokens
  - Status: complete
  - Depends On: v3_0_4_code_review_claude, v3_0_4_code_review_gemini, v3_0_4_code_review_codex
- **v3_1_1_spec_review_claude** [L2] (v3.1.1_Spec_Review_Claude.md) ~2,900 tokens
  - Status: complete
  - Depends On: v3_1_1_init_improvements_proposal, ontos_philosophy_and_ontology, dual_mode_matrix
- **v3_2_code_review_claude** [L2] (v3.2_Code_Review_Claude.md) ~1,900 tokens
  - Status: complete
  - Depends On: v3_2_implementation_spec

### LOG
- **log_20251218_v2_6_1_graduation** [L1] (2025-12-18_v2-6-1-graduation.md) ~971 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20251219_chore_maintenance_consolidate_logs_add_frontma** [L2] (2025-12-19_chore-maintenance-consolidate-logs-add-frontma.md) ~340 tokens
  - Status: active
  - Impacts: schema
- **log_20251219_docs_graduate_master_plan_to_strategy_reorganize** [L2] (2025-12-19_docs-graduate-master-plan-to-strategy-reorganize.md) ~562 tokens
  - Status: active
  - Impacts: philosophy
- **log_20251220_v2_7_1** [L1] (2025-12-20_v2-7-1.md) ~392 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260107_v2_9_5_quality_release** [L1] (2026-01-07_v2-9-5-quality-release.md) ~284 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260108_housekeeping_archive_docs** [L2] (2026-01-08_housekeeping-archive-docs.md) ~450 tokens
  - Status: active
  - Impacts: None
- **log_20260111_chore_pre_v3_0_documentation_cleanup** [L1] (2026-01-11_chore-pre-v3-0-documentation-cleanup.md) ~119 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260111_fix_v2_9_6_correct_false_implemented_status_cl** [L1] (2026-01-11_fix-v2-9-6-correct-false-implemented-status-cl.md) ~124 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260111_ontology_architecture_research** [L2] (2026-01-11_docs-v3-0-add-technical-architecture-and-finaliz.md) ~1,200 tokens
  - Status: active
  - Impacts: constitution, philosophy, schema
- **log_20260111_v2_9_6** [L1] (2026-01-11_v2-9-6.md) ~131 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260111_v2_9_6_ontology_architecture** [L1] (2026-01-11_v2-9-6-ontology-architecture.md) ~144 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260111_v2_9_6_round2_revision** [L1] (2026-01-11_v2-9-6-round2-revision.md) ~350 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260112_feat_v2_9_6_ontology_single_source_of_truth** [L2] (2026-01-12_feat-v2-9-6-ontology-single-source-of-truth.md) ~623 tokens
  - Status: active
  - Impacts: None
- **log_20260112_phase0_v3_0_alpha** [L2] (2026-01-12_phase0-v3-0-alpha.md) ~745 tokens
  - Status: active
  - Impacts: phase0_golden_master_spec
- **log_20260112_phase1_package_structure_complete** [L1] (2026-01-12_phase1-package-structure-complete.md) ~120 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260112_phase1_v3_0_alpha** [L2] (2026-01-12_phase1-v3-0-alpha.md) ~466 tokens
  - Status: active
  - Impacts: v3_0_implementation_roadmap
- **log_20260112_phase2_core_decomposition** [L1] (2026-01-12_phase2-core-decomposition.md) ~116 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260112_v2_9_6_cleanup** [L2] (2026-01-12_chore-v2-9-6-cleanup.md) ~322 tokens
  - Status: active
  - Impacts: None
- **log_20260113_analysis_docs_generation** [L2] (2026-01-13_analysis-docs-generation.md) ~348 tokens
  - Status: active
  - Impacts: ontos_strategic_analysis, ontos_technical_architecture_map
- **log_20260113_integrate_analysis_docs** [L1] (2026-01-13_integrate-analysis-docs.md) ~127 tokens  ⚠️ active
  - Status: active
  - Impacts: ontos_strategic_analysis, ontos_technical_architecture_map
- **log_20260113_phase2_v3_0_beta** [L1] (2026-01-13_phase2-v3-0-beta.md) ~197 tokens  ⚠️ auto-generated
  - Status: auto-generated
  - Impacts: None
- **log_20260113_phase4_cli_release** [L2] (2026-01-13_phase4_cli_release.md) ~1,800 tokens
  - Status: active
  - Impacts: None
- **log_20260113_v3_0_1_release** [L1] (2026-01-13_v3_0_1_release.md) ~921 tokens  ⚠️ active
  - Status: active
  - Impacts: v3_0_implementation_roadmap, phase5_implementation_spec
- **log_20260114_philosophy_research_and_tech_debt** [L2] (2026-01-14_philosophy-research-and-tech-debt.md) ~929 tokens
  - Status: active
  - Impacts: ontos_philosophy_and_ontology, obsidian_compatibility_proposal, install_experience_technical_debt_proposal, maintain_command_v3_proposal
- **log_20260115_philosophy_docs_update** [L1] (2026-01-15_philosophy-docs-update.md) ~115 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260116_version_rename** [L1] (2026-01-16_version-rename.md) ~140 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260117_archive-pr-48-approval-and-push** [L1] (2026-01-17_archive-pr-48-approval-and-push.md) ~73 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260117_readme-and-license-update-for-v3-0-0** [L1] (2026-01-17_readme-and-license-update-for-v3-0-0.md) ~75 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260117_v3-0-0-readme-license-and-log-fix** [L1] (2026-01-17_v3-0-0-readme-license-and-log-fix.md) ~74 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260117_v3_0_0_activation_survival** [L2] (2026-01-17_v3_0_0_activation_survival.md) ~683 tokens
  - Status: active
  - Impacts: ontos_agent_instructions, agents_command, doctor_staleness
- **log_20260121_feat-cli-ontos-v3-1-0-track-b-native-command-m** [L1] (2026-01-21_feat-cli-ontos-v3-1-0-track-b-native-command-m.md) ~85 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260121_v3-1-0-track-a-obsidian-similarity-token-efficienc** [L1] (2026-01-21_v3-1-0-track-a-obsidian-similarity-token-efficienc.md) ~101 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260124_fix-blocking-scaffold-issues-from-adversarial-revi** [L1] (2026-01-24_fix-blocking-scaffold-issues-from-adversarial-revi.md) ~390 tokens  ⚠️ active
  - Status: active
  - Impacts: None

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
- **phase_v3_0_4_implementation_spec** [L2] (Phase-v3.0.4-Implementation-Spec.md) ~3,700 tokens
  - Status: approved
  - Depends On: v3.0.3_Implementation_Spec, v3_0_4_cli_wrapper_fix_proposal
- **v3_0_2_chief_architect_response** [L2] (v3.0.3_Chief_Architect_Response.md) ~1,900 tokens
  - Status: complete
  - Depends On: v3_0_2_hybrid_review_consolidation
- **v3_0_2_implementation_spec_v1_1** [L2] (v3.0.3-Implementation-Spec-v1.1.md) ~2,500 tokens
  - Status: complete
  - Depends On: v3.0.3_Implementation_Spec, v3_0_2_chief_architect_response
- **v3_0_4_chief_architect_response** [L2] (v3.0.4_Chief_Architect_Response.md) ~2,500 tokens
  - Status: complete
  - Depends On: v3_0_4_spec_review_consolidation
- **v3_0_5_chief_architect_triage_response** [L2] (v3.0.5_Chief_Architect_Triage_Response.md) ~1,700 tokens
  - Status: approved
  - Depends On: v3_0_5_triage_review_consolidation
- **v3_0_5_pr_review_chief_architect** [L2] (v3.0.5_PR_Review_Chief_Architect.md) ~1,100 tokens
  - Status: complete
  - Depends On: v3_0_5_chief_architect_triage_response
- **v3_1_0_audit_triage_chief_architect** [L2] (v3_1_0_Audit_Triage_Chief_Architect.md) ~2,600 tokens
  - Status: complete
  - Depends On: v3_1_0_implementation_spec, v3_1_0_research_review_chief_architect
- **v3_1_0_chief_architect_response** [L2] (v3_1_0_Chief_Architect_Response.md) ~4,900 tokens
  - Status: complete
  - Depends On: v3_1_0_spec_review_consolidation, v3_1_0_implementation_spec
- **v3_1_0_final_decision_chief_architect** [L2] (v3_1_0_Final_Decision_Chief_Architect.md) ~2,200 tokens
  - Status: complete
  - Depends On: v3_1_0_verification_consolidation, v3_1_0_implementation_spec
- **v3_1_0_research_review_chief_architect** [L2] (v3_1_0_Research_Review_Chief_Architect.md) ~2,300 tokens
  - Status: complete
  - Depends On: v3_1_0_implementation_spec
- **v3_1_0_spec_review_claude** [L2] (v3_1_0_Spec_Review_Claude.md) ~5,100 tokens
  - Status: complete
  - Depends On: v3_1_0_implementation_spec, v3_1_0_audit_triage_chief_architect
- **v3_1_0_spec_review_consolidation** [L2] (v3_1_0_Spec_Review_Consolidation.md) ~3,300 tokens
  - Status: complete
  - Depends On: v3_1_0_spec_review_claude, v3_1_0_spec_review_gemini, v3_1_0_spec_review_gpt5
- **v3_1_0_track_a_ca_rulings_d3a** [L2] (v3_1_0_Track_A_CA_Rulings_D3a.md) ~1,100 tokens
  - Status: complete
  - Depends On: v3_1_0_track_a_pr_review_chief_architect
- **v3_1_0_track_a_code_review_consolidation** [L2] (v3_1_0_Track_A_Code_Review_Consolidation.md) ~2,500 tokens
  - Status: complete
  - Depends On: v3_1_0_track_a_pr_review_chief_architect, v3_1_0_track_a_code_review_claude, v3_1_0_track_a_code_review_codex, v3_1_0_track_a_code_review_gemini
- **v3_1_0_track_a_final_approval_d6a** [L2] (v3_1_0_Track_A_Final_Approval_D6a.md) ~862 tokens
  - Status: complete
  - Depends On: v3_1_0_track_a_ca_rulings_d3a
- **v3_1_0_track_a_implementation_prompt** [L2] (v3_1_0_Track_A_Implementation_Prompt_Antigravity.md) ~7,000 tokens
  - Status: ready
  - Depends On: v3_1_0_implementation_spec, v3_1_0_final_decision_chief_architect
- **v3_1_0_track_a_pr_review_chief_architect** [L2] (v3_1_0_Track_A_PR_Review_Chief_Architect.md) ~1,500 tokens
  - Status: complete
  - Depends On: v3_1_0_implementation_spec, v3_1_0_track_a_implementation_prompt
- **v3_1_0_track_b_code_review_consolidation** [L2] (v3_1_0_Track_B_Code_Review_Consolidation.md) ~2,000 tokens
  - Status: complete
  - Depends On: v3_1_0_track_b_pr_review_chief_architect, v3_1_0_track_b_code_review_claude, v3_1_0_track_b_code_review_codex, v3_1_0_track_b_code_review_gemini
- **v3_1_0_track_b_final_approval_chief_architect** [L2] (v3_1_0_Track_B_Final_Approval_Chief_Architect.md) ~833 tokens
  - Status: complete
  - Depends On: v3_1_0_track_b_code_verification_codex
- **v3_1_0_track_b_pr_review_chief_architect** [L2] (v3_1_0_Track_B_PR_Review_Chief_Architect.md) ~2,400 tokens
  - Status: complete
  - Depends On: v3_1_0_track_b_implementation_prompt_antigravity
- **v3_1_0_verification_consolidation** [L2] (v3_1_0_Verification_Consolidation.md) ~1,700 tokens
  - Status: complete
  - Depends On: v3_1_0_spec_verification_gemini, v3_1_0_spec_verification_gpt5
- **v3_1_tech_debt_wrapper_commands** [L2] (tech-debt-wrapper-commands.md) ~658 tokens
  - Status: open
  - Depends On: phase_v3_0_4_implementation_spec


## 2. Recent Timeline
- **2026-01-24** [fix] **Fix Blocking Scaffold Issues From Adversarial Revi** (`log_20260124_fix-blocking-scaffold-issues-from-adversarial-revi`)
- **2026-01-21** [release] **V3 1 0 Track A Obsidian Similarity Token Efficienc** (`log_20260121_v3-1-0-track-a-obsidian-similarity-token-efficienc`)
- **2026-01-21** [track-b-migration-final] **Feat Cli Ontos V3 1 0 Track B Native Command M** (`log_20260121_feat-cli-ontos-v3-1-0-track-b-native-command-m`)
- **2026-01-17** [feature] **V3 0 0 Activation Survival** (`log_20260117_v3_0_0_activation_survival`)
  - Impacted: `ontos_agent_instructions`, `agents_command`, `doctor_staleness`
  - Concepts: activation, agents, pypi, cli
- **2026-01-17** [chore] **V3 0 0 Readme License And Log Fix** (`log_20260117_v3-0-0-readme-license-and-log-fix`)
- **2026-01-17** [chore] **Readme And License Update For V3 0 0** (`log_20260117_readme-and-license-update-for-v3-0-0`)
- **2026-01-17** [chore] **Archive Pr 48 Approval And Push** (`log_20260117_archive-pr-48-approval-and-push`)
- **2026-01-16** [chore] **Version Rename** (`log_20260116_version_rename`)
- **2026-01-15** [chore] **Philosophy Docs Update** (`log_20260115_philosophy_docs_update`)
- **2026-01-14** [chore] **Philosophy Research And Tech Debt** (`log_20260114_philosophy_research_and_tech_debt`)
  - Impacted: `ontos_philosophy_and_ontology`, `obsidian_compatibility_proposal`, `install_experience_technical_debt_proposal`, `maintain_command_v3_proposal`
  - Concepts: philosophy, ontology, architecture, documentation, technical-debt

*Showing 10 of 33 sessions*

## 3. Dependency Audit
- [BROKEN LINK] **v3_2_antigravity_implementation_prompt** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2/v3.2_rearchitecting/v3.2_Antigravity_Implementation_Prompt.md) references missing ID: `v3_2_re_architecture_support_implementation_spec`
  Fix: Add a document with `id: v3_2_re_architecture_support_implementation_spec` or remove it from depends_on
- [BROKEN LINK] **v3_2_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2/v3.2_rearchitecting/v3.2_Code_Review_Consolidation.md) references missing ID: `v3_2_code_review_codex`
  Fix: Add a document with `id: v3_2_code_review_codex` or remove it from depends_on
- [BROKEN LINK] **v3_0_2_hybrid_review_alignment_claude** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.3/v3.0.3_Hybrid_Review_Alignment_Claude.md) references missing ID: `v3.0.3_Implementation_Spec`
  Fix: Add a document with `id: v3.0.3_Implementation_Spec` or remove it from depends_on
- [BROKEN LINK] **v3_0_3_hybrid_review_adversarial_codex** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.3/v3.0.3_Hybrid_Review_Adversarial_Codex.md) references missing ID: `v3.0.3_Implementation_Spec`
  Fix: Add a document with `id: v3.0.3_Implementation_Spec` or remove it from depends_on
- [BROKEN LINK] **v3_0_3_hybrid_review_peer_gemini** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.3/v3.0.3_Hybrid_Review_Peer_Gemini.md) references missing ID: `v3.0.3_Implementation_Spec`
  Fix: Add a document with `id: v3.0.3_Implementation_Spec` or remove it from depends_on
- [BROKEN LINK] **v3_0_2_implementation_spec_v1_1** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.3/v3.0.3-Implementation-Spec-v1.1.md) references missing ID: `v3.0.3_Implementation_Spec`
  Fix: Add a document with `id: v3.0.3_Implementation_Spec` or remove it from depends_on
- [BROKEN LINK] **v3_0_4_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/v3.0.4_Code_Review_Consolidation.md) references missing ID: `v3_0_4_code_review_claude`
  Fix: Add a document with `id: v3_0_4_code_review_claude` or remove it from depends_on
- [BROKEN LINK] **v3_0_4_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/v3.0.4_Code_Review_Consolidation.md) references missing ID: `v3_0_4_code_review_gemini`
  Fix: Add a document with `id: v3_0_4_code_review_gemini` or remove it from depends_on
- [BROKEN LINK] **v3_0_4_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/v3.0.4_Code_Review_Consolidation.md) references missing ID: `v3_0_4_code_review_codex`
  Fix: Add a document with `id: v3_0_4_code_review_codex` or remove it from depends_on
- [BROKEN LINK] **v3_0_4_chief_architect_response** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/v3.0.4_Chief_Architect_Response.md) references missing ID: `v3_0_4_spec_review_consolidation`
  Fix: Add a document with `id: v3_0_4_spec_review_consolidation` or remove it from depends_on
- [BROKEN LINK] **phase_v3_0_4_implementation_spec** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/Phase-v3.0.4-Implementation-Spec.md) references missing ID: `v3.0.3_Implementation_Spec`
  Fix: Add a document with `id: v3.0.3_Implementation_Spec` or remove it from depends_on
- [BROKEN LINK] **v3_0_4_cli_wrapper_fix_proposal** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/v3.0.4_CLI_Wrapper_Fix_Proposal.md) references missing ID: `v3_0_3_implementation_spec`
  Fix: Add a document with `id: v3_0_3_implementation_spec` or remove it from depends_on
- [BROKEN LINK] **v3_0_5_chief_architect_triage_response** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.5/v3.0.5_Chief_Architect_Triage_Response.md) references missing ID: `v3_0_5_triage_review_consolidation`
  Fix: Add a document with `id: v3_0_5_triage_review_consolidation` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_track_b_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_B_Code_Review_Consolidation.md) references missing ID: `v3_1_0_track_b_code_review_claude`
  Fix: Add a document with `id: v3_1_0_track_b_code_review_claude` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_track_b_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_B_Code_Review_Consolidation.md) references missing ID: `v3_1_0_track_b_code_review_codex`
  Fix: Add a document with `id: v3_1_0_track_b_code_review_codex` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_track_b_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_B_Code_Review_Consolidation.md) references missing ID: `v3_1_0_track_b_code_review_gemini`
  Fix: Add a document with `id: v3_1_0_track_b_code_review_gemini` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_implementation_spec** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Implementation_Spec_v1.2.md) references missing ID: `v3_0_5_implementation_spec`
  Fix: Add a document with `id: v3_0_5_implementation_spec` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_track_a_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_A_Code_Review_Consolidation.md) references missing ID: `v3_1_0_track_a_code_review_claude`
  Fix: Add a document with `id: v3_1_0_track_a_code_review_claude` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_track_a_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_A_Code_Review_Consolidation.md) references missing ID: `v3_1_0_track_a_code_review_codex`
  Fix: Add a document with `id: v3_1_0_track_a_code_review_codex` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_track_a_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_A_Code_Review_Consolidation.md) references missing ID: `v3_1_0_track_a_code_review_gemini`
  Fix: Add a document with `id: v3_1_0_track_a_code_review_gemini` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_track_b_final_approval_chief_architect** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_B_Final_Approval_Chief_Architect.md) references missing ID: `v3_1_0_track_b_code_verification_codex`
  Fix: Add a document with `id: v3_1_0_track_b_code_verification_codex` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_verification_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Verification_Consolidation.md) references missing ID: `v3_1_0_spec_verification_gemini`
  Fix: Add a document with `id: v3_1_0_spec_verification_gemini` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_verification_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Verification_Consolidation.md) references missing ID: `v3_1_0_spec_verification_gpt5`
  Fix: Add a document with `id: v3_1_0_spec_verification_gpt5` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_spec_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Spec_Review_Consolidation.md) references missing ID: `v3_1_0_spec_review_gemini`
  Fix: Add a document with `id: v3_1_0_spec_review_gemini` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_spec_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Spec_Review_Consolidation.md) references missing ID: `v3_1_0_spec_review_gpt5`
  Fix: Add a document with `id: v3_1_0_spec_review_gpt5` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_track_b_pr_review_chief_architect** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_B_PR_Review_Chief_Architect.md) references missing ID: `v3_1_0_track_b_implementation_prompt_antigravity`
  Fix: Add a document with `id: v3_1_0_track_b_implementation_prompt_antigravity` or remove it from depends_on
- [ORPHAN] **v3_0_5_pr_review_chief_architect** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.5/v3.0.5_PR_Review_Chief_Architect.md) has no dependents
  Fix: Add `v3_0_5_pr_review_chief_architect` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_1_0_track_a_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_A_Code_Review_Consolidation.md) has no dependents
  Fix: Add `v3_1_0_track_a_code_review_consolidation` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_1_0_track_a_final_approval_d6a** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_A_Final_Approval_D6a.md) has no dependents
  Fix: Add `v3_1_0_track_a_final_approval_d6a` to another document's depends_on, or delete if unused
- [ORPHAN] **phase3_implementation_spec_review_codex** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase3/Phase3-Implementation-Spec-Review-Codex.md) has no dependents
  Fix: Add `phase3_implementation_spec_review_codex` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_1_0_chief_architect_response** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Chief_Architect_Response.md) has no dependents
  Fix: Add `v3_1_0_chief_architect_response` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_1_0_track_b_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_B_Code_Review_Consolidation.md) has no dependents
  Fix: Add `v3_1_0_track_b_code_review_consolidation` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_0_2_implementation_spec_v1_1** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.3/v3.0.3-Implementation-Spec-v1.1.md) has no dependents
  Fix: Add `v3_0_2_implementation_spec_v1_1` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_0_4_chief_architect_response** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/v3.0.4_Chief_Architect_Response.md) has no dependents
  Fix: Add `v3_0_4_chief_architect_response` to another document's depends_on, or delete if unused
- [ORPHAN] **migration_v2_to_v3** (docs/reference/Migration_v2_to_v3.md) has no dependents
  Fix: Add `migration_v2_to_v3` to another document's depends_on, or delete if unused
- [DEPTH] **v3_1_0_spec_review_claude** has dependency depth 9 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_track_a_pr_review_chief_architect** has dependency depth 9 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_sidecar_pattern** has dependency depth 6 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_implementation_spec** has dependency depth 6 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_audit_triage_chief_architect** has dependency depth 8 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_track_a_implementation_prompt** has dependency depth 8 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_research_review_chief_architect** has dependency depth 7 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_1_final_approval** has dependency depth 7 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_track_a_code_review_consolidation** has dependency depth 10 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_track_a_ca_rulings_d3a** has dependency depth 10 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_2_code_review_consolidation** has dependency depth 8 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_spec_review_consolidation** has dependency depth 10 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_track_a_final_approval_d6a** has dependency depth 11 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_1_implementation_prompt_antigravity** has dependency depth 6 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_1_pr_review_chief_architect** has dependency depth 6 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_2_code_review_claude** has dependency depth 7 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_chief_architect_response** has dependency depth 11 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_final_decision_chief_architect** has dependency depth 7 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_2_implementation_spec** has dependency depth 6 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [ARCHITECTURE] **v3_2_backlog** (strategy) depends on **v3_1_0_track_b_final_approval_chief_architect** (approval)
  Fix: strategy should not depend on approval. Invert the dependency or change document types
- [ARCHITECTURE] **phase2_implementation_instructions_antigravity** (strategy) depends on **chief_architect_round2_critical_analysis** (atom)
  Fix: strategy should not depend on atom. Invert the dependency or change document types
- [ARCHITECTURE] **phase5_implementation_spec** (strategy) depends on **phase4_final_approval_chief_architect** (approval)
  Fix: strategy should not depend on approval. Invert the dependency or change document types
- [ARCHITECTURE] **v3_2_code_review_consolidation** (strategy) depends on **v3_2_code_review_claude** (atom)
  Fix: strategy should not depend on atom. Invert the dependency or change document types
- [ARCHITECTURE] **v3_0_4_chief_architect_notes** (strategy) depends on **phase_v3_0_4_implementation_spec** (spec)
  Fix: strategy should not depend on spec. Invert the dependency or change document types
- [ARCHITECTURE] **v3.0.4_Code_Review_Claude** (atom) depends on **phase_v3_0_4_implementation_spec** (spec)
  Fix: atom should not depend on spec. Invert the dependency or change document types
- [ARCHITECTURE] **v3_1_0_implementation_spec** (strategy) depends on **v3_1_tech_debt_wrapper_commands** (tech-debt)
  Fix: strategy should not depend on tech-debt. Invert the dependency or change document types
- [INVALID VALUE] **log_20260121_feat-cli-ontos-v3-1-0-track-b-native-command-m** (docs/logs/2026-01-21_feat-cli-ontos-v3-1-0-track-b-native-command-m.md) has invalid event_type: 'track-b-migration-final'
  Fix: Use one of: chore, decision, exploration, feature, fix, refactor, release
- [BROKEN LINK] **log_20260117_v3_0_0_activation_survival** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-17_v3_0_0_activation_survival.md) impacts non-existent document: `agents_command`
  Fix: Create `agents_command`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260117_v3_0_0_activation_survival** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-17_v3_0_0_activation_survival.md) impacts non-existent document: `doctor_staleness`
  Fix: Create `doctor_staleness`, correct the reference, or archive this log
- [LINT] **log_20260113_phase2_v3_0_beta**: Invalid status 'auto-generated'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **phase4_implementation_spec**: Invalid status 'approved'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **v3_2_re_architecture_ca_response**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_2_ca_response_consolidation**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_2_pr_review_chief_architect**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_2_antigravity_implementation_prompt**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_2_code_review_consolidation**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_2_proposal_finalization_ca**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_1_1_final_approval**: Invalid status 'approved'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **v3_1_1_implementation_prompt_antigravity**: Invalid status 'approved'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **v3_1_1_pr_review_chief_architect**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_1_1_implementation_spec**: Invalid status 'approved'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **v3_1_1_chief_architect_response**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_1_consolidated_remediation_plan**: Invalid status 'approved'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **v3_0_4_chief_architect_notes**: Active document in proposals/. Graduate to strategy/.
- [LINT] **readme_pypi_links_proposal**: Active document in proposals/. Graduate to strategy/.
- [LINT] **phase_v3_0_4_implementation_spec**: Invalid status 'approved'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **v3_0_4_cli_wrapper_fix_proposal**: Invalid status 'approved'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **v3_0_5_chief_architect_triage_response**: Invalid status 'approved'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **v3_1_0_track_a_implementation_prompt**: Invalid status 'ready'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **v3_1_0_implementation_spec**: Invalid status 'approved'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **v3_1_tech_debt_wrapper_commands**: Invalid status 'open'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold

## 4. Index
| ID | Filename | Type |
|---|---|---|
| architect_synthesis_install_ux | [Architect_Synthesis_InstallUX.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/Install_experience/Architect_Synthesis_InstallUX.md) | atom |
| chatgpt_analysis_response | [chatgpt_analysis_response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.1_Review/chatgpt_analysis_response.md) | strategy |
| chatgpt_round2_response | [chatgpt_round2_response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.1_Review/chatgpt_round2_response.md) | strategy |
| chief_architect_phase3_response | [Chief_Architect_Phase3_Response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase3/Chief_Architect_Phase3_Response.md) | strategy |
| chief_architect_round2_critical_analysis | [Chief_Architect_Round2_Critical_Analysis.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase2/Chief_Architect_Round2_Critical_Analysis.md) | atom |
| claude_analysis_response | [claude_analysis_response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.1_Review/claude_analysis_response.md) | strategy |
| claude_install_ux_review | [Claude_InstallUX_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/Install_experience/Claude_InstallUX_Review.md) | atom |
| claude_opus_4_5_phase1_review | [Claude_Opus_4.5_Phase1_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase1/Claude_Opus_4.5_Phase1_Review.md) | atom |
| claude_opus_4_5_phase1_review_round2 | [Claude_Opus_4.5_Phase1_Review_Round2.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase1/Claude_Opus_4.5_Phase1_Review_Round2.md) | atom |
| claude_opus_4_5_phase2_alignment_review | [Claude_Opus_4.5_Phase2_Alignment_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase2/Claude_Opus_4.5_Phase2_Alignment_Review.md) | atom |
| claude_opus_4_5_phase2_verification_review | [Claude_Opus_4.5_Phase2_Verification_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase2/Claude_Opus_4.5_Phase2_Verification_Review.md) | atom |
| claude_opus_4_5_phase3_alignment_review | [Claude_Opus_4.5_Phase3_Alignment_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase3/Claude_Opus_4.5_Phase3_Alignment_Review.md) | atom |
| claude_round2_response | [claude_round2_response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.1_Review/claude_round2_response.md) | strategy |
| common_concepts | [Common_Concepts.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/reference/Common_Concepts.md) | atom |
| constitution | [constitution.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/kernel/constitution.md) | kernel |
| dual_mode_matrix | [Dual_Mode_Matrix.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/reference/Dual_Mode_Matrix.md) | atom |
| gemini_analysis_response | [gemini_analysis_response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.1_Review/gemini_analysis_response.md) | strategy |
| gemini_install_ux_review | [Gemini_Review_Installation_UX_Proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/Install_experience/Gemini_Review_Installation_UX_Proposal.md) | atom |
| install_experience_technical_debt_proposal | [Install_Experience_Technical_Debt_Proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/Install_Experience_Technical_Debt_Proposal.md) | strategy |
| installation_experience_report | [Ontos_Installation_Experience_Report.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/Install_experience/Ontos_Installation_Experience_Report.md) | atom |
| installation_ux_proposal | [Installation_UX_Proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/Install_experience/Installation_UX_Proposal.md) | strategy |
| installation_ux_proposal_review | [Installation_UX_Proposal_Review_Codex.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/Install_experience/Installation_UX_Proposal_Review_Codex.md) | strategy |
| log_20251218_v2_6_1_graduation | [2025-12-18_v2-6-1-graduation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2025-12-18_v2-6-1-graduation.md) | log |
| log_20251219_chore_maintenance_consolidate_logs_add_frontma | [2025-12-19_chore-maintenance-consolidate-logs-add-frontma.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2025-12-19_chore-maintenance-consolidate-logs-add-frontma.md) | log |
| log_20251219_docs_graduate_master_plan_to_strategy_reorganize | [2025-12-19_docs-graduate-master-plan-to-strategy-reorganize.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2025-12-19_docs-graduate-master-plan-to-strategy-reorganize.md) | log |
| log_20251220_v2_7_1 | [2025-12-20_v2-7-1.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2025-12-20_v2-7-1.md) | log |
| log_20260107_v2_9_5_quality_release | [2026-01-07_v2-9-5-quality-release.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-07_v2-9-5-quality-release.md) | log |
| log_20260108_housekeeping_archive_docs | [2026-01-08_housekeeping-archive-docs.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-08_housekeeping-archive-docs.md) | log |
| log_20260111_chore_pre_v3_0_documentation_cleanup | [2026-01-11_chore-pre-v3-0-documentation-cleanup.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-11_chore-pre-v3-0-documentation-cleanup.md) | log |
| log_20260111_fix_v2_9_6_correct_false_implemented_status_cl | [2026-01-11_fix-v2-9-6-correct-false-implemented-status-cl.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-11_fix-v2-9-6-correct-false-implemented-status-cl.md) | log |
| log_20260111_ontology_architecture_research | [2026-01-11_docs-v3-0-add-technical-architecture-and-finaliz.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-11_docs-v3-0-add-technical-architecture-and-finaliz.md) | log |
| log_20260111_v2_9_6 | [2026-01-11_v2-9-6.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-11_v2-9-6.md) | log |
| log_20260111_v2_9_6_ontology_architecture | [2026-01-11_v2-9-6-ontology-architecture.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-11_v2-9-6-ontology-architecture.md) | log |
| log_20260111_v2_9_6_round2_revision | [2026-01-11_v2-9-6-round2-revision.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-11_v2-9-6-round2-revision.md) | log |
| log_20260112_feat_v2_9_6_ontology_single_source_of_truth | [2026-01-12_feat-v2-9-6-ontology-single-source-of-truth.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-12_feat-v2-9-6-ontology-single-source-of-truth.md) | log |
| log_20260112_phase0_v3_0_alpha | [2026-01-12_phase0-v3-0-alpha.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-12_phase0-v3-0-alpha.md) | log |
| log_20260112_phase1_package_structure_complete | [2026-01-12_phase1-package-structure-complete.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-12_phase1-package-structure-complete.md) | log |
| log_20260112_phase1_v3_0_alpha | [2026-01-12_phase1-v3-0-alpha.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-12_phase1-v3-0-alpha.md) | log |
| log_20260112_phase2_core_decomposition | [2026-01-12_phase2-core-decomposition.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-12_phase2-core-decomposition.md) | log |
| log_20260112_v2_9_6_cleanup | [2026-01-12_chore-v2-9-6-cleanup.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-12_chore-v2-9-6-cleanup.md) | log |
| log_20260113_analysis_docs_generation | [2026-01-13_analysis-docs-generation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-13_analysis-docs-generation.md) | log |
| log_20260113_integrate_analysis_docs | [2026-01-13_integrate-analysis-docs.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-13_integrate-analysis-docs.md) | log |
| log_20260113_phase2_v3_0_beta | [2026-01-13_phase2-v3-0-beta.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-13_phase2-v3-0-beta.md) | log |
| log_20260113_phase4_cli_release | [2026-01-13_phase4_cli_release.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-13_phase4_cli_release.md) | log |
| log_20260113_v3_0_1_release | [2026-01-13_v3_0_1_release.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-13_v3_0_1_release.md) | log |
| log_20260114_philosophy_research_and_tech_debt | [2026-01-14_philosophy-research-and-tech-debt.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-14_philosophy-research-and-tech-debt.md) | log |
| log_20260115_philosophy_docs_update | [2026-01-15_philosophy-docs-update.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-15_philosophy-docs-update.md) | log |
| log_20260116_version_rename | [2026-01-16_version-rename.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-16_version-rename.md) | log |
| log_20260117_archive-pr-48-approval-and-push | [2026-01-17_archive-pr-48-approval-and-push.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-17_archive-pr-48-approval-and-push.md) | log |
| log_20260117_readme-and-license-update-for-v3-0-0 | [2026-01-17_readme-and-license-update-for-v3-0-0.md](docs/logs/2026-01-17_readme-and-license-update-for-v3-0-0.md) | log |
| log_20260117_v3-0-0-readme-license-and-log-fix | [2026-01-17_v3-0-0-readme-license-and-log-fix.md](docs/logs/2026-01-17_v3-0-0-readme-license-and-log-fix.md) | log |
| log_20260117_v3_0_0_activation_survival | [2026-01-17_v3_0_0_activation_survival.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-17_v3_0_0_activation_survival.md) | log |
| log_20260121_feat-cli-ontos-v3-1-0-track-b-native-command-m | [2026-01-21_feat-cli-ontos-v3-1-0-track-b-native-command-m.md](docs/logs/2026-01-21_feat-cli-ontos-v3-1-0-track-b-native-command-m.md) | log |
| log_20260121_v3-1-0-track-a-obsidian-similarity-token-efficienc | [2026-01-21_v3-1-0-track-a-obsidian-similarity-token-efficienc.md](docs/logs/2026-01-21_v3-1-0-track-a-obsidian-similarity-token-efficienc.md) | log |
| log_20260124_fix-blocking-scaffold-issues-from-adversarial-revi | [2026-01-24_fix-blocking-scaffold-issues-from-adversarial-revi.md](docs/logs/2026-01-24_fix-blocking-scaffold-issues-from-adversarial-revi.md) | log |
| maintain_command_v3_proposal | [Maintain_Command_v3_Proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/Maintain_Command_v3_Proposal.md) | strategy |
| migration_v2_to_v3 | [Migration_v2_to_v3.md](docs/reference/Migration_v2_to_v3.md) | reference |
| mission | [mission.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/kernel/mission.md) | kernel |
| obsidian_compatibility_proposal | [Obsidian_Compatibility_Proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/Obsidian_Compatibility_Proposal.md) | strategy |
| ontology_spec | [ontology_spec.md](docs/reference/ontology_spec.md) | kernel |
| ontos_agent_instructions | [Ontos_Agent_Instructions.md](docs/reference/Ontos_Agent_Instructions.md) | kernel |
| ontos_claude_code_skill_proposal | [Ontos_Claude_Code_Skill_Proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/Ontos_Claude_Code_Skill_Proposal.md) | strategy |
| ontos_manual | [Ontos_Manual.md](docs/reference/Ontos_Manual.md) | kernel |
| ontos_philosophy_and_ontology | [Ontos_Philosophy_and_Ontology_v2_draft.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/reference/Ontos_Philosophy_and_Ontology_v2_draft.md) | kernel |
| ontos_strategic_analysis | [Ontos-Strategic-Analysis.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/analysis/Ontos-Strategic-Analysis.md) | strategy |
| ontos_strategic_analysis_codex | [Ontos-Strategic-Analysis-Codex.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/analysis/Ontos-Strategic-Analysis-Codex.md) | strategy |
| ontos_technical_architecture_map | [Ontos-Technical-Architecture-Map.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/analysis/Ontos-Technical-Architecture-Map.md) | atom |
| ontos_technical_architecture_map_codex | [Ontos-Technical-Architecture-Map-Codex.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/analysis/Ontos-Technical-Architecture-Map-Codex.md) | atom |
| phase0_golden_master_spec | [phase0_implementation_spec.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase0/phase0_implementation_spec.md) | strategy |
| phase1_package_structure_spec | [phase1_implementation_spec.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase1/phase1_implementation_spec.md) | strategy |
| phase2_godscript_reduction_instructions_antigravity | [Phase2_GodScript_Reduction_Instructions_Antigravity.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase2/Phase2_GodScript_Reduction_Instructions_Antigravity.md) | strategy |
| phase2_implementation_instructions_antigravity | [Phase2_Implementation_Instructions_Antigravity.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase2/Phase2_Implementation_Instructions_Antigravity.md) | strategy |
| phase3_final_approval_chief_architect | [Phase3_Final_Approval_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase3/Phase3_Final_Approval_Chief_Architect.md) | strategy |
| phase3_implementation_prompt_antigravity | [Phase3_Implementation_Prompt_Antigravity.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase3/Phase3_Implementation_Prompt_Antigravity.md) | strategy |
| phase3_implementation_spec | [Phase3-Implementation-Spec.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase3/Phase3-Implementation-Spec.md) | strategy |
| phase3_implementation_spec_review_codex | [Phase3-Implementation-Spec-Review-Codex.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase3/Phase3-Implementation-Spec-Review-Codex.md) | unknown |
| phase3_pr_review_chief_architect | [Phase3_PR_Review_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase3/Phase3_PR_Review_Chief_Architect.md) | strategy |
| phase3_review_consolidation | [Phase3-Review-Consolidation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase3/Phase3-Review-Consolidation.md) | strategy |
| phase4_chief_architect_response | [Phase4_Chief_Architect_Response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase4/Phase4_Chief_Architect_Response.md) | strategy |
| phase4_code_review_claude | [Phase4_Code_Review_Claude.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase4/Phase4_Code_Review_Claude.md) | strategy |
| phase4_final_approval_chief_architect | [Phase4_Final_Approval_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase4/Phase4_Final_Approval_Chief_Architect.md) | approval |
| phase4_implementation_spec | [Phase4-Implementation-Spec.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase4/Phase4-Implementation-Spec.md) | strategy |
| phase4_pr_review_chief_architect | [Phase4_PR_Review_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase4/Phase4_PR_Review_Chief_Architect.md) | review |
| phase5_code_review_claude | [Phase5_Code_Review_Claude.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase5/Phase5_Code_Review_Claude.md) | strategy |
| phase5_implementation_spec | [Phase5-Implementation-Spec.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase5/Phase5-Implementation-Spec.md) | strategy |
| phase5_spec_review_claude | [Phase5_Spec_Review_Claude.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase5/Phase5_Spec_Review_Claude.md) | strategy |
| phase_v3_0_4_implementation_spec | [Phase-v3.0.4-Implementation-Spec.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/Phase-v3.0.4-Implementation-Spec.md) | spec |
| philosophy | [philosophy.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/kernel/philosophy.md) | kernel |
| readme_pypi_links_proposal | [readme_pypi_links_proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/readme_pypi_links_proposal.md) | atom |
| schema | [schema.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/atom/schema.md) | atom |
| v3.0.4_Code_Review_Claude | [v3.0.4_Code_Review_Claude.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/v3.0.4_Code_Review_Claude.md) | atom |
| v3_0_2_chief_architect_response | [v3.0.3_Chief_Architect_Response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.3/v3.0.3_Chief_Architect_Response.md) | decision |
| v3_0_2_cli_legacy_remediation | [v3.0.3_CLI_Legacy_Remediation_Proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.3/v3.0.3_CLI_Legacy_Remediation_Proposal.md) | strategy |
| v3_0_2_hybrid_review_alignment_claude | [v3.0.3_Hybrid_Review_Alignment_Claude.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.3/v3.0.3_Hybrid_Review_Alignment_Claude.md) | atom |
| v3_0_2_hybrid_review_consolidation | [v3.0.3_Hybrid_Review_Consolidation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.3/v3.0.3_Hybrid_Review_Consolidation.md) | atom |
| v3_0_2_implementation_spec_v1_1 | [v3.0.3-Implementation-Spec-v1.1.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.3/v3.0.3-Implementation-Spec-v1.1.md) | spec |
| v3_0_2_tech_debt_resolution_proposal | [v3.0.3_Tech_Debt_Resolution_Proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.3/v3.0.3_Tech_Debt_Resolution_Proposal.md) | strategy |
| v3_0_3_hybrid_review_adversarial_codex | [v3.0.3_Hybrid_Review_Adversarial_Codex.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.3/v3.0.3_Hybrid_Review_Adversarial_Codex.md) | atom |
| v3_0_3_hybrid_review_peer_gemini | [v3.0.3_Hybrid_Review_Peer_Gemini.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.3/v3.0.3_Hybrid_Review_Peer_Gemini.md) | atom |
| v3_0_4_chief_architect_notes | [v3.0.4_CA_Notes.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/v3.0.4_CA_Notes.md) | strategy |
| v3_0_4_chief_architect_response | [v3.0.4_Chief_Architect_Response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/v3.0.4_Chief_Architect_Response.md) | decision |
| v3_0_4_cli_wrapper_fix_proposal | [v3.0.4_CLI_Wrapper_Fix_Proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/v3.0.4_CLI_Wrapper_Fix_Proposal.md) | strategy |
| v3_0_4_code_review_consolidation | [v3.0.4_Code_Review_Consolidation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.4/v3.0.4_Code_Review_Consolidation.md) | atom |
| v3_0_5_chief_architect_triage_response | [v3.0.5_Chief_Architect_Triage_Response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.5/v3.0.5_Chief_Architect_Triage_Response.md) | decision |
| v3_0_5_pr_review_chief_architect | [v3.0.5_PR_Review_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.0.5/v3.0.5_PR_Review_Chief_Architect.md) | review |
| v3_0_implementation_roadmap | [V3.0-Implementation-Roadmap.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/V3.0-Implementation-Roadmap.md) | strategy |
| v3_0_security_requirements | [v3.0_security_requirements.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/v3.0_security_requirements.md) | strategy |
| v3_0_strategy_decisions | [V3.0-Strategy-Decisions-Final.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/V3.0-Strategy-Decisions-Final.md) | strategy |
| v3_0_technical_architecture | [V3.0-Technical-Architecture.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/V3.0-Technical-Architecture.md) | strategy |
| v3_1_0_audit_triage_chief_architect | [v3_1_0_Audit_Triage_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Audit_Triage_Chief_Architect.md) | review |
| v3_1_0_chief_architect_response | [v3_1_0_Chief_Architect_Response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Chief_Architect_Response.md) | review |
| v3_1_0_final_decision_chief_architect | [v3_1_0_Final_Decision_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Final_Decision_Chief_Architect.md) | decision |
| v3_1_0_implementation_plan | [V3.1.0-Implementation-Plan.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/V3.1.0-Implementation-Plan.md) | strategy |
| v3_1_0_implementation_spec | [v3_1_0_Implementation_Spec_v1.2.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Implementation_Spec_v1.2.md) | strategy |
| v3_1_0_obsidian_compatibility_spec | [V3.1.0-Obsidian-Compatibility-Spec.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/V3.1.0-Obsidian-Compatibility-Spec.md) | strategy |
| v3_1_0_research_review_chief_architect | [v3_1_0_Research_Review_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Research_Review_Chief_Architect.md) | review |
| v3_1_0_sidecar_pattern | [V3.1.0-Sidecar-Pattern.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/V3.1.0-Sidecar-Pattern.md) | strategy |
| v3_1_0_spec_review_claude | [v3_1_0_Spec_Review_Claude.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Spec_Review_Claude.md) | review |
| v3_1_0_spec_review_consolidation | [v3_1_0_Spec_Review_Consolidation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Spec_Review_Consolidation.md) | review |
| v3_1_0_track_a_ca_rulings_d3a | [v3_1_0_Track_A_CA_Rulings_D3a.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_A_CA_Rulings_D3a.md) | decision |
| v3_1_0_track_a_code_review_consolidation | [v3_1_0_Track_A_Code_Review_Consolidation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_A_Code_Review_Consolidation.md) | review |
| v3_1_0_track_a_final_approval_d6a | [v3_1_0_Track_A_Final_Approval_D6a.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_A_Final_Approval_D6a.md) | decision |
| v3_1_0_track_a_implementation_prompt | [v3_1_0_Track_A_Implementation_Prompt_Antigravity.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_A_Implementation_Prompt_Antigravity.md) | implementation |
| v3_1_0_track_a_pr_review_chief_architect | [v3_1_0_Track_A_PR_Review_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_A_PR_Review_Chief_Architect.md) | review |
| v3_1_0_track_b_code_review_consolidation | [v3_1_0_Track_B_Code_Review_Consolidation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_B_Code_Review_Consolidation.md) | review |
| v3_1_0_track_b_final_approval_chief_architect | [v3_1_0_Track_B_Final_Approval_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_B_Final_Approval_Chief_Architect.md) | approval |
| v3_1_0_track_b_pr_review_chief_architect | [v3_1_0_Track_B_PR_Review_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_B_PR_Review_Chief_Architect.md) | review |
| v3_1_0_verification_consolidation | [v3_1_0_Verification_Consolidation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Verification_Consolidation.md) | review |
| v3_1_1_chief_architect_response | [v3.1.1_Chief_Architect_Response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.1.1/v3.1.1_Chief_Architect_Response.md) | strategy |
| v3_1_1_final_approval | [v3.1.1_Final_Approval_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.1.1/v3.1.1_Final_Approval_Chief_Architect.md) | strategy |
| v3_1_1_implementation_prompt_antigravity | [v3.1.1_Implementation_Prompt_Antigravity.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.1.1/v3.1.1_Implementation_Prompt_Antigravity.md) | strategy |
| v3_1_1_implementation_spec | [v3.1.1-Implementation-Spec.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.1.1/v3.1.1-Implementation-Spec.md) | strategy |
| v3_1_1_init_improvements_proposal | [init_improvements_proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.1.1/init_improvements_proposal.md) | strategy |
| v3_1_1_pr_review_chief_architect | [v3.1.1_PR_Review_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.1.1/v3.1.1_PR_Review_Chief_Architect.md) | strategy |
| v3_1_1_spec_review_claude | [v3.1.1_Spec_Review_Claude.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.1.1/v3.1.1_Spec_Review_Claude.md) | atom |
| v3_1_consolidated_remediation_plan | [consolidated_remediation_plan.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.1_Review/consolidated_remediation_plan.md) | strategy |
| v3_1_tech_debt_wrapper_commands | [tech-debt-wrapper-commands.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/tech-debt-wrapper-commands.md) | tech-debt |
| v3_2_antigravity_implementation_prompt | [v3.2_Antigravity_Implementation_Prompt.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2/v3.2_rearchitecting/v3.2_Antigravity_Implementation_Prompt.md) | strategy |
| v3_2_backlog | [v3_2_backlog.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.2/v3_2_backlog.md) | strategy |
| v3_2_ca_response_consolidation | [v3.2_CA_Response_Review_Consolidation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2/v3.2_rearchitecting/v3.2_CA_Response_Review_Consolidation.md) | strategy |
| v3_2_candidate_suggestions_exploration | [candidate_suggestions_exploration.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2/candidate_suggestions_exploration.md) | strategy |
| v3_2_code_review_claude | [v3.2_Code_Review_Claude.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2/v3.2_rearchitecting/v3.2_Code_Review_Claude.md) | atom |
| v3_2_code_review_consolidation | [v3.2_Code_Review_Consolidation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2/v3.2_rearchitecting/v3.2_Code_Review_Consolidation.md) | strategy |
| v3_2_environment_manifest_detection_proposal | [v3.2_Environment_Manifest_Detection_Proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2/v3.2_Environment_Manifest_Detection_Proposal.md) | strategy |
| v3_2_implementation_spec | [v3.2_Re-Architecture_Support_Implementation_Spec.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2/v3.2_rearchitecting/v3.2_Re-Architecture_Support_Implementation_Spec.md) | strategy |
| v3_2_pr_review_chief_architect | [v3.2_PR_Review_Chief_Architect.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2/v3.2_rearchitecting/v3.2_PR_Review_Chief_Architect.md) | strategy |
| v3_2_proposal_finalization_ca | [v3.2_Proposal_Finalization_CA.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2/v3.2_rearchitecting/v3.2_Proposal_Finalization_CA.md) | strategy |
| v3_2_re_architecture_ca_response | [v3.2_Re-Architecture_CA_Response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2/v3.2_rearchitecting/v3.2_Re-Architecture_CA_Response.md) | strategy |
| v3_2_re_architecture_support_proposal | [v3.2_Re-Architecture_Support_Proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2/v3.2_rearchitecting/v3.2_Re-Architecture_Support_Proposal.md) | strategy |


## 5. Documentation Staleness Audit
No documents use the `describes` field.
