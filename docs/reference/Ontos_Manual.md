---
id: ontos_manual
type: kernel
status: active
depends_on: []
---

# Ontos Manual v5

Ontos is a local-first documentation graph stored as Markdown and YAML
frontmatter in a Git repository. This manual describes the v5 command line,
configuration, MCP server, and operating workflows. For a compact agent
runbook, see [Ontos Agent Instructions](Ontos_Agent_Instructions.md). For the
implementation map, see [Architecture](Architecture.md).

## 1. Install and initialize

### Requirements

- Python 3.9 or newer for the base package
- Python 3.10 or newer for the MCP extra
- Git for project discovery and write-safety checks

Install in an isolated application environment when possible:

```bash
pipx install ontos
```

Or install into the active Python environment:

```bash
python3 -m pip install ontos
```

If the `ontos` executable is not on `PATH`, every command is also available as
`python3 -m ontos ...`.

Initialize from inside a Git repository:

```bash
ontos init
```

Initialization creates the default `.ontos.toml`, documentation hierarchy,
context map, and `AGENTS.md`. It offers to install Ontos-managed pre-commit and
pre-push shims. Typical output layout is:

```text
project/
├── .ontos.toml
├── AGENTS.md
├── Ontos_Context_Map.md
└── docs/
    ├── kernel/
    ├── strategy/
    ├── product/
    ├── atom/
    ├── reference/
    ├── logs/
    └── archive/
```

Initialization flags:

| Flag | Effect |
|---|---|
| `--scaffold` | Add scaffold frontmatter to untagged files in docs scope |
| `--no-scaffold` | Skip the scaffold prompt |
| `--skip-hooks` | Do not install Git hooks |
| `--yes`, `-y` | Accept non-destructive defaults without prompts |
| `--force`, `-f` | Replace the config and Ontos-managed hooks; also permits replacing other hook files |

Scaffolding modifies existing Markdown and is never implied by noninteractive
input. Use `--scaffold` to opt in explicitly.

## 2. Document model

An Ontos document is a Markdown file with YAML frontmatter:

```yaml
---
id: payment_flow
type: product
status: active
depends_on: [product_strategy]
concepts: [payments, checkout]
---

# Payment flow
```

`id`, `type`, and `status` are the normal current-schema fields. IDs must start
and end with an alphanumeric character and may contain letters, numbers,
underscores, hyphens, and dots. Keep an ID stable after publication; use
`ontos rename` when it must change.

The core dependency hierarchy is:

| Type | Rank | May depend on |
|---|---:|---|
| `kernel` | 0 | kernel |
| `strategy` | 1 | kernel |
| `product` | 2 | kernel, strategy |
| `atom` | 3 | kernel, strategy, product, atom |
| `log` | 4 | uses `impacts` instead of `depends_on` |

Ontos also supports `reference`, `concept`, `handoff`, `tracker`, `retro`,
`review`, `spec`, `report`, `adr`, and `policy` for reference and lifecycle
artifacts. Those rank-5 types may depend on any canonical document type. See
the [Ontology Specification](ontology_spec.md) for the exact type/status matrix
and schema fields.

### Curation levels

Ontos can represent documents at three levels:

| Level | Meaning | Typical creation path |
|---|---|---|
| L0 | Machine scaffold awaiting curation | `ontos scaffold --apply` |
| L1 | Goal-bearing stub | `ontos stub ...` |
| L2 | Fully curated document | edit and `ontos promote ...` |

`ontos map` includes partially curated documents. `ontos map --strict` is the
appropriate CI form when warnings must fail the run.

### `depends_on`, `impacts`, and `describes`

- `depends_on` contains document IDs required to understand the current
  document.
- `impacts` is used on logs to name documents affected by a session.
- `describes` associates a document with source paths whose changes can make
  the document stale; `describes_verified` records the review date.

Body references in Markdown links and wikilinks also participate in link
diagnostics and ID rename.

## 3. Activation and instruction files

Start an agent session with:

