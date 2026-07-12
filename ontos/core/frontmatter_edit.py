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
from typing import Any, List, Mapping, Optional, Sequence, Tuple

from ontos.core.errors import OntosUserError
from ontos.io.yaml import (
    assert_frontmatter_roundtrip,
    parse_frontmatter_content,
    split_frontmatter_text,
)


_PLAIN_FIELD_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
_TOP_LEVEL_FIELD_RE = re.compile(
    r"^(?:(?P<plain>[A-Za-z_][A-Za-z0-9_-]*)|"
    r"(?P<single>'(?:[^']|'')*')|"
    r'(?P<double>"(?:[^"\\]|\\.)*"))'
    r"\s*:(?P<value>.*)$"
)


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


def patch_frontmatter_fields(content: str, updates: Mapping[str, Any]) -> str:
    """Surgically update top-level YAML fields without reformatting a document.

    Untouched YAML, comments, BOM, leading whitespace, body bytes, and line
    endings remain unchanged.  Ambiguous constructs in a field being changed
    Inline comments on one-line changed fields are preserved. Duplicates,
    comments inside rewritten collection items, anchors, tags, and block
    scalars are rejected rather than silently discarded.
    """
    if not isinstance(content, str):
        raise TypeError("Document content must be text")
    if not updates:
        return content
    for key in updates:
        if not isinstance(key, str) or _PLAIN_FIELD_NAME_RE.fullmatch(key) is None:
            raise ValueError(f"Invalid frontmatter field name: {key!r}")

    bom = "\ufeff" if content.startswith("\ufeff") else ""
    without_bom = content[len(bom) :]
    prefix_len = len(without_bom) - len(without_bom.lstrip())
    prefix = bom + without_bom[:prefix_len]
    normalized = without_bom[prefix_len:]
    split = _split_frontmatter(normalized)
    if not split.has_frontmatter:
        raise ValueError("Document has no valid line-delimited frontmatter")

    parsed, _ = parse_frontmatter_content(
        f"---{split.frontmatter}---{split.body}"
    )
    if not isinstance(parsed, dict):
        raise ValueError("Frontmatter must be a mapping")
    expected_frontmatter = dict(parsed)
    expected_frontmatter.update(updates)

    lines = split.frontmatter.splitlines(keepends=True)
    line_ending = _dominant_line_ending(split.frontmatter, normalized)

    for key, value in updates.items():
        occurrences = [field for field in _index_top_level_fields(lines) if field.key == key]
        if len(occurrences) > 1:
            raise ValueError(f"Field {key!r} appears more than once at top level")

        replacement = _serialize_field_lines(key, value, line_ending)
        if occurrences:
            occurrence = occurrences[0]
            existing_block = lines[occurrence.line_index : occurrence.end_line_index]
            inline_comment = _preserved_inline_comment(
                key,
                existing_block,
                occurrence,
            )
            _reject_ambiguous_field_block(key, existing_block, occurrence.value_text)
            if inline_comment:
                if len(replacement) != 1:
                    raise ValueError(
                        f"Cannot safely preserve an inline comment while expanding {key!r}"
                    )
                replacement[0] = _append_before_line_ending(
                    replacement[0], inline_comment
                )
            lines[occurrence.line_index : occurrence.end_line_index] = replacement
        else:
            if lines and not lines[-1].endswith(("\n", "\r")):
                lines[-1] += line_ending
            lines.extend(replacement)

    new_frontmatter = "".join(lines)
    reparsed, _ = parse_frontmatter_content(
        f"---{new_frontmatter}---{split.body}"
    )
    from ontos.core.schema import validate_document_id

    # ID-less documents are a supported loader input: their canonical ID is
    # derived from the filename, which this content-only helper cannot see.
    # Validate an ID whenever the document declares (or this patch adds) one,
    # while preserving the absence of an explicit ID for filename-derived
    # documents.
    if "id" in reparsed:
        validate_document_id(reparsed["id"])
    for key, expected_value in updates.items():
        if reparsed.get(key) != expected_value:
            raise ValueError(
                f"Frontmatter update failed semantic verification for {key!r}"
            )
    if reparsed != expected_frontmatter:
        raise ValueError("Frontmatter update changed unrelated fields")
    assert_frontmatter_roundtrip(expected_frontmatter, new_frontmatter)
    return prefix + f"---{new_frontmatter}---{split.body}"


def _serialize_field_lines(key: str, value: Any, line_ending: str) -> List[str]:
    from ontos.core.schema import serialize_frontmatter

    serialized = serialize_frontmatter({key: value})
    normalized = serialized.replace("\r\n", "\n").replace("\r", "\n")
    return [line + line_ending for line in normalized.split("\n")]


def _dominant_line_ending(frontmatter: str, document: str) -> str:
    crlf = frontmatter.count("\r\n")
    lf = frontmatter.count("\n") - crlf
    if crlf > lf:
        return "\r\n"
    if lf:
        return "\n"
    first_line = document.splitlines(keepends=True)[0] if document else ""
    return "\r\n" if first_line.endswith("\r\n") else "\n"


