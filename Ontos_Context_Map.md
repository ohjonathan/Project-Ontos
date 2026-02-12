---
type: generated
generator: ontos_generate_context_map
generated: "2026-02-12 04:52:40 UTC"
mode: Contributor
scanned: .ontos-internal
---

> **Note for users:** This context map documents Project Ontos's own development.
> When you run `ontos map` in your project, this file will be overwritten with your project's context.

# Ontos Context Map
Generated on: 2026-02-11 23:52:40
Scanned Directory: `/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal, docs`

## 1. Hierarchy Tree
### KERNEL
- **constitution** [L2] (constitution.md) ~292 tokens
  - Status: active
  - Depends On: mission
- **mission** [L2] (mission.md) ~377 tokens
  - Status: active
  - Depends On: None
- **ontology_spec** [L2] (ontology_spec.md) ~700 tokens
  - Status: active
  - Depends On: None
- **ontos_agent_instructions** [L2] (Ontos_Agent_Instructions.md) ~2,500 tokens
  - Status: active
  - Depends On: ontos_manual
- **ontos_manual** [L2] (Ontos_Manual.md) ~4,500 tokens
  - Status: active
  - Depends On: None
- **ontos_philosophy_and_ontology** [L2] (Ontos_Philosophy_and_Ontology_v2_draft.md) ~7,300 tokens
  - Status: active
  - Depends On: mission, philosophy, constitution
- **philosophy** [L2] (philosophy.md) ~1,700 tokens
  - Status: active
  - Depends On: mission
- **v304** [L0] (v3.0.4.md) ~309 tokens  ⚠️ scaffold
  - Status: scaffold
  - Depends On: None
- **v310** [L0] (v3.1.0.md) ~671 tokens  ⚠️ scaffold
  - Status: scaffold
  - Depends On: None
- **v322** [L0] (v3.2.2.md) ~362 tokens  ⚠️ scaffold
  - Status: scaffold
  - Depends On: None

### STRATEGY
- **agent_instruction_template_parity** [L1] (agent_instruction_template_parity.md) ~1,400 tokens  ⚠️ complete
  - Status: complete
  - Depends On: None
- **chief_architect_phase3_response** [L2] (Chief_Architect_Phase3_Response.md) ~3,200 tokens
  - Status: active
  - Depends On: phase3_implementation_spec
- **install_experience_technical_debt_proposal** [L2] [draft] (Install_Experience_Technical_Debt_Proposal.md) ~2,000 tokens
  - Status: draft
  - Depends On: v3_0_implementation_roadmap, installation_ux_proposal
- **maintain_command_review** [L2] [draft] (maintain_command_review.md) ~2,500 tokens
  - Status: draft
  - Depends On: maintain_command_proposal
- **maintain_command_v3_proposal** [L2] [draft] (Maintain_Command_v3_Proposal.md) ~1,800 tokens
  - Status: draft
  - Depends On: v3_0_implementation_roadmap, v3_0_technical_architecture
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
- **v311** [L0] (v3.1.1.md) ~184 tokens  ⚠️ scaffold
  - Status: scaffold
  - Depends On: None
- **v321** [L0] (v3.2.1.md) ~414 tokens  ⚠️ scaffold
  - Status: scaffold
  - Depends On: None
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
- **v3_2_2_interop_discussion** [L2] [draft] (interop_maintenance_discussion.md) ~734 tokens
  - Status: draft
  - Depends On: v3_1_0_obsidian_compatibility_spec, v3_2_1_tiered_context_map_exploration
- **v3_2_2_maintain_command_proposal** [L2] (maintain_command_proposal.md) ~679 tokens
  - Status: complete
  - Depends On: ontos_agent_instructions, v3_2_2_interop_discussion
- **v3_2_4_discovery_design_report** [L2] [draft] (v3.2.4_Discovery_Design_Report.md) ~6,000 tokens
  - Status: draft
  - Depends On: v3_2_2_interop_discussion
- **v3_2_4_proposal_library_maintenance** [L2] [draft] (v3.2.4_Proposal_Library_Maintenance.md) ~2,700 tokens
  - Status: draft
  - Depends On: v3_2_2_interop_discussion, v3_2_4_discovery_design_report
- **v3_2_backlog** [L2] (v3_2_backlog.md) ~1,300 tokens
  - Status: active
  - Depends On: v3_1_0_track_b_final_approval_chief_architect
- **v3_2_code_review_consolidation** [L2] (v3.2_Code_Review_Consolidation.md) ~1,400 tokens
  - Status: active
  - Depends On: v3_2_pr_review_chief_architect, v3_2_code_review_claude, v3_2_code_review_codex
- **v3_3_merged_audit_findings** [L2] (v3.3_Merged_Audit_Findings.md) ~4,200 tokens
  - Status: active
  - Depends On: v3_3_audit_architecture_claude_code, v3_2_backlog
- **v3_3_release_plan** [L2] (v3.3_Release_Plan.md) ~2,000 tokens
  - Status: active
  - Depends On: v3_3_merged_audit_findings, v3_2_4_prea_consolidation
- **v3_3_track_a1_alignment_review** [L2] (v3.3_Track_A1_Alignment_Review.md) ~3,900 tokens
  - Status: active
  - Depends On: v3_3_track_a1_implementation_spec, v3_3_merged_audit_findings, v3_3_release_plan
- **v3_3_track_a1_ca_crosscheck** [L2] (v3.3_Track_A1_CA_CrossCheck.md) ~1,800 tokens
  - Status: active
  - Depends On: v3_3_track_a1_implementation_spec, v3_3_merged_audit_findings
- **v3_3_track_a1_hardening_prompt** [L2] [draft] (v3.3_Track_A1_Hardening_Prompt.md) ~5,200 tokens
  - Status: draft
  - Depends On: v3_3_track_a1_adversarial_review
- **v3_3_track_a1_implementation_spec** [L2] (v3.3_Track_A1_Implementation_Spec.md) ~5,900 tokens
  - Status: active
  - Depends On: v3_3_release_plan, v3_3_merged_audit_findings
- **v3_3_track_a1_review_consolidation_remediation** [L2] (v3.3_Track_A1_Review_Consolidation_Remediation.md) ~2,700 tokens
  - Status: active
  - Depends On: v3_3_track_a1_peer_review, v3_3_track_a1_alignment_review, v3_3_track_a1_adversarial_review
- **v3_3_track_a2_implementation_spec** [L2] [draft] (v3.3_Track_A2_Implementation_Spec.md) ~3,300 tokens
  - Status: draft
  - Depends On: v3_3_release_plan, v3_3_merged_audit_findings
