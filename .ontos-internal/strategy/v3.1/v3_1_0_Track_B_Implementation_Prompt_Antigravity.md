# Antigravity: Track B Implementation — Native Command Migration

**Project:** Ontos v3.1.0
**Track:** B
**Branch:** `feat/v3.1.0-track-b`
**Spec Reference:** v3.1.0 Implementation Spec v1.2, §4
**Author:** Chief Architect (Claude Opus 4.5)
**Date:** 2026-01-21

---

## Overview

Track B migrates 7 wrapper commands to native Python implementations, eliminating subprocess overhead and fixing broken positional argument handling.

**Critical constraint:** Output must be IDENTICAL to legacy scripts (§4.8 Behavioral Parity).

**Scope:**
- New/Modified files: 7 command modules
- Test files: 7 parity test files + golden fixtures
- Modified: `cli.py` (update registrations)

**Risk Level:** MEDIUM (behavioral parity is critical)

**Priority Order:**
1. CMD-1: `scaffold` (P0 - BROKEN)
2. CMD-2: `verify` (P0 - Limited)
3. CMD-3: `query` (P0 - Limited)
4. CMD-4: `consolidate` (P1)
5. CMD-5: `stub` (P1)
6. CMD-6: `promote` (P1)
7. CMD-7: `migrate` (P1)

---

## Prerequisites

**Ensure Track A is merged before starting:**
```bash
git checkout main
git pull origin main
git log --oneline -5  # Verify Track A merge commit present

# Create Track B branch
git checkout -b feat/v3.1.0-track-b
```

---

## Pre-Implementation: Capture Golden Fixtures

**BEFORE writing ANY code, capture legacy behavior as golden fixtures:**

```bash
mkdir -p tests/commands/golden

# Capture --help output for each command
python ontos/_scripts/ontos_scaffold.py --help > tests/commands/golden/scaffold_help.txt
python ontos/_scripts/ontos_verify.py --help > tests/commands/golden/verify_help.txt
python ontos/_scripts/ontos_query.py --help > tests/commands/golden/query_help.txt
python ontos/_scripts/ontos_consolidate.py --help > tests/commands/golden/consolidate_help.txt
python ontos/_scripts/ontos_stub.py --help > tests/commands/golden/stub_help.txt
python ontos/_scripts/ontos_promote.py --help > tests/commands/golden/promote_help.txt
python ontos/_scripts/ontos_migrate_schema.py --help > tests/commands/golden/migrate_help.txt

# Capture typical outputs (in test environment)
python ontos/_scripts/ontos_query.py --health > tests/commands/golden/query_health.txt
python ontos/_scripts/ontos_query.py --list-ids > tests/commands/golden/query_list_ids.txt
```

**Commit golden fixtures FIRST:**
```
test(golden): capture legacy command output fixtures
```

---

## Task B.1: CMD-1 `scaffold` Native Implementation (P0 - CRITICAL)

**Spec Reference:** §4.1
**Current State:** BROKEN (rejects positional arguments)
**Legacy script:** `ontos/_scripts/ontos_scaffold.py`

### Legacy Behavior Analysis

**Arguments:**
- `files` (positional, optional): Specific files to scaffold
- `--apply`: Apply scaffolding (required to modify files)
- `--dry-run`: Preview changes without applying (default)
- `--quiet, -q`: Minimal output

**Exit Codes:**
- `0`: Success or no files need scaffolding
- `1`: Error (no valid files, partial failures)

**Output Format:**
- Dry-run: Lists files with preview of scaffold frontmatter
- Apply: Success message per file, summary count
- Uses OutputHandler (success/error/info/detail)

### New File: `ontos/commands/scaffold.py`

