"""Grouping and budgeting for validation warning records (#132).

Operates on the *serialized* warning record dicts
(``{severity, message, rule_id, document_id, file_path}``) rather than
``ValidationError`` objects: the MCP activation path mixes in snapshot-level
records that have no ``ValidationError`` backing, and working on dicts
guarantees both surfaces (CLI ``activate --json`` and the MCP ``activate``
tool) group bit-identical inputs the same way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

DEFAULT_SAMPLE_SIZE = 3

UNKNOWN_RULE_ID = "unknown"


@dataclass(frozen=True)
class WarningGroup:
    """One rule_id bucket with counts and a bounded record sample."""

    rule_id: str
    count: int
    by_severity: Dict[str, int] = field(default_factory=dict)
    samples: List[Dict[str, Any]] = field(default_factory=list)


def group_warning_records(
    records: Sequence[Mapping[str, Any]],
    *,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    rule_id: Optional[str] = None,
) -> List[WarningGroup]:
    """Bucket warning records by rule_id with bounded per-group samples.

    Samples are the unmodified input records in input order. Groups are
    sorted by descending count, then rule_id, for deterministic output.
    """
    buckets: Dict[str, List[Mapping[str, Any]]] = {}
    for record in records:
        key = record.get("rule_id") or UNKNOWN_RULE_ID
        if rule_id is not None and key != rule_id:
            continue
        buckets.setdefault(key, []).append(record)

    groups: List[WarningGroup] = []
    for key, bucket in buckets.items():
        by_severity: Dict[str, int] = {}
        for record in bucket:
            severity = record.get("severity") or "warning"
            by_severity[severity] = by_severity.get(severity, 0) + 1
        groups.append(
            WarningGroup(
                rule_id=key,
                count=len(bucket),
                by_severity=by_severity,
                samples=[dict(record) for record in bucket[:sample_size]],
            )
        )
    groups.sort(key=lambda group: (-group.count, group.rule_id))
    return groups


def groups_to_payload(
    groups: Sequence[WarningGroup],
    *,
    include_samples: bool = True,
) -> List[Dict[str, Any]]:
    """Serialize groups for JSON payloads."""
    return [
        {
            "rule_id": group.rule_id,
            "count": group.count,
            "by_severity": dict(group.by_severity),
            "samples": [dict(sample) for sample in group.samples] if include_samples else [],
        }
        for group in groups
    ]


def select_warning_records(
    records: Sequence[Mapping[str, Any]],
    *,
    rule_id: Optional[str] = None,
    severity: Optional[str] = None,
    offset: int = 0,
    limit: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], int, bool]:
    """Filter + paginate full warning records.

    Returns ``(page, total_after_filter, truncated)`` where ``truncated``
    is True when the page does not cover every filtered record.
    """
    filtered = [
        dict(record)
        for record in records
        if (rule_id is None or (record.get("rule_id") or UNKNOWN_RULE_ID) == rule_id)
        and (severity is None or (record.get("severity") or "warning") == severity)
    ]
    total = len(filtered)
    if limit is None:
        page = filtered[offset:]
    else:
        page = filtered[offset:offset + limit]
    truncated = offset > 0 or len(page) < total
    return page, total, truncated


def format_group_lines(
    groups: Sequence[Any],
    *,
    limit: int = 5,
) -> List[str]:
    """Render human-readable group lines (mirrors enum_issue_summary style).

    Accepts WarningGroup objects or the dicts produced by
    ``groups_to_payload`` so callers can format straight from a payload.
    """
    lines: List[str] = []
    for group in list(groups)[:limit]:
        if isinstance(group, WarningGroup):
            rule, count, by_severity, samples = (
                group.rule_id, group.count, group.by_severity, group.samples
            )
        else:
            rule = group.get("rule_id", UNKNOWN_RULE_ID)
            count = group.get("count", 0)
            by_severity = group.get("by_severity", {})
            samples = group.get("samples", [])
        severity_text = ", ".join(
            f"{name}={num}" for name, num in sorted(by_severity.items())
        )
        line = f"{rule} x{count}" + (f" ({severity_text})" if severity_text else "")
        if samples:
            anchor = samples[0].get("document_id") or samples[0].get("file_path")
            if anchor:
                line += f" — e.g. {anchor}"
        lines.append(line)
    remaining = len(groups) - limit
    if remaining > 0:
        lines.append(f"... and {remaining} more group(s)")
    return lines