- **v3_3_track_b_implementation_spec** [L2] [draft] (v3.3_Track_B_Implementation_Spec.md) ~8,700 tokens
  - Status: draft
  - Depends On: v3_3_release_plan, v3_3_track_a1_implementation_spec, v3_3_track_a1_adversarial_review, v3_2_4_prea_consolidation, v3_3b_track_b_kickoff
- **v3_3_track_b_implementation_spec_v2** [L2] [draft] (v3.3_Track_B_Implementation_Spec_v2.md) ~11,700 tokens
  - Status: draft
  - Depends On: v3_3_release_plan, v3_3_track_a1_implementation_spec, v3_3_track_a1_adversarial_review, v3_2_4_prea_consolidation, v3_3b_track_b_kickoff
- **v3_3b_track_b_kickoff** [L2] (v3.3b_Track_B_Kickoff.md) ~326 tokens
  - Status: active
  - Depends On: v3_3_release_plan, v3_3_track_a1_implementation_spec

### ATOM
- **chief_architect_round2_critical_analysis** [L2] (Chief_Architect_Round2_Critical_Analysis.md) ~1,800 tokens
  - Status: complete
  - Depends On: claude_opus_4_5_phase2_verification_review
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
- **ontos_technical_architecture_map** [L2] (Ontos-Technical-Architecture-Map.md) ~2,300 tokens
  - Status: active
  - Depends On: v3_0_technical_architecture
- **ontos_technical_architecture_map_codex** [L2] (Ontos-Technical-Architecture-Map-Codex.md) ~3,500 tokens
  - Status: active
  - Depends On: v3_0_technical_architecture
- **pr66_review_consolidation** [L2] (pr66_review_consolidation.md) ~3,500 tokens
  - Status: complete
  - Depends On: agent_instruction_template_parity
- **schema** [L2] (schema.md) ~450 tokens
  - Status: active
  - Depends On: philosophy
- **v302** [L0] (v3.0.2.md) ~168 tokens  ⚠️ scaffold
  - Status: scaffold
  - Depends On: None
- **v305** [L0] (v3.0.5.md) ~391 tokens  ⚠️ scaffold
  - Status: scaffold
  - Depends On: None
- **v320** [L0] (v3.2.0.md) ~745 tokens  ⚠️ scaffold
  - Status: scaffold
  - Depends On: None
- **v3_0_3_hybrid_review_adversarial_codex** [L2] (v3.0.3_Hybrid_Review_Adversarial_Codex.md) ~2,700 tokens
  - Status: complete
  - Depends On: v3.0.3_Implementation_Spec

### LOG
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
- **log_20260129_v3_2_0_activation_fixes** [L2] (2026-01-29_v3-2-0-activation-fixes.md) ~352 tokens
  - Status: active
  - Impacts: map_command, agents_command, context_map
- **log_20260131_v3_2_1_and_v3_2_2_proposals** [L2] (2026-01-31_version-string-to-3-2-0-for-ci-tag-validation.md) ~361 tokens
  - Status: active
  - Impacts: ontos_agent_instructions, v3_2_re_architecture_support_proposal
- **log_20260201_add-v3-2-1-activation-resilience-and-v3-2-2-mainta** [L1] (2026-02-01_add-v3-2-1-activation-resilience-and-v3-2-2-mainta.md) ~89 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260207_improve-hidden-command-handling-add-warn-legacy** [L1] (2026-02-07_improve-hidden-command-handling-add-warn-legacy.md) ~309 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260209_close-critical-paths-edge-cases** [L1] (2026-02-09_close-critical-paths-edge-cases.md) ~298 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260209_make-critical-paths-config-driven** [L1] (2026-02-09_make-critical-paths-config-driven.md) ~315 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260209_polish-path-formatting-and-tests** [L1] (2026-02-09_polish-path-formatting-and-tests.md) ~339 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260209_reorganize-proposals-assets-and-logs-65** [L1] (2026-02-09_reorganize-proposals-assets-and-logs-65.md) ~400 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260210_codex-activation-resilience-maintain-command-revie** [L1] (2026-02-10_codex-activation-resilience-maintain-command-revie.md) ~85 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260210_github-releases-auth-fix** [L1] (2026-02-10_github-releases-auth-fix.md) ~313 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260210_session-active-received-v3-3-track-a1-implementati** [L1] (2026-02-10_session-active-received-v3-3-track-a1-implementati.md) ~84 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260210_v3-2-2-release-docs-and-tag** [L1] (2026-02-10_v3-2-2-release-docs-and-tag.md) ~71 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260210_v3-2-3-final-merge-release-wrap** [L1] (2026-02-10_v3-2-3-final-merge-release-wrap.md) ~405 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260210_v3-2-3-pr66-cross-check-backlog-cleanup** [L1] (2026-02-10_v3-2-3-pr66-cross-check-backlog-cleanup.md) ~321 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260211_init** [L1] (2026-02-11_init.md) ~59 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260211_v3-3-a1-final-hardening-wrap** [L1] (2026-02-11_v3-3-a1-final-hardening-wrap.md) ~76 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260211_v3-3-a1-hardening-tail-cherry-picked-into-main** [L1] (2026-02-11_v3-3-a1-hardening-tail-cherry-picked-into-main.md) ~92 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260211_v3-3-track-a2-command-safety-hardening-closure** [L1] (2026-02-11_v3-3-track-a2-command-safety-hardening-closure.md) ~89 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260211_v3-3-track-a3-merge-closeout** [L1] (2026-02-11_v3-3-track-a3-merge-closeout.md) ~77 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260211_v3-3-track-a4-docs-tests-dead-code-cleanup-and-def** [L1] (2026-02-11_v3-3-track-a4-docs-tests-dead-code-cleanup-and-def.md) ~85 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260211_v3-3a-merge-cleanup-and-v3-3b-setup-wrap** [L1] (2026-02-11_v3-3a-merge-cleanup-and-v3-3b-setup-wrap.md) ~484 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260211_v3-3a-v3-3b-folder-split-and-track-b-kickoff** [L1] (2026-02-11_v3-3a-v3-3b-folder-split-and-track-b-kickoff.md) ~79 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260211_v3-3b-pr2-ready-to-merge** [L1] (2026-02-11_v3-3b-pr2-ready-to-merge.md) ~76 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **log_20260211_v3-3b-track-b-complete** [L1] (2026-02-11_v3-3b-track-b-complete.md) ~69 tokens  ⚠️ active
  - Status: active
  - Impacts: None