```python
"""Native scaffold command implementation."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ontos.core.frontmatter import parse_frontmatter, create_scaffold
from ontos.io.files import find_markdown_files
from ontos.ui.output import OutputHandler


@dataclass
class ScaffoldOptions:
    """Options for scaffold command."""
    paths: List[Path] = None  # File(s) or directory to scaffold
    apply: bool = False
    dry_run: bool = True
    quiet: bool = False
    json_output: bool = False


def find_untagged_files(paths: Optional[List[Path]] = None) -> List[Path]:
    """Find markdown files without valid frontmatter.

    Args:
        paths: Specific files/directories, or None for default scan

    Returns:
        List of paths needing scaffolding
    """
    # Implementation: Use find_markdown_files(), filter by missing frontmatter
    # Respect .ontosignore patterns
    # Skip hidden directories except .ontos, .ontos-internal
    ...


def scaffold_file(path: Path, dry_run: bool = True) -> Tuple[bool, str]:
    """Add scaffold frontmatter to a file.

    Args:
        path: File to scaffold
        dry_run: If True, return preview without modifying

    Returns:
        (success, message) tuple
    """
    # Implementation: Read file, create_scaffold(), write if not dry_run
    ...


def scaffold_command(options: ScaffoldOptions) -> Tuple[int, str]:
    """Execute scaffold command.

    Args:
        options: Command options

    Returns:
        (exit_code, message) tuple
    """
    output = OutputHandler(quiet=options.quiet)

    # 1. Find untagged files
    untagged = find_untagged_files(options.paths)

    if not untagged:
        output.info("No files need scaffolding.")
        return 0, "No files need scaffolding"

    # 2. Process each file
    success_count = 0
    for path in untagged:
        if options.dry_run:
            # Show preview
            output.detail(f"Would scaffold: {path}")
            success_count += 1
        else:
            success, msg = scaffold_file(path, dry_run=False)
            if success:
                output.success(f"Scaffolded: {path}")
                success_count += 1
            else:
                output.error(f"Failed: {path} - {msg}")

    # 3. Summary
    if options.dry_run:
        output.info(f"Dry run: {success_count} files would be scaffolded")
    else:
        output.success(f"Scaffolded {success_count} files")

    return 0 if success_count > 0 else 1, f"Processed {success_count} files"
```

### CLI Registration Update (cli.py)

```python
def _register_scaffold(subparsers, parent):
    """Register scaffold command."""
    p = subparsers.add_parser(
        "scaffold",
        help="Add frontmatter to markdown files",
        parents=[parent]
    )
    p.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="File(s) or directory to scaffold (default: scan all)"
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help="Apply scaffolding (default: dry-run)"
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    p.set_defaults(func=_cmd_scaffold)


def _cmd_scaffold(args):
    """Handle scaffold command."""
    from ontos.commands.scaffold import ScaffoldOptions, scaffold_command

    options = ScaffoldOptions(
        paths=args.paths if args.paths else None,
        apply=args.apply,
        dry_run=not args.apply,  # Default to dry-run
        quiet=args.quiet,
        json_output=args.json,
    )
    exit_code, message = scaffold_command(options)
    return exit_code
```

### Parity Test: `tests/commands/test_scaffold_parity.py`

```python
"""Parity tests for scaffold command."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def golden_help():
    """Load golden help output."""
    golden_path = Path(__file__).parent / "golden" / "scaffold_help.txt"
    return golden_path.read_text()


def test_scaffold_help_parity(golden_help):
    """Native --help matches legacy."""
    result = subprocess.run(
        ["ontos", "scaffold", "--help"],
        capture_output=True,
        text=True
    )
    # Compare key elements (flags, descriptions)
    assert "--apply" in result.stdout
    assert "--dry-run" in result.stdout
    assert "frontmatter" in result.stdout.lower()


def test_scaffold_dry_run_parity(tmp_path):
    """Dry-run output matches legacy format."""
    # Create test file without frontmatter
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test\n\nContent here.")

    # Run native command
    result = subprocess.run(
        ["ontos", "scaffold", str(test_file), "--dry-run"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Would scaffold" in result.stdout or "would be scaffolded" in result.stdout
```

### Commit

```
feat(scaffold): native implementation with positional arg support

- Add ScaffoldOptions dataclass
- Implement find_untagged_files() and scaffold_file()
- Register native command in cli.py
- Support: positional paths, --apply, --dry-run, --quiet
- Exit codes: 0 (success), 1 (error)

Fixes: CMD-1 broken positional argument handling
Spec: §4.1
```

---

## Task B.2: CMD-2 `verify` Native Implementation (P0)

**Spec Reference:** §4.2
**Current State:** Limited (wrapper to legacy script)
**Legacy script:** `ontos/_scripts/ontos_verify.py`

