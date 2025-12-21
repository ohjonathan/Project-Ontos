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

## [2.8.5] - 2025-12-22

### Theme: "Unified CLI"

Introduced a unified command interface for all Ontos scripts.

### Added
- **Unified CLI dispatcher** (`ontos.py` in project root)
  - 7 commands: `log`, `map`, `verify`, `maintain`, `consolidate`, `query`, `update`
  - 11 aliases for natural language usage (`archive` → `log`, `context` → `map`, etc.)
  - Full argument passthrough to underlying scripts
  - `--help` and `--version` flags
- **32 CLI tests** in `tests/test_cli.py`
  - Tests all commands with `--help`
  - Tests all 11 aliases resolve correctly
  - Tests argument passthrough
  - Tests module structure (7 commands, 11 aliases)
- **`main()` function in `ontos_generate_context_map.py`**
  - Wrapped CLI logic for unified dispatcher compatibility
  - Direct script invocation still works

### Changed
- **Ontos_Manual.md** — Added Section 8: Unified CLI
  - Command table with old/new syntax
  - Alias reference
  - Usage examples

### Deprecated
- Direct script invocation (e.g., `python3 .ontos/scripts/ontos_end_session.py`)
  - Still works in v2.8 (no warnings)
  - Will show deprecation warnings in v2.9
  - Will be removed in v3.0

---

## [2.8.4] - 2025-12-21

### Theme: "Script Consolidation"

Refactored remaining Ontos scripts to v2.8 transactional architecture.

### Added
- **Deduplication** — Removed duplicate `graduate_proposal()` and `add_graduation_to_ledger()` from `ontos_maintain.py` (102 lines removed)
  - Now imports from `ontos_end_session.py` (already v2.8 compliant)

### Changed
- **ontos_consolidate.py** — Full v2.8 refactor
  - `append_to_decision_history()` uses `buffer_write()` with `_owns_ctx` pattern
  - `validate_decision_history()`, `consolidate_log()`, `archive_log()` use `OutputHandler`
  - `main()` creates OutputHandler for all CLI output
- **ontos_verify.py** — Full v2.8 refactor
  - `update_describes_verified()` uses `buffer_write()` with `_owns_ctx` pattern
  - `verify_single()`, `verify_all_interactive()` use `OutputHandler`
- **ontos_maintain.py** — Deduplicated + OutputHandler
  - `review_proposals()`, `main()` use `OutputHandler`
- **ontos_query.py** — OutputHandler consistency (read-only script)
  - `main()` uses `OutputHandler` for all CLI output

### Tests
- Updated `test_consolidate.py::test_append_targets_history_ledger_not_consolidation_log`
  - Now mocks `buffer_write` instead of `builtins.open`

---

## [2.8.3] - 2025-12-21

### Theme: "Transaction Composability"

Full implementation of v2.8 transactional architecture in `ontos_end_session.py`.

### Added
- **`_owns_ctx` pattern** — Transaction composability for all write functions
  - Functions only commit when they own the context (created it themselves)
  - Enables atomic commits across multiple buffered writes
- **5 transaction tests** — Comprehensive tests for commit/rollback behavior
  - `test_main_commits_all_files_atomically`
  - `test_main_rollback_on_commit_failure`
  - `test_graduate_proposal_uses_buffer_write`
  - `test_append_to_log_uses_buffer_write`
  - `test_create_changelog_uses_buffer_write`
- **`OutputHandler.detail()` method** — For indented context messages

### Changed
- **6 write functions** converted to `buffer_write()` with `_owns_ctx`:
  - `graduate_proposal()` (also uses `buffer_delete()`)
  - `add_graduation_to_ledger()`
  - `append_to_log()`
  - `create_auto_log()`
  - `create_changelog()`
  - `add_changelog_entry()`
- **6 functions** converted to use `OutputHandler`:
  - `find_existing_log_for_today()`
  - `auto_archive()`
  - `generate_auto_slug()`
  - `suggest_impacts()`
  - `validate_concepts()`
  - `check_stale_docs_warning()`
- **`main()` commits once** at end for atomic transaction

### Metrics
- All 248 tests pass
- Print statements: 71 → 57 (remaining in interactive prompts only)

