---
id: phase0_golden_master_spec
type: strategy
status: active
depends_on: [v3_0_implementation_roadmap, v3_0_technical_architecture]
---

# Phase 0 Implementation Spec: Golden Master Testing

**Version:** 1.1
**Date:** 2026-01-12
**Author:** Claude Opus 4.5 (Chief Architect)
**Status:** Active (Post-LLM Review Board)

**References:**
- `V3.0-Implementation-Roadmap.md` v1.2, Section 2
- `V3.0-Technical-Architecture.md` v1.4

**Revision History:**
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-12 | Initial spec |
| 1.1 | 2026-01-12 | LLM Review Board feedback: Added stderr/session_log comparison, `__init__.py`, git user config, `decision_history.md` handling, medium fixture templates |

---

## 1. Overview

### 1.1 Purpose

Create a safety net before decomposing the God Scripts (`ontos_end_session.py` at 1,904 lines and `ontos_generate_context_map.py` at 1,295 lines). Golden Master tests capture v2.9.x behavior exactly, enabling confident refactoring in Phase 2.

### 1.2 Scope

| In Scope | Out of Scope |
|----------|--------------|
| Capture scripts for `ontos map` and `ontos log` | Capture for MCP/daemon features |
| Three fixture sizes (small, medium, large) | Performance benchmarking |
| Comparison harness with normalization | UI/UX changes |
| CI integration with GitHub Actions | Windows testing (best-effort) |
| Baseline documentation | Database/external service mocking |

### 1.3 Exit Criteria

From Roadmap Section 2.3:
- [ ] All three fixture sizes created
- [ ] Capture script successfully records v2.9.x behavior
- [ ] Comparison harness runs and reports clean on v2.9.x
- [ ] Baseline documentation complete
- [ ] CI integration configured

---

## 2. Fixture Design

### 2.1 Directory Structure

```
tests/
├── golden/
│   ├── __init__.py          # Required for Python imports (v1.1)
│   ├── fixtures/
│   │   ├── small/           # 5-doc project
│   │   │   ├── .ontos-internal/
│   │   │   │   ├── kernel/
│   │   │   │   │   └── mission.md
│   │   │   │   ├── strategy/
│   │   │   │   │   └── project_plan.md
│   │   │   │   ├── atom/
│   │   │   │   │   └── schema.md
│   │   │   │   └── logs/
│   │   │   │       └── 2025-01-01_initial-setup.md
│   │   │   └── .ontos.toml
│   │   ├── medium/          # 25-doc project
│   │   │   └── ...
│   │   └── large/           # 100+ doc project
│   │       └── ...
│   ├── baselines/
│   │   ├── small/
│   │   │   ├── map_stdout.txt
│   │   │   ├── map_stderr.txt
│   │   │   ├── map_exit_code.txt
│   │   │   ├── context_map.md
│   │   │   ├── log_stdout.txt
│   │   │   ├── log_stderr.txt
│   │   │   ├── log_exit_code.txt
│   │   │   └── session_log.md
│   │   ├── medium/
│   │   │   └── ...
│   │   └── large/
│   │       └── ...
│   ├── capture_golden_master.py
│   ├── compare_golden_master.py
│   └── README.md
```

**File: `tests/golden/__init__.py`** (v1.1)
```python
"""Golden Master test infrastructure for Ontos v3.0 migration."""
```

### 2.2 Small Fixture (5 Documents)

**Purpose:** Fast unit-level validation, CI smoke tests

```
.ontos-internal/
├── kernel/
│   └── mission.md           # Root document
├── strategy/
│   └── project_plan.md      # Depends on mission
├── atom/
│   └── schema.md            # Depends on mission
└── logs/
    └── 2025-01-01_initial-setup.md  # Impacts: project_plan
```

**File: `kernel/mission.md`**
```markdown
---
id: mission
type: kernel
status: active
depends_on: []
---

# Mission

Build reliable software with clear documentation.
```

**File: `strategy/project_plan.md`**
```markdown
---
id: project_plan
type: strategy
status: active
depends_on: [mission]
---

# Project Plan

## Overview
This document outlines the project roadmap.

## Goals
1. Create reliable infrastructure
2. Document all decisions
```

**File: `atom/schema.md`**
```markdown
---
id: schema
type: atom
status: active
depends_on: [mission]
---

# Schema Definition

## Document Types
- kernel: Foundational rules
- strategy: Goals and decisions
- atom: Technical specifications
- log: Session records
```

**File: `logs/2025-01-01_initial-setup.md`**
```markdown
---
id: log_20250101_initial_setup
type: log
status: active
event_type: feature
concepts: [setup, architecture]
impacts: [project_plan]
---

# Initial Setup

## Goal
Set up the project structure.

## Changes Made
- Created initial documentation structure
- Defined core mission

## Raw Session History
```text
abc1234 - Initial commit
```
```

**File: `.ontos.toml`**
```toml
[ontos]
version = "3.0"

[paths]
docs_dir = ".ontos-internal"
logs_dir = ".ontos-internal/logs"
context_map = "Ontos_Context_Map.md"

[scanning]
skip_patterns = ["_template.md", "archive/*"]

[validation]
strict = false
```

