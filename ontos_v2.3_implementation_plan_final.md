# Ontos v2.3 Implementation Plan (Final)

**Version:** 2.3.0 "Less Typing, More Insight"  
**Status:** Ready for Implementation  
**Created:** 2025-12-14  
**Revised:** 2025-12-14  
**Authors:** Johnny (Human), Claude Opus 4.5, Claude Code, ChatGPT Codex, Google Gemini  

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-14 | Initial draft |
| 1.1 | 2025-12-14 | Incorporated Gemini + Claude Code feedback (see Part 8) |
| 1.2 | 2025-12-14 | Fixed two-table trap bug, added missing helpers, final polish (see Part 8) |
| 1.3 | 2025-12-14 | Added defensive table detection, hook sync notes, header coupling warnings |

---

## Executive Summary

Ontos v2.3 focuses on UX improvements that reduce ceremony while preserving curation. The release addresses friction points identified through multi-agent analysis, where four AI systems independently reviewed the codebase and converged on common pain points.

**Theme:** Less Typing, More Insight
- Kill the ceremony (defaults, auto-slug, single commands)
- Surface the data (query interface, health metrics, concept search)
- Guide don't block (contextual hook, creation-time validation)

**Scope:** UX improvements only. No architectural changes to the dual ontology model.

**Out of Scope:** 
- Full package management (pip/npm) — deferred to v3.0
- Version check on activation — deferred to v2.4 (requires network call)
- `$EDITOR` spawning for summary editing — deferred to v2.4

---

## Part 1: Multi-Agent Analysis Methodology

### Process

Four AI systems independently analyzed the Ontos v2.2 codebase to identify friction points:

| Agent | Focus Area | Approach |
|-------|------------|----------|
| Claude Opus 4.5 | Structural gaps | Analyzed data flow, identified unused capabilities |
| Claude Code | User journey | Traced new user experience, identified ceremony |
| ChatGPT Codex | Workflow friction | Focused on command-line interactions |
| Google Gemini | Tooling architecture | Identified capability gaps and maintenance debt |

### Why Multi-Agent?

Single-agent analysis risks blind spots. By comparing independent analyses:
- **Convergence** = high-confidence friction (all agents see it)
- **Divergence** = nuanced issues requiring human judgment
- **Unique insights** = valuable perspectives to steal

### Review Process

The implementation plan went through two review cycles:

**Round 1 (v1.0 → v1.1):**
- Gemini: Identified regex parsing fragility, inline Python risks, code duplication
- Claude Code: Identified edge cases, missing specs, mode handling issues

**Round 2 (v1.1 → v1.2):**
- Gemini: Caught critical two-table bug in consolidation logic
- Claude Code: Identified missing helper functions and imports

All feedback is documented in Part 8.

---

## Part 2: Friction Point Analysis

### 2.1 Strong Convergence (All 4 Sources Agree)

#### Friction #1: The Log Template Problem

| Source | Framing |
|--------|---------|
| Claude Opus | "Logs optimized for big decisions, most sessions small" |
| Claude Code | "Six sections. For a 20-minute bug fix, that's overkill" |
| Codex | "Archiving is command-heavy" |
| Gemini | "Template Fatigue - blank form generator" |

**Current State:**

The `ontos_end_session.py` generates a 6-section template:
```markdown
## 1. Goal
## 2. Key Decisions  
## 3. Alternatives Considered
## 4. Changes Made
## 5. Next Steps
## Raw Session History
```

**Problem Analysis:**

1. **One-size-fits-all:** A typo fix and an architecture decision get identical templates
2. **Placeholder anxiety:** Empty sections feel like "incomplete homework"
3. **Context switch:** User runs command, then must open editor, fill blanks, save, commit
4. **Skip cascade:** Users either skip sections (leaving placeholders) or skip archiving entirely

**Root Cause:**

The `create_log_file` function in `ontos_end_session.py` hardcodes the full template regardless of `event_type`. The `-e` flag determines the frontmatter value but not the template structure.

**Evidence:**
```python
# Current: Template is identical for all event types
content = f"""---
id: log_{today_date.replace('-', '')}_{topic_slug.replace('-', '_')}
type: log
status: active
event_type: {event_type}  # This varies, but template below doesn't
...
## 1. Goal
## 2. Key Decisions
## 3. Alternatives Considered  # Overkill for chores
## 4. Changes Made
## 5. Next Steps
```

---

#### Friction #2: Archive Ceremony

| Source | Framing |
|--------|---------|
| Claude Opus | "Too many steps at end of session" |
| Claude Code | "`--source` typed every time" + "no dry-run" |
| Codex | "Full CLI signature stalls Git pushes" |
| Gemini | "Context switch at critical moment of closure" |

**Current State:**

Archive command requires:
```bash
python3 .ontos/scripts/ontos_end_session.py "topic-slug" -s "Claude Code" -e feature
```

That's 70+ characters typed at the moment when user just wants to push and move on.

**Problem Analysis:**

1. **Repetitive source flag:** `-s "Claude Code"` typed every time, rarely changes per-project
2. **Manual slug:** User must invent a slug on the spot
3. **Event type lookup:** Must remember: feature, fix, refactor, exploration, chore
4. **No preview:** File created immediately, no "are you sure?"
5. **Blocking hook:** Pre-push fails if not archived, increasing frustration

**Root Cause:**

No configuration for defaults. No inference from context. No dry-run mode.

---

#### Friction #3: Pre-Push Hook is Binary

| Source | Framing |
|--------|---------|
| Claude Opus | "Doesn't understand commit size" |
| Claude Code | "Binary - no contextual guidance" |
| Codex | "Blocking - stalls pushes" |

**Current State:**

The `pre-push` hook checks for marker file existence only:
```bash
if [ -f "$MARKER_FILE" ]; then
    exit 0  # Allow
else
    exit 1  # Block (same for 1 line or 1000 lines changed)
fi
```

**Problem Analysis:**

1. **No magnitude awareness:** 3-character typo fix = 4-hour refactor in hook's eyes
2. **Wall of text:** Error message is 15 lines of ASCII box, no actionable info
3. **No context:** Doesn't say what changed, which docs might be relevant
4. **Binary outcome:** Block or allow, no "advisory for small changes"

**Root Cause:**

Hook checks for marker file existence only. No analysis of what changed.

---

#### Friction #4: Consolidation is Manual Database Work

| Source | Framing |
|--------|---------|
| Codex | "High effort, easy to defer or miss steps" |
| Gemini | "Manual foreign keys guarantee broken links" |
| Claude Code | (Implicit in graph health feedback) |

**Current State:**

Monthly consolidation ritual from `Ontos_Manual.md`:
1. Review oldest 5-10 logs
2. Verify decisions absorbed into Space docs
3. Manually add row to `decision_history.md` table
4. Add breadcrumb citations to Space docs
5. Move log file to `archive/`
6. Commit

**Problem Analysis:**

1. **Manual table editing:** `decision_history.md` is a markdown table acting as database
2. **Foreign key risk:** Archive paths must match actual file locations
3. **Multi-step atomicity:** 6 steps should be one atomic operation
4. **No tooling:** Entirely manual, no `ontos consolidate` command
5. **Easy to defer:** High effort + no deadline = never done

**Root Cause:**

No consolidation tooling. The ritual exists only in documentation.

---

### 2.2 Moderate Convergence (2-3 Sources)

#### Friction #5: Graph Exists But Can't Query It

| Source | Framing |
|--------|---------|
| Claude Opus | "No reverse lookup, no concept search, no timeline query" |
| Claude Code | "Pass/fail only—no health metrics" |
| Codex | "Maintenance is manual ritual" |

**Current State:**

`ontos_generate_context_map.py` builds a full dependency graph:
- Adjacency list (`adj`)
- Reverse adjacency list (`rev_adj`)
- Depth calculations
- Cycle detection

Then it writes a markdown file and discards the data structures.

**Problem Analysis:**

1. **Data exists, interface doesn't:** Reverse lookup computed for orphan detection, then thrown away
2. **No concept search:** Concepts tagged but not queryable
3. **No health metrics:** Is graph connected? What percentage of logs have impacts?
4. **Timeline locked in markdown:** Can't filter "last 30 days" or "only features"

**Root Cause:**

Scripts are generators, not query engines. No persistent data structure or query interface.

---

#### Friction #6: Concepts Are Write-Only

| Source | Framing |
|--------|---------|
| Claude Opus | "No payoff for using known concepts" |
| Claude Code | "Lookup overhead with context switching" |
| Gemini | "Creation blind to lint rules" |

**Current State:**

1. User tags log with `concepts: [auth, api]`
2. Lint warns if concept not in `Common_Concepts.md`
3. ...that's it. No query, no aggregation, no benefit.

**Problem Analysis:**

1. **No positive feedback:** Good tagging unlocks nothing
2. **Delayed validation:** Errors found at lint time, not creation time
3. **Context switch for lookup:** Must open separate file to check vocabulary
4. **v3.0 promise unfulfilled:** "Subgraph queries" mentioned but not shipped

**Root Cause:**

Concepts designed for future querying that doesn't exist yet. Current value = lint warnings only.

---

#### Friction #7: Impact Suggestions Are Brittle

| Source | Framing |
|--------|---------|
| Claude Opus | "Impacts field almost always wrong" |
| Gemini | "Multi-day branches lose context; read-only blindspots" |

**Current State:**

`suggest_impacts()` in `ontos_end_session.py`:
```python
# Step 1: Check uncommitted changes
result = subprocess.run(['git', 'status', '--porcelain'], ...)

# Step 2: If clean, check today's commits only
if not changed_files:
    today = datetime.date.today().isoformat()
    result = subprocess.run(['git', 'log', '--since', today, ...])
```

**Problem Analysis:**

1. **Today-only window:** Multi-day feature branches lose history
2. **File changes ≠ conceptual impact:** Reading a file to make a decision isn't captured
3. **Requires explicit flag:** `--suggest-impacts` not default behavior
4. **No conversation context:** Script can't know what agent discussed with user

