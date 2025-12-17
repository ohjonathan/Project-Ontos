---
id: v2_5_architectural_review_claude
type: review
status: complete
reviewer: Claude Opus 4.5
reviewed_doc: v2_5_promises_implementation_plan
date: 2025-12-17
---

# Architectural Review: Ontos v2.5 "The Promises"

**Reviewer:** Claude Opus 4.5
**Date:** 2025-12-17
**Document Reviewed:** `v2.5_promises_implementation_plan.md`
**Status:** Complete

---

## 1. Executive Summary

### Overall Assessment

The plan is **well-structured** and addresses a real user problem: passive warnings don't work. The pre-commit over pre-push decision is architecturally sound. The open questions section (Section 12) demonstrates good self-awareness of design trade-offs.

However, several design decisions could cause friction or unexpected behavior in production. This review identifies **8 concerns** ranging from critical (staging unrelated files) to low priority (Unicode compatibility).

### Recommendation

**Proceed with implementation** after addressing the critical and high-priority issues identified below.

---

## 2. Strengths

| Strength | Why It Matters |
|----------|----------------|
| Clear problem identification | "Users won't remember" is honest and leads to the right solution |
| Pre-commit rationale | The "dirty push" paradox is well-explained and the solution is correct |
| Never-block philosophy | Returning 0 always is pragmatic; hooks shouldn't break workflows |
| Self-critical open questions | Section 12 shows architectural maturity and invites collaboration |
| Mode-based behavior | Clear separation of concerns between automated/prompted/advisory |

---

## 3. Concerns & Recommendations

### 3.1 Staging Files Within Pre-commit Hook (Critical)

#### Problem

The proposed `stage_consolidated_files()` function runs:

```python
subprocess.run(['git', 'add', '-u'], capture_output=True)
```

`git add -u` stages **all tracked modified files**—not just Ontos files. This breaks a fundamental git mental model: "I control what goes into my commits."

#### Scenario

```bash
$ git status
  modified:   src/feature.py      # User wants to commit
  modified:   src/debug.py        # User does NOT want to commit (WIP)

$ git add src/feature.py
$ git commit -m "feat: add feature"

# Pre-commit hook fires, runs: git add -u
# Now debug.py is ALSO staged and committed (unintended)
```

#### Worse Case: Sensitive Files

```bash
$ git status
  modified:   .env.local          # Contains API keys (tracked by mistake)
  modified:   src/app.py

$ git add src/app.py
$ git commit -m "fix: bug"

# Hook runs git add -u → .env.local committed and pushed
# API keys exposed
```

#### Recommendation

Only stage files that consolidation actually created or modified:

```python
def stage_consolidated_files() -> None:
    """Stage ONLY files modified by consolidation."""
    from ontos_config import is_ontos_repo, PROJECT_ROOT

    if is_ontos_repo():
        decision_history = os.path.join(PROJECT_ROOT, '.ontos-internal', 'strategy', 'decision_history.md')
        archive_dir = os.path.join(PROJECT_ROOT, '.ontos-internal', 'archive')
    else:
        decision_history = os.path.join(PROJECT_ROOT, 'docs', 'decision_history.md')
        archive_dir = os.path.join(PROJECT_ROOT, 'docs', 'archive')

    # Stage ONLY specific Ontos files
    if os.path.exists(decision_history):
        subprocess.run(['git', 'add', decision_history], capture_output=True)

    if os.path.exists(archive_dir):
        subprocess.run(['git', 'add', archive_dir], capture_output=True)

    # Stage the logs directory (to capture deletions)
    subprocess.run(['git', 'add', LOGS_DIR], capture_output=True)
```

**Priority:** Critical
**Effort:** Low (simple code change)

---

### 3.2 CI/CD Interaction Not Addressed (High)

#### Problem

CI systems create commits in various scenarios:
- Version bumps (`npm version patch`)
- Changelog generation
- Auto-formatting (Prettier, Black)
- Dependency updates (Dependabot, Renovate)

These commits trigger pre-commit hooks. In CI:
- No TTY for interactive prompts
- The "user" is a bot
- Consolidation may be inappropriate

#### Scenario: Dependabot

```
Dependabot creates PR:
  Expected commit: "chore(deps): bump lodash 4.17.20 → 4.17.21"

Pre-commit hook fires, consolidates logs.

Actual commit: dependency bump + 15 archived log files

Reviewer: "Why are log files in a dependency update?"
```

#### Recommendation

Add CI detection at hook entry:

