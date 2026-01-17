---
id: phase2_godscript_reduction_instructions_antigravity
type: strategy
status: active
depends_on: [phase2_implementation_instructions_antigravity]
---

# Ontos v3.0 Phase 2: God Script Reduction — REQUIRED

**Date:** 2026-01-12
**Author:** Chief Architect (Claude Opus 4.5)
**Status:** BLOCKING MERGE
**PR:** #41

---

## CRITICAL: Read This First

### Chief Architect Made an Error

I (Chief Architect) incorrectly approved PR #41 on 2026-01-12 when it did not meet the Phase 2 exit criteria. This approval has been **revoked**.

**You MUST read the following PR comments:**

1. **Original Approval (REVOKED):** https://github.com/ohjona/Project-Ontos/pull/41#issuecomment-3740955171
2. **Approval Revocation:** https://github.com/ohjona/Project-Ontos/pull/41#issuecomment-3741389186

### Why Approval Was Revoked

The Phase 2 Implementation Spec v1.2 clearly states:

> **Exit Criteria:**
> - [ ] God Scripts < 200 lines each

**Current State:**
| Script | Current Lines | Required | Gap |
|--------|---------------|----------|-----|
| `ontos_end_session.py` | 1,911 | <200 | **1,711 lines over** |
| `ontos_generate_context_map.py` | 1,264 | <200 | **1,064 lines over** |

**The modules exist but are NOT USED.** This is unacceptable.

---

## What You Did vs What Was Required

### What You Did (Incomplete)

1. ✅ Created 11 new modules in `core/`, `io/`, `commands/`
2. ✅ Fixed subprocess violations in `core/staleness.py` and `core/config.py`
3. ✅ Golden Master passes (16/16)
4. ❌ **God Scripts still 3,175 lines total**
5. ❌ **`commands/map.py` is NOT imported by `ontos_generate_context_map.py`**
6. ❌ **`commands/log.py` is NOT imported by `ontos_end_session.py`**

### What Was Required (Spec v1.2)

> "Reduce God Scripts to <200 lines each (argparse + deprecation only)"

The new modules were supposed to **replace** the logic in God Scripts, not exist alongside it.

---

## Pre-Implementation Checklist

Before starting, verify your environment:

```bash
# 1. Correct directory
pwd
# Expected: /Users/jonathanoh/Dev/Project-Ontos

# 2. Correct branch
git branch --show-current
# Expected: Phase2_V3.0_beta

# 3. Clean git status
git status
# Expected: Clean working directory

# 4. Current line counts (THE PROBLEM)
wc -l ontos/_scripts/ontos_end_session.py ontos/_scripts/ontos_generate_context_map.py
# Current: 1911 + 1264 = 3175 lines
# Required: <200 + <200 = <400 lines

# 5. Golden Master baseline
python3 tests/golden/compare_golden_master.py --fixture all
# Expected: 16/16 PASS (must stay this way)

# 6. Unit tests baseline
python3 -m pytest tests/ -q
# Expected: 303 passed
```

---

## Task 1: Reduce `ontos_generate_context_map.py` (1,264 → <200 lines)

### 1.1 Current Problem

The script contains 1,264 lines of logic that should now live in:
- `ontos/core/tokens.py` — Token estimation (DONE, already imported)
- `ontos/core/graph.py` — Dependency graph building
- `ontos/core/validation.py` — ValidationOrchestrator
- `ontos/io/files.py` — Document scanning and loading
- `ontos/io/yaml.py` — YAML parsing
- `ontos/commands/map.py` — Orchestration

**But `commands/map.py` is NOT USED.** The God Script still has its own implementation.

### 1.2 Lines to DELETE