- **v300** [L0] (v3.0.0.md) ~518 tokens  ⚠️ scaffold
  - Status: scaffold
  - Impacts: None
- **v330** [L2] (v3.3.0.md) ~1,100 tokens
  - Status: active
  - Impacts: None

### UNKNOWN
- **migration_v2_to_v3** [L2] (Migration_v2_to_v3.md) ~761 tokens
  - Status: active
  - Depends On: ontos_manual
- **ontos_internal_tmp_readme** [L1] (README.md) ~135 tokens  ⚠️ active
  - Status: active
  - Depends On: None
- **phase3_implementation_spec_review_codex** [L0] [draft] (Phase3-Implementation-Spec-Review-Codex.md) ~2,100 tokens  ⚠️ draft
  - Status: draft
  - Depends On: None
- **phase4_final_approval_chief_architect** [L2] (Phase4_Final_Approval_Chief_Architect.md) ~776 tokens
  - Status: complete
  - Depends On: phase4_pr_review_chief_architect
- **phase4_pr_review_chief_architect** [L2] (Phase4_PR_Review_Chief_Architect.md) ~1,600 tokens
  - Status: complete
  - Depends On: phase4_chief_architect_response
- **proposals_naming_conventions** [L1] (README.md) ~145 tokens  ⚠️ active
  - Status: active
  - Depends On: None
- **v301** [L0] (v3.0.1.md) ~126 tokens  ⚠️ scaffold
  - Status: scaffold
  - Depends On: None
- **v323** [L0] (v3.2.3.md) ~159 tokens  ⚠️ scaffold
  - Status: scaffold
  - Depends On: None
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
- **v3_2_4_prea_adversarial_review** [L2] (v3.2.4_PreA_Adversarial_Review.md) ~6,800 tokens
  - Status: active
  - Depends On: v3_2_4_proposal_library_maintenance, v3_2_4_discovery_design_report
- **v3_2_4_prea_alignment_review** [L2] (v3.2.4_PreA_Alignment_Review.md) ~2,500 tokens
  - Status: active
  - Depends On: v3_2_4_proposal_library_maintenance, v3_2_4_discovery_design_report, v3_2_4_discovery_feasibility_report
- **v3_2_4_prea_consolidation** [L2] (v3.2.4_PreA_Consolidation.md) ~4,200 tokens
  - Status: active
  - Depends On: v3_2_4_prea_peer_review, v3_2_4_prea_alignment_review, v3_2_4_prea_adversarial_review
- **v3_3_audit_architecture_claude_code** [L2] (v3.3_Audit_Architecture_ClaudeCode.md) ~5,300 tokens
  - Status: active
  - Depends On: v3_2_4_proposal_library_maintenance
- **v3_3_track_a1_adversarial_review** [L2] (v3.3_Track_A1_Adversarial_Review.md) ~7,800 tokens
  - Status: active
  - Depends On: v3_3_track_a1_implementation_spec, v3_3_merged_audit_findings
- **v3_3_track_a2_review** [L2] (v3.3_Track_A2_Review.md) ~4,900 tokens
  - Status: active
  - Depends On: v3_3_track_a2_implementation_spec
- **v3_3_track_a3_review** [L2] (v3.3_Track_A3_Review.md) ~4,500 tokens
  - Status: active
  - Depends On: v3_3_release_plan
- **v3_3_track_b_adversarial_review** [L2] (v3.3_Track_B_Adversarial_Review.md) ~7,200 tokens
  - Status: active
  - Depends On: v3_3_track_b_implementation_spec, v3_3_track_a1_adversarial_review, v3_2_4_prea_consolidation, v3_2_4_discovery_content_report
- **v3_3_track_b_peer_review** [L2] [draft] (v3.3_Track_B_Peer_Review.md) ~2,000 tokens
  - Status: draft
  - Depends On: v3_3_track_b_implementation_spec, v3_3_release_plan, v3_3_track_a1_implementation_spec, v3_3_track_a1_adversarial_review, v3_2_4_prea_consolidation
- **v3_3_track_b_pr1_review** [L2] (v3.3_Track_B_PR1_Review.md) ~3,600 tokens
  - Status: active
  - Depends On: v3_3_track_b_implementation_spec_v2
- **v3_3_track_b_pr2_review** [L2] (v3.3_Track_B_PR2_Review.md) ~4,500 tokens
  - Status: active
  - Depends On: v3_3_track_b_implementation_spec_v2
- **v3_3_track_b_pr3_review** [L2] (v3.3_Track_B_PR3_Review.md) ~5,600 tokens
  - Status: active
  - Depends On: v3_3_track_b_implementation_spec_v2
- **v3_3_track_b_review_consolidation** [L2] (v3.3_Track_B_Review_Consolidation.md) ~1,900 tokens
  - Status: active
  - Depends On: v3_3_track_b_peer_review, v3_3_track_b_alignment_review, v3_3_track_b_adversarial_review, v3_3_track_b_implementation_spec_v2


## 2. Recent Timeline
- **v3.3.0.md** [release] **V3.3.0** (`v330`)
  - Concepts: v3.3, unified-loader, link-check, rename, command-safety, cli-surface
- **v3.0.0.md** [None] **V3.0.0** (`v300`)
- **2026-02-11** [release] **V3 3B Track B Complete** (`log_20260211_v3-3b-track-b-complete`)
- **2026-02-11** [chore] **V3 3B Pr2 Ready To Merge** (`log_20260211_v3-3b-pr2-ready-to-merge`)
- **2026-02-11** [chore] **V3 3A V3 3B Folder Split And Track B Kickoff** (`log_20260211_v3-3a-v3-3b-folder-split-and-track-b-kickoff`)
- **2026-02-11** [chore] **V3 3A Merge Cleanup And V3 3B Setup Wrap** (`log_20260211_v3-3a-merge-cleanup-and-v3-3b-setup-wrap`)
- **2026-02-11** [chore] **V3 3 Track A4 Docs Tests Dead Code Cleanup And Def** (`log_20260211_v3-3-track-a4-docs-tests-dead-code-cleanup-and-def`)
- **2026-02-11** [v3_3_track_a3_merge_closeout] **V3 3 Track A3 Merge Closeout** (`log_20260211_v3-3-track-a3-merge-closeout`)
- **2026-02-11** [release] **V3 3 Track A2 Command Safety Hardening Closure** (`log_20260211_v3-3-track-a2-command-safety-hardening-closure`)
- **2026-02-11** [fix] **V3 3 A1 Hardening Tail Cherry Picked Into Main** (`log_20260211_v3-3-a1-hardening-tail-cherry-picked-into-main`)

