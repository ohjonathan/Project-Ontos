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


## [2.4.0] - 2025-12-15

### Added (Configuration Automation & UX Overhaul)
- **Mode System** — Three presets (`automated`/`prompted`/`advisory`) control workflow friction
  - `automated`: Zero friction, auto-archives on push, best for solo devs
  - `prompted`: Blocked until archived, you control details (DEFAULT for new installs)
  - `advisory`: Reminders only, maximum flexibility
- **`ONTOS_MODE`** — Single config value applies sensible defaults
- **Session Appending** — Multiple pushes on same branch/day append to single log (no ghost logs)
- **`--auto` flag** — Called by pre-push hook for automatic archive
- **`--enhance` flag** — Find and display auto-generated log for enrichment
- **`--reconfig` flag** — Reconfigure mode while preserving custom settings
- **`--non-interactive` flag** — CI-friendly initialization with `--mode` and `--source`
- **`ONTOS_SOURCE`** — Environment variable support for source in CI/shared environments
- **Hook timeout** — Pre-push operations timeout gracefully (10s default)
- **Context map auto-regeneration** — Pre-push hook regenerates context map
- **`status: auto-generated`** — Auto-created logs marked for enrichment
- **Lint warning for auto-generated logs** — `--lint` shows logs needing human review
- **`branch:` field** — Frontmatter tracks original branch for session appending safety
- **`resolve_config()` function** — Mode-aware configuration resolution in `ontos_lib.py`
- **`get_source()` function** — Fallback chain for source (env → config → git user)
- **Config template** — `.ontos/templates/ontos_config.py.template` for consistent setup

### Changed
- **Version bump to 2.4.0**
- `ontos_init.py` — Complete rewrite with interactive mode selection
- `ontos_pre_push_check.py` — Now supports auto-archive and timeout handling
- Pre-push hook regenerates context map before checking archive status

### Fixed
- `ontos_migrate_frontmatter.py` now skips `archive/` directories when scanning for untagged files

### Changed
- Archived v2.3 planning documents to `.ontos-internal/archive/planning/`
- Cleaned up root directory (removed temp files)

## [2.3.0] - 2025-12-14

### Added (Tooling & Maintenance)
- **New Scripts:**
  - `ontos_query.py` — Query dependencies, find stale docs, check graph health
  - `ontos_consolidate.py` — Automate monthly log consolidation into `decision_history.md`
  - `ontos_maintain.py` — Single command for migration and regeneration
  - `ontos_pre_push_check.py` — Validation logic moved from bash to Python
- **UX Improvements:**
  - **Adaptive Templates** — `ontos_end_session.py` adapts log sections based on `event_type` (e.g., `chore` is shorter)
  - **Auto-slug** — Automatically generates log slug from branch name or last commit
  - **Archive Ceremony Reduction** — `DEFAULT_SOURCE` and optional source arg reduce typing
  - **Starter Scaffolding** — `ontos_init.py` creates `mission.md`, `roadmap.md`, `decision_history.md`
- **Data Quality:**
  - **Creation-time Validation** — Checks concepts against vocabulary when creating logs
  - **Extended Impact Suggestions** — Looks back to last session log for changes

### Changed
- **Pre-push hook** — Now delegates to Python script for better testability and "Small Change" heuristics
- **Consolidation** — `decision_history.md` now explicitly supported with correct table targeting
- `ontos_init.py` — Now includes scaffolding and hook installation (removed `ontos_install_hooks.py`)
- Version bump to 2.3.0

## [Unreleased]

### Added (v2.2 - Data Quality)
- **Common Concepts Reference** (`docs/reference/Common_Concepts.md`) — Controlled vocabulary for consistent tagging
- **Alternatives Considered section** — New section in log template for documenting rejected options
- **Impacts nudging** — Interactive prompt when creating logs with empty impacts
- **Tagging Discipline** — Agent Instructions for v3.0-ready data capture (concepts, impacts, alternatives)
- **`--lint` flag** — Soft warnings for data quality issues in `ontos_generate_context_map.py`
  - Empty impacts on active logs
  - Unknown concepts not in vocabulary
  - Excessive concepts (>6 per log)
  - Stale logs (>30 days without consolidation)
  - Active log count exceeds LOG_RETENTION_COUNT (v2.1 integration)
- **Lint test suite** (`tests/test_lint.py`) — Unit tests for data quality checks


