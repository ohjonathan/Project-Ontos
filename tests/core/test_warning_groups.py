"""Unit tests for ontos.core.warning_groups (#132)."""

from ontos.core.types import ValidationError, ValidationErrorType
from ontos.core.warning_groups import (
    DEFAULT_SAMPLE_SIZE,
    WarningGroup,
    format_group_lines,
    group_warning_records,
    groups_to_payload,
    select_warning_records,
)


def _record(rule_id, *, severity="warning", document_id=None, message="msg"):
    record = {"severity": severity, "message": message}
    if rule_id is not None:
        record["rule_id"] = rule_id
    if document_id is not None:
        record["document_id"] = document_id
    return record


def _records():
    return [
        _record("orphan", document_id="doc_a"),
        _record("orphan", document_id="doc_b"),
        _record("orphan", document_id="doc_c"),
        _record("orphan", document_id="doc_d"),
        _record("depth", document_id="doc_e"),
        _record("schema", severity="error", document_id="doc_f"),
        _record(None, document_id="doc_g"),
    ]


class TestGroupWarningRecords:
    def test_counts_match_input(self):
        groups = group_warning_records(_records())
        assert sum(group.count for group in groups) == 7
        by_rule = {group.rule_id: group.count for group in groups}
        assert by_rule == {"orphan": 4, "depth": 1, "schema": 1, "unknown": 1}

    def test_samples_bounded_at_default_size(self):
        groups = group_warning_records(_records())
        orphan = next(group for group in groups if group.rule_id == "orphan")
        assert len(orphan.samples) == DEFAULT_SAMPLE_SIZE
        # Samples preserve input order and content.
        assert orphan.samples[0]["document_id"] == "doc_a"
        assert orphan.samples[2]["document_id"] == "doc_c"

    def test_deterministic_order_count_desc_then_rule_id(self):
        groups = group_warning_records(_records())
        assert [group.rule_id for group in groups] == [
            "orphan", "depth", "schema", "unknown"
        ]

    def test_missing_rule_id_buckets_under_unknown(self):
        groups = group_warning_records([_record(None)])
        assert groups[0].rule_id == "unknown"

    def test_by_severity_tally(self):
        groups = group_warning_records(
            [_record("schema"), _record("schema", severity="error")]
        )
        assert groups[0].by_severity == {"warning": 1, "error": 1}

    def test_rule_id_filter(self):
        groups = group_warning_records(_records(), rule_id="depth")
        assert len(groups) == 1
        assert groups[0].rule_id == "depth"

    def test_samples_are_unmodified_record_dicts(self):
        """Parity guard: samples must be exactly the serialized records, so
        CLI ValidationError.to_dict() output and MCP snapshot-issue dicts
        survive grouping untouched."""
        issue = ValidationError(
            error_type=ValidationErrorType.ORPHAN,
            doc_id="doc_a",
            filepath="docs/a.md",
            message="Document has no incoming dependencies",
            fix_suggestion="",
            severity="warning",
        )
        snapshot_style = {
            "severity": "warning",
            "rule_id": "schema.log_missing_fields",
            "message": "Log missing fields: date",
        }
        records = [issue.to_dict(), snapshot_style]
        groups = group_warning_records(records)
        samples = [sample for group in groups for sample in group.samples]
        assert issue.to_dict() in samples
        assert snapshot_style in samples


class TestGroupsToPayload:
    def test_include_samples_false_empties_samples(self):
        payload = groups_to_payload(
            group_warning_records(_records()), include_samples=False
        )
        assert all(item["samples"] == [] for item in payload)
        assert all(item["count"] > 0 for item in payload)

    def test_payload_shape(self):
        payload = groups_to_payload(group_warning_records(_records()))
        assert set(payload[0]) == {"rule_id", "count", "by_severity", "samples"}


class TestSelectWarningRecords:
    def test_no_filters_returns_everything(self):
        page, total, truncated = select_warning_records(_records())
        assert total == 7
        assert len(page) == 7
        assert truncated is False

    def test_rule_filter(self):
        page, total, truncated = select_warning_records(_records(), rule_id="orphan")
        assert total == 4
        assert all(record["rule_id"] == "orphan" for record in page)
        assert truncated is False

    def test_severity_filter(self):
        page, total, _ = select_warning_records(_records(), severity="error")
        assert total == 1
        assert page[0]["rule_id"] == "schema"

    def test_offset_limit_pagination(self):
        page1, total, truncated1 = select_warning_records(
            _records(), rule_id="orphan", offset=0, limit=3
        )
        page2, _, truncated2 = select_warning_records(
            _records(), rule_id="orphan", offset=3, limit=3
        )
        assert total == 4
        assert [r["document_id"] for r in page1] == ["doc_a", "doc_b", "doc_c"]
        assert [r["document_id"] for r in page2] == ["doc_d"]
        assert truncated1 is True
        assert truncated2 is True

    def test_limit_truncation_flag(self):
        _, _, truncated = select_warning_records(_records(), limit=2)
        assert truncated is True


class TestFormatGroupLines:
    def test_formats_from_warning_group_objects(self):
        lines = format_group_lines(group_warning_records(_records()))
        assert lines[0].startswith("orphan x4")
        assert "e.g. doc_a" in lines[0]

    def test_formats_from_payload_dicts(self):
        payload = groups_to_payload(group_warning_records(_records()))
        lines = format_group_lines(payload)
        assert lines[0].startswith("orphan x4")

    def test_limit_appends_more_marker(self):
        groups = [
            WarningGroup(rule_id=f"rule_{i}", count=1, by_severity={"warning": 1})
            for i in range(7)
        ]
        lines = format_group_lines(groups, limit=5)
        assert len(lines) == 6
        assert lines[-1] == "... and 2 more group(s)"
