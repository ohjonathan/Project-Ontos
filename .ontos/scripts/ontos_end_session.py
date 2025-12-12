"""Scaffold a new session log file for Ontos with optional changelog integration."""

import os
import re
import datetime
import subprocess
import argparse
import sys

from ontos_config import __version__, LOGS_DIR, CONTEXT_MAP_FILE, PROJECT_ROOT, REQUIRE_SOURCE_IN_LOGS

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


def find_last_session_date() -> str:
    """Find the date of the most recent session log.

    Returns:
        Date string in YYYY-MM-DD format, or empty string if no logs found.
    """
    if not os.path.exists(LOGS_DIR):
        return ""

    log_files = []
    for filename in os.listdir(LOGS_DIR):
        if filename.endswith('.md') and len(filename) >= 10:
            # Extract date from filename (format: YYYY-MM-DD_topic.md)
            date_part = filename[:10]
            # Validate it looks like a date
            if date_part.count('-') == 2:
                log_files.append(date_part)

    if not log_files:
        return ""

    # Return the most recent date
    return sorted(log_files)[-1]


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
            today = datetime.date.today().isoformat()
            result = subprocess.run(
                ['git', 'log', '--since', today, '--name-only', '--pretty=format:'],
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
        return filepath

    daily_log = get_session_git_log()
    source_line = f"\nSource: {source}" if source else ""
    
    # Format concepts and impacts for YAML
    concepts_yaml = f"[{', '.join(concepts)}]" if concepts else "[]"
    impacts_yaml = f"[{', '.join(impacts)}]" if impacts else "[]"

    # v2.0 SCHEMA
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
<!-- [AGENT: Fill this in. What was the primary objective of this session?] -->

## 2. Key Decisions
<!-- [AGENT: Fill this in. What architectural or design choices were made?] -->
-

## 3. Changes Made
<!-- [AGENT: Fill this in. Summary of file changes.] -->
-

## 4. Next Steps
<!-- [AGENT: Fill this in. What should the next agent work on?] -->
-

---
## Raw Session History
```text
{daily_log}
```
"""

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
    parser.add_argument('topic', type=str, nargs='?', help='Short slug describing the session (e.g. auth-refactor)')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress non-error output')
    parser.add_argument('--changelog', '-c', action='store_true',
                        help='Prompt for a changelog entry to add to CHANGELOG.md')
    parser.add_argument('--changelog-category', type=str, metavar='CAT',
                        help='Changelog category (added/changed/fixed/etc.) - skips prompt')
    parser.add_argument('--changelog-message', type=str, metavar='MSG',
                        help='Changelog description - skips prompt')
    source_required = REQUIRE_SOURCE_IN_LOGS
    source_help = 'LLM/program that generated this log (e.g., "Claude Code", "Antigravity")'
    if source_required:
        source_help += ' [REQUIRED]'
    parser.add_argument('--source', '-s', type=str, metavar='NAME', required=source_required,
                        help=source_help)
    
    # NEW v2.0 arguments
    parser.add_argument('--event-type', '-e', type=str, metavar='TYPE',
                        choices=['feature', 'fix', 'refactor', 'exploration', 'chore'],
                        help='Type of work performed (feature/fix/refactor/exploration/chore)')
    parser.add_argument('--concepts', type=str, metavar='TAGS',
                        help='Comma-separated concept tags (e.g., "auth,oauth,security")')
    parser.add_argument('--impacts', type=str, metavar='IDS',
                        help='Comma-separated doc IDs impacted (e.g., "auth_flow,api_spec")')
    parser.add_argument('--suggest-impacts', action='store_true',
                        help='Auto-suggest impacts based on git changes')

    args = parser.parse_args()

    if not args.topic:
        print("Error: Missing required argument 'topic'. Provide a short slug describing the session.")
        print("Example: python3 ontos_end_session.py auth-refactor -s \"Claude Code\" -e feature\n")
        parser.print_help()
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
        
    # Process impacts
    impacts = []
    if args.impacts:
        impacts = [i.strip() for i in args.impacts.split(',') if i.strip()]
        
    # Auto-suggest impacts if requested
    if args.suggest_impacts:
        suggestions = suggest_impacts(args.quiet)
        if suggestions:
            impacts = prompt_for_impacts(suggestions, args.quiet)

    # Create session log
    result = create_log_file(
        args.topic,
        args.quiet,
        args.source or "",  # Empty string if not provided (when optional)
        event_type,
        concepts,
        impacts
    )
    if not result:
        sys.exit(1)

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
