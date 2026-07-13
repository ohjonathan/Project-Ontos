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


def test_single_line_backtick_span_does_not_swallow_following_diagnostics():
    body = "```inline_code```\nSee [[missing_doc]] afterward.\n"

    scan = _strict_scan(body)

    assert [match.normalized_id for match in scan.matches] == ["missing_doc"]
    assert scan.matches[0].line == 2


def test_info_string_does_not_close_an_active_fence():
    body = (
        "```\n"
        "```python\n"
        "[[inside_code]]\n"
        "```\n"
        "See [[outside_code]].\n"
    )

    scan = _strict_scan(body)

    assert [match.normalized_id for match in scan.matches] == ["outside_code"]
    assert scan.matches[0].line == 5


def test_four_space_indented_marker_is_not_a_fence():
    scan = _strict_scan("    ```yaml\nSee [[visible_doc]].\n")

    assert [match.normalized_id for match in scan.matches] == ["visible_doc"]


def test_unsupported_markdown_forms_are_ignored():
    # (#117) Wikilink spans `[[…]]` are now a SUPPORTED generic-mode source
    # for BARE_ID_TOKEN (opt-in via include_generic_bare_id_token=False
    # callers). When the legacy heuristic is enabled (the default for this
    # test), wikilinks are still treated as opaque — the prose scanner
    # already detects `v3_2_4_proposal` elsewhere — but the `[[…]]` span
    # itself doesn't double-fire.
    body = (
        "[text][ref]\n"
        "[ref]: v3_2_4_proposal\n"
        "<https://example.com>\n"
        '<a href="v3_2_4_proposal">link</a>\n'
    )
    scan = _scan(body)
    assert scan.matches == []


# ---------------------------------------------------------------------------
# (#117) include_generic_bare_id_token=False — opt-in narrow generic mode
# ---------------------------------------------------------------------------


def _strict_scan(body: str):
    return scan_body_references(
        path=Path("docs/test.md"),
        body=body,
        include_skipped=False,
        include_generic_bare_id_token=False,
    )


def test_strict_generic_mode_suppresses_prose_tokens():
    # Prose tokens that the legacy heuristic flagged (~11k false positives
    # on a 163-doc corpus) emit no matches when the heuristic is disabled.
    scan = _strict_scan(
        "Workspace `company-os` declares depends_on across many sources. "
        "We saw v3.2.1 alongside the_test_token_42 in normal prose."
    )
    bare_tokens = [m for m in scan.matches if m.match_type == MatchType.BARE_ID_TOKEN]
    assert bare_tokens == []


def test_strict_generic_mode_emits_wikilink_sigil_matches():
    scan = _strict_scan("See [[my-doc-id]] for details.")
    bare_tokens = [m for m in scan.matches if m.match_type == MatchType.BARE_ID_TOKEN]
    assert len(bare_tokens) == 1
    assert bare_tokens[0].normalized_id == "my-doc-id"


def test_strict_generic_mode_preserves_markdown_link_targets():
    scan = _strict_scan("See [proposal](v3_2_4_proposal) for details.")
    link_targets = [m for m in scan.matches if m.match_type == MatchType.MARKDOWN_LINK_TARGET]
    assert len(link_targets) == 1
    assert link_targets[0].normalized_id == "v3_2_4_proposal"


def test_strict_generic_mode_handles_multiple_wikilinks():
    scan = _strict_scan(
        "Refs: [[alpha]] and [[beta-doc]] plus prose like v3_2_4_proposal."
    )
    ids = sorted(m.normalized_id for m in scan.matches if m.match_type == MatchType.BARE_ID_TOKEN)
    assert ids == ["alpha", "beta-doc"]


def test_wikilink_alias_and_heading_emit_only_document_id():
    scan = _strict_scan(
        "Refs: [[beta|The Beta Doc]], [[beta#Section One]], "
        "and [[ beta#Heading|Alias ]]."
    )

    matches = [m for m in scan.matches if m.match_type == MatchType.BARE_ID_TOKEN]
    assert [match.normalized_id for match in matches] == ["beta", "beta", "beta"]
    assert [match.raw_match for match in matches] == ["beta", "beta", "beta"]


def test_rename_wikilink_alias_and_heading_rewrites_target_span_only():
    body = "[[beta|The Beta Doc]] [[beta#Section One]] [[beta]]"

    scan = _scan(body, rename_target="beta")

    assert len(scan.matches) == 3
    assert all(match.rewritable for match in scan.matches)
    rewritten = body
    for match in sorted(scan.matches, key=lambda item: item.abs_start, reverse=True):
        rewritten = rewritten[:match.abs_start] + "beta2" + rewritten[match.abs_end:]
    assert rewritten == "[[beta2|The Beta Doc]] [[beta2#Section One]] [[beta2]]"


def test_wikilink_alias_and_heading_text_are_not_reference_targets():
    body = "[[other|old_id alias]] [[other#old_id heading]] plain old_id"

    rename_scan = _scan(body, rename_target="old_id")
    strict_scan = _strict_scan(body)

    assert len(rename_scan.matches) == 1
    assert rename_scan.matches[0].raw_match == "old_id"
    assert rename_scan.matches[0].abs_start == body.rfind("old_id")
    assert [match.normalized_id for match in strict_scan.matches] == ["other", "other"]


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

    @pytest.mark.parametrize("token", [
        "A1", "A3", "B2", "L0", "L1", "L2", "L3",
        "M-2", "B-2", "NB-1", "NB-2", "NB-3", "X-H1", "X-H2",
    ])
    def test_short_labels_rejected(self, token):
        assert _looks_like_doc_id(token) is False

    @pytest.mark.parametrize("token", [
        "AUTO_CONSOLIDATE", "MY_CONFIG", "SOME_SETTING",
    ])
    def test_all_caps_constants_rejected(self, token):
        assert _looks_like_doc_id(token) is False

    @pytest.mark.parametrize("token", [
        "v3.2.1b", "v2.x", "v3.2.x", "3.2.1a",
    ])
    def test_version_adjacent_rejected(self, token):
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

    def test_short_labels_not_in_scan(self):
        scan = _scan("Finding A1 and issue NB-1 resolved.")
        ids = {m.normalized_id for m in scan.matches}
        assert "A1" not in ids
        assert "NB-1" not in ids

    def test_all_caps_constants_not_in_scan(self):
        scan = _scan("Set AUTO_CONSOLIDATE to true.")
        ids = {m.normalized_id for m in scan.matches}
        assert "AUTO_CONSOLIDATE" not in ids

    def test_version_wildcards_not_in_scan(self):
        scan = _scan("Supports v2.x and v3.2.1b releases.")
        ids = {m.normalized_id for m in scan.matches}
        assert "v2.x" not in ids
        assert "v3.2.1b" not in ids

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
