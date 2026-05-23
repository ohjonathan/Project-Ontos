"""Tests for public ontology metadata helpers."""

from ontos.core.ontology import get_valid_type_status, get_valid_types


def test_valid_types_include_lifecycle_artifacts():
    valid_types = get_valid_types()

    assert {
        "handoff",
        "tracker",
        "retro",
        "review",
        "spec",
        "report",
        "adr",
        "policy",
    }.issubset(valid_types)


def test_lifecycle_type_statuses_include_workflow_values():
    review_statuses = get_valid_type_status()["review"]

    assert {
        "proposed",
        "ready",
        "completed",
        "revised",
        "in-lifecycle",
    }.issubset(review_statuses)
