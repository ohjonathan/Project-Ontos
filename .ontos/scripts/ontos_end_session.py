"""Scaffold a new session log file for Ontos with optional changelog integration."""

import os
import re
import datetime
import subprocess
import argparse
import sys
from typing import Optional

from ontos_config import __version__, LOGS_DIR, CONTEXT_MAP_FILE, PROJECT_ROOT

from ontos_lib import (
    BLOCKED_BRANCH_NAMES,
    find_last_session_date,
    load_common_concepts,
    resolve_config,
    get_proposals_dir,
    get_decision_history_path,
    # v2.7 imports for staleness check
    check_staleness,
    normalize_describes,
    parse_describes_verified,
    parse_frontmatter,
)

# v2.4: Use resolve_config for mode-aware settings
REQUIRE_SOURCE_IN_LOGS = resolve_config('REQUIRE_SOURCE_IN_LOGS', True)

# Try to import DEFAULT_SOURCE
try:
    from ontos_config import DEFAULT_SOURCE
except ImportError:
    DEFAULT_SOURCE = None

# =============================================================================
# PROPOSAL GRADUATION DETECTION (v2.6.1)
# =============================================================================


def detect_implemented_proposal(branch: str, impacts: list) -> Optional[dict]:
    """Detect if current session implements a proposal.

    Detection heuristics:
    1. Branch name contains proposal slug (e.g., feat/v2.6-* matches v2.6)
    2. Session impacts a proposal document
    3. ONTOS_VERSION matches proposal version (for Ontos-internal)

    Args:
        branch: Current git branch name
        impacts: List of impacted document IDs

    Returns:
        Dict with proposal info if detected, None otherwise.
    """
    proposals_dir = get_proposals_dir()
    if not proposals_dir or not os.path.exists(proposals_dir):
        return None

    # Extract version-like patterns from branch (e.g., v2.6, v2-6)
    branch_lower = branch.lower()
    version_patterns = re.findall(r'v?(\d+)[._-](\d+)', branch_lower)

    # Scan proposals directory for draft proposals
    draft_proposals = []
    for root, dirs, files in os.walk(proposals_dir):
        for file in files:
            if not file.endswith('.md'):
                continue
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # Just need frontmatter

                # Check if it's a draft
                if 'status: draft' not in content:
                    continue

                # Extract ID
                id_match = re.search(r'^id:\s*(.+)$', content, re.MULTILINE)
                if not id_match:
                    continue

                doc_id = id_match.group(1).strip()

                # Check for version match in filepath or ID
                for major, minor in version_patterns:
                    version_str = f'{major}.{minor}'
                    version_str_alt = f'{major}_{minor}'
                    version_str_alt2 = f'{major}-{minor}'

                    if (version_str in filepath or version_str_alt in filepath or
                        version_str_alt2 in filepath or version_str in doc_id or
                        version_str_alt in doc_id):
                        draft_proposals.append({
                            'id': doc_id,
                            'filepath': filepath,
                            'version': version_str,
                            'match_type': 'branch_version'
                        })
                        break

                # Check if impacted
                if doc_id in impacts:
                    draft_proposals.append({
                        'id': doc_id,
                        'filepath': filepath,
                        'version': None,
                        'match_type': 'impacts'
                    })

            except (IOError, OSError):
                continue

    # Return first match (prefer branch_version over impacts)
    for prop in draft_proposals:
        if prop['match_type'] == 'branch_version':
            return prop

    return draft_proposals[0] if draft_proposals else None


def graduate_proposal(proposal: dict, quiet: bool = False) -> bool:
    """Graduate a proposal from proposals/ to strategy/.

    Args:
        proposal: Dict with 'id', 'filepath', 'version'
        quiet: Suppress output

    Returns:
        True if graduation succeeded.
    """
    import shutil

    filepath = proposal['filepath']
    proposals_dir = get_proposals_dir()

    # Determine destination
    # If proposal is in proposals/v2.6/, move to strategy/v2.6/
    rel_path = os.path.relpath(filepath, proposals_dir)

    # Get strategy dir (sibling of proposals)
    strategy_dir = os.path.dirname(proposals_dir)  # Parent of proposals
    dest_path = os.path.join(strategy_dir, rel_path)
    dest_dir = os.path.dirname(dest_path)

    try:
        # Create destination directory if needed
        os.makedirs(dest_dir, exist_ok=True)

        # Read and update frontmatter
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update status: draft -> active
        content = re.sub(
            r'^(status:\s*)draft\s*$',
            r'\1active',
            content,
            flags=re.MULTILINE
        )

        # Write to new location
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Remove original
        os.remove(filepath)

        # Try to remove empty parent directories
        try:
            parent = os.path.dirname(filepath)
            if os.path.isdir(parent) and not os.listdir(parent):
                os.rmdir(parent)
        except OSError:
            pass

        # Add entry to decision_history.md
        add_graduation_to_ledger(proposal, dest_path)

        if not quiet:
            print(f"   ✅ Graduated: {os.path.basename(filepath)}")
            print(f"      From: proposals/{rel_path}")
            print(f"      To: strategy/{rel_path}")
            print(f"      Status: draft → active")

        return True

    except (IOError, OSError, shutil.Error) as e:
        if not quiet:
            print(f"   ❌ Graduation failed: {e}")
        return False