```bash
ontos activate
```

Activation discovers the project, loads `.ontos.toml`, scans the effective
scope, parses documents, validates the graph, refreshes the configured context
map when usable documents are available, and returns a small set of loaded IDs.
Human output reports `usable`, `usable_with_warnings`, or `not_usable`.

```bash
ontos activate --json
ontos activate --warnings summary
ontos activate --warnings grouped
ontos activate --warnings full --limit 50
ontos activate --warning-rule broken_link
```

Grouped warnings are the default. `--warnings summary` omits samples;
`--warnings full` returns individual records and can be bounded with `--limit`.
An activation with warnings remains exit 0 when context is usable. Inspect the
result status and diagnostics instead of treating every warning as a process
failure.

Agents should read Tier 1 of the context map, select task-relevant IDs, follow
`depends_on` edges toward foundational context, and report `Loaded: [...]`.

Generate repository instruction artifacts with:

```bash
ontos agents                         # AGENTS.md
ontos agents --format cursor         # .cursorrules
ontos agents --all                   # both
ontos agents --force                 # replace generated protocol, preserve USER CUSTOM
ontos export claude --force          # CLAUDE.md
ontos export --all --force           # all three formats
ontos map --sync-agents              # map plus an existing AGENTS.md
```

The generators preserve content between `<!-- USER CUSTOM -->` and
`<!-- /USER CUSTOM -->`. Put project-specific instructions there. Regenerate
the surrounding protocol; do not maintain divergent copies by hand.

## 4. `.ontos.toml` configuration

The project configuration is `.ontos.toml` at the resolved repository root.
This is the v5 configuration surface; legacy workflow-mode presets are not
part of it.

The generated defaults are equivalent to:

```toml
[ontos]
version = "3.0"
# required_version = ">=5.0.0, <6.0.0"

[paths]
docs_dir = "docs"
logs_dir = "docs/logs"
context_map = "Ontos_Context_Map.md"

[scanning]
skip_patterns = [
  "_template.md",
  "archive/*",
  ".git/*",
  "node_modules/*",
  "__pycache__/*",
]
scan_paths = []
default_scope = "docs"

[validation]
max_dependency_depth = 5
allowed_orphan_types = ["atom", "log"]
allowed_orphan_paths = []
allowed_external_dependency_paths = []

[workflow]
log_retention_count = 20

[hooks]
pre_push = true
pre_commit = true
strict = false

[mcp]
usage_logging = false
# usage_log_path = "~/.config/ontos/usage.jsonl"
```

`[ontos].version` is the project configuration marker written by `init`; it is
not the installed package version. Optional `required_version` constrains the
runtime used by activation, doctor, and MCP activation. Supported forms include
comma-separated comparisons (`>=5.0.0, <6.0.0`), tilde ranges (`~5.0`), and
wildcards (`5.x` or `5.0.*`).

All `[paths]` values must resolve inside the repository. `scan_paths` adds
workspace-relative roots to both scopes. Library scope adds
`.ontos-internal`; it does not replace the configured docs and scan roots.

`allowed_orphan_paths` and `allowed_external_dependency_paths` use
workspace-relative glob patterns. An allowed external dependency is reported
as informational rather than as a broken link.

### Configuration validation and precedence

Root discovery walks upward from the current directory. At each directory it
checks `.ontos.toml`, then `.ontos`/`.ontos-internal`, then `.git`. Once a root
is selected, project commands load exactly `<root>/.ontos.toml`; a missing file
uses defaults and does not inherit an ancestor repository's config.

Precedence for a supported command option is:

1. Explicit command-line option, such as `--scope`, `map --output`, or
   `schema-migrate --dirs`
2. The corresponding `.ontos.toml` value
3. The built-in default

Unknown top-level sections, unknown keys, wrong value types, unsafe paths, and
malformed `required_version` expressions are errors. Legacy
`validation.strict` is normalized to `hooks.strict`; the top-level legacy
`[project]` section is ignored for compatibility. Negative dependency depth is
clamped to zero and log retention below one is clamped to one.

