"""Native consolidate command implementation."""

import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from ontos.core.context import SessionContext
from ontos.io.files import find_project_root, scan_documents, load_documents, load_frontmatter
from ontos.io.yaml import parse_frontmatter_content
from ontos.ui.output import OutputHandler

HISTORY_LEDGER_HEADER = '| Date | Slug | Event | Decision / Outcome |'


@dataclass
class ConsolidateOptions:
    """Options for consolidate command."""
    count: int = 15
    by_age: bool = False
    days: int = 30
    dry_run: bool = False
    quiet: bool = False
    all: bool = False
    json_output: bool = False


def find_logs_to_consolidate(options: ConsolidateOptions, logs_dir: Path, load_result=None) -> List[Tuple[Path, str, dict]]:
    """Find logs to consolidate based on count or age."""
    if not logs_dir.exists():
        return []

    all_logs = []
    if load_result is None:
        load_result = load_documents(list(logs_dir.glob("*.md")), parse_frontmatter_content)
        if load_result.has_fatal_errors or load_result.duplicate_ids:
            return []

    # Filter and sort by filename (date-based), oldest first
    for doc in sorted(load_result.documents.values(), key=lambda d: d.filepath.name):
        path = doc.filepath
        if re.match(r'^\d{4}-\d{2}-\d{2}', path.name):
            all_logs.append((path, doc.id, doc.frontmatter))

    if options.by_age:
        today = datetime.now()
        logs_to_consolidate = []
        for path, doc_id, fm in all_logs:
            try:
                log_date = datetime.strptime(path.name[:10], '%Y-%m-%d')
                age_days = (today - log_date).days
                if age_days > options.days:
                    logs_to_consolidate.append((path, doc_id, fm))
            except ValueError:
                continue
        return logs_to_consolidate
    else:
        if len(all_logs) <= options.count:
            return []
        return all_logs[:-options.count]


def extract_summary(filepath: Path) -> Optional[str]:
    """Extract one-line summary from log's Goal section."""
    try:
        content = filepath.read_text(encoding='utf-8')
        # Matches legacy regex
        match = re.search(r'##\s*\d*\.?\s*Goal\s*\n(.+?)(?=\n## |\n---|\Z)', content, re.DOTALL)
        if match:
            goal = match.group(1).strip()
            goal = re.sub(r'<!--.*?-->', '', goal).strip()
            for line in goal.split('\n'):
                line = line.strip().lstrip('- ')
                if line and not line.startswith('<!--'):
                    return line[:100]
    except Exception:
        pass
    return None


def append_to_decision_history(
    date_str: str,
    slug: str,
    event_type: str,
    summary: str,
    impacts: List[str],
    archive_path: str,
    history_path: Path,
    ctx: SessionContext,
    output: OutputHandler
) -> bool:
    """Append entry to the History Ledger table in decision_history.md."""
    history_file = history_path
    if not history_file.exists():
        output.error(f"{history_file} not found.")
        return False

    content = history_file.read_text(encoding='utf-8')
    if HISTORY_LEDGER_HEADER not in content:
        output.error("decision_history.md missing History Ledger table.")
        return False

    impacts_str = ', '.join(impacts) if impacts else '—'
    safe_summary = summary.replace('|', '\\|')
    new_row = f"| {date_str} | {slug} | {event_type} | {safe_summary} | {impacts_str} | `{archive_path}` |"
    
    lines = content.split('\n')
    in_history_ledger = False
    history_ledger_end = -1
    
    for i, line in enumerate(lines):
        if HISTORY_LEDGER_HEADER in line:
            in_history_ledger = True
            continue
        
        if in_history_ledger:
            if line.strip().startswith('|'):
                history_ledger_end = i
            elif line.strip().startswith('##'):
                break
            elif not line.strip():
                # Look ahead
                found_header = False
                for j in range(i + 1, min(i + 3, len(lines))):
                    if lines[j].strip().startswith('##'):
                        found_header = True
                        break
                    elif lines[j].strip():
                        break
                if found_header:
                    break

    if history_ledger_end == -1:
        # Check if separator row exists
        for i, line in enumerate(lines):
            if HISTORY_LEDGER_HEADER in line:
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('|'):
                    history_ledger_end = i + 1
                    break

    if history_ledger_end == -1:
        output.error("Could not find insertion point in History Ledger table")
        return False

    lines.insert(history_ledger_end + 1, new_row)
    ctx.buffer_write(history_file, '\n'.join(lines))
    return True


