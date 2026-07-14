---
id: ontos_agent_instructions
type: kernel
status: active
depends_on: [ontos_manual]
---

# Ontos Agent Instructions

This is the executable runbook for agents working in an Ontos v5 project.
Use the repository's `AGENTS.md`, `CLAUDE.md`, or `.cursorrules` first when one
is present; those files can add project-specific instructions. The complete
human reference is the [Ontos Manual](Ontos_Manual.md).

## Runtime selection

Use the runtime selected by the repository instructions. In the absence of a
project-specific rule:

1. Prefer an executable repository runtime such as
   `./.venv/bin/python -m ontos`.
2. Otherwise use `python3 -m ontos` when the module is installed.
3. Otherwise use the `ontos` executable on `PATH`.
4. If a candidate fails or reports an incompatible version, try each remaining
   candidate once. Do not let a stale global executable shadow a working
   repository installation.

The examples below use `ontos`. Substitute the selected runtime verbatim.

## Mandatory activation

Run activation before project work:

```bash
ontos activate
```

Then:

1. Treat `usable` as a clean activation.
2. Treat `usable_with_warnings` as usable context. Read task-critical files
   directly and inspect warnings relevant to the task.
3. Stop when activation is `not_usable`; read the reported configuration,
   project-root, or document-load error instead of guessing.
4. Read the Tier 1 section of the configured context map, normally
   `Ontos_Context_Map.md`.
5. Select only the documents relevant to the request and follow their
   `depends_on` edges upward as needed.
6. Confirm the loaded IDs: `Loaded: [id1, id2]`.

Useful activation diagnostics:

```bash
ontos activate --json
ontos activate --warnings summary
ontos activate --warnings full --limit 20
ontos activate --warning-rule orphan
ontos activate --scope library
```

`--scope docs` scans the configured documentation roots. `--scope library`
also scans `.ontos-internal`. A command-line scope overrides
`[scanning].default_scope` in `.ontos.toml`.

Re-run activation after context compaction, after a large branch change, or
whenever the project structure, document count, or current context is unclear.

## MCP activation

When an MCP host exposes Ontos tools, call `activate` before any other Ontos
tool. A pre-activation read still works but includes `_ontos_warning`; treat it
as a reminder to activate, not as project context.

Use the read tools as follows:

| Tool | Use |
|---|---|
| `activate` | Establish activation state and load IDs and warnings |
| `list_validation_warnings` | Page complete warning records by rule or severity |
| `workspace_overview` | Get key documents and graph statistics |
| `context_map` | Get the rendered context narrative |
| `get_document` | Read one document by ID or path |
| `list_documents` | Browse documents by type or status |
| `export_graph` | Return a structured graph; file export requires writable mode |
| `query` | Inspect one document's dependencies and dependents |
| `health` | Inspect server, cache, and index freshness |
| `refresh` | Force a snapshot rebuild after bulk changes |
| `get_context_bundle` | Build a token-budgeted context package |

Portfolio mode adds `project_registry` and `search`. A writable server adds
`scaffold_document`, `log_session`, `session_end`, `promote_document`, and
`rename_document`. `workspace_id` is optional in a single-workspace server and
required for cross-workspace portfolio operations. A server started with
`--read-only` does not register the five write tools.

The generated `~/.config/ontos/portfolio.toml` is intentionally inert:
`scan_roots = []`, `exclude = []`, and `registry_path = ""`. Before starting a
writable portfolio server, configure at least one scan root or a registry;
Ontos refuses before creating a database otherwise. Do not substitute the
current working directory or guess a user-specific path. Read-only mode may
consume an existing database without creating config or SQLite sidecars.

Prefer MCP for structured reads when it is already configured. Use the CLI for
repository setup, health checks, maintenance, and any workflow not represented
by an MCP tool.

## Core invariants

- Never edit the generated context map manually. Run `ontos map`.
- Never hand-edit generated instruction protocol text. Put durable local rules
  inside the preserved `USER CUSTOM` block and regenerate.
- Dry-run a mutation when the command supports it. Apply only when the user has
  authorized the write.
