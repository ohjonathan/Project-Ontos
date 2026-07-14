---
id: ontos_architecture
type: atom
status: active
depends_on: [ontos_manual, ontology_spec]
---

# Ontos architecture

This document orients contributors to the v5 package. It describes the current
module boundaries, command and MCP dispatch, document-to-map data flow, write
safety, extension points, tests, and generated-artifact policy.

## System shape

Ontos has two user-facing adapters over one document model:

```text
CLI arguments                         MCP tool calls
     │                                      │
     ▼                                      ▼
ontos.cli + command_registry          ontos.mcp.server
     │                                      │
     ├──────────── command orchestration ───┤
     ▼                                      ▼
configuration → scan scope → canonical document loader
                               │
                               ▼
                    DocumentData + load issues
                               │
                   ┌───────────┴───────────┐
                   ▼                       ▼
             graph + validation      immutable snapshot
                   │                       │
                   ▼                       ▼
              context map             MCP cache/tools
```

The CLI is process-per-command. The MCP server keeps a snapshot warm and
refreshes it when tracked inputs change. Both use the same configuration,
scope, parsing, graph, and validation primitives; differences belong in their
adapter contracts, not in a second document model.

## Package boundaries

| Location | Responsibility | Examples |
|---|---|---|
| `ontos/cli.py` | Parse global and command arguments, construct command options, normalize JSON/human dispatch | `create_parser`, `_cmd_map`, `_cmd_query` |
| `ontos/command_registry.py` | Declare public/hidden command names, parser builders, handlers, result kind, aliases, and nested command paths | `COMMAND_SPECS`, `command_path` |
| `ontos/commands/` | Orchestrate one CLI use case: discover root, load config, call core/I/O services, and return a typed exit | `map.py`, `rename.py`, `maintain.py` |
| `ontos/core/` | Hold the ontology, domain models, graph and validation algorithms, frontmatter edits, locking, transactions, and instruction templates shared by adapters | `ontology.py`, `graph.py`, `validation.py`, `context.py` |
| `ontos/io/` | Cross the filesystem/configuration boundary: TOML/YAML, scanning, canonical document loading, Git helpers, and snapshot assembly | `config.py`, `files.py`, `scan_scope.py`, `snapshot.py` |
| `ontos/ui/` | Render human output and the schema-4 command envelope | `output.py`, `json_output.py` |
| `ontos/mcp/` | Adapt snapshots and write orchestrators to FastMCP tools, cache state, portfolio indexing, schemas, and error boundaries | `server.py`, `cache.py`, `tools.py`, `writes.py` |
| `ontos/__main__.py` | Support `python -m ontos` | delegates to CLI `main` |

Command modules may compose I/O and core services. Reusable document or graph
behavior belongs below `commands/`; output formatting belongs in `ui/` or the
adapter. Avoid adding a parser or serializer local to one command when the
canonical loader or frontmatter-edit layer already owns that behavior.

## CLI registration and dispatch

`ontos.command_registry.COMMAND_SPECS` is the command-discovery source of
truth. Each entry names:

- the top-level command;
- its parser builder in `ontos.cli`;
- its handler;
- whether the command is public or hidden;
- whether it is diagnostic or operational; and
- nested handlers for `mcp` and `export`.

`create_parser()` iterates the registry and fails if a builder adds a different
name. After parsing, registry metadata resolves the canonical handler and
space-separated command path. The handler translates `argparse.Namespace` to a
small options dataclass in `ontos.commands`, invokes the command, and emits
either human output or one JSON envelope.

When adding or changing a command:

1. Add or update one registry entry.
2. Add parser arguments in its builder; reuse shared builders for aliases.
3. Keep the CLI handler thin and place behavior in a command module.
4. Classify the result kind and return the v5 exit taxonomy.
5. Add parser/registry assertions and focused command tests.
6. Update the Manual's command table and examples.

Do not add a raw `sys.argv` scan to recover global flags. `--json` and
`--quiet` are inherited global parser options and tokens after `--` remain
positional data.

## Configuration and scope

Project discovery starts at the current directory and walks upward. At a given
directory, `.ontos.toml` takes precedence over `.ontos`/`.ontos-internal`,
which take precedence over `.git`. Once the project root is known,
`load_project_config(repo_root=...)` reads exactly the root config or returns
typed defaults; it does not inherit an ancestor repository's configuration.

`ontos.core.config` owns the dataclass schema, defaults, type checks, path
containment, and required-version parsing. `ontos.io.config` owns discovery and
TOML I/O. Commands should consume `OntosConfig`, not reach into TOML directly.

