"""Consolidate old session logs into decision history."""

import os
import re
import sys
import datetime
import argparse
import shutil
from pathlib import Path
from typing import Optional, List, Tuple

# Add scripts dir to path

from ontos.core.frontmatter import parse_frontmatter
from ontos.core.paths import find_last_session_date
from ontos_config import __version__, PROJECT_ROOT, is_ontos_repo
from ontos.core.context import SessionContext
from ontos.ui.output import OutputHandler

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
    """Find logs older than threshold (age-based).

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


def find_excess_logs(retention_count: int = 15) -> List[Tuple[str, str, dict]]:
    """Find logs exceeding retention count (count-based).

    Keeps the newest N logs, returns the rest for consolidation.

    Args:
        retention_count: Number of newest logs to keep.

    Returns:
        List of (filepath, doc_id, frontmatter) tuples, oldest first.
    """
    if not os.path.exists(LOGS_DIR):
        return []

    all_logs = []

    for filename in sorted(os.listdir(LOGS_DIR)):
        if not filename.endswith('.md'):
            continue
        if not re.match(r'^\d{4}-\d{2}-\d{2}', filename):
            continue

        filepath = os.path.join(LOGS_DIR, filename)
        frontmatter = parse_frontmatter(filepath)
        if frontmatter:
            all_logs.append((filepath, frontmatter.get('id', filename), frontmatter))

    # Sort by filename (date-based), oldest first
    all_logs.sort(key=lambda x: os.path.basename(x[0]))

    # Keep newest N, return the rest
    if len(all_logs) <= retention_count:
        return []

    return all_logs[:-retention_count]


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


def validate_decision_history(output: OutputHandler = None) -> bool:
    """Validate decision_history.md exists and has expected structure.
    
    Args:
        output: OutputHandler instance (creates default if None).
    
    Returns:
        True if valid, False otherwise.
    """
    if output is None:
        output = OutputHandler()
    
    if not os.path.exists(DECISION_HISTORY_FILE):
        output.error(f"{DECISION_HISTORY_FILE} not found.")
        output.info("Create it with the standard table header, or run 'ontos init'.")
        return False
    
    with open(DECISION_HISTORY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Validate History Ledger header exists (NOT Consolidation Log)
    if HISTORY_LEDGER_HEADER not in content:
        output.error("decision_history.md missing History Ledger table.")
        output.detail(f"Expected header containing: {HISTORY_LEDGER_HEADER}")
        output.info("Please fix the table structure manually.")
        return False
    
    return True


def append_to_decision_history(
    date: str,
    slug: str,
    event_type: str,
    summary: str,
    impacts: List[str],
    archive_path: str,
    output: OutputHandler = None,
    ctx: SessionContext = None
) -> bool:
    """Append entry to the History Ledger table in decision_history.md.
    
    CRITICAL FIX (v1.2): The file has TWO tables:
    1. History Ledger (where logs go) - has header "| Date | Slug | Event |..."
    2. Consolidation Log (metadata about consolidation acts) - different columns
    
    We must target the History Ledger specifically, not just "the last table".
    
    Args:
        date: Date string for the entry.
        slug: Session slug.
        event_type: Event type (chore, feature, fix, etc.).
        summary: One-line summary.
        impacts: List of impacted doc IDs.
        archive_path: Path where log was archived.
        output: OutputHandler instance (creates default if None).
        ctx: SessionContext instance (creates and owns one if None).
    
    Returns:
        True on success, False on failure.
    """
    _owns_ctx = ctx is None
    if _owns_ctx:
        ctx = SessionContext.from_repo(Path.cwd())
    if output is None:
        output = OutputHandler()
    
    if not validate_decision_history(output=output):
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
        output.error("Could not find insertion point in History Ledger table")
        return False
    
    # Insert new row after the last row of the History Ledger
    lines.insert(history_ledger_end + 1, new_row)
    
    # Buffer write (v2.8 transactional pattern)
    ctx.buffer_write(Path(DECISION_HISTORY_FILE), '\n'.join(lines))
    
    if _owns_ctx:
        ctx.commit()
    
    return True


def archive_log(filepath: str, dry_run: bool = False, output: OutputHandler = None) -> Optional[str]:
    """Move log to archive directory.
    
    Args:
        filepath: Path to the log file.
        dry_run: If True, don't actually move.
        output: OutputHandler instance (creates default if None).
    
    Returns:
        New archive path (relative), or None on failure.
    """
    if output is None:
        output = OutputHandler()
    
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
        output.error(f"Error archiving {filepath}: {e}")
        return None


def consolidate_log(filepath: str, doc_id: str, frontmatter: dict, 
                    dry_run: bool = False, quiet: bool = False,
                    auto: bool = False, output: OutputHandler = None,
                    ctx: SessionContext = None) -> bool:
    """Consolidate a single log file.
    
    Args:
        filepath: Path to the log file.
        doc_id: Document ID from frontmatter.
        frontmatter: Parsed frontmatter dict.
        dry_run: Preview without making changes.
        quiet: Suppress output.
        auto: Process without prompting.
        output: OutputHandler instance (creates default if None).
        ctx: SessionContext for transactional writes.
    
    Returns:
        True on success, False on skip/failure.
    """
    if output is None:
        output = OutputHandler(quiet=quiet)
    
    filename = os.path.basename(filepath)
    date = filename[:10]
    slug = filename[11:-3] if len(filename) > 14 else doc_id
    event_type = frontmatter.get('event_type', 'chore')
    impacts = frontmatter.get('impacts', [])
    
    summary = extract_summary(filepath)
    
    # Interactive summary fallback (from Gemini feedback)
    if not summary and not auto and not quiet:
        output.warning(f"Could not auto-extract summary from {doc_id}")
        try:
            summary = input("   Enter one-line summary: ").strip()
        except (EOFError, KeyboardInterrupt):
            summary = "(Manual entry required)"
    
    summary = summary or "(No summary captured)"
    
    output.plain(f"\n📄 {doc_id}")
    output.detail(f"Date: {date}")
    output.detail(f"Type: {event_type}")
    output.detail(f"Summary: {summary}")
    output.detail(f"Impacts: {impacts or '(none)'}")
    
    if dry_run:
        output.info(f"[DRY RUN] Would archive to: {ARCHIVE_DIR}/{filename}")
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
            output.info("Skipped.")
            return False
    
    # Archive file first
    rel_archive_path = archive_log(filepath, dry_run, output=output)
    if not rel_archive_path:
        return False
    
    # Append to decision history
    if append_to_decision_history(date, slug, event_type, summary, impacts, rel_archive_path, output=output, ctx=ctx):
        output.success("Archived and recorded in decision_history.md")
        return True
    else:
        output.warning("File archived but failed to update decision_history.md")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Consolidate old session logs into decision history.',
        epilog="""