```python
def should_skip_hook() -> bool:
    """Check if hook should be skipped (CI environments, explicit skip)."""

    # Explicit skip flag
    if os.environ.get('ONTOS_SKIP_HOOKS', '').lower() in ('1', 'true', 'yes'):
        return True

    # Common CI environment variables
    ci_indicators = [
        'CI',                    # Generic (GitHub Actions, GitLab CI, etc.)
        'CONTINUOUS_INTEGRATION', # Travis CI
        'GITHUB_ACTIONS',        # GitHub Actions
        'GITLAB_CI',             # GitLab CI
        'JENKINS_URL',           # Jenkins
        'CIRCLECI',              # CircleCI
        'BUILDKITE',             # Buildkite
        'TF_BUILD',              # Azure Pipelines
    ]

    return any(os.environ.get(var) for var in ci_indicators)


def main() -> int:
    if should_skip_hook():
        return 0
    # ... rest of hook
```

**Priority:** High
**Effort:** Low

---

### 3.3 Count vs Age Threshold Mismatch (Medium)

#### Problem

The plan triggers consolidation when `log_count > 15` but only archives logs older than 30 days. These metrics can conflict.

**Scenario:** User has 20 logs, all from the past week (burst of activity). Hook triggers (count > 15), but consolidation finds nothing older than 30 days.

**Output:** "No logs old enough to consolidate" — confusing.

#### Analysis

- **Count is arbitrary:** Why 15? Different projects have different rhythms.
- **Burst activity is normal:** Refactoring week, incident response, onboarding.
- **Age is meaningful:** 30-day-old logs are genuinely "stale context."

#### Recommendation

Use **age-only triggering** with count as a separate advisory warning:

```python
def should_consolidate() -> bool:
    """Age-based triggering only."""
    mode = get_mode()
    if mode != 'automated':
        return False

    if not resolve_config('AUTO_CONSOLIDATE_ON_COMMIT', True):
        return False

    # Age-based: Are there old logs to consolidate?
    threshold_days = resolve_config('CONSOLIDATION_THRESHOLD_DAYS', 30)
    old_logs = get_logs_older_than(threshold_days)

    return len(old_logs) > 0
```

Separate count warning (for user awareness, not triggering):

```python
def get_count_warning() -> Optional[str]:
    """Advisory warning if count exceeds threshold."""
    count = get_log_count()
    threshold = resolve_config('LOG_COUNT_WARNING_THRESHOLD', 25)

    if count > threshold:
        return f"You have {count} active logs (threshold: {threshold})"
    return None
```

**Priority:** Medium
**Effort:** Low

---

### 3.4 The "Prompted" Mode Promise Is Hollow (High)

#### Problem

The promise for prompted mode:

> "Keep me in the loop."

But the implementation relies on:
1. AI agents reading prose in `Ontos_Agent_Instructions.md`
2. Agents choosing to follow that prose
3. Agents correctly counting logs

This is a **hope**, not a mechanism.

#### Why It Matters

| Promise | Reality |
|---------|---------|
| "Keep me in the loop" | "Hope your agent reads the docs" |
| "Gentle guidance" | "Guidance that may or may not appear" |

Users choosing "prompted" mode expect **reliable** reminders.

#### Recommendation

Add a scriptable check that users (and agents) can call:

**New File:** `.ontos/scripts/ontos_check.py`

```python
#!/usr/bin/env python3
"""Ontos status checker for prompted/advisory modes."""

import os
import sys
import argparse
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ontos_lib import resolve_config
from ontos_config import LOGS_DIR


def get_log_stats() -> dict:
    """Get statistics about current logs."""
    if not os.path.exists(LOGS_DIR):
        return {'count': 0, 'oldest_days': 0, 'logs_over_threshold': 0}

    today = datetime.datetime.now()
    threshold_days = resolve_config('CONSOLIDATION_THRESHOLD_DAYS', 30)

    count = 0
    oldest_days = 0
    logs_over_threshold = 0

    for filename in os.listdir(LOGS_DIR):
        if not filename.endswith('.md') or not filename[0].isdigit():
            continue
        count += 1
        try:
            log_date = datetime.datetime.strptime(filename[:10], '%Y-%m-%d')
            age = (today - log_date).days
            oldest_days = max(oldest_days, age)
            if age > threshold_days:
                logs_over_threshold += 1
        except ValueError:
            continue

    return {
        'count': count,
        'oldest_days': oldest_days,
        'logs_over_threshold': logs_over_threshold,
        'threshold_days': threshold_days
    }


def check_consolidation(quiet: bool = False) -> int:
    """Check if consolidation is needed. Returns 0 if OK, 1 if needed."""
    stats = get_log_stats()

    if stats['logs_over_threshold'] == 0:
        if not quiet:
            print(f"OK: No logs older than {stats['threshold_days']} days")
        return 0

    if not quiet:
        print(f"Consolidation recommended:")
        print(f"  {stats['count']} total logs")
        print(f"  {stats['logs_over_threshold']} logs older than {stats['threshold_days']} days")
        print(f"\n  Run: python3 .ontos/scripts/ontos_consolidate.py")

    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check Ontos status')
    parser.add_argument('--consolidation', '-c', action='store_true')
    parser.add_argument('--quiet', '-q', action='store_true')
    args = parser.parse_args()

    if args.consolidation:
        sys.exit(check_consolidation(args.quiet))
```

