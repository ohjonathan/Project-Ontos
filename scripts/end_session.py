"""Scaffold a new session log file for Ontos with optional changelog integration."""

import os
import re
import datetime
import subprocess
import argparse
import sys

from config import __version__, LOGS_DIR

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


def get_daily_git_log() -> str:
    """Gets the git log for the current day.

    Returns:
        Formatted git log string or error message.
    """
    try:
        result = subprocess.run(
            ['git', 'log', '--since=midnight', '--pretty=format:%h - %s'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return "Git log unavailable (not a git repository or git not installed)."

        logs = result.stdout.strip()
        if not logs:
            return "No commits found for today."
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


def create_log_file(topic_slug: str, quiet: bool = False) -> str:
    """Creates a new session log file with a template.

    Args:
        topic_slug: Short slug describing the session.
        quiet: Suppress output if True.

    Returns:
        Path to the created log file, or empty string on error.
    """
    # Normalize slug to lowercase
    topic_slug = topic_slug.lower()

    try:
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)
            if not quiet:
                print(f"Created directory: {LOGS_DIR}")
    except (IOError, OSError, PermissionError) as e:
        print(f"Error: Failed to create directory {LOGS_DIR}: {e}")
        return ""

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"{today}_{topic_slug}.md"
    filepath = os.path.join(LOGS_DIR, filename)

    if os.path.exists(filepath):
        if not quiet:
            print(f"Log file already exists: {filepath}")
        return filepath

    daily_log = get_daily_git_log()

    content = f"""---
id: log_{today.replace('-', '')}_{topic_slug.replace('-', '_')}
type: atom
status: active
depends_on: []
---

# Session Log: {topic_slug.replace('-', ' ').title()}
Date: {today}

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
    return filepath


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scaffold a new session log file with optional changelog integration.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 end_session.py auth-refactor           # Create log for auth refactor session
  python3 end_session.py bug-fix --changelog     # Create log and prompt for changelog entry
  python3 end_session.py feature-x -c            # Short form of --changelog
  python3 end_session.py hotfix --quiet          # Create log without output

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
    args = parser.parse_args()

    if not args.topic:
        parser.print_help()
        sys.exit(1)

    # Validate topic slug
    is_valid, error_msg = validate_topic_slug(args.topic)
    if not is_valid:
        print(f"Error: {error_msg}")
        sys.exit(1)

    # Create session log
    result = create_log_file(args.topic, args.quiet)
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
