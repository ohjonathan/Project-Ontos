"""Decision history generation.

This module contains functions for generating and parsing
session logs for the immutable decision history feature (v2.7).
"""

import os
import re
from datetime import date, datetime
from typing import Optional, List, Tuple

from ontos.core.frontmatter import parse_frontmatter, normalize_depends_on


class ParsedLog:
    """Represents a parsed session log for history generation."""
    
    def __init__(self, log_id: str, log_path: str, log_date: date,
                 event_type: str, summary: str, impacts: List[str], concepts: List[str]):
        self.id = log_id
        self.path = log_path
        self.date = log_date
        self.event_type = event_type
        self.summary = summary
        self.impacts = impacts
        self.concepts = concepts


def get_log_date(log_path: str, frontmatter: Optional[dict] = None) -> Optional[date]:
    """Extract date from a log file.
    
    Resolution order:
    1. Frontmatter 'date' field
    2. Filename prefix (YYYY-MM-DD_slug.md)
    3. File modification time (least reliable)
    
    Args:
        log_path: Path to the log file.
        frontmatter: Pre-parsed frontmatter (optional, will parse if not provided).
        
    Returns:
        date object, or None if cannot be determined.
    """
    # 1. Try frontmatter date field
    if frontmatter is None:
        frontmatter = parse_frontmatter(log_path) or {}
    
    if 'date' in frontmatter:
        try:
            date_val = frontmatter['date']
            if isinstance(date_val, date) and not isinstance(date_val, datetime):
                return date_val
            if isinstance(date_val, datetime):
                return date_val.date()
            if isinstance(date_val, str):
                return date.fromisoformat(date_val.strip())
        except ValueError:
            pass
    
    # 2. Try filename prefix (YYYY-MM-DD_slug.md)
    filename = os.path.basename(log_path)
    match = re.match(r'^(\d{4}-\d{2}-\d{2})_', filename)
    if match:
        try:
            return date.fromisoformat(match.group(1))
        except ValueError:
            pass
    
    # 3. Last resort: file mtime (least reliable)
    try:
        mtime = os.path.getmtime(log_path)
        return date.fromtimestamp(mtime)
    except OSError:
        return None


def parse_log_for_history(log_path: str) -> Optional[ParsedLog]:
    """Parse a session log for history generation.
    
    Args:
        log_path: Path to the log file.
        
    Returns:
        ParsedLog object, or None if parsing failed.
    """
    try:
        frontmatter = parse_frontmatter(log_path)
        if not frontmatter:
            return None
        
        log_id = frontmatter.get('id', os.path.basename(log_path).replace('.md', ''))
        log_date = get_log_date(log_path, frontmatter)
        if not log_date:
            return None
        
        # Get event type (default to 'chore' if missing)
        event_type = frontmatter.get('event_type', frontmatter.get('event', 'chore'))
        if isinstance(event_type, list):
            event_type = event_type[0] if event_type else 'chore'
        
        # Get impacts and concepts
        impacts = normalize_depends_on(frontmatter.get('impacts', []))
        concepts = normalize_depends_on(frontmatter.get('concepts', []))
        
        # Get summary from content (first non-header paragraph after frontmatter)
        summary = ""
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Extract content after frontmatter
            parts = content.split('---', 2)
            if len(parts) >= 3:
                body = parts[2].strip()
                # Find first paragraph that's not a header
                for line in body.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        summary = line[:200] + ('...' if len(line) > 200 else '')
                        break
        except (IOError, OSError):
            pass
        
        return ParsedLog(
            log_id=log_id,
            log_path=log_path,
            log_date=log_date,
            event_type=event_type,
            summary=summary,
            impacts=impacts,
            concepts=concepts
        )
    except Exception:
        return None


def sort_logs_deterministically(logs: List[ParsedLog]) -> List[ParsedLog]:
    """Sort logs deterministically for history generation.
    
    Sort order:
    1. Date descending (newest first)
    2. Event type alphabetically
    3. Log ID alphabetically
    
    Args:
        logs: List of ParsedLog objects.
        
    Returns:
        Sorted list of logs.
    """
    return sorted(logs, key=lambda l: (
        -l.date.toordinal(),  # Descending date
        l.event_type,          # Alphabetical type
        l.id                   # Alphabetical ID
    ))


def generate_decision_history(
    logs_dirs: List[str],
    output_path: str = None
) -> Tuple[str, List[str]]:
    """Generate decision_history.md from logs.
    
    v2.7: Makes history a generated artifact rather than manually maintained.
    
    Args:
        logs_dirs: List of directories containing log files.
        output_path: Path to write the generated file (optional).
        
    Returns:
        (markdown_content, list_of_warnings)
    """
    parsed = []
    warnings = []
    active_count = 0
    archived_count = 0
    
    for logs_dir in logs_dirs:
        if not os.path.exists(logs_dir):
            continue
        
        is_archive = 'archive' in logs_dir.lower()
        
        for log_file in os.listdir(logs_dir):
            if not log_file.endswith('.md'):
                continue
            # Only process date-prefixed files (session logs)
            if not log_file[0].isdigit():
                continue
            
            log_path = os.path.join(logs_dir, log_file)
            try:
                log = parse_log_for_history(log_path)
                if log:
                    parsed.append(log)
                    if is_archive:
                        archived_count += 1
                    else:
                        active_count += 1
                else:
                    warnings.append(f"Skipping malformed log: {log_file}")
            except Exception as e:
                warnings.append(f"Skipping malformed log: {log_file} ({e})")
    
    # Sort deterministically
    sorted_logs = sort_logs_deterministically(parsed)
    
    # Generate markdown
    now = datetime.now().isoformat(timespec='seconds')
    skipped = len(warnings)
    
    header = f"""<!--
GENERATED FILE - DO NOT EDIT MANUALLY
Regenerated by: ontos_generate_context_map.py
Source: {', '.join(logs_dirs)}
Last generated: {now}
Log count: {active_count} active, {archived_count} archived, {skipped} skipped
-->

---
id: decision_history
type: strategy
status: active
depends_on: [mission]
---

# Decision History

This file is auto-generated from session logs. Do not edit directly.

To regenerate: `python3 .ontos/scripts/ontos_generate_context_map.py`

"""
    
    # Group by date
    content_parts = [header]
    current_date = None
    
    for log in sorted_logs:
        if log.date != current_date:
            current_date = log.date
            content_parts.append(f"## {current_date.isoformat()}\n\n")
        
        # Format entry
        entry = f"### [{log.event_type}] {log.id.replace('_', ' ').replace('log ', '').title()}\n"
        entry += f"- **Log:** `{log.id}`\n"
        if log.impacts:
            entry += f"- **Impacts:** {', '.join(log.impacts)}\n"
        if log.concepts:
            entry += f"- **Concepts:** {', '.join(log.concepts)}\n"
        if log.summary:
            entry += f"\n> {log.summary}\n"
        entry += "\n"
        content_parts.append(entry)
    
    markdown_content = ''.join(content_parts)
    
    # Write to file if output_path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    return markdown_content, warnings