### Legacy Behavior Analysis

**Arguments:**
- `filepath` (positional, optional): Path to document to verify
- `--all`: Interactively verify all stale documents
- `--date YYYY-MM-DD`: Set specific date (default: today)

**Exit Codes:**
- `0`: Success (or no changes needed)
- `1`: Error (file not found, invalid date, no frontmatter)

**Output Format:**
- Single file: Success message with date
- All mode: Interactive prompts showing stale documents
- Prompts: `[y/N]:`

### Enhance: `ontos/commands/verify.py`

```python
"""Native verify command implementation."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional, Tuple

from ontos.core.frontmatter import parse_frontmatter, update_frontmatter_field
from ontos.core.staleness import find_stale_documents, get_staleness_reason
from ontos.ui.output import OutputHandler


@dataclass
class VerifyOptions:
    """Options for verify command."""
    path: Optional[Path] = None
    all: bool = False
    date: Optional[str] = None  # YYYY-MM-DD format
    quiet: bool = False
    json_output: bool = False


def verify_document(path: Path, verify_date: str) -> Tuple[bool, str]:
    """Update describes_verified field in document.

    Args:
        path: Document path
        verify_date: ISO date string (YYYY-MM-DD)

    Returns:
        (success, message) tuple
    """
    # Read file, parse frontmatter
    # Update describes_verified field
    # Write back
    ...


def verify_all_interactive(verify_date: str, output: OutputHandler) -> int:
    """Interactively verify all stale documents.

    Args:
        verify_date: Date to set
        output: Output handler

    Returns:
        Number of documents verified
    """
    stale_docs = find_stale_documents()
    verified = 0

    for doc in stale_docs:
        reason = get_staleness_reason(doc)
        output.info(f"\n{doc.path}")
        output.detail(f"  Stale because: {reason}")

        response = input("Verify? [y/N]: ").strip().lower()
        if response == 'y':
            success, msg = verify_document(doc.path, verify_date)
            if success:
                output.success(f"  Verified: {doc.path}")
                verified += 1
            else:
                output.error(f"  Failed: {msg}")

    return verified


def verify_command(options: VerifyOptions) -> Tuple[int, str]:
    """Execute verify command."""
    output = OutputHandler(quiet=options.quiet)
    verify_date = options.date or date.today().isoformat()

    if options.path:
        # Single file mode
        success, msg = verify_document(options.path, verify_date)
        if success:
            output.success(f"Verified {options.path} as of {verify_date}")
            return 0, msg
        else:
            output.error(msg)
            return 1, msg

    elif options.all:
        # Interactive all mode
        count = verify_all_interactive(verify_date, output)
        output.info(f"\nVerified {count} documents")
        return 0, f"Verified {count} documents"

    else:
        output.error("Specify a file path or use --all")
        return 1, "No target specified"
```

### CLI Registration Update

```python
def _register_verify(subparsers, parent):
    """Register verify command."""
    p = subparsers.add_parser(
        "verify",
        help="Verify document describes dates",
        parents=[parent]
    )
    p.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="Specific file to verify"
    )
    p.add_argument(
        "--all", "-a",
        action="store_true",
        help="Verify all stale documents interactively"
    )
    p.add_argument(
        "--date", "-d",
        help="Verification date (YYYY-MM-DD, default: today)"
    )
    p.set_defaults(func=_cmd_verify)
```

### Commit

```
feat(verify): native implementation with positional path support

- Add VerifyOptions dataclass
- Implement verify_document() and verify_all_interactive()
- Support: positional path, --all, --date
- Interactive [y/N] prompts for --all mode

Spec: §4.2
```

---

## Task B.3: CMD-3 `query` Native Implementation (P0)

**Spec Reference:** §4.3
**Current State:** Limited (wrapper)
**Legacy script:** `ontos/_scripts/ontos_query.py`

### Legacy Behavior Analysis

**Arguments (mutually exclusive):**
- `--depends-on ID`: What does this document depend on?
- `--depended-by ID`: What documents depend on this one?
- `--concept TAG`: Find all documents with this concept
- `--stale DAYS`: Find documents not updated in N days
- `--health`: Show graph health metrics
- `--list-ids`: List all document IDs
- `--dir DIR`: Documentation directory

