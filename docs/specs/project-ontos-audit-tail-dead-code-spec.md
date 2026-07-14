---
id: project_ontos_audit_tail_dead_code_spec
type: spec
status: active
depends_on:
  - project_ontos_audit_remediation_release_line_tracker
  - ontos_architecture
---

# Audit-tail PR B — patch-safe dead-code removal

## Goal

Resolve the nine patch-safe dead-code findings assigned to PR B on
`origin/main@d6eca479d5c5d71b2335e3ee2abad4f8d2651e3e`, while preserving every
documented or re-exported Python API. Start the v5.0.1 deprecation window for
the eleven legacy `ontos.core.paths` compatibility names; their removal stays
assigned to v6.0.0.

This branch changes package contents and therefore requires wheel/sdist and
non-editable-install verification. It does not change package metadata, merge,
tag, publish, or close issues.

## Governing public-surface rule

Internal call-count evidence is necessary but not sufficient for deletion.
Before removing a module or symbol, inspect package `__init__.py` files,
`__all__` declarations, re-exports, supported documentation, and tests. A
documented or re-exported import remains compatible and is deprecated instead
of removed. Undocumented private packages, internal shims covered by the
maintainer's explicit assumption, and unexported implementation helpers may be
deleted after a whole-tree consumer check.

The original `D5b-dead-code-3` wording counted twelve zero-call names. The
Phase 0 reconciliation established that `resolve_config` is live and supported,
leaving eleven compatibility names: `PROJECT_ROOT` plus ten functions.
`resolve_project_root` and `is_ontos_repo` are also supported.

## Finding contracts

| Finding | Intended v5.0.1 disposition | Public-surface gate |
|---|---|---|
| `D5b-dead-code-2` | Remove `ontos._templates` and its package-data rule. | Leading-underscore package; no re-export, documentation, or consumer may remain. |
| `D5b-dead-code-6` | Remove `ontos.io.obsidian` and move useful BOM coverage to the canonical loader. | `ontos.io` must not export it; supported Obsidian commands remain unrelated and working. |
| `D5b-dead-code-8` | Remove the three zero-call wrappers and two internal command-to-core re-export shims; keep live `_run_*` dispatch functions. | No removed name may appear in package exports or supported docs; explicit maintainer assumption permits removal of the undocumented shims. |
| `D5b-dead-code-9` | Remove private `init._create_directories`. | The live rollback-aware inline initialization path remains tested. |
| `D5b-dead-code-10` | Remove the six audited zero-call helpers and repoint test-only consumers. | Each helper must be absent from package exports, supported docs, and runtime consumers. |
| `D3b-structure-7` | Remove unreachable `cli._cmd_export` and its wrong-behavior test. | Parser dispatch for bare `ontos export` must still select and execute `_cmd_export_deprecated`. |
| `D7-cli-consistency-9` | Replace the obsolete v3.4 removal promise and `ontos_init.py` remediation. | Current guidance must name valid commands or explicit `Path` operations. |
| `D5a-repo-redundancy-3` | Remove `ontos._hooks` and its package-data rule. | First prove installed hooks are generated shims that call the live `ontos hook` CLI. |
| `D5a-repo-redundancy-6` | Delete exactly eleven tracked `.ontos/backups/*.bak` files. | Ignore policy remains in force and no runtime package consumer exists. |
| `D5b-dead-code-3` | Deprecate only; keep all eleven compatibility names importable and working. | Function calls emit `DeprecationWarning` naming v6.0.0 and a current replacement; importing `PROJECT_ROOT` emits no warning. |

## Compatibility and warning policy

- `PROJECT_ROOT` remains importable without an import-time warning and is
  marked deprecated in the ledger/documentation for removal in v6.0.0.
- Calls to `get_logs_dir`, `get_log_count`, `get_logs_older_than`,
  `get_archive_dir`, `get_decision_history_path`, `get_proposals_dir`,
  `get_archive_logs_dir`, `get_archive_proposals_dir`, `get_concepts_path`, and
  `find_last_session_date` emit `DeprecationWarning` with a v6.0.0 removal
  target and replacement guidance, then preserve their existing results.
- `resolve_config`, `resolve_project_root`, and `is_ontos_repo` remain supported
  and warning-free.
- Existing legacy-layout `FutureWarning` behavior remains separate from the
  public API deprecation and must not direct users to `ontos_init.py`.

## Acceptance

- A per-finding evidence matrix records the package export/re-export,
  documentation, and whole-tree consumer checks.
- Focused tests prove bare export dispatch, path warnings/imports, canonical BOM
  handling, live hook installation, and the activation/doctor warning tripwire.
- `ontos activate` has zero validation warnings; doctor adds no warnings beyond
  the baseline repository-hook and PATH-version environment warnings.
- No removed import or name remains outside immutable audit/history evidence.
- The full suite passes except for the explicitly accepted PR C WAL/SHM flake.
- Built wheel and sdist exclude `_templates`, `_hooks`, `io/obsidian.py`, and
  tracked backup files; a clean non-editable wheel install passes import and CLI
  smoke tests.
- Ontos map/link/doctor checks, llm-dev manifest and scope gates,
  `git diff --check`, and clean-worktree checks pass before publication.