Legacy Python configuration files are compatibility inputs, not the current
public configuration interface. New and upgraded projects should use
`.ontos.toml`.

## 5. Command-line reference

The authoritative command list is `ontos --help`. `--json` and
`--quiet`/`-q` may appear before or after a subcommand. The version flag is a
top-level query used without a subcommand:

| Option | Meaning |
|---|---|
| `--version`, `-V` | Print the package version |
| `--json` | Emit one schema-4 JSON envelope |
| `--quiet`, `-q` | Suppress nonessential human output |

Place literal positional tokens after `--`; they are not reinterpreted as
global options.

### Public commands

| Command | Purpose | Important options |
|---|---|---|
| `activate` | Best-effort agent activation | `--warnings`, `--warning-rule`, `--limit`, `--scope` |
| `init` | Initialize a Git repository for Ontos | `--force`, `--skip-hooks`, `--yes`, `--scaffold`, `--no-scaffold` |
| `map` | Generate the context map | `--strict`, `--output`, `--compact`, `--filter`, `--sync-agents`, `--scope` |
| `log` | Create an end-of-session log | `--title`, `--event-type`, `--source`, `--auto` |
| `doctor` | Run configuration and health diagnostics | `--verbose`, `--frontmatter`, `--scope` |
| `maintain` | Run the maintenance task registry | `--dry-run`, `--skip`, `--fix-frontmatter-enums`, `--apply`, `--scope` |
| `link-check` | Diagnose frontmatter and body references, duplicates, and orphans | `--summary`, `--limit`, `--frontmatter-only`, `--no-orphans`, `--scope` |
| `rename` | Plan/apply an atomic document-ID rename | `old_id new_id`, `--apply`, `--scope` |
| `retrofit` | Plan/apply computed Obsidian tags and aliases | `--obsidian`, `--apply`, `--scope` |
| `env` | Detect environment manifests | `--write`, `--force`, `--format` |
| `mcp` | Manage client configuration | `install`, `uninstall`, `print-config` |
| `serve` | Start the stdio MCP server | `--workspace`, `--portfolio`, `--read-only` |
| `agents` | Generate `AGENTS.md` and/or `.cursorrules` | `--force`, `--format`, `--all`, `--output`, `--scope` |
| `export` | Export data or instruction artifacts | `data`, `claude`, or bare `--all` |
| `verify` | Update `describes_verified` or verify portfolio parity | path, `--all`, `--date`, `--portfolio`, `--workspace-id`, `--scope` |
| `query` | Query the document graph | one of `--depends-on`, `--depended-by`, `--concept`, `--stale`, `--health`, `--list-ids` |
| `schema-migrate` | Inspect or add explicit document schema versions | exactly one of `--check`, `--dry-run`, `--apply` |
| `consolidate` | Archive old logs into decision history | `--count`, `--by-age`, `--days`, `--dry-run`, `--all` |
| `promote` | Inspect or promote curation level | files, `--check`, `--all-ready`, `--yes`, `--scope` |
| `scaffold` | Add frontmatter to untagged Markdown | paths, `--apply`, `--dry-run`, `--scope` |
| `stub` | Create a goal-bearing document stub | `--goal`, `--type`, `--id`, `--output`, `--depends-on` |
| `migration-report` | Classify documents for re-architecture | `--output`, `--format`, `--force`, `--scope` |
| `migrate` | Generate `snapshot.json` and `analysis.md` | `--out-dir`, `--force`, `--scope` |

`query` has no positional-ID form. For example:

```bash
ontos query --depends-on payment_flow
ontos query --depended-by product_strategy
ontos query --concept payments
ontos query --stale 30
ontos query --health
ontos query --list-ids
```

`migrate` and `schema-migrate` are different commands. Schema inspection uses
`ontos schema-migrate --check`.