| Line Range | Content | Replacement |
|------------|---------|-------------|
| 71-102 | Token estimation functions | Already in `core/tokens.py` ✅ |
| 103-250 | `scan_docs()` function | Use `io/files.scan_documents()` |
| 251-400 | `parse_frontmatter()` usage | Use `io/files.load_document()` |
| 401-560 | `validate_dependencies()` | Use `core/validation.ValidationOrchestrator` |
| 561-700 | `build_dependency_graph()` | Use `core/graph.build_graph()` |
| 701-850 | `detect_cycles()` | Use `core/graph.detect_cycles()` |
| 851-922 | `generate_tree()` | Use `commands/map._generate_dependency_tree()` |
| 925-1126 | `generate_context_map()` orchestration | Use `commands/map.generate_context_map()` |

### 1.3 Required Final Code

Replace the entire file with this:

```python
#!/usr/bin/env python3
"""
Generate Ontos Context Map.

DEPRECATED: This script is a compatibility wrapper.
Use `ontos map` or `python -m ontos.commands.map` instead.

Phase 2 v3.0: Reduced to <200 lines per spec requirement.
"""

import argparse
import sys
import warnings
from pathlib import Path

# === DEPRECATION WARNING ===
warnings.warn(
    "ontos_generate_context_map.py is deprecated. Use `ontos map` instead.",
    DeprecationWarning,
    stacklevel=2
)

# === IMPORTS FROM NEW MODULES ===
from ontos.io.files import scan_documents, load_document
from ontos.io.yaml import parse_yaml
from ontos.core.validation import ValidationOrchestrator
from ontos.core.tokens import estimate_tokens, format_token_count
from ontos.commands.map import generate_context_map, GenerateMapOptions

# === LEGACY CONFIG IMPORTS (Phase 3 will move to .ontos.toml) ===
from ontos_config import (
    __version__,
    DOCS_DIR,
    CONTEXT_MAP_FILE,
    SKIP_PATTERNS,
    MAX_DEPENDENCY_DEPTH,
    ALLOWED_ORPHAN_TYPES,
)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Ontos Context Map",
        epilog="DEPRECATED: Use `ontos map` instead."
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path(CONTEXT_MAP_FILE),
        help="Output file path"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error on validation warnings"
    )
    parser.add_argument(
        "--no-staleness",
        action="store_true",
        help="Skip staleness detection"
    )
    parser.add_argument(
        "--no-timeline",
        action="store_true",
        help="Skip timeline section"
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Include lint warnings"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without writing"
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"ontos {__version__}"
    )

    args = parser.parse_args()

    # --- Step 1: Scan and load documents ---
    print(f"Scanning {DOCS_DIR}...")
    docs = {}
    doc_paths = list(scan_documents([Path(DOCS_DIR)], SKIP_PATTERNS))

    for path in doc_paths:
        try:
            doc = load_document(path, parse_yaml)
            docs[doc.id] = doc
        except Exception as e:
            print(f"  Warning: Failed to load {path}: {e}", file=sys.stderr)

    print(f"  Found {len(docs)} documents")

    # --- Step 2: Configure generation options ---
    options = GenerateMapOptions(
        output_path=args.output,
        strict=args.strict,
        include_staleness=not args.no_staleness,
        include_timeline=not args.no_timeline,
        include_lint=args.lint,
        max_dependency_depth=MAX_DEPENDENCY_DEPTH,
        dry_run=args.dry_run,
    )

    config = {
        "project_name": "Ontos",
        "allowed_orphan_types": ALLOWED_ORPHAN_TYPES,
        "version": __version__,
    }

    # --- Step 3: Generate context map ---
    print("Generating context map...")
    content, result = generate_context_map(docs, config, options)

    # --- Step 4: Report validation results ---
    if result.errors:
        print(f"\nErrors ({len(result.errors)}):", file=sys.stderr)
        for error in result.errors:
            print(f"  - {error.doc_id}: {error.message}", file=sys.stderr)

    if result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  - {warning.doc_id}: {warning.message}")

    # --- Step 5: Write output ---
    if args.dry_run:
        print("\n--- DRY RUN (not writing) ---")
        print(f"Would write {len(content)} bytes to {args.output}")
        token_count = estimate_tokens(content)
        print(f"Token estimate: {format_token_count(token_count)}")
    else:
        args.output.write_text(content, encoding="utf-8")
        print(f"\nGenerated: {args.output}")
        token_count = estimate_tokens(content)
        print(f"Token estimate: {format_token_count(token_count)}")

    # --- Step 6: Exit code ---
    if result.errors:
        return 1
    if args.strict and result.warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Line count: ~140 lines** ✅

### 1.4 Verification After Task 1

```bash
# Check line count
wc -l ontos/_scripts/ontos_generate_context_map.py
# Expected: <200

