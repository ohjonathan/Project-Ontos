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
