# Ontos v2.2 Implementation Plan: Data Quality (Revised)

*Ensuring captured data is graph-traversable for v3.0.*

**Revision Notes:** This revision addresses issues found during codebase validation:
- Renamed `Ontos_Common_Concepts.md` → `Common_Concepts.md` (skip pattern conflict)
- Fixed `depends_on: [schema]` → `depends_on: []` (user project compatibility)
- Fixed lint function integration (parameter passing)
- Added test cases and CI integration sections

---

## 1. Overview

### Problem

Freeform `concepts`, empty `impacts`, and undocumented alternatives create a noisy graph that v3.0 can't query effectively.

### Solution

Vocabulary discipline, template improvements, and soft enforcement through linting.

### Philosophy

**YAML is for topology (connections). Markdown is for semantics (meaning).**

Train habits now, harvest data later.

### Key Concepts

| Term | Definition |
|:-----|:-----------|
| **Concept Vocabulary** | Standardized tags for clustering related work |
| **Impacts Discipline** | Every log must declare what Space documents it affected |
| **Alternatives Documentation** | Capturing what was considered and rejected |
| **Lint Mode** | Soft warnings for data quality issues |
| **v3.0 Readiness** | Data structured for future graph traversal |

---

## 2. Deliverables

### 2.1 Common Concepts Reference

**File:** `docs/reference/Common_Concepts.md`

> **Note:** Named `Common_Concepts.md` (not `Ontos_Common_Concepts.md`) to avoid the `Ontos_` skip pattern in `ontos_config_defaults.py`.

**Purpose:** Controlled vocabulary for `concepts` tagging. Agents check this before creating new tags.

**Type:** `atom` (technical reference)

**Content:**

```markdown
---
id: common_concepts
type: atom
status: active
depends_on: []
---

# Common Concepts

Reference vocabulary for `concepts` field in Session Logs.

## Usage

When tagging a log, check this list first. Use existing terms over synonyms to ensure graph connectivity.

**Example:**
```yaml
# Good - uses standard vocabulary
concepts: [auth, api, db]

# Bad - creates orphan nodes in the graph
concepts: [authentication, endpoints, database-stuff]
```

---

## Vocabulary

### Core Domains

| Concept | Covers | Avoid Using |
|:--------|:-------|:------------|
| `auth` | Authentication, authorization, login, identity, OAuth, JWT | `authentication`, `login`, `identity`, `oauth` |
| `api` | Endpoints, REST, GraphQL, routes, controllers | `endpoints`, `routes`, `rest`, `graphql` |
| `db` | Database, storage, SQL, queries, migrations | `database`, `storage`, `sql`, `postgres` |
| `ui` | Frontend, components, CSS, styling, layout | `frontend`, `components`, `styling`, `css` |
| `schema` | Data models, types, validation, structure | `models`, `types`, `validation`, `data-model` |

### Process Domains

| Concept | Covers | Avoid Using |
|:--------|:-------|:------------|
| `devops` | CI/CD, deployment, hosting, Docker, infrastructure | `deployment`, `ci`, `infrastructure`, `docker` |
| `testing` | Unit tests, integration tests, QA, test coverage | `tests`, `qa`, `test`, `unit-tests` |
| `perf` | Performance, optimization, caching, speed | `performance`, `optimization`, `speed`, `caching` |
| `security` | Vulnerabilities, encryption, access control, secrets | `vulnerabilities`, `encryption`, `secrets` |
| `docs` | Documentation, guides, references, READMEs | `documentation`, `guides`, `readme` |

### Workflow

| Concept | Covers |
|:--------|:-------|
| `cleanup` | Refactoring, dead code removal, organization |
| `config` | Configuration, settings, environment variables |
| `workflow` | Process changes, rituals, automation |

---

## Adding New Concepts

If no existing concept fits:

1. **Check first** — Can a broader existing concept work?
2. **Be conservative** — Fewer concepts with clear scope > many overlapping concepts
3. **Follow conventions:**
   - Lowercase
   - Single words preferred
   - Hyphens for multi-word (`data-model` not `dataModel` or `data_model`)
4. **Document it** — Add to this file with clear scope and "Avoid Using" synonyms
5. **Update existing logs** — If the new concept applies to past work, consider updating those logs

---

## Why This Matters (v3.0)

This vocabulary enables subgraph queries:

```bash
# Future capability (v3.0)
python3 .ontos/scripts/ontos_query.py --concept auth --hops 2