---

## [2.8.0] - 2025-12-20

### Theme: "Clean Architecture Refactor"

Unified package structure for better testability and maintainability.

### Added
- **`ontos/` package structure** — New modular architecture
  - `ontos/core/` — Pure logic layer (context, frontmatter, staleness, history)
  - `ontos/ui/` — I/O layer (OutputHandler for display)
- **`SessionContext` class** — Transactional file operations
  - Two-phase commit (temp-then-rename for atomicity)
  - File locking with stale lock detection
  - `from_repo()` factory method
- **Core modules**:
  - `context.py` — Session state and file operations
  - `frontmatter.py` — Pure parsing functions
  - `staleness.py` — Describes validation with impure marking
  - `history.py` — Decision history generation
  - `paths.py` — Path helpers with mode-awareness
  - `config.py` — Configuration helpers
  - `proposals.py` — Proposal management
- **`OutputHandler` class** — Centralized output formatting
- **18 new tests** — SessionContext + backwards compatibility identity checks

### Changed
- **`ontos_lib.py` is now a pure re-export shim** (1,323→95 lines)
  - All functions re-exported from `ontos.core.*` and `ontos.ui.*`
  - `from ontos_lib import X` and `from ontos.core.X import Y` reference same objects
- **Impure function marking** — Docstrings document all subprocess calls with mock guidance

### Deprecated
- **`ontos_lib.py` direct usage** — Import from `ontos.core.*` instead
  - v2.8: Silent operation (no warnings)
  - v2.9: DeprecationWarning on import
  - v3.0: Module removed

### Tests
- All 243 tests pass (225 original + 18 new)

---

## [2.7.1] - 2025-12-20

### Theme: "Polish Release"

Bug fixes, documentation, and test organization to elevate v2.7 from A- to A grade.

### Fixed
- **Root config import** — Fixed broken relative import in `ontos_config.py` (root)
  - Uses `importlib.util` to load scripts config under different name
  - Avoids circular import while re-exporting all public symbols
  - Template updated to match

### Changed
- **Exception logging** — Staleness check in `ontos_end_session.py` now logs exceptions
  - Changed from silent `pass` to `logging.debug()`
  - Improves debugging when staleness checks fail

### Added
- **v2.7 concepts** — Added `describes`, `staleness`, `immutable-history` to Common_Concepts.md
- **Cookbook examples** — Added "Documentation Staleness Tracking (v2.7)" section to Manual

### Improved
- **Test organization** — Renamed `test_v26_validation.py` to `test_validation.py`
  - Prevents version-suffixed test file accumulation
- **Legacy test folder** — Moved `test_migrate_frontmatter.py` to `tests/legacy/`
  - Migration tests are rarely needed but preserved for reuse

### Tests
- All 225 tests pass

---

## [2.7.0] - 2025-12-19

### Theme: "Documentation Staleness Tracking"

Track when documentation becomes outdated after code changes.

### Added
- **`describes` field** — Documents can declare which atoms they describe
  - Type constraint: only `atom` documents can be described
  - Circular reference detection prevents infinite loops
- **`describes_verified` field** — Date when document was last verified accurate
- **Staleness detection** — Compares verification date against atom modification dates
  - Uses git commit dates (reliable) with mtime fallback
  - In-memory caching for performance
- **Section 5: Documentation Staleness Audit** — New context map section
  - Shows stale docs with `[STALE]` prefix
  - Lists which atoms changed and when
- **`[STALE]` error flag** — Added to validation errors in Agent Instructions
- **`ontos_verify.py`** — Helper script to update `describes_verified` date
  - Single file: `ontos_verify.py <path>`
  - Interactive: `ontos_verify.py --all`
  - Backdating: `ontos_verify.py <path> --date 2025-12-01`
- **Staleness warning in Archive Ontos** — Warns about stale docs after archiving
- **Immutable history generation** — `decision_history.md` regenerated deterministically
  - Sorted by date (desc), event type (alpha), ID (alpha)
  - `--skip-history` flag to opt out of regeneration
  - GENERATED header indicates machine-managed file
- **Self-hosting** — `Ontos_Manual.md` now uses `describes` field