*Showing 10 of 45 sessions*

## 3. Dependency Audit
- [BROKEN LINK] **v3_2_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/tmp/v3.2_Code_Review_Consolidation.md) references missing ID: `v3_2_pr_review_chief_architect`
  Fix: Add a document with `id: v3_2_pr_review_chief_architect` or remove it from depends_on
- [BROKEN LINK] **v3_2_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/tmp/v3.2_Code_Review_Consolidation.md) references missing ID: `v3_2_code_review_claude`
  Fix: Add a document with `id: v3_2_code_review_claude` or remove it from depends_on
- [BROKEN LINK] **v3_2_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/tmp/v3.2_Code_Review_Consolidation.md) references missing ID: `v3_2_code_review_codex`
  Fix: Add a document with `id: v3_2_code_review_codex` or remove it from depends_on
- [BROKEN LINK] **v3_0_3_hybrid_review_adversarial_codex** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/tmp/v3.0.3_Hybrid_Review_Adversarial_Codex.md) references missing ID: `v3.0.3_Implementation_Spec`
  Fix: Add a document with `id: v3.0.3_Implementation_Spec` or remove it from depends_on
- [BROKEN LINK] **install_experience_technical_debt_proposal** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/Install_Experience_Technical_Debt_Proposal.md) references missing ID: `installation_ux_proposal`
  Fix: Add a document with `id: installation_ux_proposal` or remove it from depends_on
- [BROKEN LINK] **v3_2_4_prea_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.4/v3.2.4_PreA_Consolidation.md) references missing ID: `v3_2_4_prea_peer_review`
  Fix: Add a document with `id: v3_2_4_prea_peer_review` or remove it from depends_on
- [BROKEN LINK] **v3_2_4_prea_alignment_review** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.4/v3.2.4_PreA_Alignment_Review.md) references missing ID: `v3_2_4_discovery_feasibility_report`
  Fix: Add a document with `id: v3_2_4_discovery_feasibility_report` or remove it from depends_on
- [BROKEN LINK] **v3_2_2_interop_discussion** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.4/interop_maintenance_discussion.md) references missing ID: `v3_2_1_tiered_context_map_exploration`
  Fix: Add a document with `id: v3_2_1_tiered_context_map_exploration` or remove it from depends_on
- [BROKEN LINK] **maintain_command_review** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.2/maintain_command_review.md) references missing ID: `maintain_command_proposal`
  Fix: Add a document with `id: maintain_command_proposal` or remove it from depends_on
- [BROKEN LINK] **v3_3_track_a1_review_consolidation_remediation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Track_A1_Review_Consolidation_Remediation.md) references missing ID: `v3_3_track_a1_peer_review`
  Fix: Add a document with `id: v3_3_track_a1_peer_review` or remove it from depends_on
- [BROKEN LINK] **v3_3_track_b_adversarial_review** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_Adversarial_Review.md) references missing ID: `v3_2_4_discovery_content_report`
  Fix: Add a document with `id: v3_2_4_discovery_content_report` or remove it from depends_on
- [BROKEN LINK] **v3_3_track_b_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_Review_Consolidation.md) references missing ID: `v3_3_track_b_alignment_review`
  Fix: Add a document with `id: v3_3_track_b_alignment_review` or remove it from depends_on
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
- [BROKEN LINK] **v3_1_tech_debt_wrapper_commands** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/tech-debt-wrapper-commands.md) references missing ID: `phase_v3_0_4_implementation_spec`
  Fix: Add a document with `id: phase_v3_0_4_implementation_spec` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_spec_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Spec_Review_Consolidation.md) references missing ID: `v3_1_0_spec_review_gemini`
  Fix: Add a document with `id: v3_1_0_spec_review_gemini` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_spec_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Spec_Review_Consolidation.md) references missing ID: `v3_1_0_spec_review_gpt5`
  Fix: Add a document with `id: v3_1_0_spec_review_gpt5` or remove it from depends_on
- [BROKEN LINK] **v3_1_0_track_b_pr_review_chief_architect** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_B_PR_Review_Chief_Architect.md) references missing ID: `v3_1_0_track_b_implementation_prompt_antigravity`
  Fix: Add a document with `id: v3_1_0_track_b_implementation_prompt_antigravity` or remove it from depends_on
- [ORPHAN] **v3_3_track_a2_review** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Track_A2_Review.md) has no dependents
  Fix: Add `v3_3_track_a2_review` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_1_0_track_b_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_B_Code_Review_Consolidation.md) has no dependents
  Fix: Add `v3_1_0_track_b_code_review_consolidation` to another document's depends_on, or delete if unused
- [ORPHAN] **proposals_naming_conventions** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/README.md) has no dependents
  Fix: Add `proposals_naming_conventions` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_3_track_b_pr1_review** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_PR1_Review.md) has no dependents
  Fix: Add `v3_3_track_b_pr1_review` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_1_0_chief_architect_response** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Chief_Architect_Response.md) has no dependents
  Fix: Add `v3_1_0_chief_architect_response` to another document's depends_on, or delete if unused
- [ORPHAN] **phase3_implementation_spec_review_codex** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase3/Phase3-Implementation-Spec-Review-Codex.md) has no dependents
  Fix: Add `phase3_implementation_spec_review_codex` to another document's depends_on, or delete if unused
- [ORPHAN] **v301** (docs/releases/v3.0.1.md) has no dependents
  Fix: Add `v301` to another document's depends_on, or delete if unused
- [ORPHAN] **v323** (docs/releases/v3.2.3.md) has no dependents
  Fix: Add `v323` to another document's depends_on, or delete if unused
- [ORPHAN] **ontos_internal_tmp_readme** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/tmp/README.md) has no dependents
  Fix: Add `ontos_internal_tmp_readme` to another document's depends_on, or delete if unused
- [ORPHAN] **migration_v2_to_v3** (docs/reference/Migration_v2_to_v3.md) has no dependents
  Fix: Add `migration_v2_to_v3` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_3_track_b_pr3_review** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_PR3_Review.md) has no dependents
  Fix: Add `v3_3_track_b_pr3_review` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_3_track_b_pr2_review** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_PR2_Review.md) has no dependents
  Fix: Add `v3_3_track_b_pr2_review` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_3_track_b_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_Review_Consolidation.md) has no dependents
  Fix: Add `v3_3_track_b_review_consolidation` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_1_0_track_a_code_review_consolidation** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_A_Code_Review_Consolidation.md) has no dependents
  Fix: Add `v3_1_0_track_a_code_review_consolidation` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_3_track_a3_review** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Track_A3_Review.md) has no dependents
  Fix: Add `v3_3_track_a3_review` to another document's depends_on, or delete if unused