Hidden `tree`, `validate`, and `agent-export` aliases exist only for transition
compatibility. `hook` is an internal Git-hook entry point. Do not build new
workflows on those names.

### Nested MCP client commands

```bash
ontos mcp install --client antigravity
ontos mcp install --client cursor --scope project
ontos mcp uninstall --client cursor --scope project
ontos mcp print-config --client codex
```

`install` and `uninstall` manage Antigravity and Cursor. `print-config` also
renders Claude Code, Codex, and VS Code formats. Managed server entries are
read-only unless `--write-enabled` is present.

### Export commands

```bash
ontos export data --output graph.json
ontos export data --type strategy,product --no-content
ontos export data --deterministic --json
ontos export claude --force
ontos export --all --force
```

Bare `export` without `--all` is a deprecated route to Claude instruction
export. Use an explicit subcommand or `--all`.

## 6. Operating workflows

### Build and validate the map

```bash
ontos map
ontos map --strict
ontos map --compact basic
ontos map --compact rich
ontos map --compact tiered
ontos map --filter 'type:strategy'
ontos map --scope library
```

The map command scans the effective roots, excludes configured patterns and its
own output path, parses documents through the canonical loader, builds the
dependency graph, runs validation, and writes the configured context map.
`--no-cache` bypasses the document cache for debugging. `--obsidian` emits
wikilink-compatible references.

Use `doctor` for broad installation/configuration health and `link-check` for
the complete reference scan:

```bash
ontos doctor --verbose
ontos doctor --frontmatter
ontos link-check
ontos link-check --summary
ontos link-check --no-suggestions
```

`link-check` scans frontmatter and body references by default. Its summary
counts remain complete when finding lists are limited. `--frontmatter-only`
and `--no-orphans` intentionally narrow the basis and should not be used for a
full CI gate.

### Archive a session

```bash
ontos log --title "unique-session-title"
ontos log --event-type feature --title "payment-flow" --source "Ada"
```

The log path comes from `[paths].logs_dir`. Creation is exclusive: a duplicate
date-and-title slug is refused instead of appended or overwritten. Complete the
new log's Goal or Summary, decisions, alternatives, impacts, and testing before
committing it.

There is no log-enhancement workflow, hook-generated log mode, or legacy
workflow-mode preset.

### Scaffold, stub, promote, and retrofit

```bash
ontos scaffold                         # dry-run
ontos scaffold docs/product --apply
ontos stub --goal "Define checkout" --type product
ontos stub --goal "Define API" --type atom --output docs/atom/api.md
ontos promote --check
ontos promote docs/product/checkout.md
ontos retrofit --obsidian              # dry-run
ontos retrofit --obsidian --apply
```

Scaffold and retrofit are dry-run-first. Retrofit performs surgical updates to
computed `tags` and `aliases` fields while preserving other frontmatter.

### Rename a document ID

```bash
ontos rename old_id new_id
ontos rename old_id new_id --apply
```

The plan covers the defining frontmatter plus frontmatter and body references.
Apply uses the workspace lock, safe transaction writes, and a durable recovery
journal under `.ontos/transactions/`. It refuses unsafe or ambiguous state
rather than applying a partial rename.

### Track source staleness

```yaml
---
id: cli_reference
type: atom
status: active
describes: [ontos/cli.py]
describes_verified: 2026-07-13
---
```

After reviewing the described source:

```bash
ontos verify docs/reference/cli.md
ontos verify docs/reference/cli.md --date 2026-07-13
ontos verify --all
```

`verify --all` is interactive and is not available as a non-interactive JSON
write.

### Maintain the repository

```bash
ontos maintain --dry-run
ontos maintain
ontos maintain --verbose
ontos maintain --skip consolidate_logs,review_proposals
```

The registered tasks, in order, are:

1. `migrate_untagged`
2. `regenerate_map`
3. `health_check`
4. `curation_stats`
5. `promote_check`
6. `consolidate_logs`
7. `review_proposals`
8. `check_links`
9. `sync_agents`