**Root Cause:**

Heuristic is file-based, not semantic. Git sees file changes, not decisions.

---

### 2.3 Unique Insights Adopted

#### From Claude Code: "Blank Page Problem"

After install, user has empty `docs/` with no guidance. 

**Solution:** `ontos init` creates starter documents with prompting questions.

#### From Claude Code: "Curation vs Ceremony"

> "v2.3 should preserve curation while eliminating ceremony."

**Design Principle:** Manual classification = curation (keep). Typing `--source "Claude Code"` every time = ceremony (kill).

#### From Gemini: "Split Brain Architecture"

Creation (`ontos_end_session.py`) and validation (`--lint`) are disconnected.

**Solution:** Validate at creation time. Immediate feedback > delayed lint warnings.

#### From Codex: "Two Commands for Maintenance"

Weekly maintenance requires two separate commands.

**Solution:** Single `ontos maintain` that runs both.

---

### 2.4 Points Refined

#### "Mental Model Friction" (Claude Code)

> "Logs vs Space docs require learning"

**Verdict:** True, but irreducible. The dual ontology IS the product. Better docs help, but don't over-engineer away the core concept.

**Action:** Improve documentation, not code.

#### "Frontmatter Tagging Cognitive Load" (Codex)

**Verdict:** This is curation, not ceremony. Manual `type` and `depends_on` IS the value proposition.

**Action:** Defer smart suggestions to v3.0 (requires semantic analysis).

---

### 2.5 Points Rejected

#### "Session Logs Duplicate Git" (Claude Opus)

**Rejection reason:** Git captures WHAT changed. Logs capture WHY and what was REJECTED. The "Alternatives Considered" section has no git equivalent.

#### "Activation Requires User Intent" (Claude Opus)

**Rejection reason:** Explicit activation is intentional. Auto-loading risks wrong context, token waste, user confusion. The v2 strategy chose "intent over automation."

#### "Index Section is Redundant" (Claude Opus)

**Rejection reason:** Table format useful for quick ID lookup. Token cost ~200. Not worth removing.

---

## Part 3: Solution Specifications

### 3.0 Shared Utilities Library

**Problem:** Code duplication across scripts (`parse_frontmatter`, `scan_docs`, `load_common_concepts`).

**Solution:** Extract to shared library.

**File:** `.ontos/scripts/ontos_lib.py` (new)

```python
"""Shared utilities for Ontos scripts.

This module contains common functions used across multiple Ontos scripts.
Centralizing them here ensures consistency and simplifies maintenance.
"""

import os
import re
import yaml
import subprocess
from datetime import datetime
from typing import Optional


def parse_frontmatter(filepath: str) -> Optional[dict]:
    """Parse YAML frontmatter from a markdown file.

    Args:
        filepath: Path to the markdown file.

    Returns:
        Dictionary of frontmatter fields, or None if no valid frontmatter.
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    if content.startswith('---'):
        try:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                return frontmatter
        except yaml.YAMLError as e:
            print(f"Error parsing YAML in {filepath}: {e}")
    return None


def normalize_depends_on(value) -> list[str]:
    """Normalize depends_on field to a list of strings.

    Handles YAML edge cases: null, empty, string, or list.

    Args:
        value: Raw value from YAML frontmatter.

    Returns:
        List of dependency IDs (empty list if none).
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None and str(v).strip()]
    return []


def normalize_type(value) -> str:
    """Normalize type field to a string.

    Args:
        value: Raw value from YAML frontmatter.

    Returns:
        Type string ('unknown' if invalid).
    """
    if value is None:
        return 'unknown'
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or '|' in stripped:
            return 'unknown'
        return stripped
    if isinstance(value, list):
        if value and value[0] is not None:
            first = str(value[0]).strip()
            if '|' in first:
                return 'unknown'
            return first if first else 'unknown'
    return 'unknown'


def load_common_concepts(docs_dir: str = None) -> set[str]:
    """Load known concepts from Common_Concepts.md if it exists.
    
    Args:
        docs_dir: Documentation directory to search.
    
    Returns:
        Set of known concept strings.
    """
    if docs_dir is None:
        from ontos_config import DOCS_DIR
        docs_dir = DOCS_DIR
    
    possible_paths = [
        os.path.join(docs_dir, 'reference', 'Common_Concepts.md'),
        os.path.join(docs_dir, 'Common_Concepts.md'),
        'docs/reference/Common_Concepts.md',
    ]
    
    concepts_file = None
    for path in possible_paths:
        if os.path.exists(path):
            concepts_file = path
            break
            
    if not concepts_file:
        return set()
    
    concepts = set()
    try:
        with open(concepts_file, 'r', encoding='utf-8') as f:
            content = f.read()
        matches = re.findall(r'\|\s*`([a-z][a-z0-9-]*)`\s*\|', content)
        concepts.update(matches)
    except (IOError, OSError):
        pass
    
    return concepts


def get_git_last_modified(filepath: str) -> Optional[datetime]:
    """Get the last modified date of a file from git history.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        datetime of last modification, or None if not in git.
    """
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cd', '--date=iso-strict', '--', filepath],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            date_str = result.stdout.strip()
            # Handle timezone offset format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return None


def find_last_session_date(logs_dir: str = None) -> str:
    """Find the date of the most recent session log.

    Args:
        logs_dir: Directory containing log files. If None, uses LOGS_DIR from config.

    Returns:
        Date string in YYYY-MM-DD format, or empty string if no logs found.
    """
    if logs_dir is None:
        from ontos_config import LOGS_DIR
        logs_dir = LOGS_DIR
    
    if not os.path.exists(logs_dir):
        return ""

    log_files = []
    for filename in os.listdir(logs_dir):
        if filename.endswith('.md') and len(filename) >= 10:
            date_part = filename[:10]
            if date_part.count('-') == 2:
                log_files.append(date_part)

    if not log_files:
        return ""

    return sorted(log_files)[-1]


# Branch names that should not be used as auto-slugs
BLOCKED_BRANCH_NAMES = {'main', 'master', 'dev', 'develop', 'HEAD'}
```

#### Update Existing Scripts

All scripts that currently define these functions should import from `ontos_lib.py`:

```python
# In ontos_generate_context_map.py, ontos_query.py, ontos_consolidate.py, ontos_end_session.py:
from ontos_lib import (
    parse_frontmatter,
    normalize_depends_on,
    normalize_type,
    load_common_concepts,
    get_git_last_modified,
    find_last_session_date,
    BLOCKED_BRANCH_NAMES,
)
```

---

### 3.0.1 Configuration Helpers

**Problem:** Some helper functions referenced but not defined.

**Solution:** Add to config module.

**File:** `.ontos/scripts/ontos_config_defaults.py` (additions)

```python
import os

# Project root detection
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def is_ontos_repo() -> bool:
    """Check if this is the Ontos repository itself (contributor mode).
    
    Returns:
        True if .ontos-internal/ exists (contributor mode),
        False otherwise (user mode).
    """
    return os.path.exists(os.path.join(PROJECT_ROOT, '.ontos-internal'))


# Patterns to skip when scanning docs
SKIP_PATTERNS = [
    'archive/',
    'Ontos_CHANGELOG.md',
    'README.md',
    '.git/',
    'node_modules/',
    '__pycache__/',
]

# Small change threshold (lines) for pre-push hook
# Changes below this get softer "skip this time" message
# Rationale: ~20 lines is roughly one small function or config tweak
# Tune higher for verbose code, lower for dense code
SMALL_CHANGE_THRESHOLD = 20

# Default source for session logs (set in ontos_config.py)
# Example: DEFAULT_SOURCE = "Claude Code"
DEFAULT_SOURCE = None
```

---

### 3.1 P0: Adaptive Templates by Event Type

**Problem:** One-size-fits-all template doesn't match session complexity.

**Solution:** Generate template based on `-e` flag value.

#### Template Definitions

```python
# In ontos_end_session.py

TEMPLATES = {
    'chore': {
        'sections': ['Goal', 'Changes Made'],
        'description': 'Maintenance, dependencies, configuration'
    },
    'fix': {
        'sections': ['Goal', 'Changes Made', 'Next Steps'],
        'description': 'Bug fixes, corrections'
    },
    'feature': {
        'sections': ['Goal', 'Key Decisions', 'Changes Made', 'Next Steps'],
        'description': 'New capabilities'
    },
    'refactor': {
        'sections': ['Goal', 'Key Decisions', 'Alternatives Considered', 'Changes Made'],
        'description': 'Restructuring without behavior change'
    },
    'exploration': {
        'sections': ['Goal', 'Key Decisions', 'Alternatives Considered', 'Next Steps'],
        'description': 'Research, spikes, prototypes'
    },
    'decision': {
        'sections': ['Goal', 'Key Decisions', 'Alternatives Considered', 'Changes Made', 'Next Steps'],
        'description': 'Architectural or design decisions'
    }
}

SECTION_TEMPLATES = {
    'Goal': '## {n}. Goal\n<!-- What was the primary objective? -->\n\n',
    'Key Decisions': '## {n}. Key Decisions\n<!-- What choices were made? -->\n- \n\n',
    'Alternatives Considered': '## {n}. Alternatives Considered\n<!-- What was rejected and why? -->\n- \n\n',
    'Changes Made': '## {n}. Changes Made\n<!-- Summary of changes -->\n- \n\n',
    'Next Steps': '## {n}. Next Steps\n<!-- What should happen next? -->\n- \n\n',
}


def generate_template_sections(event_type: str) -> str:
    """Generate template sections based on event type.
    
    Args:
        event_type: Type of event (chore, fix, feature, etc.)
        
    Returns:
        Formatted markdown sections.
    """
    template = TEMPLATES.get(event_type, TEMPLATES['chore'])
    sections = template['sections']
    
    content = ""
    for i, section in enumerate(sections, 1):
        section_template = SECTION_TEMPLATES[section]
        content += section_template.format(n=i)
    
    return content
```

