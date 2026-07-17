# Changelog

All notable changes to this project will be documented in this file.

> For the full historical changelog with Ontos frontmatter (from v0.1.0), see [`Ontos_CHANGELOG.md`](Ontos_CHANGELOG.md).

## [Unreleased]

Issue-review remediation slices from the 2026-07-16 GitHub issues review
(`docs/specs/project-ontos-github-issues-review-2026-07-proposal.md`).

### Fixed

- **Bare workspace-root dependency resolution (#176)** — a `depends_on`
  entry such as `pyproject.toml` (no separator, no `.md` suffix) now
  resolves through a strict regular-file probe instead of bypassing
  filesystem resolution and reporting a hard broken link. Bare and `./`
  spellings classify identically; a bare token matching a directory stays a
  broken link; ambiguous workspace-root vs declaring-doc candidates fail
  closed. Behavior note: existing corpora with allowlisted bare root-file
  dependencies will see `broken_link` errors become
  `external_file_dependency`/`out_of_scope_dependency` records, which can
  change doctor/activation exit codes (in the fixed direction).
- **Nested archive layouts now excluded from scans (#181)** — skip patterns
  such as the default `archive/*` previously matched only direct children,
  so the nested `docs/archive/logs/…` layout that `ontos consolidate`
  itself writes (and nested markdown under `node_modules/`) was scanned
  back into the live graph. Directory patterns now exclude the whole
  subtree. Behavior note: repositories with nested archive layouts will
  correctly report lower document counts; library scope now excludes
  `.ontos-internal/archive/` like every other scope.
- **AGENTS.md ownership guard and content-based staleness (#173)** —
  `ontos maintain` and `ontos map --sync-agents` no longer force-overwrite
  an AGENTS.md that Ontos did not generate; non-Ontos files are reported by
  ownership (`user_managed`/`managed_block`) with an explicit
  `ontos agents --force` adoption path. Staleness for Ontos-owned files is
  decided by semantic content comparison instead of mtimes, so clones,
  worktrees, and touch-only changes no longer flip freshness verdicts, and
  the `touch_on_unchanged` mtime hack is retired.

### Added

- **Workspace enum-repair aliases (#178)** — new optional
  `[frontmatter.aliases.type]` / `[frontmatter.aliases.status]` tables in
  `.ontos.toml` declare explicit project mappings for
  `maintain --fix-frontmatter-enums` and `doctor --frontmatter`.
  Validation is fail-closed (targets must be canonical and never
  `unknown`; keys must not be canonical; case-normalized duplicates
  rejected) and repair edits report their mapping `source`
  (`built-in`/`config`). Projects adopting the new section should pin
  `[ontos].required_version` so older installations fail with a version
  message instead of an unknown-section config error.
- **Built-in `in-progress` → `in_progress` repair alias (#178)** — the
  canonical status existed but its most common agent-emitted spelling had
  no repair mapping.

## [5.0.2] - 2026-07-14

Patch release hardening the exact-artifact gate against TestPyPI propagation
lag and completing the inherited #148 test-hygiene tail.

### Fixed

- **Bounded TestPyPI Simple-API polling** — the hash-locked wheel download now
  retries only when pip reports that the exact manifest version is not yet
  available. Retries are bounded to 12 attempts with a 10-second interval.
  Hash mismatches, unexpected pip failures, and downloaded-wheel provenance
  mismatches remain immediate fail-closed errors.

### Changed

- **CLI help tests** — command help coverage now walks the declarative parser
  and registry recursively in-process, with selected `format_help()` golden
  comparisons. Only genuine process-boundary tests remain subprocess-based.
- **Pytest configuration** — removed the registered but unconsumed `legacy`
  marker.

## [5.0.1] - 2026-07-14

Release candidate completing the patch-safe audit-remediation code sweep.
Release tags, package publication, and other release actions remain
maintainer-owned.

### Changed

- **Neutral portfolio defaults (behavioral)** — newly generated
  `~/.config/ontos/portfolio.toml` files now start with empty `scan_roots`,
  `exclude`, and `registry_path` values. Hand-edited configs that omit those
  keys also receive empty values instead of inheriting the former
  machine-specific layout. A writable portfolio server refuses to create its
  database until at least one scan root or a registry is configured;
  read-only mode may still open an existing database without creating config
  or SQLite sidecars. `verify --portfolio` now requires an explicit registry.
- **Consolidation retention** — omitted `consolidate --count` now uses
  `[workflow].log_retention_count` (normally 20), matching `maintain`.
  An explicit `--count` still wins, `--count 0` still exits with usage code 2,
  and age mode remains independent.
- **Bundle defaults** — the existing 8,000-token, 20-log, and 30-day context
  bundle defaults now come from shared named constants. Their values and
  generated TOML bytes are unchanged.

### Fixed

- **Decision-history recovery** — consolidation initializes a missing
  decision history and appends one canonical `## History Ledger` section to a
  recognized generated/narrative history that lacks it. Repeated writes are
  idempotent; arbitrary or malformed history files still fail closed without
  moving logs. The scaffold template now uses the same six-column ledger.
- **Release provenance** — the tag workflow builds one immutable wheel/sdist
  bundle with a tag-, version-, source-, size-, kind-, filename-, and
  SHA-256-bound manifest. TestPyPI verification checks the exact published
  file set and hashes, downloads `ontos==<tag version>` from TestPyPI only
  under `--require-hashes`, installs the verified wheel with `--no-deps`, and
  asserts package and metadata versions outside the checkout. An occupied
  TestPyPI version now fails closed; production publication remains gated on
  successful exact-artifact verification.

### Compatibility notes

- The portfolio default change is intentionally inert: configure discovery
  explicitly before the first writable portfolio run. Existing configured
  portfolio files and databases are not rewritten or deleted.
- The command surface, schema-4 envelope, and exit-code taxonomy remain v5
  compatible. The deprecated v2 path aliases remain importable in 5.0.1;
  their planned removal remains a v6.0.0 change.

## [4.7.1] - 2026-07-12

Patch release stopping active frontmatter corruption and hardening local
write paths without changing the command-envelope schema or exit-code
taxonomy.

### Fixed

- **Safe frontmatter serialization (#146)** — all serializer-backed document
  writers now use PyYAML-safe scalar quoting, preserve field order, and verify
  semantic round trips before committing. Date-like IDs, quoted text,
  comma-bearing list items, hash-leading values, multiline strings, and
  Unicode no longer change type or corrupt YAML.
- **Format-preserving mutations** — promote, migrate, verify, retrofit,
  frontmatter repair, rename scalar emission, and MCP write tools preserve
  comments, BOMs, line endings, quoting outside changed fields, and document
  bodies while reparsing changed frontmatter before commit.
- **Secure transactional writes** — temporary files are unpredictable and
  exclusive; symlinks, hard links, path swaps, duplicate pending
  destinations, and paths outside the workspace fail closed. Existing file
  modes and the process umask are respected, and commits use durable atomic
  replacement with rollback.
- **Cross-platform locking** — the base package no longer depends on an
  unconditional `fcntl` import. CLI and MCP mutations share a bound
  workspace-lock abstraction and reject lock-file or workspace identity
  changes.
- **Session logs** — logs use the configured `logs_dir`, safe YAML
  serialization, and exclusive creation. A same-day slug collision returns an
  existing `E_FILE_EXISTS` error instead of overwriting the earlier log.
  Legacy project-local `ontos_config.py` `LOGS_DIR` keeps precedence; when no
  legacy override exists, `[paths].logs_dir` is honored. Existing logs are not
  moved automatically. Keep a custom directory inside the configured scan
  scope if its logs should appear in maps and queries.
- **Doctor command execution (#147)** — repository-controlled Cursor MCP
  configuration is inspected without executing an arbitrary configured
  command; managed Ontos launchers continue to receive the initialize probe.
- **Read-only MCP** — persistent graph export, usage-log writes, portfolio
  initialization, and SQLite sidecars are suppressed in read-only mode.

### Compatibility notes

- The standard command envelope remains schema version **3.4**; no v4.0
  `result` object or new exit-code taxonomy is included.
- Invalid UTF-8 remains replacement-decoded on general read-only loading for
  patch compatibility. Every mutation path decodes strictly and refuses to
  rewrite malformed input with existing `E_COMMAND_FAILED` semantics, the
  affected path in the message, and a UTF-8 recovery step. Commands retain
  their established local exit/envelope routing; cross-command unification is
  deferred to v5.0.0 with broad loader rejection.
- Filename-derived fallback IDs remain verbatim for compatibility. Only an
  explicit `id:` is required to be a string matching the documented grammar.
- Public exception fields retain their immutable/hashable behavior while
  permitting `BaseException` runtime metadata on supported Python versions,
  including Python 3.14, so context-manager propagation no longer masks the
  original domain error.
- The central transaction and serializer-backed mutation paths changed in this
  hotfix. Validate high-value bulk mutations in a scratch clone before release
  rollout, especially on unusual network or linked filesystem layouts.
- Generated-map timestamp behavior, CLI flag semantics, graph/link output,
  MCP `graph_stats.by_type`, and the accepted stub type set are unchanged.

## [4.7.0] - 2026-06-11

Minor release closing Issues #131–#136 — the "Ontos feels unstable" RCA
batch. Health/diagnostic surfaces are now bounded, mutually consistent,
and fast on medium repos.

### Added
- **Warning grouping (#132)** — `ontos activate` returns grouped warning
  summaries by default: `data.validation.warning_groups` (rule_id, count,
  by_severity, ≤3 full-record samples), `warnings_total`, and
  `warnings_truncated`. New flags `--warnings {summary,grouped,full}`,
  `--warning-rule RULE_ID`, `--limit N`. The MCP `activate` tool gains a
  `warnings: summary|grouped` parameter, and the new paginated
  **`list_validation_warnings`** MCP tool (rule_id/severity/offset/limit)
  pages complete records.
- **External file dependencies (#134)** — New
  `[validation] allowed_external_dependency_paths` config (workspace-relative
  globs). A `depends_on` target that exists on disk and matches the allowlist
  is classified `external_file_dependency` at **info** severity (new
  `validation.info` / `info_groups` surfaces; never flips
  `usable_with_warnings`). link-check re-buckets all resolved-on-disk deps
  into `data.file_dependencies` with `summary.file_dependencies` /
  `summary.unallowlisted_file_dependencies` counters.
- **link-check output controls (#135)** — `--summary`, `--limit N`,
  `--no-suggestions`, `--frontmatter-only`, `--no-orphans`; per-phase
  `data.timings_ms`; stderr stage markers on human runs;
  `findings_truncated` + `truncated_sections` indicators.
- **Map provenance (#136)** — Context map frontmatter gains
  `generator_version`, `scope`, and `documents_loaded`; the banner reports
  the installed package version. `ontos doctor` warns when the map's
  generator version is missing or doesn't match the installed CLI.
- **Health basis labels (#133)** — `query --health` reports
  `count_basis`/`orphan_basis`/`connectivity_basis` and echoes
  `allowed_orphan_types`; doctor checks carry a structured `data` block
  with their `count_basis`.

### Changed
- **link-check JSON envelope (#131, breaking)** — `ontos link-check --json`
  now emits the standard command envelope; the legacy root-level payload is
  gone. Top-level `status` is transport status; result quality lives in
  `data.result_status` (`clean|warnings|failing`). **Shell exit codes 0/1/2
  are unchanged** — exit-code-based CI needs no migration. JSON consumers:
  `.summary` → `.data.summary`, `.broken_references` →
  `.data.broken_references`, legacy root `.status` → `.data.result_status`.
  Detect the new shape via top-level `schema_version` (now **3.4** for all
  commands).
- **Activate default output (#132, behavioral)** — `data.validation.warnings`
  is `[]` unless `--warnings full`; consumers should check
  `warnings_truncated`/`warnings_total`. `validation.errors` is always the
  complete list, and status/exit semantics derive from full counts —
  CI keyed on hard errors sees no change.
- **link-check re-bucketing (#134, behavioral)** — resolved-on-disk
  `depends_on` targets no longer count as `broken_references` /
  `broken_frontmatter`; they appear under `file_dependencies` with an
  `allowlisted` flag. Exit-1 semantics are preserved for unconfigured repos
  via `unallowlisted_file_dependencies`; CI parsing broken counters should
  read the new fields.
- **`query --health` orphan counts (#133, bugfix)** — orphan detection now
  uses the same `detect_orphans` + configured `allowed_orphan_types`/
  `allowed_orphan_paths` as activate/link-check (previously a hard-coded
  type list produced contradictory counts). Connectivity reports `null` +
  `connectivity_basis: not_applicable_no_kernel_docs` when no kernel docs
  exist instead of a misleading `0.0`.
- **doctor (#133)** — `activation_health` delegates to the activation
  pipeline (read-only), so its counts match `ontos activate` by
  construction; the `validation` check is labeled as the bounded
  frontmatter quick scan it is.
- **map --strict --json (#131)** — `data` gains `result_status`, `strict`,
  and grouped `diagnostics` (rule_id/count/by_severity/samples) so strict
  failures carry triage data, not bare counts.

### Fixed
- **link-check performance (#135)** — ~200x faster on medium repos
  (709-doc benchmark: 13+ min → 3.3 s). The known-ID body scan no longer
  sorts the id set per line nor compiles a regex per (line × id); fuzzy
  suggestion generation is index-backed, gated by lossless
  `real_quick_ratio`/`quick_ratio` bounds, and memoized per broken value.
  Results are byte-identical.
- **Config discovery (#133)** — `load_project_config(repo_root=…)` starts
  discovery at the named root instead of CWD, so commands invoked from
  outside a project no longer silently load an unrelated ancestor config.

### Compatibility notes
- Ontos ≤ 4.6.0 **rejects** configs containing
  `allowed_external_dependency_paths` (strict unknown-key validation, same
  rollout tradeoff as `allowed_orphan_paths`): upgrade all CLI installs
  before adopting the key.
- MCP `ActivateResponse` schema changed (new required warning-budget fields,
  new optional info fields); strict clients revalidate via `tools/list` on
  reconnect.

## [4.6.0] - 2026-05-23

Patch release closing Issue #119, the final v4.5.0 follow-up for activation
warning metadata parity.

### Changed
- **CLI `activate --json` validation metadata** — `payload.data.validation.warnings`
  and `payload.data.validation.errors` now contain structured issue objects
  with `severity`, `message`, and optional `rule_id`, `document_id`, and
  `file_path`, matching MCP activation payloads.
- **JSON contract note** — Consumers that previously expected validation
  warnings/errors as `list[str]` should read `record["message"]`.

## [4.5.0] - 2026-05-22

Minor release closing Issues #115, #116, and #117 across activation,
link-check, lifecycle vocabulary, and MCP upgrade documentation.

### Added
- **Lifecycle artifact vocabulary** — `handoff`, `tracker`, `retro`, `review`,
  `spec`, `report`, `adr`, and `policy` are first-class document types.
- **Lifecycle workflow statuses** — `proposed`, `ready`, `completed`,
  `revised`, and `in-lifecycle` preserve review/handoff semantics.

### Fixed
- **MCP `get_context_bundle` pre-activate warning** — The reminder now uses
  the declared `warnings` field instead of an undeclared schema key.
- **`depends_on` path fallback** — Workspace-relative, declaring-doc-relative,
  and absolute path dependencies resolve before broken-link reporting.
- **Link-check noise** — Generic bare-token detection now requires explicit
  wikilink syntax for unknown IDs.
- **README/template validation skip** — README and `*_template.md` files are
  skipped unless they explicitly declare an `id`.

### Documentation
- Added guidance to restart long-lived MCP hosts after `pipx upgrade ontos`,
  `pip install --upgrade ontos`, or `pipx install --force 'ontos[mcp]'`.

## [4.4.0] - 2026-05-12

Minor release focused on agentic activation resilience.

### Added
- **`ontos activate`** — Best-effort activation with `usable`,
  `usable_with_warnings`, and `not_usable` statuses.
- **MCP `activate` and `session_end`** — Session activation state and typed
  session archive workflows.
- **Frontmatter diagnostics and repair** — `ontos doctor --frontmatter` plus
  `ontos maintain --fix-frontmatter-enums`.

### Changed
- `map`, `doctor`, `verify --all`, and frontmatter repair share configured
  scan exclusions.

## [4.3.0] - 2026-04-15

Minor release adding the Obsidian-compatible write path.

### Added
- **`ontos retrofit --obsidian`** — Dry-run-first command that writes computed
  `tags` and `aliases` into existing document frontmatter.

## [4.2.3] - 2026-04-15

Patch release closing the residual Issue #107 MCP portfolio hardening items on
top of the shipped `v4.2.2` release.

### Fixed
- **`registry_path` helper coercion** — `portfolio.registry_path` now accepts
  `os.PathLike` inputs for programmatic callers and trims leading/trailing
  zero-width/BOM edge characters in addition to normal whitespace.
- **Invalid FTS query contract pinning** — The SQLite error-text fragments that
  map malformed queries to `E_INVALID_QUERY` are now centralized and directly
  test-pinned, including the `"no such column"` path used by malformed
  explicit syntax.
- **Literal-colon limitation visibility** — Explicit colon queries such as
  `user:alice` remain a known `E_INVALID_QUERY` limitation in this patch, and
  the limitation is now documented inline and in the release notes.
- **Scanner stderr resilience** — Slug-collision warnings now ignore broken
  pipe / `EPIPE` write failures without changing warning format or slug
  allocation.

### Changed
- **Explicit `None` fallback contract** — Programmatic callers that pass
  `None` for `portfolio.registry_path` now have that warning-plus-default
  behavior called out as an intentional pinned contract for `v4.2.3`.
- **Repeated discovery warning tests** — Scanner repeated-pass coverage now
  asserts the collision-warning invariants without coupling to full stderr
  equality, so unrelated future warnings do not make the policy test brittle.

## [4.2.2] - 2026-04-15

Patch release closing the residual Issue #105 hardening items on top of the
shipped `v4.2.1` release.

### Fixed
- **Plain-word FTS regression coverage** — Sanitized plain queries are now
  pinned against substring traps like `FORD`, `ANDROID`, `NOTES`, and
  `NEARBY`, plus marker-only and bare-marker negative cases.
- **FTS length-cap enforcement** — Queries longer than 10,000 characters now
  fail before any strip-based copy, including whitespace-flood inputs; the
  `== 10,000` boundary is test-pinned as accepted. This is a new
  `E_INVALID_QUERY` behavior commitment in `v4.2.2`.
- **Unicode search parity** — Cross-form NFC/NFD search behavior is now
  explicitly test-asserted against the `unicode61` tokenizer contract.
- **`registry_path` coercion observability** — Non-string
  `portfolio.registry_path` values now emit a `WARNING` before falling back to
  the default path, and outer whitespace on string paths is normalized.
- **Malformed explicit FTS error translation** — SQLite `"no such column"`
  errors produced by malformed explicit syntax now map to `E_INVALID_QUERY`
  alongside the existing syntax-error family.

### Changed
- **Bundle ordering traceability** — `_lost_in_middle_order()` now carries an
  inline fixed-slot rationale comment, and equal-score tiebreak behavior is
  independently pinned by test.
- **Scanner warning policy** — Repeated portfolio discovery passes now
  explicitly document and test that slug-collision warnings re-emit per call.

## [4.2.1] - 2026-04-14

Patch release shipping the remaining Issue #86 release-hardening items for portfolio config semantics, FTS sanitization, slug-collision warnings, module exports, and bundle-order parity.

### Fixed
- **`registry_path` omission semantics** — Omitting `registry_path` in `portfolio.toml` now applies the default `~/Dev/.dev-hub/registry/projects.json` path; set `registry_path = ""` to disable registry metadata merging explicitly. This behavior change affects hand-edited configs with the key removed, not configs created by `ensure_portfolio_config()`.
- **Plain FTS query sanitization** — behavior expansion: plain multi-term searches are now quoted before FTS5 execution, which turns previously failing queries like `hello-world`, `what a day!`, `.hidden`, and `'foo` into successful searches while preserving explicit FTS syntax passthrough and existing `E_INVALID_QUERY` behavior for malformed explicit syntax. Literal-colon queries such as `user:alice` remain an explicit-syntax limitation in this patch.
- **Slug-collision visibility** — Portfolio discovery now emits a stderr warning when a numeric suffix is assigned after a slug collision, including the base slug, assigned slug, and workspace path.

### Changed
- **Module export hygiene** — Track A MCP modules now publish explicit `__all__` surfaces for `PortfolioIndex`, portfolio config helpers, scanner helpers, and context bundling entry points.
- **Lost-in-the-middle ordering clarity** — `_lost_in_middle_order()` now uses the spec’s fixed-slot implementation directly while preserving the existing output order.

## [4.2.0] - 2026-04-14

Adds managed Cursor MCP onboarding and a universal `print-config` fallback while preserving the shipped Antigravity contract. PR #102.

### Added
- **Managed Cursor MCP adapter** — `ontos mcp install --client cursor --scope {project,user}` writes `.cursor/mcp.json` or `~/.cursor/mcp.json` with the Ontos entry.
- **`ontos mcp uninstall`** — Removes only `mcpServers.ontos` for managed clients, returning `removed` or `noop`.
- **`ontos mcp print-config`** — Emits a complete manual config document for Antigravity, Cursor, Claude Code, Codex, and VS Code without writing to disk.
- **`cursor_mcp` doctor check** — Validates Cursor project/user MCP config with project-precedence aggregation and pinned details output.
- **Shared MCP core** — `ontos/core/mcp_shared.py` now owns launcher resolution, shared entry building, initialize probing, config rendering, and entry equivalence.
- **Cursor adapter module** — `ontos/core/cursor_mcp.py` encapsulates Cursor path discovery, read/write helpers, entry upsert/remove, and inspection.

### Fixed
- **Symlink scope-containment** — Managed MCP writes now reject config paths whose resolved targets escape the expected workspace or home scope.
- **Atomic config writes** — JSON config writes now use tempfile + `os.replace()` to avoid partial-write races during concurrent installs.
- **Doctor path coverage** — Cursor doctor tests now exercise the production adapter path and cover malformed/misconfigured entry variants directly.
- **Antigravity compatibility guard** — Golden snapshot coverage now asserts the persisted Antigravity entry shape and upsert action.

### Changed
- **Install action taxonomy** — `ontos mcp install` now reports `created`, `updated`, or `noop`; `noop` is a behavior clarification, not a breaking change.
- **Refresh semantics** — Rerunning `ontos mcp install --client ...` remains the supported refresh/re-register flow; no standalone `refresh` subcommand was added.
- **Platform scope** — Managed MCP automation remains POSIX-only in `v4.2.0`; Windows users should use `print-config`.

## [4.0.0] - 2026-04-05

Ships MCP server mode — a stdio MCP server that exposes the Ontos knowledge graph to AI agents and IDEs via 8 structured tools. PR #81.

### Added
- **`ontos serve` command** — Starts a stdio MCP server for a single workspace, enabling native AI IDE integration via the Model Context Protocol.
- **8 MCP tools**: `workspace_overview`, `context_map`, `get_document`, `list_documents`, `export_graph`, `query`, `health`, `refresh`.
- **`ontos/mcp/` package** — `server.py` (FastMCP bootstrap), `tools.py` (tool adapters), `cache.py` (snapshot cache with file-mtime invalidation), `schemas.py` (Pydantic response models).
- **Optional dependency extra** — `pip install 'ontos[mcp]'` adds `mcp>=1.2` and `pydantic>=2.0`. Base install unchanged.
- **File-mtime fingerprint cache** — Automatic staleness detection via `(path, st_mtime_ns, st_size)` fingerprints. Catches edits, new files, deletions, and renames.
- **`[mcp]` config section** in `.ontos.toml` — `usage_logging` and `usage_log_path` settings.
- **Pydantic response schemas** — Typed output validation for all MCP tool responses with structured error envelopes.

### Changed
- Python 3.10+ required for MCP features (base package remains 3.9+).
- Bumped version to `4.0.0`.

### Notes
- No breaking changes — all existing CLI commands preserved.
- All MCP tools are read-only (write tools deferred to v4.1).
- Single-workspace per server instance, stdio transport only.

## [3.4.0] - 2026-04-04

Ships `--compact tiered` context maps — a prose summary plus type-ranked compact output for token-constrained agents.

### Added
- **`--compact tiered` mode** — `ontos map --compact tiered` produces three-section output: prose project summary (Tier 1), type-ranked compact listing (Tier 2), and full ID index (Tier 3). PR #79.

### Fixed
- Consistent Tier 1 log ordering by date descending.
- `project_root` normalization before compact dispatch (crash fix on relative paths).
- Shared `_sort_key` across all compact modes for deterministic output.
- Log contract enforcement in tiered summary generation.
- Reverted anti-scope violations in `_generate_tier1_summary()`.
- Final tiered review debt removed (spec cleanup).

### Changed
- README updated with `--compact` sub-command documentation.
- Bumped version to `3.4.0`.

## [3.3.1] - 2026-02-28

Patch release shipping external review remediation, link-check false positive reduction, and `promote_check` maintenance task.

### Added
- **`promote_check` maintenance task** — `ontos maintain` now runs `ontos promote --check` non-interactively to report documents ready for promotion (order 45, 9 total tasks).
- 26 new test cases for link-check false positive filters (short labels, ALL_CAPS, version-adjacent patterns).
- 2 new integration tests documenting the precision/recall tradeoff of FP filtering.

### Fixed
- **link-check false positives reduced from 408 → 45** (89% reduction). Added pre-classification filters for bare numbers, version strings, known YAML field names, file extensions, short labels (`A1`, `NB-1`), ALL_CAPS constants, and version wildcards (`v2.x`).
- `SECURITY.md` updated from stale v0.4.x references to current v3.3.x surface.
- README roadmap updated: v3.3.0 is now "Current".
- `Ontos_Manual.md` updated to v3.3 with `link-check` and `rename` subsections added.
- `examples/minimal/` populated with 3 runnable doc files.
- Legacy test isolation: `.ontos/scripts/tests/` excluded from default `testpaths`.
- `promote.py` typo fix: "documents find" → "documents found".

### Changed
- `pyproject.toml` classifier bumped from `Development Status :: 3 - Alpha` to `Development Status :: 4 - Beta`.
- `CHANGELOG.md` cross-reference to `Ontos_CHANGELOG.md` added.
- `.cursorrules` and `AGENTS.md` regenerated to reflect v3.3.0 metadata.
- Bumped version to `3.3.1`.

## [3.3.0] - 2026-02-11

v3.3 ships 62 audit-derived hardening fixes plus 3 new commands across Track A (hardening) and Track B (features).

### Added
- **`ontos link-check`** — Scan for broken references, duplicate IDs, and orphaned documents with JSON output and exit codes `0/1/2`.
- **`ontos rename <old_id> <new_id>`** — Safe ID renaming with dry-run default, `--apply`, collision detection, and automatic `depends_on` propagation.
- **Unified scan scope** — `--scope docs|library` wired across all scanning commands for consistent document discovery.
- **Canonical unified document loader** — Single `load_document()` path used by every command, eliminating parser inconsistencies.
- **Unified JSON envelopes** — All commands emit `{ "status": "ok"|"error", "data": ... }` structured output.
- **CLI typed error routing** — Consistent error handling and exit codes across all commands.
- **JSON envelope helpers** — Shared utilities for command output formatting.
- **New test coverage** — Graph primitives, schema validation, `log` command, and review gap closures.

### Fixed
- **Core contract ambiguity** — Parser/loader contract unified; frontmatter normalization, duplicate detection, and input validation standardized (Track A1).
- **Path resolution** — `consolidate` and proposal paths now resolve relative to runtime root, not package installation directory.
- **History write contract** — Restored correct behavior in consolidate pipeline.
- **Command safety** — Transactional semantics and strict input handling for `consolidate`, `doctor`, `paths`, `migrate`, and config parsing (Track A2).
- **Return contract normalization** — Every command returns typed results, not raw dicts (Track A3).
- **Documentation drift** — `Ontos_Manual.md` realigned with implementation (Track A4).
- **3 deferred items** from Track A3 review (NB-1, NB-2, NB-3) resolved.

### Changed
- **CLI surface normalization** — Consolidated instruction exports, normalized return contracts, unified command taxonomy (Track A3).
- **Dead code removal** — Findings #54, #57, #59 cleaned up (Track A4).
- Bumped version to `3.3.0`.

### Removed
- Dead code identified across findings #54, #57, #59.

## [3.2.3] - 2026-02-10

Patch release to fix package/tag version alignment for PyPI publishing.

### Fixed
- Aligned package version metadata to `3.2.3` in `pyproject.toml` and `ontos/__init__.py`.
- Unblocked publish workflow by using a fresh tag/version pair after the `v3.2.2` mismatch.

## [3.2.2] - 2026-02-10

Patch release focused on shipping `ontos maintain` and aligning weekly maintenance documentation.

### Added
- Native `ontos maintain` command in the unified CLI.
- `maintain` flags: `--dry-run`, `--verbose`, and repeatable/comma-separated `--skip`.
- Maintain test suite in `tests/commands/test_maintain.py`.
- Release notes source file at `docs/releases/v3.2.2.md`.

### Fixed
- Documentation/implementation gap where `ontos maintain` was documented but unavailable.
- No-op interactive proposal prompt in maintenance flow; now reports candidates for manual graduation.
- Dry-run behavior for maintenance tasks that previously scanned documents unnecessarily.
- AGENTS staleness checks now use the maintain command repo root consistently.
- Maintenance workflow text alignment in `Ontos_Agent_Instructions.md` and `Ontos_Manual.md`.

### Changed
- Weekly maintenance workflow now runs 8 tasks: migrate, map, health check, curation stats, consolidate, proposal review report, link check, and AGENTS sync.
- Maintain JSON output now includes per-task `details`.

## [3.2.1] - 2026-02-09

Patch release focused on review remediation, safer context map output, and activation resilience.

### Added
- AGENTS.md Trigger Phrases and post-compaction recovery guidance
- Proposal governance references:
  - `.ontos-internal/strategy/proposals/README.md`
  - `.ontos-internal/tmp/README.md`
- `docs/assets/` visuals used in README

### Fixed
- External review remediation set from PR #61
- Key Documents formatting and path-safety issues in context map output (PR #62)
- Config-driven/mode-aware Critical Paths behavior in Tier 1 (PR #63)
- Activation resiliency content parity in `.cursorrules` transform (PR #64)
- Proposal naming typo cleanup and deterministic thumbnail generation (PR #65)

### Changed
- Reorganized v3.2.1 proposal tracks into `v3.2.1a` / `v3.2.1b` / `v3.2.1c` / `v3.2.1d`
- Added release notes source file at `docs/releases/v3.2.1.md`

## [3.2.0] - 2026-01-30

v3.2 delivers three major themes: Re-Architecture Support, Environment Detection, and Activation Resilience.

### Added

**Theme 1: Re-Architecture Support**
- `ontos export data` — Bulk JSON export with dependency graph
- `ontos export claude` — CLAUDE.md generation (deprecates bare `export`)
- `ontos migration-report` — Dependency analysis (safe/review/rewrite classification)
- `ontos migrate` — Convenience command (runs export + migration-report)

**Theme 2: Environment Detection**
- `ontos env` — Detect environment manifests (pyproject.toml, Brewfile, package.json, .tool-versions)
- `ontos doctor` environment check — Warns about missing or unparseable manifests (9 checks total)
- Candidate suggestions for document scaffolding

**Theme 3: Activation Resilience**
- Tiered context map structure (Tier 1: ~2k tokens, Tier 2: doc index, Tier 3: full graph)
- `ontos map --sync-agents` flag for AGENTS.md auto-sync
- AGENTS.md Current Project State section (branch, doc count, last log, health)
- AGENTS.md Re-Activation Trigger section for context recovery hints
- AGENTS.md USER CUSTOM section preserved during regeneration

### Fixed
- Section-aware token truncation for Tier 1 (not character-based)
- USER CUSTOM preservation uses explicit markers
- Pipe and newline escaping in Tier 1 tables
- `gather_stats` optimized (scans docs/logs directories only, not entire repo)

### Changed
- Context map format updated (`ontos_map_version: 2`)
- AGENTS.md template expanded with Current Project State and Re-Activation sections
- `ontos export` without subcommand now warns and runs `export claude`

## [3.1.0] - 2026-01-22

### Added
- **Track A: Obsidian Compatibility & Token Efficiency**
  - `ontos map --obsidian` flag for Obsidian-compatible wiki-links
  - `ontos map --compact` flag for reduced token output
  - `ontos map --filter` flag for type-based filtering
  - Token-aware caching system with 15-minute TTL
  - `ontos doctor -v` verbose mode for diagnostics

- **Track B: Native Command Migration**
  - All 7 CLI commands now run natively (no subprocess overhead)
  - `scaffold` command fixed (previously rejected positional arguments)
  - `verify` command with positional path support
  - `query` command with all 6 modes (depends-on, depended-by, concept, stale, health, list-ids)
  - `consolidate` command with count and age-based modes
  - `stub` command with interactive and CLI modes
  - `promote` command with fuzzy ID matching
  - `migrate` command for schema migration

### Fixed
- `scaffold` no longer rejects positional arguments (was broken since v3.0)
- `consolidate` import crash on missing config defaults (B1)
- `promote` crash on absolute paths outside repo (B2)

### Changed
- Commands now use `SessionContext` for transactional integrity
- Centralized CLI registration in `ontos/cli.py`
- Golden fixture tests ensure parity with legacy behavior

### Known Limitations (deferred to v3.2)
- `consolidate --count 0` semantics (X-H2)
- `stub` type/id validation (X-M1)
- `scaffold` error messaging improvements (X-M2)
- `migrate` unsupported schema handling (X-M3)
- `query --health` cycle detection (X-M4)

## [3.0.2] - 2026-01-18

### Fixed
- Fixed sys.path shadowing issue in legacy scripts where `ontos/_scripts/ontos.py`
  shadowed the `ontos` package, causing `ModuleNotFoundError: 'ontos' is not a package`
- Commands now working: `scaffold`, `stub`, `promote`, `migrate`

### Known Issues
- Commands `verify`, `query`, `consolidate` remain broken (deferred to v3.0.3)
- Legacy scripts ignore `.ontos.toml` settings (use native CLI commands which respect config)