### 2.3 Medium Fixture (25 Documents)

**Purpose:** Integration testing, dependency graph validation, cycle detection

**Structure:**
```
.ontos-internal/
├── kernel/           (3 docs)
│   ├── mission.md
│   ├── philosophy.md
│   └── constitution.md
├── strategy/         (12 docs)
│   ├── core_architecture.md
│   ├── api_design.md
│   ├── database_schema.md
│   ├── security_model.md
│   ├── deployment_strategy.md
│   ├── testing_plan.md
│   ├── documentation_guide.md
│   ├── rejected_proposal.md      # status: rejected
│   └── proposals/
│       ├── feature_a.md          # status: draft
│       ├── feature_b.md          # status: active
│       ├── deprecated_idea.md    # status: deprecated
│       └── complete_feature.md   # status: complete
├── atom/             (4 docs)
│   ├── schema.md
│   ├── validation_rules.md
│   ├── common_concepts.md
│   └── dual_mode_matrix.md
├── reference/        (1 doc)
│   └── decision_history.md       # auto-generated
└── logs/             (5 docs)
    ├── 2025-01-01_initial-setup.md
    ├── 2025-01-15_api-design.md
    ├── 2025-02-01_security-hardening.md
    ├── 2025-02-15_rejected-exploration.md
    └── 2025-03-01_feature-complete.md
```

**Key Features to Test:**
- Dependency depth: 4 levels (kernel → architecture → api → testing)
- Rejected document with `rejected_reason` field
- Multiple status types: active, draft, deprecated, complete, rejected
- Concepts vocabulary usage
- Cross-referenced impacts in logs

#### 2.3.1 Medium Fixture File Templates (v1.1)

**Kernel Documents (3):**

```markdown
# kernel/mission.md
---
id: mission
type: kernel
status: active
depends_on: []
---
# Mission
Our mission is to build reliable, well-documented software.
```

```markdown
# kernel/philosophy.md
---
id: philosophy
type: kernel
status: active
depends_on: [mission]
---
# Philosophy
We believe in simplicity, clarity, and maintainability.
```

```markdown
# kernel/constitution.md
---
id: constitution
type: kernel
status: active
depends_on: [mission, philosophy]
---
# Constitution
Rules governing how we operate and make decisions.
```

**Strategy Documents (12):**

```markdown
# strategy/core_architecture.md
---
id: core_architecture
type: strategy
status: active
depends_on: [mission]
---
# Core Architecture
Defines the foundational technical structure.
```

```markdown
# strategy/api_design.md
---
id: api_design
type: strategy
status: active
depends_on: [core_architecture]
---
# API Design
RESTful API conventions and patterns.
```

```markdown
# strategy/database_schema.md
---
id: database_schema
type: strategy
status: active
depends_on: [core_architecture]
---
# Database Schema
Data model and storage strategy.
```

```markdown
# strategy/security_model.md
---
id: security_model
type: strategy
status: active
depends_on: [core_architecture, api_design]
---
# Security Model
Authentication, authorization, and data protection.
```

```markdown
# strategy/deployment_strategy.md
---
id: deployment_strategy
type: strategy
status: active
depends_on: [core_architecture]
---
# Deployment Strategy
CI/CD and infrastructure approach.
```

```markdown
# strategy/testing_plan.md
---
id: testing_plan
type: strategy
status: active
depends_on: [api_design, database_schema]
---
# Testing Plan
Test coverage strategy and tooling.
```

```markdown
# strategy/documentation_guide.md
---
id: documentation_guide
type: strategy
status: active
depends_on: [mission]
---
# Documentation Guide
Standards for project documentation.
```

```markdown
# strategy/rejected_proposal.md
---
id: rejected_proposal
type: strategy
status: rejected
depends_on: [core_architecture]
rejected_reason: "Superseded by api_design approach"
---
# Rejected: GraphQL API
This proposal was rejected in favor of REST.
```

```markdown
# strategy/proposals/feature_a.md
---
id: feature_a
type: strategy
status: draft
depends_on: [api_design]
---
# Draft: Feature A
Proposed new capability (under review).
```

```markdown
# strategy/proposals/feature_b.md
---
id: feature_b
type: strategy
status: active
depends_on: [api_design, security_model]
---
# Feature B
Approved and in development.
```

```markdown
# strategy/proposals/deprecated_idea.md
---
id: deprecated_idea
type: strategy
status: deprecated
depends_on: [core_architecture]
---
# Deprecated: Old Approach
No longer recommended; kept for historical reference.
```

```markdown
# strategy/proposals/complete_feature.md
---
id: complete_feature
type: strategy
status: complete
depends_on: [api_design]
---
# Complete: Feature C
Successfully implemented and deployed.
```

**Atom Documents (4):**

```markdown
# atom/schema.md
---
id: medium_schema
type: atom
status: active
depends_on: [database_schema]
---
# Schema Definition
Technical schema specifications.
```

