---
id: decision_history
type: strategy
status: active
depends_on: [mission]
---

# Decision History

Permanent ledger of project decisions and their archival locations.

## For Agents

1. **Search** this file to understand *why* a decision was made
2. **Retrieve** full context by reading the Archive Path if necessary (see Historical Recall in Agent Instructions)

## For Humans

Before archiving a log, record its key decision here. This ensures institutional knowledge survives consolidation.

---

## History Ledger

| Date | Slug | Event | Decision / Outcome | Impacted | Archive Path |
|:-----|:-----|:------|:-------------------|:---------|:-------------|
| 2025-12-17 | v2-6-proposals-and-tooling | feature | APPROVED: Proposals workflow with type-status matrix, rejection metadata, stale detection. | v2_strategy, schema | `.ontos-internal/strategy/v2.6/v2.6_proposals_and_tooling.md` |
| 2025-12-13 | documentation-compaction | chore | Consolidated 5 guides into single Manual. 68% markdown reduction. | schema, v2_strategy | `.ontos-internal/archive/2025-12-13_documentation-compaction.md` |
| 2025-12-12 | blocking-hook | feature | Pre-push hook blocks until session archived. Rejected advisory-only. | v2_architecture | `.ontos-internal/archive/2025-12-12_blocking-hook-implementation.md` |
| 2025-12-12 | configurable-workflow | feature | Added ENFORCE_ARCHIVE_BEFORE_PUSH and REQUIRE_SOURCE_IN_LOGS config options. | v2_architecture | `.ontos-internal/archive/2025-12-12_configurable-workflow.md` |
| 2025-12-12 | v2-implementation | feature | Completed Dual Ontology implementation (Space + Time separation). | schema, v2_strategy, mission | `.ontos-internal/archive/2025-12-12_v2-implementation-complete.md` |
| 2025-12-13 | agent-no-verify-rule | chore | Add explicit rule to Agent Instructions: agents must ask before using `git push --no-verify`. | — | `.ontos-internal/archive/logs/2025-12-13_agent-no-verify-rule.md` |
| 2025-12-13 | cleanup-broken-links | chore | Final cleanup after documentation compaction: remove legacy v1 logs, fix broken links in README.md,  | schema | `.ontos-internal/archive/logs/2025-12-13_cleanup-broken-links.md` |
| 2025-12-13 | context-map-notice | feature | Add a notice to the context map when generated in Project Ontos repo (Contributor mode) explaining t | schema | `.ontos-internal/archive/logs/2025-12-13_context-map-notice.md` |
| 2025-12-13 | documentation-compaction | chore | Compact Project Ontos documentation to reduce token overhead while preserving essential context. The | schema, v2_strategy, mission | `.ontos-internal/archive/logs/2025-12-13_documentation-compaction.md` |
| 2025-12-13 | gemini-feedback-fixes | fix | Address minor documentation gaps identified by Google Gemini review: | schema | `.ontos-internal/archive/logs/2025-12-13_gemini-feedback-fixes.md` |
| 2025-12-13 | pr-12-fixes | fix | Address code review feedback from PR #12 to unblock CI and clean up documentation structure. | — | `.ontos-internal/archive/logs/2025-12-13_pr-12-fixes.md` |
| 2025-12-13 | smart-memory-implementation | feature | Implement Ontos v2.1 "Smart Memory" system to enable indefinite project history tracking while keepi | decision_history, v2_strategy | `.ontos-internal/archive/logs/2025-12-13_smart-memory-implementation.md` |
| 2025-12-13 | v22-ux-planning | exploration | Identify and document friction points in the Ontos workflow, with focus on activation performance an | v2_strategy | `.ontos-internal/archive/logs/2025-12-13_v22-ux-planning.md` |
| 2025-12-13 | version-fix | fix | Fix incorrect version number: 2.2.0 → 2.1.0. v2.2 (Data Quality/Summaries) has not been implemented  | — | `.ontos-internal/archive/logs/2025-12-13_version-fix.md` |
| 2025-12-14 | v2-2-implementation | feature | Implement Ontos v2.2 "Data Quality" features to prepare for v3.0, including controlled vocabulary (` | common_concepts | `.ontos-internal/archive/logs/2025-12-14_v2-2-implementation.md` |
| 2025-12-14 | v2-3-1-cleanup | chore | Clean up root directory and fix migrate script to skip archive directories. | — | `.ontos-internal/archive/logs/2025-12-14_v2-3-1-cleanup.md` |
| 2025-12-14 | v2-3-curation-not-ceremony | feature | Implement Ontos v2.3 "Less Typing, More Insight" (UX improvements, new tooling, and data quality fea | ontos_manual, ontos_agent_instructions | `.ontos-internal/archive/logs/2025-12-14_v2-3-curation-not-ceremony.md` |
| 2025-12-14 | v2-4-config-design | decision | Design a two-tier configuration system for Ontos v2.4 that reduces friction for new users while pres | v2_strategy | `.ontos-internal/archive/logs/2025-12-14_v2-4-config-design.md` |
| 2025-12-15 | v2-4-config-automation | feature | (No summary captured) | — | `.ontos-internal/archive/logs/2025-12-15_v2-4-config-automation.md` |
| 2025-12-15 | v2-4-proposal-v1-4 | decision | Review fourth round of architectural feedback (Claude v4, Codex v4, Gemini v4) and finalize the v2.4 | v2_strategy | `.ontos-internal/archive/logs/2025-12-15_v2-4-proposal-v1-4.md` |
| 2025-12-16 | v2-5-promises-implementation-plan | decision | Design v2.5 "The Promises" feature: mode-based consolidation behavior with clear user promises shown | v2_strategy | `.ontos-internal/archive/logs/2025-12-16_v2-5-promises-implementation-plan.md` |
| 2025-12-17 | ci-orphan-fix | fix | (No summary captured) | — | `.ontos-internal/archive/logs/2025-12-17_ci-orphan-fix.md` |
| 2025-12-17 | ci-strict-mode-fixes | fix | (No summary captured) | v2_5_promises_implementation_plan | `.ontos-internal/archive/logs/2025-12-17_ci-strict-mode-fixes.md` |
| 2025-12-17 | pr-18-feedback-fixes | fix | (No summary captured) | — | `.ontos-internal/archive/logs/2025-12-17_pr-18-feedback-fixes.md` |
| 2025-12-17 | pr-18-staging-fix | fix | (No summary captured) | — | `.ontos-internal/archive/logs/2025-12-17_pr-18-staging-fix.md` |
| 2025-12-17 | pr-19-review-fixes | fix | (No summary captured) | — | `.ontos-internal/archive/logs/2025-12-17_pr-19-review-fixes.md` |
| 2025-12-17 | v2-5-1-proposals-architecture | decision | Design the architectural foundation for `/strategy/proposals/` - a staging area for draft strategy d | v2_strategy, ontos_manual | `.ontos-internal/archive/logs/2025-12-17_v2-5-1-proposals-architecture.md` |
| 2025-12-17 | v2-5-2-dual-mode-implementation | feature | (No summary captured) | — | `.ontos-internal/archive/logs/2025-12-17_v2-5-2-dual-mode-implementation.md` |
| 2025-12-17 | v2-5-2-shipped-cleanup | chore | Ship v2.5.2 Dual-Mode Remediation and clean up repository after release. | v2_strategy | `.ontos-internal/archive/logs/2025-12-17_v2-5-2-shipped-cleanup.md` |
| 2025-12-17 | v2-5-architectural-review | decision | Establish Claude Code (Opus 4.5) as the architect for Project Ontos v2.5, review the implementation  | v2_5_promises_implementation_plan | `.ontos-internal/archive/logs/2025-12-17_v2-5-architectural-review.md` |

---

## Consolidation Log

| Date | Sessions Reviewed | Sessions Archived | Performed By |
|:-----|:------------------|:------------------|:-------------|
| 2025-12-13 | 8 | 8 | Johnny (initial setup) |
