# Ontos v2.3 Implementation Instructions

**For:** Agentic CLI tools (Claude Code, Cursor, Codex, Gemini CLI, etc.)  
**Reference:** `ontos_v2.3_implementation_plan_final.md`  
**Version:** 2.3.0 "Less Typing, More Insight"

---

## Mission

Implement Ontos v2.3 UX improvements following the detailed implementation plan. The goal is to reduce ceremony while preserving curation — make the system easier to use without dumbing it down.

**Theme:** Less Typing, More Insight

---

## Before You Start

### 1. Load Context

```bash
# Activate Ontos context
Ontos

# Read the implementation plan thoroughly
cat ontos_v2.3_implementation_plan_final.md
```

### 2. Verify Current State

```bash
# Check current version
grep -r "__version__" .ontos/scripts/

# Verify existing scripts
ls -la .ontos/scripts/

# Check existing config structure
cat .ontos/scripts/ontos_config_defaults.py
```

### 3. Create Working Branch

```bash
git checkout -b feature/v2.3-ux-improvements
```

---

## Implementation Phases

Execute these phases in order. Complete all tasks in a phase before moving to the next.

---

## Phase 1: Foundation (Shared Library + Config)

### Task 1.1: Create `ontos_lib.py`

**File:** `.ontos/scripts/ontos_lib.py`

Create new file with these functions (copy implementations from plan Section 3.0):

- [ ] `parse_frontmatter(filepath: str) -> Optional[dict]`
- [ ] `normalize_depends_on(value) -> list[str]`
- [ ] `normalize_type(value) -> str`
- [ ] `load_common_concepts(docs_dir: str = None) -> set[str]`
- [ ] `get_git_last_modified(filepath: str) -> Optional[datetime]`
- [ ] `find_last_session_date(logs_dir: str = None) -> str`
- [ ] `BLOCKED_BRANCH_NAMES` constant

**Verification:**
```bash
python3 -c "from ontos_lib import parse_frontmatter, BLOCKED_BRANCH_NAMES; print('OK')"
```

### Task 1.2: Update Config Defaults

**File:** `.ontos/scripts/ontos_config_defaults.py`

Add these items (see plan Section 3.0.1):

- [ ] `is_ontos_repo() -> bool` function
- [ ] `SKIP_PATTERNS` list
- [ ] `SMALL_CHANGE_THRESHOLD = 20`
- [ ] `DEFAULT_SOURCE = None`
- [ ] Add `'decision'` to `EVENT_TYPES` dict

**Verification:**
```bash
python3 -c "from ontos_config import is_ontos_repo, SKIP_PATTERNS; print('OK')"
```

### Task 1.3: Refactor Existing Scripts to Use Library

**Files to modify:**
- `.ontos/scripts/ontos_generate_context_map.py`
- `.ontos/scripts/ontos_end_session.py`

**Action:** Replace local implementations of `parse_frontmatter`, `normalize_depends_on`, `normalize_type` with imports from `ontos_lib`.

```python
# Add to imports
from ontos_lib import (
    parse_frontmatter,
    normalize_depends_on,
    normalize_type,
    load_common_concepts,
    find_last_session_date,
    BLOCKED_BRANCH_NAMES,
)
```

**Delete:** Local function definitions that are now in `ontos_lib.py`.

**Verification:**
```bash
python3 .ontos/scripts/ontos_generate_context_map.py --help
python3 .ontos/scripts/ontos_end_session.py --help
```

### Task 1.4: Implement Adaptive Templates

**File:** `.ontos/scripts/ontos_end_session.py`

Add (see plan Section 3.1):

- [ ] `TEMPLATES` dict mapping event_type → sections
- [ ] `SECTION_TEMPLATES` dict with section content
- [ ] `generate_template_sections(event_type: str) -> str` function
- [ ] Modify `create_log_file()` to use `generate_template_sections()`

**Test:**
```bash
# Should show 2 sections for chore
python3 .ontos/scripts/ontos_end_session.py "test-chore" -e chore -s "Test" --dry-run

# Should show 5 sections for decision
python3 .ontos/scripts/ontos_end_session.py "test-decision" -e decision -s "Test" --dry-run
```

### Task 1.5: Implement Archive Ceremony Reduction