```markdown
# atom/validation_rules.md
---
id: validation_rules
type: atom
status: active
depends_on: [medium_schema]
---
# Validation Rules
Input validation and constraints.
```

```markdown
# atom/common_concepts.md
---
id: common_concepts
type: atom
status: active
depends_on: [mission]
concepts: [architecture, api, testing]
---
# Common Concepts
Shared terminology and definitions.
```

```markdown
# atom/dual_mode_matrix.md
---
id: dual_mode_matrix
type: atom
status: active
depends_on: [core_architecture]
---
# Dual Mode Matrix
Configuration options by environment.
```

**Log Documents (5):**

```markdown
# logs/2025-01-01_initial-setup.md
---
id: log_20250101_initial_setup
type: log
status: active
event_type: feature
concepts: [setup, architecture]
impacts: [core_architecture]
---
# Initial Setup
## Goal
Set up the project structure.
## Changes Made
- Created initial documentation structure
## Raw Session History
` ``text
abc1234 - Initial commit
` ``
```

```markdown
# logs/2025-01-15_api-design.md
---
id: log_20250115_api_design
type: log
status: active
event_type: feature
concepts: [api, rest]
impacts: [api_design, security_model]
---
# API Design Session
## Goal
Design the REST API.
## Changes Made
- Defined API endpoints
## Raw Session History
` ``text
def5678 - Add API design doc
` ``
```

```markdown
# logs/2025-02-01_security-hardening.md
---
id: log_20250201_security
type: log
status: active
event_type: feature
concepts: [security, auth]
impacts: [security_model]
---
# Security Hardening
## Goal
Implement security measures.
## Changes Made
- Added authentication
## Raw Session History
` ``text
ghi9012 - Security update
` ``
```

```markdown
# logs/2025-02-15_rejected-exploration.md
---
id: log_20250215_rejected
type: log
status: active
event_type: exploration
concepts: [graphql, api]
impacts: [rejected_proposal]
---
# GraphQL Exploration
## Goal
Evaluate GraphQL as alternative.
## Changes Made
- Rejected in favor of REST
## Raw Session History
` ``text
jkl3456 - Mark proposal rejected
` ``
```

```markdown
# logs/2025-03-01_feature-complete.md
---
id: log_20250301_complete
type: log
status: active
event_type: feature
concepts: [release]
impacts: [complete_feature]
---
# Feature C Complete
## Goal
Finalize Feature C.
## Changes Made
- Marked as complete
## Raw Session History
` ``text
mno7890 - Feature complete
` ``
```

**Config File:**

```toml
# .ontos.toml
[ontos]
version = "3.0"

[paths]
docs_dir = ".ontos-internal"
logs_dir = ".ontos-internal/logs"
context_map = "Ontos_Context_Map.md"

[scanning]
skip_patterns = ["_template.md", "archive/*"]

[validation]
strict = false
```

### 2.4 Large Fixture (100+ Documents)

**Purpose:** Performance validation, scalability testing

**Structure:**
```
.ontos-internal/
├── kernel/           (3 docs)
├── strategy/         (40 docs)
│   ├── v1/           (8 docs - deprecated)
│   ├── v2/           (12 docs - mixed status)
│   ├── v3/           (15 docs - active)
│   └── proposals/    (5 docs - draft/rejected)
├── atom/             (12 docs)
├── reference/        (5 docs)
└── logs/             (45 docs)
    ├── 2024-*        (20 archived logs)
    └── 2025-*        (25 current logs)
```

**Key Features to Test:**
- 100+ document scan performance
- Deep dependency chains (5+ levels)
- Multiple independent subgraphs
- Archive exclusion logic
- Staleness detection at scale

---

## 3. Capture Script

### 3.1 File: `tests/golden/capture_golden_master.py`