#### Update EVENT_TYPES

**File:** `.ontos/scripts/ontos_config_defaults.py`

```python
EVENT_TYPES = {
    'feature': {
        'definition': 'Adding new capability to the system',
        'examples': ['Implemented OAuth login', 'Added search functionality'],
    },
    'fix': {
        'definition': 'Correcting broken or incorrect behavior',
        'examples': ['Fixed refresh token bug', 'Resolved race condition'],
    },
    'refactor': {
        'definition': 'Restructuring code without changing behavior',
        'examples': ['Split auth module', 'Migrated to TypeScript'],
    },
    'exploration': {
        'definition': 'Research, spikes, or prototypes',
        'examples': ['Evaluated database options', 'Tested new library'],
    },
    'chore': {
        'definition': 'Maintenance, dependencies, configuration',
        'examples': ['Updated dependencies', 'Fixed CI pipeline'],
    },
    'decision': {  # NEW
        'definition': 'Architectural or design decisions',
        'examples': ['Chose OAuth over SAML', 'Selected PostgreSQL for persistence'],
    },
}

VALID_EVENT_TYPES = set(EVENT_TYPES.keys())
```

#### Acceptance Criteria

- [ ] `chore` generates 2-section template (Goal, Changes Made)
- [ ] `decision` generates 5-section template (full)
- [ ] `feature` generates 4-section template
- [ ] Section numbers are sequential (no gaps)
- [ ] Existing tests pass
- [ ] New test: verify template selection by event type

---

### 3.2 P0: Archive Ceremony Reduction

**Problem:** 70+ character command typed at end of every session.

**Solution:** Three sub-features: DEFAULT_SOURCE, auto-slug, dry-run.

#### 3.2.1 DEFAULT_SOURCE Configuration

**File:** `.ontos/scripts/ontos_config_defaults.py`

```python
# Default source for session logs (set in ontos_config.py)
# Example: DEFAULT_SOURCE = "Claude Code"
DEFAULT_SOURCE = None
```

**File:** `.ontos/scripts/ontos_end_session.py`

```python
from ontos_config import REQUIRE_SOURCE_IN_LOGS

# Try to import DEFAULT_SOURCE
try:
    from ontos_config import DEFAULT_SOURCE
except ImportError:
    DEFAULT_SOURCE = None

# Modify argument parser
source_default = DEFAULT_SOURCE
source_required = REQUIRE_SOURCE_IN_LOGS and not DEFAULT_SOURCE

parser.add_argument('--source', '-s', type=str, metavar='NAME',
                    default=source_default,
                    required=source_required,
                    help=f'LLM/program source (default: {source_default or "required"})')
```

#### 3.2.2 Auto-Slug Generation

**File:** `.ontos/scripts/ontos_end_session.py`

```python
from ontos_lib import BLOCKED_BRANCH_NAMES, find_last_session_date

def generate_auto_slug(quiet: bool = False) -> Optional[str]:
    """Generate slug from git branch name or recent commit.
    
    Returns:
        Generated slug, or None if user input required.
    """
    # Try branch name first
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            branch = result.stdout.strip()
            
            # Block common branch names (from Gemini feedback)
            if branch.lower() in BLOCKED_BRANCH_NAMES:
                if not quiet:
                    print(f"ℹ️  Branch '{branch}' not suitable for slug, trying commit message...")
            else:
                # Clean branch name: feature/auth-flow -> auth-flow
                if '/' in branch:
                    branch = branch.split('/')[-1]
                slug = branch.lower().replace('_', '-')[:50]
                if VALID_SLUG_PATTERN.match(slug):
                    return slug
    except:
        pass
    
    # Fall back to recent commit subject
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=format:%s'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            subject = result.stdout.strip()[:50]
            # Convert to slug: "Fix auth bug" -> "fix-auth-bug"
            slug = re.sub(r'[^a-z0-9]+', '-', subject.lower()).strip('-')
            if slug and len(slug) >= 3 and VALID_SLUG_PATTERN.match(slug):
                return slug
    except:
        pass
    
    # No automatic fallback - prompt user (from Claude feedback)
    return None


# In main()
if not args.topic:
    auto_slug = generate_auto_slug(args.quiet)
    if auto_slug:
        args.topic = auto_slug
        if not args.quiet:
            print(f"Auto-generated slug: {args.topic}")
    else:
        # Prompt user instead of silent fallback (from Claude feedback)
        if not args.quiet:
            print("Could not auto-generate slug from branch or recent commits.")
        try:
            args.topic = input("Enter session slug: ").strip()
            if not args.topic:
                print("Error: Slug is required.")
                sys.exit(1)
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(1)
```

#### 3.2.3 Dry-Run Mode

**File:** `.ontos/scripts/ontos_end_session.py`

```python
parser.add_argument('--dry-run', '-n', action='store_true',
                    help='Preview log file without creating it')

# In main(), before create_log_file()
if args.dry_run:
    # Generate content preview
    template = TEMPLATES.get(event_type, TEMPLATES['chore'])
    sections = generate_template_sections(event_type)
    
    print("\n" + "=" * 60)
    print("DRY RUN - Would create the following log:")
    print("=" * 60 + "\n")
    
    print(f"File: {LOGS_DIR}/{datetime.datetime.now().strftime('%Y-%m-%d')}_{args.topic}.md")
    print(f"Event Type: {event_type} ({len(template['sections'])} sections)")
    print(f"Source: {args.source or DEFAULT_SOURCE or '(none)'}")
    print(f"Concepts: {concepts}")
    print(f"Impacts: {impacts}")
    print()
    print("Sections:")
    for s in template['sections']:
        print(f"  - {s}")
    
    print("\n" + "=" * 60)
    print("END DRY RUN - No file created")
    print("=" * 60)
    sys.exit(0)
```

#### 3.2.4 Quick Concept Lookup

```python
parser.add_argument('--list-concepts', action='store_true',
                    help='Print available concepts and exit')

# In main(), early exit
if args.list_concepts:
    from ontos_lib import load_common_concepts
    concepts = load_common_concepts()
    if concepts:
        print("Available concepts:")
        for c in sorted(concepts):
            print(f"  {c}")
    else:
        print("No Common_Concepts.md found.")
    sys.exit(0)
```

#### Combined UX Improvement

**Before:**
```bash
python3 .ontos/scripts/ontos_end_session.py "auth-refactor" -s "Claude Code" -e feature
```

**After:**
```bash
# With DEFAULT_SOURCE configured and on feature/auth-refactor branch:
python3 .ontos/scripts/ontos_end_session.py -e feature
# Output: Auto-generated slug: auth-refactor
```

#### Acceptance Criteria

- [ ] DEFAULT_SOURCE in config eliminates -s flag requirement
- [ ] Auto-slug from branch name (excluding main/master/dev)
- [ ] Auto-slug from commit message as fallback
- [ ] Prompts user when auto-generation fails (no silent timestamp)
- [ ] --dry-run shows preview without file creation
- [ ] --list-concepts prints vocabulary
- [ ] Existing tests pass

---

### 3.3 P0: Contextual Pre-Push Hook

**Problem:** Hook treats all changes identically. Inline Python is unmaintainable.

**Solution:** Extract logic to dedicated Python script (from Gemini feedback).

#### 3.3.1 Minimal Bash Hook

**File:** `.ontos/hooks/pre-push`

```bash
#!/bin/bash
# Ontos pre-push hook v2.3
# All logic delegated to Python for testability

SCRIPTS_DIR=".ontos/scripts"
HOOK_SCRIPT="$SCRIPTS_DIR/ontos_pre_push_check.py"

# Bypass if Ontos not installed
if [ ! -f "$HOOK_SCRIPT" ]; then
    exit 0
fi

# Hand off to Python immediately
python3 "$HOOK_SCRIPT"
exit $?
```

#### 3.3.2 Python Hook Logic

**File:** `.ontos/scripts/ontos_pre_push_check.py` (new)