**File:** `.ontos/scripts/ontos_end_session.py`

Add (see plan Section 3.2):

- [ ] `DEFAULT_SOURCE` import with fallback
- [ ] `generate_auto_slug(quiet: bool = False) -> Optional[str]` function
- [ ] `--dry-run` / `-n` argument
- [ ] `--list-concepts` argument
- [ ] Modify `main()` to use auto-slug when topic not provided
- [ ] Modify `main()` to prompt user when auto-slug fails (NOT silent timestamp)

**Test:**
```bash
# Should show available concepts
python3 .ontos/scripts/ontos_end_session.py --list-concepts

# Should show preview without creating file
python3 .ontos/scripts/ontos_end_session.py -e chore -s "Test" --dry-run

# On a feature branch, should auto-generate slug
git checkout -b feature/test-auto-slug
python3 .ontos/scripts/ontos_end_session.py -e feature -s "Test" --dry-run
git checkout feature/v2.3-ux-improvements
git branch -D feature/test-auto-slug
```

**Phase 1 Checkpoint:**
```bash
# All scripts should run without import errors
python3 -c "import sys; sys.path.insert(0, '.ontos/scripts'); from ontos_lib import *; from ontos_config import *; print('Phase 1 OK')"
```

---

## Phase 2: New Tooling Scripts

### Task 2.1: Create `ontos_query.py`

**File:** `.ontos/scripts/ontos_query.py` (new)

Implement full script from plan Section 3.5:

- [ ] `scan_docs_for_query(root_dir: str) -> dict`
- [ ] `build_graph(files_data: dict) -> tuple`
- [ ] `query_depends_on(files_data: dict, target_id: str) -> list`
- [ ] `query_depended_by(files_data: dict, target_id: str) -> list`
- [ ] `query_concept(files_data: dict, concept: str) -> list`
- [ ] `query_stale(files_data: dict, days: int) -> list` — **Must use git history, not mtime**
- [ ] `query_health(files_data: dict) -> dict`
- [ ] `format_health(health: dict) -> str`
- [ ] CLI argument parser with mutually exclusive group
- [ ] `--dir` flag for directory override

**Test:**
```bash
python3 .ontos/scripts/ontos_query.py --help
python3 .ontos/scripts/ontos_query.py --health
python3 .ontos/scripts/ontos_query.py --list-ids
python3 .ontos/scripts/ontos_query.py --depended-by mission
```

### Task 2.2: Create `ontos_consolidate.py`

**File:** `.ontos/scripts/ontos_consolidate.py` (new)

Implement full script from plan Section 3.4:

- [ ] Mode-aware paths using `is_ontos_repo()`
- [ ] `HISTORY_LEDGER_HEADER` constant with SYNC comment
- [ ] `find_old_logs(threshold_days: int = 30) -> List[Tuple]`
- [ ] `extract_summary(filepath: str) -> Optional[str]` — **Use relaxed regex: `r'##\s*\d*\.?\s*Goal'`**
- [ ] `validate_decision_history() -> bool`
- [ ] `append_to_decision_history(...)` — **CRITICAL: Target History Ledger table specifically**
- [ ] `archive_log(filepath: str, dry_run: bool = False) -> Optional[str]`
- [ ] `consolidate_log(...)` with interactive summary fallback
- [ ] Defensive table detection (see plan Appendix D, item 6)
- [ ] CLI with `--days`, `--dry-run`, `--quiet`, `--all` flags

**CRITICAL:** The `append_to_decision_history` function must find the History Ledger table by its header, NOT just "the last table". See plan Section 3.4 for correct implementation.

**Test:**
```bash
python3 .ontos/scripts/ontos_consolidate.py --help
python3 .ontos/scripts/ontos_consolidate.py --dry-run
python3 .ontos/scripts/ontos_consolidate.py --days 90 --dry-run
```

### Task 2.3: Create `ontos_maintain.py`

**File:** `.ontos/scripts/ontos_maintain.py` (new)

Implement full script from plan Section 3.9:

- [ ] `run_script(name: str, args: list = None, quiet: bool = False) -> tuple`
- [ ] `main()` that runs migrate then generate
- [ ] `--strict`, `--quiet`, `--lint` flags

**Test:**
```bash
python3 .ontos/scripts/ontos_maintain.py --help
python3 .ontos/scripts/ontos_maintain.py
```