```python
#!/usr/bin/env python3
"""
Golden Master Capture Script

Captures v2.9.x behavior for regression testing during v3.0 refactoring.
Run this ONCE on v2.9.x to establish baselines, then compare against v3.0.

Usage:
    python capture_golden_master.py [--fixture small|medium|large|all]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Constants
SCRIPT_DIR = Path(__file__).parent
FIXTURES_DIR = SCRIPT_DIR / "fixtures"
BASELINES_DIR = SCRIPT_DIR / "baselines"
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # tests/golden/ -> project root


def normalize_output(text: str, fixture_path: Path) -> str:
    """
    Normalize non-deterministic elements in captured output.

    Handles:
    - Timestamps (various formats)
    - Absolute paths
    - Version strings
    - Document counts (keep as-is, fixture-specific)
    """
    # Normalize timestamps
    # Format: "2026-01-12 03:21:47 UTC" or "2026-01-12 22:21:47"
    text = re.sub(
        r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}( UTC)?',
        '<TIMESTAMP>',
        text
    )

    # Format: "Date: 2026-01-12 03:21 EST"
    text = re.sub(
        r'Date: \d{4}-\d{2}-\d{2} \d{2}:\d{2} \w+',
        'Date: <TIMESTAMP>',
        text
    )

    # Format: ISO dates like "2026-01-12"
    text = re.sub(
        r'Generated: \d{4}-\d{2}-\d{2}',
        'Generated: <DATE>',
        text
    )

    # Normalize absolute paths to fixture root
    fixture_str = str(fixture_path.resolve())
    text = text.replace(fixture_str, '<FIXTURE_ROOT>')

    # Normalize any remaining absolute paths containing .ontos-internal
    text = re.sub(
        r'/[^\s]+/\.ontos-internal',
        '<FIXTURE_ROOT>/.ontos-internal',
        text
    )

    # Normalize home directory paths
    home = str(Path.home())
    text = text.replace(home, '<HOME>')

    return text


def normalize_context_map(content: str, fixture_path: Path) -> str:
    """
    Normalize the generated Ontos_Context_Map.md file.

    Additional normalizations specific to context map:
    - Provenance header timestamps
    - Mode indicator (Contributor/User)
    - Scanned directory path
    - decision_history.md references (v1.1)
    """
    content = normalize_output(content, fixture_path)

    # Normalize provenance header
    content = re.sub(
        r'Generated: <TIMESTAMP> by Ontos v[\d.]+',
        'Generated: <TIMESTAMP> by Ontos v<VERSION>',
        content
    )

    # Normalize mode (fixture always runs in contributor mode)
    content = re.sub(
        r'Mode: (Contributor|User)',
        'Mode: <MODE>',
        content
    )

    # v1.1: Normalize decision_history.md generation timestamp
    content = re.sub(
        r'decision_history\.md \(generated <TIMESTAMP>\)',
        'decision_history.md (generated <TIMESTAMP>)',
        content
    )

    return content


def normalize_session_log(content: str, fixture_path: Path) -> str:
    """
    Normalize the generated session log file.

    Additional normalizations:
    - Log ID with date
    - Date in frontmatter
    """
    content = normalize_output(content, fixture_path)

    # Normalize log ID (contains date)
    content = re.sub(
        r'id: log_\d{8}_',
        'id: log_<DATE>_',
        content
    )

    # Normalize date field in frontmatter
    content = re.sub(
        r'^date: \d{4}-\d{2}-\d{2}',
        'date: <DATE>',
        content,
        flags=re.MULTILINE
    )

    return content


def setup_fixture(fixture_name: str) -> Path:
    """
    Copy fixture to a temp location for isolated testing.
    Returns path to the temporary fixture directory.
    """
    fixture_src = FIXTURES_DIR / fixture_name
    if not fixture_src.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_src}")

    # Create temp directory
    import tempfile
    temp_dir = Path(tempfile.mkdtemp(prefix=f"golden_{fixture_name}_"))

    # Copy fixture contents
    shutil.copytree(fixture_src, temp_dir, dirs_exist_ok=True)

    # Initialize git repo (required for some commands)
    # v1.1: Configure git user to prevent CI failures
    subprocess.run(
        ["git", "init"],
        cwd=temp_dir,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "-c", "user.name=Golden Master", "-c", "user.email=test@example.com", "add", "."],
        cwd=temp_dir,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "-c", "user.name=Golden Master", "-c", "user.email=test@example.com",
         "commit", "-m", "Initial commit"],
        cwd=temp_dir,
        capture_output=True,
        check=True
    )

    return temp_dir


def capture_map_command(fixture_path: Path) -> dict:
    """
    Capture output of `python3 ontos.py map` command.

    Returns dict with:
    - stdout: normalized stdout
    - stderr: normalized stderr
    - exit_code: int
    - context_map: normalized content of generated file
    """
    # Copy ontos.py and .ontos/ to fixture (simulates installed state)
    shutil.copy(PROJECT_ROOT / "ontos.py", fixture_path / "ontos.py")
    shutil.copytree(
        PROJECT_ROOT / ".ontos",
        fixture_path / ".ontos",
        dirs_exist_ok=True
    )

    result = subprocess.run(
        [sys.executable, "ontos.py", "map"],
        cwd=fixture_path,
        capture_output=True,
        text=True,
        timeout=60
    )

    # Read generated context map
    context_map_path = fixture_path / "Ontos_Context_Map.md"
    context_map_content = ""
    if context_map_path.exists():
        context_map_content = context_map_path.read_text()

    return {
        "stdout": normalize_output(result.stdout, fixture_path),
        "stderr": normalize_output(result.stderr, fixture_path),
        "exit_code": result.returncode,
        "context_map": normalize_context_map(context_map_content, fixture_path),
    }


def capture_log_command(fixture_path: Path, event_type: str = "chore") -> dict:
    """
    Capture output of `python3 ontos.py log` command.

    Note: Uses --auto flag to avoid interactive prompts.

    Returns dict with:
    - stdout: normalized stdout
    - stderr: normalized stderr
    - exit_code: int
    - session_log: normalized content of generated log file (if any)
    """
    # Make a change to trigger log creation
    test_file = fixture_path / ".ontos-internal" / "test_change.md"
    test_file.write_text("# Test Change\nThis triggers log creation.\n")

    subprocess.run(
        ["git", "-c", "user.name=Golden Master", "-c", "user.email=test@example.com", "add", "."],
        cwd=fixture_path,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "-c", "user.name=Golden Master", "-c", "user.email=test@example.com",
         "commit", "-m", "Test change for log capture"],
        cwd=fixture_path,
        capture_output=True,
        check=True
    )

    result = subprocess.run(
        [
            sys.executable, "ontos.py", "log",
            "-e", event_type,
            "-s", "Golden Master Capture",
            "--auto"
        ],
        cwd=fixture_path,
        capture_output=True,
        text=True,
        timeout=60
    )

    # Find generated session log
    logs_dir = fixture_path / ".ontos-internal" / "logs"
    session_log_content = ""
    if logs_dir.exists():
        # Find most recent log (by filename)
        log_files = sorted(logs_dir.glob("*.md"), reverse=True)
        if log_files:
            newest_log = log_files[0]
            session_log_content = newest_log.read_text()

    return {
        "stdout": normalize_output(result.stdout, fixture_path),
        "stderr": normalize_output(result.stderr, fixture_path),
        "exit_code": result.returncode,
        "session_log": normalize_session_log(session_log_content, fixture_path),
    }


def save_baseline(fixture_name: str, command: str, data: dict) -> None:
    """Save captured data as baseline files."""
    baseline_dir = BASELINES_DIR / fixture_name
    baseline_dir.mkdir(parents=True, exist_ok=True)

    # Save individual files
    (baseline_dir / f"{command}_stdout.txt").write_text(data["stdout"])
    (baseline_dir / f"{command}_stderr.txt").write_text(data["stderr"])
    (baseline_dir / f"{command}_exit_code.txt").write_text(str(data["exit_code"]))

    # Save generated files
    if "context_map" in data and data["context_map"]:
        (baseline_dir / "context_map.md").write_text(data["context_map"])
    if "session_log" in data and data["session_log"]:
        (baseline_dir / "session_log.md").write_text(data["session_log"])

    # Save metadata
    metadata = {
        "captured_at": datetime.now().isoformat(),
        "python_version": sys.version,
        "fixture": fixture_name,
        "command": command,
    }
    (baseline_dir / f"{command}_metadata.json").write_text(
        json.dumps(metadata, indent=2)
    )


def capture_fixture(fixture_name: str) -> None:
    """Capture all baselines for a single fixture."""
    print(f"\n{'='*60}")
    print(f"Capturing baseline for: {fixture_name}")
    print(f"{'='*60}")

    # Setup isolated fixture
    fixture_path = setup_fixture(fixture_name)
    print(f"  Fixture path: {fixture_path}")

    try:
        # Capture map command
        print("  Capturing 'ontos map'...")
        map_data = capture_map_command(fixture_path)
        save_baseline(fixture_name, "map", map_data)
        print(f"    Exit code: {map_data['exit_code']}")
        print(f"    Context map: {len(map_data['context_map'])} chars")

        # Capture log command
        print("  Capturing 'ontos log'...")
        log_data = capture_log_command(fixture_path)
        save_baseline(fixture_name, "log", log_data)
        print(f"    Exit code: {log_data['exit_code']}")
        print(f"    Session log: {len(log_data['session_log'])} chars")

        print(f"  Baseline saved to: {BASELINES_DIR / fixture_name}")

    finally:
        # Cleanup temp directory
        shutil.rmtree(fixture_path, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(
        description="Capture Golden Master baselines for Ontos commands"
    )
    parser.add_argument(
        "--fixture",
        choices=["small", "medium", "large", "all"],
        default="all",
        help="Which fixture to capture (default: all)"
    )
    args = parser.parse_args()

    fixtures = ["small", "medium", "large"] if args.fixture == "all" else [args.fixture]

    print("Golden Master Capture Script")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Fixtures dir: {FIXTURES_DIR}")
    print(f"Baselines dir: {BASELINES_DIR}")

    for fixture in fixtures:
        capture_fixture(fixture)

    print("\n" + "="*60)
    print("Capture complete!")
    print("="*60)


if __name__ == "__main__":
    main()
```

