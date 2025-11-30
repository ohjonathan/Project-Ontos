---
id: po-changelog
title: Project Ontos Changelog
type: kernel
scope: ontos-tooling-only
update_policy: |
  IMPORTANT: Only update this file when making changes to Project Ontos ITSELF
  (scripts/, protocol schema, agent instructions, Ontos documentation).

  Do NOT update this file when working on projects that USE Ontos as their
  documentation system. Those projects should have their own CHANGELOG.md.
depends_on: []
---

# Project Ontos Changelog

All notable changes to **Project Ontos itself** (the protocol and tooling) will be documented in this file.

> **For AI Agents**: This changelog is for the Ontos tooling only. If you're working on a project that *uses* Ontos, update that project's `CHANGELOG.md` instead (via `end_session.py --changelog`).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Changelog integration in `end_session.py` (prompts for changelog entries)
- `POCHANGELOG.md` for Project Ontos tooling changes (distinct from project changelogs)

### Changed
- Renamed `CHANGELOG.md` to `POCHANGELOG.md` with YAML frontmatter for agent clarity

## [0.4.0] - 2025-11-29

### Added
- Centralized configuration in `scripts/config.py`
- `--version` / `-V` flag to all scripts
- `-q` shorthand for `--quiet` flag
- `--strict` mode for `migrate_frontmatter.py`
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
- UTF-8 encoding in `migrate_frontmatter.py`
- Log files no longer flagged as orphans

## [0.3.0] - 2025-11-24

### Added
- Strict mode (`--strict` flag) for CI/CD integration in `generate_context_map.py`
- Maintenance protocol ("Maintain Ontos" command)
- Session archival with `end_session.py`
- Migration script `migrate_frontmatter.py` for untagged files
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
- Basic context map generation (`generate_context_map.py`)
- Document type taxonomy (kernel, strategy, product, atom)
- `CONTEXT_MAP.md` auto-generation