### Task 2.4: Implement Extended Impact Suggestions

**File:** `.ontos/scripts/ontos_end_session.py`

Modify `suggest_impacts()` (see plan Section 3.6):

- [ ] Import `find_last_session_date` from `ontos_lib`
- [ ] Change fallback from `today` to `find_last_session_date()`

**Phase 2 Checkpoint:**
```bash
python3 .ontos/scripts/ontos_query.py --health
python3 .ontos/scripts/ontos_consolidate.py --dry-run
python3 .ontos/scripts/ontos_maintain.py
```

---

## Phase 3: Hook + Validation

### Task 3.1: Create `ontos_pre_push_check.py`

**File:** `.ontos/scripts/ontos_pre_push_check.py` (new)

Implement full script from plan Section 3.3.2:

- [ ] `get_change_stats() -> Tuple[int, int, List[str]]`
- [ ] `suggest_related_docs(changed_files: List[str]) -> List[str]`
- [ ] `print_small_change_message(lines: int, files: List[str])`
- [ ] `print_large_change_message(...)`
- [ ] `print_advisory_message(lines: int)`
- [ ] `main() -> int` with marker file check and contextual output

**Test:**
```bash
python3 .ontos/scripts/ontos_pre_push_check.py
```

### Task 3.2: Simplify Bash Hook

**File:** `.ontos/hooks/pre-push`

Replace entire contents with minimal delegation (see plan Section 3.3.1):

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

**IMPORTANT:** After modifying, reinstall hook:
```bash
python3 .ontos/scripts/ontos_install_hooks.py
```

### Task 3.3: Implement Creation-Time Concept Validation

**File:** `.ontos/scripts/ontos_end_session.py`

Add (see plan Section 3.7):

- [ ] `validate_concepts(concepts: list[str], quiet: bool = False) -> list[str]`
- [ ] Call `validate_concepts()` in `main()` after parsing concepts

**Test:**
```bash
# Should warn about unknown concept
python3 .ontos/scripts/ontos_end_session.py "test" -e chore -s "Test" -c "unknown-concept-xyz" --dry-run
```

### Task 3.4: Implement Starter Doc Scaffolding

**File:** `ontos_init.py`

Add (see plan Section 3.8):

- [ ] `STARTER_MISSION` template with prompting questions
- [ ] `STARTER_ROADMAP` template
- [ ] `STARTER_DECISION_HISTORY` template with SYNC comment and BOTH tables
- [ ] `scaffold_starter_docs()` function
- [ ] Call `scaffold_starter_docs()` in `main()`

**CRITICAL:** The `STARTER_DECISION_HISTORY` must include the SYNC comment and have the exact header that `HISTORY_LEDGER_HEADER` expects.

**Test:**
```bash
# Create temp directory and test init
mkdir /tmp/ontos-test && cd /tmp/ontos-test
python3 /path/to/ontos_init.py
ls docs/
cat docs/mission.md
cat docs/decision_history.md
cd - && rm -rf /tmp/ontos-test
```

**Phase 3 Checkpoint:**
```bash
# Hook should work
python3 .ontos/scripts/ontos_pre_push_check.py

# Concept validation should warn
python3 .ontos/scripts/ontos_end_session.py "test" -e chore -s "Test" -c "fake-concept" --dry-run
```

---

## Phase 4: Testing + Documentation

### Task 4.1: Create Test Files

Create the following test files with test cases from plan Section 5:

- [ ] `tests/test_lib.py`
- [ ] `tests/test_config.py`
- [ ] `tests/test_end_session.py`
- [ ] `tests/test_query.py`
- [ ] `tests/test_consolidate.py`
- [ ] `tests/test_pre_push_check.py`
- [ ] `tests/test_maintain.py`

**Minimum test coverage:**

```python
# tests/test_consolidate.py - CRITICAL TEST
def test_append_targets_history_ledger_not_consolidation_log():
    """Verify consolidation appends to History Ledger, not Consolidation Log."""
    # Create decision_history.md with BOTH tables
    # Run append
    # Verify row added to first table only
    pass
```

**Run tests:**
```bash
python3 -m pytest tests/ -v
```

### Task 4.2: Update Documentation

**File:** `docs/reference/Ontos_Manual.md`