`AUTO_CONSOLIDATE=0` disables the consolidation task for a run; without that
override it is enabled. Maintenance passes
`[workflow].log_retention_count` to consolidation.

For conservative lifecycle enum repair:

```bash
ontos doctor --frontmatter
ontos maintain --fix-frontmatter-enums --dry-run
ontos maintain --fix-frontmatter-enums --apply
```

Apply requires a safe Git state and preserves recognized original values in
`original_type` or `original_status` when appropriate.

### Consolidate logs

Count mode and age mode are explicit alternatives:

```bash
# Keep the newest 20 logs
ontos consolidate --dry-run --count 20
ontos consolidate --all --count 20

# Archive logs older than 30 days
ontos consolidate --dry-run --by-age --days 30
ontos consolidate --all --by-age --days 30
```

In v5.0.0, direct count mode defaults to keeping 15 logs, while maintenance
passes the configured retention default of 20. `--days` is ignored unless
`--by-age` is also present. Consolidation updates the decision-history ledger
and moves each selected log transactionally; inspect the dry run first.

### Migrate document schemas

```bash
ontos schema-migrate --check
ontos schema-migrate --dry-run
ontos schema-migrate --apply
ontos schema-migrate --check --dirs docs/product docs/atom
```

Exactly one mode is required. Check reports documents without an explicit
supported `ontos_schema`; dry-run previews additions; apply patches only that
frontmatter field. Unsupported schemas block apply so a batch is not partially
migrated.

### Prepare for a codebase re-architecture

```bash
ontos migration-report --format md
ontos migration-report --format json --output analysis.json
ontos migrate --out-dir migration/
```

`migration-report` classifies portable documents, documents needing review,
and implementation-specific atoms. `migrate` combines a full structured export
and Markdown analysis; it does not mutate source documents.

### Detect the development environment

```bash
ontos env
ontos env --format json
ontos env --write
ontos env --write --force
```

The command recognizes common Python, Node, version-manager, container, and
build manifests and can write `.ontos/environment.md`.

## 7. MCP server

Install the extra:

```bash
pipx install 'ontos[mcp]'
# or
python3 -m pip install 'ontos[mcp]'
```

Start a stdio server:

```bash
ontos serve
ontos serve --workspace /path/to/project
ontos serve --workspace /path/to/project --read-only
ontos serve --workspace /path/to/project --portfolio --read-only
```

The direct CLI default is writable. Managed client configs generated by Ontos
are read-only by default. Use `--write-enabled` at client-config generation
time only when the five write tools are intended.

The server keeps one canonical snapshot in memory. It checks file path, mtime,
and size fingerprints on tool calls and rebuilds when tracked documents or
`describes` targets change. Use `refresh` after bulk changes when an immediate
forced rebuild is useful.

### Tools

Every server exposes these core read/diagnostic tools:

| Tool | Purpose |
|---|---|
| `activate` | Establish session activation and return loaded IDs |
| `list_validation_warnings` | Page complete warning records |
| `workspace_overview` | Summarize documents and graph health |
| `context_map` | Render full or compact map context |
| `get_document` | Read by ID or path |
| `list_documents` | Filter and page canonical documents |
| `export_graph` | Return graph data; persistent export requires writable mode |
| `query` | Inspect one document's graph neighborhood |
| `health` | Report server and cache state |
| `refresh` | Force a snapshot rebuild |
| `get_context_bundle` | Assemble a token-budgeted workspace bundle |

Without `--read-only`, the server also registers:

| Tool | Purpose |
|---|---|
| `scaffold_document` | Create a scaffolded Markdown document |
| `log_session` | Create a dated session log |
| `session_end` | Create a structured session-end log |
| `promote_document` | Change `curation_level` |
| `rename_document` | Rename an ID and all references |

`read_only=True` omits those five write tools. `workspace_id` defaults to the
served workspace in single-workspace mode. Portfolio cross-workspace reads
require a valid workspace ID; rename always uses library scope.