- [ORPHAN] **v3_1_0_track_a_final_approval_d6a** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/v3_1_0_Track_A_Final_Approval_D6a.md) has no dependents
  Fix: Add `v3_1_0_track_a_final_approval_d6a` to another document's depends_on, or delete if unused
- [DEPTH] **v3_3_track_a2_review** has dependency depth 12 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_a1_implementation_spec** has dependency depth 11 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_track_a_ca_rulings_d3a** has dependency depth 10 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_b_pr1_review** has dependency depth 14 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_track_a_pr_review_chief_architect** has dependency depth 9 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_chief_architect_response** has dependency depth 11 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_audit_triage_chief_architect** has dependency depth 8 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_implementation_spec** has dependency depth 6 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3b_track_b_kickoff** has dependency depth 12 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_research_review_chief_architect** has dependency depth 7 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_2_4_prea_adversarial_review** has dependency depth 8 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_b_implementation_spec_v2** has dependency depth 13 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_a1_hardening_prompt** has dependency depth 13 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_a1_alignment_review** has dependency depth 12 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_2_4_prea_alignment_review** has dependency depth 8 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_2_4_proposal_library_maintenance** has dependency depth 7 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_spec_review_claude** has dependency depth 9 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_release_plan** has dependency depth 10 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_a1_adversarial_review** has dependency depth 12 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_2_2_maintain_command_proposal** has dependency depth 6 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_final_decision_chief_architect** has dependency depth 7 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_b_pr3_review** has dependency depth 14 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_spec_review_consolidation** has dependency depth 10 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_b_pr2_review** has dependency depth 14 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_a1_ca_crosscheck** has dependency depth 12 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_b_review_consolidation** has dependency depth 15 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_a2_implementation_spec** has dependency depth 11 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_track_a_code_review_consolidation** has dependency depth 10 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_b_adversarial_review** has dependency depth 14 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_2_4_prea_consolidation** has dependency depth 9 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_audit_architecture_claude_code** has dependency depth 8 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_a3_review** has dependency depth 11 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_merged_audit_findings** has dependency depth 9 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_track_a_final_approval_d6a** has dependency depth 11 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_2_4_discovery_design_report** has dependency depth 6 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_b_implementation_spec** has dependency depth 13 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_b_peer_review** has dependency depth 14 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_sidecar_pattern** has dependency depth 6 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_3_track_a1_review_consolidation_remediation** has dependency depth 13 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [DEPTH] **v3_1_0_track_a_implementation_prompt** has dependency depth 8 (max: 5)
  Fix: Refactor to reduce nesting or increase MAX_DEPENDENCY_DEPTH in ontos_config.py
- [ARCHITECTURE] **v3_2_backlog** (strategy) depends on **v3_1_0_track_b_final_approval_chief_architect** (approval)
  Fix: strategy should not depend on approval. Invert the dependency or change document types
- [ARCHITECTURE] **phase2_implementation_instructions_antigravity** (strategy) depends on **chief_architect_round2_critical_analysis** (atom)
  Fix: strategy should not depend on atom. Invert the dependency or change document types
- [ARCHITECTURE] **phase5_implementation_spec** (strategy) depends on **phase4_final_approval_chief_architect** (approval)
  Fix: strategy should not depend on approval. Invert the dependency or change document types
- [ARCHITECTURE] **v3_3_track_a1_hardening_prompt** (strategy) depends on **v3_3_track_a1_adversarial_review** (review)
  Fix: strategy should not depend on review. Invert the dependency or change document types
- [ARCHITECTURE] **v3_3_merged_audit_findings** (strategy) depends on **v3_3_audit_architecture_claude_code** (review)
  Fix: strategy should not depend on review. Invert the dependency or change document types
- [ARCHITECTURE] **v3_3_release_plan** (strategy) depends on **v3_2_4_prea_consolidation** (review)
  Fix: strategy should not depend on review. Invert the dependency or change document types
- [ARCHITECTURE] **v3_3_track_a1_review_consolidation_remediation** (strategy) depends on **v3_3_track_a1_adversarial_review** (review)
  Fix: strategy should not depend on review. Invert the dependency or change document types
- [ARCHITECTURE] **v3_3_track_b_implementation_spec** (strategy) depends on **v3_3_track_a1_adversarial_review** (review)
  Fix: strategy should not depend on review. Invert the dependency or change document types
- [ARCHITECTURE] **v3_3_track_b_implementation_spec** (strategy) depends on **v3_2_4_prea_consolidation** (review)
  Fix: strategy should not depend on review. Invert the dependency or change document types
- [ARCHITECTURE] **v3_3_track_b_implementation_spec_v2** (strategy) depends on **v3_3_track_a1_adversarial_review** (review)
  Fix: strategy should not depend on review. Invert the dependency or change document types
- [ARCHITECTURE] **v3_3_track_b_implementation_spec_v2** (strategy) depends on **v3_2_4_prea_consolidation** (review)
  Fix: strategy should not depend on review. Invert the dependency or change document types
- [ARCHITECTURE] **v3_1_0_implementation_spec** (strategy) depends on **v3_1_tech_debt_wrapper_commands** (tech-debt)
  Fix: strategy should not depend on tech-debt. Invert the dependency or change document types
- [MISSING FIELD] **v300** (docs/releases/v3.0.0.md) is type 'log' but missing required field: event_type
  Fix: Add `event_type: feature|fix|refactor|exploration|chore` to frontmatter
- [INVALID VALUE] **log_20260210_codex-activation-resilience-maintain-command-revie** (docs/logs/2026-02-10_codex-activation-resilience-maintain-command-revie.md) has invalid event_type: 'session'
  Fix: Use one of: chore, decision, exploration, feature, fix, refactor, release
- [INVALID VALUE] **log_20260209_polish-path-formatting-and-tests** (docs/logs/2026-02-09_polish-path-formatting-and-tests.md) has invalid event_type: 'pr-62-key-documents-paths'
  Fix: Use one of: chore, decision, exploration, feature, fix, refactor, release
- [INVALID VALUE] **log_20260209_make-critical-paths-config-driven** (docs/logs/2026-02-09_make-critical-paths-config-driven.md) has invalid event_type: 'v3-2-1b-critical-paths'
  Fix: Use one of: chore, decision, exploration, feature, fix, refactor, release