`ontos.io.scan_scope` centralizes document roots:

- docs scope includes `[paths].docs_dir` and `[scanning].scan_paths`;
- library scope adds `.ontos-internal`;
- an explicit CLI scope overrides `[scanning].default_scope`;
- configured and command-specific skip patterns are applied together; and
- explicit directory arguments are reserved for commands that advertise them.

Commands that scan the same scope should call `collect_scoped_documents`
rather than rebuilding roots or exclusions.

## Document-to-map flow

### 1. Discover and collect

The command resolves the repository and configuration, chooses a scope, and
collects Markdown paths. Transient editor/backup candidates and configured
patterns are excluded. Map generation also excludes its output path so a prior
context map cannot become an input document.

### 2. Parse once

`ontos.io.files.load_documents` with
`ontos.io.yaml.parse_frontmatter_content` is the canonical bulk loader. It
returns `DocumentLoadResult`:

- `documents`: canonical `DocumentData` indexed by ID;
- `issues`: parse, I/O, enum, and reference-type diagnostics; and
- `duplicate_ids`: every colliding path, with deterministic canonical choice.

Commands must inspect fatal issues and duplicates before mutation. They should
not reparse frontmatter with local string splitting or silently substitute a
partial YAML parser.

### 3. Build and validate

`ontos.core.graph.build_graph` converts canonical documents to dependency
nodes/edges and classifies unresolved or external-file targets. The canonical
loader reports enum and parse problems; `ValidationOrchestrator` evaluates
links, cycles, depth, orphans, log fields, impacts, `describes`, concepts, and
configured allowlists. The combined result separates errors, warnings, and
informational findings.

Vocabulary checks that require project-level concepts are supplied by the
orchestrating command. Configuration such as `max_dependency_depth`, orphan
allowlists, and external dependency paths must be passed through rather than
replaced with adapter-local defaults.

### 4. Render and write

`ontos.commands.map.generate_context_map` renders Tier 1 orientation, graph
sections, diagnostics, and staleness information. `map_command` writes the
configured output and can synchronize an existing `AGENTS.md`. Activation uses
the same map generator and reports whether it refreshed or reused the map.

The map writer compares normalized generated content and should avoid a write
when the only change is volatile generation metadata. This keeps activation
and maintenance from dirtying a worktree without a semantic map change.

## Snapshot and MCP flow

`ontos.io.snapshot.create_snapshot` assembles an immutable
`DocumentSnapshot`: documents, graph, validation result, package version, and
optional Git commit. Export, migration analysis, and MCP consume this shared
shape.

At server startup, `ontos.mcp.server` loads project configuration, creates a
snapshot, and publishes it through `SnapshotCache`. The cache records canonical
document paths plus `(mtime_ns, size)` fingerprints and fingerprints for
path-like `describes` targets. Each normal read obtains a stable cache view;
stale inputs build a replacement state and publish it atomically. `refresh`
forces the same rebuild path.

MCP registration is capability-based:

- core read/diagnostic tools are always present;
- five write tools are omitted when `read_only=True`;
- two portfolio tools require a portfolio index; and
- `get_context_bundle` is enabled by the public `serve` path.

The server boundary converts domain and user errors to structured tool results
and preserves stable error codes. Tool implementations should not print to
stdout because stdio is the MCP transport.

Portfolio mode uses a separate user-level TOML file and SQLite index. The
primary workspace snapshot remains the source for local reads; portfolio tools
resolve explicit workspace IDs against indexed projects. Cross-workspace writes
are intentionally unsupported.

## Safe writes

All mutations are expected to fail closed before changing user files.

### Frontmatter edits

Use `ontos.core.frontmatter_edit` for surgical updates and
`ontos.core.schema.serialize_frontmatter` for complete serialization. Mutators
read UTF-8 strictly, preserve body bytes and unrelated fields where promised,
and reparse serialized frontmatter before commit. Do not use ad hoc
`split('---')`, string replacement, or a hand-built YAML serializer.

### Transaction context

`ontos.core.context.SessionContext` buffers writes, moves, and deletes. Commit:

1. binds the workspace identity;
2. validates that paths remain inside the workspace;
3. acquires or verifies the advisory workspace lock;
4. uses no-follow parent/entry checks to reject symlink or replacement races;
5. stages temporary files and scoped backups;
6. applies operations; and
7. rolls back only operations from that transaction on failure.