Add sections for:
- [ ] New commands (query, consolidate, maintain)
- [ ] Simplified archive workflow
- [ ] Adaptive templates explanation
- [ ] DEFAULT_SOURCE configuration

**File:** `docs/reference/Ontos_Agent_Instructions.md`

Add command reference from plan Appendix C.

### Task 4.3: Update Changelog

**File:** `Ontos_CHANGELOG.md`

Add v2.3.0 entries from plan Appendix B.

### Task 4.4: Bump Version

**File:** `.ontos/scripts/ontos_config_defaults.py`

```python
__version__ = "2.3.0"
```

**Phase 4 Checkpoint:**
```bash
python3 -m pytest tests/ -v
grep "2.3.0" .ontos/scripts/ontos_config_defaults.py
```

---

## Final Verification

Run complete verification:

```bash
# 1. All scripts have no import errors
python3 .ontos/scripts/ontos_end_session.py --help
python3 .ontos/scripts/ontos_query.py --help
python3 .ontos/scripts/ontos_consolidate.py --help
python3 .ontos/scripts/ontos_maintain.py --help
python3 .ontos/scripts/ontos_pre_push_check.py

# 2. Adaptive templates work
python3 .ontos/scripts/ontos_end_session.py -e chore -s "Test" --dry-run
python3 .ontos/scripts/ontos_end_session.py -e decision -s "Test" --dry-run

# 3. Query interface works
python3 .ontos/scripts/ontos_query.py --health

# 4. Maintenance works
python3 .ontos/scripts/ontos_maintain.py

# 5. Tests pass
python3 -m pytest tests/ -v

# 6. Version is correct
python3 -c "from ontos_config import __version__; print(__version__)"
# Expected: 2.3.0
```

---

## Commit & Archive

```bash
# Stage all changes
git add -A

# Commit with descriptive message
git commit -m "feat(v2.3): Less Typing, More Insight

- Add shared utilities library (ontos_lib.py)
- Add adaptive templates by event type
- Add query interface (ontos_query.py)
- Add consolidation command (ontos_consolidate.py)  
- Add maintenance command (ontos_maintain.py)
- Extract pre-push hook logic to Python
- Add DEFAULT_SOURCE config
- Add auto-slug generation
- Add --dry-run and --list-concepts flags
- Add creation-time concept validation
- Add starter doc scaffolding
- Extend impact suggestions to last session

Closes #v2.3"

# Archive the session
Archive Ontos
# Or: python3 .ontos/scripts/ontos_end_session.py -e feature
```

---

## Critical Reminders

### DO:

1. **Read the full implementation plan** before starting
2. **Test after each task** — don't batch all testing to the end
3. **Use the exact function signatures** from the plan
4. **Include SYNC comments** where specified (header coupling)
5. **Target History Ledger specifically** in consolidation (two-table safety)
6. **Reinstall hooks** after modifying `.ontos/hooks/pre-push`
7. **Use git history** for stale detection, not file mtime

### DON'T:

1. **Don't skip the defensive table detection** — it prevents data corruption
2. **Don't use silent timestamp fallback** for auto-slug — prompt user instead
3. **Don't hardcode paths** — use mode-aware `is_ontos_repo()` checks
4. **Don't forget to import from ontos_lib** — remove duplicate local functions
5. **Don't modify `.git/hooks/` directly** — use the install script

### If Stuck:

1. Re-read the relevant section in `ontos_v2.3_implementation_plan_final.md`
2. Check the test cases in Part 5 for expected behavior
3. Look at Appendix D for implementation gotchas

---

## Success Criteria

When complete, verify:

- [ ] Archive command works without `-s` flag (when DEFAULT_SOURCE configured)
- [ ] Archive command auto-generates slug from branch name
- [ ] `python3 .ontos/scripts/ontos_query.py --health` returns metrics
- [ ] `python3 .ontos/scripts/ontos_consolidate.py --dry-run` shows old logs
- [ ] `python3 .ontos/scripts/ontos_maintain.py` runs both migrate and generate
- [ ] Pre-push hook shows change statistics
- [ ] Unknown concepts warn at creation time
- [ ] `ontos init` creates starter docs with prompting questions
- [ ] All tests pass
- [ ] Version shows 2.3.0