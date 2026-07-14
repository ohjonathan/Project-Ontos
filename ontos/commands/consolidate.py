"""Native consolidate command implementation."""

import re
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from ontos.core.config import ConfigError, WorkflowConfig
from ontos.core.context import SessionContext
from ontos.core.frontmatter import normalize_reference_list
from ontos.io.files import find_project_root, load_documents
from ontos.io.yaml import parse_frontmatter_content
from ontos.ui.output import OutputHandler

HISTORY_LEDGER_HEADING = "## History Ledger"
HISTORY_LEDGER_HEADER = (
    "| Date | Slug | Event | Decision / Outcome | Impacts | Archive Path |"
)
HISTORY_LEDGER_SEPARATOR = "|:---|:---|:---|:---|:---|:---|"
HISTORY_LEDGER_SECTION = (
    f"{HISTORY_LEDGER_HEADING}\n\n"
    f"{HISTORY_LEDGER_HEADER}\n"
    f"{HISTORY_LEDGER_SEPARATOR}\n"
)
_GENERATED_HISTORY_MARKER = "GENERATED FILE - DO NOT EDIT MANUALLY"
_MINIMAL_DECISION_HISTORY = (
    "---\n"
    "id: decision_history\n"
    "type: strategy\n"
    "status: active\n"
    "depends_on: []\n"
    "---\n\n"
    "# Decision History\n\n"
    "This document records consolidated session-log decisions.\n\n"
    f"{HISTORY_LEDGER_SECTION}"
)


@dataclass
class ConsolidateOptions:
    """Options for consolidate command."""
    count: Optional[int] = None
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
        retention_count = (
            options.count
            if options.count is not None
            else WorkflowConfig().log_retention_count
        )
        if len(all_logs) <= retention_count:
            return []
        return all_logs[:-retention_count]


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
    """Append to the canonical ledger, initializing recognized histories."""
    history_file = history_path
    if history_file.exists():
        with history_file.open("r", encoding="utf-8", newline="") as handle:
            content = handle.read()
        if HISTORY_LEDGER_HEADER not in content:
            content = _append_canonical_history_ledger(content, output)
            if content is None:
                return False
    else:
        content = _MINIMAL_DECISION_HISTORY

    impacts_str = ', '.join(impacts) if impacts else '—'
    safe_summary = summary.replace('|', '\\|')
    new_row = f"| {date_str} | {slug} | {event_type} | {safe_summary} | {impacts_str} | `{archive_path}` |"

    updated = _insert_history_row(content, new_row, archive_path, output)
    if updated is None:
        return False
    if updated != content:
        ctx.buffer_write(history_file, updated)
    return True


def _append_canonical_history_ledger(
    content: str,
    output: OutputHandler,
) -> Optional[str]:
    """Append one ledger section only to a recognized decision history."""
    if HISTORY_LEDGER_HEADING in content:
        output.error("decision_history.md has a malformed History Ledger table.")
        return None

    has_heading = re.search(r"(?m)^# Decision History\s*$", content) is not None
    has_identity = (
        _GENERATED_HISTORY_MARKER in content
        or re.search(r"(?m)^id:\s*decision_history\s*$", content) is not None
    )
    if not has_heading or not has_identity:
        output.error(
            "decision_history.md is not a recognized decision-history document; "
            "refusing to modify it."
        )
        return None

    if content.endswith("\n\n"):
        separator = ""
    elif content.endswith("\n"):
        separator = "\n"
    else:
        separator = "\n\n"
    return f"{content}{separator}{HISTORY_LEDGER_SECTION}"


def _insert_history_row(
    content: str,
    new_row: str,
    archive_path: str,
    output: OutputHandler,
) -> Optional[str]:
    """Insert one row into exactly one well-formed canonical ledger."""
    lines = content.splitlines(keepends=True)
    heading_indices = [
        index
        for index, line in enumerate(lines)
        if line.rstrip("\r\n") == HISTORY_LEDGER_HEADING
    ]
    header_indices = [
        index
        for index, line in enumerate(lines)
        if line.rstrip("\r\n") == HISTORY_LEDGER_HEADER
    ]
    if len(heading_indices) != 1 or len(header_indices) != 1:
        output.error("decision_history.md has an ambiguous History Ledger table.")
        return None

    heading_index = heading_indices[0]
    header_index = header_indices[0]
    if header_index <= heading_index or header_index + 1 >= len(lines):
        output.error("Could not find insertion point in History Ledger table")
        return None
    if lines[header_index + 1].rstrip("\r\n") != HISTORY_LEDGER_SEPARATOR:
        output.error("decision_history.md has a malformed History Ledger separator.")
        return None

    insertion_index = header_index + 2
    archive_token = f"`{archive_path}`"
    while insertion_index < len(lines):
        stripped = lines[insertion_index].strip()
        if not stripped.startswith("|"):
            break
        if archive_token in lines[insertion_index]:
            return content
        insertion_index += 1

    newline = "\r\n" if "\r\n" in lines[header_index] else "\n"
    lines.insert(insertion_index, f"{new_row}{newline}")
    return "".join(lines)


