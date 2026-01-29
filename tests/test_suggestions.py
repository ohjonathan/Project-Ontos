import pytest
from pathlib import Path
from ontos.core.suggestions import suggest_candidates_for_broken_ref
from ontos.core.types import DocumentData, DocumentType, DocumentStatus


@pytest.fixture
def mock_docs():
    """Create a dictionary of dummy DocumentData for testing."""
    docs = {}
    
    # 1. Base doc
    docs["finance_engine_architecture"] = DocumentData(
        id="finance_engine_architecture",
        type=DocumentType.STRATEGY,
        status=DocumentStatus.ACTIVE,
        filepath=Path("docs/strategy/finance_engine_architecture.md"),
        frontmatter={},
        content="Content",
        aliases=["finance_arch", "engine_design"]
    )
    
    # 2. Similar name
    docs["finance_api_reference"] = DocumentData(
        id="finance_api_reference",
        type=DocumentType.ATOM,
        status=DocumentStatus.ACTIVE,
        filepath=Path("docs/atoms/finance_api_reference.md"),
        frontmatter={},
        content="Content"
    )
    
    # 3. Completely different
    docs["user_onboarding_flow"] = DocumentData(
        id="user_onboarding_flow",
        type=DocumentType.PRODUCT,
        status=DocumentStatus.ACTIVE,
        filepath=Path("docs/product/user_onboarding_flow.md"),
        frontmatter={},
        content="Content"
    )
    
    return docs


def test_suggest_exact_substring_match(mock_docs):
    """Test substring matching (confidence 0.85)."""
    # "finance_engine" is a substring of "finance_engine_architecture"
    results = suggest_candidates_for_broken_ref("finance_engine", mock_docs)
    
    assert len(results) >= 1
    doc_id, score, reason = results[0]
    assert doc_id == "finance_engine_architecture"
    assert score == 0.85
    assert reason == "substring match"


def test_suggest_alias_match(mock_docs):
    """Test alias matching (confidence 0.85)."""
    # "finance_arch" is an alias of "finance_engine_architecture"
    results = suggest_candidates_for_broken_ref("finance_arch", mock_docs)
    
    assert len(results) >= 1
    doc_id, score, reason = results[0]
    assert doc_id == "finance_engine_architecture"
    assert score == 0.85
    assert reason == "alias match"


def test_suggest_levenshtein_match(mock_docs):
    """Test fuzzy matching via Levenshtein distance."""
    # "finanxe_api_reference" is close to "finance_api_reference" (one char typo)
    results = suggest_candidates_for_broken_ref("finanxe_api_reference", mock_docs)
    
    assert len(results) >= 1
    doc_id, score, reason = results[0]
    assert doc_id == "finance_api_reference"
    assert score > 0.9  # Very close match
    assert "similarity" in reason


def test_suggest_no_match_below_threshold(mock_docs):
    """Test that no results are returned if score is below threshold."""
    results = suggest_candidates_for_broken_ref("completely_unrelated_text", mock_docs, threshold=0.9)
    assert len(results) == 0


def test_suggest_max_three_results(mock_docs):
    """Test that at most 3 results are returned."""
    # Add more docs to ensure multiple matches
    for i in range(10):
        mock_docs[f"test_doc_{i}"] = DocumentData(
            id=f"test_doc_{i}",
            type=DocumentType.ATOM,
            status=DocumentStatus.ACTIVE,
            filepath=Path(f"docs/test_{i}.md"),
            frontmatter={},
            content="Content"
        )
    
    results = suggest_candidates_for_broken_ref("test", mock_docs)
    assert len(results) == 3


def test_suggest_empty_corpus():
    """Test behavior with empty document dictionary."""
    results = suggest_candidates_for_broken_ref("anything", {})
    assert len(results) == 0


def test_suggest_deterministic_order(mock_docs):
    """Test that results are sorted by score DESC, then alpha ASC (v1.1)."""
    # Create two matches with same score (substring)
    mock_docs["apple_doc"] = DocumentData(
        id="apple_doc", type=DocumentType.ATOM, status=DocumentStatus.ACTIVE,
        filepath=Path("apple.md"), frontmatter={}, content="C"
    )
    mock_docs["alligator_doc"] = DocumentData(
        id="alligator_doc", type=DocumentType.ATOM, status=DocumentStatus.ACTIVE,
        filepath=Path("alligator.md"), frontmatter={}, content="C"
    )
    
    results = suggest_candidates_for_broken_ref("doc", mock_docs)
    
    # "alligator_doc" should come before "apple_doc" alphabetically
    # Both have 0.85 score
    
    # We need to filter to only our test docs if others match
    matches = [r for r in results if r[0] in ("apple_doc", "alligator_doc")]
    if len(matches) >= 2:
        assert matches[0][0] == "alligator_doc"
        assert matches[1][0] == "apple_doc"