### Changed
- Renamed `get_git_last_modified_v27()` → `get_file_modification_date()`
- Fixed event type extraction in history (`event` → `event_type` field)
- Default event type changed from `log` to `chore`

### Tests
- 43 new v2.7 tests (`test_describes.py`, `test_immutable_history.py`)
- Fixed `test_lint_exceeds_retention_count` (was using wrong config variable)
- All 225 tests pass

---

## [2.6.2] - 2025-12-18

### Theme: "Count-Based Consolidation"

Simplifies log management with predictable count-based thresholds.

### Changed
- **Consolidation now count-based** — Keeps newest 10 logs (`LOG_RETENTION_COUNT`)
  - `--by-age` flag preserves legacy age-based behavior
  - `--count N` to customize retention count
- **Warning threshold separated** — Warns at 20 logs (`LOG_WARNING_THRESHOLD`)
  - Buffer of 10 sessions between warning and consolidation
  - No more "warning fatigue" after every session
- **Maintain Ontos help text** — Now shows all 4 steps (was missing Steps 3 and 4)

---

## [2.6.1] - 2025-12-18

### Theme: "Automated Graduation"

Smarter proposal graduation with detection and prompts—no new commands.

### Added
- **Archive Ontos graduation detection** — Detects implemented proposals on session end
  - Branch name matching (e.g., `feat/v2.6-*` matches v2.6 proposal)
  - Impact-based detection (if session impacts a proposal doc)
  - Prompts for graduation with automatic status update and ledger entry
- **Maintain Ontos proposal review** — Step 4 catches missed graduations
  - Lists draft proposals with version and age
  - Highlights proposals matching current ONTOS_VERSION
  - Interactive graduation prompt (skip in non-TTY mode)
- **`find_draft_proposals()` in ontos_lib** — Reusable proposal scanning

### Changed
- Updated Agent Instructions with graduation workflow documentation
- Updated Manual with automated vs manual graduation options

---

## [2.6.0] - 2025-12-17

### Theme: "Proposals Workflow & Validation"

Comprehensive proposal lifecycle with multi-model reviewed validation rules.

### Added
- **Status Validation System** — `VALID_STATUS` enum and type-status matrix
  - `status: rejected` for proposals that weren't approved
  - `status: complete` for finished reviews
  - Hard errors for invalid type-status combinations (e.g., `type: log, status: rejected`)
- **Rejection Metadata Enforcement** — Required fields for rejected proposals
  - `rejected_reason` (min 10 chars) mandatory for rejected docs
  - `rejected_date` recommended for temporal context
  - Location check: rejected proposals must be in `archive/proposals/`
- **Stale Proposal Detection** — 60-day threshold with mtime fallback
  - Warns on drafts older than `PROPOSAL_STALE_DAYS`
  - Uses git commit date or filesystem mtime
- **Approval Path Enforcement** — Graduate workflow validation
  - Warns if `status: active` doc is still in `proposals/`
  - Soft warning for graduated proposals not in decision history
- **Decision History Ledger Validation** — Deterministic matching
  - `rejected_slugs` and `approved_slugs` sets for reliable matching
  - Archive path matching with slug fallback
- **Inclusion Flags** — Historical recall options
  - `--include-rejected` shows rejected proposals in context map
  - `--include-archived` shows archived logs in context map
- **Status Indicator** — Tree display shows `[draft]`, `[rejected]`, `[deprecated]`
- **Version Release Reminder** — Contributor-mode changelog prompt
  - Multi-commit detection using `origin/branch..HEAD`
  - `Dual_Mode_Matrix.md` reminder when scripts modified
- **Comprehensive Tests** — 30 new v2.6 tests in `test_v26_validation.py`

### Changed
- `load_decision_history_entries()` returns deterministic structure with separate slug sets
- `schema.md` updated with new statuses and rejection metadata fields
- `event_type` enum in schema fixed to match config