def consolidate_command(options: ConsolidateOptions) -> Tuple[int, str]:
    """Execute consolidate command."""
    root = find_project_root()
    output = OutputHandler(quiet=options.quiet)
    # Resolve paths relative to runtime project root
    from ontos.io.config import load_project_config
    if (root / '.ontos-internal').exists():
        # Contributor mode
        logs_dir = root / ".ontos-internal" / "logs"
        archive_logs_dir = root / ".ontos-internal" / "archive" / "logs"
        decision_history_path = root / ".ontos-internal" / "reference" / "decision_history.md"
    else:
        # User mode
        config = load_project_config(repo_root=root)
        docs_dir_setting = str(config.paths.docs_dir).strip()
        docs_dir = root / docs_dir_setting
        from ontos.core.paths import _warn_deprecated
        
        # logs_dir
        if Path(config.paths.logs_dir).is_absolute():
            logs_dir = Path(config.paths.logs_dir)
        else:
            logs_dir = root / config.paths.logs_dir
            
        # archive_logs_dir (with fallback)
        new_archive_path = docs_dir / "archive" / "logs"
        old_archive_path = docs_dir / "archive"
        if new_archive_path.exists():
            archive_logs_dir = new_archive_path
        elif old_archive_path.exists():
            _warn_deprecated(
                f"{docs_dir_setting}/archive/",
                f"{docs_dir_setting}/archive/logs/",
            )
            archive_logs_dir = old_archive_path
        else:
            archive_logs_dir = new_archive_path
            
        # decision_history_path (with fallback)
        new_history_path = docs_dir / "strategy" / "decision_history.md"
        old_history_path = docs_dir / "decision_history.md"
        if new_history_path.exists():
            decision_history_path = new_history_path
        elif old_history_path.exists():
            _warn_deprecated(
                f"{docs_dir_setting}/decision_history.md",
                f"{docs_dir_setting}/strategy/decision_history.md",
            )
            decision_history_path = old_history_path
        else:
            decision_history_path = new_history_path

    load_result = None
    if logs_dir.exists():
        load_result = load_documents(list(logs_dir.glob("*.md")), parse_frontmatter_content)
        if load_result.has_fatal_errors or load_result.duplicate_ids:
            for issue in load_result.issues:
                if issue.code in {"duplicate_id", "parse_error", "io_error"}:
                    output.error(issue.message)
            return 1, "Document load failed"
            
    logs_to_consolidate = find_logs_to_consolidate(options, logs_dir, load_result=load_result)
    if not logs_to_consolidate:
        if not options.quiet:
            output.success("Nothing to consolidate.")
        return 0, "Nothing to consolidate"

    output.info(f"Found {len(logs_to_consolidate)} log(s) to consolidate:")
    
    ctx = SessionContext.from_repo(root)
    consolidated_count = 0
    archive_dir = archive_logs_dir
    
    for path, doc_id, fm in logs_to_consolidate:
        date_str = path.name[:10]
        slug = path.name[11:-3] if len(path.name) > 14 else doc_id
        event_type = fm.get('event_type', 'chore')
        impacts = fm.get('impacts', [])
        summary = extract_summary(path)
        
        if not summary and not options.all and not options.quiet:
            output.warning(f"Could not auto-extract summary from {doc_id}")
            try:
                summary = input("   Enter one-line summary: ").strip()
            except (EOFError, KeyboardInterrupt):
                summary = "(Manual entry required)"
        
        summary = summary or "(No summary captured)"
        
        output.plain(f"\n📄 {doc_id}")
        output.detail(f"Date: {date_str}")
        output.detail(f"Type: {event_type}")
        output.detail(f"Summary: {summary}")
        output.detail(f"Impacts: {impacts or '(none)'}")
        
        if options.dry_run:
            output.info(f"[DRY RUN] Would archive to: {archive_dir}/{path.name}")
            consolidated_count += 1
            continue

        # Confirmation
        if not options.all:
            try:
                confirm = input(f"   Archive this log? [y/N/edit]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n   Skipped.")
                continue
            
            if confirm == 'edit':
                new_summary = input(f"   New summary: ").strip()
                if new_summary:
                    summary = new_summary
                confirm = 'y'
            
            if confirm != 'y':
                output.info("Skipped.")
                continue

        # Archive
        archive_dir.mkdir(parents=True, exist_ok=True)
        new_path = archive_dir / path.name
        rel_archive_path = new_path.relative_to(root)
        
        try:
            # We use shutil.move for now, but SessionContext could handle moves too.
            # However, SessionContext currently only buffers writes/deletes.
            # For parity, we'll use shutil.move.
            shutil.move(str(path), str(new_path))
            
            if append_to_decision_history(date_str, slug, event_type, summary, impacts, str(rel_archive_path), decision_history_path, ctx, output):
                output.success("Archived and recorded in decision_history.md")
                consolidated_count += 1
            else:
                output.warning("File archived but failed to update decision_history.md")
        except Exception as e:
            output.error(f"Error archiving {path.name}: {e}")

    if not options.dry_run and consolidated_count > 0:
        ctx.commit()

    action = 'Would consolidate' if options.dry_run else 'Consolidated'
    output.info(f"{action} {consolidated_count} log(s).")
    
    return 0, f"{action} {consolidated_count} logs"