This script consolidates logs that exceed the retention threshold:
1. Finds logs exceeding retention count (default: keep newest 15)
2. Shows summary for each
3. Prompts for confirmation
4. Archives log and updates decision_history.md (History Ledger table)

Example:
  python3 ontos_consolidate.py              # Keep newest 15, consolidate rest
  python3 ontos_consolidate.py --dry-run    # Preview what would happen
  python3 ontos_consolidate.py --count 10   # Keep newest 10 logs
  python3 ontos_consolidate.py --by-age     # Use age-based (legacy, 30 days)
  python3 ontos_consolidate.py --all        # Process all without prompting
"""
    )
    parser.add_argument('--version', '-V', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--count', type=int, default=15,
                        help='Number of newest logs to keep (default: 15)')
    parser.add_argument('--by-age', action='store_true',
                        help='Use age-based instead of count-based (legacy)')
    parser.add_argument('--days', type=int, default=30,
                        help='Age threshold in days, requires --by-age (default: 30)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Preview without making changes')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress output')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Process all logs without prompting')

    args = parser.parse_args()
    
    # v2.8.4: Create OutputHandler for all output
    output = OutputHandler(quiet=args.quiet)

    # Validate setup
    if not args.dry_run and not validate_decision_history(output=output):
        sys.exit(1)

    # Find logs to consolidate (count-based by default, age-based with --by-age)
    if args.by_age:
        logs_to_consolidate = find_old_logs(args.days)
        threshold_msg = f"older than {args.days} days"
        empty_msg = f"No logs older than {args.days} days. Nothing to consolidate."
    else:
        logs_to_consolidate = find_excess_logs(args.count)
        threshold_msg = f"exceeding retention count ({args.count})"
        empty_msg = f"Log count within threshold ({args.count}). Nothing to consolidate."

    if not logs_to_consolidate:
        output.success(empty_msg)
        return

    output.info(f"Found {len(logs_to_consolidate)} log(s) {threshold_msg}:")

    consolidated = 0
    for filepath, doc_id, frontmatter in logs_to_consolidate:
        if consolidate_log(filepath, doc_id, frontmatter, args.dry_run, args.quiet, args.all, output=output):
            consolidated += 1

    action = 'Would consolidate' if args.dry_run else 'Consolidated'
    output.info(f"{action} {consolidated} log(s).")


def emit_deprecation_notice(message: str) -> None:
    """Always-visible CLI notice for deprecated usage."""
    import sys
    print(f"[DEPRECATION] {message}", file=sys.stderr)


if __name__ == "__main__":
    import os
    if not os.environ.get('ONTOS_CLI_DISPATCH'):
        if not os.environ.get('ONTOS_NO_DEPRECATION_WARNINGS'):
            emit_deprecation_notice(
                f"Direct execution of {Path(__file__).name} is deprecated. "
                "Use 'python3 ontos.py consolidate' instead. "
                "Direct script execution will be removed in v3.0."
            )
    main()