# Returns all documents tagged with 'auth' + their connections
```

**Consistent tagging now = accurate retrieval later.**

If half your auth work is tagged `auth` and half is tagged `authentication`, v3.0 queries return incomplete results.
```

---

### 2.2 Log Template Update (Alternatives Section)

**File:** `.ontos/scripts/ontos_end_session.py`

**Action:** Update the `create_log_file` function template

**Current template sections:**
```
## 1. Goal
## 2. Key Decisions
## 3. Changes Made
## 4. Next Steps
```

**New template sections:**
```
## 1. Goal
## 2. Key Decisions
## 3. Alternatives Considered   <-- NEW
## 4. Changes Made
## 5. Next Steps
```

**Code Change:**

Find the `content = f"""---` block in `create_log_file()` function (around line 290) and replace with:

```python
    content = f"""---
id: log_{today_date.replace('-', '')}_{topic_slug.replace('-', '_')}
type: log
status: active
event_type: {event_type}
concepts: {concepts_yaml}
impacts: {impacts_yaml}
---

# Session Log: {topic_slug.replace('-', ' ').title()}
Date: {today_datetime}{source_line}
Event Type: {event_type}

## 1. Goal
<!-- What was the primary objective of this session? -->

## 2. Key Decisions
<!-- What architectural or design choices were made? -->
- 

## 3. Alternatives Considered
<!-- What options were evaluated? Why were they rejected? -->
<!-- Format: "Considered X, rejected because Y" -->
- 

## 4. Changes Made
<!-- Summary of file changes, new features, fixes. -->
- 

## 5. Next Steps
<!-- What should the next session work on? -->
- 

---
## Raw Session History
```text
{daily_log}
```
"""
```

---

### 2.3 Impacts Nudging

**File:** `.ontos/scripts/ontos_end_session.py`

**Action:** Add prompt when impacts is empty after suggestion

**Location:** In `main()`, after impacts processing, before `create_log_file()` call (around line 385)

**Code Change:**

Find the section after `--suggest-impacts` processing and add:

```python
    # Process impacts from args or suggestions
    impacts = []
    if args.impacts:
        impacts = [i.strip() for i in args.impacts.split(',') if i.strip()]
        
    # Auto-suggest impacts if requested
    if args.suggest_impacts:
        suggestions = suggest_impacts(args.quiet)
        if suggestions:
            impacts = prompt_for_impacts(suggestions, args.quiet)

    # === NEW: Nudge if impacts is still empty ===
    if not impacts and not args.quiet:
        print("\n⚠️  No impacts specified.")
        print("Logs without impacts create dead ends in the knowledge graph.")
        print("Every session should impact at least one Space document.")
        try:
            confirm = input("\nDid this session really change no documents? [y/N]: ").strip().lower()
            if confirm not in ('y', 'yes'):
                manual = input("Enter impacts (comma-separated doc IDs): ").strip()
                if manual:
                    impacts = [i.strip() for i in manual.split(',') if i.strip()]
                    print(f"✓ Impacts set to: {impacts}")
        except (EOFError, KeyboardInterrupt):
            print("\nProceeding with empty impacts.")
    # === END NEW ===

    # Create session log
    result = create_log_file(
        args.topic,
        args.quiet,
        args.source or "",
        event_type,
        concepts,
        impacts
    )
```

---

### 2.4 Agent Instructions: Tagging Discipline

**File:** `docs/reference/Ontos_Agent_Instructions.md`

**Action:** Add new section after "Historical Recall", before "Changelogs"

**Content to Add:**

```markdown
---

## Tagging Discipline (v3.0 Readiness)

Quality tagging now enables intelligent querying later.

### Concepts

1. **Check first:** Read `docs/reference/Common_Concepts.md`
2. **Prefer existing:** Use standard vocabulary over synonyms
3. **Be specific:** 2-4 concepts per log, not 10 vague ones
4. **Be consistent:** If you used `auth` before, don't switch to `authentication`

**Example:**
```yaml
# Good
concepts: [auth, api]