- [INVALID VALUE] **log_20260121_feat-cli-ontos-v3-1-0-track-b-native-command-m** (docs/logs/2026-01-21_feat-cli-ontos-v3-1-0-track-b-native-command-m.md) has invalid event_type: 'track-b-migration-final'
  Fix: Use one of: chore, decision, exploration, feature, fix, refactor, release
- [INVALID VALUE] **log_20260201_add-v3-2-1-activation-resilience-and-v3-2-2-mainta** (docs/logs/2026-02-01_add-v3-2-1-activation-resilience-and-v3-2-2-mainta.md) has invalid event_type: 'critical-paths-hardcoding-proposal'
  Fix: Use one of: chore, decision, exploration, feature, fix, refactor, release
- [INVALID VALUE] **log_20260209_reorganize-proposals-assets-and-logs-65** (docs/logs/2026-02-09_reorganize-proposals-assets-and-logs-65.md) has invalid event_type: 'post-merge-cleanup'
  Fix: Use one of: chore, decision, exploration, feature, fix, refactor, release
- [INVALID VALUE] **log_20260210_github-releases-auth-fix** (docs/logs/2026-02-10_github-releases-auth-fix.md) has invalid event_type: 'feat'
  Fix: Use one of: chore, decision, exploration, feature, fix, refactor, release
- [INVALID VALUE] **log_20260211_v3-3-track-a3-merge-closeout** (docs/logs/2026-02-11_v3-3-track-a3-merge-closeout.md) has invalid event_type: 'v3_3_track_a3_merge_closeout'
  Fix: Use one of: chore, decision, exploration, feature, fix, refactor, release
- [BROKEN LINK] **log_20260129_v3_2_0_activation_fixes** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-29_v3-2-0-activation-fixes.md) impacts non-existent document: `map_command`
  Fix: Create `map_command`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260129_v3_2_0_activation_fixes** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-29_v3-2-0-activation-fixes.md) impacts non-existent document: `agents_command`
  Fix: Create `agents_command`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260129_v3_2_0_activation_fixes** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-29_v3-2-0-activation-fixes.md) impacts non-existent document: `context_map`
  Fix: Create `context_map`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260117_v3_0_0_activation_survival** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-17_v3_0_0_activation_survival.md) impacts non-existent document: `agents_command`
  Fix: Create `agents_command`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260117_v3_0_0_activation_survival** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-17_v3_0_0_activation_survival.md) impacts non-existent document: `doctor_staleness`
  Fix: Create `doctor_staleness`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260114_philosophy_research_and_tech_debt** (/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-14_philosophy-research-and-tech-debt.md) impacts non-existent document: `obsidian_compatibility_proposal`
  Fix: Create `obsidian_compatibility_proposal`, correct the reference, or archive this log
- [BROKEN LINK] **log_20260131_v3_2_1_and_v3_2_2_proposals** (docs/logs/2026-01-31_version-string-to-3-2-0-for-ci-tag-validation.md) impacts non-existent document: `v3_2_re_architecture_support_proposal`
  Fix: Create `v3_2_re_architecture_support_proposal`, correct the reference, or archive this log
- [LINT] **log_20260113_phase2_v3_0_beta**: Invalid status 'auto-generated'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **phase4_implementation_spec**: Invalid status 'approved'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **proposals_naming_conventions**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_2_4_prea_consolidation**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_2_4_prea_alignment_review**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_2_4_prea_adversarial_review**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_merged_audit_findings**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_release_plan**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_track_a3_review**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_track_a1_alignment_review**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_track_a1_review_consolidation_remediation**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_track_a1_implementation_spec**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_track_a1_adversarial_review**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_audit_architecture_claude_code**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_track_a2_review**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_track_a1_ca_crosscheck**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_track_b_pr3_review**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_track_b_adversarial_review**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3b_track_b_kickoff**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_track_b_review_consolidation**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_track_b_pr2_review**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_3_track_b_pr1_review**: Active document in proposals/. Graduate to strategy/.
- [LINT] **v3_1_0_track_a_implementation_prompt**: Invalid status 'ready'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **v3_1_0_implementation_spec**: Invalid status 'approved'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold
- [LINT] **v3_1_tech_debt_wrapper_commands**: Invalid status 'open'. Use one of: active, archived, complete, deprecated, draft, pending_curation, rejected, scaffold