Portfolio mode adds `project_registry` and `search`, for a maximum of 18 tools
on a writable portfolio server.

### Client onboarding

Ontos has three support tiers:

- **First-class**: Antigravity and Cursor have managed install/uninstall and
  doctor coverage.
- **Print-config only**: Claude Code, Codex, and VS Code receive complete
  generated config documents but no managed write.
- **Docs-only**: Claude Desktop and Windsurf use their documented native setup.

Antigravity's native config is
`~/.gemini/antigravity/mcp_config.json`:

```bash
ontos mcp install --client antigravity
```

Cursor uses `.cursor/mcp.json` for project scope and `~/.cursor/mcp.json` for
user scope:

```bash
ontos mcp install --client cursor --scope project
ontos mcp install --client cursor --scope user
ontos mcp uninstall --client cursor --scope project
```

Rerunning `ontos mcp install ...` refreshes the resolved Ontos launcher path.
Managed install, uninstall, and doctor integration are POSIX-only. On Windows,
use `print-config` and update the client manually:

```bash
ontos mcp print-config --client codex
ontos mcp print-config --client claude-code
ontos mcp print-config --client vscode
```

A generic client document contains an `"mcpServers"` entry similar to:

```json
{
  "mcpServers": {
    "ontos": {
      "command": "ontos",
      "args": ["serve", "--workspace", "/path/to/project", "--read-only"]
    }
  }
}
```

### Portfolio configuration

Portfolio settings are separate from `.ontos.toml` and live at
`~/.config/ontos/portfolio.toml`. In v5.0.0 a writable portfolio server creates
this file when absent and opens `~/.config/ontos/portfolio.db`; a read-only
portfolio server requires an existing config and database and does not create
WAL/SHM sidecars.

The v5.0.0 generated portfolio defaults are:

```toml
[portfolio]
scan_roots = ["~/Dev"]
exclude = ["~/Dev/.dev-hub", "~/Dev/archive"]
registry_path = "~/Dev/.dev-hub/registry/projects.json"

[bundle]
token_budget = 8000
max_logs = 20
log_window_days = 30
```

Review and replace those paths for the actual machine before relying on
portfolio results. `verify --portfolio` compares the database to the configured
registry; `--workspace-id` limits the comparison.

### Usage logging

Project `.ontos.toml` controls MCP usage logs:

```toml
[mcp]
usage_logging = true
usage_log_path = "~/.config/ontos/usage.jsonl"
```

Usage logging is disabled by default and records tool names and timestamps, not
document content. Read-only mode does not write usage logs.

### MCP limitations

- stdio transport only
- one primary workspace per server process
- no cross-workspace writes
- Python 3.10 or newer

## 8. Git hooks

`ontos init` can install executable shims in the repository's effective Git
hooks directory. Each shim tries `ontos hook <type>` on `PATH`, then the hook's
Python interpreter with `-m ontos`, and finally warns and permits the Git
operation if no runtime is available.

Configure them with:

```toml
[hooks]
pre_push = true
pre_commit = true
strict = false
```

The pre-push check verifies that the configured context map exists and starts
with frontmatter. With `strict = false`, findings warn and the push proceeds;
with `strict = true`, those findings block. Runtime/configuration errors remain
fail-open in normal Git-hook mode so Ontos cannot strand repository work.

The packaged pre-commit hook currently checks configuration/enablement and does
not run the full map or link validator. Use explicit CI or a project-owned
pre-commit entry for strict graph validation:

```yaml
repos:
  - repo: local
    hooks:
      - id: ontos-map
        name: Ontos map validation
        entry: ontos map --strict --quiet
        language: system
        pass_filenames: false
```

Existing non-Ontos hooks are preserved unless `ontos init --force` is used.
Prefer manual integration when a repository already has hook orchestration.

## 9. JSON and exit codes

Ontos v5 emits JSON envelope schema `4.0`. The top-level `status` reports
whether execution succeeded; `result.status` reports domain quality such as
`clean`, `findings`, `warnings`, or `incomplete`; the command-specific payload
is under `data`.