Creation-only workflows such as session logs use the exclusive no-follow
writer and refuse collisions rather than replacing an existing record.

### Command guards

Commands such as scaffold, retrofit, rename, and schema migration expose a
dry-run or plan before apply. Multi-file operations validate the complete input
set before buffering changes. Rename additionally requires a safe Git state and
records a durable transaction journal under `.ontos/transactions/`, allowing a
later invocation to recover only the paths touched by the interrupted rename.

### MCP writes

MCP mutations validate `read_only`, workspace identity, scope, and paths before
entering the shared transaction layer. After a successful commit they rebuild
the workspace snapshot and, in portfolio mode, the affected index row. If the
post-write rebuild fails, the write orchestrator restores the transaction and
reconverges the cache/index rather than reporting a successful stale state.

## Extension points

### Add a document type or status

Update `ontos.core.ontology.TYPE_DEFINITIONS`; `DocumentType` and
`DocumentStatus` in `ontos.core.types`; normalization/repair mappings when
appropriate; schema and generated output expectations; and the ontology docs.
Add tests for valid and invalid type/status combinations and MCP graph counts.

### Add a validation rule

Represent the finding with a stable `ValidationErrorType`/rule ID and structured
record. Add it to the shared validation or link-diagnostics pipeline, decide
severity and exit semantics, and test CLI/MCP parity. Counts must state their
basis and must not be derived from truncated presentation lists.

### Add a maintenance task

Register a `MaintainTask` with a stable name and order in
`ontos.commands.maintain`. Return a `TaskResult` with status, exit code,
details, and metrics. Update the parser's `--skip` help, the Manual, human
output tests, and JSON summary tests.

### Add an MCP tool

Put reusable behavior outside `server.py`, add input/output schemas, register
the tool in the correct capability group, and route calls through the shared
invocation boundary. Declare accurate MCP annotations and result-size metadata.
Test read-only discovery, activation warnings, error codes, and stdout safety.

### Add a config field

Add the dataclass field and default in `ontos.core.config`, extend strict type
validation, decide path/range validation and legacy behavior, thread the typed
value into every consumer, and document precedence. Test missing, valid,
malformed, unknown, and boundary values.

## Testing

Tests mirror the package boundaries:

| Test area | Primary coverage |
|---|---|
| `tests/core/` | ontology, graph, validation, frontmatter, transactions, locking |
| `tests/io/` | TOML/YAML, scanning, canonical loading, snapshots |
| `tests/commands/` | command contracts, human/JSON results, help, migrations, hooks |
| `tests/mcp/` | tool discovery, cache freshness, portfolio behavior, write safety |
| top-level `tests/test_cli*.py` | parser/dispatch integration and process boundaries |

Run the narrowest relevant tests while iterating, then the full suite:

```bash
pytest tests/commands/test_query.py
pytest tests/mcp
pytest
git diff --check
ontos doctor
ontos link-check --no-orphans --quiet
```

Tests that need a real process boundary should remain subprocess tests—for
example `python -m ontos --help`, arbitrary-CWD import behavior, and MCP stdout
safety. Parser shape, command registration, and formatted help are faster and
more deterministic in-process.

Changes to packaged files or public imports also require building wheel and
sdist artifacts, inspecting their contents and metadata, installing the wheel
non-editably in a clean environment, and smoking the CLI outside the checkout.

## Generated artifacts and conflicts

### Context map

The configured context map (normally `Ontos_Context_Map.md`) is generated by
`ontos map`. Never edit it manually. It may be marked as generated in repository
statistics because every meaningful byte is derived from documents and config.

### Instruction files

`AGENTS.md`, `.cursorrules`, and `CLAUDE.md` contain generated protocol text but
may also contain preserved `USER CUSTOM` content. Regenerate them with
`ontos agents`, `ontos export claude`, or `ontos export --all`. No-op or
timestamp-only regeneration should not create backups or rewrite the file.

Because instruction files include reviewable user content, do not classify the
entire files as disposable generated output. Preserve the custom block and
review protocol changes normally.

### Conflict policy

Regeneration is the conflict-resolution policy:

1. Resolve source documents, configuration, template changes, and intended
   `USER CUSTOM` content.
2. Remove conflict markers from the output artifact.
3. Run the owning Ontos generator.
4. Review the regenerated diff and validation output.

Do not configure a merge driver that silently selects `ours` or `theirs` for
the map or instruction files. A clean merge that hides semantic input changes
is worse than an explicit generated-file conflict.