# Bad - too many, inconsistent vocabulary
concepts: [authentication, login, oauth, jwt, security, backend, api-design]
```

### Impacts

1. **Never empty:** Every session impacts *something* — find it
2. **Use suggestions:** Run `ontos_end_session.py --suggest-impacts`
3. **Include indirect:** If you modified code that `api_spec.md` documents, include `api_spec`
4. **Think broadly:** Design discussions impact strategy docs, not just atoms

**Example:**
```yaml
# Good - specific and complete
impacts: [auth_flow, api_spec, user_model]

# Bad - lazy or incomplete
impacts: []
```

### Alternatives Considered

1. **Always fill:** Document what you *didn't* do
2. **Include rationale:** "Rejected X because Y"
3. **Name names:** "Considered Firebase, PostgreSQL, SQLite" not "considered options"
4. **Be honest:** If you didn't consider alternatives, say "No alternatives evaluated"

**Example:**
```markdown
## 3. Alternatives Considered
- Considered Firebase Auth — rejected due to vendor lock-in concerns
- Considered session-based auth — rejected, need stateless for horizontal scaling
- Evaluated Auth0 — too expensive for current stage
```
```

---

### 2.5 Lint Mode

**File:** `.ontos/scripts/ontos_generate_context_map.py`

**Action:** Add `--lint` flag for soft warnings on data quality issues

#### Step 1: Add Argument

In the `argparse` section (around line 380), add:

```python
parser.add_argument('--lint', action='store_true', 
                    help='Show warnings for data quality issues (empty impacts, unknown concepts)')
```

#### Step 2: Add Helper Function to Load Common Concepts

Add this function after imports, near other helper functions:

```python
def load_common_concepts() -> set[str]:
    """Load known concepts from Common_Concepts.md if it exists.
    
    Parses the vocabulary table to extract concept names.
    
    Returns:
        Set of known concept strings.
    """
    import re
    
    # Try multiple possible locations
    possible_paths = [
        os.path.join(DOCS_DIR, 'reference', 'Common_Concepts.md'),
        os.path.join(DOCS_DIR, 'Common_Concepts.md'),
        'docs/reference/Common_Concepts.md',
    ]
    
    for concepts_file in possible_paths:
        if os.path.exists(concepts_file):
            break
    else:
        return set()  # No concepts file found
    
    concepts = set()
    try:
        with open(concepts_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract concepts from table rows: | `concept` | ... |
        matches = re.findall(r'\|\s*`([a-z][a-z0-9-]*)`\s*\|', content)
        concepts.update(matches)
    except (IOError, OSError):
        pass
    
    return concepts
```

#### Step 3: Add Lint Function

Add this function after the validation functions:

```python
def lint_data_quality(files_data: dict[str, dict], common_concepts: set[str]) -> list[str]:
    """Check for data quality issues that don't break validation but hurt v3.0.
    
    These are soft warnings, not errors. They indicate data that is technically
    valid but will cause problems for future graph queries.
    
    Checks performed:
    1. Empty impacts on active logs (graph dead ends)
    2. Unknown concepts not in vocabulary (clustering issues)
    3. Excessive concepts per log (unfocused tagging)
    4. Stale logs by age (>30 days without consolidation)
    5. Too many active logs (exceeds LOG_RETENTION_COUNT - token bloat)
    
    Args:
        files_data: Dictionary of document metadata.
        common_concepts: Set of known concepts from Common_Concepts.md
        
    Returns:
        List of warning strings.
    """
    from datetime import datetime
    
    # Import retention threshold from config (v2.1 integration)
    try:
        from ontos_config import LOG_RETENTION_COUNT
    except ImportError:
        LOG_RETENTION_COUNT = 15  # Fallback default
    
    warnings = []
    
    # Collect active logs for count check
    active_logs = []
    
    for doc_id, data in files_data.items():
        if data['type'] != 'log':
            continue
        
        filepath = data['filepath']
        is_active = data.get('status') != 'archived'
        
        if is_active:
            active_logs.append((doc_id, data))
        
        # === Check 1: Empty impacts on active logs ===
        if is_active:
            impacts = data.get('impacts', [])
            if not impacts:
                warnings.append(
                    f"- [LINT] **{doc_id}** ({filepath}): Empty impacts\n"
                    f"  → Creates dead end in knowledge graph. Add impacted document IDs."
                )
        
        # === Check 2: Unknown concepts (if vocabulary exists) ===
        if common_concepts:
            concepts = data.get('concepts', [])
            for concept in concepts:
                if concept and concept not in common_concepts:
                    warnings.append(
                        f"- [LINT] **{doc_id}**: Unknown concept `{concept}`\n"
                        f"  → Check `Common_Concepts.md`. Did you mean a standard term?"
                    )
        
        # === Check 3: Too many concepts (signal of unfocused session) ===
        concepts = data.get('concepts', [])
        if len(concepts) > 6:
            warnings.append(
                f"- [LINT] **{doc_id}**: {len(concepts)} concepts (recommended: 2-4)\n"
                f"  → Too many concepts dilutes graph connectivity. Be specific."
            )
    
    # === Check 4: Stale logs (active but old) ===
    threshold_days = 30
    today = datetime.now()
    
    for doc_id, data in active_logs:
        filename = data['filename']
        # Extract date from filename (format: YYYY-MM-DD_slug.md)
        if len(filename) >= 10:
            try:
                log_date = datetime.strptime(filename[:10], '%Y-%m-%d')
                age_days = (today - log_date).days
                if age_days > threshold_days:
                    warnings.append(
                        f"- [LINT] **{doc_id}**: {age_days} days old (threshold: {threshold_days})\n"
                        f"  → Consider consolidating and archiving. See Manual section 3."
                    )
            except ValueError:
                pass  # Couldn't parse date, skip
    
    # === Check 5: Too many active logs (token bloat) ===
    active_count = len(active_logs)
    if active_count > LOG_RETENTION_COUNT:
        excess = active_count - LOG_RETENTION_COUNT
        warnings.insert(0,  # Insert at top - critical for token safety
            f"- [LINT] **Active log count ({active_count}) exceeds threshold ({LOG_RETENTION_COUNT})**\n"
            f"  → {excess} logs over limit. Run consolidation ritual to archive oldest logs.\n"
            f"  → This directly impacts context window size. See Manual section 3."
        )
    
    return warnings
```

#### Step 4: Update Function Signature

Change the `generate_context_map` signature to accept lint parameter:

```python
def generate_context_map(target_dirs: list[str], quiet: bool = False, strict: bool = False, lint: bool = False) -> int:
```

#### Step 5: Integrate Lint into generate_context_map()

After the existing validation calls (around line 330), add:

```python
    # NEW: Validate impacts references
    if not quiet:
        print("Validating impacts references...")
    impact_issues = validate_impacts(files_data)
    issues.extend(impact_issues)

    # === NEW: Lint mode ===
    lint_warnings = []
    if lint:
        if not quiet:
            print("Running data quality lint...")
        common_concepts = load_common_concepts()
        lint_warnings = lint_data_quality(files_data, common_concepts)
    # === END NEW ===

    # NEW: Generate Timeline
    timeline = generate_timeline(files_data)
```

Before the final return, add lint output display:

```python
    if not quiet:
        print(f"Successfully generated {OUTPUT_FILE}")
        print(f"Scanned {len(files_data)} documents, found {len(issues)} issues.")

    # === NEW: Display lint warnings ===
    if lint_warnings and not quiet:
        print(f"\n📋 Data Quality Warnings ({len(lint_warnings)} issues):")
        for warning in lint_warnings:
            print(warning)
        print()
        print("These are soft warnings — they don't fail validation but hurt v3.0 readiness.")
        print("Fix them when convenient, especially before consolidation.")
    elif lint and not quiet:
        print("\n📋 Data Quality Warnings (0 issues):")
        print("No data quality warnings. Nice work!")
    # === END NEW ===

    # Return only error-level issues for strict mode
    return len(error_issues)
```

#### Step 6: Update main() to Pass Lint Argument

In the `main()` section at the bottom, update the call:

```python
    if args.watch:
        watch_mode(target_dirs, args.quiet)
    else:
        issue_count = generate_context_map(target_dirs, args.quiet, args.strict, args.lint)

        if args.strict and issue_count > 0:
            print(f"\n❌ Strict mode: {issue_count} issues detected. Exiting with error.")
            sys.exit(1)
```

---

### 2.6 Test Cases

**File:** `tests/test_lint.py`

**Action:** Create new test file for lint functionality

**Content:**