**Usage:**

```bash
# For users
python3 .ontos/scripts/ontos_check.py --consolidation

# For scripts/agents (exit code only)
python3 .ontos/scripts/ontos_check.py -c -q && echo "OK" || echo "Needs consolidation"
```

**Priority:** High
**Effort:** Medium (new script)

---

### 3.5 No Rollback Mechanism (Medium)

#### Problem

Auto-consolidation moves files permanently:

```python
shutil.move(filepath, archive_path)  # File is moved, not copied
```

Once consolidated:
- Log moves from `docs/logs/` to `docs/archive/`
- Context map no longer includes it
- Agents won't read it during activation

What if the user needed that log?

#### Scenario

User sets `CONSOLIDATION_THRESHOLD_DAYS=7`. They're working on a feature referencing a decision from 8 days ago. Log gets auto-archived. Context is lost.

#### Recommendation

Add an `ontos_unarchive.py` script:

```python
"""Restore archived log to active logs directory."""

def unarchive(log_id: str) -> bool:
    """Move log from archive back to active logs."""
    archive_path = find_in_archive(log_id)
    if not archive_path:
        print(f"Error: {log_id} not found in archive")
        return False

    filename = os.path.basename(archive_path)
    logs_path = os.path.join(LOGS_DIR, filename)

    shutil.move(archive_path, logs_path)
    update_frontmatter_status(logs_path, 'active')
    regenerate_context_map()

    print(f"Restored {log_id} to active logs")
    return True
```

**Usage:**

```bash
python3 .ontos/scripts/ontos_unarchive.py log_20251201_some_decision
```

**Priority:** Medium
**Effort:** Medium

---

### 3.6 Commit Amend / Rebase Scenarios (Medium)

#### Problem

Git hooks fire during various operations:

| Operation | Pre-commit fires? |
|-----------|-------------------|
| `git commit` | Yes |
| `git commit --amend` | Yes |
| `git rebase` | Yes (per commit) |
| `git cherry-pick` | Yes |

#### Scenario: Rebase Contamination

```bash
$ git rebase -i HEAD~5
# Pre-commit fires 5 times
# First rebased commit includes consolidation changes
# History is muddled with unrelated archive files
```

#### Recommendation

Skip hook during special git operations:

```python
def is_special_git_operation() -> bool:
    """Detect rebase, cherry-pick, etc."""
    git_dir = subprocess.run(
        ['git', 'rev-parse', '--git-dir'],
        capture_output=True, text=True
    ).stdout.strip()

    # Rebase in progress
    if os.path.exists(os.path.join(git_dir, 'rebase-merge')) or \
       os.path.exists(os.path.join(git_dir, 'rebase-apply')):
        return True

    # Cherry-pick in progress
    if os.path.exists(os.path.join(git_dir, 'CHERRY_PICK_HEAD')):
        return True

    return False
```

**Note:** Allow `--amend` (hard to detect, some users may want consolidation during amend).

**Priority:** Medium
**Effort:** Low

---

### 3.7 Terminal Compatibility — Unicode (Low)

#### Problem

The proposed UI uses Unicode box-drawing characters:

```
+----------------------------------------------------------+
|                    Choose Your Workflow                        |
+==================================================================+
```

These break in:
- Windows CMD
- SSH with wrong locale
- CI logs (GitHub Actions, Jenkins)
- tmux/screen with certain configs

#### Recommendation

Use ASCII-only:

```python
print("""
+================================================================+
|                    Choose Your Workflow                        |
+================================================================+

   [1] Automated (recommended for solo devs)

       "Zero friction - just works."

       - Sessions auto-archived on push
       - Old logs auto-consolidated on commit

   ----------------------------------------------------------------

   [2] Prompted (recommended for teams) [DEFAULT]
   ...
""")
```

**Priority:** Low
**Effort:** Low

---

### 3.8 Hook Conflict Strategy (High)

#### Problem

Many projects have existing pre-commit hooks:
- **Husky** (JavaScript)
- **pre-commit framework** (Python)
- **lint-staged**
- Custom hooks

The plan backs up and **replaces** existing hooks, breaking user workflows.