---

## 4. Comparison Script

### 4.1 File: `tests/golden/compare_golden_master.py`

```python
#!/usr/bin/env python3
"""
Golden Master Comparison Script

Compares current Ontos output against captured baselines.
Used in CI to detect behavior regressions during v3.0 refactoring.

Usage:
    python compare_golden_master.py [--fixture small|medium|large|all]

Exit codes:
    0 - All comparisons pass
    1 - One or more comparisons failed
    2 - Configuration/setup error
"""

import argparse
import difflib
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Constants
SCRIPT_DIR = Path(__file__).parent
FIXTURES_DIR = SCRIPT_DIR / "fixtures"
BASELINES_DIR = SCRIPT_DIR / "baselines"
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Import normalization functions from capture script
from capture_golden_master import (
    normalize_output,
    normalize_context_map,
    normalize_session_log,
    setup_fixture,
)


class ComparisonResult:
    """Result of comparing actual vs expected output."""

    def __init__(self, name: str):
        self.name = name
        self.passed = True
        self.differences: list[str] = []

    def add_difference(self, diff: str):
        self.passed = False
        self.differences.append(diff)

    def __str__(self):
        if self.passed:
            return f"  {self.name}: PASS"
        return f"  {self.name}: FAIL\n" + "\n".join(
            f"    {line}" for line in self.differences[:20]  # Limit output
        )


def compare_text(expected: str, actual: str, name: str) -> ComparisonResult:
    """Compare two text strings and return detailed differences."""
    result = ComparisonResult(name)

    if expected == actual:
        return result

    # Generate unified diff
    expected_lines = expected.splitlines(keepends=True)
    actual_lines = actual.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile="expected",
        tofile="actual",
        lineterm=""
    ))

    if diff:
        result.add_difference(f"Text differs ({len(diff)} diff lines)")
        for line in diff[:10]:  # Show first 10 diff lines
            result.add_difference(line.rstrip())
        if len(diff) > 10:
            result.add_difference(f"... and {len(diff) - 10} more lines")

    return result


def compare_exit_code(expected: int, actual: int, name: str) -> ComparisonResult:
    """Compare exit codes."""
    result = ComparisonResult(name)

    if expected != actual:
        result.add_difference(f"Exit code: expected {expected}, got {actual}")

    return result


def run_map_command(fixture_path: Path) -> dict:
    """Run map command and return normalized results."""
    # Copy ontos.py and .ontos/ to fixture
    shutil.copy(PROJECT_ROOT / "ontos.py", fixture_path / "ontos.py")
    if (fixture_path / ".ontos").exists():
        shutil.rmtree(fixture_path / ".ontos")
    shutil.copytree(
        PROJECT_ROOT / ".ontos",
        fixture_path / ".ontos",
        dirs_exist_ok=True
    )

    result = subprocess.run(
        [sys.executable, "ontos.py", "map"],
        cwd=fixture_path,
        capture_output=True,
        text=True,
        timeout=60
    )

    context_map_path = fixture_path / "Ontos_Context_Map.md"
    context_map_content = ""
    if context_map_path.exists():
        context_map_content = context_map_path.read_text()

    return {
        "stdout": normalize_output(result.stdout, fixture_path),
        "stderr": normalize_output(result.stderr, fixture_path),
        "exit_code": result.returncode,
        "context_map": normalize_context_map(context_map_content, fixture_path),
    }


def run_log_command(fixture_path: Path) -> dict:
    """Run log command and return normalized results."""
    # Make a change to trigger log creation
    test_file = fixture_path / ".ontos-internal" / "test_change.md"
    test_file.write_text("# Test Change\nThis triggers log creation.\n")

    subprocess.run(
        ["git", "-c", "user.name=Golden Master", "-c", "user.email=test@example.com", "add", "."],
        cwd=fixture_path,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "-c", "user.name=Golden Master", "-c", "user.email=test@example.com",
         "commit", "-m", "Test change"],
        cwd=fixture_path,
        capture_output=True,
        check=True
    )

    result = subprocess.run(
        [
            sys.executable, "ontos.py", "log",
            "-e", "chore",
            "-s", "Golden Master Compare",
            "--auto"
        ],
        cwd=fixture_path,
        capture_output=True,
        text=True,
        timeout=60
    )

    logs_dir = fixture_path / ".ontos-internal" / "logs"
    session_log_content = ""
    if logs_dir.exists():
        log_files = sorted(logs_dir.glob("*.md"), reverse=True)
        if log_files:
            session_log_content = log_files[0].read_text()

    return {
        "stdout": normalize_output(result.stdout, fixture_path),
        "stderr": normalize_output(result.stderr, fixture_path),
        "exit_code": result.returncode,
        "session_log": normalize_session_log(session_log_content, fixture_path),
    }


def load_baseline(fixture_name: str, command: str) -> dict:
    """Load saved baseline data."""
    baseline_dir = BASELINES_DIR / fixture_name

    if not baseline_dir.exists():
        raise FileNotFoundError(f"Baseline not found: {baseline_dir}")

    data = {
        "stdout": (baseline_dir / f"{command}_stdout.txt").read_text(),
        "stderr": (baseline_dir / f"{command}_stderr.txt").read_text(),
        "exit_code": int((baseline_dir / f"{command}_exit_code.txt").read_text().strip()),
    }

    # Load generated files if present
    context_map_file = baseline_dir / "context_map.md"
    if context_map_file.exists():
        data["context_map"] = context_map_file.read_text()

    session_log_file = baseline_dir / "session_log.md"
    if session_log_file.exists():
        data["session_log"] = session_log_file.read_text()

    return data


def compare_fixture(fixture_name: str) -> bool:
    """
    Compare all commands for a single fixture.
    Returns True if all comparisons pass.
    """
    print(f"\n{'='*60}")
    print(f"Comparing: {fixture_name}")
    print(f"{'='*60}")

    all_passed = True
    fixture_path = setup_fixture(fixture_name)

    try:
        # Compare map command
        print("\n  Testing 'ontos map'...")
        expected_map = load_baseline(fixture_name, "map")
        actual_map = run_map_command(fixture_path)

        results = [
            compare_exit_code(
                expected_map["exit_code"],
                actual_map["exit_code"],
                "map exit_code"
            ),
            compare_text(
                expected_map["stdout"],
                actual_map["stdout"],
                "map stdout"
            ),
            # v1.1: Add stderr comparison
            compare_text(
                expected_map["stderr"],
                actual_map["stderr"],
                "map stderr"
            ),
            compare_text(
                expected_map.get("context_map", ""),
                actual_map.get("context_map", ""),
                "context_map.md"
            ),
        ]

        for r in results:
            print(r)
            if not r.passed:
                all_passed = False

        # Reset fixture for log command
        shutil.rmtree(fixture_path)
        fixture_path = setup_fixture(fixture_name)

        # Copy ontos again for log command
        shutil.copy(PROJECT_ROOT / "ontos.py", fixture_path / "ontos.py")
        shutil.copytree(
            PROJECT_ROOT / ".ontos",
            fixture_path / ".ontos",
            dirs_exist_ok=True
        )

        # Compare log command
        print("\n  Testing 'ontos log'...")
        expected_log = load_baseline(fixture_name, "log")
        actual_log = run_log_command(fixture_path)

        results = [
            compare_exit_code(
                expected_log["exit_code"],
                actual_log["exit_code"],
                "log exit_code"
            ),
            compare_text(
                expected_log["stdout"],
                actual_log["stdout"],
                "log stdout"
            ),
            # v1.1: Add stderr comparison
            compare_text(
                expected_log["stderr"],
                actual_log["stderr"],
                "log stderr"
            ),
            # v1.1: Add session_log comparison
            compare_text(
                expected_log.get("session_log", ""),
                actual_log.get("session_log", ""),
                "session_log.md"
            ),
        ]

        for r in results:
            print(r)
            if not r.passed:
                all_passed = False

    finally:
        shutil.rmtree(fixture_path, ignore_errors=True)

    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Compare Ontos output against Golden Master baselines"
    )
    parser.add_argument(
        "--fixture",
        choices=["small", "medium", "large", "all"],
        default="all",
        help="Which fixture to compare (default: all)"
    )
    args = parser.parse_args()

    fixtures = ["small", "medium", "large"] if args.fixture == "all" else [args.fixture]

    print("Golden Master Comparison Script")
    print(f"Project root: {PROJECT_ROOT}")

    all_passed = True
    for fixture in fixtures:
        if not compare_fixture(fixture):
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("All comparisons PASSED")
        print("="*60)
        sys.exit(0)
    else:
        print("Some comparisons FAILED")
        print("="*60)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## 5. CI Integration

### 5.1 File: `.github/workflows/golden-master.yml`

```yaml
name: Golden Master Tests

