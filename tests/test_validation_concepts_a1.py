"""Tests for concept structural validation (Track A1)."""
import pytest
from ontos.core.validation import ValidationOrchestrator
from ontos.core.types import DocumentData, DocumentType, DocumentStatus
from pathlib import Path

def test_validate_concepts_structural_checks():
    """Verify concept list integrity checks."""
    docs = {
        "log1": DocumentData(
            id="log1",
            type=DocumentType.LOG,
            status=DocumentStatus.ACTIVE,
            filepath=Path("log1.md"),
            frontmatter={"concepts": ["c1", "c1"]}, # Duplicate
            content=""
        ),
        "log2": DocumentData(
            id="log2",
            type=DocumentType.LOG,
            status=DocumentStatus.ACTIVE,
            filepath=Path("log2.md"),
            frontmatter={"concepts": ["c1", 123]}, # Non-string
            content=""
        ),
        "log3": DocumentData(
            id="log3",
            type=DocumentType.LOG,
            status=DocumentStatus.ACTIVE,
            filepath=Path("log3.md"),
            frontmatter={"concepts": []}, # Empty
            content=""
        )
    }
    
    orchestrator = ValidationOrchestrator(docs)
    orchestrator.validate_concepts()
    
    warnings = [w.message for w in orchestrator.warnings]
    assert any("Duplicate concepts" in m for m in warnings)
    assert any("Non-string items" in m for m in warnings)
    assert any("Empty 'concepts' list" in m for m in warnings)

def test_validate_concepts_severity_override():
    """Verify that concept validation severity can be overridden."""
    docs = {
        "log1": DocumentData(
            id="log1",
            type=DocumentType.LOG,
            status=DocumentStatus.ACTIVE,
            filepath=Path("log1.md"),
            frontmatter={"concepts": []},
            content=""
        )
    }
    
    # Override to error
    config = {"severity_map": {"concepts": "error"}}
    orchestrator = ValidationOrchestrator(docs, config=config)
    orchestrator.validate_concepts()
    
    assert len(orchestrator.errors) == 1
    assert orchestrator.errors[0].severity == "error"


def test_validate_concepts_warns_on_unknown_vocabulary_items():
    """Known vocabulary should trigger warnings for unknown concepts."""
    docs = {
        "log1": DocumentData(
            id="log1",
            type=DocumentType.LOG,
            status=DocumentStatus.ACTIVE,
            filepath=Path("log1.md"),
            frontmatter={"concepts": ["valid", "unknown_xyz"]},
            content=""
        )
    }

    orchestrator = ValidationOrchestrator(
        docs,
        config={"known_concepts": {"valid"}},
    )
    orchestrator.validate_concepts()

    assert any("Unknown concept: 'unknown_xyz'" in warning.message for warning in orchestrator.warnings)


def test_impacts_and_describes_allow_severity_override():
    """Callers can override impacts/describes severity per invocation."""
    docs = {
        "doc1": DocumentData(
            id="doc1",
            type=DocumentType.ATOM,
            status=DocumentStatus.ACTIVE,
            filepath=Path("doc1.md"),
            frontmatter={},
            content="",
            impacts=["missing_impact"],
            describes=["missing_describes"],
        )
    }

    orchestrator = ValidationOrchestrator(docs)
    orchestrator.validate_impacts(severity="error")
    orchestrator.validate_describes(severity="error")

    messages = [error.message for error in orchestrator.errors]
    assert any("Impact reference 'missing_impact' not found" in message for message in messages)
    assert any("describes 'missing_describes' not found" in message for message in messages)


def test_validate_concepts_unhashable_items_no_crash():
    """VUL-01: Concepts list containing unhashable items (dict) should not crash."""
    docs = {
        "log1": DocumentData(
            id="log1",
            type=DocumentType.LOG,
            status=DocumentStatus.ACTIVE,
            filepath=Path("log1.md"),
            frontmatter={"concepts": [{"key": "val"}, "valid"]},
            content=""
        )
    }

    orchestrator = ValidationOrchestrator(docs)
    # This should not raise TypeError: unhashable type: 'dict'
    orchestrator.validate_concepts()

    assert any("Non-string items in concepts: {'key': 'val'}" in warning.message for warning in orchestrator.warnings)
