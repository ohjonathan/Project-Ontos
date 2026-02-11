"""Tests for zone-aware body reference scanning."""

from pathlib import Path
from typing import Optional

from ontos.core.body_refs import MatchType, ZoneType, scan_body_references


def _scan(body: str, *, rename_target: Optional[str] = None):
    return scan_body_references(
        path=Path("docs/test.md"),
        body=body,
        rename_target=rename_target,
        include_skipped=True,
    )


def test_bare_token_in_plain_text_matches():
    scan = _scan("See v3_2_4_proposal for details.")
    assert any(match.normalized_id == "v3_2_4_proposal" for match in scan.matches)


def test_token_in_code_fence_is_skipped_for_link_check_mode():
    body = "```yaml\nid: v3_2_4_proposal\n```\n"
    scan = _scan(body)
    assert scan.matches == []


def test_token_in_inline_code_is_skipped_for_link_check_mode():
    scan = _scan("Use `v3_2_4_proposal` in examples.")
    assert scan.matches == []


def test_rename_target_reports_skipped_zone_sightings():
    body = "Use `v3_2_4_proposal` in examples.\n```yaml\nid: v3_2_4_proposal\n```\n"
    scan = _scan(body, rename_target="v3_2_4_proposal")
    zones = {match.zone for match in scan.matches}
    assert ZoneType.INLINE_CODE in zones
    assert ZoneType.CODE_FENCE in zones
    assert all(match.rewritable is False for match in scan.matches)


def test_markdown_link_target_internal_matches():
    scan = _scan("See [proposal](v3_2_4_proposal).")
    assert any(match.match_type == MatchType.MARKDOWN_LINK_TARGET for match in scan.matches)
    assert any(match.normalized_id == "v3_2_4_proposal" for match in scan.matches)


def test_markdown_link_target_external_url_is_ignored():
    scan = _scan("See [site](https://example.com/reference).")
    assert scan.matches == []


def test_start_and_end_boundary_matches():
    scan = _scan("v3_2_4_proposal")
    assert len(scan.matches) == 1
    assert scan.matches[0].col_start == 1


def test_prefix_collision_not_matched():
    scan = _scan("See v3_2_1 for details.")
    assert all(match.normalized_id != "v3_2" for match in scan.matches)
    assert any(match.normalized_id == "v3_2_1" for match in scan.matches)


def test_dot_containing_id_matches_exactly():
    scan = _scan("See v3.0.4_Code_Review_Claude for details.")
    assert any(match.normalized_id == "v3.0.4_Code_Review_Claude" for match in scan.matches)


def test_mixed_links_and_bare_tokens_same_line():
    scan = _scan("See [proposal](v3_2_4_proposal) and v3.0.4_Code_Review_Claude.")
    kinds = {(match.match_type, match.normalized_id) for match in scan.matches}
    assert (MatchType.MARKDOWN_LINK_TARGET, "v3_2_4_proposal") in kinds
    assert (MatchType.BARE_ID_TOKEN, "v3.0.4_Code_Review_Claude") in kinds


def test_sentence_punctuation_boundaries_match():
    scan = _scan("v3_2: v3_2; v3_2? v3_2! v3_2.")
    hits = [match for match in scan.matches if match.normalized_id == "v3_2"]
    assert len(hits) == 5


def test_period_inside_id_not_treated_as_boundary():
    scan = _scan("Do not match v3_2.1 as v3_2.")
    hits = [match for match in scan.matches if match.normalized_id == "v3_2"]
    assert len(hits) == 1
    assert hits[0].line == 1


def test_table_and_blockquote_boundaries_match():
    table_scan = _scan("| id | v3_2 |")
    quote_scan = _scan("> see v3_2")
    assert any(match.normalized_id == "v3_2" for match in table_scan.matches)
    assert any(match.normalized_id == "v3_2" for match in quote_scan.matches)


def test_markdown_link_with_title_matches():
    scan = _scan('[text](v3_2_4_proposal "title") and [text](v3_2_4_proposal \'title\')')
    links = [match for match in scan.matches if match.match_type == MatchType.MARKDOWN_LINK_TARGET]
    assert len(links) == 2
    assert all(match.normalized_id == "v3_2_4_proposal" for match in links)


def test_markdown_link_with_balanced_parentheses_and_escaped_close_paren():
    scan = _scan(r"[text](docs/ref/(v3_2_4_proposal\)).md)")
    assert any(match.match_type == MatchType.MARKDOWN_LINK_TARGET for match in scan.matches)


def test_unclosed_fence_eof_skips_remainder():
    body = "```python\nv3_2_4_proposal\nstill code"
    scan = _scan(body)
    assert scan.matches == []


def test_nested_fence_content_skipped_until_matching_closer():
    body = "````markdown\n```\nv3_2_4_proposal\n```\n````\nvisible v3_2_4_proposal"
    scan = _scan(body)
    assert len(scan.matches) == 1
    assert scan.matches[0].line == 6


def test_unsupported_markdown_forms_are_ignored():
    body = (
        "[text][ref]\n"
        "[ref]: v3_2_4_proposal\n"
        "<https://example.com>\n"
        "[[v3_2_4_proposal]]\n"
        '<a href="v3_2_4_proposal">link</a>\n'
    )
    scan = _scan(body)
    assert scan.matches == []
