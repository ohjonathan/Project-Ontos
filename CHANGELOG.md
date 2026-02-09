# Changelog

All notable changes to this project will be documented in this file.

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