- Read a command's error and help before changing course. Do not invent flags.
- Keep document IDs unique and stable. Use `ontos rename`, not a search-and-
  replace, when an ID must change.
- Treat parse failures, duplicate IDs, unsafe paths, and unsupported schemas as
  blockers for write operations.

## Command quick reference

Global `--json` and `--quiet`/`-q` work before or after a subcommand. Use
`ontos --help` and `ontos <command> --help` for the authoritative parser.

| Task | Command |
|---|---|
| Activate | `ontos activate` |
| Generate the map | `ontos map` |
| Generate map and sync an existing `AGENTS.md` | `ontos map --sync-agents` |
| Diagnose the project | `ontos doctor` |
| Validate all references | `ontos link-check` |
| List document IDs | `ontos query --list-ids` |
| Show a document's dependencies | `ontos query --depends-on <id>` |
| Show its dependents | `ontos query --depended-by <id>` |
| Search a concept | `ontos query --concept <tag>` |
| Find stale documents | `ontos query --stale <days>` |
| Archive the session | `ontos log --title "unique-session-title"` |
| Generate agent instructions | `ontos agents --force` |
| Generate all instruction files | `ontos export --all --force` |

Query requires an explicit selector such as `--depends-on` or `--depended-by`;
positional document IDs are unsupported.

## Initialize a project

Run inside a Git repository:

```bash
ontos init
```

Initialization writes `.ontos.toml`, creates the configured docs hierarchy and
logs directory, generates the context map and `AGENTS.md`, and offers to install
pre-commit and pre-push shims. It does not install a repository copy of Ontos.

For existing Markdown:

```bash
ontos init --scaffold
ontos init --no-scaffold
ontos init --skip-hooks
```

`--scaffold` is an explicit write to untagged files under docs scope. Use
`--force` only when overwriting an existing configuration or Ontos-managed
hooks is intentional; non-Ontos hooks are otherwise preserved.

## Map, inspect, and validate

```bash
ontos map
ontos map --strict
ontos map --compact tiered
ontos map --filter 'type:strategy'
ontos doctor --verbose
ontos doctor --frontmatter
ontos link-check --summary
ontos link-check --limit 20
```

`map` writes the configured context-map path. `--output` selects another path;
`--sync-agents` refreshes an existing `AGENTS.md`. `link-check` scans both
frontmatter and body references by default. Use `--frontmatter-only` only when
body references are intentionally out of scope, and `--no-orphans` only when
orphan findings are intentionally excluded.

## Create and curate documents

Scaffold and retrofit are dry-run-first:

```bash
ontos scaffold
ontos scaffold docs/feature.md --apply
ontos stub --goal "Describe the payment flow" --type product
ontos stub --goal "Describe the API" --type atom --output docs/atom/api.md
ontos promote --check
ontos promote docs/feature.md
ontos retrofit --obsidian
ontos retrofit --obsidian --apply
```

`stub` takes flags, not a positional output path. Use `--output` to choose the
file. `retrofit --obsidian` computes `tags` and `aliases`; it does not rename IDs
or modify document bodies.

## Rename safely

```bash
ontos rename old_id new_id
ontos rename old_id new_id --apply
```

The default is a plan. Apply requires a safe workspace state and updates the
document ID plus frontmatter and body references as one transaction. If a prior
rename was interrupted, allow Ontos to run its scoped recovery before retrying.

## End a session

Create a unique log:

```bash
ontos log --title "audit-tail-docs" --event-type chore --source "Codex"
```

Valid documented event types are `feature`, `fix`, `refactor`, `exploration`,
`chore`, `decision`, and `release`. Read the new file and complete the sections
that explain goal, decisions, alternatives, impacts, and testing. Ontos creates
logs exclusively: if the date-and-title slug already exists, choose a different
title rather than overwriting history.

On a writable MCP server, prefer `session_end` for the same structured fields.
On a read-only server, use the CLI.

Session logging has no enhancement subcommand or legacy workflow-mode preset.
Git hooks do not create or enrich session logs.

## Maintenance and consolidation