# Run Golden Master
python3 tests/golden/compare_golden_master.py --fixture all
# Expected: 16/16 PASS

# If Golden Master FAILS, you need to add missing functionality to commands/map.py
# Do NOT revert to keeping logic in the God Script
```

---

## Task 2: Reduce `ontos_end_session.py` (1,911 → <200 lines)

### 2.1 Current Problem

The script contains 1,911 lines of logic that should now live in:
- `ontos/io/git.py` — Git operations (partially imported but aliased as `_git_*` and NOT USED)
- `ontos/core/suggestions.py` — Impact suggestions
- `ontos/commands/log.py` — Session log orchestration

**But `commands/log.py` is NOT USED.** The God Script still has its own implementation.

### 2.2 Lines to DELETE

| Line Range | Content | Replacement |
|------------|---------|-------------|
| 46-150 | `detect_implemented_proposal()` | Move to `commands/log.py` if needed |
| 151-302 | `graduate_proposal()` | Move to `commands/log.py` if needed |
| 304-500 | Session appending logic | Move to `commands/log.py` |
| 501-773 | More session logic | Move to `commands/log.py` |
| 849-1000 | Validation functions | Use `core/validation.py` |
| 1001-1200 | Git operations | Use `io/git.py` (ALREADY EXISTS) |
| 1201-1400 | Impact suggestion | Use `core/suggestions.py` (ALREADY EXISTS) |
| 1401-1605 | Log creation | Use `commands/log.py` (ALREADY EXISTS) |

### 2.3 Required Final Code

Replace the entire file with this:

```python
#!/usr/bin/env python3
"""
End Session and Create Log.

DEPRECATED: This script is a compatibility wrapper.
Use `ontos log` or `python -m ontos.commands.log` instead.

Phase 2 v3.0: Reduced to <200 lines per spec requirement.
"""

import argparse
import sys
import warnings
from pathlib import Path

# === DEPRECATION WARNING ===
warnings.warn(
    "ontos_end_session.py is deprecated. Use `ontos log` instead.",
    DeprecationWarning,
    stacklevel=2
)

# === IMPORTS FROM NEW MODULES ===
from ontos.io.git import (
    get_current_branch,
    get_commits_since_push,
    get_changed_files_since_push,
)
from ontos.commands.log import (
    create_session_log,
    suggest_session_impacts,
    validate_session_concepts,
    EndSessionOptions,
)

# === LEGACY CONFIG IMPORTS (Phase 3 will move to .ontos.toml) ===
from ontos_config import (
    __version__,
    PROJECT_ROOT,
    CONTEXT_MAP_FILE,
)

# Try to get default source
try:
    from ontos_config import DEFAULT_SOURCE