on:
  push:
    branches: [main, v3.0, "v3.0.*"]
  pull_request:
    branches: [main]

jobs:
  golden-master:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pyyaml

      - name: Run Golden Master comparison
        run: |
          python tests/golden/compare_golden_master.py --fixture all

      - name: Upload diff artifacts on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: golden-master-diffs-${{ matrix.python-version }}
          path: tests/golden/baselines/
          retention-days: 7
```

### 5.2 File: `tests/golden/README.md`

```markdown
# Golden Master Testing

Golden Master tests capture the exact behavior of Ontos v2.9.x to ensure
v3.0 refactoring doesn't introduce regressions.

## Quick Start

### Running Comparisons (CI)

` ``bash
python tests/golden/compare_golden_master.py --fixture all
` ``

Exit code 0 means all tests pass. Exit code 1 means regression detected.

### Updating Baselines

When intentional behavior changes occur in v3.0:

` ``bash
# Re-capture baseline for specific fixture
python tests/golden/capture_golden_master.py --fixture small

# Re-capture all baselines
python tests/golden/capture_golden_master.py --fixture all

# Commit the updated baselines
git add tests/golden/baselines/
git commit -m "chore: update golden master baselines for v3.0 changes"
` ``

## Fixture Sizes

| Fixture | Documents | Purpose | CI Time |
|---------|-----------|---------|---------|
| small | 5 | Smoke test | ~2s |
| medium | 25 | Integration | ~5s |
| large | 100+ | Scalability | ~15s |

