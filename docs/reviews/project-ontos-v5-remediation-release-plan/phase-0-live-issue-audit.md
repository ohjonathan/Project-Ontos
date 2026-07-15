---
id: project_ontos_v5_remediation_phase_0_live_issue_audit
type: review
status: complete
owner: Project Ontos Maintainers
depends_on:
  - project_ontos_v5_remediation_release_plan_proposal
concepts:
  - proposals
  - external-review
  - workflow
---

# Phase 0 Live Issue Metadata Audit

## Scope

This read-only snapshot rechecks the nine issues in the merged remediation
proposal immediately before child scaffolding. It records live state, title,
labels, milestone, and update time through authenticated GitHub reads. It does
not re-audit every issue-body checklist and performs no GitHub mutation.

Captured on 2026-07-15 UTC from `ohjonathan/Project-Ontos`.

## Snapshot

| Issue | State | Current title | Labels | Milestone | Updated (UTC) | Phase 0 observation |
|---|---|---|---|---|---|---|
| [#149](https://github.com/ohjonathan/Project-Ontos/issues/149) | open | `[P1-containing] v5.0.1 patch-safe sweep + v6.0.0 path compatibility removal` | `documentation`, `audit`, `P1-high` | `Audit Release N+1` | 2026-07-14 14:36 | Title and milestone still mix released patch work with the exact v6 deletion contract; board child remains required. |
| [#158](https://github.com/ohjonathan/Project-Ontos/issues/158) | open | `Audit remediation tracker (from PR #145)` | `audit` | `Audit Release N — hotfix` | 2026-07-14 15:45 | Tracker has not yet received the proposal-authorized successor-custody closeout. |
| [#165](https://github.com/ohjonathan/Project-Ontos/issues/165) | open | `Machine-readable audit registry and external parity gate` | `audit`, `P2-hygiene` | none | 2026-07-14 03:05 | Priority and release-blocking custody remain to be reconciled before the registry child proceeds. |
| [#173](https://github.com/ohjonathan/Project-Ontos/issues/173) | open | `[Feature] Content-addressed activation receipts and portable AGENTS/map freshness` | none | none | 2026-07-14 16:53 | Labels, milestone, dependency wording, and release custody remain Phase 0 board work. |
| [#174](https://github.com/ohjonathan/Project-Ontos/issues/174) | open | `[Feature] Stable finding IDs, Git diffing, and no-new-debt validation baselines` | none | none | 2026-07-14 16:54 | Labels, milestone, dependency wording, and release custody remain Phase 0 board work. |
| [#175](https://github.com/ohjonathan/Project-Ontos/issues/175) | open | `[Feature] Git-aware multi-agent/worktree coordination and merge-result validation` | none | none | 2026-07-14 16:54 | Labels, milestone, dependency wording, and optional-CAS custody remain Phase 0 board work. |
| [#176](https://github.com/ohjonathan/Project-Ontos/issues/176) | open | `[Bug] Bare workspace-root files bypass dependency path resolution` | none | none | 2026-07-14 16:55 | The issue remains valid and unclosed; v5.0.3 labels/milestone and the dedicated resolver child remain required. |
| [#177](https://github.com/ohjonathan/Project-Ontos/issues/177) | open | `[Feature] Semantic wikilink namespaces and path-scoped body-reference policies` | none | none | 2026-07-14 16:56 | Labels, milestone, wording correction, and dependency links remain Phase 0 board work. |
| [#178](https://github.com/ohjonathan/Project-Ontos/issues/178) | open | `[Feature] Workspace-defined document vocabularies and governed enum-repair mappings` | none | none | 2026-07-14 16:56 | The issue remains open for full v5 delivery; board wording must distinguish the v5.0.3 alias and required-version slices from complete v5.1 custody. |

## Conclusion

No tracked issue has become invalid or already closed since the merged proposal.
The board-hygiene child therefore remains current and should run before live
custody is treated as authoritative. This governance PR creates all six
authorized child proposal, tracker, and manifest triples, including board
hygiene, but performs no GitHub mutation. Later execution under the
board-hygiene child lifecycle owns all issue edits, label/milestone changes,
residual-issue creation, and #158 closeout.
