"""Tests for zone-aware body reference scanning."""

import pytest
from pathlib import Path
from typing import Optional

from ontos.core.body_refs import (
    MatchType,
    ZoneType,
    _looks_like_doc_id,
    scan_body_references,
)


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


# --- False-positive filter tests ---


class TestLooksLikeDocIdFilters:
    """Tests for _looks_like_doc_id false-positive rejection."""

    @pytest.mark.parametrize("token", ["1", "2", "42", "100", "0", "999"])
    def test_bare_numbers_rejected(self, token):
        assert _looks_like_doc_id(token) is False

    @pytest.mark.parametrize("token", ["1000", "12345"])
    def test_large_numbers_still_accepted(self, token):
        """Numbers with 4+ digits pass — they're unusual enough to flag."""
        assert _looks_like_doc_id(token) is True

    @pytest.mark.parametrize("token", [
        "v3.0", "v3.2", "v3.2.1", "v3.2.3", "v3.3",
        "3.0", "3.2.1", "2.0.0",
        "V3.2",
    ])
    def test_version_strings_rejected(self, token):
        assert _looks_like_doc_id(token) is False

    @pytest.mark.parametrize("token", [
        "v3.0.4_Code_Review_Claude",  # version + underscore suffix = real doc ID
        "v3_2_4_proposal",
        "v3_2",  # underscore version = looks like an ID
    ])
    def test_real_doc_ids_accepted(self, token):
        assert _looks_like_doc_id(token) is True

    @pytest.mark.parametrize("token", [
        "depends_on", "status", "type", "id", "pending_curation",
        "update_policy", "curation_level", "ontos_schema",
    ])
    def test_known_field_names_rejected(self, token):
        assert _looks_like_doc_id(token) is False

    @pytest.mark.parametrize("token", [
        "AGENTS.md", "README.md", "config.toml", "schema.yaml",
        "body_refs.py", "index.js", "app.tsx", "styles.css",
    ])
    def test_filenames_with_extensions_rejected(self, token):
        assert _looks_like_doc_id(token) is False

    def test_underscore_id_without_digits_accepted(self):
        assert _looks_like_doc_id("auth_flow") is True

    def test_dot_id_without_version_pattern_accepted(self):
        assert _looks_like_doc_id("config.main_settings") is True


class TestFalsePositiveScanning:
    """Integration tests: false positives should not appear in scan output."""

    def test_bare_numbers_not_in_scan(self):
        scan = _scan("Items: 1, 2, 3, 4, 5")
        ids = {m.normalized_id for m in scan.matches}
        assert "1" not in ids
        assert "2" not in ids

    def test_version_strings_not_in_scan(self):
        scan = _scan("Upgraded from v3.2 to v3.3.0 today.")
        ids = {m.normalized_id for m in scan.matches}
        assert "v3.2" not in ids
        assert "v3.3.0" not in ids

    def test_field_names_not_in_scan(self):
        scan = _scan("The depends_on field links documents.")
        ids = {m.normalized_id for m in scan.matches}
        assert "depends_on" not in ids

    def test_filenames_not_in_scan(self):
        scan = _scan("See AGENTS.md for details.")
        ids = {m.normalized_id for m in scan.matches}
        assert "AGENTS.md" not in ids

    def test_real_doc_ids_still_detected(self):
        scan = _scan("See v3_2_4_proposal and auth_flow for details.")
        ids = {m.normalized_id for m in scan.matches}
        assert "v3_2_4_proposal" in ids
        assert "auth_flow" in ids


class TestKnownIdsBypassFilters:
    """Tests that known_ids mode bypasses _looks_like_doc_id filters."""

    def test_known_ids_mode_detects_version_like_and_field_name_ids(self):
        """When known_ids is provided, version-like and field-name tokens that
        would be rejected by _looks_like_doc_id ARE detected."""
        body = "References v3.2 and depends_on in text."
        scan = scan_body_references(
            path=Path("docs/test.md"),
            body=body,
            known_ids={"v3.2", "depends_on"},
            include_skipped=True,
        )
        ids = {m.normalized_id for m in scan.matches}
        assert "v3.2" in ids
        assert "depends_on" in ids

    def test_generic_mode_filters_version_and_field_tokens(self):
        """Without known_ids, version-like and field-name tokens are filtered."""
        body = "References v3.2 and depends_on in text."
        scan = scan_body_references(
            path=Path("docs/test.md"),
            body=body,
            include_skipped=True,
        )
        ids = {m.normalized_id for m in scan.matches}
        assert "v3.2" not in ids
        assert "depends_on" not in ids

    def test_known_ids_mode_detects_filename_like_id(self):
        """A doc ID that looks like a filename is detected via known_ids."""
        body = "See README.md for details."
        scan = scan_body_references(
            path=Path("docs/test.md"),
            body=body,
            known_ids={"README.md"},
            include_skipped=True,
        )
        ids = {m.normalized_id for m in scan.matches}
        assert "README.md" in ids