#### Scenario

Project uses Husky for ESLint/Prettier. Ontos overwrites `.git/hooks/pre-commit`. Now:
- Husky doesn't run
- lint-staged doesn't run
- Bad code gets committed

#### Recommendation

Detect and provide integration instructions instead of overwriting:

```python
def install_pre_commit_hook() -> None:
    """Install with conflict detection."""
    husky_dir = os.path.join(PROJECT_ROOT, '.husky')
    pre_commit_config = os.path.join(PROJECT_ROOT, '.pre-commit-config.yaml')

    if os.path.exists(husky_dir):
        print("\n   Detected Husky. Add to .husky/pre-commit:")
        print("   python3 .ontos/scripts/ontos_pre_commit_check.py")
        return

    if os.path.exists(pre_commit_config):
        print("\n   Detected pre-commit framework. Add to .pre-commit-config.yaml:")
        print("""   - repo: local
     hooks:
       - id: ontos-consolidate
         name: Ontos Auto-Consolidation
         entry: python3 .ontos/scripts/ontos_pre_commit_check.py
         language: system
         always_run: true
         pass_filenames: false""")
        return

    # Check for existing non-Ontos hook
    if os.path.exists(pre_commit_dst):
        with open(pre_commit_dst, 'r') as f:
            if 'ontos' not in f.read().lower():
                print("\n   Existing pre-commit hook detected")
                print("   Add this line to your hook:")
                print("   python3 .ontos/scripts/ontos_pre_commit_check.py")

                if input("   Overwrite? [y/N]: ").lower() != 'y':
                    return

    # Safe to install
    shutil.copy2(pre_commit_src, pre_commit_dst)
```

**Priority:** High
**Effort:** Medium

---

## 4. Additional Considerations

### 4.1 Git Worktrees

Git worktrees share `.git/hooks/`. If one worktree is `automated` and another is `advisory`, which config wins?

**Solution:** Hook should read config from the worktree's `.ontos/` directory:

```python
def get_worktree_root() -> str:
    result = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        capture_output=True, text=True
    )
    return result.stdout.strip()
```

### 4.2 Performance at Scale

`find_old_logs()` parses frontmatter for each file. With 500 logs, this could be slow on every commit.

**Solution:** Quick filename-based check first:

```python
def should_consolidate() -> bool:
    # Phase 1: Quick filename check (no file reads)
    old_by_filename = [f for f in os.listdir(LOGS_DIR)
                       if is_old_by_filename(f, threshold_days)]
    if not old_by_filename:
        return False

    # Phase 2: Proceed (frontmatter parsing happens in consolidation)
    return True
```

### 4.3 Error Surfacing Granularity

Not all failures should be silent:

| Failure Type | Should Surface? |
|--------------|-----------------|
| No old logs found | No (expected) |
| Permission error | Yes (user can fix) |
| decision_history.md missing | Yes (critical) |
| Disk full | Yes (system issue) |

---

## 5. Responses to Open Questions

| Question | Response |
|----------|----------|
| **Q1** (Count vs Age) | Option B (age-only) with separate count warning. Age is the meaningful metric. |
| **Q2** (Repeated Consolidation) | Option A (silence) with `ONTOS_VERBOSE=1` env var for debugging. |
| **Q3** (Unicode) | Option B (ASCII). Reliability over aesthetics for CLI tools. |
| **Q4** (Hook Conflicts) | Option C minimum, but add detection for Husky/pre-commit framework with integration instructions. |
| **Q5** (Agent Reminders) | Disagree with Option D. Add scriptable `ontos_check.py` to honor the "prompted" promise. |
| **Q6** (File Changes) | Option B. Keep file list, remove line estimates. |

---

## 6. Summary of Recommendations

| Issue | Recommendation | Priority | Effort |
|-------|----------------|----------|--------|
| `git add -u` staging | Stage only Ontos files explicitly | Critical | Low |
| CI detection | Auto-detect CI env vars, skip hook | High | Low |
| Hook conflicts | Detect Husky/pre-commit, provide instructions | High | Medium |
| Prompted mode promise | Add scriptable `ontos_check.py` | High | Medium |
| Count vs Age | Age-only trigger, count as advisory | Medium | Low |
| Rollback mechanism | Add `ontos_unarchive.py` | Medium | Medium |
| Rebase/cherry-pick | Skip hook during these operations | Medium | Low |
| Unicode | Use ASCII-only | Low | Low |

---

## 7. Approval Status

- [x] Architecture review complete
- [ ] Open questions addressed
- [ ] Critical issues resolved
- [ ] Ready for implementation

**Recommendation:** Address critical and high-priority issues before implementation.

---

*End of Review*