except ImportError:
    DEFAULT_SOURCE = None


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create session log",
        epilog="DEPRECATED: Use `ontos log` instead."
    )
    parser.add_argument(
        "--event-type", "-e",
        default="chore",
        choices=["feat", "fix", "chore", "docs", "refactor", "test", "perf"],
        help="Event type (default: chore)"
    )
    parser.add_argument(
        "--topic", "-t",
        help="Session topic (auto-generated if not provided)"
    )
    parser.add_argument(
        "--source", "-s",
        default=DEFAULT_SOURCE,
        help="Author/source identifier"
    )
    parser.add_argument(
        "--concepts", "-c",
        nargs="*",
        default=[],
        help="Concepts to tag"
    )
    parser.add_argument(
        "--impacts", "-i",
        nargs="*",
        default=[],
        help="Impact doc IDs (auto-suggested if not provided)"
    )
    parser.add_argument(
        "--auto", "-a",
        action="store_true",
        help="Auto mode (no prompts)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without writing"
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"ontos {__version__}"
    )

    args = parser.parse_args()

    project_root = Path(PROJECT_ROOT)
    context_map_path = project_root / CONTEXT_MAP_FILE

    # --- Step 1: Gather git information ---
    print("Gathering git information...")
    branch = get_current_branch() or "unknown"
    commits = get_commits_since_push()
    changed_files = get_changed_files_since_push()

    print(f"  Branch: {branch}")
    print(f"  Commits since push: {len(commits)}")
    print(f"  Files changed: {len(changed_files)}")

    git_info = {
        "branch": branch,
        "commits": commits,
        "changed_files": changed_files,
    }

    # --- Step 2: Get or prompt for source ---
    source = args.source
    if not source and not args.auto:
        source = input("Source (author): ").strip()
    source = source or "unknown"

    # --- Step 3: Get or prompt for topic ---
    topic = args.topic
    if not topic and not args.auto:
        suggested = commits[0][:50] if commits else "session"
        topic = input(f"Topic [{suggested}]: ").strip() or suggested

    # --- Step 4: Suggest impacts if not provided ---
    impacts = list(args.impacts)
    if not impacts:
        print("Suggesting impacts...")
        impacts = suggest_session_impacts(context_map_path, changed_files, commits)
        if impacts:
            print(f"  Suggested: {', '.join(impacts[:5])}")

    # --- Step 5: Validate concepts ---
    concepts = list(args.concepts)
    if concepts:
        valid, unknown = validate_session_concepts(context_map_path, concepts)
        if unknown:
            print(f"  Warning: Unknown concepts: {', '.join(unknown)}")

    # --- Step 6: Create session log ---
    options = EndSessionOptions(
        event_type=args.event_type,
        topic=topic,
        source=source,
        concepts=concepts,
        impacts=impacts,
        branch=branch,
        dry_run=args.dry_run,
    )

    content, output_path = create_session_log(project_root, options, git_info)

    # --- Step 7: Output ---
    if args.dry_run:
        print("\n--- DRY RUN (not writing) ---")
        print(content)
        print(f"\nWould write to: {output_path}")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"\nCreated: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Line count: ~150 lines** ✅

### 2.4 Verification After Task 2

```bash
# Check line count
wc -l ontos/_scripts/ontos_end_session.py
# Expected: <200

# Run Golden Master
python3 tests/golden/compare_golden_master.py --fixture all
# Expected: 16/16 PASS

# If Golden Master FAILS, you need to add missing functionality to commands/log.py
# Do NOT revert to keeping logic in the God Script
```

---

## Task 3: Extend `commands/map.py` If Needed

If Golden Master fails after Task 1, the `commands/map.py` module is missing functionality.

### 3.1 Check What's Missing

Compare the output of the old vs new implementation:

```bash
# Generate with OLD script (before your changes)
git stash
python3 ontos/_scripts/ontos_generate_context_map.py --output /tmp/old_map.md

# Generate with NEW script (after your changes)
git stash pop
python3 ontos/_scripts/ontos_generate_context_map.py --output /tmp/new_map.md

# Diff
diff /tmp/old_map.md /tmp/new_map.md
```

### 3.2 Add Missing Functionality

Whatever is different, add to `commands/map.py`. Common things that might be missing:

- Lint warnings section
- Staleness detection integration
- Timeline formatting
- Token count display
- Specific validation rules

**The logic goes in `commands/map.py`, NOT in the God Script.**

---

## Task 4: Extend `commands/log.py` If Needed

If Golden Master fails after Task 2, the `commands/log.py` module is missing functionality.

### 4.1 Check What's Missing