def add_graduation_to_ledger(proposal: dict, new_path: str) -> None:
    """Add APPROVED entry to decision_history.md."""
    history_path = get_decision_history_path()
    if not history_path or not os.path.exists(history_path):
        return

    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the ledger table
        # Format: | Date | Slug | Event | Decision / Outcome | Impacted | Archive Path |
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        slug = proposal['id'].replace('_', '-')
        version = proposal.get('version', '')

        new_entry = (
            f"| {today} | {slug} | feature | "
            f"APPROVED: {version or 'Proposal'} implemented. | "
            f"v2_strategy, schema | `{new_path}` |\n"
        )

        # Insert after the header row
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('|:--') or line.startswith('| Date'):
                continue
            if line.startswith('|') and '|' in line[1:]:
                # Found first data row, insert before it
                lines.insert(i, new_entry.strip())
                break

        with open(history_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    except (IOError, OSError):
        pass  # Non-fatal


def prompt_graduation(proposal: dict, quiet: bool = False) -> bool:
    """Prompt user to graduate a proposal.

    Returns:
        True if user chose to graduate and it succeeded.
    """
    if quiet:
        return False

    print(f"\n💡 Detected: This session may implement proposal '{proposal['id']}'")
    if proposal.get('version'):
        print(f"   (Branch matches version {proposal['version']})")

    try:
        response = input("   Graduate to strategy/? [y/N]: ").strip().lower()
        if response in ('y', 'yes'):
            return graduate_proposal(proposal, quiet)
    except (EOFError, KeyboardInterrupt):
        pass

    return False


# =============================================================================
# SESSION APPENDING (v2.4)
# =============================================================================


def get_current_branch() -> Optional[str]:
    """Get current git branch name.
    
    Returns:
        Branch name or None if not on a branch.
    """
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def slugify(text: str) -> str:
    """Convert text (branch name) to filename-safe slug.
    
    Examples:
        feat/login-flow -> login-flow
        fix/BUG-123 -> bug-123
    """
    # Remove common prefixes
    if '/' in text:
        text = text.split('/')[-1]
    
    # Convert to lowercase and replace unsafe chars
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    
    # Truncate to MAX_SLUG_LENGTH
    return slug[:50] if slug else 'session'


def find_existing_log_for_today(branch_slug: str, branch_name: str) -> Optional[str]:
    """Find existing log for this branch created today.
    
    v1.2: Exact match first, then collision variants. Validates branch name.
    
    Args:
        branch_slug: Slugified branch name
        branch_name: Full branch name for validation
    
    Returns:
        Path to existing log or None.
    """
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 1. Try exact match first (most common case)
    exact = os.path.join(LOGS_DIR, f"{today}_{branch_slug}.md")
    if os.path.exists(exact):
        if validate_branch_in_log(exact, branch_name):
            return exact
        # Log exists but for different branch - collision!
        print(f"⚠️  Slug collision: {exact} belongs to different branch")
    
    # 2. Check collision variants (-2, -3, etc.)
    for i in range(2, 100):  # v2.4: Extended from 10 to 100 per PR review
        variant = os.path.join(LOGS_DIR, f"{today}_{branch_slug}-{i}.md")
        if os.path.exists(variant):
            if validate_branch_in_log(variant, branch_name):
                return variant
    
    return None  # No existing log found


def validate_branch_in_log(log_path: str, expected_branch: str) -> bool:
    """Check if log's frontmatter branch matches expected.
    
    v1.2: Prevents wrong-log-appended bugs.
    
    Args:
        log_path: Path to log file
        expected_branch: Branch name to validate against
        
    Returns:
        True if branch matches or no branch field (legacy).
    """
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Extract branch from frontmatter
        match = re.search(r'^branch:\s*(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip() == expected_branch
        # Legacy logs without branch field - assume match
        return True
    except (IOError, OSError):
        return False


def append_to_log(log_path: str, new_commits: list) -> bool:
    """Append new commits to existing log's Raw Session History.
    
    v1.2: Deduplicates commits to handle amend+push scenarios.
    v1.3: Robust line-by-line parsing instead of fragile regex.
    v1.4: Fallback behavior when section is missing.
    
    Args:
        log_path: Path to log file
        new_commits: List of commit strings (format: "hash - message")
    
    Returns:
        True if append succeeded, False if fallback needed.
    """
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
    except (IOError, OSError):
        return False
    
    # Extract existing commit hashes to prevent duplicates
    existing_hashes = set()
    for line in lines:
        match = re.match(r'^([a-f0-9]{7,40}) -', line)
        if match:
            existing_hashes.add(match.group(1)[:7])
    
    # Filter out duplicates
    unique_commits = [c for c in new_commits if c.split()[0][:7] not in existing_hashes]
    
    if not unique_commits:
        print("ℹ️  No new commits to append (all already present)")
        return True
    
    # Find Raw Session History section using line-by-line parsing
    output_lines = []
    in_history_section = False
    in_code_block = False
    inserted = False
    
    for line in lines:
        output_lines.append(line)
        
        # Detect start of Raw Session History section
        if line.strip() == "## Raw Session History":
            in_history_section = True
            continue
        
        # Detect code block boundaries within history section
        if in_history_section and line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
            else:
                # End of code block - insert new commits BEFORE closing ```
                if not inserted:
                    output_lines.pop()  # Remove the closing ```
                    for commit in unique_commits:
                        output_lines.append(commit)
                    output_lines.append(line)  # Re-add closing ```
                    inserted = True
                in_code_block = False
                in_history_section = False
    
    # v1.4: Fallback if section was missing
    if not inserted:
        print(f"⚠️  Could not find '## Raw Session History' section in {log_path}")
        print(f"    Creating new log instead of appending.")
        return False  # Signal caller to create new log
    
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(output_lines))
        print(f"📝 Appended {len(unique_commits)} commits to {log_path}")
        return True
    except (IOError, OSError):
        return False


def get_commits_since_push() -> list:
    """Get commits that will be pushed (not yet on remote).
    
    Returns:
        List of commit strings (format: "hash - message")
    """
    try:
        # Get commits since upstream
        result = subprocess.run(
            ['git', 'log', '@{u}..HEAD', '--pretty=format:%h - %s'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')
        
        # Fallback to last 5 commits if no upstream
        result = subprocess.run(
            ['git', 'log', '-5', '--pretty=format:%h - %s'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def find_enhance_target() -> Optional[str]:
    """Find most recent auto-generated log for current branch.
    
    v2.4.1: Added branch validation to prevent matching logs from
    different branches with same slug suffix (per Codex review).
    
    Returns:
        Path to auto-generated log or None.
    """
    branch = get_current_branch()
    if not branch:
        return None
    
    branch_slug = slugify(branch)
    
    # Look for logs matching branch slug
    if not os.path.exists(LOGS_DIR):
        return None
    
    matching_logs = []
    for filename in os.listdir(LOGS_DIR):
        if filename.endswith('.md') and branch_slug in filename:
            log_path = os.path.join(LOGS_DIR, filename)
            # Check if it's auto-generated AND belongs to current branch
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read(500)  # Only need frontmatter
                if 'status: auto-generated' in content:
                    # v2.4.1: Validate branch to avoid slug collision false positives
                    if validate_branch_in_log(log_path, branch):
                        matching_logs.append(log_path)
            except (IOError, OSError):
                pass
    
    if not matching_logs:
        return None
    
    # Return most recent (sorted by filename which includes date)
    return sorted(matching_logs, reverse=True)[0]


def find_active_log_for_branch() -> Optional[str]:
    """Find most recent ACTIVE (already enriched) log for current branch.
    
    v2.4: Used by --enhance to distinguish between "not found" (exit 1)
    and "already enriched" (exit 2).
    
    Returns:
        Path to active log or None.
    """
    branch = get_current_branch()
    if not branch:
        return None
    
    branch_slug = slugify(branch)
    
    if not os.path.exists(LOGS_DIR):
        return None
    
    matching_logs = []
    for filename in os.listdir(LOGS_DIR):
        if filename.endswith('.md') and branch_slug in filename:
            log_path = os.path.join(LOGS_DIR, filename)
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read(500)
                # Look for active status (already enriched) AND validate branch
                if 'status: active' in content:
                    # v2.4.1: Validate branch to avoid slug collision false positives
                    if validate_branch_in_log(log_path, branch):
                        matching_logs.append(log_path)
            except (IOError, OSError):
                pass
    
    if not matching_logs:
        return None
    
    return sorted(matching_logs, reverse=True)[0]


def auto_archive(branch: str, source: str, quiet: bool = False) -> bool:
    """Auto-archive for pre-push hook.
    
    Creates or appends to session log automatically.
    
    Args:
        branch: Current branch name
        source: Source for log attribution
        quiet: Suppress output
    
    Returns:
        True if log was created/updated, False on error.
    """
    branch_slug = slugify(branch)
    commits = get_commits_since_push()
    
    if not commits:
        if not quiet:
            print("ℹ️  No commits to archive")
        return True
    
    # Check for existing log to append to
    existing_log = find_existing_log_for_today(branch_slug, branch)
    
    if existing_log:
        success = append_to_log(existing_log, commits)
        if success:
            _create_archive_marker(existing_log)
            return True
        # Fallback: create new log
        if not quiet:
            print("    Falling back to new log creation...")
    
    # Infer event type from branch prefix
    event_type = 'chore'
    if branch.startswith('feat') or branch.startswith('feature'):
        event_type = 'feature'
    elif branch.startswith('fix'):
        event_type = 'fix'
    elif branch.startswith('refactor'):
        event_type = 'refactor'
    
    # Create new log with auto-generated status
    return create_auto_log(branch_slug, branch, source, event_type, commits, quiet)


def create_auto_log(
    topic_slug: str,
    branch: str,
    source: str,
    event_type: str,
    commits: list,
    quiet: bool = False
) -> bool:
    """Create auto-generated log for session appending.
    
    Args:
        topic_slug: Slug for filename
        branch: Full branch name for frontmatter
        source: Log source attribution
        event_type: Type of work
        commits: List of commit strings
        quiet: Suppress output
    
    Returns:
        True on success.
    """
    try:
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)
    except OSError:
        return False
    
    now = datetime.datetime.now().astimezone()
    today_date = now.strftime("%Y-%m-%d")
    today_datetime = now.strftime("%Y-%m-%d %H:%M %Z")
    
    # Handle collision
    filename = f"{today_date}_{topic_slug}.md"
    filepath = os.path.join(LOGS_DIR, filename)
    counter = 2
    while os.path.exists(filepath):
        if validate_branch_in_log(filepath, branch):
            # Found the right log, append instead
            return append_to_log(filepath, commits)
        filename = f"{today_date}_{topic_slug}-{counter}.md"
        filepath = os.path.join(LOGS_DIR, filename)
        counter += 1
    
    commits_text = '\n'.join(commits) if commits else 'No commits'
    source_line = f"\nSource: {source}" if source else ""
    
    # v2.4: Auto-generated log template
    content = f"""---
id: log_{today_date.replace('-', '')}_{topic_slug.replace('-', '_')}
type: log
status: auto-generated
branch: {branch}
event_type: {event_type}
concepts: []
impacts: []
---

# Session Log: {topic_slug.replace('-', ' ').title()}
Date: {today_datetime}{source_line}
Event Type: {event_type}

## 1. Goal
<!-- Auto-generated log. Run 'Archive Ontos --enhance' to enrich. -->

## 2. Changes Made
<!-- Commits below; add human summary above. -->
-

---
## Raw Session History
```text
{commits_text}
```
"""
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except (IOError, OSError):
        return False
    
    if not quiet:
        print(f"""
┌────────────────────────────────────────────────────────────┐
│             📝 SESSION LOG AUTO-GENERATED                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Created: {filepath:<50}
│  Status: auto-generated (needs enrichment)                │
│                                                            │
│  This log will be included in your NEXT commit.           │
│  To include it now: git add . && git commit --amend       │
│                                                            │
│  Push proceeding with current commits...                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
""")
    
    _create_archive_marker(filepath)
    return True

# =============================================================================
# TEMPLATES (v2.3)
# =============================================================================

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
    
    content += "---\n## Raw Session History\n```text\n{daily_log}\n```\n"
    return content

# Marker file for pre-push hook integration
ARCHIVE_MARKER_FILE = os.path.join(PROJECT_ROOT, '.ontos', 'session_archived')

# Valid slug pattern: lowercase letters, numbers, and hyphens
VALID_SLUG_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$')
MAX_SLUG_LENGTH = 50

# Changelog categories per Keep a Changelog spec
CHANGELOG_CATEGORIES = ['added', 'changed', 'deprecated', 'removed', 'fixed', 'security']

# Default changelog path (relative to project root)
DEFAULT_CHANGELOG = 'CHANGELOG.md'


def validate_topic_slug(slug: str) -> tuple[bool, str]:
    """Validate topic slug for use in filenames.

    Args:
        slug: The topic slug to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not slug:
        return False, "Topic slug cannot be empty."

    if len(slug) > MAX_SLUG_LENGTH:
        return False, f"Topic slug too long (max {MAX_SLUG_LENGTH} characters)."

    # Convert to lowercase for validation
    slug_lower = slug.lower()

    if not VALID_SLUG_PATTERN.match(slug_lower):
        return False, (
            "Invalid topic slug. Use lowercase letters, numbers, and hyphens only.\n"
            "  Examples: 'auth-refactor', 'bug-fix', 'feature-123'"
        )

    # Check for reserved names on Windows
    reserved = {'con', 'prn', 'aux', 'nul', 'com1', 'lpt1'}
    if slug_lower in reserved:
        return False, f"'{slug}' is a reserved name and cannot be used."

    return True, ""


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
                slug = branch.lower().replace('_', '-').replace('.', '-')[:50]
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


def get_session_git_log() -> str:
    """Gets the git log since the last session log.

    Falls back to last 20 commits if no previous session log exists.

    Returns:
        Formatted git log string or error message.
    """
    try:
        last_session_date = find_last_session_date()

        if last_session_date:
            cmd = ['git', 'log', f'--since={last_session_date}', '--pretty=format:%h - %s']
        else:
            # No previous session log, get last 20 commits
            cmd = ['git', 'log', '-n', '20', '--pretty=format:%h - %s']

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return "Git log unavailable (not a git repository or git not installed)."

        logs = result.stdout.strip()
        if not logs:
            if last_session_date:
                return f"No commits found since last session ({last_session_date})."
            return "No commits found."
        return logs
    except subprocess.TimeoutExpired:
        return "Git log timed out."
    except FileNotFoundError:
        return "Git is not installed or not in PATH."
    except Exception as e:
        return f"Error running git: {e}"


def find_changelog() -> str:
    """Find the project's CHANGELOG.md file.

    Searches current directory and parent directories up to git root.

    Returns:
        Path to CHANGELOG.md or empty string if not found.
    """
    # Start from current directory
    current = os.getcwd()

    while True:
        changelog_path = os.path.join(current, DEFAULT_CHANGELOG)
        if os.path.exists(changelog_path):
            return changelog_path

        # Check if we're at git root or filesystem root
        git_dir = os.path.join(current, '.git')
        parent = os.path.dirname(current)

        if os.path.exists(git_dir) or parent == current:
            # We're at git root or filesystem root, stop searching
            break

        current = parent

    return ""


def create_changelog() -> str:
    """Create a new CHANGELOG.md file with standard template.

    Returns:
        Path to created file or empty string on error.
    """
    changelog_path = DEFAULT_CHANGELOG

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

"""

    try:
        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return changelog_path
    except (IOError, OSError, PermissionError) as e:
        print(f"Error: Failed to create CHANGELOG.md: {e}")
        return ""


def prompt_changelog_entry(quiet: bool = False) -> tuple[str, str]:
    """Prompt user for changelog entry details.

    Args:
        quiet: If True, skip prompts and return empty.

    Returns:
        Tuple of (category, description) or empty strings if skipped.
    """
    if quiet:
        return "", ""

    print("\n--- Changelog Entry ---")
    print("Categories: added, changed, deprecated, removed, fixed, security")
    print("(Press Enter to skip)\n")

    try:
        category = input("Category: ").strip().lower()
        if not category:
            return "", ""

        if category not in CHANGELOG_CATEGORIES:
            print(f"Warning: '{category}' is not a standard category. Using anyway.")

        description = input("Description: ").strip()
        if not description:
            print("Skipping changelog entry (no description).")
            return "", ""

        return category, description
    except (EOFError, KeyboardInterrupt):
        print("\nSkipping changelog entry.")
        return "", ""


def add_changelog_entry(category: str, description: str, quiet: bool = False) -> bool:
    """Add an entry to the project's CHANGELOG.md under [Unreleased].

    Args:
        category: The changelog category (added, changed, fixed, etc.)
        description: The changelog entry description.
        quiet: Suppress output if True.

    Returns:
        True if entry was added successfully.
    """
    if not category or not description:
        return False

    changelog_path = find_changelog()

    if not changelog_path:
        if not quiet:
            print("No CHANGELOG.md found. Creating one...")
        changelog_path = create_changelog()
        if not changelog_path:
            return False

    try:
        with open(changelog_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (IOError, OSError) as e:
        print(f"Error: Failed to read {changelog_path}: {e}")
        return False

    # Capitalize category for display
    category_title = category.capitalize()

    # Find [Unreleased] section
    unreleased_pattern = r'(## \[Unreleased\].*?)(\n## \[|\Z)'
    unreleased_match = re.search(unreleased_pattern, content, re.DOTALL)

    if not unreleased_match:
        # No [Unreleased] section, add one after the header
        header_end = content.find('\n\n')
        if header_end == -1:
            header_end = len(content)

        new_section = f"\n\n## [Unreleased]\n\n### {category_title}\n- {description}\n"
        content = content[:header_end] + new_section + content[header_end:]
    else:
        unreleased_section = unreleased_match.group(1)

        # Check if category already exists in unreleased section
        category_pattern = rf'(### {category_title}\n)(.*?)(\n### |\n## \[|\Z)'
        category_match = re.search(category_pattern, unreleased_section, re.DOTALL | re.IGNORECASE)

        if category_match:
            # Add to existing category
            insert_pos = unreleased_match.start(1) + category_match.end(2)
            # Check if we need a newline
            if not content[insert_pos-1:insert_pos] == '\n':
                content = content[:insert_pos] + f"\n- {description}" + content[insert_pos:]
            else:
                content = content[:insert_pos] + f"- {description}\n" + content[insert_pos:]
        else:
            # Add new category section after [Unreleased] header
            unreleased_header_end = unreleased_match.start(1) + len('## [Unreleased]')
            # Find where to insert (after any existing content in unreleased)
            insert_pos = unreleased_header_end

            # Skip any whitespace after header
            while insert_pos < len(content) and content[insert_pos] in '\n\r':
                insert_pos += 1

            new_category = f"\n### {category_title}\n- {description}\n"
            content = content[:insert_pos] + new_category + content[insert_pos:]

    try:
        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write(content)

        if not quiet:
            print(f"Added to {changelog_path}: [{category_title}] {description}")
        return True
    except (IOError, OSError, PermissionError) as e:
        print(f"Error: Failed to write {changelog_path}: {e}")
        return False


def load_document_index() -> dict[str, str]:
    """Load mapping of filepaths to document IDs from context map.
    
    Returns:
        Dictionary mapping relative filepath to doc_id.
    """
    if not os.path.exists(CONTEXT_MAP_FILE):
        return {}
    
    index = {}
    
    # Parse the Index section of the context map
    with open(CONTEXT_MAP_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the Index table
    in_index = False
    for line in content.split('\n'):
        if '## ' in line and 'Index' in line:
            in_index = True
            continue
        if in_index and line.startswith('|') and '|' in line[1:]:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4 and parts[1] and parts[2]:
                doc_id = parts[1]
                # Extract filepath from markdown link if present
                filename_part = parts[2]
                if '(' in filename_part and ')' in filename_part:
                    filepath = filename_part.split('(')[1].split(')')[0]
                else:
                    filepath = filename_part
                if doc_id and doc_id != 'ID' and filepath:
                    index[filepath] = doc_id
        if in_index and line.startswith('#') and not line.startswith('|'):
            break
    
    return index


def suggest_impacts(quiet: bool = False) -> list[str]:
    """Suggest document IDs that may have been impacted by recent changes.
    
    Algorithm:
    1. Check uncommitted changes (git status)
    2. If clean, check commits made today (git log --since)
    3. Match changed files to known document paths
    4. Return matching IDs as suggestions
    
    This handles both the "work in progress" and "commit then archive" workflows.
    
    Returns:
        List of suggested document IDs.
    """
    try:
        changed_files = set()
        
        # =====================================================
        # STEP 1: Check uncommitted changes (staged + unstaged)
        # =====================================================
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    # Format: "XY filename" or "XY original -> renamed"
                    parts = line[3:].split(' -> ')
                    changed_files.add(parts[-1])
        
        # =====================================================
        # STEP 2: If nothing uncommitted, check today's commits
        # This handles the "commit then archive" workflow
        # =====================================================
        if not changed_files:
            # Use last session date instead of just today (v2.3)
            since_date = find_last_session_date()
            if not since_date:
                since_date = datetime.date.today().isoformat()
                
            result = subprocess.run(
                ['git', 'log', '--since', since_date, '--name-only', '--pretty=format:'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        changed_files.add(line)
            
            if not quiet and changed_files:
                print(f"ℹ️  No uncommitted changes; using today's commits instead")
        
        if not changed_files:
            return []
        
        # =====================================================
        # STEP 3: Match changed files to document IDs
        # =====================================================
        doc_index = load_document_index()
        if not doc_index:
            return []
        
        suggestions = set()
        for changed_file in changed_files:
            # Direct match
            if changed_file in doc_index:
                suggestions.add(doc_index[changed_file])
            
            # Directory-based match
            changed_dir = os.path.dirname(changed_file)
            if changed_dir:
                for doc_path, doc_id in doc_index.items():
                    doc_dir = os.path.dirname(doc_path)
                    if doc_dir and (doc_dir == changed_dir or changed_dir.startswith(doc_dir)):
                        suggestions.add(doc_id)
        
        # Filter out log documents (impacts should reference Space, not Time)
        final_suggestions = [s for s in suggestions if not s.startswith('log_')]
        
        if not quiet and final_suggestions:
            print(f"\n💡 Suggested impacts based on changes: {', '.join(final_suggestions)}")
        
        return final_suggestions
        
    except Exception as e:
        if not quiet:
            print(f"Warning: Could not suggest impacts: {e}")
        return []


def prompt_for_impacts(suggestions: list[str], quiet: bool = False) -> list[str]:
    """Interactive prompt for impact confirmation.
    
    Args:
        suggestions: Pre-computed suggestions from git analysis.
        quiet: If True, skip prompts and return suggestions as-is.
        
    Returns:
        Final list of impact IDs.
    """
    if quiet:
        return suggestions
    
    if suggestions:
        print(f"\nSuggested impacts: {', '.join(suggestions)}")
        try:
            response = input("Accept suggestions? [Y/n/edit]: ").strip().lower()
            
            if response in ('', 'y', 'yes'):
                return suggestions
            elif response in ('n', 'no'):
                manual = input("Enter impacts (comma-separated, or empty): ").strip()
                return [i.strip() for i in manual.split(',') if i.strip()] if manual else []
            else:
                # Edit mode - start with suggestions
                manual = input(f"Edit impacts (starting with {', '.join(suggestions)}): ").strip()
                return [i.strip() for i in manual.split(',') if i.strip()] if manual else suggestions
        except (EOFError, KeyboardInterrupt):
            print("\nUsing suggestions.")
            return suggestions
    else:
        try:
            manual = input("Enter impacts (comma-separated doc IDs, or empty): ").strip()
            return [i.strip() for i in manual.split(',') if i.strip()] if manual else []
        except (EOFError, KeyboardInterrupt):
            return []


def validate_concepts(concepts: list[str], quiet: bool = False) -> list[str]:
    """Validate concepts against Common_Concepts.md vocabulary.
    
    Returns:
        List of validated concepts (with warnings for unknown).
    """
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


def create_log_file(
    topic_slug: str, 
    quiet: bool = False, 
    source: str = "",
    event_type: str = "chore",
    concepts: list[str] = None,
    impacts: list[str] = None
) -> str:
    """Creates a new session log file with v2.0 schema.
    
    Args:
        topic_slug: Short slug describing the session.
        quiet: Suppress output if True.
        source: LLM/program that generated this log.
        event_type: Type of work (feature/fix/refactor/exploration/chore).
        concepts: List of concept tags for searchability.
        impacts: List of document IDs affected by this session.
        
    Returns:
        Path to the created log file, or empty string on error.
    """
    # Normalize inputs
    topic_slug = topic_slug.lower()
    concepts = concepts or []
    impacts = impacts or []
    
    try:
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)
            if not quiet:
                print(f"Created directory: {LOGS_DIR}")
    except (IOError, OSError, PermissionError) as e:
        print(f"Error: Failed to create directory {LOGS_DIR}: {e}")
        return ""

    now = datetime.datetime.now().astimezone()
    today_date = now.strftime("%Y-%m-%d")
    today_datetime = now.strftime("%Y-%m-%d %H:%M %Z")
    filename = f"{today_date}_{topic_slug}.md"
    filepath = os.path.join(LOGS_DIR, filename)

    if os.path.exists(filepath):
        if not quiet:
            print(f"Log file already exists: {filepath}")
        _create_archive_marker(filepath)
        return filepath

    daily_log = get_session_git_log()
    source_line = f"\nSource: {source}" if source else ""
    
    # Format concepts and impacts for YAML
    concepts_yaml = f"[{', '.join(concepts)}]" if concepts else "[]"
    impacts_yaml = f"[{', '.join(impacts)}]" if impacts else "[]"

    # v2.0 SCHEMA + v2.3 ADAPTIVE TEMPLATE
    template_content = generate_template_sections(event_type)
    
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

"""
    # Append the adaptive template (filling {daily_log})
    content += template_content.format(daily_log=daily_log)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except (IOError, OSError, PermissionError) as e:
        print(f"Error: Failed to write log file: {e}")
        return ""

    if not quiet:
        print(f"Created session log: {filepath}")

    # Create marker file for pre-push hook
    _create_archive_marker(filepath)

    return filepath


def _create_archive_marker(log_filepath: str) -> None:
    """Create marker file to signal that a session was archived.

    The pre-push hook checks for this marker to enforce archiving before push.
    The marker is cleared by successful git push (via post-push or manual clear).

    Args:
        log_filepath: Path to the created log file (stored in marker for reference).
    """
    try:
        marker_dir = os.path.dirname(ARCHIVE_MARKER_FILE)
        os.makedirs(marker_dir, exist_ok=True)

        with open(ARCHIVE_MARKER_FILE, 'w', encoding='utf-8') as f:
            f.write(f"archived={datetime.datetime.now().isoformat()}\n")
            f.write(f"log={log_filepath}\n")
    except (IOError, OSError, PermissionError):
        # Non-fatal: marker creation failure shouldn't break archiving
        pass


# =============================================================================
# V2.7 STALENESS WARNING
# =============================================================================


def check_stale_docs_warning() -> None:
    """Check for stale documentation and warn the user.
    
    v2.7: Runs after session archiving to alert users about potentially
    outdated documentation that may need review.
    """
    from ontos_config import DOCS_DIR, is_ontos_repo
    
    try:
        # Import scan_docs dynamically to avoid circular imports
        from ontos_generate_context_map import scan_docs
        
        # Determine scan directories
        if is_ontos_repo():
            target_dirs = [DOCS_DIR, 'docs']
        else:
            target_dirs = [DOCS_DIR]
        
        files_data = scan_docs(target_dirs)
        
        # Build ID to path mapping
        id_to_path = {doc_id: data['filepath'] for doc_id, data in files_data.items()}
        
        stale_docs = []
        for doc_id, data in files_data.items():
            describes = data.get('describes', [])
            if not describes:
                continue
            
            staleness = check_staleness(
                doc_id=doc_id,
                doc_path=data['filepath'],
                describes=describes,
                describes_verified=data.get('describes_verified'),
                id_to_path=id_to_path
            )
            
            if staleness and staleness.is_stale:
                stale_docs.append(staleness)
        
        if stale_docs:
            print(f"\n⚠️  {len(stale_docs)} document(s) may be stale:")
            for doc in stale_docs[:3]:  # Show max 3
                stale_str = ", ".join([f"{a}" for a, _ in doc.stale_atoms[:2]])
                print(f"   - {doc.doc_id}: describes {stale_str} (modified after {doc.verified_date})")
            if len(stale_docs) > 3:
                print(f"   ... and {len(stale_docs) - 3} more")
            print("   Run: python3 .ontos/scripts/ontos_verify.py --all")
    except Exception as e:
        # Non-fatal: log for debugging but don't block archive
        import logging
        logging.debug(f"Staleness check skipped: {e}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scaffold a new session log file with optional changelog integration.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 ontos_end_session.py auth-refactor                     # Create log for auth refactor session
  python3 ontos_end_session.py bug-fix -e fix                    # Create log with 'fix' event type
  python3 ontos_end_session.py feature-x -e feature --suggest-impacts # Auto-detect impacts
  python3 ontos_end_session.py api-refactor --impacts "api_spec,user_model" # Manual impacts
  python3 ontos_end_session.py hotfix --quiet                    # Create log without output

Changelog Integration:
  Use --changelog to be prompted for a changelog entry. The entry will be
  added to your project's CHANGELOG.md under the [Unreleased] section.

  Categories: added, changed, deprecated, removed, fixed, security

Slug format:
  - Use lowercase letters, numbers, and hyphens
  - Examples: 'auth-refactor', 'v2-migration', 'fix-123'
"""
    )
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('topic', type=str, nargs='?', help='Short slug describing the session (optional, auto-generated if omitted)')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Preview log file without creating it')
    parser.add_argument('--list-concepts', action='store_true', help='Print available concepts and exit')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress non-error output')
    parser.add_argument('--changelog', '-c', action='store_true',
                        help='Prompt for a changelog entry to add to CHANGELOG.md')
    parser.add_argument('--changelog-category', type=str, metavar='CAT',
                        help='Changelog category (added/changed/fixed/etc.) - skips prompt')
    parser.add_argument('--changelog-message', type=str, metavar='MSG',
                        help='Changelog description - skips prompt')
    source_default = DEFAULT_SOURCE
    source_required = REQUIRE_SOURCE_IN_LOGS and not DEFAULT_SOURCE
    source_help = 'LLM/program that generated this log'
    if source_default:
        source_help += f' (default: {source_default})'
    elif source_required:
        source_help += ' [REQUIRED]'
        
    # v2.3 UX: Make source optional in argparse to allow other commands (list-concepts) to run
    # We will enforce source requirement manually later if needed.
    parser.add_argument('--source', '-s', type=str, metavar='NAME',
                        default=source_default,
                        required=False,
                        help=source_help)
    
    # NEW v2.0 arguments
    parser.add_argument('--event-type', '-e', type=str, metavar='TYPE',
                        choices=['feature', 'fix', 'refactor', 'exploration', 'chore', 'decision'],
                        help='Type of work performed (feature/fix/refactor/exploration/chore/decision)')
    parser.add_argument('--concepts', type=str, metavar='TAGS',
                        help='Comma-separated concept tags (e.g., "auth,oauth,security")')
    parser.add_argument('--impacts', type=str, metavar='IDS',
                        help='Comma-separated doc IDs impacted (e.g., "auth_flow,api_spec")')
    parser.add_argument('--suggest-impacts', action='store_true',
                        help='Auto-suggest impacts based on git changes')
    
    # v2.4 arguments
    parser.add_argument('--auto', action='store_true',
                        help='Auto-archive mode (called by pre-push hook)')
    parser.add_argument('--enhance', action='store_true',
                        help='Find and display auto-generated log for enrichment')

    args = parser.parse_args()


    # Handle --enhance early exit (v2.4)
    if args.enhance:
        target = find_enhance_target()
        if target:
            print(f"📝 Enhancing: {target}")
            print(f"   Status: auto-generated → active (after you fill in details)\n")
            try:
                with open(target, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(content)
                print("\n" + "="*60)
                print("To complete enhancement:")
                print("1. Edit the file above to fill in Goal, Key Decisions, Alternatives")
                print("2. Add concepts and verify impacts")
                print("3. Change 'status: auto-generated' to 'status: active'")
                print("4. Commit the enriched log")
                print("="*60)
            except (IOError, OSError) as e:
                print(f"Error reading log: {e}")
            sys.exit(0)
        else:
            # v2.4: Check if there's an already-active log (exit code 2)
            active = find_active_log_for_branch()
            if active:
                print(f"ℹ️  Log already enriched: {active}")
                print("   Status is already 'active'. No enhancement needed.")
                sys.exit(2)
            print("No auto-generated log found for current branch.")
            print("Run normal 'Archive Ontos' flow to create new log.")
            sys.exit(1)
    
    # Handle --auto mode (v2.4)
    if args.auto:
        branch = get_current_branch()
        if not branch:
            print("⚠️  Not on a branch, skipping auto-archive")
            sys.exit(0)
        
        if branch.lower() in BLOCKED_BRANCH_NAMES:
            print(f"⚠️  Branch '{branch}' not suitable for auto-archive")
            sys.exit(0)
        
        # Get source with fallback chain
        from ontos_lib import get_source
        source = get_source() or ''
        
        success = auto_archive(branch, source, args.quiet)
        sys.exit(0 if success else 1)

    # Handle list-concepts early exit
    if args.list_concepts:
        concepts = load_common_concepts()
        if concepts:
            print("Available concepts:")
            for c in sorted(concepts):
                print(f"  {c}")
        else:
            print("No Common_Concepts.md found.")
        sys.exit(0)

    # Auto-generate slug if missing
    if not args.topic:
        auto_slug = generate_auto_slug(args.quiet)
        if auto_slug:
            args.topic = auto_slug
            if not args.quiet:
                print(f"Auto-generated slug: {args.topic}")
        else:
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

    # Validate source manually if required (and not just listing concepts)
    if source_required and not args.source:
         print("Error: argument --source/-s is required")
         print(f"Usage: {sys.argv[0]} {args.topic or 'slug'} -s SOURCE ...")
         sys.exit(1)

    # Validate topic slug
    is_valid, error_msg = validate_topic_slug(args.topic)
    if not is_valid:
        print(f"Error: {error_msg}")
        sys.exit(1)
        
    # Process event_type
    event_type = args.event_type or 'chore'
    
    # Process concepts
    concepts = []
    if args.concepts:
        concepts = [c.strip() for c in args.concepts.split(',') if c.strip()]
        
    # Validate concepts (NEW in v2.3)
    if concepts:
        concepts = validate_concepts(concepts, args.quiet)

    # Process impacts
    impacts = []
    if args.impacts:
        impacts = [i.strip() for i in args.impacts.split(',') if i.strip()]
        
    # Auto-suggest impacts if requested
    if args.suggest_impacts:
        suggestions = suggest_impacts(args.quiet)
        if suggestions:
            impacts = prompt_for_impacts(suggestions, args.quiet)

    # Nudge if impacts is still empty
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

    # Handle Dry Run
    if args.dry_run:
        # Generate content preview
        template_sections = generate_template_sections(event_type)
        # Mock daily log for dry run
        daily_log = get_session_git_log()
        preview_content = template_sections.format(daily_log=daily_log)
        
        print("\n" + "=" * 60)
        print("DRY RUN - Would create the following log:")
        print("=" * 60 + "\n")
        
        print(f"File: {LOGS_DIR}/{datetime.datetime.now().strftime('%Y-%m-%d')}_{args.topic}.md")
        print(f"Event Type: {event_type}")
        print(f"Source: {args.source or DEFAULT_SOURCE or '(none)'}")
        print(f"Concepts: {concepts}")
        print(f"Impacts: {impacts}")
        print()
        print("Template Content:")
        # Show first few lines of template content
        lines = preview_content.split('\n')
        for line in lines[:15]:
            print(f"  {line}")
        if len(lines) > 15:
            print("  ... (rest of content)")
        
        print("\n" + "=" * 60)
        print("END DRY RUN - No file created")
        print("=" * 60)
        sys.exit(0)

    # Create session log
    result = create_log_file(
        args.topic,
        args.quiet,
        args.source or "",
        event_type,
        concepts,
        impacts
    )
    if not result:
        sys.exit(1)

    # v2.6.1: Check for proposal graduation
    branch = get_current_branch()
    if branch:
        proposal = detect_implemented_proposal(branch, impacts)
        if proposal:
            prompt_graduation(proposal, args.quiet)
    
    # v2.7: Check for stale documentation
    if not args.quiet:
        check_stale_docs_warning()

    # Handle changelog integration
    if args.changelog or args.changelog_category or args.changelog_message:
        if args.changelog_category and args.changelog_message:
            # Non-interactive mode
            add_changelog_entry(args.changelog_category, args.changelog_message, args.quiet)
        else:
            # Interactive mode
            category, description = prompt_changelog_entry(args.quiet)
            if category and description:
                add_changelog_entry(category, description, args.quiet)


if __name__ == "__main__":
    main()
