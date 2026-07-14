---
id: project_ontos_audit_tail_dead_code_tracker
type: tracker
status: active
depends_on:
  - project_ontos_audit_remediation_release_line_tracker
  - project_ontos_audit_tail_dead_code_spec
---

# Audit-tail PR B — dead-code tracker

Baseline: `origin/main@d6eca479d5c5d71b2335e3ee2abad4f8d2651e3`, the
merge of PR #167. This is the v5.0.1 patch-safe slice; release actions remain
maintainer-owned.

| Phase | Owner | Status | Artifact | Evidence | Timestamp |
|---|---|---|---|---|---|
| 0 — setup | Codex | complete | isolated `codex/audit-tail-dead-code` worktree | Ontos activation clean; `scripts/llm-dev doctor` passed | 2026-07-13 |
| A — specification | Codex | complete | `docs/specs/project-ontos-audit-tail-dead-code-spec.md` | Public-surface gate and ten finding contracts recorded | 2026-07-13 |
| B.1/B.2 — design review | external families | pending | `docs/reviews/project-ontos-audit-tail-dead-code/` | Strict lifecycle evidence awaits draft review | — |
| C — implementation | Codex | complete | package, command, helper, compatibility, and test changes | 219 focused and 1,585 full-suite tests passed; wheel/sdist inspection and clean-install smoke passed | 2026-07-13 |
| D — verification | external families | pending | `docs/reviews/project-ontos-audit-tail-dead-code/` | CI and independent verification pending | — |
| E — retrospective | Codex | pending | `docs/retros/project-ontos-audit-tail-dead-code-retro.md` | Runs after final approval | — |

## Public API and re-export gate

The `Public-path check` column records the required search across package
`__init__.py` files, `__all__`, re-exports, supported docs, and whole-tree
consumers. Immutable audit/history references are evidence, not runtime
consumers, and remain intact.

| Finding | Public-path check | v5.0.1 disposition |
|---|---|---|
| `D5b-dead-code-2` | `_templates` has no package re-export, `__all__` entry, supported-doc import, or live consumer; only the archived v2 initializer refers to it. | Remove private package and package data. |
| `D5b-dead-code-6` | `ontos.io` does not export `obsidian`; no supported doc imports it; the sole live import is its orphan test. | Remove module and move BOM coverage to `ontos.io.files.load_document`. |
| `D5b-dead-code-8` | The three audited zero-consumer wrappers appear in no package initializer, `__all__`, re-export, or supported doc. The two command shims are undocumented internal direct-import aliases explicitly classified unsupported by the maintainer. | Remove wrappers and shims; repoint tests to `ontos.core`. |
| `D5b-dead-code-9` | `_create_directories` is private, unexported, undocumented, and has no consumer. | Remove; retain rollback-aware live initialization path. |
| `D5b-dead-code-10` | None of the six helpers is exported or documented; the scanner alias is explicitly absent from `__all__`; remaining references are definitions or tests. | Remove all six and repoint/delete test-only consumers. |
| `D3b-structure-7` | `_cmd_export` is private, absent from the command registry/parser, and referenced only by the wrong-behavior test. | Remove; test registered `_cmd_export_deprecated` dispatch. |
| `D7-cli-consistency-9` | Message-only finding; no import surface. | Remove the expired v3.4 promise and replace `ontos_init.py` guidance. |
| `D5a-repo-redundancy-3` | `_hooks` is private, unexported, undocumented as an import, and unused by initialization; live generated shims invoke `ontos hook`. | Remove private package and package data. |
| `D5a-repo-redundancy-6` | Repository backups are not package API; exactly eleven tracked files violate the existing ignore rule. | Delete exactly eleven tracked `.bak` files. |
| `D5b-dead-code-3` | Ten compatibility functions are re-exported by both `ontos` and `ontos.core`; `PROJECT_ROOT` remains a direct compatibility import. `resolve_config` has package callers and is supported, correcting the audit title's count from twelve to eleven legacy names. | Retain and deprecate for v6.0.0; no import-time warning for `PROJECT_ROOT`. |

## Finding status

- [x] `D5b-dead-code-2`
- [x] `D5b-dead-code-6`
- [x] `D5b-dead-code-8`
- [x] `D5b-dead-code-9`
- [x] `D5b-dead-code-10`
- [x] `D3b-structure-7`
- [x] `D7-cli-consistency-9`
- [x] `D5a-repo-redundancy-3`
- [x] `D5a-repo-redundancy-6`
- [ ] `D5b-dead-code-3` — deprecated in v5.0.1; removal deferred to v6.0.0.

## Gate

Do not start PR C until this branch is merged and independently verified. Do
not check `D5b-dead-code-3` complete until the v6 removal lands. Tags, package
publication, issue closure, and all other release actions remain
maintainer-deferred.