def _run_consolidate_command(options: ConsolidateOptions) -> Tuple[int, str]:
    """Execute consolidate command."""
    try:
        root = find_project_root()
    except FileNotFoundError as exc:
        return 2, str(exc)
    output = OutputHandler(quiet=options.quiet)
    # Resolve paths relative to runtime project root
    from ontos.io.config import load_project_config
    if (root / '.ontos-internal').exists():
        # Contributor mode
        configured_retention_count = WorkflowConfig().log_retention_count
        logs_dir = root / ".ontos-internal" / "logs"
        archive_logs_dir = root / ".ontos-internal" / "archive" / "logs"
        decision_history_path = root / ".ontos-internal" / "reference" / "decision_history.md"
    else:
        # User mode
        try:
            config = load_project_config(repo_root=root)
        except ConfigError as exc:
            return 2, f"Config error: {exc}"
        except Exception as exc:
            return 5, f"Config error: {exc}"
        configured_retention_count = config.workflow.log_retention_count
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

    effective_count = (
        options.count
        if options.count is not None
        else configured_retention_count
    )
    if not options.by_age and effective_count < 1:
        return 2, "count must be >= 1"
    resolved_options = replace(options, count=effective_count)

    load_result = None
    if logs_dir.exists():
        load_result = load_documents(list(logs_dir.glob("*.md")), parse_frontmatter_content)
        if load_result.has_fatal_errors or load_result.duplicate_ids:
            for issue in load_result.issues:
                if issue.code in {"duplicate_id", "parse_error", "io_error"}:
                    output.error(issue.message)
            return 5, "Document load failed"
            
    logs_to_consolidate = find_logs_to_consolidate(
        resolved_options,
        logs_dir,
        load_result=load_result,
    )
    if not logs_to_consolidate:
        if not options.quiet:
            output.success("Nothing to consolidate.")
        return 0, "Nothing to consolidate"

    output.info(f"Found {len(logs_to_consolidate)} log(s) to consolidate:")
    
    ctx = SessionContext.from_repo(root)
    consolidated_count = 0
    succeeded: List[str] = []
    failed: List[Tuple[str, Path, str]] = []
    archive_dir = archive_logs_dir
    
    for path, doc_id, fm in logs_to_consolidate:
        date_str = path.name[:10]
        slug = path.name[11:-3] if len(path.name) > 14 else doc_id
        event_type = fm.get('event_type', 'chore')
        impacts = normalize_reference_list(fm.get('impacts', []), "impacts")
        summary = extract_summary(path)
        
        if not summary and not options.all and not options.quiet:
            output.warning(f"Could not auto-extract summary from {doc_id}")
            try:
                summary = input("   Enter one-line summary: ").strip()
            except EOFError:
                summary = "(Manual entry required)"
            except KeyboardInterrupt:
                return 130, "Interrupted"
        
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
            except EOFError:
                print("\n   Skipped.")
                continue
            except KeyboardInterrupt:
                return 130, "Interrupted"
            
            if confirm == 'edit':
                new_summary = input(f"   New summary: ").strip()
                if new_summary:
                    summary = new_summary
                confirm = 'y'
            
            if confirm != 'y':
                output.info("Skipped.")
                continue

        # Archive with per-log transactional boundary: history row and move are committed together.
        archive_dir.mkdir(parents=True, exist_ok=True)
        new_path = archive_dir / path.name
        rel_archive_path = new_path.relative_to(root)

        try:
            if not append_to_decision_history(
                date_str,
                slug,
                event_type,
                summary,
                impacts,
                str(rel_archive_path),
                decision_history_path,
                ctx,
                output,
            ):
                reason = "failed to update decision_history.md"
                failed.append((slug, path, reason))
                output.error(f"Failed to archive {path.name}: {reason}")
                ctx.rollback()
                continue

            ctx.buffer_move(path, new_path)
            ctx.commit()
            output.success("Archived and recorded in decision_history.md")
            consolidated_count += 1
            succeeded.append(slug)
        except Exception as e:
            reason = str(e)
            failed.append((slug, path, reason))
            output.error(f"Error archiving {path.name}: {e}")
            ctx.rollback()

    action = 'Would consolidate' if options.dry_run else 'Consolidated'
    output.info(f"{action} {consolidated_count} log(s).")

    if not options.dry_run and failed:
        output.warning("Consolidation completed with failures.")
        output.warning(f"Succeeded: {', '.join(succeeded) if succeeded else '(none)'}")
        for slug, failed_path, reason in failed:
            output.warning(f"Failed: {slug} [{failed_path}] ({reason})")
        output.warning(
            "Reconciliation: verify listed failed logs and decision history entries before re-running consolidate."
        )
        return 5, f"Consolidated {consolidated_count} logs with {len(failed)} failures"

    return 0, f"{action} {consolidated_count} logs"


def consolidate_command(options: ConsolidateOptions) -> int:
    """Execute consolidate command and return exit code."""
    exit_code, _ = _run_consolidate_command(options)
    return exit_code