```python
"""Pre-push hook logic for Ontos.

This script is called by the bash pre-push hook. It checks whether
a session has been archived and provides contextual feedback based
on the size and nature of changes.
"""

import os
import sys
import subprocess
from typing import Tuple, List

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ontos_config import PROJECT_ROOT

MARKER_FILE = os.path.join(PROJECT_ROOT, '.ontos', 'session_archived')

# Import config with fallbacks
try:
    from ontos_config import ENFORCE_ARCHIVE_BEFORE_PUSH
except ImportError:
    ENFORCE_ARCHIVE_BEFORE_PUSH = True

try:
    from ontos_config import SMALL_CHANGE_THRESHOLD
except ImportError:
    SMALL_CHANGE_THRESHOLD = 20


def get_change_stats() -> Tuple[int, int, List[str]]:
    """Analyze changes since last archive.
    
    Returns:
        Tuple of (files_changed, lines_changed, list_of_files)
    """
    try:
        # Get diff stats
        result = subprocess.run(
            ['git', 'diff', '--stat', 'HEAD~10'],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            return 0, 0, []
        
        lines = result.stdout.strip().split('\n')
        files_changed = 0
        lines_changed = 0
        changed_files = []
        
        for line in lines[:-1]:  # Skip summary line
            if ' | ' in line:
                files_changed += 1
                filename = line.split(' | ')[0].strip()
                changed_files.append(filename)
                
                # Extract line count
                parts = line.split(' | ')[1].strip().split()
                if parts and parts[0].isdigit():
                    lines_changed += int(parts[0])
        
        return files_changed, lines_changed, changed_files[:10]
        
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 0, 0, []


def suggest_related_docs(changed_files: List[str]) -> List[str]:
    """Suggest possibly related documentation based on changed files.
    
    Simple heuristic: extract base names from changed files.
    """
    suggestions = []
    for f in changed_files[:5]:
        base = os.path.splitext(os.path.basename(f))[0]
        # Skip common non-doc files
        if base not in ('index', 'main', 'app', '__init__', 'test'):
            suggestions.append(base)
    return suggestions[:3]


def print_small_change_message(lines: int, files: List[str]):
    """Print advisory message for small changes."""
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print(f"║         📝 SMALL CHANGE DETECTED ({lines} lines)                ║")
    print("╠════════════════════════════════════════════════════════════╣")
    if files:
        print(f"║  Changed: {', '.join(files[:3])}")
    print("║")
    print("║  This looks like a small change. You can:")
    print("║    1. Archive anyway: run 'Archive Ontos'")
    print("║    2. Skip this time: git push --no-verify")
    print("║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()


def print_large_change_message(files_count: int, lines: int, files: List[str], suggestions: List[str]):
    """Print blocking message for large changes."""
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         ❌ SESSION ARCHIVE REQUIRED                        ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print("║")
    print(f"║  📊 Changes detected: {files_count} files, {lines} lines")
    print("║")
    if files:
        print(f"║  📁 Modified: {', '.join(files[:5])}")
        print("║")
    if suggestions:
        print(f"║  💡 Possibly related docs: {', '.join(suggestions)}")
        print("║")
    print("║  Run: 'Archive Ontos' or:")
    print("║    python3 .ontos/scripts/ontos_end_session.py -e <type>")
    print("║")
    print("║  Emergency bypass: git push --no-verify")
    print("║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()


def print_advisory_message(lines: int):
    """Print non-blocking reminder."""
    print()
    print(f"💡 Reminder: {lines} lines changed. Consider archiving your session.")
    print()


def main() -> int:
    """Main hook logic.
    
    Returns:
        Exit code (0 = allow push, 1 = block push)
    """
    # Check if marker exists (session archived)
    if os.path.exists(MARKER_FILE):
        print()
        print("✅ Session archived. Proceeding with push...")
        print()
        
        # Delete marker (one archive = one push)
        try:
            os.remove(MARKER_FILE)
        except OSError:
            pass
        
        return 0
    
    # Analyze changes
    files_count, lines_count, changed_files = get_change_stats()
    suggestions = suggest_related_docs(changed_files)
    
    # Decide based on config and change size
    if not ENFORCE_ARCHIVE_BEFORE_PUSH:
        # Advisory mode
        print_advisory_message(lines_count)
        return 0
    
    # Blocking mode
    if lines_count < SMALL_CHANGE_THRESHOLD:
        print_small_change_message(lines_count, changed_files)
    else:
        print_large_change_message(files_count, lines_count, changed_files, suggestions)
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

#### Acceptance Criteria

- [ ] Hook is <15 lines of bash (delegation only)
- [ ] All logic in testable Python script
- [ ] Shows change statistics (files, lines)
- [ ] Lists changed files
- [ ] Suggests related docs
- [ ] Small changes (<threshold) get softer message
- [ ] Advisory mode still works
- [ ] New test file: `tests/test_pre_push_check.py`

---

### 3.4 P1: Consolidation Command (REVISED - Fixed Two-Table Bug)

**Problem:** Monthly consolidation is 6 manual steps with no tooling.

**Solution:** `ontos_consolidate.py` with robust table handling.

**Critical Fix (v1.2):** The `decision_history.md` template has TWO tables (History Ledger and Consolidation Log). The original implementation would append to the wrong table. Fixed by targeting the History Ledger header specifically.

**File:** `.ontos/scripts/ontos_consolidate.py` (new)

```python
"""Consolidate old session logs into decision history."""

import os
import re
import sys
import datetime
import argparse
import shutil
from typing import Optional, List, Tuple

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ontos_lib import parse_frontmatter, find_last_session_date
from ontos_config import __version__, PROJECT_ROOT, is_ontos_repo

# Mode-aware paths (from Claude feedback)
if is_ontos_repo():
    DECISION_HISTORY_FILE = os.path.join(PROJECT_ROOT, '.ontos-internal', 'strategy', 'decision_history.md')
    ARCHIVE_DIR = os.path.join(PROJECT_ROOT, '.ontos-internal', 'archive', 'logs')
    from ontos_config import LOGS_DIR
else:
    from ontos_config import DOCS_DIR, LOGS_DIR
    DECISION_HISTORY_FILE = os.path.join(DOCS_DIR, 'decision_history.md')
    ARCHIVE_DIR = os.path.join(DOCS_DIR, 'archive')

# Expected table header for the History Ledger (NOT the Consolidation Log)
HISTORY_LEDGER_HEADER = '| Date | Slug | Event | Decision / Outcome |'


def find_old_logs(threshold_days: int = 30) -> List[Tuple[str, str, dict]]:
    """Find logs older than threshold.
    
    Returns:
        List of (filepath, doc_id, frontmatter) tuples, oldest first.
    """
    if not os.path.exists(LOGS_DIR):
        return []
    
    old_logs = []
    today = datetime.datetime.now()
    
    for filename in sorted(os.listdir(LOGS_DIR)):
        if not filename.endswith('.md'):
            continue
        if not re.match(r'^\d{4}-\d{2}-\d{2}', filename):
            continue
        
        filepath = os.path.join(LOGS_DIR, filename)
        
        try:
            log_date = datetime.datetime.strptime(filename[:10], '%Y-%m-%d')
            age_days = (today - log_date).days
            
            if age_days > threshold_days:
                frontmatter = parse_frontmatter(filepath)
                if frontmatter:
                    old_logs.append((filepath, frontmatter.get('id', filename), frontmatter))
        except ValueError:
            continue
    
    return old_logs


def extract_summary(filepath: str) -> Optional[str]:
    """Extract one-line summary from log's Goal section.
    
    REVISED (v1.2): Relaxed regex to handle adaptive templates where
    numbering may be different or missing (e.g., "## Goal" vs "## 1. Goal").
    
    Returns:
        Summary string, or None if not found.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Relaxed regex: numbering is optional (from Gemini feedback)
    match = re.search(r'##\s*\d*\.?\s*Goal\s*\n(.+?)(?=\n## |\n---|\Z)', content, re.DOTALL)
    if match:
        goal = match.group(1).strip()
        # Remove HTML comments
        goal = re.sub(r'<!--.*?-->', '', goal).strip()
        # Take first non-empty line
        for line in goal.split('\n'):
            line = line.strip().lstrip('- ')
            if line and not line.startswith('<!--'):
                return line[:100]
    
    return None


def validate_decision_history() -> bool:
    """Validate decision_history.md exists and has expected structure.
    
    Returns:
        True if valid, False otherwise.
    """
    if not os.path.exists(DECISION_HISTORY_FILE):
        print(f"Error: {DECISION_HISTORY_FILE} not found.")
        print("Create it with the standard table header, or run 'ontos init'.")
        return False
    
    with open(DECISION_HISTORY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Validate History Ledger header exists (NOT Consolidation Log)
    if HISTORY_LEDGER_HEADER not in content:
        print(f"Error: decision_history.md missing History Ledger table.")
        print(f"Expected header containing: {HISTORY_LEDGER_HEADER}")
        print("Please fix the table structure manually.")
        return False
    
    return True


def append_to_decision_history(
    date: str,
    slug: str,
    event_type: str,
    summary: str,
    impacts: List[str],
    archive_path: str
) -> bool:
    """Append entry to the History Ledger table in decision_history.md.
    
    CRITICAL FIX (v1.2): The file has TWO tables:
    1. History Ledger (where logs go) - has header "| Date | Slug | Event |..."
    2. Consolidation Log (metadata about consolidation acts) - different columns
    
    We must target the History Ledger specifically, not just "the last table".
    """
    if not validate_decision_history():
        return False
    
    # Format new row
    impacts_str = ', '.join(impacts) if impacts else '—'
    # Escape pipe characters in summary
    safe_summary = summary.replace('|', '\\|')
    new_row = f"| {date} | {slug} | {event_type} | {safe_summary} | {impacts_str} | `{archive_path}` |"
    
    # Read file
    with open(DECISION_HISTORY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Find the History Ledger table specifically
    # Strategy: Find the header row, then find the end of THAT table
    # (ends at next ## heading or blank line before ##)
    
    in_history_ledger = False
    history_ledger_end = -1
    
    for i, line in enumerate(lines):
        # Found the History Ledger header
        if HISTORY_LEDGER_HEADER in line:
            in_history_ledger = True
            continue
        
        if in_history_ledger:
            # Still in the table (rows start with |)
            if line.strip().startswith('|'):
                history_ledger_end = i  # Keep updating while we're in the table
            # Hit a section header - table is over
            elif line.strip().startswith('##'):
                break
            # Hit a blank line followed by section header - table is over
            elif not line.strip():
                # Look ahead to see if next non-empty line is a header
                for j in range(i + 1, min(i + 3, len(lines))):
                    if lines[j].strip().startswith('##'):
                        break
                    elif lines[j].strip():
                        # Non-header content, might still be in table area
                        break
                else:
                    # Reached potential end, but keep looking
                    continue
    
    if history_ledger_end == -1:
        # Table header found but no rows yet - insert after separator row
        for i, line in enumerate(lines):
            if HISTORY_LEDGER_HEADER in line:
                # Next line should be the separator |:---|:---|
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('|'):
                    history_ledger_end = i + 1
                    break
    
    if history_ledger_end == -1:
        print("Error: Could not find insertion point in History Ledger table")
        return False
    
    # Insert new row after the last row of the History Ledger
    lines.insert(history_ledger_end + 1, new_row)
    
    # Write back
    with open(DECISION_HISTORY_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return True


def archive_log(filepath: str, dry_run: bool = False) -> Optional[str]:
    """Move log to archive directory.
    
    Returns:
        New archive path (relative), or None on failure.
    """
    filename = os.path.basename(filepath)
    archive_path = os.path.join(ARCHIVE_DIR, filename)
    rel_archive_path = os.path.relpath(archive_path, PROJECT_ROOT)
    
    if dry_run:
        return rel_archive_path
    
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    try:
        shutil.move(filepath, archive_path)
        return rel_archive_path
    except Exception as e:
        print(f"Error archiving {filepath}: {e}")
        return None


def consolidate_log(filepath: str, doc_id: str, frontmatter: dict, 
                    dry_run: bool = False, quiet: bool = False,
                    auto: bool = False) -> bool:
    """Consolidate a single log file."""
    
    filename = os.path.basename(filepath)
    date = filename[:10]
    slug = filename[11:-3] if len(filename) > 14 else doc_id
    event_type = frontmatter.get('event_type', 'chore')
    impacts = frontmatter.get('impacts', [])
    
    summary = extract_summary(filepath)
    
    # Interactive summary fallback (from Gemini feedback)
    if not summary and not auto and not quiet:
        print(f"\n⚠️  Could not auto-extract summary from {doc_id}")
        try:
            summary = input("   Enter one-line summary: ").strip()
        except (EOFError, KeyboardInterrupt):
            summary = "(Manual entry required)"
    
    summary = summary or "(No summary captured)"
    
    if not quiet:
        print(f"\n📄 {doc_id}")
        print(f"   Date: {date}")
        print(f"   Type: {event_type}")
        print(f"   Summary: {summary}")
        print(f"   Impacts: {impacts or '(none)'}")
    
    if dry_run:
        print(f"   [DRY RUN] Would archive to: {ARCHIVE_DIR}/{filename}")
        return True
    
    # Confirm (unless auto mode)
    if not auto:
        try:
            confirm = input(f"   Archive this log? [y/N/edit]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n   Skipped.")
            return False
        
        if confirm == 'edit':
            new_summary = input(f"   New summary: ").strip()
            if new_summary:
                summary = new_summary
            confirm = 'y'
        
        if confirm != 'y':
            print("   Skipped.")
            return False
    
    # Archive file first
    rel_archive_path = archive_log(filepath, dry_run)
    if not rel_archive_path:
        return False
    
    # Append to decision history
    if append_to_decision_history(date, slug, event_type, summary, impacts, rel_archive_path):
        print(f"   ✅ Archived and recorded in decision_history.md")
        return True
    else:
        print(f"   ⚠️  File archived but failed to update decision_history.md")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Consolidate old session logs into decision history.',
        epilog="""