```bash
# Create log with OLD script (before your changes)
git stash
python3 ontos/_scripts/ontos_end_session.py --auto --dry-run > /tmp/old_log.txt

# Create log with NEW script (after your changes)
git stash pop
python3 ontos/_scripts/ontos_end_session.py --auto --dry-run > /tmp/new_log.txt

# Diff
diff /tmp/old_log.txt /tmp/new_log.txt
```

### 4.2 Add Missing Functionality

Whatever is different, add to `commands/log.py`. Common things that might be missing:

- Proposal detection and graduation
- Decision history updates
- Specific frontmatter fields
- Interactive prompts handling

**The logic goes in `commands/log.py`, NOT in the God Script.**

---

## Task 5: Final Verification

### 5.1 Line Count Check (REQUIRED)

```bash
wc -l ontos/_scripts/ontos_end_session.py ontos/_scripts/ontos_generate_context_map.py
```

**Required Output:**
```
  <200 ontos/_scripts/ontos_end_session.py
  <200 ontos/_scripts/ontos_generate_context_map.py
  <400 total
```

### 5.2 Golden Master (REQUIRED)

```bash
python3 tests/golden/compare_golden_master.py --fixture all
```

**Required Output:**
```
All comparisons PASSED
```

### 5.3 Unit Tests (REQUIRED)

```bash
python3 -m pytest tests/ -q
```

**Required Output:**
```
303 passed
```

### 5.4 Import Verification (REQUIRED)

```bash
# Verify God Scripts import from new modules
grep "from ontos.commands.map import" ontos/_scripts/ontos_generate_context_map.py
# Expected: Match found

grep "from ontos.commands.log import" ontos/_scripts/ontos_end_session.py
# Expected: Match found
```

---

## Acceptance Criteria (Non-Negotiable)

| Criterion | Required | Verification |
|-----------|----------|--------------|
| `ontos_generate_context_map.py` | **< 200 lines** | `wc -l` |
| `ontos_end_session.py` | **< 200 lines** | `wc -l` |
| Imports `commands/map.py` | **YES** | `grep` |
| Imports `commands/log.py` | **YES** | `grep` |
| Golden Master | **16/16 PASS** | Test script |
| Unit Tests | **303+ PASS** | pytest |

---

## What Is NOT Acceptable

| Excuse | Why It's Invalid |
|--------|------------------|
| "Risk to behavioral parity" | Golden Master tests exist precisely for this |
| "We'll do it in Phase 4" | The spec says Phase 2. This IS Phase 2. |
| "The modules exist, that's enough" | They must be USED, not just exist |
| "It's too much work" | The code is provided in this document |

---

## Commit Message Template

After completing all tasks:

```
refactor(Phase2): reduce God Scripts to <200 lines each

BREAKING CHANGE: God Scripts are now thin wrappers.

- ontos_generate_context_map.py: 1,264 → ~140 lines
- ontos_end_session.py: 1,911 → ~150 lines
- Logic moved to commands/map.py and commands/log.py
- Golden Master: 16/16 PASS
- Unit Tests: 303/303 PASS

Closes Phase 2 spec requirement for God Script reduction.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

## Timeline

**This is BLOCKING MERGE.**

Phase 2 is NOT complete until this work is done. There is no Phase 3 until Phase 2 exit criteria are met.

---

## Summary

1. **Read the PR comments** — Understand why approval was revoked
2. **Replace `ontos_generate_context_map.py`** — Use the code provided in Task 1
3. **Replace `ontos_end_session.py`** — Use the code provided in Task 2
4. **Extend `commands/` modules if needed** — Make Golden Master pass
5. **Verify all acceptance criteria** — Line counts, tests, imports
6. **Commit and push** — Use the provided commit message template

**The spec is the spec. This is not optional.**

---

*Prepared by: Chief Architect (Claude Opus 4.5)*
*Date: 2026-01-12*
*Status: REQUIRED — Blocking Merge*
