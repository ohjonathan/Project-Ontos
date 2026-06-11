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


# =============================================================================
# (#135) SuggestionIndex parity — the pruned/index path must return identical
# results to the legacy per-call path across all strategy branches.
# =============================================================================


def _legacy_suggest(broken_ref, all_docs, threshold=0.5):
    """Reference implementation: the pre-#135 unpruned algorithm."""
    from difflib import SequenceMatcher

    if not broken_ref or not broken_ref.strip():
        return []
    candidates = []
    broken_lower = broken_ref.lower()
    for doc_id, doc in all_docs.items():
        doc_id_lower = doc_id.lower()
        if broken_lower in doc_id_lower or doc_id_lower in broken_lower:
            candidates.append((doc_id, 0.85, "substring match"))
            continue
        aliases = doc.aliases
        if aliases and any(broken_lower in alias.lower() for alias in aliases):
            candidates.append((doc_id, 0.85, "alias match"))
            continue
        ratio = SequenceMatcher(None, broken_lower, doc_id_lower).ratio()
        if ratio >= threshold:
            candidates.append((doc_id, ratio, f"similarity: {ratio:.0%}"))
    return sorted(candidates, key=lambda x: (-x[1], x[0]))[:3]


def test_index_path_matches_legacy_results(mock_docs):
    from ontos.core.suggestions import SuggestionIndex, suggest_candidates

    index = SuggestionIndex(mock_docs)
    probes = [
        "auth",                # substring
        "authentication",      # substring both directions
        "login",               # alias (if present in fixture)
        "auth_systme",         # fuzzy near-match
        "atuh_system",         # transposition
        "zzz_nothing_alike",   # below threshold
        "a",                   # very short
        "",                    # empty
        "  ",                  # whitespace
    ]
    for probe in probes:
        assert suggest_candidates(probe, index) == _legacy_suggest(probe, mock_docs), (
            f"index/legacy divergence for probe {probe!r}"
        )


def test_wrapper_remains_equivalent(mock_docs):
    from ontos.core.suggestions import suggest_candidates_for_broken_ref

    for probe in ("auth", "auth_systme", "nope_nothing"):
        assert suggest_candidates_for_broken_ref(probe, mock_docs) == _legacy_suggest(
            probe, mock_docs
        )


def test_index_threshold_boundary_parity(mock_docs):
    """Near the 0.5 threshold the quick-ratio gates must not drop survivors."""
    from ontos.core.suggestions import SuggestionIndex, suggest_candidates

    index = SuggestionIndex(mock_docs)
    # Construct probes of varying overlap against fixture ids.
    for doc_id in mock_docs:
        half = doc_id[: max(1, len(doc_id) // 2)]
        scrambled = doc_id[::-1]
        for probe in (half, scrambled, half + "_x"):
            assert suggest_candidates(probe, index) == _legacy_suggest(probe, mock_docs)