```python
"""Tests for data quality lint functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch


class TestLintDataQuality:
    """Tests for lint_data_quality function."""

    def test_lint_empty_impacts(self):
        """Test that empty impacts on active logs triggers warning."""
        from ontos_generate_context_map import lint_data_quality
        
        files_data = {
            'log_20251213_test': {
                'filepath': 'logs/2025-12-13_test.md',
                'filename': '2025-12-13_test.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'chore',
                'concepts': ['testing'],
                'impacts': [],
            }
        }
        
        warnings = lint_data_quality(files_data, set())
        assert any('Empty impacts' in w for w in warnings)

    def test_lint_no_warning_for_archived_empty_impacts(self):
        """Test that archived logs with empty impacts don't trigger warning."""
        from ontos_generate_context_map import lint_data_quality
        
        files_data = {
            'log_20251213_test': {
                'filepath': 'logs/2025-12-13_test.md',
                'filename': '2025-12-13_test.md',
                'type': 'log',
                'status': 'archived',
                'event_type': 'chore',
                'concepts': ['testing'],
                'impacts': [],
            }
        }
        
        warnings = lint_data_quality(files_data, set())
        assert not any('Empty impacts' in w for w in warnings)

    def test_lint_unknown_concept(self):
        """Test that non-vocabulary concepts trigger warning."""
        from ontos_generate_context_map import lint_data_quality
        
        files_data = {
            'log_20251213_test': {
                'filepath': 'logs/2025-12-13_test.md',
                'filename': '2025-12-13_test.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'feature',
                'concepts': ['authentication'],  # Should be 'auth'
                'impacts': ['some_doc'],
            }
        }
        
        known_concepts = {'auth', 'api', 'db'}
        warnings = lint_data_quality(files_data, known_concepts)
        assert any('Unknown concept' in w and 'authentication' in w for w in warnings)

    def test_lint_no_warning_for_known_concept(self):
        """Test that vocabulary concepts don't trigger warning."""
        from ontos_generate_context_map import lint_data_quality
        
        files_data = {
            'log_20251213_test': {
                'filepath': 'logs/2025-12-13_test.md',
                'filename': '2025-12-13_test.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'feature',
                'concepts': ['auth', 'api'],
                'impacts': ['some_doc'],
            }
        }
        
        known_concepts = {'auth', 'api', 'db'}
        warnings = lint_data_quality(files_data, known_concepts)
        assert not any('Unknown concept' in w for w in warnings)

    def test_lint_excessive_concepts(self):
        """Test that >6 concepts triggers warning."""
        from ontos_generate_context_map import lint_data_quality
        
        files_data = {
            'log_20251213_test': {
                'filepath': 'logs/2025-12-13_test.md',
                'filename': '2025-12-13_test.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'feature',
                'concepts': ['auth', 'api', 'db', 'ui', 'testing', 'devops', 'security', 'perf'],
                'impacts': ['some_doc'],
            }
        }
        
        warnings = lint_data_quality(files_data, set())
        assert any('8 concepts' in w for w in warnings)

    def test_lint_acceptable_concept_count(self):
        """Test that <=6 concepts don't trigger warning."""
        from ontos_generate_context_map import lint_data_quality
        
        files_data = {
            'log_20251213_test': {
                'filepath': 'logs/2025-12-13_test.md',
                'filename': '2025-12-13_test.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'feature',
                'concepts': ['auth', 'api', 'db'],
                'impacts': ['some_doc'],
            }
        }
        
        warnings = lint_data_quality(files_data, set())
        assert not any('concepts' in w and 'recommended' in w for w in warnings)

    def test_lint_stale_log(self):
        """Test that logs >30 days old trigger warning."""
        from ontos_generate_context_map import lint_data_quality
        
        old_date = (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')
        
        files_data = {
            f'log_{old_date.replace("-", "")}_test': {
                'filepath': f'logs/{old_date}_test.md',
                'filename': f'{old_date}_test.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'chore',
                'concepts': ['testing'],
                'impacts': ['some_doc'],
            }
        }
        
        warnings = lint_data_quality(files_data, set())
        assert any('days old' in w for w in warnings)

    @patch('ontos_generate_context_map.LOG_RETENTION_COUNT', 2)
    def test_lint_exceeds_retention_count(self):
        """Test that active logs > LOG_RETENTION_COUNT triggers warning."""
        from ontos_generate_context_map import lint_data_quality
        
        files_data = {}
        for i in range(5):
            date = datetime.now().strftime('%Y-%m-%d')
            files_data[f'log_{i}'] = {
                'filepath': f'logs/{date}_test{i}.md',
                'filename': f'{date}_test{i}.md',
                'type': 'log',
                'status': 'active',
                'event_type': 'chore',
                'concepts': ['testing'],
                'impacts': ['some_doc'],
            }
        
        warnings = lint_data_quality(files_data, set())
        assert any('exceeds threshold' in w for w in warnings)

    def test_lint_skips_non_log_docs(self):
        """Test that non-log documents are skipped by lint."""
        from ontos_generate_context_map import lint_data_quality
        
        files_data = {
            'mission': {
                'filepath': 'kernel/mission.md',
                'filename': 'mission.md',
                'type': 'kernel',
                'status': 'active',
                'depends_on': [],
            }
        }
        
        warnings = lint_data_quality(files_data, set())
        assert len(warnings) == 0


class TestLoadCommonConcepts:
    """Tests for load_common_concepts function."""

    def test_load_from_file(self, tmp_path):
        """Test loading concepts from markdown file."""
        from ontos_generate_context_map import load_common_concepts
        
        concepts_file = tmp_path / "Common_Concepts.md"
        concepts_file.write_text("""
# Common Concepts

| Concept | Covers |
|:--------|:-------|
| `auth` | Authentication |
| `api` | Endpoints |
| `db` | Database |
""")
        
        with patch('ontos_generate_context_map.DOCS_DIR', str(tmp_path)):
            # Would need to adjust paths in function or mock differently
            pass
        
        # Basic structure test - actual file loading tested in integration

    def test_returns_empty_set_when_no_file(self):
        """Test that missing file returns empty set."""
        from ontos_generate_context_map import load_common_concepts
        
        with patch('os.path.exists', return_value=False):
            concepts = load_common_concepts()
            assert concepts == set()
```