def _reject_ambiguous_field_block(
    key: str,
    block_lines: Sequence[str],
    value_text: str,
) -> None:
    block = "".join(block_lines)
    token = value_text.strip()
    if token.startswith(("|", ">", "!")):
        raise ValueError(f"Unsupported YAML style while updating {key!r}")
    if "&" in block or "*" in block:
        raise ValueError(f"Unsupported YAML anchor or alias while updating {key!r}")


def _preserved_inline_comment(
    key: str,
    block_lines: Sequence[str],
    occurrence: _TopLevelField,
) -> str:
    first = occurrence.line_text.rstrip("\r\n")
    after_colon = first[occurrence.colon_index + 1 :]
    value_part, comment_part = _split_comment_unquoted(after_colon)
    remaining = "".join(block_lines[1:])
    if "#" in remaining:
        raise ValueError(f"Refusing to discard a collection comment while updating {key!r}")
    if not comment_part:
        return ""
    padding = value_part[len(value_part.rstrip()) :]
    return (padding or " ") + comment_part


def _split_comment_unquoted(text: str) -> Tuple[str, str]:
    quote: Optional[str] = None
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if quote is not None:
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            continue
        if char == "#":
            return text[:index], text[index:]
    return text, ""


def _append_before_line_ending(line: str, suffix: str) -> str:
    if line.endswith("\r\n"):
        return line[:-2] + suffix + "\r\n"
    if line.endswith(("\n", "\r")):
        return line[:-1] + suffix + line[-1]
    return line + suffix


class InvalidDocumentEncodingError(OntosUserError):
    """A mutation target cannot be decoded without changing its bytes."""

    def __init__(self, path: Path):
        object.__setattr__(self, "path", path)
        super().__init__(
            f"{path} is not valid UTF-8 and was not modified. "
            "Re-save the file as UTF-8, then retry.",
            code="E_COMMAND_FAILED",
        )


def read_utf8_for_mutation(path: Path) -> str:
    """Decode a mutation target strictly and attach an actionable path."""
    try:
        return path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidDocumentEncodingError(path) from exc


def _read_decoded_content(path: Path) -> _DecodedContent:
    decoded = read_utf8_for_mutation(path)
    bom = "\ufeff" if decoded.startswith("\ufeff") else ""
    without_bom = decoded[len(bom) :]
    prefix_len = len(without_bom) - len(without_bom.lstrip())
    whitespace_prefix = without_bom[:prefix_len]
    leading_prefix = bom + whitespace_prefix
    normalized = without_bom[prefix_len:]
    return _DecodedContent(
        original=decoded,
        leading_prefix=leading_prefix,
        normalized=normalized,
        leading_line_offset=whitespace_prefix.count("\n"),
    )


def _split_frontmatter(normalized: str) -> _FrontmatterSplit:
    split = split_frontmatter_text(normalized)
    if split is None:
        return _FrontmatterSplit(
            has_frontmatter=False,
            frontmatter="",
            body=normalized,
            body_abs_offset=0,
        )
    yaml_text, body_text, body_offset = split
    lines = normalized.splitlines(keepends=True)
    opening_suffix = lines[0][3:]
    closing_line = ""
    consumed = len(lines[0])
    for line in lines[1:]:
        if consumed + len(line) == body_offset:
            closing_line = line
            break
        consumed += len(line)
    closing_suffix = closing_line[3:]
    frontmatter = opening_suffix + yaml_text
    body = closing_suffix + body_text
    body_abs_offset = len(f"---{frontmatter}---")
    return _FrontmatterSplit(
        has_frontmatter=True,
        frontmatter=frontmatter,
        body=body,
        body_abs_offset=body_abs_offset,
    )


def _is_blank_or_comment_line(line: str) -> bool:
    stripped = line.rstrip("\r\n").strip()
    return not stripped or stripped.startswith("#")


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
        key = _decode_top_level_key(match)
        if key is None:
            continue
        colon_index = match.start("value") - 1
        value_text = match.group("value")
        top_level_entries.append((key, index, line, colon_index, value_text))

    results: List[_TopLevelField] = []
    for pos, entry in enumerate(top_level_entries):
        next_line_index = top_level_entries[pos + 1][1] if pos + 1 < len(top_level_entries) else len(lines)
        end_line_index = next_line_index
        while end_line_index > entry[1] + 1 and _is_blank_or_comment_line(
            lines[end_line_index - 1]
        ):
            end_line_index -= 1
        results.append(
            _TopLevelField(
                key=entry[0],
                line_index=entry[1],
                line_text=entry[2],
                colon_index=entry[3],
                value_text=entry[4],
                end_line_index=end_line_index,
            )
        )
    return results


def _decode_top_level_key(match: re.Match[str]) -> Optional[str]:
    """Return the semantic key for a supported plain or quoted mapping key."""
    plain = match.group("plain")
    if plain is not None:
        return plain

    token = match.group("single") or match.group("double")
    if token is None:
        return None
    try:
        parsed, _ = parse_frontmatter_content(f"---\n{token}: null\n---\n")
    except ValueError:
        return None
    if not isinstance(parsed, dict) or len(parsed) != 1:
        return None
    key = next(iter(parsed))
    return key if isinstance(key, str) else None


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
