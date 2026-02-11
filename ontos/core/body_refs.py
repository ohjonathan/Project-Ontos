"""Zone-aware body reference scanning shared by link-check and rename."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


class ZoneType(str, Enum):
    """Body text zones."""

    NORMAL_TEXT = "normal_text"
    INLINE_CODE = "inline_code"
    CODE_FENCE = "code_fence"


class MatchType(str, Enum):
    """Supported body reference match channels."""

    MARKDOWN_LINK_TARGET = "markdown_link_target"
    BARE_ID_TOKEN = "bare_id_token"


@dataclass(frozen=True)
class BodyReferenceMatch:
    """One reference match found in body text."""

    path: Path
    line: int
    col_start: int
    col_end: int
    zone: ZoneType
    match_type: MatchType
    raw_match: str
    normalized_id: str
    line_text: str
    context_before: str
    context_after: str
    rewritable: bool
    skip_reason: Optional[str] = None
    abs_start: int = 0
    abs_end: int = 0


@dataclass(frozen=True)
class BodyReferenceScan:
    """Aggregate body reference scan output."""

    matches: List[BodyReferenceMatch]
    scanned_lines: int


_TOKEN_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9_])?")
_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_WINDOWS_ABS_RE = re.compile(r"^[A-Za-z]:[\\/]")
_REFERENCE_DEF_RE = re.compile(r"^\s*\[[^\]]+\]:")
_REFERENCE_STYLE_RE = re.compile(r"\[[^\]]+\]\[[^\]]+\]")
_WIKILINK_RE = re.compile(r"\[\[[^\]]+\]\]")
_HTML_OR_AUTOLINK_RE = re.compile(r"<[^>]+>")
_HARD_BOUNDARY = {" ", "\t", "\n", "[", "]", "(", ")", "`", ","}
_TRAILING_PUNCT_BOUNDARY = {".", ":", ";", "!", "?", "|", "\"", "'", ">"}


@dataclass(frozen=True)
class _MarkdownTarget:
    normalized_id: str
    raw_target: str
    full_start: int
    full_end: int
    target_start: int
    target_end: int


def is_leading_boundary(ch: Optional[str]) -> bool:
    """Return true when a character is a valid leading token boundary."""

    return ch is None or ch in _HARD_BOUNDARY


def is_trailing_boundary(curr: Optional[str], next_ch: Optional[str]) -> bool:
    """Return true when chars form a valid trailing token boundary."""

    if curr is None:
        return True
    if curr in _HARD_BOUNDARY:
        return True
    if curr in _TRAILING_PUNCT_BOUNDARY:
        return next_ch is None or next_ch.isspace() or next_ch in _HARD_BOUNDARY
    return False


def scan_body_references(
    path: Path,
    body: str,
    *,
    context_lines: int = 1,
    rename_target: Optional[str] = None,
    known_ids: Optional[set[str]] = None,
    include_skipped: bool = True,
) -> BodyReferenceScan:
    """Scan markdown body for reference matches.

    Modes:
    - rename mode: `rename_target` is provided and only exact target matches are emitted.
    - link-check mode: `rename_target` is omitted and all candidate references are emitted.
      If `known_ids` is set, candidates are limited to that known set.
    """

    lines = body.splitlines(keepends=True)
    if not lines:
        lines = [""]

    line_texts = [_strip_line_ending(line) for line in lines]
    line_offsets: List[int] = []
    cursor = 0
    for line in lines:
        line_offsets.append(cursor)
        cursor += len(line)

    matches: List[BodyReferenceMatch] = []
    in_fence = False
    fence_marker = ""
    fence_len = 0

    for index, line_text in enumerate(line_texts):
        line_no = index + 1
        line_abs_start = line_offsets[index]
        context_before, context_after = _build_context(line_texts, index, context_lines)
        line_is_reference_definition = _is_reference_definition_line(line_text)

        fence = _detect_fence_opener(line_text)
        if in_fence:
            if rename_target and include_skipped:
                matches.extend(
                    _scan_skipped_zone_for_target(
                        path=path,
                        segment_text=line_text,
                        segment_abs_start=line_abs_start,
                        line_no=line_no,
                        line_text=line_text,
                        context_before=context_before,
                        context_after=context_after,
                        zone=ZoneType.CODE_FENCE,
                        rename_target=rename_target,
                    )
                )
            if _is_fence_closer(line_text, fence_marker, fence_len):
                in_fence = False
                fence_marker = ""
                fence_len = 0
            continue

        if fence is not None:
            marker, marker_len = fence
            in_fence = True
            fence_marker = marker
            fence_len = marker_len

            if rename_target and include_skipped:
                matches.extend(
                    _scan_skipped_zone_for_target(
                        path=path,
                        segment_text=line_text,
                        segment_abs_start=line_abs_start,
                        line_no=line_no,
                        line_text=line_text,
                        context_before=context_before,
                        context_after=context_after,
                        zone=ZoneType.CODE_FENCE,
                        rename_target=rename_target,
                    )
                )
            continue

        for zone, seg_start, seg_end in _split_inline_code_segments(line_text):
            segment_text = line_text[seg_start:seg_end]
            segment_abs_start = line_abs_start + seg_start
            if zone == ZoneType.INLINE_CODE:
                if rename_target and include_skipped:
                    matches.extend(
                        _scan_skipped_zone_for_target(
                            path=path,
                            segment_text=segment_text,
                            segment_abs_start=segment_abs_start,
                            line_no=line_no,
                            line_text=line_text,
                            context_before=context_before,
                            context_after=context_after,
                            zone=ZoneType.INLINE_CODE,
                            rename_target=rename_target,
                        )
                    )
                continue

            matches.extend(
                _scan_normal_text_segment(
                    path=path,
                    segment_text=segment_text,
                    segment_abs_start=segment_abs_start,
                    line_no=line_no,
                    line_text=line_text,
                    context_before=context_before,
                    context_after=context_after,
                    rename_target=rename_target,
                    known_ids=known_ids,
                    line_is_reference_definition=line_is_reference_definition,
                )
            )

    return BodyReferenceScan(
        matches=sorted(matches, key=lambda match: (match.abs_start, match.abs_end)),
        scanned_lines=len(line_texts),
    )


def _strip_line_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1]
    return line


def _build_context(line_texts: Sequence[str], line_index: int, context_lines: int) -> Tuple[str, str]:
    before_start = max(0, line_index - context_lines)
    before = "\n".join(line_texts[before_start:line_index])

    after_end = min(len(line_texts), line_index + 1 + context_lines)
    after = "\n".join(line_texts[line_index + 1:after_end])
    return before, after


def _detect_fence_opener(line_text: str) -> Optional[Tuple[str, int]]:
    stripped = line_text.lstrip()
    if len(stripped) < 3:
        return None
    marker = stripped[0]
    if marker not in {"`", "~"}:
        return None
    run_len = _count_run(stripped, 0, marker)
    if run_len < 3:
        return None
    return marker, run_len


def _is_fence_closer(line_text: str, marker: str, min_len: int) -> bool:
    stripped = line_text.lstrip()
    if not stripped.startswith(marker):
        return False
    run_len = _count_run(stripped, 0, marker)
    return run_len >= min_len


def _split_inline_code_segments(line_text: str) -> List[Tuple[ZoneType, int, int]]:
    if not line_text:
        return [(ZoneType.NORMAL_TEXT, 0, 0)]

    segments: List[Tuple[ZoneType, int, int]] = []
    cursor = 0
    while cursor < len(line_text):
        opener = _find_next_unescaped_backtick_run(line_text, cursor)
        if opener is None:
            segments.append((ZoneType.NORMAL_TEXT, cursor, len(line_text)))
            break

        opener_start, run_len = opener
        closer_start = _find_matching_backtick_run(line_text, opener_start + run_len, run_len)
        if closer_start is None:
            segments.append((ZoneType.NORMAL_TEXT, cursor, len(line_text)))
            break

        if opener_start > cursor:
            segments.append((ZoneType.NORMAL_TEXT, cursor, opener_start))
        segments.append((ZoneType.INLINE_CODE, opener_start, closer_start + run_len))
        cursor = closer_start + run_len

    if not segments:
        segments.append((ZoneType.NORMAL_TEXT, 0, len(line_text)))

    return segments


def _find_next_unescaped_backtick_run(text: str, start: int) -> Optional[Tuple[int, int]]:
    idx = start
    while idx < len(text):
        if text[idx] == "`" and not _is_escaped(text, idx):
            return idx, _count_run(text, idx, "`")
        idx += 1
    return None


def _find_matching_backtick_run(text: str, start: int, run_len: int) -> Optional[int]:
    idx = start
    while idx < len(text):
        if text[idx] == "`" and not _is_escaped(text, idx):
            candidate_len = _count_run(text, idx, "`")
            if candidate_len == run_len:
                return idx
            idx += candidate_len
            continue
        idx += 1
    return None


def _is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def _scan_skipped_zone_for_target(
    *,
    path: Path,
    segment_text: str,
    segment_abs_start: int,
    line_no: int,
    line_text: str,
    context_before: str,
    context_after: str,
    zone: ZoneType,
    rename_target: str,
) -> List[BodyReferenceMatch]:
    matches: List[BodyReferenceMatch] = []
    for start, end in _iter_exact_id_matches(segment_text, rename_target):
        matches.append(
            BodyReferenceMatch(
                path=path,
                line=line_no,
                col_start=start + 1,
                col_end=end,
                zone=zone,
                match_type=MatchType.BARE_ID_TOKEN,
                raw_match=segment_text[start:end],
                normalized_id=rename_target,
                line_text=line_text,
                context_before=context_before,
                context_after=context_after,
                rewritable=False,
                skip_reason=f"zone is {zone.value}",
                abs_start=segment_abs_start + start,
                abs_end=segment_abs_start + end,
            )
        )
    return matches


def _scan_normal_text_segment(
    *,
    path: Path,
    segment_text: str,
    segment_abs_start: int,
    line_no: int,
    line_text: str,
    context_before: str,
    context_after: str,
    rename_target: Optional[str],
    known_ids: Optional[set[str]],
    line_is_reference_definition: bool,
) -> List[BodyReferenceMatch]:
    if line_is_reference_definition:
        return []

    matches: List[BodyReferenceMatch] = []
    link_targets = _find_markdown_link_targets(segment_text)
    occupied = [(item.full_start, item.full_end) for item in link_targets]
    occupied.extend(_find_unsupported_spans(segment_text))

    for link_target in link_targets:
        if rename_target is not None and link_target.normalized_id != rename_target:
            continue
        if rename_target is None and known_ids is not None and link_target.normalized_id not in known_ids:
            continue
        matches.append(
            BodyReferenceMatch(
                path=path,
                line=line_no,
                col_start=link_target.target_start + 1,
                col_end=link_target.target_end,
                zone=ZoneType.NORMAL_TEXT,
                match_type=MatchType.MARKDOWN_LINK_TARGET,
                raw_match=link_target.raw_target,
                normalized_id=link_target.normalized_id,
                line_text=line_text,
                context_before=context_before,
                context_after=context_after,
                rewritable=True,
                abs_start=segment_abs_start + link_target.target_start,
                abs_end=segment_abs_start + link_target.target_end,
            )
        )

    bare_candidates: Iterable[Tuple[int, int, str]]
    if rename_target is not None:
        bare_candidates = (
            (start, end, rename_target) for start, end in _iter_exact_id_matches(segment_text, rename_target)
        )
    elif known_ids is not None:
        ordered_ids = sorted(known_ids, key=lambda item: (-len(item), item))
        bare_candidates = _iter_known_id_candidates(segment_text, ordered_ids)
    else:
        bare_candidates = _iter_generic_id_candidates(segment_text)

    for start, end, normalized_id in bare_candidates:
        if _overlaps_any(start, end, occupied):
            continue
        matches.append(
            BodyReferenceMatch(
                path=path,
                line=line_no,
                col_start=start + 1,
                col_end=end,
                zone=ZoneType.NORMAL_TEXT,
                match_type=MatchType.BARE_ID_TOKEN,
                raw_match=segment_text[start:end],
                normalized_id=normalized_id,
                line_text=line_text,
                context_before=context_before,
                context_after=context_after,
                rewritable=True,
                abs_start=segment_abs_start + start,
                abs_end=segment_abs_start + end,
            )
        )

    return matches


def _find_markdown_link_targets(segment_text: str) -> List[_MarkdownTarget]:
    matches: List[_MarkdownTarget] = []
    cursor = 0
    while cursor < len(segment_text):
        if segment_text[cursor] != "[" or _is_escaped(segment_text, cursor):
            cursor += 1
            continue

        label_end = _find_matching_bracket(segment_text, cursor)
        if label_end is None:
            cursor += 1
            continue
        if label_end + 1 >= len(segment_text) or segment_text[label_end + 1] != "(":
            cursor = label_end + 1
            continue

        parsed = _parse_link_payload(segment_text, label_end + 2)
        if parsed is None:
            cursor = label_end + 1
            continue

        raw_target, normalized_id, rel_target_start, rel_target_end, payload_end = parsed
        matches.append(
            _MarkdownTarget(
                normalized_id=normalized_id,
                raw_target=raw_target,
                full_start=cursor,
                full_end=payload_end + 1,
                target_start=rel_target_start,
                target_end=rel_target_end,
            )
        )
        cursor = payload_end + 1

    return matches


def _find_matching_bracket(text: str, start: int) -> Optional[int]:
    depth = 1
    cursor = start + 1
    while cursor < len(text):
        char = text[cursor]
        if char == "\\":
            cursor += 2
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return cursor
        cursor += 1
    return None


def _parse_link_payload(
    text: str,
    payload_start: int,
) -> Optional[Tuple[str, str, int, int, int]]:
    depth = 1
    cursor = payload_start
    while cursor < len(text):
        char = text[cursor]
        if char == "\\":
            cursor += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                payload_end = cursor
                break
        cursor += 1
    else:
        return None

    payload = text[payload_start:payload_end]
    target = _extract_target_from_payload(payload)
    if target is None:
        return None
    target_raw, target_rel_start, target_rel_end = target
    normalized = _normalize_markdown_target(target_raw)
    if normalized is None:
        return None

    return (
        target_raw,
        normalized,
        payload_start + target_rel_start,
        payload_start + target_rel_end,
        payload_end,
    )


def _extract_target_from_payload(payload: str) -> Optional[Tuple[str, int, int]]:
    cursor = 0
    while cursor < len(payload) and payload[cursor].isspace():
        cursor += 1
    if cursor >= len(payload):
        return None

    if payload[cursor] == "<":
        target_start = cursor
        cursor += 1
        while cursor < len(payload):
            if payload[cursor] == ">" and not _is_escaped(payload, cursor):
                target_end = cursor + 1
                break
            cursor += 1
        else:
            return None
    else:
        target_start = cursor
        nested = 0
        while cursor < len(payload):
            char = payload[cursor]
            if char == "\\":
                cursor += 2
                continue
            if char == "(":
                nested += 1
            elif char == ")" and nested > 0:
                nested -= 1
            elif char.isspace() and nested == 0:
                break
            cursor += 1
        target_end = cursor

    raw_target = payload[target_start:target_end].strip()
    if not raw_target:
        return None

    remainder = payload[target_end:]
    if remainder.strip() and not _is_supported_optional_title(remainder):
        return None

    return raw_target, target_start, target_end


def _is_supported_optional_title(remainder: str) -> bool:
    stripped = remainder.strip()
    if not stripped:
        return True
    if stripped[0] not in {"\"", "'"}:
        return False
    quote = stripped[0]
    cursor = 1
    while cursor < len(stripped):
        if stripped[cursor] == "\\":
            cursor += 2
            continue
        if stripped[cursor] == quote:
            tail = stripped[cursor + 1:].strip()
            return tail == ""
        cursor += 1
    return False


def _normalize_markdown_target(raw_target: str) -> Optional[str]:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">") and len(target) >= 2:
        target = target[1:-1].strip()
    if not target:
        return None
    if target.startswith("#"):
        return None
    if _SCHEME_RE.match(target):
        return None
    if target.startswith("/") or _WINDOWS_ABS_RE.match(target):
        return None

    target = target.split("#", 1)[0].strip()
    if not target:
        return None
    if "/" in target or "\\" in target:
        target = target.replace("\\", "/").rsplit("/", 1)[-1]
    if target.lower().endswith(".md"):
        target = target[:-3]
    target = target.strip()
    return target or None


def _iter_exact_id_matches(text: str, target: str) -> Iterable[Tuple[int, int]]:
    escaped = re.escape(target)
    for found in re.finditer(escaped, text):
        start, end = found.span()
        prev_ch = text[start - 1] if start > 0 else None
        curr_ch = text[end] if end < len(text) else None
        next_ch = text[end + 1] if end + 1 < len(text) else None
        if is_leading_boundary(prev_ch) and is_trailing_boundary(curr_ch, next_ch):
            yield start, end


def _iter_known_id_candidates(text: str, ids: Sequence[str]) -> Iterable[Tuple[int, int, str]]:
    for doc_id in ids:
        for start, end in _iter_exact_id_matches(text, doc_id):
            yield start, end, doc_id


def _iter_generic_id_candidates(text: str) -> Iterable[Tuple[int, int, str]]:
    for found in _TOKEN_RE.finditer(text):
        start, end = found.span()
        token = found.group(0)
        if not _looks_like_doc_id(token):
            continue
        prev_ch = text[start - 1] if start > 0 else None
        curr_ch = text[end] if end < len(text) else None
        next_ch = text[end + 1] if end + 1 < len(text) else None
        if is_leading_boundary(prev_ch) and is_trailing_boundary(curr_ch, next_ch):
            yield start, end, token


def _looks_like_doc_id(token: str) -> bool:
    if "_" in token or "." in token:
        return True
    return any(ch.isdigit() for ch in token)


def _overlaps_any(start: int, end: int, ranges: Sequence[Tuple[int, int]]) -> bool:
    for range_start, range_end in ranges:
        if start < range_end and end > range_start:
            return True
    return False


def _count_run(text: str, index: int, char: str) -> int:
    cursor = index
    while cursor < len(text) and text[cursor] == char:
        cursor += 1
    return cursor - index


def _is_reference_definition_line(line_text: str) -> bool:
    return _REFERENCE_DEF_RE.match(line_text) is not None


def _find_unsupported_spans(segment_text: str) -> List[Tuple[int, int]]:
    spans: List[Tuple[int, int]] = []
    for pattern in (_REFERENCE_STYLE_RE, _WIKILINK_RE, _HTML_OR_AUTOLINK_RE):
        for match in pattern.finditer(segment_text):
            spans.append(match.span())
    return spans