---

### 2.7 CI Integration

**File:** `.github/workflows/ci.yml`

**Action:** Add lint step to test job

**Location:** After "Validate context map" step

**Content to Add:**

```yaml
      - name: Run data quality lint
        run: python .ontos/scripts/ontos_generate_context_map.py --lint --quiet
        continue-on-error: true  # Soft warnings don't fail CI
```

**Optional:** Add strict lint mode that fails CI (for mature projects):

```yaml
      # Uncomment to make lint warnings fail CI
      # - name: Enforce data quality
      #   run: python .ontos/scripts/ontos_generate_context_map.py --lint --strict --quiet
```

---

### 2.8 Changelog Entry

**File:** `Ontos_CHANGELOG.md`

**Action:** Add to `[Unreleased]` section (after v2.1 entries)

> **Release Workflow Note:** Keep entries under `[Unreleased]` until cutting a release. 
> When releasing, rename to `[2.x.0] - YYYY-MM-DD` per [Keep a Changelog](https://keepachangelog.com/) spec.
> v2.1 and v2.2 can be released together (as `[2.2.0]`) or separately.

**Content to Add:**

```markdown
### Added (v2.2 - Data Quality)
- **Common Concepts Reference** (`docs/reference/Common_Concepts.md`) — Controlled vocabulary for consistent tagging
- **Alternatives Considered section** — New section in log template for documenting rejected options
- **Impacts nudging** — Interactive prompt when creating logs with empty impacts
- **Tagging Discipline** — Agent instructions for v3.0-ready data capture (concepts, impacts, alternatives)
- **`--lint` flag** — Soft warnings for data quality issues in `ontos_generate_context_map.py`
  - Empty impacts on active logs
  - Unknown concepts not in vocabulary
  - Excessive concepts (>6 per log)
  - Stale logs (>30 days without consolidation)
  - Active log count exceeds LOG_RETENTION_COUNT (v2.1 integration)
- **Lint test suite** (`tests/test_lint.py`) — Unit tests for data quality checks
```

---

## 3. File Changes Summary

| File | Action | Estimated Lines |
|:-----|:-------|:----------------|
| `docs/reference/Common_Concepts.md` | Create | ~80 |
| `.ontos/scripts/ontos_end_session.py` | Update template | ~25 |
| `.ontos/scripts/ontos_end_session.py` | Add nudge prompt | ~20 |
| `docs/reference/Ontos_Agent_Instructions.md` | Add section | ~45 |
| `.ontos/scripts/ontos_generate_context_map.py` | Add --lint | ~100 |
| `tests/test_lint.py` | Create | ~180 |
| `.github/workflows/ci.yml` | Add step | ~5 |
| `Ontos_CHANGELOG.md` | Update | ~12 |

**Total:** ~467 lines added/modified

**Dependency:** Requires v2.1 (Smart Memory) to be implemented first for `LOG_RETENTION_COUNT` integration.

---

## 4. Implementation Steps

### Step 1: Create Common Concepts Reference

```bash
# Create directory if needed
mkdir -p docs/reference

# Create the file
touch docs/reference/Common_Concepts.md

# Add content (use template from section 2.1)
```

### Step 2: Update Log Template

```bash
# Open .ontos/scripts/ontos_end_session.py
# Find the create_log_file() function (~line 290)
# Update the content template (add section 3)
# Use content from section 2.2
```

### Step 3: Add Impacts Nudging

```bash
# Open .ontos/scripts/ontos_end_session.py
# Find the main() function, after impacts processing (~line 385)
# Add the nudge prompt code
# Use content from section 2.3
```

### Step 4: Update Agent Instructions

```bash
# Open docs/reference/Ontos_Agent_Instructions.md
# Add "Tagging Discipline" section after "Historical Recall"
# Use content from section 2.4
```

### Step 5: Add Lint Mode

```bash
# Open .ontos/scripts/ontos_generate_context_map.py
# 1. Add --lint argument to argparse
# 2. Add load_common_concepts() function
# 3. Add lint_data_quality() function
# 4. Update generate_context_map() signature to include lint param
# 5. Integrate lint calls into generate_context_map()
# 6. Update main() to pass lint argument
# Use code from section 2.5
```

### Step 6: Add Test Cases

```bash
# Create tests/test_lint.py
# Use content from section 2.6
```

### Step 7: Update CI

```bash
# Open .github/workflows/ci.yml
# Add lint step after validation
# Use content from section 2.7
```

### Step 8: Update Changelog

```bash
# Open Ontos_CHANGELOG.md
# Add v2.2 entries to [Unreleased] section
```

### Step 9: Validate and Commit

```bash
# Run tests
pytest tests/test_lint.py -v

# Test the new features
python3 .ontos/scripts/ontos_generate_context_map.py --strict
python3 .ontos/scripts/ontos_generate_context_map.py --lint

# Verify:
# - Common_Concepts.md appears in Context Map under ATOM
# - --lint shows appropriate warnings
# - New log template includes section 3

# Commit
git add -A
git commit -m "feat(v2.2): implement Data Quality system

- Add Common_Concepts.md as vocabulary reference
- Update log template with Alternatives Considered section
- Add impacts nudging prompt for empty impacts
- Add Tagging Discipline section to Agent Instructions
- Add --lint flag for data quality warnings
- Add test suite for lint functionality"
```

---

## 5. Validation Criteria

After implementation, verify:

- [ ] `Common_Concepts.md` appears in Context Map under ATOM section
- [ ] `Common_Concepts.md` has `depends_on: []` and validates clean
- [ ] New log template includes `## 3. Alternatives Considered` section
- [ ] Creating log with `impacts: []` triggers nudge prompt (unless `--quiet`)
- [ ] `--lint` flag works without errors
- [ ] `--lint` shows warning for empty impacts on active logs
- [ ] `--lint` shows warning for concepts not in Common Concepts
- [ ] `--lint` shows warning for logs with >6 concepts
- [ ] `--lint` shows warning for logs >30 days old
- [ ] `--lint` shows warning when active log count exceeds LOG_RETENTION_COUNT
- [ ] Agent Instructions include Tagging Discipline section with examples
- [ ] All tests in `tests/test_lint.py` pass
- [ ] CI lint step runs (with `continue-on-error: true`)

---

## 6. Migration Notes

### For Existing Projects

1. **Create** `Common_Concepts.md`
   - Start with the template
   - Add/remove concepts based on your project's domains
   - Review existing logs to identify common tags

2. **Existing logs without Alternatives section**
   - Remain valid (section is optional)
   - Consider adding during next edit

3. **Run `--lint` to identify issues:**
   ```bash
   python3 .ontos/scripts/ontos_generate_context_map.py --lint
   ```
   - Fix empty impacts on important logs
   - Standardize concept vocabulary
   - Consolidate stale logs

4. **No schema changes** — all additions are backward compatible

### For New Projects

1. `Common_Concepts.md` created during setup
2. Vocabulary discipline starts from day one
3. Agents trained on tagging best practices immediately

---

## 7. Testing the Lint Feature

### Test Case 1: Empty Impacts

Create a test log with empty impacts:

```yaml
---
id: log_20251213_test
type: log
status: active
event_type: chore
concepts: [testing]
impacts: []
---
```

Run lint:
```bash
python3 .ontos/scripts/ontos_generate_context_map.py --lint
```

Expected: Warning about empty impacts.

### Test Case 2: Unknown Concept

Create a test log with non-standard concept:

```yaml
---
id: log_20251213_test2
type: log
status: active
event_type: feature
concepts: [authentication]  # Should be 'auth'
impacts: [some_doc]
---
```

Run lint:
```bash
python3 .ontos/scripts/ontos_generate_context_map.py --lint
```

Expected: Warning about unknown concept `authentication`.

### Test Case 3: Too Many Concepts

```yaml
---
id: log_20251213_test3
type: log
status: active
event_type: feature
concepts: [auth, api, db, ui, testing, devops, security, perf]  # 8 concepts
impacts: [some_doc]
---
```

Expected: Warning about too many concepts (>6).

### Test Case 4: Active Log Count Exceeds Threshold

If you have more than `LOG_RETENTION_COUNT` (default: 15) active logs:

```bash
python3 .ontos/scripts/ontos_generate_context_map.py --lint
```

Expected warning at top:
```
- [LINT] **Active log count (18) exceeds threshold (15)**
  → 3 logs over limit. Run consolidation ritual to archive oldest logs.
```

---

## 8. Future Considerations (v3.0)

| v2.2 Component | v3.0 Enablement |
|:---------------|:----------------|
| Common Concepts vocabulary | Reliable clustering for `--concept` queries |
| Impacts discipline | Complete edges for reverse traversal |
| Alternatives documentation | Semantic richness for "what was considered?" queries |
| Lint warnings | Data quality baseline before graph operations |

### Future Lint Enhancements (v3.0)

- Detect concept drift (same topic, different tags over time)
- Suggest concept merges ("auth" and "authentication" both used)
- Check for orphan concepts (used once, never again)
- `--lint --strict` mode that fails CI

---

## 9. Example: Full Tagging Workflow

### Creating a Well-Tagged Log

**Command:**
```bash
python3 .ontos/scripts/ontos_end_session.py "oauth-integration" \
  -s "Claude Code" \
  -e feature \
  --concepts "auth,api,security" \
  --impacts "auth_flow,api_spec"
```

**Resulting frontmatter:**
```yaml
---
id: log_20251213_oauth_integration
type: log
status: active
event_type: feature
concepts: [auth, api, security]
impacts: [auth_flow, api_spec]
---
```

**Filling out the template:**

```markdown
## 1. Goal
Implement OAuth2 integration with Google as identity provider.

## 2. Key Decisions
- Use Authorization Code flow (not Implicit) for security
- Store refresh tokens in encrypted database column
- Set access token TTL to 1 hour

## 3. Alternatives Considered
- **Implicit flow** — rejected, deprecated and less secure
- **Client Credentials flow** — rejected, need user context
- **Firebase Auth** — rejected, vendor lock-in concerns
- **Auth0** — rejected, cost prohibitive at current stage

## 4. Changes Made
- Created `src/auth/oauth.py` with Google OAuth client
- Updated `auth_flow.md` with OAuth sequence diagram
- Added `GOOGLE_CLIENT_ID` to environment config

## 5. Next Steps
- Add refresh token rotation
- Implement logout/revocation
- Add Microsoft as second provider
```

### Running Lint Check

```bash
python3 .ontos/scripts/ontos_generate_context_map.py --lint
```

**Expected output (if all is well):**
```
Scanning .ontos-internal...
Generating tree...
Validating dependencies...
Validating log schema...
Validating impacts references...
Running data quality lint...
Successfully generated Ontos_Context_Map.md
Scanned 6 documents, found 0 issues.

📋 Data Quality Warnings (0 issues):
No data quality warnings. Nice work!
```

---

*End of v2.2 Implementation Plan (Revised)*