**Exit Codes:**
- `0`: Success
- `1`: Error (no documents found)

**Output Format:**
- Depends-on/depended-by: `→ doc_id` or `← doc_id`
- Concept: `• doc_id`
- Stale: `doc_id (N days)`
- Health: Formatted metrics report
- List-ids: `doc_id (type)`

### New File: `ontos/commands/query.py`

```python
"""Native query command implementation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from ontos.core.graph import build_document_graph, get_dependencies, get_dependents
from ontos.core.staleness import find_stale_documents
from ontos.ui.output import OutputHandler


@dataclass
class QueryOptions:
    """Options for query command."""
    depends_on: Optional[str] = None
    depended_by: Optional[str] = None
    concept: Optional[str] = None
    stale: Optional[int] = None
    health: bool = False
    list_ids: bool = False
    dir: Optional[Path] = None
    quiet: bool = False
    json_output: bool = False


def query_depends_on(doc_id: str, output: OutputHandler) -> int:
    """Show dependencies of a document."""
    deps = get_dependencies(doc_id)
    if not deps:
        output.warning(f"No dependencies for {doc_id}")
        return 0

    for dep in deps:
        output.plain(f"→ {dep}")
    return 0


def query_depended_by(doc_id: str, output: OutputHandler) -> int:
    """Show documents that depend on this one."""
    dependents = get_dependents(doc_id)
    if not dependents:
        output.warning(f"No documents depend on {doc_id}")
        return 0

    for dep in dependents:
        output.plain(f"← {dep}")
    return 0


def query_concept(tag: str, output: OutputHandler) -> int:
    """Find documents with a concept tag."""
    docs = find_documents_by_concept(tag)
    if not docs:
        output.warning(f"No documents with concept: {tag}")
        return 1

    for doc in docs:
        output.plain(f"• {doc.id}")
    return 0


def query_stale(days: int, output: OutputHandler) -> int:
    """Find stale documents."""
    stale = find_stale_documents(threshold_days=days)
    if not stale:
        output.info(f"No documents older than {days} days")
        return 0

    for doc in stale:
        output.plain(f"{doc.id} ({doc.age_days} days)")
    return 0


def query_health(output: OutputHandler) -> int:
    """Show graph health metrics."""
    graph = build_document_graph()

    output.info("Document Graph Health")
    output.plain(f"  Total documents: {graph.total_docs}")
    output.plain(f"  Connectivity: {graph.connectivity_pct:.1f}%")
    output.plain(f"  Orphan documents: {len(graph.orphans)}")
    output.plain(f"  Logs with empty impacts: {len(graph.empty_impact_logs)}")

    if graph.orphans:
        output.warning("\nOrphan documents:")
        for orphan in graph.orphans:
            output.plain(f"  • {orphan}")

    return 0


def query_list_ids(output: OutputHandler) -> int:
    """List all document IDs."""
    docs = get_all_documents()
    for doc in sorted(docs, key=lambda d: d.id):
        output.plain(f"{doc.id} ({doc.type})")
    return 0


def query_command(options: QueryOptions) -> Tuple[int, str]:
    """Execute query command."""
    output = OutputHandler(quiet=options.quiet)

    if options.depends_on:
        return query_depends_on(options.depends_on, output), ""
    elif options.depended_by:
        return query_depended_by(options.depended_by, output), ""
    elif options.concept:
        return query_concept(options.concept, output), ""
    elif options.stale is not None:
        return query_stale(options.stale, output), ""
    elif options.health:
        return query_health(output), ""
    elif options.list_ids:
        return query_list_ids(output), ""
    else:
        output.error("Specify a query option (--depends-on, --depended-by, --concept, --stale, --health, --list-ids)")
        return 1, "No query specified"
```

### Commit

```
feat(query): native implementation with all query modes

- Add QueryOptions dataclass
- Implement: depends-on, depended-by, concept, stale, health, list-ids
- Output format matches legacy (arrows, bullets, parentheses)

Spec: §4.3
```

---

## Task B.4: CMD-4 `consolidate` Native Implementation (P1)

**Spec Reference:** §4.4
**Legacy script:** `ontos/_scripts/ontos_consolidate.py`