This script helps with the monthly consolidation ritual:
1. Finds logs older than threshold
2. Shows summary for each
3. Prompts for confirmation
4. Archives log and updates decision_history.md (History Ledger table)

Example:
  python3 ontos_consolidate.py              # Interactive consolidation
  python3 ontos_consolidate.py --dry-run    # Preview what would happen
  python3 ontos_consolidate.py --days 60    # Logs older than 60 days
  python3 ontos_consolidate.py --all        # Process all without prompting
"""
    )
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--days', type=int, default=30,
                        help='Age threshold in days (default: 30)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Preview without making changes')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress output')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Process all old logs without prompting')
    
    args = parser.parse_args()
    
    # Validate setup
    if not args.dry_run and not validate_decision_history():
        sys.exit(1)
    
    old_logs = find_old_logs(args.days)
    
    if not old_logs:
        if not args.quiet:
            print(f"✅ No logs older than {args.days} days. Nothing to consolidate.")
        return
    
    if not args.quiet:
        print(f"Found {len(old_logs)} log(s) older than {args.days} days:")
    
    consolidated = 0
    for filepath, doc_id, frontmatter in old_logs:
        if consolidate_log(filepath, doc_id, frontmatter, args.dry_run, args.quiet, args.all):
            consolidated += 1
    
    if not args.quiet:
        action = 'Would consolidate' if args.dry_run else 'Consolidated'
        print(f"\n{action} {consolidated} log(s).")


if __name__ == "__main__":
    main()
```

#### Acceptance Criteria

- [ ] Finds logs older than threshold (default 30 days)
- [ ] Extracts summary from Goal section (with relaxed regex)
- [ ] Prompts for manual summary when extraction fails
- [ ] Validates decision_history.md structure before modifying
- [ ] **Targets History Ledger table specifically (not Consolidation Log)**
- [ ] Aborts cleanly on malformed table (no corruption)
- [ ] Mode-aware paths (User vs Contributor)
- [ ] Moves file to archive directory
- [ ] Appends row to correct table
- [ ] --dry-run shows what would happen
- [ ] --all processes without prompting

---

### 3.5 P1: Query Interface

**Problem:** Graph data exists but can't be queried.

**Solution:** `ontos_query.py` script for common queries.

**File:** `.ontos/scripts/ontos_query.py` (new)

```python
"""Query the Ontos knowledge graph."""

import os
import sys
import argparse
from collections import defaultdict
from datetime import datetime

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ontos_lib import (
    parse_frontmatter,
    normalize_depends_on,
    normalize_type,
    get_git_last_modified,
)
from ontos_config import __version__, DOCS_DIR, SKIP_PATTERNS


def scan_docs_for_query(root_dir: str) -> dict:
    """Scan documentation files for query operations.
    
    Simplified version of scan_docs from ontos_generate_context_map.py.
    """
    files_data = {}
    
    if not os.path.isdir(root_dir):
        return files_data
    
    for subdir, dirs, files in os.walk(root_dir):
        # Prune skipped directories
        dirs[:] = [d for d in dirs if not any(p.rstrip('/') == d for p in SKIP_PATTERNS)]
        
        for file in files:
            if not file.endswith('.md'):
                continue
            if any(pattern in file for pattern in SKIP_PATTERNS):
                continue
            
            filepath = os.path.join(subdir, file)
            frontmatter = parse_frontmatter(filepath)
            
            if frontmatter and frontmatter.get('id'):
                doc_id = str(frontmatter['id']).strip()
                if not doc_id or doc_id.startswith('_'):
                    continue
                
                files_data[doc_id] = {
                    'filepath': filepath,
                    'filename': file,
                    'type': normalize_type(frontmatter.get('type')),
                    'depends_on': normalize_depends_on(frontmatter.get('depends_on')),
                    'status': str(frontmatter.get('status') or 'unknown').strip(),
                    'concepts': frontmatter.get('concepts', []),
                    'impacts': frontmatter.get('impacts', []),
                }
    
    return files_data


def build_graph(files_data: dict) -> tuple:
    """Build adjacency and reverse adjacency lists."""
    depends_on = defaultdict(list)
    depended_by = defaultdict(list)
    
    for doc_id, data in files_data.items():
        deps = data.get('depends_on', [])
        for dep in deps:
            depends_on[doc_id].append(dep)
            depended_by[dep].append(doc_id)
    
    return dict(depends_on), dict(depended_by)


def query_depends_on(files_data: dict, target_id: str) -> list:
    """What does this document depend on?"""
    if target_id not in files_data:
        return []
    return files_data[target_id].get('depends_on', [])


def query_depended_by(files_data: dict, target_id: str) -> list:
    """What documents depend on this one?"""
    _, depended_by = build_graph(files_data)
    return depended_by.get(target_id, [])


def query_concept(files_data: dict, concept: str) -> list:
    """Find all documents with this concept."""
    matches = []
    for doc_id, data in files_data.items():
        concepts = data.get('concepts', [])
        if concept in concepts:
            matches.append(doc_id)
    return matches


def query_stale(files_data: dict, days: int) -> list:
    """Find documents not updated in N days.
    
    Uses git history for accurate dates (from Gemini feedback).
    """
    stale = []
    today = datetime.now()
    
    for doc_id, data in files_data.items():
        filepath = data.get('filepath', '')
        
        # Try git first (from Gemini feedback)
        last_modified = get_git_last_modified(filepath)
        
        if last_modified is None:
            # Fallback: try filename date for logs
            filename = data.get('filename', '')
            if len(filename) >= 10 and filename[4] == '-':
                try:
                    last_modified = datetime.strptime(filename[:10], '%Y-%m-%d')
                except ValueError:
                    pass
        
        if last_modified is None:
            # Final fallback: file mtime (least reliable)
            if os.path.exists(filepath):
                last_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
        
        if last_modified:
            # Handle timezone-aware vs naive datetime
            if last_modified.tzinfo is not None:
                last_modified = last_modified.replace(tzinfo=None)
            age = (today - last_modified).days
            if age > days:
                stale.append((doc_id, age))
    
    return sorted(stale, key=lambda x: -x[1])


def query_health(files_data: dict) -> dict:
    """Calculate graph health metrics."""
    depends_on_graph, depended_by = build_graph(files_data)
    
    # Count by type
    by_type = defaultdict(int)
    for doc_id, data in files_data.items():
        by_type[data.get('type', 'unknown')] += 1
    
    # Orphans
    orphans = []
    for doc_id, data in files_data.items():
        if doc_id not in depended_by:
            if data.get('type') not in ['kernel', 'strategy', 'product', 'log']:
                orphans.append(doc_id)
    
    # Logs with empty impacts
    empty_impacts = []
    for doc_id, data in files_data.items():
        if data.get('type') == 'log':
            if not data.get('impacts'):
                empty_impacts.append(doc_id)
    
    # Connectivity from kernel
    kernels = [d for d, data in files_data.items() if data.get('type') == 'kernel']
    reachable = set()
    
    def traverse(node):
        if node in reachable:
            return
        reachable.add(node)
        for child in depended_by.get(node, []):
            traverse(child)
    
    for k in kernels:
        traverse(k)
    
    connectivity = len(reachable) / len(files_data) * 100 if files_data else 0
    
    return {
        'total_docs': len(files_data),
        'by_type': dict(by_type),
        'orphans': len(orphans),
        'orphan_ids': orphans[:5],
        'empty_impacts': len(empty_impacts),
        'empty_impact_ids': empty_impacts[:5],
        'connectivity': connectivity,
        'reachable_from_kernel': len(reachable),
    }


def format_health(health: dict) -> str:
    """Format health metrics for display."""
    lines = [
        "📊 Graph Health Report",
        "=" * 40,
        f"Total documents: {health['total_docs']}",
        "",
        "By type:",
    ]
    
    for t, count in sorted(health['by_type'].items()):
        lines.append(f"  {t}: {count}")
    
    lines.extend([
        "",
        f"Connectivity: {health['connectivity']:.1f}% reachable from kernel",
        f"Orphans: {health['orphans']}",
    ])
    
    if health['orphan_ids']:
        lines.append(f"  → {', '.join(health['orphan_ids'])}")
    
    lines.append(f"Logs with empty impacts: {health['empty_impacts']}")
    
    if health['empty_impact_ids']:
        lines.append(f"  → {', '.join(health['empty_impact_ids'])}")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Query the Ontos knowledge graph.',
        epilog="""