## Normalization

The capture/compare scripts normalize:

- **Timestamps**: Replaced with `<TIMESTAMP>` or `<DATE>`
- **Absolute paths**: Replaced with `<FIXTURE_ROOT>` or `<HOME>`
- **Version strings**: Replaced with `<VERSION>`
- **Mode indicators**: Replaced with `<MODE>`

## Files Captured

For each command, we capture:

- `{command}_stdout.txt` - Normalized stdout
- `{command}_stderr.txt` - Normalized stderr
- `{command}_exit_code.txt` - Exit code
- `{command}_metadata.json` - Capture metadata
- `context_map.md` - Generated Ontos_Context_Map.md (for map)
- `session_log.md` - Generated session log (for log)

## Troubleshooting

### Comparison fails on timestamps

Check if a new timestamp format was introduced. Update normalization
patterns in `capture_golden_master.py`.

### Comparison fails on path differences

Check if new path patterns appear in output. Update normalization
patterns to handle them.

### Intentional behavior change

1. Verify the change is intentional
2. Re-capture the affected baseline
3. Document the change in commit message
4. Update this README if normalization patterns changed
```

---

## 6. Verification

### 6.1 Commands to Run

```bash
# 1. Create fixture directories
mkdir -p tests/golden/fixtures/{small,medium,large}
mkdir -p tests/golden/baselines

