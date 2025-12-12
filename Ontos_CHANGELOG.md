---
id: ontos_changelog
title: Project Ontos Changelog
type: kernel
scope: ontos-tooling-only
update_policy: |
  IMPORTANT: Only update this file when making changes to Project Ontos ITSELF
  (.ontos/scripts/, protocol schema, agent instructions, Ontos documentation).

  Do NOT update this file when working on projects that USE Ontos as their
  documentation system. Those projects should have their own CHANGELOG.md.
depends_on: []
---

# Project Ontos Changelog

All notable changes to **Project Ontos itself** (the protocol and tooling) will be documented in this file.

> **For AI Agents**: This changelog is for the Ontos tooling only. If you're working on a project that *uses* Ontos, update that project's `CHANGELOG.md` instead (via `ontos_end_session.py --changelog`).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.5.0] - 2025-12-12

### Added
- **Self-Development Protocol** — Ontos can now manage its own development ("dogfooding")
- **Smart Configuration** — Auto-detects Contributor Mode vs User Mode based on `.ontos-internal/kernel/mission.md` marker file
- **`log` document type** — New type for timeline/session history tracking (rank 4)
- **LOG section in context map** — Session logs now appear in their own hierarchy section
- **`.ontos-internal/` directory** — Hidden project documentation for building Ontos (separate from user docs in `docs/`)
- Project documentation: mission, v2 strategy, roadmap, architecture, schema, and self-development protocol specs

### Changed
- Default skip patterns now exclude `.ontos-internal/` to prevent accidental scanning in user projects
- `unknown` type moved from rank 4 to rank 5 to accommodate `log` type
- Type hierarchy documentation updated across all docs

## [1.4.0] - 2025-12-10

### Added
- **Git hooks installation** (`ontos_install_hooks.py`) — Automatically install pre-push hook to remind about session archiving
- **Hook updates via `ontos_update.py`** — Hooks are now updated alongside scripts and docs
- Pre-push hook reminds users to run "Archive Ontos" before pushing

### Changed
- Quick Install instructions now include hook installation step
- Installation Guide updated with hook setup details

## [1.1.0] - 2025-12-10

### Added
- Datetime with timezone and LLM source field in session logs

### Fixed
- Ontos tooling files (`Ontos_*.md`) are now excluded from project context maps
- Migration script no longer prompts to tag Ontos tooling files

## [1.0.0] - 2025-12-10

### Added
- **Update script** (`ontos_update.py`) — Pull latest Ontos from GitHub with one command
- **Split configuration** — `ontos_config_defaults.py` (updatable) + `ontos_config.py` (user overrides, never touched)
- **Maintenance Guide** (`Ontos_Maintenance_Guide.md`) — Comprehensive guide for context hygiene, error remediation, and updates
- **Version constant** (`ONTOS_VERSION`) in config for update checking
- **Backup system** — Updates create backups in `.ontos/backups/` before overwriting
- Changelog integration in `ontos_end_session.py` (prompts for changelog entries)
- `Ontos_CHANGELOG.md` for Project Ontos tooling changes (distinct from project changelogs)
- MIT License (`LICENSE`)
- `CONTRIBUTING.md` with contribution guidelines
- `CODE_OF_CONDUCT.md` for community standards
- `SECURITY.md` for vulnerability reporting
- GitHub Actions CI workflow (`.github/workflows/ci.yml`)
- GitHub issue and PR templates

### Changed
- **Version bump to 1.0.0** — First stable release
- Config variable renamed: `DEFAULT_DOCS_DIR` → `DOCS_DIR` (backward compatible)
- Installation Guide now documents the two-file config pattern
- Renamed `CHANGELOG.md` to `Ontos_CHANGELOG.md` with YAML frontmatter for agent clarity
- README now includes badges (CI, License, Python version)

### Removed
- Internal development files (`archive/`, review documents)

## [0.4.0] - 2025-11-29

### Added
- Centralized configuration in `ontos_config.py`
- `--version` / `-V` flag to all scripts
- `-q` shorthand for `--quiet` flag
- `--strict` mode for `ontos_migrate_frontmatter.py`
- `--quiet` mode for all scripts (CI/CD friendly)
- Pre-commit hook configuration (`.pre-commit-config.yaml`)
- Troubleshooting section in `Ontos_Manual.md`
- Unit test suite with pytest (`tests/`)
- Type hints for all script functions
- `--watch` mode for continuous monitoring
- `--dry-run` mode for migration script
- Multiple directory support (`--dir` can be repeated)

### Changed
- Template file uses `_template` ID prefix (excluded from graph)
- Orphan detection now properly excludes `/logs/` directory
- Cleaned up dead code in type hierarchy validation
- Reorganized documentation into `docs/guides/` and `docs/reference/`
- Moved feedback files to `archive/feedback/`
- Version bump to 0.4.0

### Fixed
- Broken link in `Ontos_Agent_Instructions.md` (now points to `Ontos_Manual.md`)
- UTF-8 encoding in `ontos_migrate_frontmatter.py`
- Log files no longer flagged as orphans

## [0.3.0] - 2025-11-24

### Added
- Strict mode (`--strict` flag) for CI/CD integration in `ontos_generate_context_map.py`
- Maintenance protocol ("Maintain Ontos" command)
- Session archival with `ontos_end_session.py`
- Migration script `ontos_migrate_frontmatter.py` for untagged files
- Five integrity checks (broken links, cycles, orphans, depth, architecture)

### Fixed
- String handling in `depends_on` field (now accepts string or list)
- UTF-8 encoding with fallback for file reading
- Specific exception handling (removed bare `except:`)

### Changed
- Improved orphan detection to skip templates
- Added document count and issue count to output

## [0.2.0] - 2025-11-23

### Added
- Type hierarchy validation (kernel → strategy → product → atom)
- Cycle detection using DFS algorithm
- Dependency depth checking (max 5 levels)
- Architectural violation detection

## [0.1.0] - 2025-11-22

### Added
- Initial YAML frontmatter specification
- Basic context map generation (`ontos_generate_context_map.py`)
- Document type taxonomy (kernel, strategy, product, atom)
- `Ontos_Context_Map.md` auto-generation