```bash
ontos maintain --dry-run
ontos maintain
ontos maintain --skip consolidate_logs
```

Maintenance orchestrates nine registered tasks: `migrate_untagged`,
`regenerate_map`, `health_check`, `curation_stats`, `promote_check`,
`consolidate_logs`, `review_proposals`, `check_links`, and `sync_agents`.
`--skip` is repeatable or comma-separated.

Run consolidation explicitly when the user intends to archive logs:

```bash
ontos consolidate --dry-run --count 20
ontos consolidate --all --count 20
ontos consolidate --dry-run --by-age --days 30
ontos consolidate --all --by-age --days 30
```

`--days` has an effect only with `--by-age`. If `--count` is omitted, count
mode uses `[workflow].log_retention_count` (normally 20); an explicit count
wins, and `--count 0` is invalid. Consolidation moves selected logs and records
them in the decision-history ledger, so review the dry run first. A missing or
recognized ledger-less decision history self-heals to the canonical
`## History Ledger` format; arbitrary malformed history still fails closed.

## Schema and re-architecture workflows

These commands have distinct purposes:

```bash
# Inspect or add explicit ontos_schema fields
ontos schema-migrate --check
ontos schema-migrate --dry-run
ontos schema-migrate --apply

# Analyze portability for a codebase re-architecture
ontos migration-report
ontos migrate --out-dir migration/
```

`schema-migrate` is the document-schema command and requires exactly one mode.
`migrate` is a convenience export: it creates `snapshot.json` and
`analysis.md`; it does not modify document schemas. Schema inspection belongs
to `schema-migrate --check`.

## Verify documentation currency

Use `describes` to associate an Ontos document with source paths, then mark it
reviewed after checking those sources:

```bash
ontos verify docs/reference/api.md
ontos verify docs/reference/api.md --date 2026-07-13
ontos verify --all
```

`verify --all` is interactive. Do not combine it with JSON automation.
`verify --portfolio` is a separate comparison of the portfolio database and
an explicitly configured `portfolio.registry_path`, optionally limited by
`--workspace-id`. It does not infer a registry path.

## MCP server and client setup

The MCP extra is required:

```bash
pip install 'ontos[mcp]'
ontos serve --workspace . --read-only
```

Managed client installation is available for Antigravity and Cursor:

```bash
ontos mcp install --client antigravity
ontos mcp install --client cursor --scope project
ontos mcp uninstall --client cursor --scope project
```

Generate, but do not write, complete configs for additional supported client
formats:

```bash
ontos mcp print-config --client claude-code
ontos mcp print-config --client codex
ontos mcp print-config --client vscode
```

Managed install, uninstall, and doctor checks are POSIX-only. On Windows, use
`print-config` and update the client manually. Generated server entries are
read-only by default; `--write-enabled` opts into write tools.

## Installation and upgrade

Install with pipx or pip, not a downloaded legacy installer:

```bash
pipx install ontos
# or
python3 -m pip install ontos
```

Upgrade the same environment that runs Ontos:

```bash
pipx upgrade ontos
# or
python3 -m pip install --upgrade ontos
```

For a pipx installation that needs MCP extras, use:

```bash
pipx install --force 'ontos[mcp]'
```

After an upgrade, restart long-lived MCP hosts so they spawn the new server,
then verify with `ontos --version`, `ontos doctor`, and `ontos map`. Existing v4
documents and `.ontos.toml` files load in v5; no one-time data conversion is
required. Automation consuming JSON must follow the v5 envelope and exit-code
contract described in the Manual.

Ontos has no CLI self-update command or downloaded-installer upgrade workflow;
upgrade the package through pipx or pip.

## Context selection

1. Start with IDs that directly match the user's request.
2. Follow `depends_on` toward foundational context.
3. Load the smallest set that resolves the task.
4. Use `docs` scope unless internal library documents are relevant.
5. Use the decision-history ledger to locate archived rationale, then read only
   the cited archive paths needed for the question.

For the authoritative ontology, statuses, and dependency rules, read
[Ontos Ontology Specification](ontology_spec.md).