### Legacy Behavior

**Arguments:**
- `--count N`: Number of newest logs to keep (default: 15)
- `--by-age`: Use age-based threshold
- `--days N`: Age threshold in days (default: 30)
- `--dry-run, -n`: Preview without changes
- `--quiet, -q`: Suppress output
- `--all, -a`: Process all logs without prompting

**Exit Codes:**
- `0`: Success
- `1`: Error (missing decision_history.md)

**Output:**
- Interactive: Shows log details, prompts `[y/N/edit]:`
- Dry-run: `[DRY RUN] Would archive to: ...`
- Summary count

### Implementation Approach

Extract logic from `ontos/_scripts/ontos_consolidate.py`:
- `find_old_logs()` - Count-based or age-based threshold
- `extract_summary()` - Get one-line summary from Goal section
- `archive_log()` - Move log, append to decision_history.md
- `consolidate_command()` - Main entry point

### Commit

```
feat(consolidate): native implementation

- Add ConsolidateOptions dataclass
- Support: --count, --by-age, --days, --dry-run, --all
- Interactive [y/N/edit] prompts
- Append to History Ledger table in decision_history.md

Spec: §4.4
```

---

## Task B.5: CMD-5 `stub` Native Implementation (P1)

**Spec Reference:** §4.5
**Legacy script:** `ontos/_scripts/ontos_stub.py`

### Legacy Behavior

**Arguments:**
- `--goal, -g TEXT`: Goal description
- `--type, -t TYPE`: Document type (kernel, strategy, product, atom, log)
- `--id ID`: Document ID
- `--output, -o PATH`: Output file path
- `--depends-on, -d IDS`: Comma-separated dependencies
- `--quiet, -q`: Minimal output

**Exit Codes:**
- `0`: Success
- `1`: Error (cancellation, missing fields, invalid type)

**Output:**
- Interactive prompts for missing fields
- File write success message
- Stdout mode: formatted stub between dashed lines

### Implementation Approach

Extract from `ontos/_scripts/ontos_stub.py`:
- `create_stub()` - Generate Level 1 stub content
- Interactive prompts for ID, type, goal, depends_on, output
- Write to file or stdout

### Commit

```
feat(stub): native implementation

- Add StubOptions dataclass
- Interactive mode when --goal or --type not provided
- Support: --id, --output, --depends-on
- Generate Level 1 stub with Goal/Content sections

Spec: §4.5
```

---

## Task B.6: CMD-6 `promote` Native Implementation (P1)

**Spec Reference:** §4.6
**Legacy script:** `ontos/_scripts/ontos_promote.py`

### Legacy Behavior

**Arguments:**
- `files` (positional, optional): Specific files to promote
- `--check`: Show promotable documents without changing
- `--all-ready`: Batch promote all ready documents
- `--quiet, -q`: Minimal output

**Exit Codes:**
- `0`: Success
- `1`: Error or partial failures

**Output:**
- Check mode: Lists with status (✓ ready, ○ needs work)
- Interactive: Prompts for depends_on, concepts, `[Y/n]:`
- Level markers: [L0], [L1], [L2]

### Implementation Approach

Extract from `ontos/_scripts/ontos_promote.py`:
- `find_promotable()` - Find L0/L1 documents
- `get_promotion_blockers()` - What's missing for promotion
- `promote_document()` - Update frontmatter to L2
- Fuzzy ID matching for depends_on prompts

### Commit

```
feat(promote): native implementation with fuzzy ID matching

- Add PromoteOptions dataclass
- Support: positional paths, --check, --all-ready
- Interactive depends_on/concepts prompts
- Fuzzy ID matching (prefix, substring)

Spec: §4.6
```

---

## Task B.7: CMD-7 `migrate` Native Implementation (P1)

**Spec Reference:** §4.7
**Legacy script:** `ontos/_scripts/ontos_migrate_schema.py`

### Legacy Behavior

**Arguments (mutually exclusive):**
- `--check`: Check which files need migration
- `--dry-run`: Preview changes
- `--apply`: Apply migrations
- `--dirs DIR [DIR ...]`: Directories to scan
- `--quiet, -q`: Reduce output

**Exit Codes:**
- `0`: Success (no migrations needed or completed)
- `1`: Migrations needed (check) or errors (apply/dry-run)