Examples:
  ontos_query.py --depends-on auth_flow     # What does auth_flow depend on?
  ontos_query.py --depended-by mission      # What depends on mission?
  ontos_query.py --concept auth             # All docs tagged with 'auth'
  ontos_query.py --stale 90                 # Docs not updated in 90 days
  ontos_query.py --health                   # Graph health metrics
  ontos_query.py --list-ids                 # List all document IDs
"""
    )
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--depends-on', metavar='ID',
                       help='What does this document depend on?')
    group.add_argument('--depended-by', metavar='ID',
                       help='What documents depend on this one?')
    group.add_argument('--concept', metavar='TAG',
                       help='Find all documents with this concept')
    group.add_argument('--stale', metavar='DAYS', type=int,
                       help='Find documents not updated in N days')
    group.add_argument('--health', action='store_true',
                       help='Show graph health metrics')
    group.add_argument('--list-ids', action='store_true',
                       help='List all document IDs')
    
    parser.add_argument('--dir', type=str, default=DOCS_DIR,
                        help=f'Documentation directory (default: {DOCS_DIR})')
    
    args = parser.parse_args()
    
    files_data = scan_docs_for_query(args.dir)
    
    if not files_data:
        print(f"No documents found in {args.dir}")
        sys.exit(1)
    
    if args.depends_on:
        results = query_depends_on(files_data, args.depends_on)
        if results:
            print(f"{args.depends_on} depends on:")
            for r in results:
                print(f"  → {r}")
        else:
            print(f"{args.depends_on} has no dependencies (or doesn't exist)")
    
    elif args.depended_by:
        results = query_depended_by(files_data, args.depended_by)
        if results:
            print(f"Documents that depend on {args.depended_by}:")
            for r in results:
                print(f"  ← {r}")
        else:
            print(f"Nothing depends on {args.depended_by}")
    
    elif args.concept:
        results = query_concept(files_data, args.concept)
        if results:
            print(f"Documents with concept '{args.concept}':")
            for r in results:
                print(f"  • {r}")
        else:
            print(f"No documents tagged with '{args.concept}'")
    
    elif args.stale is not None:
        results = query_stale(files_data, args.stale)
        if results:
            print(f"Documents not updated in {args.stale}+ days:")
            for doc_id, age in results:
                print(f"  • {doc_id} ({age} days)")
        else:
            print(f"All documents updated within {args.stale} days")
    
    elif args.health:
        health = query_health(files_data)
        print(format_health(health))
    
    elif args.list_ids:
        print("Document IDs:")
        for doc_id in sorted(files_data.keys()):
            doc_type = files_data[doc_id].get('type', '?')
            print(f"  {doc_id} ({doc_type})")


if __name__ == "__main__":
    main()
```

#### Acceptance Criteria

- [ ] `--depends-on` shows forward dependencies
- [ ] `--depended-by` shows reverse dependencies
- [ ] `--concept` finds all docs with tag
- [ ] `--stale` uses git history (not just mtime)
- [ ] `--health` shows connectivity metrics
- [ ] `--list-ids` helps with ID lookup
- [ ] `--dir` flag for explicit directory override

---

### 3.6 P1: Improved Impact Suggestions

**Problem:** Impact suggestions only look at today's commits.

**Solution:** Extend window to "since last session log."

**File:** `.ontos/scripts/ontos_end_session.py`

```python
from ontos_lib import find_last_session_date, BLOCKED_BRANCH_NAMES

def suggest_impacts(quiet: bool = False) -> list[str]:
    """Suggest document IDs that may have been impacted by recent changes.
    
    REVISED: Now looks back to last session log, not just today.
    """
    try:
        changed_files = set()
        
        # Step 1: Check uncommitted changes
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line[3:].split(' -> ')
                    changed_files.add(parts[-1])
        
        # Step 2: If clean, check commits since last session (REVISED)
        if not changed_files:
            # Use last session date instead of today (from Claude feedback)
            last_session = find_last_session_date()
            since_date = last_session if last_session else datetime.date.today().isoformat()
            
            result = subprocess.run(
                ['git', 'log', f'--since={since_date}', '--name-only', '--pretty=format:'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        changed_files.add(line)
            
            if not quiet and changed_files:
                print(f"ℹ️  No uncommitted changes; checking since {since_date}")
        
        # ... rest of function unchanged
```

---

### 3.7 P2: Creation-Time Concept Validation

**Problem:** Bad concepts discovered at lint time, not creation time.

**Solution:** Validate concepts when creating logs.

**File:** `.ontos/scripts/ontos_end_session.py`

```python
def validate_concepts(concepts: list[str], quiet: bool = False) -> list[str]:
    """Validate concepts against Common_Concepts.md vocabulary.
    
    Returns:
        List of validated concepts (with warnings for unknown).
    """
    from ontos_lib import load_common_concepts
    
    known = load_common_concepts()
    if not known:
        return concepts  # No vocabulary file, skip validation
    
    validated = []
    for concept in concepts:
        if concept in known:
            validated.append(concept)
        else:
            # Find similar concepts for suggestions
            similar = [k for k in known if concept[:3] in k or k[:3] in concept]
            
            if not quiet:
                print(f"⚠️  Unknown concept '{concept}'")
                if similar:
                    print(f"   Did you mean: {', '.join(similar[:3])}?")
                print(f"   See: docs/reference/Common_Concepts.md")
            
            # Still include it (warning, not error)
            validated.append(concept)
    
    return validated

# In main(), after parsing concepts:
if concepts:
    concepts = validate_concepts(concepts, args.quiet)
```

---

### 3.8 P2: Starter Doc Scaffolding

**Problem:** After install, user faces empty `docs/` directory.

**Solution:** `ontos init` creates starter documents in flat structure.

**File:** `ontos_init.py`

```python
# Starter templates with prompting questions

STARTER_MISSION = '''---
id: mission
type: kernel
status: draft
depends_on: []
---

# Mission

<!-- Answer these questions to define your project's core identity -->

## What problem does this project solve?

<!-- Who has this problem? Why does it matter? -->

## What is your one-sentence value proposition?

<!-- "We help [audience] do [outcome] by [method]" -->

## What are your non-negotiables?

<!-- Principles you won't compromise on -->

'''

STARTER_ROADMAP = '''---
id: roadmap
type: strategy
status: draft
depends_on: [mission]
---

# Roadmap

<!-- High-level direction for the project -->

## Current Phase

<!-- What are you building right now? -->

## Next Milestone

<!-- What's the next major goal? -->

## Future Considerations

<!-- Things you're thinking about but not committed to -->

'''

STARTER_DECISION_HISTORY = '''---
id: decision_history
type: strategy
status: active
depends_on: [mission]
---

# Decision History

Permanent ledger of project decisions and their archival locations.

## History Ledger

| Date | Slug | Event | Decision / Outcome | Impacted | Archive Path |
|:-----|:-----|:------|:-------------------|:---------|:-------------|

## Consolidation Log

| Date | Sessions Reviewed | Sessions Archived | Performed By |
|:-----|:------------------|:------------------|:-------------|

'''


def scaffold_starter_docs():
    """Create starter documentation files.
    
    Uses flat structure in docs/ (from Claude feedback).
    """
    # Flat structure - easier for new users
    starters = [
        ('docs/mission.md', STARTER_MISSION),
        ('docs/roadmap.md', STARTER_ROADMAP),
        ('docs/decision_history.md', STARTER_DECISION_HISTORY),
    ]
    
    for filepath, content in starters:
        if not os.path.exists(filepath):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"  Created {filepath}")
        else:
            print(f"  {filepath} already exists")


# In main():
print("\n5. Creating starter documentation...")
scaffold_starter_docs()
```

#### Acceptance Criteria

- [ ] `ontos init` creates mission.md with prompting questions
- [ ] Creates roadmap.md with prompting questions
- [ ] Creates decision_history.md with both tables (History Ledger + Consolidation Log)
- [ ] Uses flat docs/ structure (not nested by type)
- [ ] Doesn't overwrite existing files
- [ ] Files have valid frontmatter

---

### 3.9 P2: Single Maintenance Command

**Problem:** Weekly maintenance requires two commands.

**Solution:** Combined `ontos maintain` that runs both.

**File:** `.ontos/scripts/ontos_maintain.py` (new)

```python
"""Run Ontos maintenance tasks."""

import subprocess
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ontos_config import __version__, PROJECT_ROOT

SCRIPTS_DIR = os.path.join(PROJECT_ROOT, '.ontos', 'scripts')


def run_script(name: str, args: list = None, quiet: bool = False) -> tuple:
    """Run an Ontos script.
    
    Returns:
        Tuple of (success, output)
    """
    script_path = os.path.join(SCRIPTS_DIR, name)
    cmd = [sys.executable, script_path] + (args or [])
    
    if quiet:
        cmd.append('--quiet')
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr


def main():
    parser = argparse.ArgumentParser(
        description='Run Ontos maintenance tasks.',
        epilog="""
This command runs:
1. ontos_migrate_frontmatter.py - Find untagged files
2. ontos_generate_context_map.py - Rebuild graph and validate

Example:
  python3 ontos_maintain.py          # Run maintenance
  python3 ontos_maintain.py --strict # Fail on any issues
  python3 ontos_maintain.py --lint   # Include data quality checks