## 4. Index
| ID | Filename | Type |
|---|---|---|
| agent_instruction_template_parity | [agent_instruction_template_parity.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.3/agent_instruction_template_parity.md) | strategy |
| chief_architect_phase3_response | [Chief_Architect_Phase3_Response.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase3/Chief_Architect_Phase3_Response.md) | strategy |
| chief_architect_round2_critical_analysis | [Chief_Architect_Round2_Critical_Analysis.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase2/Chief_Architect_Round2_Critical_Analysis.md) | atom |
| claude_opus_4_5_phase1_review | [Claude_Opus_4.5_Phase1_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase1/Claude_Opus_4.5_Phase1_Review.md) | atom |
| claude_opus_4_5_phase1_review_round2 | [Claude_Opus_4.5_Phase1_Review_Round2.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase1/Claude_Opus_4.5_Phase1_Review_Round2.md) | atom |
| claude_opus_4_5_phase2_alignment_review | [Claude_Opus_4.5_Phase2_Alignment_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase2/Claude_Opus_4.5_Phase2_Alignment_Review.md) | atom |
| claude_opus_4_5_phase2_verification_review | [Claude_Opus_4.5_Phase2_Verification_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase2/Claude_Opus_4.5_Phase2_Verification_Review.md) | atom |
| claude_opus_4_5_phase3_alignment_review | [Claude_Opus_4.5_Phase3_Alignment_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.0/Phase3/Claude_Opus_4.5_Phase3_Alignment_Review.md) | atom |
| common_concepts | [Common_Concepts.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/reference/Common_Concepts.md) | atom |
| constitution | [constitution.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/kernel/constitution.md) | kernel |
| dual_mode_matrix | [Dual_Mode_Matrix.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/reference/Dual_Mode_Matrix.md) | atom |
| install_experience_technical_debt_proposal | [Install_Experience_Technical_Debt_Proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/Install_Experience_Technical_Debt_Proposal.md) | strategy |
| log_20260112_phase0_v3_0_alpha | [2026-01-12_phase0-v3-0-alpha.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-12_phase0-v3-0-alpha.md) | log |
| log_20260112_phase1_package_structure_complete | [2026-01-12_phase1-package-structure-complete.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-12_phase1-package-structure-complete.md) | log |
| log_20260112_phase1_v3_0_alpha | [2026-01-12_phase1-v3-0-alpha.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-12_phase1-v3-0-alpha.md) | log |
| log_20260112_phase2_core_decomposition | [2026-01-12_phase2-core-decomposition.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-12_phase2-core-decomposition.md) | log |
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
| log_20260129_v3_2_0_activation_fixes | [2026-01-29_v3-2-0-activation-fixes.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-01-29_v3-2-0-activation-fixes.md) | log |
| log_20260131_v3_2_1_and_v3_2_2_proposals | [2026-01-31_version-string-to-3-2-0-for-ci-tag-validation.md](docs/logs/2026-01-31_version-string-to-3-2-0-for-ci-tag-validation.md) | log |
| log_20260201_add-v3-2-1-activation-resilience-and-v3-2-2-mainta | [2026-02-01_add-v3-2-1-activation-resilience-and-v3-2-2-mainta.md](docs/logs/2026-02-01_add-v3-2-1-activation-resilience-and-v3-2-2-mainta.md) | log |
| log_20260207_improve-hidden-command-handling-add-warn-legacy | [2026-02-07_improve-hidden-command-handling-add-warn-legacy.md](docs/logs/2026-02-07_improve-hidden-command-handling-add-warn-legacy.md) | log |
| log_20260209_close-critical-paths-edge-cases | [2026-02-09_close-critical-paths-edge-cases.md](docs/logs/2026-02-09_close-critical-paths-edge-cases.md) | log |
| log_20260209_make-critical-paths-config-driven | [2026-02-09_make-critical-paths-config-driven.md](docs/logs/2026-02-09_make-critical-paths-config-driven.md) | log |
| log_20260209_polish-path-formatting-and-tests | [2026-02-09_polish-path-formatting-and-tests.md](docs/logs/2026-02-09_polish-path-formatting-and-tests.md) | log |
| log_20260209_reorganize-proposals-assets-and-logs-65 | [2026-02-09_reorganize-proposals-assets-and-logs-65.md](docs/logs/2026-02-09_reorganize-proposals-assets-and-logs-65.md) | log |
| log_20260210_codex-activation-resilience-maintain-command-revie | [2026-02-10_codex-activation-resilience-maintain-command-revie.md](docs/logs/2026-02-10_codex-activation-resilience-maintain-command-revie.md) | log |
| log_20260210_github-releases-auth-fix | [2026-02-10_github-releases-auth-fix.md](docs/logs/2026-02-10_github-releases-auth-fix.md) | log |
| log_20260210_session-active-received-v3-3-track-a1-implementati | [2026-02-10_session-active-received-v3-3-track-a1-implementati.md](docs/logs/2026-02-10_session-active-received-v3-3-track-a1-implementati.md) | log |
| log_20260210_v3-2-2-release-docs-and-tag | [2026-02-10_v3-2-2-release-docs-and-tag.md](docs/logs/2026-02-10_v3-2-2-release-docs-and-tag.md) | log |
| log_20260210_v3-2-3-final-merge-release-wrap | [2026-02-10_v3-2-3-final-merge-release-wrap.md](docs/logs/2026-02-10_v3-2-3-final-merge-release-wrap.md) | log |
| log_20260210_v3-2-3-pr66-cross-check-backlog-cleanup | [2026-02-10_v3-2-3-pr66-cross-check-backlog-cleanup.md](docs/logs/2026-02-10_v3-2-3-pr66-cross-check-backlog-cleanup.md) | log |
| log_20260211_init | [2026-02-11_init.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/logs/2026-02-11_init.md) | log |
| log_20260211_v3-3-a1-final-hardening-wrap | [2026-02-11_v3-3-a1-final-hardening-wrap.md](docs/logs/2026-02-11_v3-3-a1-final-hardening-wrap.md) | log |
| log_20260211_v3-3-a1-hardening-tail-cherry-picked-into-main | [2026-02-11_v3-3-a1-hardening-tail-cherry-picked-into-main.md](docs/logs/2026-02-11_v3-3-a1-hardening-tail-cherry-picked-into-main.md) | log |
| log_20260211_v3-3-track-a2-command-safety-hardening-closure | [2026-02-11_v3-3-track-a2-command-safety-hardening-closure.md](docs/logs/2026-02-11_v3-3-track-a2-command-safety-hardening-closure.md) | log |
| log_20260211_v3-3-track-a3-merge-closeout | [2026-02-11_v3-3-track-a3-merge-closeout.md](docs/logs/2026-02-11_v3-3-track-a3-merge-closeout.md) | log |
| log_20260211_v3-3-track-a4-docs-tests-dead-code-cleanup-and-def | [2026-02-11_v3-3-track-a4-docs-tests-dead-code-cleanup-and-def.md](docs/logs/2026-02-11_v3-3-track-a4-docs-tests-dead-code-cleanup-and-def.md) | log |
| log_20260211_v3-3a-merge-cleanup-and-v3-3b-setup-wrap | [2026-02-11_v3-3a-merge-cleanup-and-v3-3b-setup-wrap.md](docs/logs/2026-02-11_v3-3a-merge-cleanup-and-v3-3b-setup-wrap.md) | log |
| log_20260211_v3-3a-v3-3b-folder-split-and-track-b-kickoff | [2026-02-11_v3-3a-v3-3b-folder-split-and-track-b-kickoff.md](docs/logs/2026-02-11_v3-3a-v3-3b-folder-split-and-track-b-kickoff.md) | log |
| log_20260211_v3-3b-pr2-ready-to-merge | [2026-02-11_v3-3b-pr2-ready-to-merge.md](docs/logs/2026-02-11_v3-3b-pr2-ready-to-merge.md) | log |
| log_20260211_v3-3b-track-b-complete | [2026-02-11_v3-3b-track-b-complete.md](docs/logs/2026-02-11_v3-3b-track-b-complete.md) | log |
| maintain_command_review | [maintain_command_review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.2/maintain_command_review.md) | strategy |
| maintain_command_v3_proposal | [Maintain_Command_v3_Proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/Maintain_Command_v3_Proposal.md) | strategy |
| migration_v2_to_v3 | [Migration_v2_to_v3.md](docs/reference/Migration_v2_to_v3.md) | reference |
| mission | [mission.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/kernel/mission.md) | kernel |
| ontology_spec | [ontology_spec.md](docs/reference/ontology_spec.md) | kernel |
| ontos_agent_instructions | [Ontos_Agent_Instructions.md](docs/reference/Ontos_Agent_Instructions.md) | kernel |
| ontos_internal_tmp_readme | [README.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/tmp/README.md) | reference |
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
| philosophy | [philosophy.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/kernel/philosophy.md) | kernel |
| pr66_review_consolidation | [pr66_review_consolidation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.3/pr66_review_consolidation.md) | atom |
| proposals_naming_conventions | [README.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/README.md) | reference |
| schema | [schema.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/atom/schema.md) | atom |
| v300 | [v3.0.0.md](docs/releases/v3.0.0.md) | log |
| v301 | [v3.0.1.md](docs/releases/v3.0.1.md) | unknown |
| v302 | [v3.0.2.md](docs/releases/v3.0.2.md) | atom |
| v304 | [v3.0.4.md](docs/releases/v3.0.4.md) | kernel |
| v305 | [v3.0.5.md](docs/releases/v3.0.5.md) | atom |
| v310 | [v3.1.0.md](docs/releases/v3.1.0.md) | kernel |
| v311 | [v3.1.1.md](docs/releases/v3.1.1.md) | strategy |
| v320 | [v3.2.0.md](docs/releases/v3.2.0.md) | atom |
| v321 | [v3.2.1.md](docs/releases/v3.2.1.md) | strategy |
| v322 | [v3.2.2.md](docs/releases/v3.2.2.md) | kernel |
| v323 | [v3.2.3.md](docs/releases/v3.2.3.md) | unknown |
| v330 | [v3.3.0.md](docs/releases/v3.3.0.md) | log |
| v3_0_3_hybrid_review_adversarial_codex | [v3.0.3_Hybrid_Review_Adversarial_Codex.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/tmp/v3.0.3_Hybrid_Review_Adversarial_Codex.md) | atom |
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
| v3_1_tech_debt_wrapper_commands | [tech-debt-wrapper-commands.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.1/tech-debt-wrapper-commands.md) | tech-debt |
| v3_2_2_interop_discussion | [interop_maintenance_discussion.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.4/interop_maintenance_discussion.md) | strategy |
| v3_2_2_maintain_command_proposal | [maintain_command_proposal.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.2/maintain_command_proposal.md) | strategy |
| v3_2_4_discovery_design_report | [v3.2.4_Discovery_Design_Report.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.4/v3.2.4_Discovery_Design_Report.md) | strategy |
| v3_2_4_prea_adversarial_review | [v3.2.4_PreA_Adversarial_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.4/v3.2.4_PreA_Adversarial_Review.md) | review |
| v3_2_4_prea_alignment_review | [v3.2.4_PreA_Alignment_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.4/v3.2.4_PreA_Alignment_Review.md) | review |
| v3_2_4_prea_consolidation | [v3.2.4_PreA_Consolidation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.4/v3.2.4_PreA_Consolidation.md) | review |
| v3_2_4_proposal_library_maintenance | [v3.2.4_Proposal_Library_Maintenance.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.2.4/v3.2.4_Proposal_Library_Maintenance.md) | strategy |
| v3_2_backlog | [v3_2_backlog.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/v3.2/v3_2_backlog.md) | strategy |
| v3_2_code_review_consolidation | [v3.2_Code_Review_Consolidation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/tmp/v3.2_Code_Review_Consolidation.md) | strategy |
| v3_3_audit_architecture_claude_code | [v3.3_Audit_Architecture_ClaudeCode.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Audit_Architecture_ClaudeCode.md) | review |
| v3_3_merged_audit_findings | [v3.3_Merged_Audit_Findings.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Merged_Audit_Findings.md) | strategy |
| v3_3_release_plan | [v3.3_Release_Plan.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Release_Plan.md) | strategy |
| v3_3_track_a1_adversarial_review | [v3.3_Track_A1_Adversarial_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Track_A1_Adversarial_Review.md) | review |
| v3_3_track_a1_alignment_review | [v3.3_Track_A1_Alignment_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Track_A1_Alignment_Review.md) | strategy |
| v3_3_track_a1_ca_crosscheck | [v3.3_Track_A1_CA_CrossCheck.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Track_A1_CA_CrossCheck.md) | strategy |
| v3_3_track_a1_hardening_prompt | [v3.3_Track_A1_Hardening_Prompt.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Track_A1_Hardening_Prompt.md) | strategy |
| v3_3_track_a1_implementation_spec | [v3.3_Track_A1_Implementation_Spec.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Track_A1_Implementation_Spec.md) | strategy |
| v3_3_track_a1_review_consolidation_remediation | [v3.3_Track_A1_Review_Consolidation_Remediation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Track_A1_Review_Consolidation_Remediation.md) | strategy |
| v3_3_track_a2_implementation_spec | [v3.3_Track_A2_Implementation_Spec.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Track_A2_Implementation_Spec.md) | strategy |
| v3_3_track_a2_review | [v3.3_Track_A2_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Track_A2_Review.md) | review |
| v3_3_track_a3_review | [v3.3_Track_A3_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3a/v3.3_Track_A3_Review.md) | review |
| v3_3_track_b_adversarial_review | [v3.3_Track_B_Adversarial_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_Adversarial_Review.md) | review |
| v3_3_track_b_implementation_spec | [v3.3_Track_B_Implementation_Spec.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_Implementation_Spec.md) | strategy |
| v3_3_track_b_implementation_spec_v2 | [v3.3_Track_B_Implementation_Spec_v2.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_Implementation_Spec_v2.md) | strategy |
| v3_3_track_b_peer_review | [v3.3_Track_B_Peer_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_Peer_Review.md) | review |
| v3_3_track_b_pr1_review | [v3.3_Track_B_PR1_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_PR1_Review.md) | review |
| v3_3_track_b_pr2_review | [v3.3_Track_B_PR2_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_PR2_Review.md) | review |
| v3_3_track_b_pr3_review | [v3.3_Track_B_PR3_Review.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_PR3_Review.md) | review |
| v3_3_track_b_review_consolidation | [v3.3_Track_B_Review_Consolidation.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3_Track_B_Review_Consolidation.md) | review |
| v3_3b_track_b_kickoff | [v3.3b_Track_B_Kickoff.md](/Users/jonathanoh/Dev/Ontos-dev/.ontos-internal/strategy/proposals/v3.3b/v3.3b_Track_B_Kickoff.md) | strategy |


## 5. Documentation Staleness Audit
No documents use the `describes` field.
