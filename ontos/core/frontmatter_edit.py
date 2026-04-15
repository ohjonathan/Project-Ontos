"""Shared frontmatter-surgery helpers for commands that patch YAML in place.

Extracted from ``ontos/commands/rename.py`` so both ``rename`` and
``retrofit`` can reuse the same byte-level decoding, frontmatter split,
top-level field indexing, and git-clean check without duplicating the
subtle line-indexing logic.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


_TOP_LEVEL_FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:(.*)$")


@dataclass(frozen=True)
class _DecodedContent:
    original: str
    leading_prefix: str
    normalized: str
    leading_line_offset: int


@dataclass(frozen=True)
class _FrontmatterSplit:
    has_frontmatter: bool
    frontmatter: str
    body: str
    body_abs_offset: int


@dataclass(frozen=True)
class _TopLevelField:
    key: str
    line_index: int
    line_text: str
    colon_index: int
    value_text: str
    end_line_index: int


def _read_decoded_content(path: Path) -> _DecodedContent:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    decoded = raw.decode("utf-8", errors="replace")
    prefix_len = len(decoded) - len(decoded.lstrip())
    leading_prefix = decoded[:prefix_len]
    normalized = decoded[prefix_len:]
    return _DecodedContent(
        original=decoded,
        leading_prefix=leading_prefix,
        normalized=normalized,
        leading_line_offset=leading_prefix.count("\n"),
    )


def _split_frontmatter(normalized: str) -> _FrontmatterSplit:
    if not normalized.startswith("---"):
        return _FrontmatterSplit(
            has_frontmatter=False,
            frontmatter="",
            body=normalized,
            body_abs_offset=0,
        )
    parts = normalized.split("---", 2)
    if len(parts) < 3:
        return _FrontmatterSplit(
            has_frontmatter=False,
            frontmatter="",
            body=normalized,
            body_abs_offset=0,
        )
    frontmatter = parts[1]
    body = parts[2]
    body_abs_offset = len(f"---{frontmatter}---")
    return _FrontmatterSplit(
        has_frontmatter=True,
        frontmatter=frontmatter,
        body=body,
        body_abs_offset=body_abs_offset,
    )


def _index_top_level_fields(lines: Sequence[str]) -> List[_TopLevelField]:
    top_level_entries: List[Tuple[str, int, str, int, str]] = []
    for index, line in enumerate(lines):
        no_newline = line.rstrip("\r\n")
        if not no_newline:
            continue
        if no_newline.startswith((" ", "\t")):
            continue
        stripped = no_newline.strip()
        if stripped.startswith("#"):
            continue
        match = _TOP_LEVEL_FIELD_RE.match(no_newline)
        if match is None:
            continue
        key = match.group(1)
        colon_index = no_newline.find(":")
        value_text = no_newline[colon_index + 1:]
        top_level_entries.append((key, index, line, colon_index, value_text))

    results: List[_TopLevelField] = []
    for pos, entry in enumerate(top_level_entries):
        next_line_index = top_level_entries[pos + 1][1] if pos + 1 < len(top_level_entries) else len(lines)
        results.append(
            _TopLevelField(
                key=entry[0],
                line_index=entry[1],
                line_text=entry[2],
                colon_index=entry[3],
                value_text=entry[4],
                end_line_index=next_line_index,
            )
        )
    return results


def _check_clean_git_state(repo_root: Path) -> Tuple[bool, Optional[str]]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"Unable to check git state: {exc}"

    if result.returncode != 0:
        return False, "Git working tree must be clean for --apply."
    if result.stdout.strip():
        return False, "Git working tree must be clean for --apply."
    return True, None