### Fixed
- Orphan check now skips draft proposals (they're expected to be orphans until approved)

## [2.5.2] - 2025-12-17

### Theme: "Dual-Mode Remediation"

Fixes critical user-mode gaps discovered during v2.5.1 development.

### Added
- **Template Loading System** — `.ontos/templates/` directory with `templates.py` loader module
  - Centralizes starter file content (decision_history.md, Common_Concepts.md)
  - Prevents duplication between contributor and user modes
- **Nested Directory Structure** — Organized user docs layout
  - `docs/strategy/` — Strategic documents and decision history
  - `docs/strategy/proposals/` — Draft proposals (status: draft)
  - `docs/archive/logs/` — Archived session logs
  - `docs/archive/proposals/` — Rejected/completed proposals
  - `docs/reference/` — Reference documents (Common_Concepts.md)
- **Backward Compatibility Path Helpers** — `ontos_lib.py` functions with deprecation warnings
  - `get_decision_history_path()` — Falls back to flat structure
  - `get_concepts_path()` — Falls back to flat structure
  - `get_archive_logs_dir()` — Falls back to old archive location
  - `get_archive_proposals_dir()` — New in v2.5.2
  - `get_proposals_dir()` — Mode-aware proposals path
- **Dual-Mode Testing Infrastructure** — `--mode` flag in conftest.py
  - `pytest --mode=contributor` — Tests against `.ontos-internal/`
  - `pytest --mode=user` — Tests against `docs/` (simulates fresh install)
  - `mode_aware_project` fixture creates appropriate structure
- **Explicit Directory Assertions** — User mode fixture validates all expected directories

### Changed
- `ontos_init.py` — Now creates 8 directories and copies 2 starter files via template loader
- Tests now run in both modes in CI (149 tests × 2 modes)

### Fixed
- User mode silent failures — `ontos_init.py` now creates complete structure
- Path helper inconsistencies — All helpers now support both nested and flat layouts
- Missing starter files in user mode — Template loader ensures consistent content

## [2.5.1] - 2025-12-17

### Theme: "Proposals Architecture"

Architectural foundation for `/strategy/proposals/` staging area.

### Added
- **Proposals Directory** — `/strategy/proposals/` for draft strategy documents
- **`status: rejected`** — New status value for proposals that were considered but not approved
- **Rejection Recording** — Rejected proposals tracked in `decision_history.md` alongside approvals

### Changed
- **Status Field Evolution** — Clarified semantic meaning:
  - `draft` — Work in progress (potential future)
  - `active` — Approved, current truth (present)
  - `deprecated` — Was true, no longer (past truth)
  - `rejected` — Considered but not approved (never became truth)

### Technical
- Proposals are Space (Truth) with `status: draft`, not Time (History)
- Maintains clean dual ontology — proposals are pre-strategy, not a separate category
- Non-breaking: purely additive, existing workflows unchanged

## [2.5.0] - 2025-12-17

### Theme: "The Promises"

Clear, honest communication about what each mode delivers.

### Added
- **Mode Promises** — Redesigned setup flow showing clear promises for each mode
  - `automated`: "Zero friction — just works" (auto-archive, auto-consolidate)
  - `prompted`: "Keep me in the loop" (blocked push, consolidation reminders)
  - `advisory`: "Maximum flexibility" (warnings only)
- **Pre-commit hook** — Auto-consolidation for automated mode
- **`AUTO_CONSOLIDATE_ON_COMMIT`** — New config setting for pre-commit consolidation
- **Agent consolidation reminders** — Context map generation shows warning when logs exceed threshold
- **Hook conflict detection** — Detects Husky, pre-commit framework, and existing hooks

### Changed
- `ontos_init.py` — Visually distinct mode selection with promise messaging (ASCII-only)
- `ontos_init.py` — Now installs both pre-push and pre-commit hooks
- `MODE_PRESETS` — Added consolidation-on-commit settings per mode
- `Ontos_Agent_Instructions.md` — Updated activation flow with consolidation check
- `Ontos_Manual.md` — Updated mode table with promises and consolidation behavior

### Technical
- Pre-commit hook stages consolidated files automatically (explicit paths only)
- Consolidation never blocks commit (graceful degradation with try/except)
- CI environments detected and skipped automatically
- Rebase/cherry-pick operations detected and skipped
- Dual condition for consolidation: count > threshold AND old logs exist

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

## [2.2.0] - 2025-12-14

### Theme: "Data Quality"

### Added
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

---

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