**Output:**
- Check: Summary with counts, file list with target schema
- Dry-run: Files that would be migrated
- Apply: Success per file, summary statistics

### Implementation Approach

Extract from `ontos/_scripts/ontos_migrate_schema.py`:
- `detect_schema_version()` - Infer from existing fields
- `add_schema_to_frontmatter()` - Add ontos_schema field
- Different exit codes for check vs apply modes

### Commit

```
feat(migrate): native schema migration

- Add MigrateOptions dataclass
- Support: --check, --dry-run, --apply, --dirs
- Detect schema version from existing fields
- Add ontos_schema field to frontmatter

Spec: §4.7
```

---

## Test Strategy

### Golden Fixture Tests

For each command, create parity tests in `tests/commands/`:

```
tests/commands/
  golden/
    scaffold_help.txt
    verify_help.txt
    query_help.txt
    query_health.txt
    query_list_ids.txt
    consolidate_help.txt
    stub_help.txt
    promote_help.txt
    migrate_help.txt
  test_scaffold_parity.py
  test_verify_parity.py
  test_query_parity.py
  test_consolidate_parity.py
  test_stub_parity.py
  test_promote_parity.py
  test_migrate_parity.py
```

### Parity Verification

Each parity test should:
1. Compare --help output structure
2. Compare typical command output format
3. Verify exit codes match legacy behavior

```bash
# Run all parity tests
pytest tests/commands/test_*_parity.py -v
```

---

## PR Preparation

**Branch:** `feat/v3.1.0-track-b`

**PR Title:** `feat: Track B — Native command migration`

**Expected Commits:**
1. `test(golden): capture legacy command output fixtures`
2. `feat(scaffold): native implementation with positional arg support`
3. `feat(verify): native implementation with positional path support`
4. `feat(query): native implementation with all query modes`
5. `feat(consolidate): native implementation`
6. `feat(stub): native implementation`
7. `feat(promote): native implementation with fuzzy ID matching`
8. `feat(migrate): native schema migration`

**PR Description Template:**
```markdown
## Summary

Track B migrates 7 wrapper commands to native Python implementations:

- **CMD-1 scaffold**: Fixed broken positional argument handling
- **CMD-2 verify**: Added positional path support
- **CMD-3 query**: Native with all query modes
- **CMD-4 consolidate**: Native log consolidation
- **CMD-5 stub**: Native stub creation
- **CMD-6 promote**: Native with fuzzy ID matching
- **CMD-7 migrate**: Native schema migration

## Test Plan

- [ ] All existing tests pass (449+)
- [ ] Golden fixture parity tests pass
- [ ] Smoke tests: `ontos scaffold docs/ --dry-run`
- [ ] Smoke tests: `ontos verify --all`
- [ ] Smoke tests: `ontos query --health`
- [ ] Exit codes match legacy behavior

## Spec Reference

v3.1.0 Implementation Spec v1.2, §4
```

---

## Critical Reminders

1. **Golden fixtures FIRST** — Capture before any code changes
2. **Parity is non-negotiable** — If output differs, fix native implementation
3. **Extract, don't rewrite** — Legacy scripts work; extract their logic
4. **CMD-1 (scaffold) is highest priority** — Currently broken
5. **Test each command before moving to next**
6. **Exit codes must match** — 0=success, 1=error, 2=abort

---

## CA Guidance from Spec

Per v3.1.0 Final Decision:

**Scaffold collision handling:**
- Skip files with existing frontmatter
- No auto-suffix for ID collisions; warn and skip

**Interactive prompts:**
- Use `[y/N]:` format (default No)
- Use `[Y/n]:` when default is Yes

---

## Verification

After completing all tasks:

```bash
# Full test suite
pytest tests/ -v

# Parity tests specifically
pytest tests/commands/test_*_parity.py -v

# Smoke tests
ontos scaffold docs/ --dry-run
ontos verify --all
ontos query --health
ontos query --list-ids
ontos consolidate --dry-run
ontos stub --help
ontos promote --check
ontos migrate --check
```

---

*Phase C.1b — Antigravity Implementation Prompt*
*Chief Architect (Claude Opus 4.5) — 2026-01-21*