"""
    )
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--strict', action='store_true', help='Exit with error if issues found')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress output')
    parser.add_argument('--lint', action='store_true', help='Include data quality checks')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("🔧 Running Ontos maintenance...\n")
    
    all_success = True
    
    # Step 1: Check for untagged files
    if not args.quiet:
        print("Step 1: Checking for untagged files...")
    
    migrate_args = []
    if args.strict:
        migrate_args.append('--strict')
    
    success, output = run_script('ontos_migrate_frontmatter.py', migrate_args, args.quiet)
    if not args.quiet and output.strip():
        print(output)
    all_success = all_success and success
    
    # Step 2: Rebuild context map
    if not args.quiet:
        print("\nStep 2: Rebuilding context map...")
    
    generate_args = []
    if args.strict:
        generate_args.append('--strict')
    if args.lint:
        generate_args.append('--lint')
    
    success, output = run_script('ontos_generate_context_map.py', generate_args, args.quiet)
    if not args.quiet and output.strip():
        print(output)
    all_success = all_success and success
    
    # Summary
    if not args.quiet:
        if all_success:
            print("\n✅ Maintenance complete. No issues found.")
        else:
            print("\n⚠️  Maintenance complete with issues. Review output above.")
    
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
```

---

## Part 4: Implementation Phases

### Phase 1: Foundation (Week 1)

**Goal:** Shared library and archive UX improvements.

**Deliverables:**
1. `ontos_lib.py` with shared utilities
2. `is_ontos_repo()` and `SKIP_PATTERNS` in config
3. Refactor existing scripts to use library
4. DEFAULT_SOURCE configuration
5. Auto-slug generation (with blocked branches)
6. --dry-run and --list-concepts flags
7. Adaptive templates by event type

**Success Metric:** Archive command under 30 characters for common cases.

### Phase 2: Tooling (Week 2)

**Goal:** New scripts for querying and maintenance.

**Deliverables:**
1. `ontos_query.py` with all query types
2. `ontos_consolidate.py` with two-table-safe logic
3. `ontos_maintain.py` for single-command maintenance
4. Extended impact suggestion window

**Success Metric:** All three commands functional with --help.

### Phase 3: Guidance (Week 3)

**Goal:** Contextual feedback instead of binary blocking.

**Deliverables:**
1. `ontos_pre_push_check.py` (extracted from hook)
2. Minimal bash hook (delegation only)
3. Creation-time concept validation
4. Starter doc scaffolding

**Success Metric:** Hook shows context; unknown concepts warn immediately.

### Phase 4: Polish (Week 4)

**Goal:** Documentation, testing, release.

**Deliverables:**
1. Update Ontos_Manual.md
2. Update Ontos_Agent_Instructions.md
3. All test files with specified test cases
4. Ontos_CHANGELOG.md v2.3 entries
5. Bump version to 2.3.0

**Success Metric:** All tests pass; CI green.

---

## Part 5: Test Specifications

### Test Cases by Script

#### tests/test_lib.py (NEW)

```python
def test_parse_frontmatter_valid(): ...
def test_parse_frontmatter_missing(): ...
def test_parse_frontmatter_malformed(): ...
def test_normalize_depends_on_none(): ...
def test_normalize_depends_on_string(): ...
def test_normalize_depends_on_list(): ...
def test_normalize_type_none(): ...
def test_normalize_type_valid(): ...
def test_load_common_concepts_found(): ...
def test_load_common_concepts_missing(): ...
def test_get_git_last_modified_tracked(): ...
def test_get_git_last_modified_untracked(): ...
def test_find_last_session_date_with_logs(): ...
def test_find_last_session_date_empty(): ...
def test_blocked_branch_names_contains_main(): ...
```

#### tests/test_config.py (NEW)

```python
def test_is_ontos_repo_contributor_mode(): ...
def test_is_ontos_repo_user_mode(): ...
def test_skip_patterns_contains_archive(): ...
```

#### tests/test_end_session.py

```python
def test_adaptive_template_chore_has_two_sections(): ...
def test_adaptive_template_decision_has_five_sections(): ...
def test_adaptive_template_feature_has_four_sections(): ...
def test_section_numbers_are_sequential(): ...
def test_auto_slug_from_branch_name(): ...
def test_auto_slug_blocks_main_master_dev(): ...
def test_auto_slug_from_commit_message(): ...
def test_auto_slug_returns_none_when_all_fail(): ...
def test_dry_run_does_not_create_file(): ...
def test_list_concepts_prints_vocabulary(): ...
def test_concept_validation_warns_unknown(): ...
def test_concept_validation_suggests_similar(): ...
def test_default_source_used_when_configured(): ...
def test_suggest_impacts_uses_last_session_date(): ...
```

#### tests/test_query.py

```python
def test_depends_on_returns_direct_dependencies(): ...
def test_depends_on_nonexistent_returns_empty(): ...
def test_depended_by_returns_reverse_graph(): ...
def test_depended_by_kernel_shows_all_children(): ...
def test_concept_search_finds_matching_logs(): ...
def test_concept_search_no_matches(): ...
def test_stale_uses_git_log_not_mtime(): ...
def test_stale_handles_fresh_clone(): ...
def test_health_calculates_connectivity(): ...
def test_health_counts_by_type(): ...
def test_health_identifies_orphans(): ...
def test_health_identifies_empty_impacts(): ...
def test_list_ids_includes_all_types(): ...
```

#### tests/test_consolidate.py

```python
def test_find_old_logs_respects_threshold(): ...
def test_find_old_logs_returns_oldest_first(): ...
def test_extract_summary_from_goal_section(): ...
def test_extract_summary_different_numbering(): ...
def test_extract_summary_no_numbering(): ...  # NEW: relaxed regex
def test_extract_summary_missing_returns_none(): ...
def test_validate_decision_history_valid(): ...
def test_validate_decision_history_missing(): ...
def test_validate_decision_history_malformed(): ...
def test_append_targets_history_ledger_not_consolidation_log(): ...  # NEW: two-table fix
def test_append_to_decision_history_adds_row(): ...
def test_append_escapes_pipe_in_summary(): ...
def test_archive_log_moves_file(): ...
def test_archive_log_creates_directory(): ...
def test_mode_aware_paths_contributor(): ...
def test_mode_aware_paths_user(): ...
def test_consolidate_all_skips_prompts(): ...  # NEW: --all flag
```

#### tests/test_pre_push_check.py (NEW)

```python
def test_marker_exists_allows_push(): ...
def test_marker_deleted_after_check(): ...
def test_small_change_shows_soft_message(): ...
def test_large_change_shows_block_message(): ...
def test_advisory_mode_always_allows(): ...
def test_change_stats_parses_git_diff(): ...
def test_suggest_related_docs_from_filenames(): ...
def test_threshold_configurable(): ...
```

#### tests/test_maintain.py

```python
def test_runs_migrate_then_generate(): ...
def test_strict_mode_fails_on_issues(): ...
def test_lint_flag_passed_to_generate(): ...
def test_quiet_suppresses_output(): ...
def test_returns_nonzero_on_failure(): ...
```

---

## Part 6: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Two-table confusion in consolidation | **Eliminated** | High | Target History Ledger header specifically |
| Regex table parsing corrupts data | Low | High | Validate header before modify; append-only strategy |
| Inline Python quoting issues | **Eliminated** | Medium | Extracted to dedicated Python script |
| Auto-slug generates bad names | Low | Low | Block common branches; prompt on failure |
| Code duplication causes drift | **Eliminated** | Medium | Centralized in ontos_lib.py |
| Stale query misleads on fresh clone | Low | Low | Use git history, not mtime |
| Consolidation paths wrong for users | Low | Medium | Mode-aware paths with is_ontos_repo() |
| Goal extraction fails with adaptive templates | Low | Low | Relaxed regex with optional numbering |

---

## Part 7: Success Criteria

### Quantitative

- [ ] Archive command length: 70 chars → <30 chars (typical case)
- [ ] Maintenance commands: 2 → 1
- [ ] Consolidation steps: 6 manual → 1 interactive
- [ ] New query capabilities: 0 → 5 query types
- [ ] Bash hook lines: ~100 → <15 (logic in Python)
- [ ] Code duplication: 3 copies of parse_frontmatter → 1 in lib

### Qualitative

- [ ] Users can archive without looking up syntax
- [ ] Users can query "what depends on X" in one command
- [ ] Pre-push hook provides actionable context
- [ ] New users have starting point after init
- [ ] Hook logic is testable in isolation
- [ ] Table modifications are safe (validate before modify)
- [ ] Consolidation appends to correct table (History Ledger, not Consolidation Log)

---

## Part 8: Feedback Incorporation Record

### Round 1: Initial Review (v1.0 → v1.1)

#### From Gemini Review

| Issue | Severity | Resolution |
|-------|----------|------------|
| Regex table parsing fragility | P0 | Validate header before modify; append-only; abort on mismatch |
| Inline Python in hook | P0 | Extracted to `ontos_pre_push_check.py` |
| Code duplication | P1 | Created `ontos_lib.py` with shared utilities |
| Auto-slug collision on main | P1 | Block main/master/dev/develop branches |
| Goal extraction with dynamic templates | P2 | Interactive fallback when extraction fails |
| Stale uses mtime | P2 | Use git log for true modification date |

#### From Claude Code Review

| Issue | Severity | Resolution |
|-------|----------|------------|
| Auto-slug timestamp fallback | P0 | Prompt user instead of silent fallback |
| Pre-push hook complexity | P0 | (Same as Gemini) Extracted to Python |
| Starter doc directory convention | P1 | Flat docs/ structure for simplicity |
| Consolidation paths for User Mode | P1 | Mode-aware paths using is_ontos_repo() |
| Missing test specs | P1 | Added detailed test case list per script |
| Missing --concepts lookup | P2 | Added --list-concepts flag |
| Impact window today-only | P2 | Extended to since last session log |
| SMALL_CHANGE_THRESHOLD arbitrary | P3 | Added documentation comment |
| Missing changelog entries | P3 | Added full changelog text |
| Query mode handling | P3 | Documented --dir flag override |

---

### Round 2: Final Review (v1.1 → v1.2)

#### From Gemini Review

| Issue | Severity | Resolution |
|-------|----------|------------|
| **Two-table trap in consolidation** | **P0** | **Fixed: Target History Ledger header specifically, not "last table row"** |
| Goal extraction regex too strict | P2 | Relaxed to `r'##\s*\d*\.?\s*Goal'` (numbering optional) |
| CLI summary edit is painful | P3 | Noted for v2.4: spawn `$EDITOR` |
| sys.executable drift risk | P3 | Documented assumption |

#### From Claude Code Review

| Issue | Severity | Resolution |
|-------|----------|------------|
| `is_ontos_repo()` not defined | P2 | Added to config defaults |
| Missing import `find_last_session_date` | P2 | Added to imports from ontos_lib |
| `SKIP_PATTERNS` not shown | P2 | Added to config defaults |
| Missing test for `--all` flag | P3 | Added `test_consolidate_all_skips_prompts()` |
| Path alignment verification | P3 | Verified DOCS_DIR = 'docs' alignment |

---

### Round 3: Final Polish (v1.2 → v1.3)

#### From Claude Code Review

| Issue | Severity | Resolution |
|-------|----------|------------|
| Defensive table detection | P3 | Added sanity check warning when multiple tables exist but header not found |

#### From Gemini Review

| Issue | Severity | Resolution |
|-------|----------|------------|
| Hook installation sync | P3 | Documented that source hook changes don't auto-update .git/hooks |
| Header constant coupling | P3 | Added SYNC comments cross-referencing ontos_init.py and ontos_consolidate.py |

---

### Explicitly Deferred

| Item | Reason | Target Version |
|------|--------|----------------|
| Version check on activation | Requires network call to GitHub | v2.4 |
| `$EDITOR` spawning for summary edit | Adds complexity, CLI input works | v2.4 |
| Package management (pip/npm) | Adds complexity, reduces portability | v3.0 |
| Smart dependency suggestions | Requires semantic analysis | v3.0 |

---

## Appendix A: Files Changed

### New Files

- `.ontos/scripts/ontos_lib.py`
- `.ontos/scripts/ontos_query.py`
- `.ontos/scripts/ontos_consolidate.py`
- `.ontos/scripts/ontos_maintain.py`
- `.ontos/scripts/ontos_pre_push_check.py`
- `tests/test_lib.py`
- `tests/test_config.py`
- `tests/test_query.py`
- `tests/test_consolidate.py`
- `tests/test_maintain.py`
- `tests/test_pre_push_check.py`
- `tests/test_end_session.py`

### Modified Files

- `.ontos/scripts/ontos_config_defaults.py` (is_ontos_repo, SKIP_PATTERNS, DEFAULT_SOURCE, SMALL_CHANGE_THRESHOLD)
- `.ontos/scripts/ontos_end_session.py` (templates, auto-slug, dry-run, concept validation, imports)
- `.ontos/scripts/ontos_generate_context_map.py` (import from lib)
- `.ontos/hooks/pre-push`
- `ontos_init.py`
- `docs/reference/Ontos_Manual.md`
- `docs/reference/Ontos_Agent_Instructions.md`
- `Ontos_CHANGELOG.md`

---

## Appendix B: Changelog Entries

```markdown
## [2.3.0] - 2025-XX-XX

### Added
- **Shared utilities library** (`ontos_lib.py`) — Centralized common functions
- **Adaptive templates** — Log templates scale to event type (chore=2, decision=5 sections)
- **`decision` event type** — For architectural choices requiring full documentation
- **Query interface** (`ontos_query.py`) — Query graph: `--depends-on`, `--depended-by`, `--concept`, `--stale`, `--health`, `--list-ids`
- **Consolidation command** (`ontos_consolidate.py`) — Interactive archival of old logs
- **Maintenance command** (`ontos_maintain.py`) — Single command for weekly maintenance
- **DEFAULT_SOURCE config** — Set once, never type `-s "Claude Code"` again
- **Auto-slug generation** — From branch name or commit message
- **Dry-run mode** (`--dry-run`) — Preview archive output before creating
- **`--list-concepts` flag** — Quick vocabulary lookup
- **Contextual pre-push hook** — Shows change stats, file list, suggested docs
- **Creation-time concept validation** — Warns on unknown concepts immediately
- **Starter doc scaffolding** — `ontos init` creates mission.md, roadmap.md, decision_history.md
- **`is_ontos_repo()` helper** — Detects contributor vs user mode
- **`SKIP_PATTERNS` config** — Centralized list of files/dirs to skip when scanning

### Changed
- Pre-push hook logic extracted to testable Python script
- Impact suggestions now look back to last session (not just today)
- Stale document detection uses git history (not file mtime)
- Consolidation validates table structure before modifying
- Consolidation targets History Ledger table specifically (ignores Consolidation Log)
- Auto-slug blocks common branch names (main, master, dev)
- Goal extraction regex relaxed to handle adaptive template numbering variations

### Fixed
- Fresh git clone no longer shows all docs as "stale"
- Consolidation no longer corrupts decision_history.md on malformed tables
- Consolidation no longer appends to wrong table in two-table files
- Auto-slug prompts user instead of generating meaningless timestamps
```

---

## Appendix C: Agent Instructions Update

Add to `docs/reference/Ontos_Agent_Instructions.md`:

```markdown
### New Commands (v2.3)

#### Query the Graph
```bash
python3 .ontos/scripts/ontos_query.py --health           # Graph health metrics
python3 .ontos/scripts/ontos_query.py --depended-by X    # What depends on X?
python3 .ontos/scripts/ontos_query.py --depends-on X     # What does X depend on?
python3 .ontos/scripts/ontos_query.py --concept auth     # Find by concept
python3 .ontos/scripts/ontos_query.py --stale 90         # Docs >90 days old
python3 .ontos/scripts/ontos_query.py --list-ids         # All document IDs
```

#### Consolidate Old Logs
```bash
python3 .ontos/scripts/ontos_consolidate.py             # Interactive
python3 .ontos/scripts/ontos_consolidate.py --dry-run   # Preview
python3 .ontos/scripts/ontos_consolidate.py --days 60   # Custom threshold
python3 .ontos/scripts/ontos_consolidate.py --all       # Batch mode (no prompts)
```

#### Archive (Simplified)
```bash
# With DEFAULT_SOURCE configured in ontos_config.py:
python3 .ontos/scripts/ontos_end_session.py -e feature  # Auto-slug
python3 .ontos/scripts/ontos_end_session.py -e chore    # 2-section template
python3 .ontos/scripts/ontos_end_session.py -e decision # Full 5-section template
python3 .ontos/scripts/ontos_end_session.py --dry-run   # Preview first
python3 .ontos/scripts/ontos_end_session.py --list-concepts  # Show vocabulary
```

#### Single Maintenance Command
```bash
python3 .ontos/scripts/ontos_maintain.py                # Run all checks
python3 .ontos/scripts/ontos_maintain.py --lint         # Include data quality
python3 .ontos/scripts/ontos_maintain.py --strict       # Fail on issues
```
```

---

## Appendix D: Implementation Notes for Agents

When implementing this plan, note the following:

1. **`is_ontos_repo()` must exist** — If not already in the codebase, add to `ontos_config_defaults.py` as specified in Section 3.0.1

2. **`SKIP_PATTERNS` must exist** — Verify it's in config or add as specified in Section 3.0.1

3. **Import statements** — When refactoring `ontos_end_session.py`, add:
   ```python
   from ontos_lib import find_last_session_date, BLOCKED_BRANCH_NAMES, load_common_concepts
   ```

4. **Two-table safety** — The consolidation script MUST target the History Ledger table specifically. The `HISTORY_LEDGER_HEADER` constant identifies which table to append to.

5. **Test the two-table scenario** — Create a decision_history.md with both tables and verify consolidation appends to the first table only.

6. **Defensive table detection** — Add a sanity check if multiple tables exist but the expected header isn't found:
   ```python
   if content.count('| Date |') > 1 and HISTORY_LEDGER_HEADER not in content:
       print("Warning: Multiple tables detected but History Ledger header not found.")
       print("This may indicate a custom table format. Please verify manually.")
       return False
   ```

7. **Hook installation sync** — Modifying `.ontos/hooks/pre-push` in the codebase does NOT automatically update the active hook in `.git/hooks/pre-push` for existing users. After implementation, run `python3 .ontos/scripts/ontos_install_hooks.py` (or equivalent) to apply changes locally. Document this in release notes for existing users.

8. **Header constant coupling** — `HISTORY_LEDGER_HEADER` in `ontos_consolidate.py` must match the table header in `STARTER_DECISION_HISTORY` in `ontos_init.py`. If you change one, you must change the other. Add cross-reference comments in both locations:
   ```python
   # SYNC: Must match STARTER_DECISION_HISTORY in ontos_init.py
   HISTORY_LEDGER_HEADER = '| Date | Slug | Event | Decision / Outcome |'
   ```
   
   ```python
   # SYNC: Must match HISTORY_LEDGER_HEADER in ontos_consolidate.py
   ## History Ledger
   | Date | Slug | Event | Decision / Outcome | Impacted | Archive Path |
   ```

---

## Appendix E: Version History

| Version | Theme | Key Features |
|---------|-------|--------------|
| 2.0.0 | Dual Ontology | Space/Time separation, impacts field, log type |
| 2.1.0 | Smart Memory | Decision history, consolidation ritual |
| 2.2.0 | Data Quality | Common concepts, lint mode |
| **2.3.0** | **Less Typing, More Insight** | **Adaptive templates, query interface, contextual hook, shared library** |
| 2.4.0 (planned) | Awareness | Version checking, $EDITOR integration |
| 3.0.0 (planned) | Distribution | Package management, semantic queries |