# 2. Create small fixture files (copy from Section 2.2)
# ... create files ...

# 3. Run capture script on v2.9.x
python tests/golden/capture_golden_master.py --fixture small

# 4. Verify capture succeeded
ls -la tests/golden/baselines/small/

# 5. Run comparison (should pass on v2.9.x)
python tests/golden/compare_golden_master.py --fixture small

# 6. Verify CI workflow
act push  # or push to GitHub
```

### 6.2 Manual Verification

| Check | How | Expected |
|-------|-----|----------|
| Fixture valid | `python ontos.py map` in fixture dir | Exit 0, no errors |
| Baseline captured | `ls tests/golden/baselines/small/` | 8+ files |
| Normalization works | `grep '<TIMESTAMP>' baselines/small/map_stdout.txt` | Matches found |
| Comparison passes | `python compare_golden_master.py --fixture small` | Exit 0 |
| CI runs | Push to branch | GitHub Actions green |

### 6.3 Sign-off Checklist

- [ ] All fixtures created (small, medium, large)
- [ ] Capture script runs successfully
- [ ] Baseline captured from v2.9.x
- [ ] Comparison script passes on v2.9.x
- [ ] CI workflow configured and passing
- [ ] README complete
- [ ] Ready for Phase 1

---

## 7. Notes for Implementation Team

### 7.1 Watch Out For

1. **Git initialization**: Fixtures need `.git/` for some commands. The capture script handles this, but manual testing requires `git init`.

2. **Interactive prompts**: The `ontos log` command has interactive prompts. Use `--auto` flag to bypass.

3. **Deprecation warnings**: Current scripts emit FutureWarning. These are captured in stderr and compared (v1.1). If warnings change between Ontos versions, re-capture baselines.

4. **File ordering**: Context map sections may have non-deterministic ordering. Current implementation sorts by doc_id, but verify this.

5. **Decision history**: The `decision_history.md` is auto-generated. v1.1 adds normalization for its timestamps.

6. **Git user config** (v1.1): CI environments may lack git user.name/user.email. The `setup_fixture` function now configures these automatically.

7. **Python imports** (v1.1): `compare_golden_master.py` imports from `capture_golden_master.py`. The `__init__.py` file ensures this works correctly.

### 7.2 Recommended Order

1. Create `tests/golden/` directory structure
2. Write small fixture files (copy from spec)
3. Write capture script (copy from spec)
4. Run capture on current v2.9.x
5. Write compare script (copy from spec)
6. Verify compare passes
7. Create medium fixture
8. Create large fixture
9. Add CI workflow
10. Document in README

### 7.3 Decisions to Make

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Fixture location | `tests/golden/` vs `tests/fixtures/golden/` | `tests/golden/` (simpler) |
| Large fixture size | 100 vs 150 vs 200 docs | 100 (sufficient for perf testing) |
| CI matrix | Python 3.9-3.12 vs 3.11 only | 3.9-3.12 (ensure compatibility) |
| Baseline storage | Git LFS vs regular | Regular (baselines are text, <1MB) |

---

## 8. LLM Review Board Feedback (v1.1)

### 8.1 Reviewers

| Reviewer | Recommendation | Addressed |
|----------|----------------|-----------|
| Codex (GPT-5) | Minor Revisions | Yes |
| Claude Opus 4.5 | Minor Revisions | Yes |
| Gemini CLI | Ready to Implement | Yes |

### 8.2 Changes Made

| Feedback | Source | Resolution |
|----------|--------|------------|
| Missing stderr comparison | Codex | Added to `compare_fixture()` |
| Missing session_log comparison | Codex | Added to `compare_fixture()` |
| Missing `__init__.py` | Gemini | Added to directory structure |
| Git user config in scripts | Codex | Added to `setup_fixture()` |
| `decision_history.md` handling | Claude | Added normalization pattern |
| Medium fixture templates | Codex, Claude | Added Section 2.3.1 |

### 8.3 Feedback Not Addressed (with rationale)

| Feedback | Source | Rationale |
|----------|--------|-----------|
| JSON output capture | Codex | v3.0 feature, not v2.9.x baseline (Claude, Gemini concur) |
| Large fixture generator | Claude | Deferred - can add during implementation if needed |
| `.gitignore` | Gemini | Minor - can add during implementation |

### 8.4 Verdict

**Status:** Ready for Implementation

The spec has been updated to address all blocking and high-priority feedback from the LLM Review Board. No re-review needed.

---

*End of Phase 0 Implementation Spec*