## [2.1.0] - 2025-12-13

### Added (Smart Memory)
- **Decision History Index** (`.ontos-internal/strategy/decision_history.md`) — Permanent ledger for archived session decisions
- **Consolidation Ritual** — Monthly maintenance process documented in Manual (section 3)
- **Absorption Pattern** — Documented pattern for capturing decisions in Space documents with constraints and citations
- **Historical Recall** — Agents can read archived logs referenced in decision_history.md (Agent Instructions update)
- **LOG_RETENTION_COUNT** — Configurable threshold for active logs before consolidation (default: 15)

### Added (UX & Workflow)
- **Context map notice for contributors** — When generated in Project Ontos repo, context map shows a notice explaining it will be overwritten when users initialize Ontos in their projects
- **Agent `--no-verify` rule** — Agents must ask before using `git push --no-verify` (behavioral expectation, not technical restriction)
- **v2.3 UX improvement ideas** — Documented 10 friction points with proposed solutions and priority matrix
- **Blocking pre-push hook** — Push is blocked until session is archived (prevents context loss)
- **Marker file system** — `ontos_end_session.py` creates `.ontos/session_archived` marker
- **Pre-Push Protocol** — Added to Agent Instructions (section 3.1) with CRITICAL enforcement
- **Workflow configuration options** — `ENFORCE_ARCHIVE_BEFORE_PUSH` and `REQUIRE_SOURCE_IN_LOGS` in ontos_config.py
- **Configuration documentation** — Added Configuration section to Manual with examples for relaxed/strict modes
- **Archive directory** — `.ontos-internal/archive/` for historical docs that should be preserved but not scanned
- **Directory-level skip patterns** — `ontos_generate_context_map.py` now prunes entire directories matching skip patterns (e.g., `archive/`)
- **Minimal example** — `examples/minimal/` with single-file quick-start example

### Changed
- Pre-push hook now blocks by default (was advisory only)
- Pre-push hook respects `ENFORCE_ARCHIVE_BEFORE_PUSH` config (blocking vs advisory mode)
- `--source` requirement in `ontos_end_session.py` respects `REQUIRE_SOURCE_IN_LOGS` config
- One archive enables one push (marker deleted after successful check)
- **Documentation compaction** — 5 guide files consolidated into single `Ontos_Manual.md` (-80%)
- **Agent Instructions trimmed** — Reduced to essential commands only
- **Example simplified** — 8-file task-tracker replaced with 1-file minimal example (-88%)
- **Total line reduction** — 13,100 → 7,000 lines (-47%), markdown specifically -68%
- **README.md** — Documentation section simplified from nested headers to flat list
- **ontos_update.py** — `UPDATABLE_DOCS` reduced from 7 to 2 entries (removed deleted guide references)
- **Installation standardized** — `ontos_init.py` is now the single entry point (replaces separate hook + map commands)

### Removed
- `docs/guides/` directory (consolidated into `Ontos_Manual.md`)
- `examples/task-tracker/` (replaced with `examples/minimal/`)
- `v2_implementation_plan.md`, `self_development_protocol_spec.md` (completed, no longer needed)
- `Ontos_Technical_Architecture.md` (consolidated)
- `docs/logs/` — 4 legacy v1-era session logs (predated current Ontos structure)

## [2.0.0] - 2025-12-12

### Added
- **Dual Ontology Model** — Separation of Space (Truth) and Time (History) for project knowledge
- **`impacts` field for logs** — Logs now connect to Space documents via `impacts` instead of `depends_on`
- **`event_type` field for logs** — Categorize sessions by intent: feature, fix, refactor, exploration, chore
- **`concepts` field for logs** — Freeform tags for searchability
- **Token estimates** — Context map shows approximate token count per document
- **Timeline section** — Context map includes recent session history
- **Provenance header** — Context map shows generation mode and timestamp
- **Auto-suggested impacts** — `ontos_end_session.py` suggests impacted docs based on git diff
- **Log validation rules** — Validates event_type, impacts references, and log schema

### Changed
- **Major version bump** — Semver aligned with v2.0 Dual Ontology architecture
- Logs no longer use `depends_on` (use `impacts` instead)
- Context map structure updated with Timeline section
- Validation now enforces log-specific schema requirements

### Fixed
- Invalid `event_type: implementation` in legacy logs (not a valid event type)

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