```json
{
  "schema_version": "4.0",
  "command": "link-check",
  "status": "success",
  "exit_code": 1,
  "message": "broken references found",
  "result": {
    "status": "findings",
    "kind": "diagnostic",
    "exit_category": "findings",
    "diagnostics": {}
  },
  "data": {},
  "warnings": [],
  "error": null
}
```

Nested command names are canonical space-separated paths such as
`mcp install`, `export data`, and `export claude`.

| Exit | Category | Meaning |
|---:|---|---|
| 0 | clean | Completed; also used by warning-only activation and doctor |
| 1 | findings | Completed diagnostic findings require attention |
| 2 | usage | Invalid input, missing project/config, or refused operation |
| 3 | warnings | Completed warning result, including orphan-only link-check |
| 4 | reserved | Do not use |
| 5 | internal | Unexpected execution or I/O failure |
| 130 | interrupted | Operator or signal interruption |

Codes 1 and 3 can still have top-level `status: "success"` because the command
completed and reported a diagnostic outcome. Automation should branch on both
execution status and `result`, not on nonzero alone. JSON mode does not prompt
and writes exactly one envelope to stdout.

## 10. Upgrade to and within v5

Upgrade the environment that supplies the executable:

```bash
pipx upgrade ontos
# or
python3 -m pip install --upgrade ontos
```

For pipx plus MCP extras:

```bash
pipx install --force 'ontos[mcp]'
```

Ontos has no CLI self-update command and no supported downloaded-installer
upgrade path; use pipx or pip.

Existing v4 documents and `.ontos.toml` files load in v5. Regenerate the map;
there is no one-time data conversion:

```bash
ontos --version
ontos doctor
ontos map
```

The breaking v5 changes are integrations, not repository data: JSON envelope
4.0, the exit-code taxonomy, canonical nested command paths, physical body-link
line numbers, an open-map MCP `graph_stats.by_type`, and scoped durable rename
recovery. See [the v5.0.0 migration guide](../releases/v5.0.0.md) before
upgrading automation.

Long-lived MCP hosts keep their child process alive across package upgrades.
Restart the MCP host or reload its plugin, then check `ontos --version` in a new
CLI process. A stale running MCP process will continue to report its old server
version until restarted.

## 11. Safety and troubleshooting

### Dry-run-first commands

Use the preview before applying:

```bash
ontos scaffold --dry-run
ontos retrofit --obsidian
ontos rename old_id new_id
ontos schema-migrate --dry-run
ontos consolidate --dry-run --count 20
```

### Common failures

| Symptom | Action |
|---|---|
| No Ontos project found | Change into the intended Git repository or run `ontos init` |
| Malformed `.ontos.toml` | Fix the reported section/key/type; Ontos does not silently ignore malformed TOML |
| Incompatible required version | Use a runtime satisfying `[ontos].required_version` |
| Duplicate ID | Rename or remove the duplicate before mutation |
| Broken reference | Correct the ID or intentional external-file allowlist |
| Orphan-only link-check exit 3 | Connect or allow the document, or intentionally use `--no-orphans` |
| Context map missing frontmatter | Regenerate with `ontos map` |
| Instruction file conflict | Preserve `USER CUSTOM`, resolve source changes, and regenerate |
| MCP reports an old version | Restart the MCP host |

### Generated artifacts

`Ontos_Context_Map.md` is generated state and should be regenerated with
`ontos map`, never hand-edited. `AGENTS.md`, `.cursorrules`, and `CLAUDE.md`
combine generated protocol text with preserved user content; regenerate them
with their Ontos commands. Resolve merge conflicts by preserving intended
inputs and `USER CUSTOM` content, then regenerating. Do not install merge
drivers that silently choose one generated side.

The repository may classify only the context map as a generated file for code
review statistics because instruction files contain reviewable user-owned
content. Timestamp-only or otherwise content-neutral regeneration should not
produce committed churn.
