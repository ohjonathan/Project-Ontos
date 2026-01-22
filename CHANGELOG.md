# Changelog

All notable changes to this project will be documented in this file.

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
